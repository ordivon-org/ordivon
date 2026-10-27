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
