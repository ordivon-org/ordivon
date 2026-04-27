"""pytest configuration — auto-detect test database.

Sets PFIOS_DB_URL to duckdb:///:memory: as the default for all tests,
so unit tests can run without PostgreSQL via Docker Compose.

To run with PostgreSQL, set PFIOS_DB_URL explicitly:
    PFIOS_DB_URL=postgresql://pfios:pfios@127.0.0.1:5432/pfios_test uv run pytest

The explicit env var always takes precedence over this default.
"""

import os


def pytest_configure(config):
    """Set test database default before any test runs."""
    if "PFIOS_DB_URL" not in os.environ:
        os.environ["PFIOS_DB_URL"] = "duckdb:///:memory:"
