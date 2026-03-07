# Feature Specification: CSV Import/Export

**Feature Branch**: `001-csv-import-export`  
**Created**: 2026-03-07  
**Status**: Draft  
**Input**: User description: "bookmark export --format csv [--file out.csv] and bookmark import --format csv <file>. Map columns: url, title, tags (semicolon-separated), created_at. Handle malformed rows gracefully."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export Bookmarks to CSV (Priority: P1)

A user wants to back up or share their bookmark library in a portable, universally readable format. They run a single export command and receive a CSV file — or standard output — containing all their bookmarks with URL, title, tags, and creation date.

**Why this priority**: Export is the simpler direction with no risk of data loss, and it enables data portability for backup and sharing. It also validates the CSV column mapping before import is built.

**Independent Test**: Can be fully tested by populating the bookmark store with several bookmarks (including ones with multiple tags), running the export command with and without `--file`, and verifying the CSV content matches the stored data.

**Acceptance Scenarios**:

1. **Given** a bookmark store with several bookmarks, **When** the user runs `bookmark export --format csv`, **Then** CSV content is written to standard output with a header row and one data row per bookmark.
2. **Given** a bookmark store with several bookmarks, **When** the user runs `bookmark export --format csv --file out.csv`, **Then** a file `out.csv` is created containing the same CSV content.
3. **Given** a bookmark with tags "python" and "dev", **When** the export runs, **Then** the tags column contains `python;dev` (semicolon-separated, no spaces).
4. **Given** an empty bookmark store, **When** the export runs, **Then** only the header row is output and the command exits successfully.
5. **Given** the user specifies `--file out.csv` and the path is not writable, **When** the export runs, **Then** a clear error message is displayed and no partial file is left.

---

### User Story 2 - Import Bookmarks from CSV (Priority: P2)

A user wants to bulk-load bookmarks from a CSV file — for example, migrating from another tool or restoring from a backup. They run an import command pointing at the CSV file, and all valid rows are added to their bookmark store.

**Why this priority**: Import completes the round-trip data portability story and enables migration from other tools, but depends on the export column mapping being stable first.

**Independent Test**: Can be fully tested by preparing a CSV file with valid bookmark rows, running the import command, and confirming each valid row appears in the bookmark store with correct field values.

**Acceptance Scenarios**:

1. **Given** a valid CSV file with a header row and several data rows, **When** the user runs `bookmark import --format csv <file>`, **Then** each valid row is added to the bookmark store and a success summary is displayed.
2. **Given** a CSV file where the tags column contains `python;dev`, **When** the import runs, **Then** the resulting bookmark has the tags "python" and "dev" stored as individual tags.
3. **Given** a CSV file where `created_at` is provided, **When** the import runs, **Then** the stored bookmark's creation timestamp matches the value from the CSV.
4. **Given** a CSV file where `created_at` is absent or empty for a row, **When** the import runs, **Then** the current time is used as the creation timestamp for that bookmark.
5. **Given** a non-existent file path, **When** the user runs `bookmark import --format csv missing.csv`, **Then** a clear error is displayed and no bookmarks are modified.

---

### User Story 3 - Graceful Handling of Malformed Import Rows (Priority: P3)

A user imports a CSV file that contains some malformed or incomplete rows mixed with valid ones. The tool skips invalid rows without aborting and reports exactly which rows were skipped and why.

**Why this priority**: Resilient error handling enables importing from real-world CSV sources (e.g., browser exports) that may have inconsistencies, without requiring the user to manually clean the entire file first.

**Independent Test**: Can be fully tested by crafting a CSV file with a mix of valid rows and known-bad rows (missing URL, extra columns, malformed date), running import, and verifying only the valid rows appear in the store while the summary accurately reports skipped row counts.

**Acceptance Scenarios**:

1. **Given** a CSV file with 5 valid rows and 2 rows missing the `url` field, **When** the import runs, **Then** 5 bookmarks are added, 2 rows are skipped, and the summary reports "5 imported, 2 skipped".
2. **Given** a CSV file with a row whose `url` field is blank, **When** the import runs, **Then** that row is skipped and the rest are imported normally.
3. **Given** a CSV file with rows containing extra unexpected columns, **When** the import runs, **Then** the extra columns are ignored and the row is imported using only the known columns.
4. **Given** a CSV file where every row is malformed, **When** the import runs, **Then** zero bookmarks are added, all rows are reported as skipped, and the command exits with a non-zero status.
5. **Given** a CSV file with no header row, **When** the import runs, **Then** a clear error is displayed explaining that a header row is required.

---

### Edge Cases

- What happens when the export `--file` path already exists? The file is overwritten without warning (standard CLI convention; future versions may add `--force`).
- How does the system handle a URL that already exists in the store during import? The duplicate row is imported as a new entry; deduplication is out of scope for this feature.
- What happens when a `created_at` value cannot be parsed as a date? The row is treated as malformed and skipped, with a note in the summary.
- What happens when the CSV file is empty (zero bytes or header-only)? The import exits successfully with "0 imported, 0 skipped".
- What happens when a tag in the semicolon-separated list is an empty string (e.g., `python;;dev`)? Empty segments are silently ignored; only non-empty tag values are stored.
- What happens if the CSV contains Windows-style line endings (CRLF)? The import handles both CRLF and LF line endings transparently.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Users MUST be able to export all bookmarks to CSV format using `bookmark export --format csv`.
- **FR-002**: The export command MUST write CSV output to standard output when `--file` is not specified.
- **FR-003**: The export command MUST write CSV output to the specified file when `--file <path>` is provided.
- **FR-004**: The exported CSV MUST include a header row with columns in this order: `url`, `title`, `tags`, `created_at`.
- **FR-005**: The `tags` column MUST encode multiple tags as a single semicolon-separated string (e.g., `python;dev`).
- **FR-006**: Users MUST be able to import bookmarks from a CSV file using `bookmark import --format csv <file>`.
- **FR-007**: The import command MUST require the CSV file to have a header row; absence of a header MUST produce a clear error.
- **FR-008**: The import command MUST parse the `tags` column by splitting on semicolons and storing each non-empty segment as an individual tag.
- **FR-009**: When `created_at` is present and parseable in an import row, the stored bookmark MUST use that value as its creation timestamp.
- **FR-010**: When `created_at` is absent or unparseable in an import row, the current time MUST be used as the creation timestamp.
- **FR-011**: The import command MUST skip rows where the `url` field is absent or blank, treating them as malformed.
- **FR-012**: The import command MUST skip rows where `created_at` is present but cannot be parsed as a valid date/time value, treating them as malformed.
- **FR-013**: Rows with extra/unknown columns MUST be accepted; the extra columns MUST be ignored.
- **FR-014**: After import, the command MUST display a summary showing the count of successfully imported rows and the count of skipped rows.
- **FR-015**: If every row in the import file is malformed (zero successful imports), the command MUST exit with a non-zero status code.
- **FR-016**: Both import and export commands MUST report a clear error message when the file path is inaccessible or does not exist.

### Key Entities

- **CSV Record**: A single row in a CSV file representing one bookmark. Fields: `url` (required), `title` (optional), `tags` (optional, semicolon-separated), `created_at` (optional, ISO 8601 datetime).
- **Import Result**: The outcome of a completed import operation. Tracks total rows processed, count of successfully imported bookmarks, count of skipped rows, and reasons for each skipped row.

## Assumptions

- The CSV format follows standard RFC 4180 conventions: fields may be quoted when they contain commas, quotes, or newlines; the default field delimiter is a comma.
- `created_at` values in CSV files are expected in ISO 8601 format (e.g., `2025-01-15T10:30:00`). Other common date formats may be supported as a best-effort extension.
- Duplicate URL handling is out of scope: if a URL already exists in the store, the import row is still added as a new entry.
- Export always outputs all bookmarks; filtering by tag or date range is out of scope for this feature.
- The `updated_at` field is not included in the CSV; it is set to the current time on import.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can export their entire bookmark library to a CSV file with a single command in under 2 seconds for libraries up to 10,000 bookmarks.
- **SC-002**: Users can import a CSV file containing up to 10,000 rows in under 5 seconds, with all valid rows present in the store afterward.
- **SC-003**: A CSV file exported and then re-imported produces an identical set of bookmarks (same URLs, titles, tags, and creation timestamps) — round-trip fidelity is 100% for well-formed data.
- **SC-004**: When a CSV file contains malformed rows, 100% of valid rows are imported successfully; no valid data is lost due to the presence of invalid rows.
- **SC-005**: After every import, the user receives a clear summary that accounts for all rows in the file (imported + skipped = total data rows).
