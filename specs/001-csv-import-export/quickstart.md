# Quickstart: CSV Import/Export

**Branch**: `001-csv-import-export`

## Prerequisites

- Python ≥ 3.11
- `uv` package manager

```bash
uv sync          # install / sync all dependencies
```

No new runtime dependencies are required. The feature uses Python's stdlib `csv` module.

---

## Export Bookmarks

### Write CSV to stdout

```bash
bookmarkcli export --format csv
```

Example output:
```
url,title,tags,created_at
https://example.com,Example Site,python;dev,2025-01-15T10:30:00+00:00
https://other.org,Other,,2025-03-01T08:00:00+00:00
```

### Write CSV to a file

```bash
bookmarkcli export --format csv --file bookmarks.csv
```

The file is created (or overwritten) at the given path. Command exits 0 on success.

### Empty store

```bash
bookmarkcli export --format csv
# Output: url,title,tags,created_at
# Exit code: 0
```

---

## Import Bookmarks

### Import from a CSV file

```bash
bookmarkcli import --format csv bookmarks.csv
```

Example output:
```
Imported 3, skipped 0
```

### Partial import (malformed rows)

```bash
bookmarkcli import --format csv messy.csv
# Output:
# Imported 5, skipped 2
#   Row 3: url is missing or blank
#   Row 7: created_at cannot be parsed: '2025-99-99T00:00:00'
# Exit code: 0
```

### All rows malformed

```bash
bookmarkcli import --format csv broken.csv
# Output:
# Imported 0, skipped 4
#   Row 1: url is missing or blank
#   ...
# Exit code: 1
```

---

## CSV Format Reference

| Column | Required | Example |
|--------|----------|---------|
| `url` | **yes** | `https://example.com` |
| `title` | no | `My Bookmark` |
| `tags` | no | `python;dev;tools` |
| `created_at` | no | `2025-01-15T10:30:00+00:00` |

- **Tags**: semicolon-separated; empty segments are ignored
- **`created_at`**: ISO 8601 format; omit or leave blank to use the current time
- **Extra columns**: silently ignored
- **Header row**: required; must contain at minimum a `url` column

---

## Running Tests

```bash
uv run pytest -q
```

CSV-specific tests live in:
- `tests/test_csv_io.py` — unit tests for `csv_io.py` helpers
- `tests/test_cli.py` — CLI-level integration tests for `export` and `import`

---

## Implementation Files

| File | Role |
|------|------|
| `src/bookmarkcli/csv_io.py` | Pure CSV read/write helpers (no Click dependency) |
| `src/bookmarkcli/models.py` | Extended with `SkippedRow` and `ImportResult` dataclasses |
| `src/bookmarkcli/cli.py` | `export` and `import` Click commands wired to `csv_io.py` |
