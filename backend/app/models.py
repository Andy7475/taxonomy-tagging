from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime


class TaxonomyNode(BaseModel):
    path: str
    label: str
    depth: int = 0
    synonyms: list[str] = []
    description: Optional[str] = None


class TaxonomyNodeCreate(BaseModel):
    path: str
    label: str
    synonyms: list[str] = []
    description: Optional[str] = None


class Document(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    tags: list[str] = []
    created_at: Optional[datetime] = None
    metadata: Optional[dict[str, Any]] = None


class DocumentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    tags: list[str] = []
    metadata: Optional[dict[str, Any]] = None


class TagSuggestion(BaseModel):
    path: str
    label: str
    depth: int
    matched_via: str  # "path", "label", or "synonym"


class SearchResponse(BaseModel):
    total: int
    documents: list[Document]
