from __future__ import annotations

import os

import psycopg
import pytest

from ordivon_host_v2 import HostV2


@pytest.fixture(scope="session")
def host_test_db_ready() -> None:
    """Qualify the real Host database only for selected DB-test consumers."""
    dsn = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")
    if not dsn:
        pytest.skip("ORDIVON_HOST_V2_TEST_DSN not set")
    try:
        # Bind an explicit timeout so an unavailable DSN does not hang a test session.
        HostV2(psycopg.conninfo.make_conninfo(dsn, connect_timeout=5)).initialize()
    except (RuntimeError, psycopg.Error) as error:
        pytest.exit(f"HOST_TEST_DB_PREFLIGHT_FAILED: {error}", returncode=4)
