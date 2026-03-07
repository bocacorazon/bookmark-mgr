# Feature Specification: Python Project Scaffold

**Feature Branch**: `001-project-scaffold`  
**Created**: 2026-03-07  
**Status**: Draft  
**Input**: User description: "Python project scaffold: pyproject.toml, src/bookmarkcli/, tests/, SQLite dev dependencies, Click, pytest. Must pass pytest with zero tests collected."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Bootstrap Project Environment (Priority: P1)

A developer clones the repository and sets up the project with all required tools and dependencies in a single operation. They can immediately begin writing code without any additional configuration steps.

**Why this priority**: This is the foundation that enables all other work. Without a valid, reproducible environment setup, no development can proceed. Every contributor needs this to work correctly on their first attempt.

**Independent Test**: Can be fully tested by a fresh clone followed by running the install command, then verifying the CLI entry point is available — this delivers a working development environment with zero additional steps.

**Acceptance Scenarios**:

1. **Given** a freshly cloned repository with no installed dependencies, **When** the developer runs the project install command, **Then** all runtime and development dependencies are installed and the `bookmarkcli` command is available on the PATH.
2. **Given** a clean environment, **When** the install command is run, **Then** it completes without errors and produces a reproducible result captured in the lock file.

---

### User Story 2 - Run Test Suite with No Tests (Priority: P2)

A developer runs the test suite immediately after project setup, before any tests have been written. The command exits successfully, confirming that the project structure is correct and the test runner is properly configured.

**Why this priority**: The requirement explicitly mandates that `pytest` passes with zero tests collected. This validates the entire scaffold configuration (project structure, test runner settings, exit-code normalization) and gives developers confidence the toolchain is working.

**Independent Test**: Can be fully tested by running the test command on the freshly set-up project with no test files present, verifying a zero exit code — this proves the scaffold is correctly configured end-to-end.

**Acceptance Scenarios**:

1. **Given** the project is installed and the tests/ directory contains no test functions, **When** the developer runs the test suite, **Then** the command exits with code 0 (success).
2. **Given** a pytest "no tests collected" condition (exit code 5), **When** the session finishes, **Then** the framework normalizes this to exit code 0 so CI pipelines report success.

---

### User Story 3 - Invoke the CLI Entry Point (Priority: P3)

A developer invokes the `bookmarkcli` command-line tool after installation. The command responds with help text, confirming the Click-based CLI group is wired up and executable.

**Why this priority**: This validates that the package entry point is correctly registered and the CLI framework integration works. It acts as a smoke test for the installed package.

**Independent Test**: Can be fully tested by running `bookmarkcli --help` and verifying it prints usage information without errors.

**Acceptance Scenarios**:

1. **Given** the project is installed, **When** the developer runs `bookmarkcli --help`, **Then** the tool prints usage/help text and exits with code 0.
2. **Given** an incomplete or broken install, **When** the developer runs `bookmarkcli`, **Then** an informative error is shown rather than a cryptic traceback.

---

### Edge Cases

- What happens when a developer attempts to install dependencies without the lock file present? The package manager must still resolve a consistent dependency set.
- What happens if a test file is accidentally added without any test functions? The suite must still exit with code 0.
- What happens if the `conftest.py` is missing or deleted? The test suite must document this dependency so contributors do not accidentally remove it.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The project MUST declare all runtime dependencies (including Click ≥ 8.0) in a standard project configuration file (`pyproject.toml`).
- **FR-002**: The project MUST declare development-only dependencies (pytest ≥ 8.0 and an async SQLite library) separately from runtime dependencies, so production installs remain lean.
- **FR-003**: Source code MUST be organized under `src/bookmarkcli/` using the src-layout convention so the package is only importable after installation, preventing accidental reliance on raw source paths.
- **FR-004**: Tests MUST be organized under a `tests/` directory, and the test runner MUST be configured to discover tests from that directory.
- **FR-005**: Running the test suite when zero test functions exist MUST exit with code 0 (success), so CI pipelines do not report false failures on a fresh project.
- **FR-006**: The project MUST provide a `bookmarkcli` command-line entry point that can be invoked after installation.
- **FR-007**: The CLI entry point MUST be implemented using the Click library, exposing at minimum a top-level command group.
- **FR-008**: Dependency versions MUST be locked in a lock file (`uv.lock`) to guarantee reproducible installs across all environments.
- **FR-009**: The build system configuration MUST explicitly declare which package directory to include in the built wheel to prevent unintended files from being packaged.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer with the correct language runtime installed can go from a fresh clone to a working environment with a single command in under 2 minutes.
- **SC-002**: Running the test suite on the unmodified scaffold exits with code 0 in 100% of runs with zero tests collected.
- **SC-003**: The `bookmarkcli` entry point responds to `--help` with usage text in under 1 second after a successful install.
- **SC-004**: Any developer can reproduce the exact same installed environment on a different machine using only the repository contents (lock file included), with zero version conflicts.

## Assumptions

- The project uses `uv` as the package and environment manager, as evidenced by the `uv.lock` file in the repository.
- SQLite access in tests is provided via an async adapter library (`aiosqlite`); the Python standard library `sqlite3` module is available at runtime without an explicit dependency declaration.
- The exit-code normalization for "no tests collected" is implemented in `conftest.py` at the repository root, which pytest loads automatically.
- Python ≥ 3.11 is assumed as the minimum runtime version.
