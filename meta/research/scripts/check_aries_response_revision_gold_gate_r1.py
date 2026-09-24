#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

META = Path(__file__).resolve().parents[2]
SUBSTRATE = (
    META / "research/evidence/aries-response-revision-annotation-substrate-r1.json"
)
ATTEMPT = (
    META / "research/evidence/aries-response-revision-coder-campaign-attempt-r1.json"
)
PLAN = META / "research/campaigns/aries-response-revision-r1/campaign-plan.json"
A_SPEC = META / "research/campaigns/aries-response-revision-r1/coder-a-campaign.json"
B_SPEC = META / "research/campaigns/aries-response-revision-r1/coder-b-campaign.json"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def main() -> int:
    substrate = load(SUBSTRATE)
    attempt = load(ATTEMPT)
    plan = load(PLAN)
    specs = {"A": load(A_SPEC), "B": load(B_SPEC)}

    if (
        substrate.get("standing")
        != "PASS_ARIES_RESPONSE_REVISION_ANNOTATION_SUBSTRATE_R1"
    ):
        raise SystemExit("annotation substrate not accepted")
    if substrate.get("relationStanding") != "ANNOTATION_SUBSTRATE_ONLY_NO_GOLD_YET":
        raise SystemExit("annotation substrate silently promoted")
    if (
        attempt.get("standing")
        != "BLOCKED_NO_FROZEN_CODER_CUTS_PROVIDER_MATERIALIZATION_UNRESOLVED"
    ):
        raise SystemExit("campaign attempt standing drifted")
    expected_counts = {
        "requestedOccurrences": 8,
        "preEffectFailed": 6,
        "unknown": 2,
        "bound": 0,
        "providerResourcesBound": 0,
        "frozenCoderCuts": 0,
        "semanticJudgments": 0,
    }
    if attempt.get("counts") != expected_counts:
        raise SystemExit("campaign effect counts drifted")
    occurrences = attempt.get("occurrences", [])
    if len(occurrences) != 8 or len({row["agentId"] for row in occurrences}) != 8:
        raise SystemExit("campaign occurrence identity drifted")
    standing_counts = {
        standing: sum(row["standing"] == standing for row in occurrences)
        for standing in ("pre-effect-failed", "unknown", "bound")
    }
    if standing_counts != {"pre-effect-failed": 6, "unknown": 2, "bound": 0}:
        raise SystemExit("occurrence standings differ from frozen receipt")
    unknown = [row for row in occurrences if row["standing"] == "unknown"]
    if {row["agentId"] for row in unknown} != {"ARIES_A_03", "ARIES_B_03"}:
        raise SystemExit("unexpected unknown occurrence set")
    if any(row["blindRedispatchAuthorized"] for row in unknown):
        raise SystemExit("unknown occurrence silently authorized for blind redispatch")
    if any(row["providerResource"] is not None for row in occurrences):
        raise SystemExit("receipt unexpectedly claims bound provider resource")
    if attempt.get("goldAdmission") != "BLOCKED_NO_FROZEN_INDEPENDENT_CODER_CUTS":
        raise SystemExit("gold gate silently opened")
    if attempt.get("modelTrainingStanding") != "BLOCKED_PENDING_GOLD_ADMISSION":
        raise SystemExit("model training gate silently opened")
    alt = attempt.get("alternativeExecutorObservation", {})
    if alt.get("standing") != "NOT_USED_NO_EXPOSED_RUNTIME_CREDENTIAL_AUTHORITY":
        raise SystemExit("alternative executor standing drifted")
    if alt.get("currentRuntimeCredentialAuthorities") != []:
        raise SystemExit("historical credential-authority observation drifted")

    for campaign in attempt["campaigns"]:
        family = campaign["family"]
        spec = specs[family]
        if spec["campaignId"] != campaign["campaignId"]:
            raise SystemExit(f"campaign id drift: {family}")
        attachment = spec["sharedAttachments"][0]
        if attachment["digest"] != campaign["attachmentDigest"]:
            raise SystemExit(f"attachment digest drift: {family}")
        if len(spec["roster"]) != 4:
            raise SystemExit(f"coder shard count drift: {family}")

    if plan.get("standing") != "TEMPORAL_ADMITTED_PROVIDER_MATERIALIZATION_BLOCKED":
        raise SystemExit("campaign plan standing drifted")
    if plan.get("goldAdmission") != "BLOCKED_NO_FROZEN_INDEPENDENT_CODER_CUTS":
        raise SystemExit("campaign plan gold gate drifted")

    result = {
        "schemaVersion": 1,
        "kind": "ordivon.research.aries-response-revision-gold-gate",
        "standing": "PASS_EXPLICITLY_BLOCKED_ARIES_RESPONSE_REVISION_GOLD_R1",
        "annotationSubstrate": substrate["standing"],
        "campaignAttempt": attempt["standing"],
        "counts": expected_counts,
        "unknownEffectIds": [row["effectId"] for row in unknown],
        "goldAdmission": attempt["goldAdmission"],
        "modelTrainingStanding": attempt["modelTrainingStanding"],
        "truthBoundary": "PASS means the no-gold/no-training boundary is mechanically preserved despite a prepared annotation substrate. It does not mean semantic gold exists.",
    }
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
