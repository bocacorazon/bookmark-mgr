# Spec Prompt: Project Scaffold

## Feature
**S00 — Project Scaffold**: Set up the Python project structure for BookmarkCLI.

## Context
BookmarkCLI is a terminal bookmark manager built with Python 3.12+, SQLite, and Click.

## Scope

### In Scope
- Create `pyproject.toml` with project metadata, dependencies (`click`, `rich`), and dev dependencies (`pytest`, `pytest-cov`).
- Create `src/bookmarkcli/` package with `__init__.py` and `__main__.py`.
- Create `tests/` directory with `conftest.py`.
- Create a `bookmark` CLI entry point (Click group) that prints help when invoked with no arguments.
- Ensure `pytest` runs successfully (zero tests collected is acceptable).
- Add a `.gitignore` for Python projects.
- Add a minimal `README.md`.

### Out of Scope
- Any business logic, data models, or storage — those belong to S01+.
- Docker configuration.
- CI/CD pipelines.

## Dependencies
None — this is the first spec.

## Key Design Decisions
- Use `src/` layout (not flat).
- Use Click for CLI framework.
- Use `rich` for terminal output formatting.
- Target Python 3.12+.
