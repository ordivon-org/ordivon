from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "system1_decision_benchmark.py"
spec = importlib.util.spec_from_file_location("system1_decision_benchmark", SCRIPT)
assert spec and spec.loader
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)


class System1DecisionBenchmarkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.corpus = B.load_corpus()

    def observation(self) -> dict:
        rows = []
        for case in self.corpus["cases"]:
            label = case["expected"]["category"]
            keys = list(self.corpus["questions"]["category"]["criteria"])
            probs = {key: (1.0 if key == label else 0.0) for key in keys}
            actionable = 0.9 if case["expected"]["actionable_for_student"] else 0.1
            rows.append({
                "caseId": case["caseId"],
                "caseDigest": case["caseDigest"],
                "standing": "EXECUTED",
                "latencyMs": 10.0,
                "answers": {
                    "category": {"choice": label, "probabilities": probs},
                    "actionable_for_student": {"noul": actionable},
                },
            })
        return {
            "schemaVersion": 1,
            "kind": "ordivon.system1-decision-benchmark-observation",
            "corpusDigest": self.corpus["corpusDigest"],
            "provider": {"providerId": "fake-perfect", "model": "fixture"},
            "cases": rows,
        }

    def test_default_corpus_is_explicitly_synthetic_and_digest_bound(self) -> None:
        self.assertEqual(self.corpus["standing"], "SYNTHETIC_SMOKE_ONLY")
        self.assertEqual(len(self.corpus["cases"]), 30)
        self.assertTrue(self.corpus["corpusDigest"].startswith("sha256:"))

    def test_perfect_provider_scores(self) -> None:
        score = B.score_observation(self.observation(), self.corpus)
        self.assertEqual(score["coverage"]["fraction"], 1.0)
        self.assertEqual(score["choice"]["accuracy"], 1.0)
        self.assertEqual(score["choice"]["meanBrier"], 0.0)
        self.assertEqual(score["noul"]["accuracyAt0_5"], 1.0)
        self.assertEqual(score["latencyMs"]["median"], 10.0)

    def test_blocked_case_does_not_become_wrong_or_zero_latency(self) -> None:
        obs = self.observation()
        obs["cases"][0]["standing"] = "BLOCKED"
        obs["cases"][0]["latencyMs"] = None
        obs["cases"][0]["answers"] = None
        score = B.score_observation(obs, self.corpus)
        self.assertEqual(score["coverage"]["executedCases"], 29)
        self.assertEqual(score["coverage"]["standings"]["BLOCKED"], 1)
        self.assertEqual(score["choice"]["accuracy"], 1.0)

    def test_blocked_case_cannot_carry_fake_zero_latency(self) -> None:
        obs = self.observation()
        obs["cases"][0]["standing"] = "BLOCKED"
        obs["cases"][0]["answers"] = None
        obs["cases"][0]["latencyMs"] = 0
        with self.assertRaisesRegex(ValueError, "cannot carry latency"):
            B.validate_observation(obs, self.corpus)

    def test_probability_key_drift_is_rejected(self) -> None:
        obs = self.observation()
        del obs["cases"][0]["answers"]["category"]["probabilities"]["research"]
        with self.assertRaisesRegex(ValueError, "probability key set mismatch"):
            B.validate_observation(obs, self.corpus)

    def test_case_identity_drift_is_rejected(self) -> None:
        obs = self.observation()
        obs["cases"][0]["caseDigest"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ValueError, "caseDigest mismatch"):
            B.validate_observation(obs, self.corpus)

    def test_bad_probability_mass_is_rejected(self) -> None:
        obs = self.observation()
        probs = obs["cases"][0]["answers"]["category"]["probabilities"]
        for key in probs:
            probs[key] = 0.5
        with self.assertRaisesRegex(ValueError, "do not sum to one"):
            B.validate_observation(obs, self.corpus)


if __name__ == "__main__":
    unittest.main()


def dynamic_corpus() -> dict:
    raw = {
        "schemaVersion": 1,
        "kind": "ordivon.system1-decision-corpus",
        "corpusId": "dynamic-choice-fixture",
        "standing": "CONTROLLED_FIXTURE_ONLY",
        "nonClaims": ["representative_population"],
        "questions": {
            "target": {
                "type": "dynamic_choice",
                "candidateSetField": "candidates",
                "instructions": "Choose the candidate that fulfills the goal.",
            }
        },
        "cases": [
            {
                "caseId": "d1",
                "state": {
                    "goal": "Apply",
                    "candidates": [
                        {"candidateId": "a", "text": "How to apply"},
                        {"candidateId": "b", "text": "Apply now"},
                        {"candidateId": "c", "text": "Deadline"},
                    ],
                },
                "expected": {"target": "b"},
            },
            {
                "caseId": "d2",
                "state": {
                    "goal": "Register",
                    "candidates": [
                        {"candidateId": "x", "text": "FAQ"},
                        {"candidateId": "y", "text": "Register now"},
                    ],
                },
                "expected": {"target": "y"},
            },
        ],
    }
    import json
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "corpus.json"
        path.write_text(json.dumps(raw), encoding="utf-8")
        return B.load_corpus(path)


class DynamicChoiceSystem1DecisionBenchmarkTests(unittest.TestCase):
    def test_dynamic_choice_scores_variable_candidate_sets(self) -> None:
        corpus = dynamic_corpus()
        rows = []
        observations = {
            "d1": {"choice": "b", "probabilities": {"a": 0.1, "b": 0.8, "c": 0.1}},
            "d2": {"choice": "x", "probabilities": {"x": 0.6, "y": 0.4}},
        }
        for case in corpus["cases"]:
            rows.append(
                {
                    "caseId": case["caseId"],
                    "caseDigest": case["caseDigest"],
                    "standing": "EXECUTED",
                    "latencyMs": 5.0,
                    "answers": {"target": observations[case["caseId"]]},
                }
            )
        obs = {
            "schemaVersion": 1,
            "kind": "ordivon.system1-decision-benchmark-observation",
            "corpusDigest": corpus["corpusDigest"],
            "provider": {"providerId": "dynamic-fixture"},
            "cases": rows,
        }

        score = B.score_observation(obs, corpus)

        self.assertEqual(score["choice"]["accuracy"], 0.5)
        self.assertEqual(score["choice"]["meanExpectedRank"], 1.5)
        self.assertEqual(score["choice"]["meanReciprocalRank"], 0.75)

    def test_dynamic_choice_rejects_probability_key_drift(self) -> None:
        corpus = dynamic_corpus()
        rows = []
        for index, case in enumerate(corpus["cases"]):
            if index == 0:
                answer = {
                    "target": {
                        "choice": "b",
                        "probabilities": {"a": 0.5, "b": 0.5},
                    }
                }
                standing = "EXECUTED"
                latency = 1.0
            else:
                answer = None
                standing = "BLOCKED"
                latency = None
            rows.append(
                {
                    "caseId": case["caseId"],
                    "caseDigest": case["caseDigest"],
                    "standing": standing,
                    "latencyMs": latency,
                    "answers": answer,
                }
            )
        obs = {
            "schemaVersion": 1,
            "kind": "ordivon.system1-decision-benchmark-observation",
            "corpusDigest": corpus["corpusDigest"],
            "provider": {"providerId": "bad"},
            "cases": rows,
        }
        with self.assertRaisesRegex(ValueError, "probability key set mismatch"):
            B.validate_observation(obs, corpus)

    def test_dynamic_choice_requires_expected_candidate_to_exist(self) -> None:
        import json
        import tempfile

        raw = {
            "schemaVersion": 1,
            "kind": "ordivon.system1-decision-corpus",
            "corpusId": "bad-dynamic",
            "standing": "CONTROLLED_FIXTURE_ONLY",
            "questions": {
                "target": {
                    "type": "dynamic_choice",
                    "candidateSetField": "candidates",
                }
            },
            "cases": [
                {
                    "caseId": "x",
                    "state": {
                        "candidates": [
                            {"candidateId": "a"},
                            {"candidateId": "b"},
                        ]
                    },
                    "expected": {"target": "missing"},
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unknown expected dynamic choice"):
                B.load_corpus(path)


class ExternalBenchmarkCorpusTests(unittest.TestCase):
    def test_external_benchmark_requires_source_provenance(self) -> None:
        import json
        import tempfile

        raw = {
            "schemaVersion": 1,
            "kind": "ordivon.system1-decision-corpus",
            "corpusId": "external",
            "standing": "EXTERNAL_BENCHMARK",
            "questions": {
                "target": {
                    "type": "dynamic_choice",
                    "candidateSetField": "candidates",
                }
            },
            "cases": [{
                "caseId": "x",
                "state": {
                    "candidates": [
                        {"candidateId": "a"},
                        {"candidateId": "b"},
                    ]
                },
                "expected": {"target": "a"},
            }],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "external.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "requires source provenance"):
                B.load_corpus(path)

    def test_external_benchmark_source_is_digest_bound(self) -> None:
        import json
        import tempfile

        raw = {
            "schemaVersion": 1,
            "kind": "ordivon.system1-decision-corpus",
            "corpusId": "external",
            "standing": "EXTERNAL_BENCHMARK",
            "source": {"dataset": "fixture", "revision": "abc"},
            "questions": {
                "target": {
                    "type": "dynamic_choice",
                    "candidateSetField": "candidates",
                }
            },
            "cases": [{
                "caseId": "x",
                "state": {
                    "candidates": [
                        {"candidateId": "a"},
                        {"candidateId": "b"},
                    ]
                },
                "expected": {"target": "a"},
            }],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "external.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            first = B.load_corpus(path)
            raw["source"]["revision"] = "def"
            path.write_text(json.dumps(raw), encoding="utf-8")
            second = B.load_corpus(path)
        self.assertEqual(first["standing"], "EXTERNAL_BENCHMARK")
        self.assertNotEqual(first["corpusDigest"], second["corpusDigest"])
