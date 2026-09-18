from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PRESSURE = ROOT / "planning/evidence-standing-pressure-r1.json"


class ArtifactEvidenceStandingPressureR1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.value = json.loads(PRESSURE.read_text(encoding="utf-8"))
        self.cases = {item["id"]: item for item in self.value["cases"]}

    def test_scalar_standing_is_explicitly_rejected(self) -> None:
        self.assertEqual(
            self.value["standing"],
            "COMMON_OBSERVATION_ENVELOPE_PLAUSIBLE_SINGLE_SCALAR_STANDING_REJECTED",
        )
        self.assertEqual(
            self.value["candidateStandingDecision"]["shape"],
            "MULTI_AXIS_VECTOR",
        )

    def test_standing_vector_keeps_consumer_acceptance_external(self) -> None:
        for case_id in ("wave-consumer-smoke", "png-consumer-smoke"):
            standing = self.cases[case_id]["standingProjection"]
            self.assertEqual(
                standing["consumerDomainAcceptanceKernelStanding"],
                "EXTERNAL_NOT_KERNEL",
            )
            self.assertEqual(standing["profileAuthority"], "SHADOW")

    def test_presentation_projection_preserves_frozen_receipt_statuses(self) -> None:
        src = json.loads(
            (
                ROOT
                / "artifact-delivery/golden/pdu-sdu-34x10-r1/pdu-sdu-34x10-acceptance-r2.json"
            ).read_text(encoding="utf-8")
        )
        case = self.cases["presentation-golden-r2"]
        by_kind = {item["observationKind"]: item for item in case["observations"]}
        self.assertEqual(by_kind["structural"]["status"], src["structuralEvidence"]["status"])
        self.assertEqual(by_kind["target"]["status"], src["targetEvidence"]["status"])
        self.assertEqual(by_kind["visual"]["status"], src["visualEvidence"]["status"])
        self.assertEqual(
            by_kind["aggregateFinalGate"]["status"], src["finalGate"]["status"]
        )
        self.assertEqual(case["standingProjection"]["nonClaims"], src["nonClaims"])

    def test_family_projection_preserves_source_verification_statuses(self) -> None:
        wave = json.loads(
            (
                ROOT
                / "artifact-delivery/consumer-acceptance/game-veilwild-wave-pcm16-r1.json"
            ).read_text(encoding="utf-8")
        )
        case = self.cases["wave-consumer-smoke"]
        by_kind = {item["observationKind"]: item for item in case["observations"]}
        self.assertEqual(
            by_kind["decoderMatrix"]["status"],
            wave["verification"]["decoderMatrixStatus"],
        )
        self.assertEqual(
            by_kind["familyVerifier"]["status"],
            wave["verification"]["familyStatus"],
        )
        self.assertEqual(
            by_kind["verificationService"]["status"],
            wave["verification"]["serviceStatus"],
        )

    def test_trust_and_release_are_not_inferred_from_verification_pass(self) -> None:
        for case in self.value["cases"]:
            standing = case["standingProjection"]
            self.assertEqual(standing["trustStatus"], "NOT_EVALUATED")
            self.assertEqual(standing["releaseStatus"], "NOT_EVALUATED")


if __name__ == "__main__":
    unittest.main()
