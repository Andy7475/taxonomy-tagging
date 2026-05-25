from fastapi import APIRouter, HTTPException, Depends
from elasticsearch import AsyncElasticsearch, NotFoundError

from ..es_client import get_es
from ..config import settings
from ..models import TaxonomyNode, TaxonomyNodeCreate, TagSuggestion

router = APIRouter()


async def _ensure_parent_paths(path: str, es: AsyncElasticsearch):
    """Ensure all ancestor path nodes exist in the taxonomy index."""
    segments = path.split("/")
    for i in range(1, len(segments)):
        parent = "/".join(segments[:i])
        exists = await es.exists(index=settings.taxonomy_index, id=parent)
        if not exists:
            await es.index(
                index=settings.taxonomy_index,
                id=parent,
                document={
                    "path": parent,
                    "label": segments[i - 1].replace("_", " ").title(),
                    "depth": i - 1,
                    "synonyms": [],
                    "description": None,
                },
            )


@router.post("/", response_model=TaxonomyNode, status_code=201)
async def create_taxonomy_node(
    node: TaxonomyNodeCreate, es: AsyncElasticsearch = Depends(get_es)
):
    segments = node.path.split("/")
    depth = len(segments) - 1

    doc = {
        "path": node.path,
        "label": node.label,
        "depth": depth,
        "synonyms": [s.lower() for s in node.synonyms],
        "description": node.description,
    }

    await es.index(index=settings.taxonomy_index, id=node.path, document=doc, refresh=True)
    await _ensure_parent_paths(node.path, es)

    return TaxonomyNode(**doc)


@router.get("/suggest", response_model=list[TagSuggestion])
async def suggest_tags(
    q: str = "",
    exclude: str = "",
    limit: int = 10,
    es: AsyncElasticsearch = Depends(get_es),
):
    if not q.strip():
        return []

    exclude_list = [e.strip() for e in exclude.split(",") if e.strip()]
    q_lower = q.lower()

    result = await es.search(
        index=settings.taxonomy_index,
        body={
            "size": min(limit * 4, 200),
            "query": {
                "bool": {
                    "should": [
                        {"term": {"synonyms.keyword": q_lower}},
                        {"match": {"synonyms": {"query": q, "boost": 2}}},
                        {"match": {"label": {"query": q, "fuzziness": "AUTO", "boost": 3}}},
                        {"match": {"path.segments": {"query": q}}},
                    ],
                    "minimum_should_match": 1,
                }
            },
            "sort": ["_score", {"depth": "asc"}],
        },
    )

    suggestions: list[TagSuggestion] = []
    seen: set[str] = set()

    for hit in result["hits"]["hits"]:
        src = hit["_source"]
        path = src["path"]

        if path in exclude_list or path in seen:
            continue
        seen.add(path)

        syns = [s.lower() for s in src.get("synonyms", [])]
        if q_lower in syns or any(s.startswith(q_lower) for s in syns):
            matched_via = "synonym"
        elif q_lower in src.get("label", "").lower():
            matched_via = "label"
        else:
            matched_via = "path"

        suggestions.append(
            TagSuggestion(
                path=path,
                label=src["label"],
                depth=src["depth"],
                matched_via=matched_via,
            )
        )

        if len(suggestions) >= limit:
            break

    return suggestions


@router.get("/tree")
async def get_taxonomy_tree(es: AsyncElasticsearch = Depends(get_es)):
    result = await es.search(
        index=settings.taxonomy_index,
        body={
            "size": 1000,
            "query": {"match_all": {}},
            "sort": [{"depth": "asc"}, {"path": "asc"}],
        },
    )
    return [hit["_source"] for hit in result["hits"]["hits"]]


@router.get("/{path:path}", response_model=TaxonomyNode)
async def get_taxonomy_node(path: str, es: AsyncElasticsearch = Depends(get_es)):
    try:
        result = await es.get(index=settings.taxonomy_index, id=path)
        return TaxonomyNode(**result["_source"])
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Path '{path}' not found")


@router.delete("/{path:path}")
async def delete_taxonomy_node(path: str, es: AsyncElasticsearch = Depends(get_es)):
    try:
        await es.delete(index=settings.taxonomy_index, id=path, refresh=True)
        return {"deleted": path}
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Path '{path}' not found")
