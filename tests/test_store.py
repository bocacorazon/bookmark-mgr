import sqlite3
import time
from datetime import timezone
from pathlib import Path

import pytest

from bookmarkcli.models import MISSING, BookmarkNotFoundError, BookmarkValidationError
from bookmarkcli.store import BookmarkStore


@pytest.fixture
def store(tmp_path: Path) -> BookmarkStore:
    bookmark_store = BookmarkStore(db_path=tmp_path / "bookmarks.db")
    bookmark_store.initialize()
    return bookmark_store


def test_initialize_creates_bookmarks_table(tmp_path: Path) -> None:
    db_path = tmp_path / "create.db"
    bookmark_store = BookmarkStore(db_path=db_path)

    bookmark_store.initialize()

    con = sqlite3.connect(db_path)
    row = con.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'bookmarks'"
    ).fetchone()
    con.close()
    assert row is not None


def test_initialize_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "idempotent.db"
    bookmark_store = BookmarkStore(db_path=db_path)

    bookmark_store.initialize()
    bookmark_store.initialize()


def test_migration_v0_to_v1_preserves_seeded_row(tmp_path: Path) -> None:
    db_path = tmp_path / "migrate.db"
    con = sqlite3.connect(db_path)
    con.execute(
        "CREATE TABLE bookmarks (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT NOT NULL, title TEXT, tags TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL)"
    )
    con.execute("PRAGMA user_version = 0")
    con.execute(
        "INSERT INTO bookmarks (url, title, tags, created_at, updated_at) VALUES ('https://seed.example', 'Seed', '', '2026-01-01T00:00:00+00:00', '2026-01-01T00:00:00+00:00')"
    )
    con.commit()
    con.close()

    bookmark_store = BookmarkStore(db_path=db_path)
    bookmark_store.initialize()

    verify = sqlite3.connect(db_path)
    row = verify.execute("SELECT COUNT(*) FROM bookmarks").fetchone()
    url_row = verify.execute("SELECT url FROM bookmarks WHERE id = 1").fetchone()
    verify.close()

    assert row is not None
    assert row[0] == 1
    assert url_row is not None
    assert url_row[0] == "https://seed.example"


def test_create_url_only_returns_bookmark_with_id(store: BookmarkStore) -> None:
    bookmark = store.create(url="https://example.com")

    assert bookmark.id is not None
    assert bookmark.url == "https://example.com"
    assert bookmark.title is None
    assert bookmark.tags == []


def test_create_with_title_and_tags_stores_all_fields(store: BookmarkStore) -> None:
    bookmark = store.create(
        url="https://example.com/article", title="Example", tags=["python", "cli"]
    )

    assert bookmark.id is not None
    assert bookmark.title == "Example"
    assert bookmark.tags == ["python", "cli"]


def test_create_empty_url_raises_bookmark_validation_error(store: BookmarkStore) -> None:
    with pytest.raises(BookmarkValidationError):
        store.create(url="")


def test_create_whitespace_url_raises_bookmark_validation_error(
    store: BookmarkStore,
) -> None:
    with pytest.raises(BookmarkValidationError):
        store.create(url="   ")


def test_create_sets_created_at_and_updated_at_to_utc(store: BookmarkStore) -> None:
    bookmark = store.create(url="https://example.com/utc")

    assert bookmark.created_at.tzinfo == timezone.utc
    assert bookmark.updated_at.tzinfo == timezone.utc
    assert bookmark.created_at == bookmark.updated_at


def test_get_returns_correct_bookmark(store: BookmarkStore) -> None:
    created = store.create(url="https://example.com/get")

    loaded = store.get(created.id or 0)

    assert loaded.id == created.id
    assert loaded.url == "https://example.com/get"


def test_get_preserves_all_fields(store: BookmarkStore) -> None:
    created = store.create(
        url="https://example.com/full", title="Example", tags=["python", "cli"]
    )

    loaded = store.get(created.id or 0)

    assert loaded.id == created.id
    assert loaded.url == "https://example.com/full"
    assert loaded.title == "Example"
    assert loaded.tags == ["python", "cli"]
    assert loaded.created_at.tzinfo == timezone.utc
    assert loaded.updated_at.tzinfo == timezone.utc


def test_get_nonexistent_raises_bookmark_not_found_error(store: BookmarkStore) -> None:
    with pytest.raises(BookmarkNotFoundError):
        store.get(9999)


def test_find_by_url_returns_matching_bookmark(store: BookmarkStore) -> None:
    created = store.create(url="https://example.com/find-me", title="Find Me")

    found = store.find_by_url("https://example.com/find-me")

    assert found is not None
    assert found.id == created.id
    assert found.url == created.url
    assert found.title == created.title


def test_find_by_url_returns_none_when_url_missing(store: BookmarkStore) -> None:
    store.create(url="https://example.com/existing")

    found = store.find_by_url("https://example.com/missing")

    assert found is None


def test_find_by_url_returns_none_for_empty_store(store: BookmarkStore) -> None:
    found = store.find_by_url("https://example.com/empty")

    assert found is None


def test_list_all_empty_store_returns_empty_list(store: BookmarkStore) -> None:
    bookmarks = store.list_all()

    assert bookmarks == []


def test_list_all_returns_all_records(store: BookmarkStore) -> None:
    first = store.create(url="https://example.com/one")
    second = store.create(url="https://example.com/two")
    third = store.create(url="https://example.com/three")

    bookmarks = store.list_all()
    urls = [bookmark.url for bookmark in bookmarks]

    assert len(bookmarks) == 3
    assert {first.url, second.url, third.url} == set(urls)


def test_list_all_ordered_by_id_ascending(store: BookmarkStore) -> None:
    first = store.create(url="https://example.com/a")
    second = store.create(url="https://example.com/b")
    third = store.create(url="https://example.com/c")

    bookmarks = store.list_all()

    assert [bookmark.id for bookmark in bookmarks] == [first.id, second.id, third.id]


def test_update_title_changes_stored_value(store: BookmarkStore) -> None:
    created = store.create(url="https://example.com/update-title", title="Old")

    updated = store.update(created.id or 0, title="New")

    assert updated.title == "New"
    assert store.get(created.id or 0).title == "New"


def test_update_refreshes_updated_at_timestamp(store: BookmarkStore) -> None:
    created = store.create(url="https://example.com/update-time")
    time.sleep(0.001)

    updated = store.update(created.id or 0, title="Changed")

    assert updated.updated_at > created.updated_at


def test_update_add_tags_to_tagless_bookmark(store: BookmarkStore) -> None:
    created = store.create(url="https://example.com/add-tags")

    updated = store.update(created.id or 0, tags=["python", "sqlite"])

    assert updated.tags == ["python", "sqlite"]


def test_update_clear_tags_with_empty_list(store: BookmarkStore) -> None:
    created = store.create(url="https://example.com/clear-tags", tags=["a", "b"])

    updated = store.update(created.id or 0, tags=[])

    assert updated.tags == []


def test_update_missing_fields_leaves_them_unchanged(store: BookmarkStore) -> None:
    created = store.create(
        url="https://example.com/unchanged", title="Keep Me", tags=["stable"]
    )
    time.sleep(0.001)

    updated = store.update(created.id or 0, title=MISSING, tags=MISSING)

    assert updated.title == "Keep Me"
    assert updated.tags == ["stable"]
    assert updated.updated_at > created.updated_at


def test_update_no_fields_still_refreshes_updated_at(store: BookmarkStore) -> None:
    created = store.create(url="https://example.com/no-fields")
    time.sleep(0.001)

    updated = store.update(created.id or 0)

    assert updated.url == created.url
    assert updated.title == created.title
    assert updated.tags == created.tags
    assert updated.updated_at > created.updated_at


def test_update_nonexistent_raises_bookmark_not_found_error(store: BookmarkStore) -> None:
    with pytest.raises(BookmarkNotFoundError):
        store.update(9999, title="Nothing")


def test_delete_removes_record(store: BookmarkStore) -> None:
    created = store.create(url="https://example.com/delete-me")

    store.delete(created.id or 0)

    with pytest.raises(BookmarkNotFoundError):
        store.get(created.id or 0)


def test_delete_reduces_list_all_count(store: BookmarkStore) -> None:
    first = store.create(url="https://example.com/first")
    second = store.create(url="https://example.com/second")

    store.delete(first.id or 0)

    remaining = store.list_all()
    assert len(remaining) == 1
    assert remaining[0].id == second.id


def test_deleted_id_raises_bookmark_not_found_error_on_get(store: BookmarkStore) -> None:
    created = store.create(url="https://example.com/deleted")
    store.delete(created.id or 0)

    with pytest.raises(BookmarkNotFoundError):
        store.get(created.id or 0)


def test_delete_nonexistent_raises_bookmark_not_found_error(store: BookmarkStore) -> None:
    with pytest.raises(BookmarkNotFoundError):
        store.delete(9999)


def test_duplicate_urls_produce_distinct_records(store: BookmarkStore) -> None:
    first = store.create(url="https://example.com/duplicate")
    second = store.create(url="https://example.com/duplicate")

    assert first.id != second.id
    assert len(store.list_all()) == 2


def test_create_tags_none_treated_as_empty_list(store: BookmarkStore) -> None:
    created = store.create(url="https://example.com/no-tags", tags=None)
    loaded = store.get(created.id or 0)

    assert created.tags == []
    assert loaded.tags == []


def test_update_no_change_still_refreshes_updated_at(store: BookmarkStore) -> None:
    created = store.create(
        url="https://example.com/no-change", title="Same", tags=["one", "two"]
    )
    time.sleep(0.001)

    updated = store.update(created.id or 0, title="Same", tags=["one", "two"])

    assert updated.title == "Same"
    assert updated.tags == ["one", "two"]
    assert updated.updated_at > created.updated_at


def test_list_all_10000_records_completes_under_2s(tmp_path: Path) -> None:
    db_path = tmp_path / "perf.db"
    store = BookmarkStore(db_path=db_path)
    store.initialize()

    con = sqlite3.connect(db_path)
    now = "2026-01-01T00:00:00+00:00"
    con.executemany(
        """
        INSERT INTO bookmarks (url, title, tags, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (f"https://example.com/{idx}", None, "", now, now)
            for idx in range(10_000)
        ],
    )
    con.commit()
    con.close()

    started_at = time.perf_counter()
    bookmarks = store.list_all()
    elapsed = time.perf_counter() - started_at

    assert len(bookmarks) == 10_000
    assert elapsed < 2.0


def test_list_filtered_without_arguments_returns_all_bookmarks(
    store: BookmarkStore,
) -> None:
    first = store.create(url="https://example.com/one")
    second = store.create(url="https://example.com/two")

    bookmarks = store.list_filtered()

    assert {bookmark.id for bookmark in bookmarks} == {first.id, second.id}


def test_list_filtered_default_sort_is_newest_first(store: BookmarkStore) -> None:
    older = store.create(url="https://example.com/older")
    time.sleep(0.001)
    newer = store.create(url="https://example.com/newer")

    bookmarks = store.list_filtered()

    assert [bookmark.id for bookmark in bookmarks] == [newer.id, older.id]


def test_list_filtered_empty_store_returns_empty_list(store: BookmarkStore) -> None:
    assert store.list_filtered() == []


def test_list_filtered_tag_matches_first_middle_and_last_positions(
    store: BookmarkStore,
) -> None:
    first = store.create(url="https://example.com/first", tags=["python", "cli"])
    middle = store.create(url="https://example.com/middle", tags=["dev", "python", "ops"])
    last = store.create(url="https://example.com/last", tags=["docs", "python"])
    store.create(url="https://example.com/other", tags=["pythonic"])

    bookmarks = store.list_filtered(tag="python")

    assert {bookmark.id for bookmark in bookmarks} == {first.id, middle.id, last.id}


def test_list_filtered_tag_is_case_sensitive(store: BookmarkStore) -> None:
    store.create(url="https://example.com/one", tags=["Dev"])
    store.create(url="https://example.com/two", tags=["dev"])

    bookmarks = store.list_filtered(tag="dev")

    assert len(bookmarks) == 1
    assert bookmarks[0].tags == ["dev"]


def test_list_filtered_unknown_tag_returns_empty_list(store: BookmarkStore) -> None:
    store.create(url="https://example.com/one", tags=["python"])
    assert store.list_filtered(tag="rust") == []


def test_list_filtered_limit_caps_results(store: BookmarkStore) -> None:
    store.create(url="https://example.com/1")
    store.create(url="https://example.com/2")
    store.create(url="https://example.com/3")

    bookmarks = store.list_filtered(limit=2)
    assert len(bookmarks) == 2


def test_list_filtered_sort_title_ascending_case_insensitive(store: BookmarkStore) -> None:
    store.create(url="https://example.com/1", title="beta")
    store.create(url="https://example.com/2", title="Alpha")
    store.create(url="https://example.com/3", title="gamma")

    bookmarks = store.list_filtered(sort="title")

    assert [bookmark.title for bookmark in bookmarks] == ["Alpha", "beta", "gamma"]


def test_list_filtered_sort_title_places_null_titles_last(store: BookmarkStore) -> None:
    store.create(url="https://example.com/1", title=None)
    store.create(url="https://example.com/2", title="Alpha")
    store.create(url="https://example.com/3", title="beta")

    bookmarks = store.list_filtered(sort="title")

    assert [bookmark.title for bookmark in bookmarks] == ["Alpha", "beta", None]


def test_list_filtered_sort_url_ascending(store: BookmarkStore) -> None:
    store.create(url="https://example.com/z")
    store.create(url="https://example.com/a")
    store.create(url="https://example.com/m")

    bookmarks = store.list_filtered(sort="url")

    assert [bookmark.url for bookmark in bookmarks] == [
        "https://example.com/a",
        "https://example.com/m",
        "https://example.com/z",
    ]


def test_list_filtered_sort_date_newest_first(store: BookmarkStore) -> None:
    older = store.create(url="https://example.com/older")
    time.sleep(0.001)
    newer = store.create(url="https://example.com/newer")

    bookmarks = store.list_filtered(sort="date")

    assert [bookmark.id for bookmark in bookmarks] == [newer.id, older.id]


def test_list_filtered_applies_filter_before_limit(store: BookmarkStore) -> None:
    store.create(url="https://example.com/rust", tags=["rust"])
    first = store.create(url="https://example.com/python-1", tags=["python"])
    time.sleep(0.001)
    second = store.create(url="https://example.com/python-2", tags=["python"])

    bookmarks = store.list_filtered(tag="python", limit=1)

    assert len(bookmarks) == 1
    assert bookmarks[0].id == second.id
    assert bookmarks[0].id != first.id


def test_list_filtered_invalid_sort_raises_value_error(store: BookmarkStore) -> None:
    with pytest.raises(ValueError):
        store.list_filtered(sort="newest")


def test_search_matches_title_substring(store: BookmarkStore) -> None:
    store.create(url="https://example.com/python", title="Python Docs")
    store.create(url="https://example.com/rust", title="Rust Docs")

    results = store.search("python")

    assert len(results) == 1
    assert results[0].title == "Python Docs"


def test_search_matches_url_substring(store: BookmarkStore) -> None:
    store.create(url="https://github.com/python/cpython", title="CPython")
    store.create(url="https://example.com/rust", title="Rust")

    results = store.search("github.com")

    assert len(results) == 1
    assert results[0].url == "https://github.com/python/cpython"


def test_search_is_case_insensitive(store: BookmarkStore) -> None:
    store.create(url="https://github.com/python/cpython", title="GitHub CPython")

    results = store.search("gItHuB")

    assert len(results) == 1
    assert results[0].title == "GitHub CPython"


def test_search_no_match_returns_empty_list(store: BookmarkStore) -> None:
    store.create(url="https://python.org", title="Python")
    assert store.search("nomatch") == []


def test_search_percent_and_underscore_are_literal(store: BookmarkStore) -> None:
    literal = store.create(url="https://example.com/100%_done", title="100%_done")
    store.create(url="https://example.com/100Xdone", title="100Xdone")

    results = store.search("%_")

    assert [bookmark.id for bookmark in results] == [literal.id]


def test_search_special_characters_match_literally(store: BookmarkStore) -> None:
    store.create(url="https://github.com/python/cpython", title="CPython")

    results = store.search("https://")

    assert len(results) == 1
    assert results[0].url.startswith("https://")


def test_search_matches_title_or_url(store: BookmarkStore) -> None:
    title_match = store.create(url="https://example.com/one", title="GitHub Mirror")
    url_match = store.create(url="https://github.com/org/repo", title="Repo")
    store.create(url="https://example.com/three", title="Elsewhere")

    results = store.search("github")
    ids = {bookmark.id for bookmark in results}

    assert ids == {title_match.id, url_match.id}
