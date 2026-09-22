from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional
from pydantic import BaseModel, Field

# ==========================================
# Domain Entities (Data Classes)
# ==========================================


@dataclass
class Participant:
    id: int
    name: str
    email: str
    status: str
    visibility: str
    key_hash: str
    created_at: str


@dataclass
class Assignment:
    id: str  # Unique thread ID
    giver_id: int
    receiver_id: int
    thread_key: str
    created_at: str


@dataclass
class Message:
    id: int
    assignment_id: str
    sender_role: str  # "SANTA" | "CHILD"
    encrypted_content: str
    created_at: str


# ==========================================
# Pydantic Schemas (API DTOs)
# ==========================================


class KeyRequest(BaseModel):
    key: str = Field(
        ..., min_length=3, max_length=64, description="Participant secret key"
    )


class WorkerResponse(BaseModel):
    worker_name: str


class SantaMission(BaseModel):
    thread_id: str
    target_name: str
    target_visibility: str


class ChildMission(BaseModel):
    thread_id: str
    santa_display: str = "Père Noël Mystère 🎅"


class SessionResponse(BaseModel):
    valid: bool
    participant_name: str
    santa_mission: Optional[SantaMission] = None
    child_mission: Optional[ChildMission] = None


class ThreadMessageDTO(BaseModel):
    id: int
    sender_role: Literal["SANTA", "CHILD"]
    sender_display: str
    content: str
    created_at: str
    is_mine: bool


class SendMessageRequest(BaseModel):
    key: str = Field(..., min_length=3, max_length=64)
    content: str = Field(
        ..., min_length=1, max_length=1000, description="Message content"
    )
