"""Shared disposable schema lifecycle for actual Harness acceptance consumers.

Each invocation owns exactly one freshly created test schema. No production
DSN fallback, separate persistence authority, or deletion of an existing schema.
"""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import uuid

import psycopg
from psycopg import sql


@contextmanager
def isolated_acceptance_schema(dsn: str, *, purpose: str) -> Iterator[str]:
    """Create and drop only a fresh owned schema in an explicit test database."""
    if not dsn or not dsn.strip():
        raise ValueError("HARNESS_PG_TEST_DSN is required for PostgreSQL Harness acceptance")
    if purpose not in {"scale", "edit", "behavior"}:
        raise ValueError("unknown Harness acceptance purpose")
    schema = f"hpg_{purpose}_" + uuid.uuid4().hex
    with psycopg.connect(dsn, autocommit=True) as connection:
        # No IF NOT EXISTS: a pre-existing schema is not ours to remove.
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    try:
        yield schema
    finally:
        with psycopg.connect(dsn, autocommit=True) as connection:
            connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
