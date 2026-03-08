# CLI Command Contracts: CSV Import/Export

**Branch**: `001-csv-import-export` | **Date**: 2026-03-07

These contracts define the command-line interface surface for the CSV Import/Export feature. They are the authoritative specification for CLI behaviour — tests and implementations must conform to these contracts.

---

## `bookmark export`

### Synopsis

```
bookmarkcli export --format csv [--file PATH]
```

### Options

| Option | Short | Type | Required | Default | Description |
|--------|-------|------|----------|---------|-------------|
| `--format` | | choice: `csv` | yes | — | Output format. Only `csv` is supported in this version. |
| `--file` | | PATH (writable file) | no | `None` (stdout) | Destination file path. If omitted, CSV is written to standard output. |

### Behaviour

1. Opens the bookmark store (path from app context / environment).
2. Reads all bookmarks via `BookmarkStore.list_all()`.
3. Writes a CSV to the destination (stdout or `--file` path):
   - First row: header `url,title,tags,created_at`
   - One data row per bookmark, tags semicolon-joined
   - `created_at` serialised as ISO 8601 (`.isoformat()`)
4. Exits with code **0** on success (including empty store — header only).
5. If `--file` already exists, **overwrites silently** (FR edge case).

### Exit Codes

| Code | Condition |
|------|-----------|
| 0 | Success (all bookmarks exported, or store empty) |
| 1 | File path is not writable / cannot be created |
| 2 | Click usage error (e.g., unknown option) |

### Example Invocations

```bash
# Write to stdout
bookmarkcli export --format csv

# Write to file
bookmarkcli export --format csv --file bookmarks.csv
```

### Stdout (success, 2 bookmarks)

```
url,title,tags,created_at
https://example.com,Example,python;dev,2025-01-15T10:30:00+00:00
https://other.org,Other,,2025-03-01T08:00:00+00:00
```

### Stderr (error)

```
Error: Could not open file 'read-only-dir/out.csv': Permission denied
```

---

## `bookmark import`

### Synopsis

```
bookmarkcli import --format csv FILE
```

### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `FILE` | PATH (exists, readable file) | yes | Path to the CSV file to import. |

### Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `--format` | choice: `csv` | yes | — | Input format. Only `csv` is supported in this version. |

### Behaviour

1. Opens `FILE` for reading (UTF-8).
2. Validates that a header row is present and contains the `url` column. If not → error, exit 1.
3. For each data row:
   a. Checks `url` is non-empty → skip if not.
   b. Parses `created_at` if present → skip if unparseable. Uses current time if absent/empty.
   c. Parses `tags` by splitting on `;`, dropping empty segments.
   d. Ignores any extra/unknown columns.
   e. Calls `BookmarkStore.create(url, title, tags, ...)`.
4. Prints a summary to **stdout**: `Imported N, skipped M`.
5. Exits **0** if at least one row was imported (or file had zero data rows).
6. Exits **1** if every data row was skipped (FR-015).

### Exit Codes

| Code | Condition |
|------|-----------|
| 0 | At least one row imported, or file contains no data rows (header only / empty) |
| 1 | FILE not found or not readable (handled by Click) |
| 1 | Header row missing or lacks `url` column |
| 1 | Every data row was malformed (zero imports) |
| 2 | Click usage error |

### Example Invocations

```bash
bookmarkcli import --format csv bookmarks.csv
```

### Stdout (success, mixed result)

```
Imported 5, skipped 2
  Row 3: url is missing or blank
  Row 7: created_at cannot be parsed: '2025-99-99T00:00:00'
```

### Stdout (all-malformed result)

```
Imported 0, skipped 4
  Row 1: url is missing or blank
  Row 2: url is missing or blank
  Row 3: created_at cannot be parsed: 'not-a-date'
  Row 4: url is missing or blank
```

### Stderr (header missing)

```
Error: CSV file must have a header row with at least a 'url' column.
```

### Stderr (file not found — Click default)

```
Error: Invalid value for 'FILE': Path 'missing.csv' does not exist.
```

---

## Forward Compatibility Note

Both commands use `--format csv`. This option is designed for future extensibility (e.g., `--format json`). Adding new format values is a non-breaking change; any unsupported format value produces a Click usage error.
