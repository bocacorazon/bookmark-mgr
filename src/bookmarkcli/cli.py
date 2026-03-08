import click
from pathlib import Path
from typing import Literal

from bookmarkcli.formatting import render_bookmarks_table, render_empty_state
from bookmarkcli.store import BookmarkStore

DEFAULT_DB_PATH = Path.home() / ".bookmarkcli" / "bookmarks.db"


def _open_store(db_path: Path) -> BookmarkStore:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    store = BookmarkStore(db_path=db_path)
    store.initialize()
    return store


def _validate_limit(
    _ctx: click.Context, _param: click.Parameter, value: int | None
) -> int | None:
    if value is not None and value < 0:
        raise click.BadParameter("'--limit' must be 0 or a positive integer.")
    return value

@click.group()
def main() -> None:
    """Bookmark manager CLI."""


@main.command("add")
@click.argument("url")
@click.argument("title", required=False)
@click.option("--tag", "tags", multiple=True, type=click.STRING)
def add_cmd(url: str, title: str | None, tags: tuple[str, ...]) -> None:
    store = _open_store(DEFAULT_DB_PATH)
    bookmark = store.create(url=url, title=title, tags=list(tags))
    click.echo(f"Added bookmark {bookmark.id}.")


@main.command("list")
@click.option("--tag", type=click.STRING, default=None)
@click.option("--limit", type=click.INT, default=None, callback=_validate_limit)
@click.option(
    "--sort",
    type=click.Choice(["newest", "oldest"], case_sensitive=False),
    default="newest",
)
def list_cmd(tag: str | None, limit: int | None, sort: str) -> None:
    store = _open_store(DEFAULT_DB_PATH)
    normalized_sort: Literal["newest", "oldest"] = (
        "oldest" if sort.lower() == "oldest" else "newest"
    )
    bookmarks = store.list_filtered(tag=tag, limit=limit, sort=normalized_sort)
    if bookmarks:
        render_bookmarks_table(bookmarks)
        return
    render_empty_state("No bookmarks found.")


@main.command("search")
@click.argument("query")
def search_cmd(query: str) -> None:
    if not query.strip():
        raise click.UsageError("Search query cannot be empty. Usage: bookmark search <query>")

    store = _open_store(DEFAULT_DB_PATH)
    bookmarks = store.search(query)
    if bookmarks:
        render_bookmarks_table(bookmarks)
        return
    render_empty_state("No bookmarks match your search.")


if __name__ == "__main__":
    main()
