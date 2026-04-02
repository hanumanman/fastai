import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).parent / "sessions.db"


@dataclass
class Session:
    id: str
    messages: list[dict[str, Any]] = field(default_factory=list)


class SessionStore:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self._db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    messages TEXT NOT NULL DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def create(self, messages: list[dict[str, Any]] | None = None) -> Session:
        session_id = uuid.uuid4().hex[:12]
        msg_json = json.dumps(messages or [])
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO sessions (id, messages) VALUES (?, ?)",
                (session_id, msg_json),
            )
        return Session(id=session_id, messages=messages or [])

    def get(self, session_id: str) -> Session | None:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT id, messages FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
        if row is None:
            return None
        return Session(id=row["id"], messages=json.loads(row["messages"]))

    def update(self, session_id: str, messages: list[dict[str, Any]]) -> Session | None:
        msg_json = json.dumps(messages)
        with self._get_conn() as conn:
            cursor = conn.execute(
                "UPDATE sessions SET messages = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (msg_json, session_id),
            )
        if cursor.rowcount == 0:
            return None
        return Session(id=session_id, messages=messages)

    def delete(self, session_id: str) -> bool:
        with self._get_conn() as conn:
            cursor = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        return cursor.rowcount > 0

    def list_all(self) -> list[Session]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT id, messages FROM sessions ORDER BY updated_at DESC"
            ).fetchall()
        return [
            Session(id=row["id"], messages=json.loads(row["messages"])) for row in rows
        ]


store = SessionStore()
