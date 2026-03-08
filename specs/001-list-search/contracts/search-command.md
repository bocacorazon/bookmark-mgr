# Contract: `bookmark search` Command

**Feature**: S03 — List & Search Commands  
**Branch**: `001-list-search`  
**Date**: 2026-03-08

---

## Command Signature

```
bookmark search <query>
```

## Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `query` | `TEXT` | Yes | Case-insensitive substring to match against title and URL |

## Behavior

1. Validates that `query` is non-empty and non-whitespace; raises `UsageError` otherwise (FR-013).
2. Opens `BookmarkStore` and calls `search(query)`.
3. If results are non-empty, renders via `render_bookmarks_table()`.
4. If results are empty, renders via `render_empty_state("No bookmarks match your search.")`.
5. Output is rich-formatted when stdout is a TTY; plain text otherwise (FR-008, SC-004).

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success (even when no results) |
| `2` | Usage error (missing or empty query) |

## Output Format (TTY mode)

```
 ┌────┬─────────────────────────────────────┬────────────────────────────────────────────────────┬──────────────────┬─────────────────┐
 │ ID │ Title                               │ URL                                                │ Tags             │ Created At      │
 ├────┼─────────────────────────────────────┼────────────────────────────────────────────────────┼──────────────────┼─────────────────┤
 │  1 │ Python Docs                         │ https://docs.python.org                            │ python, docs     │ 2026-03-08 01:00 │
 └────┴─────────────────────────────────────┴────────────────────────────────────────────────────┴──────────────────┴─────────────────┘
```

## Output Format (piped / plain mode)

```
ID  Title                                URL                                                  Tags          Created At
1   Python Docs                          https://docs.python.org                              python, docs  2026-03-08 01:00
```

## Empty State Output

```
No bookmarks match your search.
```

## Error Examples

```
$ bookmark search
Error: Missing argument 'QUERY'.

$ bookmark search "   "
Error: Search query cannot be empty. Usage: bookmark search <query>
```

## Acceptance Scenarios Covered

- FR-006, FR-007, FR-008, FR-009, FR-010, FR-013
- User Story 4 (all acceptance scenarios)
