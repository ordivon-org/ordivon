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
        assert row["services/runtime/main.rs"]["sourceSectionRole"] == "UNQUALIFIED_SECTION"
        # No automatic promotion of an arbitrary root source into a LEGO type.
        assert row["services/runtime/main.rs"]["classificationLayer"] == "REPOSITORY_VERIFICATION_REGION"
        assert row[".agents/skills/recursive-lego-calculus/SKILL.md"]["semanticName"] == "Agent methods not service routing"
        assert row[".agents/skills/recursive-lego-calculus/SKILL.md"]["verificationOwner"] is None
        assert row[".agents/skills/recursive-lego-calculus/SKILL.md"]["classificationLayer"] == "SOURCE_NAVIGATION_ONLY"
        assert row["loose/unplaced.txt"]["semanticName"] is None

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
