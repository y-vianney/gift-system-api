"""API Routes for Gift System."""

from .auth import router as auth_router
from .chat import router as chat_router
from .legacy import router as legacy_router

__all__ = ["auth_router", "chat_router", "legacy_router"]
