# Feature Specification: Add & Delete Bookmark Commands

**Feature Branch**: `001-add-delete-commands`  
**Created**: 2026-03-07  
**Status**: Draft  
**Input**: User description: "bookmark add <url> [--title] [--tags] and bookmark delete <id/url> commands. Validate URL format. Prevent duplicates. Confirm before delete."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Add a Bookmark by URL (Priority: P1)

A user wants to save a URL to their bookmark collection. They run `bookmark add <url>` and the URL is stored. Optionally they supply a human-readable title and one or more tags to organise it.

**Why this priority**: Adding bookmarks is the core write operation that all other commands depend on. Without it the tool has no data to work with.

**Independent Test**: Can be fully tested by running `bookmark add https://example.com` and verifying a new entry appears in the stored collection with the correct URL, a default title, and no tags.

**Acceptance Scenarios**:

1. **Given** the bookmark store is empty, **When** the user runs `bookmark add https://example.com`, **Then** a new bookmark entry is created with the given URL and a system-generated or page-derived title, no tags, and the command prints a confirmation message including the assigned ID.
2. **Given** the bookmark store is empty, **When** the user runs `bookmark add https://example.com --title "Example Site" --tags news,tech`, **Then** a new bookmark is created with that URL, title "Example Site", and tags `["news", "tech"]`, and a confirmation message is printed.
3. **Given** a bookmark with URL `https://example.com` already exists, **When** the user runs `bookmark add https://example.com`, **Then** no new bookmark is created and the command prints an error message indicating the URL already exists.
4. **Given** the user runs `bookmark add not-a-valid-url`, **Then** no bookmark is created and an error message indicates the URL format is invalid.

---

### User Story 2 - Delete a Bookmark by ID (Priority: P2)

A user wants to remove a bookmark they no longer need, referencing it by its numeric ID. The tool asks for confirmation before permanently deleting it.

**Why this priority**: Deletion by ID is the primary removal path; it directly pairs with the add command and completes basic CRUD for the collection.

**Independent Test**: Can be fully tested by adding a bookmark, noting its ID, running `bookmark delete <id>`, confirming the prompt, and verifying the entry no longer appears in the collection.

**Acceptance Scenarios**:

1. **Given** a bookmark with ID `42` exists, **When** the user runs `bookmark delete 42`, **Then** the tool displays the bookmark details (URL and title) and prompts "Delete this bookmark? [y/N]".
2. **Given** the confirmation prompt is shown, **When** the user enters `y` or `Y`, **Then** the bookmark is permanently removed and the tool prints a success message.
3. **Given** the confirmation prompt is shown, **When** the user enters `n`, `N`, or presses Enter (default No), **Then** no bookmark is deleted and the tool prints a cancellation message.
4. **Given** no bookmark with ID `99` exists, **When** the user runs `bookmark delete 99`, **Then** an error message is shown and no data is modified.

---

### User Story 3 - Delete a Bookmark by URL (Priority: P3)

A user wants to remove a bookmark by pasting its URL rather than looking up its ID. The same confirmation flow applies.

**Why this priority**: A convenience path that improves usability; the ID-based delete (P2) already covers correctness — URL-based delete reduces friction.

**Independent Test**: Can be fully tested by adding a bookmark, running `bookmark delete https://example.com`, confirming, and verifying removal.

**Acceptance Scenarios**:

1. **Given** a bookmark with URL `https://example.com` exists, **When** the user runs `bookmark delete https://example.com`, **Then** the tool displays the matching bookmark's details and prompts for confirmation.
2. **Given** the user confirms, **Then** the bookmark is removed and a success message is shown.
3. **Given** no bookmark matches `https://example.com`, **When** the user runs `bookmark delete https://example.com`, **Then** an error message reports that no such bookmark was found.

---

### Edge Cases

- What happens when `--tags` is given an empty string or only whitespace?
- How does the system handle a URL that is syntactically valid but unreachable (e.g., `https://`)?
- What if the same URL appears with different trailing slashes (`https://example.com` vs `https://example.com/`)? (Assumed to be treated as distinct unless normalisation is added later.)
- What if `--title` is an empty string?
- What happens when the user passes both an ID and a URL-looking string to `bookmark delete`? (The system distinguishes by format — numeric = ID, URL-shaped = URL.)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide an `add` sub-command that accepts a URL as a positional argument.
- **FR-002**: The `add` command MUST accept an optional `--title` flag to set a human-readable name for the bookmark.
- **FR-003**: The `add` command MUST accept an optional `--tags` flag that accepts a comma-separated list of tag names.
- **FR-004**: The `add` command MUST validate that the supplied URL conforms to a valid URL format (scheme + host at minimum) and reject invalid values with a clear error message.
- **FR-005**: The `add` command MUST prevent duplicate bookmarks: if a bookmark with the same URL already exists the command MUST refuse to add it and report the conflict.
- **FR-006**: On successful `add`, the system MUST display a confirmation message that includes the newly assigned bookmark ID.
- **FR-007**: The system MUST provide a `delete` sub-command that accepts either a numeric bookmark ID or a URL as its argument.
- **FR-008**: Before deleting, the `delete` command MUST display the matching bookmark's URL and title and prompt the user for explicit confirmation (defaulting to No/cancel).
- **FR-009**: The bookmark MUST only be removed from the store after the user explicitly confirms the deletion.
- **FR-010**: If the user declines confirmation, the system MUST leave the bookmark store unchanged and print a cancellation message.
- **FR-011**: If the supplied ID or URL does not match any existing bookmark, the `delete` command MUST report a not-found error without modifying the store.
- **FR-012**: Both commands MUST exit with a non-zero status code on any error condition (invalid input, not found, duplicate).

### Key Entities

- **Bookmark**: Represents a saved URL. Key attributes: unique numeric ID, URL string, title string, list of tag strings, creation timestamp.
- **Tag**: A label attached to a bookmark for categorisation. Represented as a plain string; multiple tags may be associated with one bookmark.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can add a bookmark with a single command in under 5 seconds of wall-clock time.
- **SC-002**: Attempting to add a duplicate URL always results in an error — the duplicate rate in the store is 0%.
- **SC-003**: Invalid URL inputs are rejected 100% of the time with a human-readable error message before any data is written.
- **SC-004**: A bookmark targeted for deletion is never removed without an explicit affirmative confirmation from the user.
- **SC-005**: All add and delete operations complete their primary path (success or user-facing error) within one command invocation — no additional steps required.
- **SC-006**: Both commands exit with a non-zero status code on every error condition, enabling reliable scripting and automation.

## Assumptions

- URL uniqueness is determined by exact string match after the user-supplied value is parsed; no automatic normalisation (e.g., lowercasing scheme/host or stripping trailing slashes) is performed in this iteration.
- When `--title` is omitted, the bookmark is stored without a title (empty string or null); automatic page-title fetching is out of scope for this feature.
- Tags supplied via `--tags` are split on commas; leading/trailing whitespace around each tag name is trimmed.
- The confirmation prompt reads on standard input; non-interactive (piped) usage is out of scope — the command is designed for interactive terminal use.
- The bookmark store from S01 (data model & storage layer) is the persistence mechanism; this feature adds the CLI surface on top of it.
