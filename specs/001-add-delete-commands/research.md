# Research: Add & Delete Commands

**Feature**: 001-add-delete-commands  
**Date**: 2026-03-07  
**Status**: Complete — no NEEDS CLARIFICATION items remain

---

## Research Items

### 1. URL Validation Strategy

**Question**: Which approach should validate the URL format (scheme + host required, per FR-004)?

**Decision**: Use `urllib.parse.urlparse` from Python's standard library.

**Rationale**:
- No new runtime dependency (keeps `pyproject.toml` unchanged).
- Checks for non-empty `scheme` and `netloc` — exactly the "scheme + host" requirement in FR-004.
- Already available everywhere Python 3.11 is installed.
- Handles edge cases like `https://` (scheme present, host empty → invalid) and `not-a-valid-url` (no scheme → invalid).

**Validation function**:
```python
from urllib.parse import urlparse

def _is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return bool(result.scheme and result.netloc)
    except ValueError:
        return False
```

**Alternatives considered**:
- `validators` (PyPI) — adds a runtime dependency; overkill for basic scheme+host check.
- Custom regex — fragile; harder to maintain than stdlib.
- `httpx`/`yarl` — heavy transitive dependencies; inappropriate for a lightweight CLI.

---

### 2. Duplicate Detection (find bookmark by URL)

**Question**: How should the CLI detect that a URL already exists in the store (FR-005)?

**Decision**: Add a `find_by_url(url: str) -> Bookmark | None` method to `BookmarkStore`, backed by a `WHERE url = ?` SQL query.

**Rationale**:
- Keeps duplicate detection O(1) in SQL rather than loading all bookmarks into Python.
- Clean separation of concerns: store owns all SQL; CLI layer calls `find_by_url`.
- Additive change — does not break any existing `BookmarkStore` callers.

**New store method**:
```python
def find_by_url(self, url: str) -> Bookmark | None:
    con = self._require_connection()
    row = con.execute(
        "SELECT id, url, title, tags, created_at, updated_at FROM bookmarks WHERE url = ?",
        (url,),
    ).fetchone()
    return self._row_to_bookmark(row) if row is not None else None
```

**Alternatives considered**:
- `list_all()` + Python filter — O(n) scan; becomes slow for large stores.
- Relying on a UNIQUE database constraint + catching `IntegrityError` — works but obscures intent and requires schema migration; deferred to a later hardening spec.

---

### 3. Delete Argument Dispatch (ID vs URL)

**Question**: How should `bookmark delete <arg>` distinguish between a numeric ID and a URL (FR-007)?

**Decision**: Attempt `int(arg)` — if it succeeds, treat as ID; otherwise treat as URL.

**Rationale**:
- Numeric IDs are always valid integers; URLs never are (they contain `://`).
- Simple, no regex required, matches the spec edge-case note: "numeric = ID, URL-shaped = URL".
- Graceful fallback: if integer parse fails the value is assumed to be a URL; if no matching URL is found, a not-found error is reported.

**Dispatch logic**:
```python
try:
    bookmark_id = int(arg)
    bookmark = store.get(bookmark_id)   # raises BookmarkNotFoundError if missing
except ValueError:
    bookmark = store.find_by_url(arg)   # returns None if missing
    if bookmark is None:
        raise BookmarkNotFoundError(...)
```

**Alternatives considered**:
- Separate `--id` / `--url` flags — more explicit but worse UX; spec says single positional arg.
- URL regex detection before integer attempt — over-engineering; integer parse is simpler.

---

### 4. Database Path & Configuration

**Question**: Where does the CLI persist bookmarks, and how can it be overridden?

**Decision**: Default to `~/.bookmarkcli/bookmarks.db`. Support override via environment variable `BOOKMARKCLI_DB`.

**Rationale**:
- `~/.bookmarkcli/` is a conventional hidden directory for a user-scoped CLI tool.
- Environment variable override (no CLI flag needed) keeps the command surface clean and enables testing/scripting without touching real user data.
- Click's `auto_envvar_prefix` or `click.option(..., envvar=...)` makes this easy to implement.

**Implementation**:
```python
import os
from pathlib import Path

DEFAULT_DB = Path.home() / ".bookmarkcli" / "bookmarks.db"

def _get_db_path() -> Path:
    env = os.environ.get("BOOKMARKCLI_DB")
    return Path(env) if env else DEFAULT_DB
```

**Alternatives considered**:
- `~/.local/share/bookmarkcli/bookmarks.db` (XDG) — more correct on Linux but adds complexity and requires XDG detection; deferred.
- Pass `--db` flag on every command — verbose UX; environment variable is more ergonomic.

---

### 5. Confirmation Prompt Pattern

**Question**: How should `bookmark delete` implement the "default No" confirmation prompt (FR-008, FR-010)?

**Decision**: Use `click.confirm("Delete this bookmark? [y/N]", default=False)`.

**Rationale**:
- `click.confirm` handles `y/Y/yes` → `True` and `n/N/no/Enter` → `False` out of the box.
- `default=False` means pressing Enter without typing defaults to No, satisfying SC-004.
- In tests, `CliRunner(mix_stderr=False)` with `input="y\n"` or `input="\n"` simulates both paths.

**Alternatives considered**:
- Manual `input()` loop — re-invents what Click already provides; harder to test.
- `--force` / `--yes` flag — skips confirmation entirely; out of scope and reduces safety.

---

### 6. New Exception: `DuplicateBookmarkError`

**Question**: Should duplicate-URL detection raise a new exception type or reuse `BookmarkValidationError`?

**Decision**: Introduce `DuplicateBookmarkError(Exception)` in `bookmarkcli.models`.

**Rationale**:
- Allows callers (and tests) to distinguish "URL already stored" from "URL is syntactically invalid".
- Both are user-facing errors that produce non-zero exit codes (FR-012), but the message and handling differ.
- Additive change to `models.py`; does not break existing callers.

**Alternatives considered**:
- Reuse `BookmarkValidationError` with a message — conflates two distinct error conditions; harder to test specifically.
- Raise `BookmarkNotFoundError` in reverse — semantically wrong.

---

### 7. Tags Parsing

**Question**: How should `--tags news,tech` be parsed into `["news", "tech"]`?

**Decision**: Split on commas and strip whitespace from each element; drop empty elements.

**Implementation**:
```python
def _parse_tags(raw: str) -> list[str]:
    return [t.strip() for t in raw.split(",") if t.strip()]
```

**Rationale**: Matches the spec assumption: "split on commas; leading/trailing whitespace around each tag name is trimmed." Empty or whitespace-only `--tags` values produce an empty list, consistent with not passing the flag at all.

---

## Summary of Decisions

| # | Topic | Decision |
|---|-------|----------|
| 1 | URL validation | `urllib.parse.urlparse` — scheme + netloc required |
| 2 | Duplicate detection | Add `find_by_url()` to `BookmarkStore` |
| 3 | Delete arg dispatch | `int(arg)` → ID; `ValueError` → URL |
| 4 | DB path | `~/.bookmarkcli/bookmarks.db` / `BOOKMARKCLI_DB` env var |
| 5 | Confirmation prompt | `click.confirm(..., default=False)` |
| 6 | Duplicate error | New `DuplicateBookmarkError` in `models.py` |
| 7 | Tags parsing | comma-split + strip + drop empty |
