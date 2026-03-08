import json
import os
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

import click

from bookmarkcli.formatter import render_table
from bookmarkcli.jsonport import bookmarks_to_json, import_from_json
from bookmarkcli.models import BookmarkNotFoundError, DuplicateBookmarkError
from bookmarkcli.store import BookmarkStore

DEFAULT_DB_PATH = Path.home() / ".bookmarkcli" / "bookmarks.db"
JSON_IO_DB_PATH = Path("bookmarks.db")


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


def _open_json_io_store() -> BookmarkStore:
    store = BookmarkStore(db_path=JSON_IO_DB_PATH)
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
    raise DuplicateBookmarkError(f"A bookmark with this URL already exists (id={existing_id}).")


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
    store = BookmarkStore(db_path=_get_db_path())
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

    store = BookmarkStore(db_path=_get_db_path())
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


@main.command("export")
@click.option(
    "--format",
    "output_format",
    required=True,
    type=click.Choice(["json"]),
)
@click.option("--file", "file_path", type=click.Path(path_type=Path))
def export_command(output_format: str, file_path: Path | None) -> None:
    del output_format
    store = _open_json_io_store()
    payload = bookmarks_to_json(store.list_all())

    if file_path is None:
        click.echo(payload, nl=False)
        return
    if file_path.is_dir():
        click.echo(f"Error: {file_path} is a directory", err=True)
        raise click.exceptions.Exit(1)

    try:
        file_path.write_text(payload, encoding="utf-8")
    except OSError as exc:
        reason = exc.strerror or str(exc)
        click.echo(f"Error: cannot write to {file_path}: {reason}", err=True)
        raise click.exceptions.Exit(1)


@main.command("import")
@click.option(
    "--format",
    "input_format",
    required=True,
    type=click.Choice(["json"]),
)
@click.option(
    "--on-duplicate",
    type=click.Choice(["skip", "update"]),
    default="skip",
    show_default=True,
)
@click.argument("file_path", type=click.Path(path_type=Path))
def import_command(input_format: str, on_duplicate: str, file_path: Path) -> None:
    del input_format

    if not file_path.exists():
        click.echo(f"Error: file not found: {file_path}", err=True)
        raise click.exceptions.Exit(1)

    try:
        json_str = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        reason = exc.strerror or str(exc)
        click.echo(f"Error: cannot read file: {file_path}: {reason}", err=True)
        raise click.exceptions.Exit(1)

    store = _open_json_io_store()
    try:
        result = import_from_json(json_str, store, on_duplicate=on_duplicate)
    except json.JSONDecodeError:
        click.echo(f"Error: invalid JSON in {file_path}", err=True)
        raise click.exceptions.Exit(1)
    except ValueError:
        click.echo(f"Error: invalid format in {file_path}", err=True)
        raise click.exceptions.Exit(1)

    click.echo(
        f"Import complete: {result.added} added, {result.skipped} skipped, "
        f"{result.updated} updated, {result.invalid} invalid."
    )


if __name__ == "__main__":
    main()
