from __future__ import annotations

import os
import sqlite3
from pathlib import Path


def _read_env_local() -> dict[str, str]:
    env_path = Path(__file__).resolve().parents[3] / ".env.local"
    if not env_path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")

    return values


class SQLiteSnippetStore:
    TABLE_NAME = "text_snippets"

    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_table()

    @classmethod
    def from_env(cls) -> "SQLiteSnippetStore":
        file_env = _read_env_local()
        db_path = os.getenv("SQLITE_DB_PATH", file_env.get("SQLITE_DB_PATH", "app/data/snippets.sqlite3"))
        return cls(db_path=db_path)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_table(self) -> None:
        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_id TEXT NOT NULL UNIQUE,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL DEFAULT 'upload',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.commit()
        finally:
            connection.close()

    def upsert_snippet(self, doc_id: str, content: str, source: str = "upload") -> None:
        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute(
                f"""
                INSERT INTO {self.TABLE_NAME} (doc_id, content, source)
                VALUES (?, ?, ?)
                ON CONFLICT(doc_id) DO UPDATE SET
                    content = excluded.content,
                    source = excluded.source,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (doc_id, content, source),
            )
            connection.commit()
        finally:
            connection.close()

    def fetch_all_documents(self) -> list[dict]:
        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute(
                f"""
                SELECT doc_id, content, source
                FROM {self.TABLE_NAME}
                ORDER BY datetime(updated_at) DESC, id DESC
                """
            )
            rows = cursor.fetchall()
        finally:
            connection.close()

        return [
            {
                "doc_id": str(row["doc_id"]),
                "content": str(row["content"]),
                "metadata": {"source": str(row["source"])},
            }
            for row in rows
        ]