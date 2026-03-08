# Research: Tag Management

**Feature**: 004-tag-management  
**Date**: 2026-03-07

---

## Overview

This document captures all design decisions resolved in Phase 0. Four technical questions were investigated: tag storage strategy, Click mutual-exclusion pattern, normalization placement, and `list_tags()` aggregation approach.

---

## Decision 1: Tag Storage — Comma-separated TEXT vs. Junction Table

**Decision**: Keep tags as a comma-separated TEXT column on `bookmarks`. No schema migration.

**Rationale**: The spec explicitly states "tags remain a list of strings on each bookmark." At the stated scale of 10 000 records, all three required operations are implementable with one `SELECT` or `UPDATE` per call. A single table scan for `list_tags()` touches at most ~1 MB of data, completing well under the SC-005 < 1 s budget.

**Alternatives considered**:

| Approach | Pros | Cons |
|----------|------|------|
| **TEXT column (chosen)** | No migration; trivial add/remove; single scan for aggregation | Tag search (not required) needs full-table scan |
| **Junction table `bookmark_tags`** | Indexed tag lookups; clean relational model | Requires schema migration; 3-way JOINs; INSERT/DELETE per tag change; overkill at this scale |

---

## Decision 2: Click Mutual Exclusion — `--add` and `--remove`

**Decision**: Validate flag exclusivity inline in the command function body.

**Rationale**: Two guard clauses in the command function body are the simplest, most readable approach for two mutually exclusive options:

```python
if add_tag and remove_tag:
    raise click.UsageError("--add and --remove are mutually exclusive.")
if not add_tag and not remove_tag:
    raise click.UsageError("Provide exactly one of --add or --remove.")
```

**Alternatives considered**:

| Approach | Pros | Cons |
|----------|------|------|
| **Inline validation (chosen)** | Simple; no extra classes; obvious to readers | None at this scale |
| Custom `MutuallyExclusiveOption(click.Option)` class | Reusable; error message on parse | Adds ~20 lines of boilerplate for a two-option case |
| `click.Choice` + `--action add\|remove` | Built-in support | Changes UX from `--add TAG` to `--action add --tag TAG`; contradicts spec |

---

## Decision 3: `normalize_tag()` Placement

**Decision**: Module-level function in `models.py`.

**Rationale**: Tag normalization is a domain rule (data semantics), not a storage or CLI concern. Placing it in `models.py` co-locates it with the exception classes (`TagValidationError`, `TagNotFoundError`) and makes it importable without pulling in `store.py`. It also keeps `store.py` free of domain logic.

```python
# models.py
def normalize_tag(tag: str) -> str:
    """Return tag stripped of surrounding whitespace and converted to lowercase."""
    return tag.strip().lower()
```

**Alternatives considered**:

| Location | Pros | Cons |
|----------|------|------|
| **`models.py` (chosen)** | Domain logic lives with domain types | None |
| `store.py` | Close to usage | Mixes domain logic with persistence |
| New `utils.py` | Clearly a utility | Extra module for a one-liner |

---

## Decision 4: `list_tags()` Implementation — In-memory vs. SQL Aggregation

**Decision**: In-memory aggregation (read all `tags` column values, parse, count in Python).

**Rationale**: For 10 000 records with typical tag data (~200 KB–1 MB total), a single `SELECT tags FROM bookmarks WHERE tags != ''` scan followed by in-memory parsing and dict counting runs in < 50 ms — well within SC-005's < 1 s budget. SQLite has no `UNNEST`/`ARRAY_AGG`, so SQL aggregation over comma-separated strings requires complex non-portable workarounds with no performance benefit at this scale.

```python
def list_tags(self) -> list[tuple[str, int]]:
    con = self._require_connection()
    rows = con.execute("SELECT tags FROM bookmarks WHERE tags != ''").fetchall()
    counts: dict[str, int] = {}
    for row in rows:
        for tag in self._deserialize_tags(row[0]):
            counts[tag] = counts.get(tag, 0) + 1
    return sorted(counts.items())
```

**Alternatives considered**:

| Approach | Pros | Cons |
|----------|------|------|
| **In-memory (chosen)** | Simple; portable; fast enough | — |
| Raw SQL aggregation | No Python loop | Non-portable SQLite string hacks; marginal gain at 10k rows |
| Materialized `tag_counts` table | O(1) reads | Cache invalidation complexity; extra writes on every tag change |

---

## Summary

| # | Question | Decision |
|---|----------|----------|
| 1 | Tag storage | Keep comma-separated TEXT; no schema migration |
| 2 | Click mutex | Inline validation in command function body |
| 3 | Normalize location | Module-level function `normalize_tag()` in `models.py` |
| 4 | `list_tags()` impl | In-memory aggregation over single table scan |
