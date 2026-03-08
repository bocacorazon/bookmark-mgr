# Implementation Plan: List & Search Commands

**Branch**: `001-list-search` | **Date**: 2026-03-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-list-search/spec.md`

## Summary

Add `bookmark list` and `bookmark search` commands to the CLI. `bookmark list` displays all stored bookmarks in a formatted table with optional `--tag`, `--limit`, and `--sort` filters. `bookmark search <query>` performs case-insensitive substring matching across title and URL fields. Output is rich-formatted when stdout is a terminal and plain-text when piped. Both commands build directly on the `BookmarkStore` from S01, adding two new query methods (`list_filtered` and `search`). The `rich` library is added as a dependency to power table rendering.

## Technical Context

**Language/Version**: Python 3.12 (CPython, pyproject.toml `requires-python = ">=3.11"`)
**Primary Dependencies**: Click >= 8.0 (existing), rich >= 13.0 (new — tables/formatting), SQLite stdlib (existing via BookmarkStore)
**Storage**: SQLite via `BookmarkStore` (S01 foundation — `src/bookmarkcli/store.py`)
**Testing**: pytest >= 8.0 (existing), Click's `CliRunner` for CLI integration tests
**Target Platform**: Linux/macOS terminal (stdout detection for rich vs plain)
**Project Type**: CLI tool (`bookmarkcli` entry point, Click group)
**Performance Goals**: < 1 second for list/search on collections of up to 10,000 bookmarks (SC-001–SC-003)
**Constraints**: Auto-detect terminal vs pipe for output format; no extra flags required (SC-004)
**Scale/Scope**: 10,000 bookmarks per collection

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The project constitution is a placeholder template (not yet configured). Based on observed project conventions:

| Gate | Status | Notes |
|------|--------|-------|
| Single project structure | ✅ PASS | Feature extends existing `src/bookmarkcli/` package |
| CLI interface standard | ✅ PASS | Click group pattern already in use |
| Test-first approach | ✅ PASS | Tests will be written before implementation |
| Simplicity (YAGNI) | ✅ PASS | No new abstractions beyond what's needed for the spec |
| No external service dependencies | ✅ PASS | Only `rich` added; no network or service calls |

## Project Structure

### Documentation (this feature)

```text
specs/001-list-search/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── list-command.md
│   └── search-command.md
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookmarkcli/
├── __init__.py
├── cli.py               # Add: list_cmd, search_cmd, register with main group
├── models.py            # No change needed
├── store.py             # Add: list_filtered(), search() methods
└── formatting.py        # New: render_bookmarks_table() with rich/plain fallback

tests/
├── __init__.py
├── test_store.py        # Existing; add: test_list_filtered_*, test_search_*
├── test_formatting.py   # New: unit tests for table rendering
└── test_cli.py          # New: Click CliRunner integration tests for list/search
```

**Structure Decision**: Single project layout (Option 1). All new code lives inside the existing `src/bookmarkcli/` package. A new `formatting.py` module isolates the `rich` dependency so it can be tested independently of the CLI entry points.

## Complexity Tracking

> No constitution violations found.
