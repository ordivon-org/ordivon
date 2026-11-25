"""Test-only admission of provisioner-owned disposable PostgreSQL databases.

The caller must create a fresh database and its lease marker independently.
This module never creates or marks databases. A marker is an accidental-target
guard, not authority against a malicious privileged database administrator.
"""

from __future__ import annotations

import re
from collections.abc import Mapping

import psycopg
from psycopg.conninfo import conninfo_to_dict

DSN_NAMES = ("ORDIVON_CAPITAL_PG_TEST_DSN", "ORDIVON_CAPITAL_PAPER_PG_TEST_DSN")
LEASE = "ORDIVON_CAPITAL_TEST_LEASE"
PREFIX = "ordivon-capital-test:v1:"
_ALLOWED = {"host", "port", "dbname", "user", "password", "connect_timeout"}
_AMBIENT = ("PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE", "PGOPTIONS", "PGPORT")


class LeaseError(ValueError):
    """Unqualified native test target; deliberately no DSN or token in messages."""


def targets(env: Mapping[str, str]) -> tuple[tuple[str, dict[str, str]], ...]:
    names = [name for name in DSN_NAMES if name in env]
    if not names:
        return ()
    token = env.get(LEASE, "")
    if not re.fullmatch(r"[0-9a-f]{64}", token):
        raise LeaseError("explicit provisioner-issued disposable PostgreSQL lease required")
    if any(env.get(key) for key in _AMBIENT):
        raise LeaseError("ambiguous ambient libpq configuration")
    result = []
    for name in names:
        try:
            params = conninfo_to_dict(env[name])
        except psycopg.Error, ValueError, TypeError:
            raise LeaseError(f"{name}: invalid explicit test connection") from None
        host = params.get("host", "")
        dbname = params.get("dbname", "")
        user = params.get("user", "")
        port = params.get("port", "5432")
        timeout = params.get("connect_timeout", "5")
        if (
            set(params) - _ALLOWED
            or not (host in ("127.0.0.1", "::1") or host.startswith("/"))
            or "," in host
            or any(ch.isspace() for ch in host)
            or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,62}", dbname)
            or dbname in ("postgres", "template0", "template1")
            or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,62}", user)
            or not re.fullmatch(r"[0-9]{1,5}", port)
            or not 1 <= int(port) <= 65535
            or not re.fullmatch(r"[0-9]{1,2}", timeout)
            or not 1 <= int(timeout) <= 30
        ):
            raise LeaseError(f"{name}: ambiguous or nonlocal test connection")
        result.append((name, params))
    return tuple(result)


def verify_leases(env: Mapping[str, str]) -> tuple[tuple[str, int], ...]:
    """Read actual database marker before test collection; no target writes."""
    selected = targets(env)
    observed = {}
    qualified = []
    for name, params in selected:
        key = tuple(sorted(params.items()))
        if key not in observed:
            try:
                with (
                    psycopg.connect(
                        **(params | {"connect_timeout": params.get("connect_timeout", "5")}),
                        autocommit=True,
                    ) as db,
                    db.transaction(),
                ):
                    db.execute("SET TRANSACTION READ ONLY")
                    row = db.execute(
                        "SELECT pg_catalog.current_database(), current_user, d.oid, "
                        "pg_catalog.shobj_description(d.oid, 'pg_database'), "
                        "pg_catalog.pg_is_in_recovery() "
                        "FROM pg_catalog.pg_database AS d "
                        "WHERE d.datname=pg_catalog.current_database()"
                    ).fetchone()
            except psycopg.Error, OSError, ValueError:
                raise LeaseError(f"{name}: disposable PostgreSQL readback unavailable") from None
            expected = PREFIX + env[LEASE] + ":" + params["dbname"]
            if (
                row is None
                or row[0] != params["dbname"]
                or row[1] != params["user"]
                or row[3] != expected
                or row[4] is not False
            ):
                raise LeaseError(f"{name}: disposable PostgreSQL lease mismatch")
            observed[key] = row[2]
        qualified.append((name, observed[key]))
    return tuple(qualified)
