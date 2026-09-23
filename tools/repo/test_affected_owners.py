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
            self.names("extensions/chatgpt-skills-mcp/src/ordivon_skills/catalog.py"),
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
