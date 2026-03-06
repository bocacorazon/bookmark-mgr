# Spec Prompt: CSV Import/Export

## Feature
**S06 — CSV Import/Export**: Implement commands to export and import bookmarks as CSV.

## Context
This is part of Track B (Import/Export). It builds on the `BookmarkStore` from S01.

## Scope

### In Scope
- `bookmark export --format csv [--file out.csv]`:
  - Export all bookmarks as CSV with headers: `url,title,tags,created_at,updated_at`.
  - Tags column uses semicolons as separator (e.g., `python;cli;tools`).
  - If `--file` is omitted, print to stdout.
  - Print count of exported bookmarks to stderr.
- `bookmark import --format csv <file>`:
  - Import bookmarks from a CSV file.
  - Map columns by header name (order-independent).
  - Handle duplicates: `--on-duplicate skip` (default) or `--on-duplicate update`.
  - Skip malformed rows with a warning (missing URL, parse errors).
  - Print import summary: added, skipped, updated, errors.
- Tests covering: export, import, round-trip, malformed rows, missing columns, encoding issues.

### Out of Scope
- JSON or HTML formats — those belong to S05, S07.

## Dependencies
- **S01**: `BookmarkStore` CRUD operations.

## Key Design Decisions
- Use Python's `csv` module (no external dependency).
- Tags use semicolons (not commas) to avoid CSV escaping issues.
- Header row is required for import.
