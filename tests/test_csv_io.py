import csv
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

import pytest

from bookmarkcli.csv_io import export_bookmarks, import_bookmarks
from bookmarkcli.models import Bookmark, SkippedRow
from bookmarkcli.store import BookmarkStore


def test_export_bookmarks_writes_header_and_rows() -> None:
    now = datetime(2026, 3, 7, 12, 0, tzinfo=timezone.utc)
    bookmarks = [
        Bookmark(
            id=1,
            url="https://example.com",
            title="Example",
            tags=["python", "dev"],
            created_at=now,
            updated_at=now,
        ),
        Bookmark(
            id=2,
            url="https://example.org",
            title=None,
            tags=[],
            created_at=now,
            updated_at=now,
        ),
    ]
    dest = StringIO()

    export_bookmarks(bookmarks, dest)

    exported = dest.getvalue()
    reader = csv.DictReader(StringIO(exported))
    rows = list(reader)

    assert reader.fieldnames == ["url", "title", "tags", "created_at"]
    assert len(rows) == 2
    assert rows[0]["url"] == "https://example.com"
    assert rows[0]["title"] == "Example"
    assert rows[0]["tags"] == "python;dev"
    assert rows[0]["created_at"] == now.isoformat()
    assert rows[1]["url"] == "https://example.org"
    assert rows[1]["title"] == ""
    assert rows[1]["tags"] == ""
    assert rows[1]["created_at"] == now.isoformat()


def test_export_bookmarks_empty_list_writes_header_only() -> None:
    dest = StringIO()

    export_bookmarks([], dest)

    assert dest.getvalue().splitlines() == ["url,title,tags,created_at"]


@pytest.fixture
def store(tmp_path: Path) -> BookmarkStore:
    bookmark_store = BookmarkStore(db_path=tmp_path / "bookmarks.db")
    bookmark_store.initialize()
    return bookmark_store


def test_import_bookmarks_happy_path_creates_rows(store: BookmarkStore) -> None:
    src = StringIO(
        "\n".join(
            [
                "url,title,tags,created_at",
                "https://example.com,Example,python;dev,2025-01-15T10:30:00+00:00",
                "https://example.org,Other,tools,2025-01-16T11:45:00+00:00",
            ]
        )
    )

    result = import_bookmarks(src, store)
    rows = store.list_all()

    assert result.imported == 2
    assert result.skipped == 0
    assert result.skipped_rows == []
    assert len(rows) == 2
    assert rows[0].url == "https://example.com"
    assert rows[0].title == "Example"
    assert rows[0].tags == ["python", "dev"]
    assert rows[0].created_at == datetime.fromisoformat("2025-01-15T10:30:00+00:00")
    assert rows[1].url == "https://example.org"
    assert rows[1].tags == ["tools"]


def test_import_bookmarks_uses_current_time_when_created_at_missing_or_empty(
    store: BookmarkStore,
) -> None:
    before = datetime.now(tz=timezone.utc)
    src_missing_created_at = StringIO(
        "\n".join(
            [
                "url,title,tags",
                "https://example.net,Net,python;;dev",
                "https://example.edu,Edu,one;two;",
            ]
        )
    )
    src_empty_created_at = StringIO(
        "\n".join(
            [
                "url,title,tags,created_at",
                "https://example.io,Io,three;four,",
            ]
        )
    )

    result_missing = import_bookmarks(src_missing_created_at, store)
    result_empty = import_bookmarks(src_empty_created_at, store)
    after = datetime.now(tz=timezone.utc)
    rows = store.list_all()

    assert result_missing.imported == 2
    assert result_missing.skipped == 0
    assert result_empty.imported == 1
    assert result_empty.skipped == 0
    assert len(rows) == 3
    assert rows[0].tags == ["python", "dev"]
    assert rows[1].tags == ["one", "two"]
    assert rows[2].tags == ["three", "four"]
    assert before <= rows[0].created_at <= after
    assert before <= rows[1].created_at <= after
    assert before <= rows[2].created_at <= after


def test_import_bookmarks_skips_malformed_rows_and_ignores_unknown_columns(
    store: BookmarkStore,
) -> None:
    src = StringIO(
        "\n".join(
            [
                "url,title,tags,created_at,extra",
                "https://valid.example,Valid,python;dev,2025-01-15T10:30:00+00:00,foo",
                ",Missing Url,python,2025-01-15T10:30:00+00:00,bar",
                "   ,Blank Url,python,2025-01-15T10:30:00+00:00,baz",
                "https://bad-date.example,Bad Date,python,not-a-date,zzz",
                "https://valid-two.example,Valid Two,one;;two,2025-01-16T11:45:00+00:00,qux",
            ]
        )
    )

    result = import_bookmarks(src, store)
    rows = store.list_all()

    assert result.imported == 2
    assert result.skipped == 3
    assert result.skipped_rows == [
        SkippedRow(row_number=2, reason="url is missing or blank"),
        SkippedRow(row_number=3, reason="url is missing or blank"),
        SkippedRow(row_number=4, reason="created_at cannot be parsed: 'not-a-date'"),
    ]
    assert len(rows) == 2
    assert rows[0].url == "https://valid.example"
    assert rows[1].url == "https://valid-two.example"
    assert rows[1].tags == ["one", "two"]


def test_import_bookmarks_all_malformed_returns_zero_imported(
    store: BookmarkStore,
) -> None:
    src = StringIO(
        "\n".join(
            [
                "url,title,tags,created_at",
                ",Missing,python,2025-01-15T10:30:00+00:00",
                "   ,Blank,python,2025-01-15T10:30:00+00:00",
                "https://bad-date.example,Bad Date,python,not-a-date",
            ]
        )
    )

    result = import_bookmarks(src, store)

    assert result.imported == 0
    assert result.skipped == 3
    assert [row.row_number for row in result.skipped_rows] == [1, 2, 3]


def test_import_bookmarks_accepts_crlf_line_endings(store: BookmarkStore) -> None:
    src = StringIO(
        "url,title,tags,created_at\r\n"
        "https://crlf.example,CRLF,python;dev,2025-01-15T10:30:00+00:00\r\n"
    )

    result = import_bookmarks(src, store)
    rows = store.list_all()

    assert result.imported == 1
    assert result.skipped == 0
    assert rows[0].url == "https://crlf.example"


def test_import_bookmarks_drops_empty_tag_segments(store: BookmarkStore) -> None:
    src = StringIO(
        "\n".join(
            [
                "url,title,tags,created_at",
                "https://tags.example,Tags,python;;dev;,2025-01-15T10:30:00+00:00",
            ]
        )
    )

    result = import_bookmarks(src, store)
    rows = store.list_all()

    assert result.imported == 1
    assert result.skipped == 0
    assert rows[0].tags == ["python", "dev"]
