from fastapi import APIRouter, Depends
from elasticsearch import AsyncElasticsearch

from ..es_client import get_es
from ..config import settings
from ..models import Document, SearchResponse

router = APIRouter()


@router.get("/", response_model=SearchResponse)
async def search_documents(
    filters: str = "",      # comma-separated AND tag paths
    or_filters: str = "",   # comma-separated OR tag paths (must match at least one)
    exclude: str = "",      # comma-separated NOT tag paths
    q: str = "",            # free-text
    size: int = 50,
    from_: int = 0,
    es: AsyncElasticsearch = Depends(get_es),
):
    filter_list = [f.strip() for f in filters.split(",") if f.strip()]
    or_list = [f.strip() for f in or_filters.split(",") if f.strip()]
    exclude_list = [f.strip() for f in exclude.split(",") if f.strip()]

    must: list = []
    should: list = []
    must_not: list = []

    for tag in filter_list:
        must.append({"prefix": {"tags": tag}})

    for tag in or_list:
        should.append({"prefix": {"tags": tag}})

    for tag in exclude_list:
        must_not.append({"prefix": {"tags": tag}})

    if q.strip():
        terms = q.strip().split()
        include_terms = [t for t in terms if not t.startswith("-")]
        exclude_terms = [t[1:] for t in terms if t.startswith("-") and len(t) > 1]

        if include_terms:
            query_text = " ".join(include_terms)
            # english analyzer stems name/description at index time, so fuzzy multi_match
            # handles "party" → "partying" etc. Tag wildcards catch substring matches on
            # keyword paths (e.g. "face" inside "type/face/emotion/positive").
            text_should: list = [
                {
                    "multi_match": {
                        "query": query_text,
                        "fields": ["name^3", "description"],
                        "fuzziness": "AUTO",
                    }
                }
            ]
            for term in include_terms:
                text_should.append({
                    "match": {"tags.segments": {"query": term}}
                })
            must.append({"bool": {"should": text_should, "minimum_should_match": 1}})

        for excl in exclude_terms:
            must_not.append({
                "multi_match": {
                    "query": excl,
                    "fields": ["name", "description"],
                }
            })
            must_not.append({
                "match": {"tags.segments": {"query": excl}}
            })

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
