#!/usr/bin/env python3
"""Repository GitHub governance acceptance must not disappear under Python -O."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/repo/check_github_governance.py"
DEPENDABOT = ROOT / ".github/dependabot.yml"

VERIFY = """
import importlib.util
import sys
from pathlib import Path
script, manifest = sys.argv[1:]
sys.path.insert(0, str(Path(script).parent))
spec = importlib.util.spec_from_file_location("github_governance_under_test", script)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.DEPENDABOT = Path(manifest)
raise SystemExit(module.main())
"""


class GovernanceAcceptanceTests(unittest.TestCase):
    def run_contract(self, *, invalid: bool, optimized: bool) -> subprocess.CompletedProcess[str]:
        source = DEPENDABOT.read_text(encoding="utf-8")
        if invalid:
            self.assertEqual(source.count("version: 2"), 1)
            source = source.replace("version: 2", "version: 9", 1)
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "dependabot.yml"
            manifest.write_text(source, encoding="utf-8")
            return subprocess.run(
                [
                    sys.executable,
                    *(["-O"] if optimized else []),
                    "-c",
                    VERIFY,
                    str(SCRIPT),
                    str(manifest),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=35,
                check=False,
            )

    def test_uv_lock_governance_rejects_historical_update_owner_faults(self) -> None:
        # Recover the distinct historical negative consumer from local Main,
        # without restoring its old provider implementation or source cut.
        import copy
        import importlib.util
        import json

        import yaml

        sys.path.insert(0, str(SCRIPT.parent))
        spec = importlib.util.spec_from_file_location("repo_github_governance", SCRIPT)
        assert spec and spec.loader
        checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checker)
        base_dependabot = yaml.safe_load(DEPENDABOT.read_text(encoding="utf-8"))
        base_renovate = json.loads((ROOT / "renovate.json").read_text(encoding="utf-8"))
        self.assertTrue(checker.validate_uv_lock_renovate(base_dependabot, base_renovate))

        for name in ("missing_pep621", "duplicate_uv_owner", "lock_maintenance_off", "unsafe_lock_automerge"):
            with self.subTest(name=name):
                dependabot = copy.deepcopy(base_dependabot)
                renovate = copy.deepcopy(base_renovate)
                if name == "missing_pep621":
                    renovate["enabledManagers"].remove("pep621")
                elif name == "duplicate_uv_owner":
                    dependabot["updates"].append({"package-ecosystem": "uv", "directory": "/"})
                elif name == "lock_maintenance_off":
                    renovate["lockFileMaintenance"]["enabled"] = False
                else:
                    renovate["lockFileMaintenance"]["automerge"] = True
                with self.assertRaises(AssertionError):
                    checker.validate_uv_lock_renovate(dependabot, renovate)

    def test_valid_manifest_is_accepted_in_normal_mode(self) -> None:
        result = self.run_contract(invalid=False, optimized=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_invalid_manifest_is_rejected_in_both_modes(self) -> None:
        for optimized in (False, True):
            with self.subTest(optimized=optimized):
                result = self.run_contract(invalid=True, optimized=optimized)
                self.assertNotEqual(
                    result.returncode,
                    0,
                    f"invalid Dependabot schema was accepted (optimized={optimized}): "
                    + result.stdout + result.stderr,
                )

    def test_optimized_mode_refuses_assert_based_governance_verification(self) -> None:
        result = self.run_contract(invalid=False, optimized=True)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("optimized Python", result.stderr)


if __name__ == "__main__":
    unittest.main()
