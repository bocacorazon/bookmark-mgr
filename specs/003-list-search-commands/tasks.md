# Tasks: List & Search Commands

**Input**: Design documents from `/specs/003-list-search-commands/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/cli-schema.md ✅, quickstart.md ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths are included in every description

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add new runtime dependency required by all rendering work.

- [X] T001 Add `rich>=13.0` to `[project.dependencies]` in `pyproject.toml` and run `uv sync` to install

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before any user story can be implemented. Both `bookmark list` (US1/US2) and `bookmark search` (US3) depend on `formatter.py`, and `list_filtered` is shared by US1 and US2.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 Create `src/bookmarkcli/formatter.py` with `render_table(bookmarks, *, plain=False, query=None)`: TTY auto-detection via `sys.stdout.isatty()`, rich `Console`/`Table` rendering with columns ID (max 6), Title (max 40, overflow ellipsis), URL (max 50, overflow ellipsis), Tags (max 25, overflow ellipsis), Date Added (max 20); plain tab-separated fallback with header row; "No bookmarks found." empty-state message; `_truncate(value, max_len)` helper for plain mode
- [X] T003 Add `list_filtered(self, tag=None, limit=None, sort="date")` method to `src/bookmarkcli/store.py`: parameterised SQL with four-disjunct tag pattern (`tags = ?` / `LIKE ? || ',%'` / `LIKE '%,' || ?` / `LIKE '%,' || ? || ',%'`), `ORDER BY` using `CASE` for title/url/date (newest-first default), `LIMIT ?` clause when limit is provided, raises `ValueError` for invalid sort values

**Checkpoint**: `formatter.py` and `list_filtered` are ready — user story implementation can begin.

---

## Phase 3: User Story 1 — List All Bookmarks (Priority: P1) 🎯 MVP

**Goal**: Users can run `bookmark list` and see all stored bookmarks in a readable table with rich output in a terminal and plain text when piped.

**Independent Test**: Run `bookmark list` against a store with several bookmarks; verify a formatted table is printed with one row per bookmark showing ID, title, URL, tags, and date added. Run `bookmark list | cat` and verify plain tab-separated output with no ANSI codes.

- [X] T004 [P] [US1] Add `render_table` unit tests in `tests/test_formatter.py`: rich mode with mock TTY (verify Console called with `force_terminal=True`), plain mode with `plain=True` (verify tab-separated header + rows), non-TTY stdout falls back to plain, empty bookmarks list prints `"No bookmarks found."`
- [X] T005 [P] [US1] Add `list_filtered` baseline unit tests in `tests/test_store.py`: call with no arguments returns all bookmarks, default sort is newest-first by `created_at DESC`, returns empty list when store is empty
- [X] T006 [US1] Add `bookmark list` command to `src/bookmarkcli/cli.py`: register `list` as a `@main.command()`, add `--plain` flag (`is_flag=True, default=False`), call `store.initialize()` then `store.list_filtered()` with no filter args, call `render_table(bookmarks, plain=plain)`, handle `RuntimeError` with `click.echo` + `sys.exit(1)`
- [X] T007 [US1] Add `bookmark list` CLI integration tests in `tests/test_cli.py` using `click.testing.CliRunner`: empty store shows `"No bookmarks found."`, store with bookmarks shows one row per bookmark, `--plain` produces tab-separated output, rich mode with `mix_stderr=False` and TTY mock shows formatted output

**Checkpoint**: `bookmark list` (no options) is fully functional and independently testable — MVP deliverable.

---

## Phase 4: User Story 2 — Filter and Sort the List (Priority: P2)

**Goal**: Users can narrow and reorder `bookmark list` results using `--tag`, `--limit`, and `--sort` options, with correct filter-before-limit and sort-before-limit ordering.

**Independent Test**: Run `bookmark list --tag dev --limit 5 --sort title` against a populated store; verify only bookmarks tagged "dev" appear, at most 5 rows, alphabetically sorted by title.

- [X] T008 [US2] Extend `bookmark list` command in `src/bookmarkcli/cli.py`: add `--tag TEXT` (`default=None`), `--limit` (`type=click.IntRange(min=1), default=None`), `--sort` (`type=click.Choice(["date","title","url"]), default="date"`); pass all three to `store.list_filtered(tag=tag, limit=limit, sort=sort)`
- [X] T009 [P] [US2] Add `list_filtered` filter/sort unit tests in `tests/test_store.py`: `--tag` returns only exact-match bookmarks (case-sensitive), middle/first/last tag positions all match, unknown tag returns empty list, `--limit 2` caps results, `--sort title` returns ascending by title (case-insensitive), `--sort url` returns ascending by url, `--sort date` returns newest-first, combined `tag + limit` applies filter before cap
- [X] T010 [P] [US2] Add filter/sort CLI integration tests in `tests/test_cli.py`: `--tag` filters correctly, `--limit` caps output rows, `--sort title` reorders results, `--limit 0` exits with code 2 and error message, `--sort invalid` exits with code 2, combined `--tag + --limit` applies filter before limit

**Checkpoint**: `bookmark list` with any combination of `--tag`, `--limit`, `--sort` works correctly and independently.

---

## Phase 5: User Story 3 — Search Bookmarks by Keyword (Priority: P3)

**Goal**: Users can run `bookmark search <query>` to find bookmarks whose title or URL contains the query (case-insensitive), with matching terms highlighted in rich mode.

**Independent Test**: Run `bookmark search github` against a store containing bookmarks; verify only bookmarks whose title or URL includes "github" (case-insensitive) are returned in tabular format.

- [X] T011 [US3] Add `_escape_like(query)` helper and `search(self, query)` method to `src/bookmarkcli/store.py`: escape `\`, `%`, `_` in query before embedding; SQL `WHERE LOWER(title) LIKE '%' || LOWER(?) || '%' ESCAPE '\' OR LOWER(url) LIKE '%' || LOWER(?) || '%' ESCAPE '\'`; `ORDER BY created_at DESC`
- [X] T012 [US3] Extend `src/bookmarkcli/formatter.py` to support `query` highlighting: when `query` is not None and in rich mode, wrap Title and URL cell values as `rich.text.Text` objects and apply `Text.highlight_regex(re.escape(query), style="bold yellow", flags=re.IGNORECASE)`
- [X] T013 [US3] Add `bookmark search` command to `src/bookmarkcli/cli.py`: positional `QUERY` argument (`required=True`), guard against empty string with `click.UsageError`, `--plain` flag, call `store.initialize()` then `store.search(query)`, call `render_table(bookmarks, plain=plain, query=query)`, empty-results message uses `"No bookmarks matched \"{query}\"."` format, handle `RuntimeError` with exit code 1
- [X] T014 [P] [US3] Add `search` store unit tests in `tests/test_store.py`: basic substring match in title, match in URL, case-insensitive match, no-match returns empty list, `%` and `_` in query treated as literals (no wildcard expansion), special chars like `https://` match correctly, OR logic — title match alone and URL match alone both return bookmark
- [X] T015 [P] [US3] Add `bookmark search` CLI integration tests in `tests/test_cli.py`: basic query returns matching rows, no-match shows `"No bookmarks matched"` message, `--plain` suppresses ANSI codes, piped output is plain text, empty QUERY exits code 2
- [X] T016 [P] [US3] Add highlight unit tests in `tests/test_formatter.py`: `render_table` with `query="github"` in rich mode includes highlighted Text for matching terms, plain mode with query produces no escape codes

**Checkpoint**: `bookmark search <query>` is fully functional with highlighting in rich mode and plain text when piped.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate edge cases, error paths, and end-to-end quickstart scenarios.

- [X] T017 Verify all error/edge-case paths across `src/bookmarkcli/cli.py`: `--limit 0` → exit 2, `--limit abc` → exit 2, `--sort newest` → exit 2, `bookmark search ""` → exit 2, unreadable DB → exit 1; confirm error messages are human-readable per FR-017
- [X] T018 Run full quickstart.md validation: `uv sync`, `uv run bookmarkcli list`, `uv run bookmarkcli list --tag python`, `uv run bookmarkcli list --limit 5 --sort title`, `uv run bookmarkcli search github`, `uv run bookmarkcli search "https://"`, `uv run bookmarkcli list --plain | head`, `uv run pytest -q` — all must exit 0

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (T001 must complete before T002/T003)
- **User Stories (Phases 3–5)**: All depend on Phase 2 completion
  - US1 can start after T002 + T003 complete
  - US2 depends on US1's `list` command existing in `cli.py` (T006 must precede T008)
  - US3 is independent of US1/US2 once Phase 2 is done
- **Polish (Phase 6)**: Depends on all user story phases completing

### User Story Dependencies

- **US1 (P1)**: Requires Phase 2 complete — independent of US2 and US3
- **US2 (P2)**: Requires Phase 2 complete AND T006 (list command) — extends US1's `list` command
- **US3 (P3)**: Requires Phase 2 complete — fully independent of US1/US2

### Within Each User Story

- Implementation task (adding the command/method) before its CLI integration tests
- Store method tests (T005, T009, T014) are independent of command implementation
- Formatter tests (T004, T016) are independent of command implementation

### Parallel Opportunities

- **Phase 2**: T002 and T003 touch different parts of different files — can be done concurrently
- **Phase 3**: T004, T005, T006 can all start in parallel (different files); T007 depends on T006
- **Phase 4**: T009 and T010 are parallel (different concerns); T008 must precede T010
- **Phase 5**: T011 and T012 can start in parallel (different files); T013, T014, T015, T016 all parallel (different files); T015 depends on T012 being complete

---

## Parallel Examples

### Phase 3 (US1)

```
# Parallel start — all independent files:
T004: tests/test_formatter.py  (render_table unit tests)
T005: tests/test_store.py      (list_filtered baseline tests)
T006: src/bookmarkcli/cli.py   (add list command)

# After T006 completes:
T007: tests/test_cli.py        (list CLI integration tests)
```

### Phase 4 (US2)

```
# T008 first (extends cli.py), then parallel:
T009: tests/test_store.py      (filter/sort store tests)
T010: tests/test_cli.py        (filter/sort CLI tests)
```

### Phase 5 (US3)

```
# Parallel start:
T011: src/bookmarkcli/store.py    (search method)
T012: src/bookmarkcli/formatter.py (highlight support)

# After T011 + T012:
T013: src/bookmarkcli/cli.py      (search command)

# Parallel after T013:
T014: tests/test_cli.py           (search CLI tests)
T015: tests/test_cli.py           (search CLI tests — bookmark search)
T016: tests/test_formatter.py     (highlight unit tests)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: add `rich` dependency
2. Complete Phase 2: `formatter.py` + `list_filtered` in store
3. Complete Phase 3: basic `bookmark list` command + tests
4. **STOP and VALIDATE**: `uv run bookmarkcli list` works; `uv run pytest -q` passes
5. Ship MVP — users can browse their bookmarks

### Incremental Delivery

1. Setup + Foundational → dependency and core rendering ready
2. Add US1 → test independently → **MVP: `bookmark list` works**
3. Add US2 → test independently → **Enhanced: filtering and sorting work**
4. Add US3 → test independently → **Full feature: `bookmark search` with highlighting**
5. Polish → validate all edge cases and quickstart end-to-end

### Parallel Team Strategy

With two developers after Phase 2:

- Developer A: US1 (T004–T007) then US2 (T008–T010)
- Developer B: US3 (T011–T016) independently

---

## Notes

- [P] tasks operate on different files with no cross-dependencies — safe to parallelize
- [Story] label maps each task to its user story for traceability
- `rich.console.Console(force_terminal=...)` is the single TTY-detection point — keep it in `formatter.py`
- Tag filtering SQL uses four disjuncts to handle all comma-separated positions (see research.md §4)
- `_escape_like` must escape `\` first, then `%`, then `_` to avoid double-escaping
- Commit after each completed task or logical group
- Stop at Phase 3 checkpoint to validate US1 independently before proceeding
