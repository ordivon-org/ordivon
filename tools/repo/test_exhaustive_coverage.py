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


class PythonStaticConsumerFrontierTests(unittest.TestCase):
    """Exact Git source import witnesses, not runtime/consumer qualification."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.source = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True,
        ).strip()
        cls.frontier = M.static_python_import_frontier(
            ROOT, cls.source, focus_prefix="services/harness/")

    def test_named_harness_plugin_test_has_actual_source_import_candidate(self) -> None:
        matching = [x for x in self.frontier["staticCandidateEdges"]
                    if x["consumerPath"] ==
                    "services/harness/tests/test_agent_plugin_composition.py"
                    and x["providerPath"] ==
                    "services/harness/src/ordivon_harness/agent_plugin.py"]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["moduleExpression"], "ordivon_harness.agent_plugin")
        self.assertEqual(matching[0]["runtimeConsumerStanding"], "UNKNOWN")
        self.assertEqual(matching[0]["agentQueryHandle"],
                         "python-module:ordivon_harness.agent_plugin")
        self.assertEqual(matching[0]["consumerSourceRole"],
                         "TEST_SOURCE_IMPORT_SYNTAX")

    def test_script_import_witness_and_current_risk_boundaries(self) -> None:
        actual = [x for x in self.frontier["staticCandidateEdges"] if x["consumerPath"] ==
                  "services/harness/scripts/agent_automation_mcp.py"]
        providers = {x["providerPath"] for x in actual}
        self.assertIn("services/harness/scripts/agent_automation_browserless.py", providers)
        self.assertIn("services/harness/scripts/agent_automation_registry.py", providers)
        self.assertIn("services/harness/scripts/standard_identifiers.py", providers)
        self.assertFalse(self.frontier["proofReuseAdmissible"])
        self.assertFalse(self.frontier["summary"]["zeroStaticEdgesProvesNoConsumers"])
        self.assertEqual(
            self.frontier["summary"]["gitPythonPaths"],
            self.frontier["summary"]["sourceModuleLayoutIndexed"] +
            self.frontier["summary"]["sourceModuleLayoutUnknown"])
        self.assertGreater(self.frontier["summary"]["allUnresolvedImportStatements"], 0)
        self.assertGreater(self.frontier["summary"]["allDynamicSyntaxSites"], 0)

    def test_source_path_lexical_module_is_never_installed_authority(self) -> None:
        self.assertEqual(
            M._python_module_path(
                "services/harness/src/ordivon_harness/agent_plugin.py"),
            ("ordivon_harness.agent_plugin", "services/harness/src/"))
        self.assertEqual(
            M._python_module_path(
                "services/harness/scripts/agent_automation_browserless.py"),
            ("agent_automation_browserless", "services/harness/scripts/"))
        self.assertIsNone(M._python_module_path("services/harness/evidence/claim.json"))

    def test_non_src_python_package_needs_real_init_files(self) -> None:
        module = "capabilities/artifact/artifact_capabilities/presentation/admission.py"
        inits = {
            "capabilities/artifact/artifact_capabilities/__init__.py",
            "capabilities/artifact/artifact_capabilities/presentation/__init__.py",
        }
        self.assertEqual(
            M._python_module_path(module, inits),
            ("artifact_capabilities.presentation.admission", "capabilities/artifact/"))
        self.assertIsNone(M._python_module_path(module, set()))
        self.assertEqual(
            M._python_module_path(
                "capabilities/artifact/artifact_capabilities/presentation/__init__.py",
                inits),
            ("artifact_capabilities.presentation", "capabilities/artifact/"))
        # Without the parent marker, the exact *candidate search root*
        # changes; neither variant guarantees runtime sys.path resolution.
        self.assertEqual(
            M._python_module_path(module, {
                "capabilities/artifact/artifact_capabilities/presentation/__init__.py"}),
            ("presentation.admission",
             "capabilities/artifact/artifact_capabilities/"))

    def test_exact_cut_required_and_invalid_prefix_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "exact"):
            M.static_python_import_frontier(ROOT, "HEAD")
        for path in ("", "/services/", "services/../harness/",
                     "services//harness/", "services/./harness/",
                     "services" + chr(92) + "harness/"):
            with self.assertRaisesRegex(ValueError, "canonical"):
                M.static_python_import_frontier(ROOT, self.source, focus_prefix=path)

    def test_import_frontier_remains_bounded_when_no_prefix_witness(self) -> None:
        output = M.static_python_import_frontier(
            ROOT, self.source, focus_prefix="unused/static/no-such-source/")
        self.assertEqual(output["summary"]["selectedEdges"], 0)
        self.assertFalse(output["summary"]["zeroStaticEdgesProvesNoConsumers"])
        self.assertEqual(output["sourceCut"], self.source)

    def test_ambiguous_module_name_fails_closed_without_preferred_owner(self) -> None:
        out = M.static_python_import_frontier(
            ROOT, self.source,
            focus_prefix="domains/capital/tests/test_accounting_substrate_type_authority.py")
        unresolved = [x for x in out["unresolvedImportStatements"]
                      if x["standing"] == "AMBIGUOUS_MODULE_CANDIDATES"]
        self.assertTrue(any(x["expression"] == "ordivon_capital.accounting"
                            for x in unresolved))
        self.assertFalse(any(x["moduleExpression"] == "ordivon_capital.accounting"
                             for x in out["staticCandidateEdges"]))
        self.assertGreater(out["summary"]["sourceModuleLayoutUnknown"], 0)
        self.assertFalse(out["summary"]["zeroStaticEdgesProvesNoConsumers"])


class ExactGitCrossFormatReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cut = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            text=True,
        ).strip()

    def test_artifact_schema_has_json_and_code_lexical_witnesses(self) -> None:
        target = (
            "capabilities/artifact/artifact-delivery/shadow-contracts/"
            "audio-flac-contract-v1.schema.json"
        )
        result = M.exact_git_reference_hints(ROOT, self.cut, [target])
        self.assertEqual(result["sourceCut"], self.cut)
        self.assertFalse(result["proofReuseAdmissible"])
        query = result["queries"][0]
        self.assertTrue(query["basenameUniqueInSource"])
        hits = query["textualHits"]
        self.assertTrue(any(h["candidateConsumerPath"] ==
                            "capabilities/artifact/scripts/artifact_audio.py"
                            for h in hits))
        self.assertTrue(any(h["candidateConsumerPath"] ==
                            "capabilities/artifact/artifact-delivery/donor-r1/manifest.json"
                            for h in hits))
        self.assertTrue(all(h["semanticConsumerStanding"] == "UNKNOWN"
                            for h in hits))
        self.assertTrue(all(h["installedConsumerStanding"] == "UNKNOWN"
                            for h in hits))
        self.assertTrue(all(h["sourceLine"] > 0 for h in hits))
        self.assertTrue(any(h["candidateConsumerCarrierRole"] ==
                            "JSON_DECLARATION_LITERAL_REFERENCE" for h in hits))
        self.assertTrue(any(h["candidateConsumerCarrierRole"] ==
                            "PYTHON_SOURCE_LITERAL_REFERENCE" for h in hits))
        self.assertFalse(query["zeroTextualHitsProvesNoConsumers"])

    def test_bounded_limit_does_not_exclude_evidence_without_disclosure(self) -> None:
        target = (
            "capabilities/artifact/artifact-delivery/shadow-contracts/"
            "audio-flac-contract-v1.schema.json"
        )
        query = M.exact_git_reference_hints(
            ROOT, self.cut, [target], per_path_limit=1,
        )["queries"][0]
        self.assertTrue(query["truncated"])
        self.assertGreater(query["totalTextualHits"], 1)
        self.assertEqual(len(query["textualHits"]), 1)

    def test_absent_path_and_ambiguous_common_basename_do_not_grant_edges(self) -> None:
        result = M.exact_git_reference_hints(
            ROOT, self.cut,
            ["nonexistent/no-such-source.json",
             "extensions/ordivon-control-plane/plugin.json"],
        )
        self.assertEqual(result["queries"][0]["standing"],
                         "NOT_IN_EXACT_GIT_SOURCE")
        self.assertFalse(result["queries"][1]["basenameUniqueInSource"])
        self.assertNotIn("plugin.json", result["queries"][1]["patternsUsed"])
        self.assertFalse(result["queries"][0]["zeroTextualHitsProvesNoConsumers"])

    def test_bad_cut_invalid_relative_path_and_bounds_fail_closed(self) -> None:
        target = "capabilities/artifact/scripts/artifact_audio.py"
        with self.assertRaises(ValueError):
            M.exact_git_reference_hints(ROOT, "HEAD", [target])
        for query in ("", "/etc/hosts", "foo/../bar", "foo//bar", "foo/./bar"):
            with self.assertRaises(ValueError):
                M.exact_git_reference_hints(ROOT, self.cut, [query])
        with self.assertRaises(ValueError):
            M.exact_git_reference_hints(ROOT, self.cut, [target] * 9)
        with self.assertRaises(ValueError):
            M.exact_git_reference_hints(ROOT, self.cut, [target], per_path_limit=0)
        with self.assertRaises(ValueError):
            M.exact_git_reference_hints(ROOT, self.cut, [target], per_path_limit=257)



class DerivedProblemLegoFrontierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sha = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            text=True,
        ).strip()
        cls.inventory = M.classification(ROOT, cls.sha)
        cls.result = M.derived_problem_legos(cls.inventory, repo=ROOT)

    def test_every_tracked_git_source_is_mapped_to_one_recursive_cell(self) -> None:
        output = self.result
        summary = output["summary"]
        self.assertEqual(output["sourceCut"], self.sha)
        self.assertEqual(output["sourceTree"], self.inventory["sourceTree"])
        self.assertFalse(output["proofReuseAdmissible"])
        self.assertEqual(summary["trackedPaths"], summary["countedPaths"])
        self.assertEqual(summary["trackedPaths"], len(output["sourcePathCellIndex"]))
        self.assertEqual(summary["recursiveSourceCells"], len(output["sourceCells"]))
        refs = {cell["sourceCellRef"] for cell in output["sourceCells"]}
        self.assertEqual(len(refs), len(output["sourceCells"]))
        self.assertTrue(set(output["sourcePathCellIndex"].values()) <= refs)

    def test_problem_refs_are_unique_and_bound_to_observed_cells_or_plans(self) -> None:
        output = self.result
        refs = {cell["sourceCellRef"] for cell in output["sourceCells"]}
        problems = output["problemLegos"]
        self.assertEqual(len({p["problemRef"] for p in problems}), len(problems))
        self.assertEqual(output["summary"]["issueRecords"], len(problems))
        self.assertEqual(output["summary"]["issueKinds"].get(
            "RECURSIVE_SOURCE_CELL_ISSUE"), len([
                x for x in problems if x["kind"] == "RECURSIVE_SOURCE_CELL_ISSUE"]))
        self.assertEqual(output["summary"]["issueKinds"].get(
            "PLAN_NODE_DECLARATION_ISSUE"), len([
                x for x in self.inventory["semanticPlans"]["nodes"] if x["problems"]]))
        for problem in problems:
            if "sourceCellRef" in problem:
                self.assertIn(problem["sourceCellRef"], refs)
            self.assertEqual(problem["callSemanticsStanding"], "NOT_YET_QUALIFIED")
            self.assertEqual(
                problem["remediationStanding"], "DEFER_UNTIL_JOINT_CALL_SEMANTICS")
        node_refs = {x["nodeRef"] for x in self.inventory["semanticPlans"]["nodes"]}
        self.assertTrue(
            all(x["nodeRef"] in node_refs for x in problems if "nodeRef" in x))

    def test_recursive_edges_are_physical_only_and_plan_edges_never_calls(self) -> None:
        output = self.result
        refs = {cell["sourceCellRef"] for cell in output["sourceCells"]}
        parents = {cell["sourceCellRef"]: cell["parentSourceCellRef"]
                   for cell in output["sourceCells"]}
        self.assertEqual(len(output["sourceContainment"]),
                         output["summary"]["hierarchyRelations"])
        for edge in output["sourceContainment"]:
            self.assertIn(edge["child"], refs)
            self.assertIn(edge["parent"], refs)
            self.assertEqual(parents[edge["child"]], edge["parent"])
            self.assertEqual(edge["callStanding"], "NOT_ESTABLISHED")
            self.assertNotEqual(edge["child"], edge["parent"])
        self.assertEqual(len(output["declaredPlanEdgesNotActualCalls"]),
                         output["summary"]["declaredPlanEdges"])
        self.assertTrue(all(e["runtimeCallStanding"] == "NOT_ESTABLISHED"
                            and e["effectStanding"] == "UNKNOWN"
                            for e in output["declaredPlanEdgesNotActualCalls"]))
        self.assertFalse(output["summary"]["crossPlanReuseIsError"])

    def test_missing_local_plan_is_review_not_authority(self) -> None:
        recorded = {
            x["sourceZone"] for x in self.result["problemLegos"]
            if x["kind"] == "LOCAL_PLAN_MAPPING_REVIEW"
        }
        expected = {"ROOT:" + name for name in self.inventory["summary"][
            "registeredRootsWithoutLocalLegoPlan"]}
        self.assertEqual(recorded, expected)
        self.assertIn("installation", self.result["truthBoundary"])
        self.assertTrue(self.result["summary"]["missingInstalledAndDynamicCallClosure"])

    def test_deterministic_and_proposal_is_explicit_not_installed(self) -> None:
        a = self.result
        b = M.derived_problem_legos(self.inventory, repo=ROOT)
        self.assertEqual(a, b)
        with self.assertRaisesRegex(ValueError, "exact"):
            M.classification(ROOT, "HEAD")
        with self.assertRaisesRegex(ValueError, "proposal"):
            M.derived_problem_legos(self.inventory, repo=ROOT, use_proposal=True)
        with self.assertRaises(ValueError):
            M.derived_problem_legos(self.inventory, repo=ROOT, max_depth=13)

    def test_cli_summary_has_no_hidden_static_snapshot_or_unproved_edges(self) -> None:
        data = subprocess.check_output([
            "python3", str(ROOT / "tools/repo/exhaustive_coverage.py"),
            "--source-cut", self.sha, "--problem-legos", "--summary",
            "--repo", str(ROOT),
        ], text=True)
        output = __import__("json").loads(data)
        self.assertEqual(output["summary"], self.result["summary"])
        self.assertNotIn("sourceCells", output)
        self.assertNotIn("problemLegos", output)
        self.assertNotIn("sourcePathCellIndex", output)



class ExplicitIndependentScopeTests(unittest.TestCase):
    def test_exact_independent_git_cut_not_mixed_into_subject_repo(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp).resolve() / "secondary"
            root.mkdir()
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "src").mkdir()
            (root / "src" / "main.py").write_text("print(123)\n")
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run([
                "git", "-C", str(root), "-c", "user.name=Phase1",
                "-c", "user.email=phase1@example.invalid",
                "commit", "-qm", "fixture",
            ], check=True)
            other_cut = subprocess.check_output(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                text=True,
            ).strip()
            primary_cut = subprocess.check_output(
                ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                text=True,
            ).strip()
            out = M.independent_scope_frontier(
                ROOT, primary_cut,
                external_git=[f"research-example={root}@{other_cut}"],
                non_git_data=[],
            )
            self.assertEqual(out["sourceCut"], primary_cut)
            self.assertEqual(out["summary"]["externalGitTrackedPaths"], 1)
            source = out["observedScopes"][0]
            self.assertEqual(source["sourceCut"], other_cut)
            self.assertEqual(source["sourceTree"],
                             M.git(root, "rev-parse", f"{other_cut}^{{tree}}").decode().strip())
            self.assertEqual(source["sourceIdentityStanding"], "EXACT_GIT_TREE_ONLY")
            self.assertEqual(source["labelStanding"],
                             "CALLER_SCOPED_ALIAS_NOT_GLOBAL_IDENTITY")
            self.assertEqual(source["ordivonAffiliationStanding"], "UNKNOWN")
            self.assertEqual(out["summary"]["crossScopeCallsVerified"], 0)
            self.assertEqual(out["summary"]["installedSourcesBoundToGit"], 0)
            self.assertEqual(out["pendingScopeProblems"][0]["consumerStanding"], "UNKNOWN")
            self.assertEqual(out["pendingScopeProblems"][0]["runtimeCallStanding"], "NOT_ESTABLISHED")
            self.assertFalse(out["proofReuseAdmissible"])
            # A different Git cut is NOT accepted as the claimed independent identity.
            with self.assertRaises(ValueError):
                M.independent_scope_frontier(
                    ROOT, primary_cut,
                    external_git=[f"research-example={root}@HEAD"], non_git_data=[],
                )
            with self.assertRaises(ValueError):
                M.independent_scope_frontier(
                    ROOT, primary_cut,
                    external_git=[f"research-example={root / 'src'}@{other_cut}"],
                    non_git_data=[],
                )
            with self.assertRaises(ValueError):
                M.independent_scope_frontier(
                    ROOT, primary_cut,
                    external_git=[f"research-example={root}@{other_cut}"],
                    non_git_data=[f"research-example={pathlib.Path(tmp)}"],
                )

    def test_non_git_directory_never_gets_fake_content_digest(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp).resolve() / "corpora"
            root.mkdir()
            (root / "dataset").mkdir()
            (root / "manifest.txt").write_text("data")
            primary = subprocess.check_output(
                ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                text=True,
            ).strip()
            args = dict(external_git=[], non_git_data=[f"paper-corpora={root}"])
            out = M.independent_scope_frontier(ROOT, primary, **args)
            self.assertEqual(out["summary"]["nonGitDirectoryLocators"], 1)
            obj = out["observedScopes"][0]
            self.assertEqual(obj["directChildEntries"], 2)
            self.assertEqual(obj["directChildKinds"], {"directory": 1, "file": 1})
            self.assertEqual(obj["sourceIdentityStanding"], "UNBOUND_NON_GIT_BYTES")
            self.assertEqual(obj["contentDigestStanding"], "NOT_COMPUTED")
            self.assertNotIn("sourceCut", obj)
            self.assertNotIn("sourceTree", obj)
            self.assertEqual(out["pendingScopeProblems"][0]["kind"],
                             "NON_GIT_DATA_IDENTITY_REVIEW")
            with self.assertRaises(ValueError):
                M.independent_scope_frontier(ROOT, primary, max_entries=1, **args)
            symlink = pathlib.Path(tmp) / "alias"
            symlink.symlink_to(root, target_is_directory=True)
            with self.assertRaises(ValueError):
                M.independent_scope_frontier(
                    ROOT, primary, external_git=[],
                    non_git_data=[f"alias={symlink}"])

    def test_missing_explicit_namespace_and_invalid_mode_fail_closed(self) -> None:
        sha = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True,
        ).strip()
        for gis, datasets in (
            ([], []),
            (["missing"], []),
            ([], ["noncanonical=relative/path"]),
            ([], ["NOT_CANONICAL=/tmp"]),
        ):
            with self.assertRaises(ValueError):
                M.independent_scope_frontier(
                    ROOT, sha, external_git=gis, non_git_data=datasets,
                )
        p = subprocess.run([
            "python3", str(ROOT / "tools/repo/exhaustive_coverage.py"),
            "--source-cut", sha, "--external-git-cut", "fake=/tmp@HEAD",
            "--repo", str(ROOT),
        ], capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("require --scope-census", p.stderr)


    def test_scope_census_cli_explicit_git_and_non_git_without_new_registry(self) -> None:
        import tempfile
        import json
        with tempfile.TemporaryDirectory() as tmp:
            folder = pathlib.Path(tmp).resolve() / "dataset"
            folder.mkdir()
            commit = subprocess.check_output(
                ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True,
            ).strip()
            out = subprocess.check_output([
                "python3", str(ROOT / "tools/repo/exhaustive_coverage.py"),
                "--source-cut", commit, "--repo", str(ROOT),
                "--scope-census", "--non-git-root", f"test-corpus={folder}",
            ], text=True)
            v = json.loads(out)
            self.assertEqual(v["summary"]["crossPlaneProblemRecords"], 1)
            self.assertEqual(v["summary"]["externalGitRoots"], 0)
            self.assertEqual(v["summary"]["installedSourcesBoundToGit"], 0)
            self.assertEqual(v["observedScopes"][0]["contentDigestStanding"],
                             "NOT_COMPUTED")
            self.assertFalse(v["proofReuseAdmissible"])
            self.assertNotIn("semanticPlans", v)
            self.assertNotIn("sourceCells", v)

class ExternalAuthorityObservationJoinTests(unittest.TestCase):
    """Cross-authority *candidate* links must not invent call or installed proof."""

    @classmethod
    def setUpClass(cls):
        cls.cut = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
        ).strip()
        cls.frontier = M.derived_problem_legos(M.classification(ROOT, cls.cut), repo=ROOT)
        cls.sample_problem = cls.frontier["problemLegos"][0]["problemRef"]

    @classmethod
    def observation(cls, **updates):
        record = {
            "authorityRef": "git:root-abcd1234",
            "subjectRef": "independent-repo",
            "observationKind": "INDEPENDENT_GIT_SOURCE",
            "observationRevision": "a" * 40,
            "witnessRef": "job-12345678",
            "observedAt": "2026-10-28T06:48:00Z",
            "candidateProblemRef": cls.sample_problem,
            "observedFacts": {"trackedPaths": 200, "crossRepoLexicalCandidates": 3},
        }
        record.update(updates)
        return record

    @classmethod
    def envelope(cls, observations, **updates):
        blob = {
            "kind": "ordivon.external-authority-observations-r1",
            "subjectSourceCut": cls.cut,
            "observations": observations,
        }
        blob.update(updates)
        return blob

    def test_source_problem_and_external_identity_join_is_nonauthoritative(self):
        base = self.frontier
        before = dict(base)
        joined = M.join_observed_authorities(
            base, self.envelope([self.observation()])
        )
        assert joined["observationJoin"]["summary"]["reportedObservationSubjects"] == 1
        assert joined["observationJoin"]["summary"]["explicitCandidateAssociations"] == 1
        assert joined["observationJoin"]["proofReuseAdmissible"] is False
        assert joined["observationJoin"]["dynamicConsumerClosureEstablished"] is False
        assert joined["observationJoin"]["deletionAuthorized"] is False
        assert joined["observationJoin"]["observedSubjects"][0]["evidenceStanding"] == (
            "CALLER_REPORTED_NOT_AUTHORITY_REVERIFIED"
        )
        assert joined["observationJoin"]["candidateAssociations"][0]["relation"] == (
            "EXPLICIT_CANDIDATE_ASSOCIATION_NOT_AN_INVOKED_EDGE"
        )
        assert base == before

    def test_other_authority_same_local_subject_cannot_alias(self):
        original = self.observation(candidateProblemRef=None)
        peer = self.observation(
            authorityRef="non-git:root-bb22",
            observationKind="NON_GIT_DATA_INVENTORY",
            observationRevision="inventory-20261028",
            witnessRef="job-87654321",
            candidateProblemRef=None,
        )
        joined = M.join_observed_authorities(
            self.frontier, self.envelope([original, peer])
        )
        refs = [r["subjectRef"] for r in joined["observationJoin"]["observedSubjects"]]
        assert len(set(refs)) == 2
        assert joined["observationJoin"]["summary"]["unassociatedExternalSubjects"] == 2

    def test_source_revision_changes_evidence_not_stable_subject_identity(self):
        first = M.join_observed_authorities(
            self.frontier, self.envelope([self.observation()])
        )["observationJoin"]["observedSubjects"][0]
        second = M.join_observed_authorities(
            self.frontier, self.envelope([self.observation(
                observationRevision="b"*40,
                observedFacts={"trackedPaths": 201, "crossRepoLexicalCandidates": 3},
            )])
        )["observationJoin"]["observedSubjects"][0]
        assert first["subjectRef"] == second["subjectRef"]
        assert first["evidenceDigest"] != second["evidenceDigest"]
        assert second["installedSourceEquivalence"] == "UNKNOWN"

    def test_stale_source_cut_is_refused(self):
        with self.assertRaisesRegex(ValueError, "SourceCut mismatch"):
            M.join_observed_authorities(self.frontier, self.envelope(
                [self.observation()], subjectSourceCut="0"*40
            ))

    def test_short_id_is_never_promoted_to_scoped_plan_reference(self):
        with self.assertRaisesRegex(ValueError, "unscoped or unrecognized"):
            M.join_observed_authorities(self.frontier, self.envelope(
                [self.observation(candidateProblemRef="G01")]
            ))
        short_ids = self.frontier["sameLocalIdAcrossPlansObservation"]
        assert short_ids
        first_id = sorted(short_ids)[0]
        ref = "problem:unscoped-plan-id:" + first_id
        with self.assertRaisesRegex(ValueError, "syntax witness"):
            M.join_observed_authorities(self.frontier, self.envelope([
                self.observation(candidateProblemRef=ref)]))
        valid = M.join_observed_authorities(self.frontier, self.envelope([
            self.observation(observationKind="UNSCOPED_PLAN_LOOKUP_CANDIDATE",
                             candidateProblemRef=ref)]))
        assert not valid["observationJoin"]["unscopedShortIdQuestions"][0][
            "bareIdIsAnActualCollision"]

    def test_duplicate_and_fake_evidence_status_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            M.join_observed_authorities(self.frontier, self.envelope([
                self.observation(), self.observation(observationRevision="b"*40)]))
        with self.assertRaisesRegex(ValueError, "exact scoped"):
            M.join_observed_authorities(self.frontier, self.envelope([
                {**self.observation(), "proofStatus": "PASS"}]))

    def test_bounds_and_invalid_authority_provenance_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "bounded list"):
            M.join_observed_authorities(
                self.frontier, self.envelope([self.observation()] * 513))
        with self.assertRaisesRegex(ValueError, "namespaced"):
            M.join_observed_authorities(self.frontier, self.envelope([
                self.observation(authorityRef="unscoped")]))
        with self.assertRaisesRegex(ValueError, "witness"):
            M.join_observed_authorities(self.frontier, self.envelope([
                self.observation(witnessRef="human-says-green")]))
        with self.assertRaisesRegex(ValueError, "bounded scalar"):
            M.join_observed_authorities(self.frontier, self.envelope([
                self.observation(observedFacts={"secret": {"nested": "not bounded"}})]))

    def test_cli_opt_in_and_summary(self):
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            file = pathlib.Path(td) / "observations.json"
            file.write_text(json.dumps(self.envelope([self.observation()])), encoding="utf-8")
            proc = subprocess.run([
                "python3", str(ROOT/"tools/repo/exhaustive_coverage.py"),
                "--source-cut", self.cut,
                "--problem-legos", "--summary",
                "--authority-observations", str(file),
            ], cwd=ROOT, capture_output=True, text=True, timeout=20)
            assert proc.returncode == 0, proc.stderr
            payload = json.loads(proc.stdout)
            assert payload["observationJoin"]["summary"]["reportedObservationSubjects"] == 1
            assert "observedSubjects" not in payload["observationJoin"]
            invalid = subprocess.run([
                "python3", str(ROOT/"tools/repo/exhaustive_coverage.py"),
                "--source-cut", self.cut,
                "--authority-observations", str(file),
            ], cwd=ROOT, capture_output=True, text=True, timeout=12)
            assert invalid.returncode != 0

    def test_scope_census_and_observations_are_separate_surfaces(self):
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            folder = pathlib.Path(td)
            evidence = folder / "reported.json"
            evidence.write_text(json.dumps(self.envelope([
                self.observation(candidateProblemRef=None)])), encoding="utf-8")
            proc = subprocess.run([
                "python3", str(ROOT / "tools/repo/exhaustive_coverage.py"),
                "--source-cut", self.cut,
                "--scope-census", "--non-git-root", f"test-data={folder}",
                "--authority-observations", str(evidence),
            ], cwd=ROOT, capture_output=True, text=True, timeout=12)
            assert proc.returncode != 0
            assert "scope census is separate" in proc.stderr



class CrossScopeLexicalHintsTests(unittest.TestCase):
    def _git_cut(self, repo: pathlib.Path, name: str, text: str) -> str:
        repo.mkdir()
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        (repo / name).write_text(text)
        subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
        subprocess.run([
            "git", "-C", str(repo),
            "-c", "user.name=Phase1", "-c", "user.email=phase1@example.invalid",
            "commit", "-qm", "fixture",
        ], check=True)
        return subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()

    def test_exact_pinned_git_blob_locator_is_a_hint_not_a_call(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp).resolve()
            target = root / "research"
            main = root / "monorepo"
            data = root / "corpora"
            data.mkdir()
            sub_cut = self._git_cut(target, "info.txt", "not a consumer")
            cut = self._git_cut(
                main, "docs.txt",
                "documentation only: " + str(target) + "\n" +
                "dataset string: " + str(data) + "\n",
            )
            source = M.independent_scope_frontier(
                main, cut, external_git=[f"research={target}@{sub_cut}"],
                non_git_data=[f"corpora={data}"],
            )
            hints = M.cross_scope_exact_locator_hints(main, source)
            self.assertEqual(hints["summary"]["gitRootsScanned"], 2)
            self.assertEqual(hints["summary"]["pairsWithLiteralReferences"], 2)
            self.assertEqual(hints["summary"]["runtimeCallEdgesVerified"], 0)
            self.assertFalse(hints["proofReuseAdmissible"])
            self.assertFalse(hints["summary"]["zeroLexicalHitsProveNoConsumers"])
            self.assertTrue(all(x["runtimeCallStanding"] == "NOT_ESTABLISHED"
                                and x["consumerStanding"] == "UNKNOWN"
                                for x in hints["literalReferencePairsNotCalls"]))
            w = hints["literalReferencePairsNotCalls"][0]["witnesses"][0]
            self.assertEqual(w["readerSourceCut"], cut)
            self.assertEqual(w["readerPath"], "docs.txt")
            self.assertIn("blob:", w["readerSourceIdentity"])
            # The results depend on immutable Git, NOT working tree edits.
            (main / "docs.txt").write_text("changed uncommitted content")
            self.assertEqual(
                hints,
                M.cross_scope_exact_locator_hints(main, source),
            )

    def test_syntax_generated_path_does_not_prove_missing_consumers(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp).resolve()
            target = root / "external"
            main = root / "main"
            sub_cut = self._git_cut(target, "info.txt", "data")
            cut = self._git_cut(
                main, "code.py",
                "import os\npath = os.path.join('/root', 'projects', "
                "'external')\n",
            )
            census = M.independent_scope_frontier(
                main, cut, external_git=[f"external={target}@{sub_cut}"],
                non_git_data=[],
            )
            result = M.cross_scope_exact_locator_hints(main, census)
            self.assertEqual(result["summary"]["pairsWithLiteralReferences"], 0)
            self.assertFalse(result["summary"]["zeroLexicalHitsProveNoConsumers"])
            self.assertEqual(result["summary"]["runtimeCallEdgesVerified"], 0)
            self.assertFalse(result["proofReuseAdmissible"])
            with self.assertRaisesRegex(ValueError, "limit"):
                M.cross_scope_exact_locator_hints(main, census, max_witnesses=0)
            with self.assertRaisesRegex(ValueError, "scope census"):
                M.cross_scope_exact_locator_hints(main, {"kind": "bad"})

    def test_cli_fails_closed_for_cross_mode_and_emits_bounded_summary(self) -> None:
        import tempfile
        import json
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp).resolve()
            data = root / "corpora"
            data.mkdir()
            commit = subprocess.check_output(
                ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                text=True).strip()
            cmd = [
                "python3", str(ROOT / "tools/repo/exhaustive_coverage.py"),
                "--repo", str(ROOT), "--source-cut", commit,
                "--scope-census", "--scope-locator-hints", "--summary",
                "--non-git-root", f"corpora={data}",
            ]
            output = json.loads(subprocess.check_output(cmd, text=True))
            self.assertEqual(output["lexicalSourceHints"]["summary"]["gitRootsScanned"], 1)
            self.assertNotIn("literalReferencePairsNotCalls",
                             output["lexicalSourceHints"])
            self.assertEqual(output["summary"]["crossPlaneProblemRecords"], 1)
            p = subprocess.run(cmd + ["--problem-legos"], text=True, capture_output=True)
            self.assertNotEqual(p.returncode, 0)
            self.assertIn("separate", p.stderr)
            p = subprocess.run(cmd + ["--scope-witness-limit", "0"],
                               text=True, capture_output=True)
            self.assertNotEqual(p.returncode, 0)
