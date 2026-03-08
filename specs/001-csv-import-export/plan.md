# Implementation Plan: CSV Import/Export

**Branch**: `001-csv-import-export` | **Date**: 2026-03-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-csv-import-export/spec.md`

## Summary

Add `bookmark export --format csv [--file PATH]` and `bookmark import --format csv FILE` commands to the existing bookmark-mgr CLI. Export writes all bookmarks as RFC 4180 CSV to stdout or a file; import reads a CSV file, parses each row, skips malformed rows (missing URL, unparseable date), and prints an imported/skipped summary. Tags use semicolons as the separator in CSV (the store uses commas internally). No new runtime dependencies — Python's stdlib `csv` module handles all parsing and serialisation.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: Click 8.x (existing), Python stdlib `csv`, `datetime` (no new runtime deps)  
**Storage**: SQLite via existing `BookmarkStore` (`src/bookmarkcli/store.py`)  
**Testing**: pytest (existing), `click.testing.CliRunner` for CLI tests  
**Target Platform**: Linux / macOS / Windows (cross-platform CLI)  
**Project Type**: CLI tool  
**Performance Goals**: Export ≤2 s for 10 000 bookmarks; Import ≤5 s for 10 000 rows  
**Constraints**: Zero new runtime dependencies; stdlib `csv` only; round-trip fidelity 100 %  
**Scale/Scope**: Single-user local library; up to ~10 000 bookmarks in scope

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

> **Note**: The constitution file is a template with unfilled placeholders (`[PRINCIPLE_1_NAME]`, etc.). No project-specific gates are formally defined. The checks below apply standard software-engineering principles inferred from the spec and existing codebase.

| Gate | Status | Notes |
|------|--------|-------|
| No new runtime dependencies without justification | ✅ PASS | stdlib `csv` only |
| CLI interface follows existing Click patterns | ✅ PASS | `@main.command()` + `@click.option` / `@click.argument` |
| Errors written to stderr, data to stdout | ✅ PASS | `click.echo(..., err=True)` for errors |
| Round-trip fidelity maintained | ✅ PASS | ISO 8601 timestamps preserved; tag separator conversion handled |
| Malformed input handled gracefully (no crash) | ✅ PASS | per-row try/except; non-zero exit only when 0 rows imported |

**Post-design re-check**: No violations identified after Phase 1 design.

## Project Structure

### Documentation (this feature)

```text
specs/001-csv-import-export/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── cli-commands.md
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookmarkcli/
├── cli.py          # extend: add export + import commands
├── csv_io.py       # NEW: pure CSV read/write helpers
├── models.py       # extend: add ImportResult, SkippedRow dataclasses
└── store.py        # no changes required

tests/
├── test_csv_io.py  # NEW: unit tests for csv_io helpers
└── test_store.py   # existing — no changes required
```

**Structure Decision**: Single-project layout (Option 1). The feature slots entirely into the existing `src/bookmarkcli/` package. A dedicated `csv_io.py` module keeps serialisation logic isolated and independently testable without touching the CLI layer.
