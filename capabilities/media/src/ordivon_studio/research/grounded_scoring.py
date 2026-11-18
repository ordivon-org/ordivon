"""Provider receipt scoring and evidence validity; no task construction or I/O."""

from __future__ import annotations

import statistics
from collections.abc import Mapping, Sequence
from typing import Any

from .grounded_contracts import RELATION_LABELS, canonical_digest


def _group_results(receipt: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    raw = receipt.get("results")
    if not isinstance(raw, list):
        raise ValueError("provider receipt has no results array")
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in raw:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("taskId"), str)
            or not isinstance(item.get("result"), dict)
        ):
            raise ValueError("provider receipt result record is invalid")
        grouped.setdefault(item["taskId"], []).append(item)
    return grouped


def _relation_map(result: Mapping[str, Any]) -> dict[str, str]:
    judgments = result.get("judgments")
    if not isinstance(judgments, list):
        raise ValueError("relation result has no judgments")
    mapped: dict[str, str] = {}
    for item in judgments:
        if not isinstance(item, dict) or item.get("relation") not in RELATION_LABELS:
            raise ValueError("relation judgment is invalid")
        probe = str(item.get("probeId"))
        if probe in mapped:
            raise ValueError("duplicate probe judgment")
        mapped[probe] = str(item["relation"])
    return mapped


def _replicate_agreement(maps: Sequence[Mapping[str, str]]) -> float:
    if len(maps) < 2:
        return 1.0
    keys = sorted(set().union(*(set(item) for item in maps)))
    if not keys:
        return 1.0
    agreements = []
    for key in keys:
        values = [item.get(key) for item in maps]
        agreements.append(1.0 if len(set(values)) == 1 else 0.0)
    return statistics.fmean(agreements)


def _supplied_evidence_ids(task: Mapping[str, Any]) -> set[str]:
    payload = task.get("userPayload")
    if not isinstance(payload, dict):
        return set()
    raw = payload.get("evidence", payload.get("artifactEvidence", []))
    if not isinstance(raw, list):
        return set()
    return {
        str(item["evidenceId"])
        for item in raw
        if isinstance(item, dict) and isinstance(item.get("evidenceId"), str)
    }


def _grounding_validity(task: Mapping[str, Any], result: Mapping[str, Any]) -> float:
    supplied = _supplied_evidence_ids(task)
    kind = task.get("kind")
    checks: list[bool] = []
    if kind == "relation-probes":
        payload = task.get("userPayload")
        probes = payload.get("probes", []) if isinstance(payload, dict) else []
        probe_map = {
            str(item["probeId"]): {str(item["sourceEvidenceId"]), str(item["targetEvidenceId"])}
            for item in probes
            if isinstance(item, dict)
            and isinstance(item.get("probeId"), str)
            and isinstance(item.get("sourceEvidenceId"), str)
            and isinstance(item.get("targetEvidenceId"), str)
        }
        judgments = result.get("judgments", [])
        if not isinstance(judgments, list):
            return 0.0
        for item in judgments:
            if not isinstance(item, dict):
                checks.append(False)
                continue
            refs = item.get("evidenceIds")
            ref_set = (
                set(refs)
                if isinstance(refs, list) and all(isinstance(ref, str) for ref in refs)
                else set()
            )
            required = probe_map.get(str(item.get("probeId")), set())
            checks.append(
                bool(required) and required.issubset(ref_set) and ref_set.issubset(supplied)
            )
    elif kind == "timeline-checks":
        oracle = task.get("oracle")
        required_map = oracle.get("requiredEvidenceAny", {}) if isinstance(oracle, dict) else {}
        events = result.get("events", [])
        if not isinstance(events, list):
            return 0.0
        for item in events:
            if not isinstance(item, dict):
                checks.append(False)
                continue
            refs = item.get("evidenceIds")
            ref_set = (
                set(refs)
                if isinstance(refs, list) and all(isinstance(ref, str) for ref in refs)
                else set()
            )
            if not ref_set.issubset(supplied):
                checks.append(False)
                continue
            if bool(item.get("present")):
                required = set(required_map.get(str(item.get("eventId")), []))
                checks.append(bool(ref_set) and (not required or bool(ref_set & required)))
            else:
                checks.append(not ref_set)
    elif kind == "speech-acts":
        cues = result.get("cues", [])
        if not isinstance(cues, list):
            return 0.0
        for item in cues:
            if not isinstance(item, dict):
                checks.append(False)
                continue
            cue_id = str(item.get("cueId"))
            refs = item.get("evidenceIds")
            ref_set = (
                set(refs)
                if isinstance(refs, list) and all(isinstance(ref, str) for ref in refs)
                else set()
            )
            checks.append(cue_id in supplied and cue_id in ref_set and ref_set.issubset(supplied))
    elif kind == "comprehension-qa":
        answers = result.get("answers", [])
        if not isinstance(answers, list):
            return 0.0
        for item in answers:
            if not isinstance(item, dict):
                checks.append(False)
                continue
            refs = item.get("evidenceIds")
            ref_set = (
                set(refs)
                if isinstance(refs, list) and all(isinstance(ref, str) for ref in refs)
                else set()
            )
            if str(item.get("optionId")) == "O4":
                checks.append(not ref_set)
            else:
                checks.append(bool(ref_set) and ref_set.issubset(supplied))
    return statistics.fmean(checks) if checks else 0.0


def score_provider_receipt(bundle: Mapping[str, Any], receipt: Mapping[str, Any]) -> dict[str, Any]:
    tasks = {
        str(item["taskId"]): item for item in bundle.get("tasks", []) if isinstance(item, dict)
    }
    grouped = _group_results(receipt)
    missing = sorted(set(tasks) - set(grouped))
    extra = sorted(set(grouped) - set(tasks))
    task_scores: dict[str, Any] = {}
    relation_maps: dict[str, list[dict[str, str]]] = {}
    qa_maps: dict[str, list[dict[str, str]]] = {}

    for task_id, task in tasks.items():
        records = grouped.get(task_id, [])
        expected_replicates = int(task.get("replicates", 1))
        base = {"replicatesExpected": expected_replicates, "replicatesObserved": len(records)}
        kind = task.get("kind")
        if kind == "relation-probes":
            expected = task["oracle"]["relations"]
            maps = [_relation_map(record["result"]) for record in records]
            relation_maps[task_id] = maps
            correct = [
                sum(mapping.get(probe) == relation for probe, relation in expected.items())
                / len(expected)
                for mapping in maps
            ]
            base.update(
                {
                    "meanAccuracy": statistics.fmean(correct) if correct else 0.0,
                    "replicateAgreement": _replicate_agreement(maps),
                    "replicateAccuracies": correct,
                    "meanGroundingValidity": statistics.fmean(
                        _grounding_validity(task, record["result"]) for record in records
                    )
                    if records
                    else 0.0,
                }
            )
        elif kind == "timeline-checks":
            expected = task["oracle"]["presence"]
            accuracies = []
            grounding_rates = []
            for record in records:
                events = record["result"].get("events", [])
                mapped = {
                    str(item.get("eventId")): item for item in events if isinstance(item, dict)
                }
                accuracies.append(
                    sum(
                        bool(mapped.get(event, {}).get("present")) == present
                        for event, present in expected.items()
                    )
                    / len(expected)
                )
                grounding_rates.append(
                    sum(
                        (not bool(item.get("present"))) or bool(item.get("evidenceIds"))
                        for item in mapped.values()
                    )
                    / max(1, len(mapped))
                )
            base.update(
                {
                    "meanPresenceAccuracy": statistics.fmean(accuracies) if accuracies else 0.0,
                    "meanGroundingDiscipline": statistics.fmean(grounding_rates)
                    if grounding_rates
                    else 0.0,
                    "meanGroundingValidity": statistics.fmean(
                        _grounding_validity(task, record["result"]) for record in records
                    )
                    if records
                    else 0.0,
                }
            )
        elif kind == "speech-acts":
            expected = task["oracle"]["cues"]
            accuracies = []
            cue_maps = []
            for record in records:
                cues = record["result"].get("cues", [])
                mapped = {
                    str(item.get("cueId")): (item.get("speechAct"), item.get("polarity"))
                    for item in cues
                    if isinstance(item, dict)
                }
                cue_maps.append({key: f"{value[0]}:{value[1]}" for key, value in mapped.items()})
                accuracies.append(
                    sum(
                        mapped.get(cue) == (target["speechAct"], target["polarity"])
                        for cue, target in expected.items()
                    )
                    / len(expected)
                )
            base.update(
                {
                    "meanAccuracy": statistics.fmean(accuracies) if accuracies else 0.0,
                    "replicateAgreement": _replicate_agreement(cue_maps),
                    "meanGroundingValidity": statistics.fmean(
                        _grounding_validity(task, record["result"]) for record in records
                    )
                    if records
                    else 0.0,
                }
            )
        elif kind == "comprehension-qa":
            expected = task["oracle"]["answers"]
            substantive = task["oracle"]["substantiveAnswers"]
            stages = task["oracle"]["stages"]
            accuracies = []
            substantive_grounded_rates = []
            unsupported_assertion_rates = []
            abstention_rates = []
            stage_accs: dict[str, list[float]] = {
                "perception": [],
                "comprehension": [],
                "adaptation": [],
            }
            answer_maps = []
            supplied = _supplied_evidence_ids(task)
            for record in records:
                answers = record["result"].get("answers", [])
                answer_items = {
                    str(item.get("questionId")): item for item in answers if isinstance(item, dict)
                }
                mapped = {
                    question: str(item.get("optionId")) for question, item in answer_items.items()
                }
                answer_maps.append(mapped)
                accuracies.append(
                    sum(mapped.get(q) == answer for q, answer in expected.items()) / len(expected)
                )
                substantive_checks = []
                unsupported_checks = []
                for question, target in substantive.items():
                    item = answer_items.get(question, {})
                    option = str(item.get("optionId"))
                    refs = item.get("evidenceIds")
                    ref_set = (
                        set(refs)
                        if isinstance(refs, list) and all(isinstance(ref, str) for ref in refs)
                        else set()
                    )
                    grounded = bool(ref_set) and ref_set.issubset(supplied)
                    substantive_checks.append(option == target and option != "O4" and grounded)
                    unsupported_checks.append(option != "O4" and not grounded)
                substantive_grounded_rates.append(sum(substantive_checks) / len(substantive_checks))
                unsupported_assertion_rates.append(
                    sum(unsupported_checks) / len(unsupported_checks)
                )
                abstention_rates.append(
                    sum(option == "O4" for option in mapped.values()) / len(expected)
                )
                for stage in stage_accs:
                    ids = [q for q, value in stages.items() if value == stage]
                    score = sum(mapped.get(q) == expected[q] for q in ids) / len(ids)
                    stage_accs[stage].append(score)
            qa_maps[task_id] = answer_maps
            base.update(
                {
                    "meanAccuracy": statistics.fmean(accuracies) if accuracies else 0.0,
                    "replicateAgreement": _replicate_agreement(answer_maps),
                    "stageAccuracy": {
                        stage: statistics.fmean(values) if values else 0.0
                        for stage, values in stage_accs.items()
                    },
                    "meanGroundingValidity": statistics.fmean(
                        _grounding_validity(task, record["result"]) for record in records
                    )
                    if records
                    else 0.0,
                    "groundedSubstantiveCorrectRate": statistics.fmean(substantive_grounded_rates)
                    if substantive_grounded_rates
                    else 0.0,
                    "unsupportedAssertionRate": statistics.fmean(unsupported_assertion_rates)
                    if unsupported_assertion_rates
                    else 0.0,
                    "abstentionRate": statistics.fmean(abstention_rates)
                    if abstention_rates
                    else 0.0,
                }
            )
        else:
            raise ValueError(f"unknown provider task kind: {kind}")
        task_scores[task_id] = base

    article_invariance = None
    baseline_maps = relation_maps.get("r5a:baseline", [])
    paraphrase_maps = relation_maps.get("r5a:paraphrase", [])
    if baseline_maps and paraphrase_maps:
        pairs = []
        for left, right in zip(baseline_maps, paraphrase_maps):
            keys = sorted(set(left) | set(right))
            pairs.append(sum(left.get(key) == right.get(key) for key in keys) / len(keys))
        article_invariance = statistics.fmean(pairs)

    omission_sensitivity = None
    baseline_events = task_scores.get("r5b:runtime-baseline", {})
    omitted_events = task_scores.get("r5b:runtime-recovery-omitted", {})
    if baseline_events and omitted_events:
        omission_sensitivity = min(
            float(baseline_events.get("meanPresenceAccuracy", 0.0)),
            float(omitted_events.get("meanPresenceAccuracy", 0.0)),
        )

    no_artifact_score = task_scores.get("r5e:no-artifact", {})
    no_artifact_epistemic = float(no_artifact_score.get("meanAccuracy", 0.0))
    no_artifact_unsupported = float(no_artifact_score.get("unsupportedAssertionRate", 0.0))
    artifact_task_ids = [
        f"r5e:{name}" for name in ("explicit-chain", "fragmented", "evidence-delayed")
    ]
    artifact_accuracies = [
        float(task_scores.get(task_id, {}).get("meanAccuracy", 0.0))
        for task_id in artifact_task_ids
    ]
    artifact_acquisition = [
        float(task_scores.get(task_id, {}).get("groundedSubstantiveCorrectRate", 0.0))
        for task_id in artifact_task_ids
    ]
    knowledge_acquisition = statistics.fmean(artifact_acquisition) if artifact_acquisition else 0.0

    order_agreements: list[float] = []
    explicit_maps = qa_maps.get("r5e:explicit-chain", [])
    for other_id in ("r5e:fragmented", "r5e:evidence-delayed"):
        other_maps = qa_maps.get(other_id, [])
        for left, right in zip(explicit_maps, other_maps):
            keys = sorted(set(left) | set(right))
            if keys:
                order_agreements.append(
                    sum(left.get(key) == right.get(key) for key in keys) / len(keys)
                )
    knowledge_order_invariance = statistics.fmean(order_agreements) if order_agreements else None

    grounding_values = [
        float(score.get("meanGroundingValidity", 0.0))
        for score in task_scores.values()
        if "meanGroundingValidity" in score
    ]

    summary = {
        "schemaVersion": 1,
        "kind": "ordivon.studio-r5-grounded-meaning-score",
        "bundleDigest": bundle.get("bundleDigest"),
        "providerReceiptDigest": canonical_digest(receipt),
        "missingTasks": missing,
        "extraTasks": extra,
        "taskScores": task_scores,
        "acceptanceSignals": {
            "articleParaphraseInvariance": article_invariance,
            "runtimeOmissionSensitivity": omission_sensitivity,
            "minimumTaskGroundingValidity": min(grounding_values) if grounding_values else 0.0,
            "meanTaskGroundingValidity": statistics.fmean(grounding_values)
            if grounding_values
            else 0.0,
            "agentObserverArtifactTaskAccuracy": statistics.fmean(artifact_accuracies)
            if artifact_accuracies
            else 0.0,
            "agentObserverKnowledgeAcquisitionRate": knowledge_acquisition,
            "agentObserverOrderInvariance": knowledge_order_invariance,
            "noArtifactEpistemicAccuracy": no_artifact_epistemic,
            "noArtifactUnsupportedAssertionRate": no_artifact_unsupported,
        },
        "claimBoundary": {
            "providerOutput": "candidate semantic observation only; Studio oracle scoring is independent admission",
            "video": "R5-B reasons over time-coded video-source semantics and narration, not native raw-video Provider perception",
            "speech": "R5-C reasons over exact transcript/timing, not ASR or prosodic perception",
            "consequence": "R5-E measures Agent-observer knowledge transfer on fictitious facts, not human comprehension",
        },
    }
    summary["scoreDigest"] = canonical_digest(summary)
    return summary
