import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from elasticsearch import AsyncElasticsearch

from ..es_client import get_es
from ..config import settings

router = APIRouter()

try:
    from scripts.seed import TAXONOMY_NODES, DOCUMENTS
except ImportError:
    TAXONOMY_NODES = []
    DOCUMENTS = []


async def _ensure_parents(path: str, es: AsyncElasticsearch):
    segments = path.split("/")
    for i in range(1, len(segments)):
        parent = "/".join(segments[:i])
        if not await es.exists(index=settings.taxonomy_index, id=parent):
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


@router.post("/seed")
async def seed_demo_data(es: AsyncElasticsearch = Depends(get_es)):
    """Seed taxonomy nodes and emoji documents for the demo."""
    now = datetime.now(timezone.utc).isoformat()

    for node in TAXONOMY_NODES:
        segments = node["path"].split("/")
        depth = len(segments) - 1
        await es.index(
            index=settings.taxonomy_index,
            id=node["path"],
            document={
                "path": node["path"],
                "label": node["label"],
                "depth": depth,
                "synonyms": [s.lower() for s in node["synonyms"]],
                "description": None,
            },
        )
        await _ensure_parents(node["path"], es)

    await es.indices.refresh(index=settings.taxonomy_index)

    for doc in DOCUMENTS:
        await es.index(
            index=settings.documents_index,
            id=str(uuid.uuid4()),
            document={**doc, "description": None, "metadata": None, "created_at": now},
        )

    await es.indices.refresh(index=settings.documents_index)

    return {
        "status": "ok",
        "taxonomy_nodes": len(TAXONOMY_NODES),
        "documents": len(DOCUMENTS),
    }
