"""H-9C1: Migration runner idempotency tests.

Uses a fresh in-memory SQLite DB to verify migrations are safe to run
repeatedly and correctly add missing columns.
"""

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class _TestBase(DeclarativeBase):
    pass


class _TestTable(_TestBase):
    __tablename__ = "reviews"
    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(default="pending")


@pytest.fixture
def fresh_db():
    """Create an in-memory SQLite DB with the base table but without outcome_ref columns."""
    engine = create_engine("sqlite:///:memory:")
    _TestBase.metadata.create_all(bind=engine)
    return engine


def test_migration_adds_outcome_ref_columns(fresh_db):
    """run_migrations adds outcome_ref columns when they're missing."""
    from state.db.migrations.runner import run_migrations

    with fresh_db.connect() as conn:
        run_migrations(conn)

    inspector = inspect(fresh_db)
    columns = {col["name"] for col in inspector.get_columns("reviews")}
    assert "outcome_ref_type" in columns
    assert "outcome_ref_id" in columns


def test_migration_is_idempotent(fresh_db):
    """Running migrations twice does not error."""
    from state.db.migrations.runner import run_migrations

    with fresh_db.connect() as conn:
        run_migrations(conn)  # first run
        run_migrations(conn)  # second run — should be no-op

    inspector = inspect(fresh_db)
    columns = {col["name"] for col in inspector.get_columns("reviews")}
    assert "outcome_ref_type" in columns
    assert "outcome_ref_id" in columns


def test_run_migrations_returns_count():
    """run_migrations returns the number of registered migrations."""
    from state.db.migrations.runner import run_migrations, _MIGRATIONS

    engine = create_engine("sqlite:///:memory:")
    _TestBase.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        count = run_migrations(conn)

    assert count == len(_MIGRATIONS)
    assert count >= 1
