"""Synthetic, controlled text-relation and knowledge-transfer R5 tasks.

These fixtures are experimental Agent observations, not literary quality claims.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .grounded_evidence import EvidenceItem, _relation_result_schema


def _qa_result_schema(question_ids: Sequence[str], option_ids: Sequence[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "answers": {
                "type": "array",
                "minItems": len(question_ids),
                "maxItems": len(question_ids),
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "questionId": {"type": "string", "enum": list(question_ids)},
                        "optionId": {"type": "string", "enum": list(option_ids)},
                        "evidenceIds": {
                            "type": "array",
                            "maxItems": 6,
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["questionId", "optionId", "evidenceIds"],
                },
            }
        },
        "required": ["answers"],
    }


def _article_variants() -> dict[str, dict[str, str]]:
    baseline = {
        "A1": "The first visible symptom of a failed Heliox startup is a stalled Varo spindle.",
        "A2": "However, the actual starting fault is upstream in the coolant chain, so the visible symptom is not the first cause.",
        "A3": "When the Neral gauge reaches 7, the amber latch opens.",
        "A4": "Opening the amber latch sends coolant into the blue chamber, and that coolant begins the chamber-cooling step.",
        "A5": "Because the coolant lowers the chamber below 40 degrees, the spindle can then rotate safely.",
        "A6": "Therefore, if the chamber remains above 40 degrees, the spindle must not rotate.",
    }
    paraphrase = {
        "A1": "A stalled Varo spindle is the first symptom operators can see when Heliox startup fails.",
        "A2": "Yet the initiating fault lies earlier in the coolant chain; the visible stall is an effect rather than the initial cause.",
        "A3": "The amber latch opens once the Neral gauge reaches 7.",
        "A4": "That open latch admits coolant to the blue chamber and starts cooling it.",
        "A5": "The coolant drives the chamber under 40 degrees, which permits safe spindle rotation.",
        "A6": "So the spindle must remain stopped whenever chamber temperature stays above 40 degrees.",
    }
    causal_break = dict(baseline)
    causal_break["A5"] = "Despite coolant entering the chamber, coolant does not cool it; an independent heater controller alone determines whether the chamber falls below 40 degrees."
    contradiction = dict(baseline)
    contradiction["A2"] = "In fact the Varo spindle is not stalled during the startup failure; it is rotating normally."
    return {
        "baseline": baseline,
        "paraphrase": paraphrase,
        "causal-break": causal_break,
        "contradiction": contradiction,
    }


def _article_probes(variant: str) -> list[dict[str, Any]]:
    expected = {
        "P12": "CONTRASTS" if variant != "contradiction" else "CONTRADICTS",
        "P34": "CAUSES",
        "P45": "CAUSES" if variant != "causal-break" else "CONTRADICTS",
        "P56": "SUPPORTS" if variant != "causal-break" else "NONE",
    }
    pairs = {
        "P12": ("A1", "A2"),
        "P34": ("A3", "A4"),
        "P45": ("A4", "A5"),
        "P56": ("A5", "A6"),
    }
    return [
        {"probeId": probe_id, "sourceEvidenceId": pair[0], "targetEvidenceId": pair[1], "expectedRelation": expected[probe_id]}
        for probe_id, pair in pairs.items()
    ]


def build_article_tasks(*, replicates: int = 2) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for variant, segments in _article_variants().items():
        evidence = [
            EvidenceItem(segment_id, "text", f"synthetic-heliox-article:{variant}", {"segmentId": segment_id}, text).to_dict()
            for segment_id, text in segments.items()
        ]
        probes = _article_probes(variant)
        tasks.append(
            {
                "taskId": f"r5a:{variant}",
                "kind": "relation-probes",
                "replicates": replicates,
                "systemPrompt": (
                    "You are a bounded discourse-relation annotator. Judge only the specified evidence pairs. "
                    "Do not infer popularity, quality, author intent, or facts outside the supplied segments. "
                    "Return exactly one relation for each probe. Evidence IDs must name only supplied segments. "
                    "Use CONTRADICTS when the target explicitly rejects or reverses the source claim; use NONE when no listed relation is supported."
                ),
                "userPayload": {
                    "evidence": evidence,
                    "probes": [
                        {key: item[key] for key in ("probeId", "sourceEvidenceId", "targetEvidenceId")}
                        for item in probes
                    ],
                },
                "resultSchema": _relation_result_schema(probes),
                "oracle": {"relations": {item["probeId"]: item["expectedRelation"] for item in probes}},
                "scope": "synthetic controlled writing fixture; relation labels are experimental probes, not a universal discourse ontology",
            }
        )
    return tasks


def _knowledge_artifacts() -> dict[str, list[tuple[str, str]]]:
    facts = [
        ("K1", "In the fictitious Heliox rig, the Neral gauge reaching 7 causes the amber latch to open."),
        ("K2", "When the amber latch opens, coolant enters the blue chamber."),
        ("K3", "Coolant in the blue chamber lowers its temperature below 40 degrees."),
        ("K4", "Only a blue chamber below 40 degrees permits the Varo spindle to rotate safely."),
        ("K5", "If the Neral gauge stays below 7, the amber latch remains closed and the spindle must not rotate."),
    ]
    return {
        "explicit-chain": facts,
        "fragmented": [facts[3], facts[0], facts[4], facts[2], facts[1]],
        "evidence-delayed": [facts[1], facts[2], facts[3], facts[4], facts[0]],
        "no-artifact": [],
    }


def build_comprehension_tasks(*, replicates: int = 2) -> list[dict[str, Any]]:
    questions = [
        {"questionId": "Q1", "stage": "perception", "question": "What gauge reading is the stated trigger for the amber latch to open?", "options": {"O1": "7", "O2": "40", "O3": "55", "O4": "The artifact does not say"}, "answer": "O1"},
        {"questionId": "Q2", "stage": "perception", "question": "What directly happens when the amber latch opens?", "options": {"O1": "The spindle stops", "O2": "Coolant enters the blue chamber", "O3": "The gauge falls to zero", "O4": "The artifact does not say"}, "answer": "O2"},
        {"questionId": "Q3", "stage": "comprehension", "question": "Why must the chamber fall below 40 degrees in this fictitious mechanism?", "options": {"O1": "It permits safe spindle rotation", "O2": "It opens the latch", "O3": "It raises the gauge", "O4": "The artifact does not say"}, "answer": "O1"},
        {"questionId": "Q4", "stage": "comprehension", "question": "If the gauge is 5, what does the artifact imply?", "options": {"O1": "The latch stays closed and the spindle must not rotate", "O2": "The latch opens immediately", "O3": "The spindle rotates faster", "O4": "The artifact does not say"}, "answer": "O1"},
        {"questionId": "Q5", "stage": "adaptation", "question": "Gauge=8, latch=open, coolant flows, chamber=35. Is safe spindle rotation permitted by the stated mechanism?", "options": {"O1": "Yes", "O2": "No", "O3": "Only if the gauge drops", "O4": "The artifact does not say"}, "answer": "O1"},
        {"questionId": "Q6", "stage": "adaptation", "question": "Gauge=8 and latch=open, but coolant fails and chamber remains at 55. Is safe spindle rotation permitted?", "options": {"O1": "Yes", "O2": "No", "O3": "Only if the latch closes", "O4": "The artifact does not say"}, "answer": "O2"},
    ]
    option_ids = ["O1", "O2", "O3", "O4"]
    question_ids = [item["questionId"] for item in questions]
    tasks = []
    for variant, facts in _knowledge_artifacts().items():
        evidence = [
            EvidenceItem(evidence_id, "artifact-text", f"synthetic-heliox-learning:{variant}", {"segmentId": evidence_id}, text).to_dict()
            for evidence_id, text in facts
        ]
        tasks.append(
            {
                "taskId": f"r5e:{variant}",
                "kind": "comprehension-qa",
                "replicates": replicates,
                "systemPrompt": (
                    "You are an isolated observer in a controlled knowledge-transfer experiment. The Heliox/Neral/Varo mechanism is fictitious. "
                    "Answer only from the artifact evidence supplied in this call. If the evidence does not establish an answer, choose O4 (The artifact does not say). "
                    "Do not use outside assumptions. For each answer, cite only evidence IDs that actually support it; use an empty evidenceIds array when choosing O4 because evidence is absent."
                ),
                "userPayload": {"artifactEvidence": evidence, "questions": [{k: v for k, v in item.items() if k != "answer"} for item in questions]},
                "resultSchema": _qa_result_schema(question_ids, option_ids),
                "oracle": {
                    "answers": {item["questionId"]: ("O4" if variant == "no-artifact" else item["answer"]) for item in questions},
                    "substantiveAnswers": {item["questionId"]: item["answer"] for item in questions},
                    "stages": {item["questionId"]: item["stage"] for item in questions},
                },
                "scope": "Agent-observer knowledge-transfer consequence on fictitious facts; not human comprehension",
            }
        )
    return tasks
