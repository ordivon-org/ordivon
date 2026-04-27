"""Idempotent migration runner.

Each migration is a function that receives a SQLAlchemy connection
and performs its changes only if they haven't been applied yet.
"""

from __future__ import annotations

from sqlalchemy import Connection, inspect, text

# ── Migration registry ──────────────────────────────────────────────────
# Ordered list of (migration_id, migration_fn).  Each fn is idempotent.

_MIGRATIONS: list[tuple[str, object]] = []


def migration(migration_id: str):
    """Decorator: register an idempotent migration function."""

    def decorator(fn):
        _MIGRATIONS.append((migration_id, fn))
        return fn

    return decorator


def _column_exists(conn: Connection, table: str, column: str) -> bool:
    """Check whether a column exists on the given table.

    Uses SQLAlchemy's DB-agnostic inspector.
    """
    inspector = inspect(conn)
    try:
        existing = {col["name"] for col in inspector.get_columns(table)}
    except Exception:
        # Table might not exist at all — let create_all handle that case.
        return False
    return column in existing


def _add_column_if_missing(conn: Connection, table: str, column: str, col_type: str) -> None:
    """Add a column to a table if it doesn't already exist.

    The inspector-based check is not reliable across all backends
    (e.g. DuckDB).  We try the ALTER TABLE and ignore "already exists"
    errors so the migration stays truly idempotent.
    """
    if not _column_exists(conn, table, column):
        try:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
            conn.commit()
        except Exception:
            # Column already exists (or table missing) — idempotent skip.
            conn.rollback()


# ── H9C1-001: Add outcome_ref columns to reviews table ──────────────────


@migration("h9c1_001_add_outcome_ref_columns")
def add_outcome_ref_columns(conn: Connection) -> None:
    """Add outcome_ref_type and outcome_ref_id to reviews table.

    These columns exist in ReviewORM but may be missing from existing
    PostgreSQL databases that were created before the ORM change.
    """
    _add_column_if_missing(conn, "reviews", "outcome_ref_type", "VARCHAR(64)")
    _add_column_if_missing(conn, "reviews", "outcome_ref_id", "VARCHAR(64)")


# ── WB-001: Add lesson_ids + source_refs columns to candidate_rules ────


@migration("wb_001_add_candidate_rule_lesson_and_source_refs")
def add_candidate_rule_lesson_and_source_refs(conn: Connection) -> None:
    """Add lesson_ids_json and source_refs_json to candidate_rules table.

    Wave B introduced Lesson → CandidateRule draft extraction.
    These columns store the lesson IDs and structured source references.
    """
    _add_column_if_missing(conn, "candidate_rules", "lesson_ids_json", "TEXT DEFAULT '[]'")
    _add_column_if_missing(conn, "candidate_rules", "source_refs_json", "TEXT DEFAULT '[]'")


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
