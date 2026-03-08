# Research: List & Search Commands

**Feature**: S03 — List & Search Commands  
**Branch**: `001-list-search`  
**Date**: 2026-03-08

---

## 1. Rich Table Output

**Decision**: Use the `rich` library (`rich.table.Table`) for formatted terminal output.

**Rationale**:
- `rich` is the de-facto standard for Python CLI table rendering.
- Provides automatic column width handling, borders, colors, and alignment out of the box.
- `rich.console.Console(highlight=False)` with `force_terminal=False` (default) naturally falls back to plain text when stdout is piped, satisfying FR-008 and SC-004 with zero extra configuration.
- Widely used in Python CLI projects (Typer, FastAPI docs, etc.); well-maintained and stable.

**Terminal Detection**: `rich.console.Console` auto-detects `sys.stdout.isatty()`. When piped or redirected, it strips all ANSI escape codes automatically. No extra flags are needed in the CLI.

**Truncation**: `rich.table.Column(no_wrap=True)` with `overflow="ellipsis"` and a `max_width` truncates long values with `…` to preserve readability at standard terminal widths (FR-009 / edge case in spec).

**Alternatives Considered**:
- `tabulate` — simpler, but no colors/borders; would require manual truncation logic.
- `texttable` — fewer features; less actively maintained.
- Manual ANSI — error-prone; reinventing the wheel.

---

## 2. BookmarkStore Query Extensions

### 2a. Filtered List (`list_filtered`)

**Decision**: Add a `list_filtered(tag, limit, sort)` method to `BookmarkStore` that builds a parameterized SQL query.

**Rationale**:
- Keeps all data-access logic inside `BookmarkStore`, consistent with the S01 pattern.
- SQLite handles all filtering/sorting server-side, so it scales to 10,000 records well within the 1-second target (SC-001, SC-002).
- `ORDER BY created_at DESC` (newest) / `ASC` (oldest) directly maps to the `--sort` values from FR-004/FR-005.
- Tag filtering uses `INSTR(','||tags||',', ','||?||',')` to perform an exact comma-delimited tag match — avoids matching `python` inside `micropython` (assumption: exact tag match, not substring).
- `LIMIT ?` clause handles `--limit` (FR-003). `--limit 0` returns empty result set (spec edge case: "show none").

**Alternatives Considered**:
- Building the query in the CLI layer — violates single-responsibility; harder to unit-test.
- ORM (SQLAlchemy) — overkill for a small SQLite CLI tool; adds dependency weight.

### 2b. Full-Text Search (`search`)

**Decision**: Add a `search(query)` method that uses SQL `LIKE '%?%'` with `LOWER()` on both sides for case-insensitive substring matching across `title` and `url`.

**Rationale**:
- `LOWER(title) LIKE LOWER('%' || ? || '%') OR LOWER(url) LIKE LOWER('%' || ? || '%')` is straightforward, requires no schema changes, and performs acceptably for up to 10,000 records.
- Satisfies FR-006, FR-007, and the case-insensitivity requirement (Acceptance Scenario 4 of User Story 4).
- SQLite FTS5 would add schema complexity (new virtual table, triggers) without meaningful gain at this scale.

**Alternatives Considered**:
- SQLite FTS5 — powerful, but over-engineered for < 10k rows with simple substring requirements; spec explicitly says "substring matching, no advanced ranking".
- Python-side filtering after `list_all()` — correct but wastes memory and bypasses DB indexes; avoids for clarity.

---

## 3. Click CLI Integration

**Decision**: Add `list_cmd` (aliased to `list` — note: `list` is a Python builtin, so the Click command is named `list` with the Python function `list_cmd`) and `search_cmd` as `@main.command()` decorators.

**Rationale**:
- Matches the existing CLI pattern in `cli.py` (Click group `main`).
- Click's `@click.option` provides built-in validation for `--sort` via `type=click.Choice(["newest", "oldest"])` — satisfies FR-012.
- `--limit` uses `type=click.INT` with a custom callback or `is_eager=False` to validate positive-only values — satisfies FR-011.
- Empty search query is validated before invoking the store (FR-013): `if not query.strip(): raise UsageError(...)`.

**DB Path Resolution**: Passed via `Click.Context` object or a shared `--db` root option. Research shows Click's `pass_context` or `Context.obj` pattern is idiomatic. For simplicity, a `DB_PATH` constant derived from `platformdirs` or a default path is used (consistent with S01 pattern — check existing `cli.py`).

**Note**: The existing `cli.py` has no DB wiring yet. A `pass_context` pattern or a module-level default path constant will be established in this feature.

---

## 4. Empty State Messages

**Decision**: Display `"No bookmarks found."` (list empty store) or `"No bookmarks match your search."` (filtered/search no results) as styled `rich` text when in terminal mode, plain text when piped.

**Rationale**: Satisfies FR-010 / Acceptance Scenarios for User Stories 1–4.

---

## 5. Output Format Detection Summary

| Scenario | Behavior |
|----------|----------|
| stdout is a TTY | `rich` table with borders, colors |
| stdout is piped / redirected | Plain-text table (tab/space separated), no ANSI codes |
| `rich.Console` default | Auto-detects; no explicit `--plain` flag needed |

---

## 6. Dependencies to Add

| Package | Version | Reason |
|---------|---------|--------|
| `rich` | `>=13.0` | Terminal table rendering with auto plain-text fallback |

No other new runtime dependencies required.
