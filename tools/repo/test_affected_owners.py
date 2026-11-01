#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
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

    def test_project_agent_skill_changes_select_existing_skills_consumer(self) -> None:
        # Real Skills test reads this canonical project Skill, not just platform/skills source.
        source = ".agents/skills/recursive-lego-calculus/SKILL.md"
        self.assertEqual(self.names(source), ["skills"])
        self.assertEqual(self.queue_tasks(source), ["skills:verify"])
        self.assertEqual(
            self.names(".agents/skills/recursive-lego-calculus/references/formal-model.md"),
            ["skills"],
        )
        self.assertEqual(self.names("docs/agent-skills-example.md"), [])

    def test_runtime_release_workflow_selects_actual_runtime_verifier(self) -> None:
        # Tagged release workflow builds Runtime binary, SBOM and attestations.
        source = ".github/workflows/runtime-release.yml"
        self.assertEqual(self.names(source), ["runtime"])
        self.assertEqual(self.queue_tasks(source), ["runtime:verify"])
        self.assertEqual(self.names(".github/workflows/release-notes-example.yml"), [])

    def test_multiple_existing_owner_changes_preserve_relative_order(self) -> None:
        self.assertEqual(
            self.names(
                "domains/game/package.json",
                "services/runtime/crates/ordivon-runtime-core/src/lib.rs",
                "services/host/src/ordivon_host/api.py",
            ),
            ["runtime", "host", "game"],
        )

    def test_root_mise_formal_task_contract_change_requires_formal_verifier(self) -> None:
        # Root mise.toml defines formal:verify itself. A change to the task
        # wiring invalidates the proof-invocation contract even if proof
        # source files have not changed.
        self.assertTrue(MODULE.requires_core_formal_verification(["mise.toml"]))
        self.assertFalse(MODULE.requires_core_formal_verification(["docs/mise.toml"]))

    def test_core_formal_source_requires_real_proof_task_without_new_owner(self) -> None:
        verify = MODULE.requires_core_formal_verification
        self.assertTrue(verify(("tools/formal/Proof.rs",)))
        self.assertTrue(verify(("tools/formal/RecursiveLegoRefinement.lean",)))
        self.assertTrue(verify(("apps/web/README.md", "tools/formal/verify.py")))
        self.assertFalse(verify(("tools/formalized/Proof.rs",)))
        self.assertFalse(verify(("tools/repo/check_architecture_docs.py",)))
        with self.assertRaisesRegex(ValueError, "noncanonical"):
            verify(("tools/formal/../other.py",))
        self.assertEqual(
            self.queue_tasks("tools/formal/RecursiveLegoRefinement.lean"), []
        )

    def test_harness_timeout_proof_input_selects_existing_formal_task(self) -> None:
        # The native Formal source readset consumes this exact Harness adapter.
        # A Harness-only change must invalidate the proof task as well.
        source = "services/harness/src/ordivon_harness/plugin_gateway_effect.py"
        self.assertEqual(self.names(source), ["harness"])
        self.assertTrue(MODULE.requires_core_formal_verification((source,)))
        self.assertFalse(MODULE.requires_core_formal_verification((
            "services/harness/README.md",
        )))

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

    def test_executed_shared_producer_selects_exact_known_owner_consumer(self) -> None:
        # The root repo:ci always checks the repository source tools.
        # Composition additionally *executes* the source-history producer.
        source = "tools/repo/source_history_legos.py"
        self.assertEqual(self.names(source), ["composition"])
        self.assertEqual(self.queue_tasks(source), ["composition:verify"])
        self.assertEqual(
            self.names("docs/architecture/EXAMPLE.md", source), ["composition"],
        )
        # An independent actual owner source composes without duplicates.
        self.assertEqual(
            self.names(source, "services/runtime/crates/ordivon-runtime-core/src/lib.rs"),
            ["composition", "runtime"],
        )

    def test_source_history_inherits_full_transitive_composition_queue(self) -> None:
        # Assert the real CLI's TRANSITIVE consumers, not a fixed six-task
        # snapshot. New legitimate Composition dependents extend both sides.
        cli = MODULE_PATH.with_name("convergence_plan.py")

        def selected(path: str) -> dict:
            result = subprocess.run(
                [sys.executable, str(cli), "--changed-file", path],
                check=True, capture_output=True, text=True,
            )
            return json.loads(result.stdout)

        history = selected("tools/repo/source_history_legos.py")
        composition = selected(
            "packages/composition/src/ordivon_composition/verification_obligation_r1.py"
        )
        self.assertEqual(history["queueVerifyTasks"], composition["queueVerifyTasks"])
        self.assertEqual(history["verificationOwners"], composition["verificationOwners"])
        self.assertIn("composition:verify", history["queueVerifyTasks"])
        self.assertNotIn("formal:verify", history["queueVerifyTasks"])

    def test_repo_inventory_producer_is_covered_by_unconditional_root_ci(self) -> None:
        # convergence_plan imports this module; the canonical root suite
        # already runs test_convergence_plan before affected-owner selection.
        self.assertEqual(self.names("tools/repo/exhaustive_coverage.py"), [])
        self.assertEqual(self.queue_tasks("tools/repo/exhaustive_coverage.py"), [])
        self.assertEqual(self.names("tools/repo/README.md"), [])
        self.assertEqual(self.names("tools/repo/test_source_history_legos.py"), [])

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

    def test_exact_git_sourcecut_ignores_foreign_repository_environment(self) -> None:
        # CI and agents may inherit GIT_DIR from a separate git-worktree or
        # GIT_OBJECT_DIRECTORY from an alternate repository. Verify actual
        # source/consumer selection for the cwd repository, not the ambient one.
        import os
        from unittest.mock import patch

        with tempfile.TemporaryDirectory(prefix="ordivon-owner-git-env-") as tmp:
            root = Path(tmp)
            local = root / "actual"
            foreign = root / "foreign"
            for repo in (local, foreign):
                repo.mkdir()
                subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
                subprocess.run(["git", "-C", str(repo), "config",
                                "user.email", "test@example.invalid"], check=True)
                subprocess.run(["git", "-C", str(repo), "config",
                                "user.name", "Owner Git testcase"], check=True)
                (repo / "file.txt").write_text("initial\n", encoding="utf-8")
                subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
                subprocess.run(["git", "-C", str(repo), "commit", "-qm", "base"], check=True)

            def git(repo: Path, *args: str) -> str:
                return subprocess.check_output(
                    ["git", "-C", str(repo), *args], text=True,
                ).strip()

            before = git(local, "rev-parse", "HEAD")
            target = local / "services" / "runtime" / "src" / "consumer.py"
            target.parent.mkdir(parents=True)
            target.write_text("ENABLED = True\n", encoding="utf-8")
            git(local, "add", ".")
            git(local, "commit", "-qm", "introduce runtime consumer")
            after = git(local, "rev-parse", "HEAD")
            expected = ("services/runtime/src/consumer.py",)
            previous = Path.cwd()
            try:
                os.chdir(local)
                self.assertEqual(MODULE.changed_paths(before, after), expected)
                for env in (
                    {"GIT_DIR": str(foreign / ".git")},
                    {"GIT_OBJECT_DIRECTORY": str(foreign / ".git" / "objects")},
                    {"GIT_ALTERNATE_OBJECT_DIRECTORIES": str(foreign / ".git" / "objects")},
                ):
                    with self.subTest(env=tuple(env)):
                        with patch.dict(os.environ, env):
                            self.assertEqual(
                                MODULE.changed_paths(before, after), expected
                            )
            finally:
                os.chdir(previous)

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


if __name__ == "__main__":
    unittest.main()
