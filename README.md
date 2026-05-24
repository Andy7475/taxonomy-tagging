# Taxonomy Tagging — Production Demo

Hierarchical tagging and semantic search using **Elasticsearch**, **FastAPI**, and **React**. Based on the emoji discovery demo, but backed by a real search engine.

## Key features

| Feature | How it works |
|---|---|
| **Hierarchical tags** | `path_hierarchy` tokenizer: tagging `type/face/emotion/positive` auto-indexes all ancestor paths, so filtering on `type/face` matches everything underneath |
| **AND composition** | Each filter chip adds a `term` query on `tags.hierarchy` — all must match |
| **Exclusion (`-term`)** | Type `-red` in the search box → `must_not` clause in the ES bool query |
| **Synonym resolution** | Each taxonomy node stores synonyms (e.g. `smile → type/face/emotion/positive`). Autocomplete resolves them and shows _how_ the match was found (synonym / label / path) |
| **Prefix + contains search** | Autocomplete queries ES with `prefix`, `wildcard`, `match` (fuzzy) and `term` (exact synonym) — all in one `should` clause |
| **Reverse path hierarchy** | Tags also indexed with `reverse: true` so leaf-level terms match without knowing the full path |

---

## Prerequisites

- **Docker Desktop** (includes Docker Engine + Compose)
  - Mac/Windows: https://www.docker.com/products/docker-desktop/
  - Linux: install Docker Engine + the Compose plugin

Minimum resources: 2 GB RAM free for Elasticsearch.

---

## Setup (step by step)

### 1. Install Docker Desktop

Download and install Docker Desktop for your platform. On Windows, WSL 2 backend is recommended (Docker Desktop will prompt you). After install, start Docker Desktop and wait for the whale icon in the taskbar.

Verify it works:
```bash
docker --version
docker compose version
```

### 2. Clone the repository

```bash
git clone https://github.com/andy7475/taxonomy-tagging.git
cd taxonomy-tagging
```

### 3. Start the stack

```bash
docker compose up --build
```

This starts three containers:
- `taxonomy_es` — Elasticsearch 8.13 on port 9200
- `taxonomy_api` — FastAPI on port 8000
- `taxonomy_frontend` — Nginx serving the React app on port 3000

First run takes a few minutes (image pulls + frontend build). Elasticsearch is the slowest to start — the API container waits for it via a health check.

You'll know it's ready when you see:
```
taxonomy_api  | INFO:     Application startup complete.
```

### 4. Open the app

Visit **http://localhost:3000**

Click **"Seed Demo Data"** in the top right to load 50 emoji documents and 27 taxonomy nodes.

### 5. Explore

- **Filter bar**: click the `+` input and type a trait (e.g. `smile`, `red`, `music`, `sparkl`). Watch synonym resolution — `smile` resolves to `type/face/emotion/positive`.
- **AND logic**: add multiple filter chips — results must match all of them.
- **Exclusion**: type `-yellow` in the search box to hide yellow items.
- **Hierarchy traversal**: filter on `type/face` to see all face-category items across all emotion depths.
- **Add your own**: use the left panel form to index a new item with any combination of tags.

---

## API reference

Interactive docs at **http://localhost:8000/docs** once the stack is running.

### Key endpoints

```
GET  /api/health                     # Check ES connection
POST /api/seed                       # Load demo data (50 emojis + taxonomy)

GET  /api/taxonomy/suggest?q=smile   # Tag autocomplete (synonym-aware)
GET  /api/taxonomy/tree              # Full taxonomy hierarchy
POST /api/taxonomy/                  # Add a taxonomy node

GET  /api/search/?filters=type/face,visual/color/red&q=emotion
                                     # Search with AND filters + text query

POST /api/documents/                 # Index a new document
GET  /api/documents/                 # List all documents
PUT  /api/documents/{id}             # Update a document
DELETE /api/documents/{id}           # Delete a document
```

### Suggest API response

```json
[
  {
    "path": "type/face/emotion/positive",
    "label": "Positive Emotion",
    "depth": 3,
    "matched_via": "synonym"   // "synonym" | "label" | "path"
  }
]
```

### Search query params

| Param | Example | Effect |
|---|---|---|
| `filters` | `type/face,visual/color/red` | AND — docs must match all (hierarchical) |
| `exclude` | `visual/color/yellow` | NOT — docs matching this are excluded |
| `q` | `emotion -sparkly` | Full-text; prefix `-` on a word excludes it |

---

## Elasticsearch internals

### Index: `taxonomy_paths`

Stores every node in the tag hierarchy. Key fields:
- `path` (keyword) — unique ID and exact path, e.g. `type/face/emotion/positive`
- `label` (text) — human-readable name for fuzzy autocomplete
- `synonyms` (keyword) — list of synonyms for exact term matching
- `depth` (integer) — 0-based depth for ordering suggestions

### Index: `taxonomy_documents`

Stores tagged items. The `tags` field uses layered analysis:

```json
"tags": {
  "type": "keyword",           // exact stored path
  "fields": {
    "hierarchy": {             // path_hierarchy tokenizer — indexes all ancestors
      "type": "text",
      "analyzer": "path_hierarchy_analyzer"
    },
    "reverse_hierarchy": {     // reverse path_hierarchy — find by leaf segment
      "type": "text",
      "analyzer": "reverse_path_analyzer"
    }
  }
}
```

Filtering on `tags.hierarchy: "type/face"` matches documents tagged with:
`type/face`, `type/face/emotion`, `type/face/emotion/positive`, `type/face/emotion/negative`, etc.

---

## Development

### Run backend locally (without Docker)

```bash
# Start just Elasticsearch
docker compose up elasticsearch -d

cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# API available at http://localhost:8000
```

### Run frontend locally (without Docker)

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173 — proxies /api to localhost:8000
```

### Seed from CLI

```bash
docker compose exec api python -m scripts.seed
# or point at a remote ES:
docker compose exec api python -m scripts.seed http://my-es-host:9200
```

### Add taxonomy nodes via API

```bash
curl -X POST http://localhost:8000/api/taxonomy/ \
  -H 'Content-Type: application/json' \
  -d '{
    "path": "type/animal/mammal/dog",
    "label": "Dog",
    "synonyms": ["canine", "puppy", "hound", "woof"]
  }'
```

Parent paths (`type`, `type/animal`, `type/animal/mammal`) are created automatically.

---

## Resetting all data

```bash
docker compose down -v   # -v removes the Elasticsearch data volume
docker compose up
```

Then click "Seed Demo Data" again.

---

## Architecture

```
Browser (port 3000)
    │
    ├─ /          → Nginx → React SPA (dist/)
    └─ /api/*     → Nginx proxy → FastAPI (port 8000)
                                      │
                                      └─ Elasticsearch (port 9200)
                                         ├─ taxonomy_paths index
                                         └─ taxonomy_documents index
```
