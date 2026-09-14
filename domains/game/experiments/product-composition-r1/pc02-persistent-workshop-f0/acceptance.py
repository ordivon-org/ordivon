#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
from pathlib import Path

from carrier import WorkshopCarrier, canonical_digest, profile_feedback

ROOT = Path(__file__).resolve().parent
EVIDENCE_DIR = ROOT / "evidence"
EVIDENCE = EVIDENCE_DIR / "structural-acceptance-r1.json"
RELOAD_R1 = EVIDENCE_DIR / "reload-state-after-r1.json"
RELOAD_R2 = EVIDENCE_DIR / "reload-state-after-r2.json"


def contains_forbidden_scalar(value: object) -> bool:
    forbidden = {"score", "utility", "rank", "ranking", "total", "aggregate"}
    if isinstance(value, dict):
        if any(str(key).lower() in forbidden for key in value):
            return True
        return any(contains_forbidden_scalar(child) for child in value.values())
    if isinstance(value, list):
        return any(contains_forbidden_scalar(child) for child in value)
    return False


def seed_wide_artifact(carrier: WorkshopCarrier) -> None:
    carrier.add_piece("ring", 40, 72, size=64, piece_id="p1")
    carrier.add_piece("bar", 240, 88, size=80, piece_id="p2")
    carrier.add_piece("diamond", 448, 76, size=60, piece_id="p3")


# Main three-round path.
carrier = WorkshopCarrier()
no_commit_affordances = carrier.available_affordances()
carrier.declare_intent("spread", "wide")
seed_wide_artifact(carrier)

r1 = carrier.commit("wide scaffold")
r1_frozen = copy.deepcopy(r1)
working_before_response = canonical_digest(carrier.pieces)
intent_before_response = copy.deepcopy(carrier.intent)
service_r1 = carrier.expose("service_bay")
service_suggestions = {item["id"] for item in service_r1["feedback"]["suggestions"]}
carrier.record_preference_decision(
    "service_bay",
    "compress-span",
    "reject",
    "preserve the declared wide spread intent while continuing through artifact-derived structure",
)
audience_left_artifact_unchanged = working_before_response == canonical_digest(carrier.pieces)
audience_left_intent_unchanged = intent_before_response == carrier.intent
round_after_reject = carrier.advance_round()

# Physical state persistence: round transition -> file -> fresh carrier object.
carrier.save_state(RELOAD_R1)
reloaded_r1 = WorkshopCarrier.load_state(RELOAD_R1)
r1_reload_ok = (
    reloaded_r1.round == 2
    and len(reloaded_r1.revisions) == 1
    and reloaded_r1.revisions[0]["artifactDigest"] == r1["artifactDigest"]
    and reloaded_r1.preference_decisions[0]["decision"] == "reject"
)
carrier = reloaded_r1

p2_anchor = next(a for a in carrier.revisions[0]["derivedAffordances"] if a["sourcePieceId"] == "p2")
p4 = carrier.attach_from_commit(p2_anchor["token"], "circle", size=48)
carrier.transform("p2", "rotate")
r2 = carrier.commit("derived attachment without compacting")
gallery_r2 = carrier.expose("open_gallery")
carrier.advance_round()

# Reload again with >=2 immutable revisions recoverable before Round 3.
carrier.save_state(RELOAD_R2)
reloaded_r2 = WorkshopCarrier.load_state(RELOAD_R2)
r2_reload_ok = (
    reloaded_r2.round == 3
    and len(reloaded_r2.revisions) == 2
    and [r["artifactDigest"] for r in reloaded_r2.revisions] == [r1["artifactDigest"], r2["artifactDigest"]]
    and reloaded_r2.revisions[0]["artifactDigest"] == r1_frozen["artifactDigest"]
)
carrier = reloaded_r2

carrier.transform(p4, "grow")
carrier.transform("p2", "rotate")
r3 = carrier.commit("revision preserves declared spread")
service_r3 = carrier.expose("service_bay")

# Counterfactual: artifact-derived affordance cannot be used without a commit.
fresh = WorkshopCarrier()
fresh.declare_intent("spread", "wide")
attach_without_commit_rejected = False
try:
    fresh.attach_from_commit(p2_anchor["token"], "circle")
except RuntimeError:
    attach_without_commit_rejected = True

# Counterfactual: the same geometry under a different explicit intent changes non-audience commit admissibility.
intent_wide = WorkshopCarrier()
intent_wide.declare_intent("spread", "wide")
seed_wide_artifact(intent_wide)
intent_wide_commit = intent_wide.commit("intent causality probe")
intent_compact = WorkshopCarrier()
intent_compact.declare_intent("spread", "compact")
seed_wide_artifact(intent_compact)
compact_same_artifact_rejected = False
try:
    intent_compact.commit("same artifact, compact intent")
except RuntimeError:
    compact_same_artifact_rejected = True

# Counterfactual: two distinct commits under the same intent/round produce different later affordances.
alt = WorkshopCarrier()
alt.declare_intent("spread", "wide")
alt.add_piece("ring", 20, 180, size=64, piece_id="q1")
alt.add_piece("bar", 190, 196, size=64, piece_id="q2")
alt.add_piece("diamond", 410, 184, size=60, piece_id="q3")
alt_r1 = alt.commit("alternate wide scaffold")
alt_service = alt.expose("service_bay")
artifact_affordance_counterfactual = (
    r1["artifactDigest"] != alt_r1["artifactDigest"]
    and r1["derivedAffordances"] != alt_r1["derivedAffordances"]
)

# Post-commit live edits must not leak into context evaluation before a new commit.
live_probe = WorkshopCarrier()
live_probe.declare_intent("spread", "wide")
seed_wide_artifact(live_probe)
live_probe_commit = live_probe.commit("committed view probe")
expected_committed_feedback = profile_feedback("service_bay", live_probe_commit["pieces"])
live_probe.transform("p2", "rotate")
live_working_digest = canonical_digest(live_probe.pieces)
live_probe_response = live_probe.expose("service_bay")
committed_read_not_working_copy = (
    live_working_digest != live_probe_commit["artifactDigest"]
    and live_probe_response["artifactDigest"] == live_probe_commit["artifactDigest"]
    and live_probe_response["feedback"] == expected_committed_feedback
)

service_same_artifact = profile_feedback("service_bay", r1["pieces"])
gallery_same_artifact = profile_feedback("open_gallery", r1["pieces"])
service_repeat = profile_feedback("service_bay", r1["pieces"])
feedback_objects = [
    service_r1["feedback"],
    gallery_r2["feedback"],
    service_r3["feedback"],
    service_same_artifact,
    gallery_same_artifact,
    alt_service["feedback"],
]

r1_reloaded_final = carrier.revisions[0]
checks = {
    "threeRoundsCommitted": [r1["round"], r2["round"], r3["round"]] == [1, 2, 3],
    "revisionsPersistAndRemainDistinct": (
        r1_reloaded_final["artifactDigest"] == r1_frozen["artifactDigest"]
        and len({r1["artifactDigest"], r2["artifactDigest"], r3["artifactDigest"]}) == 3
        and [r["parentRevisionId"] for r in (r1, r2, r3)] == [None, 1, 2]
    ),
    "twoRevisionsRecoverAcrossRoundReload": r1_reload_ok and r2_reload_ok,
    "explicitIntentAxisPersists": (
        r1["intentAxis"] == {"axis": "spread", "target": "wide"}
        and r2["intentAxis"] == r1["intentAxis"]
        and r3["intentAxis"] == r1["intentAxis"]
        and all(r["intentSatisfied"] for r in (r1, r2, r3))
    ),
    "intentAxisChangesNonAudienceCommitConstraint": (
        intent_wide_commit["intentSatisfied"] and compact_same_artifact_rejected
    ),
    "contextFeedbackDoesNotConsumeIntentMetadata": (
        service_r1["feedback"] == service_same_artifact
        and "intent" not in json.dumps(service_same_artifact).lower()
    ),
    "audienceCannotWriteArtifactOrIntent": audience_left_artifact_unchanged and audience_left_intent_unchanged,
    "audienceReadsCommittedRevisionNotWorkingCopy": committed_read_not_working_copy,
    "sameArtifactContextIsDeterministic": service_same_artifact == service_repeat,
    "twoProfilesHaveConflictingFootprintPreference": (
        service_same_artifact["dimensions"]["footprint"]["status"] == "tension"
        and service_same_artifact["dimensions"]["footprint"]["preference"] == "compact"
        and gallery_same_artifact["dimensions"]["footprint"]["status"] == "supports"
        and gallery_same_artifact["dimensions"]["footprint"]["preference"] == "wide"
    ),
    "feedbackIsMultidimensionalAndNonScalar": (
        all(len(item["dimensions"]) >= 3 for item in feedback_objects)
        and all(item["authority"] == "advisory-context-observation" for item in feedback_objects)
        and not any(contains_forbidden_scalar(item) for item in feedback_objects)
    ),
    "differentCommittedArtifactsChangeLaterAffordances": artifact_affordance_counterfactual,
    "committedArtifactCreatesLaterAffordance": (
        no_commit_affordances == []
        and bool(r1["derivedAffordances"])
        and carrier.revisions[1]["pieces"][-1]["sourceAffordance"] == p2_anchor["token"]
        and carrier.affordance_history[0]["sourceRevisionId"] == 1
        and attach_without_commit_rejected
    ),
    "rejectedAudiencePreferenceStillProgresses": (
        "compress-span" in service_suggestions
        and carrier.preference_decisions[0]["decision"] == "reject"
        and round_after_reject == 2
        and r2["round"] == 2
    ),
    "reusedPGPIPrimitiveBudget": (
        all(piece["shape"] in {"circle", "square", "diamond", "bar", "ring"} for piece in carrier.pieces)
        and len(carrier.pieces) <= 6
    ),
    "revisionUsesPGPITransform": int(next(p for p in r3["pieces"] if p["id"] == "p2")["rot"]) == 30,
    "separateIKCRAPTraceExists": (
        bool(carrier.intent_history)
        and len(carrier.revisions) == 3
        and len(carrier.context_history) == 3
        and all("feedback" in entry for entry in carrier.context_history)
        and bool(carrier.affordance_history)
        and len(carrier.progress_events) == 2
    ),
}

standing = "SURVIVES_PC02_F0_STRUCTURAL_COMPOSITION" if all(checks.values()) else "FAILS_PC02_F0_STRUCTURAL_COMPOSITION"
out = {
    "schemaVersion": 2,
    "kind": "pc02-persistent-workshop-f0-structural-acceptance",
    "standing": standing,
    "mechanismLibraryModified": False,
    "runtimeAgentProfile": "none",
    "reusedPGPI": {
        "primitiveGrammar": ["circle", "square", "diamond", "bar", "ring"],
        "pieceBudget": 6,
        "transformGrammar": ["left", "up", "right", "down", "rotate", "grow", "shrink"],
        "revisionSemantics": "explicit immutable snapshots with JSON save/load re-entry",
    },
    "checks": checks,
    "rounds": [
        {
            "round": 1,
            "revision": r1,
            "context": service_r1,
            "preferenceDecision": carrier.preference_decisions[0],
        },
        {"round": 2, "revision": r2, "context": gallery_r2, "usedAffordance": p2_anchor},
        {"round": 3, "revision": r3, "context": service_r3},
    ],
    "counterfactuals": {
        "affordancesBeforeAnyCommit": no_commit_affordances,
        "attachUsingRevisionTokenWithoutCommitRejected": attach_without_commit_rejected,
        "sameWideArtifactCommitsUnderWideIntent": intent_wide_commit["artifactDigest"],
        "sameWideArtifactRejectedUnderCompactIntent": compact_same_artifact_rejected,
        "alternateCommittedArtifactDigest": alt_r1["artifactDigest"],
        "alternateArtifactChangesAffordances": artifact_affordance_counterfactual,
        "postCommitLiveEditIgnoredByAudienceUntilNewCommit": committed_read_not_working_copy,
    },
    "reloadEvidence": {
        "afterRound1": str(RELOAD_R1.relative_to(ROOT)),
        "afterRound2": str(RELOAD_R2.relative_to(ROOT)),
        "round1ReloadPassed": r1_reload_ok,
        "round2ReloadRecoveredTwoRevisions": r2_reload_ok,
    },
    "causalTrace": {
        "I_intent": carrier.intent_history,
        "K_commits": [
            {"revisionId": r["id"], "artifactDigest": r["artifactDigest"], "intentAxis": r["intentAxis"]}
            for r in carrier.revisions
        ],
        "C_context": [entry["feedback"]["profile"] for entry in carrier.context_history],
        "R_response": [entry["feedback"]["dimensions"] for entry in carrier.context_history],
        "A_affordance": carrier.affordance_history,
        "P_progress": carrier.progress_events,
    },
    "artifactLineageDigest": canonical_digest([r1["artifactDigest"], r2["artifactDigest"], r3["artifactDigest"]]),
    "boundary": (
        "Structural carrier only. It demonstrates deterministic composition/revision, an explicit mechanically causal intent axis, "
        "recoverable committed revisions, committed-artifact-derived later affordance, conflicting qualitative context profiles, "
        "and progression after rejecting one context preference. It does not establish Human authorship, expressive ownership, "
        "aesthetic value, desire to create, enjoyment, retention, market demand, product selection, or G0 admission."
    ),
}

EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
EVIDENCE.write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, indent=2))
raise SystemExit(0 if standing.startswith("SURVIVES") else 3)
