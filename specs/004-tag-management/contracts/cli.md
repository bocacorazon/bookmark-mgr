# CLI Contract: bookmarkcli — Tag Management

**Feature**: 004-tag-management  
**Date**: 2026-03-07  
**Module**: `bookmarkcli.cli`  
**Version**: 0.4.0

---

## Overview

This document extends the `bookmarkcli` CLI contract to cover two new subcommands introduced in S04: `tag` and `tags`. All prior contract guarantees from S01–S03 remain in effect.

---

## New Subcommands

### `bookmarkcli tag`

Add or remove a tag on a single bookmark.

```
Usage: bookmarkcli tag [OPTIONS] BOOKMARK_ID

  Add or remove a tag on a bookmark.

Arguments:
  BOOKMARK_ID  Integer ID of the bookmark.  [required]

Options:
  --add TEXT     Tag to add.
  --remove TEXT  Tag to remove.
  --help         Show this message and exit.
```

**Constraints**:
- Exactly one of `--add` or `--remove` must be provided.
- Providing both or neither is a usage error (exit code 2).

#### `bookmarkcli tag <id> --add <tag>`

Adds a normalized tag to the specified bookmark.

| Condition | stdout | stderr | Exit code |
|-----------|--------|--------|-----------|
| Tag newly added | `Tagged bookmark <id> with '<tag>'.` | — | 0 |
| Tag already present (idempotent) | `Bookmark <id> already has tag '<tag>'.` | — | 0 |
| Bookmark not found | — | `Error: Bookmark <id> not found.` | 1 |
| Tag empty or all-whitespace | — | `Error: Tag must not be empty or whitespace.` | 1 |
| Both `--add` and `--remove` given | — | `Error: --add and --remove are mutually exclusive.` | 2 |
| Neither `--add` nor `--remove` given | — | `Error: Provide exactly one of --add or --remove.` | 2 |

#### `bookmarkcli tag <id> --remove <tag>`

Removes a normalized tag from the specified bookmark.

| Condition | stdout | stderr | Exit code |
|-----------|--------|--------|-----------|
| Tag removed | `Removed tag '<tag>' from bookmark <id>.` | — | 0 |
| Tag not on bookmark | — | `Error: Tag '<tag>' not found on bookmark <id>.` | 1 |
| Bookmark not found | — | `Error: Bookmark <id> not found.` | 1 |
| Tag empty or all-whitespace | — | `Error: Tag must not be empty or whitespace.` | 1 |

---

### `bookmarkcli tags`

List all tags currently in use, with bookmark counts.

```
Usage: bookmarkcli tags [OPTIONS]

  List all tags with their bookmark counts.

Options:
  --help  Show this message and exit.
```

| Condition | stdout | stderr | Exit code |
|-----------|--------|--------|-----------|
| Tags exist | One line per tag (see format below), sorted alphabetically | — | 0 |
| No tags in use | `No tags found.` | — | 0 |

**Output format** (tags exist):

```
python  3
tutorial  1
web  2
```

- One tag per line.
- Tag name and count separated by two spaces.
- Tags listed in ascending alphabetical order.
- Count = number of distinct bookmarks carrying that tag.

---

## Tag Normalization (Observable Behaviour)

All tag arguments are normalized before storage, removal, or comparison:

| Rule | Example |
|------|---------|
| Leading/trailing whitespace trimmed | `--add " python "` → stored as `"python"` |
| Converted to lowercase | `--add "Python"` → stored as `"python"` |

Confirmation messages always echo the **normalized** form of the tag.

---

## Output Protocol

Consistent with the project-wide convention established in S01:

| Stream | Usage |
|--------|-------|
| `stdout` | Confirmation messages, tag listings |
| `stderr` | All error messages |

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Application error (bookmark not found, tag not found, tag validation failure) |
| 2 | Usage error (bad flag combination, missing required flag) |

---

## Stability Guarantees

| Item | Status |
|------|--------|
| `bookmarkcli tag <id> --add <tag>` exits 0 on success | **Stable** from S04 |
| `bookmarkcli tag <id> --remove <tag>` exits 0 on success | **Stable** from S04 |
| `bookmarkcli tags` exits 0 | **Stable** from S04 |
| Two-space separator in `tags` output | **Stable** from S04 |
| Normalized tag echoed in confirmation | **Stable** from S04 |
