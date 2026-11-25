from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tomllib
import unittest

RUNTIME_ROOT = Path(__file__).resolve().parents[2]
TAXONOMY = RUNTIME_ROOT / "planning" / "test-taxonomy-r1.json"
POSITIVE_TEST = "nonterminal_native_transition_requires_reconciliation"
LEGACY_TEST = "public_requests_reject_unknown_fields_and_path_escape"
ZERO_MATCH_TEST = "ordivon_zero_match_probe_must_not_exist"


class FocusedVerificationContractTests(unittest.TestCase):
    def test_taxonomy_declares_fail_closed_focused_verifier(self) -> None:
        data = json.loads(TAXONOMY.read_text(encoding="utf-8"))
        contract = data["focusedVerification"]
        self.assertEqual(contract["id"], "R01-V1")
        self.assertEqual(contract["provider"], "cargo-nextest")
        self.assertEqual(contract["entrypoint"], "mise run test:focused")
        self.assertEqual(contract["selectorEnv"], "RUNTIME_TEST_EXPR")
        self.assertEqual(contract["zeroMatchStanding"], "FAIL_CLOSED")
        self.assertIn("matched(selector) >= 1", contract["formalObligation"])

    def test_nextest_source_is_official_version_matched_and_checksum_pinned(self) -> None:
        """The root CI toolchain must not require a third-party release proxy."""
        mise = tomllib.loads((RUNTIME_ROOT / "mise.toml").read_text(encoding="utf-8"))
        nextest = mise["tools"]["http:cargo-nextest"]
        version = nextest["version"]
        expected_assets = {
            "linux-x64": "x86_64-unknown-linux-gnu.tar.gz",
            "windows-x64": "x86_64-pc-windows-msvc.zip",
        }
        self.assertEqual(set(nextest["platforms"]), set(expected_assets))
        for platform, suffix in expected_assets.items():
            with self.subTest(platform=platform):
                artifact = nextest["platforms"][platform]
                expected_url = (
                    "https://github.com/nextest-rs/nextest/releases/download/"
                    f"cargo-nextest-{version}/cargo-nextest-{version}-{suffix}"
                )
                self.assertEqual(artifact["url"], expected_url)
                self.assertRegex(artifact["checksum"], r"^sha256:[0-9a-f]{64}$")
                self.assertIs(type(artifact["size"]), int)
                self.assertGreater(artifact["size"], 0)

    @staticmethod
    def run_focused(selector: str | None, profile: str | None = None) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        env.pop("RUNTIME_TEST_EXPR", None)
        env.pop("RUNTIME_TEST_PROFILE", None)
        if selector is not None:
            env["RUNTIME_TEST_EXPR"] = f"test({selector})"
        if profile is not None:
            env["RUNTIME_TEST_PROFILE"] = profile
        return subprocess.run(
            ["mise", "run", "test:focused"],
            cwd=RUNTIME_ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=120,
            close_fds=False,
        )

    def test_real_focused_entrypoint_rejects_zero_matches(self) -> None:
        result = self.run_focused(ZERO_MATCH_TEST)
        combined = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0, combined)
        self.assertIn("0 tests run", combined)
        self.assertIn("no tests to run", combined)

    def test_real_focused_entrypoint_runs_named_consumer(self) -> None:
        result = self.run_focused(None)
        combined = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, combined)
        expected = tomllib.loads((RUNTIME_ROOT / "mise.toml").read_text(encoding="utf-8"))[
            "tools"
        ]["http:cargo-nextest"]["version"]
        self.assertIn(f"qualified cargo-nextest {expected}", combined)
        self.assertIn("1 test run", combined)
        self.assertIn(POSITIVE_TEST, combined)
        self.assertIn("Runtime focused feature: postgres-registry-admission", combined)

    def test_legacy_is_explicit_and_does_not_select_pg_only_test(self) -> None:
        result = self.run_focused(POSITIVE_TEST, "legacy")
        combined = result.stdout + result.stderr
        self.assertEqual(result.returncode, 4, combined)
        self.assertIn("Runtime focused feature: transactional-runtime", combined)
        self.assertIn("0 tests run", combined)

    def test_legacy_consumer_still_runs(self) -> None:
        result = self.run_focused(LEGACY_TEST, "legacy")
        combined = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, combined)
        self.assertIn("Runtime focused feature: transactional-runtime", combined)
        self.assertIn("1 test run", combined)
        self.assertIn(LEGACY_TEST, combined)

    def test_archive_profile_runs_real_integration_binary(self) -> None:
        result = self.run_focused(None, "archive")
        combined = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, combined)
        self.assertIn("Runtime focused feature: operator-tools", combined)
        for name in ("migrated_unknown_recovery_cannot_become_absent",
                     "real_migration_archive_refinement"):
            self.assertIn(name, combined)

    def test_archive_profile_does_not_select_legacy_library_consumer(self) -> None:
        result = self.run_focused(LEGACY_TEST, "archive")
        combined = result.stdout + result.stderr
        self.assertEqual(result.returncode, 4, combined)
        self.assertIn("0 tests run", combined)

    def test_unknown_profile_fails_before_test_execution(self) -> None:
        result = self.run_focused(None, "typo")
        combined = result.stdout + result.stderr
        self.assertEqual(result.returncode, 2, combined)
        self.assertIn("Invalid RUNTIME_TEST_PROFILE", combined)


if __name__ == "__main__":
    unittest.main()
