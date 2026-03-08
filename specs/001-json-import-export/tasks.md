---
description: "Task list for JSON Import/Export feature implementation"
---

# Tasks: JSON Import/Export

**Input**: Design documents from `/specs/001-json-import-export/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/cli-commands.md ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on other in-progress tasks)
- **[Story]**: Which user story this task belongs to (US1–US5)
- Exact file paths included in every description

## Path Conventions

Single-project layout (repository root):

- Source: `src/bookmarkcli/`
- Tests: `tests/`

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Scaffold the new module with its data model so all user story phases can proceed.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T001 Create `src/bookmarkcli/jsonport.py` with the `ImportResult` dataclass (`added`, `skipped`, `updated`, `invalid` integer fields) and stub signatures for `bookmarks_to_json()` and `import_from_json()` (raise `NotImplementedError`)

**Checkpoint**: `src/bookmarkcli/jsonport.py` exists and is importable; `ImportResult` can be instantiated — user story phases can now begin.

---

## Phase 2: User Story 1 — Export Bookmarks to a JSON File (Priority: P1) 🎯 MVP

**Goal**: `bookmark export --format json --file <path>` serialises all bookmarks to a JSON file with full field fidelity.

**Independent Test**: Populate a store with three bookmarks (some with tags), run `bookmark export --format json --file out.json`, confirm `out.json` is valid JSON containing all three bookmarks with correct `url`, `title`, and `tags` fields.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T002 [P] [US1] Write unit tests for `bookmarks_to_json()` (non-empty list, empty list, null title, empty tags, timestamps) in `tests/test_jsonport.py`
- [X] T003 [P] [US1] Write CLI integration tests for `bookmark export --format json --file <path>` (file created, valid JSON, bookmarks present, empty store) in `tests/test_jsonport.py`

### Implementation for User Story 1

- [X] T004 [P] [US1] Implement `bookmarks_to_json(bookmarks: list[Bookmark], indent: int = 2) -> str` in `src/bookmarkcli/jsonport.py`: serialise to `{"bookmarks": [...]}` JSON string; exclude `id`; encode `tags` as array; encode `created_at`/`updated_at` as ISO 8601 strings; encode `null` title as JSON null; return `'{"bookmarks": []}'\n` for empty list
- [X] T005 [US1] Add `export` Click command to `src/bookmarkcli/cli.py` with `--format` (required choice: `json`) and `--file` (optional path string) options; call `bookmarks_to_json()` and write the JSON string to the specified file (create or overwrite silently)
- [X] T006 [US1] Add file-path error handling to `export` command in `src/bookmarkcli/cli.py`: if `--file` path is a directory, print `"Error: <path> is a directory"` to stderr and exit 1; if path is not writable, print `"Error: cannot write to <path>: <reason>"` to stderr and exit 1

**Checkpoint**: `bookmark export --format json --file out.json` creates a valid JSON file; empty-store export produces `{"bookmarks": []}`.

---

## Phase 3: User Story 3 — Import Bookmarks from a JSON File (Priority: P1)

**Goal**: `bookmark import --format json <file>` parses a JSON export file, inserts all valid bookmarks into the store (skipping duplicates by default), and prints a summary.

**Independent Test**: Export three bookmarks to a file, clear the store, run `bookmark import --format json <file>`, confirm the store contains all three bookmarks and the summary reads `Import complete: 3 added, 0 skipped, 0 updated, 0 invalid.`

### Tests for User Story 3 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T007 [P] [US3] Write unit tests for `import_from_json()` (new bookmarks added, missing url skipped with warning, invalid JSON raises, missing bookmarks key raises, empty array returns zeros) in `tests/test_jsonport.py`
- [X] T008 [P] [US3] Write CLI integration tests for `bookmark import --format json <file>` (success summary, file-not-found error, invalid-JSON error, partial-invalid-entries warning+summary) in `tests/test_jsonport.py`

### Implementation for User Story 3

- [X] T009 [US3] Implement `import_from_json(json_str: str, store: BookmarkStore, on_duplicate: str = "skip") -> ImportResult` in `src/bookmarkcli/jsonport.py`: call `json.loads()` (raises `json.JSONDecodeError` on invalid JSON); extract `"bookmarks"` array (raise `ValueError` if key missing or value not a list); load existing bookmarks via `store.list_all()` into `dict[str, Bookmark]` keyed by URL; track seen-this-run URLs in a `set[str]`; for each entry: skip with warning to stderr if `url` missing/empty/null (increment `invalid`), skip if URL already in store or seen set and `on_duplicate="skip"` (increment `skipped`), otherwise call `store.create(url=..., title=..., tags=...)` (increment `added`); add URL to seen set; return `ImportResult`
- [X] T010 [US3] Add `import` Click command to `src/bookmarkcli/cli.py` with `--format` (required choice: `json`) option and `file` positional argument (required path string); read file content, call `import_from_json()`, print summary to stdout: `"Import complete: N added, N skipped, N updated, N invalid."`
- [X] T011 [US3] Add error handling to `import` command in `src/bookmarkcli/cli.py`: if file does not exist, print `"Error: file not found: <path>"` to stderr and exit 1; if file not readable, print `"Error: cannot read file: <path>: <reason>"` to stderr and exit 1; if `json.JSONDecodeError` raised, print `"Error: invalid JSON in <path>"` to stderr and exit 1; if `ValueError` raised (missing bookmarks key), print `"Error: invalid format in <path>"` to stderr and exit 1

**Checkpoint**: `bookmark import --format json backup.json` inserts all bookmarks and prints a correct summary; invalid file path and malformed JSON produce actionable error messages.

---

## Phase 4: User Story 2 — Export Bookmarks to Standard Output (Priority: P2)

**Goal**: Running `bookmark export --format json` without `--file` prints valid JSON to stdout.

**Independent Test**: Run `bookmark export --format json` without `--file` and confirm valid JSON is printed to stdout; run on an empty store and confirm `{"bookmarks": []}` is printed.

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T012 [P] [US2] Write CLI integration tests for `bookmark export --format json` without `--file` (valid JSON to stdout, empty store produces empty bookmarks array) in `tests/test_jsonport.py`

### Implementation for User Story 2

- [X] T013 [P] [US2] Add stdout fallback to `export` command in `src/bookmarkcli/cli.py`: when `--file` is omitted, print the JSON string to stdout via `click.echo()` instead of writing to file

**Checkpoint**: `bookmark export --format json` (no `--file`) prints valid JSON to stdout; can be piped to `jq`.

---

## Phase 5: User Story 4 — Handle Duplicate Bookmarks on Import (Priority: P2)

**Goal**: Users can control duplicate handling with `--on-duplicate skip` (default) or `--on-duplicate update`; the import summary correctly reports skipped and updated counts.

**Independent Test**: Import a file containing a URL already in the store without any flag (confirm existing bookmark unchanged, summary shows 1 skipped); import again with `--on-duplicate update` (confirm existing bookmark's title and tags replaced, summary shows 1 updated).

### Tests for User Story 4 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T014 [P] [US4] Write CLI integration tests for `--on-duplicate skip` (existing record unchanged, skipped count correct) and `--on-duplicate update` (title/tags overwritten, updated count correct) and mixed file (some new, some duplicate) in `tests/test_jsonport.py`

### Implementation for User Story 4

- [X] T015 [P] [US4] Add `--on-duplicate` option (choice: `skip`, `update`; default `skip`) to `import` command in `src/bookmarkcli/cli.py`; pass value to `import_from_json()` as `on_duplicate` argument
- [X] T016 [P] [US4] Implement the `on_duplicate="update"` branch in `import_from_json()` in `src/bookmarkcli/jsonport.py`: when URL is already in the store and policy is `update`, call `store.update(existing.id, title=entry_title, tags=entry_tags)` and increment `updated` instead of `skipped`; also apply update policy for within-file duplicates (second occurrence treated as duplicate of first)

**Checkpoint**: Both duplicate modes work correctly; import summary reports accurate counts for added, skipped, and updated.

---

## Phase 6: User Story 5 — Full Round-Trip Fidelity (Priority: P2)

**Goal**: Exporting and then importing into an empty store produces a store identical to the original — every bookmark's URL, title, tags, and timestamps are preserved exactly.

**Independent Test**: Populate a store with diverse bookmarks (long URLs, multi-word titles, multiple tags, varied timestamps, a bookmark with null title and empty tags). Export to file. Clear the store. Import the file. Assert field-by-field equality for every bookmark including `created_at` and `updated_at`.

### Tests for User Story 5 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T017 [P] [US5] Write a round-trip integration test in `tests/test_jsonport.py`: populate store with diverse bookmarks → export to JSON string → clear store → import JSON string → assert each bookmark's `url`, `title`, `tags`, `created_at`, and `updated_at` match the originals exactly

### Implementation for User Story 5

- [X] T018 [US5] Implement timestamp-aware insertion in `import_from_json()` in `src/bookmarkcli/jsonport.py`: when `created_at` or `updated_at` are present in the entry, parse them via `datetime.fromisoformat()`; if parseable, use a direct `store._con.execute("INSERT INTO bookmarks ...")` with the preserved timestamps (fall back to current UTC time for missing or unparseable timestamps); ensure `store._con.commit()` is called

**Checkpoint**: After export + clear + import, every bookmark in the restored store has the same URL, title, tags, `created_at`, and `updated_at` as the original.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Validate the complete implementation end-to-end.

- [X] T019 Run `uv run pytest -q` from the repository root to confirm all tests in `tests/test_jsonport.py` and `tests/test_store.py` pass
- [X] T020 [P] Run the quickstart.md validation scenarios manually: export to file, export to stdout, basic import, import with `--on-duplicate update`, full round-trip, error cases (missing file, invalid JSON, entry missing url)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — start immediately
- **User Story phases (Phases 2–6)**: All depend on Phase 1 completion
  - US1 (Phase 2) and US3 (Phase 3) can proceed in parallel after Phase 1
  - US2 (Phase 4) depends on US1 (Phase 2) — same `export` command
  - US4 (Phase 5) depends on US3 (Phase 3) — same `import` command
  - US5 (Phase 6) depends on US3 (Phase 3) — modifies `import_from_json()`
- **Polish (Phase 7)**: Depends on all desired user story phases being complete

### User Story Dependencies

- **US1 (P1)**: No story dependencies; depends only on Phase 1
- **US3 (P1)**: No story dependencies; depends only on Phase 1
- **US2 (P2)**: Depends on US1 (adds stdout path to `export` command)
- **US4 (P2)**: Depends on US3 (adds `--on-duplicate` to `import` command)
- **US5 (P2)**: Depends on US3 (modifies `import_from_json()` for timestamp preservation)

### Within Each User Story

- Tests (marked ⚠️) MUST be written and confirmed FAILING before implementation tasks begin
- `jsonport.py` implementation tasks before `cli.py` command tasks (CLI calls the module)
- Core implementation before error handling additions
- Story complete before moving to next phase

---

## Parallel Opportunities

### Across Phases 2 and 3 (both P1)

```
# After Phase 1 completes, two developers can work simultaneously:
Developer A: Phase 2 (US1 — export to file)
Developer B: Phase 3 (US3 — import from file)
```

### Within Phase 2 (US1)

```
# Tests and implementation can be written simultaneously (different files):
Task T002: Write tests for bookmarks_to_json() → tests/test_jsonport.py
Task T003: Write CLI integration tests for export --file → tests/test_jsonport.py

Task T004: Implement bookmarks_to_json() → src/bookmarkcli/jsonport.py
(T005 and T006 follow sequentially in cli.py)
```

### Within Phase 3 (US3)

```
# Tests and implementation can be written simultaneously:
Task T007: Write unit tests for import_from_json() → tests/test_jsonport.py
Task T008: Write CLI integration tests for import → tests/test_jsonport.py

Task T009: Implement import_from_json() → src/bookmarkcli/jsonport.py
(T010 and T011 follow sequentially in cli.py)
```

### Within Phase 5 (US4)

```
# Tests, CLI change, and module change are in different files:
Task T014: Write duplicate handling tests → tests/test_jsonport.py
Task T015: Add --on-duplicate option → src/bookmarkcli/cli.py
Task T016: Implement update branch → src/bookmarkcli/jsonport.py
```

---

## Implementation Strategy

### MVP First (US1 + US3 Only)

1. Complete Phase 1: Foundational
2. Complete Phase 2: US1 — export to file
3. Complete Phase 3: US3 — basic import (skip duplicates)
4. **STOP and VALIDATE**: Users can back up and restore bookmarks
5. Deploy/demo if ready

### Incremental Delivery

1. Phase 1 → Foundation ready
2. Phase 2 + 3 → Basic export + import working (MVP!)
3. Phase 4 → Add stdout export
4. Phase 5 → Add duplicate update mode
5. Phase 6 → Guarantee full timestamp fidelity
6. Phase 7 → Validated and polished

### Parallel Team Strategy

With two developers:

1. Both complete Phase 1 together
2. Once Phase 1 is done:
   - Developer A: Phase 2 (US1 — export)
   - Developer B: Phase 3 (US3 — import)
3. Merge and continue with Phases 4–6 sequentially or split further

---

## Notes

- **No new dependencies**: `jsonport.py` uses only Python stdlib (`json`, `datetime`, `sys`); no `pyproject.toml` changes needed
- **No schema changes**: `BookmarkStore` and `models.py` are unchanged; US5 uses `store._con` directly for timestamp-preserving INSERT (documented in research.md Decision 3)
- **`--format` is required**: Both `export` and `import` require `--format json`; it is never defaulted (per spec assumption)
- **[P] tasks**: Different files, no in-progress dependencies — safe to parallelize
- **Story labels**: Map each task to its user story for traceability
- Commit after each checkpoint to enable clean rollback
- Stop at any phase checkpoint to validate independently before continuing
