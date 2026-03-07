# Data Model: Add & Delete Commands

**Feature**: 001-add-delete-commands  
**Date**: 2026-03-07

---

## Scope

This feature adds the CLI surface for adding and deleting bookmarks. It introduces:

1. A new **`DuplicateBookmarkError`** exception in `bookmarkcli.models`.
2. A new **`find_by_url()`** method on `BookmarkStore` in `bookmarkcli.store`.
3. Two new Click subcommands — **`add`** and **`delete`** — in `bookmarkcli.cli`.

No schema migrations are required; the SQLite schema from S01 (version 1) is sufficient.

---

## Entities

### No new domain entities

The `Bookmark` dataclass (defined in S01) is unchanged. This feature consumes it via the existing `BookmarkStore` API.

---

## New Exception: `DuplicateBookmarkError`

Added to `src/bookmarkcli/models.py`.

```python
class DuplicateBookmarkError(Exception):
    """Raised when attempting to add a URL that already exists in the store."""
```

| Exception | Raised when | FR ref |
|-----------|-------------|--------|
| `DuplicateBookmarkError` | `add` command finds an existing bookmark with the same URL | FR-005 |

**Note**: This exception is raised by the CLI layer (`cli.py`), not by `BookmarkStore.create()`. The store remains agnostic to duplication; the CLI queries `find_by_url()` before calling `create()`.

---

## Store Additions

### New method: `BookmarkStore.find_by_url()`

Added to `src/bookmarkcli/store.py`.

```python
def find_by_url(self, url: str) -> Bookmark | None:
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | `str` | Exact URL string to look up. |

**Returns**: The matching `Bookmark` if found; `None` otherwise.  
**Raises**: nothing (returns `None` for no-match).  
**Side effects**: Read-only SELECT query.

**SQL**:
```sql
SELECT id, url, title, tags, created_at, updated_at
FROM bookmarks
WHERE url = ?
```

**Behaviour notes**:
- Exact string match; no normalisation performed (consistent with spec assumption on URL uniqueness).
- Returns the first matching row (uniqueness enforced by application logic in `add` command, not a DB constraint in this spec).

---

## CLI Commands

### `bookmark add`

```
bookmark add <url> [--title TEXT] [--tags TEXT]
```

**Arguments / Options**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `url` | `str` (positional) | ✅ | The URL to bookmark. Must have scheme + host. |
| `--title TEXT` | `str` option | ❌ | Human-readable label. Stored as-is; `None` if omitted. |
| `--tags TEXT` | `str` option | ❌ | Comma-separated tag names. Whitespace around each tag is stripped. Empty/whitespace-only → no tags stored. |

**Processing flow**:

```
1. Validate URL format (scheme + netloc via urllib.parse)
   → invalid: print error, exit 1

2. call store.find_by_url(url)
   → found: print "Error: URL already exists (id=N)", exit 1

3. Parse --tags: split on ",", strip, drop empty
4. call store.create(url, title, parsed_tags)
5. Print: "✓ Bookmark #<id> added: <url>"
6. exit 0
```

**Output examples**:

```
# Success
✓ Bookmark #7 added: https://example.com

# Duplicate
Error: A bookmark with this URL already exists (id=3).

# Invalid URL
Error: "not-a-url" is not a valid URL. URLs must include a scheme (e.g., https://) and a host.
```

---

### `bookmark delete`

```
bookmark delete <id-or-url>
```

**Arguments**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `id-or-url` | `str` (positional) | ✅ | Numeric bookmark ID or full URL. Parsed as integer if possible; otherwise treated as URL. |

**Processing flow**:

```
1. Try int(arg):
   - success → store.get(id)  [raises BookmarkNotFoundError if missing]
   - ValueError → store.find_by_url(arg)  [None if missing]

2. If bookmark not found: print "Error: No bookmark found for '<arg>'", exit 1

3. Display bookmark details:
   ID   : <id>
   URL  : <url>
   Title: <title or "(none)">

4. click.confirm("Delete this bookmark?", default=False)
   - user enters n/N/Enter → print "Cancelled.", exit 0
   - user enters y/Y      → store.delete(bookmark.id)
                            print "✓ Bookmark #<id> deleted."
                            exit 0
```

**Output examples**:

```
# Prompt shown
  ID   : 7
  URL  : https://example.com
  Title: Example Site
Delete this bookmark? [y/N]:

# After 'y'
✓ Bookmark #7 deleted.

# After 'n' or Enter
Cancelled.

# Not found
Error: No bookmark found for '99'.
```

---

## Validation Rules

| Rule | Applies to | Condition | Error |
|------|-----------|-----------|-------|
| URL format | `add` | `urlparse(url).scheme` or `urlparse(url).netloc` is empty | Exit 1, message describing required format |
| Duplicate URL | `add` | `find_by_url(url)` returns non-None | Exit 1, include conflicting ID |
| Record existence | `delete` | `get(id)` raises `BookmarkNotFoundError` or `find_by_url` returns `None` | Exit 1, show argument |
| Confirmation required | `delete` | User must enter `y`/`Y` | Cancellation message, exit 0 |

---

## State Transitions

```
[absent]
   │  bookmark add <url>
   ▼
[Bookmark(id=N)]
   │  bookmark delete N  (confirmed)
   ▼
[absent]
```

No partial states: `add` is atomic (store.create) and `delete` is atomic (store.delete).

---

## Module Layout (additions in bold)

```text
src/bookmarkcli/
├── __init__.py          — unchanged
├── models.py            — + DuplicateBookmarkError
├── store.py             — + find_by_url()
└── cli.py               — + @main.command() add, + @main.command() delete

tests/
├── test_store.py        — + tests for find_by_url
└── test_cli.py          — new: tests for add and delete via Click CliRunner
```
