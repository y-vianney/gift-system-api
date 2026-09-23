from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from .routes import auth_router, chat_router, legacy_router

UI_INDEX = Path(__file__).resolve().parent.parent / "ui" / "index.html"
ROOT = Path(__file__).resolve().parents[3]
EMPLOYEES_FILE = ROOT / "data" / "employees.txt"

app = FastAPI(
    title="Gift System API",
    version="2.0.0",
    description="secret santa assignment & anonymous letterbox API",
)

# cors configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
def index_or_ping(request: Request):
    """
    serve the modern web UI for browser requests (Accept: text/html),
    or return standard health status JSON for API clients
    """
    accept = request.headers.get("accept", "")
    if "text/html" in accept and UI_INDEX.exists():
        return FileResponse(UI_INDEX, media_type="text/html")
    return JSONResponse({ "status": "ok", "app": "Gift System", "version": "2.0.0" })


@app.get("/app", include_in_schema=False)
def app_ui():
    """direct route for web application UI"""
    if UI_INDEX.exists():
        return FileResponse(UI_INDEX, media_type="text/html")
    return JSONResponse({"error": "UI not found"}, status_code=404)


@app.post("/init", include_in_schema=False)
def init_app():
    """direct route for app config init"""

    if EMPLOYEES_FILE.exists():
        try:
            from ..cli import run_build
            run_build(EMPLOYEES_FILE, send_emails=True, log_keys=True, force=True)

            return { "ok": True }
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc),
            )


app.include_router(legacy_router)
app.include_router(auth_router)
app.include_router(chat_router)
