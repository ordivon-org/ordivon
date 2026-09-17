from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from artifact_core.bindings import CapabilityBindingRegistry
from artifact_core.contracts import FileCommitment, sha256_file
from artifact_core.operations import OperationPlanner
from artifact_core.profiles import ProfileRegistry


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifact-delivery"


class ArtifactCoreRegistryTests(unittest.TestCase):
    def test_file_commitment_binds_exact_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            subject = Path(d) / "subject.bin"
            subject.write_bytes(b"artifact-core-r1")
            commitment = FileCommitment.from_path(subject)
            self.assertEqual(commitment.path, subject.resolve())
            self.assertEqual(commitment.size, len(b"artifact-core-r1"))
            self.assertEqual(commitment.sha256, sha256_file(subject))
            commitment.verify()
            subject.write_bytes(b"artifact-core-r2")
            with self.assertRaisesRegex(RuntimeError, "SHA-256 drift"):
                commitment.verify()

    def test_profile_registry_normalizes_v1_and_native_v2_to_one_shape(self) -> None:
        registry = ProfileRegistry(ART)
        production = registry.resolve("pdu-sdu-presentation-r1")
        shadow = registry.resolve("still-image-png-srgb-r1")
        self.assertEqual(production.profile_id, "pdu-sdu-presentation-r1")
        self.assertEqual(production.canonical["classification"]["family"], "presentation")
        self.assertEqual(production.source_kind, "production-v1-adapted")
        self.assertEqual(production.source_path.name, "pdu-sdu-presentation-r1.json")
        self.assertEqual(shadow.profile_id, "still-image-png-srgb-r1")
        self.assertEqual(shadow.canonical["classification"]["family"], "still-image")
        self.assertEqual(shadow.source_kind, "native-v2-shadow")
        self.assertEqual(shadow.source_path.name, "still-image-png-srgb-r1-v2.json")

    def test_capability_binding_registry_replaces_python_route_table(self) -> None:
        registry = CapabilityBindingRegistry(ART)
        binding = registry.resolve("audio-flac-pcm16-r1", "verify")
        self.assertEqual(binding.profile_id, "audio-flac-pcm16-r1")
        self.assertEqual(binding.operation, "verify")
        self.assertEqual(binding.capability_id, "artifact.audio.flac.verify")
        self.assertEqual(binding.entrypoint.module, "scripts/artifact_audio.py")
        self.assertEqual(binding.entrypoint.callable, "verify_flac")
        self.assertTrue(binding.object_contract_required)
        self.assertEqual(binding.standing, "LOCAL_LIVE_PROVEN")

    def test_operation_planner_uses_registries_without_family_specific_branching(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            subject = root / "tone.flac"
            subject.write_bytes(b"not-a-real-flac-the-planner-only-binds-bytes")
            contract = root / "contract.json"
            contract.write_text(json.dumps({"kind": "fixture"}), encoding="utf-8")
            planner = OperationPlanner(ProfileRegistry(ART), CapabilityBindingRegistry(ART))
            plan = planner.plan_verify(
                profile_id="audio-flac-pcm16-r1",
                subject=FileCommitment.from_path(subject),
                object_contract=FileCommitment.from_path(contract),
            )
            self.assertEqual(plan.operation, "verify")
            self.assertEqual(plan.profile.profile_id, "audio-flac-pcm16-r1")
            self.assertEqual(plan.binding.capability_id, "artifact.audio.flac.verify")
            self.assertEqual(plan.subject.sha256, sha256_file(subject))
            self.assertIsNotNone(plan.object_contract)

    def test_operation_planner_fails_closed_when_required_object_contract_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            subject = Path(d) / "tone.flac"
            subject.write_bytes(b"bytes")
            planner = OperationPlanner(ProfileRegistry(ART), CapabilityBindingRegistry(ART))
            with self.assertRaisesRegex(ValueError, "requires an object contract"):
                planner.plan_verify(
                    profile_id="audio-flac-pcm16-r1",
                    subject=FileCommitment.from_path(subject),
                    object_contract=None,
                )

    def test_binding_registry_is_data_driven_not_derived_from_artifact_verify_source(self) -> None:
        registry = CapabilityBindingRegistry(ART)
        ids = {item.profile_id for item in registry.list(operation="verify")}
        self.assertIn("audio-flac-pcm16-r1", ids)
        self.assertIn("design-3d-step-solid-r1", ids)
        self.assertEqual(registry.registry_path.name, "capability-bindings-v1.json")


if __name__ == "__main__":
    unittest.main()
