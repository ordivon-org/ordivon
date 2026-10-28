#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest import mock
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("convergence_plan.py")
SPEC = importlib.util.spec_from_file_location("convergence_plan", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ConvergencePlanTests(unittest.TestCase):
    def test_exact_git_replace_cannot_erase_formal_source_queue_or_spoof_tree(self) -> None:
        """LEGO 2.1 source identity must not follow mutable Git replacement refs.

        Run the actual native CLI with a disposable, independently constructed
        Git commit DAG. Do not touch the worktree's shared Git replacement refs.
        """
        with tempfile.TemporaryDirectory(prefix="ordivon-queue-git-replace-") as temp:
            repo = Path(temp)

            def git(*args: str) -> str:
                return subprocess.check_output(
                    ["git", "-C", str(repo), *args],
                    text=True, stderr=subprocess.PIPE,
                ).strip()

            git("init", "-q")
            git("config", "user.email", "formal-cut-fixture@example.invalid")
            git("config", "user.name", "Ordivon source-cut fixture")
            (repo / "tools/formal").mkdir(parents=True)
            (repo / "docs").mkdir()
            (repo / "tools/formal/Proof.qnt").write_text("version 1\\n")
            (repo / "docs/note.md").write_text("version 1\\n")
            git("add", ".")
            git("commit", "-qm", "base")
            base = git("rev-parse", "HEAD")

            (repo / "tools/formal/Proof.qnt").write_text("version 2\\n")
            git("add", ".")
            git("commit", "-qm", "real formal proof change")
            real = git("rev-parse", "HEAD")
            real_tree = git("--no-replace-objects", "rev-parse", real + "^{tree}")

            git("checkout", "--detach", "-q", base)
            (repo / "docs/note.md").write_text("version 2\\n")
            git("add", ".")
            git("commit", "-qm", "docs-only decoy")
            decoy = git("rev-parse", "HEAD")
            git("checkout", "--detach", "-q", real)
            git("replace", real, decoy)

            output = subprocess.check_output(
                [
                    sys.executable, str(MODULE_PATH),
                    "--base", base, "--head", real, "--format", "json",
                ],
                cwd=repo, text=True, stderr=subprocess.PIPE, timeout=30,
            )
            plan = __import__("json").loads(output)
            self.assertEqual(plan["headRevision"], real)
            self.assertEqual(plan["headTree"], real_tree)
            self.assertEqual(plan["changedPaths"], ["tools/formal/Proof.qnt"])
            self.assertEqual(plan["queueVerifyTasks"], ["formal:verify"])

    def test_git_graft_cannot_hide_required_formal_task_from_real_queue(self) -> None:
        """Exact Git SourceCut ancestors cannot be rewritten by local grafts."""
        with tempfile.TemporaryDirectory(prefix="ordivon-queue-git-graft-") as temp:
            repo = Path(temp)

            def git(*args: str) -> str:
                return subprocess.check_output(
                    ["git", "-C", str(repo), *args],
                    text=True, stderr=subprocess.PIPE,
                ).strip()

            git("init", "-q")
            git("config", "user.email", "formal-cut-fixture@example.invalid")
            git("config", "user.name", "Ordivon source-cut fixture")
            (repo / "tools/formal").mkdir(parents=True)
            (repo / "tools/formal/Proof.qnt").write_text("before\n")
            git("add", ".")
            git("commit", "-qm", "base")
            base = git("rev-parse", "HEAD")

            (repo / "tools/formal/Proof.qnt").write_text("after\n")
            git("add", ".")
            git("commit", "-qm", "real formal proof source delta")
            head = git("rev-parse", "HEAD")
            real_tree = git("--no-replace-objects", "rev-parse", head + "^{tree}")

            # Construct a different root with exactly the new head's tree.
            # Forging a common ancestor can make a three-dot Git diff empty
            # even with --no-replace-objects unless grafts are also disabled.
            graft_parent = git("commit-tree", real_tree, "-m", "false common ancestor")
            grafts = repo / ".git/info/grafts"
            grafts.write_text(
                base + " " + graft_parent + "\n"
                + head + " " + graft_parent + "\n"
            )

            output = subprocess.check_output(
                [
                    sys.executable, str(MODULE_PATH),
                    "--base", base, "--head", head, "--format", "json",
                ],
                cwd=repo, text=True, stderr=subprocess.PIPE, timeout=30,
            )
            plan = __import__("json").loads(output)
            self.assertEqual(plan["headRevision"], head)
            self.assertEqual(plan["headTree"], real_tree)
            self.assertEqual(plan["changedPaths"], ["tools/formal/Proof.qnt"])
            self.assertEqual(plan["queueVerifyTasks"], ["formal:verify"])

    def test_self_hosted_impact_explanation_binds_real_source_and_verification(self) -> None:
        source = "tools/repo/affected_owners.py"
        plan = MODULE.build_plan(changed_files=[source])
        explanation = MODULE.explain_source_impacts(plan, source_cut=MODULE._git("rev-parse", "HEAD"))
        self.assertEqual(explanation["sourceCut"], MODULE._git("rev-parse", "HEAD"))
        self.assertEqual(explanation["sourceTree"], MODULE._git("rev-parse", "HEAD^{tree}"))
        self.assertEqual(explanation["queueVerifyTasks"], plan["queueVerifyTasks"])
        self.assertEqual(explanation["verificationStanding"], "REQUIRED_NOT_EXECUTED_BY_PROJECTION")
        target = next(item for item in explanation["changedSourceInputs"] if item["path"] == source)
        self.assertTrue(target["sourceCellRef"].startswith("source-cell:sha256:"))
        self.assertTrue(target["gitSourceIdentity"].startswith(("100644:blob:", "100755:blob:")))
        self.assertTrue(target["candidateConsumers"])
        self.assertIn(
            "tools/repo/convergence_plan.py",
            {c["consumerPath"] for c in target["candidateConsumers"]},
        )
        self.assertTrue(all(
            c["relation"] == "STATIC_PYTHON_IMPORT_CANDIDATE_NOT_RUNTIME_CALL"
            and c["runtimeCallStanding"] == "UNKNOWN"
            for c in target["candidateConsumers"]
        ))
        self.assertFalse(explanation["impactClosureAdmissible"])
        self.assertFalse(explanation["proofReuseAdmissible"])

    def test_self_hosted_formal_source_impact_preserves_existing_real_task(self) -> None:
        plan = MODULE.build_plan(changed_files=["tools/formal/RecursiveLegoRefinement.lean"])
        explanation = MODULE.explain_source_impacts(
            plan, source_cut=MODULE._git("rev-parse", "HEAD")
        )
        self.assertEqual(explanation["queueVerifyTasks"], ["formal:verify"])
        self.assertEqual(explanation["verificationOwners"], [])
        self.assertEqual(explanation["unindexedChangedPaths"], [])
        self.assertEqual(explanation["changedSourceInputs"][0]["candidateConsumers"], [])
        self.assertEqual(explanation["nonPythonConsumerStanding"], "NOT_ANALYZED")

    def test_self_hosted_impact_rejects_mismatched_source_cut_and_forged_tasks(self) -> None:
        cut = MODULE._git("rev-parse", "HEAD")
        plan = MODULE.build_plan(changed_files=["tools/formal/verify.py"])
        pinned = {**plan, "headRevision": cut}
        with self.assertRaisesRegex(ValueError, "SourceCut mismatch"):
            MODULE.explain_source_impacts(pinned, source_cut="0" * 40)
        forged = {**plan, "queueVerifyTasks": []}
        with self.assertRaisesRegex(ValueError, "queue task selection"):
            MODULE.explain_source_impacts(forged, source_cut=cut)

    def test_self_hosted_root_task_change_composes_formal_and_owner_tasks(self) -> None:
        """Peer Formal root-entrypoint rule and source evidence compose in one call."""
        plan = MODULE.build_plan(changed_files=["mise.toml"])
        evidence = MODULE.explain_source_impacts(
            plan, source_cut=MODULE._git("rev-parse", "HEAD")
        )
        self.assertEqual(len(evidence["verificationOwners"]), 18)
        self.assertEqual(len(evidence["queueVerifyTasks"]), 19)
        self.assertEqual(evidence["queueVerifyTasks"].count("formal:verify"), 1)
        self.assertEqual(evidence["queueVerifyTasks"], plan["queueVerifyTasks"])
        self.assertEqual(
            evidence["changedSourceInputs"][0]["sourceStanding"],
            "EXACT_GIT_SOURCE_PRESENT",
        )
        self.assertFalse(evidence["proofReuseAdmissible"])

    def test_self_hosted_impact_rejects_forged_owner_selection_even_with_valid_tasks(self) -> None:
        """Never accept a caller-manufactured reduced queue as canonical impact."""
        source = "services/runtime/crates/ordivon-runtime-core/src/lib.rs"
        plan = MODULE.build_plan(changed_files=[source])
        self.assertEqual(plan["verificationOwners"], ["composition", "runtime"])
        cut = MODULE._git("rev-parse", "HEAD")
        for owners, tasks in (
            ([], []),
            (["runtime"], ["runtime:verify"]),
        ):
            with self.subTest(owners=owners, tasks=tasks):
                forged = {**plan, "verificationOwners": owners, "queueVerifyTasks": tasks}
                with self.assertRaisesRegex(ValueError, "noncanonical source impact"):
                    MODULE.explain_source_impacts(forged, source_cut=cut)

    def test_self_hosted_impact_rejects_uncommitted_executed_producer_bytes(self) -> None:
        """A source-bound explanation must not hide mutable producer code drift."""
        plan = MODULE.build_plan(changed_files=["tools/formal/verify.py"])
        cut = MODULE._git("rev-parse", "HEAD")
        root = MODULE_PATH.parents[2]
        for relative in (
            "tools/repo/convergence_plan.py",
            "tools/repo/affected_owners.py",
            "tools/repo/exhaustive_coverage.py",
        ):
            with self.subTest(producer=relative):
                file = root / relative
                exact = file.read_bytes()
                try:
                    file.write_bytes(exact + b"\n# drift injected only for source-qualification test\n")
                    with self.assertRaisesRegex(ValueError, "executed producer source"):
                        MODULE.explain_source_impacts(plan, source_cut=cut)
                finally:
                    file.write_bytes(exact)

    def test_self_hosted_impact_rejects_uncommitted_root_task_manifest(self) -> None:
        """Chosen task commands are consumed from root mise, not just Owner names."""
        plan = MODULE.build_plan(
            changed_files=["tools/formal/RecursiveLegoRefinement.lean"]
        )
        cut = MODULE._git("rev-parse", "HEAD")
        root_task = MODULE_PATH.parents[2] / "mise.toml"
        exact = root_task.read_bytes()
        try:
            root_task.write_bytes(
                exact + b"\n# injected uncommitted task source drift\n"
            )
            with self.assertRaisesRegex(ValueError, "verification contract differs"):
                MODULE.explain_source_impacts(plan, source_cut=cut)
        finally:
            root_task.write_bytes(exact)

    def test_self_hosted_impact_refuses_stale_native_contract_and_old_cut(self) -> None:
        cut = MODULE._git("rev-parse", "HEAD")
        plan = MODULE.build_plan(changed_files=["tools/formal/verify.py"])
        with self.assertRaisesRegex(ValueError, "SourceCut mismatch"):
            MODULE.explain_source_impacts(
                plan, source_cut=MODULE._git("rev-parse", "HEAD^")
            )
        with tempfile.TemporaryDirectory() as folder:
            shadow = Path(folder) / "dependency_contracts.toml"
            shadow.write_text("schema_version = 1\n", encoding="utf-8")
            with mock.patch.object(MODULE, "DEPENDENCY_PATH", shadow):
                with self.assertRaisesRegex(ValueError, "outside active Git"):
                    MODULE.explain_source_impacts(plan, source_cut=cut)

    def test_self_hosted_impact_cli_returns_same_bounded_contract(self) -> None:
        output = subprocess.check_output([
            sys.executable, str(MODULE_PATH),
            "--changed-file", "tools/repo/affected_owners.py",
            "--explain-impacts",
        ], cwd=MODULE_PATH.parents[2], text=True, timeout=30)
        payload = __import__("json").loads(output)
        self.assertEqual(
            payload["changedSourceInputs"][0]["path"], "tools/repo/affected_owners.py"
        )
        self.assertEqual(payload["sourceCut"], MODULE._git("rev-parse", "HEAD"))
        self.assertFalse(payload["impactClosureAdmissible"])
        self.assertGreaterEqual(payload["staticPythonCandidateCount"], 1)

    def test_self_hosted_impact_does_not_silently_claim_deleted_or_missing_source(self) -> None:
        plan = MODULE.build_plan(changed_files=["docs/architecture/definitely-absent.md"])
        result = MODULE.explain_source_impacts(
            plan, source_cut=MODULE._git("rev-parse", "HEAD")
        )
        self.assertEqual(
            result["unindexedChangedPaths"], ["docs/architecture/definitely-absent.md"]
        )
        self.assertEqual(result["changedSourceInputs"][0]["sourceStanding"],
                         "NOT_IN_SOURCE_CUT_OR_DELETED")
        self.assertFalse(result["impactClosureAdmissible"])

    def test_runtime_change_stays_in_isolated_owner_component(self) -> None:
        plan = MODULE.build_plan(
            changed_files=["services/runtime/crates/ordivon-runtime-core/src/lib.rs"]
        )
        self.assertEqual(plan["directOwners"], ["runtime"])
        # One test-only Runtime trace consumer must not merge the entire
        # security/harness/web component into Runtime's business closure.
        self.assertEqual(plan["verificationOwners"], ["composition", "runtime"])
        self.assertEqual(plan["taskLocalTestConsumers"], ["composition"])
        self.assertEqual(plan["verifyTasks"], ["composition:verify", "runtime:verify"])
        self.assertEqual(plan["queueVerifyTasks"], ["composition:verify", "runtime:verify"])
        self.assertEqual(plan["scopeIds"], ["owner-component:runtime"])
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

    def test_formal_task_definition_change_rechecks_native_verifier(self) -> None:
        plan = MODULE.build_plan(changed_files=["mise.toml"])
        self.assertIn("formal:verify", plan["verifyTasks"])
        self.assertEqual(plan["queueVerifyTasks"][-1], "formal:verify")
        MODULE.validate_queue_task_selection(
            list(plan["verificationOwners"]),
            list(plan["queueVerifyTasks"]),
            list(plan["changedPaths"]),
        )
        # This is the real command-line queue contract, not a invented
        # substitute for the native formal toolchain.
        result = subprocess.check_output([
            sys.executable, str(MODULE_PATH), "--changed-file", "mise.toml",
            "--format", "queue-tasks",
        ], text=True)
        self.assertEqual(result.splitlines()[-1], "formal:verify")

    def test_formal_source_change_queues_existing_formal_verifier_without_owner(self) -> None:
        """Mathematical source changes need the real formal task, not just REPOSITORY_ONLY."""
        for path in (
            "tools/formal/RecursiveLegoRefinement.lean",
            "tools/formal/Proof.qnt",
            "tools/formal/verify.py",
        ):
            plan = MODULE.build_plan(changed_files=[path])
            self.assertEqual(plan["queueClass"], "REPOSITORY_ONLY")
            self.assertEqual(plan["directOwners"], [])
            self.assertEqual(plan["verificationOwners"], [])
            self.assertEqual(plan["verifyTasks"], ["formal:verify"])
            self.assertEqual(plan["queueVerifyTasks"], ["formal:verify"])

        output = subprocess.check_output([
            sys.executable, str(MODULE_PATH),
            "--changed-file", "tools/formal/RecursiveLegoRefinement.lean",
            "--format", "queue-tasks",
        ], text=True)
        self.assertEqual(output.strip(), "formal:verify")

    def test_formal_source_change_composes_with_real_owner_verification(self) -> None:
        plan = MODULE.build_plan(changed_files=[
            "tools/formal/RecursiveLegoRefinement.lean",
            "services/runtime/crates/ordivon-runtime-core/src/lib.rs",
        ])
        self.assertEqual(plan["queueClass"], "SCOPED")
        self.assertEqual(plan["verificationOwners"], ["composition", "runtime"])
        self.assertEqual(
            plan["queueVerifyTasks"],
            ["composition:verify", "runtime:verify", "formal:verify"],
        )
        self.assertEqual(plan["scopeIds"], ["owner-component:runtime"])

    def test_repository_docs_do_not_enqueue_formal_tools(self) -> None:
        plan = MODULE.build_plan(changed_files=["docs/architecture/EXAMPLE.md"])
        self.assertEqual(plan["queueVerifyTasks"], [])
        self.assertEqual(plan["verifyTasks"], [])

    def test_formal_source_extra_task_is_admitted_by_real_queue_contract(self) -> None:
        MODULE.validate_queue_task_selection(
            [], ["formal:verify"],
            ["tools/formal/RecursiveLegoRefinement.lean"],
        )
        MODULE.validate_queue_task_selection(
            ["composition", "runtime"],
            ["composition:verify", "runtime:verify", "formal:verify"],
            ["services/runtime/crates/ordivon-runtime-core/src/lib.rs",
             "tools/formal/Proof.qnt"],
        )

    def test_formal_source_task_queue_validation_denies_missing_or_forged_tasks(self) -> None:
        for owners, requested, changed in (
            ([], [], ["tools/formal/Proof.qnt"]),
            ([], ["formal:verify"], ["docs/architecture/EXAMPLE.md"]),
            ([], ["formal:verify", "formal:verify"], ["tools/formal/Proof.qnt"]),
            ([], ["runtime:verify"], ["tools/formal/Proof.qnt"]),
            (["runtime"], ["formal:verify"], ["tools/formal/Proof.qnt"]),
            (["runtime", "runtime"], ["runtime:verify", "runtime:verify"], []),
            (["made-up-owner"], ["formal:verify"], ["tools/formal/Proof.qnt"]),
        ):
            with self.subTest(owners=owners, requested=requested, changed=changed):
                with self.assertRaises(ValueError):
                    MODULE.validate_queue_task_selection(owners, requested, changed)

    def test_github_queue_uses_same_strict_formal_source_task_validation(self) -> None:
        workflow = (MODULE_PATH.parents[2] / ".github/workflows/ci.yml").read_text()
        self.assertIn("convergence_plan.validate_queue_task_selection(", workflow)
        self.assertIn("ordivon-convergence-plan.json", workflow)
        self.assertIn('mise run "$task"', workflow)

    def test_real_github_queue_inline_validator_rejects_forged_formal_tasks(self) -> None:
        """Execute the exact inline Python consumer, not a duplicate example."""
        root = MODULE_PATH.parents[2]
        workflow = (root / ".github/workflows/ci.yml").read_text()
        marker = (
            '          python3 - "$owners_file" "$tasks_file" '
            '"$RUNNER_TEMP/ordivon-convergence-plan.json" <<' + "'PY'"
        )
        self.assertEqual(workflow.count(marker), 1)
        body = workflow.split(marker, 1)[1].split("          PY", 1)[0]
        code = "\n".join(line[10:] for line in body.splitlines() if line.strip())
        self.assertIn("convergence_plan.validate_queue_task_selection(", code)
        self.assertNotIn(
            "Selected verification owners and executable tasks disagree", workflow
        )
        examples = (
            ([], ["formal:verify"], ["tools/formal/Proof.qnt"], True),
            (["runtime"], ["runtime:verify"],
             ["services/runtime/crates/ordivon-runtime-core/src/lib.rs"], True),
            (["composition", "runtime"],
             ["composition:verify", "runtime:verify", "formal:verify"],
             ["services/runtime/crates/ordivon-runtime-core/src/lib.rs",
              "tools/formal/RecursiveLegoRefinement.lean"], True),
            ([], ["formal:verify"], ["docs/architecture/EXAMPLE.md"], False),
            ([], [], ["tools/formal/Proof.qnt"], False),
            (["runtime"], ["runtime:verify", "unexpected-task"],
             ["tools/formal/Proof.qnt"], False),
        )
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            owners_path = folder / "owners.txt"
            tasks_path = folder / "tasks.txt"
            plan_path = folder / "plan.json"
            for owners, tasks, changed, accepted in examples:
                with self.subTest(owners=owners, tasks=tasks, changed=changed):
                    owners_path.write_text("\n".join(owners) + "\n")
                    tasks_path.write_text("\n".join(tasks) + "\n")
                    plan_path.write_text(__import__("json").dumps({
                        "changedPaths": changed,
                    }))
                    result = subprocess.run(
                        [sys.executable, "-c", code,
                         str(owners_path), str(tasks_path), str(plan_path)],
                        cwd=root, capture_output=True, text=True, timeout=20,
                    )
                    self.assertEqual(
                        result.returncode == 0, accepted,
                        result.stdout + result.stderr,
                    )

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
        # The direct test witness is selected without merging the operational
        # composition/harness/security/web owner component into Runtime.
        self.assertEqual(runtime["verificationOwners"], ["composition", "runtime"])
        self.assertEqual(runtime["taskLocalTestConsumers"], ["composition"])

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

    def test_test_only_runtime_source_contract_cannot_be_widened_to_wildcard(self) -> None:
        policy = MODULE.DEPENDENCY_PATH.read_text(encoding="utf-8")
        mutations = [
            (
                'source_glob = "packages/composition/tests/test_verification_obligation_r1.py"',
                'source_glob = "packages/composition/**"',
            ),
            (
                'allowed_fragment = "services/runtime/formal/RuntimeDispatchR1.trace-r1.json"',
                'allowed_fragment = "services/runtime/formal/unqualified.json"',
            ),
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dependency_contracts.toml"
            for original, widened in mutations:
                self.assertIn(original, policy)
                path.write_text(policy.replace(original, widened), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "unapproved test-only source contract"):
                    MODULE.load_dependency_graph(path=path)


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
