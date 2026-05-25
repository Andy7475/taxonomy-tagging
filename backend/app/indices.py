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
