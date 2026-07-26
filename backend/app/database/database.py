"""
Database configuration module.

Supports PostgreSQL (production) and SQLite (local development fallback).
Uses SQLAlchemy with connection pooling optimized for concurrent access.
"""

import os
import logging

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./colab.db")

# ---------------------------------------------------------------------------
# Engine configuration — adapts to the detected database dialect
# ---------------------------------------------------------------------------

_is_sqlite = DATABASE_URL.startswith("sqlite")

if _is_sqlite:
    # SQLite: single-writer, needs check_same_thread=False for FastAPI
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )

    # Enable WAL mode for better concurrent read performance on SQLite
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    logger.info("Database: using SQLite (development mode)")
else:
    # PostgreSQL: production-grade connection pooling
    engine = create_engine(
        DATABASE_URL,
        pool_size=20,           # Persistent connections in the pool
        max_overflow=10,        # Extra connections under burst load
        pool_timeout=30,        # Seconds to wait for a connection
        pool_recycle=1800,      # Recycle connections every 30 min
        pool_pre_ping=True,     # Verify connections before checkout
        echo=False,
    )
    logger.info("Database: using PostgreSQL (production mode)")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# Declarative base for ORM models
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


# ---------------------------------------------------------------------------
# Dependency for FastAPI route injection
# ---------------------------------------------------------------------------

def get_db():
    """Yield a database session, ensuring it is closed after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
