from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "planning" / "ordivon-core-zero-enforcement-r3.json"
AGENT_SERVICE = ROOT / "agent_service"

ALLOWED_NON_AUTHORITY_ROLES = {
    "ADAPTER",
    "CLIENT",
    "ERROR",
    "PROJECTION",
    "READER",
    "VERIFIER",
}
FORBIDDEN_LOCAL_OWNERS = {"ordivon", "local", "custom", "self"}


def _top_level_classes(root: Path) -> set[str]:
    classes: set[str] = set()
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        classes.update(
            node.name for node in tree.body if isinstance(node, ast.ClassDef)
        )
    return classes


def _load_profile() -> dict:
    if not PROFILE_PATH.exists():
        raise AssertionError(
            "CORE_ZERO profile is missing; architecture-zero is still prose-only"
        )
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


class OrdivonCoreZeroEnforcementR3Tests(unittest.TestCase):
    def test_architectural_core_and_residuals_are_empty(self) -> None:
        profile = _load_profile()
        self.assertEqual(profile["architecturalCore"], "EMPTY")
        self.assertEqual(profile["acceptedIrreduciblePrimitives"], [])
        self.assertEqual(profile["residualCandidates"], [])

    def test_agent_service_top_level_type_vocabulary_can_only_shrink(self) -> None:
        profile = _load_profile()
        observed = _top_level_classes(AGENT_SERVICE)
        legacy_ceiling = set(
            profile["legacyTypeCeilings"]["agentServiceTopLevelClasses"]
        )
        approved = {
            entry["name"] for entry in profile["approvedPostBaselineTypes"]
        }

        unexpected = sorted(observed - legacy_ceiling - approved)
        self.assertEqual(
            unexpected,
            [],
            "new Agent Service top-level types require explicit external ownership "
            "and a non-authority role before admission",
        )

    def test_retired_legacy_types_cannot_reenter_the_ceiling_or_source(self) -> None:
        profile = _load_profile()
        observed = _top_level_classes(AGENT_SERVICE)
        legacy_ceiling = set(
            profile["legacyTypeCeilings"]["agentServiceTopLevelClasses"]
        )
        retired = set(profile["retiredLegacyTypes"])

        self.assertIn("CapabilityAdvertisement", retired)
        self.assertTrue(retired.isdisjoint(observed))
        self.assertTrue(retired.isdisjoint(legacy_ceiling))

    def test_post_baseline_types_cannot_become_local_semantic_authority(self) -> None:
        profile = _load_profile()
        for entry in profile["approvedPostBaselineTypes"]:
            self.assertIn(entry["role"], ALLOWED_NON_AUTHORITY_ROLES)
            self.assertFalse(entry["authoritative"])
            self.assertNotIn(entry["owner"].strip().lower(), FORBIDDEN_LOCAL_OWNERS)
            self.assertTrue(entry["canonicalReference"].startswith("https://"))

    def test_external_owner_registry_has_no_ordivon_owner(self) -> None:
        profile = _load_profile()
        owners = profile["externalOwners"]
        self.assertGreaterEqual(len(owners), 8)
        for owner in owners:
            self.assertNotEqual(owner["name"].strip().lower(), "ordivon")
            self.assertTrue(owner["canonicalReference"].startswith("https://"))

    def test_deletion_gates_are_behavioral_not_brand_based(self) -> None:
        profile = _load_profile()
        gates = set(profile["mandatoryDeletionGates"])
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
