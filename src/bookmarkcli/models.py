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


class _MISSING_TYPE:
    def __repr__(self) -> str:
        return "MISSING"


MISSING = _MISSING_TYPE()


class BookmarkNotFoundError(Exception):
    """Raised when a bookmark ID does not exist."""


class BookmarkValidationError(Exception):
    """Raised when bookmark input data is invalid."""
