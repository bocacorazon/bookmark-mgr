# Implementation Plan: List & Search Commands

**Branch**: `003-list-search-commands` | **Date**: 2026-03-07 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/003-list-search-commands/spec.md`

## Summary

Add `bookmark list` and `bookmark search` commands to the CLI. `list` displays all stored bookmarks with optional `--tag`, `--limit`, and `--sort` filtering; `search` performs case-insensitive substring matching across title and URL. Both commands auto-detect TTY state to render a rich table (using the `rich` library) when running interactively, or plain-text tabular output when piped. A `--plain` flag forces plain-text mode. Matching terms are highlighted in rich mode for `search`. The storage layer gains two new query methods (`list_filtered` and `search`) implemented via parameterised SQLite queries.

## Technical Context

**Language/Version**: Python ≥ 3.11  
**Primary Dependencies**: `click>=8.0` (existing), `rich>=13.0` (new — table rendering, TTY detection, highlight)  
**Storage**: SQLite via `BookmarkStore` (S02) — two new query methods added: `list_filtered` and `search`  
**Testing**: pytest ≥ 8.0 (existing dev dependency); Click's `CliRunner` for CLI integration tests  
**Target Platform**: Linux / macOS desktop (single-user CLI tool)  
**Project Type**: CLI tool — extends existing `src/bookmarkcli/` package  
**Performance Goals**: `bookmark search` returns results in < 1 s for up to 10 000 bookmarks (SC-003)  
**Constraints**: No concurrent writes; single-file SQLite; special characters in search treated as literals  
**Scale/Scope**: Up to ~10 000 bookmark records; single user

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

> The project constitution file (`.specify/memory/constitution.md`) is currently the default template with no project-specific principles ratified. No constitution gates exist to evaluate at this time.

**Pre-design check**: ✅ No violations — proceed to Phase 0.  
**Post-design check**: ✅ No violations — proceed to Phase 1 output.

## Project Structure

### Documentation (this feature)

```text
specs/003-list-search-commands/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── cli-schema.md
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
src/
└── bookmarkcli/
    ├── __init__.py       # existing — namespace only
    ├── cli.py            # MODIFIED — register list + search commands
    ├── models.py         # existing — Bookmark dataclass + exceptions (no changes)
    ├── store.py          # MODIFIED — add list_filtered() and search() methods
    └── formatter.py      # NEW — TTY detection, rich/plain table rendering, highlighting

tests/
├── __init__.py           # existing
├── test_store.py         # existing — MODIFIED to add list_filtered + search tests
├── test_formatter.py     # NEW — unit tests for formatter (TTY, plain, highlight)
└── test_cli.py           # NEW — CLI integration tests via Click CliRunner
```

**Structure Decision**: Single-project flat layout extending the existing `src/bookmarkcli/` package. A dedicated `formatter.py` module isolates rendering logic from CLI command definitions, keeping `cli.py` focused on argument parsing and orchestration.

## Complexity Tracking

> No constitution violations — section not applicable.
