#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

STUDY = Path(__file__).resolve().parents[1]
R1 = STUDY / "campaigns/aries-response-revision-r1"
R2 = STUDY / "campaigns/aries-response-revision-r2"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    R2.mkdir(parents=True, exist_ok=True)
    families = []
    for family in ("A", "B"):
        low = family.lower()
        old_spec = load(R1 / f"coder-{low}-campaign.json")
        old_shards = load(R1 / f"coder-{low}-shards.json")
        spec = copy.deepcopy(old_spec)
        spec["campaignId"] = f"campaign:aries-response-revision-coder-{low}-r2-20260924"
        new_roster = []
        new_shards = []
        for i, (role, shard) in enumerate(
            zip(old_spec["roster"], old_shards, strict=True), 1
        ):
            new_id = f"ARIES_{family}_R2_{i:02d}"
            nr = copy.deepcopy(role)
            nr["agentId"] = new_id
            new_roster.append(nr)
            ns = copy.deepcopy(shard)
            ns["agentId"] = new_id
            new_shards.append(ns)
        spec["roster"] = new_roster
        spec_path = R2 / f"coder-{low}-campaign.json"
        shard_path = R2 / f"coder-{low}-shards.json"
        write(spec_path, spec)
        write(shard_path, new_shards)
        families.append(
            {
                "family": family,
                "campaignId": spec["campaignId"],
                "predecessorCampaignId": old_spec["campaignId"],
                "spec": str(spec_path.relative_to(STUDY.parents[2])),
                "specSha256": sha(spec_path),
                "shards": new_shards,
                "attachmentDigest": spec["sharedAttachments"][0]["digest"],
                "attachmentRelativePath": spec["sharedAttachments"][0][
                    "stagingRelativePath"
                ],
                "attachmentPresentationName": spec["sharedAttachments"][0][
                    "presentationName"
                ],
            }
        )
    plan = {
        "schemaVersion": 1,
        "kind": "aries-response-revision-coder-campaign-plan-r2",
        "standing": "PREPARED_NOT_LAUNCHED_PROVIDER_CHALLENGE_GATED",
        "predecessor": {
            "generation": "r1",
            "retirementReceipt": "studies/research/scholarly-intelligence-r1/evidence/aries-response-revision-coder-r1-retirement-r1.json",
            "standing": "RETIRED_AS_GOLD_INPUT_ALL_EFFECTS_UNKNOWN_NO_RESEND",
        },
        "families": families,
        "providerReadinessEvidence": "studies/research/scholarly-intelligence-r1/evidence/aries-response-revision-provider-readiness-r2.json",
        "launchGate": {
            "requiredFreshStanding": "READY",
            "currentStanding": "CHALLENGE_GATED",
            "launchAuthorized": False,
            "rule": "A fresh provider preflight must establish at least one READY Browserless carrier before either R2 campaign is launched.",
        },
        "independence": "A/B retain the independently shuffled R1 blind packs while using new R2 campaign and agent identities; no R1 output is admitted into R2 coder cuts.",
        "goldAdmission": "BLOCKED_NO_FROZEN_INDEPENDENT_CODER_CUTS",
        "modelTrainingStanding": "BLOCKED_PENDING_GOLD_ADMISSION",
        "truthBoundary": "R2 preparation is a clean effect generation only. It does not imply provider readiness, materialization, semantic judgments, gold, adequacy, or causality.",
    }
    write(R2 / "campaign-plan.json", plan)
    print(json.dumps(plan, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
