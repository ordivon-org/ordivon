#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

SOURCE = Path(
    "/root/projects/ordivon-corpora/scholarly-data/aries/"
    "aries-response-revision-annotation-r1-20260924"
)
STAGE_ROOT = Path("/mnt/c/ProgramData/Ordivon/chat-ingress")
STAGE_REL = Path("attachments/aries-response-revision-r1")
CAMPAIGN_DIR = Path("studies/research/scholarly-intelligence-r1/campaigns/aries-response-revision-r1")
PROTOCOL_PATH = Path(
    "studies/research/scholarly-intelligence-r1/data/ARIES_RESPONSE_REVISION_ANNOTATION_PROTOCOL_R1.md"
)
SHARDS = 4


def sha(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(x)
        for x in path.read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]


def main() -> int:
    protocol = PROTOCOL_PATH.read_text(encoding="utf-8")
    CAMPAIGN_DIR.mkdir(parents=True, exist_ok=True)
    (STAGE_ROOT / STAGE_REL).mkdir(parents=True, exist_ok=True)
    campaign_manifest = []
    for family in ("A", "B"):
        units = read_jsonl(SOURCE / f"coder-packs/coder-{family.lower()}-units.jsonl")
        shards = [units[i::SHARDS] for i in range(SHARDS)]
        bundle = {
            "schemaVersion": 1,
            "kind": "aries-response-revision-blind-coder-pack-r1",
            "family": family,
            "protocol": protocol,
            "units": units,
            "diagnosticRankingIncluded": False,
            "outputContract": {
                "format": "JSONL",
                "schema": "aries-response-revision-annotation-v1",
                "doNotRepeatPaperText": True,
            },
        }
        raw = (
            json.dumps(
                bundle, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
            + "\n"
        ).encode()
        stage_rel = STAGE_REL / f"coder-{family.lower()}-pack.json"
        stage_abs = STAGE_ROOT / stage_rel
        if stage_abs.exists() and stage_abs.read_bytes() != raw:
            raise SystemExit(
                f"refusing to overwrite changed staged attachment: {stage_abs}"
            )
        stage_abs.write_bytes(raw)
        digest = sha(raw)
        roster = []
        assignment = []
        for i, shard in enumerate(shards, 1):
            unit_ids = [x["unitId"] for x in shard]
            roster.append(
                {
                    "agentId": f"ARIES_{family}_{i:02d}",
                    "roleCard": (
                        f"Independent blinded semantic coder family {family}, shard {i}/{SHARDS}. "
                        "Use only the attached protocol and attached units. Do not search the web, do not use any ranking/score, "
                        "and do not infer causality, adequacy, or scientific correctness. Annotate ONLY the unitIds listed in your shard assignment. "
                        "Return one JSON object per assigned unit, newline-delimited, exactly matching the annotation schema. "
                        "Set coderId to your AGENT_ID. Do not repeat concern/response/revision text in your output. "
                        f"Assigned unitIds: {','.join(unit_ids)}"
                    ),
                }
            )
            assignment.append(
                {
                    "agentId": f"ARIES_{family}_{i:02d}",
                    "unitIds": unit_ids,
                    "unitCount": len(unit_ids),
                }
            )
        spec = {
            "campaignId": f"campaign:aries-response-revision-coder-{family.lower()}-r1-20260924",
            "sharedPrompt": (
                "This is a blinded scholarly annotation task. Read the attached ARIES response-revision coder pack and its embedded protocol. "
                "Your role card identifies the only units you may annotate. Judge semantic realization only. "
                "Do not infer causality, adequacy, scientific truth, acceptance, or reviewer correctness. "
                "Do not browse or consult other agents. Output JSONL only, with no markdown fences and no prose outside the JSON objects."
            ),
            "roster": roster,
            "sharedAttachments": [
                {
                    "stagingRelativePath": str(stage_rel).replace("\\", "/"),
                    "digest": digest,
                    "mediaType": "application/json",
                    "presentationName": f"ARIES_RESPONSE_REVISION_CODER_{family}_R1.json",
                }
            ],
        }
        spec_path = CAMPAIGN_DIR / f"coder-{family.lower()}-campaign.json"
        spec_path.write_text(
            json.dumps(spec, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        assign_path = CAMPAIGN_DIR / f"coder-{family.lower()}-shards.json"
        assign_path.write_text(
            json.dumps(assignment, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        campaign_manifest.append(
            {
                "family": family,
                "campaignId": spec["campaignId"],
                "spec": str(spec_path),
                "attachmentRelativePath": str(stage_rel).replace("\\", "/"),
                "attachmentDigest": digest,
                "attachmentBytes": len(raw),
                "shards": assignment,
            }
        )
    manifest = {
        "schemaVersion": 1,
        "kind": "aries-response-revision-coder-campaign-plan-r1",
        "standing": "PREPARED_NOT_LAUNCHED",
        "families": campaign_manifest,
        "independence": "A/B use independently shuffled source packs and distinct campaigns/effect identities.",
        "goldAuthority": "Neither campaign output is gold before merge/agreement/adjudication gates.",
    }
    (CAMPAIGN_DIR / "campaign-plan.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
