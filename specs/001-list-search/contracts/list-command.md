# Contract: `bookmark list` Command

**Feature**: S03 — List & Search Commands  
**Branch**: `001-list-search`  
**Date**: 2026-03-08

---

## Command Signature

```
bookmark list [OPTIONS]
```

## Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--tag <tag>` | `TEXT` | None | Filter to bookmarks carrying this exact tag |
| `--limit <n>` | `INT` | None | Return at most N bookmarks (`0` = return none) |
| `--sort <order>` | `Choice[newest\|oldest]` | `newest` | Order by creation date |

## Behavior

1. Opens `BookmarkStore` at the default DB path and calls `list_filtered(tag, limit, sort)`.
2. If results are non-empty, renders via `render_bookmarks_table()`.
3. If results are empty, renders via `render_empty_state("No bookmarks found.")`.
4. Output is rich-formatted when stdout is a TTY; plain text otherwise.

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success (even when no results) |
| `2` | Usage error (invalid `--limit` or `--sort`) |

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
No bookmarks found.
```

## Error Examples

```
$ bookmark list --limit -1
Error: Invalid value for '--limit': -1 is not a valid positive integer.

$ bookmark list --sort alpha
Error: Invalid value for '--sort': 'alpha' is not one of 'newest', 'oldest'.
```

## Acceptance Scenarios Covered

- FR-001, FR-002, FR-003, FR-004, FR-005, FR-008, FR-009, FR-010, FR-011, FR-012
- User Stories 1, 2, 3 (all acceptance scenarios)
