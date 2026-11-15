"""Native unittest qualification: scoring, source binding, and nonclaims."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("episode_value_pilot", HERE / "pilot.py")
assert spec and spec.loader
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)


class ValuePilotTest(unittest.TestCase):
    def test_actual_source_binds_gold(self) -> None:
        witness, digests, gold = pilot.evidence()
        self.assertEqual(len(gold), len(pilot.CASES))
        self.assertEqual(
            gold,
            {
                "projectedEpisodes": "10007",
                "runtimeSucceeded": "8927",
                "runtimeFailed": "955",
                "harnessSucceededRefs": "35",
                "harnessCostCoverage": "2",
                "developmentEpisodes": "0",
                "judgeEpisodes": "0",
                "causalStanding": "NOT_IDENTIFIED",
                "retentionSchedule": "UNASSIGNED",
                "promotionDecision": "HOLD",
            },
        )
        self.assertEqual(len(digests), 3)
        self.assertEqual(
            witness["analysis"]["generalization"]["standing"], "NOT_IDENTIFIED"
        )

    def test_control_receives_no_document_observations(self) -> None:
        witness, _, gold = pilot.evidence()
        control = pilot.prompt("control", witness)
        treatment = pilot.prompt("evidence", witness)
        self.assertIn("NO SOURCE DOCUMENT EVIDENCE", control)
        self.assertNotIn("8927", control)
        self.assertNotIn("10007", control)
        self.assertIn('"succeeded":8927', treatment)
        self.assertIn('"runtime-r5c-v1":10000', treatment)
        self.assertNotIn("caseGoldSourceBound", treatment)
        self.assertEqual(set(gold), {case[0] for case in pilot.CASES})

    def test_literal_gold_and_valid_source_ref(self) -> None:
        _, _, gold = pilot.evidence()
        source = {case[0]: case[2] for case in pilot.CASES}
        response = {
            "answers": [
                {"id": k, "answer": v, "evidenceRef": source[k]}
                for k, v in gold.items()
            ]
        }
        scores = pilot.grade(response, gold)
        self.assertEqual(scores["correct"], len(gold))
        self.assertEqual(scores["unknown"], 0)
        self.assertEqual(scores["unsupported"], 0)
        self.assertEqual(scores["evidenceBackedCorrect"], len(gold))

    def test_unknown_is_abstention_not_factual_success(self) -> None:
        _, _, gold = pilot.evidence()
        response = {
            "answers": [{"id": k, "answer": "UNKNOWN", "evidenceRef": ""} for k in gold]
        }
        result = pilot.grade(response, gold)
        self.assertEqual(result["correct"], 0)
        self.assertEqual(result["unknown"], len(gold))
        self.assertEqual(result["unsupported"], 0)

    def test_false_assertion_and_wrong_reference_do_not_pass(self) -> None:
        _, _, gold = pilot.evidence()
        response = {
            "answers": [
                {
                    "id": k,
                    "answer": ("PROVEN" if k == "causalStanding" else v),
                    "evidenceRef": "analysis",
                }
                for k, v in gold.items()
            ]
        }
        scores = pilot.grade(response, gold)
        self.assertEqual(scores["unsupported"], 1)
        self.assertEqual(scores["correct"], len(gold) - 1)
        self.assertLess(scores["evidenceBackedCorrect"], len(gold) - 1)

    def test_duplicate_and_missing_cases_rejected(self) -> None:
        _, _, gold = pilot.evidence()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            pilot.grade(
                {
                    "answers": [
                        {
                            "id": "judgeEpisodes",
                            "answer": "0",
                            "evidenceRef": "analysis",
                        },
                        {
                            "id": "judgeEpisodes",
                            "answer": "0",
                            "evidenceRef": "analysis",
                        },
                    ]
                },
                gold,
            )
        with self.assertRaisesRegex(ValueError, "missing"):
            pilot.grade({"answers": []}, gold)

    def test_preregistration_deterministic_without_model(self) -> None:
        import subprocess

        with tempfile.TemporaryDirectory() as folder:
            a = Path(folder) / "first.json"
            b = Path(folder) / "second.json"
            for path in (a, b):
                subprocess.run(
                    ["python3", str(HERE / "pilot.py"), "--output", str(path)],
                    capture_output=True,
                    check=True,
                    text=True,
                )
            self.assertEqual(a.read_bytes(), b.read_bytes())
            record = json.loads(a.read_text())
            self.assertEqual(
                record["contract"]["assignment"],
                ["control", "evidence", "evidence", "control"],
            )
            self.assertEqual(record["runs"], [])


if __name__ == "__main__":
    unittest.main()
