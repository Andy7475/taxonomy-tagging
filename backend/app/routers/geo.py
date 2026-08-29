"""Geo endpoints: live SPARQL over the in-process facility graph
(graph_store.py), joined with Elasticsearch's facility_locations index by
the shared facility `uri` — no coordination between the two stores beyond
that shared identifier, and no change to the Elasticsearch mapping at all.
"""

import asyncio
from typing import Optional

from elasticsearch import AsyncElasticsearch
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from rdflib.plugins.sparql import prepareQuery
from rdflib.plugins.sparql.sparql import SPARQLError

from .. import graph_store
from ..config import settings
from ..es_client import get_es
from ..models_locations import FloorplanResponse, GeoFeature, MapLocation
from .locations import _resolve_canonical_uri

router = APIRouter()

SPARQL_TIMEOUT_SECONDS = 5.0
SPARQL_ROW_LIMIT = 200


@router.get("/locations", response_model=list[GeoFeature])
async def geo_locations(uris: str = ""):
    """Every geo:Feature (Point or Polygon) known to the graph, optionally
    restricted to a comma-separated uri list. Demonstrates the triple store
    on its own, with no Elasticsearch involved."""
    uri_list = [u.strip() for u in uris.split(",") if u.strip()] or None
    return [GeoFeature(**feat) for feat in graph_store.geo_features(uri_list)]


async def _paths_for_value(value: str, es: AsyncElasticsearch) -> list[str]:
    """A location filter value (URI or bare path) resolved to the path(s) a
    `prefix` query against facility_locations.path should match — mirrors
    the same URI-to-paths resolution routers/maintenance_issues.py already
    does against location_path, just applied to facility_locations' own
    `path` field."""
    value = value.strip()
    if not value:
        return []
    if not (value.startswith("http://") or value.startswith("https://")):
        return [value]

    canonical_uri = await _resolve_canonical_uri(value, es)
    if canonical_uri is None:
        return []
    result = await es.search(
        index=settings.locations_index,
        body={"size": 20, "query": {"term": {"uri": canonical_uri}}},
    )
    return sorted({h["_source"]["path"] for h in result["hits"]["hits"]})


async def _prefix_clauses(value: str, es: AsyncElasticsearch) -> list[dict]:
    paths = await _paths_for_value(value, es)
    return [{"prefix": {"path": p}} for p in paths]


@router.get("/map", response_model=list[MapLocation])
async def geo_map(
    filters: str = "",     # AND: comma-separated location URIs/paths
    or_filters: str = "",  # OR: comma-separated
    exclude: str = "",     # NOT: comma-separated
    es: AsyncElasticsearch = Depends(get_es),
):
    """The join demo: resolve the same AND/OR/NOT filter shape already used
    by LocationSearchBuilder against facility_locations itself (rather than
    maintenance_issues), collect the matching facilities' URIs, walk each up
    to its nearest self-or-ancestor geo-tagged node via a live SPARQL
    isPartOf* property-path traversal (graph_store.enclosing_geo_uris —
    isPartOf's own declared owl:TransitiveProperty, no OWL reasoner needed),
    then fetch geometry + Elasticsearch metadata for whichever nodes that
    resolves to and merge the two by URI."""
    filter_list = [f.strip() for f in filters.split(",") if f.strip()]
    or_list = [f.strip() for f in or_filters.split(",") if f.strip()]
    exclude_list = [f.strip() for f in exclude.split(",") if f.strip()]

    must: list = []
    should: list = []
    must_not: list = []

    for value in filter_list:
        clauses = await _prefix_clauses(value, es)
        if not clauses:
            return []
        must.append({"bool": {"should": clauses, "minimum_should_match": 1}})

    for value in or_list:
        should.extend(await _prefix_clauses(value, es))

    for value in exclude_list:
        must_not.extend(await _prefix_clauses(value, es))

    if not must and not should and not must_not:
        query = {"match_all": {}}
    else:
        bool_q: dict = {}
        if must:
            bool_q["must"] = must
        if should:
            bool_q["should"] = should
            bool_q["minimum_should_match"] = 1
        if must_not:
            bool_q["must_not"] = must_not
        query = {"bool": bool_q}

    result = await es.search(
        index=settings.locations_index,
        body={"size": 500, "query": query},
    )

    # One facility can appear as several (uri, path) documents; a map needs
    # one pin per facility, so dedupe by uri before looking up geometry.
    by_uri: dict[str, dict] = {}
    for hit in result["hits"]["hits"]:
        src = hit["_source"]
        by_uri.setdefault(src["uri"], src)

    # A matched Storey/Zone has no geo:Feature of its own — walk the live
    # graph up isPartOf* to whichever enclosing Site/Building actually has
    # one, then fetch THAT node's own facility_locations document (by uri),
    # so the map still shows something for it instead of silently dropping
    # every incident filed below Building depth.
    geo_uris = graph_store.enclosing_geo_uris(list(by_uri.keys()))
    missing_uris = geo_uris - by_uri.keys()
    if missing_uris:
        ancestor_result = await es.search(
            index=settings.locations_index,
            body={"size": len(missing_uris) * 2, "query": {"terms": {"uri": list(missing_uris)}}},
        )
        for hit in ancestor_result["hits"]["hits"]:
            src = hit["_source"]
            by_uri.setdefault(src["uri"], src)

    features = {feat["uri"]: feat for feat in graph_store.geo_features(list(geo_uris))}

    return [
        MapLocation(
            uri=uri,
            geometry_type=features[uri]["geometry_type"],
            lat=features[uri]["lat"],
            lon=features[uri]["lon"],
            polygon=features[uri]["polygon"],
            label=src["label"],
            path=src["path"],
            facility_type=src["facility_type"],
        )
        for uri, src in by_uri.items()
        if uri in features
    ]


@router.get("/floorplan", response_model=FloorplanResponse)
async def geo_floorplan(storey_uri: str):
    """A Storey's mock 2D floor plan with its Zones highlighted as regions —
    demonstrates facility_floorplans.ttl as a third independent ABox layered
    on the same Storey/Zone URIs, alongside facility_instances.ttl
    (containment) and facility_geo.ttl (lat/lon points)."""
    result = graph_store.floorplan(storey_uri)
    if result is None:
        raise HTTPException(status_code=404, detail="No floor plan for this storey")
    return FloorplanResponse(**result)


@router.post("/reload")
async def reload_geo_graph():
    """Re-parse ontology/*.ttl from disk — the SPARQL-side equivalent of
    POST /api/locations/ingest, but there's no Elasticsearch write step:
    the graph itself IS the queryable store."""
    return graph_store.reload_graph()


class SparqlRequest(BaseModel):
    query: str


class SparqlResponse(BaseModel):
    columns: list[str]
    rows: list[list[Optional[str]]]


def _run_select(query: str) -> SparqlResponse:
    try:
        parsed = prepareQuery(query)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid SPARQL: {exc}")

    if parsed.algebra.name != "SelectQuery":
        raise HTTPException(
            status_code=400,
            detail="Only SELECT queries are allowed in the playground",
        )

    try:
        result = graph_store.get_graph().query(parsed)
    except SPARQLError as exc:
        raise HTTPException(status_code=400, detail=f"Query failed: {exc}")

    columns = [str(v) for v in result.vars]
    rows = [
        [str(row[v]) if row[v] is not None else None for v in result.vars]
        for row in list(result)[:SPARQL_ROW_LIMIT]
    ]
    return SparqlResponse(columns=columns, rows=rows)


@router.post("/sparql", response_model=SparqlResponse)
async def run_sparql(body: SparqlRequest):
    """Read-only SPARQL playground over the live graph. Restricted to SELECT
    (rejecting anything else, including malformed queries, with a 400) and
    bounded by a wall-clock timeout — rdflib's query execution is
    synchronous/CPU-bound, so it's run in a thread to avoid blocking the
    event loop."""
    loop = asyncio.get_running_loop()
    try:
        return await asyncio.wait_for(
            loop.run_in_executor(None, _run_select, body.query),
            timeout=SPARQL_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Query timed out")
