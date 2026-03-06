# Spec Prompt: List & Search Commands

## Feature
**S03 — List & Search Commands**: Implement the CLI commands for listing and searching bookmarks.

## Context
This is part of Track A (CLI Commands). It builds on the `BookmarkStore` from S01.

## Scope

### In Scope
- `bookmark list [--tag TAG] [--limit N] [--sort created_at|title|url]`:
  - Display bookmarks in a formatted table (using `rich` if available, plain text fallback).
  - Columns: ID, Title (truncated to 40 chars), URL (truncated to 50 chars), Tags, Created.
  - `--tag` filters to bookmarks with that tag.
  - `--limit` defaults to 20.
  - `--sort` defaults to `created_at` descending.
  - Print "No bookmarks found." if empty.
- `bookmark search <query>`:
  - Full-text search across title and URL using `BookmarkStore.search()`.
  - Same table output as `list`.
  - Print "No results for '<query>'." if empty.
- Tests for both commands using Click's `CliRunner`.

### Out of Scope
- Adding, deleting, or modifying bookmarks — those belong to S02, S04.
- Export functionality.

## Dependencies
- **S01**: `BookmarkStore` with `list`, `search`.

## Key Design Decisions
- Use `rich.table.Table` for formatted output when `rich` is installed.
- Truncate long URLs and titles in table display to keep output readable.
