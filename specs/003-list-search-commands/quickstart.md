# Quickstart: List & Search Commands

## Prerequisites

- S01 (project scaffold) and S02 (data model & storage) are merged and available.
- `uv` is installed and dependencies are synced:

```bash
uv sync
```

---

## Running the Commands

### List All Bookmarks

```bash
uv run bookmarkcli list
```

Displays all stored bookmarks in a rich table (borders, colours) when run in a terminal:

```
 ID   Title                        URL                                       Tags           Date Added
 ──   ──────────────────────────   ───────────────────────────────────────   ────────────   ──────────────────
  1   GitHub CPython               https://github.com/python/cpython         python,dev     2026-03-07 12:00
  2   Rich Documentation           https://rich.readthedocs.io/              docs           2026-03-06 09:30
  3   Click Docs                   https://click.palletsprojects.com/        docs,python    2026-03-05 08:00
```

### Filter by Tag

```bash
uv run bookmarkcli list --tag python
```

Only bookmarks with the exact tag `python` are shown.

### Limit Results

```bash
uv run bookmarkcli list --limit 5
```

Shows at most 5 bookmarks (newest-first by default).

### Sort by Title

```bash
uv run bookmarkcli list --sort title
```

Results are alphabetically sorted by title.

### Combine Options

```bash
uv run bookmarkcli list --tag dev --limit 3 --sort title
```

Filters by `dev` tag, sorts alphabetically, then caps at 3 rows.

### Search Bookmarks

```bash
uv run bookmarkcli search github
```

Returns all bookmarks whose title or URL contains `"github"` (case-insensitive):

```
 ID   Title                        URL                                       Tags           Date Added
 ──   ──────────────────────────   ───────────────────────────────────────   ────────────   ──────────────────
  1   GitHub CPython               https://github.com/python/cpython         python,dev     2026-03-07 12:00
```

Matching text is **highlighted** in rich mode.

### Search with Special Characters

```bash
uv run bookmarkcli search "https://"
```

Special characters are treated as literals. No wildcard expansion.

### Force Plain-Text Output

```bash
uv run bookmarkcli list --plain
uv run bookmarkcli search python --plain
```

Outputs tab-separated rows with a header line — suitable for piping to `grep`, `awk`, or `cut`.

### Pipe to Unix Tools

```bash
# Plain text is used automatically when piped
uv run bookmarkcli list | grep "python"
uv run bookmarkcli search github | awk -F'\t' '{print $3}'  # print URL column
```

---

## Empty and Error States

| Scenario                         | Output                                         |
|----------------------------------|------------------------------------------------|
| No bookmarks in store            | `No bookmarks found.`                          |
| Tag matches nothing              | `No bookmarks found.`                          |
| Search query matches nothing     | `No bookmarks matched "your-query".`           |
| `--limit 0`                      | `Error: Invalid value for '--limit'...`        |
| `--limit abc`                    | `Error: Invalid value for '--limit'...`        |
| `--sort invalid`                 | `Error: Invalid value for '--sort'...`         |
| `bookmark search` (empty query)  | `Error: Missing argument 'QUERY'.`             |

---

## Running Tests

```bash
uv run pytest -q
```

All tests (store, formatter, CLI integration) run from the `tests/` directory. A zero-tests-collected run exits `0` via `conftest.py`.

---

## Environment

- **Database path**: Defaults to `~/.bookmarks.db`. Configurable via the `BOOKMARKCLI_DB` environment variable (exact mechanism defined in the CLI entry point).
- **Rich output**: Automatically enabled when stdout is a TTY. Override with `--plain`.
- **`NO_COLOR` env var**: Setting `NO_COLOR=1` suppresses colour output (respected by `rich` automatically).
