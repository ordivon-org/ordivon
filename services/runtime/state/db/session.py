"""Database session management for Ordivon.

Reads PFIOS_DB_URL from environment (or .env).
Supports PostgreSQL (primary), DuckDB (analytics/fallback), and SQLite (dev/test).
"""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _load_dotenv() -> None:
    """Load .env from repo root if present and vars not already set."""
    if os.environ.get("ORDIVON_DB_URL") or os.environ.get("PFIOS_DB_URL"):
        return
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = val


_load_dotenv()

DATABASE_URL = os.environ.get("ORDIVON_DB_URL") or os.environ.get("PFIOS_DB_URL") or ""
ENGINE_KWARGS: dict = {}

if DATABASE_URL and DATABASE_URL.startswith("postgresql"):
    # PostgreSQL: connection pooling for production
    ENGINE_KWARGS = {
        "pool_size": int(os.environ.get("PFIOS_DB_POOL_SIZE", "5")),
        "max_overflow": int(os.environ.get("PFIOS_DB_MAX_OVERFLOW", "10")),
        "pool_pre_ping": True,
    }
elif DATABASE_URL and DATABASE_URL.startswith("duckdb"):
    # DuckDB: analytics/fallback
    ENGINE_KWARGS = {"connect_args": {"read_only": False}}
elif not DATABASE_URL:
    # SQLite fallback for dev/test when no DB configured
    db_path = Path(os.environ.get("PFIOS_SQLITE_PATH", "./data/ordivon.sqlite"))
    db_path = db_path if db_path.is_absolute() else Path(__file__).resolve().parents[2] / db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    DATABASE_URL = f"sqlite:///{db_path}"
    ENGINE_KWARGS = {"connect_args": {"check_same_thread": False}}

engine = create_engine(DATABASE_URL, **ENGINE_KWARGS, echo=False)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
