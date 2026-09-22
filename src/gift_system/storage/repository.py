from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Optional

from ..core.models import Assignment, Message, Participant


def current_iso_time() -> str:
    return datetime.now(timezone.utc).isoformat()


class GiftRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    # ==========================================
    # System State
    # ==========================================

    def get_state(self, key: str) -> Optional[str]:
        cur = self.conn.execute("SELECT value FROM system_state WHERE key = ?", (key,))
        row = cur.fetchone()
        return row["value"] if row else None

    def set_state(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO system_state (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )

    # ==========================================
    # Participants
    # ==========================================

    def create_participant(
        self,
        name: str,
        email: str,
        status: str,
        visibility: str,
        key_hash: str,
    ) -> int:
        now = current_iso_time()
        cur = self.conn.execute(
            """
            INSERT INTO participants (name, email, status, visibility, key_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name.strip(), email.strip(), status.strip(), visibility.strip(), key_hash, now),
        )
        return cur.lastrowid

    def get_participant_by_key_hash(self, key_hash: str) -> Optional[Participant]:
        cur = self.conn.execute(
            "SELECT id, name, email, status, visibility, key_hash, created_at FROM participants WHERE key_hash = ?",
            (key_hash,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return Participant(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            status=row["status"],
            visibility=row["visibility"],
            key_hash=row["key_hash"],
            created_at=row["created_at"],
        )

    def get_participant_by_id(self, participant_id: int) -> Optional[Participant]:
        cur = self.conn.execute(
            "SELECT id, name, email, status, visibility, key_hash, created_at FROM participants WHERE id = ?",
            (participant_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return Participant(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            status=row["status"],
            visibility=row["visibility"],
            key_hash=row["key_hash"],
            created_at=row["created_at"],
        )

    # ==========================================
    # Assignments
    # ==========================================

    def create_assignment(
        self,
        thread_id: str,
        giver_id: int,
        receiver_id: int,
        thread_key: str,
    ) -> None:
        now = current_iso_time()
        self.conn.execute(
            """
            INSERT INTO assignments (id, giver_id, receiver_id, thread_key, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (thread_id, giver_id, receiver_id, thread_key, now),
        )

    def get_assignment_by_thread_id(self, thread_id: str) -> Optional[Assignment]:
        cur = self.conn.execute(
            "SELECT id, giver_id, receiver_id, thread_key, created_at FROM assignments WHERE id = ?",
            (thread_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return Assignment(
            id=row["id"],
            giver_id=row["giver_id"],
            receiver_id=row["receiver_id"],
            thread_key=row["thread_key"],
            created_at=row["created_at"],
        )

    def get_assignment_where_giver(self, giver_id: int) -> Optional[tuple[Assignment, Participant]]:
        """Find assignment where participant is the Giver, including Receiver details."""
        cur = self.conn.execute(
            """
            SELECT a.id, a.giver_id, a.receiver_id, a.thread_key, a.created_at,
                   p.id as p_id, p.name as p_name, p.email as p_email, p.status as p_status,
                   p.visibility as p_visibility, p.key_hash as p_key_hash, p.created_at as p_created_at
            FROM assignments a
            JOIN participants p ON a.receiver_id = p.id
            WHERE a.giver_id = ?
            """,
            (giver_id,),
        )
        row = cur.fetchone()
        if not row:
            return None

        assignment = Assignment(
            id=row["id"],
            giver_id=row["giver_id"],
            receiver_id=row["receiver_id"],
            thread_key=row["thread_key"],
            created_at=row["created_at"],
        )
        receiver = Participant(
            id=row["p_id"],
            name=row["p_name"],
            email=row["p_email"],
            status=row["p_status"],
            visibility=row["p_visibility"],
            key_hash=row["p_key_hash"],
            created_at=row["p_created_at"],
        )
        return assignment, receiver

    def get_assignment_where_receiver(self, receiver_id: int) -> Optional[Assignment]:
        """Find assignment where participant is the Receiver (Child). Does NOT expose giver."""
        cur = self.conn.execute(
            "SELECT id, giver_id, receiver_id, thread_key, created_at FROM assignments WHERE receiver_id = ?",
            (receiver_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return Assignment(
            id=row["id"],
            giver_id=row["giver_id"],
            receiver_id=row["receiver_id"],
            thread_key=row["thread_key"],
            created_at=row["created_at"],
        )

    # ==========================================
    # Messages (Letterbox)
    # ==========================================

    def create_message(
        self,
        assignment_id: str,
        sender_role: str,
        encrypted_content: str,
    ) -> int:
        now = current_iso_time()
        cur = self.conn.execute(
            """
            INSERT INTO messages (assignment_id, sender_role, encrypted_content, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (assignment_id, sender_role, encrypted_content, now),
        )
        return cur.lastrowid

    def get_messages_by_assignment(self, assignment_id: str) -> list[Message]:
        cur = self.conn.execute(
            """
            SELECT id, assignment_id, sender_role, encrypted_content, created_at
            FROM messages
            WHERE assignment_id = ?
            ORDER BY id ASC
            """,
            (assignment_id,),
        )
        return [
            Message(
                id=row["id"],
                assignment_id=row["assignment_id"],
                sender_role=row["sender_role"],
                encrypted_content=row["encrypted_content"],
                created_at=row["created_at"],
            )
            for row in cur.fetchall()
        ]

    # ==========================================
    # Clear / Reset
    # ==========================================

    def clear_all_assignments(self) -> None:
        self.conn.execute("DELETE FROM messages")
        self.conn.execute("DELETE FROM assignments")
        self.conn.execute("DELETE FROM participants")
        self.conn.execute("DELETE FROM system_state")
