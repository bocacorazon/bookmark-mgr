# Data Model: Data Model & Storage

**Feature**: 002-data-model-storage  
**Date**: 2026-03-07

---

## Scope

This feature introduces the persistence layer for the `bookmarkcli` application. It defines:

1. The **`Bookmark`** domain entity (pure Python dataclass).
2. The **`BookmarkNotFoundError`** and **`BookmarkValidationError`** exceptions.
3. The **`BookmarkStore`** class that owns all SQLite interaction.

No new CLI subcommands are added in this feature; those depend on this storage layer and arrive in a subsequent spec.

---

## Entities

### `Bookmark`

Represents a saved reference to a web resource.

| Field        | Python Type        | SQLite Column     | Constraints                              |
|--------------|--------------------|-------------------|------------------------------------------|
| `id`         | `int \| None`      | `INTEGER PK AUTOINCREMENT` | `None` before insertion; immutable after |
| `url`        | `str`              | `TEXT NOT NULL`   | Non-empty; required for creation         |
| `title`      | `str \| None`      | `TEXT`            | Optional; `NULL` stored as `None`        |
| `tags`       | `list[str]`        | `TEXT`            | Serialised as comma-separated string; empty list ↔ `""` |
| `created_at` | `datetime` (UTC)   | `TEXT` (ISO 8601) | Set automatically at creation; immutable |
| `updated_at` | `datetime` (UTC)   | `TEXT` (ISO 8601) | Set automatically at creation; refreshed on every update |

**Python declaration** (`src/bookmarkcli/models.py`):

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Bookmark:
    id: int | None
    url: str
    created_at: datetime
    updated_at: datetime
    title: str | None = None
    tags: list[str] = field(default_factory=list)
```

---

## Exceptions

Both exceptions live in `src/bookmarkcli/models.py` and are part of the public API.

| Exception                  | Raised when                                           | Spec ref |
|----------------------------|-------------------------------------------------------|----------|
| `BookmarkNotFoundError`    | `get`, `update`, or `delete` called with unknown `id` | FR-013   |
| `BookmarkValidationError`  | `create` called with absent or empty `url`            | FR-005   |

---

## `BookmarkStore`

The data-access object responsible for all SQLite interaction.

### Constructor

```python
BookmarkStore(db_path: str | Path)
```

- `db_path`: path to the SQLite file; created automatically if it does not exist.
- Does **not** open a database connection on construction; call `initialize()` before any CRUD operation.

### Method: `initialize()`

```python
def initialize(self) -> None
```

- Opens (or creates) the SQLite file at `db_path`.
- Reads `PRAGMA user_version`.
- Applies any pending migrations in order (version 0 → 1, 1 → 2, …).
- On completion, `PRAGMA user_version` equals the current application schema version (`1`).
- Idempotent: safe to call multiple times.
- Satisfies FR-002, FR-003.

### Method: `create()`

```python
def create(
    self,
    url: str,
    title: str | None = None,
    tags: list[str] | None = None,
) -> Bookmark
```

- Validates that `url` is non-empty; raises `BookmarkValidationError` otherwise.
- Inserts a new row; sets `created_at` and `updated_at` to the current UTC time.
- Returns the newly created `Bookmark` with its assigned `id`.
- Satisfies FR-004, FR-005, FR-006, FR-007.

### Method: `get()`

```python
def get(self, bookmark_id: int) -> Bookmark
```

- Returns the `Bookmark` with the given `id`.
- Raises `BookmarkNotFoundError` if no matching record exists.
- Satisfies FR-009, FR-013.

### Method: `list_all()`

```python
def list_all(self) -> list[Bookmark]
```

- Returns all `Bookmark` records ordered by `id` ascending.
- Returns an empty list when the store is empty.
- Satisfies FR-010.

### Method: `update()`

```python
def update(
    self,
    bookmark_id: int,
    title: str | None | _MISSING_TYPE = MISSING,
    tags: list[str] | _MISSING_TYPE = MISSING,
) -> Bookmark
```

- Only fields explicitly passed (not `MISSING`) are written; other fields remain unchanged.
- Always refreshes `updated_at` regardless of whether any data field changed.
- Raises `BookmarkNotFoundError` if no matching record exists.
- Satisfies FR-008, FR-011, FR-013.

### Method: `delete()`

```python
def delete(self, bookmark_id: int) -> None
```

- Permanently removes the record with the given `id`.
- Raises `BookmarkNotFoundError` if no matching record exists.
- Satisfies FR-012, FR-013.

---

## SQLite Schema

### Version 1 (initial, migration 0 → 1)

```sql
CREATE TABLE IF NOT EXISTS bookmarks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    url        TEXT    NOT NULL,
    title      TEXT,
    tags       TEXT    NOT NULL DEFAULT '',
    created_at TEXT    NOT NULL,
    updated_at TEXT    NOT NULL
);
```

### Migration ladder

| From version | To version | SQL applied                                  |
|-------------|-----------|----------------------------------------------|
| 0           | 1         | `CREATE TABLE bookmarks (…)` (initial schema)|

---

## Serialisation Rules

| Direction   | Field     | Transformation                                            |
|-------------|-----------|-----------------------------------------------------------|
| Write       | `tags`    | `",".join(tag.strip() for tag in tags)` (empty list → `""`) |
| Read        | `tags`    | `[t for t in stored.split(",") if t]` (empty string → `[]`) |
| Write       | timestamps| `dt.isoformat()` (always UTC)                             |
| Read        | timestamps| `datetime.fromisoformat(s).replace(tzinfo=timezone.utc)` |

---

## Validation Rules

| Field | Rule                                          | Error raised              |
|-------|-----------------------------------------------|---------------------------|
| `url` | Must be a non-empty string on `create()`     | `BookmarkValidationError` |
| `id`  | Must resolve to an existing row on get/update/delete | `BookmarkNotFoundError` |

---

## State Transitions

```
[absent]
   │  create(url, ...)
   ▼
[Bookmark(id=N, created_at=T₀, updated_at=T₀)]
   │  update(id=N, ...)
   ▼
[Bookmark(id=N, created_at=T₀, updated_at=T₁)]  (T₁ > T₀)
   │  delete(id=N)
   ▼
[absent]
```

---

## Module Layout

```text
src/bookmarkcli/
├── models.py   — Bookmark dataclass, MISSING sentinel, exception classes
└── store.py    — BookmarkStore, _MIGRATIONS list, serialisation helpers

tests/
└── test_store.py  — pytest suite (all CRUD paths, edge cases, migration)
```
