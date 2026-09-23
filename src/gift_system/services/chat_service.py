from __future__ import annotations


from ..config import SECRET_SALT
from ..core.crypto import decrypt_message, encrypt_message, hash_key
from ..core.models import ThreadMessageDTO
from ..storage.database import get_db_connection, init_db
from ..storage.repository import GiftRepository


class ChatAccessError(Exception):
    """Raised when access to a letterbox thread is unauthorized."""

    pass


def verify_thread_access(thread_id: str, key: str) -> tuple[str, str]:
    """
    Verify that the given key has access to the thread
    Returns (caller_role, participant_name) where caller_role is 'SANTA' or 'CHILD'
    Raises ChatAccessError if unauthorized
    """
    init_db()
    with get_db_connection() as conn:
        repo = GiftRepository(conn)
        k_hash = hash_key(key, salt=SECRET_SALT)
        participant = repo.get_participant_by_key_hash(k_hash)
        if not participant:
            raise ChatAccessError("Clé invalide ou participante introuvable.")

        assignment = repo.get_assignment_by_thread_id(thread_id)
        if not assignment:
            raise ChatAccessError("Fil de discussion introuvable.")

        if participant.id == assignment.giver_id:
            return "SANTA", participant.name
        elif participant.id == assignment.receiver_id:
            return "CHILD", participant.name
        else:
            raise ChatAccessError("Vous n'êtes pas autorisé à accéder à ce fil.")


def get_thread_messages(thread_id: str, key: str) -> list[ThreadMessageDTO]:
    """
    Retrieve and decrypt messages in a letterbox thread
    Enforces that only the assigned Giver (Santa) or assigned Receiver (Child) can read
    """
    init_db()
    with get_db_connection() as conn:
        repo = GiftRepository(conn)
        k_hash = hash_key(key, salt=SECRET_SALT)
        participant = repo.get_participant_by_key_hash(k_hash)
        if not participant:
            raise ChatAccessError("Clé invalide ou participante introuvable.")

        assignment = repo.get_assignment_by_thread_id(thread_id)
        if not assignment:
            raise ChatAccessError("Fil de discussion introuvable.")

        """
        if participant.id == assignment.giver_id:
            caller_role = "SANTA"
        elif participant.id == assignment.receiver_id:
            caller_role = "CHILD"
        """
        if not (participant.id == assignment.giver_id or participant.id == assignment.receiver_id):
            raise ChatAccessError("Vous n'êtes pas autorisé à accéder à ce fil.")

        raw_messages = repo.get_messages_by_assignment(thread_id)
        result: list[ThreadMessageDTO] = []

        for msg in raw_messages:
            decrypted = decrypt_message(msg.encrypted_content, assignment.thread_key)
            if decrypted is None:
                decrypted = "[Message illisible ou corrompu]"

            """
            is_mine = msg.sender_role == caller_role
            if is_mine:
                display = "Vous"
            elif msg.sender_role == "SANTA":
                display = "Père Noël"
            else:
                display = "Votre Enfant"
            """

            result.append(
                ThreadMessageDTO(
                    id=msg.id,
                    sender_role=msg.sender_role,  # type: ignore
                    # sender_display=display,
                    # is_mine=is_mine,
                    content=decrypted,
                    created_at=msg.created_at,
                )
            )

        return result


def post_thread_message(thread_id: str, key: str, content: str) -> ThreadMessageDTO:
    """
    Post a new anonymous message to the thread.
    Automatically identifies caller as SANTA or CHILD, encrypts content, and records to DB.
    """
    cleaned = content.strip()
    if not cleaned:
        raise ValueError("Le message ne peut pas être vide.")
    if len(cleaned) > 1000:
        raise ValueError("Le message dépasse la limite autorisée (1000 caractères).")

    init_db()
    with get_db_connection() as conn:
        repo = GiftRepository(conn)else
        k_hash = hash_key(key, salt=SECRET_SALT)
        participant = repo.get_participant_by_key_hash(k_hash)
        if not participant:
            raise ChatAccessError("Clé invalide ou participante introuvable.")

        assignment = repo.get_assignment_by_thread_id(thread_id)
        if not assignment:
            raise ChatAccessError("Fil de discussion introuvable.")

        if participant.id == assignment.giver_id:
            sender_role = "SANTA"
        elif participant.id == assignment.receiver_id:
            sender_role = "CHILD"
        else:
            raise ChatAccessError("Vous n'êtes pas autorisé à écrire dans ce fil.")

        encrypted = encrypt_message(cleaned, assignment.thread_key)
        msg_id = repo.create_message(
            assignment_id=thread_id,
            sender_role=sender_role,
            encrypted_content=encrypted,
        )

        from ..storage.repository import current_iso_time

        return ThreadMessageDTO(
            id=msg_id,
            sender_role=sender_role,  # type: ignore
            # sender_display="Vous",
            content=cleaned,
            created_at=current_iso_time(),
            # is_mine=True,
        )
