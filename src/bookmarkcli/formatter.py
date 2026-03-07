import re
import sys
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.text import Text

from bookmarkcli.models import Bookmark


def _truncate(value: str, max_len: int) -> str:
    if len(value) <= max_len:
        return value
    if max_len <= 1:
        return "…"
    return f"{value[: max_len - 1]}…"


def _format_date(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M")


def _highlight(value: str, query: str) -> Text:
    text = Text(value)
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    text.highlight_regex(
        pattern,
        style="bold yellow",
    )
    return text


def render_table(
    bookmarks: list[Bookmark],
    *,
    plain: bool = False,
    query: str | None = None,
) -> None:
    if not bookmarks:
        print("No bookmarks found.")
        return

    should_use_plain = plain or not sys.stdout.isatty()
    if should_use_plain:
        header = "ID\tTitle\tURL\tTags\tDate Added"
        print(header)
        for bookmark in bookmarks:
            title = _truncate(bookmark.title or "", 40)
            url = _truncate(bookmark.url, 50)
            tags = _truncate(",".join(bookmark.tags), 25)
            date_added = _truncate(_format_date(bookmark.created_at), 20)
            row = (
                f"{bookmark.id}\t{title}\t{url}\t{tags}\t{date_added}"
            )
            print(row)
        return

    console = Console(force_terminal=True)
    table = Table()
    table.add_column("ID", max_width=6, overflow="crop")
    table.add_column("Title", max_width=40, overflow="ellipsis")
    table.add_column("URL", max_width=50, overflow="ellipsis")
    table.add_column("Tags", max_width=25, overflow="ellipsis")
    table.add_column("Date Added", max_width=20, overflow="crop")

    for bookmark in bookmarks:
        title_value: str | Text = bookmark.title or ""
        url_value: str | Text = bookmark.url
        if query:
            title_value = _highlight(title_value, query)
            url_value = _highlight(url_value, query)

        table.add_row(
            str(bookmark.id),
            title_value,
            url_value,
            ",".join(bookmark.tags),
            _format_date(bookmark.created_at),
        )

    console.print(table)
