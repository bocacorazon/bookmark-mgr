# Python API Contract: bookmarkcli Storage Layer

**Feature**: 002-data-model-storage  
**Date**: 2026-03-07  
**Module**: `bookmarkcli.models`, `bookmarkcli.store`  
**Version**: 0.2.0

---

## Overview

This document defines the public Python API contract for the `bookmarkcli` storage layer. The storage layer is an internal library consumed by the CLI layer and future tooling. Callers depend on the interfaces described here; implementation details (SQL, serialisation) are **not** part of the contract.

---

## Public Symbols

All symbols listed below are importable from their respective module. Anything not listed is considered private and subject to change without notice.

---

### Module `bookmarkcli.models`

#### Class `Bookmark`

```python
@dataclass
class Bookmark:
    id: int | None
    url: str
    created_at: datetime          # UTC-aware datetime
    updated_at: datetime          # UTC-aware datetime
    title: str | None = None
    tags: list[str] = field(default_factory=list)
```

**Invariants**:
- `id` is `None` only before the record is persisted; after `BookmarkStore.create()` returns, `id` is a positive integer.
- `created_at` and `updated_at` are always timezone-aware `datetime` values in UTC.
- `tags` is never `None`; the absent-tags state is represented as `[]`.

**Mutability**: All fields are mutable in Python, but callers MUST NOT mutate `id` or `created_at` on a persisted instance. `updated_at` is managed exclusively by `BookmarkStore`.

---

#### Class `BookmarkNotFoundError`

```python
class BookmarkNotFoundError(Exception):
    ...
```

Raised by `BookmarkStore.get()`, `BookmarkStore.update()`, and `BookmarkStore.delete()` when the requested `bookmark_id` does not correspond to any stored record.

```python
# Example
try:
    store.get(999)
except BookmarkNotFoundError as exc:
    print(exc)  # "Bookmark 999 not found"
```

---

#### Class `BookmarkValidationError`

```python
class BookmarkValidationError(Exception):
    ...
```

Raised by `BookmarkStore.create()` when `url` is absent, `None`, or an empty/whitespace-only string.

```python
# Example
try:
    store.create(url="")
except BookmarkValidationError as exc:
    print(exc)  # "url must not be empty"
```

---

#### Sentinel `MISSING`

```python
MISSING: _MISSING_TYPE
```

Module-level sentinel used as the default value for optional `update()` parameters. Callers SHOULD import `MISSING` if they need to call `update()` without a particular field.

```python
# Only update tags, leave title unchanged
store.update(bookmark_id=1, tags=["python"])

# Explicitly clear title
store.update(bookmark_id=1, title=None)
```

---

### Module `bookmarkcli.store`

#### Class `BookmarkStore`

```python
class BookmarkStore:
    def __init__(self, db_path: str | Path) -> None: ...
    def initialize(self) -> None: ...
    def create(self, url: str, title: str | None = None, tags: list[str] | None = None) -> Bookmark: ...
    def get(self, bookmark_id: int) -> Bookmark: ...
    def list_all(self) -> list[Bookmark]: ...
    def update(self, bookmark_id: int, title: str | None | _MISSING_TYPE = MISSING, tags: list[str] | _MISSING_TYPE = MISSING) -> Bookmark: ...
    def delete(self, bookmark_id: int) -> None: ...
```

---

#### `BookmarkStore.__init__(db_path)`

| Parameter | Type | Description |
|-----------|------|-------------|
| `db_path` | `str \| Path` | File system path for the SQLite database file. Created automatically on `initialize()` if absent. |

Does **not** open a database connection. Construction is always safe.

---

#### `BookmarkStore.initialize()`

```python
def initialize(self) -> None
```

- Opens the SQLite file (creating it if absent).
- Applies all pending schema migrations up to the current version.
- Must be called before any CRUD method.
- Safe to call multiple times (idempotent).
- Raises `sqlite3.OperationalError` if the file path is not writable.

---

#### `BookmarkStore.create(url, title, tags)`

```python
def create(
    self,
    url: str,
    title: str | None = None,
    tags: list[str] | None = None,
) -> Bookmark
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | `str` | ✅ | The web address to bookmark. Must be non-empty. |
| `title` | `str \| None` | ❌ | Human-readable label. `None` if omitted. |
| `tags` | `list[str] \| None` | ❌ | Classification labels. `None` treated as empty list. |

**Returns**: The newly created `Bookmark` with a populated `id`, `created_at`, and `updated_at`.

**Raises**:
- `BookmarkValidationError` — `url` is empty or whitespace-only.

**Side effects**: Inserts one row into the database.

---

#### `BookmarkStore.get(bookmark_id)`

```python
def get(self, bookmark_id: int) -> Bookmark
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `bookmark_id` | `int` | ID of the record to retrieve. |

**Returns**: The `Bookmark` with the given `id`, all fields populated.

**Raises**:
- `BookmarkNotFoundError` — no record with `bookmark_id` exists.

---

#### `BookmarkStore.list_all()`

```python
def list_all(self) -> list[Bookmark]
```

**Returns**: A list of all `Bookmark` records, ordered by `id` ascending. Returns `[]` when the store is empty.

---

#### `BookmarkStore.update(bookmark_id, title, tags)`

```python
def update(
    self,
    bookmark_id: int,
    title: str | None | _MISSING_TYPE = MISSING,
    tags: list[str] | _MISSING_TYPE = MISSING,
) -> Bookmark
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bookmark_id` | `int` | — | ID of the record to update. |
| `title` | `str \| None \| MISSING` | `MISSING` | New title. Pass `None` to clear. Omit (leave as `MISSING`) to leave unchanged. |
| `tags` | `list[str] \| MISSING` | `MISSING` | New tag list. Pass `[]` to clear all tags. Omit to leave unchanged. |

**Returns**: The updated `Bookmark` with the refreshed `updated_at` timestamp.

**Raises**:
- `BookmarkNotFoundError` — no record with `bookmark_id` exists.

**Behaviour when no data fields change**: `updated_at` is still refreshed. The operation always succeeds.

---

#### `BookmarkStore.delete(bookmark_id)`

```python
def delete(self, bookmark_id: int) -> None
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `bookmark_id` | `int` | ID of the record to delete. |

**Returns**: `None`.

**Raises**:
- `BookmarkNotFoundError` — no record with `bookmark_id` exists.

**Side effects**: Permanently removes one row from the database.

---

## Exit / Error Summary

| Situation | Exception | HTTP analogy |
|-----------|-----------|--------------|
| Record not found (get/update/delete) | `BookmarkNotFoundError` | 404 Not Found |
| Invalid input on create (empty url) | `BookmarkValidationError` | 422 Unprocessable Entity |
| Database I/O failure | `sqlite3.OperationalError` (propagated) | 500 Internal Error |

---

## Typical Usage

```python
from pathlib import Path
from bookmarkcli.store import BookmarkStore
from bookmarkcli.models import BookmarkNotFoundError, BookmarkValidationError

store = BookmarkStore(db_path=Path("~/.bookmarks.db").expanduser())
store.initialize()

# Create
bm = store.create(url="https://example.com", title="Example", tags=["demo"])
print(bm.id)          # e.g. 1
print(bm.tags)        # ['demo']

# Read
bm = store.get(bm.id)

# List
all_bms = store.list_all()

# Update
bm = store.update(bm.id, title="New Title")

# Delete
store.delete(bm.id)

# Not found
try:
    store.get(9999)
except BookmarkNotFoundError:
    print("not found")
```

---

## Stability Guarantees

| Symbol | Status |
|--------|--------|
| `Bookmark` dataclass fields | **Stable** from 002 |
| `BookmarkNotFoundError` | **Stable** from 002 |
| `BookmarkValidationError` | **Stable** from 002 |
| `MISSING` sentinel | **Stable** from 002 |
| `BookmarkStore` public methods | **Stable** from 002 |
| SQLite schema version `1` | **Stable** — future migrations are additive |
| Internal SQL / serialisation | **Private** — may change |
