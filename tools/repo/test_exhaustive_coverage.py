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


class ProblemLegoDerivedFrontierTests(unittest.TestCase):
    """Problem LEGO candidates are identities for questions, never execution authority."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.cut = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            text=True,
        ).strip()
        cls.inventory = M.classification(ROOT, cls.cut)
        cls.cells = M.active_source_cells(
            cls.inventory, repo=ROOT, include_member_index=True,
        )
        cls.frontier = M.derive_problem_legos(cls.inventory, repo=ROOT)

    def test_no_problem_lost_or_duplicated_or_solved(self):
        f = self.frontier
        cells = self.cells
        assert f["sourceCut"] == self.cut
        assert f["sourceTree"] == self.inventory["sourceTree"]
        assert f["proofReuseAdmissible"] is False
        assert f["summary"]["trackedSourcePaths"] == self.inventory["summary"]["trackedPaths"]
        assert f["summary"]["recursiveSourceCells"] == cells["summary"]["cells"]
        assert f["summary"]["problemBearingCells"] == cells["summary"]["problemCells"]
        assert f["summary"]["problemCounts"] == cells["summary"]["problemCounts"]
        assert f["summary"]["problemLegos"] == sum(
            len(c["problems"]) for c in cells["cells"]
        )
        assert len(f["problemLegos"]) == len({p["problemRef"] for p in f["problemLegos"]})
        for p in f["problemLegos"]:
            assert p["kind"] == "ordivon.phase1.pending-source-problem-lego"
            assert p["standing"] == "PROBLEM_DISCOVERED_NOT_YET_RESOLVED"
            assert p["consumerStanding"] == p["formalStanding"] == p["installedStanding"] == "UNKNOWN"
            assert p["invocationStanding"] == "NOT_MAPPED"
            assert p["replaceOrDeleteStanding"] == "NOT_QUALIFIED"

    def test_source_atoms_are_exact_git_and_density_is_flat_not_fake_semantics(self):
        actual = {i["path"]: i["sourceIdentity"] for i in self.inventory["sourcePaths"]}
        by_cell = {x["memberGitObjectDigest"]: x for x in self.cells["cells"]}
        dense_members = []
        for p in self.frontier["problemLegos"]:
            c = by_cell[p["sourceCellDigest"]]
            assert p["issue"] in c["problems"]
            assert len(p["sourceAtoms"]) == p["sourcePathCount"] == c["pathCount"]
            for a in p["sourceAtoms"]:
                assert actual[a["sourcePath"]] == a["sourceIdentity"]
                assert self.cells["memberCellDigests"][a["sourcePath"]] == p["sourceCellDigest"]
                assert a["proposedClassification"] is None
            if p["issue"] == "DENSE_CELL_REQUIRES_SUBCLASSIFICATION_REVIEW":
                assert p["densityCause"] in (
                    "FLAT_DIRECTORY_ATOMIC_SOURCE_FILES",
                    "RECURSIVE_DEPTH_CAP_REACHED",
                    "MIXED_DIRECT_AND_NESTED_PATHS_REQUIRE_RECHECK",
                )
                dense_members += [a["sourcePath"] for a in p["sourceAtoms"]]
        assert len(dense_members) == len(set(dense_members))
        assert len(dense_members) == self.frontier["summary"]["denseSourceAtomIncidences"]

    def test_plan_issue_references_only_actual_problematic_declarations(self):
        expected = {
            n["nodeRef"]: n["problems"]
            for n in self.inventory["semanticPlans"]["nodes"]
            if n["problems"]
        }
        got = {}
        obligations = {}
        for p in self.frontier["problemLegos"]:
            if p["issue"] == "PLAN_DECLARATION_GAPS_REQUIRE_SEMANTIC_MAPPING":
                got.update(p["planNodeDeclaredProblems"])
                assert set(p["planNodeRefs"]) == set(p["planNodeDeclaredProblems"])
                for ref in p["planNodeRefs"]:
                    assert "#" in ref and ref in expected
                    assert any(a["sourcePath"] == ref.split("#", 1)[0]
                               for a in p["sourceAtoms"])
                for row in p["planProblemObligations"]:
                    assert row["planNodeRef"] in p["planNodeRefs"]
                    assert row["missingDeclaration"] in expected[row["planNodeRef"]]
                    assert row["planSourceIdentity"] in {
                        a["sourceIdentity"] for a in p["sourceAtoms"]
                        if a["sourcePath"] == row["planNodeRef"].split("#", 1)[0]
                    }
                    assert row["standing"] == "DECLARATION_GAP_NOT_BEHAVIORAL_ABSENCE"
                    assert row["consumerAndInvocationStanding"] == "UNKNOWN"
                    assert row["obligationRef"] not in obligations
                    obligations[row["obligationRef"]] = row
            else:
                assert not p["planNodeRefs"]
                assert not p["planNodeDeclaredProblems"]
                assert not p["planProblemObligations"]
        assert got == expected
        assert len(obligations) == sum(len(v) for v in expected.values())
        assert len(obligations) == self.frontier["summary"]["planGapAtomicObligations"]
        assert self.frontier["summary"]["planGapNodes"] == len(expected)

    def test_repeatable_no_mutation_without_leaking_runtime_trust(self):
        again = M.derive_problem_legos(self.inventory, repo=ROOT)
        assert again == self.frontier
        assert "decisionsDeferred" in again
        assert "CONSUMER_AND_INVOCATION_GRAPH" in again["decisionsDeferred"]
        assert all("consumerEvidence" not in x for x in again["problemLegos"])
        assert all("invocation" not in x for x in again["problemLegos"])

    def test_tampered_git_blob_identity_rejected(self):
        import copy
        corrupted = copy.deepcopy(self.inventory)
        corrupted["sourcePaths"][0]["sourceIdentity"] = "100644:blob:" + "0" * 40
        with self.assertRaisesRegex(ValueError, "differ from exact Git"):
            M.derive_problem_legos(corrupted, repo=ROOT)

    def test_proposal_needs_explicit_exact_source_and_may_not_grant_proof(self):
        with self.assertRaisesRegex(ValueError, "proposal"):
            M.derive_problem_legos(self.inventory, repo=ROOT, use_proposal=True)

    def test_invalid_limits_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "cell limits"):
            M.derive_problem_legos(self.inventory, repo=ROOT, max_files=0)


class CrossPlaneObservationJoinTests(unittest.TestCase):
    """Cross-plane facts are operator observations, not consumer attestations."""

    @classmethod
    def setUpClass(cls):
        import subprocess
        cls.sha = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
        cls.problems = M.derive_problem_legos(M.classification(ROOT, cls.sha), repo=ROOT)

    def source(self):
        return {
            "schemaVersion": 1,
            "kind": "ordivon.phase1.cross-plane-observation-input",
            "subjectSourceCut": self.sha,
            "observations": [
                {"plane":"GIT_SOURCE_VIEW","hostScope":"linux","locator":"git:research_v2",
                 "versionIdentity":"a"*40+":"+"b"*40, "gitObjectStoreGroup":"gitgroup:research",
                 "witnessRef":"job:test-git-cut"},
                {"plane":"GIT_SOURCE_VIEW","hostScope":"linux","locator":"git:paper1_frozen",
                 "versionIdentity":"c"*40+":"+"d"*40, "gitObjectStoreGroup":"gitgroup:research",
                 "witnessRef":"job:test-worktree-common"},
                {"plane":"NON_GIT_NAMESPACE","hostScope":"linux","locator":"data:corpora",
                 "observedState":"DIRECTORY_OBSERVED","witnessRef":"job:test-data-root"},
                {"plane":"SERVICE_STATUS","hostScope":"windows",
                 "locator":"scm:OrdivonRuntimeR6Candidate","observedState":"RUNNING",
                 "pid":7240, "witnessRef":"job:test-cim"},
                {"plane":"PROCESS_PID","hostScope":"windows","locator":"pid:7240",
                 "serviceLocator":"scm:OrdivonRuntimeR6Candidate",
                 "observedState":"RUNNING","pid":7240,"witnessRef":"job:test-process"},
            ],
            "candidateRelations": [
                {"source":"linux:GIT_SOURCE_VIEW:git:research_v2",
                 "target":"linux:GIT_SOURCE_VIEW:git:paper1_frozen",
                 "relationKind":"SHARED_GIT_OBJECT_STORE_OBSERVED","witnessRef":"job:test-common"},
                {"source":"linux:GIT_SOURCE_VIEW:git:research_v2",
                 "target":"linux:NON_GIT_NAMESPACE:data:corpora",
                 "relationKind":"SOURCE_TEXT_EXTERNAL_PATH_REFERENCE_CANDIDATE",
                 "witnessRef":"git:corpus_manifest_source"},
                {"source":"windows:SERVICE_STATUS:scm:OrdivonRuntimeR6Candidate",
                 "target":"windows:PROCESS_PID:pid:7240",
                 "relationKind":"SERVICE_PID_ASSOCIATION_OBSERVED",
                 "witnessRef":"job:test-cim"},
            ],
        }

    def test_preserves_source_problem_namespace_without_promotion(self):
        inp=self.source()
        g=M.join_cross_plane_observations(self.problems,inp)
        self.assertEqual(g["sourceCut"],self.sha)
        self.assertEqual(g["problemSources"]["gitRecursive"],
                         self.problems["summary"]["problemLegos"])
        self.assertEqual(g["observationCount"],5)
        self.assertEqual(g["candidateRelationCount"],3)
        self.assertEqual(g["problemSources"]["crossPlaneObserved"],5)
        self.assertFalse(g["proofReuseAdmissible"])
        self.assertEqual(len({x["problemRef"] for x in g["problems"]}),5)
        for node in g["observations"]:
            self.assertEqual(node["semanticConsumerStanding"],"UNKNOWN")
            self.assertEqual(node["loadedImplementationStanding"],"UNKNOWN")
            self.assertEqual(node["proofStanding"],
                             "OBSERVATION_INPUT_NOT_INDEPENDENTLY_ATTESTED")
        for p in g["problems"]:
            self.assertEqual(p["invocationStanding"],"NOT_MAPPED")
            self.assertEqual(p["deleteOrReplaceStanding"],"NOT_QUALIFIED")
        for edge in g["candidateRelations"]:
            self.assertEqual(edge["consumerAndCallSemantics"],"UNKNOWN")
            self.assertEqual(edge["formalProofStanding"],"UNKNOWN")

    def test_stable_identity_across_service_state_changes(self):
        import copy
        a=self.source()
        b=copy.deepcopy(a)
        b["observations"][3]["observedState"]="STOPPED"
        b["observations"][3]["pid"]=None
        b["observations"][4]["observedState"]="STOPPED"
        b["candidateRelations"].pop()
        before=M.join_cross_plane_observations(self.problems,a)
        after=M.join_cross_plane_observations(self.problems,b)
        self.assertEqual(
            {x["observationRef"] for x in before["observations"]},
            {x["observationRef"] for x in after["observations"]})
        self.assertEqual(
            {x["problemRef"] for x in before["problems"]},
            {x["problemRef"] for x in after["problems"]})

    def test_no_fake_consumer_invocation_edge(self):
        x=self.source()
        x["candidateRelations"][2]["relationKind"]="CALLS"
        with self.assertRaisesRegex(ValueError,"unknown node or asserted"):
            M.join_cross_plane_observations(self.problems,x)

    def test_pid_mismatch_rejected(self):
        x=self.source()
        x["observations"][4]["pid"]=7284
        with self.assertRaisesRegex(ValueError,"association"):
            M.join_cross_plane_observations(self.problems,x)

    def test_self_claimed_proof_or_sensitive_fields_rejected(self):
        x=self.source()
        x["observations"][0]["proof"]="TRUSTED"
        with self.assertRaisesRegex(ValueError,"unsupported or sensitive"):
            M.join_cross_plane_observations(self.problems,x)

    def test_unknown_git_identity_and_duplicate_locator_rejected(self):
        import copy
        x=self.source()
        x["observations"][0]["versionIdentity"]="untracked"
        with self.assertRaisesRegex(ValueError,"exact commit"):
            M.join_cross_plane_observations(self.problems,x)
        y=self.source()
        y["observations"].append(copy.deepcopy(y["observations"][0]))
        with self.assertRaisesRegex(ValueError,"duplicate"):
            M.join_cross_plane_observations(self.problems,y)

    def test_crossplane_input_must_bind_exact_sourcecut(self):
        x=self.source()
        x["subjectSourceCut"]="0"*40
        with self.assertRaisesRegex(ValueError,"SourceCut mismatch"):
            M.join_cross_plane_observations(self.problems,x)

    def test_wrong_edge_type_rejected_without_claiming_consumption(self):
        x=self.source()
        x["candidateRelations"][1]["target"]="windows:PROCESS_PID:pid:7240"
        with self.assertRaisesRegex(ValueError,"lexical path hint"):
            M.join_cross_plane_observations(self.problems,x)


    def test_cli_crossplane_summary_no_semantic_promotion(self):
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            obs = pathlib.Path(tmp) / "observations.json"
            obs.write_text(json.dumps(self.source()))
            result = subprocess.run([
                "python3", str(ROOT / "tools/repo/exhaustive_coverage.py"),
                "--source-cut", self.sha, "--problem-legos",
                "--cross-plane-observations", str(obs), "--summary",
            ], cwd=ROOT, capture_output=True, text=True, check=True, timeout=30)
            output = json.loads(result.stdout)
            assert output["crossPlane"]["observationCount"] == 5
            assert output["crossPlane"]["candidateRelationCount"] == 3
            assert output["crossPlane"]["proofReuseAdmissible"] is False
            assert "observations" not in output["crossPlane"]
            assert "problemLegos" not in output
