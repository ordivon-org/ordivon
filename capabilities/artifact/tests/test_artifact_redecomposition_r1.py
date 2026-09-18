from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "planning/lego-plan-r2.json"


class ArtifactRedecompositionR1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = json.loads(PLAN.read_text(encoding="utf-8"))

    def test_plan_is_non_authoritative_and_source_fenced(self) -> None:
        self.assertEqual(
            self.plan["truthRole"], "planning-projection-not-project-truth"
        )
        self.assertEqual(
            self.plan["project"]["sourceRevision"],
            "10d0f076c32621f50f7c60ef6f847e19ea2cc9ec",
        )

    def test_node_ids_are_unique_and_evidence_paths_exist(self) -> None:
        nodes = self.plan["nodes"]
        ids = [node["id"] for node in nodes]
        self.assertEqual(len(ids), len(set(ids)))
        for node in nodes:
            for relative in node.get("currentEvidence", []):
                self.assertTrue((ROOT / relative).exists(), (node["id"], relative))

    def test_kernel_is_exactly_five_semantic_responsibilities(self) -> None:
        kernel = [
            node for node in self.plan["nodes"]
            if node["kind"] == "kernel"
        ]
        self.assertEqual(
            [node["id"] for node in kernel],
            ["K01", "K02", "K03", "K04", "K05"],
        )
        self.assertEqual(
            [node["label"] for node in kernel],
            [
                "SubjectCommitment",
                "ProfileSemantics",
                "CapabilityBinding",
                "EvidenceObservation",
                "StandingDecision",
            ],
        )

    def test_transport_and_consumer_acceptance_are_outside_kernel(self) -> None:
        nodes = {node["id"]: node for node in self.plan["nodes"]}
        self.assertEqual(nodes["X01"]["kind"], "externalize")
        self.assertEqual(nodes["X01"]["state"], "DO_NOT_PROMOTE")
        self.assertEqual(nodes["X03"]["state"], "OUTSIDE_ARTIFACT")

    def test_next_slice_is_evaluation_model_pressure_test(self) -> None:
        slices = {item["id"]: item for item in self.plan["slices"]}
        self.assertEqual(slices["R2-S1"]["status"], "PRESSURE_TEST_COMPLETE")
        self.assertEqual(slices["R2-S1B"]["status"], "PRESSURE_TEST_COMPLETE")
        self.assertEqual(slices["R2-S1C"]["status"], "NEXT")
        self.assertIn("K05", slices["R2-S1C"]["nodeIds"])

    def test_current_empirical_topology_is_recorded(self) -> None:
        topology = self.plan["observedTopology"]
        self.assertEqual(topology["projectPythonPackageCycles"], 0)
        self.assertEqual(topology["capabilityVerifyBindings"], 19)
        self.assertEqual(topology["deliveryFacadeLines"], 750)
        self.assertEqual(topology["directPythonProviderProjectFanout"], 17)


if __name__ == "__main__":
    unittest.main()
