# Feature Specification: Data Model & Storage

**Feature Branch**: `002-data-model-storage`  
**Created**: 2026-03-07  
**Status**: Draft  
**Input**: User description: "SQLite-backed storage layer: Bookmark model (url, title, tags, created_at, updated_at), BookmarkStore class with CRUD operations, migration/init logic, full test coverage."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Save a New Bookmark (Priority: P1)

A user saves a new bookmark by providing a URL. An optional title and zero or more tags may accompany the URL. The bookmark is immediately available for future retrieval.

**Why this priority**: Saving bookmarks is the foundational operation; every other capability depends on records existing in storage.

**Independent Test**: Can be fully tested by saving a bookmark and confirming it can be retrieved by its assigned ID, demonstrating basic end-to-end persistence.

**Acceptance Scenarios**:

1. **Given** an empty bookmark store, **When** a bookmark is saved with a valid URL, **Then** a new record is created and a unique ID is returned.
2. **Given** an existing bookmark store, **When** a bookmark is saved with a URL, title, and multiple tags, **Then** all provided fields are stored and retrievable.
3. **Given** a bookmark store, **When** a bookmark is saved without a URL, **Then** the operation is rejected with a clear error and no record is created.

---

### User Story 2 - Retrieve Saved Bookmarks (Priority: P2)

A user fetches one or all bookmarks from storage. Retrieving a single bookmark uses its unique ID; listing retrieves all records.

**Why this priority**: Retrieval is required for every downstream feature (search, display, export) and validates that saved data is accessible.

**Independent Test**: Can be fully tested by saving several bookmarks and confirming that fetching by ID returns the correct record and listing returns all records.

**Acceptance Scenarios**:

1. **Given** a bookmark with a known ID exists, **When** that ID is looked up, **Then** the exact bookmark record is returned with all its fields intact.
2. **Given** three bookmarks have been saved, **When** all bookmarks are listed, **Then** exactly three records are returned.
3. **Given** no bookmark exists for a requested ID, **When** that ID is looked up, **Then** the operation signals that the record was not found.

---

### User Story 3 - Update an Existing Bookmark (Priority: P3)

A user modifies the title or tags of an already-saved bookmark. The record reflects the new values immediately, and the last-modified timestamp is refreshed automatically.

**Why this priority**: Editing allows users to correct or enrich existing data without deleting and recreating records.

**Independent Test**: Can be fully tested by saving a bookmark, updating its title and tags, then retrieving it and asserting the updated values and a newer modification timestamp.

**Acceptance Scenarios**:

1. **Given** a bookmark exists, **When** its title is changed, **Then** the stored record reflects the new title and the modification timestamp is newer than the creation timestamp.
2. **Given** a bookmark exists with no tags, **When** tags are added via an update, **Then** the stored record includes the new tags.
3. **Given** no bookmark exists for a requested ID, **When** an update is attempted, **Then** the operation signals that the record was not found.

---

### User Story 4 - Delete a Bookmark (Priority: P4)

A user permanently removes a bookmark from storage by its unique ID. Subsequent retrievals of that ID confirm the record no longer exists.

**Why this priority**: Deletion completes the full data lifecycle and prevents stale data from accumulating.

**Independent Test**: Can be fully tested by saving a bookmark, deleting it, then confirming that attempting to retrieve it returns "not found".

**Acceptance Scenarios**:

1. **Given** a bookmark exists, **When** it is deleted, **Then** the operation succeeds and the record can no longer be retrieved.
2. **Given** three bookmarks exist, **When** one is deleted, **Then** listing returns the remaining two records.
3. **Given** no bookmark exists for a requested ID, **When** deletion is attempted, **Then** the operation signals that the record was not found.

---

### User Story 5 - Automatic Storage Initialization (Priority: P1)

On first launch, the storage layer detects that no persistent store exists and creates the necessary schema automatically, without any user action. On subsequent launches it uses the existing store unchanged.

**Why this priority**: Seamless initialization is required before any other operation can work; it must succeed silently to avoid blocking the user.

**Independent Test**: Can be fully tested by starting the application against a directory that has no existing store and confirming that a save operation succeeds immediately without manual setup.

**Acceptance Scenarios**:

1. **Given** no data store exists, **When** the storage layer is initialized, **Then** the store is created and ready for use without errors.
2. **Given** a store already exists with saved bookmarks, **When** the application is restarted and the storage layer is initialized again, **Then** previously saved bookmarks remain accessible and no data is lost.
3. **Given** the store schema is at an older version, **When** the storage layer is initialized, **Then** the schema is migrated to the current version without data loss.

---

### Edge Cases

- What happens when a bookmark is saved with a URL that has already been saved? (Duplicates are allowed; each save produces a distinct record.)
- How does the system handle an update where no fields are changed? (The operation succeeds; the modification timestamp is still refreshed.)
- What happens when tags is an empty list or omitted on creation or update? (Treated as no tags; existing tags are cleared on update if explicitly set to empty.)
- How does the system behave if the storage file is deleted while the application is running? (Out of scope for this feature; single-session use is assumed.)
- What happens when a very large number of bookmarks are stored? (Retrieval of all records must remain functional; performance degradation is not expected at typical usage volumes up to 10,000 records.)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The storage layer MUST persist bookmark records durably across application sessions.
- **FR-002**: The storage layer MUST initialize the data store and create the required schema automatically on first use, without manual user intervention.
- **FR-003**: The storage layer MUST apply schema migrations automatically when an existing store uses an older schema version.
- **FR-004**: The storage layer MUST support creating a new Bookmark record given a URL; title and tags are optional.
- **FR-005**: The storage layer MUST reject bookmark creation when the URL field is absent or empty, returning a clear error.
- **FR-006**: The storage layer MUST assign each bookmark a unique identifier at creation time.
- **FR-007**: The storage layer MUST automatically record the creation timestamp when a bookmark is first saved.
- **FR-008**: The storage layer MUST automatically update the modification timestamp whenever a bookmark record is changed.
- **FR-009**: The storage layer MUST support retrieving a single Bookmark record by its unique identifier.
- **FR-010**: The storage layer MUST support retrieving all Bookmark records.
- **FR-011**: The storage layer MUST support updating the title and/or tags of an existing Bookmark by its unique identifier.
- **FR-012**: The storage layer MUST support deleting an existing Bookmark by its unique identifier.
- **FR-013**: The storage layer MUST return a clear, distinguishable error when a requested record does not exist (get, update, or delete by ID).
- **FR-014**: The test suite MUST cover all CRUD operations, schema initialization, migration, and the edge cases identified in this specification.

### Key Entities

- **Bookmark**: Represents a saved reference to a web resource.
  - *ID*: system-assigned unique identifier; immutable after creation.
  - *URL*: the web address being bookmarked; required; non-empty.
  - *Title*: a human-readable label for the bookmark; optional.
  - *Tags*: an ordered or unordered collection of classification labels; optional; may be empty.
  - *created_at*: the moment the record was first stored; set automatically at creation.
  - *updated_at*: the moment the record was last modified; updated automatically on any change.

- **BookmarkStore**: The data access component that owns all persistence operations for Bookmark records.
  - Manages the lifecycle of the data store (initialization, migration, connection).
  - Exposes create, read (single and all), update, and delete operations for Bookmark records.
  - Encapsulates all storage details so that calling code has no direct dependency on the underlying store technology.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All CRUD operations (create, read single, read all, update, delete) complete without errors when given valid input.
- **SC-002**: Bookmark data is retrievable after the application is stopped and restarted, confirming durable persistence.
- **SC-003**: Storage initialization completes in under one second on first launch with no existing data store.
- **SC-004**: Listing all bookmarks from a store containing 10,000 records completes in under two seconds.
- **SC-005**: All tests in the test suite pass with zero failures, and every functional requirement has at least one corresponding test.
- **SC-006**: Operations on non-existent record IDs return a distinguishable error in 100% of tested cases.
- **SC-007**: Schema migration from a prior version to the current version completes without data loss, verified by tests that create records under the old schema and confirm their presence after migration.

## Assumptions

- Single-user, single-process access is assumed; concurrent writes are out of scope for this feature.
- SQLite is the designated storage backend (specified explicitly in the feature description); this is a hard constraint, not an implementation choice.
- Tags are stored as a simple string with a defined delimiter (e.g., comma-separated); advanced tag querying is out of scope for this feature.
- URL uniqueness is not enforced at the storage layer; the same URL may appear in multiple bookmark records.
- The file path for the data store is determined by the application layer; the storage component accepts a configurable path.
- Auto-increment integers serve as bookmark IDs for simplicity; the format is considered an implementation detail that does not affect external behavior.
- "Full test coverage" means all public operations and documented edge cases have explicit test assertions; 100% line/branch coverage is a desired side effect, not a hard requirement.
