# Implementation Plan: JSON Import/Export

**Branch**: `001-json-import-export` | **Date**: 2026-03-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-json-import-export/spec.md`

## Summary

Add `bookmark export --format json [--file <path>]` and `bookmark import --format json [--on-duplicate skip|update] <file>` commands to the CLI. Export serialises the full bookmark store to a JSON document; import parses that document, applies configurable duplicate handling (default: skip), and reports a summary. Round-trip fidelity is guaranteed for URL, title, and tags; timestamps are included in export and honoured on import where present.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: Click 8.x (existing), stdlib `json`, `pathlib`, `sys`  
**Storage**: SQLite via existing `BookmarkStore` (S02) — no schema changes required  
**Testing**: pytest (existing), `click.testing.CliRunner` for CLI integration tests  
**Target Platform**: Linux/macOS CLI  
**Project Type**: CLI tool (single-project)  
**Performance Goals**: Export <5 s for 1 000 bookmarks; import <10 s for 1 000 bookmarks  
**Constraints**: No new runtime dependencies; store loaded once per import via `list_all()` for O(N) URL lookup  
**Scale/Scope**: Handles thousands of bookmarks; no hard limit imposed

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The project constitution file is a template (not yet ratified). No explicit gates are defined. The design follows the pre-existing conventions established in S01 (scaffold) and S02 (storage):

| Convention | Status |
|---|---|
| Single Python package under `src/bookmarkcli/` | ✅ Compliant |
| Click-based CLI entry point | ✅ Compliant |
| No new runtime dependencies without justification | ✅ Compliant (stdlib only) |
| pytest test coverage for new logic | ✅ Planned |
| No changes to existing `BookmarkStore` public API | ✅ Compliant |

Post-design re-check: ✅ No violations.

## Project Structure

### Documentation (this feature)

```text
specs/001-json-import-export/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── cli-commands.md  # Phase 1 output
└── tasks.md             # Phase 2 output (speckit.tasks — not created here)
```

### Source Code (repository root)

```text
src/bookmarkcli/
├── cli.py          — existing; add `export` and `import` Click command groups
├── models.py       — existing; no changes
├── store.py        — existing; no changes
└── jsonport.py     — NEW: JSON serialisation, deserialisation, import orchestration

tests/
├── test_store.py       — existing
└── test_jsonport.py    — NEW: unit + integration tests for JSON I/O and CLI commands
```

**Structure Decision**: Single-project layout (Option 1). All new logic lives in one new module (`jsonport.py`) to keep the package flat. CLI commands are added directly to `cli.py` following the established pattern.
