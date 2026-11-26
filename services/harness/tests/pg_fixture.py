"""Real isolated PG Store for behavioral tests, never a production fallback."""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager, ExitStack
import os
import unittest

from psycopg import sql

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

    def persisted_sentinel_hits(self, sentinels: tuple[str, ...]) -> list[tuple[str, str, str]]:
        """Inspect every logical table cell in this test's PG schema.

        This is a logical durable-row check, not a WAL, physical page,
        backup, log, or server-wide privacy claim.
        """
        hits = []
        with self.connect() as store, store.connection.transaction():
            store.connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
            tables = store.connection.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema=%s AND table_type='BASE TABLE' ORDER BY table_name",
                (self.schema,),
            ).fetchall()
            if not tables:
                raise AssertionError("PG privacy test has no durable tables")
            for table in tables:
                name = table["table_name"]
                rows = store.connection.execute(
                    sql.SQL("SELECT * FROM {}.{}").format(sql.Identifier(self.schema), sql.Identifier(name))
                )
                for row in rows:
                    for column, value in row.items():
                        raw = bytes(value) if isinstance(value, (bytes, bytearray, memoryview)) else str(value).encode()
                        for sentinel in sentinels:
                            if sentinel.encode() in raw:
                                hits.append((name, column, sentinel))
        return hits


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
