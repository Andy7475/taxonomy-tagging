import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from elasticsearch import AsyncElasticsearch, NotFoundError

from ..es_client import get_es
from ..config import settings
from ..models_locations import MaintenanceIssue, MaintenanceIssueCreate

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


@router.get("/", response_model=list[MaintenanceIssue])
async def list_issues(
    under: str = "",
    size: int = 50,
    from_: int = 0,
    es: AsyncElasticsearch = Depends(get_es),
):
    query: dict = {"match_all": {}}

    under = under.strip()
    if under:
        if under.startswith("http://") or under.startswith("https://"):
            _, prefixes = await _resolve_paths(under, es)
            if not prefixes:
                return []
            # Match if the issue's location falls under ANY of the target's
            # known paths — needed once a facility can have more than one
            # valid ancestry (sameAs-linked owner/contractor hierarchies).
            query = {
                "bool": {
                    "should": [{"prefix": {"location_path": p}} for p in prefixes],
                    "minimum_should_match": 1,
                }
            }
        else:
            query = {"prefix": {"location_path": under}}

    result = await es.search(
        index=settings.maintenance_issues_index,
        body={
            "size": size,
            "from": from_,
            "query": query,
            "sort": [{"created_at": {"order": "desc"}}],
        },
    )
    return [MaintenanceIssue(id=h["_id"], **h["_source"]) for h in result["hits"]["hits"]]


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
