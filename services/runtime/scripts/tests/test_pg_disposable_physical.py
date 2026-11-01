"""Contract tests for disposable PG18 launcher; no installed PG service touched."""

from __future__ import annotations

import importlib.util
import os
import tempfile
import sys
import unittest
import tomllib
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "pg_disposable_physical.py"
spec = importlib.util.spec_from_file_location("pg_disposable_physical", SOURCE)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class DisposablePg18Contract(unittest.TestCase):
    def test_external_dsn_is_overridden_and_stage_removed(self) -> None:
        env = module.fixture_environment(
            {"ORDIVON_PG_TEST_DSN": "host=PRODUCTION", "ORDIVON_PG_STAGE_TEST_DSN": "stage", "EXISTING": "keep"},
            Path("/var/tmp/isolated-pg"),
            54321,
        )
        self.assertEqual(env["EXISTING"], "keep")
        self.assertEqual(
            env["ORDIVON_PG_TEST_DSN"],
            "host=/var/tmp/isolated-pg port=54321 user=postgres dbname=postgres",
        )
        self.assertNotIn("ORDIVON_PG_STAGE_TEST_DSN", env)

    @unittest.skipUnless(sys.platform == "linux", "Linux Runtime FD-backed cache only")
    def test_fd_backed_cargo_cache_survives_child_fd_closure(self) -> None:
        with tempfile.TemporaryDirectory() as location:
            fd = os.open(location, os.O_RDONLY | os.O_DIRECTORY)
            try:
                env = module.fixture_environment(
                    {"CARGO_TARGET_DIR": f"/proc/self/fd/{fd}"},
                    Path("/var/tmp/isolated-pg"),
                    54321,
                )
                self.assertEqual(Path(env["CARGO_TARGET_DIR"]), Path(location).resolve())
                self.assertTrue(Path(env["CARGO_TARGET_DIR"]).is_dir())
            finally:
                os.close(fd)

    def test_direct_cargo_invocation_reuses_native_owner_contract(self) -> None:
        config = tomllib.loads((SOURCE.parents[1] / "mise.toml").read_text())
        owner_run = config["tasks"]["test:postgres-registry:physical"]["run"]
        for token in module.CARGO_ARGS:
            if token == "test":
                continue
            self.assertIn(token, owner_run)
        self.assertIn("printenv ORDIVON_PG_TEST_DSN", owner_run)

    def test_positive_execution_receipts_reject_vacuous_green(self) -> None:
        lines = [f"test pg_admission::live_pg_tests::pg18_case_{i} ... ok" for i in range(module.EXPECTED_PG18)]
        good = "\n".join(lines) + "\ntest result: ok. 18 passed; 0 failed; 0 ignored;"
        self.assertEqual(module.exact_test_count(good), 18)
        for false_green in [
            "test result: ok. 0 passed; 0 failed; 18 ignored;",
            "test result: ok. 18 passed; 0 failed; 0 ignored;",
            good.replace("pg18_case_0 ... ok", "pg18_case_0 ... FAILED"),
            good.replace("18 passed; 0 failed", "17 passed; 1 failed"),
        ]:
            with self.subTest(false_green=false_green[-48:]):
                with self.assertRaises(ValueError):
                    module.exact_test_count(false_green)


if __name__ == "__main__":
    unittest.main()
