from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Location(BaseModel):
    uri: str
    source_uri: str
    path: str
    label: str
    facility_type: str
    depth: int
    synonyms: list[str] = []
    description: Optional[str] = None


class LocationSuggestion(BaseModel):
    uri: str
    path: str
    label: str
    facility_type: str
    depth: int
    matched_via: str  # "synonym", "label", "path", or "issue"


class MaintenanceIssue(BaseModel):
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    status: str = "open"
    priority: str = "medium"
    location_uri: str
    location_path: Optional[list[str]] = None
    created_at: Optional[datetime] = None


class MaintenanceIssueCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "open"
    priority: str = "medium"
    location_uri: str
