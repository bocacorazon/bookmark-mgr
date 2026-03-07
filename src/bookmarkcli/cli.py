import os
from pathlib import Path

import click

from bookmarkcli.models import (
    BookmarkNotFoundError,
    TagNotFoundError,
    TagValidationError,
    normalize_tag,
)
from bookmarkcli.store import BookmarkStore


def _raise_usage_error(message: str) -> None:
    click.echo(f"Error: {message}", err=True)
    raise SystemExit(2)


def _raise_application_error(exc: Exception) -> None:
    message = str(exc)
    if not message.endswith("."):
        message = f"{message}."
    raise click.ClickException(message)


@click.group()
@click.pass_context
def main(ctx: click.Context) -> None:
    """Bookmark manager CLI."""
    db_path = Path(os.getenv("BOOKMARKCLI_DB_PATH", "bookmarks.db"))
    store = BookmarkStore(db_path=db_path)
    store.initialize()
    ctx.ensure_object(dict)
    ctx.obj["store"] = store


@main.command()
@click.argument("bookmark_id", type=int, metavar="BOOKMARK_ID")
@click.option("--add", "add_tag", type=str, help="Tag to add.")
@click.option("--remove", "remove_tag", type=str, help="Tag to remove.")
@click.pass_context
def tag(
    ctx: click.Context,
    bookmark_id: int,
    add_tag: str | None,
    remove_tag: str | None,
) -> None:
    """Add or remove a tag on a bookmark."""
    if add_tag and remove_tag:
        _raise_usage_error("--add and --remove are mutually exclusive.")
    if not add_tag and not remove_tag:
        _raise_usage_error("Provide exactly one of --add or --remove.")

    store: BookmarkStore = ctx.obj["store"]
    if add_tag is not None:
        normalized = normalize_tag(add_tag)
        try:
            existing = store.get(bookmark_id)
            store.add_tag(bookmark_id, add_tag)
        except (BookmarkNotFoundError, TagValidationError) as exc:
            _raise_application_error(exc)

        if normalized in existing.tags:
            click.echo(f"Bookmark {bookmark_id} already has tag '{normalized}'.")
        else:
            click.echo(f"Tagged bookmark {bookmark_id} with '{normalized}'.")
        return

    normalized = normalize_tag(remove_tag or "")
    try:
        store.remove_tag(bookmark_id, remove_tag or "")
    except (BookmarkNotFoundError, TagNotFoundError, TagValidationError) as exc:
        _raise_application_error(exc)

    click.echo(f"Removed tag '{normalized}' from bookmark {bookmark_id}.")


@main.command()
@click.pass_context
def tags(ctx: click.Context) -> None:
    """List all tags with their bookmark counts."""
    store: BookmarkStore = ctx.obj["store"]
    tag_counts = store.list_tags()
    if not tag_counts:
        click.echo("No tags found.")
        return

    for tag_name, count in tag_counts:
        click.echo(f"{tag_name}  {count}")


if __name__ == "__main__":
    main()
