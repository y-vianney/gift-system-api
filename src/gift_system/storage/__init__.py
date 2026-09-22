"""Storage package: SQLite database initialization and repository operations."""

from .database import get_db_connection, init_db
from .repository import GiftRepository

__all__ = ["get_db_connection", "init_db", "GiftRepository"]
