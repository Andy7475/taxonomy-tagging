"""Parse the facility ontology (TBox + ABox turtle files) and flatten it into
Elasticsearch documents, mirroring the path-prefix pattern used by the
taxonomy index elsewhere in this app.

One Elasticsearch document is indexed per (uri, path) pair rather than per
instance: a facility reachable via more than one `isPartOf` chain (see
ontology/facility_instances.ttl's Plant Room example, which has both an
owner-facing and a contractor-facing parent) is indexed once per chain, all
rows sharing the same `uri`. This lets the frontend surface every valid
hierarchy path for a facility without forcing the ingestion script to guess
which parent is "correct" — the user picks whichever path matches their own
frame of reference, and every choice writes back the same `uri`.
"""

import asyncio
import hashlib
import logging
from pathlib import Path

import owlrl
from elasticsearch import AsyncElasticsearch
from rdflib import Graph, Namespace, RDF, RDFS
from rdflib.namespace import SKOS, OWL

from app.config import settings

logger = logging.getLogger(__name__)

IES = Namespace("http://example.org/ontology/ies-lite#")

# Ordered root-to-leaf; also doubles as the depth-by-type lookup used for
# the `depth` field (kept independent of chain length so it stays stable
# even if a chain happens to skip a level).
HIERARCHY_TYPES = ["Site", "Building", "Storey", "Zone"]


def _ontology_dir() -> Path:
    if settings.ontology_dir:
        return Path(settings.ontology_dir)
    return Path(__file__).resolve().parents[2] / "ontology"


def _load_graph() -> Graph:
    g = Graph()
    ontology_dir = _ontology_dir()
    g.parse(ontology_dir / "facility.ttl", format="turtle")
    g.parse(ontology_dir / "facility_instances.ttl", format="turtle")
    return g


def _facility_type(g: Graph, uri) -> str | None:
    for t in HIERARCHY_TYPES:
        if (uri, RDF.type, IES[t]) in g:
            return t
    return None


def _enumerate_chains(g: Graph, uri, visited: frozenset = frozenset()) -> list[list]:
    """All root-to-`uri` ancestor chains, following every isPartOf parent
    that is itself typed within the hierarchy. An instance with a single
    parent yields one chain; an instance with several unrelated parents
    (e.g. Plant Room) yields one chain per parent."""
    if uri in visited:
        logger.warning("Cycle detected in isPartOf involving <%s>; truncating chain", uri)
        return [[uri]]

    parents = [
        p for p in g.objects(uri, IES.isPartOf)
        if _facility_type(g, p) is not None
    ]

    if not parents:
        return [[uri]]

    chains = []
    for parent in sorted(parents):
        for parent_chain in _enumerate_chains(g, parent, visited | {uri}):
            chains.append(parent_chain + [uri])
    return chains


def _local_name(uri: str) -> str:
    return uri.rstrip("/").rsplit("/", 1)[-1]


class _UnionFind:
    """Builds owl:sameAs equivalence classes across separately-minted
    individuals (e.g. an owner's Storey and a contractor's Storey that
    denote the same physical place). Deliberately NOT consulted during
    `_enumerate_chains` — expanding sameAs-equivalents at every level of
    the ancestor walk produces a combinatorial explosion of duplicate,
    mislabeled chains. Instead each instance is walked independently via
    isPartOf as before, and sameAs is only used afterwards, once per
    instance, to decide which `uri` value its resulting documents share
    with any equivalent instance's documents."""

    def __init__(self):
        self._parent: dict = {}

    def _find(self, node):
        self._parent.setdefault(node, node)
        while self._parent[node] != node:
            self._parent[node] = self._parent[self._parent[node]]
            node = self._parent[node]
        return node

    def union(self, a, b):
        ra, rb = self._find(a), self._find(b)
        if ra != rb:
            # Deterministic, otherwise-arbitrary tie-break: which URI string
            # "wins" as canonical carries no meaning and is never shown to
            # end users (the UI only ever displays label/path) — it only
            # decides which literal string multiple documents agree to share.
            winner, loser = sorted([ra, rb], key=str)
            self._parent[loser] = winner

    def canonical(self, node):
        return self._find(node)


def _sameas_closure(g: Graph) -> _UnionFind:
    """Equivalence classes derived via genuine OWL-RL entailment (owlrl's
    built-in symmetric/transitive rules for owl:sameAs) rather than a
    hand-rolled transitive walk. Reasoning is deliberately scoped to an
    isolated copy of JUST the sameAs triples — never the full graph — so it
    can't also touch isPartOf's declared transitivity, which the ancestor-
    chain walk above needs to stay un-collapsed (see facility.ttl's comment
    on why isPartOf is walked explicitly instead of relying on a reasoner)."""
    sameas_only = Graph()
    for s, o in g.subject_objects(OWL.sameAs):
        sameas_only.add((s, OWL.sameAs, o))

    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(sameas_only)

    uf = _UnionFind()
    for s, o in sameas_only.subject_objects(OWL.sameAs):
        if s != o:
            uf.union(s, o)
    return uf


async def ingest_locations(es: AsyncElasticsearch) -> dict:
    g = _load_graph()
    sameas = _sameas_closure(g)

    instances = sorted(
        {s for t in HIERARCHY_TYPES for s in g.subjects(RDF.type, IES[t])}
    )

    facility_count = 0
    document_count = 0

    for uri in instances:
        facility_type = _facility_type(g, uri)
        label = g.value(uri, RDFS.label)
        comment = g.value(uri, RDFS.comment)
        synonyms = [str(s).lower() for s in g.objects(uri, SKOS.altLabel)]
        canonical_uri = str(sameas.canonical(uri))

        chains = _enumerate_chains(g, uri)
        facility_count += 1

        for chain in chains:
            path = "/".join(_local_name(str(u)) for u in chain)
            doc = {
                # `uri` is the shared identity a sameAs-equivalent instance's
                # documents agree on (see _UnionFind); `source_uri` is always
                # this specific individual, used for provenance and to
                # resolve a raw/foreign identifier back to its canonical uri.
                "uri": canonical_uri,
                "source_uri": str(uri),
                "path": path,
                "label": str(label) if label else _local_name(str(uri)),
                "facility_type": facility_type,
                "depth": HIERARCHY_TYPES.index(facility_type),
                "synonyms": synonyms,
                "description": str(comment) if comment else None,
            }
            doc_id = hashlib.sha1(f"{uri}|{path}".encode()).hexdigest()
            await es.index(index=settings.locations_index, id=doc_id, document=doc)
            document_count += 1

    await es.indices.refresh(index=settings.locations_index)

    return {
        "status": "ok",
        "facilities": facility_count,
        "documents": document_count,
    }


async def main():
    es = AsyncElasticsearch([settings.elasticsearch_url])
    print(f"Connecting to Elasticsearch at {settings.elasticsearch_url}...")
    info = await es.info()
    print(f"Connected: ES {info['version']['number']}")

    print(f"Parsing ontology from {_ontology_dir()}...")
    result = await ingest_locations(es)
    print(
        f"Done! Indexed {result['facilities']} facilities "
        f"as {result['documents']} location documents."
    )
    await es.close()


if __name__ == "__main__":
    asyncio.run(main())
