from __future__ import annotations

import json
from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect, status

from ...core.models import SendMessageRequest, ThreadMessageDTO
from ...services.chat_service import (
    ChatAccessError,
    get_thread_messages,
    post_thread_message,
    verify_thread_access,
)
from ..ws_manager import ws_manager

router = APIRouter(prefix="/api/threads", tags=["chat"])


@router.get("/{thread_id}/messages", response_model=list[ThreadMessageDTO])
def list_messages(
    thread_id: str,
    key: str = Query(..., min_length=3, description="Participant secret key"),
):
    """
    Fetch all decrypted messages for the given thread.
    Access is strictly limited to the Santa or the Child of this assignment.
    """
    try:
        return get_thread_messages(thread_id, key.strip())
    except ChatAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )


@router.post("/{thread_id}/messages", response_model=ThreadMessageDTO)
async def send_message(
    thread_id: str,
    payload: SendMessageRequest,
):
    """
    Post a new anonymous message in the thread.
    The sender role ('SANTA' or 'CHILD') is derived securely from the provided key.
    Broadcasts the new message to all active WebSockets on this thread.
    """
    try:
        msg_dto = post_thread_message(thread_id, payload.key.strip(), payload.content)

        # Real-time WebSocket broadcast
        await ws_manager.broadcast(
            thread_id,
            {
                "type": "new_message",
                "message": {
                    "id": msg_dto.id,
                    "sender_role": msg_dto.sender_role,
                    "content": msg_dto.content,
                    "created_at": msg_dto.created_at,
                },
            },
        )

        return msg_dto
    except ChatAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.websocket("/{thread_id}/ws")
async def websocket_thread_chat(
    websocket: WebSocket,
    thread_id: str,
    key: str = Query(..., min_length=3, description="Participant secret key"),
):
    """
    Lightweight real-time WebSocket connection for a letterbox thread.
    - Validates key against the thread on connection.
    - Broadcasts new messages in real-time.
    - Supports sending messages directly over WS as: {"content": "..."}
    - Supports ping-pong keepalive: {"type": "ping"} -> {"type": "pong"}
    """
    clean_key = key.strip()
    try:
        caller_role, participant_name = verify_thread_access(thread_id, clean_key)
    except ChatAccessError as exc:
        await websocket.close(code=1008, reason=str(exc))
        return

    await ws_manager.connect(thread_id, websocket)

    try:
        # Send handshake confirmation
        await websocket.send_text(
            json.dumps(
                {
                    "type": "connected",
                    "thread_id": thread_id,
                    "role": caller_role,
                }
            )
        )

        while True:
            text_data = await websocket.receive_text()
            try:
                data = json.loads(text_data)
            except Exception:
                continue

            msg_type = data.get("type", "message")
            if msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
                continue

            content = data.get("content", "").strip()
            if not content:
                continue

            # Encrypt and persist message
            msg_dto = post_thread_message(thread_id, clean_key, content)

            # Broadcast to all connected clients in this thread
            await ws_manager.broadcast(
                thread_id,
                {
                    "type": "new_message",
                    "message": {
                        "id": msg_dto.id,
                        "sender_role": msg_dto.sender_role,
                        "content": msg_dto.content,
                        "created_at": msg_dto.created_at,
                    },
                },
            )

    except WebSocketDisconnect:
        ws_manager.disconnect(thread_id, websocket)
    except Exception:
        ws_manager.disconnect(thread_id, websocket)
