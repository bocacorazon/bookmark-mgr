from pathlib import Path

from click.testing import CliRunner

from bookmarkcli import cli as cli_module
from bookmarkcli.store import BookmarkStore


def _seed_bookmarks(db_path: Path) -> tuple[int, int]:
    store = BookmarkStore(db_path=db_path)
    store.initialize()
    first = store.create(url="https://example.com/python", title="Python Docs")
    second = store.create(url="https://example.com/click", title="Click Docs")
    return (first.id or 0, second.id or 0)


def _seed_counted_bookmarks(db_path: Path, count: int) -> None:
    store = BookmarkStore(db_path=db_path)
    store.initialize()
    for index in range(count):
        store.create(
            url=f"https://example.com/{index}",
            title=f"Title {index}",
        )


def _bookmark_row_count(output: str) -> int:
    return sum(1 for line in output.splitlines() if "https://example.com/" in line)


def test_list_empty_store_shows_empty_state(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "bookmarks.db"
    monkeypatch.setattr(cli_module, "DEFAULT_DB_PATH", db_path)

    result = CliRunner().invoke(cli_module.main, ["list"])

    assert result.exit_code == 0
    assert "No bookmarks found." in result.output


def test_list_with_bookmarks_shows_rows_and_headers(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "bookmarks.db"
    first_id, second_id = _seed_bookmarks(db_path)
    monkeypatch.setattr(cli_module, "DEFAULT_DB_PATH", db_path)

    result = CliRunner().invoke(cli_module.main, ["list"])

    assert result.exit_code == 0
    assert "ID" in result.output
    assert "Title" in result.output
    assert "Python Docs" in result.output
    assert "Click Docs" in result.output
    assert str(first_id) in result.output
    assert str(second_id) in result.output


def test_list_uses_plain_text_in_clirunner_non_tty(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "bookmarks.db"
    _seed_bookmarks(db_path)
    monkeypatch.setattr(cli_module, "DEFAULT_DB_PATH", db_path)

    result = CliRunner().invoke(cli_module.main, ["list"])

    assert result.exit_code == 0
    assert "┌" not in result.output
    assert "ID" in result.output


def test_list_tag_filters_to_exact_matching_tag(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "bookmarks.db"
    store = BookmarkStore(db_path=db_path)
    store.initialize()
    store.create(url="https://docs.python.org", title="Python Docs", tags=["python"])
    store.create(url="https://www.rust-lang.org", title="Rust", tags=["rust"])
    monkeypatch.setattr(cli_module, "DEFAULT_DB_PATH", db_path)

    result = CliRunner().invoke(cli_module.main, ["list", "--tag", "python"])

    assert result.exit_code == 0
    assert "Python Docs" in result.output
    assert "Rust" not in result.output


def test_list_tag_nonexistent_shows_empty_state(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "bookmarks.db"
    _seed_bookmarks(db_path)
    monkeypatch.setattr(cli_module, "DEFAULT_DB_PATH", db_path)

    result = CliRunner().invoke(cli_module.main, ["list", "--tag", "nonexistent"])

    assert result.exit_code == 0
    assert "No bookmarks found." in result.output


def test_list_tag_includes_bookmark_with_multiple_tags(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "bookmarks.db"
    store = BookmarkStore(db_path=db_path)
    store.initialize()
    store.create(
        url="https://click.palletsprojects.com",
        title="Click Docs",
        tags=["python", "cli"],
    )
    store.create(url="https://example.com/go", title="Go Docs", tags=["go"])
    monkeypatch.setattr(cli_module, "DEFAULT_DB_PATH", db_path)

    result = CliRunner().invoke(cli_module.main, ["list", "--tag", "python"])

    assert result.exit_code == 0
    assert "Click Docs" in result.output
    assert "Go Docs" not in result.output


def test_search_query_matching_title_returns_bookmark(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "bookmarks.db"
    store = BookmarkStore(db_path=db_path)
    store.initialize()
    store.create(url="https://docs.python.org", title="Python Docs")
    store.create(url="https://www.rust-lang.org", title="Rust Book")
    monkeypatch.setattr(cli_module, "DEFAULT_DB_PATH", db_path)

    result = CliRunner().invoke(cli_module.main, ["search", "Python"])

    assert result.exit_code == 0
    assert "Python Docs" in result.output
    assert "Rust Book" not in result.output


def test_search_query_matching_url_returns_bookmark(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "bookmarks.db"
    store = BookmarkStore(db_path=db_path)
    store.initialize()
    store.create(url="https://docs.python.org/3/library", title="Library Docs")
    store.create(url="https://www.rust-lang.org", title="Rust")
    monkeypatch.setattr(cli_module, "DEFAULT_DB_PATH", db_path)

    result = CliRunner().invoke(cli_module.main, ["search", "python.org/3"])

    assert result.exit_code == 0
    assert "Library Docs" in result.output
    assert "Rust" not in result.output


def test_search_is_case_insensitive(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "bookmarks.db"
    store = BookmarkStore(db_path=db_path)
    store.initialize()
    store.create(url="https://example.com/python", title="python tips")
    monkeypatch.setattr(cli_module, "DEFAULT_DB_PATH", db_path)

    result = CliRunner().invoke(cli_module.main, ["search", "Python"])

    assert result.exit_code == 0
    assert "python tips" in result.output


def test_search_no_matches_shows_empty_state(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "bookmarks.db"
    _seed_bookmarks(db_path)
    monkeypatch.setattr(cli_module, "DEFAULT_DB_PATH", db_path)

    result = CliRunner().invoke(cli_module.main, ["search", "xyz123"])

    assert result.exit_code == 0
    assert "No bookmarks match your search." in result.output


def test_search_empty_string_exits_with_usage_error(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "bookmarks.db"
    monkeypatch.setattr(cli_module, "DEFAULT_DB_PATH", db_path)

    result = CliRunner().invoke(cli_module.main, ["search", ""])

    assert result.exit_code == 2
    assert "Search query cannot be empty. Usage: bookmark search <query>" in result.output


def test_search_whitespace_query_exits_with_usage_error(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "bookmarks.db"
    monkeypatch.setattr(cli_module, "DEFAULT_DB_PATH", db_path)

    result = CliRunner().invoke(cli_module.main, ["search", "   "])

    assert result.exit_code == 2
    assert "Search query cannot be empty. Usage: bookmark search <query>" in result.output


def test_list_limit_returns_exactly_requested_rows(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "bookmarks.db"
    _seed_counted_bookmarks(db_path, 5)
    monkeypatch.setattr(cli_module, "DEFAULT_DB_PATH", db_path)

    result = CliRunner().invoke(cli_module.main, ["list", "--limit", "2"])

    assert result.exit_code == 0
    assert _bookmark_row_count(result.output) == 2


def test_list_limit_larger_than_total_returns_all_rows(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "bookmarks.db"
    _seed_counted_bookmarks(db_path, 3)
    monkeypatch.setattr(cli_module, "DEFAULT_DB_PATH", db_path)

    result = CliRunner().invoke(cli_module.main, ["list", "--limit", "100"])

    assert result.exit_code == 0
    assert _bookmark_row_count(result.output) == 3


def test_list_limit_zero_shows_empty_state(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "bookmarks.db"
    _seed_counted_bookmarks(db_path, 3)
    monkeypatch.setattr(cli_module, "DEFAULT_DB_PATH", db_path)

    result = CliRunner().invoke(cli_module.main, ["list", "--limit", "0"])

    assert result.exit_code == 0
    assert "No bookmarks found." in result.output


def test_list_sort_oldest_outputs_ascending_order(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "bookmarks.db"
    store = BookmarkStore(db_path=db_path)
    store.initialize()
    store.create(url="https://example.com/oldest", title="Oldest")
    store.create(url="https://example.com/middle", title="Middle")
    store.create(url="https://example.com/newest", title="Newest")
    monkeypatch.setattr(cli_module, "DEFAULT_DB_PATH", db_path)

    result = CliRunner().invoke(cli_module.main, ["list", "--sort", "oldest"])

    assert result.exit_code == 0
    assert result.output.index("Oldest") < result.output.index("Middle")
    assert result.output.index("Middle") < result.output.index("Newest")


def test_list_sort_newest_outputs_descending_order(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "bookmarks.db"
    store = BookmarkStore(db_path=db_path)
    store.initialize()
    store.create(url="https://example.com/oldest", title="Oldest")
    store.create(url="https://example.com/middle", title="Middle")
    store.create(url="https://example.com/newest", title="Newest")
    monkeypatch.setattr(cli_module, "DEFAULT_DB_PATH", db_path)

    result = CliRunner().invoke(cli_module.main, ["list", "--sort", "newest"])

    assert result.exit_code == 0
    assert result.output.index("Newest") < result.output.index("Middle")
    assert result.output.index("Middle") < result.output.index("Oldest")


def test_list_limit_negative_exits_with_error(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "bookmarks.db"
    _seed_counted_bookmarks(db_path, 2)
    monkeypatch.setattr(cli_module, "DEFAULT_DB_PATH", db_path)

    result = CliRunner().invoke(cli_module.main, ["list", "--limit", "-1"])

    assert result.exit_code == 2
    assert "'--limit' must be 0 or a positive integer." in result.output


def test_list_sort_invalid_value_exits_with_error(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "bookmarks.db"
    _seed_counted_bookmarks(db_path, 2)
    monkeypatch.setattr(cli_module, "DEFAULT_DB_PATH", db_path)

    result = CliRunner().invoke(cli_module.main, ["list", "--sort", "alpha"])

    assert result.exit_code == 2
    assert "Invalid value for '--sort'" in result.output
    assert "newest" in result.output
    assert "oldest" in result.output
