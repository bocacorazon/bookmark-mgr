import csv
from io import StringIO
from pathlib import Path

import pytest
from click.testing import CliRunner

from bookmarkcli.cli import main
from bookmarkcli.store import BookmarkStore


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "bookmarks.db"


def _init_store(db_path: Path) -> BookmarkStore:
    store = BookmarkStore(db_path=db_path)
    store.initialize()
    return store


def test_export_command_writes_csv_to_stdout(
    runner: CliRunner,
    db_path: Path,
) -> None:
    store = _init_store(db_path)
    first = store.create(url="https://example.com", title="Example", tags=["python", "dev"])
    second = store.create(url="https://example.org")

    result = runner.invoke(
        main,
        ["export", "--format", "csv"],
        env={"BOOKMARKCLI_DB": str(db_path)},
    )

    assert result.exit_code == 0
    assert result.stderr == ""

    reader = csv.DictReader(StringIO(result.stdout))
    rows = list(reader)

    assert reader.fieldnames == ["url", "title", "tags", "created_at"]
    assert len(rows) == 2
    assert rows[0]["url"] == first.url
    assert rows[0]["title"] == "Example"
    assert rows[0]["tags"] == "python;dev"
    assert rows[0]["created_at"] == first.created_at.isoformat()
    assert rows[1]["url"] == second.url
    assert rows[1]["title"] == ""
    assert rows[1]["tags"] == ""
    assert rows[1]["created_at"] == second.created_at.isoformat()


def test_export_command_writes_csv_to_file(
    runner: CliRunner,
    db_path: Path,
    tmp_path: Path,
) -> None:
    store = _init_store(db_path)
    bookmark = store.create(url="https://example.net", title="Net", tags=["one"])
    output_file = tmp_path / "bookmarks.csv"

    result = runner.invoke(
        main,
        ["export", "--format", "csv", "--file", str(output_file)],
        env={"BOOKMARKCLI_DB": str(db_path)},
    )

    assert result.exit_code == 0
    assert result.stdout == ""
    assert output_file.exists()

    reader = csv.DictReader(StringIO(output_file.read_text(encoding="utf-8")))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["url"] == bookmark.url
    assert rows[0]["tags"] == "one"


def test_export_command_empty_store_prints_header_only(
    runner: CliRunner,
    db_path: Path,
) -> None:
    _init_store(db_path)

    result = runner.invoke(
        main,
        ["export", "--format", "csv"],
        env={"BOOKMARKCLI_DB": str(db_path)},
    )

    assert result.exit_code == 0
    assert result.stdout.splitlines() == ["url,title,tags,created_at"]


def test_export_command_non_writable_path_returns_click_error(
    runner: CliRunner,
    db_path: Path,
    tmp_path: Path,
) -> None:
    _init_store(db_path)
    directory_target = tmp_path / "existing-dir"
    directory_target.mkdir()

    result = runner.invoke(
        main,
        ["export", "--format", "csv", "--file", str(directory_target)],
        env={"BOOKMARKCLI_DB": str(db_path)},
    )

    assert result.exit_code != 0
    assert "Invalid value for '--file'" in result.stderr


def test_export_command_file_output_overwrites_existing_file(
    runner: CliRunner,
    db_path: Path,
    tmp_path: Path,
) -> None:
    store = _init_store(db_path)
    store.create(url="https://overwrite.example", title="Overwrite", tags=["one", "two"])
    output_file = tmp_path / "bookmarks.csv"
    output_file.write_text("old content", encoding="utf-8")

    result = runner.invoke(
        main,
        ["export", "--format", "csv", "--file", str(output_file)],
        env={"BOOKMARKCLI_DB": str(db_path)},
    )

    assert result.exit_code == 0
    assert "old content" not in output_file.read_text(encoding="utf-8")
    assert output_file.read_text(encoding="utf-8").startswith("url,title,tags,created_at")


def test_import_command_loads_valid_csv_and_prints_summary(
    runner: CliRunner,
    db_path: Path,
    tmp_path: Path,
) -> None:
    _init_store(db_path)
    input_file = tmp_path / "import.csv"
    input_file.write_text(
        "\n".join(
            [
                "url,title,tags,created_at",
                "https://example.com,Example,python;dev,2025-01-15T10:30:00+00:00",
                "https://example.org,Other,tools,2025-01-16T11:45:00+00:00",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        main,
        ["import", "--format", "csv", str(input_file)],
        env={"BOOKMARKCLI_DB": str(db_path)},
    )

    assert result.exit_code == 0
    assert result.stdout == "Imported 2, skipped 0\n"
    assert result.stderr == ""

    store = _init_store(db_path)
    rows = store.list_all()
    assert len(rows) == 2
    assert rows[0].url == "https://example.com"
    assert rows[0].tags == ["python", "dev"]
    assert rows[1].url == "https://example.org"
    assert rows[1].tags == ["tools"]


def test_import_command_missing_file_returns_click_error(
    runner: CliRunner,
    db_path: Path,
) -> None:
    _init_store(db_path)

    result = runner.invoke(
        main,
        ["import", "--format", "csv", "missing.csv"],
        env={"BOOKMARKCLI_DB": str(db_path)},
    )

    assert result.exit_code != 0
    assert "Invalid value for 'FILE'" in result.stderr


def test_import_command_mixed_valid_and_invalid_rows_reports_skips(
    runner: CliRunner,
    db_path: Path,
    tmp_path: Path,
) -> None:
    _init_store(db_path)
    input_file = tmp_path / "mixed.csv"
    input_file.write_text(
        "\n".join(
            [
                "url,title,tags,created_at",
                "https://valid.example,Valid,python;dev,2025-01-15T10:30:00+00:00",
                ",Missing Url,python,2025-01-15T10:30:00+00:00",
                "https://bad-date.example,Bad Date,python,not-a-date",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        main,
        ["import", "--format", "csv", str(input_file)],
        env={"BOOKMARKCLI_DB": str(db_path)},
    )

    assert result.exit_code == 0
    assert result.stdout == (
        "Imported 1, skipped 2\n"
        "  Row 2: url is missing or blank\n"
        "  Row 3: created_at cannot be parsed: 'not-a-date'\n"
    )


def test_import_command_all_invalid_rows_exits_one(
    runner: CliRunner,
    db_path: Path,
    tmp_path: Path,
) -> None:
    _init_store(db_path)
    input_file = tmp_path / "all-invalid.csv"
    input_file.write_text(
        "\n".join(
            [
                "url,title,tags,created_at",
                ",Missing Url,python,2025-01-15T10:30:00+00:00",
                "https://bad-date.example,Bad Date,python,not-a-date",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        main,
        ["import", "--format", "csv", str(input_file)],
        env={"BOOKMARKCLI_DB": str(db_path)},
    )

    assert result.exit_code == 1
    assert result.stdout.startswith("Imported 0, skipped 2\n")


def test_import_command_missing_url_header_exits_with_stderr(
    runner: CliRunner,
    db_path: Path,
    tmp_path: Path,
) -> None:
    _init_store(db_path)
    input_file = tmp_path / "missing-header.csv"
    input_file.write_text(
        "\n".join(
            [
                "title,tags,created_at",
                "No Url,python,2025-01-15T10:30:00+00:00",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        main,
        ["import", "--format", "csv", str(input_file)],
        env={"BOOKMARKCLI_DB": str(db_path)},
    )

    assert result.exit_code == 1
    assert result.stdout == ""
    assert "CSV file must have a header row with at least a 'url' column" in result.stderr


def test_import_command_header_only_file_exits_zero(
    runner: CliRunner,
    db_path: Path,
    tmp_path: Path,
) -> None:
    _init_store(db_path)
    input_file = tmp_path / "header-only.csv"
    input_file.write_text("url,title,tags,created_at\n", encoding="utf-8")

    result = runner.invoke(
        main,
        ["import", "--format", "csv", str(input_file)],
        env={"BOOKMARKCLI_DB": str(db_path)},
    )

    assert result.exit_code == 0
    assert result.stdout == "Imported 0, skipped 0\n"
