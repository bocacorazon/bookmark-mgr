import os
import sqlite3
from pathlib import Path

import click

from bookmarkcli.formatter import render_table
from bookmarkcli.store import BookmarkStore


def _db_path() -> Path:
    configured = os.environ.get("BOOKMARKCLI_DB", "~/.bookmarks.db")
    return Path(configured).expanduser()


@click.group()
def main() -> None:
    """Bookmark manager CLI."""


@main.command(name="list")
@click.option("--tag", default=None)
@click.option("--limit", type=click.IntRange(min=1), default=None)
@click.option("--sort", type=click.Choice(["date", "title", "url"]), default="date")
@click.option("--plain", is_flag=True, default=False)
def list_bookmarks(
    tag: str | None,
    limit: int | None,
    sort: str,
    plain: bool,
) -> None:
    store = BookmarkStore(db_path=_db_path())
    try:
        store.initialize()
        bookmarks = store.list_filtered(tag=tag, limit=limit, sort=sort)
        render_table(bookmarks, plain=plain)
    except (RuntimeError, sqlite3.Error) as error:
        click.echo(f"Error: {error}", err=True)
        raise SystemExit(1) from error


@main.command()
@click.argument("query", required=True)
@click.option("--plain", is_flag=True, default=False)
def search(query: str, plain: bool) -> None:
    if not query.strip():
        raise click.UsageError("QUERY must not be empty.")

    store = BookmarkStore(db_path=_db_path())
    try:
        store.initialize()
        bookmarks = store.search(query)
        if not bookmarks:
            click.echo(f'No bookmarks matched "{query}".')
            return
        render_table(bookmarks, plain=plain, query=query)
    except (RuntimeError, sqlite3.Error) as error:
        click.echo(f"Error: {error}", err=True)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
