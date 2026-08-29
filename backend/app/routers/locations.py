from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from elasticsearch import AsyncElasticsearch

from ..es_client import get_es
from ..config import settings
from ..models_locations import Location, LocationSuggestion

router = APIRouter()


@router.get("/suggest", response_model=list[LocationSuggestion])
async def suggest_locations(
    q: str = "",
    exclude: str = "",
    limit: int = 10,
    es: AsyncElasticsearch = Depends(get_es),
):
    if not q.strip():
        return []

    exclude_uris = {e.strip() for e in exclude.split(",") if e.strip()}
    q_lower = q.lower()

    result = await es.search(
        index=settings.locations_index,
        body={
            "size": min(limit * 4, 200),
            "query": {
                "bool": {
                    "should": [
                        {"term": {"synonyms.keyword": q_lower}},
                        {"match": {"synonyms": {"query": q, "boost": 2}}},
                        {
                            "match": {
                                "label": {"query": q, "fuzziness": "AUTO", "boost": 3}
                            }
                        },
                        # `prefix` queries are not analyzed, so the term is
                        # lowercased explicitly to match path_segment_analyzer's
                        # lowercase-filtered index-time tokens (e.g. "ZoneA" ->
                        # "zonea") regardless of how the user capitalized it.
                        {"prefix": {"path.segments": q_lower}},
                    ],
                    "minimum_should_match": 1,
                }
            },
            "sort": ["_score", {"depth": "asc"}],
        },
    )

    # Deliberately not deduplicated by `uri`: a facility reachable via more
    # than one isPartOf chain (see ontology/facility_instances.ttl's Plant
    # Room) is indexed as one document per path, and every path-row is
    # surfaced as its own suggestion so the user can pick whichever
    # hierarchy frame of reference they recognize.
    suggestions: list[LocationSuggestion] = []
    for hit in result["hits"]["hits"]:
        src = hit["_source"]
        if src["uri"] in exclude_uris:
            continue

        syns = [s.lower() for s in src.get("synonyms", [])]
        if q_lower in syns or any(s.startswith(q_lower) for s in syns):
            matched_via = "synonym"
        elif q_lower in src.get("label", "").lower():
            matched_via = "label"
        else:
            matched_via = "path"

        suggestions.append(
            LocationSuggestion(
                uri=src["uri"],
                path=src["path"],
                label=src["label"],
                facility_type=src["facility_type"],
                depth=src["depth"],
                matched_via=matched_via,
            )
        )
        if len(suggestions) >= limit:
            break

    return suggestions


@router.get("/browse", response_model=list[LocationSuggestion])
async def browse_locations(
    exclude: str = "",
    es: AsyncElasticsearch = Depends(get_es),
):
    exclude_uris = {e.strip() for e in exclude.split(",") if e.strip()}

    result = await es.search(
        index=settings.locations_index,
        body={
            "size": 200,
            "query": {
                "bool": {
                    "must": {"match_all": {}},
                    "filter": {"range": {"depth": {"lte": 1}}},
                }
            },
            "sort": [{"label.keyword": "asc"}],
        },
    )

    return [
        LocationSuggestion(
            uri=hit["_source"]["uri"],
            path=hit["_source"]["path"],
            label=hit["_source"]["label"],
            facility_type=hit["_source"]["facility_type"],
            depth=hit["_source"]["depth"],
            matched_via="label",
        )
        for hit in result["hits"]["hits"]
        if hit["_source"]["uri"] not in exclude_uris
    ]


async def _resolve_canonical_uri(
    raw_uri: str, es: AsyncElasticsearch
) -> Optional[str]:
    """Hop 1: find the shared `uri` for any known identifier — the
    canonical uri itself, or any sameAs-equivalent instance's source_uri.
    A single-hop `uri OR source_uri` match is not enough on its own to
    fetch a *complete* equivalence class (see hop 2) but is enough to
    discover which canonical value that class shares."""
    result = await es.search(
        index=settings.locations_index,
        body={
            "size": 1,
            "query": {
                "bool": {
                    "should": [
                        {"term": {"uri": raw_uri}},
                        {"term": {"source_uri": raw_uri}},
                    ],
                    "minimum_should_match": 1,
                }
            },
        },
    )
    hits = result["hits"]["hits"]
    return hits[0]["_source"]["uri"] if hits else None


@router.get("/resolve", response_model=list[Location])
async def resolve_location(uri: str, es: AsyncElasticsearch = Depends(get_es)):
    """Return every known path realization of a location URI — across every
    sameAs-equivalent instance, not just the one `uri` happens to name — so
    a detail view can show all recognized hierarchy frames for an
    already-selected location. Two plain Elasticsearch queries (resolve to
    canonical, then fetch everything sharing it), no SPARQL required: the
    sameAs closure was already computed once at ingest time."""
    canonical_uri = await _resolve_canonical_uri(uri, es)
    if canonical_uri is None:
        raise HTTPException(status_code=404, detail=f"Location '{uri}' not found")

    result = await es.search(
        index=settings.locations_index,
        body={"size": 20, "query": {"term": {"uri": canonical_uri}}},
    )
    return [Location(**hit["_source"]) for hit in result["hits"]["hits"]]


@router.post("/ingest")
async def ingest(es: AsyncElasticsearch = Depends(get_es)):
    from scripts.ingest_locations import ingest_locations

    return await ingest_locations(es)
