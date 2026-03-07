import json
from pathlib import Path

import click

from bookmarkcli.jsonport import bookmarks_to_json, import_from_json
from bookmarkcli.store import BookmarkStore

DEFAULT_DB_PATH = Path("bookmarks.db")


@click.group()
def main() -> None:
    """Bookmark manager CLI."""


def _open_store() -> BookmarkStore:
    store = BookmarkStore(db_path=DEFAULT_DB_PATH)
    store.initialize()
    return store


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
    store = _open_store()
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

    store = _open_store()
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
