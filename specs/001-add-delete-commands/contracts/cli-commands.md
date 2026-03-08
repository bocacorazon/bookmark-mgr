# CLI Command Contract: Add & Delete Commands

**Feature**: 001-add-delete-commands  
**Date**: 2026-03-07  
**Entry point**: `bookmarkcli` (alias `bookmark`)  
**Version**: 0.3.0

---

## Overview

This document defines the CLI contract for the `add` and `delete` subcommands added in feature S02. Callers (users, scripts, tests) depend on the argument signatures, output formats, and exit codes described here.

---

## Global Options

The top-level `bookmarkcli` group accepts no additional options beyond `--help`.

```
bookmarkcli [OPTIONS] COMMAND [ARGS]...
```

The database path is resolved from the environment variable `BOOKMARKCLI_DB` if set, otherwise defaults to `~/.bookmarkcli/bookmarks.db`. The parent directory is created automatically on first use.

---

## Command: `add`

### Synopsis

```
bookmarkcli add URL [--title TEXT] [--tags TEXT]
```

### Arguments

| Name | Position | Required | Description |
|------|----------|----------|-------------|
| `URL` | 1 | ✅ | The URL to save. Must contain a scheme (e.g., `https://`) and a host. |

### Options

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--title TEXT` | string | `None` | Human-readable label for the bookmark. Stored as-is; not validated. |
| `--tags TEXT` | string | `None` | Comma-separated tag names. Leading/trailing whitespace around each tag is stripped. Empty string → no tags. |
| `--help` | flag | — | Show help and exit. |

### Exit Codes

| Code | Condition |
|------|-----------|
| `0` | Bookmark successfully created |
| `1` | Invalid URL format |
| `1` | Duplicate URL — bookmark already exists |
| `1` | Unexpected storage error |

### Standard Output

**Success**:
```
✓ Bookmark #<id> added: <url>
```

**Error — invalid URL** (stderr):
```
Error: "<value>" is not a valid URL. URLs must include a scheme (e.g., https://) and a host.
```

**Error — duplicate URL** (stderr):
```
Error: A bookmark with this URL already exists (id=<id>).
```

### Examples

```bash
# Minimal add
bookmarkcli add https://example.com

# With title and tags
bookmarkcli add https://example.com --title "Example Site" --tags news,tech

# Tags with spaces (shell quoting)
bookmarkcli add https://example.com --tags "news, tech, python"

# Invalid URL → exit 1
bookmarkcli add not-a-url

# Duplicate → exit 1
bookmarkcli add https://example.com   # (when already stored)
```

---

## Command: `delete`

### Synopsis

```
bookmarkcli delete ID_OR_URL
```

### Arguments

| Name | Position | Required | Description |
|------|----------|----------|-------------|
| `ID_OR_URL` | 1 | ✅ | Numeric bookmark ID (e.g., `42`) or full URL (e.g., `https://example.com`). The CLI determines the type by attempting integer conversion: success → ID, `ValueError` → URL. |

### Options

| Flag | Description |
|------|-------------|
| `--help` | Show help and exit. |

### Confirmation Prompt

Before deleting, the command **always** displays the matching bookmark's details and prompts:

```
  ID   : <id>
  URL  : <url>
  Title: <title or "(none)">
Delete this bookmark? [y/N]:
```

- Default is **No** — pressing Enter without typing cancels the operation.
- Accepted affirmative inputs: `y`, `Y`.
- All other inputs (including empty/Enter) cancel.

### Exit Codes

| Code | Condition |
|------|-----------|
| `0` | Bookmark successfully deleted |
| `0` | User cancelled at confirmation prompt |
| `1` | Bookmark not found (by ID or URL) |
| `1` | Unexpected storage error |

### Standard Output

**Prompt + confirmed delete**:
```
  ID   : 42
  URL  : https://example.com
  Title: Example Site
Delete this bookmark? [y/N]: y
✓ Bookmark #42 deleted.
```

**Prompt + cancelled**:
```
  ID   : 42
  URL  : https://example.com
  Title: (none)
Delete this bookmark? [y/N]:
Cancelled.
```

**Error — not found** (stderr):
```
Error: No bookmark found for '99'.
```

### Examples

```bash
# Delete by ID
bookmarkcli delete 42

# Delete by URL
bookmarkcli delete https://example.com

# Not found → exit 1
bookmarkcli delete 9999

# Non-interactive cancel (pipe 'n')
echo n | bookmarkcli delete 42
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BOOKMARKCLI_DB` | Full path to the SQLite database file | `~/.bookmarkcli/bookmarks.db` |

---

## Error Format

All user-facing errors are prefixed with `Error:` and written to **stderr**. The exit code is **1** for all error conditions. This enables reliable scripting:

```bash
bookmarkcli add not-a-url 2>/dev/null || echo "add failed"
```

---

## Stability

| Symbol | Status |
|--------|--------|
| `add` command signature | **Stable** from 001 |
| `delete` command signature | **Stable** from 001 |
| Output format (success lines) | **Stable** from 001 |
| Exit codes | **Stable** from 001 |
| `BOOKMARKCLI_DB` env var | **Stable** from 001 |
| Confirmation prompt text | Advisory — subject to UX refinement |
