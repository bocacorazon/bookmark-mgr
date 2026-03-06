# Spec Prompt: Tag Management

## Feature
**S04 — Tag Management**: Implement CLI commands for managing tags on bookmarks.

## Context
This is part of Track A (CLI Commands). It depends on S02 and S03 being complete so that bookmarks can be created and listed.

## Scope

### In Scope
- `bookmark tag <id> --add <tag>`:
  - Add a tag to an existing bookmark. Normalize tag (lowercase, trim).
  - No-op if tag already exists on the bookmark (print info message).
  - Print error if bookmark ID not found.
- `bookmark tag <id> --remove <tag>`:
  - Remove a tag from a bookmark.
  - Print error if tag not found on the bookmark.
- `bookmark tags`:
  - List all tags in the system with their bookmark counts.
  - Output format: `tag-name (N bookmarks)`, sorted by count descending.
  - Print "No tags found." if empty.
- Tests for all commands using Click's `CliRunner`.

### Out of Scope
- Bulk tag operations (rename all, merge tags).
- Tag-based deletion.

## Dependencies
- **S02**: Add command (to create test bookmarks).
- **S03**: List command (tag filtering must work with list).

## Key Design Decisions
- Tags are always normalized: lowercase, whitespace trimmed, no duplicates.
- `bookmark tag` requires exactly one of `--add` or `--remove`.
