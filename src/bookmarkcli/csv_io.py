"""CSV import/export helpers for bookmark records.

This module provides two entry points:
- ``export_bookmarks(bookmarks, dest)`` to write bookmark rows as CSV.
- ``import_bookmarks(src, store)`` to read CSV rows and create bookmarks.
"""

import csv
from datetime import datetime, timezone
from typing import IO

from bookmarkcli.models import Bookmark, ImportResult, SkippedRow
from bookmarkcli.store import BookmarkStore


def export_bookmarks(bookmarks: list[Bookmark], dest: IO[str]) -> None:
    writer = csv.DictWriter(
        dest,
        fieldnames=["url", "title", "tags", "created_at"],
    )
    writer.writeheader()
    for bookmark in bookmarks:
        writer.writerow(
            {
                "url": bookmark.url,
                "title": bookmark.title or "",
                "tags": ";".join(bookmark.tags),
                "created_at": bookmark.created_at.isoformat(),
            }
        )


def import_bookmarks(src: IO[str], store: BookmarkStore) -> ImportResult:
    reader = csv.DictReader(src)
    if reader.fieldnames is None or "url" not in reader.fieldnames:
        raise ValueError("CSV file must have a header row with at least a 'url' column")

    imported = 0
    skipped_rows: list[SkippedRow] = []

    for row_number, row in enumerate(reader, start=1):
        url = (row.get("url") or "").strip()
        if not url:
            skipped_rows.append(SkippedRow(row_number=row_number, reason="url is missing or blank"))
            continue

        title_value = (row.get("title") or "").strip()
        title = title_value or None

        tags_value = row.get("tags") or ""
        tags = [tag.strip() for tag in tags_value.split(";") if tag.strip()]

        created_at_value = (row.get("created_at") or "").strip()
        if created_at_value:
            try:
                created_at = datetime.fromisoformat(created_at_value)
            except ValueError:
                skipped_rows.append(
                    SkippedRow(
                        row_number=row_number,
                        reason=f"created_at cannot be parsed: '{created_at_value}'",
                    )
                )
                continue
        else:
            created_at = datetime.now(tz=timezone.utc)

        store.create(url=url, title=title, tags=tags, created_at=created_at)
        imported += 1

    return ImportResult(
        imported=imported,
        skipped=len(skipped_rows),
        skipped_rows=skipped_rows,
    )
