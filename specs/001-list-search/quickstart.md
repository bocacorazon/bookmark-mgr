# Quickstart: List & Search Commands

**Feature**: S03 — List & Search Commands  
**Branch**: `001-list-search`

---

## Prerequisites

- S01 (Bookmark storage foundation) must be complete.
- Python 3.11+ and `uv` installed.

## Setup

```bash
# Install dependencies (adds 'rich' as new runtime dependency)
uv sync
```

## Usage

### List all bookmarks

```bash
uv run bookmarkcli list
```

### Filter by tag

```bash
uv run bookmarkcli list --tag python
```

### Limit results and sort

```bash
uv run bookmarkcli list --limit 10 --sort newest
uv run bookmarkcli list --limit 10 --sort oldest
```

### Search by keyword (title or URL)

```bash
uv run bookmarkcli search python
uv run bookmarkcli search "docs.python"
```

### Plain-text output (pipe to a file or another command)

```bash
uv run bookmarkcli list | head -5
uv run bookmarkcli search python > results.txt
```

## Running Tests

```bash
uv run pytest -q
```

All tests should pass. New tests for this feature live in:
- `tests/test_store.py` — `list_filtered` and `search` method tests
- `tests/test_formatting.py` — table rendering unit tests
- `tests/test_cli.py` — Click `CliRunner` integration tests for `list` and `search`

## Example Session

```bash
# Add some bookmarks first (S01 feature)
uv run bookmarkcli add https://docs.python.org "Python Docs" --tag python --tag docs
uv run bookmarkcli add https://click.palletsprojects.com "Click Docs" --tag python --tag cli
uv run bookmarkcli add https://github.com "GitHub" --tag git

# List all
uv run bookmarkcli list

# Filter by tag
uv run bookmarkcli list --tag python

# Search
uv run bookmarkcli search python
uv run bookmarkcli search github.com

# List 2 most recent
uv run bookmarkcli list --limit 2 --sort newest
```

## Key Design Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Table rendering | `rich` library | Auto TTY detection, no extra flags needed |
| Tag matching | Exact (not substring) | `--tag py` does NOT match `python` (per spec assumptions) |
| Default sort | Newest first | FR-005 |
| Search scope | Title + URL | FR-006, FR-007 |
| Search type | Case-insensitive substring | Spec assumption, no stemming/ranking needed |
| `--limit 0` | Returns empty | Spec edge case: "show none" |
