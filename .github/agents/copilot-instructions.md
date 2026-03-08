# S00 Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-07

## Active Technologies
- N/A for S00 (aiosqlite declared for future use, not exercised) (001-project-scaffold)
- N/A (SQLite via aiosqlite declared for future features; no schema in S00) (001-project-scaffold)
- Python ≥ 3.11 + `sqlite3` (stdlib) — no new runtime packages required; `pytest ≥ 8.0` (dev, already declared) (002-data-model-storage)
- SQLite (hard constraint per spec) — single-file database managed via stdlib `sqlite3` (002-data-model-storage)
- Python ≥ 3.11 + `click>=8.0` (existing), `sqlite3` stdlib (existing) — no new runtime packages (004-tag-management)
- SQLite via existing `BookmarkStore`; tags remain comma-separated in `bookmarks.tags` TEXT column (004-tag-management)
- Python 3.11 + Click 8.x (existing), Python stdlib `csv`, `datetime` (no new runtime deps) (001-csv-import-export)
- SQLite via existing `BookmarkStore` (`src/bookmarkcli/store.py`) (001-csv-import-export)
- Python 3.11+ + Click 8.x (existing), stdlib `json`, `pathlib`, `sys` (001-json-import-export)
- SQLite via existing `BookmarkStore` (S02) — no schema changes required (001-json-import-export)
- Python 3.11 + Click 8.x (CLI framework), Python stdlib `urllib.parse` (URL validation, no new runtime deps) (001-add-delete-commands)
- SQLite via `BookmarkStore` — `src/bookmarkcli/store.py` (stable from S01) (001-add-delete-commands)

- Python ≥ 3.11 + Click ≥ 8.0 (runtime); pytest ≥ 8.0, aiosqlite ≥ 0.20 (dev) (001-project-scaffold)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python ≥ 3.11: Follow standard conventions

## Recent Changes
- 004-tag-management: Added Python ≥ 3.11 + `click>=8.0` (existing), `sqlite3` stdlib (existing) — no new runtime packages
- 001-csv-import-export: Added Python 3.11 + Click 8.x (existing), Python stdlib `csv`, `datetime` (no new runtime deps)
- 001-json-import-export: Added Python 3.11+ + Click 8.x (existing), stdlib `json`, `pathlib`, `sys`
- 001-add-delete-commands: Added Python 3.11 + Click 8.x (CLI framework), Python stdlib `urllib.parse` (URL validation, no new runtime deps)
- 002-data-model-storage: Added Python ≥ 3.11 + `sqlite3` (stdlib) — no new runtime packages required; `pytest ≥ 8.0` (dev, already declared)
- 001-project-scaffold: Added Python ≥ 3.11 + Click ≥ 8.0 (runtime); pytest ≥ 8.0, aiosqlite ≥ 0.20 (dev)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
