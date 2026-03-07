# CLI Schema: List & Search Commands

**Project**: bookmark-mgr  
**Version**: 0.1.0  
**Interface type**: Click CLI (entry point `bookmarkcli`)

---

## Command: `bookmark list`

Displays stored bookmarks in a table. Supports optional filtering by tag, limiting the number of results, and sorting.

### Synopsis

```
bookmarkcli list [OPTIONS]
```

### Options

| Option              | Type                        | Default  | Description                                                                 |
|---------------------|-----------------------------|----------|-----------------------------------------------------------------------------|
| `--tag TEXT`        | `str`                       | —        | Filter to bookmarks carrying this exact, case-sensitive tag.                |
| `--limit INTEGER`   | `int` (≥ 1)                 | —        | Maximum number of rows to display. Applied after tag filtering and sorting. |
| `--sort [date\|title\|url]` | `Choice`          | `date`   | Sort field. `date` = newest-first; `title` / `url` = ascending.             |
| `--plain`           | `bool` flag                 | `False`  | Force plain-text (tab-separated) output, suppressing all ANSI codes.        |
| `--help`            | —                           | —        | Show usage and exit.                                                        |

### Exit Codes

| Code | Meaning                                                        |
|------|----------------------------------------------------------------|
| `0`  | Success (including empty results).                             |
| `2`  | Invalid option value (`--limit` non-integer or ≤ 0, unrecognised `--sort` field). |
| `1`  | Unexpected runtime error (e.g., unreadable database).          |

### Output — Rich Mode (TTY, `--plain` not set)

```
 ID   Title                                     URL                                                 Tags           Date Added
 ──   ───────────────────────────────────────   ─────────────────────────────────────────────────   ────────────   ──────────────────
  1   GitHub - python/cpython                   https://github.com/python/cpython                   python,dev     2026-03-07 12:00
  2   Rich documentation                        https://rich.readthedocs.io/en/stable/              docs,python    2026-03-06 09:30
```

- Borders, column alignment, and alternating row colours rendered via `rich`.
- Long titles and URLs truncated with `…` to preserve table alignment (FR-015).

### Output — Plain Mode (pipe or `--plain`)

```
ID\tTitle\tURL\tTags\tDate Added
1\tGitHub - python/cpython\thttps://github.com/python/cpython\tpython,dev\t2026-03-07 12:00
2\tRich documentation\thttps://rich.readthedocs.io/en/stable/\tdocs,python\t2026-03-06 09:30
```

- Tab-separated values (`\t`).
- Header row on the first line.
- No ANSI escape codes.
- Long values are truncated in the same way as rich mode (FR-015, FR-012).

### Empty-State Output

```
No bookmarks found.
```

Printed when the store is empty or the active filters match no records (FR-016).

### Error Examples

```
Error: Invalid value for '--limit': '0' is not a positive integer.
Error: Invalid value for '--sort': 'newest' is not one of 'date', 'title', 'url'.
```

---

## Command: `bookmark search`

Searches bookmarks by a keyword. Returns bookmarks whose title or URL contains the query string (case-insensitive, literal substring).

### Synopsis

```
bookmarkcli search [OPTIONS] QUERY
```

### Arguments

| Argument | Type  | Required | Description                                                         |
|----------|-------|----------|---------------------------------------------------------------------|
| `QUERY`  | `str` | Yes      | Literal search string. Case-insensitive substring match. Must be non-empty. |

### Options

| Option    | Type       | Default | Description                                                      |
|-----------|------------|---------|------------------------------------------------------------------|
| `--plain` | `bool` flag | `False` | Force plain-text output, suppressing ANSI codes and highlighting. |
| `--help`  | —          | —       | Show usage and exit.                                             |

### Exit Codes

| Code | Meaning                                                        |
|------|----------------------------------------------------------------|
| `0`  | Success (including no matches).                                |
| `2`  | Missing or empty `QUERY` argument.                             |
| `1`  | Unexpected runtime error (e.g., unreadable database).          |

### Output — Rich Mode (TTY, `--plain` not set)

```
 ID   Title                                     URL                                                 Tags           Date Added
 ──   ───────────────────────────────────────   ─────────────────────────────────────────────────   ────────────   ──────────────────
  1   GitHub - python/cpython                   https://github.com/python/cpython                   python,dev     2026-03-07 12:00
```

- Matching query terms **highlighted** (bold yellow) within the Title and URL columns (FR-013).
- All other rich-mode properties identical to `bookmark list`.

### Output — Plain Mode (pipe or `--plain`)

Identical format to `bookmark list` plain mode. No highlight codes.

### Empty-State Output

```
No bookmarks matched "your-query".
```

### Error Examples

```
Error: Missing argument 'QUERY'.
Error: QUERY must not be empty.
```

---

## Shared Behaviour

- Both commands read from the SQLite database at the path configured in the CLI context (path resolved via environment variable or default `~/.bookmarks.db`).
- Both commands call `store.initialize()` before any query.
- Column order: **ID, Title, URL, Tags, Date Added** (FR-014).
- `--plain` flag is available on both commands (FR-011).
- Piped output (non-TTY stdout) automatically uses plain-text mode regardless of `--plain` (FR-010).
