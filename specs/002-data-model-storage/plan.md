# Implementation Plan: Data Model & Storage

**Branch**: `002-data-model-storage` | **Date**: 2026-03-07 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/002-data-model-storage/spec.md`

## Summary

Add a SQLite-backed storage layer to `bookmarkcli` by introducing a `Bookmark` dataclass and a `BookmarkStore` class that encapsulates all CRUD operations. Schema initialization and migration run automatically on first use via `PRAGMA user_version`. Tags are stored as a comma-separated string; IDs are auto-increment integers. A complete pytest test suite covers all public operations and the edge cases in the spec.

## Technical Context

**Language/Version**: Python ≥ 3.11  
**Primary Dependencies**: `sqlite3` (stdlib) — no new runtime packages required; `pytest ≥ 8.0` (dev, already declared)  
**Storage**: SQLite (hard constraint per spec) — single-file database managed via stdlib `sqlite3`  
**Testing**: pytest ≥ 8.0 (already in dev dependency-group)  
**Target Platform**: Linux / macOS desktop (single-user CLI tool)  
**Project Type**: CLI tool — internal library layer (`src/bookmarkcli/`)  
**Performance Goals**: Schema init < 1 s; list 10 000 records < 2 s (SC-003, SC-004)  
**Constraints**: Single-process access; SQLite WAL not required; database path is caller-supplied  
**Scale/Scope**: Up to ~10 000 bookmark records; single-user; no concurrent writes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

> The project constitution file (`.specify/memory/constitution.md`) is currently the default template with no project-specific principles ratified. No constitution gates exist to evaluate at this time.

**Pre-design check**: ✅ No violations — proceed to Phase 0.  
**Post-design check**: ✅ No violations — proceed to Phase 1 output.

## Project Structure

### Documentation (this feature)

```text
specs/002-data-model-storage/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── python-api.md
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
└── bookmarkcli/
    ├── __init__.py     # existing — namespace only
    ├── cli.py          # existing — Click entry point (unchanged this feature)
    ├── models.py       # NEW — Bookmark dataclass + exceptions
    └── store.py        # NEW — BookmarkStore (SQLite CRUD + migration)

tests/
├── __init__.py         # existing
└── test_store.py       # NEW — full pytest suite for BookmarkStore
```

**Structure Decision**: Single-project flat layout inside the existing `src/bookmarkcli/` package. Two new modules are sufficient: `models.py` for pure domain types and `store.py` for all storage logic. No sub-packages needed at this scope.

## Complexity Tracking

> No constitution violations — section not applicable.
