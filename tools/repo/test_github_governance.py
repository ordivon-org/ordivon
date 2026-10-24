#!/usr/bin/env python3
"""Repository GitHub governance acceptance must not disappear under Python -O."""
from __future__ import annotations

import json
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
script, manifest, *overrides = sys.argv[1:]
sys.path.insert(0, str(Path(script).parent))
spec = importlib.util.spec_from_file_location("github_governance_under_test", script)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.DEPENDABOT = Path(manifest)
if overrides:
    from unittest.mock import patch
    original_read_text = Path.read_text
    def source_read_text(path, *args, **kwargs):
        if path == module.ROOT / "renovate.json":
            return original_read_text(Path(overrides[0]), *args, **kwargs)
        return original_read_text(path, *args, **kwargs)
    with patch.object(Path, "read_text", source_read_text):
        raise SystemExit(module.main())
raise SystemExit(module.main())
"""


class GovernanceAcceptanceTests(unittest.TestCase):
    def run_contract(
        self,
        *,
        invalid: bool,
        optimized: bool,
        duplicate_uv: bool = False,
        renovate_override: dict | None = None,
    ) -> subprocess.CompletedProcess[str]:
        source = DEPENDABOT.read_text(encoding="utf-8")
        if invalid:
            self.assertEqual(source.count("version: 2"), 1)
            source = source.replace("version: 2", "version: 9", 1)
        if duplicate_uv:
            source += (
                "\n  - package-ecosystem: uv\n"
                '    directory: "/"\n'
                "    schedule:\n      interval: weekly\n"
            )
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "dependabot.yml"
            manifest.write_text(source, encoding="utf-8")
            override_file = Path(directory) / "renovate.json"
            if renovate_override is not None:
                override_file.write_text(json.dumps(renovate_override), encoding="utf-8")
            return subprocess.run(
                [
                    sys.executable,
                    *(["-O"] if optimized else []),
                    "-c",
                    VERIFY,
                    str(SCRIPT),
                    str(manifest),
                    *([str(override_file)] if renovate_override is not None else []),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=35,
                check=False,
            )

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

    def test_historical_uv_lock_update_authority_failures_remain_rejected(self) -> None:
        """Local-only 2eaaf11f: prove the current Renovate owner rejects three real drift modes."""
        baseline = json.loads((ROOT / "renovate.json").read_text(encoding="utf-8"))
        valid = self.run_contract(invalid=False, optimized=False)
        self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)

        def mutated(field: str, value: object) -> dict:
            copy = json.loads(json.dumps(baseline))
            copy[field] = value
            return copy

        fault_cases = (
            ("missing_pep621", mutated("enabledManagers", []), "Renovate must own Python PEP 621"),
            ("lock_maintenance_off", mutated("lockFileMaintenance", {"enabled": False}), "Renovate must refresh uv.lock"),
            ("automerge_without_owner_cdc", mutated("automerge", True), "Python dependency upgrades require consumer verification"),
        )
        for name, override, marker in fault_cases:
            with self.subTest(name=name):
                result = self.run_contract(
                    invalid=False, optimized=False, renovate_override=override
                )
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn(marker, result.stderr)

        duplicate = self.run_contract(
            invalid=False, optimized=False, duplicate_uv=True
        )
        self.assertNotEqual(duplicate.returncode, 0, duplicate.stdout + duplicate.stderr)
        self.assertIn("Dependabot uv duplicates Renovate pep621 ownership", duplicate.stderr)

    def test_optimized_mode_refuses_assert_based_governance_verification(self) -> None:
        result = self.run_contract(invalid=False, optimized=True)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("optimized Python", result.stderr)


if __name__ == "__main__":
    unittest.main()
