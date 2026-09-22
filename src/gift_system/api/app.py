from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from .routes import auth_router, chat_router, legacy_router

UI_INDEX = Path(__file__).resolve().parent.parent / "ui" / "index.html"

app = FastAPI(
    title="Gift System API",
    version="2.0.0",
    description="Professional Secret Santa Assignment & Anonymous Letterbox API",
)

# CORS Configuration
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
    Serve the modern web UI for browser requests (Accept: text/html),
    or return standard health status JSON for API clients.
    """
    accept = request.headers.get("accept", "")
    if "text/html" in accept and UI_INDEX.exists():
        return FileResponse(UI_INDEX, media_type="text/html")
    return JSONResponse({"status": "ok", "app": "Gift System", "version": "2.0.0"})


@app.get("/app", include_in_schema=False)
def app_ui():
    """Direct route for web application UI."""
    if UI_INDEX.exists():
        return FileResponse(UI_INDEX, media_type="text/html")
    return JSONResponse({"error": "UI not found"}, status_code=404)


# Include modular routers
app.include_router(legacy_router)
app.include_router(auth_router)
app.include_router(chat_router)
