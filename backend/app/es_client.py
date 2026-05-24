from elasticsearch import AsyncElasticsearch
from .config import settings

_es: AsyncElasticsearch | None = None

def get_es() -> AsyncElasticsearch:
    return _es

async def connect() -> AsyncElasticsearch:
    global _es
    _es = AsyncElasticsearch([settings.elasticsearch_url])
    return _es

async def disconnect():
    global _es
    if _es:
        await _es.close()
        _es = None
