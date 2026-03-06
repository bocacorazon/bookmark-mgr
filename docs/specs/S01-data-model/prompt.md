# Spec Prompt: Data Model & Storage

## Feature
**S01 — Data Model & Storage**: Implement the SQLite-backed storage layer for bookmarks.

## Context
BookmarkCLI stores bookmarks locally in a SQLite database. This spec defines the core data model and all CRUD operations that other specs build on.

## Scope

### In Scope
- `Bookmark` dataclass/model with fields: `id` (int, auto), `url` (str, unique), `title` (str, optional), `tags` (list[str]), `created_at` (datetime), `updated_at` (datetime).
- `BookmarkStore` class:
  - `__init__(db_path)`: Open or create the SQLite database, run migrations.
  - `add(url, title, tags) -> Bookmark`: Insert a bookmark. Raise on duplicate URL.
  - `get(id) -> Bookmark | None`: Fetch by ID.
  - `get_by_url(url) -> Bookmark | None`: Fetch by URL.
  - `list(tag=None, limit=None, sort_by="created_at") -> list[Bookmark]`: List bookmarks with optional filters.
  - `search(query) -> list[Bookmark]`: Full-text search across URL and title.
  - `update(id, **fields) -> Bookmark`: Update fields, set `updated_at`.
  - `delete(id) -> bool`: Delete by ID.
  - `all_tags() -> list[tuple[str, int]]`: Return all tags with their bookmark counts.
- Tags stored in a separate `bookmark_tags` join table (normalized, lowercase, trimmed).
- Database schema migration on first run (create tables if not exist).
- Full pytest coverage for all `BookmarkStore` methods.

### Out of Scope
- CLI commands — those belong to S02+.
- Import/export — those belong to S05+.

## Dependencies
- **S00**: Project scaffold must exist.

## Key Design Decisions
- Store the database at `~/.local/share/bookmarkcli/bookmarks.db` by default.
- Tags are many-to-many via a join table (not comma-separated in a single column).
- Full-text search uses SQLite FTS5.
