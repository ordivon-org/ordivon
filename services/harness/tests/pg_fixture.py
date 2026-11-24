"""Real isolated PG Store for behavioral tests, never a production fallback."""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager, ExitStack
import os
import unittest

from ordivon_harness.postgres_store import PostgresHarnessStore
from scripts.harness_acceptance_pg import isolated_acceptance_schema


class PgTestSchema:
    """One test-owned schema; close/reopen uses distinct original PG connections."""

    def __init__(self, dsn: str, schema: str, connections: ExitStack) -> None:
        self.dsn = dsn
        self.schema = schema
        self._connections = connections

    def connect(self, *, initialize: bool = False) -> PostgresHarnessStore:
        """Return an independently owned connection for an explicit with block."""
        return PostgresHarnessStore(self.dsn, schema=self.schema, initialize=initialize)

    def open(self, *, initialize: bool = False) -> PostgresHarnessStore:
        return self._connections.enter_context(self.connect(initialize=initialize))


@contextmanager
def pg_test_schema() -> Iterator[PgTestSchema]:
    dsn = os.environ.get("HARNESS_PG_TEST_DSN", "").strip()
    if not dsn:
        raise unittest.SkipTest("dedicated PostgreSQL test database required")
    with (
        isolated_acceptance_schema(dsn, purpose="behavior") as schema,
        ExitStack() as connections,
    ):
        yield PgTestSchema(dsn, schema, connections)


@contextmanager
def pg_test_store() -> Iterator[PostgresHarnessStore]:
    with pg_test_schema() as database:
        yield database.open(initialize=True)
