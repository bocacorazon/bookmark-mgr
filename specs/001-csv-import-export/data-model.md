# Data Model: CSV Import/Export

**Branch**: `001-csv-import-export` | **Date**: 2026-03-07

## Existing Domain Entity (unchanged)

### `Bookmark` _(src/bookmarkcli/models.py)_

| Field | Type | Nullable | Notes |
|-------|------|----------|-------|
| `id` | `int \| None` | yes (None before insert) | SQLite AUTOINCREMENT |
| `url` | `str` | no | Required; validated non-empty |
| `title` | `str \| None` | yes | Optional display name |
| `tags` | `list[str]` | no (empty list) | Stored as comma-separated in DB |
| `created_at` | `datetime` | no | UTC timezone-aware |
| `updated_at` | `datetime` | no | UTC timezone-aware; set to now on every write |

## New Domain Entities (src/bookmarkcli/models.py additions)

### `SkippedRow`

Represents a single row that was rejected during import.

| Field | Type | Nullable | Notes |
|-------|------|----------|-------|
| `row_number` | `int` | no | 1-based, counting only data rows (header excluded) |
| `reason` | `str` | no | Human-readable explanation, e.g. `"url is missing"`, `"created_at cannot be parsed: '2025-99-99'"` |

### `ImportResult`

Aggregates the outcome of a completed import operation.

| Field | Type | Nullable | Notes |
|-------|------|----------|-------|
| `imported` | `int` | no | Count of rows successfully added to the store |
| `skipped` | `int` | no | Count of rows that were rejected |
| `skipped_rows` | `list[SkippedRow]` | no (empty list) | Detail for each rejected row |

**Invariant**: `imported + skipped == total data rows processed`

---

## CSV Record Schema

The CSV format is the external representation of a `Bookmark`. It is **not** a Python class; it is the wire format for import and export.

| Column | Required | Type | Notes |
|--------|----------|------|-------|
| `url` | **yes** | string | Must be non-empty; absence or blank → skip row (FR-011) |
| `title` | no | string | Empty string treated as `None` on import |
| `tags` | no | string | Semicolons separate multiple tags, e.g. `python;dev`; empty segments silently dropped (FR-008) |
| `created_at` | no | ISO 8601 string | `datetime.fromisoformat()` used for parsing; unparseable value → skip row (FR-012); absent/empty → use current time (FR-010) |

**Column order** (header row): `url`, `title`, `tags`, `created_at`  
**Encoding**: UTF-8  
**Line endings**: CRLF or LF accepted on import; LF used on export (Python default)  
**Quoting**: RFC 4180 — fields with commas, double-quotes, or newlines are quoted; double-quote escaped by doubling

---

## Validation Rules

| Rule | Entity | Behaviour |
|------|--------|-----------|
| `url` absent or blank | CSV Record (import) | Skip row; append `SkippedRow(reason="url is missing or blank")` |
| `created_at` present but not ISO 8601 | CSV Record (import) | Skip row; append `SkippedRow(reason="created_at cannot be parsed: '<value>'")` |
| Extra/unknown columns | CSV Record (import) | Silently ignored (FR-013) |
| Header row absent | CSV file (import) | Error: "CSV file must have a header row with at least a 'url' column"; exit non-zero |
| Zero successful imports | `ImportResult` | Command exits with non-zero status code (FR-015) |
| File not found / not readable | Import FILE arg | Click handles automatically via `click.Path(exists=True)` (FR-016) |
| File path not writable | Export `--file` | Click handles automatically via `click.Path(writable=True)` (FR-016) |

---

## State Transitions

Import is a write-only operation on the store. There are no state machines; each valid row triggers a single `BookmarkStore.create()` call. `updated_at` is set to `now` by the store (existing behaviour).

```
CSV Row (valid)
  → BookmarkStore.create(url, title, tags, created_at=parsed_dt)
  → Bookmark persisted in SQLite

CSV Row (malformed)
  → SkippedRow appended to ImportResult
  → No store mutation
```
