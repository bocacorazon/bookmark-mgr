# Data Model: List & Search Commands

## Existing Entities (unchanged from S02)

### Bookmark

Defined in `src/bookmarkcli/models.py`.

| Field        | Type             | Nullable | Description                                      |
|--------------|------------------|----------|--------------------------------------------------|
| `id`         | `int \| None`    | Yes (pre-insert only) | Auto-increment primary key                |
| `url`        | `str`            | No       | The bookmarked URL; must be non-empty            |
| `title`      | `str \| None`    | Yes      | Human-readable page title                       |
| `tags`       | `list[str]`      | No       | Zero or more labels; stored as comma-separated string in SQLite |
| `created_at` | `datetime` (UTC) | No       | Timestamp of insertion; always UTC-aware         |
| `updated_at` | `datetime` (UTC) | No       | Timestamp of last update; always UTC-aware       |

**Storage serialisation**: Tags are stored as `"tag1,tag2,tag3"` in the `tags TEXT` column. An empty list serialises to `""`.

**Validation rules** (enforced by `BookmarkStore`):
- `url` must not be empty or whitespace-only (`BookmarkValidationError`).
- `id` is `None` before insertion; always a positive integer after.

---

## Store Extensions (new in S03)

Two new methods are added to `BookmarkStore` in `src/bookmarkcli/store.py`. The `Bookmark` dataclass itself is **not modified**.

### `list_filtered`

```python
def list_filtered(
    self,
    tag: str | None = None,
    limit: int | None = None,
    sort: str = "date",
) -> list[Bookmark]:
```

**Parameters**:

| Parameter | Type           | Default  | Description                                                      |
|-----------|----------------|----------|------------------------------------------------------------------|
| `tag`     | `str \| None`  | `None`   | Exact, case-sensitive tag filter. `None` = no filter.            |
| `limit`   | `int \| None`  | `None`   | Maximum rows to return (applied after filtering and sorting). `None` = no limit. Must be a positive integer when provided. |
| `sort`    | `str`          | `"date"` | Sort field. Accepted values: `"date"` (newest-first), `"title"` (ascending, case-insensitive), `"url"` (ascending). |

**Returns**: `list[Bookmark]` — sorted, filtered, and capped to `limit`.

**Filtering logic**:
- When `tag` is provided, only bookmarks carrying that **exact** tag token are included. Tag matching is case-sensitive and token-exact (e.g., `"Dev"` does not match `"dev"`).
- SQL-level tag pattern matches tag in any position within the comma-separated `tags` column.

**Sorting logic** (applied before limit):
- `"date"`: `ORDER BY created_at DESC` (newest first)
- `"title"`: `ORDER BY LOWER(title) ASC NULLS LAST`
- `"url"`: `ORDER BY url ASC`

**Error behaviour**: Raises `ValueError` if `sort` is not one of the accepted values (defensive; normally prevented by CLI validation).

---

### `search`

```python
def search(self, query: str) -> list[Bookmark]:
```

**Parameters**:

| Parameter | Type  | Description                                                                 |
|-----------|-------|-----------------------------------------------------------------------------|
| `query`   | `str` | Literal search string. Must be non-empty (validated by CLI before calling). |

**Returns**: `list[Bookmark]` — all bookmarks whose `title` or `url` contains `query` as a case-insensitive substring, ordered newest-first.

**Matching rules**:
- Case-insensitive substring match across `title` and `url`.
- Special characters (`%`, `_`, `\`) in `query` are escaped and treated as literals (FR-009).
- A bookmark is included if either `title` OR `url` matches.

**Implementation note**: Uses `LOWER(column) LIKE '%' || LOWER(?) || '%' ESCAPE '\'` with `%` and `_` pre-escaped in the query string.

---

## New Module: `formatter.py`

`src/bookmarkcli/formatter.py` — rendering logic, no domain model changes.

### `render_table`

```python
def render_table(
    bookmarks: list[Bookmark],
    *,
    plain: bool = False,
    query: str | None = None,
) -> None:
```

**Parameters**:

| Parameter   | Type               | Description                                                     |
|-------------|--------------------|-----------------------------------------------------------------|
| `bookmarks` | `list[Bookmark]`   | Rows to display.                                                |
| `plain`     | `bool`             | `True` → force plain-text output; `False` → auto-detect TTY.   |
| `query`     | `str \| None`      | When provided (search mode), highlight this term in rich output.|

**Behaviour**:
- When `plain=False` and stdout is a TTY: renders a `rich.table.Table` with borders, colour, and (if `query`) highlighted matching terms.
- When `plain=True` or stdout is not a TTY: renders tab-separated plain text with a header line.
- When `bookmarks` is empty: prints an empty-state message (e.g., `"No bookmarks found."`) instead of an empty table.

**Columns rendered** (FR-014):

| Column      | Source field    | Max width (rich) | Overflow  |
|-------------|-----------------|------------------|-----------|
| ID          | `id`            | 6                | crop      |
| Title       | `title`         | 40               | ellipsis  |
| URL         | `url`           | 50               | ellipsis  |
| Tags        | `tags` (joined) | 25               | ellipsis  |
| Date Added  | `created_at`    | 20               | crop      |

---

## State Transitions

No state transitions — `list` and `search` are read-only operations. No mutations to `Bookmark` records occur during this feature.

---

## Validation Rules Summary

| Rule                     | Enforced by         | Behaviour on violation           |
|--------------------------|---------------------|----------------------------------|
| `--limit` must be ≥ 1    | Click `IntRange`    | Error message + exit code 2      |
| `--sort` must be valid   | Click `Choice`      | Error message + exit code 2      |
| `query` must be non-empty| CLI guard + `required=True` | Error message + exit code 2 |
| `store` must be initialised | `BookmarkStore._require_connection()` | `RuntimeError` |
