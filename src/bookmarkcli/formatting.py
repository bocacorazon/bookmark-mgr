import sys
from datetime import timezone
from typing import IO

from rich.console import Console
from rich.table import Table

from bookmarkcli.models import Bookmark


def _is_tty(file: IO[str]) -> bool:
    return bool(getattr(file, "isatty", lambda: False)())


def _truncate(value: str, max_width: int) -> str:
    if len(value) <= max_width:
        return value
    return value[: max_width - 1] + "…"


def _format_created_at(bookmark: Bookmark) -> str:
    return bookmark.created_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M")


def render_bookmarks_table(bookmarks: list[Bookmark], file: IO[str] | None = None) -> None:
    output = file or sys.stdout
    if _is_tty(output):
        console = Console(file=output, highlight=False)
        table = Table(show_header=True)
        table.add_column("ID", justify="right", no_wrap=True)
        table.add_column("Title", max_width=40, overflow="ellipsis", no_wrap=True)
        table.add_column("URL", max_width=50, overflow="ellipsis", no_wrap=True)
        table.add_column("Tags")
        table.add_column("Created At", no_wrap=True)

        for bookmark in bookmarks:
            table.add_row(
                str(bookmark.id or ""),
                bookmark.title or "",
                bookmark.url,
                ", ".join(bookmark.tags),
                _format_created_at(bookmark),
            )

        console.print(table)
        return

    headers = ["ID", "Title", "URL", "Tags", "Created At"]
    rows: list[list[str]] = []
    for bookmark in bookmarks:
        rows.append(
            [
                str(bookmark.id or ""),
                _truncate(bookmark.title or "", 40),
                _truncate(bookmark.url, 50),
                ", ".join(bookmark.tags),
                _format_created_at(bookmark),
            ]
        )

    col_widths = [len(header) for header in headers]
    for row in rows:
        for index, value in enumerate(row):
            col_widths[index] = max(col_widths[index], len(value))

    output.write(
        "  ".join(header.ljust(col_widths[index]) for index, header in enumerate(headers))
        + "\n"
    )
    for row in rows:
        output.write(
            "  ".join(value.ljust(col_widths[index]) for index, value in enumerate(row))
            + "\n"
        )


def render_empty_state(message: str, file: IO[str] | None = None) -> None:
    output = file or sys.stdout
    if _is_tty(output):
        Console(file=output, highlight=False).print(f"[dim]{message}[/dim]")
        return
    output.write(f"{message}\n")
