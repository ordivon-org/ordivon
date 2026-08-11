from __future__ import annotations

import hashlib
import json
import re
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


RELATION_LABELS = (
    "CAUSES",
    "ENABLES",
    "CONDITION",
    "SUPPORTS",
    "CONTRASTS",
    "DUPLICATES",
    "EXTENDS",
    "CONTRADICTS",
    "SEQUENCE",
    "IRRELEVANT",
    "NONE",
)

SPEECH_ACT_LABELS = (
    "PROBLEM",
    "MECHANISM",
    "PROCESS",
    "RECOVERY",
    "EVIDENCE",
    "BOUNDARY",
    "IMPERATIVE",
    "OTHER",
)

SCENE_PROPOSITIONS: dict[str, str] = {
    "HookScene": "A response can disappear while the underlying work can remain recoverable; blind redispatch is the failure boundary.",
    "RuntimeFlowComposition": "Runtime separates and connects source, Workspace, durable Job, Attempt, evidence, observation, and recovery as distinct execution facts.",
    "SourcePatchScene": "A guarded patch is admitted against identified source bytes and changes one bounded path.",
    "ObserveScene": "Execution becomes a durable recorded Job and Attempt whose progress can be observed until the owned process tree finishes.",
    "RequestReplayComposition": "Replaying the same client request identity refers back to the same recorded Job rather than admitting another opaque operation.",
    "RecoveryScene": "After uncertain delivery, the caller reconnects using the exact request identity and recovers the same Job.",
    "EvidenceScene": "The Job retains bounded execution evidence and dispositions without claiming semantic Task completion or every external-world effect.",
    "ExactCloseComposition": "Workspace closure is fenced to the exact reviewed source state rather than an unfenced cleanup action.",
    "DiffScene": "The source consequence remains inspectable as one modified path.",
    "BoundaryScene": "Runtime does not own semantic Task completion, hostile multi-tenant isolation, or universal external-effect idempotency.",
    "EndScene": "The final message is to recover the same work and inspect its evidence within the current trusted-local product boundary.",
}

_SEQUENCE_RE = re.compile(
    r"<Sequence\s+from=\{(?P<start>\d+)\}\s+durationInFrames=\{(?P<duration>\d+)\}>(?P<body>.*?)</Sequence>",
    re.DOTALL,
)


@dataclass(frozen=True, slots=True)
class EvidenceItem:
    evidence_id: str
    modality: str
    source_id: str
    locator: dict[str, Any]
    observed: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidenceId": self.evidence_id,
            "modality": self.modality,
            "sourceId": self.source_id,
            "locator": dict(self.locator),
            "observed": self.observed,
        }


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _strict_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{label} must be a non-empty trimmed string")
    return value


def validate_evidence_catalog(items: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    catalog: dict[str, dict[str, Any]] = {}
    for raw in items:
        item = dict(raw)
        evidence_id = _strict_text(item.get("evidenceId"), "evidenceId")
        if evidence_id in catalog:
            raise ValueError(f"duplicate evidence identity: {evidence_id}")
        _strict_text(item.get("modality"), "evidence modality")
        _strict_text(item.get("sourceId"), "evidence sourceId")
        _strict_text(item.get("observed"), "evidence observed text")
        locator = item.get("locator")
        if not isinstance(locator, dict) or not locator:
            raise ValueError("evidence locator must be a non-empty object")
        if "startMs" in locator or "endMs" in locator:
            start = locator.get("startMs")
            end = locator.get("endMs")
            if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end <= start:
                raise ValueError("time locator must be a positive half-open millisecond range")
        catalog[evidence_id] = item
    return catalog


def validate_grounded_result(result: Mapping[str, Any], evidence: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    catalog = validate_evidence_catalog(evidence)
    value = dict(result)
    claims = value.get("claims", [])
    relations = value.get("relations", [])
    if not isinstance(claims, list) or not isinstance(relations, list):
        raise ValueError("grounded result claims/relations must be arrays")
    known_claims: set[str] = set()
    for raw in claims:
        if not isinstance(raw, dict):
            raise ValueError("grounded claim must be an object")
        claim_id = _strict_text(raw.get("claimId"), "claimId")
        if claim_id in known_claims:
            raise ValueError(f"duplicate claim identity: {claim_id}")
        known_claims.add(claim_id)
        _strict_text(raw.get("statement"), "claim statement")
        refs = raw.get("evidenceIds")
        if not isinstance(refs, list) or not refs or any(ref not in catalog for ref in refs):
            raise ValueError(f"claim {claim_id} has invalid or empty grounding")
    for raw in relations:
        if not isinstance(raw, dict):
            raise ValueError("grounded relation must be an object")
        relation = raw.get("relation")
        if relation not in RELATION_LABELS:
            raise ValueError(f"unsupported experimental relation label: {relation}")
        source = raw.get("sourceClaimId")
        target = raw.get("targetClaimId")
        if source not in known_claims or target not in known_claims:
            raise ValueError("grounded relation references an unknown claim")
        refs = raw.get("evidenceIds")
        if not isinstance(refs, list) or not refs or any(ref not in catalog for ref in refs):
            raise ValueError("grounded relation has invalid or empty evidence grounding")
    return value


def _relation_result_schema(probes: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    probe_ids = [str(item["probeId"]) for item in probes]
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "judgments": {
                "type": "array",
                "minItems": len(probe_ids),
                "maxItems": len(probe_ids),
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "probeId": {"type": "string", "enum": probe_ids},
                        "relation": {"type": "string", "enum": list(RELATION_LABELS)},
                        "evidenceIds": {
                            "type": "array",
                            "minItems": 1,
                            "maxItems": 8,
                            "items": {"type": "string"},
                        },
                        "uncertainty": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                        },
                    },
                    "required": ["probeId", "relation", "evidenceIds", "uncertainty"],
                },
            }
        },
        "required": ["judgments"],
    }


def _speech_result_schema(cue_ids: Sequence[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "cues": {
                "type": "array",
                "minItems": len(cue_ids),
                "maxItems": len(cue_ids),
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "cueId": {"type": "string", "enum": list(cue_ids)},
                        "speechAct": {"type": "string", "enum": list(SPEECH_ACT_LABELS)},
                        "polarity": {"type": "string", "enum": ["affirmed", "negated", "mixed"]},
                        "evidenceIds": {
                            "type": "array",
                            "minItems": 1,
                            "maxItems": 3,
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["cueId", "speechAct", "polarity", "evidenceIds"],
                },
            }
        },
        "required": ["cues"],
    }


def _timeline_result_schema(event_ids: Sequence[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "events": {
                "type": "array",
                "minItems": len(event_ids),
                "maxItems": len(event_ids),
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "eventId": {"type": "string", "enum": list(event_ids)},
                        "present": {"type": "boolean"},
                        "summary": {"type": "string", "minLength": 1, "maxLength": 500},
                        "evidenceIds": {
                            "type": "array",
                            "maxItems": 8,
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["eventId", "present", "summary", "evidenceIds"],
                },
            }
        },
        "required": ["events"],
    }


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


def parse_runtime_scenes(source_text: str, *, fps: int = 30) -> list[dict[str, Any]]:
    scenes: list[dict[str, Any]] = []
    for index, match in enumerate(_SEQUENCE_RE.finditer(source_text), start=1):
        body = match.group("body")
        component = next((name for name in SCENE_PROPOSITIONS if f"<{name}" in body), None)
        if component is None:
            raise ValueError(f"unknown Runtime Introduction scene body: {body[:120]}")
        start_frame = int(match.group("start"))
        duration = int(match.group("duration"))
        scenes.append(
            {
                "evidenceId": f"V{index:02d}",
                "modality": "video-source-semantics",
                "sourceId": "runtime-introduction-master-composition",
                "locator": {
                    "startMs": round(start_frame * 1000 / fps),
                    "endMs": round((start_frame + duration) * 1000 / fps),
                    "component": component,
                },
                "observed": SCENE_PROPOSITIONS[component],
            }
        )
    if len(scenes) != len(SCENE_PROPOSITIONS):
        raise ValueError(f"expected {len(SCENE_PROPOSITIONS)} Runtime scenes, found {len(scenes)}")
    validate_evidence_catalog(scenes)
    return scenes


def narration_evidence(timed_text: Mapping[str, Any]) -> list[dict[str, Any]]:
    time_base = timed_text.get("timeBase")
    ticks = time_base.get("ticksPerSecond") if isinstance(time_base, dict) else None
    cues = timed_text.get("cues")
    if not isinstance(ticks, int) or ticks <= 0 or not isinstance(cues, list):
        raise ValueError("invalid timed text")
    evidence = []
    for cue in cues:
        if not isinstance(cue, dict):
            raise ValueError("timed-text cue must be an object")
        evidence.append(
            EvidenceItem(
                str(cue["id"]),
                "speech-transcript",
                str(timed_text.get("id") or "runtime-introduction-narration-en"),
                {
                    "startMs": round(int(cue["startTick"]) * 1000 / ticks),
                    "endMs": round(int(cue["endTick"]) * 1000 / ticks),
                },
                str(cue["text"]),
            ).to_dict()
        )
    validate_evidence_catalog(evidence)
    return evidence


def build_runtime_timeline_tasks(
    *,
    source_text: str,
    timed_text: Mapping[str, Any],
    replicates: int = 2,
) -> list[dict[str, Any]]:
    scenes = parse_runtime_scenes(source_text)
    narration = narration_evidence(timed_text)
    evidence = scenes + narration
    event_checks = [
        {"eventId": "E_PATCH", "description": "A guarded mutation is tied to identified source bytes and one bounded path.", "expectedPresent": True, "requiredEvidenceAny": ["V03", "en-003"]},
        {"eventId": "E_OBSERVE", "description": "Execution becomes an observable recorded Job/Attempt.", "expectedPresent": True, "requiredEvidenceAny": ["V04", "en-004"]},
        {"eventId": "E_RECOVER", "description": "The same request identity is used to recover the same recorded Job after uncertain delivery.", "expectedPresent": True, "requiredEvidenceAny": ["V05", "V06", "en-005"]},
        {"eventId": "E_BOUNDARY", "description": "Runtime explicitly does not claim semantic Task completion, hostile multi-tenant isolation, or universal external-effect idempotency.", "expectedPresent": True, "requiredEvidenceAny": ["V10", "en-008"]},
    ]
    event_ids = [item["eventId"] for item in event_checks]
    baseline = {
        "taskId": "r5b:runtime-baseline",
        "kind": "timeline-checks",
        "replicates": replicates,
        "systemPrompt": (
            "You are a grounded event/narrative checker over a time-coded representation of an owned video. "
            "The evidence contains video-source semantics and exact narration transcript cues, not raw pixels. "
            "For each requested event, decide whether the supplied representation contains evidence for it. "
            "If absent, set present=false and return an empty evidenceIds array. Never reconstruct omitted events from general knowledge."
        ),
        "userPayload": {
            "evidence": evidence,
            "eventChecks": [
                {"eventId": item["eventId"], "description": item["description"]}
                for item in event_checks
            ],
        },
        "resultSchema": _timeline_result_schema(event_ids),
        "oracle": {
            "presence": {item["eventId"]: item["expectedPresent"] for item in event_checks},
            "requiredEvidenceAny": {item["eventId"]: list(item["requiredEvidenceAny"]) for item in event_checks},
        },
        "scope": "grounded reasoning over time-coded source semantics + transcript; not raw-video VLM perception",
    }
    recovery_semantic_ids = {"V02", "V05", "V06", "V11", "en-002", "en-005", "en-009"}
    omitted_evidence = [item for item in evidence if item["evidenceId"] not in recovery_semantic_ids]
    omitted_checks = [dict(item) for item in event_checks]
    for item in omitted_checks:
        if item["eventId"] == "E_RECOVER":
            item["expectedPresent"] = False
    omission = {
        **baseline,
        "taskId": "r5b:runtime-recovery-omitted",
        "userPayload": {
            "evidence": omitted_evidence,
            "eventChecks": [
                {"eventId": item["eventId"], "description": item["description"]}
                for item in omitted_checks
            ],
        },
        "oracle": {
            "presence": {item["eventId"]: item["expectedPresent"] for item in omitted_checks},
            "requiredEvidenceAny": {item["eventId"]: list(item["requiredEvidenceAny"]) for item in omitted_checks},
        },
        "scope": "controlled evidence-omission falsifier over the owned-video representation; all generic recovery references are removed",
    }
    return [baseline, omission]


def build_speech_tasks(*, timed_text: Mapping[str, Any], replicates: int = 2) -> list[dict[str, Any]]:
    base = narration_evidence(timed_text)
    selected_ids = ["en-001", "en-003", "en-005", "en-006", "en-008", "en-009"]
    acts = {
        "en-001": ("PROBLEM", "negated"),
        "en-003": ("PROCESS", "affirmed"),
        "en-005": ("RECOVERY", "affirmed"),
        "en-006": ("EVIDENCE", "mixed"),
        "en-008": ("BOUNDARY", "negated"),
        "en-009": ("IMPERATIVE", "affirmed"),
    }

    def task(name: str, evidence: list[dict[str, Any]], override: dict[str, tuple[str, str]] | None = None) -> dict[str, Any]:
        oracle = dict(acts)
        if override:
            oracle.update(override)
        selected = [item for item in evidence if item["evidenceId"] in selected_ids]
        return {
            "taskId": f"r5c:{name}",
            "kind": "speech-acts",
            "replicates": replicates,
            "systemPrompt": (
                "You are a speech-meaning annotator operating on exact time-coded transcript cues. "
                "Classify only the listed cues. Polarity describes the cue's central proposition: negated when the cue centrally denies a claim, mixed when it contains both positive and limiting/negative propositions. "
                "Ground each annotation to its own cue evidence ID. Do not infer vocal emotion or prosody from transcript text."
            ),
            "userPayload": {"evidence": selected},
            "resultSchema": _speech_result_schema(selected_ids),
            "oracle": {"cues": {cue_id: {"speechAct": role, "polarity": polarity} for cue_id, (role, polarity) in oracle.items()}},
            "scope": "speech meaning from exact transcript/timing; not ASR or acoustic semantic recognition",
        }

    paraphrase = [dict(item) for item in base]
    for item in paraphrase:
        if item["evidenceId"] == "en-008":
            item["observed"] = "Runtime neither establishes external idempotency nor provides hostile multi-tenant isolation, and it does not determine semantic Task completion."
    polarity_flip = [dict(item) for item in base]
    for item in polarity_flip:
        if item["evidenceId"] == "en-008":
            item["observed"] = "Runtime proves external idempotency, hostile multi-tenant isolation, and semantic Task completion."
    return [
        task("baseline", base),
        task("boundary-paraphrase", paraphrase),
        task("boundary-polarity-flip", polarity_flip, {"en-008": ("OTHER", "affirmed")}),
    ]


def build_crossmodal_tasks(*, replicates: int = 2) -> list[dict[str, Any]]:
    evidence = [
        EvidenceItem("M1V", "visual-proposition", "synthetic-crossmodal", {"segmentId": "M1V"}, "A diagram shows the amber latch opening, followed by coolant entering the blue chamber.").to_dict(),
        EvidenceItem("M1A", "audio-proposition", "synthetic-crossmodal", {"segmentId": "M1A"}, "The narrator says that opening the amber latch allows coolant into the chamber.").to_dict(),
        EvidenceItem("M2V", "visual-proposition", "synthetic-crossmodal", {"segmentId": "M2V"}, "A card states: temperature must be below 40 degrees before safe spindle rotation.").to_dict(),
        EvidenceItem("M2A", "audio-proposition", "synthetic-crossmodal", {"segmentId": "M2A"}, "The narrator says the spindle can rotate safely at any temperature.").to_dict(),
        EvidenceItem("M3V", "visual-proposition", "synthetic-crossmodal", {"segmentId": "M3V"}, "The frame displays a gauge reading of 7 with the latch icon unlocked.").to_dict(),
        EvidenceItem("M3A", "audio-proposition", "synthetic-crossmodal", {"segmentId": "M3A"}, "The narrator explains that the gauge reached 7, and adds that the operator should now inspect coolant flow.").to_dict(),
        EvidenceItem("M4V", "visual-proposition", "synthetic-crossmodal", {"segmentId": "M4V"}, "The frame shows one modified file named policy.py.").to_dict(),
        EvidenceItem("M4A", "audio-proposition", "synthetic-crossmodal", {"segmentId": "M4A"}, "The narrator discusses rainfall measurements on a distant island.").to_dict(),
        EvidenceItem("M5V", "visual-proposition", "synthetic-crossmodal", {"segmentId": "M5V"}, "The frame text says: recover the same work.").to_dict(),
        EvidenceItem("M5A", "audio-proposition", "synthetic-crossmodal", {"segmentId": "M5A"}, "The narrator says: recover the same work.").to_dict(),
    ]
    probes = [
        {"probeId": "M1", "sourceEvidenceId": "M1V", "targetEvidenceId": "M1A", "expectedRelation": "SUPPORTS"},
        {"probeId": "M2", "sourceEvidenceId": "M2V", "targetEvidenceId": "M2A", "expectedRelation": "CONTRADICTS"},
        {"probeId": "M3", "sourceEvidenceId": "M3V", "targetEvidenceId": "M3A", "expectedRelation": "EXTENDS"},
        {"probeId": "M4", "sourceEvidenceId": "M4V", "targetEvidenceId": "M4A", "expectedRelation": "IRRELEVANT"},
        {"probeId": "M5", "sourceEvidenceId": "M5V", "targetEvidenceId": "M5A", "expectedRelation": "DUPLICATES"},
    ]
    return [
        {
            "taskId": "r5d:crossmodal-relations",
            "kind": "relation-probes",
            "replicates": replicates,
            "systemPrompt": (
                "You are a bounded crossmodal-relation annotator. Treat the supplied visual and audio propositions as already-grounded modality observations; do not infer unseen pixels or sounds. "
                "SUPPORTS means the second modality reinforces the same proposition; DUPLICATES means it restates essentially the same proposition; EXTENDS adds material compatible information; CONTRADICTS conflicts; IRRELEVANT lacks a meaningful relation."
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
            "scope": "controlled relation classification over already-grounded modality propositions",
        }
    ]


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


def build_provider_bundle(*, root: Path, replicates: int = 2) -> dict[str, Any]:
    timed_text = json.loads((root / "productions/runtime-introduction/timed-text/narration.en.json").read_text(encoding="utf-8"))
    source_text = (root / "apps/motion-remotion/src/runtime-introduction-master-composition.tsx").read_text(encoding="utf-8")
    tasks = [
        *build_article_tasks(replicates=replicates),
        *build_runtime_timeline_tasks(source_text=source_text, timed_text=timed_text, replicates=replicates),
        *build_speech_tasks(timed_text=timed_text, replicates=replicates),
        *build_crossmodal_tasks(replicates=replicates),
        *build_comprehension_tasks(replicates=replicates),
    ]
    bundle = {
        "schemaVersion": 1,
        "kind": "ordivon.studio-r5-grounded-meaning-provider-bundle",
        "sourceRevisionRole": "caller must bind current Studio revision separately",
        "tasks": tasks,
        "acceptanceLaw": {
            "grounding": "Every semantic observation must cite supplied evidence identifiers; absent evidence must remain absent rather than reconstructed from prior knowledge.",
            "sensitivity": "Known meaning-changing perturbations must change the targeted semantic result.",
            "invariance": "Meaning-preserving paraphrase should preserve the targeted relation/speech result.",
            "counterexample": "Contradiction and omission variants must not be smoothed into the baseline interpretation.",
            "disagreement": "Replicate disagreement is retained as uncertainty evidence rather than hidden by majority vote.",
            "consequence": "Knowledge transfer is measured separately from semantic annotation and is labeled Agent-observer consequence only.",
        },
    }
    bundle["bundleDigest"] = canonical_digest(bundle)
    return bundle


def _group_results(receipt: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    raw = receipt.get("results")
    if not isinstance(raw, list):
        raise ValueError("provider receipt has no results array")
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in raw:
        if not isinstance(item, dict) or not isinstance(item.get("taskId"), str) or not isinstance(item.get("result"), dict):
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
            ref_set = set(refs) if isinstance(refs, list) and all(isinstance(ref, str) for ref in refs) else set()
            required = probe_map.get(str(item.get("probeId")), set())
            checks.append(bool(required) and required.issubset(ref_set) and ref_set.issubset(supplied))
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
            ref_set = set(refs) if isinstance(refs, list) and all(isinstance(ref, str) for ref in refs) else set()
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
            ref_set = set(refs) if isinstance(refs, list) and all(isinstance(ref, str) for ref in refs) else set()
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
            ref_set = set(refs) if isinstance(refs, list) and all(isinstance(ref, str) for ref in refs) else set()
            if str(item.get("optionId")) == "O4":
                checks.append(not ref_set)
            else:
                checks.append(bool(ref_set) and ref_set.issubset(supplied))
    return statistics.fmean(checks) if checks else 0.0


def score_provider_receipt(bundle: Mapping[str, Any], receipt: Mapping[str, Any]) -> dict[str, Any]:
    tasks = {str(item["taskId"]): item for item in bundle.get("tasks", []) if isinstance(item, dict)}
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
            correct = [sum(mapping.get(probe) == relation for probe, relation in expected.items()) / len(expected) for mapping in maps]
            base.update({
                "meanAccuracy": statistics.fmean(correct) if correct else 0.0,
                "replicateAgreement": _replicate_agreement(maps),
                "replicateAccuracies": correct,
                "meanGroundingValidity": statistics.fmean(_grounding_validity(task, record["result"]) for record in records) if records else 0.0,
            })
        elif kind == "timeline-checks":
            expected = task["oracle"]["presence"]
            accuracies = []
            grounding_rates = []
            for record in records:
                events = record["result"].get("events", [])
                mapped = {str(item.get("eventId")): item for item in events if isinstance(item, dict)}
                accuracies.append(sum(bool(mapped.get(event, {}).get("present")) == present for event, present in expected.items()) / len(expected))
                grounding_rates.append(sum((not bool(item.get("present"))) or bool(item.get("evidenceIds")) for item in mapped.values()) / max(1, len(mapped)))
            base.update({
                "meanPresenceAccuracy": statistics.fmean(accuracies) if accuracies else 0.0,
                "meanGroundingDiscipline": statistics.fmean(grounding_rates) if grounding_rates else 0.0,
                "meanGroundingValidity": statistics.fmean(_grounding_validity(task, record["result"]) for record in records) if records else 0.0,
            })
        elif kind == "speech-acts":
            expected = task["oracle"]["cues"]
            accuracies = []
            cue_maps = []
            for record in records:
                cues = record["result"].get("cues", [])
                mapped = {str(item.get("cueId")): (item.get("speechAct"), item.get("polarity")) for item in cues if isinstance(item, dict)}
                cue_maps.append({key: f"{value[0]}:{value[1]}" for key, value in mapped.items()})
                accuracies.append(sum(mapped.get(cue) == (target["speechAct"], target["polarity"]) for cue, target in expected.items()) / len(expected))
            base.update({
                "meanAccuracy": statistics.fmean(accuracies) if accuracies else 0.0,
                "replicateAgreement": _replicate_agreement(cue_maps),
                "meanGroundingValidity": statistics.fmean(_grounding_validity(task, record["result"]) for record in records) if records else 0.0,
            })
        elif kind == "comprehension-qa":
            expected = task["oracle"]["answers"]
            substantive = task["oracle"]["substantiveAnswers"]
            stages = task["oracle"]["stages"]
            accuracies = []
            substantive_grounded_rates = []
            unsupported_assertion_rates = []
            abstention_rates = []
            stage_accs: dict[str, list[float]] = {"perception": [], "comprehension": [], "adaptation": []}
            answer_maps = []
            supplied = _supplied_evidence_ids(task)
            for record in records:
                answers = record["result"].get("answers", [])
                answer_items = {str(item.get("questionId")): item for item in answers if isinstance(item, dict)}
                mapped = {question: str(item.get("optionId")) for question, item in answer_items.items()}
                answer_maps.append(mapped)
                accuracies.append(sum(mapped.get(q) == answer for q, answer in expected.items()) / len(expected))
                substantive_checks = []
                unsupported_checks = []
                for question, target in substantive.items():
                    item = answer_items.get(question, {})
                    option = str(item.get("optionId"))
                    refs = item.get("evidenceIds")
                    ref_set = set(refs) if isinstance(refs, list) and all(isinstance(ref, str) for ref in refs) else set()
                    grounded = bool(ref_set) and ref_set.issubset(supplied)
                    substantive_checks.append(option == target and option != "O4" and grounded)
                    unsupported_checks.append(option != "O4" and not grounded)
                substantive_grounded_rates.append(sum(substantive_checks) / len(substantive_checks))
                unsupported_assertion_rates.append(sum(unsupported_checks) / len(unsupported_checks))
                abstention_rates.append(sum(option == "O4" for option in mapped.values()) / len(expected))
                for stage in stage_accs:
                    ids = [q for q, value in stages.items() if value == stage]
                    score = sum(mapped.get(q) == expected[q] for q in ids) / len(ids)
                    stage_accs[stage].append(score)
            qa_maps[task_id] = answer_maps
            base.update({
                "meanAccuracy": statistics.fmean(accuracies) if accuracies else 0.0,
                "replicateAgreement": _replicate_agreement(answer_maps),
                "stageAccuracy": {stage: statistics.fmean(values) if values else 0.0 for stage, values in stage_accs.items()},
                "meanGroundingValidity": statistics.fmean(_grounding_validity(task, record["result"]) for record in records) if records else 0.0,
                "groundedSubstantiveCorrectRate": statistics.fmean(substantive_grounded_rates) if substantive_grounded_rates else 0.0,
                "unsupportedAssertionRate": statistics.fmean(unsupported_assertion_rates) if unsupported_assertion_rates else 0.0,
                "abstentionRate": statistics.fmean(abstention_rates) if abstention_rates else 0.0,
            })
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
        omission_sensitivity = min(float(baseline_events.get("meanPresenceAccuracy", 0.0)), float(omitted_events.get("meanPresenceAccuracy", 0.0)))

    no_artifact_score = task_scores.get("r5e:no-artifact", {})
    no_artifact_epistemic = float(no_artifact_score.get("meanAccuracy", 0.0))
    no_artifact_unsupported = float(no_artifact_score.get("unsupportedAssertionRate", 0.0))
    artifact_task_ids = [f"r5e:{name}" for name in ("explicit-chain", "fragmented", "evidence-delayed")]
    artifact_accuracies = [float(task_scores.get(task_id, {}).get("meanAccuracy", 0.0)) for task_id in artifact_task_ids]
    artifact_acquisition = [float(task_scores.get(task_id, {}).get("groundedSubstantiveCorrectRate", 0.0)) for task_id in artifact_task_ids]
    knowledge_acquisition = statistics.fmean(artifact_acquisition) if artifact_acquisition else 0.0

    order_agreements: list[float] = []
    explicit_maps = qa_maps.get("r5e:explicit-chain", [])
    for other_id in ("r5e:fragmented", "r5e:evidence-delayed"):
        other_maps = qa_maps.get(other_id, [])
        for left, right in zip(explicit_maps, other_maps):
            keys = sorted(set(left) | set(right))
            if keys:
                order_agreements.append(sum(left.get(key) == right.get(key) for key in keys) / len(keys))
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
            "meanTaskGroundingValidity": statistics.fmean(grounding_values) if grounding_values else 0.0,
            "agentObserverArtifactTaskAccuracy": statistics.fmean(artifact_accuracies) if artifact_accuracies else 0.0,
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
