"""Isolated real-PostgreSQL Harness test schema, never a production DB selector."""

from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import unittest
import uuid

import psycopg
from psycopg import sql

from ordivon_harness.postgres_store import PostgresHarnessStore
from ordivon_harness.agent_run import HarnessAgentRun


@contextmanager
def isolated_harness_schema():
    dsn = os.environ.get("HARNESS_PG_TEST_DSN")
    if not dsn:
        raise unittest.SkipTest("HARNESS_PG_TEST_DSN real PostgreSQL test authority is absent")
    # These unique test schemas are created from scratch and destroyed at teardown.
    schema = "hpg_test_" + uuid.uuid4().hex[:20]
    with PostgresHarnessStore(dsn, schema=schema, initialize=True):
        pass
    try:
        yield dsn, schema
    finally:
        with psycopg.connect(dsn, autocommit=True) as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


class PostgresAgentRunCase:
    """Test-only adaptation of historical root-shaped cases to the PG public API."""

    def set_up_pg(self) -> None:
        manager = isolated_harness_schema()
        self.pg_dsn, self.pg_schema = manager.__enter__()
        self.addCleanup(manager.__exit__, None, None, None)

    def create_pg(self, _historical_root: Path, contract, adapter_factory, **options):
        return HarnessAgentRun.create(
            self.pg_dsn, self.pg_schema, contract, adapter_factory, **options
        )

    def open_pg(self, _historical_root: Path, harness_run_id, adapter_factory, **options):
        return HarnessAgentRun.open(
            self.pg_dsn, self.pg_schema, harness_run_id, adapter_factory, **options
        )
