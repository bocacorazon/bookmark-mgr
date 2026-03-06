# Spec Prompt: JSON Import/Export

## Feature
**S05 — JSON Import/Export**: Implement commands to export and import bookmarks as JSON.

## Context
This is part of Track B (Import/Export). It builds on the `BookmarkStore` from S01.

## Scope

### In Scope
- `bookmark export --format json [--file out.json]`:
  - Export all bookmarks as a JSON array.
  - If `--file` is omitted, print to stdout.
  - Each bookmark object: `{"url": "...", "title": "...", "tags": [...], "created_at": "ISO8601", "updated_at": "ISO8601"}`.
  - Print count of exported bookmarks to stderr.
- `bookmark import --format json <file>`:
  - Import bookmarks from a JSON file.
  - Handle duplicates: `--on-duplicate skip` (default) or `--on-duplicate update`.
  - Validate each entry (URL required, skip malformed entries with warning).
  - Print import summary: added, skipped, updated, errors.
- Round-trip fidelity: export then import should produce identical data.
- Tests covering: export empty DB, export with data, import new, import duplicates (skip and update modes), malformed input.

### Out of Scope
- CSV or HTML formats — those belong to S06, S07.
- Filtering exports (export always exports all).

## Dependencies
- **S01**: `BookmarkStore` CRUD operations.

## Key Design Decisions
- JSON format uses ISO 8601 timestamps.
- `--on-duplicate skip` is the safe default.
- Malformed entries are skipped with a warning, not fatal.
