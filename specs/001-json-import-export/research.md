# Research: JSON Import/Export

**Feature**: 001-json-import-export  
**Date**: 2026-03-07  

---

## Decision Log

### 1. JSON Document Schema

**Decision**: Top-level object with a `"bookmarks"` array key.

```json
{
  "bookmarks": [
    {
      "url": "https://example.com",
      "title": "Example Site",
      "tags": ["web", "example"],
      "created_at": "2026-03-07T12:00:00+00:00",
      "updated_at": "2026-03-07T12:00:00+00:00"
    }
  ]
}
```

**Rationale**: A named array at the top level (versus a bare array `[...]`) allows future additions of top-level metadata (e.g., `"version"`, `"exported_at"`) without breaking parsers. A named key is the dominant pattern in portable CLI tool exports (e.g., `gh`, `npm`, `pip`).

**Alternatives considered**:
- **Bare JSON array** (`[{...}, ...]`): Simpler but not extensible; rejected.
- **NDJSON** (newline-delimited JSON): Better for streaming large files but harder to validate and less human-readable; out of scope for initial release.

---

### 2. Field Inclusion in Export

**Decision**: Export all `Bookmark` fields: `url`, `title`, `tags`, `created_at`, `updated_at`.

**Rationale**: FR-004 mandates inclusion of all fields. Including timestamps enables future features (e.g., date-based filtering, audit logs) and round-trips full record fidelity for power users. The `id` field is **excluded** because it is a store-internal surrogate key; using URL as the natural key for duplicate detection is correct (spec assumption: "Duplicate detection uses URL").

**Alternatives considered**:
- **Exclude timestamps**: Would satisfy the minimum fidelity requirement (FR-005 only mandates URL/title/tags) but reduces utility; rejected.
- **Include `id`**: Would create coupling to internal storage layout and cause conflicts on import to a different store; rejected.

---

### 3. Timestamp Handling on Import

**Decision**: If `created_at` / `updated_at` are present in the import file, honor them by inserting directly via a raw SQL path in `jsonport.py`. If absent, use current UTC time (same as `store.create()`).

**Rationale**: The spec assumption states "if timestamps are present in the file they are honored". However, FR-005 (round-trip fidelity) only mandates URL/title/tags. To avoid modifying `BookmarkStore`'s public API, timestamp-aware insertion will be implemented as a direct SQL call within the `jsonport` module (an internal detail, not a new store method).

**Alternatives considered**:
- **Add `create_with_timestamps()` to `BookmarkStore`**: Cleaner separation but adds API surface to a stable module; deferred to a future spec if needed.
- **Always use current time on import**: Simpler but violates the spec assumption; rejected.

---

### 4. Duplicate Detection Strategy

**Decision**: Load all existing bookmarks once via `store.list_all()`, build a `dict[str, Bookmark]` keyed by URL, then apply the policy per-entry.

**Rationale**: A single bulk read is far cheaper than one `SELECT` per import entry. For 1 000 bookmarks, `list_all()` loads them in < 5 ms; per-entry queries would add N round-trips. Memory impact is negligible (< 1 MB for 1 000 bookmarks with typical field sizes).

**Alternatives considered**:
- **Per-entry `SELECT` by URL**: Correct but O(N) database round-trips; rejected.
- **`INSERT OR IGNORE` / `INSERT OR REPLACE`**: Requires exposing SQL-level upsert semantics; violates the store abstraction; rejected.

---

### 5. Duplicate Policy Default

**Decision**: Default policy is **skip** (`--on-duplicate skip`).

**Rationale**: Matches spec assumption: "Skipping is the safer default to prevent accidental overwrites; users must explicitly opt in to update behavior." FR-006 mandates skip as default; FR-007 mandates `--on-duplicate update` as the opt-in.

---

### 6. In-File Duplicate Handling

**Decision**: Track already-seen URLs within a single import run using a `set`. For a within-file duplicate, apply the configured policy (skip or update the just-inserted record).

**Rationale**: The spec edge case states: "The first occurrence is imported; subsequent duplicate entries in the same file follow the configured duplicate policy." This means the per-run seen-URL set is updated after each successful insertion, so subsequent occurrences are treated exactly like a store-resident duplicate.

---

### 7. Invalid Entry Handling

**Decision**: Entries missing `url` (absent key, `None`, or empty string) are **rejected with a warning** printed to stderr; processing continues for all other entries; the summary reports the invalid count.

**Rationale**: FR-011 mandates per-entry rejection without aborting the batch. Printing warnings to stderr preserves stdout for machine-readable output (e.g., when piped).

---

### 8. Module Layout

**Decision**: New module `src/bookmarkcli/jsonport.py` for all serialisation and import orchestration. CLI commands added directly to `src/bookmarkcli/cli.py`.

**Rationale**: Keeps the package flat (consistent with S02 pattern). `jsonport.py` is independently testable without going through Click. CLI thin-wrapper approach keeps `cli.py` free of business logic.

**Alternatives considered**:
- **`src/bookmarkcli/io/` subpackage**: Adds a directory level not justified by one module; rejected.
- **All logic in `cli.py`**: Violates separation of concerns; makes unit testing harder; rejected.

---

### 9. No New Runtime Dependencies

**Decision**: Use Python stdlib `json`, `sys`, `pathlib` only. No third-party JSON libraries.

**Rationale**: `json` module is sufficient for the schema complexity (flat objects, simple types). Adding a dependency (e.g., `pydantic`) is unjustified overhead for this feature scope.

---

### 10. Export File Overwrite Behaviour

**Decision**: Silently overwrite the export file if it already exists.

**Rationale**: Standard POSIX CLI behaviour (cp, curl -o, etc.). The spec edge case explicitly states: "The file is overwritten without prompting." No --force flag needed.

---

## Summary of Resolved Unknowns

| Topic | Decision |
|---|---|
| JSON schema shape | Top-level `{"bookmarks": [...]}` |
| Fields exported | `url`, `title`, `tags`, `created_at`, `updated_at` (no `id`) |
| Timestamps on import | Honored if present; current time otherwise |
| Duplicate detection | In-memory URL dict from `list_all()` |
| Default duplicate policy | Skip |
| In-file duplicates | Follow configured policy from first occurrence onward |
| Invalid entries | Warn + skip per entry, continue batch |
| New module | `src/bookmarkcli/jsonport.py` |
| New dependencies | None (stdlib only) |
| Overwrite on export | Silent overwrite |
