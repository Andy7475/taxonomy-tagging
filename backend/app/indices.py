_PATH_ANALYSIS = {
    "tokenizer": {
        "path_segment_tokenizer": {"type": "pattern", "pattern": "/"}
    },
    "analyzer": {
        "path_segment_analyzer": {
            "type": "custom",
            "tokenizer": "path_segment_tokenizer",
            "filter": ["lowercase"],
        }
    },
}

_PATH_FIELD = {
    "type": "keyword",
    "fields": {
        "segments": {"type": "text", "analyzer": "path_segment_analyzer"}
    },
}

DOCUMENTS_MAPPING = {
    "settings": {"analysis": _PATH_ANALYSIS},
    "mappings": {
        "properties": {
            "name": {
                "type": "text",
                "analyzer": "english",
                "fields": {"keyword": {"type": "keyword"}},
            },
            "description": {"type": "text", "analyzer": "english"},
            "icon": {"type": "keyword"},
            "tags": _PATH_FIELD,
            "created_at": {"type": "date"},
            "metadata": {"type": "object", "dynamic": True},
        }
    },
}

TAXONOMY_MAPPING = {
    "settings": {"analysis": _PATH_ANALYSIS},
    "mappings": {
        "properties": {
            "path": _PATH_FIELD,
            "label": {
                "type": "text",
                "analyzer": "english",
                "fields": {"keyword": {"type": "keyword"}},
            },
            "depth": {"type": "integer"},
            "synonyms": {
                "type": "text",
                "analyzer": "english",
                "fields": {"keyword": {"type": "keyword"}},
            },
            "description": {"type": "text", "analyzer": "english"},
        }
    },
}

# One document per (uri, path) pair — a facility reachable via more than one
# isPartOf chain (see ontology/facility_instances.ttl's Plant Room example)
# is indexed as multiple documents sharing the same `uri`. `uri` is
# therefore NOT the document _id (see backend/scripts/ingest_locations.py).
LOCATIONS_MAPPING = {
    "settings": {"analysis": _PATH_ANALYSIS},
    "mappings": {
        "properties": {
            "uri": {"type": "keyword"},
            "source_uri": {"type": "keyword"},
            "path": _PATH_FIELD,
            "label": {
                "type": "text",
                "analyzer": "english",
                "fields": {"keyword": {"type": "keyword"}},
            },
            "facility_type": {"type": "keyword"},
            "depth": {"type": "integer"},
            "synonyms": {
                "type": "text",
                "analyzer": "english",
                "fields": {"keyword": {"type": "keyword"}},
            },
            "description": {"type": "text", "analyzer": "english"},
        }
    },
}

MAINTENANCE_ISSUES_MAPPING = {
    "settings": {"analysis": _PATH_ANALYSIS},
    "mappings": {
        "properties": {
            "title": {
                "type": "text",
                "analyzer": "english",
                "fields": {"keyword": {"type": "keyword"}},
            },
            "description": {"type": "text", "analyzer": "english"},
            "status": {"type": "keyword"},
            "priority": {"type": "keyword"},
            "location_uri": {"type": "keyword"},
            "location_path": _PATH_FIELD,
            "created_at": {"type": "date"},
        }
    },
}
