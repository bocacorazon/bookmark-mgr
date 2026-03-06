# Implementation Plan — BookmarkCLI

**Created**: 2026-02-28  
**Status**: Sample (for skrunner demo)  
**Language**: Python 3.12+  
**Workflow**: Each spec follows the spec-kit pipeline: `specify → plan → tasks → implement`

---

## Strategy

A CLI bookmark manager built with Python, using SQLite for storage and Click for the CLI framework. The implementation is split into a **foundation** phase (data model + storage), followed by two **parallel tracks**: CLI commands and import/export. Each spec is a self-contained unit suitable for an independent agent.

---

## Spec Inventory

### Phase 0 — Foundation

| Spec | Name | Description | Depends On | Parallel Group |
|---|---|---|---|---|
| **S00** | Project Scaffold | Python project scaffold: `pyproject.toml`, `src/bookmarkcli/`, `tests/`, SQLite dev dependencies, Click, pytest. Must pass `pytest` with zero tests collected. | — | — |
| **S01** | Data Model & Storage | SQLite-backed storage layer: `Bookmark` model (url, title, tags, created_at, updated_at), `BookmarkStore` class with CRUD operations, migration/init logic, full test coverage. | S00 | — |

### Phase 1 — CLI Commands (Track A)

| Spec | Name | Description | Depends On | Parallel Group |
|---|---|---|---|---|
| **S02** | Add & Delete Commands | `bookmark add <url> [--title] [--tags]` and `bookmark delete <id/url>` commands. Validate URL format. Prevent duplicates. Confirm before delete. | S01 | A |
| **S03** | List & Search Commands | `bookmark list [--tag] [--limit] [--sort]` and `bookmark search <query>` commands. Full-text search across title and URL. Tabular output with `rich` or plain text. | S01 | A |
| **S04** | Tag Management | `bookmark tag <id> --add <tag>` and `bookmark tag <id> --remove <tag>` commands. `bookmark tags` to list all tags with counts. Tag normalization (lowercase, trim). | S02, S03 | — |

### Phase 2 — Import/Export (Track B)

| Spec | Name | Description | Depends On | Parallel Group |
|---|---|---|---|---|
| **S05** | JSON Import/Export | `bookmark export --format json [--file out.json]` and `bookmark import --format json <file>`. Round-trip fidelity: export then import should produce identical data. Handle duplicates on import (skip or update). | S01 | B |
| **S06** | CSV Import/Export | `bookmark export --format csv [--file out.csv]` and `bookmark import --format csv <file>`. Map columns: url, title, tags (semicolon-separated), created_at. Handle malformed rows gracefully. | S01 | B |
| **S07** | Browser Bookmark Import | `bookmark import --format html <file>`. Parse Netscape Bookmark File Format (exported by Chrome/Firefox). Extract URL, title, and folder-as-tag mapping. Report import summary (added, skipped, errors). | S05, S06 | — |

---

## Parallelism Map

```
Phase 0:  S00
           │
           ▼
          S01
           │
     ┌─────┴─────┐
     ▼           ▼
    S02         S05    ◄── Track A and Track B start in parallel
    S03         S06
     │           │
     ▼           ▼
    S04         S07
```

**Maximum parallelism**: up to **4 specs simultaneously** during Phase 1+2 (S02, S03, S05, S06).

---

## Spec Document Conventions

Each spec prompt lives at:

```
docs/specs/S##-spec-name/prompt.md
```

After running `speckit.specify`, the spec-kit pipeline produces:
```
docs/specs/S##-spec-name/
├── prompt.md      # input to speckit.specify
├── spec.md        # output of speckit.specify
├── plan.md        # output of speckit.plan
└── tasks.md       # output of speckit.tasks
```
