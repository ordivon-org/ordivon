#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("affected_owners.py")
SPEC = importlib.util.spec_from_file_location("affected_owners", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class AffectedOwnersTests(unittest.TestCase):
    def names(self, *paths: str) -> list[str]:
        return [owner.name for owner in MODULE.owners_for_paths(paths)]

    def tasks(self, *paths: str) -> list[str]:
        return [owner.task for owner in MODULE.owners_for_paths(paths)]

    def queue_tasks(self, *paths: str) -> list[str]:
        return [owner.queue_task for owner in MODULE.owners_for_paths(paths)]

    def test_owner_local_change_selects_only_that_owner(self) -> None:
        self.assertEqual(
            self.names("platform/skills/src/ordivon_skills/catalog.py"),
            ["skills"],
        )

    def test_multiple_existing_owner_changes_preserve_relative_order(self) -> None:
        self.assertEqual(
            self.names(
                "domains/game/package.json",
                "services/runtime/crates/ordivon-runtime-core/src/lib.rs",
                "services/host/src/ordivon_host/api.py",
            ),
            ["runtime", "host", "game"],
        )

    def test_next_queue_verification_defaults_to_full_verify(self) -> None:
        self.assertEqual(self.tasks("meta/next/README.md"), ["next:verify"])
        self.assertEqual(self.queue_tasks("meta/next/README.md"), ["next:verify"])

    def test_host_has_explicit_postgres_queue_verification(self) -> None:
        self.assertEqual(self.tasks("services/host/README.md"), ["host:verify"])
        self.assertEqual(self.queue_tasks("services/host/README.md"), ["host:queue"])

    def test_harness_has_explicit_queue_portable_verification(self) -> None:
        self.assertEqual(self.tasks("services/harness/README.md"), ["harness:verify"])
        self.assertEqual(
            self.queue_tasks("services/harness/README.md"), ["harness:queue"]
        )

    def test_gateway_queue_verification_defaults_to_full_verify(self) -> None:
        self.assertEqual(
            self.queue_tasks("services/gateway/src/ordivon_gateway/service.py"),
            ["gateway:verify"],
        )

    def test_artifact_has_explicit_queue_portable_verification(self) -> None:
        self.assertEqual(
            self.tasks("capabilities/artifact/README.md"), ["artifact:verify"]
        )
        self.assertEqual(
            self.queue_tasks("capabilities/artifact/README.md"), ["artifact:queue"]
        )

    def test_control_plugin_is_a_first_class_owner(self) -> None:
        self.assertEqual(
            self.tasks("extensions/ordivon-control-plane/plugin.json"),
            ["control-plugin:verify"],
        )

    def test_gateway_is_a_first_class_owner(self) -> None:
        self.assertEqual(
            self.tasks("services/gateway/src/ordivon_gateway/service.py"),
            ["gateway:verify"],
        )

    def test_web_is_a_first_class_owner(self) -> None:
        self.assertEqual(self.tasks("apps/web/src/app.ts"), ["web:verify"])

    def test_preservation_is_a_first_class_owner(self) -> None:
        self.assertEqual(
            self.tasks("capabilities/preservation/SOURCE_BOUNDARY.json"),
            ["preservation:verify"],
        )

    def test_network_uses_portable_root_ci_task_not_full_live_verify(self) -> None:
        self.assertEqual(
            self.tasks("platform/network/config/sing-box/direct.json"),
            ["network:ci"],
        )

    def test_workstation_uses_portable_ci_not_live_consequence_verify(self) -> None:
        self.assertEqual(
            self.tasks("platform/workstation/tests/test_service_profiles.py"),
            ["workstation:ci"],
        )

    def test_root_mise_is_cross_cutting(self) -> None:
        self.assertEqual(self.names("mise.toml"), [owner.name for owner in MODULE.OWNERS])

    def test_root_required_workflow_is_cross_cutting(self) -> None:
        self.assertEqual(
            self.names(".github/workflows/ci.yml"),
            [owner.name for owner in MODULE.OWNERS],
        )

    def test_owner_manifest_change_is_cross_cutting(self) -> None:
        self.assertEqual(
            self.names("tools/repo/owners.toml"),
            [owner.name for owner in MODULE.OWNERS],
        )

    def test_selector_change_is_cross_cutting(self) -> None:
        self.assertEqual(
            self.names("tools/repo/affected_owners.py"),
            [owner.name for owner in MODULE.OWNERS],
        )

    def test_dependency_policy_change_is_cross_cutting(self) -> None:
        self.assertEqual(
            self.names("tools/repo/dependency_contracts.toml"),
            [owner.name for owner in MODULE.OWNERS],
        )

    def test_dependency_checker_change_is_cross_cutting(self) -> None:
        self.assertEqual(
            self.names("tools/repo/check_owner_boundaries.py"),
            [owner.name for owner in MODULE.OWNERS],
        )

    def test_governance_or_docs_only_change_does_not_fake_owner_impact(self) -> None:
        self.assertEqual(
            self.names(
                ".github/CODEOWNERS",
                ".github/dependabot.yml",
                "docs/migration/acceptance/EXAMPLE.md",
            ),
            [],
        )

    def test_unknown_executable_root_fails_closed_at_verification_admission(self) -> None:
        self.assertEqual(self.names("services/unregistered/new.py"), [])
        with self.assertRaisesRegex(ValueError, "unregistered owner path"):
            MODULE.require_registered_execution_paths(["services/unregistered/new.py"])
        MODULE.require_registered_execution_paths(
            ["services/runtime/crates/ordivon-runtime-core/src/lib.rs"]
        )

    def test_noncanonical_paths_cannot_bypass_owner_verification(self) -> None:
        malformed = (
            "../services/runtime/src/lib.rs",
            "services/runtime/../../gateway/src/lib.rs",
            "/services/runtime/src/lib.rs",
            "services" + chr(92) + "runtime/src/lib.rs",
        )
        for path in malformed:
            with self.subTest(path=path):
                with self.assertRaisesRegex(ValueError, "noncanonical repository path"):
                    MODULE.require_registered_execution_paths([path])
                with self.assertRaisesRegex(ValueError, "noncanonical repository path"):
                    MODULE.owners_for_paths([path])

    def test_safe_relative_prefix_keeps_the_same_owner(self) -> None:
        self.assertEqual(self.names("./services/runtime/src/lib.rs"), ["runtime"])

    def test_git_cross_owner_move_selects_both_endpoints(self) -> None:
        import os
        import subprocess

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", "-b", "main", directory], check=True)
            subprocess.run(["git", "-C", directory, "config", "user.name", "CDC"], check=True)
            subprocess.run(["git", "-C", directory, "config", "user.email", "cdc@example.invalid"], check=True)
            source = root / "services/runtime/src/example.txt"
            source.parent.mkdir(parents=True)
            source.write_text("consumer\n")
            subprocess.run(["git", "-C", directory, "add", "-A"], check=True)
            subprocess.run(["git", "-C", directory, "commit", "-qm", "base"], check=True)
            before = subprocess.check_output(["git", "-C", directory, "rev-parse", "HEAD"], text=True).strip()
            destination = root / "services/gateway/src/example.txt"
            destination.parent.mkdir(parents=True)
            source.rename(destination)
            subprocess.run(["git", "-C", directory, "add", "-A"], check=True)
            subprocess.run(["git", "-C", directory, "commit", "-qm", "move"], check=True)
            after = subprocess.check_output(["git", "-C", directory, "rev-parse", "HEAD"], text=True).strip()
            previous = Path.cwd()
            try:
                os.chdir(root)
                paths = MODULE.changed_paths(before, after)
            finally:
                os.chdir(previous)
            self.assertEqual(
                set(paths),
                {"services/runtime/src/example.txt", "services/gateway/src/example.txt"},
            )

    def test_unknown_top_level_path_is_not_silently_attributed(self) -> None:
        self.assertEqual(self.names("README.md"), [])

    def test_all_owner_names_roots_and_tasks_are_unique(self) -> None:
        names = [owner.name for owner in MODULE.OWNERS]
        roots = [owner.root for owner in MODULE.OWNERS]
        tasks = [owner.task for owner in MODULE.OWNERS]
        queue_tasks = [owner.queue_task for owner in MODULE.OWNERS]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(roots), len(set(roots)))
        self.assertEqual(len(tasks), len(set(tasks)))
        self.assertEqual(len(queue_tasks), len(set(queue_tasks)))

    def test_manifest_rejects_duplicate_names(self) -> None:
        content = """schema_version = 1
kind = "ordivon.repo-owner-manifest"
truth_role = "repository-mechanics-only-not-domain-authority"
[[owners]]
name = "x"
root = "x/"
verify_task = "x:verify"
[[owners]]
name = "x"
root = "y/"
verify_task = "y:verify"
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "owners.toml"
            path.write_text(content, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate name"):
                MODULE.load_owners(path)

    def test_manifest_rejects_parent_traversal_root(self) -> None:
        content = MODULE.MANIFEST_PATH.read_text(encoding="utf-8").replace(
            'root = "meta/next/"', 'root = "meta/../next/"', 1
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "owners.toml"
            path.write_text(content, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "noncanonical repository path"):
                MODULE.load_owners(path)

    def test_manifest_rejects_overlapping_roots(self) -> None:
        content = """schema_version = 1
kind = "ordivon.repo-owner-manifest"
truth_role = "repository-mechanics-only-not-domain-authority"
[[owners]]
name = "x"
root = "domains/"
verify_task = "x:verify"
[[owners]]
name = "y"
root = "domains/game/"
verify_task = "y:verify"
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "owners.toml"
            path.write_text(content, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must not overlap"):
                MODULE.load_owners(path)


    def test_current_git_cut_classifies_all_source_without_expanding_owner_authority(self) -> None:
        import subprocess

        repo = Path(__file__).resolve().parents[2]
        head = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
        ).strip()
        projection = MODULE.project_source_classification(repo, head)
        self.assertEqual(projection["summary"]["unassigned"], 0)
        self.assertEqual(projection["summary"]["ambiguous"], 0)
        self.assertEqual(
            projection["summary"]["trackedPaths"],
            projection["summary"]["registeredOwnerPaths"]
            + projection["summary"]["declaredRegionPaths"],
        )
        assert projection["proofReuseAdmissible"] is False
        entries = {entry["path"]: entry for entry in projection["entries"]}
        named_navigation = {
            "tools/formal/RecursiveLegoRefinement.lean": "native-formal-toolchain-source",
            "tools/repo/planning/lego-plan-r1.json": "repository-lego-plan-carrier",
            ".agents/skills/recursive-lego-calculus/SKILL.md": "lego-r21-mathematical-foundation",
            ".github/workflows/ci.yml": "repository-configuration",
        }
        for path, region in named_navigation.items():
            with self.subTest(path=path):
                self.assertIn(path, entries)
                self.assertIsNone(entries[path]["verificationOwner"])
                self.assertEqual(entries[path]["sourceRegion"], region)
                self.assertEqual(entries[path]["classificationLayer"],
                                 "SOURCE_NAVIGATION_ONLY")
        self.assertEqual(
            entries["services/runtime/crates/ordivon-runtime-core/src/lib.rs"]["verificationOwner"],
            "runtime",
        )
        self.assertEqual(
            entries["services/runtime/crates/ordivon-runtime-core/src/lib.rs"]["semanticName"],
            "physical-execution-runtime",
        )



class SourceClassificationTests(unittest.TestCase):
    """Exercise real Git cuts; path classification never selects execution authority."""

    def setUp(self) -> None:
        import subprocess
        self.subprocess = subprocess
        self.temp = tempfile.TemporaryDirectory(prefix="ordivon-source-regions-")
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Source Region Test")
        self.git("config", "user.email", "source-region@example.invalid")
        self.header = (
            'schema_version = 1\ntruth_role = "repository-mechanics-only-not-domain-authority"\n'
            '[[owners]]\nname = "runtime"\nroot = "services/runtime/"\n'
            'verify_task = "runtime:verify"\n'
        )
        self.manifest = self.repo / "tools/repo/owners.toml"
        self.manifest.parent.mkdir(parents=True)
        self.manifest.write_text(self.header)
        for name in ["services/runtime/main.rs", ".agents/skills/recursive-lego-calculus/SKILL.md",
                     "loose/unplaced.txt", "mise.toml", "odd/ leading\npath.txt"]:
            p = self.repo / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("source")
        self.base = self.commit()

    def git(self, *args: str) -> str:
        return self.subprocess.check_output(
            ["git", "-c", "maintenance.auto=false", "-c", "gc.auto=0",
             "-C", str(self.repo), *args], text=True
        ).strip()

    def commit(self) -> str:
        self.git("add", ".")
        self.git("commit", "-qm", "source cut")
        return self.git("rev-parse", "HEAD")

    def project(self, cut: str) -> dict:
        fn = getattr(MODULE, "project_source_classification", None)
        self.assertTrue(callable(fn), "existing Repo CLI must expose exact-cut source classification")
        return fn(self.repo, cut)

    def test_empty_semantic_names_fail_closed_without_affecting_owner_id(self) -> None:
        self.manifest.write_text(
            self.header.replace('name = "runtime"\n', 'name = "runtime"\nsemantic_name = ""\n')
        )
        cut = self.commit()
        with self.assertRaisesRegex(ValueError, "semantic_name must be a canonical nonempty string"):
            self.project(cut)
        self.manifest.write_text(
            self.header + '\n[[source_regions]]\n'
            'name = "methods"\ndescription = ""\npaths = [".agents/skills/"]\n'
        )
        cut = self.commit()
        with self.assertRaisesRegex(ValueError, "source region description must be a canonical nonempty string"):
            self.project(cut)

    def test_root_file_form_and_nested_cells_are_distinct_source_dimensions(self) -> None:
        # Physical file form can be known even when business semantics are not.
        artifacts = [
            "services/runtime/README.md",
            "services/runtime/Cargo.toml",
            "services/runtime/Cargo.lock",
            "services/runtime/config/opaque.blob",
            "services/runtime/crates/ordivon-runtime-core/src/lib.rs",
            "domains/capital/wave_b/fixtures/sample.json",
            "domains/capital/destroyer/false-green-corpus-v0.json",
        ]
        self.manifest.write_text(
            self.header + '\n[[owners]]\nname = "capital"\n'
            'root = "domains/capital/"\nverify_task = "capital:verify"\n'
        )
        for name in artifacts:
            p = self.repo / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("test source")
        cut = self.commit()
        by_path = {e["path"]: e for e in self.project(cut)["entries"]}
        assert by_path["services/runtime/README.md"]["sourceFileForm"] == "PROJECT_README"
        assert by_path["services/runtime/Cargo.toml"]["sourceFileForm"] == "RUST_PACKAGE_MANIFEST"
        assert by_path["services/runtime/Cargo.toml"]["sourceFileFormStanding"] == "FILENAME_OR_EXTENSION_ONLY_NOT_CONTENT_PROVEN"
        assert by_path["services/runtime/Cargo.toml"]["sourceCellDisplayName"] == "runtime / (root files)"
        assert by_path["services/runtime/Cargo.lock"]["sourceFileForm"] == "RUST_DEPENDENCY_LOCK"
        assert by_path["services/runtime/Cargo.lock"]["sourceCell"] == "runtime/(root-files)"
        assert by_path["services/runtime/config/opaque.blob"]["sourceFileForm"] == "UNQUALIFIED_FILE_FORM"
        assert by_path["services/runtime/config/opaque.blob"]["sourceFileFormStanding"] == "OPAQUE_FORM_NEEDS_CONTENT_EVIDENCE"
        assert by_path["services/runtime/crates/ordivon-runtime-core/src/lib.rs"]["sourceCell"] == "runtime/crates/ordivon-runtime-core"
        assert by_path["services/runtime/crates/ordivon-runtime-core/src/lib.rs"]["sourceCellRole"] == "RUNTIME_CORE_CRATE_SOURCE"
        assert by_path["domains/capital/wave_b/fixtures/sample.json"]["sourceCellRole"] == "HISTORICAL_PORTFOLIO_TEST_FIXTURE_SOURCE"
        assert by_path["domains/capital/destroyer/false-green-corpus-v0.json"]["sourceFileForm"] == "JSON_STRUCTURED_DATA_SOURCE"
        assert by_path["domains/capital/destroyer/false-green-corpus-v0.json"]["sourceSectionRole"] == "FALSIFICATION_CORPUS_SOURCE"
        assert self.project(cut)["summary"]["unqualifiedSourceFileForms"] >= 1
        assert by_path["services/runtime/Cargo.toml"]["classificationLayer"] == "REPOSITORY_VERIFICATION_REGION"
        assert by_path["services/runtime/Cargo.toml"]["verificationOwner"] == "runtime"

    def test_gap_projection_exposes_unknown_source_cells_without_inventing_authority(self) -> None:
        # A completely assigned Git tree may still contain unqualified meaning.
        for name in (
            "services/runtime/config/opaque.blob",
            "services/runtime/crates/unseen-third-party/src/lib.rs",
        ):
            file = self.repo / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text("unknown")
        cut = self.commit()
        result = MODULE.project_source_classification_gaps(self.project(cut))
        self.assertEqual(result["sourceRevision"], cut)
        self.assertEqual(result["truthRole"],
                         "SOURCE_NAVIGATION_GAPS_NOT_SEMANTIC_LEGO_PROOF_OR_INSTALLATION")
        self.assertEqual(result["semanticCompletion"], "UNKNOWN")
        self.assertFalse(result["proofReuseAdmissible"])
        self.assertGreaterEqual(result["gapSummary"]["UNASSIGNED_OR_AMBIGUOUS_PATH"]["paths"], 1)
        self.assertEqual(result["gapSummary"]["UNQUALIFIED_SECTION"]["paths"], 0)
        self.assertGreaterEqual(result["gapSummary"]["MIXED_ROOT_CARRIERS"]["paths"], 1)
        self.assertGreaterEqual(result["gapSummary"]["UNQUALIFIED_NESTED_CELL"]["paths"], 1)
        self.assertGreaterEqual(result["gapSummary"]["OPAQUE_FILE_FORM"]["paths"], 1)
        gaps = {(x["gapKind"], x["sourceLocator"]): x for x in result["groups"]}
        self.assertIn(("UNASSIGNED_OR_AMBIGUOUS_PATH", "loose/unplaced.txt"), gaps)
        self.assertIn(("MIXED_ROOT_CARRIERS", "runtime/(root-files)"), gaps)
        self.assertIn(("UNQUALIFIED_NESTED_CELL",
                       "runtime/crates/unseen-third-party"), gaps)
        self.assertIn(("OPAQUE_FILE_FORM", "runtime/config/(direct-files)"), gaps)
        self.assertIn("services/runtime/config/opaque.blob",
                      gaps[("OPAQUE_FILE_FORM", "runtime/config/(direct-files)")]["sampleGitPaths"])

    def test_semantic_names_do_not_become_verification_authorities(self) -> None:
        # Source presentation changes without changing the actual owner ID
        # or granting it an additional verification task or runtime authority.
        src = self.header.replace(
            'name = "runtime"\n',
            'name = "runtime"\nsemantic_name = "Execution Runtime"\n'
        )
        self.manifest.write_text(
            src + '\n[[source_regions]]\n'
            'name = "methods"\n'
            'description = "Agent methods not service routing"\n'
            'paths = [".agents/skills/"]\n'
        )
        cut = self.commit()
        projection = self.project(cut)
        row = {r["path"]: r for r in projection["entries"]}
        assert row["services/runtime/main.rs"]["verificationOwner"] == "runtime"
        assert row["services/runtime/main.rs"]["semanticName"] == "Execution Runtime"
        assert row["services/runtime/main.rs"]["sourceSection"] == "runtime/(root-files)"
        assert row["services/runtime/main.rs"]["sourceSectionRole"] == "MIXED_ROOT_CARRIER_FORMS_NOT_ONE_RESPONSIBILITY"
        # No automatic promotion of an arbitrary root source into a LEGO type.
        assert row["services/runtime/main.rs"]["classificationLayer"] == "REPOSITORY_VERIFICATION_REGION"
        assert row[".agents/skills/recursive-lego-calculus/SKILL.md"]["semanticName"] == "Agent methods not service routing"
        assert row[".agents/skills/recursive-lego-calculus/SKILL.md"]["verificationOwner"] is None
        assert row[".agents/skills/recursive-lego-calculus/SKILL.md"]["classificationLayer"] == "SOURCE_NAVIGATION_ONLY"
        assert row["loose/unplaced.txt"]["semanticName"] is None

    def test_semantic_name_only_delta_detects_unchanged_source_reclassification(self) -> None:
        # A physical Git blob stays identical, but its Agent-facing meaning
        # changes through the exact manifest: this MUST be part of delta.
        self.manifest.write_text(
            self.header.replace('name = "runtime"\n',
                                'name = "runtime"\nsemantic_name = "Execution Runtime"\n')
        )
        prior = self.commit()
        self.manifest.write_text(
            self.header.replace('name = "runtime"\n',
                                'name = "runtime"\nsemantic_name = "Runtime Attempt Lifecycle"\n')
        )
        current = self.commit()
        d = MODULE.project_source_classification_delta(self.repo, prior, current)
        indexed = {row["path"]: row for row in d["changes"]}
        changed = indexed["services/runtime/main.rs"]
        self.assertFalse(changed["sourceChanged"])
        self.assertTrue(changed["classificationChanged"])
        self.assertEqual(changed["before"]["semanticName"], "Execution Runtime")
        self.assertEqual(changed["after"]["semanticName"], "Runtime Attempt Lifecycle")
        self.assertGreaterEqual(d["summary"]["classificationOnlyChanges"], 1)
        self.assertFalse(d["requiresWholeClassificationReprojection"])
        self.assertFalse(d["proofReuseAdmissible"])

    def test_source_classifier_code_change_never_claims_complete_historical_delta(self) -> None:
        # Re-running one *current* Python classifier for two different Git
        # source cuts cannot reconstruct older source semantics mechanically.
        classifier = self.repo / "tools/repo/affected_owners.py"
        classifier.write_text("source classifier v1", encoding="utf-8")
        prior = self.commit()
        classifier.write_text("source classifier v2", encoding="utf-8")
        current = self.commit()
        d = MODULE.project_source_classification_delta(self.repo, prior, current)
        self.assertTrue(d["classifierSourceChanged"])
        self.assertTrue(d["requiresWholeClassificationReprojection"])
        self.assertEqual(
            d["deltaCompleteness"], "UNKNOWN_SOURCE_CLASSIFIER_IMPLEMENTATION_CHANGED"
        )
        self.assertFalse(d["proofReuseAdmissible"])

    def test_nested_source_cell_names_do_not_certify_actual_consumers_or_deployment(self) -> None:
        self.manifest.write_text(
            self.header +
            '\n[[owners]]\nname = "network"\nroot = "platform/network/"\n'
            'verify_task = "network:ci"\n'
        )
        paths = (
            "platform/network/consumers/new-agent/requirements.json",
            "services/runtime/crates/ordivon-runtime-mcp/src/lib.rs",
            "services/runtime/crates/unseen-third-party/src/lib.rs",
        )
        for value in paths:
            path = self.repo / value
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("source-only", encoding="utf-8")
        d = self.project(self.commit())
        rows = {row["path"]: row for row in d["entries"]}
        network = rows[paths[0]]
        self.assertEqual(network["sourceCell"], "network/consumers/new-agent")
        self.assertEqual(network["sourceCellRole"], "NETWORK_CONSUMER_REQUIREMENT_SOURCE")
        self.assertEqual(network["verificationOwner"], "network")
        self.assertEqual(network["sourceFileForm"], "JSON_STRUCTURED_DATA_SOURCE")
        # Skill prose, an MCP client manifest, and a Gateway service are not
        # interchangeable Tool/Skill/Plugin types.
        portable_method = rows[".agents/skills/recursive-lego-calculus/SKILL.md"]
        self.assertEqual(portable_method["sourceFileForm"], "AGENT_SKILL_INSTRUCTION_SOURCE")
        self.assertIsNone(portable_method["verificationOwner"])
        self.assertEqual(rows[paths[1]]["sourceCellRole"], "RUNTIME_MCP_CRATE_SOURCE")
        self.assertEqual(rows[paths[2]]["sourceCellRole"], "UNQUALIFIED_NESTED_CELL")
        self.assertFalse(d["proofReuseAdmissible"])

    def test_regions_classify_source_without_manufacturing_execution_owner(self) -> None:
        self.manifest.write_text(self.header + (
            '\n[[source_regions]]\nname = "lego-core"\n'
            'paths = [".agents/skills/recursive-lego-calculus/"]\n'
        ))
        cut = self.commit()
        value = self.project(cut)
        entries = {e["path"]: e for e in value["entries"]}
        self.assertEqual(entries["services/runtime/main.rs"]["verificationOwner"], "runtime")
        core = entries[".agents/skills/recursive-lego-calculus/SKILL.md"]
        self.assertEqual(core["sourceRegion"], "lego-core")
        self.assertIsNone(core["verificationOwner"])
        self.assertEqual(core["classificationStanding"], "DECLARED_SOURCE_REGION")
        self.assertEqual(entries["loose/unplaced.txt"]["classificationStanding"], "UNASSIGNED")
        # Cross-cutting verification fanout must not masquerade as file ownership.
        self.assertIsNone(entries["mise.toml"]["verificationOwner"])
        self.assertEqual(value["sourceRevision"], cut)
        self.assertFalse(value["proofReuseAdmissible"])
        old = self.project(self.base)
        prior = next(e for e in old["entries"] if e["path"] == core["path"])
        self.assertEqual(prior["classificationStanding"], "UNASSIGNED")
        # Mutable bytes cannot backfill a historical SourceCut.
        self.manifest.write_text("broken mutable worktree")
        self.assertEqual(self.project(cut), value)

    def test_overlapping_regions_remain_ambiguous_and_git_names_are_lossless(self) -> None:
        self.manifest.write_text(self.header + (
            '\n[[source_regions]]\nname = "one"\npaths = ["odd/"]\n'
            '\n[[source_regions]]\nname = "two"\npaths = ["odd/"]\n'
        ))
        value = self.project(self.commit())
        row = next(e for e in value["entries"] if e["path"] == "odd/ leading\npath.txt")
        self.assertEqual(row["classificationStanding"], "AMBIGUOUS")
        self.assertIsNone(row["sourceRegion"])
        self.assertEqual(len(row["matchedRules"]), 2)
        self.assertEqual(value["summary"]["ambiguous"], 1)
        self.manifest.write_text(self.manifest.read_text() + 'exclude = ["odd/"]\n')
        fixed = self.project(self.commit())
        row = next(e for e in fixed["entries"] if e["path"] == "odd/ leading\npath.txt")
        self.assertEqual(row["sourceRegion"], "one")
        self.assertEqual(row["classificationStanding"], "DECLARED_SOURCE_REGION")

    def test_source_cell_names_are_bounded_path_labels_not_new_lego_owners(self) -> None:
        # One native Runtime systemd source carries a visibly distinct
        # packaging responsibility, but source naming is not installation,
        # verification authority or a second LEGO identity.
        source = self.repo / "services/runtime/packaging/systemd/runtime.service"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("[Service]\\nExecStart=/bin/true\\n")
        result = self.project(self.commit())
        row = next(item for item in result["entries"] if item["path"] ==
                   "services/runtime/packaging/systemd/runtime.service")
        self.assertEqual(row["sourceCellRole"], "RUNTIME_SYSTEMD_PACKAGING_SOURCE")
        self.assertEqual(row["verificationOwner"], "runtime")
        self.assertEqual(row["classificationLayer"], "REPOSITORY_VERIFICATION_REGION")
        self.assertFalse(result["proofReuseAdmissible"])
        self.assertNotIn("installed", row)
        self.assertNotIn("verifiedBy", row)

    def test_x_reality_is_x_api_transport_not_xray_or_oauth_authority(self) -> None:
        # The native source's README limits this consumer to api.x.com:443
        # transport; Agent/user OAuth credentials belong to another authority.
        self.manifest.write_text(self.header + (
            '\n[[owners]]\nname = "network"\nroot = "platform/network/"\n'
            'verify_task = "network:ci"\n'
        ))
        path = self.repo / "platform/network/consumers/x-reality/config/authority.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{"apiHost":"api.x.com"}')
        result = self.project(self.commit())
        row = next(r for r in result["entries"] if r["path"] ==
                   "platform/network/consumers/x-reality/config/authority.json")
        self.assertEqual(row["sourceCellRole"],
                         "NETWORK_X_API_TRANSPORT_CONSUMER_SOURCE")
        self.assertEqual(row["verificationOwner"], "network")
        self.assertFalse(result["proofReuseAdmissible"])
        self.assertNotIn("oauth", str(row).lower())
        self.assertNotIn("installed", row)

    def test_regions_cannot_acquire_validation_or_authority(self) -> None:
        for field in ["verify_task", "authority"]:
            with self.subTest(field=field):
                self.manifest.write_text(self.header + (
                    '\n[[source_regions]]\nname = "pretender"\npaths = ["loose/"]\n'
                    + field + ' = "runtime:verify"\n'
                ))
                with self.assertRaisesRegex(ValueError, "source region"):
                    self.project(self.commit())

    def test_incremental_navigation_reports_unmodified_source_reclassified_by_manifest(self) -> None:
        source = ".agents/skills/recursive-lego-calculus/SKILL.md"
        self.manifest.write_text(self.header + (
            '\n[[source_regions]]\nname = "method-core"\n'
            'paths = [".agents/skills/recursive-lego-calculus/"]\n'
        ))
        head = self.commit()
        delta = MODULE.project_source_classification_delta(self.repo, self.base, head)
        self.assertFalse(delta["proofReuseAdmissible"])
        self.assertEqual(delta["beforeRevision"], self.base)
        self.assertEqual(delta["afterRevision"], head)
        index = {entry["path"]: entry for entry in delta["changes"]}
        changed = index[source]
        self.assertFalse(changed["sourceChanged"])
        self.assertTrue(changed["classificationChanged"])
        self.assertEqual(changed["before"]["sourceIdentity"], changed["after"]["sourceIdentity"])
        self.assertEqual(changed["before"]["classificationStanding"], "UNASSIGNED")
        self.assertEqual(changed["after"]["sourceRegion"], "method-core")
        self.assertGreater(delta["summary"]["classificationOnlyChanges"], 0)
        self.assertNotIn("services/runtime/main.rs", index)
        # A renaming of the *region* must still invalidate navigation on
        # immutable, untouched source bytes.
        self.manifest.write_text(self.manifest.read_text().replace(
            'name = "method-core"', 'name = "renamed-contract"',
        ))
        renamed = MODULE.project_source_classification_delta(self.repo, head, self.commit())
        changed = next(row for row in renamed["changes"] if row["path"] == source)
        self.assertTrue(changed["classificationChanged"])
        self.assertFalse(changed["sourceChanged"])
        self.assertEqual(changed["after"]["sourceRegion"], "renamed-contract")

    def test_exact_cut_delta_preserves_both_move_endpoints_without_proving_consumers(self) -> None:
        original = self.repo / "loose/unplaced.txt"
        destination = self.repo / "loose/moved.txt"
        original.rename(destination)
        self.manifest.write_text(self.header + (
            '\n[[source_regions]]\nname = "loose"\npaths = ["loose/"]\n'
        ))
        head = self.commit()
        value = MODULE.project_source_classification_delta(self.repo, self.base, head)
        observations = {row["path"]: row for row in value["changes"]}
        self.assertIsNone(observations["loose/unplaced.txt"]["after"])
        self.assertIsNone(observations["loose/moved.txt"]["before"])
        self.assertTrue(observations["loose/moved.txt"]["sourceChanged"])
        self.assertFalse(value["proofReuseAdmissible"])
        self.assertNotIn("consumerProof", value)
        self.assertNotIn("installed", value)

    def test_narrow_cli_reads_only_requested_source_cut_entries(self) -> None:
        import shutil
        import json
        for name in ["affected_owners.py", "source_history_legos.py"]:
            shutil.copy2(MODULE_PATH.parent / name, self.repo / "tools/repo" / name)
        base = self.commit()
        proc = self.subprocess.run(
            [sys.executable, "tools/repo/affected_owners.py",
             "--classify-source-revision", base,
             "--source-path", "services/runtime/main.rs",
             "--source-path", "nonexistent/consumer.ts"],
            cwd=self.repo, text=True, capture_output=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(len(result["entries"]), 1)
        self.assertEqual(result["entries"][0]["verificationOwner"], "runtime")
        self.assertEqual(result["query"]["mode"], "EXACT_SOURCE_PATHS_ONLY")
        self.assertEqual(result["query"]["absentFromSourceCut"], ["nonexistent/consumer.ts"])
        self.assertFalse(result["proofReuseAdmissible"])
        for invalid in [
            ["--source-path", "../services/runtime/main.rs"],
            ["--source-path", "./services/runtime/main.rs"],
            ["--source-path", ""],
            ["--classify-source-delta-base", self.base,
             "--source-path", "services/runtime/main.rs"],
        ]:
            negative = self.subprocess.run(
                [sys.executable, "tools/repo/affected_owners.py",
                 "--classify-source-revision", base, *invalid],
                cwd=self.repo, text=True, capture_output=True,
            )
            self.assertNotEqual(negative.returncode, 0)

    def test_real_cli_ignores_malformed_mutable_manifest(self) -> None:
        import shutil
        import json
        for name in ["affected_owners.py", "source_history_legos.py"]:
            shutil.copy2(MODULE_PATH.parent / name, self.repo / "tools/repo" / name)
        cut = self.commit()
        self.manifest.write_text("broken mutable TOML [")
        proc = self.subprocess.run(
            [sys.executable, "tools/repo/affected_owners.py",
             "--classify-source-revision", cut],
            cwd=self.repo, text=True, capture_output=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["sourceRevision"], cut)

    def test_mutable_revision_and_symlink_manifest_cannot_witness_classification(self) -> None:
        with self.assertRaisesRegex(ValueError, "exact"):
            self.project("HEAD")
        saved = self.manifest.read_text()
        self.manifest.unlink()
        (self.repo / "manifest.toml").write_text(saved)
        self.manifest.symlink_to("../../manifest.toml")
        with self.assertRaisesRegex(ValueError, "regular"):
            self.project(self.commit())


if __name__ == "__main__":
    unittest.main()
