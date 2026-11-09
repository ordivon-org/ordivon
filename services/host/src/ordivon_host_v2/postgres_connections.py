"""Narrow Host PG session adapter: native Psycopg connections or native pool checkouts.

The host database remains one authority; this class creates no own transaction
or data state. Pool lifecycle is owned by the MCP process, never by a tool.
"""
from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool


class HostPostgresConnections:
    def __init__(self, dsn: str, *, pool: ConnectionPool | None = None) -> None:
        self.dsn = dsn
        self._pool = pool

    def _connect(self) -> AbstractContextManager[psycopg.Connection[dict[str, Any]]]:
        if self._pool is not None:
            return self._pool.connection()
        return psycopg.connect(self.dsn, row_factory=dict_row)
