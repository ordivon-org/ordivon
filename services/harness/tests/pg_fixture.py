"""Real isolated PG Store for behavioral tests, never a production fallback."""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import os
import unittest

from ordivon_harness.postgres_store import PostgresHarnessStore
from scripts.harness_acceptance_pg import isolated_acceptance_schema


@contextmanager
def pg_test_store() -> Iterator[PostgresHarnessStore]:
    dsn = os.environ.get("HARNESS_PG_TEST_DSN", "").strip()
    if not dsn:
        raise unittest.SkipTest("dedicated PostgreSQL test database required")
    with (
        isolated_acceptance_schema(dsn, purpose="behavior") as schema,
        PostgresHarnessStore(dsn, schema=schema, initialize=True) as store,
    ):
        yield store
