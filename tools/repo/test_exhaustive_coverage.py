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
    def test_native_git_inventory_obeys_explicit_repo_under_foreign_git_env(self):
        # The actual convergence_plan consumer calls these source-projection
        # functions against an explicit repo. Inherited GIT_DIR or object-store
        # overrides must not substitute an unrelated repo for the source-cut.
        import os
        import tempfile
        from unittest.mock import patch

        with tempfile.TemporaryDirectory(prefix="ordivon-source-inventory-git-env-") as tmp:
            actual = pathlib.Path(tmp) / "actual"
            foreign = pathlib.Path(tmp) / "foreign"
            for repo in (actual, foreign):
                repo.mkdir()
                for args in (
                    ("init", "-q"),
                    ("config", "user.name", "Git census CDC"),
                    ("config", "user.email", "git-census@example.invalid"),
                ):
                    subprocess.run(["git", "-C", str(repo), *args], check=True)
                (repo / "common.txt").write_text(repo.name + "\n")
                if repo == actual:
                    (repo / "provider.py").write_text("VALUE = 1\n")
                    (repo / "consumer.py").write_text("import provider\n")
                subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
                subprocess.run(["git", "-C", str(repo), "commit", "-qm", "init"], check=True)

            expected_oid = subprocess.check_output(
                ["git", "-C", str(actual), "rev-parse", "HEAD"], text=True,
            ).strip()
            expected_tree = M.tree(actual, expected_oid)
            self.assertEqual(
                [x["path"] for x in expected_tree],
                ["common.txt", "consumer.py", "provider.py"],
            )
            expected_imports = M.static_python_import_frontier(actual, expected_oid)
            # Both tracked Python blobs are passed through native cat-file
            # even if top-level imports are unqualified static edges.
            self.assertEqual(expected_imports["summary"]["gitPythonPaths"], 2)
            for injected in (
                {"GIT_DIR": str(foreign / ".git")},
                {"GIT_OBJECT_DIRECTORY": str(foreign / ".git" / "objects")},
                {"GIT_ALTERNATE_OBJECT_DIRECTORIES": str(foreign / ".git" / "objects")},
            ):
                with self.subTest(injected=tuple(injected)):
                    with patch.dict(os.environ, injected):
                        self.assertEqual(
                            M.git(actual, "rev-parse", "HEAD").decode().strip(),
                            expected_oid,
                        )
                        self.assertEqual(M.exact_commit(actual, expected_oid), expected_oid)
                        self.assertEqual(M.tree(actual, expected_oid), expected_tree)
                        # This consumer uses direct Git cat-file --batch too;
                        # the helper alone must not hide an unguarded Git path.
                        self.assertEqual(
                            M.static_python_import_frontier(actual, expected_oid),
                            expected_imports,
                        )

    def test_root_only_is_not_evidence_of_semantic_qualification(self):
        now = M.source_partition("services/runtime/src/main.rs", {
            "owners": [{"name": "runtime", "root": "services/runtime/"}]})
        self.assertEqual(now["standing"], "CLASSIFIED")
        self.assertEqual(now["classification"], "ROOT:runtime")

    def test_formal_source_region_has_real_task_but_no_owner_authority(self):
        # The existing root formal:verify task consumes tools/formal, yet this
        # path was mechanically unclassified. The region is navigation only.
        import tomllib
        policy = tomllib.loads(
            (ROOT / "tools/repo/owners.toml").read_text(encoding="utf-8"))
        classified = M.source_partition("tools/formal/verify.py", policy)
        self.assertEqual(classified["classification"],
                         "REGION:formal-verification-source")
        self.assertEqual(classified["standing"], "CLASSIFIED")
        self.assertTrue(
            all(not o["root"].startswith("tools/formal/")
                for o in policy["owners"]))
        root_tasks = tomllib.loads((ROOT / "mise.toml").read_text())["tasks"]
        formal_tasks = tomllib.loads(
            (ROOT / "tools/formal/mise.toml").read_text())["tasks"]
        self.assertEqual(root_tasks["formal:verify"]["run"],
                         "cd tools/formal && mise run verify")
        # Accept an isolated KANI_HOME shell prologue (Formal toolchain PR)
        # without confusing source task routing with an exact shell string.
        verify_run = formal_tasks["verify"]["run"]
        executable_lines = [
            line.strip() for line in verify_run.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertTrue(executable_lines)
        self.assertEqual(executable_lines[-1], "python3 verify.py")
        self.assertEqual(executable_lines.count("python3 verify.py"), 1)
        self.assertEqual(M.source_partition("tools/unknown_script.py", policy)
                         ["standing"], "UNASSIGNED")

    def test_repository_mechanics_source_region_has_real_cli_consumers(self):
        import tomllib
        policy = tomllib.loads(
            (ROOT / "tools/repo/owners.toml").read_text(encoding="utf-8"))
        assert M.source_partition(
            "tools/repo/exhaustive_coverage.py", policy)["classification"] == (
                "REGION:repository-mechanics-source")
        assert M.source_partition(
            "tools/repo/migration/test-integrate-main.sh", policy)["classification"] == (
                "REGION:repository-mechanics-source")
        assert not any(o["root"].startswith("tools/repo/")
                       for o in policy["owners"])
        tasks = tomllib.loads((ROOT / "mise.toml").read_text())["tasks"]
        ci = tasks["repo:ci"]["run"]
        assert "tools/repo/test_affected_owners.py" in ci
        assert "tools/repo/migration/test-integrate-main.sh" in ci
        assert "tools/repo/check_owner_boundaries.py" in ci
        assert M.source_partition("tools/nonexistent.py", policy)["standing"] == (
            "UNASSIGNED")

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
            "catalogs/authorities/records/iso/",
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
                            "capabilities/artifact/artifact-delivery/shadow-v2/examples/audio-flac-pcm16-r1-v2.json"
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

    def test_each_declared_gap_has_one_typed_problem_question(self) -> None:
        rows = self.result["declarationFieldQuestions"]
        expected = {(node["nodeRef"], tag) for node in self.inventory["semanticPlans"]["nodes"]
                    for tag in node["problems"]}
        actual = {(q["nodeRef"], q["missingDeclarationTag"]) for q in rows}
        self.assertEqual(actual, expected)
        self.assertEqual(len(rows), len(expected))
        self.assertEqual(len(rows), self.result["summary"]["declarationFieldQuestions"])
        parents = {q["problemRef"] for q in self.result["problemLegos"]}
        self.assertTrue(all(q["parentProblemRef"] in parents for q in rows))
        self.assertTrue(all(q["relation"] == "DECLARED_FIELD_NOT_FOUND_NOT_RUNTIME_ABSENCE"
                            for q in rows))
        self.assertTrue(all(q["actualConsumerStanding"] == "UNKNOWN" for q in rows))

    def test_structure_mapping_review_covers_every_declared_unrealized_path(self) -> None:
        rows = self.result["mappingDeclarationReviews"]
        self.assertEqual(len(rows), self.result["summary"]["mappingDeclarationReviews"])
        self.assertEqual(len({r["reviewRef"] for r in rows}), len(rows))
        counts = __import__("collections").Counter()
        for item in rows:
            counts[item["problemTag"]] += item["matchedPathCount"]
            self.assertTrue(item["sourceMembersDigest"].startswith("sha256:"))
            self.assertTrue(item["sourceCellRefs"])
            self.assertEqual(item["consumerStanding"], "UNKNOWN")
            self.assertEqual(item["installedStanding"], "UNKNOWN")
            self.assertEqual(item["relation"],
                             "STRUCTURE_DECLARATION_TO_SOURCE_NOT_REALIZED_MOVE")
        expected = self.inventory["summary"]["sourceProblemCounts"]
        self.assertEqual(counts["DECLARED_MOVE_CONSUMER_QUALIFICATION_REQUIRED"],
                         expected["PHYSICAL_MOVE_NOT_REALIZED_OR_CONSUMER_NOT_CUT_OVER"])
        self.assertEqual(counts["DECLARED_SPLIT_CONSUMER_QUALIFICATION_REQUIRED"],
                         expected["STRUCTURE_SPLIT_REQUIRES_CONSUMER_WITNESS"])

    def test_cross_plan_repeated_short_ids_are_not_identified_as_same_lego(self) -> None:
        rows = self.result["crossPlanIdentityScopeReviews"]
        src = self.inventory["semanticPlans"]["sameLocalIdAcrossPlans"]
        self.assertEqual({q["localId"] for q in rows}, set(src))
        self.assertEqual(len(rows), self.result["summary"]["crossPlanIdentityScopeReviews"])
        self.assertEqual(len({q["reviewRef"] for q in rows}), len(rows))
        for row in rows:
            self.assertEqual(row["scopedNodeRefs"], src[row["localId"]])
            self.assertEqual(row["collisionStanding"],
                             "REVIEW_REQUIRED_NOT_PROVEN_CONFLICT")

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

    def test_recursive_view_identity_includes_decomposition_policy(self) -> None:
        # Same exact Git source objects can be grouped differently without
        # introducing a new semantic LEGO, owner or verified consumer.
        current = self.result
        finer = M.derived_problem_legos(
            self.inventory, repo=ROOT, max_files=18, max_depth=6)
        assert current["sourceCut"] == finer["sourceCut"]
        assert current["sourceTree"] == finer["sourceTree"]
        assert current["sourcePathDigest"] == finer["sourcePathDigest"]
        assert current["sourceCellDecomposition"] == {
            "maxCellFiles": 24,
            "maxCellDepth": 6,
            "identityStanding": "VIEW_PARAMETERS_NOT_SEMANTIC_LEGO_IDENTITY"}
        assert finer["sourceCellDecomposition"]["maxCellFiles"] == 18
        assert finer["sourceCellDecomposition"]["maxCellDepth"] == 6
        assert set(current["sourcePathCellIndex"]) == set(
            finer["sourcePathCellIndex"])
        assert not current["proofReuseAdmissible"]
        assert not finer["proofReuseAdmissible"]

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
        self.assertNotIn("declarationFieldQuestions", output)
        self.assertNotIn("mappingDeclarationReviews", output)
        self.assertNotIn("crossPlanIdentityScopeReviews", output)



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


    def test_self_and_linked_worktree_never_count_as_independent_git(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            subject = pathlib.Path(tmp).resolve() / "subject"
            subject.mkdir()
            subprocess.run(["git", "init", "-q", str(subject)], check=True)
            (subject / "unit.py").write_text("stable = True\n")
            subprocess.run(["git", "-C", str(subject), "add", "unit.py"], check=True)
            subprocess.run([
                "git", "-C", str(subject), "-c", "user.name=Phase1",
                "-c", "user.email=phase1@example.invalid",
                "commit", "-qm", "fixture",
            ], check=True)
            sha = subprocess.check_output(
                ["git", "-C", str(subject), "rev-parse", "HEAD"], text=True,
            ).strip()
            linked = pathlib.Path(tmp).resolve() / "linked"
            subprocess.run(["git", "-C", str(subject), "worktree",
                            "add", "--detach", "-q", str(linked), sha], check=True)
            for other in (subject, linked):
                with self.subTest(other=other), self.assertRaisesRegex(
                        ValueError, "not independent|same Git repository"):
                    M.independent_scope_frontier(
                        subject, sha, external_git=[f"false-external={other}@{sha}"],
                        non_git_data=[],
                    )

    def test_duplicate_git_repository_and_data_locator_do_not_double_count(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            subject = pathlib.Path(tmp).resolve() / "subject"
            external = pathlib.Path(tmp).resolve() / "external"
            corpus = pathlib.Path(tmp).resolve() / "corpus"
            for root in (subject, external):
                root.mkdir()
                subprocess.run(["git", "init", "-q", str(root)], check=True)
                (root / "a.txt").write_text("content")
                subprocess.run(["git", "-C", str(root), "add", "."], check=True)
                subprocess.run([
                    "git", "-C", str(root), "-c", "user.name=Phase1",
                    "-c", "user.email=phase1@example.invalid",
                    "commit", "-qm", "fixture",
                ], check=True)
            corpus.mkdir()
            subject_cut = subprocess.check_output([
                "git", "-C", str(subject), "rev-parse", "HEAD",
            ], text=True).strip()
            other_cut = subprocess.check_output([
                "git", "-C", str(external), "rev-parse", "HEAD",
            ], text=True).strip()
            valid = M.independent_scope_frontier(
                subject, subject_cut,
                external_git=[f"other={external}@{other_cut}"],
                non_git_data=[f"data={corpus}"],
            )
            self.assertEqual(valid["summary"]["externalGitRoots"], 1)
            self.assertEqual(valid["summary"]["nonGitDirectoryLocators"], 1)
            with self.assertRaisesRegex(ValueError, "duplicate|same Git repository"):
                M.independent_scope_frontier(
                    subject, subject_cut,
                    external_git=[
                        f"first={external}@{other_cut}",
                        f"second={external}@{other_cut}",
                    ],
                    non_git_data=[],
                )
            with self.assertRaisesRegex(ValueError, "duplicate|same directory"):
                M.independent_scope_frontier(
                    subject, subject_cut, external_git=[],
                    non_git_data=[f"first={corpus}", f"second={corpus}"],
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

    def test_opt_in_checkout_observations_distinguish_commit_index_worktrees(self) -> None:
        import tempfile
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp).resolve() / "independent"
            root.mkdir()
            def run(*args):
                return subprocess.check_output(
                    ["git", "-C", str(root), *args], text=True,
                    stderr=subprocess.DEVNULL).strip()
            run("init", "-q")
            run("config", "user.name", "Fixture")
            run("config", "user.email", "fixture@example.test")
            (root / "source.py").write_text("x = 1\n")
            run("add", "source.py")
            run("commit", "-qm", "source")
            pinned = run("rev-parse", "HEAD")
            orphan = pathlib.Path(tmp).resolve() / "missing-after-worktree"
            run("worktree", "add", "-q", "-b", "fixture-other", str(orphan), pinned)
            shutil.rmtree(orphan)
            # Index is not the Git commit tree. It can be zero even while the
            # pinned commit contains a real source blob; never classify empty.
            run("rm", "--cached", "-q", "source.py")
            main_cut = subprocess.check_output(
                ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
            args = dict(external_git=[f"fixture={root}@{pinned}"], non_git_data=[])
            default = M.independent_scope_frontier(ROOT, main_cut, **args)
            self.assertNotIn("checkoutObservation", default["observedScopes"][0])
            observed = M.independent_scope_frontier(
                ROOT, main_cut, git_checkout_observations=True, **args)
            scope = observed["observedScopes"][0]
            state = scope["checkoutObservation"]
            self.assertEqual(scope["trackedPaths"], 1)
            self.assertEqual(state["pinnedCommitTreePaths"], 1)
            self.assertEqual(state["indexTrackedPaths"], 0)
            self.assertEqual(state["indexToCommitCountStanding"],
                             "COUNT_MISMATCH_NO_SEMANTIC_CONCLUSION")
            self.assertEqual(state["checkedOutHead"], pinned)
            self.assertTrue(state["checkedOutHeadMatchesSourceCut"])
            self.assertEqual(state["prunableWorktreeRecords"], 1)
            self.assertEqual(state["prunableLocationMissingCount"], 1)
            self.assertEqual(state["safeCleanupStanding"], "NOT_ESTABLISHED")
            kinds = {x["kind"] for x in observed["pendingScopeProblems"]}
            self.assertIn("INDEX_AND_COMMIT_TREE_COUNTS_DIFFER", kinds)
            self.assertIn("PRUNABLE_WORKTREE_METADATA_REQUIRES_CONSUMER_REVIEW", kinds)
            self.assertTrue(all(x["consumerStanding"] == "UNKNOWN"
                                for x in observed["pendingScopeProblems"]))
            self.assertEqual(observed["summary"]["installedSourcesBoundToGit"], 0)
            self.assertEqual(observed["summary"]["crossScopeCallsVerified"], 0)

    def test_checkout_observation_cli_requires_explicit_scope_mode(self) -> None:
        cut = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
        cmd = ["python3", str(ROOT / "tools/repo/exhaustive_coverage.py"),
               "--source-cut", cut, "--repo", str(ROOT), "--scope-git-worktrees"]
        bad = subprocess.run(cmd, capture_output=True, text=True)
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("require --scope-census", bad.stderr)

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

    def test_distinct_temporal_observations_preserve_identity_and_provenance(self):
        first = self.observation(
            observationRevision="a"*40, observedAt="2026-10-28T06:48:00Z",
            observedFacts={"trackedPaths": 200})
        second = self.observation(
            observationRevision="b"*40, observedAt="2026-10-28T06:49:00Z",
            witnessRef="job-87654321", observedFacts={"trackedPaths": 201})
        joined = M.join_observed_authorities(
            self.frontier, self.envelope([second, first])
        )["observationJoin"]
        reverse = M.join_observed_authorities(
            self.frontier, self.envelope([first, second])
        )["observationJoin"]
        assert joined == reverse
        records = joined["observedSubjects"]
        assert len(records) == 2
        assert len({record["subjectRef"] for record in records}) == 1
        assert len({record["authoritySubjectRef"] for record in records}) == 1
        assert len({record["observationRef"] for record in records}) == 2
        assert joined["summary"]["distinctObservedSubjects"] == 1
        assert joined["summary"]["reportedObservationSubjects"] == 2
        assert len(joined["candidateAssociations"]) == 2
        assert all(record["semanticConsumerStanding"] == "UNKNOWN" for record in records)
        assert not joined["proofReuseAdmissible"]
        assert not joined["deletionAuthorized"]

    def test_two_observation_kinds_keep_authority_subject_alias_without_physical_proof(self):
        first = self.observation(candidateProblemRef=None)
        second = self.observation(
            observationKind="ENVIRONMENT_EFFECT_OBSERVED",
            observationRevision="runtime-v2",
            candidateProblemRef=None,
        )
        joined = M.join_observed_authorities(
            self.frontier, self.envelope([first, second])
        )["observationJoin"]
        records = joined["observedSubjects"]
        assert len({r["subjectRef"] for r in records}) == 2
        assert len({r["authoritySubjectRef"] for r in records}) == 1
        assert all(r["authoritySubjectStanding"] ==
                   "CALLER_SCOPED_ALIAS_NOT_VERIFIED" for r in records)

    def test_duplicate_and_conflicting_observations_are_rejected(self):
        original = self.observation()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            M.join_observed_authorities(
                self.frontier, self.envelope([original, original]))
        with self.assertRaisesRegex(ValueError, "conflicting"):
            M.join_observed_authorities(self.frontier, self.envelope([
                original, self.observation(
                    witnessRef="job-87654321",
                    observedFacts={"trackedPaths": 999}),
            ]))
        with self.assertRaisesRegex(ValueError, "exact scoped"):
            M.join_observed_authorities(self.frontier, self.envelope([
                {**original, "proofStatus": "PASS"}]))

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

    def test_external_observation_rejects_nonfinite_json_numbers(self):
        import math
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=repr(value)):
                with self.assertRaisesRegex(ValueError, "finite bounded scalar"):
                    M.join_observed_authorities(self.frontier, self.envelope([
                        self.observation(observedFacts={"metric": value})
                    ]))
        accepted = M.join_observed_authorities(self.frontier, self.envelope([
            self.observation(observedFacts={"zero": 0, "finite": -1.25,
                                           "flag": False, "empty": None})
        ]))
        # This is genuinely strict JSON (no non-standard NaN/Infinity literals).
        import json
        json.loads(json.dumps(accepted, allow_nan=False),
                   parse_constant=lambda literal: self.fail(literal))

    def test_external_observation_requires_real_canonical_utc_instant(self):
        for instant in (
            "2026-19-39T29:59:59Z",
            "2026-02-29T12:00:00Z",
            "2026-10-28T08:61:00Z",
            "2026-10-28T08:20:60Z",
            "2026-10-28T08:20:00+00:00",
            "2026-10-28T8:20:00Z",
        ):
            with self.subTest(instant=instant):
                with self.assertRaisesRegex(ValueError, "UTC|timestamp"):
                    M.join_observed_authorities(self.frontier, self.envelope([
                        self.observation(observedAt=instant)
                    ]))
        valid = M.join_observed_authorities(self.frontier, self.envelope([
            self.observation(observedAt="2024-02-29T23:59:59Z")
        ]))
        self.assertEqual(valid["observationJoin"]["observedSubjects"][0]["observedAt"],
                         "2024-02-29T23:59:59Z")

    def test_cli_rejects_duplicate_json_keys_and_nonstandard_constants(self):
        import json
        import tempfile
        original = json.dumps(self.envelope([self.observation()]))
        cut_field = '"subjectSourceCut": "' + self.cut + '"'
        assert original.count(cut_field) == 1
        duplicate_cut = original.replace(
            cut_field,
            '"subjectSourceCut": "' + "0" * 40 + '", ' + cut_field, 1,
        )
        assert original.count('"trackedPaths": 200') == 1
        duplicate_fact = original.replace(
            '"trackedPaths": 200',
            '"trackedPaths": 0, "trackedPaths": 200', 1,
        )
        # The unknown root field is intentionally ignored by the join today;
        # raw ingress still cannot admit an invalid JSON number outside it.
        nonstandard_unknown = original.replace(
            '"kind": ', '"unknownMetadata": NaN, "kind": ', 1,
        )
        # Python's JSON parser treats this valid JSON numeric syntax as inf.
        # The existing parse_constant hook never sees overflowing exponents.
        overflow_unknown = original.replace(
            '"kind": ', '"unknownMetadata": 1e309, "kind": ', 1,
        )
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td) / "reported.json"
            cmd = [
                "python3", str(ROOT / "tools/repo/exhaustive_coverage.py"),
                "--source-cut", self.cut, "--problem-legos", "--summary",
                "--authority-observations", str(path),
            ]
            for label, payload in (
                ("duplicate_source_cut", duplicate_cut),
                ("duplicate_nested_fact", duplicate_fact),
                ("nonstandard_ignored_constant", nonstandard_unknown),
                ("overflowing_ignored_float", overflow_unknown),
            ):
                with self.subTest(label=label):
                    path.write_text(payload, encoding="utf-8")
                    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True,
                                          text=True, timeout=30)
                    self.assertNotEqual(proc.returncode, 0, proc.stdout)
                    self.assertRegex(proc.stderr, "duplicate|non-standard|constant")
            path.write_text(original, encoding="utf-8")
            accepted = subprocess.run(cmd, cwd=ROOT, capture_output=True,
                                      text=True, timeout=30)
            self.assertEqual(accepted.returncode, 0, accepted.stderr)

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


class StableSourceProblemQuestionTests(unittest.TestCase):
    """Stable navigation question identity != member version or semantic LEGO."""

    @classmethod
    def setUpClass(cls):
        cls.old_cut = "4e76f8bd6ebcc65b201ff9253314c2b5a82f08ab"
        cls.new_cut = "d0c87351ac36ce157bbd7b0ca195ec19aae16b78"
        cls.old = M.derived_problem_legos(
            M.classification(ROOT, cls.old_cut), repo=ROOT
        )
        cls.new = M.derived_problem_legos(
            M.classification(ROOT, cls.new_cut), repo=ROOT
        )

    @staticmethod
    def source_issues(frontier):
        rows = [x for x in frontier["problemLegos"]
                if x["kind"] == "RECURSIVE_SOURCE_CELL_ISSUE"]
        return {(x["sourceZone"], x["physicalPrefix"]): x for x in rows}

    def test_known_source_change_keeps_question_but_invalidates_member_evidence(self):
        before = self.source_issues(self.old)
        after = self.source_issues(self.new)
        changed = [
            (before[k], after[k]) for k in before.keys() & after.keys()
            if before[k]["sourceCellRef"] != after[k]["sourceCellRef"]
            and set(before[k]["issueTags"]) & set(after[k]["issueTags"])
        ]
        assert len(changed) >= 5
        assert any(a["physicalPrefix"] == "tools/repo/" for a, _ in changed)
        for old, new in changed:
            assert old["sourceScopeQuestionRef"] == new["sourceScopeQuestionRef"]
            assert old["problemRef"] != new["problemRef"]
            assert old["sourceCellRef"] != new["sourceCellRef"]
            assert old["sourceScopeIdentityStanding"] == (
                "PHYSICAL_LOCATION_QUESTION_NOT_SEMANTIC_LEGO"
            )
        assert not self.old["proofReuseAdmissible"]
        assert not self.new["proofReuseAdmissible"]

    def test_problem_question_id_is_unique_within_exact_git_cut(self):
        for frontier in (self.old, self.new):
            issues = self.source_issues(frontier)
            refs = [r["sourceScopeQuestionRef"] for r in issues.values()]
            assert len(refs) == len(set(refs))
            assert all(r.startswith("problem:source-scope:") for r in refs)
            assert all(x["sourceCellRef"].startswith("source-cell:sha256:")
                       for x in issues.values())

    def test_scoped_question_is_accepted_but_resolves_to_current_versioned_problem(self):
        import copy
        row = self.source_issues(self.new)[("UNASSIGNED", "tools/repo/")]
        obs = {
            "authorityRef": "git:main-candidate",
            "subjectRef": "source/tools/repo",
            "observationKind": "STATIC_DYNAMIC_CONSUMER_CANDIDATE",
            "observationRevision": self.new_cut,
            "witnessRef": "job-12345678",
            "observedAt": "2026-10-28T08:00:00Z",
            "candidateProblemRef": row["sourceScopeQuestionRef"],
            "observedFacts": {"sourceCut": self.new_cut},
        }
        base = {
            "kind": "ordivon.external-authority-observations-r1",
            "subjectSourceCut": self.new_cut,
            "observations": [obs],
        }
        result = M.join_observed_authorities(self.new, base)
        link = result["observationJoin"]["candidateAssociations"][0]
        assert link["toProblemRef"] == row["problemRef"]
        assert link["sourceScopeQuestionRef"] == row["sourceScopeQuestionRef"]
        assert link["proofStanding"] == "NOT_ESTABLISHED"
        assert result["observationJoin"]["installedCurrentnessEstablished"] is False
        legacy = copy.deepcopy(base)
        legacy["observations"][0]["candidateProblemRef"] = row["problemRef"]
        old_link = M.join_observed_authorities(
            self.new, legacy
        )["observationJoin"]["candidateAssociations"][0]
        assert old_link["toProblemRef"] == row["problemRef"]
        assert old_link["sourceScopeQuestionRef"] is None

    def test_cross_cut_observation_or_unknown_question_never_gets_rebound(self):
        issue = self.source_issues(self.new)[("UNASSIGNED", "tools/repo/")]
        entry = {
            "authorityRef": "git:main-candidate",
            "subjectRef": "source/tools/repo",
            "observationKind": "STATIC_DYNAMIC_CONSUMER_CANDIDATE",
            "observationRevision": self.new_cut,
            "witnessRef": "job-12345678",
            "observedAt": "2026-10-28T08:00:00Z",
            "candidateProblemRef": issue["sourceScopeQuestionRef"],
            "observedFacts": {},
        }
        base = {"kind": "ordivon.external-authority-observations-r1",
                "subjectSourceCut": self.old_cut, "observations": [entry]}
        with self.assertRaisesRegex(ValueError, "SourceCut mismatch"):
            M.join_observed_authorities(self.new, base)
        base["subjectSourceCut"] = self.new_cut
        entry["candidateProblemRef"] = "problem:source-scope:" + "0" * 64
        with self.assertRaisesRegex(ValueError, "unscoped or unrecognized"):
            M.join_observed_authorities(self.new, base)


class TypedProblemRelationProjectionTests(unittest.TestCase):
    """Relation witnesses are exact-source candidates, never certified calls."""

    @classmethod
    def setUpClass(cls):
        cls.cut = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
        ).strip()
        cls.frontier = M.derived_problem_legos(M.classification(ROOT, cls.cut), repo=ROOT)
        cls.imports = M.static_python_import_frontier(ROOT, cls.cut)
        cls.view = M.source_problem_relation_projection(cls.frontier, cls.imports)

    def test_exact_index_and_source_evidence_are_lossless(self):
        v = self.view
        expected = self.imports["summary"]
        assert v["sourceCut"] == self.cut
        assert v["sourcePathCellIndex"] == self.frontier["sourcePathCellIndex"]
        assert v["summary"]["indexedSourcePaths"] == (
            self.frontier["summary"]["trackedPaths"]
        )
        assert v["summary"]["staticImportCandidateEdges"] == (
            expected["allStaticCandidateEdges"]
        )
        assert v["summary"]["dynamicSyntaxSites"] == (
            expected["allDynamicSyntaxSites"]
        )
        assert v["summary"]["unresolvedImportStatements"] == (
            expected["allUnresolvedImportStatements"]
        )
        assert v["summary"]["declaredPlanEdgesNotActualCalls"] == (
            self.frontier["summary"]["declaredPlanEdges"]
        )

    def test_every_import_edge_has_real_source_cells_without_claiming_calls(self):
        known = {row["sourceCellRef"] for row in self.frontier["sourceCells"]}
        for e in self.view["staticPythonImportCandidates"]:
            assert e["consumerCellRef"] in known
            assert e["providerCellRef"] in known
            assert e["consumerPath"] in self.view["sourcePathCellIndex"]
            assert e["providerPath"] in self.view["sourcePathCellIndex"]
            assert e["relation"] == "STATIC_PYTHON_IMPORT_CANDIDATE_NOT_RUNTIME_CALL"
            assert e["runtimeCallStanding"] == "UNKNOWN"
            assert e["effectStanding"] == "UNKNOWN"
            assert e["installedConsumerStanding"] == "UNKNOWN"
        assert self.view["semanticCallClosureEstablished"] is False
        assert self.view["impactClosureAdmissible"] is False
        assert self.view["deletionAuthorized"] is False
        assert self.view["proofReuseAdmissible"] is False

    def test_unresolved_imports_are_grouped_and_dynamic_providers_unresolved(self):
        v = self.view
        assert sum(x["count"] for x in v["unresolvedImportFacets"]) == (
            len(self.imports["unresolvedImportStatements"])
        )
        assert all(len(x["boundedWitnesses"]) <= 4 for x in v["unresolvedImportFacets"])
        assert all(x["standing"] == "UNRESOLVED_SYNTAX_NOT_A_MISSING_PROVIDER_PROOF"
                   for x in v["unresolvedImportFacets"])
        for row in v["dynamicSyntaxUnresolvedProviders"]:
            assert row["providerRef"] is None
            assert row["runtimeCallStanding"] == "UNKNOWN"
        assert v["summary"]["dynamicSyntaxSitesInProblemCells"] > 0

    def test_cross_plan_and_declarations_remain_noncall(self):
        v = self.view
        assert v["summary"]["unscopedPlanIdReuseQuestions"] == len(
            self.frontier["sameLocalIdAcrossPlansObservation"])
        assert all(e["runtimeCallStanding"] == "NOT_ESTABLISHED" for e in
                   v["declaredPlanRelationsNotRuntimeCalls"])
        assert len(v["reportedExternalCandidateAssociations"]) == 0

    def test_cross_cut_or_partial_ast_is_rejected(self):
        import copy
        ast = copy.deepcopy(self.imports)
        ast["sourceCut"] = "f" * 40
        with self.assertRaisesRegex(ValueError, "SourceCut mismatch"):
            M.source_problem_relation_projection(self.frontier, ast)
        ast = copy.deepcopy(self.imports)
        ast["focusPrefix"] = "services/"
        with self.assertRaisesRegex(ValueError, "unfiltered AST"):
            M.source_problem_relation_projection(self.frontier, ast)

    def test_unknown_consumer_git_path_fails_closed(self):
        import copy
        ast = copy.deepcopy(self.imports)
        assert ast["staticCandidateEdges"]
        ast["staticCandidateEdges"][0]["providerPath"] = "not/in/current/Git.py"
        with self.assertRaisesRegex(ValueError, "outside exact Git"):
            M.source_problem_relation_projection(self.frontier, ast)

    def test_false_plan_or_external_relation_promotion_is_rejected(self):
        import copy
        modified = copy.deepcopy(self.frontier)
        modified["declaredPlanEdgesNotActualCalls"][0]["runtimeCallStanding"] = "PASS"
        with self.assertRaisesRegex(ValueError, "claim runtime calls"):
            M.source_problem_relation_projection(modified, self.imports)
        modified = copy.deepcopy(self.frontier)
        modified["observationJoin"] = {"candidateAssociations": [{
            "relation": "EXECUTED_CALL",
            "proofStanding": "PROVEN",
        }]}
        with self.assertRaisesRegex(ValueError, "promoted to proof"):
            M.source_problem_relation_projection(modified, self.imports)

    def test_command_line_distinct_mode_and_summary(self):
        import json
        args = [
            "python3", str(ROOT / "tools/repo/exhaustive_coverage.py"),
            "--source-cut", self.cut,
        ]
        good = subprocess.run(
            args + ["--problem-legos", "--relation-evidence", "--summary"],
            cwd=ROOT, capture_output=True, text=True, timeout=35
        )
        assert good.returncode == 0, good.stderr
        v = json.loads(good.stdout)
        assert v["summary"]["staticImportCandidateEdges"] == len(
            self.imports["staticCandidateEdges"])
        assert "staticPythonImportCandidates" not in v
        for bad in (["--relation-evidence"], [
            "--problem-legos", "--relation-evidence", "--scope-census"
        ], [
            "--problem-legos", "--relation-evidence", "--use-proposal-cells"
        ]):
            p = subprocess.run(args + bad, cwd=ROOT,
                               capture_output=True, text=True, timeout=35)
            assert p.returncode != 0, bad

    def test_repeat_without_external_changes_is_deterministic(self):
        assert self.view == M.source_problem_relation_projection(
            self.frontier, self.imports
        )
