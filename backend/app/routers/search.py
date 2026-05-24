from fastapi import APIRouter, Depends
from elasticsearch import AsyncElasticsearch

from ..es_client import get_es
from ..config import settings
from ..models import Document, SearchResponse

router = APIRouter()


@router.get("/", response_model=SearchResponse)
async def search_documents(
    filters: str = "",      # comma-separated AND tag paths
    exclude: str = "",      # comma-separated NOT tag paths
    q: str = "",            # free-text (supports -term for NOT)
    size: int = 50,
    from_: int = 0,
    es: AsyncElasticsearch = Depends(get_es),
):
    filter_list = [f.strip() for f in filters.split(",") if f.strip()]
    exclude_list = [f.strip() for f in exclude.split(",") if f.strip()]

    must: list = []
    must_not: list = []

    # Hierarchical AND filters: term query on the path_hierarchy-analyzed field
    # so "type/face" will match docs tagged with "type/face/emotion/positive" etc.
    for tag in filter_list:
        must.append({"term": {"tags.hierarchy": tag}})

    # Hierarchical NOT filters
    for tag in exclude_list:
        must_not.append({"term": {"tags.hierarchy": tag}})

    # Free-text with optional -term exclusion syntax
    if q.strip():
        terms = q.strip().split()
        include_terms = [t for t in terms if not t.startswith("-")]
        exclude_terms = [t[1:] for t in terms if t.startswith("-") and len(t) > 1]

        if include_terms:
            must.append({
                "multi_match": {
                    "query": " ".join(include_terms),
                    "fields": ["name^3", "description", "tags"],
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                }
            })

        for excl in exclude_terms:
            must_not.append({
                "multi_match": {
                    "query": excl,
                    "fields": ["name", "tags"],
                }
            })

    if not must and not must_not:
        query = {"match_all": {}}
    else:
        bool_q: dict = {}
        if must:
            bool_q["must"] = must
        if must_not:
            bool_q["must_not"] = must_not
        query = {"bool": bool_q}

    result = await es.search(
        index=settings.documents_index,
        body={
            "size": size,
            "from": from_,
            "query": query,
            "sort": [{"_score": "desc"}, {"created_at": "desc"}],
        },
    )

    docs = [Document(id=h["_id"], **h["_source"]) for h in result["hits"]["hits"]]
    return SearchResponse(total=result["hits"]["total"]["value"], documents=docs)
