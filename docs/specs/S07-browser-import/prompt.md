# Spec Prompt: Browser Bookmark Import

## Feature
**S07 — Browser Bookmark Import**: Import bookmarks from browser-exported HTML files.

## Context
This is part of Track B (Import/Export). It depends on S05 and S06 being complete so that the `import` command infrastructure and duplicate handling are already in place.

## Scope

### In Scope
- `bookmark import --format html <file>`:
  - Parse the Netscape Bookmark File Format (the HTML format exported by Chrome, Firefox, Edge, and Safari).
  - Extract from each `<DT><A>` entry: URL (`HREF`), title (link text), and add date (`ADD_DATE` Unix timestamp).
  - Map bookmark folders (`<DT><H3>`) to tags (e.g., folder "Programming/Python" → tags `programming`, `python`).
  - Handle duplicates using the same `--on-duplicate` flag as S05/S06.
  - Print import summary: added, skipped, updated, errors.
- Tests using sample HTML bookmark files (include a small fixture in `tests/fixtures/`).

### Out of Scope
- Exporting to HTML format.
- Importing from browser-specific formats (e.g., Firefox JSON backups).
- Nested folder depth limits.

## Dependencies
- **S05**: JSON import establishes the `import` command group and `--on-duplicate` flag.
- **S06**: CSV import confirms the import summary pattern.

## Key Design Decisions
- Use Python's `html.parser` (no external dependency like BeautifulSoup).
- Folder hierarchy is flattened to tags (each folder level becomes a separate tag).
- `ADD_DATE` is converted from Unix timestamp to ISO 8601 for `created_at`.
