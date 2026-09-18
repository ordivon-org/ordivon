from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class LegoQuestionCompilerOutcomePressureR1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.analysis = json.loads(
            (ROOT / "evidence/analysis/lego-question-compiler-outcome-pressure-r1.json").read_text(encoding="utf-8")
        )
        cls.acceptance = json.loads(
            (ROOT / "evidence/acceptance/lego-question-compiler-outcome-pressure-r1.json").read_text(encoding="utf-8")
        )

    def test_agent_census_closes(self):
        a = self.analysis["agentBirth"]
        self.assertEqual(sum(a["standingCounts"].values()), a["source"]["rowCount"])
        self.assertFalse(a["observationGap"]["transitionHistoryAvailableInBirthLedger"])
        self.assertFalse(a["observationGap"]["trueRecoveryLatencyIdentified"])

    def test_control_stability_does_not_self_promote(self):
        c = self.analysis["agentBirth"]["controlStability"]
        self.assertEqual(sum(c["classificationCounts"].values()), c["scenarioCount"])
        self.assertEqual(c["firstRecommendedProductionChange"], "FRESHNESS_CONSERVATION")
        self.assertTrue(c["noProductionControlLawPromoted"])

    def test_paper2_first_pass_counts_close(self):
        p = self.analysis["researchPaper2"]["titleAbstractFirstPass"]
        self.assertEqual(p["agreement"] + p["disagreements"], p["pairedRecords"])
        self.assertEqual(p["reviewerA"]["records"], p["pairedRecords"])
        self.assertEqual(p["reviewerB"]["records"], p["pairedRecords"])
        self.assertEqual(p["combined"]["reviewerRecords"], 2 * p["pairedRecords"])

    def test_fulltext_queue_closes(self):
        f = self.analysis["researchPaper2"]["fulltext"]
        self.assertEqual(
            f["localPdfReady"] + f["retrievalBoundaryReviewRequired"],
            f["escalationRecords"],
        )
        self.assertTrue(f["acquisitionRoutesMechanicallyClosed"])
        self.assertFalse(f["acquisitionClosureIsEligibilityClosure"])

    def test_stage2_keeps_human_authority_boundary(self):
        s = self.analysis["researchPaper2"]["stage2"]
        self.assertEqual(s["status"], "CALIBRATION_OPEN_FINAL_ELIGIBILITY_CLOSED")
        self.assertEqual(s["calibrationReports"], 8)
        self.assertFalse(s["automaticMergeAllowed"])
        self.assertIn("two people", s["finalHumanIndependenceBoundary"])

    def test_acceptance_blocks_outcome_claim_and_schema_promotion(self):
        self.assertEqual(
            self.acceptance["verdict"],
            "PASS_DECISION_ALLOCATION_EFFECT__BLOCK_OUTCOME_PROMOTION",
        )
        self.assertFalse(self.acceptance["promotion"]["questionCompilerOutcomeValidated"])
        self.assertFalse(self.acceptance["promotion"]["commonSchemaExpansion"])


if __name__ == "__main__":
    unittest.main()
