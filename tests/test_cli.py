from pathlib import Path

from click.testing import CliRunner

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
