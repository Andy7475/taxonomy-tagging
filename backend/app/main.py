from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .es_client import connect, disconnect, get_es
from . import graph_store
from .indices import (
    DOCUMENTS_MAPPING,
    TAXONOMY_MAPPING,
    LOCATIONS_MAPPING,
    MAINTENANCE_ISSUES_MAPPING,
)
from .routers import taxonomy, documents, search, seed, locations, maintenance_issues, geo


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = await connect()

    for index, mapping in [
        (settings.documents_index, DOCUMENTS_MAPPING),
        (settings.taxonomy_index, TAXONOMY_MAPPING),
        (settings.locations_index, LOCATIONS_MAPPING),
        (settings.maintenance_issues_index, MAINTENANCE_ISSUES_MAPPING),
    ]:
        if not await client.indices.exists(index=index):
            await client.indices.create(index=index, body=mapping)

    graph_store.load_graph()

    yield

    await disconnect()


app = FastAPI(
    title="Taxonomy Tagging API",
    description="Hierarchical tagging and search with Elasticsearch",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(taxonomy.router, prefix="/api/taxonomy", tags=["taxonomy"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(seed.router, prefix="/api", tags=["seed"])
app.include_router(locations.router, prefix="/api/locations", tags=["locations"])
app.include_router(
    maintenance_issues.router,
    prefix="/api/maintenance-issues",
    tags=["maintenance-issues"],
)
app.include_router(geo.router, prefix="/api/geo", tags=["geo"])


@app.get("/api/health")
async def health():
    es = get_es()
    info = await es.info()
    return {"status": "ok", "elasticsearch": info["version"]["number"]}
