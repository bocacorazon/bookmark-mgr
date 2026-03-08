# Data Model: List & Search Commands

**Feature**: S03 — List & Search Commands  
**Branch**: `001-list-search`  
**Date**: 2026-03-08

---

## Entities

### Bookmark (existing — S01)

No schema changes required. All fields needed by this feature already exist.

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `id` | `int` | SQLite `AUTOINCREMENT` | Unique identifier |
| `url` | `str` | User input | Bookmark URL (required, non-empty) |
| `title` | `str \| None` | User input | Human-readable title (optional) |
| `tags` | `list[str]` | User input | Comma-serialized in DB; deserialized by `BookmarkStore` |
| `created_at` | `datetime` (UTC) | Auto-set on create | Creation timestamp |
| `updated_at` | `datetime` (UTC) | Auto-set on create/update | Last-modified timestamp |

**SQLite schema** (from S01 migration, no changes):
```sql
CREATE TABLE IF NOT EXISTS bookmarks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    url        TEXT    NOT NULL,
    title      TEXT,
    tags       TEXT    NOT NULL DEFAULT '',
    created_at TEXT    NOT NULL,
    updated_at TEXT    NOT NULL
)
```

---

## New Store Methods

### `BookmarkStore.list_filtered`

**Signature**:
```python
def list_filtered(
    self,
    tag: str | None = None,
    limit: int | None = None,
    sort: Literal["newest", "oldest"] = "newest",
) -> list[Bookmark]:
```

**Behavior**:
- Returns bookmarks ordered by `created_at DESC` (newest, default) or `ASC` (oldest).
- If `tag` is provided, only bookmarks whose tag list contains that exact tag are returned.
  - Tag matching uses exact comma-delimited containment: `INSTR(','||tags||',', ','||?||',') > 0`
  - e.g., tag `python` matches `python,cli` but NOT `micropython`.
- If `limit` is provided and `>= 1`, at most `limit` rows are returned. If `limit == 0`, zero rows are returned.
- Validation of `limit` (non-negative integer, non-numeric) is done at the CLI layer before calling this method.

**SQL pattern**:
```sql
SELECT id, url, title, tags, created_at, updated_at
FROM bookmarks
[WHERE INSTR(','||tags||',', ','||:tag||',') > 0]
ORDER BY created_at [DESC|ASC]
[LIMIT :limit]
```

---

### `BookmarkStore.search`

**Signature**:
```python
def search(self, query: str) -> list[Bookmark]:
```

**Behavior**:
- Returns all bookmarks where `query` appears as a case-insensitive substring of `title` OR `url`.
- Results ordered by `created_at DESC` (newest first, consistent default).
- Empty/blank `query` is rejected at the CLI layer before calling this method.

**SQL pattern**:
```sql
SELECT id, url, title, tags, created_at, updated_at
FROM bookmarks
WHERE LOWER(title) LIKE LOWER('%' || :q || '%')
   OR LOWER(url)   LIKE LOWER('%' || :q || '%')
ORDER BY created_at DESC
```

---

## New Module: `formatting.py`

Encapsulates all `rich`-dependent rendering. The CLI imports only from this module, keeping `rich` isolated.

### `render_bookmarks_table`

**Signature**:
```python
def render_bookmarks_table(bookmarks: list[Bookmark], file: IO[str] | None = None) -> None:
```

**Behavior**:
- Renders a table to `file` (defaults to `sys.stdout`).
- Auto-detects terminal vs pipe via `rich.console.Console` default behavior (`force_terminal` not set).
- Columns: ID, Title, URL, Tags, Created At.
- Long values (Title, URL) truncated with `…` at `max_width=40` (Title) and `max_width=50` (URL) for standard terminal widths.
- Tags displayed as comma-separated string.
- Dates formatted as `YYYY-MM-DD HH:MM` in UTC.

### `render_empty_state`

**Signature**:
```python
def render_empty_state(message: str, file: IO[str] | None = None) -> None:
```

**Behavior**:
- Prints a plain message (e.g., `"No bookmarks found."`) with dim styling in terminal mode; plain text in pipe mode.

---

## Validation Rules (CLI Layer)

| Input | Rule | Error |
|-------|------|-------|
| `--limit` value | Must be a non-negative integer. `0` returns empty. Negative or non-integer → error. | `"Invalid value for '--limit': N is not a valid integer."` (Click default) + custom: `"'--limit' must be 0 or a positive integer."` |
| `--sort` value | Must be `newest` or `oldest`. | `"Invalid value for '--sort': 'X' is not one of 'newest', 'oldest'."` (Click `Choice`) |
| `search` query | Must be non-empty and non-whitespace-only. | `"Error: search query cannot be empty. Usage: bookmark search <query>"` |

---

## State Transitions

No state transitions. Both commands are read-only queries — no mutations to the bookmark store.

---

## Relationships

```
CLI (cli.py)
  └── uses → BookmarkStore.list_filtered / BookmarkStore.search
  └── uses → formatting.render_bookmarks_table / render_empty_state

BookmarkStore (store.py)
  └── queries → bookmarks (SQLite table — S01 schema, unchanged)

formatting.py
  └── uses → rich.console.Console, rich.table.Table
  └── renders → Bookmark fields
```
