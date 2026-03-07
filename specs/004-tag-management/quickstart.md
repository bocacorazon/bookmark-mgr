# Quickstart: bookmarkcli Tag Management

**Feature**: 004-tag-management  
**Last updated**: 2026-03-07

---

## Prerequisites

- Python ≥ 3.11 on `PATH`
- [`uv`](https://docs.astral.sh/uv/) installed
- Repository cloned on branch `004-tag-management` (or merged into `main`)
- Features S02 (data model / storage) and S03 (CLI CRUD commands) already implemented

---

## 1. Install / Sync Dependencies

```bash
uv sync
```

No new runtime dependencies are introduced in this feature.

---

## 2. Verify the CLI Entry Point

```bash
uv run bookmarkcli --help
```

Expected output now includes `tag` and `tags` subcommands:

```
Usage: bookmarkcli [OPTIONS] COMMAND [ARGS]...

  Bookmark manager CLI.

Options:
  --help  Show this message and exit.

Commands:
  add     Add a new bookmark.
  delete  Delete a bookmark by ID.
  list    List all bookmarks.
  search  Search bookmarks by keyword.
  tag     Add or remove a tag on a bookmark.
  tags    List all tags with their bookmark counts.
```

---

## 3. Run the Test Suite

```bash
uv run pytest -q
```

Expected output:

```
........................................
N passed in X.XXs
```

---

## 4. Project Layout

```text
bookmark-mgr/
├── pyproject.toml
├── uv.lock
├── conftest.py
├── src/
│   └── bookmarkcli/
│       ├── __init__.py
│       ├── cli.py          # + tag, tags subcommands
│       ├── models.py       # + normalize_tag(), TagNotFoundError, TagValidationError
│       └── store.py        # + add_tag(), remove_tag(), list_tags()
└── tests/
    ├── __init__.py
    ├── test_store.py       # + tag store tests
    └── test_cli.py         # NEW — CLI tag tests
```

---

## 5. Usage Examples

### Add a tag

```bash
# Add a bookmark first (S03 `add` command)
uv run bookmarkcli add https://docs.python.org "Python Docs"

# Add a tag
uv run bookmarkcli tag 1 --add python
# Tagged bookmark 1 with 'python'.

uv run bookmarkcli tag 1 --add docs
# Tagged bookmark 1 with 'docs'.
```

### Tag normalization

```bash
uv run bookmarkcli tag 1 --add "  Python  "
# Tagged bookmark 1 with 'python'.

uv run bookmarkcli tag 1 --add PYTHON
# Bookmark 1 already has tag 'python'.
```

### Remove a tag

```bash
uv run bookmarkcli tag 1 --remove docs
# Removed tag 'docs' from bookmark 1.
```

### List all tags with counts

```bash
uv run bookmarkcli tags
# docs  2
# python  5
# tutorial  1
```

### Error cases

```bash
# Non-existent bookmark
uv run bookmarkcli tag 999 --add python
# Error: Bookmark 999 not found.

# Remove tag not on bookmark
uv run bookmarkcli tag 1 --remove java
# Error: Tag 'java' not found on bookmark 1.

# Empty tag
uv run bookmarkcli tag 1 --add "   "
# Error: Tag must not be empty or whitespace.

# Both flags
uv run bookmarkcli tag 1 --add python --remove docs
# Error: --add and --remove are mutually exclusive.

# No tags yet
uv run bookmarkcli tags
# No tags found.
```

---

## 6. Using the Store Layer Directly

```python
from pathlib import Path
from bookmarkcli.store import BookmarkStore
from bookmarkcli.models import TagNotFoundError, TagValidationError

store = BookmarkStore(db_path=Path("/tmp/bookmarks.db"))
store.initialize()

bm = store.create(url="https://example.com")

# Add a tag
updated = store.add_tag(bm.id, "python")
print(updated.tags)   # ['python']

# Idempotent add
store.add_tag(bm.id, "PYTHON")    # no-op; 'python' already present
store.add_tag(bm.id, " Python ")  # no-op

# Add another
store.add_tag(bm.id, "web")
print(store.get(bm.id).tags)  # ['python', 'web']

# Remove
store.remove_tag(bm.id, "python")
print(store.get(bm.id).tags)  # ['web']

# List all tags
print(store.list_tags())  # [('web', 1)]

# Validation errors
try:
    store.add_tag(bm.id, "   ")
except TagValidationError:
    print("Empty tag rejected")

try:
    store.remove_tag(bm.id, "java")
except TagNotFoundError:
    print("Tag not found on bookmark")
```

---

## 7. Common Commands

| Task | Command |
|------|---------|
| Install / sync deps | `uv sync` |
| Run CLI | `uv run bookmarkcli [ARGS]` |
| Run all tests | `uv run pytest -q` |
| Run tests verbosely | `uv run pytest -v` |
| Run tag-specific tests | `uv run pytest -v -k tag` |
| Run store tests only | `uv run pytest tests/test_store.py -v` |
| Run CLI tests only | `uv run pytest tests/test_cli.py -v` |
