# Implementation Plan: Tag Management

**Branch**: `004-tag-management` | **Date**: 2026-03-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-tag-management/spec.md`

## Summary

Add `bookmark tag <id> --add <tag>` / `bookmark tag <id> --remove <tag>` and `bookmark tags` CLI subcommands to `bookmarkcli`. Tags are normalized (lowercase + strip) before any operation. Three new `BookmarkStore` methods (`add_tag`, `remove_tag`, `list_tags`) own the business logic; the CLI layer handles flag validation and output formatting. No schema migration is needed — tags already live as a comma-separated TEXT column on the `bookmarks` table (schema version 1 from S02).

## Technical Context

**Language/Version**: Python ≥ 3.11  
**Primary Dependencies**: `click>=8.0` (existing), `sqlite3` stdlib (existing) — no new runtime packages  
**Storage**: SQLite via existing `BookmarkStore`; tags remain comma-separated in `bookmarks.tags` TEXT column  
**Testing**: pytest ≥ 8.0 (existing dev dependency)  
**Target Platform**: Linux/macOS desktop (single-user CLI tool)  
**Project Type**: CLI tool — extending existing `src/bookmarkcli/` package  
**Performance Goals**: All tag operations complete in < 1 s for a 10 000-record collection (SC-005)  
**Constraints**: No new runtime packages; no schema migration needed; single-process SQLite access  
**Scale/Scope**: Up to ~10 000 bookmark records; single user; no concurrent writes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

> The project constitution file (`.specify/memory/constitution.md`) is the default template with no project-specific principles ratified. No constitution gates exist to evaluate at this time.

**Pre-design check**: ✅ No violations — proceed to Phase 0.  
**Post-design check**: ✅ No violations — proceed to Phase 1 output.

## Project Structure

### Documentation (this feature)

```text
specs/004-tag-management/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── cli.md
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
└── bookmarkcli/
    ├── __init__.py     # existing — namespace only (unchanged)
    ├── cli.py          # modified — add `tag` and `tags` subcommands
    ├── models.py       # modified — add normalize_tag(), TagNotFoundError, TagValidationError
    └── store.py        # modified — add add_tag(), remove_tag(), list_tags()

tests/
├── __init__.py         # existing
├── test_store.py       # modified — add tests for new store methods
└── test_cli.py         # NEW — CLI tests for `tag` and `tags` commands
```

**Structure Decision**: Single-project flat layout inside the existing `src/bookmarkcli/` package. Three existing modules are extended; one new test file is added. No sub-packages or new runtime dependencies are needed at this scope.

## Complexity Tracking

> No constitution violations — section not applicable.
