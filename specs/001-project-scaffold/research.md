# Research: Project Scaffold

**Feature**: 001-project-scaffold  
**Date**: 2026-03-07  
**Status**: Complete — all decisions resolved

---

## R-001: Package Manager — `uv`

- **Decision**: Use `uv` (Astral) as the package and environment manager.
- **Rationale**: The `uv.lock` file is already present in the repository, confirming `uv` is the chosen tool. `uv` provides fast, reproducible installs with a single lock file and is compatible with standard `pyproject.toml` metadata.
- **Alternatives considered**: `pip + pip-tools` (slower, no single-command sync), `poetry` (non-standard pyproject metadata), `pdm` (less adoption).
- **Resolved**: No clarification needed — evidenced by existing `uv.lock`.

---

## R-002: Source Layout — `src/` convention

- **Decision**: All package source code lives under `src/bookmarkcli/`.
- **Rationale**: The src-layout prevents the package from being importable without installation, which eliminates a class of bugs where tests pass on the developer's machine (raw path import) but fail in CI (installed package). This is the recommended layout for modern Python packaging (PEP 517, Hatch, setuptools docs).
- **Alternatives considered**: Flat layout (`bookmarkcli/` at root) — simpler but allows accidental raw imports; rejected per FR-003.
- **Resolved**: `src/bookmarkcli/` already present.

---

## R-003: Build Backend — Hatchling

- **Decision**: Use Hatchling as the PEP 517 build backend.
- **Rationale**: Hatchling is the default build backend for projects using the src-layout with `pyproject.toml`. It requires explicit `packages` declaration (`[tool.hatch.build.targets.wheel] packages = ["src/bookmarkcli"]`), satisfying FR-009.
- **Alternatives considered**: `setuptools` (requires more configuration for src-layout), `flit` (only flat layout), `meson-python` (overkill for pure Python).
- **Resolved**: Already declared in `pyproject.toml`.

---

## R-004: CLI Framework — Click

- **Decision**: Use Click ≥ 8.0 for the CLI entry point.
- **Rationale**: Click provides decorator-based command composition, automatic `--help` generation, and is the de-facto standard for Python CLI tools. The `@click.group()` pattern satisfies FR-006 and FR-007 and is extensible for future subcommands.
- **Alternatives considered**: `argparse` (stdlib, verbose, no decorator API), `typer` (Click wrapper with type hints; adds dependency), `fire` (introspection-based, less control).
- **Resolved**: Click already declared in `pyproject.toml` and `cli.py` is implemented.

---

## R-005: Dev Dependencies — pytest + aiosqlite

- **Decision**: Declare dev-only dependencies under `[dependency-groups] dev` in `pyproject.toml`.
- **Rationale**: `[dependency-groups]` is the PEP 735 standard for dev dependencies in `pyproject.toml` (supported natively by `uv`). This keeps the production wheel lean (FR-002). `aiosqlite ≥ 0.20` provides an async interface to SQLite for future integration tests.
- **Alternatives considered**: `[project.optional-dependencies]` (the older `extras` pattern — less semantic), inline scripts — both rejected.
- **Resolved**: Already in `pyproject.toml`.

---

## R-006: pytest Exit-Code Normalization

- **Decision**: Implement a `conftest.py` at the repository root that maps pytest exit code 5 ("no tests collected") to 0.
- **Rationale**: pytest exits with code 5 when no test functions are found. CI pipelines treat any non-zero exit as failure. FR-005 mandates `exit 0` for zero-test runs. The `pytest_sessionfinish` hook in `conftest.py` is the canonical mechanism.
- **Alternatives considered**: `pytest --ignore` flags (brittle), CI-level exit-code overrides (not portable), `addopts = --co` (changes collection mode).
- **Resolved**: `conftest.py` already present at repo root.

---

## R-007: Python Minimum Version

- **Decision**: Python ≥ 3.11.
- **Rationale**: 3.11 is the oldest currently-supported CPython release with active security support. It introduces `tomllib` in stdlib and improved error messages. `aiosqlite ≥ 0.20` requires ≥ 3.8; no upper bound conflicts.
- **Alternatives considered**: 3.12 (newer, fewer platforms), 3.10 (end-of-life 2026-10).
- **Resolved**: Declared as `requires-python = ">=3.11"` in `pyproject.toml`.

---

## Summary of Resolved Items

| ID    | Topic                        | Status   |
|-------|------------------------------|----------|
| R-001 | Package manager (uv)         | Resolved |
| R-002 | src-layout convention        | Resolved |
| R-003 | Build backend (Hatchling)    | Resolved |
| R-004 | CLI framework (Click)        | Resolved |
| R-005 | Dev deps (pytest + aiosqlite)| Resolved |
| R-006 | pytest exit-code normalization| Resolved |
| R-007 | Python minimum version       | Resolved |

**No NEEDS CLARIFICATION items remain.**
