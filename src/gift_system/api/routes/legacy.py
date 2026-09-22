from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ...core.models import KeyRequest, WorkerResponse
from ...services.santa_service import resolve_worker_name

router = APIRouter(tags=["legacy"])


@router.get("/")
def ping() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/worker-name", response_model=WorkerResponse)
def fetch_worker_name(payload: KeyRequest):
    key = payload.key.strip()
    result = resolve_worker_name(key)
    if not result:
        raise HTTPException(status_code=404, detail="Invalid key")

    return WorkerResponse(worker_name=result)
