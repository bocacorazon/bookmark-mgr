from pathlib import Path

from click.testing import CliRunner, Result

from bookmarkcli.cli import main
from bookmarkcli.store import BookmarkStore


def _invoke(
    runner: CliRunner,
    db_path: Path,
    args: list[str],
    input_text: str | None = None,
) -> Result:
    env = {"BOOKMARKCLI_DB": str(db_path)}
    return runner.invoke(main, args, env=env, input=input_text)


def test_add_with_url_only_succeeds(tmp_path: Path) -> None:
    runner = CliRunner()
    db_path = tmp_path / "bookmarks.db"

    result = _invoke(runner, db_path, ["add", "https://example.com"])

    assert result.exit_code == 0
    assert result.stdout == "✓ Bookmark #1 added: https://example.com\n"
    store = BookmarkStore(db_path=db_path)
    store.initialize()
    bookmarks = store.list_all()
    assert len(bookmarks) == 1
    assert bookmarks[0].url == "https://example.com"
    assert bookmarks[0].title is None
    assert bookmarks[0].tags == []


def test_add_with_title_and_tags_succeeds(tmp_path: Path) -> None:
    runner = CliRunner()
    db_path = tmp_path / "bookmarks.db"

    result = _invoke(
        runner,
        db_path,
        ["add", "https://python.org", "--title", "Python", "--tags", "lang,docs"],
    )

    assert result.exit_code == 0
    assert result.stdout == "✓ Bookmark #1 added: https://python.org\n"
    store = BookmarkStore(db_path=db_path)
    store.initialize()
    bookmarks = store.list_all()
    assert len(bookmarks) == 1
    assert bookmarks[0].title == "Python"
    assert bookmarks[0].tags == ["lang", "docs"]


def test_add_duplicate_url_exits_1(tmp_path: Path) -> None:
    runner = CliRunner()
    db_path = tmp_path / "bookmarks.db"
    seed_store = BookmarkStore(db_path=db_path)
    seed_store.initialize()
    seed_store.create("https://example.com")

    result = _invoke(runner, db_path, ["add", "https://example.com"])

    assert result.exit_code == 1
    assert result.stdout == ""
    assert (
        result.stderr
        == "Error: A bookmark with this URL already exists (id=1).\n"
    )


def test_add_invalid_url_exits_1(tmp_path: Path) -> None:
    runner = CliRunner()
    db_path = tmp_path / "bookmarks.db"

    result = _invoke(runner, db_path, ["add", "not-a-url"])

    assert result.exit_code == 1
    assert result.stdout == ""
    assert (
        result.stderr
        == 'Error: "not-a-url" is not a valid URL. URLs must include a scheme (e.g., '
        "https://) and a host.\n"
    )


def test_add_tags_whitespace_is_stripped(tmp_path: Path) -> None:
    runner = CliRunner()
    db_path = tmp_path / "bookmarks.db"

    result = _invoke(
        runner,
        db_path,
        ["add", "https://example.com/tags", "--tags", " news,  tech ,  , python  "],
    )

    assert result.exit_code == 0
    store = BookmarkStore(db_path=db_path)
    store.initialize()
    bookmarks = store.list_all()
    assert len(bookmarks) == 1
    assert bookmarks[0].tags == ["news", "tech", "python"]


def test_delete_by_id_confirm_y_deletes_bookmark(tmp_path: Path) -> None:
    runner = CliRunner()
    db_path = tmp_path / "bookmarks.db"
    seed_store = BookmarkStore(db_path=db_path)
    seed_store.initialize()
    created = seed_store.create("https://example.com/delete")

    result = _invoke(runner, db_path, ["delete", str(created.id)], input_text="y\n")

    assert result.exit_code == 0
    assert f"  ID   : {created.id}\n" in result.stdout
    assert "  URL  : https://example.com/delete\n" in result.stdout
    assert "Delete this bookmark? [y/N]: y\n" in result.stdout
    assert f"✓ Bookmark #{created.id} deleted.\n" in result.stdout
    verify_store = BookmarkStore(db_path=db_path)
    verify_store.initialize()
    assert verify_store.list_all() == []


def test_delete_by_id_cancel_n_keeps_bookmark(tmp_path: Path) -> None:
    runner = CliRunner()
    db_path = tmp_path / "bookmarks.db"
    seed_store = BookmarkStore(db_path=db_path)
    seed_store.initialize()
    created = seed_store.create("https://example.com/cancel")

    result = _invoke(runner, db_path, ["delete", str(created.id)], input_text="n\n")

    assert result.exit_code == 0
    assert "Delete this bookmark? [y/N]: n\n" in result.stdout
    assert result.stdout.endswith("Cancelled.\n")
    verify_store = BookmarkStore(db_path=db_path)
    verify_store.initialize()
    assert len(verify_store.list_all()) == 1


def test_delete_by_id_enter_defaults_to_cancel(tmp_path: Path) -> None:
    runner = CliRunner()
    db_path = tmp_path / "bookmarks.db"
    seed_store = BookmarkStore(db_path=db_path)
    seed_store.initialize()
    created = seed_store.create("https://example.com/default-cancel")

    result = _invoke(runner, db_path, ["delete", str(created.id)], input_text="\n")

    assert result.exit_code == 0
    assert "Delete this bookmark? [y/N]: \n" in result.stdout
    assert result.stdout.endswith("Cancelled.\n")
    verify_store = BookmarkStore(db_path=db_path)
    verify_store.initialize()
    assert len(verify_store.list_all()) == 1


def test_delete_by_id_not_found_exits_1(tmp_path: Path) -> None:
    runner = CliRunner()
    db_path = tmp_path / "bookmarks.db"

    result = _invoke(runner, db_path, ["delete", "9999"])

    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr == "Error: No bookmark found for '9999'.\n"


def test_delete_by_url_confirm_y_deletes_bookmark(tmp_path: Path) -> None:
    runner = CliRunner()
    db_path = tmp_path / "bookmarks.db"
    seed_store = BookmarkStore(db_path=db_path)
    seed_store.initialize()
    created = seed_store.create("https://example.com/delete-by-url", title="By URL")

    result = _invoke(
        runner,
        db_path,
        ["delete", "https://example.com/delete-by-url"],
        input_text="y\n",
    )

    assert result.exit_code == 0
    assert f"  ID   : {created.id}\n" in result.stdout
    assert "  URL  : https://example.com/delete-by-url\n" in result.stdout
    assert "Delete this bookmark? [y/N]: y\n" in result.stdout
    assert f"✓ Bookmark #{created.id} deleted.\n" in result.stdout
    verify_store = BookmarkStore(db_path=db_path)
    verify_store.initialize()
    assert verify_store.list_all() == []


def test_delete_by_url_cancel_keeps_bookmark(tmp_path: Path) -> None:
    runner = CliRunner()
    db_path = tmp_path / "bookmarks.db"
    seed_store = BookmarkStore(db_path=db_path)
    seed_store.initialize()
    seed_store.create("https://example.com/delete-url-cancel")

    result = _invoke(
        runner,
        db_path,
        ["delete", "https://example.com/delete-url-cancel"],
        input_text="n\n",
    )

    assert result.exit_code == 0
    assert "Delete this bookmark? [y/N]: n\n" in result.stdout
    assert result.stdout.endswith("Cancelled.\n")
    verify_store = BookmarkStore(db_path=db_path)
    verify_store.initialize()
    assert len(verify_store.list_all()) == 1


def test_delete_by_url_not_found_exits_1(tmp_path: Path) -> None:
    runner = CliRunner()
    db_path = tmp_path / "bookmarks.db"

    result = _invoke(runner, db_path, ["delete", "https://unknown.com"])

    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr == "Error: No bookmark found for 'https://unknown.com'.\n"
