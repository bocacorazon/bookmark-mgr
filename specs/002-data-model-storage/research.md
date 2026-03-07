# Research: Data Model & Storage

**Feature**: 002-data-model-storage  
**Date**: 2026-03-07  
**Status**: Complete — all decisions resolved

---

## R-001: Storage Engine — `sqlite3` (stdlib)

- **Decision**: Use Python's built-in `sqlite3` module (synchronous) rather than `aiosqlite`.
- **Rationale**: The CLI is a single-process, single-user tool executing commands sequentially. There is no event loop, no concurrent I/O, and no benefit to async database access. The stdlib `sqlite3` module requires zero additional dependencies, ships with every CPython ≥ 3.11 installation, and is fully capable of satisfying all functional requirements. `aiosqlite` (already in dev deps) was declared in S00 as a placeholder for _future_ features; it is not exercised here.
- **Alternatives considered**: `aiosqlite` (async wrapper — no event loop in CLI path; adds indirection with no benefit), `SQLAlchemy` (full ORM — heavy for a single table at this scale), `Peewee`/`TinyDB` (third-party; adds dependency).
- **Resolved**: Use `sqlite3` from stdlib — no new runtime dependency.

---

## R-002: Schema Migration — `PRAGMA user_version`

- **Decision**: Track schema version with SQLite's built-in `PRAGMA user_version`. On every `BookmarkStore` initialization, compare the stored version to the current application version and apply migration SQL in order.
- **Rationale**: `PRAGMA user_version` is a 32-bit integer stored in the SQLite file header — no extra migration table required. This is the recommended lightweight pattern for single-developer SQLite projects. It supports FR-002 (auto-init) and FR-003 (auto-migrate) with minimal code.
- **Current version**: `1` (initial schema).
- **Migration ladder**:
  - `0 → 1`: `CREATE TABLE bookmarks (...)` — applied on first init.
- **Alternatives considered**: `alembic` (industrial-strength, targets SQLAlchemy, overkill here), `yoyo-migrations` (third-party), storing version in a dedicated `schema_versions` table (redundant when `PRAGMA user_version` exists).
- **Resolved**: `PRAGMA user_version` pattern — standard and dependency-free.

---

## R-003: Tags Storage — Comma-Separated String

- **Decision**: Store tags as a single `TEXT` column containing a comma-separated list (e.g., `"python,cli,bookmark"`). The empty-tags case is stored as an empty string `""` or `NULL`.
- **Rationale**: The spec explicitly states _"Tags are stored as a simple string with a defined delimiter (e.g., comma-separated)"_ and _"advanced tag querying is out of scope for this feature."_ A separate tags table or JSON array would add schema complexity with no current benefit. Serialization/deserialization (`","join` / `",".split`) is trivial and lives entirely in `BookmarkStore`.
- **Tag rules**:
  - Tags may not contain commas (treated as delimiters).
  - Leading/trailing whitespace on individual tags is stripped on write.
  - An empty list and `None` are both serialized as `""` (empty string).
  - On read, an empty string deserializes to `[]`.
- **Alternatives considered**: Separate `tags` table with many-to-many join (future-proof but over-engineered for this feature), JSON column with `json_each` (SQLite ≥ 3.38 only, less portable, spec doesn't require JSON querying).
- **Resolved**: Comma-separated `TEXT` column in `bookmarks` table.

---

## R-004: Identifier Type — `INTEGER PRIMARY KEY AUTOINCREMENT`

- **Decision**: Use `INTEGER PRIMARY KEY AUTOINCREMENT` as the bookmark ID.
- **Rationale**: The spec states _"Auto-increment integers serve as bookmark IDs for simplicity; the format is considered an implementation detail."_ SQLite's `ROWID` alias via `INTEGER PRIMARY KEY` provides a unique, stable, monotonically increasing integer at zero extra cost. The `AUTOINCREMENT` keyword adds the guarantee that deleted IDs are never reused (prevents confusion in external references), at a negligible performance cost for single-user scale.
- **Alternatives considered**: UUID (string — more portable but heavier and spec explicitly allows integers), `WITHOUT ROWID` table (optimised for range scans — irrelevant at this scale), application-generated UUIDs (unnecessary complexity).
- **Resolved**: `INTEGER PRIMARY KEY AUTOINCREMENT` — matches spec assumption.

---

## R-005: Timestamp Handling — ISO 8601 UTC Strings

- **Decision**: Store `created_at` and `updated_at` as `TEXT` columns in ISO 8601 format (`YYYY-MM-DDTHH:MM:SS.ffffff`) in UTC. Return them as Python `datetime` objects (timezone-aware, UTC) in the `Bookmark` dataclass.
- **Rationale**: SQLite has no native `DATETIME` type; TEXT with ISO 8601 format is the canonical approach recommended in the SQLite documentation and supported by Python's `datetime.fromisoformat()`. UTC-only storage avoids timezone arithmetic at the storage layer. `datetime.now(tz=timezone.utc)` provides the current timestamp with microsecond precision.
- **Alternatives considered**: Unix epoch integers (compact but opaque), SQLite `CURRENT_TIMESTAMP` trigger (DB-side timestamp; harder to override in tests), `pendulum` / `arrow` libraries (third-party; no added value for UTC-only storage).
- **Resolved**: ISO 8601 TEXT stored/retrieved as `datetime` with `timezone.utc`.

---

## R-006: Error Signalling — Custom Exceptions

- **Decision**: Define two exception classes in `models.py`:
  - `BookmarkNotFoundError(Exception)` — raised by `get`, `update`, and `delete` when the requested ID does not exist (FR-013).
  - `BookmarkValidationError(Exception)` — raised by `create` when `url` is absent or empty (FR-005).
- **Rationale**: Distinct exception types allow calling code to handle "not found" and "invalid input" cases independently without inspecting error messages. This is the standard Python exception hierarchy pattern. Both exceptions carry a human-readable message for display.
- **Alternatives considered**: Return `None` for missing records (ambiguous — conflates "not found" with "no result"), `Optional[Bookmark]` with `None` sentinel (forces callers to always check, error-prone), integer error codes (non-Pythonic).
- **Resolved**: `BookmarkNotFoundError` and `BookmarkValidationError` in `models.py`.

---

## R-007: Domain Object — `dataclass`

- **Decision**: Represent the `Bookmark` entity as a `@dataclass` with typed fields (Python 3.11 `from __future__ import annotations` not required; `list[str]` type syntax available natively).
- **Rationale**: `@dataclass` provides `__init__`, `__repr__`, and `__eq__` for free, making test assertions straightforward (`assert bookmark.title == "Expected"`). It is stdlib, requires no dependencies, and signals that `Bookmark` is a pure data container with no business logic.
- **Fields**:
  - `id: int | None` — `None` before insertion; populated by `BookmarkStore.create()`.
  - `url: str`
  - `title: str | None`
  - `tags: list[str]` (default `[]`)
  - `created_at: datetime`
  - `updated_at: datetime`
- **Alternatives considered**: `TypedDict` (no default values, no `__eq__`), `NamedTuple` (immutable — prevents in-place update in tests), Pydantic `BaseModel` (third-party).
- **Resolved**: `@dataclass` — stdlib, testable, idiomatic.

---

## R-008: `update()` Sentinel — `MISSING` for Optional Fields

- **Decision**: Use a module-level `MISSING` sentinel object (similar to `dataclasses.MISSING`) for `update()` parameters to distinguish "caller passed `None`" from "caller did not provide the field."
- **Rationale**: `update(id, title=None, tags=None)` is ambiguous: does `title=None` mean "clear the title" or "don't touch the title"? A sentinel lets the store update only the fields the caller explicitly provides. This satisfies the spec edge case: _"How does the system handle an update where no fields are changed? The operation succeeds; the modification timestamp is still refreshed."_
- **Signature**:
  ```python
  def update(
      self,
      bookmark_id: int,
      title: str | None | _MISSING_TYPE = MISSING,
      tags: list[str] | _MISSING_TYPE = MISSING,
  ) -> Bookmark
  ```
- **Alternatives considered**: `**kwargs` dict (loses type safety), always-required fields (breaks the "update only what's provided" contract), `Optional` with a separate `clear_title: bool` flag (verbose).
- **Resolved**: `MISSING` sentinel pattern — standard Python idiom.

---

## Summary of Resolved Items

| ID    | Topic                              | Status   |
|-------|------------------------------------|----------|
| R-001 | Storage engine (sqlite3 stdlib)    | Resolved |
| R-002 | Schema migration (PRAGMA user_version) | Resolved |
| R-003 | Tags storage (comma-separated)     | Resolved |
| R-004 | ID type (INTEGER AUTOINCREMENT)    | Resolved |
| R-005 | Timestamps (ISO 8601 UTC TEXT)     | Resolved |
| R-006 | Error signalling (custom exceptions) | Resolved |
| R-007 | Domain object (@dataclass)         | Resolved |
| R-008 | update() sentinel (MISSING)        | Resolved |

**No NEEDS CLARIFICATION items remain.**
