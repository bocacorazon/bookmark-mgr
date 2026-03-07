from pathlib import Path

from click.testing import CliRunner, Result

from bookmarkcli.cli import main
from bookmarkcli.store import BookmarkStore


def _seed(db_path: Path) -> BookmarkStore:
    store = BookmarkStore(db_path=db_path)
    store.initialize()
    return store


def test_list_empty_store_shows_no_bookmarks_found(tmp_path: Path) -> None:
    db_path = tmp_path / "bookmarks.db"
    _seed(db_path)

    runner = CliRunner()
    result = runner.invoke(main, ["list"], env={"BOOKMARKCLI_DB": str(db_path)})

    assert result.exit_code == 0
    assert "No bookmarks found." in result.output


def test_list_shows_one_row_per_bookmark(tmp_path: Path) -> None:
    db_path = tmp_path / "bookmarks.db"
    store = _seed(db_path)
    store.create(url="https://python.org", title="Python", tags=["python"])
    store.create(url="https://palletsprojects.com", title="Pallets", tags=["python"])

    runner = CliRunner()
    result = runner.invoke(main, ["list"], env={"BOOKMARKCLI_DB": str(db_path)})

    assert result.exit_code == 0
    assert "Python" in result.output
    assert "Pallets" in result.output


def test_list_plain_outputs_tab_separated_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "bookmarks.db"
    store = _seed(db_path)
    store.create(url="https://python.org", title="Python")

    runner = CliRunner()
    result = runner.invoke(
        main, ["list", "--plain"], env={"BOOKMARKCLI_DB": str(db_path)}
    )

    assert result.exit_code == 0
    assert "ID\tTitle\tURL\tTags\tDate Added" in result.output
    assert "\x1b[" not in result.output


def test_list_rich_mode_prints_formatted_output_when_tty(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "bookmarks.db"
    store = _seed(db_path)
    store.create(url="https://python.org", title="Python")

    monkeypatch.setattr("bookmarkcli.formatter.sys.stdout.isatty", lambda: True)
    runner = CliRunner()
    result = runner.invoke(main, ["list"], env={"BOOKMARKCLI_DB": str(db_path)})

    assert result.exit_code == 0
    assert "Python" in result.output


def test_list_tag_filters_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "bookmarks.db"
    store = _seed(db_path)
    store.create(url="https://python.org", title="Python", tags=["python", "docs"])
    store.create(url="https://rust-lang.org", title="Rust", tags=["rust"])

    runner = CliRunner()
    result = runner.invoke(
        main, ["list", "--tag", "python"], env={"BOOKMARKCLI_DB": str(db_path)}
    )

    assert result.exit_code == 0
    assert "Python" in result.output
    assert "Rust" not in result.output


def test_list_limit_caps_output_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "bookmarks.db"
    store = _seed(db_path)
    store.create(url="https://example.com/1", title="One")
    store.create(url="https://example.com/2", title="Two")
    store.create(url="https://example.com/3", title="Three")

    runner = CliRunner()
    result = runner.invoke(
        main, ["list", "--plain", "--limit", "2"], env={"BOOKMARKCLI_DB": str(db_path)}
    )

    lines = [line for line in result.output.strip().splitlines() if line]
    assert result.exit_code == 0
    assert len(lines) == 3  # header + 2 data rows


def test_list_sort_title_orders_results(tmp_path: Path) -> None:
    db_path = tmp_path / "bookmarks.db"
    store = _seed(db_path)
    store.create(url="https://example.com/b", title="Beta")
    store.create(url="https://example.com/a", title="Alpha")

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["list", "--plain", "--sort", "title"],
        env={"BOOKMARKCLI_DB": str(db_path)},
    )

    lines = result.output.strip().splitlines()
    assert result.exit_code == 0
    assert lines[1].split("\t")[1] == "Alpha"
    assert lines[2].split("\t")[1] == "Beta"


def test_list_limit_zero_exits_with_code_2(tmp_path: Path) -> None:
    db_path = tmp_path / "bookmarks.db"
    _seed(db_path)
    runner = CliRunner()
    result = runner.invoke(
        main, ["list", "--limit", "0"], env={"BOOKMARKCLI_DB": str(db_path)}
    )

    assert result.exit_code == 2
    assert "Invalid value for '--limit'" in result.output


def test_list_invalid_sort_exits_with_code_2(tmp_path: Path) -> None:
    db_path = tmp_path / "bookmarks.db"
    _seed(db_path)
    runner = CliRunner()
    result = runner.invoke(
        main, ["list", "--sort", "invalid"], env={"BOOKMARKCLI_DB": str(db_path)}
    )

    assert result.exit_code == 2
    assert "Invalid value for '--sort'" in result.output


def test_list_tag_then_limit_applies_filter_before_limit(tmp_path: Path) -> None:
    db_path = tmp_path / "bookmarks.db"
    store = _seed(db_path)
    store.create(url="https://example.com/rust", title="Rust", tags=["rust"])
    store.create(url="https://example.com/python1", title="Python 1", tags=["python"])
    store.create(url="https://example.com/python2", title="Python 2", tags=["python"])

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["list", "--plain", "--tag", "python", "--limit", "1"],
        env={"BOOKMARKCLI_DB": str(db_path)},
    )

    lines = result.output.strip().splitlines()
    assert result.exit_code == 0
    assert len(lines) == 2
    assert "Python" in lines[1]
    assert "Rust" not in result.output


def test_search_basic_query_returns_matching_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "bookmarks.db"
    store = _seed(db_path)
    store.create(url="https://github.com/python/cpython", title="GitHub CPython")
    store.create(url="https://python.org", title="Python")

    runner = CliRunner()
    result = runner.invoke(
        main, ["search", "github", "--plain"], env={"BOOKMARKCLI_DB": str(db_path)}
    )

    assert result.exit_code == 0
    assert "GitHub CPython" in result.output
    assert "\n2\tPython\t" not in result.output


def test_search_no_match_shows_no_bookmarks_matched(tmp_path: Path) -> None:
    db_path = tmp_path / "bookmarks.db"
    store = _seed(db_path)
    store.create(url="https://python.org", title="Python")

    runner = CliRunner()
    result = runner.invoke(
        main, ["search", "nomatch"], env={"BOOKMARKCLI_DB": str(db_path)}
    )

    assert result.exit_code == 0
    assert 'No bookmarks matched "nomatch".' in result.output


def test_search_plain_suppresses_ansi_codes(tmp_path: Path) -> None:
    db_path = tmp_path / "bookmarks.db"
    store = _seed(db_path)
    store.create(url="https://github.com/python/cpython", title="GitHub")

    runner = CliRunner()
    result = runner.invoke(
        main, ["search", "github", "--plain"], env={"BOOKMARKCLI_DB": str(db_path)}
    )

    assert result.exit_code == 0
    assert "\x1b[" not in result.output


def test_search_piped_output_is_plain_text(tmp_path: Path) -> None:
    db_path = tmp_path / "bookmarks.db"
    store = _seed(db_path)
    store.create(url="https://github.com/python/cpython", title="GitHub")

    runner = CliRunner()
    result = runner.invoke(main, ["search", "github"], env={"BOOKMARKCLI_DB": str(db_path)})

    assert result.exit_code == 0
    assert "ID\tTitle\tURL\tTags\tDate Added" in result.output


def test_search_empty_query_exits_code_2(tmp_path: Path) -> None:
    db_path = tmp_path / "bookmarks.db"
    _seed(db_path)
    runner = CliRunner()
    result = runner.invoke(main, ["search", ""], env={"BOOKMARKCLI_DB": str(db_path)})

    assert result.exit_code == 2
    assert "QUERY must not be empty." in result.output


def test_list_limit_non_integer_exits_code_2(tmp_path: Path) -> None:
    db_path = tmp_path / "bookmarks.db"
    _seed(db_path)
    runner = CliRunner()
    result = runner.invoke(
        main, ["list", "--limit", "abc"], env={"BOOKMARKCLI_DB": str(db_path)}
    )

    assert result.exit_code == 2
    assert "Invalid value for '--limit'" in result.output


def test_runtime_error_unreadable_db_exits_code_1(tmp_path: Path) -> None:
    db_path = tmp_path / "missing-dir" / "bookmarks.db"
    runner = CliRunner()
    result = runner.invoke(main, ["list"], env={"BOOKMARKCLI_DB": str(db_path)})

    assert result.exit_code == 1
    combined = result.output + getattr(result, "stderr", "")
    assert "Error:" in combined
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
