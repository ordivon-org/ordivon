from __future__ import annotations

import psycopg

from .health.diagnostics import HostStatusQueries

REQUIRED_SCHEMA_VERSION = 15


class HostV2(HostStatusQueries):
    """Public Host façade: database schema readiness plus inherited read-only status."""

    required_schema_version = REQUIRED_SCHEMA_VERSION

    def initialize(self) -> None:
        """Verify that Alembic already initialized the authority schema.

        Schema creation and migration are deliberately not owned by the running Host service.
        Production and tests must run ``alembic upgrade head`` before Host opens authority.
        """
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT schema_version FROM host_v2_schema WHERE singleton"
                ).fetchone()
        except psycopg.errors.UndefinedTable as exc:
            raise RuntimeError(
                "Host v2 schema is not initialized; run alembic upgrade head"
            ) from exc
        if row is None or int(row["schema_version"]) != REQUIRED_SCHEMA_VERSION:
            observed = None if row is None else int(row["schema_version"])
            raise RuntimeError(
                f"Host v2 schema is not at required version {REQUIRED_SCHEMA_VERSION} (observed={observed}); "
                "run alembic upgrade head"
            )
