# Tasks: Add & Delete Commands

**Input**: Design documents from `specs/001-add-delete-commands/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/cli-commands.md ✅, quickstart.md ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies between marked tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths are included in each description

---

## Phase 1: Setup (Confirm Baseline)

**Purpose**: Verify the S01 foundation is intact before making any changes.

- [X] T001 Confirm S01 baseline passes — run `uv sync && uv run pytest -q` from repo root and verify all existing tests pass

**Checkpoint**: Baseline green — feature work can begin

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Extend the storage layer with the two additions that ALL user story phases depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 Add `DuplicateBookmarkError` exception class to `src/bookmarkcli/models.py`
- [X] T003 [P] Implement `BookmarkStore.find_by_url(url: str) -> Bookmark | None` in `src/bookmarkcli/store.py` using `SELECT … WHERE url = ?`
- [X] T004 Write tests for `BookmarkStore.find_by_url()` in `tests/test_store.py` covering: URL found, URL not found, empty store

**Checkpoint**: Foundation ready — `DuplicateBookmarkError` importable, `find_by_url` tested and passing

---

## Phase 3: User Story 1 — Add a Bookmark by URL (Priority: P1) 🎯 MVP

**Goal**: Users can run `bookmarkcli add <url> [--title TEXT] [--tags TEXT]` to persist a bookmark with confirmation of the assigned ID.

**Independent Test**: `BOOKMARKCLI_DB=/tmp/test.db uv run bookmarkcli add https://example.com` prints `✓ Bookmark #1 added: https://example.com` and exits 0. Invalid URL and duplicate URL each exit 1 with a message on stderr.

- [X] T005 [P] [US1] Write `CliRunner` tests for the `add` command in `tests/test_cli.py` covering: success with URL only, success with `--title` and `--tags`, duplicate URL (exit 1), invalid URL (exit 1), tags whitespace stripping
- [X] T006 [US1] Implement the `add` Click subcommand in `src/bookmarkcli/cli.py`: URL validation via `urllib.parse.urlparse`, duplicate check via `store.find_by_url()`, tag parsing, `store.create()` call, and output `✓ Bookmark #<id> added: <url>`

**Checkpoint**: `uv run pytest -q tests/test_cli.py` passes for all US1 tests; smoke tests 4a–4d from quickstart.md pass

---

## Phase 4: User Story 2 — Delete a Bookmark by ID (Priority: P2)

**Goal**: Users can run `bookmarkcli delete <id>` to view a bookmark's details and permanently remove it after explicit `y/Y` confirmation.

**Independent Test**: Add a bookmark, note its ID, run `echo y | bookmarkcli delete <id>`, verify the entry is gone. `echo n | bookmarkcli delete <id>` prints `Cancelled.` and leaves data intact. `bookmarkcli delete 9999` exits 1 with a not-found error.

- [X] T007 [US2] Extend `tests/test_cli.py` with `CliRunner` tests for the `delete` command (ID path): confirm with `y` (exit 0, deleted), cancel with `n` (exit 0, not deleted), press Enter/default (exit 0, not deleted), ID not found (exit 1)
- [X] T008 [P] [US2] Implement the `delete` Click subcommand (ID dispatch only) in `src/bookmarkcli/cli.py`: `int(arg)` conversion, `store.get(id)`, display bookmark details, `click.confirm("Delete this bookmark?", default=False)`, call `store.delete()` on confirm, print success/cancellation messages

**Checkpoint**: `uv run pytest -q tests/test_cli.py` passes for all US2 tests; smoke tests 4e–4f from quickstart.md pass

---

## Phase 5: User Story 3 — Delete a Bookmark by URL (Priority: P3)

**Goal**: Users can run `bookmarkcli delete <url>` as a convenience alternative to delete by ID — the same confirmation flow applies.

**Independent Test**: `echo y | bookmarkcli delete https://example.com` removes the matching bookmark; `bookmarkcli delete https://unknown.com` exits 1 with a not-found message.

- [X] T009 [US3] Extend `tests/test_cli.py` with `CliRunner` tests for the delete-by-URL path: URL found + confirm (deleted), URL found + cancel (not deleted), URL not found (exit 1)
- [X] T010 [US3] Add the URL-dispatch path to the existing `delete` command in `src/bookmarkcli/cli.py`: wrap the `int(arg)` branch in try/except `ValueError`, fall through to `store.find_by_url(arg)` on `ValueError`, raise not-found error if `None` returned

**Checkpoint**: `uv run pytest -q tests/test_cli.py` passes for all US3 tests; smoke tests 4g–4h from quickstart.md pass

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and any cleanup across all stories.

- [X] T011 [P] Verify CLI help output matches `specs/001-add-delete-commands/contracts/cli-commands.md` — run `uv run bookmarkcli add --help` and `uv run bookmarkcli delete --help` and compare argument/option listings
- [X] T012 Run the full quickstart.md smoke test sequence (steps 4a–4i) end-to-end against a temporary database

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — **BLOCKS all user story phases**
- **US1 (Phase 3)**: Depends on Phase 2 (needs `DuplicateBookmarkError` and `find_by_url`)
- **US2 (Phase 4)**: Depends on Phase 2 — independent of US1
- **US3 (Phase 5)**: Depends on Phase 4 (extends the `delete` command created in T008)
- **Polish (Phase 6)**: Depends on all desired user story phases being complete

### Within Each User Story

- Tests (T005, T007, T009) should be written first so they fail before implementation — confirms tests are exercising real behavior
- Implementation tasks (T006, T008, T010) follow test tasks
- T010 (US3 implementation) depends on T008 (US2 implementation) — both touch `cli.py` `delete` command

### Parallel Opportunities

- T002 and T003 can run in parallel (different files: `models.py` vs `store.py`)
- T005 (write tests) and T006 (implementation) can overlap if one dev writes tests while another implements
- T007 (write tests) and T008 (implementation) can overlap for the same reason
- T011 (help output check) can run in parallel with T012 (smoke tests) — independent validations

---

## Parallel Example: Foundational Phase

```bash
# Run simultaneously (different files):
Task T002: "Add DuplicateBookmarkError to src/bookmarkcli/models.py"
Task T003: "Implement BookmarkStore.find_by_url() in src/bookmarkcli/store.py"
# Then sequentially:
Task T004: "Write tests for find_by_url() in tests/test_store.py"
```

## Parallel Example: User Story 1

```bash
# Overlap (different files):
Task T005: "Write CliRunner tests for add command in tests/test_cli.py"
Task T006: "Implement add subcommand in src/bookmarkcli/cli.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Verify baseline
2. Complete Phase 2: Foundational (T002–T004)
3. Complete Phase 3: User Story 1 (T005–T006)
4. **STOP and VALIDATE**: `uv run pytest -q` + quickstart steps 4a–4d
5. Ship / demo if ready

### Incremental Delivery

1. Setup + Foundational → storage layer extended
2. US1 complete → `add` command working (MVP)
3. US2 complete → `delete <id>` working
4. US3 complete → `delete <url>` convenience path working
5. Polish → full smoke test passes, docs verified

### Story Independence

- US1 is self-contained in `cli.py` (add subcommand) — no dependency on US2/US3
- US2 introduces the `delete` command structure; US3 is an additive path on the same command
- Each story's tests live in `tests/test_cli.py` as distinct test functions — they do not conflict
