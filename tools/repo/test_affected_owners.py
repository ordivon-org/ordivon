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

    def test_r21_semantic_core_and_native_repo_formal_sources_are_independent_roots(self) -> None:
        expected = {
            ".agents/skills/recursive-lego-calculus/references/formal-model.md": "lego-core",
            "tools/formal/RecursiveLegoRefinement.lean": "formal",
        }
        for path, natural_owner in expected.items():
            self.assertEqual(self.names(path), [natural_owner], path)
        # Skills runtime/catalog is a different responsibility from canonical
        # LEGO calculus; a formal verifier is a tool, not a second truth owner.
        self.assertEqual(self.names("platform/skills/src/ordivon_skills/catalog.py"), ["skills"])
        self.assertEqual(self.names("packages/composition/src/ordivon_composition/interface_contract_r2.py"), ["composition"])
        # A method outside canonical R2.1 is not silently promoted into core.
        self.assertEqual(self.names(".agents/skills/method-router/SKILL.md"), [])
        self.assertEqual(self.names("meta/research/publication-closure-profile-r2.json"), [])
        # Repo mechanics are already central cross-cutting Git/Owner tools;
        # naming their test fixture paths a production Owner would invent
        # cross-Owner consumers and permission seams.
        self.assertEqual(self.names("tools/repo/source_history_legos.py"), [])

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


if __name__ == "__main__":
    unittest.main()
