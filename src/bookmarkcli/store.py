import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from bookmarkcli.models import (
    MISSING,
    Bookmark,
    BookmarkNotFoundError,
    BookmarkValidationError,
    _MISSING_TYPE,
)


class BookmarkStore:
    _MIGRATIONS: list[str] = [
        """
        CREATE TABLE IF NOT EXISTS bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            title TEXT,
            tags TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    ]

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = Path(db_path)
        self._con: sqlite3.Connection | None = None

    @staticmethod
    def _serialize_tags(tags: list[str] | None) -> str:
        if not tags:
            return ""
        return ",".join(tag.strip() for tag in tags)

    @staticmethod
    def _deserialize_tags(tags: str | None) -> list[str]:
        if not tags:
            return []
        return [tag for tag in tags.split(",") if tag]

    @staticmethod
    def _row_to_bookmark(row: sqlite3.Row) -> Bookmark:
        created_at = datetime.fromisoformat(row["created_at"])
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        else:
            created_at = created_at.astimezone(timezone.utc)

        updated_at = datetime.fromisoformat(row["updated_at"])
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        else:
            updated_at = updated_at.astimezone(timezone.utc)
        return Bookmark(
            id=row["id"],
            url=row["url"],
            created_at=created_at,
            updated_at=updated_at,
            title=row["title"],
            tags=BookmarkStore._deserialize_tags(row["tags"]),
        )

    def initialize(self) -> None:
        if self._con is None:
            self._con = sqlite3.connect(self._db_path)
            self._con.row_factory = sqlite3.Row

        row = self._con.execute("PRAGMA user_version").fetchone()
        current_version = int(row[0]) if row is not None else 0
        target_version = len(self._MIGRATIONS)

        for index, migration_sql in enumerate(self._MIGRATIONS, start=1):
            if index > current_version:
                self._con.execute(migration_sql)

        if current_version != target_version:
            self._con.execute(f"PRAGMA user_version = {target_version}")
        self._con.commit()

    def create(
        self,
        url: str,
        title: str | None = None,
        tags: list[str] | None = None,
    ) -> Bookmark:
        if not url or not url.strip():
            raise BookmarkValidationError("url must not be empty")

        con = self._require_connection()
        now = datetime.now(tz=timezone.utc)
        serialized_tags = self._serialize_tags(tags)
        cursor = con.execute(
            """
            INSERT INTO bookmarks (url, title, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (url, title, serialized_tags, now.isoformat(), now.isoformat()),
        )
        con.commit()
        bookmark_id = cursor.lastrowid
        if bookmark_id is None:
            raise sqlite3.OperationalError("failed to get inserted bookmark id")

        return Bookmark(
            id=int(bookmark_id),
            url=url,
            created_at=now,
            updated_at=now,
            title=title,
            tags=list(tags) if tags else [],
        )

    def get(self, bookmark_id: int) -> Bookmark:
        con = self._require_connection()
        row = con.execute(
            """
            SELECT id, url, title, tags, created_at, updated_at
            FROM bookmarks
            WHERE id = ?
            """,
            (bookmark_id,),
        ).fetchone()
        if row is None:
            raise BookmarkNotFoundError(f"Bookmark {bookmark_id} not found")
        return self._row_to_bookmark(row)

    def find_by_url(self, url: str) -> Bookmark | None:
        con = self._require_connection()
        row = con.execute(
            """
            SELECT id, url, title, tags, created_at, updated_at
            FROM bookmarks
            WHERE url = ?
            """,
            (url,),
        ).fetchone()
        if row is None:
            return None
        return self._row_to_bookmark(row)

    def list_all(self) -> list[Bookmark]:
        con = self._require_connection()
        rows = con.execute(
            """
            SELECT id, url, title, tags, created_at, updated_at
            FROM bookmarks
            ORDER BY id ASC
            """
        ).fetchall()
        return [self._row_to_bookmark(row) for row in rows]

    def list_filtered(
        self,
        tag: str | None = None,
        limit: int | None = None,
        sort: str = "date",
    ) -> list[Bookmark]:
        if sort not in {"date", "title", "url"}:
            raise ValueError(f"invalid sort value: {sort}")

        con = self._require_connection()
        query = """
            SELECT id, url, title, tags, created_at, updated_at
            FROM bookmarks
        """
        params: list[object] = []
        if tag is not None:
            query += """
            WHERE
                tags = ?
                OR tags LIKE ? || ',%'
                OR tags LIKE '%,' || ?
                OR tags LIKE '%,' || ? || ',%'
            """
            params.extend([tag, tag, tag, tag])

        query += """
            ORDER BY
                CASE WHEN ? = 'title' THEN title IS NULL END ASC,
                CASE WHEN ? = 'title' THEN LOWER(title) END ASC,
                CASE WHEN ? = 'url' THEN url END ASC,
                CASE WHEN ? = 'date' THEN created_at END DESC,
                created_at DESC
        """
        params.extend([sort, sort, sort, sort])

        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        rows = con.execute(query, tuple(params)).fetchall()
        return [self._row_to_bookmark(row) for row in rows]

    @staticmethod
    def _escape_like(query: str) -> str:
        return query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    def search(self, query: str) -> list[Bookmark]:
        con = self._require_connection()
        escaped_query = self._escape_like(query)
        rows = con.execute(
            """
            SELECT id, url, title, tags, created_at, updated_at
            FROM bookmarks
            WHERE LOWER(title) LIKE '%' || LOWER(?) || '%' ESCAPE '\\'
               OR LOWER(url) LIKE '%' || LOWER(?) || '%' ESCAPE '\\'
            ORDER BY created_at DESC
            """,
            (escaped_query, escaped_query),
        ).fetchall()
        return [self._row_to_bookmark(row) for row in rows]

    def update(
        self,
        bookmark_id: int,
        title: str | None | _MISSING_TYPE = MISSING,
        tags: list[str] | _MISSING_TYPE = MISSING,
    ) -> Bookmark:
        con = self._require_connection()
        exists = con.execute(
            "SELECT 1 FROM bookmarks WHERE id = ?",
            (bookmark_id,),
        ).fetchone()
        if exists is None:
            raise BookmarkNotFoundError(f"Bookmark {bookmark_id} not found")

        set_clauses: list[str] = []
        values: list[object] = []
        if not isinstance(title, _MISSING_TYPE):
            set_clauses.append("title = ?")
            values.append(title)
        if not isinstance(tags, _MISSING_TYPE):
            set_clauses.append("tags = ?")
            values.append(self._serialize_tags(tags))

        now = datetime.now(tz=timezone.utc).isoformat()
        set_clauses.append("updated_at = ?")
        values.append(now)
        values.append(bookmark_id)

        con.execute(
            f"UPDATE bookmarks SET {', '.join(set_clauses)} WHERE id = ?",
            tuple(values),
        )
        con.commit()
        return self.get(bookmark_id)

    def delete(self, bookmark_id: int) -> None:
        con = self._require_connection()
        cursor = con.execute("DELETE FROM bookmarks WHERE id = ?", (bookmark_id,))
        if cursor.rowcount == 0:
            raise BookmarkNotFoundError(f"Bookmark {bookmark_id} not found")
        con.commit()

    def _require_connection(self) -> sqlite3.Connection:
        if self._con is None:
            raise RuntimeError("BookmarkStore is not initialized; call initialize() first")
        return self._con
