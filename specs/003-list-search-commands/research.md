# Research: List & Search Commands

## 1. Terminal Rendering Library

**Decision**: Use `rich>=13.0`  
**Rationale**: `rich` is the de-facto standard for rich terminal output in Python. It provides `rich.table.Table` with built-in borders, colour, column alignment, overflow/ellipsis handling, and automatic TTY detection via `rich.console.Console(force_terminal=...)`. It also provides `rich.text.Text.highlight_words()` for search result highlighting. No other library covers all these requirements without additional glue code.  
**Alternatives considered**:
- `tabulate`: Produces plain/markdown/grid tables but has no colour/highlight support and no TTY auto-detection; would still require a second library for rich mode.
- `prettytable`: Similar to tabulate; no colour, no highlight.
- `columnar`: Lightweight but unmaintained and no highlight.
- Manual `str.ljust`/`str.rjust` formatting: Feasible for plain text only; too much bespoke code for rich mode.

---

## 2. TTY Detection

**Decision**: Use `rich.console.Console` with `force_terminal` driven by `sys.stdout.isatty()`; honour `--plain` flag by passing `force_terminal=False`.  
**Rationale**: `Console(force_terminal=True)` renders ANSI escape codes; `Console(force_terminal=False)` or `Console(no_color=True, highlight=False)` renders clean ASCII-safe text. Coupling detection to a single `Console` factory keeps the formatter stateless and easy to test.  
**Alternatives considered**:
- `click.get_terminal_size()`: Returns size but not a boolean; less idiomatic for this use.
- `os.isatty(sys.stdout.fileno())`: Equivalent to `sys.stdout.isatty()` but raises `io.UnsupportedOperation` in some test harnesses; `isatty()` method is safer.
- `NO_COLOR` env var: `rich` already respects this convention automatically.

---

## 3. Plain-Text Column Format

**Decision**: Use `rich.table.Table` with `box=rich.box.SIMPLE_HEAVY` stripped to `box=None` (no box drawing characters) and `show_header=True`, producing space-separated columns with a header underline. Alternatively, use `rich.table.Table(box=rich.box.MINIMAL_DOUBLE_HEAD)` for minimal separators.  
**Rationale**: Using the same `Table` object in both modes (toggled by `Console` settings) minimises code duplication. Plain output with consistent whitespace padding works reliably with `awk`/`cut` on fixed-width columns; for variable-width, tab (`\t`) separators are simpler for scripting.  
**Final choice**: Tab-separated values (`\t`) in plain mode, rendered by iterating rows directly. This is the most reliable format for `cut -f2`, `awk -F'\t'`, etc.  
**Alternatives considered**:
- Pipe-separated (`|`): Common in CLI tools but requires escaping if a value contains `|`.
- Space-padded fixed-width: Hard to predict column widths without two-pass rendering; breaks with long values even after truncation.

---

## 4. Tag Filtering Strategy

**Decision**: Apply tag filtering in SQLite using a parameterised `LIKE`-based pattern that matches exact tag tokens within the comma-separated `tags` column.  
**Rationale**: The spec requires exact, case-sensitive tag matching (e.g., `Dev` ≠ `dev`). Tags are stored as `"python,cli,dev"`. The SQL pattern `'%,' || ? || ',%'` plus boundary anchors handles leading/trailing/middle positions. Filtering at the SQL layer avoids loading unneeded rows.  
**SQL pattern (four disjuncts)**:
```sql
tags = ?                              -- only tag
OR tags LIKE ? || ',%'                -- first of several
OR tags LIKE '%,' || ?                -- last of several
OR tags LIKE '%,' || ? || ',%'        -- middle of several
```
**Alternatives considered**:
- Python-level filter after `list_all()`: Correct and simpler, fine for ≤10 K rows. Chosen as a fallback if SQL complexity proves bug-prone during implementation.
- SQLite FTS5 virtual table: Overkill for exact-match tag filtering on a comma-separated field.

---

## 5. Search Strategy

**Decision**: Use SQLite `LIKE` with `LOWER()` for case-insensitive substring matching; escape `%` and `_` metacharacters in the user query before embedding it in the pattern.  
**Rationale**: SQLite's `LIKE` is case-insensitive only for ASCII letters by default; wrapping both sides in `LOWER()` ensures correctness for mixed-case inputs. Escaping user input prevents accidental wildcard expansion (FR-009).  
**Escaping approach**:
```python
def _escape_like(query: str) -> str:
    return query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
```
Used with `ESCAPE '\\'` in the SQL clause.  
**SQL**:
```sql
WHERE LOWER(title) LIKE '%' || LOWER(?) || '%' ESCAPE '\'
   OR LOWER(url)   LIKE '%' || LOWER(?) || '%' ESCAPE '\'
ORDER BY created_at DESC
```
**Alternatives considered**:
- Python-level filter: Load all rows then filter with `query.lower() in (title or "").lower()`. Correct and avoids SQL escaping complexity; acceptable for ≤10 K rows. May be preferred for simplicity.
- SQLite FTS5: Full-text tokenisation; not suited for literal-prefix substring matching on URLs.
- `re.search` with `re.escape`: Works but adds regex overhead and requires Python-level loop over all rows.

---

## 6. Search Term Highlighting

**Decision**: Use `rich.text.Text` with `Text.highlight_regex(pattern, style)` where `pattern = re.escape(query)` with `re.IGNORECASE`.  
**Rationale**: `rich.text.Text.highlight_regex` applies a named style (e.g., `bold yellow`) to every non-overlapping match of a regex within a `Text` object. Using `re.escape` ensures the user's literal query is matched without regex interpretation.  
**Alternatives considered**:
- `Text.highlight_words([query], style)`: Only matches whole words, not substrings; unsuitable for URL partial matching.
- Manual string split and reassembly: Fragile; `rich.Text` is the idiomatic approach.

---

## 7. Value Truncation

**Decision**: Use `rich.table.Column(overflow="ellipsis", max_width=N)` where `N` is derived from terminal width (with a sensible minimum of 40 for title and 50 for URL). In plain mode, truncate manually using a helper that appends `…` (U+2026) when the value exceeds the column cap.  
**Rationale**: `rich` handles truncation automatically when `overflow="ellipsis"` is set. For plain mode, manual truncation with a Unicode ellipsis matches the spec requirement (FR-015).  
**Alternatives considered**:
- Truncate in the store layer: Wrong separation of concerns; the store should return raw data.
- Fixed 80-character width regardless of terminal: Poor UX on wide terminals; `rich` adapts automatically.

---

## 8. Sort Order Implementation

**Decision**: Implement sorting in SQL via a `CASE` expression on the `sort` parameter.  
**SQL**:
```sql
ORDER BY
  CASE WHEN sort = 'title' THEN LOWER(title) END ASC NULLS LAST,
  CASE WHEN sort = 'url'   THEN url END ASC,
  created_at DESC   -- default, also used when sort = 'date'
```
**Rationale**: Sorting at the SQL layer is more efficient than Python-level sorting for large datasets and avoids loading then re-sorting results.  
**Alternatives considered**:
- Python `sorted()`: Correct and simple; preferred if SQL CASE proves difficult to parameterise safely. Acceptable fallback.

---

## 9. `--limit` and `--sort` Validation

**Decision**: Validate in the Click command handler before any store calls.
- `--limit`: Click's `type=click.IntRange(min=1)` rejects non-integers and values ≤ 0 automatically with a clear error message.
- `--sort`: Click's `type=click.Choice(["date", "title", "url"])` rejects unrecognised fields automatically.
- Empty search query: Click's `required=True` on the positional argument handles missing query; a manual check rejects empty string.  

**Rationale**: Delegating validation to Click leverages its built-in error formatting and ensures non-zero exit codes for invalid input (FR-017) without bespoke guard code.
