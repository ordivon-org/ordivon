"""Time-coded source/narration and crossmodal grounded R5 tasks.

This code reads exact source-composition and transcript propositions; it does
not perform pixel analysis, voice recognition, or audio feature inference.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from .grounded_evidence import EvidenceItem, _relation_result_schema, validate_evidence_catalog

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
