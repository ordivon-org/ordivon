"""Contract tests for disposable PG18 launcher; no installed PG service touched."""

from __future__ import annotations

import importlib.util
import os
import tempfile
import sys
import unittest
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

    def test_pg18_extended_owner_inventory_is_not_a_stale_literal_count(self) -> None:
        names = [
            *[f"pg_admission::live_pg_tests::pg18_case_{i}" for i in range(22)],
            "pg_windows_evidence::qualified_pg18_preflight_tests::native_check",
        ]
        listing = "\n".join(f"{name}: test" for name in names) + "\n23 tests, 0 benchmarks\n"
        expected = module.listed_pg18_tests(listing)
        self.assertEqual(expected, frozenset(names))
        completed = (
            "\n".join(f"test {name} ... ok" for name in names) + "\ntest result: ok. 23 passed; 0 failed; 0 ignored;"
        )
        self.assertEqual(module.exact_test_count(completed, expected), 23)

    def test_positive_execution_receipts_reject_vacuous_green(self) -> None:
        expected = frozenset(
            (
                "pg_admission::live_pg_tests::pg18_transaction",
                "pg_windows_evidence::qualified_pg18_preflight_tests::preflight",
            )
        )
        good = (
            "\n".join(f"test {name} ... ok" for name in sorted(expected))
            + "\ntest result: ok. 2 passed; 0 failed; 0 ignored;"
        )
        self.assertEqual(module.exact_test_count(good, expected), 2)
        for false_green in (
            "test result: ok. 0 passed; 0 failed; 2 ignored;",
            "test result: ok. 2 passed; 0 failed; 0 ignored;",
            good.replace("pg18_transaction ... ok", "pg18_transaction ... FAILED"),
            good.replace("2 passed; 0 failed", "1 passed; 1 failed"),
            good.replace("pg18_transaction ... ok", "pg18_mismatched ... ok"),
            good + "\ntest pg_admission::live_pg_tests::pg18_transaction ... ok",
        ):
            with self.subTest(false_green=false_green[-48:]):
                with self.assertRaises(ValueError):
                    module.exact_test_count(false_green, expected)

    def test_single_witness_accepts_moved_module_but_not_changed_execution(self) -> None:
        for identity in (module.WINDOWS_PG_WITNESS_CASE, module.STAGE_CASE):
            for namespace in ("old_module", "new_pg_core::physical"):
                name = f"{namespace}::{identity}"
                expected = module.listed_single_case(f"{name}: test", identity)
                evidence = f"test {name} ... ok\ntest result: ok. 1 passed; 0 failed; 0 ignored;"
                self.assertEqual(module.exact_test_count(evidence, expected), 1)
                for bad in (
                    "test result: ok. 0 passed; 0 failed; 0 ignored;",
                    evidence.replace(name, f"other_module::{identity}"),
                    evidence.replace("... ok", "... FAILED"),
                    evidence + "\ntest result: ok. 0 passed; 0 failed; 0 ignored;",
                ):
                    with self.subTest(identity=identity, output=bad):
                        with self.assertRaises(ValueError):
                            module.exact_test_count(bad, expected)
            for invalid in ("0 tests, 0 benchmarks", f"{identity}_suffix: test",
                            f"a::{identity}: test\nb::{identity}: test"):
                with self.subTest(identity=identity, inventory=invalid):
                    with self.assertRaises(ValueError):
                        module.listed_single_case(invalid, identity)

    def test_inventory_admits_renamed_and_new_native_cases_but_separates_other_lanes(self) -> None:
        original = "pg_admission::live_pg_tests::pg18_existing"
        renamed = "runtime::recovery::native_postgres_current_identity"
        new = "new_module::native_claim_consumer"
        excluded = [f"moved_module::{name}" for name in module.SEPARATE_LANES]
        listing = "\n".join(f"{name}: test" for name in [original, renamed, new, *excluded])
        self.assertEqual(module.listed_pg18_tests(listing), {original, renamed, new})
        for source in (
            "0 tests, 0 benchmarks\n",
            f"{original}: test\n{original}: test\n",
            "\n".join(f"{name}: test" for name in excluded),
            listing + f"\nother::{module.STAGE_CASE}: test",
        ):
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    module.listed_pg18_tests(source)


if __name__ == "__main__":
    unittest.main()
