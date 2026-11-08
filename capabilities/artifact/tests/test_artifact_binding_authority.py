"""Native authority registry duplicate, stale-cache and standing falsifiers."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from artifact_core.bindings import CapabilityBindingRegistry
from artifact_core.build_bindings import BuildCapabilityBindingRegistry
from artifact_core.contracts import sha256_file


class ArtifactBindingAuthorityTests(unittest.TestCase):
    @staticmethod
    def _test_root(root: Path) -> Path:
        result = root / "artifact-delivery"
        result.mkdir()
        return result

    @staticmethod
    def _verify_record() -> dict:
        return {
            "schemaVersion": 1,
            "kind": "artifact-capability-binding-registry",
            "bindings": [
                {
                    "profileId": "example", "operation": "verify",
                    "capabilityId": "artifact.verify.example",
                    "entrypoint": {
                        "module": "scripts/artifact_verify.py", "callable": "verify_example"
                    },
                    "standingRef": "artifact-delivery/shadow-bindings/example.json",
                }
            ],
        }

    @staticmethod
    def _build_record() -> dict:
        return {
            "schemaVersion": 1,
            "kind": "artifact-build-capability-binding-registry",
            "bindings": [
                {
                    "artifactClass": "presentation",
                    "sourceKind": "presentation",
                    "adapterId": "example",
                    "capabilityId": "artifact.build.example",
                    "builderId": "example",
                    "buildType": "presentation",
                }
            ],
        }

    def test_ambiguous_registry_identity_fields_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = self._test_root(Path(d))
            (root / "capability-bindings-v1.json").write_text(
                '{"schemaVersion":1,"kind":"artifact-capability-binding-registry",'
                '"bindings":[{"profileId":"a","profileId":"b","operation":"verify"}]}'
            )
            with self.assertRaisesRegex(ValueError, "duplicate JSON key: profileId"):
                CapabilityBindingRegistry(root)

    def test_ambiguous_provider_standing_cannot_claim_live(self):
        with tempfile.TemporaryDirectory() as d:
            root = self._test_root(Path(d))
            standing = root / "shadow-bindings/example.json"
            standing.parent.mkdir()
            standing.write_text('{"status":"FAIL","status":"LOCAL_LIVE_PROVEN"}')
            (root / "capability-bindings-v1.json").write_text(json.dumps(self._verify_record()))
            registry = CapabilityBindingRegistry(root)
            with self.assertRaisesRegex(ValueError, "duplicate JSON key: status"):
                registry.resolve("example", "verify")

    def test_binding_bytes_changed_after_indexing_cannot_reuse_cached_route(self):
        with tempfile.TemporaryDirectory() as d:
            root = self._test_root(Path(d))
            standing = root / "shadow-bindings/example.json"
            standing.parent.mkdir()
            standing.write_text('{"status":"LOCAL_LIVE_PROVEN"}')
            registry_path = root / "capability-bindings-v1.json"
            registry_path.write_text(json.dumps(self._verify_record()))
            registry = CapabilityBindingRegistry(root)
            first = registry.resolve("example", "verify")
            self.assertEqual(first.standing_sha256, sha256_file(standing))
            registry_path.write_bytes(registry_path.read_bytes() + b" ")
            with self.assertRaisesRegex(RuntimeError, "changed after indexing"):
                registry.resolve("example", "verify")
            with self.assertRaisesRegex(RuntimeError, "changed after indexing"):
                registry.list(operation="verify")

    def test_standing_report_sha_covers_parsed_bytes_not_a_later_reread(self):
        with tempfile.TemporaryDirectory() as d:
            root = self._test_root(Path(d))
            standing = root / "shadow-bindings/example.json"
            standing.parent.mkdir()
            standing.write_text('{"status":"LOCAL_LIVE_PROVEN"}')
            (root / "capability-bindings-v1.json").write_text(json.dumps(self._verify_record()))
            result = CapabilityBindingRegistry(root).resolve("example", "verify")
            self.assertEqual(result.standing_sha256, sha256_file(standing))

    def test_snapshot_policy_is_separate_from_claim_completeness(self):
        from pathlib import Path

        root = Path(__file__).resolve().parents[1] / "artifact-delivery"
        registry = CapabilityBindingRegistry(root)
        parquet = registry.resolve("dataset-parquet-flat-r1", "verify")
        self.assertTrue(parquet.snapshot_inputs)
        self.assertFalse(parquet.require_claim_results)
        for profile_id in ("audio-flac-pcm16-r1", "audio-wave-pcm16-r1", "still-image-png-srgb-r1"):
            with self.subTest(profile=profile_id):
                binding = registry.resolve(profile_id, "verify")
                self.assertTrue(binding.snapshot_inputs)
                self.assertTrue(binding.require_claim_results)
        self.assertFalse(registry.resolve("still-image-svg-static-r1", "verify").snapshot_inputs)

    def test_registry_rejects_non_boolean_snapshot_configuration(self):
        with tempfile.TemporaryDirectory() as d:
            root = self._test_root(Path(d))
            record = self._verify_record()
            record["bindings"][0]["snapshotInputs"] = "true"
            (root / "capability-bindings-v1.json").write_text(json.dumps(record))
            with self.assertRaisesRegex(RuntimeError, "snapshotInputs must be a boolean"):
                CapabilityBindingRegistry(root)

    def test_duplicate_build_fields_and_stale_binding_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = self._test_root(Path(d))
            path = root / "build-capability-bindings-v1.json"
            path.write_text(
                '{"schemaVersion":1,"kind":"artifact-build-capability-binding-registry",'
                '"bindings":[{"capabilityId":"a","capabilityId":"b"}]}'
            )
            with self.assertRaisesRegex(ValueError, "duplicate JSON key: capabilityId"):
                BuildCapabilityBindingRegistry(root)
            path.write_text(json.dumps(self._build_record()))
            registry = BuildCapabilityBindingRegistry(root)
            self.assertEqual(registry.resolve("presentation", "presentation").capability_id,
                             "artifact.build.example")
            path.write_bytes(path.read_bytes() + b" ")
            with self.assertRaisesRegex(RuntimeError, "changed after indexing"):
                registry.resolve("presentation", "presentation")
            with self.assertRaisesRegex(RuntimeError, "changed after indexing"):
                registry.list()


if __name__ == "__main__":
    unittest.main()
