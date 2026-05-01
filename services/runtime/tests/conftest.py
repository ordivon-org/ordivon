"""pytest configuration.

Ordivon tests (product/governance/finance) do not require a database.
Legacy PFIOS tests (contracts/integration/e2e) require PFIOS_DB_URL
and set it in their own conftest or via explicit env var.
"""

import os


def pytest_configure(config):
    """Legacy PFIOS test infrastructure — scoped to PFIOS test paths only."""
    test_path = config.invocation_params.args if hasattr(config, "invocation_params") else []
    path_str = " ".join(str(p) for p in test_path)
    if any(kw in path_str for kw in ("tests/contracts", "tests/integration", "tests/e2e")):
        if "PFIOS_DB_URL" not in os.environ:
            os.environ["PFIOS_DB_URL"] = "duckdb:///:memory:"
