import os
from pathlib import Path

import click

from bookmarkcli.csv_io import export_bookmarks, import_bookmarks
from bookmarkcli.store import BookmarkStore


@click.group()
def main() -> None:
    """Bookmark manager CLI."""


def _get_db_path() -> Path:
    configured = os.environ.get("BOOKMARKCLI_DB")
    if configured:
        return Path(configured)
    return Path.home() / ".local" / "share" / "bookmarkcli" / "bookmarks.db"


def _get_store() -> BookmarkStore:
    db_path = _get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    store = BookmarkStore(db_path=db_path)
    store.initialize()
    return store


@main.command()
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["csv"]),
    required=True,
)
@click.option(
    "--file",
    "output_file",
    type=click.Path(writable=True, dir_okay=False, path_type=Path),
    default=None,
)
def export(output_format: str, output_file: Path | None) -> None:
    del output_format
    store = _get_store()
    if output_file is None:
        export_bookmarks(store.list_all(), click.get_text_stream("stdout"))
        return

    with output_file.open("w", encoding="utf-8", newline="") as destination:
        export_bookmarks(store.list_all(), destination)


@main.command(name="import")
@click.option(
    "--format",
    "input_format",
    type=click.Choice(["csv"]),
    required=True,
)
@click.argument(
    "file",
    type=click.Path(exists=True, readable=True, dir_okay=False, path_type=Path),
)
@click.pass_context
def import_cmd(ctx: click.Context, input_format: str, file: Path) -> None:
    del input_format
    store = _get_store()
    with file.open("r", encoding="utf-8", newline="") as source:
        try:
            result = import_bookmarks(source, store)
        except ValueError as exc:
            click.echo(f"Error: {exc}", err=True)
            ctx.exit(1)

    click.echo(f"Imported {result.imported}, skipped {result.skipped}")
    for skipped_row in result.skipped_rows:
        click.echo(f"  Row {skipped_row.row_number}: {skipped_row.reason}")

    if result.imported == 0 and result.skipped > 0:
        ctx.exit(1)


if __name__ == "__main__":
    main()
