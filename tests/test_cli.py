from pathlib import Path

import pytest
from click.testing import CliRunner, Result

from bookmarkcli.cli import main
from bookmarkcli.store import BookmarkStore


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "bookmarks.db"


@pytest.fixture
def store(db_path: Path) -> BookmarkStore:
    bookmark_store = BookmarkStore(db_path=db_path)
    bookmark_store.initialize()
    return bookmark_store


def invoke_cli(runner: CliRunner, db_path: Path, args: list[str]) -> Result:
    return runner.invoke(main, args, env={"BOOKMARKCLI_DB_PATH": str(db_path)})


def test_tag_add_newly_added_exits_zero_with_confirmation(
    runner: CliRunner, db_path: Path, store: BookmarkStore
) -> None:
    created = store.create(url="https://example.com/new-tag")

    result = invoke_cli(runner, db_path, ["tag", str(created.id or 0), "--add", "python"])

    assert result.exit_code == 0
    assert result.stdout == f"Tagged bookmark {created.id or 0} with 'python'.\n"
    assert result.stderr == ""


def test_tag_add_idempotent_exits_zero_with_already_has_message(
    runner: CliRunner, db_path: Path, store: BookmarkStore
) -> None:
    created = store.create(url="https://example.com/idempotent-tag", tags=["python"])

    result = invoke_cli(runner, db_path, ["tag", str(created.id or 0), "--add", "PYTHON"])

    assert result.exit_code == 0
    assert result.stdout == f"Bookmark {created.id or 0} already has tag 'python'.\n"
    assert result.stderr == ""


def test_tag_add_bookmark_not_found_exits_one_with_error(
    runner: CliRunner, db_path: Path
) -> None:
    result = invoke_cli(runner, db_path, ["tag", "999", "--add", "python"])

    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr == "Error: Bookmark 999 not found.\n"


def test_tag_add_empty_or_whitespace_tag_exits_one_with_error(
    runner: CliRunner, db_path: Path, store: BookmarkStore
) -> None:
    created = store.create(url="https://example.com/invalid-tag")

    result = invoke_cli(runner, db_path, ["tag", str(created.id or 0), "--add", "   "])

    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr == "Error: Tag must not be empty or whitespace.\n"


def test_tag_requires_exactly_one_action_flag(
    runner: CliRunner, db_path: Path, store: BookmarkStore
) -> None:
    created = store.create(url="https://example.com/no-flag")

    result = invoke_cli(runner, db_path, ["tag", str(created.id or 0)])

    assert result.exit_code == 2
    assert result.stdout == ""
    assert result.stderr == "Error: Provide exactly one of --add or --remove.\n"


def test_tag_remove_tag_removed_exits_zero_with_confirmation(
    runner: CliRunner, db_path: Path, store: BookmarkStore
) -> None:
    created = store.create(url="https://example.com/remove-success", tags=["python", "web"])

    result = invoke_cli(
        runner, db_path, ["tag", str(created.id or 0), "--remove", "python"]
    )

    assert result.exit_code == 0
    assert result.stdout == f"Removed tag 'python' from bookmark {created.id or 0}.\n"
    assert result.stderr == ""


def test_tag_remove_tag_not_found_exits_one_with_error(
    runner: CliRunner, db_path: Path, store: BookmarkStore
) -> None:
    created = store.create(url="https://example.com/remove-missing", tags=["python"])

    result = invoke_cli(runner, db_path, ["tag", str(created.id or 0), "--remove", "java"])

    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr == f"Error: Tag 'java' not found on bookmark {created.id or 0}.\n"


def test_tag_remove_bookmark_not_found_exits_one_with_error(
    runner: CliRunner, db_path: Path
) -> None:
    result = invoke_cli(runner, db_path, ["tag", "999", "--remove", "python"])

    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr == "Error: Bookmark 999 not found.\n"


def test_tag_remove_normalizes_whitespace_and_case(
    runner: CliRunner, db_path: Path, store: BookmarkStore
) -> None:
    created = store.create(url="https://example.com/normalize-remove", tags=["python"])

    result = invoke_cli(
        runner, db_path, ["tag", str(created.id or 0), "--remove", "  PyThOn  "]
    )

    assert result.exit_code == 0
    assert result.stdout == f"Removed tag 'python' from bookmark {created.id or 0}.\n"
    assert result.stderr == ""


def test_tag_rejects_add_and_remove_together(
    runner: CliRunner, db_path: Path, store: BookmarkStore
) -> None:
    created = store.create(url="https://example.com/mutex", tags=["python"])

    result = invoke_cli(
        runner,
        db_path,
        [
            "tag",
            str(created.id or 0),
            "--add",
            "python",
            "--remove",
            "docs",
        ],
    )

    assert result.exit_code == 2
    assert result.stdout == ""
    assert result.stderr == "Error: --add and --remove are mutually exclusive.\n"


def test_tags_command_lists_tags_with_counts_in_alphabetical_order(
    runner: CliRunner, db_path: Path, store: BookmarkStore
) -> None:
    store.create(url="https://example.com/tags-1", tags=["web"])
    store.create(url="https://example.com/tags-2", tags=["python", "web"])
    store.create(url="https://example.com/tags-3", tags=["python"])

    result = invoke_cli(runner, db_path, ["tags"])

    assert result.exit_code == 0
    assert result.stdout == "python  2\nweb  2\n"
    assert result.stderr == ""


def test_tags_command_shows_no_tags_found_when_empty(
    runner: CliRunner, db_path: Path
) -> None:
    result = invoke_cli(runner, db_path, ["tags"])

    assert result.exit_code == 0
    assert result.stdout == "No tags found.\n"
    assert result.stderr == ""


def test_tags_output_updates_immediately_after_add_and_remove(
    runner: CliRunner, db_path: Path, store: BookmarkStore
) -> None:
    created = store.create(url="https://example.com/immediate-tags")

    add_result = invoke_cli(runner, db_path, ["tag", str(created.id or 0), "--add", "python"])
    list_after_add = invoke_cli(runner, db_path, ["tags"])
    remove_result = invoke_cli(
        runner, db_path, ["tag", str(created.id or 0), "--remove", "python"]
    )
    list_after_remove = invoke_cli(runner, db_path, ["tags"])

    assert add_result.exit_code == 0
    assert remove_result.exit_code == 0
    assert list_after_add.exit_code == 0
    assert list_after_add.stdout == "python  1\n"
    assert list_after_remove.exit_code == 0
    assert list_after_remove.stdout == "No tags found.\n"
