# Implementation Plan: Add & Delete Commands

**Branch**: `001-add-delete-commands` | **Date**: 2026-03-07 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/001-add-delete-commands/spec.md`

## Summary

Implement `bookmark add <url> [--title TEXT] [--tags TEXT]` and `bookmark delete <id|url>` CLI subcommands on top of the existing `BookmarkStore` persistence layer (from S01/002-data-model-storage). The `add` command validates URL format via `urllib.parse`, prevents duplicate URLs, and prints a confirmation including the assigned ID. The `delete` command accepts either a numeric ID or a URL string, displays the matching bookmark details, and requires explicit `y/Y` confirmation before removing. Both commands exit non-zero on any error condition.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: Click 8.x (CLI framework), Python stdlib `urllib.parse` (URL validation, no new runtime deps)  
**Storage**: SQLite via `BookmarkStore` — `src/bookmarkcli/store.py` (stable from S01)  
**Testing**: pytest via `uv run pytest -q`  
**Target Platform**: Linux/macOS interactive terminal  
**Project Type**: CLI application  
**Performance Goals**: Sub-second interactive response for all add/delete operations  
**Constraints**: No new runtime dependencies — URL validation uses stdlib only  
**Scale/Scope**: Single-user personal bookmark store; hundreds to low-thousands of entries

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The project constitution file is the default template (no project-specific rules ratified). Applying standard software engineering gates:

| Gate | Status | Notes |
|------|--------|-------|
| No unnecessary complexity | ✅ PASS | Thin CLI layer over existing store; no new abstractions |
| Builds on existing primitives | ✅ PASS | Reuses `BookmarkStore`, Click, pytest from prior specs |
| No redundant persistence | ✅ PASS | Single SQLite store; no caching layer added |
| No new runtime dependencies | ✅ PASS | URL validation via `urllib.parse` (stdlib) |
| Tests accompany implementation | ✅ PASS | `tests/test_cli.py` to be created alongside `cli.py` changes |

*Post-design re-check*: `find_by_url()` added to `BookmarkStore` is additive and non-breaking. `DuplicateBookmarkError` added to `models.py` is additive. ✅ No violations.

## Project Structure

### Documentation (this feature)

```text
specs/001-add-delete-commands/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/
│   └── cli-commands.md  # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/bookmarkcli/
├── __init__.py          # unchanged
├── models.py            # + DuplicateBookmarkError
├── store.py             # + find_by_url(url) -> Bookmark | None
└── cli.py               # + add subcommand, + delete subcommand

tests/
├── test_store.py        # existing + tests for find_by_url
└── test_cli.py          # new: add/delete command tests via Click CliRunner
```

**Structure Decision**: Single-project layout. All changes land in the existing `src/bookmarkcli/` package. No new packages, modules beyond adjustments to the three files above, or external services are required.

## Complexity Tracking

No constitution violations — table not required.
