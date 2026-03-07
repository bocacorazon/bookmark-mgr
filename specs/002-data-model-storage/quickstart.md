# Quickstart: bookmarkcli Storage Layer

**Feature**: 002-data-model-storage  
**Last updated**: 2026-03-07

---

## Prerequisites

- Python ≥ 3.11 installed and available on `PATH`
- [`uv`](https://docs.astral.sh/uv/) installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Git
- Repository cloned and on branch `002-data-model-storage` (or merged into `main`)

---

## 1. Clone and Install

```bash
git clone <repository-url>
cd bookmark-mgr

# Install all dependencies (runtime + dev) and the package in editable mode
uv sync
```

No new runtime dependencies are introduced in this feature. The storage layer uses Python's built-in `sqlite3` module exclusively.

---

## 2. Verify the CLI Entry Point

```bash
uv run bookmarkcli --help
```

Expected output (unchanged from S00):

```
Usage: bookmarkcli [OPTIONS] COMMAND [ARGS]...

  Bookmark manager CLI.

Options:
  --help  Show this message and exit.
```

---

## 3. Run the Test Suite

```bash
uv run pytest -q
```

Expected output (after implementing this feature):

```
.......................
23 passed in 0.15s
```

All tests cover the `BookmarkStore` CRUD operations, schema initialisation, migration, and the edge cases defined in the spec.

---

## 4. Project Layout

```text
bookmark-mgr/
├── pyproject.toml          # Build config, deps, entry points, pytest config
├── uv.lock                 # Locked dependency graph (commit this file)
├── conftest.py             # Root-level pytest plugin (exit-code normalisation)
├── src/
│   └── bookmarkcli/
│       ├── __init__.py     # Package namespace
│       ├── cli.py          # Click entry point (unchanged from S00)
│       ├── models.py       # Bookmark dataclass, exceptions, MISSING sentinel
│       └── store.py        # BookmarkStore — SQLite CRUD + migration
└── tests/
    ├── __init__.py         # Test package marker
    └── test_store.py       # Full pytest suite for BookmarkStore
```

---

## 5. Using the Storage Layer (Python REPL / Script)

```python
from pathlib import Path
from bookmarkcli.store import BookmarkStore
from bookmarkcli.models import BookmarkNotFoundError

# Point at any writable path; created automatically on initialize()
store = BookmarkStore(db_path=Path("/tmp/bookmarks.db"))
store.initialize()

# Create a bookmark
bm = store.create(url="https://example.com", title="Example Site", tags=["demo", "test"])
print(bm.id)        # 1
print(bm.tags)      # ['demo', 'test']

# Retrieve by ID
bm2 = store.get(bm.id)
assert bm2.url == "https://example.com"

# List all
all_bms = store.list_all()
print(len(all_bms))  # 1

# Update
updated = store.update(bm.id, title="Updated Title", tags=["demo"])
assert updated.updated_at > updated.created_at

# Delete
store.delete(bm.id)
try:
    store.get(bm.id)
except BookmarkNotFoundError:
    print("deleted successfully")
```

---

## 6. Common Commands

| Task | Command |
|------|---------|
| Install / sync deps | `uv sync` |
| Run CLI | `uv run bookmarkcli [ARGS]` |
| Run tests | `uv run pytest -q` |
| Run tests verbosely | `uv run pytest -v` |
| Run a single test file | `uv run pytest tests/test_store.py -v` |
| Add a runtime dependency | `uv add <package>` |
| Add a dev-only dependency | `uv add --dev <package>` |

---

## 7. In-Memory Testing Pattern

Tests use a temporary directory fixture to avoid touching the real filesystem:

```python
import pytest
from pathlib import Path
from bookmarkcli.store import BookmarkStore

@pytest.fixture
def store(tmp_path: Path) -> BookmarkStore:
    s = BookmarkStore(db_path=tmp_path / "test.db")
    s.initialize()
    return s
```

Each test gets a fresh, isolated SQLite database. The `tmp_path` fixture is built into pytest ≥ 3.9 and requires no additional configuration.

---

## 8. Schema Migration Testing Pattern

To test that migrations preserve data, seed the old schema version manually before calling `initialize()`:

```python
import sqlite3
from pathlib import Path
from bookmarkcli.store import BookmarkStore

def test_migration_preserves_data(tmp_path: Path) -> None:
    db_path = tmp_path / "migrate.db"

    # Seed schema v0 (no schema, user_version = 0)
    con = sqlite3.connect(db_path)
    con.execute("CREATE TABLE bookmarks (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT NOT NULL, title TEXT, tags TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL)")
    con.execute("PRAGMA user_version = 0")
    con.execute("INSERT INTO bookmarks (url, title, tags, created_at, updated_at) VALUES ('https://seed.example', 'Seed', '', '2026-01-01T00:00:00', '2026-01-01T00:00:00')")
    con.commit()
    con.close()

    store = BookmarkStore(db_path=db_path)
    store.initialize()

    bms = store.list_all()
    assert len(bms) == 1
    assert bms[0].url == "https://seed.example"
```

---

## 9. Troubleshooting

**`ModuleNotFoundError: No module named 'bookmarkcli.store'`**  
Run `uv sync` to reinstall the package in editable mode.

**`sqlite3.OperationalError: unable to open database file`**  
Check that the parent directory of `db_path` exists and is writable. `BookmarkStore` does **not** create parent directories.

**`BookmarkNotFoundError` on a valid-looking ID**  
The store is scoped to a single SQLite file. Verify you are pointing at the same `db_path` instance that was used to create the record.

**pytest exits with code 5 (no tests collected)**  
Verify `tests/test_store.py` exists and test function names start with `test_`. The root `conftest.py` normalises exit code 5 to 0 for empty test runs only.
