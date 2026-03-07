# Data Model: Tag Management

**Feature**: 004-tag-management  
**Date**: 2026-03-07

---

## Scope

This feature extends the existing domain and persistence layers to support tag management on `Bookmark` records. No schema migration is required — the `tags` TEXT column already exists on the `bookmarks` table (schema version 1, from S02).

Changes:

1. **`models.py`**: add `normalize_tag()`, `TagNotFoundError`, `TagValidationError`.
2. **`store.py`**: add `add_tag()`, `remove_tag()`, `list_tags()` to `BookmarkStore`.

---

## Domain Additions

### Function `normalize_tag()`

```python
# models.py
def normalize_tag(tag: str) -> str:
    """Return tag stripped of surrounding whitespace and converted to lowercase."""
    return tag.strip().lower()
```

**Invariants**:
- Input: any `str`.
- Output: leading/trailing whitespace removed; all ASCII letters lowercased.
- An all-whitespace input normalizes to `""` (the caller must then reject it).

| Input         | Output      |
|---------------|-------------|
| `"Python"`    | `"python"`  |
| `"  web  "`   | `"web"`     |
| `"TUTORIAL"`  | `"tutorial"`|
| `"my-tag_1"`  | `"my-tag_1"`|
| `"   "`       | `""`        |

---

### Class `TagNotFoundError`

```python
class TagNotFoundError(Exception):
    """Raised when attempting to remove a tag not present on a bookmark."""
```

Raised by `BookmarkStore.remove_tag()` when the normalized tag does not appear in the bookmark's current tag list.

```python
# Example
try:
    store.remove_tag(5, "java")
except TagNotFoundError as exc:
    print(exc)  # "Tag 'java' not found on bookmark 5"
```

---

### Class `TagValidationError`

```python
class TagValidationError(Exception):
    """Raised when a tag value is empty or all-whitespace after normalization."""
```

Raised by `BookmarkStore.add_tag()` and `BookmarkStore.remove_tag()` when the tag reduces to an empty string after normalization.

```python
# Example
try:
    store.add_tag(5, "   ")
except TagValidationError as exc:
    print(exc)  # "Tag must not be empty or whitespace"
```

---

## `BookmarkStore` Extensions

### Method: `add_tag()`

```python
def add_tag(self, bookmark_id: int, tag: str) -> Bookmark
```

- Normalizes `tag` via `normalize_tag()`.
- Raises `TagValidationError` if the normalized tag is empty.
- Raises `BookmarkNotFoundError` if `bookmark_id` does not exist.
- If the normalized tag is already present on the bookmark: **no-op** (idempotent).
- Otherwise appends the normalized tag to the bookmark's tag list and calls `update()` to persist.
- Returns the (possibly unchanged) `Bookmark`.

**Post-condition**: `normalize_tag(tag) in store.get(bookmark_id).tags` is `True`.

---

### Method: `remove_tag()`

```python
def remove_tag(self, bookmark_id: int, tag: str) -> Bookmark
```

- Normalizes `tag` via `normalize_tag()`.
- Raises `TagValidationError` if the normalized tag is empty.
- Raises `BookmarkNotFoundError` if `bookmark_id` does not exist.
- Raises `TagNotFoundError` if the normalized tag is not in the bookmark's current tag list.
- Removes the tag and calls `update()` to persist.
- Returns the updated `Bookmark`.

**Post-condition**: `normalize_tag(tag) not in store.get(bookmark_id).tags` is `True`.

---

### Method: `list_tags()`

```python
def list_tags(self) -> list[tuple[str, int]]
```

- Reads all `tags` column values from `bookmarks` (skips empty-string rows).
- Parses each via `_deserialize_tags()`.
- Counts the number of distinct bookmarks carrying each tag.
- Returns a list of `(tag, count)` tuples sorted ascending by tag name.
- Returns `[]` when no bookmarks have any tags.

**Example**:

```python
# Three bookmarks: {python}, {python, web}, {web}
store.list_tags()
# → [("python", 2), ("web", 2)]
```

---

## Exception Hierarchy

```text
Exception
├── BookmarkNotFoundError    # existing — bookmark ID not found
├── BookmarkValidationError  # existing — URL empty on create
├── TagNotFoundError         # NEW — tag not on bookmark during remove
└── TagValidationError       # NEW — empty/whitespace tag value
```

---

## Validation Rules

| Input | Rule | Error raised |
|-------|------|--------------|
| `tag` | After `normalize_tag()`, must be non-empty | `TagValidationError` |
| `bookmark_id` (add/remove) | Must resolve to an existing row | `BookmarkNotFoundError` |
| `tag` (remove) | Must be present in bookmark's current tag list | `TagNotFoundError` |

---

## No Schema Changes

The existing `bookmarks` table (schema version 1) is fully sufficient.

| Table | Column | Change |
|-------|--------|--------|
| `bookmarks` | `tags TEXT NOT NULL DEFAULT ''` | None — existing column reused |

---

## Module Layout

```text
src/bookmarkcli/
├── models.py   — + normalize_tag(), TagNotFoundError, TagValidationError
└── store.py    — + add_tag(), remove_tag(), list_tags()

tests/
├── test_store.py  — + tests for add_tag, remove_tag, list_tags
└── test_cli.py    — NEW — tests for `tag` and `tags` CLI commands
```
