# S00 Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-07

## Active Technologies
- N/A for S00 (aiosqlite declared for future use, not exercised) (001-project-scaffold)
- N/A (SQLite via aiosqlite declared for future features; no schema in S00) (001-project-scaffold)
- Python ≥ 3.11 + `sqlite3` (stdlib) — no new runtime packages required; `pytest ≥ 8.0` (dev, already declared) (002-data-model-storage)
- SQLite (hard constraint per spec) — single-file database managed via stdlib `sqlite3` (002-data-model-storage)
- Python 3.12 (CPython, pyproject.toml `requires-python = ">=3.11"`) + Click >= 8.0 (existing), rich >= 13.0 (new — tables/formatting), SQLite stdlib (existing via BookmarkStore) (001-list-search)
- SQLite via `BookmarkStore` (S01 foundation — `src/bookmarkcli/store.py`) (001-list-search)

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
- 001-list-search: Added Python 3.12 (CPython, pyproject.toml `requires-python = ">=3.11"`) + Click >= 8.0 (existing), rich >= 13.0 (new — tables/formatting), SQLite stdlib (existing via BookmarkStore)
- 002-data-model-storage: Added Python ≥ 3.11 + `sqlite3` (stdlib) — no new runtime packages required; `pytest ≥ 8.0` (dev, already declared)
- 001-project-scaffold: Added Python ≥ 3.11 + Click ≥ 8.0 (runtime); pytest ≥ 8.0, aiosqlite ≥ 0.20 (dev)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
