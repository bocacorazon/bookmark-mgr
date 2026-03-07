---
description: "Task list for 002-data-model-storage implementation"
---

# Tasks: Data Model & Storage

**Input**: Design documents from `/specs/002-data-model-storage/`
**Prerequisites**: plan.md ✅, spec.md ✅, data-model.md ✅, research.md ✅, contracts/python-api.md ✅, quickstart.md ✅

**Tests**: Included — FR-014 and SC-005 explicitly require a full pytest suite covering all CRUD operations, schema initialisation, migration, and edge cases.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5)
- Exact file paths included in every description

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm existing scaffold is compatible with this feature's plan before writing any code.

- [X] T001 Verify src/bookmarkcli/ contains `__init__.py` and `cli.py`, and tests/ contains `__init__.py`, matching the project layout in plan.md section "Project Structure"

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Pure domain types used by every user story — must exist before any CRUD code or tests can be written.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 Create `src/bookmarkcli/models.py` — `@dataclass Bookmark` (fields: `id: int | None`, `url: str`, `created_at: datetime`, `updated_at: datetime`, `title: str | None = None`, `tags: list[str] = field(default_factory=list)`), `_MISSING_TYPE` class and module-level `MISSING` sentinel, `BookmarkNotFoundError(Exception)`, `BookmarkValidationError(Exception)`

**Checkpoint**: Foundation ready — all user story phases may now begin.

---

## Phase 3: User Story 5 — Automatic Storage Initialization (Priority: P1)

**Goal**: On first use `BookmarkStore` creates the SQLite schema automatically; on subsequent uses it uses the existing store unchanged; if schema is at an older version it migrates without data loss.

**Independent Test**: Instantiate `BookmarkStore` against a temp path, call `initialize()`, assert the `bookmarks` table exists; call `initialize()` again and assert no error; seed a v0 database, call `initialize()`, assert seeded rows are still present.

### Tests for User Story 5

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation (T005)**

- [X] T003 [US5] Create `src/bookmarkcli/store.py` — `BookmarkStore` class with `__init__(self, db_path: str | Path) -> None` (stores path, sets `_con = None`), `_MIGRATIONS: list[str]` (one entry: v0→v1 `CREATE TABLE bookmarks (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT NOT NULL, title TEXT, tags TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL)`), private helpers `_serialize_tags`, `_deserialize_tags`, `_row_to_bookmark`
- [X] T004 [P] [US5] Create `tests/test_store.py` — `@pytest.fixture store(tmp_path)` that constructs and initialises a `BookmarkStore`, then write: `test_initialize_creates_bookmarks_table`, `test_initialize_is_idempotent`, `test_migration_v0_to_v1_preserves_seeded_row` (seed old schema with `sqlite3` directly per quickstart.md section 8)
- [X] T005 [US5] Implement `BookmarkStore.initialize()` in `src/bookmarkcli/store.py` — open `sqlite3.connect(db_path)`, read `PRAGMA user_version`, iterate `_MIGRATIONS` applying each pending SQL, set `PRAGMA user_version` to current schema version (`1`) after all migrations

**Checkpoint**: US5 tests pass — storage initialises and migrates correctly.

---

## Phase 4: User Story 1 — Save a New Bookmark (Priority: P1) 🎯 MVP

**Goal**: A caller passes a URL (plus optional title and tags) to `BookmarkStore.create()` and receives back a persisted `Bookmark` with a unique integer ID and UTC timestamps.

**Independent Test**: After `store.create(url="https://example.com")`, assert the returned bookmark has a non-None `id`; call `store.get(bookmark.id)` and assert the URL matches.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation (T007)**

- [X] T006 [P] [US1] Add create() tests to `tests/test_store.py` — `test_create_url_only_returns_bookmark_with_id`, `test_create_with_title_and_tags_stores_all_fields`, `test_create_empty_url_raises_BookmarkValidationError`, `test_create_whitespace_url_raises_BookmarkValidationError`, `test_create_sets_created_at_and_updated_at_to_utc`
- [X] T007 [US1] Implement `BookmarkStore.create()` in `src/bookmarkcli/store.py` — validate `url` is non-empty (raise `BookmarkValidationError`), insert row with `datetime.now(tz=timezone.utc)` for both timestamps, return `Bookmark` dataclass with assigned `id`

**Checkpoint**: US1 tests pass — bookmarks can be saved and re-fetched by ID.

---

## Phase 5: User Story 2 — Retrieve Saved Bookmarks (Priority: P2)

**Goal**: A caller can fetch one bookmark by its ID (`get`) or retrieve all bookmarks in ID order (`list_all`). Missing IDs signal `BookmarkNotFoundError`.

**Independent Test**: Save three bookmarks, call `list_all()` and assert length is 3; call `get(id)` for each and assert fields round-trip correctly; call `get(9999)` and assert `BookmarkNotFoundError` is raised.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation (T009, T010)**

- [X] T008 [P] [US2] Add get()/list_all() tests to `tests/test_store.py` — `test_get_returns_correct_bookmark`, `test_get_preserves_all_fields`, `test_get_nonexistent_raises_BookmarkNotFoundError`, `test_list_all_empty_store_returns_empty_list`, `test_list_all_returns_all_records`, `test_list_all_ordered_by_id_ascending`
- [X] T009 [US2] Implement `BookmarkStore.get()` in `src/bookmarkcli/store.py` — `SELECT` row by `id`, raise `BookmarkNotFoundError` if not found, deserialise and return `Bookmark`
- [X] T010 [US2] Implement `BookmarkStore.list_all()` in `src/bookmarkcli/store.py` — `SELECT` all rows `ORDER BY id ASC`, return `list[Bookmark]` (empty list when store is empty)

**Checkpoint**: US2 tests pass — bookmarks can be retrieved individually and in bulk.

---

## Phase 6: User Story 3 — Update an Existing Bookmark (Priority: P3)

**Goal**: A caller can change the `title` and/or `tags` of a persisted bookmark; `updated_at` is always refreshed. Passing `MISSING` for a field leaves it unchanged. Passing `None` for `title` clears it. Passing `[]` for `tags` clears them.

**Independent Test**: Save a bookmark, update its title, retrieve it, assert the new title is stored and `updated_at > created_at`. Update with no fields; assert `updated_at` was still refreshed.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation (T012)**

- [X] T011 [P] [US3] Add update() tests to `tests/test_store.py` — `test_update_title_changes_stored_value`, `test_update_refreshes_updated_at_timestamp`, `test_update_add_tags_to_tagless_bookmark`, `test_update_clear_tags_with_empty_list`, `test_update_missing_fields_leaves_them_unchanged`, `test_update_no_fields_still_refreshes_updated_at`, `test_update_nonexistent_raises_BookmarkNotFoundError`
- [X] T012 [US3] Implement `BookmarkStore.update()` in `src/bookmarkcli/store.py` — verify record exists (raise `BookmarkNotFoundError` if not), build `SET` clause including only non-`MISSING` fields plus `updated_at = UTC now`, execute `UPDATE`, return refreshed `Bookmark` via `get()`

**Checkpoint**: US3 tests pass — bookmarks can be partially or fully updated.

---

## Phase 7: User Story 4 — Delete a Bookmark (Priority: P4)

**Goal**: A caller permanently removes a bookmark by ID. Subsequent `get` on that ID raises `BookmarkNotFoundError`. Deleting a non-existent ID raises `BookmarkNotFoundError` immediately.

**Independent Test**: Save two bookmarks, delete one, assert `list_all()` returns one record, assert `get(deleted_id)` raises `BookmarkNotFoundError`.

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation (T014)**

- [X] T013 [P] [US4] Add delete() tests to `tests/test_store.py` — `test_delete_removes_record`, `test_delete_reduces_list_all_count`, `test_deleted_id_raises_BookmarkNotFoundError_on_get`, `test_delete_nonexistent_raises_BookmarkNotFoundError`
- [X] T014 [US4] Implement `BookmarkStore.delete()` in `src/bookmarkcli/store.py` — verify record exists (raise `BookmarkNotFoundError` if not), execute `DELETE FROM bookmarks WHERE id = ?`, return `None`

**Checkpoint**: US4 tests pass — all CRUD operations are complete and independently tested.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Edge cases from spec, performance criteria, and final validation.

- [X] T015 [P] Add edge case and performance tests to `tests/test_store.py` — `test_duplicate_urls_produce_distinct_records`, `test_create_tags_none_treated_as_empty_list`, `test_update_no_change_still_refreshes_updated_at` (mirrors spec edge cases), `test_list_all_10000_records_completes_under_2s` (SC-004)
- [X] T016 Run `uv run pytest -q` from repository root and confirm all tests pass (target: 23 passed per quickstart.md) with zero failures, satisfying SC-005

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — **BLOCKS all user stories**
- **US5 (Phase 3)**: Depends on Phase 2 (needs `Bookmark`, exceptions, `MISSING` from models.py)
- **US1 (Phase 4)**: Depends on Phase 3 (needs `initialize()` to open the DB before `create()` works)
- **US2 (Phase 5)**: Depends on Phase 4 (test pattern saves a record before retrieving it)
- **US3 (Phase 6)**: Depends on Phase 5 (update tests save and retrieve via `get()`)
- **US4 (Phase 7)**: Depends on Phase 5 (delete tests verify with `list_all()` and `get()`)
- **Polish (Phase 8)**: Depends on Phase 7 — all CRUD implemented

### User Story Dependencies

| Story | Depends on | Notes |
|-------|-----------|-------|
| US5 (init) | Foundational | Blocking prerequisite for all CRUD |
| US1 (create) | US5 | `initialize()` must succeed before create |
| US2 (retrieve) | US1 | Tests save records first |
| US3 (update) | US2 | Tests use `get()` to verify update |
| US4 (delete) | US2 | Tests verify with `list_all()` and `get()` |

### Within Each User Story

- Tests MUST be written first and confirmed to FAIL before adding implementation
- Private helpers (`_serialize_tags`, `_deserialize_tags`, `_row_to_bookmark`) are created in T003 and shared by all subsequent story phases
- All methods live in `src/bookmarkcli/store.py`; all tests live in `tests/test_store.py`

### Parallel Opportunities

- **T004 [P]** (test_store.py creation) can run alongside **T005** (store.py initialize implementation) — different files
- **T006 [P]** (create tests) can run alongside **T007** (create implementation) — different files
- **T008 [P]** (get/list_all tests) can run alongside **T009/T010** (implementations) — different files
- **T011 [P]** (update tests) can run alongside **T012** (update implementation) — different files
- **T013 [P]** (delete tests) can run alongside **T014** (delete implementation) — different files
- **T015 [P]** (edge case tests) can run alongside **T016** (final test run) — different concerns

---

## Parallel Example: User Story 1

```bash
# Developer A writes failing tests while Developer B implements:
Task T006: "Add create() tests to tests/test_store.py"
Task T007: "Implement BookmarkStore.create() in src/bookmarkcli/store.py"
# Both are in different files — start together; merge when both complete
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational — models.py (T002)
3. Complete Phase 3: US5 — store.py init (T003–T005)
4. Complete Phase 4: US1 — create (T006–T007)
5. **STOP and VALIDATE**: `uv run pytest -q` should show passing tests for US5 + US1

### Incremental Delivery

1. Setup + Foundational + US5 → store initialises ✅
2. Add US1 → bookmarks can be saved ✅
3. Add US2 → bookmarks can be retrieved ✅
4. Add US3 → bookmarks can be updated ✅
5. Add US4 → bookmarks can be deleted ✅ (full CRUD)
6. Polish → all 23 tests pass ✅

### Single-Developer Strategy

Work story by story in priority order: US5 → US1 → US2 → US3 → US4 → Polish.
Within each story: write tests (FAIL) → implement → confirm tests pass → commit.

---

## Notes

- `[P]` tasks are always in a different file from their paired implementation task — safe to run in parallel on a team
- `[Story]` label maps each task to its acceptance scenarios in spec.md for traceability
- No new runtime dependencies — `sqlite3` is stdlib; `pytest ≥ 8.0` is already in dev dependency-group
- All timestamps must be `timezone.utc`-aware `datetime` objects; never use naive datetimes
- `MISSING` sentinel distinguishes "field not provided" from `None` (clear the field) in `update()`
- Tags serialisation: `","`.join on write; `[t for t in s.split(",") if t]` on read — empty list ↔ `""`
- `BookmarkStore` does **not** open a connection in `__init__`; `initialize()` must be called first
- Commit after each story phase checkpoint or after any green test run
