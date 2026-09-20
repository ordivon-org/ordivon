from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "policies" / "external-ownership-boundary.json"
AGENT_SERVICE = ROOT / "agent_service"


def _load_profile() -> dict:
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


class ExternalOwnershipBoundaryTests(unittest.TestCase):
    def test_architectural_core_and_residuals_are_empty(self) -> None:
        profile = _load_profile()
        self.assertEqual(profile["architecturalCore"], "EMPTY")
        self.assertEqual(profile["acceptedIrreduciblePrimitives"], [])
        self.assertEqual(profile["residualCandidates"], [])

    def test_agent_service_is_retired_and_cannot_reappear_as_a_ceiling(self) -> None:
        profile = _load_profile()
        self.assertFalse(any(AGENT_SERVICE.rglob("*.py")))
        self.assertEqual(
            profile["legacyTypeCeilings"]["agentServiceTopLevelClasses"], []
        )
        retirement = profile["agentServiceRetirement"]
        self.assertEqual(retirement["status"], "RETIRED")
        self.assertTrue(retirement["sourceRemoved"])
        self.assertFalse(retirement["canaryUnitInstalled"])
        self.assertFalse(retirement["canaryActive"])
        self.assertFalse(retirement["port8894Listening"])
        self.assertEqual(retirement["crossRepositoryNamedConsumers"], 0)

    def test_post_baseline_types_cannot_become_local_semantic_authority(self) -> None:
        profile = _load_profile()
        allowed = {"ADAPTER", "CLIENT", "ERROR", "PROJECTION", "READER", "VERIFIER"}
        for entry in profile["approvedPostBaselineTypes"]:
            self.assertIn(entry["role"], allowed)
            self.assertFalse(entry["authoritative"])
            self.assertNotIn(
                entry["owner"].strip().lower(), {"ordivon", "local", "custom", "self"}
            )
            self.assertTrue(entry["canonicalReference"].startswith("https://"))

    def test_external_owner_registry_has_no_ordivon_owner(self) -> None:
        owners = _load_profile()["externalOwners"]
        self.assertGreaterEqual(len(owners), 8)
        for owner in owners:
            self.assertNotEqual(owner["name"].strip().lower(), "ordivon")
            self.assertTrue(owner["canonicalReference"].startswith("https://"))

    def test_credential_reference_persistence_is_retired(self) -> None:
        profile = _load_profile()
        boundary = profile["credentialReferenceBoundary"]
        self.assertEqual(boundary["status"], "RETIRED_WITH_AGENT_SERVICE")
        self.assertFalse(boundary["authoritative"])
        self.assertEqual(boundary["localResponsibilities"], [])
        self.assertIn("credential_references", profile["retiredPersistenceSurfaces"])

    def test_deletion_gates_remain_behavioral_not_brand_based(self) -> None:
        gates = set(_load_profile()["mandatoryDeletionGates"])
        required = {
            "response-loss-after-real-effect",
            "provider-replacement",
            "projection-destroy-rebuild",
            "semantic-completion-independent-of-exit-zero",
            "no-ordivon-only-external-identifier",
        }
        self.assertTrue(required.issubset(gates))


if __name__ == "__main__":
    unittest.main()
