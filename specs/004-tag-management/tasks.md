---

description: "Task list for Tag Management (S04)"
---

# Tasks: Tag Management

**Input**: Design documents from `/specs/004-tag-management/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/cli.md ✅, quickstart.md ✅

**Tests**: Included — required by SC-006 ("All functional requirements have at least one automated test, and all tests pass with zero failures.")

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm baseline is green before any new code is added.

No new runtime dependencies, no schema migrations required (tags TEXT column already exists from S02).

- [X] T001 Verify baseline test suite passes: run `uv run pytest -q` from repo root and confirm all existing tests pass

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Domain types shared by all three user stories; MUST be complete before any story work begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 Add `normalize_tag()` function, `TagNotFoundError` exception class, and `TagValidationError` exception class to `src/bookmarkcli/models.py`

**Checkpoint**: Domain types available — user story implementation can now begin.

---

## Phase 3: User Story 1 — Add a Tag to a Bookmark (Priority: P1) 🎯 MVP

**Goal**: Users can run `bookmarkcli tag <id> --add <tag>` to add a normalized tag to an existing bookmark. The tag is persisted immediately and is idempotent on duplicate adds.

**Independent Test**: Add a bookmark, run `bookmarkcli tag <id> --add python`, retrieve the bookmark, confirm "python" is in its tag list.

### Tests for User Story 1 ⚠️ Write FIRST — ensure they FAIL before implementing

- [X] T003 [P] [US1] Write `add_tag()` store tests (happy path, idempotent add, bookmark-not-found, tag-validation-error, case/whitespace normalization) in `tests/test_store.py`
- [X] T004 [P] [US1] Create `tests/test_cli.py` with `tag --add` command tests: newly added (exit 0, stdout confirmation), idempotent add (exit 0, already-has-tag message), bookmark-not-found (exit 1, stderr error), empty/whitespace tag (exit 1, stderr error), neither flag provided (exit 2, stderr error)

### Implementation for User Story 1

- [X] T005 [US1] Implement `BookmarkStore.add_tag(bookmark_id, tag)` in `src/bookmarkcli/store.py`: normalize via `normalize_tag()`, raise `TagValidationError` if empty, raise `BookmarkNotFoundError` if ID missing, skip if already present (idempotent), append and persist via `update()`, return `Bookmark`
- [X] T006 [US1] Implement `tag` command in `src/bookmarkcli/cli.py`: define `BOOKMARK_ID` argument, `--add TEXT` option, `--remove TEXT` option; add inline validation (both flags → `UsageError` exit 2; neither flag → `UsageError` exit 2); implement `--add` branch calling `store.add_tag()` with stdout confirmation messages and stderr error handling (exit 1 for `BookmarkNotFoundError`/`TagValidationError`)

**Checkpoint**: User Story 1 fully functional. `bookmarkcli tag <id> --add <tag>` works end-to-end with all acceptance scenarios passing.

---

## Phase 4: User Story 2 — Remove a Tag from a Bookmark (Priority: P2)

**Goal**: Users can run `bookmarkcli tag <id> --remove <tag>` to remove a normalized tag from a bookmark. Clear error shown if tag not present or bookmark not found.

**Independent Test**: Add a bookmark with a tag, run `bookmarkcli tag <id> --remove <tag>`, retrieve the bookmark, confirm the tag no longer appears.

### Tests for User Story 2 ⚠️ Write FIRST — ensure they FAIL before implementing

- [X] T007 [P] [US2] Write `remove_tag()` store tests (happy path, tag-not-found, bookmark-not-found, tag-validation-error, case/whitespace normalization, multi-tag bookmark preserves remaining tags) in `tests/test_store.py`
- [X] T008 [P] [US2] Write `tag --remove` CLI tests in `tests/test_cli.py`: tag removed (exit 0, stdout confirmation), tag not on bookmark (exit 1, stderr error), bookmark-not-found (exit 1, stderr error), whitespace/case normalization, both `--add` and `--remove` provided (exit 2, stderr mutual-exclusion error)

### Implementation for User Story 2

- [X] T009 [US2] Implement `BookmarkStore.remove_tag(bookmark_id, tag)` in `src/bookmarkcli/store.py`: normalize via `normalize_tag()`, raise `TagValidationError` if empty, raise `BookmarkNotFoundError` if ID missing, raise `TagNotFoundError` if tag not in list, remove tag and persist via `update()`, return updated `Bookmark`
- [X] T010 [US2] Add `--remove` branch handling and complete `--add`/`--remove` mutual exclusion in `tag` command in `src/bookmarkcli/cli.py`: implement `--remove` path calling `store.remove_tag()` with stdout confirmation and stderr error handling (exit 1 for `BookmarkNotFoundError`/`TagNotFoundError`/`TagValidationError`)

**Checkpoint**: User Stories 1 and 2 both work independently. Full tag lifecycle (add + remove) operational.

---

## Phase 5: User Story 3 — List All Tags with Counts (Priority: P3)

**Goal**: Users can run `bookmarkcli tags` to see all tags in use across their bookmark collection, each paired with a bookmark count, sorted alphabetically. Shows "No tags found." when no tags are in use.

**Independent Test**: Add several bookmarks with overlapping tags, run `bookmarkcli tags`, confirm each unique tag and its correct count appear in alphabetical order.

### Tests for User Story 3 ⚠️ Write FIRST — ensure they FAIL before implementing

- [X] T011 [P] [US3] Write `list_tags()` store tests (empty store returns `[]`, single tag, multiple bookmarks with overlapping tags returns correct counts, alphabetical sort, removed tags no longer appear) in `tests/test_store.py`
- [X] T012 [P] [US3] Write `tags` CLI tests in `tests/test_cli.py`: tags exist (exit 0, stdout with two-space-separated `tag  count` lines in alphabetical order), no tags in use (exit 0, "No tags found." on stdout)

### Implementation for User Story 3

- [X] T013 [US3] Implement `BookmarkStore.list_tags()` in `src/bookmarkcli/store.py`: single `SELECT tags FROM bookmarks WHERE tags != ''`, parse with `_deserialize_tags()`, count per-tag with `dict`, return `sorted(counts.items())` as `list[tuple[str, int]]`
- [X] T014 [US3] Implement `tags` command in `src/bookmarkcli/cli.py`: call `store.list_tags()`, print "No tags found." if empty, otherwise print each `(tag, count)` pair as `f"{tag}  {count}"` (two spaces) in the order returned

**Checkpoint**: All three user stories fully functional and independently testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and edge-case coverage across all stories.

- [X] T015 [P] Add edge-case tests not covered in story phases: all-whitespace tag rejected by `add_tag` and `remove_tag` store methods in `tests/test_store.py`; `bookmark tags` output reflects state immediately after add/remove operations in `tests/test_cli.py`
- [X] T016 Run full quickstart validation: `uv run pytest -q` (all tests pass), `uv run bookmarkcli --help` (shows `tag` and `tags` subcommands), and smoke-test the usage examples from `specs/004-tag-management/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — **BLOCKS all user stories**
- **User Stories (Phase 3–5)**: All depend on Foundational completion
  - US1 (Phase 3) must complete before US2 (Phase 4) due to shared `tag` command in `cli.py`
  - US3 (Phase 5) can start after Foundational (Phase 2); independent of US1/US2
- **Polish (Phase 6)**: Depends on all user story phases completing

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2)
- **User Story 2 (P2)**: Can start after Phase 2; extends `tag` command built in US1 — sequentially after US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2); fully independent of US1 and US2

### Within Each User Story

- Tests MUST be written and confirmed to FAIL before running implementation tasks
- Store method before CLI command (CLI depends on store)
- Both test tasks marked [P] within a story can run in parallel (different files)

### Parallel Opportunities

- T003 and T004 (US1 tests): parallel — different files
- T007 and T008 (US2 tests): parallel — different files
- T011 and T012 (US3 tests): parallel — different files
- T011/T012 (US3 tests) can run in parallel with T007/T008 (US2 tests) — independent stories

---

## Parallel Example: User Story 1

```bash
# Launch both test tasks for US1 simultaneously:
Task: "Write add_tag() store tests in tests/test_store.py"         # T003
Task: "Create tests/test_cli.py with tag --add CLI tests"          # T004

# After tests confirmed FAILING, implement sequentially:
Task: "Implement BookmarkStore.add_tag() in src/bookmarkcli/store.py"   # T005
Task: "Implement tag command (--add branch) in src/bookmarkcli/cli.py"  # T006
```

## Parallel Example: User Stories 2 & 3 (if team has capacity)

```bash
# After Phase 2 complete, launch US2 and US3 test tasks simultaneously:
Task: "Write remove_tag() store tests in tests/test_store.py"      # T007
Task: "Write tag --remove CLI tests in tests/test_cli.py"          # T008
Task: "Write list_tags() store tests in tests/test_store.py"       # T011
Task: "Write tags CLI tests in tests/test_cli.py"                  # T012
# Note: T008 and T012 both write to tests/test_cli.py — serialize these two
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Verify baseline
2. Complete Phase 2: Add domain types to models.py (T002)
3. Complete Phase 3: US1 — add tag command (T003 → T004 → T005 → T006)
4. **STOP and VALIDATE**: `bookmarkcli tag <id> --add <tag>` works end-to-end
5. Ship MVP if ready

### Incremental Delivery

1. Phase 1 + 2 → Domain types ready
2. Phase 3 → Add tag works → Ship MVP
3. Phase 4 → Remove tag works → Ship increment
4. Phase 5 → List tags works → Ship full feature
5. Phase 6 → All edge cases covered → Polish release

### Notes

- No new runtime packages needed; no `pyproject.toml` changes required
- No schema migration needed; `tags TEXT` column already exists from S02
- `test_cli.py` is a NEW file — T004 creates it; subsequent test tasks append to it
- `test_store.py` is an EXISTING file — test tasks append to existing file
- Confirmation messages always echo the **normalized** form of the tag (see contracts/cli.md)
- Use `CliRunner()` without `mix_stderr=True`; assert `result.stdout` / `result.stderr` separately (project convention)
