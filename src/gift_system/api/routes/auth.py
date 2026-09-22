from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from ...core.models import KeyRequest, SessionResponse
from ...services.santa_service import get_session_by_key

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/session", response_model=SessionResponse)
def authenticate_key(payload: KeyRequest):
    """
    Authenticate participant private key and return the dual-role dashboard session:
    - Giver / Santa role (target name and letterbox thread ID)
    - Receiver / Child role (anonymous Santa letterbox thread ID)
    """
    key = payload.key.strip()
    session = get_session_by_key(key)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé secrète invalide ou non reconnue.",
        )
    return session
