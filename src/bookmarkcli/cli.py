import os
from pathlib import Path
from urllib.parse import urlparse

import click

from bookmarkcli.models import BookmarkNotFoundError, DuplicateBookmarkError
from bookmarkcli.store import BookmarkStore

DEFAULT_DB_PATH = Path.home() / ".bookmarkcli" / "bookmarks.db"


def _get_db_path() -> Path:
    db_env = os.environ.get("BOOKMARKCLI_DB")
    if db_env:
        return Path(db_env)
    return DEFAULT_DB_PATH


def _build_store() -> BookmarkStore:
    db_path = _get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    store = BookmarkStore(db_path=db_path)
    store.initialize()
    return store


def _is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return bool(parsed.scheme and parsed.netloc)


def _parse_tags(raw: str | None) -> list[str]:
    if raw is None:
        return []
    return [tag.strip() for tag in raw.split(",") if tag.strip()]


def _ensure_url_not_duplicate(store: BookmarkStore, url: str) -> None:
    existing = store.find_by_url(url)
    if existing is None:
        return
    existing_id = existing.id if existing.id is not None else "unknown"
    raise DuplicateBookmarkError(
        f"A bookmark with this URL already exists (id={existing_id})."
    )


@click.group()
def main() -> None:
    """Bookmark manager CLI."""


@main.command("add")
@click.argument("url")
@click.option("--title", type=str, default=None, help="Title for the bookmark.")
@click.option(
    "--tags",
    type=str,
    default=None,
    help="Comma-separated tags for the bookmark.",
)
def add(url: str, title: str | None, tags: str | None) -> None:
    """Add a new bookmark."""
    if not _is_valid_url(url):
        raise click.ClickException(
            f'"{url}" is not a valid URL. URLs must include a scheme (e.g., '
            "https://) and a host."
        )

    store = _build_store()
    try:
        _ensure_url_not_duplicate(store, url)
    except DuplicateBookmarkError as exc:
        raise click.ClickException(str(exc)) from exc

    bookmark = store.create(url=url, title=title, tags=_parse_tags(tags))
    bookmark_id = bookmark.id if bookmark.id is not None else "unknown"
    click.echo(f"✓ Bookmark #{bookmark_id} added: {bookmark.url}")


@main.command("delete")
@click.argument("bookmark_ref")
def delete(bookmark_ref: str) -> None:
    """Delete a bookmark by ID or URL."""
    store = _build_store()
    try:
        bookmark_id = int(bookmark_ref)
    except ValueError:
        bookmark = store.find_by_url(bookmark_ref)
        if bookmark is None:
            raise click.ClickException(f"No bookmark found for '{bookmark_ref}'.")
    else:
        try:
            bookmark = store.get(bookmark_id)
        except BookmarkNotFoundError as exc:
            raise click.ClickException(f"No bookmark found for '{bookmark_ref}'.") from exc

    title = bookmark.title if bookmark.title else "(none)"
    click.echo(f"  ID   : {bookmark.id}")
    click.echo(f"  URL  : {bookmark.url}")
    click.echo(f"  Title: {title}")

    if not click.confirm("Delete this bookmark?", default=False):
        click.echo("Cancelled.")
        return

    if bookmark.id is None:
        raise click.ClickException(f"No bookmark found for '{bookmark_ref}'.")
    delete_id = bookmark.id
    try:
        store.delete(delete_id)
    except BookmarkNotFoundError as exc:
        raise click.ClickException(f"No bookmark found for '{bookmark_ref}'.") from exc
    click.echo(f"✓ Bookmark #{delete_id} deleted.")


if __name__ == "__main__":
    main()
