from __future__ import annotations

import json
import unittest
from pathlib import Path

from artifact_core.bindings import CapabilityBindingRegistry
from artifact_core.profiles import ProfileRegistry

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "artifact-delivery"
PRESSURE = ROOT / "planning/evaluation-model-pressure-r1.json"


class ArtifactEvaluationPressureR1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.value = json.loads(PRESSURE.read_text(encoding="utf-8"))
        self.profiles = ProfileRegistry(ARTIFACT_ROOT)
        self.bindings = CapabilityBindingRegistry(ARTIFACT_ROOT)

    def test_pressure_result_is_bounded_not_false_unification(self) -> None:
        self.assertEqual(
            self.value["standing"],
            "REQUEST_MODEL_PASS_EVIDENCE_AND_STANDING_NORMALIZATION_OPEN",
        )
        self.assertIn(
            "OPEN_PRESSURE_TEST_REQUIRED",
            self.value["provisionalModel"]["EvidenceObservation"]["standing"],
        )

    def test_profile_claim_boundaries_equal_live_canonical_profiles(self) -> None:
        for case in self.value["cases"]:
            with self.subTest(profile=case["profileId"]):
                canonical = self.profiles.resolve(case["profileId"]).canonical
                self.assertEqual(
                    case["claimBoundary"]["requiredEvidence"],
                    canonical.get("requiredEvidence", {}),
                )
                self.assertEqual(
                    case["claimBoundary"]["targetAuthorities"],
                    canonical.get("targetAuthorities", []),
                )
                self.assertEqual(
                    case["claimBoundary"]["nonClaims"],
                    canonical.get("nonClaims", []),
                )

    def test_registered_cases_equal_live_capability_bindings(self) -> None:
        for case in self.value["cases"]:
            cap = case["evaluationRequest"]["capabilityRef"]
            if cap["mode"] != "REGISTERED_BINDING":
                continue
            binding = self.bindings.resolve(case["profileId"], "verify")
            self.assertEqual(cap["capabilityId"], binding.capability_id)
            self.assertEqual(cap["entrypoint"]["module"], binding.entrypoint.module)
            self.assertEqual(
                cap["entrypoint"]["callable"], binding.entrypoint.callable
            )
            self.assertEqual(
                cap["objectContractRequired"], binding.object_contract_required
            )
            self.assertEqual(cap["standing"], "LOCAL_LIVE_PROVEN")

    def test_legacy_cases_do_not_invent_capability_bindings(self) -> None:
        legacy = [
            case for case in self.value["cases"]
            if case["evaluationRequest"]["capabilityRef"]["mode"]
            == "COMPATIBILITY_ADAPTER_REQUIRED"
        ]
        self.assertEqual(
            {case["profileId"] for case in legacy},
            {"pdu-sdu-presentation-r1", "document-r1"},
        )
        live = json.loads(
            (ARTIFACT_ROOT / "capability-bindings-v1.json").read_text(
                encoding="utf-8"
            )
        )["bindings"]
        live_keys = {(item["profileId"], item["operation"]) for item in live}
        for case in legacy:
            self.assertNotIn((case["profileId"], "verify"), live_keys)

    def test_four_cases_cover_required_pressure_dimensions(self) -> None:
        cases = {case["profileId"]: case for case in self.value["cases"]}
        self.assertEqual(len(cases), 4)
        self.assertEqual(
            cases["audio-wave-pcm16-r1"]["evaluationRequest"]["capabilityRef"][
                "objectContractRequired"
            ],
            True,
        )
        self.assertEqual(
            cases["still-image-png-srgb-r1"]["evaluationRequest"]["capabilityRef"][
                "objectContractRequired"
            ],
            False,
        )
        self.assertEqual(
            cases["document-r1"]["currentResultMode"],
            "MULTI_GATE_STAGE_RECEIPTS_PLUS_PROFILE_VERIFICATION_COMPLETE",
        )
        self.assertEqual(
            cases["audio-wave-pcm16-r1"]["currentResultMode"],
            "DELEGATED_BOUNDED_FAMILY_RESULT",
        )


if __name__ == "__main__":
    unittest.main()
