# Data Model: Project Scaffold

**Feature**: 001-project-scaffold  
**Date**: 2026-03-07

---

## Scope

This feature establishes the project scaffold only. There is **no persistent data model** in this iteration — no database schema, no domain entities, and no state transitions. The SQLite dependency (`aiosqlite`) is declared for future features (S01+) but is not used in S00.

The only "model" in this scaffold is the Python package namespace itself.

---

## Package Structure

### `bookmarkcli` Package

| Artifact | Path | Purpose |
|----------|------|---------|
| Package init | `src/bookmarkcli/__init__.py` | Declares the `bookmarkcli` namespace |
| CLI entry | `src/bookmarkcli/cli.py` | Click `main` group — top-level command router |

### Entry Point Registration

```toml
# pyproject.toml
[project.scripts]
bookmarkcli = "bookmarkcli.cli:main"
```

`main` is a `click.Group` instance. All future subcommands (`add`, `delete`, `list`, etc.) will be registered to this group.

---

## Future Entity Placeholders (S01+)

The following entities are expected in future specs but are **not implemented here**:

| Entity | Expected Feature | Notes |
|--------|-----------------|-------|
| `Bookmark` | S01-data-model | URL, title, tags, timestamps |
| `Tag` | S01-data-model | Many-to-many with Bookmark |
| `Database` | S01-data-model | SQLite file via aiosqlite |

---

## Validation Rules

None applicable in S00 (no user input processed beyond CLI arguments to Click).

---

## State Transitions

None applicable in S00.
