---
description: "Task list for List & Search Commands (S03)"
---

# Tasks: List & Search Commands

**Input**: Design documents from `/specs/001-list-search/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Exact file paths included in every description

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the `rich` dependency required by all rendering tasks.

- [X] T001 Add `rich>=13.0` to `[project.dependencies]` in `pyproject.toml` and run `uv sync` to lock and install it

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Store query methods and the formatting module that every user story depends on.

**⚠️ CRITICAL**: No user story CLI work can begin until this phase is complete.

> **TDD**: Write and confirm tests FAIL before implementing.

- [X] T002 [P] Write failing pytest tests for `BookmarkStore.list_filtered()` (no-args returns all bookmarks, `tag=` returns only exact-tag matches, `limit=` caps row count, `sort="oldest"` returns ascending order, `sort="newest"` returns descending order) and `BookmarkStore.search()` (matches title substring, matches URL substring, case-insensitive, returns empty list for no match) in `tests/test_store.py`
- [X] T003 [P] Create `tests/test_formatting.py` with failing unit tests for `render_bookmarks_table()` (non-empty list produces string output containing ID/Title/URL/Tags/Created At headers, long values truncated with `…`) and `render_empty_state()` (output contains the provided message string)
- [X] T004 [P] Implement `BookmarkStore.list_filtered(tag: str | None = None, limit: int | None = None, sort: Literal["newest", "oldest"] = "newest") -> list[Bookmark]` in `src/bookmarkcli/store.py` using parameterized SQL with `INSTR(','||tags||',', ','||:tag||',') > 0` for exact tag matching, `ORDER BY created_at DESC/ASC`, and `LIMIT :limit`
- [X] T005 [P] Create `src/bookmarkcli/formatting.py` with `render_bookmarks_table(bookmarks: list[Bookmark], file: IO[str] | None = None) -> None` (rich.table.Table with ID/Title/URL/Tags/Created At columns; Title `max_width=40`, URL `max_width=50`, both `overflow="ellipsis"`, `no_wrap=True`; dates as `YYYY-MM-DD HH:MM` UTC; tags as comma-separated string) and `render_empty_state(message: str, file: IO[str] | None = None) -> None` (dim-styled in TTY, plain text when piped)
- [X] T006 Implement `BookmarkStore.search(query: str) -> list[Bookmark]` in `src/bookmarkcli/store.py` using `LOWER(title) LIKE LOWER('%'||:q||'%') OR LOWER(url) LIKE LOWER('%'||:q||'%')` ordered by `created_at DESC`

**Checkpoint**: Run `uv run pytest tests/test_store.py tests/test_formatting.py -q` — all T002/T003 tests should now pass.

---

## Phase 3: User Story 1 - List All Bookmarks (Priority: P1) 🎯 MVP

**Goal**: `bookmark list` displays all bookmarks in a formatted table (or empty-state message when none exist), with automatic rich/plain output based on TTY detection.

**Independent Test**: `uv run bookmarkcli add <url> <title>` then `uv run bookmarkcli list` shows a table; `uv run bookmarkcli list` on an empty store shows "No bookmarks found."

> **TDD**: Write and confirm tests FAIL before implementing T008.

- [X] T007 [US1] Create `tests/test_cli.py` with failing CliRunner tests for `bookmark list`: (1) empty store exits 0 with "No bookmarks found." in output; (2) store with two bookmarks exits 0 and output contains both titles, IDs, and column headers; (3) plain-text output produced by default CliRunner (non-TTY stdout)
- [X] T008 [US1] Implement `list_cmd` as `@main.command("list")` in `src/bookmarkcli/cli.py`: open `BookmarkStore` at default DB path (consistent with S01 pattern in `cli.py`), call `list_filtered()` with no arguments, render results with `render_bookmarks_table()` or `render_empty_state("No bookmarks found.")` from `src/bookmarkcli/formatting.py`

**Checkpoint**: `uv run pytest tests/test_cli.py -k list -q` passes; `uv run bookmarkcli list` works end-to-end.

---

## Phase 4: User Story 2 - Filter Bookmarks by Tag (Priority: P2)

**Goal**: `bookmark list --tag <tag>` returns only bookmarks carrying that exact tag; shows empty state if none match.

**Independent Test**: Add bookmarks with different tags, run `bookmark list --tag python` — only python-tagged bookmarks appear; `bookmark list --tag nonexistent` shows "No bookmarks found."

> **TDD**: Write and confirm tests FAIL before implementing T010.

- [X] T009 [US2] Add failing CliRunner tests to `tests/test_cli.py` for `bookmark list --tag`: (1) `--tag python` on mixed-tag store returns only python-tagged rows; (2) `--tag nonexistent` exits 0 with "No bookmarks found."; (3) bookmark with multiple tags including the queried one is included in results
- [X] T010 [US2] Add `--tag TEXT` option (default `None`) to `list_cmd` in `src/bookmarkcli/cli.py`; pass `tag=tag` to `list_filtered()` call

**Checkpoint**: `uv run pytest tests/test_cli.py -k tag -q` passes; `uv run bookmarkcli list --tag python` filters correctly.

---

## Phase 5: User Story 4 - Full-Text Search (Priority: P2)

**Goal**: `bookmark search <query>` returns all bookmarks where query appears (case-insensitively) in title or URL; shows empty state if none match; rejects blank query with a usage error.

**Independent Test**: Add bookmarks with known titles/URLs; `bookmark search python` returns those containing "python" in title or URL; `bookmark search "   "` exits with code 2; `bookmark search xyz123` shows "No bookmarks match your search."

> **TDD**: Write and confirm tests FAIL before implementing T012.

- [X] T011 [US4] Add failing CliRunner tests to `tests/test_cli.py` for `bookmark search`: (1) query matching title returns that bookmark; (2) query matching URL returns that bookmark; (3) `search "Python"` matches bookmark with lowercase "python" in title (case-insensitive); (4) query with no matches exits 0 with "No bookmarks match your search."; (5) empty string query exits 2 with usage error message; (6) whitespace-only query exits 2 with usage error message
- [X] T012 [US4] Implement `search_cmd` as `@main.command("search")` with `@click.argument("query")` in `src/bookmarkcli/cli.py`; validate `query.strip()` is non-empty (raise `click.UsageError("Search query cannot be empty. Usage: bookmark search <query>")` if blank); call `BookmarkStore.search(query)`; render with `render_bookmarks_table()` or `render_empty_state("No bookmarks match your search.")`

**Checkpoint**: `uv run pytest tests/test_cli.py -k search -q` passes; `uv run bookmarkcli search python` works end-to-end.

---

## Phase 6: User Story 3 - Limit and Sort the List (Priority: P3)

**Goal**: `bookmark list --limit <n>` caps results at N rows; `bookmark list --sort oldest|newest` orders by creation date; invalid values produce descriptive errors.

**Independent Test**: Add 10 bookmarks; `bookmark list --limit 3` returns exactly 3 rows; `bookmark list --sort oldest` returns them in ascending date order; `bookmark list --limit -1` and `bookmark list --sort alpha` both exit with code 2.

> **TDD**: Write and confirm tests FAIL before implementing T014.

- [X] T013 [US3] Add failing CliRunner tests to `tests/test_cli.py` for `bookmark list --limit` and `--sort`: (1) `--limit 2` with 5 bookmarks returns exactly 2 rows; (2) `--limit 100` with 3 bookmarks returns all 3; (3) `--limit 0` exits 0 with "No bookmarks found."; (4) `--sort oldest` returns rows in ascending `created_at` order; (5) `--sort newest` returns rows in descending `created_at` order; (6) `--limit -1` exits 2 with error message; (7) `--sort alpha` exits 2 with error message listing valid options
- [X] T014 [US3] Add `--limit INTEGER` (default `None`) and `--sort click.Choice(["newest", "oldest"], case_sensitive=False)` (default `"newest"`) options to `list_cmd` in `src/bookmarkcli/cli.py`; add a Click callback or `is_eager=False` parameter check to reject `--limit` values `< 0` with `click.BadParameter("'--limit' must be 0 or a positive integer.")`; pass both options to `list_filtered(limit=limit, sort=sort)`

**Checkpoint**: `uv run pytest tests/test_cli.py -k "limit or sort" -q` passes; `uv run bookmarkcli list --limit 5 --sort oldest` works end-to-end.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all user stories.

- [X] T015 Run `uv run pytest -q` to confirm all tests pass; then manually step through every command in `specs/001-list-search/quickstart.md` (add bookmarks, `list`, `list --tag`, `list --limit --sort`, `search`, piped output) to verify all acceptance scenarios from spec.md work as expected

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user story phases
- **User Story Phases (3–6)**: All depend on Phase 2 completion; can proceed in priority order
- **Polish (Phase 7)**: Depends on all user story phases being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — no story dependencies
- **US2 (P2)**: Can start after Phase 2 — independent of US1 (shares `list_filtered` from foundational)
- **US4 (P2)**: Can start after Phase 2 — independent of US1/US2 (uses `search` from foundational)
- **US3 (P3)**: Can start after Phase 2 — independent of US2 (extends `list_cmd`, but `--tag` already wired)

### Within Each Phase

- Tests MUST be written and confirmed to FAIL before corresponding implementation tasks
- T002 → T004 (same file, same test target)
- T003 → T005 (different file, different test target)
- T004 → T006 (T006 extends the same `store.py` file)
- T007 → T008, T009 → T010, T011 → T012, T013 → T014

### Parallel Opportunities

- **Phase 2**: T002 ‖ T003 (different files); T004 ‖ T005 (different files, after T002/T003)
- **Within each user story**: test task is single; implementation task is single (no intra-story parallelism)
- **Across stories after Phase 2**: US2, US4, and US3 phases can be worked by different developers simultaneously (all touch `cli.py`, so coordinate on that file)

---

## Parallel Example: Phase 2 (Foundational)

```bash
# Round 1 — write tests in parallel (different files):
Task: "Write failing tests for list_filtered() and search() in tests/test_store.py"      # T002
Task: "Create tests/test_formatting.py with failing tests for render_bookmarks_table()"  # T003

# Round 2 — implement in parallel (different files, after tests fail confirmed):
Task: "Implement BookmarkStore.list_filtered() in src/bookmarkcli/store.py"              # T004
Task: "Create src/bookmarkcli/formatting.py with render_bookmarks_table()"               # T005

# Sequential — extends same store.py file:
Task: "Implement BookmarkStore.search() in src/bookmarkcli/store.py"                     # T006
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (`uv sync` with `rich`)
2. Complete Phase 2: Foundational (store methods + formatting module)
3. Complete Phase 3: US1 (`bookmark list` basic)
4. **STOP and VALIDATE**: `uv run bookmarkcli list` works, tests pass
5. Ship MVP if sufficient

### Incremental Delivery

1. **Phase 1–2**: Foundation — `uv run pytest -q` on store + formatting tests
2. **Phase 3**: `bookmark list` → validate US1 independently
3. **Phase 4**: `bookmark list --tag` → validate US2 independently
4. **Phase 5**: `bookmark search` → validate US4 independently
5. **Phase 6**: `bookmark list --limit --sort` → validate US3 independently
6. **Phase 7**: Full suite green + quickstart walkthrough

---

## Notes

- `list` is a Python built-in; the Click command is named `"list"` but the Python function is `list_cmd`
- Tag matching is **exact** (comma-delimited `INSTR`): `--tag py` does NOT match a bookmark tagged `python`
- `--limit 0` is valid and returns an empty result set (not an error)
- `rich.console.Console` auto-detects TTY vs pipe — no `--plain` flag needed
- DB path resolution must be consistent with the S01 pattern already in `src/bookmarkcli/cli.py`
