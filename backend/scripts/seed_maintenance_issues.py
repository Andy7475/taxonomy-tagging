"""Demo maintenance issues for the facility-locations feature.

Deliberately spans the interesting cases the location ontology demonstrates:
a leaf-level Zone, a coarse Building-level selection (paint the whole
building, not one room), a Site-level selection, and an issue filed against
the contractor's own Plant Room identifier (simulating an imported
contractor record) to exercise the owl:sameAs cross-system reconciliation.

Requires the location ontology to already be ingested (POST
/api/locations/ingest) — an issue whose location_uri isn't found in the
locations index is skipped, not created with bad data.
"""

DEMO_ISSUES = [
    {
        "id": "demo-issue-1",
        "title": "Leaking tap",
        "description": "Slow drip under the sink in the storage bay.",
        "priority": "low",
        "location_uri": "https://example.org/facility/SiteBlue/Annex/GroundFloor/ZoneA",
    },
    {
        "id": "demo-issue-2",
        "title": "Flickering light",
        "description": "Overhead light flickers intermittently near the east windows.",
        "priority": "medium",
        "location_uri": "https://example.org/facility/SiteOrange/MainBuilding/Storey2/ZoneA",
    },
    {
        "id": "demo-issue-3",
        "title": "Repaint reception walls",
        "description": "Scuffed walls throughout — a building-wide job, not a specific room.",
        "priority": "low",
        "location_uri": "https://example.org/facility/SiteOrange/MainBuilding",
    },
    {
        "id": "demo-issue-4",
        "title": "HVAC service due",
        "description": "Routine service reported by the maintenance contractor.",
        "priority": "medium",
        "location_uri": "https://example.org/facility/SiteOrange/MainBuilding/Storey1/PlantRoom",
    },
    {
        "id": "demo-issue-5",
        "title": "Site walkthrough — minor wear noted",
        "description": "General condition survey, no specific room.",
        "priority": "low",
        "location_uri": "https://example.org/facility/SiteOrange",
    },
]
