from __future__ import annotations

import secrets
from pathlib import Path
from typing import Optional

from ..config import SECRET_SALT
from ..core.crypto import (
    generate_private_key,
    generate_thread_key,
    hash_key,
)
from ..core.matching import partition_and_match
from ..core.models import ChildMission, SantaMission, SessionResponse
from ..smtp import send_key_email
from ..storage.database import get_db_connection, init_db
from ..storage.repository import GiftRepository


def load_employees_from_file(path: str | Path) -> list[tuple[str, str, str, str]]:
    """Parse employee text file format: name|email|status|visibility."""
    employees: list[tuple[str, str, str, str]] = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 4:
                name, email, status, visibility = parts[0], parts[1], parts[2], parts[3]
                employees.append((name, email, status, visibility))
    return employees


def is_system_initialized() -> bool:
    """Check if assignments have already been generated in SQLite."""
    init_db()
    with get_db_connection() as conn:
        repo = GiftRepository(conn)
        return repo.get_state("INITIALIZED") == "TRUE"


def build_and_save_assignments(
    employees_path: str | Path,
    send_emails: bool = False,
    force_reset: bool = False,
) -> list[tuple[str, str, str, str]]:
    """
    Build Secret Santa assignments and persist them securely to SQLite.
    Returns: list of (giver_name, giver_email, private_key, receiver_name)
    """
    init_db()

    with get_db_connection() as conn:
        repo = GiftRepository(conn)
        if not force_reset and repo.get_state("INITIALIZED") == "TRUE":
            raise RuntimeError("Le système est déjà initialisé.")

        if force_reset:
            repo.clear_all_assignments()

        raw_employees = load_employees_from_file(employees_path)
        active_employees = [e for e in raw_employees if e[2].lower() == "active"]

        # run matching algorithm
        assignments = partition_and_match(active_employees)

        # register participants with unique keys
        participant_ids: dict[str, int] = {}
        participant_keys: dict[str, str] = {}
        used_keys: set[str] = set()

        for name, email, status, visibility in active_employees:
            while True:
                raw_key = generate_private_key()
                if raw_key not in used_keys:
                    used_keys.add(raw_key)
                    break

            k_hash = hash_key(raw_key, salt=SECRET_SALT)
            p_id = repo.create_participant(name, email, status, visibility, k_hash)
            participant_ids[email] = p_id
            participant_keys[email] = raw_key

        # register assignments and letterbox thread keys
        result_keys: list[tuple[str, str, str, str]] = []

        for giver, receiver in assignments:
            giver_email = giver[1]
            receiver_email = receiver[1]

            giver_id = participant_ids[giver_email]
            receiver_id = participant_ids[receiver_email]

            thread_id = f"thr_{secrets.token_hex(8)}"
            thread_key = generate_thread_key()

            repo.create_assignment(thread_id, giver_id, receiver_id, thread_key)

            giver_key = participant_keys[giver_email]
            result_keys.append((giver[0], giver[1], giver_key, receiver[0]))

        # set system state
        repo.set_state("INITIALIZED", "TRUE")

    # email dispatch
    if send_emails:
        for name, mail, key, _ in result_keys:
            try:
                send_key_email(email=mail, name=name, key=key)
            except Exception as exc:
                print(f"Erreur lors de l'envoi du mail à {mail}: {exc}")
    else:
        print("<!> L'envoi des emails est désactivé. Les clés ne seront pas envoyées par email.\n")
        for name, mail, key, _ in result_keys:
            print(f"Nom: {name}, Email: {mail}, Clé: {key}")

    return result_keys


def resolve_worker_name(key: str) -> Optional[str]:
    """Resolve recipient name for given key from database."""
    init_db()
    with get_db_connection() as conn:
        repo = GiftRepository(conn)
        k_hash = hash_key(key, salt=SECRET_SALT)
        participant = repo.get_participant_by_key_hash(k_hash)
        if not participant:
            return None

        giver_res = repo.get_assignment_where_giver(participant.id)
        if not giver_res:
            return None
        _, receiver = giver_res
        return receiver.name


def get_session_by_key(key: str) -> Optional[SessionResponse]:
    """
    Authenticate key and return the dual-role session:
    - Santa mission: assigned recipient's name & letterbox thread ID
    - Child mission: anonymous Santa letterbox thread ID
    """
    init_db()
    with get_db_connection() as conn:
        repo = GiftRepository(conn)
        k_hash = hash_key(key, salt=SECRET_SALT)
        participant = repo.get_participant_by_key_hash(k_hash)
        if not participant:
            return None

        # Role A: Giver (Santa)
        santa_mission = None
        giver_res = repo.get_assignment_where_giver(participant.id)
        if giver_res:
            assignment, receiver = giver_res
            santa_mission = SantaMission(
                thread_id=assignment.id,
                target_name=receiver.name,
                target_visibility=receiver.visibility,
            )

        # Role B: Receiver (Child)
        child_mission = None
        receiver_assignment = repo.get_assignment_where_receiver(participant.id)
        if receiver_assignment:
            child_mission = ChildMission(
                thread_id=receiver_assignment.id,
                santa_display="Père Noël Mystère",
            )

        return SessionResponse(
            valid=True,
            participant_name=participant.name,
            santa_mission=santa_mission,
            child_mission=child_mission,
        )
