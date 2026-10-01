from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dwc_dw10 import canonical_digest, project_epoch  # noqa: E402


def D(ch: str) -> str:
    return "sha256:" + ch * 64


def node(node_id: str, *, role: str, digest: str, standing: str = "CURRENT", cost: int = 0, kind: str = "stage") -> dict:
    return {
        "id": node_id,
        "role": role,
        "kind": kind,
        "ownerId": f"owner:{node_id}",
        "stateDigest": digest,
        "standing": standing,
        "revalidationCostUnits": cost,
    }


def edge(source: str, target: str, *, relation: str = "requires", invalidates: bool = True, temporal: bool = False) -> dict:
    return {
        "from": source,
        "to": target,
        "relation": relation,
        "invalidatesOnChange": invalidates,
        "temporalDependency": temporal,
    }


def base_epoch(policy_digest: str) -> dict:
    nodes = [
        node("source:subject", role="source", kind="subject", digest=D("1")),
        node("source:threat", role="source", kind="threat", digest=D("2")),
        node("source:policy", role="source", kind="policy", digest=policy_digest),
        node("dw01", role="derived", digest=D("a"), standing="VERIFIED", cost=1),
        node("dw02", role="derived", digest=D("b"), standing="VERIFIED", cost=2),
        node("dw03", role="derived", digest=D("c"), standing="VERIFIED", cost=2),
        node("dw04", role="derived", digest=D("d"), standing="VERIFIED", cost=3),
        node("dw05", role="derived", digest=D("e"), standing="VERIFIED", cost=4),
        node("dw06", role="derived", digest=D("f"), standing="VERIFIED", cost=5),
        node("dw07", role="derived", digest=D("6"), standing="VERIFIED", cost=8),
        node("dw08", role="derived", digest=D("7"), standing="VERIFIED", cost=5),
        node("dw09", role="derived", digest=D("8"), standing="VERIFIED", cost=7),
    ]
    edges = [
        edge("source:subject", "dw01"),
        edge("source:threat", "dw02"),
        edge("dw01", "dw02"),
        edge("dw01", "dw03"),
        edge("dw02", "dw03"),
        edge("source:policy", "dw03"),
        edge("dw01", "dw04"),
        edge("dw02", "dw04"),
        edge("dw04", "dw05"),
        edge("dw03", "dw06"),
        edge("dw04", "dw06"),
        edge("dw05", "dw06"),
        edge("dw06", "dw07"),
        edge("dw07", "dw08"),
        edge("dw01", "dw09"),
        edge("dw02", "dw09"),
        edge("dw04", "dw09"),
    ]
    return {
        "schemaVersion": 1,
        "kind": "ordivon.dwc-defense-epoch",
        "epochId": "epoch:synthetic",
        "nodes": nodes,
        "edges": edges,
        "milestones": {},
        "policyDeadline": None,
    }


def timed_epoch() -> dict:
    epoch = base_epoch(D("3"))
    epoch["epochId"] = "epoch:synthetic-timed"
    epoch["milestones"] = {
        "T0": 0,
        "T1": 500,
        "T2": 1500,
        "T3": 2500,
        "T4": 3000,
        "T5": 5000,
        "T6": 6000,
        "T7": 9000,
        "Tc": 1000,
        "Te": 10000,
        "Tr": 12000,
    }
    epoch["policyDeadline"] = {
        "deadlineFromT0Ms": 12000,
        "sourceRef": "policy:dw03:synthetic-v1",
    }
    durations = {
        "dw01": 1000,
        "dw02": 1000,
        "dw03": 2000,
        "dw04": 500,
        "dw05": 500,
        "dw06": 1000,
        "dw07": 3000,
        "dw08": 1000,
        "dw09": 400,
    }
    temporal_pairs = {
        ("dw01", "dw02"),
        ("dw02", "dw03"),
        ("dw03", "dw06"),
        ("dw01", "dw04"),
        ("dw04", "dw05"),
        ("dw05", "dw06"),
        ("dw06", "dw07"),
        ("dw07", "dw08"),
        ("dw02", "dw09"),
    }
    for item in epoch["nodes"]:
        if item["id"] in durations:
            item["durationMs"] = durations[item["id"]]
            item["durationBasis"] = "OBSERVED"
    for item in epoch["edges"]:
        if (item["from"], item["to"]) in temporal_pairs:
            item["temporalDependency"] = True
    return epoch


def exchange_public_negative_control() -> dict:
    epoch = base_epoch(D("3"))
    epoch["epochId"] = "epoch:exchange-public-replay"
    epoch["milestones"] = {"T0": 0}
    epoch["policyDeadline"] = None
    return epoch


def main() -> int:
    previous = base_epoch(D("3"))
    current = base_epoch(D("4"))
    invalidation = project_epoch(previous, current)
    timed = project_epoch(None, timed_epoch())
    historical = project_epoch(None, exchange_public_negative_control())

    assert invalidation["invalidatedNodeIds"] == ["dw03", "dw06", "dw07", "dw08"]
    assert invalidation["selectiveRevalidationCostUnits"] == 20
    assert invalidation["fullRecomputeCostUnits"] == 37
    assert invalidation["costSavingsUnits"] == 17
    assert timed["latency"]["TTVPms"] == 9000
    assert timed["criticalPath"]["durationMs"] == 9000
    assert timed["criticalPath"]["slackMs"] == 3000
    assert historical["latency"]["TTVPms"] is None
    assert historical["criticalPath"]["standing"] == "PARTIAL_UNKNOWN"

    receipt = {
        "schemaVersion": 1,
        "kind": "ordivon.dwc-dw10-fixture-receipt",
        "standing": "PASS",
        "syntheticSelectiveInvalidation": {
            "changedNodeIds": invalidation["changedNodeIds"],
            "invalidatedNodeIds": invalidation["invalidatedNodeIds"],
            "selectiveRevalidationCostUnits": invalidation["selectiveRevalidationCostUnits"],
            "fullRecomputeCostUnits": invalidation["fullRecomputeCostUnits"],
            "costSavingsUnits": invalidation["costSavingsUnits"],
            "costSavingsRatio": invalidation["costSavingsRatio"],
            "staleSupportRiskNodeIds": invalidation["staleSupportRiskNodeIds"],
        },
        "syntheticTemporalPerformance": {
            "TTVPms": timed["latency"]["TTVPms"],
            "compromiseToEradicationMs": timed["latency"]["compromiseToEradicationMs"],
            "compromiseToRecoveryMs": timed["latency"]["compromiseToRecoveryMs"],
            "criticalPathStageIds": timed["criticalPath"]["stageIds"],
            "criticalPathDurationMs": timed["criticalPath"]["durationMs"],
            "policySlackMs": timed["criticalPath"]["slackMs"],
            "deadlineSourceRef": timed["criticalPath"]["deadlineSourceRef"],
        },
        "exchangePublicNegativeControl": {
            "publicAnchors": [
                {
                    "sourceRef": "MSRC:2021-03-02:exchange-security-updates",
                    "date": "2021-03-02",
                    "role": "public signal anchor only",
                },
                {
                    "sourceRef": "CISA:ED-21-02:2021-03-03",
                    "date": "2021-03-03",
                    "role": "public response anchor only",
                },
            ],
            "localTTVPms": historical["latency"]["TTVPms"],
            "localCompromiseToRecoveryMs": historical["latency"]["compromiseToRecoveryMs"],
            "criticalPathStanding": historical["criticalPath"]["standing"],
            "slackStanding": historical["criticalPath"]["slackStanding"],
            "attackerTimingAssumed": historical["latency"]["attackerTimingAssumed"],
        },
        "schedulerAuthorityEstablished": False,
        "domainAcceptanceEstablished": False,
        "claimBoundary": (
            "Synthetic timing demonstrates projection mechanics only. Public Exchange dates "
            "anchor historical replay but do not establish any organization's local TTVP, "
            "compromise timing, eradication timing, recovery timing, or attacker slack."
        ),
    }
    receipt["receiptDigest"] = canonical_digest(receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
