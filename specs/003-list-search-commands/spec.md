# Feature Specification: List & Search Commands

**Feature Branch**: `003-list-search-commands`  
**Created**: 2026-03-07  
**Status**: Draft  
**Input**: User description: "bookmark list [--tag] [--limit] [--sort] and bookmark search <query> commands. Full-text search across title and URL. Tabular output with rich or plain text."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - List All Bookmarks (Priority: P1)

A user wants to review their saved bookmarks. They run `bookmark list` and see all stored bookmarks displayed in a readable table with title, URL, tags, and date added. This is the foundational browse experience.

**Why this priority**: Listing bookmarks is the most fundamental read operation — without it, users cannot review what they have saved. All other listing features build on this base.

**Independent Test**: Run `bookmark list` against a store with several bookmarks; verify a formatted table is printed with one row per bookmark showing title, URL, tags, and date added.

**Acceptance Scenarios**:

1. **Given** the bookmark store contains saved bookmarks, **When** the user runs `bookmark list`, **Then** a table is printed with one row per bookmark showing ID, title, URL, tags, and date added.
2. **Given** the bookmark store is empty, **When** the user runs `bookmark list`, **Then** a message is shown indicating no bookmarks exist.
3. **Given** a terminal session (TTY), **When** the user runs `bookmark list`, **Then** output is rendered with rich formatting (borders, colors, column alignment).
4. **Given** output is piped to another command, **When** the user runs `bookmark list | grep ...`, **Then** output is plain text with no formatting artifacts.

---

### User Story 2 - Filter and Sort the List (Priority: P2)

A user has many bookmarks and wants to narrow down or reorder what they see. They use `--tag`, `--limit`, and `--sort` options to focus on relevant bookmarks without wading through everything.

**Why this priority**: Once users accumulate bookmarks, filtering and sorting become essential for usability. These options can be combined and tested independently of search.

**Independent Test**: Run `bookmark list --tag dev --limit 5 --sort title` against a populated store; verify only bookmarks tagged "dev" appear, at most 5 rows, alphabetically sorted by title.

**Acceptance Scenarios**:

1. **Given** bookmarks with various tags, **When** the user runs `bookmark list --tag <tag>`, **Then** only bookmarks carrying that tag are shown.
2. **Given** many bookmarks, **When** the user runs `bookmark list --limit 10`, **Then** at most 10 bookmarks are shown.
3. **Given** bookmarks with different titles, **When** the user runs `bookmark list --sort title`, **Then** results are ordered alphabetically by title.
4. **Given** bookmarks with different creation dates, **When** the user runs `bookmark list --sort date`, **Then** results are ordered newest-first.
5. **Given** `--tag` and `--limit` both supplied, **When** the user runs the command, **Then** filtering is applied first, then the row limit is applied to the filtered set.
6. **Given** a tag that no bookmark carries, **When** the user runs `bookmark list --tag <unknown>`, **Then** the output shows an empty-results message rather than an error.

---

### User Story 3 - Search Bookmarks by Keyword (Priority: P3)

A user remembers a keyword from a page title or URL but not the exact bookmark. They run `bookmark search <query>` and see all bookmarks whose title or URL contains the query string, ranked or ordered by relevance.

**Why this priority**: Search directly addresses the core retrieval problem; filtering by tag covers structured navigation, while search covers unstructured recall.

**Independent Test**: Run `bookmark search github` against a store containing bookmarks; verify only bookmarks whose title or URL includes "github" (case-insensitive) are returned in tabular format.

**Acceptance Scenarios**:

1. **Given** bookmarks exist, **When** the user runs `bookmark search <query>`, **Then** bookmarks whose title or URL contains the query string (case-insensitive) are shown in a table.
2. **Given** no bookmarks match the query, **When** the user runs `bookmark search <query>`, **Then** an empty-results message is shown.
3. **Given** a terminal session, **When** the user runs `bookmark search`, **Then** matching terms are visually highlighted in the rich output.
4. **Given** output is piped, **When** the user runs `bookmark search <query> | head`, **Then** plain text output contains no highlight escape codes.
5. **Given** a query with special characters (e.g., `.`, `?`, `/`), **When** the user runs `bookmark search https://`, **Then** the query is treated as a literal string and matching bookmarks are returned without error.

---

### Edge Cases

- What happens when `--limit 0` is supplied? The command should display an empty table (or treat 0 as "no limit" — see Assumptions).
- What happens when `--limit` receives a non-integer value? The command must print a clear error and exit with a non-zero code.
- What happens when `--sort` receives an unrecognised field name? The command must print the list of valid sort fields and exit with a non-zero code.
- What happens when the search query is an empty string? The command must require a non-empty query and print a usage hint.
- What happens when the bookmark store file is missing or unreadable? Both commands must print a clear error message and exit with a non-zero code.
- How does the system handle extremely long titles or URLs in table output? Long values are truncated with an ellipsis to preserve column alignment.

## Requirements *(mandatory)*

### Functional Requirements

**`bookmark list` command**

- **FR-001**: The system MUST provide a `bookmark list` command that displays all stored bookmarks.
- **FR-002**: `bookmark list` MUST accept an optional `--tag <tag>` option that restricts output to bookmarks carrying that exact tag.
- **FR-003**: `bookmark list` MUST accept an optional `--limit <n>` option that caps the number of rows shown; `n` must be a positive integer.
- **FR-004**: `bookmark list` MUST accept an optional `--sort <field>` option; supported fields are `date` (default, newest-first), `title` (ascending), and `url` (ascending).
- **FR-005**: When `--tag` and `--limit` are combined, filtering MUST be applied before the row cap.
- **FR-006**: When `--sort` and `--limit` are combined, sorting MUST be applied before the row cap.

**`bookmark search` command**

- **FR-007**: The system MUST provide a `bookmark search <query>` command that accepts a required positional query argument.
- **FR-008**: `bookmark search` MUST match bookmarks whose title or URL contains the query string using case-insensitive full-text substring matching.
- **FR-009**: Special characters in the query string MUST be treated as literals (no wildcard or regex expansion).

**Output formatting**

- **FR-010**: Both commands MUST auto-detect whether output is directed to a terminal; when a terminal is detected, rich (formatted, coloured) table output MUST be used; when output is piped or redirected, plain-text tabular output MUST be used.
- **FR-011**: Both commands MUST accept a `--plain` flag that forces plain-text output regardless of terminal detection.
- **FR-012**: Plain-text output MUST use consistent column separators suitable for downstream processing (e.g., piping to `grep`, `awk`, `cut`).
- **FR-013**: In rich output mode, `bookmark search` MUST visually highlight matching terms within the displayed title and URL columns.
- **FR-014**: Both commands MUST display columns: ID, Title, URL, Tags, Date Added.
- **FR-015**: Long values (title, URL) MUST be truncated with an ellipsis (`…`) to fit the column width and preserve table alignment.

**Empty and error states**

- **FR-016**: When no bookmarks match the active filters or search query, both commands MUST display a descriptive empty-state message rather than an error.
- **FR-017**: When an invalid option value is supplied (non-integer `--limit`, unrecognised `--sort` field, empty search query), the command MUST print a human-readable error and exit with a non-zero status code.

### Key Entities

- **Bookmark**: A saved web resource with an ID, title, URL, one or more optional tags, and a date-added timestamp.
- **Tag**: A label attached to a bookmark; used as a filter criterion; a bookmark may carry zero or more tags.
- **Search Query**: A free-text string supplied by the user; matched as a case-insensitive substring against bookmark titles and URLs.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can view all their bookmarks with a single command invocation, with no additional steps required.
- **SC-002**: `bookmark list` with any combination of `--tag`, `--limit`, and `--sort` returns correctly filtered and ordered results every time.
- **SC-003**: `bookmark search` returns matching results in under 1 second for a bookmark collection of up to 10,000 entries.
- **SC-004**: Plain-text output can be piped directly to standard Unix tools (`grep`, `awk`, `cut`, `sort`) without producing display artifacts or requiring pre-processing.
- **SC-005**: Rich output renders a properly aligned table in a standard terminal; no garbled characters appear in non-terminal environments.
- **SC-006**: All invalid inputs produce a human-readable error message and a non-zero exit code 100% of the time.

## Assumptions

- `--limit 0` is treated as an invalid input (FR-017 applies); users must supply a positive integer.
- The default sort order for `bookmark list` with no `--sort` flag is newest-first (`date` descending).
- Tag matching via `--tag` is exact and case-sensitive (e.g., `--tag Dev` does not match bookmarks tagged `dev`).
- Output column widths adapt to the terminal width; in plain-text mode a fixed minimum width is used.
- The `--plain` flag is available on both commands for scripting use; no separate `--rich` flag is needed since rich is already the default in a terminal.
- Bookmark data is retrieved from the storage layer established in S02 (data model & storage feature).

## Dependencies

- **S01** (Project Scaffold): CLI entry point, command registration, and dependency toolchain must exist.
- **S02** (Data Model & Storage): Bookmark persistence layer must be available for read operations.
