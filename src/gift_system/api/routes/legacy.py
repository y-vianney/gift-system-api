from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ...core.models import KeyRequest, WorkerResponse, PingResponse
from ...services.santa_service import resolve_worker_name, is_system_initialized

router = APIRouter(tags=["legacy"])



@router.get("/", response_model=PingResponse)
def ping() -> PingResponse:
    """
    Ping the API to check if it's alive.
    """

    if not is_system_initialized():
        raise HTTPException(status_code=503, detail="System not initialized")

    return PingResponse(status="ok")



@router.get("/test-view", response_class=FileResponse)
def test_view() -> FileResponse:
    """
    Serve a simple HTML page for testing the API.
    """

    return FileResponse("src/gift_system/static/index.html", media_type="text/html")


@router.post("/worker-name", response_model=WorkerResponse)
def fetch_worker_name(payload: KeyRequest):
    """
    Fetch the name of the worker associated with the given key.
    This endpoint is part of the legacy API and is maintained for backward compatibility.
    """

    key = payload.key.strip()
    result = resolve_worker_name(key)
    if not result:
        raise HTTPException(status_code=404, detail="Invalid key")

    return WorkerResponse(worker_name=result)
