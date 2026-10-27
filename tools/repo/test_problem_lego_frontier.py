"""SourceCut-bound Problem LEGO candidates; never infer runtime call semantics."""
from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
MODULE = pathlib.Path(__file__).with_name("problem_lego_frontier.py")
SPEC = importlib.util.spec_from_file_location("problem_lego_frontier", MODULE)
M = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
# Adjacent canonical importer resolves exactly this repository's source tools.
import sys
sys.path.insert(0, str(MODULE.parent))
SPEC.loader.exec_module(M)


class ProblemLegoFrontierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cut = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True,
        ).strip()
        cls.inventory = M.classification(ROOT, cls.cut)
        cls.frontier = M.project_problem_legos(cls.inventory, repo=ROOT)

    def test_covers_exactly_all_tracked_git_paths_once(self) -> None:
        f = self.frontier
        s = f["summary"]
        paths = [p for c in f["sourceUnits"] for p in c["memberPaths"]]
        expected = {r["path"] for r in self.inventory["sourcePaths"]}
        self.assertEqual(s["trackedPaths"], len(expected))
        self.assertEqual(len(paths), len(expected))
        self.assertEqual(set(paths), expected)
        self.assertEqual(s["sourceUnits"], len(f["sourceUnits"]))
        self.assertEqual(f["sourceCut"], self.cut)
        self.assertFalse(f["proofReuseAdmissible"])
        self.assertFalse(f["callerOrRuntimeAuthorityInferred"])

    def test_multilabel_cell_is_one_problem_lego_candidate(self) -> None:
        f = self.frontier
        problems = f["sourceProblemCandidates"]
        self.assertEqual(f["summary"]["sourceProblemCandidates"], len(problems))
        self.assertEqual(
            f["summary"]["sourceProblemLabelOccurrences"],
            sum(len(x["problemCodes"]) for x in problems),
        )
        self.assertEqual(
            f["summary"]["multiLabelSourceProblemCandidates"],
            sum(len(x["problemCodes"]) > 1 for x in problems),
        )
        self.assertEqual(
            len({x["sourceUnitRef"] for x in problems}), len(problems))
        self.assertEqual(
            len({x["problemLegoCandidateRef"] for x in problems}), len(problems))
        self.assertTrue(all(x["decision"].startswith("HOLD_") for x in problems))
        self.assertTrue(all(x["callSemanticsStanding"] == "NOT_ASSESSED" for x in problems))

    def test_plan_node_ids_are_plan_scoped_not_assumed_global(self) -> None:
        f = self.frontier
        nodes = f["planNodeProblemCandidates"]
        self.assertEqual(len(nodes), len(self.inventory["semanticPlans"]["nodes"]))
        self.assertEqual(len({n["nodeRef"] for n in nodes}), len(nodes))
        self.assertEqual(
            len({n["problemLegoCandidateRef"] for n in nodes}), len(nodes))
        repeated = {}
        for n in nodes:
            repeated.setdefault(n["localId"], []).append(n)
        self.assertTrue(any(len(v) > 1 for v in repeated.values()))
        cell_refs = {c["sourceUnitRef"] for c in f["sourceUnits"]}
        self.assertTrue(all(n["sourceUnitRef"] in cell_refs for n in nodes))
        self.assertEqual(f["summary"]["unqualifiedPlanNodeCandidates"], len(nodes))
        self.assertEqual(
            f["summary"]["planNodesWithDeclarationGaps"] +
            f["summary"]["planNodesWithFourRolesDeclaredButStillUnverified"], len(nodes))
        self.assertTrue(all(n["consumerStanding"] == "UNKNOWN" and
                            n["formalStanding"] == "UNKNOWN" and
                            n["implementationStanding"] == "UNKNOWN" for n in nodes))

    def test_declared_edges_are_not_promoted_to_executable_call_graph(self) -> None:
        f = self.frontier
        edges = f["deferredPlanRelationDeclarations"]
        self.assertEqual(len(edges), len(self.inventory["semanticPlans"]["edges"]))
        node_refs = {n["nodeRef"] for n in f["planNodeProblemCandidates"]}
        for e in edges:
            self.assertEqual(e["callSemanticsStanding"], "NOT_ASSESSED")
            self.assertFalse(e["executableDependencyProof"])
            for name in ("fromScopedNodeRef", "toScopedNodeRef"):
                self.assertTrue(e[name] is None or e[name] in node_refs)
        self.assertEqual(f["summary"]["consumerSemanticsResolved"], 0)
        self.assertEqual(f["summary"]["installedEquivalenceProven"], 0)

    def test_determinism_and_repartition_do_not_change_source_universe(self) -> None:
        first = self.frontier
        second = M.project_problem_legos(self.inventory, repo=ROOT)
        self.assertEqual(first, second)
        finer = M.project_problem_legos(
            self.inventory, repo=ROOT, max_files=10, max_depth=7)
        self.assertEqual(finer["sourceCut"], first["sourceCut"])
        self.assertEqual(finer["summary"]["trackedPaths"],
                         first["summary"]["trackedPaths"])
        self.assertEqual(
            {p for c in finer["sourceUnits"] for p in c["memberPaths"]},
            {p for c in first["sourceUnits"] for p in c["memberPaths"]})
        self.assertEqual(
            {n["nodeRef"] for n in finer["planNodeProblemCandidates"]},
            {n["nodeRef"] for n in first["planNodeProblemCandidates"]})
        self.assertFalse(finer["proofReuseAdmissible"])

    def test_cli_summary_never_saves_snapshot_as_current_authority(self) -> None:
        p = subprocess.run(
            ["python3", str(MODULE), "--repo", str(ROOT),
             "--source-cut", self.cut, "--summary"],
            text=True, capture_output=True, timeout=160, check=True,
        )
        x = json.loads(p.stdout)
        self.assertEqual(x["sourceCut"], self.cut)
        self.assertEqual(x["summary"], self.frontier["summary"])
        self.assertNotIn("sourceUnits", x)
        self.assertNotIn("planNodeProblemCandidates", x)
        self.assertFalse(x["proofReuseAdmissible"])
        self.assertEqual(x["defaultRemediation"],
                         "DEFER_UNTIL_CONSUMER_AND_CALL_SEMANTICS_QUALIFIED")

    def test_symbolic_git_revision_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "exact"):
            M.classification(ROOT, "HEAD")


if __name__ == "__main__":
    unittest.main()
