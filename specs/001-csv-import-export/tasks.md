# Tasks: CSV Import/Export

**Input**: Design documents from `/specs/001-csv-import-export/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/cli-commands.md ✅, quickstart.md ✅

**Tests**: Included — test files (`tests/test_csv_io.py`, `tests/test_cli.py`) are part of the planned project structure (plan.md) and quickstart.md defines test scenarios.

**Organization**: Tasks grouped by user story for independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no shared dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths included in every description

---

## Phase 1: Setup

**Purpose**: Create the new `csv_io.py` module to unblock all user story phases.

- [X] T001 Create `src/bookmarkcli/csv_io.py` with two stub public functions: `export_bookmarks(bookmarks, dest)` and `import_bookmarks(src, store)` (stubs raise `NotImplementedError`); add module-level docstring describing the two entry points

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add new domain types to `models.py` required by the import user stories (US2, US3).

**⚠️ CRITICAL**: US2 and US3 cannot be fully implemented until T002 is complete.

- [X] T002 Add `SkippedRow(row_number: int, reason: str)` and `ImportResult(imported: int, skipped: int, skipped_rows: list[SkippedRow])` dataclasses to `src/bookmarkcli/models.py`

**Checkpoint**: Foundation ready — all user story phases can now begin.

---

## Phase 3: User Story 1 — Export Bookmarks to CSV (Priority: P1) 🎯 MVP

**Goal**: Users can run `bookmarkcli export --format csv [--file PATH]` to receive all bookmarks as a CSV with columns `url,title,tags,created_at` (tags semicolon-joined), either written to stdout or a named file.

**Independent Test**: Populate the store with several bookmarks (including multi-tag entries); run `export --format csv` and verify header + data rows match stored data; run with `--file out.csv` and verify file contents; test empty store produces header-only output and exit 0.

### Tests for User Story 1

> **Write these tests FIRST — they MUST FAIL before implementation (T005, T006)**

- [X] T003 [P] [US1] Write unit tests for `export_bookmarks()`: header row present, one data row per bookmark, tags semicolon-joined, empty bookmark list produces header only, `created_at` serialised as ISO 8601 — in `tests/test_csv_io.py`
- [X] T004 [P] [US1] Write CLI tests for `bookmarkcli export --format csv` (stdout output matches store contents) and `--file PATH` (file created with correct content); include empty store case and non-writable path error case — in `tests/test_cli.py`

### Implementation for User Story 1

- [X] T005 [US1] Implement `export_bookmarks(bookmarks: list[Bookmark], dest: IO[str]) -> None` in `src/bookmarkcli/csv_io.py`: use `csv.DictWriter` with `fieldnames=["url","title","tags","created_at"]`; write header row; emit one row per bookmark with `tags` as `";".join(bookmark.tags)` and `created_at` as `.isoformat()`
- [X] T006 [US1] Add `export` Click command to `src/bookmarkcli/cli.py`: `@main.command()`, `--format` required choice `["csv"]`, `--file` optional `click.Path(writable=True, dir_okay=False)` defaulting to `None`; open file or use `click.get_text_stream("stdout")`; call `export_bookmarks(store.list_all(), dest)`

**Checkpoint**: `bookmarkcli export --format csv` and `--file` variant both work end-to-end; T003 and T004 tests pass.

---

## Phase 4: User Story 2 — Import Bookmarks from CSV (Priority: P2)

**Goal**: Users can run `bookmarkcli import --format csv FILE` to bulk-load bookmarks from a CSV file; all valid rows are added to the store and a summary line "Imported N, skipped M" is printed to stdout.

**Independent Test**: Prepare a well-formed CSV with 3–5 valid rows; run `import --format csv file.csv`; verify each row appears in the store with correct URL, title, tags (split on `;`), and `created_at`; verify summary shows "Imported N, skipped 0" and exit code is 0.

### Tests for User Story 2

> **Write these tests FIRST — they MUST FAIL before implementation (T009, T010)**

- [X] T007 [P] [US2] Write unit tests for `import_bookmarks()` happy path: valid rows added to store, `tags` column split on `;` with empty segments dropped, `created_at` preserved when present and valid, current time used when `created_at` absent or empty string — in `tests/test_csv_io.py`
- [X] T008 [P] [US2] Write CLI tests for `bookmarkcli import --format csv FILE`: success summary printed, imported count matches valid row count, file-not-found produces Click error — in `tests/test_cli.py`

### Implementation for User Story 2

- [X] T009 [US2] Implement `import_bookmarks(src: IO[str], store: BookmarkStore) -> ImportResult` in `src/bookmarkcli/csv_io.py`: open with `csv.DictReader`; iterate rows (1-based counter for data rows); parse `url`, `title`, `tags` (split on `;`, drop empty segments), `created_at` via `datetime.fromisoformat()` falling back to `datetime.now(tz=timezone.utc)` when absent/empty; call `store.create()` per valid row; return `ImportResult`
- [X] T010 [US2] Add `import_cmd` Click command (registered as `"import"` via `@main.command(name="import")`) to `src/bookmarkcli/cli.py`: `--format` required choice `["csv"]`, `FILE` positional `click.Path(exists=True, readable=True, dir_okay=False)`; open file, call `import_bookmarks()`; print `f"Imported {result.imported}, skipped {result.skipped}"` to stdout

**Checkpoint**: `bookmarkcli import --format csv bookmarks.csv` works for well-formed CSV; T007 and T008 tests pass.

---

## Phase 5: User Story 3 — Graceful Handling of Malformed Import Rows (Priority: P3)

**Goal**: When a CSV file contains malformed rows (missing/blank URL, unparseable `created_at`, missing header), valid rows are still imported, each skipped row is reported with a reason, and the command exits with code 1 when zero rows were imported.

**Independent Test**: Craft a CSV with 5 valid rows + 2 rows missing URL + 1 row with an unparseable `created_at`; run import; verify only 5 rows in store; verify summary reports "Imported 5, skipped 3" with per-row reason lines; also verify all-malformed file exits 1 and missing-header file writes error to stderr and exits 1.

### Tests for User Story 3

> **Write these tests FIRST — they MUST FAIL before implementation (T013, T014)**

- [X] T011 [P] [US3] Write unit tests for malformed row handling in `import_bookmarks()`: missing `url` → skip with reason, blank `url` → skip, bad `created_at` present → skip with reason, extra unknown columns silently ignored, all-malformed returns `ImportResult(imported=0, skipped=N, ...)` — in `tests/test_csv_io.py`
- [X] T012 [P] [US3] Write CLI tests for malformed import scenarios: mixed valid+invalid rows → correct "Imported N, skipped M" summary + per-row detail + exit 0; all-invalid rows → exit 1; missing header (or no `url` column) → stderr error + exit 1; empty/header-only file → "Imported 0, skipped 0" + exit 0 — in `tests/test_cli.py`

### Implementation for User Story 3

- [X] T013 [US3] Extend `import_bookmarks()` in `src/bookmarkcli/csv_io.py` with per-row validation: after calling `csv.DictReader`, check `reader.fieldnames` — if `None` or `"url"` not in `reader.fieldnames`, raise a `ValueError` with message `"CSV file must have a header row with at least a 'url' column"`; in the row loop, skip rows where `url` is absent/blank (append `SkippedRow(row_number, "url is missing or blank")`); skip rows where `created_at` is a non-empty string that raises `ValueError` from `fromisoformat()` (append `SkippedRow(row_number, f"created_at cannot be parsed: '{value}'")`)
- [X] T014 [US3] Extend `import_cmd` in `src/bookmarkcli/cli.py`: wrap `import_bookmarks()` call to catch `ValueError` from missing/invalid header — emit message to stderr via `click.echo(..., err=True)` and `ctx.exit(1)`; after successful import, print one detail line per skipped row: `f"  Row {sr.row_number}: {sr.reason}"`; call `ctx.exit(1)` when `result.imported == 0` and `result.skipped > 0`

**Checkpoint**: All three user stories work end-to-end; T011 and T012 tests pass; `uv run pytest -q` is all green.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Edge cases, round-trip validation, and quickstart verification.

- [X] T015 [P] Add edge case tests: CRLF line endings on import (`\r\n` in CSV content), empty tag segments dropped (`"python;;dev"` → `["python","dev"]`), export `--file` overwrites existing file silently, header-only CSV import exits 0 with "Imported 0, skipped 0" — in `tests/test_csv_io.py` and `tests/test_cli.py`
- [X] T016 Run end-to-end quickstart validation per `specs/001-csv-import-export/quickstart.md`: `uv sync && uv run bookmarkcli --help && uv run bookmarkcli export --format csv && uv run pytest -q`; confirm all assertions in quickstart scenarios pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — blocks US2 and US3 fully
- **User Story 1 — Phase 3**: Depends on Phase 1 only (csv_io.py skeleton); independent of Phase 2
- **User Story 2 — Phase 4**: Depends on Phase 1 and Phase 2 (csv_io.py skeleton + ImportResult/SkippedRow types)
- **User Story 3 — Phase 5**: Depends on Phase 4 (extends the same `import_bookmarks()` and `import_cmd`)
- **Polish (Phase 6)**: Depends on Phases 3, 4, and 5

### User Story Dependencies

- **US1 (Export, P1)**: Can start after T001 only — fully independent of US2 and US3
- **US2 (Import, P2)**: Can start after T001 and T002 — independent of US1
- **US3 (Malformed, P3)**: Depends on US2 completion — extends `import_bookmarks()` and `import_cmd`

### Within Each User Story

- Tests (T003/T004, T007/T008, T011/T012) must be written first and must fail before implementation
- T005 (export logic) must complete before T006 (export CLI command)
- T009 (import logic) must complete before T010 (import CLI command)
- T013 (malformed validation) extends T009 in the same file; T014 extends T010 in the same file

---

## Parallel Opportunities

### User Story 1 (can start after T001)

```bash
# Run in parallel:
Task T003: "Write unit tests for export_bookmarks() in tests/test_csv_io.py"
Task T004: "Write CLI tests for export command in tests/test_cli.py"
# Then sequentially:
Task T005: "Implement export_bookmarks() in src/bookmarkcli/csv_io.py"
Task T006: "Add export Click command to src/bookmarkcli/cli.py"
```

### User Story 2 (can start after T001 + T002)

```bash
# Run in parallel:
Task T007: "Write unit tests for import_bookmarks() happy path in tests/test_csv_io.py"
Task T008: "Write CLI tests for import command in tests/test_cli.py"
# Then sequentially:
Task T009: "Implement import_bookmarks() in src/bookmarkcli/csv_io.py"
Task T010: "Add import_cmd Click command to src/bookmarkcli/cli.py"
```

### User Story 3 (can start after T009 + T010)

```bash
# Run in parallel:
Task T011: "Write unit tests for malformed row handling in tests/test_csv_io.py"
Task T012: "Write CLI tests for malformed import in tests/test_cli.py"
# Then sequentially:
Task T013: "Extend import_bookmarks() with per-row validation in src/bookmarkcli/csv_io.py"
Task T014: "Extend import_cmd with error handling in src/bookmarkcli/cli.py"
```

### Cross-Story Parallelism (after T001 + T002)

With two developers: US1 (T003–T006) and US2 (T007–T010) can proceed in parallel since they work on independent halves of `csv_io.py` (export vs import functions) and separate sections of `cli.py`.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Create csv_io.py skeleton (T001)
2. Complete Phase 3: Export US1 (T003–T006)
3. **STOP and VALIDATE**: `bookmarkcli export --format csv` works; `uv run pytest -q` green
4. Deploy / demo if ready

### Incremental Delivery

1. T001 → csv_io.py module created
2. T002 → import domain types available
3. T003–T006 → **MVP: Export fully functional** ✓
4. T007–T010 → Import happy path ✓
5. T011–T014 → Full resilience + malformed row handling ✓
6. T015–T016 → Polish and edge case coverage ✓

### Parallel Team Strategy

With two developers (after T001 + T002 complete):

- **Developer A**: T003 → T004 → T005 → T006 (User Story 1 — Export)
- **Developer B**: T007 → T008 → T009 → T010 (User Story 2 — Import)
- **Both contribute**: T011 → T012 → T013 → T014 (User Story 3 — Malformed handling)

---

## Notes

- `import` is a Python keyword; Click command function is named `import_cmd`, registered via `@main.command(name="import")`
- Export writes to `click.get_text_stream("stdout")` when `--file` is omitted; `open(path, "w", newline="", encoding="utf-8")` when `--file` is given
- `csv.DictReader` auto-populates unknown columns in `row`; they are safely ignored by accessing only known keys
- Round-trip fidelity: `.isoformat()` on export ↔ `datetime.fromisoformat()` on import preserves UTC timestamps exactly (Python 3.11 supports the `Z` suffix)
- All CLI tests use `click.testing.CliRunner()` without `mix_stderr`; assert on `Result.stdout` and `Result.stderr` separately (per codebase conventions)
- Empty tag segments after semicolon split: `[t.strip() for t in tags_str.split(";") if t.strip()]`
