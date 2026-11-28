from __future__ import annotations

import inspect
from pathlib import Path
import unittest

from ordivon_harness.ordivon.run_store_port import (
    HarnessRunContinuityStore,
)
from ordivon_harness.ordivon.run_continuity import EventSourcedRunContinuity
from ordivon_harness.postgres_store import PostgresHarnessStore
from tests.pg_test_support import isolated_harness_schema
from tests.test_p0_sqlite_provider_store import MutableClock, contract

ROOT = Path(__file__).resolve().parents[1] / "src" / "ordivon_harness"


class HarnessRunStorePortTests(unittest.TestCase):
    def test_port_and_current_store_do_not_import_host(self) -> None:
        for relative in (
            "ordivon/run_store_port.py",
            "ordivon/run_continuity.py",
        ):
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("ordivon_host", source)
            self.assertNotIn("_host_compat", source)
            self.assertNotIn("HostHarnessRunStore", source)

    def test_postgres_store_supplies_every_port_operation(self) -> None:
        required = {
            name
            for name, value in HarnessRunContinuityStore.__dict__.items()
            if name not in {"__module__", "__doc__", "__parameters__"}
            and (callable(value) or isinstance(value, property))
            and not name.startswith("_")
        }
        missing = sorted(
            name
            for name in required - {"harness_run_id"}
            if not hasattr(EventSourcedRunContinuity, name)
        )
        self.assertEqual(missing, [])
        with isolated_harness_schema() as (dsn, schema):
            run_contract = contract()
            with PostgresHarnessStore(dsn, schema=schema) as store:
                store.create_run(run_contract)
                continuity = EventSourcedRunContinuity(
                    store, run_contract, clock_ms=MutableClock()
                )
                self.assertIsInstance(continuity, HarnessRunContinuityStore)

    def test_runtime_bridge_contract_depends_on_port_not_concrete_host_store(self) -> None:
        source = (ROOT / "ordivon" / "runtime_bridge.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("HostHarnessRunStore", source)
        annotation = inspect.signature(
            EventSourcedRunContinuity.__init__
        ).parameters["contract"].annotation
        self.assertTrue(annotation)


if __name__ == "__main__":
    unittest.main()
