# Feature Specification: Tag Management

**Feature Branch**: `004-tag-management`  
**Created**: 2026-03-07  
**Status**: Draft  
**Input**: User description: "bookmark tag <id> --add <tag> and bookmark tag <id> --remove <tag> commands. bookmark tags to list all tags with counts. Tag normalization (lowercase, trim)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Add a Tag to a Bookmark (Priority: P1)

A user labels an existing bookmark with a classification tag. They run `bookmark tag <id> --add <tag>`, providing the bookmark's ID and the desired tag text. The tag is immediately stored with the bookmark and appears in subsequent tag listings.

**Why this priority**: Adding tags is the entry point for the entire tagging system. Without it, no tags exist to remove or list, and the feature delivers no value.

**Independent Test**: Can be fully tested by adding a bookmark, running `bookmark tag <id> --add python`, then retrieving the bookmark and confirming "python" appears in its tag list.

**Acceptance Scenarios**:

1. **Given** a bookmark with ID 5 exists and has no tags, **When** the user runs `bookmark tag 5 --add Python`, **Then** the tag "python" (normalized) is stored on the bookmark and a confirmation message is shown.
2. **Given** a bookmark with ID 5 already has the tag "python", **When** the user runs `bookmark tag 5 --add python`, **Then** the operation completes without error and the bookmark still has exactly one "python" tag (no duplicate).
3. **Given** a bookmark with ID 5 already has the tag "python", **When** the user runs `bookmark tag 5 --add  Python  ` (with surrounding spaces), **Then** the tag is normalized to "python" and the bookmark still has exactly one "python" tag.
4. **Given** no bookmark with ID 99 exists, **When** the user runs `bookmark tag 99 --add python`, **Then** a clear error is shown indicating the bookmark was not found.

---

### User Story 2 - Remove a Tag from a Bookmark (Priority: P2)

A user removes a previously applied tag from a bookmark. They run `bookmark tag <id> --remove <tag>`, providing the bookmark's ID and the tag to remove. The tag is immediately disassociated from that bookmark.

**Why this priority**: Tag removal completes the tag lifecycle, allowing users to correct mislabeled bookmarks and maintain a clean tag set.

**Independent Test**: Can be fully tested by adding a bookmark with a tag, running `bookmark tag <id> --remove <tag>`, then retrieving the bookmark and confirming the tag no longer appears.

**Acceptance Scenarios**:

1. **Given** a bookmark with ID 5 has tags ["python", "web"], **When** the user runs `bookmark tag 5 --remove python`, **Then** only "web" remains on the bookmark and a confirmation message is shown.
2. **Given** a bookmark with ID 5 has the tag "python", **When** the user runs `bookmark tag 5 --remove  Python  ` (with surrounding spaces and different case), **Then** the tag is normalized to "python" and successfully removed.
3. **Given** a bookmark with ID 5 does not have the tag "java", **When** the user runs `bookmark tag 5 --remove java`, **Then** a clear message indicates the tag was not found on that bookmark.
4. **Given** no bookmark with ID 99 exists, **When** the user runs `bookmark tag 99 --remove python`, **Then** a clear error is shown indicating the bookmark was not found.

---

### User Story 3 - List All Tags with Counts (Priority: P3)

A user wants to see all tags currently in use across their entire bookmark collection, along with how many bookmarks each tag is applied to. They run `bookmark tags` and receive a sorted list of tag names paired with their bookmark counts.

**Why this priority**: The listing command gives users visibility into their tag vocabulary, helping them reuse existing tags consistently. It depends on tags existing (stories 1 and 2) but delivers standalone value for discovery.

**Independent Test**: Can be fully tested by adding several bookmarks with overlapping tags, running `bookmark tags`, and confirming the output shows each unique tag and its correct count in alphabetical order.

**Acceptance Scenarios**:

1. **Given** three bookmarks: one tagged "python", one tagged "python" and "web", one tagged "web", **When** the user runs `bookmark tags`, **Then** the output shows "python  2" and "web  2" (or equivalent formatted output) in alphabetical order.
2. **Given** no bookmarks have any tags, **When** the user runs `bookmark tags`, **Then** the output indicates that no tags are in use (e.g., "No tags found.").
3. **Given** tags were added and then some were removed so only "web" remains in use once, **When** the user runs `bookmark tags`, **Then** only "web  1" is shown; removed tags no longer appear.

---

### Edge Cases

- What happens when a tag consists entirely of whitespace (e.g., `--add "   "`)? (Rejected with a clear validation error; no tag is stored.)
- What happens when a tag is an empty string (e.g., `--add ""`)? (Rejected with a clear validation error.)
- What happens when `bookmark tag <id> --add <tag>` and `--remove <tag>` are both provided in the same command? (Rejected; only one action flag may be used at a time.)
- What happens when a bookmark has all its tags removed and `bookmark tags` is run? (That bookmark no longer contributes counts; if no other bookmarks have tags, the output shows "No tags found.")
- What happens with tags that use mixed characters (numbers, hyphens, underscores)? (Allowed; normalization applies only to case and surrounding whitespace.)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The CLI MUST provide a `bookmark tag <id> --add <tag>` command that adds a tag to the bookmark identified by `<id>`.
- **FR-002**: The CLI MUST provide a `bookmark tag <id> --remove <tag>` command that removes a tag from the bookmark identified by `<id>`.
- **FR-003**: The CLI MUST provide a `bookmark tags` command that lists every distinct tag currently applied to at least one bookmark, together with the count of bookmarks carrying that tag.
- **FR-004**: The CLI MUST normalize all tag input by converting to lowercase and trimming leading and trailing whitespace before storing, removing, or querying.
- **FR-005**: The CLI MUST reject tag values that are empty or consist entirely of whitespace, returning a clear validation error.
- **FR-006**: When adding a tag that is already present on the bookmark, the operation MUST be idempotent: the tag is not duplicated, and the command completes without error.
- **FR-007**: When removing a tag that is not present on the bookmark, the CLI MUST display a clear message indicating the tag was not found on that bookmark.
- **FR-008**: When `bookmark tag <id>` is invoked against a non-existent bookmark ID, the CLI MUST display a clear error indicating the bookmark was not found.
- **FR-009**: The `bookmark tags` output MUST list tags in ascending alphabetical order.
- **FR-010**: The `bookmark tags` command MUST display a user-friendly message when no tags are in use across the entire bookmark collection.
- **FR-011**: Providing both `--add` and `--remove` in the same `bookmark tag` command invocation MUST be rejected with a clear usage error.

### Key Entities

- **Tag**: A normalized classification label (lowercase, trimmed) associated with one or more bookmarks. A tag has no independent identity outside its association with bookmarks; it ceases to exist in listings when no bookmark carries it.
- **Bookmark**: An existing entity (established in S02) extended with mutable tag membership. A bookmark may have zero or more tags; tags on a bookmark are unique (no duplicates).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can add a tag to any existing bookmark with a single command; the tag appears on the bookmark in subsequent retrievals.
- **SC-002**: Users can remove a tag from a bookmark with a single command; the tag no longer appears on the bookmark in subsequent retrievals.
- **SC-003**: `bookmark tags` accurately reflects the current tag-to-bookmark counts immediately after any add or remove operation, with zero stale entries.
- **SC-004**: Tags entered with different capitalizations or surrounding whitespace (e.g., "Python", "PYTHON", "  python  ") are stored and counted as the same normalized tag "python" in 100% of tested cases.
- **SC-005**: All add, remove, and list operations complete and return output in under one second for a bookmark collection of up to 10,000 records.
- **SC-006**: All functional requirements have at least one automated test, and all tests pass with zero failures.

## Assumptions

- The tag storage mechanism is an extension of the existing Bookmark record (as established in S02); tags remain a list of strings on each bookmark.
- Tag uniqueness per bookmark is enforced at the application level: no bookmark may carry the same normalized tag more than once.
- There is no maximum number of tags per bookmark unless a future constraint is introduced.
- Tag text may contain letters, digits, hyphens, and underscores; normalization is limited to case conversion and whitespace trimming. No further character validation is required for this feature.
- The `bookmark tags` count represents the number of distinct bookmarks carrying a tag, not the total number of times it was added.
- Deleting a bookmark (covered in S02/S03) removes all its tags from the effective tag pool automatically; no separate cleanup step is required.
