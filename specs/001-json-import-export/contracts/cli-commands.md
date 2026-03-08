# CLI Command Contract: JSON Import/Export

**Feature**: 001-json-import-export  
**Date**: 2026-03-07  
**Module**: `bookmarkcli.cli` (Click commands)  
**Version**: 0.3.0

---

## Overview

This document defines the CLI contract for the two new commands added in this feature: `bookmark export` and `bookmark import`. Both are subcommands of the top-level `bookmark` (i.e., `bookmarkcli`) Click group.

---

## Commands

### `bookmark export`

Export all bookmarks from the store to JSON.

#### Synopsis

```
bookmark export --format json [--file <path>]
```

#### Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `--format` | choice: `json` | ✅ | — | Output format. Only `json` is supported in v0.3.0. |
| `--file` | path string | ❌ | — | Destination file path. If omitted, output goes to stdout. |

#### Behaviour

1. Opens the bookmark store (uses the application's configured DB path).
2. Loads all bookmarks via `store.list_all()`.
3. Serialises to JSON using `bookmarks_to_json()`.
4. **If `--file` is given**: writes the JSON string to the specified file (creates or overwrites; no prompt).
5. **If `--file` is omitted**: prints the JSON string to stdout.
6. Exits with code 0 on success.

#### Error conditions

| Condition | Output | Exit code |
|-----------|--------|-----------|
| `--file` path points to a directory | Error message to stderr: `"Error: <path> is a directory"` | 1 |
| `--file` path is not writable | Error message to stderr: `"Error: cannot write to <path>: <reason>"` | 1 |
| Store cannot be opened | Error message to stderr | 1 |

#### Examples

```bash
# Export to file
bookmark export --format json --file ~/backup.json

# Export to stdout (inspect or pipe)
bookmark export --format json

# Pipe to jq
bookmark export --format json | jq '.bookmarks | length'
```

#### Sample output (stdout or file content)

```json
{
  "bookmarks": [
    {
      "url": "https://example.com",
      "title": "Example Site",
      "tags": ["web", "example"],
      "created_at": "2026-03-07T12:00:00+00:00",
      "updated_at": "2026-03-07T12:34:56+00:00"
    }
  ]
}
```

Empty store:

```json
{
  "bookmarks": []
}
```

---

### `bookmark import`

Import bookmarks from a JSON file into the store.

#### Synopsis

```
bookmark import --format json [--on-duplicate (skip|update)] <file>
```

#### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `file` | path string | ✅ | Path to the JSON file to import. |

#### Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `--format` | choice: `json` | ✅ | — | Input format. Only `json` is supported. |
| `--on-duplicate` | choice: `skip`, `update` | ❌ | `skip` | Policy for URLs already in the store. |

#### Behaviour

1. Validates that `<file>` exists and is readable; exits with an error if not.
2. Reads the file content.
3. Parses the JSON; exits with an error if the content is not valid JSON.
4. Iterates over the `"bookmarks"` array, applying the duplicate policy.
5. Prints a summary to stdout after completion.
6. Exits with code 0 on success (even if some entries were skipped or invalid).
7. Exits with code 1 only on fatal errors (missing file, invalid JSON, unreadable path).

#### Duplicate policy

| Policy | Behaviour when URL already exists in store |
|--------|--------------------------------------------|
| `skip` (default) | Leave existing bookmark unchanged; count as skipped |
| `update` | Replace `title` and `tags` with values from the file; count as updated |

#### Error conditions

| Condition | Output | Exit code |
|-----------|--------|-----------|
| `<file>` does not exist | `"Error: file not found: <path>"` to stderr | 1 |
| `<file>` is not readable | `"Error: cannot read file: <path>: <reason>"` to stderr | 1 |
| File contains invalid JSON | `"Error: invalid JSON in <path>"` to stderr | 1 |
| Entry missing `url` field | Warning to stderr: `"Warning: skipping entry <n>: missing url"` | 0 (continues) |

#### Summary output format

Printed to stdout after successful import:

```
Import complete: 3 added, 1 skipped, 0 updated, 0 invalid.
```

When no entries processed (empty array):

```
Import complete: 0 added, 0 skipped, 0 updated, 0 invalid.
```

#### Examples

```bash
# Import from file (default: skip duplicates)
bookmark import --format json backup.json

# Import and overwrite duplicates
bookmark import --format json --on-duplicate update backup.json
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Command completed successfully (partial skips/invalids are not errors) |
| 1 | Fatal error: unreadable file, invalid JSON, I/O failure, bad `--file` path |
| 2 | Click usage error: missing required option/argument, invalid choice |

---

## Compatibility Notes

- The `--format json` flag is **required** on both commands (not defaulted) to allow future formats without breaking the interface (spec assumption: "The `--format` flag is required").
- Both commands are idempotent with respect to `--on-duplicate skip`: running export then import multiple times will not create duplicate records.
- The `id` field is never exported; the import command does not accept or use an `id` field.
