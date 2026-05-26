# About the Tagging System

## The Core Idea

The problem this system solves: how do you find the right thing when you don't quite know what it's called, or when the thing belongs to multiple overlapping categories at once?

The answer is a layered approach:

1. **Hierarchical taxonomies** — structured, authoritative categories
2. **Multiple mini taxonomies** — separate dimensions that describe different aspects of the same item
3. **Composable filters** — AND/OR/NOT logic to narrow across those dimensions simultaneously
4. **Free-text search** — layered on top of the filters for when you want to describe rather than categorise
5. **Synonyms** — so the same concept can be found by many different names

---

## Hierarchical Taxonomy

Each taxonomy is a tree of concepts expressed as a path, using `/` as a separator:

```
type/
type/face/
type/face/emotion/
type/face/emotion/positive
type/face/emotion/negative
type/animal/
type/animal/mammal/dog
type/animal/mammal/cat
```

The path is both the identifier and the hierarchy. A document tagged with `type/face/emotion/positive` is implicitly also tagged with `type/face/emotion`, `type/face`, and `type` — the hierarchy is encoded in the string itself.

This matters for search: a filter on `type/face` will match anything tagged with any descendant of that node, without needing to enumerate them all. The search layer uses a prefix query, so `type/face` matches everything that starts with `type/face/`.

---

## Multiple Mini Taxonomies

Rather than one giant taxonomy that tries to describe everything about an item in a single hierarchy, the system uses several independent taxonomies — each capturing a different dimension of meaning.

For example, an emoji like 🐕 might be tagged across three separate taxonomies:

| Taxonomy | Tag | What it captures |
|----------|-----|-----------------|
| `type/` | `type/animal/mammal/dog` | What *kind* of thing it is |
| `visual/` | `visual/color/brown`, `visual/style/cute` | How it looks |
| `mood/` | `mood/wholesome` | The feeling it conveys |

Each taxonomy is its own small, coherent hierarchy. Keeping them separate makes it easier to:

- **Author** — each taxonomy has a clear, bounded scope
- **Maintain** — changes in one dimension don't ripple into others
- **Filter** — you can target just the dimensions you care about

In practice, taxonomies tend to fall into a few natural kinds: *what* (type, category), *how it looks* (visual properties), *when or where* (context), and *how it feels* (mood, tone). The structure of any given project's taxonomies will reflect the dimensions that actually matter for finding its content.

---

## Composable Filters

Once items are tagged across multiple taxonomies, the filtering system lets you combine those tags using boolean logic. There are three lanes:

| Lane | Meaning |
|------|---------|
| **AND** | The result must match all of these tags |
| **OR** | The result must match at least one of these tags |
| **NOT** | The result must not match any of these tags |

This maps directly to Elasticsearch boolean clauses (`must`, `should`, `must_not`).

### What this enables

Consider a collection of emoji. You want: *animals, but not insects, that also have a positive or playful mood.*

- AND: `type/animal`
- NOT: `type/animal/insect`
- OR: `mood/positive`, `mood/playful`

These three lanes work together as a single query. The AND clause narrows the universe, the NOT clause removes a subtree, and the OR clause selects within what remains.

Because filters use prefix matching on the hierarchy, you often need far fewer tags than you might expect. Filtering on `type/animal` automatically includes dogs, cats, fish, birds — you only need to go deeper when you want to exclude or specifically target a subcategory.

---

## Free-Text Search Over Filters

Filters are precise but require knowing the taxonomy. Free-text search lets you describe what you want in natural language.

Text search operates *on top of* whatever filters are active. The filters define the universe of eligible documents; the text query ranks them by relevance within that universe.

Text matching covers:
- The item's name (weighted highest)
- The item's description
- The path segments of its tags (so searching "mammal" or "dog" also finds things through their tag paths)

In production, this layer is the natural home for **semantic / RAG-style search** — embedding the query and finding semantically similar items rather than doing keyword matching. The architecture is already set up for this: filters run first to reduce the candidate set, then semantic ranking applies within those results. This keeps embedding search tractable even over large collections.

---

## Synonyms

Taxonomies use precise, canonical labels — "Positive Emotion", "Canine", "Chromatic Red". But users think in everyday language: "happy", "dog", "red".

Synonyms bridge this gap. Each taxonomy node can hold a list of alternative terms:

```json
{
  "path": "type/face/emotion/positive",
  "label": "Positive Emotion",
  "synonyms": ["happy", "glad", "joy", "smile", "cheerful", "grin", "laugh"]
}
```

When a user types "smile" into the tag picker, the autocomplete searches:

1. **Exact synonym match** — highest priority, finds nodes where `smile` is listed as a synonym
2. **Fuzzy synonym match** — catches typos and close variants
3. **Label match** — fuzzy match on the node's canonical label
4. **Path segment match** — prefix match on the path components

The UI shows which route was taken — a "synonym" badge means you found the concept through an alias, not its official name. This is useful feedback: it tells the user what the system understood their term to mean.

The key property of synonyms is that **they point to one canonical node**. If "happy", "glad", "smile", and "cheerful" all resolve to `type/face/emotion/positive`, then filtering on that node is equivalent to filtering on any of those words. You write the synonym list once, and every user query benefits from it regardless of which word they happened to use.

---

## How the Layers Work Together

A typical interaction might go like this:

1. The user opens the filter builder and types "dog" — the autocomplete resolves this to `type/animal/mammal/dog` via its synonym list. They add it to the AND lane.

2. They type "insect" and add `type/animal/insect` to the NOT lane, because they want things in the animal category but not bugs.

3. They type "happy" into the free-text search box. This runs as a keyword query over the name and description of everything that passed the filter.

4. The results show items that are classified as dogs, not insects, and whose name or description contains something like "happy" or "happiness".

Each layer does a different job:
- **Taxonomy** provides the structure and vocabulary
- **Multiple taxonomies** let one item live in several independent dimensions at once
- **Filters** let you combine those dimensions with boolean precision
- **Synonyms** mean users don't need to know the canonical label for any of this to work
- **Free text** handles the remainder — the subjective, the descriptive, the fuzzy

---

## Authoring Considerations

A few principles that emerge from using this kind of system:

**Keep taxonomies narrow in scope.** A taxonomy that tries to cover everything becomes a taxonomy that covers nothing well. Better to have five tightly-scoped trees than one sprawling one.

**Synonyms belong to the taxonomy, not the documents.** If you put synonyms on the taxonomy nodes, every document benefits automatically. If you put them on individual documents, you'll end up with inconsistent coverage.

**Depth should reflect real distinctions.** Adding levels just to add levels makes the hierarchy harder to navigate. A new depth level is justified when it creates a meaningful new filter surface — when users will actually want to filter at that level.

**Start broad, go deep on demand.** A document can be tagged at `type/animal` even if there isn't yet a `type/animal/mammal/dog` node. You can refine the taxonomy later without re-tagging every document — the prefix matching means that as you add deeper nodes, existing tags remain valid and more specific filters just become available.
