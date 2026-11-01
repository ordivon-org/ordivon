"""Source contract for non-vacuous PostgreSQL Registry physical tests."""

from pathlib import Path
import json
import re
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "crates/ordivon-runtime-core/src/pg_admission.rs"
MISE = ROOT / "mise.toml"
PLAN = ROOT / "planning/lego-plan-r1.json"
ENGINE = ROOT / "crates/ordivon-runtime-core/src/runtime"


class PgPhysicalVerificationContractTests(unittest.TestCase):
    def test_pg18_tests_are_explicitly_ignored_until_physical_task(self) -> None:
        text = SOURCE.read_text(encoding="utf-8")
        names = re.findall(r"(?m)^    fn (pg18_[A-Za-z0-9_]+)\(\)", text)
        self.assertGreaterEqual(len(names), 18)
        # All native database-dependent tests must remain opt-in, not silently skip.
        for name in names:
            pattern = (
                r'#\[test\]\s*'
                r'#\[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"\]\s*'
                + r"fn " + re.escape(name) + r"\(\)"
            )
            self.assertRegex(text, pattern)
        self.assertNotIn('let Ok(dsn) = std::env::var("ORDIVON_PG_TEST_DSN")', text)

    def test_historical_stage_test_is_a_distinct_physical_obligation(self) -> None:
        text = SOURCE.read_text(encoding="utf-8")
        self.assertRegex(
            text,
            r'#\[ignore = "requires explicit ORDIVON_PG_STAGE_TEST_DSN historical-stage qualification"\]\s*'
            r'fn historical_pg_stage_is_not_an_admission_authority\(\)',
        )
        self.assertNotIn(
            'let Ok(dsn) = std::env::var("ORDIVON_PG_STAGE_TEST_DSN")', text
        )


    def test_r19_is_partial_challenger_not_installed_backend(self) -> None:
        plan = json.loads(PLAN.read_text(encoding="utf-8"))
        r19 = next(row for row in plan["nodes"] if row["id"] == "R19")
        self.assertEqual(
            r19["authority"], "SOURCE_CHALLENGER_ONLY_NO_INSTALLED_RUNTIME_AUTHORITY"
        )
        self.assertEqual(r19["state"], "IMPLEMENTED")
        standings = {row["standing"] for row in r19["replacementCoverage"]}
        self.assertIn(
            "SOURCE_IMPLEMENTED_PHYSICAL_PG18_QUALIFICATION_REQUIRED", standings
        )
        self.assertIn("EXPLICITLY_BLOCKED", standings)
        self.assertIn("UNKNOWN_NOT_IMPLEMENTED", standings)
        self.assertIn("UNKNOWN_NOT_AUTHORIZED", standings)
        rw12 = next(row for row in plan["slices"] if row["id"] == "RW12")
        self.assertIn("R19", rw12["nodeIds"])

        # The new feature-gated PG vertical may consume PgAdmissionStore.
        # The installed legacy Registry and default MCP binary must not
        # silently switch durability ownership as a side effect of this PR.
        legacy_registry = (ENGINE / "registry.rs").read_text(encoding="utf-8")
        legacy_mcp = (
            ROOT / "crates/ordivon-runtime-mcp/src/main.rs"
        ).read_text(encoding="utf-8")
        self.assertNotIn("PgAdmissionStore", legacy_registry)
        self.assertNotIn("pg_admission::", legacy_registry)
        self.assertNotIn("PgRuntime", legacy_mcp)
        cargo = tomllib.loads(
            (ROOT / "crates/ordivon-runtime-mcp/Cargo.toml").read_text(encoding="utf-8")
        )
        pg_bin = next(row for row in cargo["bin"] if row["name"] == "ordivon-runtime-pg")
        self.assertEqual(pg_bin["required-features"], ["postgres-runtime"])
        self.assertIn("postgres-runtime", cargo["features"])

    def test_disposable_pg_launcher_is_explicit_and_does_not_replace_required_dsn_gate(self) -> None:
        data = tomllib.loads(MISE.read_text(encoding="utf-8"))
        launcher = data["tasks"]["test:postgres-registry:disposable"]["run"]
        self.assertEqual(launcher, "python scripts/pg_disposable_physical.py")
        self.assertIn("test:postgres-registry:physical", data["tasks"])

    def test_mise_has_fail_closed_physical_and_stage_tasks(self) -> None:
        data = tomllib.loads(MISE.read_text(encoding="utf-8"))
        physical = data["tasks"]["test:postgres-registry:physical"]["run"]
        stage = data["tasks"]["test:postgres-registry:stage"]["run"]
        self.assertIn("printenv ORDIVON_PG_TEST_DSN", physical)
        self.assertIn("pg18_", physical)
        self.assertIn("--ignored", physical)
        self.assertIn("printenv ORDIVON_PG_STAGE_TEST_DSN", stage)
        self.assertIn("historical_pg_stage_is_not_an_admission_authority", stage)
        self.assertIn("--ignored", stage)


if __name__ == "__main__":
    unittest.main()
