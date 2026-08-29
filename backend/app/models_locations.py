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


class GeoFeature(BaseModel):
    uri: str
    geometry_type: str  # "Point" or "Polygon"
    lat: Optional[float] = None
    lon: Optional[float] = None
    polygon: Optional[list[list[float]]] = None  # [[lat, lon], ...] ring, Polygon only


class MapLocation(GeoFeature):
    label: str
    path: str
    facility_type: str


class FloorplanZone(BaseModel):
    uri: str
    label: str
    points: list[list[float]]


class FloorplanResponse(BaseModel):
    width: float
    height: float
    zones: list[FloorplanZone]


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


class MaintenanceIssueSearchResponse(BaseModel):
    total: int
    issues: list[MaintenanceIssue]
