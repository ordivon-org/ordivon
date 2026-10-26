#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import textwrap
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
        self.assertEqual(plan["queueVerifyTasks"], ["runtime:verify"])
        self.assertEqual(plan["queueClass"], "SCOPED")
        self.assertEqual(
            plan["independenceClaim"],
            "NOT_ESTABLISHED_BY_THIS_PROJECTION",
        )

    def test_next_queue_projection_uses_full_portable_verification(self) -> None:
        plan = MODULE.build_plan(changed_files=["meta/next/README.md"])
        self.assertIn("next:verify", plan["verifyTasks"])
        self.assertIn("next:verify", plan["queueVerifyTasks"])

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
        self.assertIn("artifact:verify", plan["verifyTasks"])
        self.assertIn("artifact:queue", plan["queueVerifyTasks"])

    def test_security_change_expands_to_harness_and_web_component(self) -> None:
        plan = MODULE.build_plan(changed_files=["platform/security/README.md"])
        self.assertEqual(
            plan["verificationOwners"],
            ["composition", "harness", "next", "security", "skills", "web"],
        )
        self.assertIn("harness:verify", plan["verifyTasks"])
        self.assertIn("harness:queue", plan["queueVerifyTasks"])

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

    def test_unregistered_executable_path_refuses_to_skip_consumer_verification(self) -> None:
        with self.assertRaisesRegex(ValueError, "unregistered owner path"):
            MODULE.build_plan(changed_files=["services/new-owner/src/main.py"])

    def test_repository_only_change_does_not_invent_domain_impact(self) -> None:
        plan = MODULE.build_plan(changed_files=["docs/architecture/EXAMPLE.md"])
        self.assertEqual(plan["queueClass"], "REPOSITORY_ONLY")
        self.assertEqual(plan["directOwners"], [])
        self.assertEqual(plan["verificationOwners"], [])
        self.assertEqual(plan["scopeIds"], [])

    def test_explicit_owner_universe_is_used_for_direct_selection(self) -> None:
        # Scoped owner sets must not leak global owner identities into plans.
        scoped_owner = MODULE.affected_owners.Owner(
            name="scoped-runtime",
            root="services/runtime/",
            task="scoped-runtime:verify",
            queue_task="scoped-runtime:verify",
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dependencies.toml"
            path.write_text(
                'schema_version = 1\n'
                'truth_role = "repository-boundary-policy-not-domain-authority"\n',
                encoding="utf-8",
            )
            plan = MODULE.build_plan(
                changed_files=["services/runtime/crates/ordivon-runtime-core/src/lib.rs"],
                owners=(scoped_owner,),
                dependency_path=path,
            )
            self.assertEqual(plan["directOwners"], ["scoped-runtime"])
            self.assertEqual(plan["verificationOwners"], ["scoped-runtime"])
            self.assertEqual(plan["verifyTasks"], ["scoped-runtime:verify"])
            cross_cutting = MODULE.build_plan(
                changed_files=["tools/repo/owners.toml"],
                owners=(scoped_owner,),
                dependency_path=path,
            )
            self.assertEqual(cross_cutting["queueClass"], "CROSS_CUTTING")
            self.assertEqual(cross_cutting["verificationOwners"], ["scoped-runtime"])

    def test_pinned_upstream_formal_tool_is_not_a_runtime_business_owner_dependency(self) -> None:
        """A public mathematical tool may be shared without merging owner scopes."""
        graph = MODULE.load_dependency_graph()
        self.assertNotIn("runtime", graph["composition"])
        self.assertNotIn("composition", graph["runtime"])
        self.assertNotIn("runtime", graph["harness"])
        self.assertNotIn("harness", graph["runtime"])
        # Existing public code/data dependencies must still propagate.
        self.assertIn("composition", graph["next"])
        runtime = MODULE.build_plan(changed_files=["services/runtime/crates/ordivon-runtime-core/src/lib.rs"])
        self.assertEqual(runtime["verificationOwners"], ["runtime"])

    def test_formal_toolchain_exception_rejects_unapproved_consumer_paths(self) -> None:
        """The tool-only exemption is an exact named file, not owner authority."""
        policy = MODULE.DEPENDENCY_PATH.read_text(encoding="utf-8")
        known = 'source_glob = "services/harness/mise.toml"'
        assert known in policy
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dependency_contracts.toml"
            path.write_text(
                policy.replace(
                    known,
                    'source_glob = "services/harness/src/ordivon_harness/standalone.py"',
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "unapproved upstream toolchain-only seam"):
                MODULE.load_dependency_graph(path=path)

    def test_pinned_git_source_fixture_does_not_add_live_owner_edge(self) -> None:
        """A test's immutable source fixture is provenance, not a live consumer."""
        graph = MODULE.load_dependency_graph()
        self.assertNotIn("runtime", graph["composition"])
        policy = MODULE.DEPENDENCY_PATH.read_text(encoding="utf-8")
        exact_kind = 'kind = "TEST_ONLY_PINNED_SOURCE_FIXTURE"'
        self.assertEqual(policy.count(exact_kind), 1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dependency_contracts.toml"
            path.write_text(
                policy.replace(
                    'allowed_fragment = "services/runtime/formal/RuntimeDispatchR1.trace-r1.json"',
                    'allowed_fragment = "services/runtime/formal/unqualified.json"',
                ), encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "unapproved immutable-Git"):
                MODULE.load_dependency_graph(path=path)
            # Reclassifying the same path as a live test dependency changes
            # the verification closure, rather than silently granting a skip.
            path.write_text(
                policy.replace(exact_kind, 'kind = "TEST_ONLY_SOURCE_CONTRACT"'),
                encoding="utf-8",
            )
            live = MODULE.load_dependency_graph(path=path)
            self.assertIn("runtime", live["composition"])

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


class OwnerVerificationExecutionTests(unittest.TestCase):
    @staticmethod
    def actual_owner_runner() -> str:
        # Execute the real GitHub workflow's shell, never a copied imitation.
        workflow = (MODULE_PATH.parents[2] / ".github/workflows/ci.yml").read_text(
            encoding="utf-8"
        )
        section = workflow.split("      - name: Verify affected owners\n", 1)[1]
        section = section.split("      - name: Runtime supply-chain policy\n", 1)[0]
        return textwrap.dedent(section.split("        run: |\n", 1)[1]).rstrip()

    @staticmethod
    def verify_tasks(tasks: str) -> tuple[subprocess.CompletedProcess[str], list[str]]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ordivon-affected-tasks.txt").write_text(tasks, encoding="utf-8")
            fake = root / "mise"
            fake.write_text(
                '#!/bin/sh\n'
                'printf "%s\\n" "$2" >> "$RUNNER_TEMP/called"\n'
                'cat >/dev/null\n'
                'if [ "$2" = "fail:verify" ]; then exit 29; fi\n',
                encoding="utf-8",
            )
            fake.chmod(0o755)
            proc = subprocess.run(
                ["/bin/bash", "-c", OwnerVerificationExecutionTests.actual_owner_runner()],
                cwd=MODULE_PATH.parents[2],
                env={
                    **os.environ,
                    "PATH": f"{root}:{os.environ['PATH']}",
                    "RUNNER_TEMP": str(root),
                },
                capture_output=True,
                text=True,
                timeout=15,
            )
            called = (
                (root / "called").read_text(encoding="utf-8").splitlines()
                if (root / "called").exists()
                else []
            )
            return proc, called

    def test_earlier_owner_consuming_stdin_cannot_skip_failing_next_owner(self) -> None:
        proc, called = self.verify_tasks("first:verify\nfail:verify\n")
        self.assertEqual(proc.returncode, 29, proc.stdout + proc.stderr)
        self.assertEqual(called, ["first:verify", "fail:verify"])

    def test_final_task_without_newline_must_not_be_skipped(self) -> None:
        proc, called = self.verify_tasks("first:verify\nfail:verify")
        self.assertEqual(proc.returncode, 29, proc.stdout + proc.stderr)
        self.assertEqual(called, ["first:verify", "fail:verify"])

class OwnerSelectorFailClosedRegression(unittest.TestCase):
    """Run the actual protected GitHub Actions shell, not a Python stand-in."""

    @staticmethod
    def selection_shell():
        import textwrap
        path = Path(__file__).resolve().parents[2] / ".github/workflows/ci.yml"
        workflow = path.read_text(encoding="utf-8")
        start = workflow.index("      - name: Select affected owners\n")
        end = workflow.index("      - name: Verify affected owners\n", start)
        section = workflow[start:end]
        assert section.count("        run: |\n") == 1
        return textwrap.dedent(section.split("        run: |\n", 1)[1])

    def run_selection(self, event, program):
        import os
        import subprocess
        with tempfile.TemporaryDirectory() as scratch:
            folder = Path(scratch)
            fake = folder / "python3"
            fake.write_text("#!/bin/sh\n" + program, encoding="utf-8")
            fake.chmod(0o755)
            env = {
                **os.environ,
                "PATH": str(folder) + os.pathsep + os.environ["PATH"],
                "EVENT_NAME": event,
                "PR_BASE": "a" * 40,
                "PR_HEAD": "b" * 40,
                "RUNNER_TEMP": str(folder),
                "GITHUB_OUTPUT": str(folder / "output"),
                "GITHUB_STEP_SUMMARY": str(folder / "summary"),
            }
            return subprocess.run(
                ["/usr/bin/bash", "-c", self.selection_shell()],
                cwd=Path(__file__).resolve().parents[2],
                env=env,
                capture_output=True,
                text=True,
                timeout=12,
            )

    def test_failing_owner_selector_never_becomes_empty_green_scope(self):
        stub = (
            'if [ "$1" = "tools/repo/convergence_plan.py" ]; then\n'
            '  echo \'{"verificationOwners":["runtime"],"queueVerifyTasks":["runtime:verify"]}\'\n'
            '  exit 0\n'
            'fi\n'
            'exit 29\n'
        )
        for event in ("workflow_dispatch", "pull_request"):
            with self.subTest(event=event):
                outcome = self.run_selection(event, stub)
                self.assertNotEqual(outcome.returncode, 0, outcome.stdout+outcome.stderr)

    def test_selected_owner_without_executable_queue_task_is_rejected(self):
        stub = (
            'if [ "$1" = "tools/repo/convergence_plan.py" ]; then\n'
            '  echo \'{"verificationOwners":["runtime"],"queueVerifyTasks":[]}\'\n'
            '  exit 0\n'
            'fi\n'
            'exec /usr/bin/python3 "$@"\n'
        )
        result = self.run_selection("pull_request", stub)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
