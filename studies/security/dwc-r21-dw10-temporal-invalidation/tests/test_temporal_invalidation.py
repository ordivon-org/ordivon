from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "dwc_dw10" / "temporal_invalidation.py"


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
        "epochId": "epoch:test",
        "nodes": nodes,
        "edges": edges,
        "milestones": {},
        "policyDeadline": None,
    }


def load_module():
    if not MODULE_PATH.exists():
        raise AssertionError(f"production module missing: {MODULE_PATH}")
    spec = importlib.util.spec_from_file_location("dw10_under_test", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TemporalInvalidationTests(unittest.TestCase):
    def test_policy_drift_invalidates_only_policy_descendants(self) -> None:
        mod = load_module()
        previous = base_epoch(D("3"))
        current = base_epoch(D("4"))

        result = mod.project_epoch(previous, current)

        self.assertEqual(result["changedNodeIds"], ["source:policy"])
        self.assertEqual(result["invalidatedNodeIds"], ["dw03", "dw06", "dw07", "dw08"])
        self.assertEqual(result["revalidationNodeIds"], ["dw03", "dw06", "dw07", "dw08"])
        self.assertEqual(result["selectiveRevalidationCostUnits"], 20)
        self.assertEqual(result["fullRecomputeCostUnits"], 37)
        self.assertEqual(result["costSavingsUnits"], 17)
        self.assertEqual(result["staleSupportRiskNodeIds"], ["dw03", "dw06", "dw07", "dw08"])
        self.assertFalse(result["schedulerAuthorityEstablished"])
        self.assertFalse(result["domainAcceptanceEstablished"])

    def test_dependency_topology_change_invalidates_target_and_descendants(self) -> None:
        mod = load_module()
        previous = base_epoch(D("3"))
        current = base_epoch(D("3"))
        current["edges"].append(
            edge("source:threat", "dw03", relation="additional-support", invalidates=True)
        )

        result = mod.project_epoch(previous, current)

        self.assertEqual(result["changedNodeIds"], ["dw03"])
        self.assertEqual(result["invalidatedNodeIds"], ["dw03", "dw06", "dw07", "dw08"])

    def test_non_invalidating_observation_edge_does_not_trigger_revalidation(self) -> None:
        mod = load_module()
        previous = base_epoch(D("3"))
        current = base_epoch(D("3"))
        current["edges"].append(
            edge("source:threat", "dw08", relation="observes", invalidates=False)
        )

        result = mod.project_epoch(previous, current)

        self.assertEqual(result["changedNodeIds"], [])
        self.assertEqual(result["invalidatedNodeIds"], [])

    def test_cycle_in_invalidation_graph_fails_closed(self) -> None:
        mod = load_module()
        current = base_epoch(D("3"))
        current["edges"].append(edge("dw08", "dw03", relation="bad-cycle"))

        with self.assertRaisesRegex(ValueError, "cyclic"):
            mod.project_epoch(None, current)

    def test_edge_flags_must_be_real_booleans(self) -> None:
        mod = load_module()
        current = base_epoch(D("3"))
        current["edges"][0]["invalidatesOnChange"] = "false"

        with self.assertRaisesRegex(ValueError, "boolean"):
            mod.project_epoch(None, current)

    def test_owner_identity_must_be_explicit(self) -> None:
        mod = load_module()
        current = base_epoch(D("3"))
        current["nodes"][0]["ownerId"] = ""

        with self.assertRaisesRegex(ValueError, "ownerId"):
            mod.project_epoch(None, current)

    def test_dangling_dependency_fails_closed(self) -> None:
        mod = load_module()
        current = base_epoch(D("3"))
        current["edges"].append(edge("missing:node", "dw03"))

        with self.assertRaisesRegex(ValueError, "dangling"):
            mod.project_epoch(None, current)

    def test_owner_binding_change_invalidates_dependents_even_when_digest_is_same(self) -> None:
        mod = load_module()
        previous = base_epoch(D("3"))
        current = base_epoch(D("3"))
        for item in current["nodes"]:
            if item["id"] == "source:policy":
                item["ownerId"] = "owner:policy-successor"
                break

        result = mod.project_epoch(previous, current)

        self.assertEqual(result["changedNodeIds"], ["source:policy"])
        self.assertEqual(result["invalidatedNodeIds"], ["dw03", "dw06", "dw07", "dw08"])

    def test_incomplete_timing_never_mints_precise_slack(self) -> None:
        mod = load_module()
        current = base_epoch(D("3"))
        current["milestones"] = {"T0": 0, "T2": 1000}
        current["policyDeadline"] = {
            "deadlineFromT0Ms": 12000,
            "sourceRef": "policy:dw03:v1",
        }
        for item in current["nodes"]:
            if item["id"] == "dw01":
                item["durationMs"] = 1000
                item["durationBasis"] = "OBSERVED"
                break

        result = mod.project_epoch(None, current)

        self.assertIsNone(result["latency"]["TTVPms"])
        self.assertIsNone(result["latency"]["compromiseToEradicationMs"])
        self.assertFalse(result["latency"]["attackerTimingAssumed"])
        self.assertEqual(result["criticalPath"]["standing"], "PARTIAL_UNKNOWN")
        self.assertEqual(result["criticalPath"]["slackStanding"], "UNKNOWN_DURATION")
        self.assertIsNone(result["criticalPath"]["slackMs"])
        self.assertIn("dw02", result["criticalPath"]["unknownDurationStageIds"])

    def test_public_historical_anchor_without_local_milestones_stays_unknown(self) -> None:
        mod = load_module()
        current = base_epoch(D("3"))
        current["epochId"] = "epoch:exchange-public-replay"
        current["milestones"] = {"T0": 0}
        current["policyDeadline"] = None

        result = mod.project_epoch(None, current)

        self.assertIsNone(result["latency"]["TTVPms"])
        self.assertIsNone(result["latency"]["compromiseToRecoveryMs"])
        self.assertEqual(result["criticalPath"]["standing"], "PARTIAL_UNKNOWN")
        self.assertEqual(result["criticalPath"]["slackStanding"], "UNKNOWN_DURATION")
        self.assertFalse(result["schedulerAuthorityEstablished"])
        self.assertFalse(result["domainAcceptanceEstablished"])

    def test_latency_and_known_critical_path_use_only_explicit_timing(self) -> None:
        mod = load_module()
        current = base_epoch(D("3"))
        current["milestones"] = {
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
        current["policyDeadline"] = {
            "deadlineFromT0Ms": 12000,
            "sourceRef": "policy:dw03:v1",
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
        for item in current["nodes"]:
            if item["id"] in durations:
                item["durationMs"] = durations[item["id"]]
                item["durationBasis"] = "OBSERVED"
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
        for item in current["edges"]:
            if (item["from"], item["to"]) in temporal_pairs:
                item["temporalDependency"] = True

        result = mod.project_epoch(None, current)

        self.assertEqual(result["latency"]["TTVPms"], 9000)
        self.assertEqual(result["latency"]["compromiseToEradicationMs"], 9000)
        self.assertEqual(result["latency"]["compromiseToRecoveryMs"], 11000)
        self.assertEqual(result["latency"]["eradicationToRecoveryMs"], 2000)
        self.assertEqual(result["criticalPath"]["standing"], "KNOWN")
        self.assertEqual(
            result["criticalPath"]["stageIds"],
            ["dw01", "dw02", "dw03", "dw06", "dw07", "dw08"],
        )
        self.assertEqual(result["criticalPath"]["durationMs"], 9000)
        self.assertEqual(result["criticalPath"]["slackStanding"], "KNOWN")
        self.assertEqual(result["criticalPath"]["slackMs"], 3000)
        self.assertEqual(result["criticalPath"]["deadlineSourceRef"], "policy:dw03:v1")


if __name__ == "__main__":
    unittest.main()
