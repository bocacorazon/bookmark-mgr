# Feature Specification: List & Search Commands

**Feature Branch**: `001-list-search`  
**Created**: 2026-03-08  
**Status**: Draft  
**Depends On**: S01 (Bookmark storage foundation)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - List All Bookmarks (Priority: P1)

A user wants to see all their saved bookmarks at a glance in a readable table. They run `bookmark list` and receive a formatted table showing each bookmark's ID, title, URL, tags, and creation date.

**Why this priority**: This is the fundamental retrieval feature. Without it, users have no way to review their saved bookmarks. Every other filter and search capability builds on top of it.

**Independent Test**: Can be fully tested by adding a few bookmarks and running `bookmark list`; delivers a complete list view with no additional features needed.

**Acceptance Scenarios**:

1. **Given** the bookmark store contains at least one bookmark, **When** the user runs `bookmark list`, **Then** the output displays a table with columns for ID, title, URL, tags, and creation date, one row per bookmark.
2. **Given** the bookmark store is empty, **When** the user runs `bookmark list`, **Then** the output shows an empty state message indicating no bookmarks are stored.
3. **Given** the terminal supports color and rich formatting, **When** the user runs `bookmark list`, **Then** the table is rendered with rich formatting (borders, colors, alignment).
4. **Given** the output is piped to another command or a file, **When** the user runs `bookmark list`, **Then** the output falls back to plain-text tabular format without color escape codes.

---

### User Story 2 - Filter Bookmarks by Tag (Priority: P2)

A user has many bookmarks tagged by topic and wants to see only those related to a specific topic. They run `bookmark list --tag python` and receive only the bookmarks carrying that tag.

**Why this priority**: Tags are the primary organizational mechanism for bookmarks; tag-based filtering turns a flat list into a useful categorized view.

**Independent Test**: Can be tested by adding bookmarks with different tags and verifying `bookmark list --tag <tag>` returns only matching bookmarks.

**Acceptance Scenarios**:

1. **Given** bookmarks exist with various tags, **When** the user runs `bookmark list --tag python`, **Then** only bookmarks whose tag list includes "python" are shown.
2. **Given** no bookmarks carry the specified tag, **When** the user runs `bookmark list --tag nonexistent`, **Then** an empty state message is displayed (no error).
3. **Given** a bookmark has multiple tags including the requested one, **When** filtering by that tag, **Then** the bookmark is included in the results.

---

### User Story 3 - Limit and Sort the List (Priority: P3)

A user wants a quick view of their most recently added bookmarks without scrolling through everything. They run `bookmark list --limit 10 --sort newest` to get the 10 most recently created bookmarks.

**Why this priority**: Limit and sort control output volume and ordering, improving usability for large collections, but the list is useful without them.

**Independent Test**: Can be tested by adding many bookmarks then verifying `bookmark list --limit 5` returns exactly 5 rows and `--sort oldest` returns them in ascending creation order.

**Acceptance Scenarios**:

1. **Given** more bookmarks exist than the limit value, **When** the user runs `bookmark list --limit 5`, **Then** exactly 5 bookmarks are shown.
2. **Given** fewer bookmarks exist than the limit value, **When** the user runs `bookmark list --limit 100`, **Then** all bookmarks are shown (no error).
3. **Given** the user runs `bookmark list --sort newest`, **Then** bookmarks are ordered with the most recently created first.
4. **Given** the user runs `bookmark list --sort oldest`, **Then** bookmarks are ordered with the earliest created first.
5. **Given** no `--sort` flag is provided, **When** the user runs `bookmark list`, **Then** bookmarks are returned in a consistent default order (newest first).

---

### User Story 4 - Full-Text Search (Priority: P2)

A user remembers a keyword from a bookmark's title or URL but not the exact address. They run `bookmark search python` and receive all bookmarks whose title or URL contains "python".

**Why this priority**: Search is the primary discovery mechanism for users who cannot recall exact titles or URLs; it directly addresses the core value of a bookmark manager.

**Independent Test**: Can be tested end-to-end by adding bookmarks with known titles/URLs and verifying `bookmark search <query>` returns the expected subset.

**Acceptance Scenarios**:

1. **Given** bookmarks exist with titles or URLs containing the query term, **When** the user runs `bookmark search python`, **Then** all matching bookmarks are shown in a table.
2. **Given** the query matches the title of some bookmarks and the URL of others, **When** the user searches, **Then** results from both matches are combined and returned.
3. **Given** no bookmarks match the query, **When** the user runs `bookmark search xyz123`, **Then** an empty state message is displayed (no error).
4. **Given** the search query is case-insensitive, **When** the user runs `bookmark search Python`, **Then** bookmarks containing "python", "Python", or "PYTHON" are all matched.
5. **Given** the output is piped, **When** the user runs `bookmark search <query>`, **Then** plain-text tabular output is produced without formatting codes.

---

### Edge Cases

- What happens when `--limit 0` is provided? The system returns an empty result or treats it as no limit (documented behavior; assume 0 means "show none" — return empty with a note).
- What happens when `--limit` is a negative number or non-integer? The system rejects the value with a clear error message.
- What happens when the search query is an empty string? The system returns an error or treats it equivalently to listing all (assume: error with usage hint).
- What happens when the bookmark store file does not exist yet? The system shows an empty state message rather than an error.
- What happens when `--sort` receives an unrecognized value? The system rejects it with a clear error listing valid options.
- How does tabular output handle very long URLs or titles? Values are truncated with an ellipsis to preserve readability on standard terminal widths.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The CLI MUST provide a `bookmark list` command that displays all stored bookmarks in tabular format.
- **FR-002**: The `bookmark list` command MUST support a `--tag <tag>` option that filters results to only bookmarks carrying that tag.
- **FR-003**: The `bookmark list` command MUST support a `--limit <n>` option that restricts the number of rows returned to at most N.
- **FR-004**: The `bookmark list` command MUST support a `--sort <order>` option accepting `newest` and `oldest` as values, ordering results by creation date accordingly.
- **FR-005**: When no `--sort` option is given, results MUST default to newest-first ordering.
- **FR-006**: The CLI MUST provide a `bookmark search <query>` command that performs case-insensitive full-text search across bookmark titles and URLs.
- **FR-007**: Search results MUST include bookmarks where the query term appears in the title, the URL, or both.
- **FR-008**: Both `bookmark list` and `bookmark search` MUST render output as a rich formatted table when the terminal supports it, and as plain-text tabular output when output is piped or the terminal does not support formatting.
- **FR-009**: The tabular output MUST include columns for: ID, Title, URL, Tags, and Creation Date.
- **FR-010**: When results are empty (no bookmarks match), both commands MUST display a user-friendly empty state message instead of an error.
- **FR-011**: Invalid values for `--limit` (non-positive integers, non-numeric) MUST produce a descriptive error message.
- **FR-012**: An unrecognized value for `--sort` MUST produce a descriptive error message listing the valid options.
- **FR-013**: A missing or empty query argument to `bookmark search` MUST produce a usage error with a helpful hint.

### Key Entities

- **Bookmark**: The core data record with fields: ID, URL, title (optional), tags (list), creation date, and last-updated date. Queried, filtered, and displayed by these commands.
- **Search Query**: A user-supplied text string matched against bookmark titles and URLs in a case-insensitive, substring manner.
- **Output Format**: The presentation mode (rich/plain) determined automatically by whether the output destination is an interactive terminal.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can view their full bookmark list with a single command in under 1 second for collections up to 10,000 bookmarks.
- **SC-002**: Users can filter by tag and see matching results in under 1 second for collections up to 10,000 bookmarks.
- **SC-003**: Users can find a specific bookmark by a keyword in its title or URL using a single `bookmark search` command in under 1 second for collections up to 10,000 bookmarks.
- **SC-004**: Output automatically adapts between rich and plain-text modes with no extra flags required; 100% of piped output is free of formatting codes.
- **SC-005**: All invalid inputs (bad `--limit`, unknown `--sort`, empty search query) produce human-readable error messages that guide the user toward correct usage.
- **SC-006**: The feature is fully usable as a standalone capability without requiring any other new commands beyond S01 storage.

## Assumptions

- The bookmark data model from S01 provides at minimum: ID, URL, title, tags, and creation date — all available for display and filtering.
- "Full-text search" means substring matching across title and URL fields; advanced ranking or stemming is out of scope.
- Tags are matched exactly (e.g., `--tag py` does not match a bookmark tagged `python`).
- Rich output is rendered when stdout is connected to an interactive terminal; plain text is used otherwise (piped, redirected).
- The default sort order (newest first) is by creation date descending.
- Long values (titles, URLs) in table cells are truncated to fit terminal width without wrapping.
