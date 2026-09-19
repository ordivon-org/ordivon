#!/usr/bin/env python3
"""Campaign input validation, deterministic carrier-request compilation, and effect census.

Campaign is input data only. Temporal owns durable execution; Browserless owns provider mechanics;
CarrierMaterializationRequest is the provider-effect contract. No separate occurrence lifecycle is
defined here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

try:
    from chatgpt_provider_resource import normalize_provider_resource
    from conversation_relay_carrier import CarrierMaterializationRequest, MaterializationStanding
except ModuleNotFoundError:
    from scripts.chatgpt_provider_resource import normalize_provider_resource
    from scripts.conversation_relay_carrier import (
        CarrierMaterializationRequest,
        MaterializationStanding,
    )


def _text(value: str, label: str, *, max_bytes: int = 65536) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{label} must be non-empty and trimmed")
    if len(value.encode("utf-8")) > max_bytes:
        raise ValueError(f"{label} exceeds {max_bytes} UTF-8 bytes")
    return value


def canonical_digest(value: object) -> str:
    # Migration target: RFC 8785/JCS at the admission compiler boundary. Existing persisted
    # identities are byte-equivalent for the current string-only digest inputs.
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def bytes_digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


CURRENT_ROSTER_LIMIT = 256


@dataclass(frozen=True, slots=True)
class RoleCard:
    agent_id: str
    role_card: str

    def __post_init__(self) -> None:
        _text(self.agent_id, "agentId", max_bytes=128)
        _text(self.role_card, "roleCard", max_bytes=16384)


@dataclass(frozen=True, slots=True)
class CampaignLaunchSpec:
    campaign_id: str
    shared_prompt: str
    roster: tuple[RoleCard, ...]

    def __post_init__(self) -> None:
        _text(self.campaign_id, "campaignId", max_bytes=512)
        _text(self.shared_prompt, "sharedPrompt", max_bytes=32768)
        if not self.roster:
            raise ValueError("roster must be non-empty")
        if len(self.roster) > CURRENT_ROSTER_LIMIT:
            raise ValueError(
                f"current roster exceeds service capability limit {CURRENT_ROSTER_LIMIT}"
            )
        ids = [role.agent_id for role in self.roster]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate agentId in roster")

    @property
    def is_current(self) -> bool:
        return True

    @property
    def spec_digest(self) -> str:
        raise ValueError("current CampaignSpec identity is its registry content descriptor digest")

    @classmethod
    def from_dict(cls, value: dict) -> "CampaignLaunchSpec":
        if not isinstance(value, dict):
            raise ValueError("campaign launch spec must be an object")
        allowed = {"campaignId", "sharedPrompt", "roster"}
        extra = set(value) - allowed
        missing = allowed - set(value)
        if extra:
            raise ValueError(f"unsupported CampaignSpec fields: {sorted(extra)}")
        if missing:
            raise ValueError(f"missing CampaignSpec fields: {sorted(missing)}")
        roster_raw = value["roster"]
        if not isinstance(roster_raw, list):
            raise ValueError("roster must be a list")
        roster: list[RoleCard] = []
        for row in roster_raw:
            if not isinstance(row, dict):
                raise ValueError("roster entries must be objects")
            if set(row) != {"agentId", "roleCard"}:
                raise ValueError("roster entries require exactly agentId/roleCard")
            roster.append(RoleCard(agent_id=row["agentId"], role_card=row["roleCard"]))
        return cls(
            campaign_id=value["campaignId"],
            shared_prompt=value["sharedPrompt"],
            roster=tuple(roster),
        )


def _task_prompt(shared_prompt: str, role: RoleCard) -> str:
    return shared_prompt.rstrip() + "\n\nROLE_CARD\n" + role.role_card.strip()


def compile_request(spec: CampaignLaunchSpec, role: RoleCard) -> CarrierMaterializationRequest:
    task_prompt = _task_prompt(spec.shared_prompt, role)
    task_prompt_digest = bytes_digest(task_prompt)
    role_digest = bytes_digest(role.role_card)
    effect_id = canonical_digest(
        {
            "campaignId": spec.campaign_id,
            "agentId": role.agent_id,
            "taskPromptDigest": task_prompt_digest,
        }
    )
    header = "\n".join(
        (
            f"CAMPAIGN_ID={spec.campaign_id}",
            f"AGENT_ID={role.agent_id}",
            f"TASK_PROMPT_DIGEST={task_prompt_digest}",
            f"EFFECT_ID={effect_id}",
            "",
        )
    )
    bootstrap_prompt = header + task_prompt
    bootstrap_prompt_digest = bytes_digest(bootstrap_prompt)
    preparation_digest = canonical_digest(
        {
            "effectId": effect_id,
            "roleDigest": role_digest,
            "taskPromptDigest": task_prompt_digest,
            "bootstrapPromptDigest": bootstrap_prompt_digest,
        }
    )
    if len(bootstrap_prompt.encode("utf-8")) > 16384:
        raise ValueError(f"compiled bootstrap prompt for {role.agent_id} exceeds carrier limit")
    return CarrierMaterializationRequest(
        request_id=effect_id,
        preparation_digest=preparation_digest,
        bootstrap_prompt=bootstrap_prompt,
    )


def compile_campaign(spec: CampaignLaunchSpec) -> dict[str, CarrierMaterializationRequest]:
    return {role.agent_id: compile_request(spec, role) for role in spec.roster}


def _ledger_rows(path: Path) -> dict[str, sqlite3.Row]:
    if not path.exists():
        return {}
    db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        exists = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='requests'"
        ).fetchone()
        if exists is None:
            return {}
        return {row["request_id"]: row for row in db.execute("SELECT * FROM requests")}
    finally:
        db.close()


def campaign_census(spec: CampaignLaunchSpec, ledger_path: Path) -> dict:
    requests = compile_campaign(spec)
    rows = _ledger_rows(Path(ledger_path))
    projected = []
    counts = {"unrecorded": 0, **{standing.value: 0 for standing in MaterializationStanding}}
    for agent_id, request in requests.items():
        row = rows.get(request.request_id)
        standing = None
        provider = None
        effect_generation = None
        updated_at_ms = None
        if row is None:
            counts["unrecorded"] += 1
        else:
            if row["request_digest"] != request.request_digest:
                raise RuntimeError(
                    f"durable request digest conflict for materialization {request.request_id}"
                )
            standing = MaterializationStanding(row["standing"])
            provider = (
                normalize_provider_resource(row["provider_coordinate"])
                if row["provider_coordinate"]
                else None
            )
            keys = set(row.keys())
            if "effect_generation" in keys and row["effect_generation"] is not None:
                effect_generation = int(row["effect_generation"])
            if "updated_at_ms" in keys and row["updated_at_ms"] is not None:
                updated_at_ms = int(row["updated_at_ms"])
            counts[standing.value] += 1
        projected.append(
            {
                "agentId": agent_id,
                "effectId": request.request_id,
                "materializationStanding": standing.value if standing else None,
                "providerResource": provider,
                "effectGeneration": effect_generation,
                "updatedAtMs": updated_at_ms,
                "blindResendForbidden": standing
                in {
                    MaterializationStanding.UNKNOWN,
                    MaterializationStanding.SUBMIT_OBSERVED,
                    MaterializationStanding.BOUND,
                    MaterializationStanding.READY_CONFIRMED,
                },
            }
        )
    return {
        "campaignId": spec.campaign_id,
        "requested": len(requests),
        "counts": counts,
        "occurrences": projected,
    }


def _load_spec(path: Path) -> CampaignLaunchSpec:
    return CampaignLaunchSpec.from_dict(json.loads(path.read_text(encoding="utf-8")))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    census_cmd = sub.add_parser("census")
    census_cmd.add_argument("--spec", type=Path, required=True)
    census_cmd.add_argument("--ledger", type=Path, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    result = campaign_census(_load_spec(args.spec), args.ledger)
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
