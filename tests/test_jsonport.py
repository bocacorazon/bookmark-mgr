import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from click.testing import CliRunner

from bookmarkcli.cli import main
from bookmarkcli.jsonport import ImportResult, bookmarks_to_json, import_from_json
from bookmarkcli.models import Bookmark
from bookmarkcli.store import BookmarkStore


def _init_store(db_path: str | Path = "bookmarks.db") -> BookmarkStore:
    store = BookmarkStore(db_path=db_path)
    store.initialize()
    return store


def test_bookmarks_to_json_serializes_all_supported_fields() -> None:
    first = Bookmark(
        id=1,
        url="https://example.com/one",
        title="One",
        tags=["python", "cli"],
        created_at=datetime(2026, 3, 7, 12, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 3, 7, 12, 30, tzinfo=timezone.utc),
    )
    second = Bookmark(
        id=2,
        url="https://example.com/two",
        title=None,
        tags=[],
        created_at=datetime(2026, 3, 7, 13, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 3, 7, 13, 5, tzinfo=timezone.utc),
    )

    payload = bookmarks_to_json([first, second])
    parsed = json.loads(payload)

    assert list(parsed.keys()) == ["bookmarks"]
    assert len(parsed["bookmarks"]) == 2
    assert "id" not in parsed["bookmarks"][0]
    assert parsed["bookmarks"][0]["url"] == "https://example.com/one"
    assert parsed["bookmarks"][0]["title"] == "One"
    assert parsed["bookmarks"][0]["tags"] == ["python", "cli"]
    assert parsed["bookmarks"][0]["created_at"] == "2026-03-07T12:00:00+00:00"
    assert parsed["bookmarks"][0]["updated_at"] == "2026-03-07T12:30:00+00:00"
    assert parsed["bookmarks"][1]["title"] is None
    assert parsed["bookmarks"][1]["tags"] == []
    assert payload.endswith("\n")


def test_bookmarks_to_json_empty_returns_expected_document() -> None:
    assert bookmarks_to_json([]) == '{"bookmarks": []}\n'


def test_import_from_json_adds_new_bookmarks(tmp_path: Path) -> None:
    store = _init_store(tmp_path / "import-add.db")
    payload = json.dumps(
        {
            "bookmarks": [
                {"url": "https://example.com/a", "title": "A", "tags": ["one"]},
                {"url": "https://example.com/b", "title": None, "tags": []},
            ]
        }
    )

    result = import_from_json(payload, store)

    assert result == ImportResult(added=2, skipped=0, updated=0, invalid=0)
    bookmarks = store.list_all()
    assert [bookmark.url for bookmark in bookmarks] == [
        "https://example.com/a",
        "https://example.com/b",
    ]
    assert bookmarks[1].title is None
    assert bookmarks[1].tags == []


def test_import_from_json_missing_url_is_reported_and_skipped(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    store = _init_store(tmp_path / "import-invalid.db")
    payload = json.dumps(
        {
            "bookmarks": [
                {"title": "Missing URL"},
                {"url": " ", "title": "Blank URL"},
                {"url": "https://example.com/ok", "title": "OK", "tags": ["good"]},
            ]
        }
    )

    result = import_from_json(payload, store)
    captured = capsys.readouterr()

    assert result == ImportResult(added=1, skipped=0, updated=0, invalid=2)
    assert "Warning: skipping entry 1: missing url" in captured.err
    assert "Warning: skipping entry 2: missing url" in captured.err
    assert [bookmark.url for bookmark in store.list_all()] == ["https://example.com/ok"]


def test_import_from_json_invalid_json_raises_decode_error(tmp_path: Path) -> None:
    store = _init_store(tmp_path / "import-decode.db")
    with pytest.raises(json.JSONDecodeError):
        import_from_json("{not valid json", store)


def test_import_from_json_missing_bookmarks_key_raises_value_error(tmp_path: Path) -> None:
    store = _init_store(tmp_path / "import-key.db")
    with pytest.raises(ValueError):
        import_from_json(json.dumps({"items": []}), store)


def test_import_from_json_empty_array_returns_zero_result(tmp_path: Path) -> None:
    store = _init_store(tmp_path / "import-empty.db")
    result = import_from_json(json.dumps({"bookmarks": []}), store)
    assert result == ImportResult(added=0, skipped=0, updated=0, invalid=0)
    assert store.list_all() == []


def test_cli_export_to_file_writes_valid_json() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        store = _init_store("bookmarks.db")
        store.create(url="https://example.com/one", title="One", tags=["a", "b"])
        store.create(url="https://example.com/two")

        result = runner.invoke(
            main, ["export", "--format", "json", "--file", "out.json"]
        )

        assert result.exit_code == 0
        payload = Path("out.json").read_text(encoding="utf-8")
        parsed = json.loads(payload)
        assert len(parsed["bookmarks"]) == 2
        assert parsed["bookmarks"][0]["url"] == "https://example.com/one"


def test_cli_export_to_file_with_empty_store_writes_empty_document() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        _init_store("bookmarks.db")

        result = runner.invoke(
            main, ["export", "--format", "json", "--file", "empty.json"]
        )

        assert result.exit_code == 0
        assert Path("empty.json").read_text(encoding="utf-8") == '{"bookmarks": []}\n'


def test_cli_export_to_directory_returns_error() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        _init_store("bookmarks.db")
        Path("output-dir").mkdir()

        result = runner.invoke(
            main, ["export", "--format", "json", "--file", "output-dir"]
        )

        assert result.exit_code == 1
        assert "Error: output-dir is a directory" in result.stderr


def test_cli_export_to_missing_parent_path_returns_error() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        _init_store("bookmarks.db")

        result = runner.invoke(
            main, ["export", "--format", "json", "--file", "missing/out.json"]
        )

        assert result.exit_code == 1
        assert "Error: cannot write to missing/out.json:" in result.stderr


def test_cli_export_without_file_prints_valid_json_to_stdout() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        store = _init_store("bookmarks.db")
        store.create(url="https://example.com/stdout", title="Stdout", tags=["json"])

        result = runner.invoke(main, ["export", "--format", "json"])

        assert result.exit_code == 0
        parsed = json.loads(result.stdout)
        assert parsed["bookmarks"][0]["url"] == "https://example.com/stdout"


def test_cli_export_without_file_on_empty_store_prints_empty_document() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        _init_store("bookmarks.db")

        result = runner.invoke(main, ["export", "--format", "json"])

        assert result.exit_code == 0
        assert result.stdout == '{"bookmarks": []}\n'


def test_cli_import_success_prints_summary_and_inserts_bookmarks() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        _init_store("bookmarks.db")
        Path("input.json").write_text(
            json.dumps(
                {
                    "bookmarks": [
                        {"url": "https://example.com/a", "title": "A", "tags": ["x"]},
                        {"url": "https://example.com/b", "title": None, "tags": []},
                    ]
                }
            ),
            encoding="utf-8",
        )

        result = runner.invoke(main, ["import", "--format", "json", "input.json"])

        assert result.exit_code == 0
        assert (
            result.stdout
            == "Import complete: 2 added, 0 skipped, 0 updated, 0 invalid.\n"
        )
        store = _init_store("bookmarks.db")
        assert len(store.list_all()) == 2


def test_cli_import_missing_file_returns_error() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        _init_store("bookmarks.db")

        result = runner.invoke(main, ["import", "--format", "json", "missing.json"])

        assert result.exit_code == 1
        assert "Error: file not found: missing.json" in result.stderr


def test_cli_import_invalid_json_returns_error() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        _init_store("bookmarks.db")
        Path("broken.json").write_text("{invalid json", encoding="utf-8")

        result = runner.invoke(main, ["import", "--format", "json", "broken.json"])

        assert result.exit_code == 1
        assert "Error: invalid JSON in broken.json" in result.stderr


def test_cli_import_missing_bookmarks_key_returns_error() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        _init_store("bookmarks.db")
        Path("wrong-shape.json").write_text(json.dumps({"items": []}), encoding="utf-8")

        result = runner.invoke(main, ["import", "--format", "json", "wrong-shape.json"])

        assert result.exit_code == 1
        assert "Error: invalid format in wrong-shape.json" in result.stderr


def test_cli_import_partial_invalid_entries_emits_warning_and_summary() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        _init_store("bookmarks.db")
        Path("partial.json").write_text(
            json.dumps(
                {
                    "bookmarks": [
                        {"url": "https://example.com/ok", "title": "OK", "tags": []},
                        {"title": "missing url"},
                    ]
                }
            ),
            encoding="utf-8",
        )

        result = runner.invoke(main, ["import", "--format", "json", "partial.json"])

        assert result.exit_code == 0
        assert "Warning: skipping entry 2: missing url" in result.stderr
        assert (
            result.stdout
            == "Import complete: 1 added, 0 skipped, 0 updated, 1 invalid.\n"
        )


def test_cli_import_on_duplicate_skip_leaves_existing_record_unchanged() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        store = _init_store("bookmarks.db")
        existing = store.create(
            url="https://example.com/dupe", title="Original", tags=["old"]
        )
        Path("dupe.json").write_text(
            json.dumps(
                {
                    "bookmarks": [
                        {
                            "url": "https://example.com/dupe",
                            "title": "Incoming",
                            "tags": ["new"],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        result = runner.invoke(main, ["import", "--format", "json", "dupe.json"])

        assert result.exit_code == 0
        assert (
            result.stdout
            == "Import complete: 0 added, 1 skipped, 0 updated, 0 invalid.\n"
        )
        refreshed = _init_store("bookmarks.db").get(existing.id or 0)
        assert refreshed.title == "Original"
        assert refreshed.tags == ["old"]


def test_cli_import_on_duplicate_update_overwrites_existing_record() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        store = _init_store("bookmarks.db")
        existing = store.create(
            url="https://example.com/dupe", title="Original", tags=["old"]
        )
        Path("dupe.json").write_text(
            json.dumps(
                {
                    "bookmarks": [
                        {
                            "url": "https://example.com/dupe",
                            "title": "Incoming",
                            "tags": ["new"],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        result = runner.invoke(
            main,
            ["import", "--format", "json", "--on-duplicate", "update", "dupe.json"],
        )

        assert result.exit_code == 0
        assert (
            result.stdout
            == "Import complete: 0 added, 0 skipped, 1 updated, 0 invalid.\n"
        )
        refreshed = _init_store("bookmarks.db").get(existing.id or 0)
        assert refreshed.title == "Incoming"
        assert refreshed.tags == ["new"]


def test_cli_import_mixed_file_reports_added_and_skipped_counts() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        store = _init_store("bookmarks.db")
        store.create(url="https://example.com/existing", title="Existing", tags=["keep"])
        Path("mixed.json").write_text(
            json.dumps(
                {
                    "bookmarks": [
                        {
                            "url": "https://example.com/existing",
                            "title": "Incoming Existing",
                            "tags": ["incoming"],
                        },
                        {
                            "url": "https://example.com/new-one",
                            "title": "New One",
                            "tags": ["n1"],
                        },
                        {
                            "url": "https://example.com/new-two",
                            "title": "New Two",
                            "tags": [],
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )

        result = runner.invoke(main, ["import", "--format", "json", "mixed.json"])

        assert result.exit_code == 0
        assert (
            result.stdout
            == "Import complete: 2 added, 1 skipped, 0 updated, 0 invalid.\n"
        )


def test_import_from_json_on_duplicate_update_handles_within_file_duplicates(
    tmp_path: Path,
) -> None:
    store = _init_store(tmp_path / "within-file.db")
    payload = json.dumps(
        {
            "bookmarks": [
                {"url": "https://example.com/same", "title": "First", "tags": ["one"]},
                {"url": "https://example.com/same", "title": "Second", "tags": ["two"]},
            ]
        }
    )

    result = import_from_json(payload, store, on_duplicate="update")

    assert result == ImportResult(added=1, skipped=0, updated=1, invalid=0)
    bookmark = store.list_all()[0]
    assert bookmark.title == "Second"
    assert bookmark.tags == ["two"]


def test_round_trip_preserves_url_title_tags_and_timestamps(tmp_path: Path) -> None:
    store = _init_store(tmp_path / "roundtrip.db")
    con = store._con
    assert con is not None
    seed_rows = [
        (
            "https://example.com/a/very/long/url?query=1",
            "Long URL",
            "long,tagged",
            "2026-03-01T00:00:00+00:00",
            "2026-03-01T12:00:00+00:00",
        ),
        (
            "https://example.com/b",
            "Multi Word Title",
            "alpha,beta,gamma",
            "2026-03-02T08:15:30+00:00",
            "2026-03-03T09:45:10+00:00",
        ),
        (
            "https://example.com/c",
            None,
            "",
            "2026-03-04T11:22:33+00:00",
            "2026-03-04T11:22:33+00:00",
        ),
    ]
    con.executemany(
        """
        INSERT INTO bookmarks (url, title, tags, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        seed_rows,
    )
    con.commit()

    original = sorted(store.list_all(), key=lambda bookmark: bookmark.url)
    json_payload = bookmarks_to_json(original)

    con.execute("DELETE FROM bookmarks")
    con.commit()

    result = import_from_json(json_payload, store)
    restored = sorted(store.list_all(), key=lambda bookmark: bookmark.url)

    assert result == ImportResult(added=3, skipped=0, updated=0, invalid=0)
    assert len(restored) == len(original)
    for before, after in zip(original, restored):
        assert after.url == before.url
        assert after.title == before.title
        assert after.tags == before.tags
        assert after.created_at == before.created_at
        assert after.updated_at == before.updated_at
