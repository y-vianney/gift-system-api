from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from ..config import DB_FILE


@contextmanager
def get_db_connection(db_path: Path | str = DB_FILE) -> Generator[sqlite3.Connection, None, None]:
    """Provide a transactional SQLite connection with Row factory enabled."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Path | str = DB_FILE) -> None:
    """Initialize database tables and indexes if they do not exist."""
    with get_db_connection(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                status TEXT NOT NULL,
                visibility TEXT NOT NULL,
                key_hash TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS assignments (
                id TEXT PRIMARY KEY,
                giver_id INTEGER NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
                receiver_id INTEGER NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
                thread_key TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(giver_id),
                UNIQUE(receiver_id)
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assignment_id TEXT NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
                sender_role TEXT NOT NULL CHECK(sender_role IN ('SANTA', 'CHILD')),
                encrypted_content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS system_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_participants_key_hash ON participants(key_hash);
            CREATE INDEX IF NOT EXISTS idx_assignments_giver ON assignments(giver_id);
            CREATE INDEX IF NOT EXISTS idx_assignments_receiver ON assignments(receiver_id);
            CREATE INDEX IF NOT EXISTS idx_messages_assignment ON messages(assignment_id);
            """
        )
