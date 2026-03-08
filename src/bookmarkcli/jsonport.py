import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from bookmarkcli.models import Bookmark
from bookmarkcli.store import BookmarkStore


@dataclass
class ImportResult:
    added: int = 0
    skipped: int = 0
    updated: int = 0
    invalid: int = 0


def bookmarks_to_json(bookmarks: list[Bookmark], indent: int = 2) -> str:
    if not bookmarks:
        return '{"bookmarks": []}\n'

    payload = {
        "bookmarks": [
            {
                "url": bookmark.url,
                "title": bookmark.title,
                "tags": bookmark.tags,
                "created_at": bookmark.created_at.isoformat(),
                "updated_at": bookmark.updated_at.isoformat(),
            }
            for bookmark in bookmarks
        ]
    }
    return json.dumps(payload, indent=indent) + "\n"


def import_from_json(
    json_str: str, store: BookmarkStore, on_duplicate: str = "skip"
) -> ImportResult:
    if on_duplicate not in {"skip", "update"}:
        raise ValueError("on_duplicate must be 'skip' or 'update'")

    document = json.loads(json_str)
    bookmarks_value = document.get("bookmarks") if isinstance(document, dict) else None
    if not isinstance(bookmarks_value, list):
        raise ValueError("document must contain a bookmarks list")

    result = ImportResult()
    known_by_url = {bookmark.url: bookmark for bookmark in store.list_all()}
    seen_this_run: set[str] = set()

    for index, raw_entry in enumerate(bookmarks_value, start=1):
        entry = raw_entry if isinstance(raw_entry, dict) else {}
        url_value = entry.get("url")
        url = url_value.strip() if isinstance(url_value, str) else ""
        if not url:
            print(f"Warning: skipping entry {index}: missing url", file=sys.stderr)
            result.invalid += 1
            continue

        title = _coerce_title(entry.get("title"))
        tags = _coerce_tags(entry.get("tags"))
        is_duplicate = url in known_by_url or url in seen_this_run
        if is_duplicate:
            if on_duplicate == "update":
                existing = known_by_url.get(url)
                if existing is None or existing.id is None:
                    raise RuntimeError(f"cannot update duplicate with unknown id: {url}")
                updated = store.update(existing.id, title=title, tags=tags)
                known_by_url[url] = updated
                result.updated += 1
            else:
                result.skipped += 1
            seen_this_run.add(url)
            continue

        created = _create_bookmark_from_entry(store, url=url, title=title, tags=tags, entry=entry)
        known_by_url[url] = created
        seen_this_run.add(url)
        result.added += 1

    return result


def _coerce_title(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _coerce_tags(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(tag) for tag in value]


def _parse_iso8601(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _create_bookmark_from_entry(
    store: BookmarkStore,
    url: str,
    title: str | None,
    tags: list[str],
    entry: dict[str, Any],
) -> Bookmark:
    if "created_at" not in entry and "updated_at" not in entry:
        return store.create(url=url, title=title, tags=tags)

    now = datetime.now(tz=timezone.utc)
    created_at = _parse_iso8601(entry.get("created_at")) or now
    updated_at = _parse_iso8601(entry.get("updated_at")) or now
    return _insert_with_timestamps(
        store, url=url, title=title, tags=tags, created_at=created_at, updated_at=updated_at
    )


def _insert_with_timestamps(
    store: BookmarkStore,
    url: str,
    title: str | None,
    tags: list[str],
    created_at: datetime,
    updated_at: datetime,
) -> Bookmark:
    con = store._con
    if con is None:
        raise RuntimeError("BookmarkStore is not initialized; call initialize() first")

    cursor = con.execute(
        """
        INSERT INTO bookmarks (url, title, tags, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            url,
            title,
            BookmarkStore._serialize_tags(tags),
            created_at.isoformat(),
            updated_at.isoformat(),
        ),
    )
    con.commit()
    bookmark_id = cursor.lastrowid
    if bookmark_id is None:
        raise RuntimeError("failed to persist imported bookmark")
    return store.get(int(bookmark_id))
