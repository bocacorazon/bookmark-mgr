import time, sqlite3
from pathlib import Path

def test_sqlite_speed(commits=True):
    path = Path("test.db")
    if path.exists(): path.unlink()
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE t (x)")
    start = time.time()
    for i in range(1000):
        con.execute("INSERT INTO t VALUES (?)", (i,))
        if commits: con.commit()
    end = time.time()
    if path.exists(): path.unlink()
    return end - start

print(f"1000 inserts with commit: {test_sqlite_speed(True):.2f}s")
