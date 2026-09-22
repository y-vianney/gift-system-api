"""Core domain logic, models, cryptography, and matching."""

from .crypto import (
    decrypt_message,
    encrypt_message,
    generate_private_key,
    generate_thread_key,
    hash_key,
    normalize_key,
)
from .matching import generate_cycle_derangement, partition_and_match
from .models import (
    Assignment,
    ChildMission,
    KeyRequest,
    Message,
    Participant,
    SantaMission,
    SendMessageRequest,
    SessionResponse,
    ThreadMessageDTO,
    WorkerResponse,
)

__all__ = [
    "decrypt_message",
    "encrypt_message",
    "generate_private_key",
    "generate_thread_key",
    "hash_key",
    "normalize_key",
    "generate_cycle_derangement",
    "partition_and_match",
    "Assignment",
    "ChildMission",
    "KeyRequest",
    "Message",
    "Participant",
    "SantaMission",
    "SendMessageRequest",
    "SessionResponse",
    "ThreadMessageDTO",
    "WorkerResponse",
]
