#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

STUDY = Path(__file__).resolve().parents[1]
SUBSTRATE = STUDY / "evidence/aries-response-revision-annotation-substrate-r1.json"
R1_ATTEMPT = STUDY / "evidence/aries-response-revision-coder-campaign-attempt-r1.json"
R1_RETIRE = STUDY / "evidence/aries-response-revision-coder-r1-retirement-r1.json"
PROVIDER = STUDY / "evidence/aries-response-revision-provider-readiness-r2.json"
R1_DIR = STUDY / "campaigns/aries-response-revision-r1"
R2_DIR = STUDY / "campaigns/aries-response-revision-r2"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"expected object: {path}")
    return value


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    substrate = load(SUBSTRATE)
    historical = load(R1_ATTEMPT)
    retired = load(R1_RETIRE)
    provider = load(PROVIDER)
    plan = load(R2_DIR / "campaign-plan.json")
    if (
        substrate.get("standing")
        != "PASS_ARIES_RESPONSE_REVISION_ANNOTATION_SUBSTRATE_R1"
    ):
        raise SystemExit("annotation substrate not accepted")
    if (
        historical.get("standing")
        != "BLOCKED_NO_FROZEN_CODER_CUTS_PROVIDER_MATERIALIZATION_UNRESOLVED"
    ):
        raise SystemExit("historical R1 attempt drifted")
    if retired.get("standing") != "RETIRED_AS_GOLD_INPUT_ALL_EFFECTS_UNKNOWN_NO_RESEND":
        raise SystemExit("R1 retirement standing drifted")
    effects = retired.get("effects", [])
    if len(effects) != 8 or len({row["effectId"] for row in effects}) != 8:
        raise SystemExit("R1 retirement effect identity drifted")
    if any(row.get("standing") != "unknown" for row in effects):
        raise SystemExit("R1 retirement silently changed UNKNOWN standing")
    if any(row.get("safeToResend") is not False for row in effects):
        raise SystemExit("R1 retirement silently authorized resend")
    if any(row.get("observationCompleted") is not True for row in effects):
        raise SystemExit("R1 retirement lacks completed observation")
    counts = retired.get("counts", {})
    expected_counts = {
        "effects": 8,
        "unknown": 8,
        "observationCompleted": 8,
        "safeToResend": 0,
        "providerResourcesBound": 0,
        "frozenCoderCuts": 0,
        "semanticJudgments": 0,
    }
    if counts != expected_counts:
        raise SystemExit("R1 retirement counts drifted")
    archive = retired.get("archiveMutation", {})
    if (
        archive.get("addedEntries") != 8
        or archive.get("archiveHealthyAfter") is not True
        or archive.get("staleArchiveEntriesAfter") != 0
    ):
        raise SystemExit("R1 archive closure evidence drifted")

    if provider.get("standing") != "HOLD_PROVIDER_CHALLENGE_GATED":
        raise SystemExit("R2 provider readiness snapshot drifted")
    endpoints = provider.get("endpoints", [])
    if len(endpoints) != 3 or {row.get("endpointId") for row in endpoints} != {
        "chatgpt-carrier-11",
        "chatgpt-carrier-12",
        "chatgpt-carrier-13",
    }:
        raise SystemExit("R2 provider endpoint set drifted")
    if any(
        row.get("standing") != "CHALLENGE_GATED"
        or row.get("substrateHealthy") is not True
        for row in endpoints
    ):
        raise SystemExit("R2 provider standing snapshot drifted")
    if any(
        row.get("sendAttempted") is not False
        or row.get("providerEffectAttempted") is not False
        for row in endpoints
    ):
        raise SystemExit(
            "provider readiness snapshot unexpectedly crossed effect boundary"
        )
    if provider.get("r2LaunchAuthorized") is not False:
        raise SystemExit("R2 launch silently authorized")

    if plan.get("standing") != "PREPARED_NOT_LAUNCHED_PROVIDER_CHALLENGE_GATED":
        raise SystemExit("R2 plan standing drifted")
    if plan.get("launchGate", {}).get("launchAuthorized") is not False:
        raise SystemExit("R2 launch gate silently opened")
    if (
        plan.get("goldAdmission") != "BLOCKED_NO_FROZEN_INDEPENDENT_CODER_CUTS"
        or plan.get("modelTrainingStanding") != "BLOCKED_PENDING_GOLD_ADMISSION"
    ):
        raise SystemExit("gold/training gate silently opened")

    old_campaigns = {
        load(R1_DIR / f"coder-{f}-campaign.json")["campaignId"] for f in ("a", "b")
    }
    new_campaigns = set()
    all_new_agents: set[str] = set()
    for family in ("A", "B"):
        low = family.lower()
        old = load(R1_DIR / f"coder-{low}-campaign.json")
        new = load(R2_DIR / f"coder-{low}-campaign.json")
        shards = json.loads(
            (R2_DIR / f"coder-{low}-shards.json").read_text(encoding="utf-8")
        )
        if not isinstance(shards, list):
            raise SystemExit(f"expected shard array: {family}")
        new_campaigns.add(new["campaignId"])
        expected_id = f"campaign:aries-response-revision-coder-{low}-r2-20260924"
        if new["campaignId"] != expected_id or new["campaignId"] == old["campaignId"]:
            raise SystemExit(f"R2 campaign identity drift: {family}")
        if (
            new["sharedPrompt"] != old["sharedPrompt"]
            or new["sharedAttachments"] != old["sharedAttachments"]
        ):
            raise SystemExit(f"R2 blind input drift: {family}")
        if len(new["roster"]) != 4 or len(shards) != 4:
            raise SystemExit(f"R2 shard count drift: {family}")
        for i, (role, shard) in enumerate(zip(new["roster"], shards, strict=True), 1):
            expected_agent = f"ARIES_{family}_R2_{i:02d}"
            if role["agentId"] != expected_agent or shard["agentId"] != expected_agent:
                raise SystemExit(f"R2 agent identity drift: {family}/{i}")
            all_new_agents.add(expected_agent)
        plan_family = next(row for row in plan["families"] if row["family"] == family)
        if plan_family["specSha256"] != sha(R2_DIR / f"coder-{low}-campaign.json"):
            raise SystemExit(f"R2 spec digest drift: {family}")
        old_shards = json.loads(
            (R1_DIR / f"coder-{low}-shards.json").read_text(encoding="utf-8")
        )
        if not isinstance(old_shards, list):
            raise SystemExit(f"expected R1 shard array: {family}")
        old_units = [row["unitIds"] for row in old_shards]
        new_units = [row["unitIds"] for row in shards]
        if old_units != new_units:
            raise SystemExit(f"R2 shard membership drift: {family}")
    if old_campaigns & new_campaigns:
        raise SystemExit("R2 reused R1 campaign identity")
    if len(all_new_agents) != 8:
        raise SystemExit("R2 agent identity collision")

    result = {
        "schemaVersion": 1,
        "kind": "ordivon.research.aries-response-revision-gold-gate-r2",
        "standing": "PASS_R1_RETIRED_R2_PREPARED_PROVIDER_HOLD_NO_GOLD",
        "annotationSubstrate": substrate["standing"],
        "r1Retirement": retired["standing"],
        "r1UnknownEffects": 8,
        "r2CampaignsPrepared": 2,
        "r2AgentsPrepared": 8,
        "providerStanding": provider["standing"],
        "r2LaunchAuthorized": False,
        "goldAdmission": plan["goldAdmission"],
        "modelTrainingStanding": plan["modelTrainingStanding"],
        "truthBoundary": "PASS proves the poisoned R1 generation is preserved as UNKNOWN/no-resend evidence and a distinct R2 generation is prepared but held before provider effect. It does not establish semantic judgments, frozen coder cuts, gold, adequacy, causality, or scientific correctness.",
    }
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
