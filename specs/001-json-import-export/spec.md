# Feature Specification: JSON Import/Export

**Feature Branch**: `001-json-import-export`  
**Created**: 2026-03-07  
**Status**: Draft  
**Input**: User description: "bookmark export --format json [--file out.json] and bookmark import --format json <file>. Round-trip fidelity: export then import should produce identical data. Handle duplicates on import (skip or update)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export Bookmarks to a JSON File (Priority: P1)

A user wants to back up their bookmarks or transfer them to another machine. They run the export command with a file path, and a JSON file is created containing all their bookmarks with all data fields preserved.

**Why this priority**: Export is the producer side of the round-trip; it must exist before import can be tested. Saving to a file is the primary use case for backup and portability.

**Independent Test**: Can be fully tested by populating a store with a few bookmarks, running the export command with a file path, and confirming the resulting file contains valid JSON with every bookmark's URL, title, and tags present.

**Acceptance Scenarios**:

1. **Given** a bookmark store with three saved bookmarks, **When** the user runs `bookmark export --format json --file out.json`, **Then** a file named `out.json` is created containing all three bookmarks in valid JSON format.
2. **Given** a bookmark store with bookmarks that have tags, **When** the user exports to a file, **Then** the output file includes the tags for each bookmark.
3. **Given** an empty bookmark store, **When** the user exports to a file, **Then** a valid JSON file is created containing an empty list of bookmarks.

---

### User Story 2 - Export Bookmarks to Standard Output (Priority: P2)

A user wants to inspect their bookmarks as JSON or pipe the output to another tool. When no output file is specified, the JSON is printed directly to the terminal.

**Why this priority**: Stdout output supports scripting and ad-hoc inspection without creating temporary files, making the tool more composable.

**Independent Test**: Can be fully tested by running the export command without a `--file` flag and confirming that valid JSON is written to stdout.

**Acceptance Scenarios**:

1. **Given** a bookmark store with bookmarks, **When** the user runs `bookmark export --format json` without a `--file` option, **Then** valid JSON is printed to standard output.
2. **Given** an empty bookmark store, **When** the user exports without a `--file` option, **Then** a valid empty JSON array representation is printed to standard output.

---

### User Story 3 - Import Bookmarks from a JSON File (Priority: P1)

A user has a JSON file (produced by a previous export or a compatible tool) and wants to load its bookmarks into the store. All bookmarks in the file are added, and a summary of how many were imported is shown.

**Why this priority**: Import is the other half of the round-trip and the primary mechanism for restoring or migrating bookmarks.

**Independent Test**: Can be fully tested by exporting bookmarks to a file, clearing the store, importing the file, and confirming that the store contains the same bookmarks.

**Acceptance Scenarios**:

1. **Given** an empty bookmark store and a valid JSON export file with three bookmarks, **When** the user runs `bookmark import --format json <file>`, **Then** all three bookmarks are added to the store and a success summary is shown.
2. **Given** a JSON file with bookmarks including titles and tags, **When** the user imports the file, **Then** each imported bookmark retains its title and tags exactly.
3. **Given** a JSON file that does not exist at the given path, **When** the user runs the import command, **Then** an informative error message is shown and no data is changed.
4. **Given** a file containing invalid JSON, **When** the user runs the import command, **Then** an informative error message is shown and no data is changed.

---

### User Story 4 - Handle Duplicate Bookmarks on Import (Priority: P2)

A user imports a file that contains URLs already present in their store. They can control whether existing bookmarks are skipped (preserved) or updated (overwritten) using a flag.

**Why this priority**: Duplicate handling prevents accidental data loss or unwanted overwrites; the default safe behavior (skip) lets users confidently re-run imports.

**Independent Test**: Can be fully tested by importing a file with a URL already in the store, first without any flag (confirming the existing record is unchanged) and then with the update flag (confirming the existing record is overwritten).

**Acceptance Scenarios**:

1. **Given** a bookmark with URL "https://example.com" exists in the store and the import file contains the same URL with a different title, **When** the user imports without any duplicate flag, **Then** the existing bookmark is unchanged and the import summary reports it was skipped.
2. **Given** a bookmark with URL "https://example.com" exists in the store and the import file contains the same URL with a different title, **When** the user imports with the `--on-duplicate update` flag, **Then** the existing bookmark's title (and tags) are replaced with the values from the file and the import summary reports it was updated.
3. **Given** an import file with five bookmarks where two URLs already exist in the store, **When** the user imports with the default behavior, **Then** three new bookmarks are added, two are skipped, and the summary reports both counts.

---

### User Story 5 - Full Round-Trip Fidelity (Priority: P2)

A user exports all their bookmarks to a JSON file and then imports that file into an empty store. After the import, the store is identical to the original: every bookmark with every field is fully recovered.

**Why this priority**: This validates the contract between export and import and is the key quality guarantee of the feature.

**Independent Test**: Can be fully tested by exporting a populated store to a file, clearing the store, importing the file, and asserting field-by-field equality for every bookmark.

**Acceptance Scenarios**:

1. **Given** a store with bookmarks having diverse data (long URLs, multi-word titles, multiple tags, timestamps), **When** the user exports to a file and then imports that file into an empty store, **Then** every bookmark in the restored store has the same URL, title, and tags as the original.
2. **Given** a bookmark with no title and no tags, **When** it is exported and then imported, **Then** the restored bookmark also has no title and no tags (nulls and empty collections round-trip correctly).

---

### Edge Cases

- What happens when the import file contains duplicate URLs within the file itself (not in the store)? The first occurrence is imported; subsequent duplicate entries in the same file follow the configured duplicate policy (skip or update the just-imported record).
- What happens when a bookmark in the import file is missing the required URL field? That entry is rejected with a warning, the valid entries continue to be processed, and the summary reports the number of invalid entries skipped.
- What happens when the `--file` path for export points to a directory or an unwritable location? The command fails with an informative error before any data is read.
- What happens when the export file already exists at the given path? The file is overwritten without prompting (standard CLI behavior; no data in the store is affected).
- What happens when the store is very large (thousands of bookmarks)? Export and import complete successfully; no hard limit is imposed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Users MUST be able to export all bookmarks to a JSON file by running `bookmark export --format json --file <path>`.
- **FR-002**: Users MUST be able to export all bookmarks to standard output by running `bookmark export --format json` (without `--file`).
- **FR-003**: Users MUST be able to import bookmarks from a JSON file by running `bookmark import --format json <file>`.
- **FR-004**: The exported JSON MUST include all bookmark fields: URL, title, tags, and timestamps (created and last modified).
- **FR-005**: Importing a valid export file into an empty store MUST restore all bookmark content (URL, title, tags) exactly, achieving full round-trip fidelity.
- **FR-006**: On import, when a URL in the file already exists in the store, the system MUST skip the duplicate by default and report the skip in the summary.
- **FR-007**: On import, users MUST be able to specify `--on-duplicate update` to replace an existing bookmark's title and tags with the values from the file.
- **FR-008**: The import command MUST display a summary after completion reporting the number of bookmarks added, skipped, and (if applicable) updated.
- **FR-009**: If the import file does not exist or is not readable, the command MUST display an informative error and exit without modifying any data.
- **FR-010**: If the import file contains invalid JSON, the command MUST display an informative error and exit without modifying any data.
- **FR-011**: If an entry in the import file is missing the required URL field, that entry MUST be skipped with a warning; all other valid entries MUST still be processed.
- **FR-012**: The export command MUST produce valid, well-formed JSON for any store state, including an empty store.

### Key Entities

- **Bookmark**: The core data record being transferred. Carries URL (required, unique identifier for duplicate detection), title (optional free-text label), tags (optional ordered collection of labels), creation timestamp, and last-modified timestamp.
- **Export File**: A JSON document representing a collection of bookmarks. Acts as the portable interchange artifact between export and import operations.
- **Import Summary**: A human-readable report produced at the end of an import operation. Reports counts of bookmarks added, skipped (duplicate), updated (duplicate with update flag), and invalid (missing required fields).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can export all bookmarks and have the resulting file importable into an empty store with 100% content fidelity (zero data loss for URL, title, and tags).
- **SC-002**: An import of a 1,000-bookmark JSON file completes in under 10 seconds on a standard workstation.
- **SC-003**: An export of a 1,000-bookmark store completes in under 5 seconds on a standard workstation.
- **SC-004**: After importing a file where 50% of entries are duplicates of existing bookmarks, the store contains exactly the expected records (no unintended duplicates, no unintended overwrites) and the summary counts match.
- **SC-005**: 100% of invalid import entries (missing URL, malformed) are reported in the summary without aborting processing of valid entries.
- **SC-006**: Every error condition (missing file, invalid JSON, bad path) produces an actionable error message that a user can act on without consulting documentation.

## Assumptions

- **Default duplicate policy is skip**: Skipping is the safer default to prevent accidental overwrites; users must explicitly opt in to update behavior.
- **Duplicate detection uses URL**: The URL is the natural unique identifier for bookmarks; two bookmarks with the same URL are considered duplicates regardless of title or tags.
- **Timestamps are included in export**: Export includes creation and last-modified timestamps so that a full round-trip preserves the complete record; on import, if timestamps are present in the file they are honored, otherwise the import time is used.
- **Export covers all bookmarks**: The initial version exports the entire store; filtering by tag or search term is out of scope for this feature.
- **File format version is implicit**: The JSON format does not require an explicit schema version field in the initial release; format evolution is out of scope.
- **The `--format` flag is required**: Even though only JSON is supported initially, the `--format json` flag is required on both commands to allow other formats to be added in the future without breaking the interface.
