---

description: "Task list for Project Scaffold implementation"

---

# Tasks: Project Scaffold

**Input**: Design documents from `/specs/001-project-scaffold/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/cli.md ✅, quickstart.md ✅

**Tests**: No test tasks generated — tests were not requested in this feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths are included in each description

## Path Conventions

Single-project src-layout:

- Source: `src/bookmarkcli/`
- Tests: `tests/`
- Config: `pyproject.toml`, `conftest.py`, `uv.lock` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the repository directory structure required for the src-layout convention.

- [X] T001 Create project directory structure: `src/bookmarkcli/` and `tests/` under repository root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core scaffolding files that MUST exist before any user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 Create `pyproject.toml` with project metadata (`name = "bookmark-mgr"`, `version = "0.1.0"`, `requires-python = ">=3.11"`), `[build-system]` block declaring `hatchling` as the build backend, and `[tool.hatch.build.targets.wheel]` with `packages = ["src/bookmarkcli"]` in `pyproject.toml`
- [X] T003 [P] Create empty package namespace file in `src/bookmarkcli/__init__.py`
- [X] T004 [P] Create empty test package marker file in `tests/__init__.py`

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 - Bootstrap Project Environment (Priority: P1) 🎯 MVP

**Goal**: A developer with Python ≥ 3.11 and `uv` installed can run `uv sync` on a fresh clone and immediately have all runtime and development dependencies installed with `bookmarkcli` available on the PATH.

**Independent Test**: Fresh clone → `uv sync` exits 0; `uv run bookmarkcli --help` exits 0.

### Implementation for User Story 1

- [X] T005 [US1] Add `click>=8.0` to `[project.dependencies]`, `pytest>=8.0` and `aiosqlite>=0.20` to `[dependency-groups] dev`, and `bookmarkcli = "bookmarkcli.cli:main"` to `[project.scripts]` in `pyproject.toml`
- [X] T006 [P] [US1] Create `@click.group()` decorated `main` function with docstring `"Bookmark manager CLI."` in `src/bookmarkcli/cli.py`
- [X] T007 [US1] Run `uv lock` to generate the complete reproducible locked dependency graph in `uv.lock` and commit it

**Checkpoint**: User Story 1 fully functional — `uv sync` installs all dependencies and `bookmarkcli` entry point is registered.

---

## Phase 4: User Story 2 - Run Test Suite with No Tests (Priority: P2)

**Goal**: Running `uv run pytest -q` on the unmodified scaffold exits with code 0 even when zero test functions are collected, so CI pipelines report success on a fresh project.

**Independent Test**: `uv run pytest -q` exits 0 and output contains `no tests ran`.

### Implementation for User Story 2

- [X] T008 [US2] Add `[tool.pytest.ini_options]` section with `testpaths = ["tests"]` to `pyproject.toml`
- [X] T009 [P] [US2] Create `conftest.py` at repository root with a `pytest_sessionfinish` hook that sets `session.exitstatus = 0` when `exitstatus == 5` ("no tests collected") in `conftest.py`

**Checkpoint**: User Stories 1 and 2 both independently functional.

---

## Phase 5: User Story 3 - Invoke the CLI Entry Point (Priority: P3)

**Goal**: `bookmarkcli --help` prints usage/help text and exits with code 0, confirming the Click-based CLI group is wired up correctly per `contracts/cli.md`.

**Independent Test**: `uv run bookmarkcli --help` exits 0 and output contains `"Bookmark manager CLI."`.

### Implementation for User Story 3

- [X] T010 [US3] Run `uv sync` to install the package editably, registering the `bookmarkcli` console script declared in `pyproject.toml`
- [X] T011 [US3] Verify CLI contract per `contracts/cli.md`: run `uv run bookmarkcli --help` and confirm output shows `"Usage: bookmarkcli [OPTIONS] COMMAND [ARGS]..."`, description `"Bookmark manager CLI."`, and exits 0

**Checkpoint**: All three user stories independently functional; scaffold is complete.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final end-to-end validation confirming all acceptance criteria are met.

- [X] T012 Run full `quickstart.md` validation sequence: `uv sync && uv run bookmarkcli --help && uv run pytest -q`; verify all three commands exit 0

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001) — BLOCKS all user stories
- **User Stories (Phase 3–5)**: All depend on Foundational phase completion
  - User stories proceed in priority order: P1 → P2 → P3
  - US2 and US3 have no file-level dependencies on US1 but are lower priority; sequence after US1 to avoid `pyproject.toml` conflicts
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 — no dependencies on other stories
- **User Story 2 (P2)**: Can start after Phase 2 — independent of US1 except both edit `pyproject.toml`; sequence after US1 to avoid conflicts
- **User Story 3 (P3)**: Depends on US1 completing T006 (`cli.py`) and T007 (`uv.lock`) before T010 (`uv sync`) is useful

### Within Each User Story

- `pyproject.toml` edits before `uv lock` / `uv sync`
- Source files (`cli.py`, `conftest.py`) can be created in parallel with `pyproject.toml` edits (different files)
- `uv sync` / `uv lock` after all `pyproject.toml` changes are complete

### Parallel Opportunities

- T003 + T004 (Phase 2): both create new files, no conflicts
- T005 + T006 (Phase 3): different files (`pyproject.toml` vs `src/bookmarkcli/cli.py`)
- T008 + T009 (Phase 4): different files (`pyproject.toml` vs `conftest.py`)

---

## Parallel Example: User Story 1

```bash
# Run in parallel (different files, no dependencies):
Task T005: "Add deps and entry point to pyproject.toml"
Task T006: "Create src/bookmarkcli/cli.py with Click main group"

# Then sequentially (depends on T005 + T006):
Task T007: "Run uv lock to generate uv.lock"
```

## Parallel Example: User Story 2

```bash
# Run in parallel (different files, no dependencies):
Task T008: "Add pytest config to pyproject.toml"
Task T009: "Create conftest.py with exit-code normalization hook"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002–T004)
3. Complete Phase 3: User Story 1 (T005–T007)
4. **STOP and VALIDATE**: `uv sync` → `uv run bookmarkcli --help`
5. All further stories layer on top of this working foundation

### Incremental Delivery

1. Complete Setup + Foundational → project structure exists
2. Add User Story 1 → `uv sync` works, entry point registered → **MVP!**
3. Add User Story 2 → `uv run pytest -q` exits 0
4. Add User Story 3 → `bookmarkcli --help` verified end-to-end
5. Each story validates independently without breaking previous stories

---

## Notes

- **[P]** tasks touch different files and have no blocking dependencies — safe to run in parallel
- **[Story]** labels map each task to its user story for full traceability
- No test tasks generated — TDD was not requested in this specification
- `conftest.py` must be at the **repository root** (not inside `tests/`); pytest auto-loads it as a plugin
- `uv.lock` must be committed to the repository to guarantee reproducible installs (SC-004)
- The production wheel must NOT include dev dependencies — confirmed by `[dependency-groups]` pattern (R-005)
- All acceptance criteria for this scaffold are verifiable via the `quickstart.md` commands
