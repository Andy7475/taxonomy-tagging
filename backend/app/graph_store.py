"""In-process triple store for the facility ontology, queried live via SPARQL.

Mirrors es_client.py's singleton pattern, but for an rdflib.Graph instead of
an Elasticsearch connection. Unlike scripts/ingest_locations.py (which
flattens the graph into Elasticsearch once, at ingest time), this graph is
kept in memory for the lifetime of the process and queried directly — the
live-triple-store half of the demo, alongside the build-time-flatten half.

Facts here (currently: geo:hasGeometry/geo:asWKT points) are looked up by the
same facility URIs already used as the `uri` field in Elasticsearch's
facility_locations documents, so a caller can freely mix a SPARQL result and
an ES result keyed on that shared identifier.
"""

from pathlib import Path

from rdflib import Graph, Namespace
from shapely import wkt as shapely_wkt

GEO = Namespace("http://www.opengis.net/ont/geosparql#")

_graph: Graph | None = None


def _ontology_dir() -> Path:
    from .config import settings

    if settings.ontology_dir:
        return Path(settings.ontology_dir)
    return Path(__file__).resolve().parents[2] / "ontology"


def _parse_graph() -> Graph:
    g = Graph()
    ontology_dir = _ontology_dir()
    for filename in (
        "facility.ttl",
        "facility_instances.ttl",
        "facility_geo.ttl",
        "facility_floorplans.ttl",
    ):
        g.parse(ontology_dir / filename, format="turtle")
    return g


def load_graph() -> Graph:
    global _graph
    _graph = _parse_graph()
    return _graph


def reload_graph() -> dict:
    g = load_graph()
    return {"status": "ok", "triples": len(g)}


def get_graph() -> Graph:
    if _graph is None:
        raise RuntimeError("Graph store not loaded — call load_graph() at startup")
    return _graph


_GEO_FEATURES_QUERY = """
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
SELECT ?uri ?wkt WHERE {
    ?uri geo:hasGeometry/geo:asWKT ?wkt .
}
"""


def geo_features(uris: list[str] | None = None) -> list[dict]:
    """Run a SPARQL SELECT for every geo:Feature's WKT geometry, parse it via
    shapely, and optionally restrict to a given set of URIs. Filtering is
    done in Python rather than a SPARQL FILTER/VALUES clause — the graph is
    small and in-memory, so there's no benefit to pushing the filter into
    the query itself, and it keeps this function simple to call with an
    arbitrary (possibly large) uri list.

    facility_geo.ttl mixes geometry kinds by facility_type (Site -> Polygon
    footprint, Building -> Point) under the same geo:asWKT predicate, so
    this returns a {uri, geometry_type, lat, lon, polygon} shape per
    feature: Points populate lat/lon, Polygons populate polygon (a ring of
    [lat, lon] pairs, ready for a Leaflet <Polygon>) and leave lat/lon None.

    Results are canonicalized through the graph's owl:sameAs closure using
    the SAME tie-break rule scripts/ingest_locations.py uses to pick each
    equivalence class's shared `uri` for Elasticsearch — otherwise a
    geo:Feature asserted on one sameAs-equivalent individual (e.g. Site
    Orange, whose facility_locations documents actually share Contractor
    Site 7's uri once merged) would silently fail to join with the
    Elasticsearch side, which only ever sees the canonical uri.
    """
    from scripts.ingest_locations import _sameas_closure

    g = get_graph()
    sameas = _sameas_closure(g)
    wanted = set(uris) if uris is not None else None

    results = []
    for row in g.query(_GEO_FEATURES_QUERY):
        uri = str(sameas.canonical(row.uri))
        if wanted is not None and uri not in wanted:
            continue
        geom = shapely_wkt.loads(str(row.wkt))
        # WKT axis order is (longitude latitude) per GeoSPARQL/OGC — shapely
        # preserves that as (x, y), so x is longitude, y is latitude; a
        # Leaflet position is [lat, lng], i.e. (y, x).
        if geom.geom_type == "Point":
            results.append({
                "uri": uri, "geometry_type": "Point",
                "lat": geom.y, "lon": geom.x, "polygon": None,
            })
        elif geom.geom_type == "Polygon":
            results.append({
                "uri": uri, "geometry_type": "Polygon",
                "lat": None, "lon": None,
                "polygon": [[y, x] for x, y in geom.exterior.coords],
            })
        # Other geometry kinds aren't part of this demo's vocabulary — skip
        # rather than guess at a representation.
    return results


_ENCLOSING_GEO_QUERY = """
PREFIX ies: <http://example.org/ontology/ies-lite#>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
SELECT ?subject ?ancestor WHERE {
    ?subject ies:isPartOf* ?ancestor .
    ?ancestor geo:hasGeometry ?g .
}
"""


def enclosing_geo_uris(uris: list[str]) -> set[str]:
    """For each given uri, the canonical uri of every self-or-ancestor node
    that carries a geo:Feature, reached by walking `ies:isPartOf*` — a
    SPARQL 1.1 property-path traversal of isPartOf's own declared
    owl:TransitiveProperty (facility.ttl). This is plain SPARQL, not OWL
    reasoning: the `*` (zero-or-more) path is evaluated by the query engine
    at query time, no owlrl closure involved. A Site or Building (which
    carries its own geometry) resolves to itself via the zero-length case;
    a Storey or Zone (which never does, see facility_geo.ttl) resolves to
    whichever enclosing Site/Building actually has one.

    Deliberately a separate query from geo_features() rather than folded
    into it: this only answers "which geo-tagged node(s) represent this
    uri", not "what does that node's geometry look like" — callers still
    fetch geometry via geo_features() for whatever this returns.
    """
    from scripts.ingest_locations import _sameas_closure

    g = get_graph()
    sameas = _sameas_closure(g)
    wanted = set(uris)

    found: set[str] = set()
    for row in g.query(_ENCLOSING_GEO_QUERY):
        if str(sameas.canonical(row.subject)) in wanted:
            found.add(str(sameas.canonical(row.ancestor)))
    return found


_FLOORPLAN_DIMS_QUERY = """
PREFIX fp: <http://example.org/ontology/floorplan#>
SELECT ?width ?height WHERE {
    ?storey fp:hasFloorplan ?plan .
    ?plan fp:width ?width ; fp:height ?height .
}
"""

_FLOORPLAN_ZONES_QUERY = """
PREFIX ies:  <http://example.org/ontology/ies-lite#>
PREFIX geo:  <http://www.opengis.net/ont/geosparql#>
PREFIX fp:   <http://example.org/ontology/floorplan#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?zone ?label ?wkt WHERE {
    ?zone ies:isPartOf ?storey ;
          rdfs:label ?label ;
          fp:hasRegion/geo:asWKT ?wkt .
}
"""


def floorplan(storey_uri: str) -> dict | None:
    """A Storey's mock 2D floor plan: canvas size plus each of its Zones'
    highlighted region, both sourced from facility_floorplans.ttl — the same
    geo:asWKT literal shape geo_features() reads for map points, just linked
    via fp:hasRegion (floorplan-local units) instead of geo:hasGeometry
    (WGS84). Returns None if this storey has no floor plan attached.
    """
    from rdflib import URIRef

    g = get_graph()
    storey = URIRef(storey_uri)

    dims = list(g.query(_FLOORPLAN_DIMS_QUERY, initBindings={"storey": storey}))
    if not dims:
        return None
    width, height = float(dims[0].width), float(dims[0].height)

    zones = []
    for row in g.query(_FLOORPLAN_ZONES_QUERY, initBindings={"storey": storey}):
        polygon = shapely_wkt.loads(str(row.wkt))
        zones.append(
            {
                "uri": str(row.zone),
                "label": str(row.label),
                "points": [list(pt) for pt in polygon.exterior.coords],
            }
        )

    return {"width": width, "height": height, "zones": zones}
