from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Bookmark:
    id: int | None
    url: str
    created_at: datetime
    updated_at: datetime
    title: str | None = None
    tags: list[str] = field(default_factory=list)


@dataclass
class SkippedRow:
    row_number: int
    reason: str


@dataclass
class ImportResult:
    imported: int
    skipped: int
    skipped_rows: list[SkippedRow] = field(default_factory=list)


class _MISSING_TYPE:
    def __repr__(self) -> str:
        return "MISSING"


MISSING = _MISSING_TYPE()


class BookmarkNotFoundError(Exception):
    """Raised when a bookmark ID does not exist."""


class BookmarkValidationError(Exception):
    """Raised when bookmark input data is invalid."""


class TagNotFoundError(Exception):
    """Raised when attempting to remove a tag not present on a bookmark."""


class TagValidationError(Exception):
    """Raised when a tag is empty or whitespace after normalization."""


def normalize_tag(tag: str) -> str:
    """Return tag stripped of surrounding whitespace and converted to lowercase."""
    return tag.strip().lower()


class DuplicateBookmarkError(Exception):
    """Raised when attempting to add a URL that already exists."""
