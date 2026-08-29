# About the Facility Locations Demo

This is a second demo living alongside the emoji tagging system (see [about-the-tagging-system.md](about-the-tagging-system.md)), built on the same core idea — a slash-delimited `path` indexed as a prefix-queryable Elasticsearch field, with an autocomplete that disambiguates same-named items by showing their ancestor path. The difference here is where the hierarchy comes from: instead of hand-authored taxonomy nodes, it's derived from a small RDF ontology and instance graph.

## The ontology

- [ontology/facility.ttl](ontology/facility.ttl) — the TBox: `Site`, `Building`, `Storey`, `Zone` as subclasses of a `Facility` class, and an `isPartOf` object property connecting them. Naming is inspired by IES (the UK "Information Exchange Standard" family) but is a small, self-contained, local ontology — not an import of real IES4, which models containment with much heavier reified/time-bounded relationships.
- [ontology/facility_instances.ttl](ontology/facility_instances.ttl) — the ABox: a sample dataset of two sites, buildings, storeys, and zones, with `rdfs:label`, `rdfs:comment`, and `skos:altLabel` (synonyms) on instances.

## Build-time flattening, not a live triple store

`backend/scripts/ingest_locations.py` parses both TTL files with `rdflib` and writes Elasticsearch documents into the `facility_locations` index — once, at ingest time (via `POST /api/locations/ingest` or `python -m scripts.ingest_locations`). There is no live SPARQL endpoint or triple store running in this app; every runtime query (autocomplete, "everything under Site Orange") runs against Elasticsearch using the same `prefix`-on-`path` technique the taxonomy index already uses.

This is a deliberate tradeoff, not an oversight:

- **Query expressiveness.** Tree-scoped containment queries are trivial with `prefix` matching on a flattened path — no SPARQL needed. What a flattened path *can't* express is anything relational or cross-cutting beyond the containment chains baked in at ingest time (e.g. "zones on a shared emergency-exit route spanning two buildings"). That needs real graph traversal over a different relation, evaluated at query time against the actual graph.
- **Operational simplicity.** Build-time-only means no triple store service, client library, or extra ops surface — this demo reuses the Elasticsearch/Kibana stack the rest of the app already runs.
- **Kibana's role.** Kibana is useful for exploring the *derived* `facility_locations` index (Discover/Lens over `label`, `synonyms`, `path`, `facility_type`) — good for sanity-checking ingestion output. It is not a graph/ontology browser; it has no notion of `isPartOf` edges or SPARQL. That role would fall to inspecting the TTL directly, or a dedicated triple-store UI, if a genuinely relational query need ever showed up.

The ontology remains the source of truth and can be re-ingested any time the physical structure changes.

## `uri` vs `path`

Every indexed location document has two distinct fields:

- **`uri`** — the facility's stable RDF identifier (e.g. `https://example.org/facility/SiteOrange/MainBuilding/Storey2/ZoneA`). This is the value a maintenance issue actually stores back (`location_uri`) — it is what identifies *which physical place* was selected.
- **`path`** — a derived, slash-joined display string built from the ancestor chain's URI local names, used purely for the prefix-query hierarchy UX and disambiguation rendering. It is never the value written back to a record.

## One facility, more than one path

A facility can have more than one `isPartOf` parent — for example, a room known via a building owner's Site/Building/Storey hierarchy *and* via a maintenance sub-contractor's separate site-coding hierarchy (see the `Plant Room` example in `facility_instances.ttl`, which has two `isPartOf` triples). Rather than picking one "correct" parent, the ingestion script enumerates **every** valid root-to-instance chain and indexes one Elasticsearch document per `(uri, path)` pair, all sharing the same `uri`.

This means the location `suggest` endpoint deliberately does *not* deduplicate by `uri`: typing "Plant Room" returns two suggestion rows with different ancestor paths but the same underlying `uri`. The user picks whichever hierarchy frame of reference they recognize; both choices write back the identical value. This is the opposite situation from two *different* zones that happen to share a label (e.g. two "Zone A"s under different storeys) — those have distinct `uri`s and are genuinely different places. The demo's sample data includes both cases side by side so they can be told apart.
