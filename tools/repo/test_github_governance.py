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

    def test_release_policy_uses_exact_runtime_rust_toolchain(self) -> None:
        """Release dependency policy must use the checked consumer Rust compiler."""
        import tomllib
        import yaml

        toolchain = tomllib.loads(
            (ROOT / "services/runtime/rust-toolchain.toml").read_text()
        )["toolchain"]["channel"]
        root = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
        release = yaml.safe_load(
            (ROOT / ".github/workflows/runtime-release.yml").read_text()
        )
        for workflow, job in ((root, "root-verification"),
                              (release, "runtime-release")):
            steps = workflow["jobs"][job]["steps"]
            matches = [step for step in steps
                       if step.get("uses", "").startswith("EmbarkStudios/cargo-deny-action@")]
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0]["with"]["rust-version"], toolchain)

    def test_runtime_release_attestations_verify_every_subject_and_fail_closed(self) -> None:
        """Exercise official verifier CLI orchestration, not cryptographic trust."""
        import os
        import yaml

        doc = yaml.safe_load((ROOT / ".github/workflows/runtime-release.yml").read_text())
        steps = doc["jobs"]["runtime-release"]["steps"]
        names = [step["name"] for step in steps]
        title = "Verify signed canonical Runtime release attestations"
        self.assertIn(title, names)
        self.assertLess(names.index("Attest canonical Runtime release SPDX SBOM"), names.index(title))
        self.assertLess(names.index(title), names.index("Retain canonical Runtime release evidence"))
        step = steps[names.index(title)]
        self.assertEqual(step["env"]["GH_TOKEN"], "$" + "{{ github.token }}")
        source_sha = "a" * 40
        run = step["run"].replace("$" + "{{ steps.release.outputs.repository_commit }}", source_sha)
        self.assertIn("set -euo pipefail", run)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stage = root / "ordivon-runtime-tagged-release" / "attest-subjects"
            stage.mkdir(parents=True)
            for i in range(12):
                (stage / f"component-{i:02d}").write_bytes(bytes([i]))
            bindir = root / "bin"
            bindir.mkdir()
            verifier = bindir / "gh"
            verifier.write_text(
                "#!/usr/bin/env python3\n"
                "import json, os, sys\n"
                "args = sys.argv[1:]\n"
                "with open(os.environ['GH_VERIFY_LOG'],'a',encoding='utf8') as f:\n"
                " f.write(json.dumps(args)+'\\n')\n"
                "if args[:2] != ['attestation','verify']: sys.exit(90)\n"
                "if '--predicate-type' in args and os.getenv('REJECT_SBOM')=='yes' "
                "and 'https://spdx.dev/Document/v2.3' in args: sys.exit(91)\n",
                encoding="utf-8",
            )
            verifier.chmod(0o755)
            env = dict(os.environ)
            env.update(
                RUNNER_TEMP=str(root), GITHUB_REPOSITORY="ordivon-org/ordivon",
                GITHUB_REF="refs/tags/runtime-v0.1.0", GITHUB_REF_NAME="runtime-v0.1.0",
                GH_VERIFY_LOG=str(root / "verified.jsonl"),
                PATH=str(bindir) + os.pathsep + env["PATH"],
            )
            command = ["bash", "-c", run]
            result = subprocess.run(command, cwd=ROOT, env=env, text=True,
                                    capture_output=True, timeout=25, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            calls = [
                json.loads(line) for line in Path(env["GH_VERIFY_LOG"])
                .read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(len(calls), 24)
            targets = {str(path) for path in stage.iterdir()}
            for predicate in ("https://slsa.dev/provenance/v1", "https://spdx.dev/Document/v2.3"):
                matches = [x for x in calls if x[x.index("--predicate-type")+1] == predicate]
                self.assertEqual({x[2] for x in matches}, targets)
                for argv in matches:
                    self.assertEqual(argv[argv.index("--source-digest")+1], source_sha)
                    self.assertEqual(argv[argv.index("--source-ref")+1], env["GITHUB_REF"])
                    self.assertEqual(
                        argv[argv.index("--signer-workflow")+1],
                        "ordivon-org/ordivon/.github/workflows/runtime-release.yml",
                    )
            env["REJECT_SBOM"] = "yes"
            failed = subprocess.run(command, cwd=ROOT, env=env, text=True,
                                    capture_output=True, timeout=25, check=False)
            self.assertNotEqual(failed.returncode, 0, "bad SBOM admitted as releasable")

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


    def test_codeowners_explicit_root_rules_cannot_be_comments_prefixes_or_ownerless(
        self,
    ) -> None:
        """GitHub ignores comments and a later rule can erase explicit ownership."""
        import importlib.util

        sys.path.insert(0, str(SCRIPT.parent))
        spec = importlib.util.spec_from_file_location(
            "github_codeowner_native_gate", SCRIPT
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        governance = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(governance)

        canonical = (ROOT / ".github/CODEOWNERS").read_text(encoding="utf-8")
        rule = "/services/runtime/ @zycxfyh"
        self.assertEqual(canonical.count(rule), 1)
        defects = {
            "commented_only": "# " + rule,
            "prefix_impersonator": "/services/runtime/impersonator/ @zycxfyh",
            "ownerless": "/services/runtime/",
            "later_ownerless_override": rule + "\n/services/runtime/",
            "later_unowned_catchall": rule + "\n*",
            # GitHub will not load any CODEOWNERS file at/above its 3 MB
            # limit, regardless of whether its visible root rules are valid.
            "oversized_ignored_by_github": rule + "\n# " + ("x" * 3_000_000),
        }
        with tempfile.TemporaryDirectory() as folder:
            relocated = Path(folder) / "CODEOWNERS"
            governance.CODEOWNERS = relocated
            for name, replacement in defects.items():
                with self.subTest(name=name):
                    relocated.write_text(
                        canonical.replace(rule, replacement), encoding="utf-8"
                    )
                    with self.assertRaisesRegex(AssertionError, "CODEOWNERS"):
                        governance.main()

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
