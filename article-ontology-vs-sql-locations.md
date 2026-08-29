# One Location, Many Names: Why We Stopped Modeling Buildings as Foreign Keys

*A follow-up to [How to Tag & Find Anything in a Database](https://www.linkedin.com/pulse/how-tag-find-anything-database-andrew-laing-vfcue/) — this time applying the same taxonomy-tagging philosophy to a problem every facilities/maintenance system eventually hits: how do you let someone log an issue against "a place" without forcing them to understand your database schema, and without your data going stale every time the portfolio changes?*

---

## The problem, concretely

You're building a maintenance-issue tracker. Every issue needs a location. Your facilities have a natural hierarchy — Site, Building, Storey, Zone — and any given issue might be reported at any level of it: "the boiler in Plant Room 2" is precise; "the walls need painting" is a whole-building concern; "general wear across the site" doesn't need a room at all.

Two requirements collide immediately:

1. **The UI should be one field, not four.** Nobody wants to fill in a Site dropdown, then wait for a Building dropdown to populate, then a Storey dropdown, then a Zone dropdown, just to log a light bulb.
2. **The data model should let you restructure the portfolio without rewriting history.** A new wing gets built, a floor gets renumbered, a contractor starts using their own site codes — none of that should require touching every existing maintenance record that happens to reference the affected area.

This article walks through how you'd solve this in a conventional relational schema, where the friction actually shows up, and then how a small RDF ontology — flattened into Elasticsearch, not queried live via SPARQL — solves the same problem with a meaningfully different cost profile. Every schema and code snippet below is real, taken from a working demo, not a sketch.

---

## Part 1: The SQL approach

### 1a. The tempting shortcut: flat columns

The fastest thing to ship is columns directly on the issue table:

```sql
CREATE TABLE maintenance_issues (
    id          SERIAL PRIMARY KEY,
    title       TEXT NOT NULL,
    site        TEXT,
    building    TEXT,
    storey      TEXT,
    zone        TEXT,
    created_at  TIMESTAMPTZ DEFAULT now()
);
```

This works for approximately one demo. There's no referential integrity — `'Site Orange'`, `'site orange'`, and `'Site-Orange'` are three different strings as far as the database is concerned. There's no way to express that Storey 1 belongs to Main Building; the "hierarchy" exists only in the four column names, not as data. Querying "everything at Site Orange" is a brittle `WHERE site = 'Site Orange'`, and it silently misses every future typo.

Nobody who's shipped a real system stays here long. So:

### 1b. The proper normalized version

A single, generic `locations` table, self-referencing, so an issue can point at *any* level with one foreign key:

```sql
CREATE TABLE locations (
    id         SERIAL PRIMARY KEY,
    label      TEXT NOT NULL,
    type       TEXT NOT NULL CHECK (type IN ('site','building','storey','zone')),
    parent_id  INTEGER REFERENCES locations(id)
);

CREATE TABLE maintenance_issues (
    id           SERIAL PRIMARY KEY,
    title        TEXT NOT NULL,
    location_id  INTEGER NOT NULL REFERENCES locations(id),
    created_at   TIMESTAMPTZ DEFAULT now()
);
```

```sql
INSERT INTO locations (id, label, type, parent_id) VALUES
  (1, 'Site Orange',   'site',     NULL),
  (2, 'Main Building',  'building', 1),
  (3, 'Storey 1',       'storey',   2),
  (4, 'Zone A',         'zone',     3);
```

Credit where due — this is a reasonable design, and it handles the core containment case well. "Everything under Site Orange" is a recursive CTE:

```sql
WITH RECURSIVE descendants AS (
    SELECT id FROM locations WHERE id = 1          -- Site Orange
    UNION ALL
    SELECT l.id FROM locations l
    JOIN descendants d ON l.parent_id = d.id
)
SELECT mi.* FROM maintenance_issues mi
JOIN descendants d ON mi.location_id = d.id;
```

Adding a brand-new leaf under an existing branch is trivial and doesn't touch any existing issue: one `INSERT`. Adding a synonym ("HQ" for Main Building) is trivial too, with a small child table:

```sql
CREATE TABLE location_synonyms (
    location_id  INTEGER REFERENCES locations(id),
    synonym      TEXT NOT NULL
);
INSERT INTO location_synonyms VALUES (2, 'HQ'), (2, 'Headquarters');
```

**So far, honestly, SQL is fine.** If your locations only ever grow one tree from one root, this design is not the problem. The problem shows up the moment two organizations need to talk about the same physical place using two different identifiers.

### 1c. The part SQL genuinely struggles with

Say your maintenance contractor runs their own facilities system, with their own site codes — `Contractor Site 7 / Block B / Ground Floor` — and Ground Floor happens to be *the exact same physical storey* as your `Storey 1`. You want their imported work orders to show up when you filter "everything at Site Orange," without either side renaming anything.

You have two options, and both cost something real:

**Option A — merge the rows.** Delete the contractor's duplicate `locations` rows, repoint everything at your existing `Storey 1` row:

```sql
UPDATE maintenance_issues
SET location_id = 3          -- Storey 1
WHERE location_id = 103;     -- the contractor's Ground Floor row, now gone

DELETE FROM locations WHERE id IN (101, 102, 103);
```

This is exactly the operation the article's title is about — you are now rewriting existing maintenance records because two location systems needed reconciling. Every future import from the contractor also needs a translation step, by hand, before it can be inserted.

**Option B — keep both, add an equivalence table.**

```sql
INSERT INTO locations (id, label, type, parent_id) VALUES
  (101, 'Contractor Site 7', 'site',     NULL),
  (102, 'Block B',           'building', 101),
  (103, 'Ground Floor',      'storey',   102);

CREATE TABLE location_equivalences (
    location_id_a INTEGER REFERENCES locations(id),
    location_id_b INTEGER REFERENCES locations(id),
    PRIMARY KEY (location_id_a, location_id_b)
);
INSERT INTO location_equivalences VALUES (103, 3);   -- Ground Floor = Storey 1
```

No existing `maintenance_issues.location_id` needs to change — good, this preserves the property we actually want. But look at what the containment query now has to become. "Everything under Site Orange" must also chase the equivalence table, transitively, in both directions, *before* walking the parent/child hierarchy:

```sql
WITH RECURSIVE equiv(id) AS (
    SELECT 1
    UNION
    SELECT b.location_id_b FROM location_equivalences b
    JOIN equiv e ON b.location_id_a = e.id
    UNION
    SELECT a.location_id_a FROM location_equivalences a
    JOIN equiv e ON a.location_id_b = e.id
),
descendants AS (
    SELECT id FROM equiv
    UNION ALL
    SELECT l.id FROM locations l JOIN descendants d ON l.parent_id = d.id
)
SELECT mi.* FROM maintenance_issues mi
JOIN descendants d ON mi.location_id = d.id;
```

This is achievable SQL — most engines can express it, with some fighting over recursive-CTE restrictions depending on vendor. But notice what actually happened: **you just hand-invented a bespoke schema and query pattern for two extremely common relationship types — "is part of" and "is the same thing as."** You designed the `location_equivalences` table, you wrote and debugged the double-recursive traversal, and every developer who touches this codebase now has to learn *your* particular encoding of those two ideas before they can safely write a new query against it. And this is only for **one** external system. A third contractor with their own codes means extending the same bespoke machinery further, not reusing anything you already had — where does that scale to when you have 12 buildings each run by different sub-contractors, and 100s of assets/rooms within each of them?

---

## Part 2: The ontology approach

The core move: stop treating "contains" and "is the same as" as problems you invent a schema for, and instead use vocabulary that already exists for exactly this purpose — RDF's `isPartOf`-style object properties and OWL's `owl:sameAs` — combined with **URIs as the one stable thing a maintenance issue ever points at.**

### 2a. The TBox — a small, self-contained schema

```turtle
ies:Facility a owl:Class .
ies:Site     a owl:Class ; rdfs:subClassOf ies:Facility .
ies:Building a owl:Class ; rdfs:subClassOf ies:Facility .
ies:Storey   a owl:Class ; rdfs:subClassOf ies:Facility .
ies:Zone     a owl:Class ; rdfs:subClassOf ies:Facility .

ies:isPartOf a owl:ObjectProperty, owl:TransitiveProperty ;
    rdfs:domain ies:Facility ;
    rdfs:range  ies:Facility .
```

That's the entire schema. Naming is *inspired by* IES (a real UK information-sharing ontology standard) but this is a small, local, self-contained vocabulary — deliberately not importing IES4's much heavier state-based modeling. `isPartOf` plays the role of `parent_id`. `owl:sameAs` — a standard OWL primitive, not something we invented — plays the role of the equivalence table, except every RDF tool in existence already knows what it means.

### 2b. The ABox — instances, and the cross-system reconciliation

```turtle
<https://example.org/facility/SiteOrange> a ies:Site ;
    rdfs:label "Site Orange" .

<https://example.org/facility/SiteOrange/MainBuilding> a ies:Building ;
    rdfs:label "Main Building" ;
    skos:altLabel "HQ", "Headquarters" ;
    ies:isPartOf <https://example.org/facility/SiteOrange> .

<https://example.org/facility/SiteOrange/MainBuilding/Storey1> a ies:Storey ;
    rdfs:label "Storey 1" ;
    ies:isPartOf <https://example.org/facility/SiteOrange/MainBuilding> .
```

Synonyms use `skos:altLabel` — again, standard vocabulary, not a bespoke `location_synonyms` table. Now the contractor's parallel system:

```turtle
<https://example.org/facility/ContractorSite7/BlockB/GroundFloor> a ies:Storey ;
    rdfs:label "Ground Floor" ;
    ies:isPartOf <https://example.org/facility/ContractorSite7/BlockB> ;
    owl:sameAs <https://example.org/facility/SiteOrange/MainBuilding/Storey1> .
```

One triple. No new table. No `UPDATE` against anything. The contractor's Ground Floor and our Storey 1 remain two distinct, independently-labeled individuals — two organizations' honest records of their own naming — declared equivalent, not merged.

### 2c. Flattening it — build time, not query time

This is the piece that matters for anyone worried "does this mean every search now needs a live graph database and SPARQL?" No. The graph is walked **once**, at ingest, with an ordinary ~100-line Python script using `rdflib`:

```python
class _UnionFind:
    """Groups owl:sameAs-linked individuals; picks one arbitrary
    representative per group, used purely so multiple documents
    can agree on one shared identifier."""
    ...

for uri in every_site_building_storey_zone_instance:
    chains = enumerate_isPartOf_chains(uri)        # e.g. Site/Building/Storey/Zone
    canonical_uri = sameas_groups.canonical(uri)    # the shared identity
    for chain in chains:
        index_document({
            "uri": canonical_uri,        # what a maintenance issue stores
            "source_uri": str(uri),      # this individual's own real identity
            "path": "/".join(local_names(chain)),   # human-readable, for display
            "label": rdfs_label(uri),
            "synonyms": skos_altLabels(uri),
        })
```

The output is ordinary Elasticsearch documents. `Storey 1` and `Ground Floor` each get their own document — with different `path` and `label` — but **the same `uri` field value**, because they were declared `sameAs`. That's the entire mechanism. No live ontology reasoning happens when a user searches; Elasticsearch is comparing plain strings, same as it always does. The union-find over `owl:sameAs` — the closest thing to "graph logic" anywhere in this system — runs once, in a script, whenever the ontology changes.

### 2d. What a maintenance issue actually stores

```json
{
  "title": "HVAC service due",
  "location_uri": "https://example.org/facility/SiteOrange/MainBuilding/Storey1/PlantRoom",
  "location_path": [
    "SiteOrange/MainBuilding/Storey1/PlantRoom",
    "ContractorSite7/BlockB/GroundFloor/PlantRoomX"
  ]
}
```

One stable URI. That URI never needs to change, no matter how the ontology is restructured later, because it's a reference — the same role a foreign key plays in SQL, except what it points *at* can be re-derived and re-projected without ever touching this document. (`location_path` here is a denormalized cache of the currently-known display paths, for search performance — more on that trade-off honestly, below.)

---

## Part 3: One identity, any number of taxonomies

Here's the part worth dwelling on, because it's the actual payoff, not just a cleverer equivalence table.

**A taxonomy — the thing a human picks from — is not the ontology. It's a *view* generated from it.** The ontology is just facts: this contains that, this is the same as that, this is called such-and-such. A taxonomy is one particular walk through those facts, rendered as a human-readable hierarchy of labels.

That means you can generate as many taxonomies as you have audiences, from the same underlying graph, without duplicating any data:

- **The owner's taxonomy**: `Site Orange / Main Building / Storey 1 / Plant Room`
- **The contractor's taxonomy**: `Contractor Site 7 / Block B / Ground Floor / Plant Room (PR-114)`
- *(Hypothetically, cheaply, if you needed it)* **A fire-safety zoning taxonomy** that groups the same physical spaces along completely different boundaries — just more `isPartOf` triples in a separate file, loaded alongside the rest, reusing the exact same ingestion code.

A user typing into the search box never sees a URI, never sees the word "ontology," and never needs to know any of this exists. They see exactly what they'd see from a well-built taxonomy picker: a label, and — critically, for disambiguation — the ancestor path in small grey text underneath it, so if two things share a name, they can tell them apart at a glance:

```
Zone A                                    Zone A
SiteOrange / MainBuilding / Storey1       SiteOrange / MainBuilding / Storey2
```

```
Plant Room                                Plant Room (PR-114)
SiteOrange / MainBuilding / Storey1       ContractorSite7 / BlockB / GroundFloor
```

Two *different* physical zones, disambiguated by distinct paths and distinct identifiers on the left. One *same* physical room, reachable through two organizations' completely independent naming conventions on the right — and picking either row writes back the identical `location_uri`. The user experience is indistinguishable from a normal taxonomy dropdown. The only difference is what's generating the picklist underneath it, and how cheaply a new one can be added.

---

## Side-by-side

| | Flat SQL columns | Normalized SQL (adjacency list) | Ontology → Elasticsearch |
|---|---|---|---|
| Location entry UI | 4 dependent dropdowns, or free text | 4 dependent dropdowns | 1 autocomplete field |
| Add a new leaf location | New row, no migration | New row, no migration | New triple, re-ingest, no migration |
| Add a synonym | New column value / hacky | New row in a synonym table | New `skos:altLabel` triple |
| Reconcile two systems' identifiers | Not modeled at all | Bespoke equivalence table + hand-written recursive traversal | `owl:sameAs`, one triple, standard vocabulary + tooling |
| Rewrite existing maintenance records to reconcile? | N/A | Only if you choose the "merge" option | Never |
| Support N independent taxonomies over the same data | Not modeled | N more tables, N more join queries | N more triples, same ingestion code |
| Disambiguating two same-named locations at entry time | Not possible | Possible, with app-level work | Built in — ancestor path shown per row |

---

## The honest caveats

This isn't magic, and the article would be dishonest without saying where the edges are:

**`location_path` is a cache, and caches can go stale.** Denormalizing the resolved paths onto each issue at write time is a performance optimization — it avoids re-resolving the ontology for every issue on every search. If you later *remove* a `sameAs` assertion (rather than add one), an issue written while it still held onto a since-revoked equivalence will keep matching a filter it semantically shouldn't, until that issue is re-saved. Additions are effectively self-healing (a fresh query always re-resolves live); removals are the case that needs care — the same trade-off any materialized view or cache makes, not something unique to ontologies.

**No live SPARQL, on purpose.** Everything above happens with an ordinary Elasticsearch `prefix` query at request time. The graph reasoning — walking `isPartOf`, computing `sameAs` closures — happens once, at ingest, in plain Python. If you eventually need genuinely relational queries that don't reduce to "everything under X" (say, "which rooms share a fire-exit route that also passes through a different building"), that's the point at which a live triple store earns its keep — and because the search layer only ever talks to flattened documents, adding one later is additive, not a rewrite.

**A well-designed SQL schema isn't incompetent.** The normalized adjacency-list version in Part 1b is a perfectly reasonable design for a single, self-consistent hierarchy. The gap opens specifically at cross-system identity and multiple simultaneous taxonomies — which is exactly the situation any organization with contractors, subsidiaries, or legacy systems eventually runs into.

---

## The takeaway

The SQL version isn't wrong so much as it's missing vocabulary. "Contains" and "is the same as" are two of the most common relationships in any real-world data model, and relational schemas make you invent your own encoding for them every single time, from scratch, per project. RDF and OWL already have words for them — words that come with generic tooling that already knows how to walk them. Use that vocabulary at the modeling layer, flatten it into whatever your search engine wants at build time, and the field a user types into stays exactly as simple as a well-built taxonomy always was — while what's underneath it can be restructured, merged, and reconciled across organizational boundaries without ever touching the maintenance record itself.
