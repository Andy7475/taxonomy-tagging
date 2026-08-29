import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from elasticsearch import AsyncElasticsearch, NotFoundError

from ..es_client import get_es
from ..config import settings
from ..models_locations import (
    MaintenanceIssue,
    MaintenanceIssueCreate,
    MaintenanceIssueSearchResponse,
)

router = APIRouter()


async def _resolve_canonical_uri(
    raw_uri: str, es: AsyncElasticsearch
) -> Optional[str]:
    """Hop 1: find the shared `uri` for any known identifier — the
    canonical uri, or a sameAs-equivalent instance's source_uri (e.g. an
    imported contractor issue referencing the contractor's own facility
    identifier directly)."""
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


async def _resolve_paths(
    raw_uri: str, es: AsyncElasticsearch
) -> tuple[Optional[str], list[str]]:
    """Hop 2: every path realization across the WHOLE merged identity, not
    just whichever instance `raw_uri` happened to name. This is what makes
    a contractor-sourced issue findable under the owner's hierarchy (and
    vice versa): `location_path` is denormalized as the FULL list below, so
    a `prefix` query against any one of those paths finds it — no SPARQL
    involved, the sameAs closure was already resolved once at ingest time."""
    canonical_uri = await _resolve_canonical_uri(raw_uri, es)
    if canonical_uri is None:
        return None, []
    result = await es.search(
        index=settings.locations_index,
        body={"size": 20, "query": {"term": {"uri": canonical_uri}}},
    )
    paths = sorted({h["_source"]["path"] for h in result["hits"]["hits"]})
    return canonical_uri, paths


async def _location_prefix_clauses(value: str, es: AsyncElasticsearch) -> list[dict]:
    """Turn one location filter value into the `prefix` clauses that should
    be OR'd together to match it: a URI resolves (via _resolve_paths) to
    every path across its whole sameAs-merged identity — so an AND/OR/NOT
    filter on a location correctly matches an issue regardless of which of
    that location's known hierarchy frames the issue happens to have been
    filed under. A bare path string (not a URI) is used directly."""
    value = value.strip()
    if not value:
        return []
    if value.startswith("http://") or value.startswith("https://"):
        _, paths = await _resolve_paths(value, es)
    else:
        paths = [value]
    return [{"prefix": {"location_path": p}} for p in paths]


@router.post("/", response_model=MaintenanceIssue, status_code=201)
async def create_issue(
    issue: MaintenanceIssueCreate, es: AsyncElasticsearch = Depends(get_es)
):
    canonical_uri, location_paths = await _resolve_paths(issue.location_uri, es)
    if canonical_uri is None:
        raise HTTPException(
            status_code=400, detail=f"Unknown location_uri '{issue.location_uri}'"
        )

    issue_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    body = {
        **issue.model_dump(),
        # Always store the canonical uri, even if the caller passed a
        # sameAs-equivalent instance's own identifier (e.g. an imported
        # contractor issue referencing their own facility uri directly).
        "location_uri": canonical_uri,
        "location_path": location_paths,
        "created_at": now,
    }

    await es.index(
        index=settings.maintenance_issues_index,
        id=issue_id,
        document=body,
        refresh=True,
    )
    return MaintenanceIssue(id=issue_id, **body)


@router.post("/seed")
async def seed_demo_issues(es: AsyncElasticsearch = Depends(get_es)):
    """Seed the demo maintenance issues from scripts/seed_maintenance_issues.py.
    Uses fixed ids, so it's idempotent — safe to click again (e.g. after
    re-ingesting the ontology). Requires the location ontology to already be
    ingested; any demo issue whose location_uri isn't found is skipped."""
    from scripts.seed_maintenance_issues import DEMO_ISSUES

    now = datetime.now(timezone.utc).isoformat()
    created = 0
    skipped = []

    for demo in DEMO_ISSUES:
        canonical_uri, paths = await _resolve_paths(demo["location_uri"], es)
        if canonical_uri is None:
            skipped.append(demo["title"])
            continue
        body = {
            "title": demo["title"],
            "description": demo.get("description"),
            "status": "open",
            "priority": demo.get("priority", "medium"),
            "location_uri": canonical_uri,
            "location_path": paths,
            "created_at": now,
        }
        await es.index(
            index=settings.maintenance_issues_index, id=demo["id"], document=body
        )
        created += 1

    await es.indices.refresh(index=settings.maintenance_issues_index)
    return {"status": "ok", "created": created, "skipped": skipped}


@router.get("/", response_model=MaintenanceIssueSearchResponse)
async def list_issues(
    filters: str = "",      # AND: comma-separated location URIs (or bare paths) — must match every one
    or_filters: str = "",   # OR: comma-separated — must match at least one
    exclude: str = "",      # NOT: comma-separated — must match none
    under: str = "",        # back-compat alias: equivalent to one extra AND filter
    size: int = 50,
    from_: int = 0,
    es: AsyncElasticsearch = Depends(get_es),
):
    filter_list = [f.strip() for f in filters.split(",") if f.strip()]
    if under.strip():
        filter_list.append(under.strip())
    or_list = [f.strip() for f in or_filters.split(",") if f.strip()]
    exclude_list = [f.strip() for f in exclude.split(",") if f.strip()]

    must: list = []
    should: list = []
    must_not: list = []

    for value in filter_list:
        clauses = await _location_prefix_clauses(value, es)
        if not clauses:
            # Unknown/unresolvable location — this AND condition can never
            # be satisfied, so the whole query can't match anything.
            return MaintenanceIssueSearchResponse(total=0, issues=[])
        must.append({"bool": {"should": clauses, "minimum_should_match": 1}})

    for value in or_list:
        should.extend(await _location_prefix_clauses(value, es))

    for value in exclude_list:
        must_not.extend(await _location_prefix_clauses(value, es))

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
        index=settings.maintenance_issues_index,
        body={
            "size": size,
            "from": from_,
            "query": query,
            "sort": [{"created_at": {"order": "desc"}}],
        },
    )
    issues = [MaintenanceIssue(id=h["_id"], **h["_source"]) for h in result["hits"]["hits"]]
    return MaintenanceIssueSearchResponse(
        total=result["hits"]["total"]["value"], issues=issues
    )


@router.get("/{issue_id}", response_model=MaintenanceIssue)
async def get_issue(issue_id: str, es: AsyncElasticsearch = Depends(get_es)):
    try:
        r = await es.get(index=settings.maintenance_issues_index, id=issue_id)
        return MaintenanceIssue(id=r["_id"], **r["_source"])
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Maintenance issue not found")


@router.delete("/{issue_id}")
async def delete_issue(issue_id: str, es: AsyncElasticsearch = Depends(get_es)):
    try:
        await es.delete(
            index=settings.maintenance_issues_index, id=issue_id, refresh=True
        )
        return {"deleted": issue_id}
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Maintenance issue not found")
