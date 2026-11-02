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


# Exact finite Formal receipt acceptance fixture for the existing GitHub consumer.
# This models the expected checker output, not a real mathematical proof.
_FORMAL_SOURCE_FILES = (
    "mise.toml", "tools/formal/mise.toml", "tools/formal/verify.py",
    "tools/formal/RecursiveLegoRefinement.lean",
    "tools/formal/RecursiveLegoVariationFrame.lean",
    "tools/formal/Proof.rs", "tools/formal/Proof.dfy",
    "tools/formal/ProofKani.rs", "tools/formal/Proof.qnt",
    "tools/formal/Proof.als",
    "services/harness/src/ordivon_harness/plugin_gateway_effect.py",
)
_FORMAL_PROBE_ORACLES = (
    ("Lean kernel R2.1 relational composition", 0),
    ("Lean kernel qualified variation frame and countermodels", 0),
    ("Lean rejects false theorem", 1),
    ("Z3: sat", 0), ("Z3: unsat", 0),
    ("cvc5: sat", 0), ("cvc5: unsat", 0),
    ("Verus Rust proof", 0), ("Verus rejects false postcondition", 1),
    ("Dafny method proof", 0), ("Dafny rejects false postcondition", 4),
    ("Kani native Rust bounded proof", 0),
    ("Kani rejects reachable assertion failure", 1),
    ("Quint typed state machine", 0),
    ("Quint rejects type error", 1),
    ("Alloy finite SAT model", 0),
)
_FORMAL_TOOLS = ("lean", "z3", "cvc5", "verus", "dafny", "kani", "quint", "alloy")

def _qualified_formal_test_receipt(
    checkout: Path, source_cut: str, fake_bin_dir: Path
) -> dict:
    """Positive fake-checker protocol fixture; never a proof or trusted result."""
    import hashlib
    fake_bin_dir.mkdir(parents=True, exist_ok=True)
    fixture_binaries = {}
    for name in _FORMAL_TOOLS:
        executable = fake_bin_dir / name
        executable.write_bytes(("fixture executable: " + name).encode("utf-8"))
        executable.chmod(0o700)
        fixture_binaries[name] = {
            "path": str(executable.resolve(strict=True)), "version": "fixture",
            "sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
        }
    sources = {
        rel: subprocess.check_output(
            ["git", "--no-replace-objects", "-C", str(checkout), "rev-parse",
             "HEAD:" + rel], text=True,
        ).strip()
        for rel in _FORMAL_SOURCE_FILES
    }
    # Real Alloy's launcher uses an application JAR and a bundled JVM.
    # These are separate executable inputs, not contained in the ELF SHA.
    resource_paths = {
        "alloyAppJar": fake_bin_dir.parent / "lib/app/org.alloytools.alloy.dist.jar",
        "alloyJvm": fake_bin_dir.parent / "lib/runtime/lib/server/libjvm.so",
    }
    resource_records = {}
    for name, resource in resource_paths.items():
        resource.parent.mkdir(parents=True, exist_ok=True)
        resource.write_bytes(("fixture Alloy dependency: " + name).encode("utf-8"))
        resource_records[name] = {
            "path": str(resource.resolve(strict=True)),
            "sha256": hashlib.sha256(resource.read_bytes()).hexdigest(),
        }
    return {
        "kind": "source-scoped-native-formal-toolchain-check",
        "status": "PASS", "sourceCut": source_cut,
        "gitObjectFormat": "sha1",
        "sourceQualification": "EXACT_GIT_BLOBS_CHECKED_PRE_AND_POST",
        "toolQualification": "MISE_RESOLVED_EXECUTABLE_SHA256_PRE_AND_POST",
        "toolResources": resource_records,
        "proofReuseAdmissible": False,
        "sourceFragmentRefinement": {
            "scope": "source_ast_python_option_timeout_and_gateway_projection_only",
            "producerPath": "services/harness/src/ordivon_harness/plugin_gateway_effect.py",
            "model": "OrdivonR21.TimeoutConnection.modeledBehavior",
            "sourceAstAnchorsObserved": True,
            "effectFrameObserved": "exact_post_projection_return_and_immediate_gateway_dispatch",
            "codeFragmentRefined": False,
            "sourceRefinementStanding": "UNKNOWN",
            "runtimeRustRefined": False,
            "installedCurrentness": "UNKNOWN",
        },
        "implementationRefinement": "UNKNOWN",
        "installedCurrentness": "UNKNOWN",
        "sourceBlobs": sources,
        "toolBinaries": fixture_binaries,
        "count": len(_FORMAL_PROBE_ORACLES),
        "probes": [
            {"probe": label, "result": "PASS", "rc": rc}
            for label, rc in _FORMAL_PROBE_ORACLES
        ],
    }


class MonorepoCodeQLTests(unittest.TestCase):
    def test_active_root_matrix_and_negative_falsifiers(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location("github_governance_codeql", SCRIPT)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(SCRIPT.parent))
        try:
            spec.loader.exec_module(module)
        finally:
            sys.path.pop(0)
        source = (ROOT / ".github/workflows/codeql.yml").read_text(encoding="utf-8")
        module.validate_monorepo_codeql(source)
        corruptions = (
            source.replace("python, javascript-typescript, rust", "python, javascript-typescript", 1),
            source.replace("  merge_group:\n", "  skipped_merge_group:\n", 1),
            source.replace("security-events: write", "security-events: read", 1),
            source.replace(
                "github/codeql-action/analyze@1c5b675653bb5c22dbe9b12b556ec555138e09fd",
                "github/codeql-action/analyze@v4", 1
            ),
        )
        for corrupt in corruptions:
            self.assertNotEqual(corrupt, source)
            with self.subTest(mutant=corrupt[:120]):
                with self.assertRaises(AssertionError):
                    module.validate_monorepo_codeql(corrupt)


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

    def test_formal_cold_install_reuses_scoped_github_job_token(self) -> None:
        """Native GitHub release backend must not use anonymous 60/hour API quota."""
        import yaml

        workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
        self.assertEqual(workflow["permissions"], {"contents": "read"})
        steps = {step["name"]: step for step in
                 workflow["jobs"]["root-verification"]["steps"]}
        # Only the selected Formal owner gets this token, not every arbitrary
        # unselected Owner task or the entire job.
        self.assertNotIn("env", workflow["jobs"]["root-verification"])
        formal = steps["Verify changed core Formal source"]
        self.assertEqual(formal["env"]["GITHUB_TOKEN"], "$" + "{{ github.token }}")
        self.assertIn("mise install", formal["run"])
        self.assertIn("mise run formal:verify", formal["run"])
        self.assertNotIn("GITHUB_TOKEN", steps["Verify affected owners"].get("env", {}))

    def test_selected_formal_has_one_isolated_real_invocation_and_owner_failures_propagate(self) -> None:
        """Execute the real GitHub queue shell and dedicated Formal step."""
        import os
        import yaml

        workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
        steps = {step["name"]: step for step in workflow["jobs"]["root-verification"]["steps"]}
        selected = steps["Verify affected owners"]["run"]
        formal_step = steps["Verify changed core Formal source"]
        self.assertEqual(formal_step["if"], "steps.affected.outputs.formal == 'true'")
        self.assertIn("KANI_HOME", formal_step["env"])
        self.assertIn("mise run formal:verify", formal_step["run"])
        interpolation = "$" + "{{ steps.affected.outputs.formal }}"
        self.assertIn(interpolation, selected)

        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            (folder / "bin").mkdir()
            fake = folder / "bin/mise"
            fake.write_text(
                '#!/usr/bin/env bash\n'
                'if [[ "$1" == --cd && "$3" == config && "$4" == ls ]]; then '
                'exec "$MISE_NATIVE_FOR_CONFIG" "$@"; fi\n'
                'if [[ "$1" == which ]]; then\n'
                '  if [[ "$2" == --version && -f "$FORMAL_FAKE_BINARY_DIR/$3" ]]; then\n'
                '    printf "fixture\\n"; exit 0; fi\n'
                '  if [[ -f "$FORMAL_FAKE_BINARY_DIR/$2" ]]; then\n'
                '    printf "%s\\n" "$FORMAL_FAKE_BINARY_DIR/$2"; exit 0; fi\n'
                '  exit 44; fi\n'
                'printf "%s\\n" "$*" >> "$MISE_RECORD"\n'
                'if [[ "$1" == run && "$2" == runtime:verify && '
                '"$' + '{MOCK_FAIL_RUNTIME:-0}" == 1 ]]; then exit 37; fi\n'
                'if [[ "$1" == run && "$2" == formal:verify && '
                '"$' + '{MOCK_FAIL_FORMAL:-0}" == 1 ]]; then exit 41; fi\n',
                encoding="utf-8",
            )
            fake.chmod(0o755)
            # The real CI installs pinned Verus rustup tooling. Tests must
            # not mutate the host toolchain or download from the network.
            fake_rustup = folder / "bin/rustup"
            fake_rustup.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            fake_rustup.chmod(0o755)
            with fake.open("a", encoding="utf-8") as script:
                script.write(
                    'if [[ "$1" == run && "$2" == formal:verify ]]; then '
                    'cat "$FORMAL_MOCK_RECEIPT"; fi\n'
                )
            report_path = folder / "formal-fixture.json"
            report_path.write_text(json.dumps(_qualified_formal_test_receipt(
                ROOT, subprocess.check_output(
                    ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True,
                ).strip(), folder / "fake-formal-tool-binaries",
            )), encoding="utf-8")
            tasks = folder / "ordivon-affected-tasks.txt"
            log = folder / "mise.log"
            env = os.environ.copy()
            import shutil
            env["MISE_NATIVE_FOR_CONFIG"] = shutil.which("mise") or "/usr/bin/mise"
            env["MISE_TRUSTED_CONFIG_PATHS"] = str(ROOT)
            env.update({
                "RUNNER_TEMP": str(folder),
                "MISE_RECORD": str(log),
                "FORMAL_MOCK_RECEIPT": str(report_path),
                "FORMAL_FAKE_BINARY_DIR": str(folder / "fake-formal-tool-binaries"),
                "PATH": str(folder / "bin") + os.pathsep + env.get("PATH", ""),
            })

            def actual_queue(
                items: list[str], *, formal: str, failed_owner: bool = False
            ) -> subprocess.CompletedProcess[str]:
                tasks.write_text("\n".join(items) + "\n", encoding="utf-8")
                log.write_text("", encoding="utf-8")
                run_env = dict(env)
                run_env["MOCK_FAIL_RUNTIME"] = "1" if failed_owner else "0"
                return subprocess.run(
                    ["/usr/bin/bash", "-c", selected.replace(interpolation, formal)],
                    cwd=ROOT, env=run_env, capture_output=True, text=True,
                    timeout=14, check=False,
                )

            ok = actual_queue(
                ["runtime:verify", "formal:verify", "host:queue"], formal="true",
            )
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertEqual(
                log.read_text().splitlines(), ["run runtime:verify", "run host:queue"]
            )
            dedicated = subprocess.run(
                ["/usr/bin/bash", "-c", formal_step["run"]],
                cwd=ROOT, env=env, capture_output=True, text=True,
                timeout=14, check=False,
            )
            self.assertEqual(dedicated.returncode, 0, dedicated.stderr)
            self.assertEqual(
                log.read_text().splitlines(),
                ["run runtime:verify", "run host:queue",
                 "install", "run formal:verify"],
            )

            # A plausible subset, duplicate probe, or fabricated membership
            # is NOT a successful complete Formal verification receipt.
            full_report = json.loads(report_path.read_text(encoding="utf-8"))
            import copy
            invalid_receipts = {}
            partial = copy.deepcopy(full_report)
            partial["probes"] = partial["probes"][:1]
            partial["count"] = 1
            invalid_receipts["one-pass-subset"] = json.dumps(partial)
            duplicate = copy.deepcopy(full_report)
            duplicate["probes"][1] = copy.deepcopy(duplicate["probes"][0])
            invalid_receipts["duplicate-probe-identity"] = json.dumps(duplicate)
            missing_negative = copy.deepcopy(full_report)
            missing_negative["probes"] = [
                x for x in missing_negative["probes"]
                if "rejects" not in x["probe"]
            ]
            missing_negative["count"] = len(missing_negative["probes"])
            invalid_receipts["no-negative-oracles"] = json.dumps(missing_negative)
            wrong_rc = copy.deepcopy(full_report)
            next(x for x in wrong_rc["probes"]
                 if x["probe"] == "Lean rejects false theorem")["rc"] = 0
            invalid_receipts["falsifier-incorrect-return"] = json.dumps(wrong_rc)
            no_sources = copy.deepcopy(full_report)
            no_sources.pop("sourceBlobs")
            invalid_receipts["no-source-blob-membership"] = json.dumps(no_sources)
            no_fragment = copy.deepcopy(full_report)
            no_fragment.pop("sourceFragmentRefinement")
            invalid_receipts["missing-executable-fragment-evidence"] = json.dumps(no_fragment)
            forged_fragment = copy.deepcopy(full_report)
            forged_fragment["sourceFragmentRefinement"]["runtimeRustRefined"] = True
            invalid_receipts["forged-rust-refinement-claim"] = json.dumps(forged_fragment)
            forged_code_grade = copy.deepcopy(full_report)
            forged_code_grade["sourceFragmentRefinement"]["codeFragmentRefined"] = True
            invalid_receipts["unearned-python-code-refinement"] = json.dumps(forged_code_grade)
            no_effect_frame = copy.deepcopy(full_report)
            del no_effect_frame["sourceFragmentRefinement"]["effectFrameObserved"]
            invalid_receipts["missing-effect-frame-evidence"] = json.dumps(no_effect_frame)
            forged_effect_frame = copy.deepcopy(full_report)
            forged_effect_frame["sourceFragmentRefinement"]["effectFrameObserved"] = "implementation_proven"
            invalid_receipts["forged-effect-frame-evidence"] = json.dumps(forged_effect_frame)
            no_tools = copy.deepcopy(full_report)
            no_tools.pop("toolBinaries")
            invalid_receipts["no-eight-tool-witnesses"] = json.dumps(no_tools)
            absent_resources = copy.deepcopy(full_report)
            absent_resources.pop("toolResources")
            invalid_receipts["no-alloy-runtime-resources"] = json.dumps(absent_resources)
            missing_jar = copy.deepcopy(full_report)
            missing_jar["toolResources"].pop("alloyAppJar")
            invalid_receipts["alloy-app-jar-omitted"] = json.dumps(missing_jar)
            wrong_jar = copy.deepcopy(full_report)
            wrong_jar["toolResources"]["alloyAppJar"]["sha256"] = "0" * 64
            invalid_receipts["alloy-app-jar-wrong-digest"] = json.dumps(wrong_jar)
            wrong_jvm = copy.deepcopy(full_report)
            wrong_jvm["toolResources"]["alloyJvm"]["sha256"] = "0" * 64
            invalid_receipts["alloy-jvm-wrong-digest"] = json.dumps(wrong_jvm)
            foreign_jar = copy.deepcopy(full_report)
            foreign_jar["toolResources"]["alloyAppJar"] = copy.deepcopy(
                foreign_jar["toolResources"]["alloyJvm"]
            )
            invalid_receipts["alloy-jar-valid-hash-foreign-path"] = json.dumps(foreign_jar)
            # The Formal mathematical model cannot grant implementation
            # refinement or actual installed effect acceptance. A checker that
            # claims PASS for either must fail this consumer's admission, even
            # if all 16 real mathematical probes pass.
            for field in ("implementationRefinement", "installedCurrentness"):
                unearned = copy.deepcopy(full_report)
                unearned[field] = "PASS"
                invalid_receipts[f"unearned-{field}-PASS"] = json.dumps(unearned)
                missing_grade = copy.deepcopy(full_report)
                del missing_grade[field]
                invalid_receipts[f"missing-{field}"] = json.dumps(missing_grade)
            both_promoted = copy.deepcopy(full_report)
            both_promoted["implementationRefinement"] = "PASS"
            both_promoted["installedCurrentness"] = "PASS"
            invalid_receipts["both-grades-unearned"] = json.dumps(both_promoted)
            forged_blob = copy.deepcopy(full_report)
            forged_blob["sourceBlobs"]["tools/formal/Proof.qnt"] = "0" * 40
            invalid_receipts["fake-proof-source-blob"] = json.dumps(forged_blob)
            invalid_receipts["duplicate-JSON-kind"] = (
                '{"kind":"incorrect",' + json.dumps(full_report)[1:]
            )
            for index in range(len(full_report["probes"])):
                missing = copy.deepcopy(full_report)
                del missing["probes"][index]
                missing["count"] = len(missing["probes"])
                invalid_receipts[f"required-probe-omitted-{index}"] = json.dumps(missing)
            for relative in full_report["sourceBlobs"]:
                incomplete = copy.deepcopy(full_report)
                del incomplete["sourceBlobs"][relative]
                invalid_receipts[f"source-blob-omitted-{relative}"] = json.dumps(incomplete)
            for name in full_report["toolBinaries"]:
                incomplete = copy.deepcopy(full_report)
                del incomplete["toolBinaries"][name]
                invalid_receipts[f"tool-binary-omitted-{name}"] = json.dumps(incomplete)
            for item in full_report["probes"]:
                if "rejects" in item["probe"]:
                    invalid = copy.deepcopy(full_report)
                    target = next(
                        x for x in invalid["probes"]
                        if x["probe"] == item["probe"]
                    )
                    target["rc"] = 0
                    invalid_receipts[f"negative-oracle-accepted-{item['probe']}"] = json.dumps(invalid)
            unexpected = copy.deepcopy(full_report)
            unexpected["probes"][0]["probe"] = "unrecognized proof obligation"
            invalid_receipts["unknown-probe-identity"] = json.dumps(unexpected)
            boolean_rc = copy.deepcopy(full_report)
            boolean_rc["probes"][0]["rc"] = True
            invalid_receipts["bool-accepted-as-integer-return-code"] = json.dumps(boolean_rc)
            wrong_tool_hash = copy.deepcopy(full_report)
            wrong_tool_hash["toolBinaries"]["lean"]["sha256"] = "Z" * 64
            invalid_receipts["tool-digest-not-hex"] = json.dumps(wrong_tool_hash)
            valid_hex_wrong_digest = copy.deepcopy(full_report)
            valid_hex_wrong_digest["toolBinaries"]["lean"]["sha256"] = "0" * 64
            invalid_receipts["tool-digest-valid-hex-but-wrong-bytes"] = json.dumps(
                valid_hex_wrong_digest
            )
            no_version = copy.deepcopy(full_report)
            no_version["toolBinaries"]["lean"]["version"] = ""
            invalid_receipts["tool-version-missing"] = json.dumps(no_version)
            wrong_version = copy.deepcopy(full_report)
            wrong_version["toolBinaries"]["lean"]["version"] = "unselected-version"
            invalid_receipts["tool-version-mismatch"] = json.dumps(wrong_version)
            # A valid SHA of another executable does not bind the declared
            # verifier to the Mise-selected tool that ran the proof.
            wrong_tool_identity = copy.deepcopy(full_report)
            wrong_tool_identity["toolBinaries"]["lean"] = copy.deepcopy(
                wrong_tool_identity["toolBinaries"]["z3"]
            )
            invalid_receipts["valid-digest-foreign-tool-identity"] = json.dumps(
                wrong_tool_identity
            )
            stale_cut = copy.deepcopy(full_report)
            stale_cut["sourceCut"] = "0" * len(stale_cut["sourceCut"])
            invalid_receipts["stale-source-cut"] = json.dumps(stale_cut)
            failed_receipt = copy.deepcopy(full_report)
            failed_receipt["status"] = "FAIL"
            invalid_receipts["explicit-failure"] = json.dumps(failed_receipt)
            wrong_count = copy.deepcopy(full_report)
            wrong_count["count"] += 1
            invalid_receipts["forged-count"] = json.dumps(wrong_count)
            # Two new forged/missing fragment receipts and one extra
            # source-blob omission case extend the negative corpus.
            self.assertEqual(len(invalid_receipts), 73)

            try:
                for label, payload in invalid_receipts.items():
                    with self.subTest(receipt=label):
                        report_path.write_text(payload, encoding="utf-8")
                        failed = subprocess.run(
                            ["/usr/bin/bash", "-c", formal_step["run"]],
                            cwd=ROOT, env=env, text=True, capture_output=True,
                            timeout=14, check=False,
                        )
                        self.assertNotEqual(failed.returncode, 0, label)
                        self.assertIn(
                            "Formal execution lacks a valid scoped PASS receipt",
                            failed.stderr, label,
                        )
            finally:
                report_path.write_text(
                    json.dumps(full_report), encoding="utf-8",
                )

            # A true mathematical verifier failure must remain a failing
            # GitHub required step, not an accepted projected task name.
            log.write_text("", encoding="utf-8")
            proof_failure_env = dict(env)
            proof_failure_env["MOCK_FAIL_FORMAL"] = "1"
            failed_proof = subprocess.run(
                ["/usr/bin/bash", "-c", formal_step["run"]],
                cwd=ROOT, env=proof_failure_env, capture_output=True,
                text=True, timeout=14, check=False,
            )
            self.assertEqual(failed_proof.returncode, 41)
            self.assertEqual(
                log.read_text().splitlines(),
                ["install", "run formal:verify"],
            )

            mismatch = actual_queue(["formal:verify"], formal="false")
            self.assertNotEqual(mismatch.returncode, 0)
            self.assertNotIn("run formal:verify", log.read_text())
            failure = actual_queue(
                ["runtime:verify", "formal:verify", "host:queue"],
                formal="true", failed_owner=True,
            )
            self.assertEqual(failure.returncode, 37)
            self.assertEqual(log.read_text().splitlines(), ["run runtime:verify"])
            no_formal = actual_queue(["host:queue"], formal="false")
            self.assertEqual(no_formal.returncode, 0)
            self.assertEqual(log.read_text().splitlines(), ["run host:queue"])

    def test_real_queue_rejects_modified_root_task_script_before_exec(self) -> None:
        """Native GH bash consumers must not run task code outside Git HEAD."""
        import os
        import yaml

        root = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
        steps = {
            step["name"]: step
            for step in root["jobs"]["root-verification"]["steps"]
        }
        queue_script = steps["Verify affected owners"]["run"].replace(
            "$" + "{{ steps.affected.outputs.formal }}", "true"
        )
        formal_script = steps["Verify changed core Formal source"]["run"]
        mechanics = steps["Repository mechanics"]["run"]
        for script in (queue_script, mechanics):
            self.assertIn("root task source differs from exact Git HEAD", script)
            self.assertIn("git --no-replace-objects show HEAD:mise.toml", script)
        self.assertIn("Formal executable source differs from exact Git HEAD", formal_script)
        for required in ("mise.toml", "tools/formal/mise.toml", "tools/formal/verify.py"):
            self.assertIn(required, formal_script)
        self.assertIn("Formal execution lacks a valid scoped PASS receipt", formal_script)

        with tempfile.TemporaryDirectory(prefix="ordivon-root-mise-runner-") as temp:
            work = Path(temp)
            repo = work / "git"
            repo.mkdir()
            (repo / "tools/formal").mkdir(parents=True)
            manifest = repo / "mise.toml"
            exact = b'[tasks."formal:verify"]\nrun = "echo harmless"\n'
            manifest.write_bytes(exact)
            (repo / "tools/formal/mise.toml").write_text(
                '[tasks.verify]\nrun = "python3 verify.py"\n', encoding="utf-8"
            )
            (repo / "tools/formal/verify.py").write_text(
                'print("mock")\n', encoding="utf-8"
            )
            # One actual nested Mise source is sufficient to falsify the
            # Owner runner if it only checks the root task manifest.
            (repo / "domains/game").mkdir(parents=True)
            nested_game = repo / "domains/game/mise.toml"
            nested_game.write_text(
                '[tasks.verify]\nrun = "echo harmless nested task"\n',
                encoding="utf-8",
            )
            # The real verifier consumes 10 exact source inputs; the disposable
            # Git fixture must contain the same declared source universe.
            for rel in _FORMAL_SOURCE_FILES:
                file = repo / rel
                if not file.exists():
                    file.parent.mkdir(parents=True, exist_ok=True)
                    file.write_text("source fixture\\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(
                ["git", "-C", str(repo), "config", "user.name", "Fixture"],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(repo), "config", "user.email", "fixture@local"],
                check=True,
            )
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(
                ["git", "-C", str(repo), "commit", "-qm", "source-cut"],
                check=True,
            )
            binary = work / "bin"
            binary.mkdir()
            mock = binary / "mise"
            mock.write_text(
                '#!/usr/bin/env bash\n'
                'if [[ "$1" == --cd && "$3" == config && "$4" == ls ]]; then exec "$MISE_NATIVE_FOR_CONFIG" "$@"; fi\n'
                'if [[ "$1" == which ]]; then\n'
                '  if [[ "$2" == --version && -f "$FORMAL_FAKE_BINARY_DIR/$3" ]]; then\n'
                '    printf "fixture\\n"; exit 0; fi\n'
                '  if [[ -f "$FORMAL_FAKE_BINARY_DIR/$2" ]]; then\n'
                '    printf "%s\\n" "$FORMAL_FAKE_BINARY_DIR/$2"; exit 0; fi\n'
                '  exit 44; fi\n'
                'printf "%s\\n" "$*" >> "$MISE_RECORD"\n',
                encoding="utf-8",
            )
            mock.chmod(0o755)
            fake_rustup = binary / "rustup"
            fake_rustup.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            fake_rustup.chmod(0o755)
            with mock.open("a", encoding="utf-8") as script:
                script.write(
                    'if [[ "$1" == run && "$2" == formal:verify ]]; then '
                    'cat "$FORMAL_MOCK_RECEIPT"; fi\n'
                )
            source_cut = subprocess.check_output(
                ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
            ).strip()
            report = work / "formal-fixture.json"
            example_receipt = _qualified_formal_test_receipt(
                repo, source_cut, work / "fake-formal-tool-binaries",
            )
            # A structurally valid positive fake receipt must NEVER
            # promote source AST anchors to real Python code refinement.
            self.assertIs(
                example_receipt["sourceFragmentRefinement"]["codeFragmentRefined"],
                False,
            )
            report.write_text(json.dumps(example_receipt), encoding="utf-8")
            tasks = work / "ordivon-affected-tasks.txt"
            tasks.write_text("runtime:verify\n", encoding="utf-8")
            record = work / "mise-record.txt"
            env = os.environ.copy()
            env["RUNNER_TEMP"] = str(work)
            env["MISE_RECORD"] = str(record)
            env["FORMAL_MOCK_RECEIPT"] = str(report)
            env["FORMAL_FAKE_BINARY_DIR"] = str(work / "fake-formal-tool-binaries")
            import shutil
            env["MISE_NATIVE_FOR_CONFIG"] = shutil.which("mise") or "/usr/bin/mise"
            env["MISE_TRUSTED_CONFIG_PATHS"] = str(repo)
            env.pop("GITHUB_SHA", None)
            env["PATH"] = str(binary) + os.pathsep + env.get("PATH", "")

            def invoke(script: str) -> subprocess.CompletedProcess[str]:
                record.write_text("", encoding="utf-8")
                return subprocess.run(
                    ["/usr/bin/bash", "-c", script],
                    cwd=repo, env=env, capture_output=True, text=True,
                    timeout=15, check=False,
                )

            for script, calls in (
                (queue_script, ["run runtime:verify"]),
                (formal_script, ["install", "run formal:verify"]),
            ):
                accepted = invoke(script)
                self.assertEqual(accepted.returncode, 0, accepted.stderr)
                self.assertEqual(record.read_text().splitlines(), calls)

            for mutation in ("different_bytes", "symlink_same_bytes"):
                with self.subTest(mutation=mutation):
                    if mutation == "different_bytes":
                        manifest.write_bytes(exact + b"# changed after selection\n")
                    else:
                        alternative = repo / "same-bytes.toml"
                        alternative.write_bytes(exact)
                        manifest.unlink()
                        manifest.symlink_to(alternative)
                    for script in (queue_script, formal_script):
                        rejected = invoke(script)
                        self.assertEqual(rejected.returncode, 43, rejected.stderr)
                        self.assertIn(
                            ("Formal executable source differs from exact Git HEAD"
                             if script == formal_script else
                             "root task source differs from exact Git HEAD"),
                            rejected.stderr,
                        )
                        self.assertNotIn(
                            "run ", record.read_text(),
                            "mutable task source reached the executor",
                        )
                    if manifest.is_symlink():
                        manifest.unlink()
                    manifest.write_bytes(exact)
            self.assertEqual(manifest.read_bytes(), exact)

            env["GITHUB_SHA"] = "0" * len(source_cut)
            refused = invoke(queue_script)
            self.assertEqual(refused.returncode, 43)
            self.assertIn("root task checkout differs from provider GITHUB_SHA", refused.stderr)
            self.assertEqual(record.read_text(), "")
            env.pop("GITHUB_SHA", None)

            # Source-qualify nested Owner task manifests as well as root.
            nested_bytes = nested_game.read_bytes()
            try:
                nested_game.write_bytes(nested_bytes + b"\n# changed nested source\n")
                denied_nested = invoke(queue_script)
                self.assertEqual(denied_nested.returncode, 43, denied_nested.stderr)
                self.assertIn(
                    "nested Mise task source differs from exact Git HEAD",
                    denied_nested.stderr,
                )
                self.assertEqual(record.read_text(), "")
            finally:
                nested_game.write_bytes(nested_bytes)

            # Git blob byte-equivalence is not sufficient if the actual
            # executed nested task path becomes a symbolic link or vanishes.
            identical_bytes = work / "same-nested-task.toml"
            identical_bytes.write_bytes(nested_bytes)
            for mutation in ("symlink", "missing"):
                with self.subTest(nested_task_mutation=mutation):
                    nested_game.unlink()
                    if mutation == "symlink":
                        nested_game.symlink_to(identical_bytes)
                    try:
                        rejected = invoke(queue_script)
                        self.assertEqual(rejected.returncode, 43, rejected.stderr)
                        self.assertEqual(record.read_text(), "")
                    finally:
                        if nested_game.is_symlink():
                            nested_game.unlink()
                        nested_game.write_bytes(nested_bytes)

            # Native Mise discovers higher-precedence local task overrides:
            # an UNTRACKED config must never count as Git-qualified execution.
            untracked = nested_game.with_name("mise.local.toml")
            self.assertFalse(untracked.exists())
            try:
                untracked.write_text(
                    '[tasks.verify]\nrun = "echo untracked override"\n',
                    encoding="utf-8",
                )
                denied_override = invoke(queue_script)
                self.assertEqual(denied_override.returncode, 43, denied_override.stderr)
                self.assertIn("nested Mise task source differs from exact Git HEAD",
                              denied_override.stderr)
                self.assertEqual(record.read_text(), "")
            finally:
                untracked.unlink(missing_ok=True)

            for relative in ("tools/formal/mise.toml", "tools/formal/verify.py"):
                target = repo / relative
                exact_target = target.read_bytes()
                try:
                    target.write_bytes(exact_target + b"# uncommitted checker drift\n")
                    denied = invoke(formal_script)
                    self.assertEqual(denied.returncode, 43, denied.stderr)
                    self.assertEqual(record.read_text(), "")
                finally:
                    target.write_bytes(exact_target)

            # The dedicated Formal runner also consumes native effective Mise
            # inputs, not only the Git-tracked child manifest and verify.py.
            formal_override = repo / "tools/formal/mise.local.toml"
            self.assertFalse(formal_override.exists())
            try:
                formal_override.write_text(
                    '[tasks.verify]\nrun = "echo fake proof"\n',
                    encoding="utf-8",
                )
                denied_local_formal = invoke(formal_script)
                self.assertEqual(denied_local_formal.returncode, 43,
                                 denied_local_formal.stderr)
                self.assertIn(
                    "effective Formal Mise config differs from Git HEAD",
                    denied_local_formal.stderr,
                )
                self.assertEqual(record.read_text(), "")
            finally:
                formal_override.unlink(missing_ok=True)

            before = report.read_bytes()
            try:
                for invalid in (
                    b"not-json",
                    json.dumps({
                        "kind": "source-scoped-native-formal-toolchain-check",
                        "status": "PASS",
                        "sourceCut": source_cut,
                        "sourceQualification": "EXACT_GIT_BLOBS_CHECKED_PRE_AND_POST",
                        "toolQualification": "MISE_RESOLVED_EXECUTABLE_SHA256_PRE_AND_POST",
                        "proofReuseAdmissible": True,
                        "count": 0,
                        "probes": [],
                    }).encode(),
                ):
                    report.write_bytes(invalid)
                    denied = invoke(formal_script)
                    self.assertNotEqual(denied.returncode, 0, denied.stderr)
                    self.assertIn(
                        "Formal execution lacks a valid scoped PASS receipt",
                        denied.stderr,
                    )
            finally:
                report.write_bytes(before)

    def test_actual_github_selector_qualifies_all_known_local_source_inputs(self) -> None:
        """Real GitHub selection script rejects any dirty direct producer or policy."""
        import os
        import yaml

        workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
        script = next(
            step["run"] for step in workflow["jobs"]["root-verification"]["steps"]
            if step["name"] == "Select affected owners"
        )
        selected_readset = (
            ".github/workflows/ci.yml",
            "tools/repo/convergence_plan.py",
            "tools/repo/affected_owners.py",
            "tools/repo/owners.toml",
            "tools/repo/dependency_contracts.toml",
            "mise.toml",
        )
        for path in selected_readset:
            self.assertIn(path, script)

        with tempfile.TemporaryDirectory(prefix="ordivon-selector-consumer-") as temp:
            root = Path(temp)
            clone = root / "checkout"
            subprocess.run(
                ["git", "clone", "-q", "--shared", str(ROOT), str(clone)],
                check=True, capture_output=True, text=True, timeout=35,
            )
            cut = subprocess.check_output(
                ["git", "-C", str(clone), "rev-parse", "HEAD"], text=True
            ).strip()
            env = os.environ.copy()
            env.update({
                "EVENT_NAME": "workflow_dispatch",
                "GITHUB_SHA": cut,
                "RUNNER_TEMP": str(root),
                "GITHUB_OUTPUT": str(root / "outputs"),
                "GITHUB_STEP_SUMMARY": str(root / "summary"),
                # The clone is a disposable test-only Git checkout, not a
                # globally approved config. Trust only this one native source.
                "MISE_TRUSTED_CONFIG_PATHS": str(clone),
            })

            def invoke() -> subprocess.CompletedProcess[str]:
                (root / "outputs").write_text("", encoding="utf-8")
                (root / "summary").write_text("", encoding="utf-8")
                return subprocess.run(
                    ["/usr/bin/bash", "-c", script],
                    cwd=clone, env=env, text=True, capture_output=True,
                    timeout=35, check=False,
                )

            clean = invoke()
            self.assertEqual(clean.returncode, 0, clean.stderr)
            self.assertIn("formal=true", (root / "outputs").read_text())

            for relative in selected_readset:
                with self.subTest(source=relative):
                    source = clone / relative
                    original = source.read_bytes()
                    try:
                        source.write_bytes(original + b"\n# changed by other caller\n")
                        altered = invoke()
                        self.assertEqual(altered.returncode, 43, altered.stderr)
                        self.assertIn(
                            "source selection producer differs from exact Git checkout",
                            altered.stderr,
                        )
                    finally:
                        source.write_bytes(original)

            env["GITHUB_SHA"] = "0" * len(cut)
            mismatched_provider = invoke()
            self.assertEqual(mismatched_provider.returncode, 43)
            env["GITHUB_SHA"] = cut
            self.assertEqual(invoke().returncode, 0)

    def test_capital_current_native_verify_replaces_unreachable_nested_ci(self) -> None:
        """A nested historic workflow is not GitHub Actions for this monorepo.

        Root queue selection and Capital's actual mise task are the only
        claimed source-level route; this is not a provider/live admission.
        """
        import tomllib
        import yaml

        nested = ROOT / "domains/capital/.github/workflows/ci.yml"
        self.assertFalse(nested.exists(), "obsolete nested Capital workflow persists")
        owners = tomllib.loads((ROOT / "tools/repo/owners.toml").read_text())
        rows = [x for x in owners["owners"] if x["name"] == "capital"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["root"], "domains/capital/")
        self.assertEqual(rows[0]["verify_task"], "capital:verify")
        self.assertEqual(rows[0].get("queue_verify_task", "capital:verify"), "capital:verify")

        root_tasks = tomllib.loads((ROOT / "mise.toml").read_text())["tasks"]
        route = root_tasks["capital:verify"]["run"]
        self.assertIn("cd domains/capital", route)
        self.assertIn("mise run verify", route)
        capital_mise = tomllib.loads((ROOT / "domains/capital/mise.toml").read_text())
        self.assertEqual(capital_mise["tools"]["python"], "3.15.1")
        verify = capital_mise["tasks"]["verify"]["run"]
        for check in ("uv lock --check", "uv sync --locked --group test",
                      "uv run --group test ruff check .", "pytest -m"):
            self.assertIn(check, verify)
        self.assertIn("not provider_qualification", verify)
        self.assertIn("provider_qualification",
                      capital_mise["tasks"]["verify:provider"]["run"])

        root_ci = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
        steps = root_ci["jobs"]["root-verification"]["steps"]
        selected = next(x["run"] for x in steps if x.get("name") == "Select affected owners")
        verified = next(x["run"] for x in steps if x.get("name") == "Verify affected owners")
        self.assertIn("tools/repo/convergence_plan.py", selected)
        self.assertIn("queueVerifyTasks", selected)
        self.assertIn("mise run", verified)
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/repo/affected_owners.py"),
             "--changed-file", "domains/capital/.github/workflows/ci.yml",
             "--format", "queue-tasks"],
            cwd=ROOT, capture_output=True, text=True, timeout=20, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "capital:verify")

    def test_host_queue_replaces_non_discovered_nested_host_ci(self) -> None:
        """Root GitHub Actions must consume the Host's native current queue.

        This is a source-to-CI contract, not an installed Host/service proof.
        """
        import tomllib
        import yaml

        self.assertFalse(
            (ROOT / "services/host/.github/workflows/ci.yml").exists(),
            "obsolete owner-local YAML is not discovered as a root Actions workflow"
        )
        owners = tomllib.loads((ROOT / "tools/repo/owners.toml").read_text())
        host = [o for o in owners["owners"] if o["name"] == "host"]
        self.assertEqual(len(host), 1)
        self.assertEqual(host[0]["root"], "services/host/")
        self.assertEqual(host[0]["queue_verify_task"], "host:queue")
        root = tomllib.loads((ROOT / "mise.toml").read_text())
        queue = root["tasks"]["host:queue"]["run"]
        self.assertIn("cd services/host", queue)
        self.assertIn("mise run queue", queue)
        host_mise = tomllib.loads((ROOT / "services/host/mise.toml").read_text())
        self.assertIn("tools/host_queue_verify.sh", host_mise["tasks"]["queue"]["run"])
        actual = (ROOT / "services/host/tools/host_queue_verify.sh").read_text()
        for necessary in (
            "uv lock --check", "uv sync --locked", "uv run ruff check .",
            "uv run python -m pytest", "alembic upgrade head",
            "SHOW server_version_num",
        ):
            self.assertIn(necessary, actual)
        workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
        steps = workflow["jobs"]["root-verification"]["steps"]
        selection = next(step["run"] for step in steps if
                         step.get("name") == "Select affected owners")
        verification = next(step["run"] for step in steps if
                            step.get("name") == "Verify affected owners")
        self.assertIn("tools/repo/convergence_plan.py", selection)
        self.assertIn("queueVerifyTasks", selection)
        self.assertIn("mise run", verification)
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/repo/affected_owners.py"),
             "--changed-file", "services/host/.github/workflows/ci.yml",
             "--format", "queue-tasks"],
            cwd=ROOT, capture_output=True, text=True, timeout=20, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "host:queue")

    def test_next_root_queue_replaces_non_discovered_nested_ci(self) -> None:
        """Next's root queue and root security scan replace nested CI.

        This is a repository source/CI contract, not an installed provider proof.
        """
        import tomllib
        import yaml

        nested = ROOT / "meta/next/.github/workflows/ci.yml"
        self.assertFalse(nested.exists(), "nested Next CI is not root-discovered")
        manifest = tomllib.loads((ROOT / "tools/repo/owners.toml").read_text())
        next_owners = [o for o in manifest["owners"] if o["name"] == "next"]
        self.assertEqual(len(next_owners), 1)
        self.assertEqual(next_owners[0]["root"], "meta/next/")
        self.assertEqual(next_owners[0]["verify_task"], "next:verify")
        top = tomllib.loads((ROOT / "mise.toml").read_text())
        route = top["tasks"]["next:verify"]["run"]
        for fragment in ("cd meta/next", "mise run verify", "cd experimental/episode-store-r1"):
            self.assertIn(fragment, route)
        native = tomllib.loads((ROOT / "meta/next/mise.toml").read_text())
        checks = native["tasks"]["verify"]["run"]
        for obligation in (
            "uv lock --check", "uv sync --locked",
            "uv run --locked python -m pytest",
            "uv run --locked --group quality ruff check scripts tests",
            "uv run --locked --group quality ruff format --check scripts tests",
            "scripts/check_authority_catalog_r1.py",
            "scripts/check_standard_native_enterprise_r2.py",
            "scripts/check_reasoning_waist_r1.py",
            "bandit -r scripts", "pip-audit",
        ):
            self.assertIn(obligation, checks)
        workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
        steps = workflow["jobs"]["root-verification"]["steps"]
        scripts = {step.get("name"): step.get("run", "") for step in steps}
        self.assertIn("tools/repo/convergence_plan.py", scripts["Select affected owners"])
        self.assertIn("queueVerifyTasks", scripts["Select affected owners"])
        self.assertIn('mise run "$task"', scripts["Verify affected owners"])
        self.assertIn("mise run repo:secrets:verify", scripts["Repository-wide secret scan"])
        self.assertIn(
            "tools/repo/check_tracked_secrets.sh",
            scripts["Current committed-source secret scan"],
        )
        selected = subprocess.run(
            [
                sys.executable, str(ROOT / "tools/repo/affected_owners.py"),
                "--changed-file", "meta/next/.github/workflows/ci.yml",
                "--format", "queue-tasks",
            ],
            cwd=ROOT, capture_output=True, text=True, timeout=20, check=False,
        )
        self.assertEqual(selected.returncode, 0, selected.stderr)
        self.assertEqual(selected.stdout.strip(), "next:verify")

    def test_media_root_queue_replaces_non_discovered_nested_ci(self) -> None:
        """Media's live root-queue contract supersedes its old nested CI YAML.

        This checks source/CI consumer parity, not deployed Media effect parity.
        """
        import tomllib
        import yaml

        nested = ROOT / "capabilities/media/.github/workflows/ci.yml"
        self.assertFalse(nested.exists(), "nested Media CI is not a root GitHub Action")
        self.assertFalse(
            (ROOT / "capabilities/media/.github/workflows/codeql.yml").exists(),
            "inactive Media CodeQL workflow must be retired after root CodeQL activation",
        )
        root_codeql = ROOT / ".github/workflows/codeql.yml"
        self.assertTrue(root_codeql.is_file(), "live root-loaded CodeQL is missing")
        from tools.repo.check_github_governance import validate_monorepo_codeql
        validate_monorepo_codeql(root_codeql.read_text(encoding="utf-8"))
        owners = tomllib.loads((ROOT / "tools/repo/owners.toml").read_text())
        media = [o for o in owners["owners"] if o["name"] == "media"]
        self.assertEqual(len(media), 1)
        self.assertEqual(media[0]["root"], "capabilities/media/")
        self.assertEqual(media[0]["verify_task"], "media:verify")
        top = tomllib.loads((ROOT / "mise.toml").read_text())
        route = top["tasks"]["media:verify"]["run"]
        self.assertIn("cd capabilities/media", route)
        self.assertIn("mise run verify", route)
        native = tomllib.loads((ROOT / "capabilities/media/mise.toml").read_text())
        checks = native["tasks"]["verify"]["run"]
        for requirement in (
            "pnpm install --frozen-lockfile",
            "pnpm bootstrap:python",
            ".venv/bin/ruff check .",
            "pnpm check",
            "python -m unittest discover",
            "git ls-files -z -- '*.sh' | xargs -0 -r shellcheck",
        ):
            self.assertIn(requirement, checks)
        root_ci = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
        steps = root_ci["jobs"]["root-verification"]["steps"]
        select = next(x["run"] for x in steps if x.get("name") == "Select affected owners")
        run = next(x["run"] for x in steps if x.get("name") == "Verify affected owners")
        self.assertIn("tools/repo/convergence_plan.py", select)
        self.assertIn("queueVerifyTasks", select)
        self.assertIn('mise run "$task"', run)
        selected = subprocess.run(
            [
                sys.executable, str(ROOT / "tools/repo/affected_owners.py"),
                "--changed-file", "capabilities/media/.github/workflows/ci.yml",
                "--format", "queue-tasks",
            ],
            cwd=ROOT, capture_output=True, text=True, timeout=20, check=False,
        )
        self.assertEqual(selected.returncode, 0, selected.stderr)
        self.assertEqual(selected.stdout.strip(), "media:verify")

    def test_network_shellcheck_uses_mature_root_queue_not_nested_action(self) -> None:
        """A named YAML under a component is not active root GitHub CI."""
        import tomllib
        import yaml

        nested = ROOT / "platform/network/.github/workflows/shellcheck.yml"
        self.assertFalse(nested.exists(), "redundant undiscovered ShellCheck YAML")
        manifest = tomllib.loads((ROOT / "tools/repo/owners.toml").read_text())
        network = [o for o in manifest["owners"] if o["name"] == "network"]
        self.assertEqual(len(network), 1)
        self.assertEqual(network[0]["root"], "platform/network/")
        self.assertEqual(network[0]["verify_task"], "network:ci")
        root_mise = tomllib.loads((ROOT / "mise.toml").read_text())
        queue = root_mise["tasks"]["network:ci"]["run"]
        self.assertIn("cd platform/network", queue)
        self.assertIn("mise run ci", queue)
        native = tomllib.loads((ROOT / "platform/network/mise.toml").read_text())
        self.assertEqual(native["tools"]["shellcheck"], root_mise["tools"]["shellcheck"])
        checks = native["tasks"]["ci"]["run"]
        self.assertIn("git ls-files -z -- '*.sh' | xargs -0 shellcheck", checks)
        self.assertIn("python -m pytest", checks)
        root_ci = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
        steps = root_ci["jobs"]["root-verification"]["steps"]
        selected = next(x["run"] for x in steps if x.get("name") == "Select affected owners")
        verified = next(x["run"] for x in steps if x.get("name") == "Verify affected owners")
        self.assertIn("tools/repo/convergence_plan.py", selected)
        self.assertIn("queueVerifyTasks", selected)
        self.assertIn('mise run "$task"', verified)
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/repo/affected_owners.py"),
             "--changed-file", "platform/network/.github/workflows/shellcheck.yml",
             "--format", "queue-tasks"],
            cwd=ROOT, capture_output=True, text=True, timeout=20, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "network:ci")
    def test_distribution_queue_replaces_non_discovered_nested_ci(self) -> None:
        """GitHub root workflow invokes the Distribution's native current verification."""
        import tomllib
        import yaml

        legacy = "capabilities/distribution/.github/workflows/ci.yml"
        self.assertFalse((ROOT / legacy).exists(),
                         "old nested CI is not an active GitHub Actions workflow")
        registered = tomllib.loads((ROOT / "tools/repo/owners.toml").read_text())
        distribution = [o for o in registered["owners"] if o["name"] == "distribution"]
        self.assertEqual(len(distribution), 1)
        self.assertEqual(distribution[0]["root"], "capabilities/distribution/")
        self.assertEqual(distribution[0]["verify_task"], "distribution:verify")
        root_tasks = tomllib.loads((ROOT / "mise.toml").read_text())["tasks"]
        wrapper = root_tasks["distribution:verify"]["run"]
        self.assertIn("cd capabilities/distribution", wrapper)
        self.assertIn("mise run verify", wrapper)
        native = tomllib.loads(
            (ROOT / "capabilities/distribution/mise.toml").read_text()
        )["tasks"]["verify"]["run"]
        # Source-only Distribution retains R7/n8n fixture and shell contracts;
        # retired Python/OPA policy acceptance has no production consumer.
        self.assertIn("bash scripts/test-structure.sh", native)
        self.assertIn("shellcheck", native)
        for retired in ("uv lock --check", "uv sync --locked",
                        "uv run ruff check .", "scripts/test-all.sh"):
            self.assertNotIn(retired, native)
        workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
        self.assertIn("merge_group", workflow.get("on", workflow.get(True, {})))
        steps = workflow["jobs"]["root-verification"]["steps"]
        select = next(x["run"] for x in steps if
                      x.get("name") == "Select affected owners")
        verify = next(x["run"] for x in steps if
                      x.get("name") == "Verify affected owners")
        self.assertIn("convergence_plan.py", select)
        self.assertIn("queueVerifyTasks", select)
        self.assertIn("mise run", verify)
        route = subprocess.run(
            [sys.executable, str(ROOT / "tools/repo/affected_owners.py"),
             "--changed-file", legacy, "--format", "queue-tasks"],
            cwd=ROOT, capture_output=True, text=True, timeout=20, check=False,
        )
        self.assertEqual(route.returncode, 0, route.stderr)
        self.assertEqual(route.stdout.strip(), "distribution:verify")

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

    def test_artifact_native_verification_replaces_nondiscovered_nested_ci(self) -> None:
        """Use root GitHub CI plus Artifact's pinned native queue, not nested CI.

        This source routing test is not deployed Artifact/provider verification.
        """
        import tomllib

        nested = ROOT / "capabilities/artifact/.github/workflows/ci.yml"
        self.assertFalse(nested.exists(), "nested owner CI cannot be discovered by root Actions")
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn("  pull_request:", workflow)
        self.assertIn("  merge_group:", workflow)
        self.assertIn("root-verification:", workflow)
        self.assertLess(workflow.index("Select affected owners"), workflow.index("Verify affected owners"))
        owners = tomllib.loads((ROOT / "tools/repo/owners.toml").read_text(encoding="utf-8"))
        artifact = [o for o in owners["owners"] if o["name"] == "artifact"]
        self.assertEqual(len(artifact), 1)
        self.assertEqual(artifact[0]["root"], "capabilities/artifact/")
        self.assertEqual(artifact[0]["verify_task"], "artifact:verify")
        self.assertEqual(artifact[0]["queue_verify_task"], "artifact:queue")
        root = tomllib.loads((ROOT / "mise.toml").read_text(encoding="utf-8"))
        for task_name, native in (("artifact:queue", "queue"), ("artifact:verify", "verify")):
            self.assertIn("cd capabilities/artifact", root["tasks"][task_name]["run"])
            self.assertIn(f"mise run {native}", root["tasks"][task_name]["run"])
        artifact_mise = tomllib.loads(
            (ROOT / "capabilities/artifact/mise.toml").read_text(encoding="utf-8")
        )
        for task_name in ("queue", "verify"):
            native = artifact_mise["tasks"][task_name]["run"]
            for required in ("uv lock --check", "uv sync --locked", "uv run ruff check",
                             'uv run python -m pytest -m "not integration"'):
                self.assertIn(required, native)
        source_selection = subprocess.run(
            [sys.executable, str(ROOT / "tools/repo/affected_owners.py"),
             "--changed-file", "capabilities/artifact/.github/workflows/ci.yml",
             "--format", "queue-tasks"],
            cwd=ROOT, capture_output=True, text=True, timeout=25, check=False,
        )
        self.assertEqual(source_selection.returncode, 0, source_selection.stderr)
        self.assertEqual(source_selection.stdout.strip(), "artifact:queue")
        self.assertIn("--deselect=", artifact_mise["tasks"]["queue"]["run"])
        self.assertNotIn("--deselect=", artifact_mise["tasks"]["verify"]["run"])

    def test_workstation_native_ci_replaces_nondiscovered_nested_ci(self) -> None:
        """GitHub current-monorepo CI delegates to current Workstation native CI.

        A standalone extracted Workstation repo or installed Windows runner
        is a DIFFERENT source namespace and not qualified by this assertion.
        """
        import tomllib

        self.assertFalse(
            (ROOT / "platform/workstation/.github/workflows/ci.yml").exists(),
            "nested GitHub Actions owner CI is not discovered in this monorepo",
        )
        root_workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn("  pull_request:", root_workflow)
        self.assertIn("  merge_group:", root_workflow)
        self.assertLess(root_workflow.index("Select affected owners"),
                        root_workflow.index("Verify affected owners"))
        owners = tomllib.loads((ROOT / "tools/repo/owners.toml").read_text(encoding="utf-8"))
        records = [o for o in owners["owners"] if o["name"] == "workstation"]
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["root"], "platform/workstation/")
        self.assertEqual(records[0]["verify_task"], "workstation:ci")
        root_mise = tomllib.loads((ROOT / "mise.toml").read_text(encoding="utf-8"))
        for outer, inner in (("workstation:ci", "ci"), ("workstation:verify", "verify")):
            cmd = root_mise["tasks"][outer]["run"]
            self.assertIn("cd platform/workstation", cmd)
            self.assertIn(f"mise run {inner}", cmd)
        native = tomllib.loads((ROOT / "platform/workstation/mise.toml").read_text(encoding="utf-8"))
        self.assertEqual(native["tools"]["python"], "3.15.1")
        self.assertEqual(native["tools"]["pnpm"], "12.16.1")
        ci = native["tasks"]["ci"]["run"]
        for required in (
            "uv lock --check", "uv sync --locked", "uv run ruff check .",
            "uv run python -m pytest", "pnpm install --frozen-lockfile",
            "pnpm run ci", "shellcheck",
        ):
            self.assertIn(required, ci)
        self.assertIn("--ignore=tests/test_workstation_consequences.py", ci)
        self.assertIn("tests/test_workstation_consequences.py", native["tasks"]["verify"]["run"])
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/repo/affected_owners.py"),
             "--changed-file", "platform/workstation/.github/workflows/ci.yml",
             "--format", "queue-tasks"],
            cwd=ROOT, capture_output=True, text=True, timeout=25, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "workstation:ci")


    def test_security_and_decision_index_reuse_current_repo_governance(self) -> None:
        """Missing root security and ADR navigation are checked without duplicating peer templates."""
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
        decisions = (ROOT / "docs/architecture/DECISIONS.md").read_text(encoding="utf-8")
        self.assertIn("SECURITY.md", readme)
        self.assertIn("docs/architecture/DECISIONS.md", readme)
        self.assertIn("https://github.com/ordivon-org/ordivon/security/advisories/new", security)
        self.assertIn("private vulnerability reporting", security)
        for target in ("CURRENT_ARCHITECTURE.md", "STRUCTURE_R2.md", "OWNER_DEPENDENCY_BOUNDARY_R1.md"):
            self.assertIn(target, decisions)
            self.assertTrue((ROOT / "docs/architecture" / target).is_file())
        self.assertIn("not a new architectural authority", decisions)


if __name__ == "__main__":
    unittest.main()
