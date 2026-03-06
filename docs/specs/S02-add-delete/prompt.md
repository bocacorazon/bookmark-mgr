# Spec Prompt: Add & Delete Commands

## Feature
**S02 — Add & Delete Commands**: Implement the CLI commands for adding and deleting bookmarks.

## Context
This is part of Track A (CLI Commands). It builds on the `BookmarkStore` from S01.

## Scope

### In Scope
- `bookmark add <url> [--title TEXT] [--tags TAG1,TAG2,...]`:
  - Validate that `<url>` is a well-formed URL.
  - If `--title` is omitted, use the URL as the title.
  - Tags are comma-separated, normalized to lowercase.
  - Print confirmation with bookmark ID on success.
  - Print error and exit non-zero if URL already exists.
- `bookmark delete <id_or_url>`:
  - Accept either a numeric ID or a URL string.
  - Print the bookmark details and ask for confirmation (`Are you sure? [y/N]`).
  - Support `--force` to skip confirmation.
  - Print error if bookmark not found.
- Tests for both commands using Click's `CliRunner`.

### Out of Scope
- Listing, searching, or tag management — those belong to S03, S04.
- Batch operations.

## Dependencies
- **S01**: `BookmarkStore` with `add`, `get`, `get_by_url`, `delete`.

## Key Design Decisions
- URL validation uses `urllib.parse` (no external dependency).
- The `delete` command defaults to requiring confirmation for safety.
