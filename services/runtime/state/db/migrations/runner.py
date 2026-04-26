"""Idempotent migration runner.

Each migration is a function that receives a SQLAlchemy connection
and performs its changes only if they haven't been applied yet.
"""

from __future__ import annotations

from sqlalchemy import Connection, text

# ── Migration registry ──────────────────────────────────────────────────
# Ordered list of (migration_id, migration_fn).  Each fn is idempotent.

_MIGRATIONS: list[tuple[str, object]] = []


def migration(migration_id: str):
    """Decorator: register an idempotent migration function."""
    def decorator(fn):
        _MIGRATIONS.append((migration_id, fn))
        return fn
    return decorator


# ── H9C1-001: Add outcome_ref columns to reviews table ──────────────────

@migration("h9c1_001_add_outcome_ref_columns")
def add_outcome_ref_columns(conn: Connection) -> None:
    """Add outcome_ref_type and outcome_ref_id to reviews table.

    These columns exist in ReviewORM but may be missing from existing
    PostgreSQL databases that were created before the ORM change.
    """
    conn.execute(text(
        "ALTER TABLE reviews "
        "ADD COLUMN IF NOT EXISTS outcome_ref_type VARCHAR(64)"
    ))
    conn.execute(text(
        "ALTER TABLE reviews "
        "ADD COLUMN IF NOT EXISTS outcome_ref_id VARCHAR(64)"
    ))
    conn.commit()


# ── Runner ─────────────────────────────────────────────────────────────

def run_migrations(conn: Connection) -> int:
    """Execute all registered migrations in order.

    Each migration is idempotent — safe to run repeatedly.

    Returns the number of migrations executed.
    """
    count = 0
    for _migration_id, fn in _MIGRATIONS:
        fn(conn)
        count += 1
    return count
