from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "evidence" / "index.json"
SCRIPT = ROOT / "scripts" / "check_evidence.py"

spec = importlib.util.spec_from_file_location("harness_check_evidence", SCRIPT)
assert spec is not None and spec.loader is not None
check_evidence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_evidence)

EXPECTED = {
    "harness.research.campaign3-rich-effect-owner-capture-v1": (
        "harness-campaign3-rich-effect-owner-v1-capture.json",
        "historical",
        "786d64a7cfb21d52e9e541331c3db67a9edd4f29",
        "5695253f4148536178e7e579624762d27af68f541632121e3dd507f1d2a1f698",
    ),
    "harness.research.campaign3-rich-effect-owner-result-v1": (
        "harness-campaign3-rich-effect-owner-v1-result.json",
        "historical",
        "786d64a7cfb21d52e9e541331c3db67a9edd4f29",
        "bd251924d98b9cd25bb76fd0496bdfd51f485d86a878767ef45533a2aedc7c4d",
    ),
    "harness.research.campaign5-provider-route-preservation-v1": (
        "harness-campaign5-provider-route-preservation-v1-result.json",
        "historical",
        "a1a61430047dfa0c43fb2f32d1d2529d57c19018",
        "0693df87e7541a5589ba865e17937b46e79fb2f25bb7175b3856cae682ff0aa1",
    ),
    "harness.execution.current-no-tool-conclusion-control-repair-v1": (
        "harness-current-no-tool-conclusion-control-repair-v1.json",
        "historical",
        "8925fdba026cdef4f9d8969fae244ee3e5e46730",
        "d455cc726e6356e4463a6c7463d9573d3d2730c88b78723fa362129159b7b4ae",
    ),
    "harness.execution.first-interface-owner-composition-atlas-v1": (
        "harness-first-interface-owner-composition-atlas-v1.json",
        "historical",
        "792cd48cc9fbdddb7431462876d8e57d8f003643",
        "c14b0b932ed15a0f7483a69191a8b3c6f6cd1030377c2138e92d5c227363d329",
    ),
    "harness.execution.first-interface-owner-bridges-v2": (
        "harness-first-interface-owner-bridges-v2.json",
        "historical",
        "0cfed2338a28be428c11816668651463cd9ccb8b",
        "2e5590de07107d84718c3c903f151a64fd29764dd0ad8d930d67ed761f047083",
    ),
    "harness.execution.first-interface-owner-bridges-v3": (
        "harness-first-interface-owner-bridges-v3.json",
        "historical",
        "00edab4e4f6aeac395c9de3ab6a300162e56f6c1",
        "1f2abd65f175ddfff851dbdd6d568c89f422ee77e0c16d6f7908670e8f9dd66a",
    ),
    "harness.execution.first-interface-owner-bridges-v4": (
        "harness-first-interface-owner-bridges-v4.json",
        "historical",
        "f4b05bb38ef7bff10f889df69611de6aaff3a40c",
        "3a2bd1a860714b27672fa228dd25b6660bb318a75320deb18292c4461c49404d",
    ),
    "harness.execution.first-interface-owner-bridges-v5": (
        "harness-first-interface-owner-bridges-v5.json",
        "historical",
        "233bb6354f81eff070996cef898b91726857ca8e",
        "2a2c8eaf2f38af01e129d0a24cdcb1dc406e97a659f42d8cf1cb32f32dde634e",
    ),
    "harness.execution.source-reconciliation-structured-observation-v1": (
        "harness-source-reconciliation-structured-observation-v1.json",
        "historical",
        "e983c79f5582160b37ac56c1898efa80e486880d",
        "db9d22a113a1e7b5f4f4ea882d71e6aec91da2a6e61c16f5dc0abd8e821b28ea",
    ),
    "harness.execution.capability-environment-v1": (
        "harness-capability-environment-v1.json",
        "historical",
        "830dd160b1025928521204f4713cbe0e1bbbf589",
        "aa7d2c696268b218fd32ea09edaa27699d444da2632943b9824cd828a137209e",
    ),
    "harness.execution.current-affordance-compact-v2": (
        "harness-current-affordance-compact-v2.json",
        "historical",
        "17e8943edb16c0f586d5a8d022c63590755a7d6b",
        "e3a24628400842fcb9563969101b2ab7335326c2bb90128b14c51a2bf41c3598",
    ),
    "harness.recovery.unreachable-abandonment-retirement-v1": (
        "harness-unreachable-abandonment-retirement-v1.json",
        "historical",
        "46030ae7d5725cffcad4686707d391ba29fd7f01",
        "f0f415fe6677b2d1a8089510ac83c8a5b7a3f5a51a064aaf65e21ef0ffd3d6b1",
    ),
}


class EvidenceIndexTypedIngestionTests(unittest.TestCase):
    def _entries(self) -> dict[str, dict[str, object]]:
        raw = json.loads(INDEX.read_text(encoding="utf-8"))
        return {entry["claimId"]: entry for entry in raw["entries"]}

    def test_expected_projection_entries_are_bound_without_rewriting_bytes(self) -> None:
        entries = self._entries()
        for claim_id, (filename, status, revision, digest) in EXPECTED.items():
            entry = entries[claim_id]
            self.assertEqual(entry["file"], filename)
            self.assertEqual(entry["status"], status)
            self.assertEqual(entry["implementationRevision"], revision)
            self.assertEqual(entry["revisionBinding"], "index-creation-lineage")
            actual = hashlib.sha256((ROOT / "evidence" / filename).read_bytes()).hexdigest()
            self.assertEqual(actual, digest)

    def test_ts11_stale_verified_receipt_is_historical(self) -> None:
        entry = self._entries()["harness.tool-surface.ts11-turn-working-set"]
        self.assertEqual(entry["status"], "historical")
        self.assertEqual(
            entry["implementationRevision"],
            "a57963c476d366aea0d73d96cddd223f3bd5dbaf",
        )

    def test_legacy_embedded_binding_stays_exact(self) -> None:
        entries = self._entries()
        entry = next(item for item in entries.values() if "revisionBinding" not in item)
        filename = str(entry["file"])
        revision = str(entry["implementationRevision"])
        receipt = json.loads((ROOT / "evidence" / filename).read_text(encoding="utf-8"))
        validator = check_evidence._validate_embedded_revision_binding
        self.assertEqual(validator(filename, receipt, revision), [])
        errors = validator(filename, receipt, "0" * 40)
        self.assertTrue(any("revision mismatch" in error for error in errors))

    def test_verified_currentness_still_rejects_stale_implementation(self) -> None:
        current, invalidating = check_evidence._verified_revision_is_current(
            "a57963c476d366aea0d73d96cddd223f3bd5dbaf"
        )
        self.assertFalse(current)
        self.assertTrue(invalidating)
        current, invalidating = check_evidence._verified_revision_is_current(
            "8925fdba026cdef4f9d8969fae244ee3e5e46730"
        )
        self.assertFalse(current)
        self.assertTrue(invalidating)
        current, invalidating = check_evidence._verified_revision_is_current(
            "792cd48cc9fbdddb7431462876d8e57d8f003643"
        )
        self.assertFalse(current)
        # This revision predates the Finance observe bridge. After that bridge is retired,
        # endpoint diffing no longer lists the transient path because it is absent at both
        # endpoints; currentness must still fail on the remaining verified source changes.
        self.assertTrue(any(path.startswith("src/") for path in invalidating), invalidating)
        self.assertNotIn(
            "src/ordivon_harness/ordivon/finance_observe_runtime_bridge.py",
            invalidating,
        )
        current, invalidating = check_evidence._verified_revision_is_current(
            "0cfed2338a28be428c11816668651463cd9ccb8b"
        )
        self.assertFalse(current)
        # This revision also predates the Finance research bridge. Retirement removes the
        # transient path from the endpoint diff, but the historical implementation remains
        # stale because later verified source changed. A revision where the bridge already
        # existed is checked immediately below and must still name the deletion explicitly.
        self.assertTrue(any(path.startswith("src/") for path in invalidating), invalidating)
        self.assertNotIn(
            "src/ordivon_harness/ordivon/finance_research_runtime_bridge.py",
            invalidating,
        )
        current, invalidating = check_evidence._verified_revision_is_current(
            "00edab4e4f6aeac395c9de3ab6a300162e56f6c1"
        )
        self.assertFalse(current)
        self.assertIn(
            "src/ordivon_harness/ordivon/finance_research_runtime_bridge.py", invalidating
        )
        current, invalidating = check_evidence._verified_revision_is_current(
            "f4b05bb38ef7bff10f889df69611de6aaff3a40c"
        )
        self.assertFalse(current)
        self.assertIn(
            "src/ordivon_harness/ordivon/finance_observe_runtime_bridge.py",
            invalidating,
        )
        current, invalidating = check_evidence._verified_revision_is_current(
            "233bb6354f81eff070996cef898b91726857ca8e"
        )
        self.assertFalse(current)
        self.assertIn("src/ordivon_harness/capability_catalog.py", invalidating)
        current, invalidating = check_evidence._verified_revision_is_current(
            "e983c79f5582160b37ac56c1898efa80e486880d"
        )
        self.assertFalse(current)
        self.assertIn("pyproject.toml", invalidating)
        self.assertIn("uv.lock", invalidating)
        self.assertTrue(
            any(path.startswith("src/") for path in invalidating),
            invalidating,
        )
        current, invalidating = check_evidence._verified_revision_is_current(
            "830dd160b1025928521204f4713cbe0e1bbbf589"
        )
        self.assertFalse(current)
        self.assertIn("src/ordivon_harness/capability_discovery.py", invalidating)
        self.assertIn("src/ordivon_harness/interaction_context.py", invalidating)
        self.assertTrue(any(path.startswith("src/") for path in invalidating), invalidating)
        current, invalidating = check_evidence._verified_revision_is_current(
            "17e8943edb16c0f586d5a8d022c63590755a7d6b"
        )
        self.assertFalse(current)
        self.assertIn("pyproject.toml", invalidating)
        self.assertIn("uv.lock", invalidating)
        self.assertIn("src/ordivon_harness/ordivon/deepseek.py", invalidating)
        current, invalidating = check_evidence._verified_revision_is_current(
            "46030ae7d5725cffcad4686707d391ba29fd7f01"
        )
        self.assertFalse(current)
        required_invalidating = {
            "src/ordivon_harness/ordivon/loop.py",
            "src/ordivon_harness/ordivon/run_recovery.py",
            "src/ordivon_harness/ordivon/runtime_lowering.py",
            "src/ordivon_harness/ordivon/sqlite_runtime_bridge.py",
        }
        self.assertTrue(required_invalidating <= set(invalidating), invalidating)
        self.assertIn("pyproject.toml", invalidating)
        self.assertIn("uv.lock", invalidating)
        self.assertTrue(
            all(
                path.startswith("src/")
                or path
                in {
                    "pyproject.toml",
                    "uv.lock",
                    "scripts/harness_p0_scale_acceptance.py",
                }
                for path in invalidating
            ),
            invalidating,
        )

    def test_scoped_verified_currentness_detects_runtime_dependency_closure_change(self) -> None:
        adaptive_scope = (
            "src/anc_canonical/",
            "src/ordivon_harness/adaptive_edit.py",
            "src/ordivon_harness/execution_binding.py",
            "src/ordivon_harness/runtime_port.py",
            "src/ordivon_harness/ordivon/",
        )
        current, invalidating = check_evidence._verified_revision_is_current(
            "9d936e98d8c02772aa2becc924ba9006c71aa989",
            adaptive_scope,
            runtime_dependency_closure_digest="sha256:4cc6d831b89db3b09f716fff844601eb39196be13410c45ee1b12d3e7c27c829",
        )
        self.assertFalse(current)
        self.assertEqual(
            invalidating,
            [
                "src/ordivon_harness/ordivon/runtime_lowering.py",
                "src/ordivon_harness/ordivon/sqlite_runtime_bridge.py",
                "@runtime-dependency-closure",
            ],
        )

        lsp_scope = ("src/ordivon_harness/lsp_workspace_edit.py",)
        current, invalidating = check_evidence._verified_revision_is_current(
            "9d936e98d8c02772aa2becc924ba9006c71aa989",
            lsp_scope,
            runtime_dependency_closure_digest="sha256:4cc6d831b89db3b09f716fff844601eb39196be13410c45ee1b12d3e7c27c829",
        )
        self.assertFalse(current)
        self.assertEqual(
            invalidating,
            ["src/ordivon_harness/lsp_workspace_edit.py", "@runtime-dependency-closure"],
        )

    def test_scoped_implementation_paths_are_validated_conservatively(self) -> None:
        normalize = check_evidence._normalize_implementation_paths
        accepted = normalize(
            [
                "src/ordivon_harness/adaptive_edit.py",
                "src/ordivon_harness/ordivon/",
            ]
        )
        self.assertEqual(
            accepted,
            (
                "src/ordivon_harness/adaptive_edit.py",
                "src/ordivon_harness/ordivon/",
            ),
        )
        for invalid in (
            [],
            ["docs/"],
            ["src/ordivon_harness/adaptive_edit.py", "pyproject.toml"],
            ["../src/"],
        ):
            with self.assertRaises(ValueError):
                normalize(invalid)

    def test_scoped_historical_evidence_preserves_old_runtime_dependency_closure(self) -> None:
        entries = self._entries()
        scoped = [
            entry
            for entry in entries.values()
            if "implementationPaths" in entry
            and entry.get("runtimeDependencyClosureDigest")
            == "sha256:4cc6d831b89db3b09f716fff844601eb39196be13410c45ee1b12d3e7c27c829"
        ]
        self.assertEqual(len(scoped), 9)
        for entry in scoped:
            self.assertEqual(entry.get("status"), "historical", entry.get("claimId"))
            self.assertNotIn("pyproject.toml", entry["implementationPaths"])
            self.assertNotIn("uv.lock", entry["implementationPaths"])
            self.assertEqual(
                check_evidence._runtime_dependency_closure_digest(
                    str(entry["implementationRevision"])
                ),
                "sha256:4cc6d831b89db3b09f716fff844601eb39196be13410c45ee1b12d3e7c27c829",
            )
            current, invalidating = check_evidence._verified_revision_is_current(
                str(entry["implementationRevision"]),
                tuple(entry["implementationPaths"]),
                runtime_dependency_closure_digest=str(entry["runtimeDependencyClosureDigest"]),
            )
            self.assertFalse(current, entry.get("claimId"))
            self.assertIn("@runtime-dependency-closure", invalidating, entry.get("claimId"))
        self.assertEqual(
            check_evidence._runtime_dependency_closure_digest("HEAD"),
            "sha256:c24519d0fdfbbaf56233fb25568428ff6fbdf3dac962ea62e2b95590e1a2d7d5",
        )

    def test_scoped_runtime_dependency_digest_fails_closed_on_wrong_revision_binding(self) -> None:
        scope = ("src/ordivon_harness/adaptive_edit.py",)
        with self.assertRaisesRegex(ValueError, "differs from its implementation revision"):
            check_evidence._verified_revision_is_current(
                "9d936e98d8c02772aa2becc924ba9006c71aa989",
                scope,
                runtime_dependency_closure_digest="sha256:" + "0" * 64,
            )

    def test_index_creation_lineage_binding_accepts_exact_and_rejects_nonancestor(self) -> None:
        validator = check_evidence._validate_index_creation_lineage_binding
        for filename, _status, revision, _digest in EXPECTED.values():
            self.assertEqual(validator(filename, revision), [])
        current_head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        ).stdout.strip()
        errors = validator(
            "harness-campaign3-rich-effect-owner-v1-capture.json",
            current_head,
        )
        self.assertTrue(any("ancestor" in error for error in errors))

    def test_environment_and_h1_profiles_are_historical_after_plugin_h2(self) -> None:
        entries = self._entries()

        old = entries["harness.environment.python-3.14.7-upgrade"]
        self.assertEqual(old["status"], "historical")
        old_current, invalidating = check_evidence._verified_revision_is_current(
            str(old["implementationRevision"])
        )
        self.assertFalse(old_current)
        self.assertIn("pyproject.toml", invalidating)

        post_skills = entries["harness.environment.post-skills-extraction-python-3.14.7"]
        self.assertEqual(post_skills["status"], "historical")
        post_current, post_invalidating = check_evidence._verified_revision_is_current(
            str(post_skills["implementationRevision"])
        )
        self.assertFalse(post_current)
        self.assertIn("src/ordivon_harness/agent_plugin.py", post_invalidating)

        h1 = entries["harness.composition.agent-plugin-h1"]
        self.assertEqual(h1["status"], "historical")
        h1_receipt = json.loads(
            (ROOT / "evidence" / "harness-agent-plugin-h1-acceptance-20260922.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(h1_receipt["composition"]["pluginStandard"], "Agent Plugins v1")
        self.assertFalse(h1_receipt["composition"]["effectfulToolsAdmitted"])
        h1_current, h1_invalidating = check_evidence._verified_revision_is_current(
            str(h1["implementationRevision"])
        )
        self.assertFalse(h1_current)
        self.assertIn("src/ordivon_harness/agent_run.py", h1_invalidating)
        self.assertIn("src/ordivon_harness/plugin_gateway_effect.py", h1_invalidating)

        h2 = entries["harness.composition.agent-plugin-h2-durable-gateway-effects"]
        self.assertEqual(h2["status"], "historical")
        h2_receipt = json.loads(
            (
                ROOT / "evidence" / "harness-agent-plugin-h2-durable-gateway-effects-20260922.json"
            ).read_text(encoding="utf-8")
        )
        self.assertTrue(h2_receipt["composition"]["durablePreDispatchIntent"])
        self.assertFalse(h2_receipt["composition"]["blindEffectRedispatchOnResponseLoss"])
        h2_current, h2_invalidating = check_evidence._verified_revision_is_current(
            str(h2["implementationRevision"])
        )
        self.assertFalse(h2_current)
        self.assertIn(
            "src/ordivon_harness/ordivon/sqlite_runtime_bridge.py",
            h2_invalidating,
        )
        self.assertIn("src/ordivon_harness/plugin_gateway_effect.py", h2_invalidating)

        h2b = entries["harness.composition.agent-plugin-h2b-cooperative-cancellation"]
        self.assertEqual(h2b["status"], "historical")
        h2b_current, h2b_invalidating = check_evidence._verified_revision_is_current(
            str(h2b["implementationRevision"]),
            tuple(h2b["implementationPaths"]),
            runtime_dependency_closure_digest=str(h2b["runtimeDependencyClosureDigest"]),
        )
        self.assertFalse(h2b_current)
        self.assertIn(
            "src/ordivon_harness/ordivon/sqlite_runtime_bridge.py",
            h2b_invalidating,
        )
        self.assertIn("src/ordivon_harness/plugin_gateway_effect.py", h2b_invalidating)

        current = entries["harness.runtime.runtime-job-tool-contract-r1"]
        self.assertEqual(current["status"], "verified")
        self.assertEqual(
            current["implementationRevision"],
            "045cf62eed2e1039ab39d71bdc179349d1e974b9",
        )
        receipt = json.loads(
            (ROOT / "evidence" / "harness-runtime-job-tool-contract-r1-20260923.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(receipt["contract"]["runtimeJobDiscoveryTool"], "job.list")
        self.assertEqual(receipt["contract"]["runtimeJobObservationTool"], "job.observe")
        self.assertEqual(
            receipt["contract"]["retiredCompatibilityNames"],
            ["task.list", "task.observe"],
        )
        self.assertTrue(receipt["contract"]["cooperativeGatewayCancellationPreserved"])
        self.assertFalse(receipt["contract"]["runtimeOwnsTaskSemanticCompletion"])
        self.assertEqual(
            receipt["runtimeDependencyClosureDigest"],
            "sha256:c24519d0fdfbbaf56233fb25568428ff6fbdf3dac962ea62e2b95590e1a2d7d5",
        )
        self.assertEqual(
            current["implementationPaths"],
            [
                "src/ordivon_harness/ordivon/runtime_lowering.py",
                "src/ordivon_harness/ordivon/sqlite_runtime_bridge.py",
                "src/ordivon_harness/plugin_gateway_effect.py",
            ],
        )
        self.assertEqual(
            current["runtimeDependencyClosureDigest"],
            receipt["runtimeDependencyClosureDigest"],
        )
        current_ok, current_invalidating = check_evidence._verified_revision_is_current(
            str(current["implementationRevision"]),
            tuple(current["implementationPaths"]),
            runtime_dependency_closure_digest=str(current["runtimeDependencyClosureDigest"]),
        )
        self.assertTrue(current_ok, current_invalidating)
        self.assertEqual(current_invalidating, [])

    def test_owner_relative_git_paths_survive_identity_preserving_monorepo_import(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "source"
            target = base / "target"
            subprocess.run(["git", "init", "-q", "-b", "main", str(source)], check=True)
            subprocess.run(["git", "-C", str(source), "config", "user.name", "test"], check=True)
            subprocess.run(
                ["git", "-C", str(source), "config", "user.email", "test@example.invalid"],
                check=True,
            )
            (source / "src").mkdir()
            (source / "scripts").mkdir()
            (source / "evidence").mkdir()
            (source / "src" / "a.py").write_text("VALUE = 1\n", encoding="utf-8")
            (source / "pyproject.toml").write_text("[project]\nname='probe'\n", encoding="utf-8")
            (source / "uv.lock").write_text("version = 1\n", encoding="utf-8")
            (source / "scripts" / "harness_p0_scale_acceptance.py").write_text(
                "print('probe')\n", encoding="utf-8"
            )
            subprocess.run(["git", "-C", str(source), "add", "."], check=True)
            subprocess.run(
                ["git", "-C", str(source), "commit", "-q", "-m", "implementation"], check=True
            )
            implementation = subprocess.check_output(
                ["git", "-C", str(source), "rev-parse", "HEAD"], text=True
            ).strip()

            receipt_bytes = b'{"kind":"probe"}\n'
            (source / "evidence" / "receipt.json").write_bytes(receipt_bytes)
            subprocess.run(["git", "-C", str(source), "add", "evidence/receipt.json"], check=True)
            subprocess.run(["git", "-C", str(source), "commit", "-q", "-m", "evidence"], check=True)
            source_head = subprocess.check_output(
                ["git", "-C", str(source), "rev-parse", "HEAD"], text=True
            ).strip()

            subprocess.run(["git", "init", "-q", "-b", "main", str(target)], check=True)
            subprocess.run(["git", "-C", str(target), "config", "user.name", "test"], check=True)
            subprocess.run(
                ["git", "-C", str(target), "config", "user.email", "test@example.invalid"],
                check=True,
            )
            (target / "README.md").write_text("# target\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(target), "add", "README.md"], check=True)
            subprocess.run(["git", "-C", str(target), "commit", "-q", "-m", "root"], check=True)
            before = subprocess.check_output(
                ["git", "-C", str(target), "rev-parse", "HEAD"], text=True
            ).strip()
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(target),
                    "fetch",
                    "-q",
                    str(source),
                    f"{source_head}:refs/ordivon/import-sources/harness",
                ],
                check=True,
            )
            subprocess.run(["git", "-C", str(target), "read-tree", "--reset", before], check=True)
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(target),
                    "read-tree",
                    "--prefix=services/harness/",
                    f"{source_head}^{{tree}}",
                ],
                check=True,
            )
            merge_tree = subprocess.check_output(
                ["git", "-C", str(target), "write-tree"], text=True
            ).strip()
            merge = subprocess.run(
                [
                    "git",
                    "-C",
                    str(target),
                    "commit-tree",
                    merge_tree,
                    "-p",
                    before,
                    "-p",
                    source_head,
                ],
                input="import harness\n",
                text=True,
                check=True,
                stdout=subprocess.PIPE,
            ).stdout.strip()
            subprocess.run(["git", "-C", str(target), "reset", "--hard", "-q", merge], check=True)

            owner_root = target / "services" / "harness"
            previous_root = check_evidence.ROOT
            previous_evidence = check_evidence.EVIDENCE
            check_evidence.ROOT = owner_root
            check_evidence.EVIDENCE = owner_root / "evidence"
            try:
                self.assertEqual(
                    check_evidence._git_file_bytes(implementation, "uv.lock"),
                    b"version = 1\n",
                )
                self.assertEqual(
                    check_evidence._git_file_bytes("HEAD", "uv.lock"),
                    b"version = 1\n",
                )
                self.assertEqual(
                    check_evidence._invalidating_paths(source_head, "HEAD"),
                    [],
                )
                self.assertEqual(
                    check_evidence._validate_index_creation_lineage_binding(
                        "receipt.json", implementation
                    ),
                    [],
                )

                (owner_root / "src" / "a.py").write_text("VALUE = 2\n", encoding="utf-8")
                subprocess.run(
                    ["git", "-C", str(target), "add", "services/harness/src/a.py"],
                    check=True,
                )
                subprocess.run(
                    ["git", "-C", str(target), "commit", "-q", "-m", "change owner source"],
                    check=True,
                )
                self.assertEqual(
                    check_evidence._invalidating_paths(source_head, "HEAD"),
                    ["src/a.py"],
                )
            finally:
                check_evidence.ROOT = previous_root
                check_evidence.EVIDENCE = previous_evidence

    def test_complete_evidence_contract_is_green(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("evidence contract: valid", completed.stdout)


if __name__ == "__main__":
    unittest.main()
