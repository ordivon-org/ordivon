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

    def test_root_ci_does_not_install_unselected_owners(self) -> None:
        """Root mechanics must not fetch Nextest/Godot for Repo-only PRs."""
        import yaml

        workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
        steps = workflow["jobs"]["root-verification"]["steps"]
        by_name = {step["name"]: step for step in steps}
        setup = by_name["Install monorepo toolchain"]
        self.assertIs(setup["with"]["install"], False)
        root_install = by_name["Install root verification tools"]["run"]
        self.assertEqual(root_install.strip(), "set -euo pipefail\nmise install")
        self.assertNotIn("--monorepo", root_install)
        names = [step["name"] for step in steps]
        self.assertLess(names.index("Install root verification tools"), names.index("Repository mechanics"))
        self.assertLess(names.index("Repository mechanics"), names.index("Select affected owners"))
        self.assertLess(names.index("Select affected owners"), names.index("Verify affected owners"))

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
        """Local-only 2eaaf11f: prove the current Renovate owner rejects historical drift modes."""
        baseline = json.loads((ROOT / "renovate.json").read_text(encoding="utf-8"))
        valid = self.run_contract(invalid=False, optimized=False)
        self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)

        def mutated(field: str, value: object) -> dict:
            copy = json.loads(json.dumps(baseline))
            copy[field] = value
            return copy

        fault_cases = (
            ("missing_pep621", mutated("enabledManagers", []), "Renovate must own Python PEP 621"),
            (
                "missing_mise",
                mutated("enabledManagers", ["pep621"]),
                "Renovate must own Mise toolchain",
            ),
            (
                "duplicate_npm_manager",
                mutated("enabledManagers", ["pep621", "mise", "npm"]),
                "Renovate must not duplicate Dependabot",
            ),
            ("lock_maintenance_off", mutated("lockFileMaintenance", {"enabled": False}), "Renovate must refresh uv.lock"),
            ("automerge_without_owner_cdc", mutated("automerge", True), "Python dependency upgrades require consumer verification"),
            (
                "lock_maintenance_automerge_without_cdc",
                mutated("lockFileMaintenance", {"enabled": True, "automerge": True}),
                "Renovate uv.lock maintenance must not bypass consumer verification",
            ),
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

    def test_native_git_path_inventory_keeps_newlines_and_non_utf8_bytes(self) -> None:
        """Git file identity is NUL-delimited bytes, not display lines."""
        import importlib.util
        import os
        from unittest import mock

        sys.path.insert(0, str(SCRIPT.parent))
        spec = importlib.util.spec_from_file_location("governance_git_bytes_test", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        governance = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(governance)

        with tempfile.TemporaryDirectory() as folder:
            repo = Path(folder)
            subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
            unusual = ["apps/newline\nin-path/Cargo.lock"]
            if os.name != "nt":
                unusual.append(os.fsdecode(b"apps/nonutf8-\xff/Cargo.lock"))
            for name in unusual:
                path = repo / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("lock", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "--all"], check=True)
            with mock.patch.object(governance, "ROOT", repo):
                self.assertEqual(
                    set(governance.tracked("**/Cargo.lock")),
                    set(unusual),
                )
                self.assertEqual(
                    governance.dirs_for_lock("**/Cargo.lock", "Cargo.lock"),
                    {"/" + str(Path(path).parent) for path in unusual},
                )

    def test_local_composite_action_cannot_escape_sha_pin_authority(self) -> None:
        """Reproduce the historic local-only composite Action nested-uses bypass."""
        import importlib.util
        from unittest import mock

        sys.path.insert(0, str(SCRIPT.parent))
        spec = importlib.util.spec_from_file_location("governance_action_test", SCRIPT)
        assert spec is not None and spec.loader is not None
        governance = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(governance)
        with tempfile.TemporaryDirectory() as directory:
            action = Path(directory) / "action.yml"
            action.write_text(
                "name: nested\nruns:\n  using: composite\n  steps:\n"
                "    - uses: actions/checkout@v7\n", encoding="utf-8"
            )
            rglob_original = Path.rglob

            def source_action_files(folder: Path, pattern: str):
                if folder == ROOT / ".github" / "actions":
                    return iter([action]) if pattern == "action.yml" else iter([])
                return rglob_original(folder, pattern)

            with mock.patch.object(Path, "rglob", source_action_files):
                with self.assertRaisesRegex(AssertionError, "non-SHA action references"):
                    governance.main()
                action.write_text(
                    "name: nested\nruns:\n  using: composite\n  steps:\n"
                    "    - uses: actions/checkout@" + "f" * 40 + "\n"
                    "    - uses: $/.github/actions/another\n",
                    encoding="utf-8",
                )
                self.assertEqual(governance.main(), 0)

    def test_optimized_mode_refuses_assert_based_governance_verification(self) -> None:
        result = self.run_contract(invalid=False, optimized=True)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("optimized Python", result.stderr)


    def test_explicit_codeowner_rules_target_existing_sources(self) -> None:
        """Literal root CODEOWNERS overrides must have real current consumers."""
        source = (ROOT / ".github/CODEOWNERS").read_text(encoding="utf-8")
        for line in source.splitlines():
            raw = line.strip()
            if not raw or raw.startswith("#"):
                continue
            pattern = raw.split()[0]
            if not pattern.startswith("/") or any(c in pattern for c in "*?[]"):
                continue
            with self.subTest(pattern=pattern):
                self.assertTrue(
                    (ROOT / pattern.lstrip("/")).exists(),
                    f"orphan CODEOWNERS rule: {pattern}",
                )


if __name__ == "__main__":
    unittest.main()
