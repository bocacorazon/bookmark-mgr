# Data Model: JSON Import/Export

**Feature**: 001-json-import-export  
**Date**: 2026-03-07  

---

## Scope

This feature adds JSON serialisation and deserialisation on top of the existing `Bookmark` entity (defined in S02). It introduces:

1. The **JSON Export Document** format.
2. The **`ImportResult`** value object (Python dataclass).
3. The **`jsonport`** module (`src/bookmarkcli/jsonport.py`) that owns all serialisation and import orchestration logic.

No changes are made to `bookmarkcli.models` or `bookmarkcli.store`.

---

## Entities

### `Bookmark` (existing — S02)

No changes. Defined in `src/bookmarkcli/models.py`.

| Field        | Python Type        | Notes                               |
|--------------|--------------------|-------------------------------------|
| `id`         | `int \| None`      | Store-internal surrogate key; **excluded from JSON export** |
| `url`        | `str`              | Required; natural unique key for duplicate detection |
| `title`      | `str \| None`      | Optional                            |
| `tags`       | `list[str]`        | Never `None`; empty list when absent |
| `created_at` | `datetime` (UTC)   | Included in export                  |
| `updated_at` | `datetime` (UTC)   | Included in export                  |

---

### `ImportResult` (new — this feature)

A value object returned by `jsonport.import_from_json()` summarising the outcome of one import run.

```python
@dataclass
class ImportResult:
    added: int    # bookmarks successfully inserted
    skipped: int  # duplicates skipped (policy=skip or already-seen in-file)
    updated: int  # duplicates updated (policy=update)
    invalid: int  # entries missing url or otherwise malformed
```

**Invariants**:
- All counts are non-negative integers.
- `added + skipped + updated + invalid` equals the total number of entries in the input file.
- `updated` is 0 when `on_duplicate="skip"`.

---

## JSON Export Document Format

The export document is a UTF-8 encoded JSON file with the following schema:

```json
{
  "bookmarks": [
    {
      "url": "https://example.com",
      "title": "Example Site",
      "tags": ["web", "example"],
      "created_at": "2026-03-07T12:00:00+00:00",
      "updated_at": "2026-03-07T12:34:56+00:00"
    }
  ]
}
```

### Field rules

| JSON key      | Type             | Required | Notes |
|---------------|------------------|----------|-------|
| `url`         | string           | ✅        | Non-empty string |
| `title`       | string or `null` | ❌        | `null` for untitled bookmarks |
| `tags`        | array of strings | ✅        | `[]` for untagged bookmarks |
| `created_at`  | ISO 8601 string  | ❌        | UTC; honoured on import if present |
| `updated_at`  | ISO 8601 string  | ❌        | UTC; honoured on import if present |

### Empty store export

```json
{"bookmarks": []}
```

### Validation rules on import

| Rule | Action on failure |
|------|-------------------|
| `url` key missing or value is `null`/`""` | Skip entry; increment `invalid`; print warning to stderr |
| `tags` key missing | Treat as `[]` (lenient) |
| `title` key missing | Treat as `null` (lenient) |
| `created_at`/`updated_at` missing | Use current UTC time |
| `created_at`/`updated_at` present but not parseable as ISO 8601 | Use current UTC time; no error |

---

## `jsonport` Module

### Location

`src/bookmarkcli/jsonport.py`

### Public API

```python
from bookmarkcli.jsonport import (
    bookmarks_to_json,   # list[Bookmark] → JSON string
    import_from_json,    # JSON string × BookmarkStore × policy → ImportResult
    ImportResult,        # dataclass (see above)
)
```

#### `bookmarks_to_json(bookmarks: list[Bookmark], indent: int = 2) -> str`

Serialises a list of `Bookmark` objects to a JSON string using the export document format.

- `id` is excluded.
- `tags` serialised as a JSON array.
- `created_at` / `updated_at` serialised as ISO 8601 strings (`dt.isoformat()`).
- `title` serialised as `null` when `None`.
- Returns `'{"bookmarks": []}'\n` (with trailing newline) when `bookmarks` is empty.

#### `import_from_json(json_str: str, store: BookmarkStore, on_duplicate: str = "skip") -> ImportResult`

Parses a JSON string and imports valid entries into `store`.

**Parameters**:

| Parameter | Type | Description |
|---|---|---|
| `json_str` | `str` | The raw JSON document string |
| `store` | `BookmarkStore` | An **initialised** store instance |
| `on_duplicate` | `"skip"` \| `"update"` | Duplicate handling policy (default: `"skip"`) |

**Behaviour**:
1. Parse `json_str` with `json.loads()`. Raises `json.JSONDecodeError` on invalid JSON (caller handles).
2. Extract the `"bookmarks"` array. Raises `KeyError` if missing (caller handles).
3. Load all existing bookmarks from `store.list_all()` into `dict[str, Bookmark]` keyed by URL.
4. Track seen URLs within this run in a `set[str]`.
5. For each entry in the array:
   - If `url` is missing/empty → increment `invalid`, print warning, continue.
   - If URL is in `existing_urls` or `seen_this_run`:
     - `on_duplicate="skip"` → increment `skipped`, continue.
     - `on_duplicate="update"` → `store.update(existing.id, title=..., tags=...)`, increment `updated`.
   - Otherwise → `store.create(url=..., title=..., tags=...)`, increment `added`.
   - Add URL to `seen_this_run`.
6. Return `ImportResult`.

**Raises** (caller converts to CLI error):
- `json.JSONDecodeError` — unparseable JSON.
- `ValueError` — document is valid JSON but not an object with a `"bookmarks"` array.

---

## Module Layout

```text
src/bookmarkcli/
├── cli.py          — existing; new `export` and `import` Click commands added
├── models.py       — existing; unchanged
├── store.py        — existing; unchanged
└── jsonport.py     — NEW

tests/
├── test_store.py       — existing; unchanged
└── test_jsonport.py    — NEW; covers jsonport unit tests and CLI integration tests
```

---

## State Transitions

```
Export:
  store.list_all()
    └──[list[Bookmark]]──► bookmarks_to_json()
                               └──[JSON str]──► stdout or file

Import:
  file or stdin
    └──[JSON str]──► import_from_json(store, on_duplicate)
                         ├── store.list_all()        [read existing]
                         ├── store.create(...)       [new entries]
                         ├── store.update(id, ...)   [on_duplicate=update]
                         └──[ImportResult]──► CLI summary
```
