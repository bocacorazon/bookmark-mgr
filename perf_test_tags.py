import sqlite3
import time
from pathlib import Path
from bookmarkcli.store import BookmarkStore

def test_list_tags_perf():
    db_path = Path("perf_tags.db")
    if db_path.exists():
        db_path.unlink()
    
    store = BookmarkStore(db_path=db_path)
    store.initialize()
    
    con = sqlite3.connect(db_path)
    now = "2026-01-01T00:00:00+00:00"
    
    # Insert 10,000 bookmarks with tags
    # Each bookmark has "python" and "web" tags
    con.executemany(
        """
        INSERT INTO bookmarks (url, title, tags, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (f"https://example.com/{idx}", None, "python,web", now, now)
            for idx in range(10_000)
        ],
    )
    con.commit()
    con.close()
    
    start = time.perf_counter()
    tags = store.list_tags()
    elapsed = time.perf_counter() - start
    
    print(f"Elapsed time for list_tags with 10k records: {elapsed:.4f}s")
    assert len(tags) == 2
    assert tags[0] == ("python", 10000)
    assert tags[1] == ("web", 10000)
    
if __name__ == "__main__":
    test_list_tags_perf()
