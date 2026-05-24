import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends
from elasticsearch import AsyncElasticsearch, NotFoundError

from ..es_client import get_es
from ..config import settings
from ..models import Document, DocumentCreate

router = APIRouter()


@router.post("/", response_model=Document, status_code=201)
async def create_document(
    doc: DocumentCreate, es: AsyncElasticsearch = Depends(get_es)
):
    doc_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    body = {**doc.model_dump(), "created_at": now}

    await es.index(
        index=settings.documents_index, id=doc_id, document=body, refresh=True
    )
    return Document(id=doc_id, **body)


@router.get("/", response_model=list[Document])
async def list_documents(
    size: int = 50, from_: int = 0, es: AsyncElasticsearch = Depends(get_es)
):
    result = await es.search(
        index=settings.documents_index,
        body={
            "size": size,
            "from": from_,
            "query": {"match_all": {}},
            "sort": [{"created_at": {"order": "desc"}}],
        },
    )
    return [Document(id=h["_id"], **h["_source"]) for h in result["hits"]["hits"]]


@router.get("/{doc_id}", response_model=Document)
async def get_document(doc_id: str, es: AsyncElasticsearch = Depends(get_es)):
    try:
        r = await es.get(index=settings.documents_index, id=doc_id)
        return Document(id=r["_id"], **r["_source"])
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")


@router.put("/{doc_id}", response_model=Document)
async def update_document(
    doc_id: str, doc: DocumentCreate, es: AsyncElasticsearch = Depends(get_es)
):
    try:
        await es.update(
            index=settings.documents_index,
            id=doc_id,
            doc=doc.model_dump(),
            refresh=True,
        )
        r = await es.get(index=settings.documents_index, id=doc_id)
        return Document(id=r["_id"], **r["_source"])
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")


@router.delete("/{doc_id}")
async def delete_document(doc_id: str, es: AsyncElasticsearch = Depends(get_es)):
    try:
        await es.delete(index=settings.documents_index, id=doc_id, refresh=True)
        return {"deleted": doc_id}
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")
