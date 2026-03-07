# CLI Contract: bookmarkcli

**Feature**: 001-project-scaffold  
**Date**: 2026-03-07  
**Version**: 0.1.0 (scaffold)

---

## Overview

`bookmarkcli` is a Click-based command-line tool. This document defines the CLI contract: the commands, arguments, options, exit codes, and output formats that the tool guarantees to callers (users and scripts).

The S00 scaffold establishes the **root command group only**. Subcommands will be added in subsequent features (S01+).

---

## Root Command

### `bookmarkcli`

The top-level Click group. Dispatches to subcommands.

```
Usage: bookmarkcli [OPTIONS] COMMAND [ARGS]...

  Bookmark manager CLI.

Options:
  --help  Show this message and exit.

Commands:
  (none yet — added in S01+)
```

**Exit codes**:

| Code | Meaning |
|------|---------|
| 0 | Success (or no-op) |
| 1 | Usage error / unrecognised option |
| 2 | Click internal usage error |

---

## Output Protocol

All future subcommands MUST follow this protocol:

| Stream | Usage |
|--------|-------|
| `stdout` | Primary output (results, data) |
| `stderr` | Errors, warnings, diagnostics |

---

## Stability Guarantees

| Item | Status |
|------|--------|
| `bookmarkcli --help` exits 0 | **Stable** from S00 |
| Root group exists at `bookmarkcli.cli:main` | **Stable** from S00 |
| Subcommand interface | **To be defined** in S01+ |

---

## Entry Point Registration

Declared in `pyproject.toml`:

```toml
[project.scripts]
bookmarkcli = "bookmarkcli.cli:main"
```

This registers `bookmarkcli` as a console script installed into the virtualenv's `bin/` directory.

---

## Future Subcommands (planned, not contracted)

| Subcommand | Feature | Description |
|------------|---------|-------------|
| `add` | S02 | Add a new bookmark |
| `delete` | S02 | Delete a bookmark by ID |
| `list` | S03 | List all bookmarks |
| `search` | S03 | Search bookmarks by keyword |
| `tag` | S04 | Manage tags |
| `import` | S05/S06/S07 | Import from JSON, CSV, or browser |
| `export` | S05/S06 | Export to JSON or CSV |
