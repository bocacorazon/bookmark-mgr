# Research: CSV Import/Export

**Branch**: `001-csv-import-export` | **Date**: 2026-03-07

## Resolved Decisions

### 1. CSV Parsing Library

**Decision**: Python stdlib `csv` module (no new runtime dependency).

**Rationale**: `csv.DictReader` / `csv.DictWriter` handle RFC 4180 fully — quoted fields, embedded commas, CRLF line endings — without any external package. `csv.DictWriter` generates the header row automatically from `fieldnames`. `csv.DictReader` maps columns by name, so extra columns are silently available in `row.keys()` and can be ignored simply by accessing only the known keys.

**Alternatives Considered**:
- `pandas` — powerful but a heavy dependency (~35 MB wheel); overkill for sequential row processing with no vectorised operations needed.
- `petl` — lightweight ETL library; still an unnecessary dependency for a task stdlib handles cleanly.

---

### 2. Tag Separator: Semicolons in CSV vs. Commas in Store

**Decision**: Use semicolons (`;`) as the separator in the CSV `tags` column; convert to/from the store's internal comma-separated format at the CSV I/O boundary in `csv_io.py`.

**Rationale**: The spec mandates semicolons. The store already serialises tags as comma-separated strings (`_serialize_tags` / `_deserialize_tags` in `store.py`). Conversion belongs at the CSV boundary to keep the store API unchanged.

**Implementation**:
```python
# Export: store tags list → CSV tags string
csv_tags = ";".join(bookmark.tags)

# Import: CSV tags string → store tags list
tags = [t.strip() for t in csv_tags.split(";") if t.strip()]
```

---

### 3. `created_at` Datetime Handling

**Decision**: `datetime.fromisoformat()` for parsing; `.isoformat()` for serialisation. Fall back to `None` (use current time) when the field is absent or unparseable.

**Rationale**: Python 3.11 extended `fromisoformat()` to accept the full ISO 8601 offset syntax (e.g., `+00:00`, `Z`). The spec requires ISO 8601 format; the existing store already stores and retrieves ISO 8601 strings. Timezone-naive values are treated as UTC (matching `store._row_to_bookmark` behaviour).

**Malformed date rule** (FR-012): If `created_at` is present but raises `ValueError` from `fromisoformat()`, skip the row. If absent or empty string, use `datetime.now(tz=timezone.utc)`.

---

### 4. Click Command Structure

**Decision**: `export` and `import` as top-level sub-commands of the existing `main` Click group. Both accept `--format` as a required option (value `csv`) for forward compatibility with future formats.

**Rationale**: The existing CLI has a single `@click.group()` called `main`. Adding `@main.command()` functions for `export` and `import` follows the established pattern.

**Import command note**: `import` is a Python reserved word; the Click command function is named `import_cmd` and exposed as `"import"` via `@main.command(name="import")`.

**Export `--file` option**: `click.Path(writable=True, dir_okay=False)` with `default=None`. When `None`, write to `sys.stdout` via `click.get_text_stream('stdout')`.

**Import `FILE` argument**: `click.Path(exists=True, readable=True, dir_okay=False)` — Click handles the "file not found" error automatically (FR-016).

---

### 5. `ImportResult` / `SkippedRow` Design

**Decision**: Two new dataclasses added to `models.py`:

```python
@dataclass
class SkippedRow:
    row_number: int   # 1-based (excluding header)
    reason: str

@dataclass
class ImportResult:
    imported: int
    skipped: int
    skipped_rows: list[SkippedRow]
```

**Rationale**: Keeps the result structure serialisable and testable without coupling to Click. The CLI layer formats the result into human-readable output.

---

### 6. `csv_io.py` Module Responsibilities

**Decision**: A single `csv_io.py` module with two public functions:

```python
def export_bookmarks(bookmarks: list[Bookmark], dest: IO[str]) -> None: ...
def import_bookmarks(src: IO[str], store: BookmarkStore) -> ImportResult: ...
```

**Rationale**: Pure-ish functions (no Click dependency) make unit testing straightforward with `io.StringIO`. The CLI layer opens files and calls these functions.

---

### 7. Exit Code on All-Rows-Malformed (FR-015)

**Decision**: `sys.exit(1)` / `raise SystemExit(1)` via `ctx.exit(1)` in the Click command when `result.imported == 0` and `result.skipped > 0`.

**Rationale**: Standard CLI convention for "processed input but nothing succeeded". Click's `ctx.exit()` is preferred over raw `sys.exit()` for testability with `CliRunner`.

---

### 8. File Already Exists on Export

**Decision**: Overwrite silently (standard CLI convention, per spec edge case).

**Rationale**: The spec explicitly states "The file is overwritten without warning". `open(path, 'w')` achieves this.

---

### 9. Header-Required Validation (FR-007)

**Decision**: After opening the file with `csv.DictReader`, check `reader.fieldnames`. If `None` (empty file) or `'url'` not in `reader.fieldnames`, emit an error and exit non-zero.

**Rationale**: `DictReader` populates `fieldnames` from the first row. An empty file yields `None`. A header without `url` is ambiguous but cannot be processed.
