# Quickstart: Add & Delete Commands

**Feature**: 001-add-delete-commands  
**Last updated**: 2026-03-07

---

## Prerequisites

- Python ≥ 3.11 installed and on `PATH`
- [`uv`](https://docs.astral.sh/uv/) installed
- Repository cloned and on branch `001-add-delete-commands` (or merged into `main`)
- S01 (002-data-model-storage) complete — `src/bookmarkcli/store.py` must be present

---

## 1. Install Dependencies

```bash
uv sync
```

No new runtime dependencies are introduced. All additions use Python stdlib (`urllib.parse`) and existing dependencies (`click`, `sqlite3`).

---

## 2. Verify the CLI Entry Point

```bash
uv run bookmarkcli --help
```

Expected output (after this feature is implemented):

```
Usage: bookmarkcli [OPTIONS] COMMAND [ARGS]...

  Bookmark manager CLI.

Commands:
  add     Add a new bookmark.
  delete  Delete a bookmark by ID or URL.

Options:
  --help  Show this message and exit.
```

---

## 3. Run the Test Suite

```bash
uv run pytest -q
```

All existing store tests plus the new CLI tests should pass:

```
........                  [100%]
8 passed in 0.XXs
```

---

## 4. Manual Smoke Test

The smoke test uses a temporary database to avoid touching real user data.

```bash
export BOOKMARKCLI_DB=/tmp/bm-smoke.db
```

### 4a. Add a bookmark (minimal)

```bash
uv run bookmarkcli add https://example.com
```

Expected:
```
✓ Bookmark #1 added: https://example.com
```

### 4b. Add a bookmark with title and tags

```bash
uv run bookmarkcli add https://python.org --title "Python" --tags "lang,docs"
```

Expected:
```
✓ Bookmark #2 added: https://python.org
```

### 4c. Reject a duplicate URL

```bash
uv run bookmarkcli add https://example.com
echo "Exit code: $?"
```

Expected:
```
Error: A bookmark with this URL already exists (id=1).
Exit code: 1
```

### 4d. Reject an invalid URL

```bash
uv run bookmarkcli add not-a-url
echo "Exit code: $?"
```

Expected:
```
Error: "not-a-url" is not a valid URL. URLs must include a scheme (e.g., https://) and a host.
Exit code: 1
```

### 4e. Delete by ID (confirm)

```bash
echo y | uv run bookmarkcli delete 1
echo "Exit code: $?"
```

Expected:
```
  ID   : 1
  URL  : https://example.com
  Title: (none)
Delete this bookmark? [y/N]: y
✓ Bookmark #1 deleted.
Exit code: 0
```

### 4f. Delete by ID (cancel)

```bash
echo n | uv run bookmarkcli delete 2
echo "Exit code: $?"
```

Expected:
```
  ID   : 2
  URL  : https://python.org
  Title: Python
Delete this bookmark? [y/N]: n
Cancelled.
Exit code: 0
```

### 4g. Delete by URL

```bash
# Re-add example.com first
uv run bookmarkcli add https://example.com
echo y | uv run bookmarkcli delete https://example.com
```

Expected:
```
✓ Bookmark #3 added: https://example.com
  ID   : 3
  URL  : https://example.com
  Title: (none)
Delete this bookmark? [y/N]: y
✓ Bookmark #3 deleted.
```

### 4h. Delete not found

```bash
uv run bookmarkcli delete 9999
echo "Exit code: $?"
```

Expected:
```
Error: No bookmark found for '9999'.
Exit code: 1
```

### 4i. Clean up

```bash
unset BOOKMARKCLI_DB
rm -f /tmp/bm-smoke.db
```

---

## 5. Environment Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `BOOKMARKCLI_DB` | Path to the SQLite database file | `~/.bookmarkcli/bookmarks.db` |
