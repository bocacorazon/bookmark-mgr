# Quickstart: JSON Import/Export

**Feature**: 001-json-import-export  
**Date**: 2026-03-07

---

## Prerequisites

- `bookmark-mgr` installed (`uv sync` from repo root).
- A bookmark store with data (use `bookmarkcli add` to create bookmarks if needed).

---

## Export

### Export to a file

```bash
bookmarkcli export --format json --file ~/my-bookmarks.json
```

The file `~/my-bookmarks.json` is created (or overwritten) with all bookmarks:

```json
{
  "bookmarks": [
    {
      "url": "https://example.com",
      "title": "Example Site",
      "tags": ["web", "example"],
      "created_at": "2026-03-07T12:00:00+00:00",
      "updated_at": "2026-03-07T12:34:56+00:00"
    },
    {
      "url": "https://python.org",
      "title": null,
      "tags": [],
      "created_at": "2026-03-07T09:00:00+00:00",
      "updated_at": "2026-03-07T09:00:00+00:00"
    }
  ]
}
```

### Export to stdout

Omit `--file` to print to stdout (useful for inspection or piping):

```bash
bookmarkcli export --format json
```

Pipe to `jq` to count bookmarks:

```bash
bookmarkcli export --format json | jq '.bookmarks | length'
# 2
```

### Empty store

Export still produces valid JSON:

```bash
bookmarkcli export --format json
# {"bookmarks": []}
```

---

## Import

### Basic import (skip duplicates)

```bash
bookmarkcli import --format json ~/my-bookmarks.json
# Import complete: 2 added, 0 skipped, 0 updated, 0 invalid.
```

### Import with update on duplicates

If a URL already exists in the store, overwrite its title and tags:

```bash
bookmarkcli import --format json --on-duplicate update ~/my-bookmarks.json
# Import complete: 0 added, 0 skipped, 2 updated, 0 invalid.
```

### Mixed import (some new, some existing)

```bash
bookmarkcli import --format json ~/new-and-existing.json
# Import complete: 5 added, 3 skipped, 0 updated, 0 invalid.
```

---

## Round-Trip Example

Full backup and restore:

```bash
# 1. Export current store
bookmarkcli export --format json --file backup.json

# 2. (Simulating a fresh store or new machine)

# 3. Import from backup — restores all bookmarks with full content fidelity
bookmarkcli import --format json backup.json
# Import complete: N added, 0 skipped, 0 updated, 0 invalid.
```

After the import, every bookmark has the same URL, title, and tags as the original.

---

## Error Cases

### File not found

```bash
bookmarkcli import --format json missing.json
# Error: file not found: missing.json
# (exits with code 1)
```

### Invalid JSON

```bash
bookmarkcli import --format json broken.json
# Error: invalid JSON in broken.json
# (exits with code 1)
```

### Entry missing URL (partial failure — does not abort)

```bash
bookmarkcli import --format json partial.json
# Warning: skipping entry 3: missing url
# Import complete: 4 added, 0 skipped, 0 updated, 1 invalid.
```

---

## Validation

Run tests to confirm everything works end-to-end:

```bash
uv run pytest -q
```

All tests should pass, including the import/export integration tests in `tests/test_jsonport.py`.
