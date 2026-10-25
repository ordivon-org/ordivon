from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "planning/lego-plan-r2.json"


def _require_owner_evidence_file(root: Path, relative: str) -> None:
    """A current evidence locator must be an owner-local regular source file."""
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise AssertionError("Artifact LEGO evidence path is not canonical")
    components = relative.split("/")
    if any(not component or component in {".", ".."} for component in components):
        raise AssertionError("Artifact LEGO evidence escapes Owner")
    candidate = Path(relative)
    if candidate.is_absolute() or candidate.as_posix() != relative:
        raise AssertionError("Artifact LEGO evidence path is not canonical")
    path = root
    for component in components:
        path = path / component
        if path.is_symlink():
            raise AssertionError("Artifact LEGO evidence symlink is forbidden")
    if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise AssertionError("Artifact LEGO evidence must be an owner-local source file")


class ArtifactRedecompositionR1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = json.loads(PLAN.read_text(encoding="utf-8"))

    def test_plan_is_non_authoritative_and_source_fenced(self) -> None:
        self.assertEqual(
            self.plan["truthRole"], "planning-projection-not-project-truth"
        )
        self.assertEqual(
            self.plan["project"]["sourceRevision"],
            "3d4184a0289cc407dbb221a3919d26e5e97dedfc",
        )

    def test_node_ids_are_unique_and_evidence_paths_exist(self) -> None:
        nodes = self.plan["nodes"]
        ids = [node["id"] for node in nodes]
        self.assertEqual(len(ids), len(set(ids)))
        for node in nodes:
            references = node.get("currentEvidence", [])
            self.assertEqual(len(references), len(set(references)), node["id"])
            for relative in references:
                _require_owner_evidence_file(ROOT, relative)
        # Project-level evidence is the same Owner-local source relation.
        for relative in self.plan["project"]["evidence"]:
            _require_owner_evidence_file(ROOT, relative)

    def _require_referentially_closed(self, plan: dict) -> None:
        """R2 graph references must denote its own declared, unique vertices."""
        vertices = {node["id"] for node in plan["nodes"]}
        slices = [part["id"] for part in plan["slices"]]
        self.assertEqual(len(slices), len(set(slices)), "duplicate R2 slice identity")
        for edge in plan["edges"]:
            self.assertIn(edge["from"], vertices, "R2 edge has no producer vertex")
            self.assertIn(edge["to"], vertices, "R2 edge has no consumer vertex")
        for part in plan["slices"]:
            members = part["nodeIds"]
            self.assertEqual(len(members), len(set(members)), "duplicate R2 slice member")
            for member in members:
                self.assertIn(member, vertices, "R2 slice has no member vertex")

    def test_r2_graph_edges_and_slices_are_referentially_closed(self) -> None:
        self._require_referentially_closed(self.plan)

    def test_r2_graph_rejects_dangling_edge_and_slice_mutations(self) -> None:
        for boundary, key, replacement in (
            ("edges", "to", "MISSING_EDGE_VERTEX"),
            ("slices", "nodeIds", ["MISSING_SLICE_VERTEX"]),
        ):
            with self.subTest(boundary=boundary):
                changed = copy.deepcopy(self.plan)
                changed[boundary][0][key] = replacement
                with self.assertRaisesRegex(AssertionError, "not found"):
                    self._require_referentially_closed(changed)

    def test_cross_owner_existing_path_must_not_count_as_artifact_evidence(self) -> None:
        # A real sibling source file cannot satisfy this Owner's evidence.
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            owner = base / "artifact"
            sibling = base / "media"
            owner.mkdir()
            sibling.mkdir()
            (sibling / "README.md").write_text("# other Owner", encoding="utf-8")
            foreign = "../media/README.md"
            self.assertTrue((owner / foreign).is_file())
            with self.assertRaisesRegex(AssertionError, "escapes Owner"):
                _require_owner_evidence_file(owner, foreign)

    def test_source_evidence_rejects_symlink_and_directory_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            owner = base / "artifact"
            owner.mkdir()
            (owner / "good.py").write_text("print('ok')", encoding="utf-8")
            (base / "outside.py").write_text("print('foreign')", encoding="utf-8")
            (owner / "alias.py").symlink_to(base / "outside.py")
            _require_owner_evidence_file(owner, "good.py")
            for invalid in ("alias.py", ".", "good.py/..", "../outside.py", "missing.py"):
                with self.subTest(reference=invalid), self.assertRaises(AssertionError):
                    _require_owner_evidence_file(owner, invalid)
            (owner / "folder").mkdir()
            with self.assertRaisesRegex(AssertionError, "source file"):
                _require_owner_evidence_file(owner, "folder")

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
        self.assertEqual(slices["R2-S1C"]["status"], "PRESSURE_TEST_COMPLETE")
        self.assertIn("K05", slices["R2-S1C"]["nodeIds"])
        self.assertEqual(slices["R2-S1D"]["status"], "NEXT")
        self.assertIn("P02", slices["R2-S1D"]["nodeIds"])

    def test_current_empirical_topology_is_recorded(self) -> None:
        topology = self.plan["observedTopology"]
        self.assertEqual(topology["projectPythonPackageCycles"], 0)
        self.assertEqual(topology["capabilityVerifyBindings"], 19)
        self.assertEqual(topology["deliveryFacadeLines"], 0)
        self.assertEqual(topology["deliveryCliProviderLines"], 0)
        self.assertEqual(topology["directPythonProviderProjectFanout"], 17)


if __name__ == "__main__":
    unittest.main()
