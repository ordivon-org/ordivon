#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("convergence_plan.py")
SPEC = importlib.util.spec_from_file_location("convergence_plan", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ConvergencePlanTests(unittest.TestCase):
    def test_runtime_change_stays_in_isolated_owner_component(self) -> None:
        plan = MODULE.build_plan(
            changed_files=["services/runtime/crates/ordivon-runtime-core/src/lib.rs"]
        )
        self.assertEqual(plan["directOwners"], ["runtime"])
        self.assertEqual(plan["verificationOwners"], ["runtime"])
        self.assertEqual(plan["verifyTasks"], ["runtime:verify"])
        self.assertEqual(plan["queueClass"], "SCOPED")
        self.assertEqual(
            plan["independenceClaim"],
            "NOT_ESTABLISHED_BY_THIS_PROJECTION",
        )

    def test_media_change_expands_to_declared_interaction_component(self) -> None:
        plan = MODULE.build_plan(
            changed_files=["capabilities/media/src/ordivon_studio/agent_surface.py"]
        )
        self.assertEqual(plan["directOwners"], ["media"])
        self.assertEqual(
            plan["verificationOwners"],
            ["artifact", "distribution", "game", "media", "workstation"],
        )
        self.assertEqual(len(plan["scopeIds"]), 1)

    def test_security_change_expands_to_harness_and_web_component(self) -> None:
        plan = MODULE.build_plan(changed_files=["platform/security/README.md"])
        self.assertEqual(
            plan["verificationOwners"],
            ["composition", "harness", "next", "security", "skills", "web"],
        )

    def test_cross_cutting_change_requires_all_owner_verification(self) -> None:
        plan = MODULE.build_plan(
            changed_files=["tools/repo/dependency_contracts.toml"]
        )
        self.assertTrue(plan["crossCutting"])
        self.assertEqual(plan["queueClass"], "CROSS_CUTTING")
        self.assertEqual(
            plan["verificationOwners"],
            sorted(owner.name for owner in MODULE.affected_owners.OWNERS),
        )
        self.assertEqual(plan["scopeIds"], ["owner-component:ALL"])

    def test_repository_only_change_does_not_invent_domain_impact(self) -> None:
        plan = MODULE.build_plan(changed_files=["docs/architecture/EXAMPLE.md"])
        self.assertEqual(plan["queueClass"], "REPOSITORY_ONLY")
        self.assertEqual(plan["directOwners"], [])
        self.assertEqual(plan["verificationOwners"], [])
        self.assertEqual(plan["scopeIds"], [])

    def test_dependency_graph_rejects_unknown_owner(self) -> None:
        content = """schema_version = 1
kind = "ordivon.repo-owner-dependency-contracts"
truth_role = "repository-boundary-policy-not-domain-authority"
[[seams]]
from_owner = "runtime"
to_owner = "missing"
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dependencies.toml"
            path.write_text(content, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unknown owner"):
                MODULE.load_dependency_graph(path=path)


if __name__ == "__main__":
    unittest.main()
