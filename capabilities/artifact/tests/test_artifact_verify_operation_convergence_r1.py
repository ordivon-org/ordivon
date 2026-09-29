from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from artifact_core.contracts import file_fact
from artifact_core.profiles import ProfileRegistry
from artifact_operations import operation_envelope
from artifact_operations.providers.verification import VerifyOperationHandler
from artifact_operations.receipt import operation_file_fact

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifact-delivery"
PROFILES = ProfileRegistry(ART)


def claims(profile: dict) -> dict:
    return {
        key: {
            "status": "PASS",
            "observationIds": [key],
            "evidenceRefs": [],
            "nativePointers": [f"/{key}"],
            "nonClaims": [],
        }
        for key in sorted(profile["requiredEvidence"])
    }


def fake_production_verify(
    profile_path: Path,
    artifact: Path,
    evidence: Path,
    request_path: Path | None,
) -> dict:
    del request_path
    profile_id = json.loads(profile_path.read_text(encoding="utf-8"))["id"]
    canonical = PROFILES.resolve(profile_id).canonical
    receipts = {
        key: {"status": "PASS", "verificationResult": "PASSED"}
        for key in sorted(canonical["requiredEvidence"])
    }
    required = sorted(
        key for key, value in canonical["requiredEvidence"].items() if value.get("required") is True
    )
    evidence.mkdir(parents=True, exist_ok=True)
    return {
        "schemaVersion": 1,
        "kind": "artifact-delivery-verify-stage",
        "status": "PASS",
        "profileId": profile_id,
        "artifact": file_fact(artifact),
        "receipts": receipts,
        "profileRequiredGates": required,
        "pendingRequiredGates": [],
        "profileVerificationComplete": True,
        "failures": [],
    }


class FakePlugin:
    def __init__(self, profile: dict) -> None:
        self.profile = profile

    def verify(
        self,
        subject: Path,
        evidence_directory: Path,
        *,
        object_contract: Path | None = None,
    ) -> dict:
        self.subject = subject
        self.contract = object_contract
        evidence_directory.mkdir(parents=True, exist_ok=True)
        return {
            "schemaVersion": 1,
            "kind": "fake-family-verification",
            "status": "PASS",
            "profileId": self.profile["id"],
            "claimResults": claims(self.profile),
            "failures": [],
        }


class ArtifactVerifyOperationConvergenceR1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.handler = VerifyOperationHandler(
            ART,
            production_verify=fake_production_verify,
        )

    def test_registered_production_v1_uses_existing_stage_and_common_projection(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            artifact = root / "subject.pptx"; artifact.write_bytes(b"subject")
            profile = ART / "examples/pdu-sdu-presentation-r1.json"
            operation = operation_envelope(
                "d01/production",
                "verify",
                {
                    "profile": operation_file_fact(profile),
                    "artifact": operation_file_fact(artifact),
                },
            )
            prepared = self.handler.prepare(operation)
            self.assertEqual(prepared.context["verificationMode"], "production-v1-registered")
            roles, metadata = self.handler.produce(prepared.context, root / "out")
            self.assertEqual(roles["verifyReport"], "verify-stage.json")
            self.assertEqual(roles["evaluationProjection"], "evaluation-projection.json")
            self.assertTrue(metadata["profileVerificationComplete"])
            projection = json.loads((root / "out/evaluation-projection.json").read_text())
            self.assertEqual(projection["kind"], "artifact-evaluation-projection")
            self.assertEqual(projection["sourceKind"], "production-v1-compatibility")

    def test_registered_v2_requires_binding_contract_and_uses_plugin_provider(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            subject = root / "subject.wav"; subject.write_bytes(b"subject")
            contract = root / "contract.json"; contract.write_text("{}")
            record = PROFILES.resolve("audio-wave-pcm16-r1")
            missing = operation_envelope(
                "d01/v2-missing-contract",
                "verify",
                {
                    "profile": operation_file_fact(record.canonical_path),
                    "artifact": operation_file_fact(subject),
                },
            )
            with self.assertRaisesRegex(RuntimeError, "requires an object contract"):
                self.handler.prepare(missing)

            operation = operation_envelope(
                "d01/v2",
                "verify",
                {
                    "profile": operation_file_fact(record.canonical_path),
                    "artifact": operation_file_fact(subject),
                    "objectContract": operation_file_fact(contract),
                },
            )
            prepared = self.handler.prepare(operation)
            self.assertEqual(prepared.context["verificationMode"], "registered-v2-family")
            plugin = FakePlugin(record.canonical)
            with patch(
                "artifact_operations.providers.verification.resolve_verifier_plugin",
                return_value=plugin,
            ):
                roles, metadata = self.handler.produce(prepared.context, root / "out")
            self.assertIsNotNone(plugin.contract)
            self.assertEqual(plugin.contract.read_bytes(), contract.read_bytes())
            self.assertEqual(roles["verifyReport"], "family-verification.json")
            self.assertEqual(roles["evaluationProjection"], "evaluation-projection.json")
            self.assertTrue(metadata["profileVerificationComplete"])
            projection = json.loads((root / "out/evaluation-projection.json").read_text())
            self.assertEqual(projection["sourceKind"], "registered-v2-family")
            self.assertEqual(
                projection["standingDecision"]["standingVector"]["verificationStatus"],
                "PASS",
            )

    def test_legacy_unregistered_v1_keeps_historical_stage_without_fake_v2_projection(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            artifact = root / "subject.pptx"; artifact.write_bytes(b"subject")
            raw = json.loads((ART / "examples/pdu-sdu-presentation-r1.json").read_text())
            raw["id"] = "d01-ephemeral-v1"
            profile = root / "profile.json"; profile.write_text(json.dumps(raw))
            operation = operation_envelope(
                "d01/legacy-v1",
                "verify",
                {
                    "profile": operation_file_fact(profile),
                    "artifact": operation_file_fact(artifact),
                },
            )
            prepared = self.handler.prepare(operation)
            self.assertEqual(
                prepared.context["verificationMode"],
                "production-v1-legacy-unregistered",
            )
            # Do not execute fake callback here: it intentionally has no canonical profile.


if __name__ == "__main__":
    unittest.main()
