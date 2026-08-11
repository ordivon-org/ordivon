from __future__ import annotations

import json
import unittest
from pathlib import Path

from ordivon_studio.grounded_meaning import (
    build_provider_bundle,
    canonical_digest,
    narration_evidence,
    parse_runtime_scenes,
    score_provider_receipt,
    validate_grounded_result,
)


ROOT = Path(__file__).resolve().parents[1]


class GroundedMeaningTest(unittest.TestCase):
    def test_runtime_scene_source_is_time_grounded(self) -> None:
        source = (ROOT / "apps/motion-remotion/src/runtime-introduction-master-composition.tsx").read_text(encoding="utf-8")
        scenes = parse_runtime_scenes(source)
        self.assertEqual(len(scenes), 11)
        self.assertEqual(scenes[0]["locator"]["startMs"], 0)
        self.assertEqual(scenes[0]["locator"]["endMs"], 6000)
        self.assertEqual(scenes[-1]["locator"]["startMs"], 74000)
        self.assertEqual(scenes[-1]["locator"]["endMs"], 78000)
        self.assertIn("semantic Task completion", scenes[-2]["observed"])

    def test_narration_evidence_preserves_exact_cue_time(self) -> None:
        timed = json.loads((ROOT / "productions/runtime-introduction/timed-text/narration.en.json").read_text(encoding="utf-8"))
        evidence = narration_evidence(timed)
        self.assertEqual(len(evidence), 9)
        self.assertEqual(evidence[4]["evidenceId"], "en-005")
        self.assertEqual(evidence[4]["locator"], {"startMs": 37000, "endMs": 48000})

    def test_grounded_result_rejects_unknown_evidence(self) -> None:
        evidence = [{"evidenceId": "E1", "modality": "text", "sourceId": "fixture", "locator": {"segmentId": "S1"}, "observed": "one fact"}]
        with self.assertRaises(ValueError):
            validate_grounded_result({"claims": [{"claimId": "C1", "statement": "claim", "evidenceIds": ["MISSING"]}], "relations": []}, evidence)

    def test_provider_bundle_covers_r5_without_secret_or_oracle_leakage(self) -> None:
        bundle = build_provider_bundle(root=ROOT, replicates=2)
        task_ids = {task["taskId"] for task in bundle["tasks"]}
        self.assertEqual(len(bundle["tasks"]), 14)
        for task_id in ("r5a:baseline", "r5b:runtime-baseline", "r5c:baseline", "r5d:crossmodal-relations", "r5e:explicit-chain"):
            self.assertIn(task_id, task_ids)
        serialized = json.dumps(bundle)
        self.assertNotIn("apiKey", serialized)
        self.assertNotIn("secrets/deepseek", serialized)
        for task in bundle["tasks"]:
            provider_payload = json.dumps(task["userPayload"], sort_keys=True)
            self.assertNotIn("expectedRelation", provider_payload)
            self.assertNotIn("expectedPresent", provider_payload)
            self.assertNotIn("requiredEvidenceAny", provider_payload)
            self.assertNotIn('"answer"', provider_payload)
        omission = next(task for task in bundle["tasks"] if task["taskId"] == "r5b:runtime-recovery-omitted")
        omitted_ids = {item["evidenceId"] for item in omission["userPayload"]["evidence"]}
        self.assertTrue({"V02", "V05", "V06", "V11", "en-002", "en-005", "en-009"}.isdisjoint(omitted_ids))
        without_digest = {k: v for k, v in bundle.items() if k != "bundleDigest"}
        self.assertEqual(canonical_digest(without_digest), bundle["bundleDigest"])

    def test_controlled_variants_change_only_target_oracle_relations(self) -> None:
        bundle = build_provider_bundle(root=ROOT, replicates=1)
        tasks = {task["taskId"]: task for task in bundle["tasks"]}
        base = tasks["r5a:baseline"]["oracle"]["relations"]
        paraphrase = tasks["r5a:paraphrase"]["oracle"]["relations"]
        causal_break = tasks["r5a:causal-break"]["oracle"]["relations"]
        contradiction = tasks["r5a:contradiction"]["oracle"]["relations"]
        self.assertEqual(base, paraphrase)
        self.assertNotEqual(base["P45"], causal_break["P45"])
        self.assertNotEqual(base["P12"], contradiction["P12"])
        speech_flip = tasks["r5c:boundary-polarity-flip"]["oracle"]["cues"]["en-008"]
        self.assertEqual(speech_flip, {"speechAct": "OTHER", "polarity": "affirmed"})

    def test_perfect_provider_receipt_scores_grounding_and_knowledge_acquisition(self) -> None:
        bundle = build_provider_bundle(root=ROOT, replicates=2)
        results = []
        for task in bundle["tasks"]:
            for replicate in range(1, task["replicates"] + 1):
                kind = task["kind"]
                if kind == "relation-probes":
                    probes = {item["probeId"]: item for item in task["userPayload"]["probes"]}
                    result = {
                        "judgments": [
                            {
                                "probeId": probe,
                                "relation": relation,
                                "evidenceIds": [probes[probe]["sourceEvidenceId"], probes[probe]["targetEvidenceId"]],
                                "uncertainty": "low",
                            }
                            for probe, relation in task["oracle"]["relations"].items()
                        ]
                    }
                elif kind == "timeline-checks":
                    required = task["oracle"]["requiredEvidenceAny"]
                    result = {
                        "events": [
                            {
                                "eventId": event,
                                "present": present,
                                "summary": "oracle event" if present else "absent",
                                "evidenceIds": ([next(ref for ref in required[event] if ref in {item["evidenceId"] for item in task["userPayload"]["evidence"]})] if present else []),
                            }
                            for event, present in task["oracle"]["presence"].items()
                        ]
                    }
                elif kind == "speech-acts":
                    result = {
                        "cues": [
                            {"cueId": cue, "speechAct": target["speechAct"], "polarity": target["polarity"], "evidenceIds": [cue]}
                            for cue, target in task["oracle"]["cues"].items()
                        ]
                    }
                elif kind == "comprehension-qa":
                    available = [item["evidenceId"] for item in task["userPayload"]["artifactEvidence"]]
                    result = {
                        "answers": [
                            {
                                "questionId": q,
                                "optionId": option,
                                "evidenceIds": ([] if option == "O4" else [available[0]]),
                            }
                            for q, option in task["oracle"]["answers"].items()
                        ]
                    }
                else:
                    self.fail(kind)
                results.append({"taskId": task["taskId"], "replicate": replicate, "result": result})
        receipt = {"schemaVersion": 1, "kind": "test-provider-receipt", "results": results}
        score = score_provider_receipt(bundle, receipt)
        self.assertEqual(score["missingTasks"], [])
        self.assertEqual(score["extraTasks"], [])
        signals = score["acceptanceSignals"]
        self.assertEqual(signals["articleParaphraseInvariance"], 1.0)
        self.assertEqual(signals["runtimeOmissionSensitivity"], 1.0)
        self.assertEqual(signals["minimumTaskGroundingValidity"], 1.0)
        self.assertEqual(signals["agentObserverKnowledgeAcquisitionRate"], 1.0)
        self.assertEqual(signals["agentObserverOrderInvariance"], 1.0)
        self.assertEqual(signals["noArtifactEpistemicAccuracy"], 1.0)
        self.assertEqual(signals["noArtifactUnsupportedAssertionRate"], 0.0)

    def test_unsupported_no_artifact_assertions_are_separate_from_abstention_accuracy(self) -> None:
        bundle = build_provider_bundle(root=ROOT, replicates=1)
        task = next(task for task in bundle["tasks"] if task["taskId"] == "r5e:no-artifact")
        guessed = {
            "answers": [
                {"questionId": q, "optionId": task["oracle"]["substantiveAnswers"][q], "evidenceIds": []}
                for q in task["oracle"]["answers"]
            ]
        }
        receipt = {"schemaVersion": 1, "kind": "test-provider-receipt", "results": [{"taskId": task["taskId"], "replicate": 1, "result": guessed}]}
        score = score_provider_receipt(bundle, receipt)
        task_score = score["taskScores"]["r5e:no-artifact"]
        self.assertEqual(task_score["meanAccuracy"], 0.0)
        self.assertEqual(task_score["groundedSubstantiveCorrectRate"], 0.0)
        self.assertEqual(task_score["unsupportedAssertionRate"], 1.0)
        self.assertEqual(task_score["meanGroundingValidity"], 0.0)


if __name__ == "__main__":
    unittest.main()
