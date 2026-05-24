DOCUMENTS_MAPPING = {
    "settings": {
        "analysis": {
            "tokenizer": {
                "path_hierarchy_tokenizer": {
                    "type": "path_hierarchy",
                    "delimiter": "/"
                },
                "reverse_path_tokenizer": {
                    "type": "path_hierarchy",
                    "delimiter": "/",
                    "reverse": True
                }
            },
            "analyzer": {
                "path_hierarchy_analyzer": {
                    "type": "custom",
                    "tokenizer": "path_hierarchy_tokenizer"
                },
                "reverse_path_analyzer": {
                    "type": "custom",
                    "tokenizer": "reverse_path_tokenizer"
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "name": {
                "type": "text",
                "analyzer": "english",
                "fields": {"keyword": {"type": "keyword"}}
            },
            "description": {
                "type": "text",
                "analyzer": "english"
            },
            "icon": {"type": "keyword"},
            "tags": {
                "type": "keyword",
                "fields": {
                    "hierarchy": {
                        "type": "text",
                        "analyzer": "path_hierarchy_analyzer"
                    },
                    "reverse_hierarchy": {
                        "type": "text",
                        "analyzer": "reverse_path_analyzer"
                    }
                }
            },
            "created_at": {"type": "date"},
            "metadata": {"type": "object", "dynamic": True}
        }
    }
}

TAXONOMY_MAPPING = {
    "mappings": {
        "properties": {
            "path": {"type": "keyword"},
            "label": {
                "type": "text",
                "fields": {"keyword": {"type": "keyword"}}
            },
            "parent_path": {"type": "keyword"},
            "depth": {"type": "integer"},
            "synonyms": {"type": "keyword"},
            "description": {"type": "text"}
        }
    }
}
