"""Negative and positive controls for exact-cut full-source coverage.

These are classification mechanics tests, not mathematical implementation
refinement or proof of semantic consumers.
"""
import importlib.util
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "exhaustive_coverage", pathlib.Path(__file__).with_name("exhaustive_coverage.py"))
M = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(M)


class FullCoverageTests(unittest.TestCase):
    def test_root_only_is_not_evidence_of_semantic_qualification(self):
        now = M.source_partition("services/runtime/src/main.rs", {
            "owners": [{"name": "runtime", "root": "services/runtime/"}]})
        self.assertEqual(now["standing"], "CLASSIFIED")
        self.assertEqual(now["classification"], "ROOT:runtime")

    def test_unknown_never_disappears(self):
        self.assertEqual(M.source_partition("unforeseen/place.rs", {"owners": []})["standing"], "UNASSIGNED")

    def test_duplicate_owner_prefix_rejected(self):
        with self.assertRaisesRegex(ValueError, "overlapping"):
            M.source_partition("services/runtime/main.rs", {"owners": [
                {"name": "one", "root": "services/"}, {"name": "two", "root": "services/runtime/"}]})

    def test_region_exclusion_protects_lego_core(self):
        policy = {"owners": [], "source_regions": [
            {"name": "methods", "paths": [".agents/skills/"],
             "exclude": [".agents/skills/recursive-lego-calculus/"]}]}
        self.assertEqual(M.source_partition(".agents/skills/recursive-lego-calculus/SKILL.md",
                                             policy)["standing"], "UNASSIGNED")

    def test_unlisted_region_overlap_fails_to_classify(self):
        regions = [{"name": s, "paths": ["meta/research/"]} for s in ("one", "two")]
        self.assertEqual(M.source_partition("meta/research/foo", {
            "owners": [], "source_regions": regions})["standing"], "AMBIGUOUS")

    def test_scope_local_id_and_no_runtime_promotion(self):
        sha = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                                      text=True).strip()
        p = M.classification(ROOT, sha)
        self.assertFalse(p["proofReuseAdmissible"])
        self.assertEqual(p["summary"]["trackedPaths"], p["summary"]["accountedForPaths"])
        self.assertEqual(p["summary"]["nodes"], len(p["semanticPlans"]["nodes"]))
        self.assertTrue(all(n["formalQualification"] == "UNKNOWN" for n in p["semanticPlans"]["nodes"]))
        self.assertGreater(p["summary"]["trackedPaths"], 1)

    def test_result_deterministic_under_same_source(self):
        sha = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                                      text=True).strip()
        a = M.classification(ROOT, sha)
        b = M.classification(ROOT, sha)
        self.assertEqual(a["sourcePathDigest"], b["sourcePathDigest"])
        self.assertEqual(a["summary"], b["summary"])

    def test_symbolic_commit_rejected(self):
        with self.assertRaisesRegex(ValueError, "exact"):
            M.classification(ROOT, "HEAD")

    def test_nested_structure_mapping_is_not_a_duplicate_semantic_owner(self):
        from collections import Counter
        sha = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                                      text=True).strip()
        out = M.classification(ROOT, sha)
        self.assertNotIn("MULTIPLE_STRUCTURE_MAPPING_CANDIDATES",
                         out["summary"]["sourceProblemCounts"])
        self.assertNotIn("EQUALLY_SPECIFIC_STRUCTURE_MAPPINGS",
                         out["summary"]["sourceProblemCounts"])

    def test_types_of_source_carriers(self):
        self.assertEqual(M.entrypoint_kind("domains/game/Cargo.toml"), "Cargo.toml")
        self.assertEqual(M.entrypoint_kind(".agents/skills/method/SKILL.md"), "SKILL.md")
        self.assertIsNone(M.entrypoint_kind("README.md"))


if __name__ == "__main__":
    unittest.main()



class LiveRecursiveCellsTests(unittest.TestCase):
    def test_live_recursive_cells_cover_current_git_without_static_snapshot(self) -> None:
        sha = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True,
        ).strip()
        source = M.classification(ROOT, sha)
        out = M.active_source_cells(source, repo=ROOT, max_files=24, max_depth=6)
        assert out["sourceCut"] == sha
        assert out["sourceTree"] == source["sourceTree"]
        assert out["proposalCut"] is None
        assert out["summary"]["trackedPaths"] == out["summary"]["countedPaths"]
        assert out["summary"]["trackedPaths"] == len(source["sourcePaths"])
        assert out["summary"]["cells"] == len(out["cells"])
        assert out["summary"]["cells"] > out["summary"]["sourceZones"]
        assert out["proofReuseAdmissible"] is False
        assert all(x["semanticStanding"] == "UNQUALIFIED_SOURCE_CELL" for x in out["cells"])
        assert all(x["memberGitObjectDigest"].startswith("sha256:") for x in out["cells"])
        assert all(x["consumerStanding"] == "UNKNOWN" for x in out["cells"])
        assert all(x["installedStanding"] == "UNKNOWN" for x in out["cells"])
        assert all(x["formalStanding"] == "UNKNOWN" for x in out["cells"])
        assert "sourceRepo" not in out and "sourceRepo" not in source


    def test_live_recursive_cells_preserve_node_gap_counts_and_unknown_source(self) -> None:
        sha = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True,
        ).strip()
        source = M.classification(ROOT, sha)
        out = M.active_source_cells(source, repo=ROOT)
        from collections import Counter
        source_problems = Counter()
        plan_problems = Counter()
        for cell in out["cells"]:
            source_problems.update(cell["sourceProblemCounts"])
            plan_problems.update(cell["planDeclarationProblemCounts"])
        assert dict(source_problems) == source["summary"]["sourceProblemCounts"]
        assert dict(plan_problems) == source["summary"]["nodeProblems"]
        assert sum(cell["pathCount"] for cell in out["cells"]
                   if cell["sourceZone"] == "UNASSIGNED") == sum(
            p["currentSource"]["standing"] != "CLASSIFIED"
            for p in source["sourcePaths"]
        )
        assert not any("OWNER_PROOF" in cell["problems"] for cell in out["cells"])


    def test_exact_path_query_covers_all_source_bytes_once_without_claiming_proof(self) -> None:
        sha = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True,
        ).strip()
        inventory = M.classification(ROOT, sha)
        exact_paths = [r["path"] for r in inventory["sourcePaths"]]
        cells = M.active_source_cells(inventory, repo=ROOT, include_member_index=True)
        memberships = cells["memberCellDigests"]
        self.assertEqual(set(memberships), set(exact_paths))
        self.assertEqual(len(memberships), inventory["summary"]["trackedPaths"])
        self.assertEqual(sum(x["pathCount"] for x in cells["cells"]), len(memberships))
        self.assertEqual({x["memberGitObjectDigest"] for x in cells["cells"]},
                         set(memberships.values()))
        out = M.lookup_source_paths(inventory, repo=ROOT, paths=exact_paths[:32])
        self.assertEqual(out["sourceCut"], sha)
        self.assertEqual(out["sourceTree"], inventory["sourceTree"])
        self.assertEqual(out["lookupCount"], 32)
        self.assertFalse(out["proofReuseAdmissible"])
        self.assertEqual({r["query"] for r in out["lookups"]}, set(exact_paths[:32]))
        actual = {r["path"]: r for r in inventory["sourcePaths"]}
        for row in out["lookups"]:
            self.assertEqual(row["standing"], "EXACT_GIT_SOURCE")
            self.assertEqual(row["sourceIdentity"], actual[row["query"]]["sourceIdentity"])
            self.assertEqual(row["currentSource"], actual[row["query"]]["currentSource"])
            self.assertEqual(row["consumerStanding"], "UNKNOWN")
            self.assertEqual(row["installedStanding"], "UNKNOWN")
            self.assertEqual(row["formalStanding"], "UNKNOWN")
            self.assertTrue(row["sourceCell"]["memberGitObjectDigest"].startswith("sha256:"))
            self.assertTrue(row["agentNavigationLabel"].startswith(
                row["sourceCell"]["sourceZone"] + " :: "
            ))

    def test_unknown_exact_path_and_misleading_aliases_fail_closed(self) -> None:
        sha = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True,
        ).strip()
        inventory = M.classification(ROOT, sha)
        queries = [
            "extensions/ordivon-control-plane/plugin.json",
            "meta/next/authorities/records/iso/",
            "tools/formal/LatentInputReachability.lean",
            "/etc/ordivon/secret",
            "meta/next/../tools/repo/exhaustive_coverage.py",
            "README.md",
            "README.MD",
            "",
        ]
        out = M.lookup_source_paths(inventory, repo=ROOT, paths=queries)
        statuses = [x["standing"] for x in out["lookups"]]
        self.assertEqual(statuses, [
            "EXACT_GIT_SOURCE", "INVALID_SOURCE_LOCATOR",
            "NOT_IN_SOURCE_CUT", "INVALID_SOURCE_LOCATOR",
            "INVALID_SOURCE_LOCATOR", "EXACT_GIT_SOURCE",
            "NOT_IN_SOURCE_CUT", "INVALID_SOURCE_LOCATOR",
        ])
        plugin = out["lookups"][0]
        self.assertEqual(plugin["carrierType"], "plugin.json")
        self.assertEqual(plugin["sourceCell"]["sourceZone"], "ROOT:control-plugin")
        self.assertEqual(plugin["semanticStanding"], "UNKNOWN")
        self.assertIsNone(out["lookups"][2]["sourceIdentity"])

    def test_path_query_does_not_mutate_default_cell_projection(self) -> None:
        sha = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True,
        ).strip()
        inventory = M.classification(ROOT, sha)
        before = M.active_source_cells(inventory, repo=ROOT)
        self.assertNotIn("memberCellDigests", before)
        query = M.lookup_source_paths(inventory, repo=ROOT, paths=[
            "tools/repo/exhaustive_coverage.py"
        ])
        after = M.active_source_cells(inventory, repo=ROOT)
        self.assertEqual(before, after)
        self.assertEqual(query["lookups"][0]["standing"], "EXACT_GIT_SOURCE")
        with self.assertRaisesRegex(ValueError, "cell limits"):
            M.lookup_source_paths(inventory, repo=ROOT, paths=["README.md"],
                                  max_files=0)
        with self.assertRaisesRegex(ValueError, "1..32"):
            M.lookup_source_paths(inventory, repo=ROOT, paths=["README.md"] * 33)

    def test_live_recursive_cells_reject_unqualified_proposal_or_invalid_limits(self) -> None:
        sha = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True,
        ).strip()
        source = M.classification(ROOT, sha)
        for files, depth in ((0, 5), (24, 0), (24, 13)):
            with self.assertRaises(ValueError):
                M.active_source_cells(source, repo=ROOT, max_files=files, max_depth=depth)
        with self.assertRaisesRegex(ValueError, "proposal"):
            M.active_source_cells(source, repo=ROOT, use_proposal=True)


    def test_live_recursive_cells_report_dense_unsplittable_as_problem(self) -> None:
        sha = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True,
        ).strip()
        source = M.classification(ROOT, sha)
        out = M.active_source_cells(source, repo=ROOT, max_files=1, max_depth=1)
        assert out["summary"]["countedPaths"] == len(source["sourcePaths"])
        assert out["summary"]["problemCounts"]["DENSE_CELL_REQUIRES_SUBCLASSIFICATION_REVIEW"] > 0
        assert len(out["cells"]) > out["summary"]["sourceZones"]
