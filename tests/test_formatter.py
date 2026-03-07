from datetime import datetime, timezone
from unittest.mock import patch

from bookmarkcli.formatter import _truncate, render_table
from bookmarkcli.models import Bookmark


def _bookmark(
    bookmark_id: int,
    *,
    title: str = "Title",
    url: str = "https://example.com",
    tags: list[str] | None = None,
) -> Bookmark:
    now = datetime(2026, 3, 7, 12, 0, tzinfo=timezone.utc)
    return Bookmark(
        id=bookmark_id,
        title=title,
        url=url,
        tags=tags or [],
        created_at=now,
        updated_at=now,
    )


def test_truncate_short_value_unchanged() -> None:
    assert _truncate("short", 10) == "short"


def test_render_table_plain_prints_tab_separated_header_and_rows(capsys) -> None:
    bookmarks = [
        _bookmark(1, title="Python", url="https://python.org", tags=["python", "docs"]),
        _bookmark(2, title="Click", url="https://click.palletsprojects.com", tags=["cli"]),
    ]

    render_table(bookmarks, plain=True)

    output = capsys.readouterr().out.strip().splitlines()
    assert output[0] == "ID\tTitle\tURL\tTags\tDate Added"
    assert output[1].startswith("1\tPython\thttps://python.org\tpython,docs\t")
    assert output[2].startswith("2\tClick\thttps://click.palletsprojects.com\tcli\t")


def test_render_table_non_tty_falls_back_to_plain(capsys) -> None:
    bookmarks = [_bookmark(1, title="Python")]
    with patch("bookmarkcli.formatter.sys.stdout.isatty", return_value=False):
        render_table(bookmarks, plain=False)

    output = capsys.readouterr().out
    assert "ID\tTitle\tURL\tTags\tDate Added" in output
    assert "\x1b[" not in output


def test_render_table_empty_prints_no_bookmarks_found(capsys) -> None:
    render_table([], plain=True)
    assert capsys.readouterr().out.strip() == "No bookmarks found."


def test_render_table_rich_mode_uses_force_terminal_true() -> None:
    bookmarks = [_bookmark(1, title="Python")]
    with patch("bookmarkcli.formatter.sys.stdout.isatty", return_value=True):
        with patch("bookmarkcli.formatter.Console") as mock_console:
            mock_console.return_value.print.return_value = None
            render_table(bookmarks, plain=False)

    mock_console.assert_called_once_with(force_terminal=True)


def test_render_table_query_highlights_in_rich_mode() -> None:
    bookmarks = [_bookmark(1, title="GitHub Repo", url="https://github.com/org/repo")]
    with patch("bookmarkcli.formatter.sys.stdout.isatty", return_value=True):
        with patch("bookmarkcli.formatter.Console") as mock_console:
            render_table(bookmarks, plain=False, query="github")
            table = mock_console.return_value.print.call_args[0][0]
            title_cell = table.columns[1]._cells[0]
            url_cell = table.columns[2]._cells[0]
            assert title_cell.plain == "GitHub Repo"
            assert url_cell.plain == "https://github.com/org/repo"
            assert title_cell.spans
            assert url_cell.spans


def test_render_table_plain_with_query_has_no_ansi_codes(capsys) -> None:
    bookmarks = [_bookmark(1, title="GitHub Repo", url="https://github.com/org/repo")]
    render_table(bookmarks, plain=True, query="github")

    output = capsys.readouterr().out
    assert "\x1b[" not in output
