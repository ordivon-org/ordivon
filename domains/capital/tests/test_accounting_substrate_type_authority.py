"""Canonical accounting result types must not be owned by a retired DB engine."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from ordivon_capital.accounting import substrate


def test_result_types_have_one_database_independent_source() -> None:
    from ordivon_capital.accounting import postgres_ledger, sqlite_ledger

    for name in ("LedgerApplyStatus", "AccountState", "TransferState"):
        contract = getattr(substrate, name)
        assert getattr(postgres_ledger, name) is contract
        assert getattr(sqlite_ledger, name) is contract
        assert contract.__module__ == substrate.__name__


def test_postgres_backend_import_does_not_import_retired_sqlite_backend() -> None:
    isolated = r"""
import importlib.abc
import sys

class ForbidLegacyBackend(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.endswith(".sqlite_ledger"):
            raise AssertionError("PG runtime loaded the legacy SQLite backend")
        return None

sys.meta_path.insert(0, ForbidLegacyBackend())
from ordivon_capital.accounting.postgres_ledger import (
    PostgresAccountingLedger, LedgerApplyStatus,
)
assert PostgresAccountingLedger.__module__.endswith(".postgres_ledger")
assert LedgerApplyStatus.__module__.endswith(".substrate")
assert not any(name.endswith(".sqlite_ledger") for name in sys.modules)
"""
    observed = subprocess.run(
        [sys.executable, "-c", isolated],
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert observed.returncode == 0, observed.stdout + observed.stderr
