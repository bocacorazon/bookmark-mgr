from datetime import datetime, timezone
from io import StringIO

from bookmarkcli.formatting import render_bookmarks_table, render_empty_state
from bookmarkcli.models import Bookmark


def test_render_bookmarks_table_outputs_headers_and_rows() -> None:
    stream = StringIO()
    bookmarks = [
        Bookmark(
            id=1,
            url="https://example.com",
            title="Example",
            tags=["python", "cli"],
            created_at=datetime(2026, 3, 8, 1, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 3, 8, 1, 0, tzinfo=timezone.utc),
        )
    ]

    render_bookmarks_table(bookmarks, file=stream)
    output = stream.getvalue()

    assert "ID" in output
    assert "Title" in output
    assert "URL" in output
    assert "Tags" in output
    assert "Created At" in output
    assert "Example" in output
    assert "https://example.com" in output
    assert "python, cli" in output
    assert "2026-03-08 01:00" in output


def test_render_bookmarks_table_truncates_long_values_with_ellipsis() -> None:
    stream = StringIO()
    bookmarks = [
        Bookmark(
            id=1,
            url="https://example.com/" + ("very-long-path/" * 10),
            title="Very long title " + ("segment " * 10),
            tags=["python"],
            created_at=datetime(2026, 3, 8, 1, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 3, 8, 1, 0, tzinfo=timezone.utc),
        )
    ]

    render_bookmarks_table(bookmarks, file=stream)

    assert "…" in stream.getvalue()


def test_render_empty_state_outputs_message() -> None:
    stream = StringIO()

    render_empty_state("No bookmarks found.", file=stream)

    assert "No bookmarks found." in stream.getvalue()
