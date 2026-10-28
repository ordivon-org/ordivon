#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from itertools import combinations
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
    def test_all_native_owner_combinations_preserve_mandatory_queue_closure(self) -> None:
        """A finite consumer CDC bridge for existing R2.1 monotone-impact laws.

        The Lean ImpactReach/demand_monotone laws apply to qualified roots and
        edges, not arbitrary Python. Protect the actual CI-facing queue against
        omissions for every currently declared natural Owner and ordered pair.
        Future Owners extend this finite fixture without new registry metadata.
        This is source/selected-task evidence, never implementation refinement
        or installed effect acceptance.
        """
        repo = MODULE_PATH.parents[2]
        native_owners = MODULE.affected_owners.OWNERS
        self.assertTrue(native_owners)
        actual_paths: dict[str, str] = {}
        plans: dict[str, dict[str, object]] = {}
        for owner in native_owners:
            git_paths = subprocess.check_output(
                ["git", "ls-files", "-z", "--", owner.root],
                cwd=repo, timeout=20,
            ).split(b"\\0")
            candidates = [os.fsdecode(path) for path in git_paths if path]
            self.assertTrue(candidates, f"no real tracked source for {owner.name}")
            source = candidates[0]
            actual_paths[owner.name] = source
            plan = MODULE.build_plan(changed_files=[source])
            plans[owner.name] = plan
            self.assertIn(owner.name, plan["verificationOwners"])
            self.assertIn(owner.queue_task, plan["queueVerifyTasks"])
            with self.assertRaisesRegex(ValueError, "queue source impact"):
                MODULE.validate_queue_task_selection([], [], [source])
            MODULE.validate_queue_task_selection(
                plan["verificationOwners"], plan["queueVerifyTasks"], [source]
            )

        # All ordered two-Owner source changes preserve both closures.
        for left in native_owners:
            for right in native_owners:
                paths = [actual_paths[left.name], actual_paths[right.name]]
                plan = MODULE.build_plan(changed_files=paths)
                expected = (
                    set(plans[left.name]["queueVerifyTasks"])
                    | set(plans[right.name]["queueVerifyTasks"])
                )
                self.assertLessEqual(expected, set(plan["queueVerifyTasks"]))
                MODULE.validate_queue_task_selection(
                    plan["verificationOwners"], plan["queueVerifyTasks"], paths
                )

        # The separately real Formal task must survive any Owner change.
        for owner in native_owners:
            paths = [actual_paths[owner.name], "tools/formal/Proof.qnt"]
            plan = MODULE.build_plan(changed_files=paths)
            self.assertEqual(plan["queueVerifyTasks"].count("formal:verify"), 1)
            MODULE.validate_queue_task_selection(
                plan["verificationOwners"], plan["queueVerifyTasks"], paths
            )

        cross_cutting = ["tools/repo/owners.toml"]
        plan = MODULE.build_plan(changed_files=cross_cutting)
        self.assertEqual(set(plan["verificationOwners"]),
                         {owner.name for owner in native_owners})
        with self.assertRaisesRegex(ValueError, "queue source impact"):
            MODULE.validate_queue_task_selection([], [], cross_cutting)
        # Manual/scheduled complete verification has no scoped source delta.
        MODULE.validate_queue_task_selection(
            [owner.name for owner in native_owners],
            [owner.queue_task for owner in native_owners],
        )

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
    def test_phase2_temporal_git_frontier_composes_with_canonical_consumers(self) -> None:
        """Two Git cuts -> exact changed members -> mandatory native verifier.

        Source & task-selection contract only, NOT runtime effect or theorem.
        """
        root = MODULE_PATH.parents[2]
        def git(*args: str) -> str:
            return subprocess.check_output(
                ["git", "-C", str(root), "--no-replace-objects", *args],
                text=True, stderr=subprocess.PIPE
            ).strip()
        head = git("rev-parse", "HEAD")
        latest_formal = git(
            "log", "-1", "--format=%H", "HEAD", "--", "tools/formal/mise.toml"
        )
        base = git("rev-parse", latest_formal + "^")
        receipt = MODULE.build_qualified_temporal_impact(
            base=base, head=head, prefixes=["tools/formal/"]
        )
        self.assertEqual(receipt["sourceCuts"]["current"], head)
        self.assertIn("tools/formal/mise.toml", receipt["selectedChangedPaths"])
        self.assertEqual(receipt["queueVerifyTasks"], ["formal:verify"])
        self.assertFalse(receipt["proofReuseAdmissible"])
        self.assertEqual(
            receipt["verificationStanding"],
            "SCOPE_INCOMPLETE_NO_COMPLETE_QUEUE_ADMISSION",
        )
        coverage = receipt["gitDeltaCoverage"]
        self.assertFalse(coverage["allTrackedGitChangesObserved"])
        self.assertEqual(
            coverage["observedChangedPathCount"] +
            coverage["unobservedChangedPathCount"],
            coverage["exactChangedPathCount"],
        )
        self.assertGreater(coverage["unobservedChangedPathCount"], 0)
        self.assertLessEqual(len(coverage["unobservedChangedPathWitness"]), 8)
        self.assertEqual(receipt["runtimeCallStanding"], "UNKNOWN")
        self.assertEqual(receipt["installedEffectStanding"], "UNKNOWN")
        self.assertEqual(receipt["sourceConsumerEvidence"]["queueVerifyTasks"], ["formal:verify"])
        self.assertFalse(receipt["sourceConsumerEvidence"]["impactClosureAdmissible"])
        self.assertEqual(receipt["sourceConsumerEvidence"]["sourceCut"], head)
        args = [
            sys.executable, str(MODULE_PATH), "--base", base, "--head", head,
            "--impact-prefix", "tools/formal/"
        ]
        actual = __import__("json").loads(subprocess.check_output(args, text=True))
        self.assertEqual(actual["selectedChangedPaths"], receipt["selectedChangedPaths"])
        partial_queue = subprocess.run(
            [*args, "--format", "queue-tasks"],
            text=True, capture_output=True, check=False,
        )
        self.assertNotEqual(partial_queue.returncode, 0)
        self.assertEqual(partial_queue.stdout, "")
        self.assertIn("unobserved Git source changes", partial_queue.stderr)
        empty = MODULE.build_qualified_temporal_impact(
            base=base, head=head, prefixes=["tools/formal/not-a-real-subtree/"]
        )
        self.assertEqual(empty["queueVerifyTasks"], [])
        self.assertEqual(empty["sourceConsumerEvidence"]["changedSourceInputs"], [])
        self.assertEqual(empty["sourceConsumerEvidence"]["sourceCut"], head)
        self.assertFalse(empty["sourceConsumerEvidence"]["proofReuseAdmissible"])
        self.assertFalse(empty["proofReuseAdmissible"])
        self.assertEqual(empty["gitDeltaCoverage"]["observedChangedPathCount"], 0)
        self.assertGreater(empty["gitDeltaCoverage"]["unobservedChangedPathCount"], 0)
        self.assertFalse(empty["gitDeltaCoverage"]["allTrackedGitChangesObserved"])
        # Exact no-change interval is complete in Git SOURCE space only.
        # It is not evidence that current code/installation is correct.
        unchanged = MODULE.build_qualified_temporal_impact(
            base=head, head=head, prefixes=["tools/repo/"]
        )
        self.assertTrue(unchanged["gitDeltaCoverage"]["allTrackedGitChangesObserved"])
        self.assertEqual(unchanged["gitDeltaCoverage"]["exactChangedPathCount"], 0)
        self.assertEqual(unchanged["sourceConsumerEvidence"]["changedSourceInputs"], [])
        self.assertEqual(unchanged["sourceConsumerEvidence"]["sourceCut"], head)
        self.assertFalse(unchanged["proofReuseAdmissible"])
        for wrong in (
            dict(base=base, head=base, prefixes=["tools/formal/"]),
            dict(base=base, head=head, prefixes=["tools/formal/", "tools/formal/"]),
            dict(base=base, head=head, prefixes=["../unbounded/"]),
        ):
            with self.assertRaises(ValueError):
                MODULE.build_qualified_temporal_impact(**wrong)
        forged = subprocess.run(
            [*args, "--changed-file", "docs/README.md"],
            text=True, capture_output=True, check=False
        )
        self.assertNotEqual(forged.returncode, 0)
        self.assertIn("no competing", forged.stderr)

    def test_empty_temporal_change_still_rejects_dirty_producer_and_policy(self) -> None:
        """No Git delta never certifies a drifted live verification contract."""
        head = MODULE._git("rev-parse", "HEAD")
        root = MODULE_PATH.parents[2]
        for relative, expected_error in (
            ("tools/repo/owners.toml", "verification contract differs"),
            ("tools/repo/convergence_plan.py", "executed producer source differs"),
        ):
            source = root / relative
            original = source.read_bytes()
            try:
                source.write_bytes(original + b"\\n# synthetic sourcecut drift fixture\\n")
                with self.assertRaisesRegex(ValueError, expected_error):
                    MODULE.build_qualified_temporal_impact(
                        base=head, head=head, prefixes=["tools/repo/"]
                    )
            finally:
                source.write_bytes(original)

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
        with self.assertRaisesRegex(ValueError, "queue source impact|queue .*task|queue task selection"):
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
                with self.assertRaisesRegex(ValueError, "queue source impact|noncanonical source impact"):
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

    def test_queue_consumer_rejects_omitted_actual_change_impact(self) -> None:
        """Real queue validator must enforce changed-source impact, not just list consistency."""
        runtime = "services/runtime/crates/ordivon-runtime-core/src/lib.rs"
        changes = (
            ([runtime], [], []),
            ([runtime], ["runtime"], ["runtime:verify"]),
            (["tools/repo/owners.toml"], [], []),
            (["tools/repo/owners.toml"], ["runtime"], ["runtime:verify"]),
        )
        for paths, selected, tasks in changes:
            with self.subTest(paths=paths, selected=selected):
                with self.assertRaisesRegex(ValueError, "source impact"):
                    MODULE.validate_queue_task_selection(selected, tasks, paths)

        for paths in (
            [runtime],
            ["tools/repo/owners.toml"],
            ["tools/formal/Proof.qnt"],
            ["tools/formal/Proof.qnt", runtime],
            ["docs/architecture/EXAMPLE.md"],
        ):
            with self.subTest(accepted=paths):
                plan = MODULE.build_plan(changed_files=paths)
                MODULE.validate_queue_task_selection(
                    plan["verificationOwners"], plan["queueVerifyTasks"], paths
                )
        # Manual/schedule with no planned change remain governed by complete
        # canonical Owner->task consistency, not an invented empty source delta.
        all_owners = [item.name for item in MODULE.affected_owners.OWNERS]
        all_tasks = [item.queue_task for item in MODULE.affected_owners.OWNERS]
        MODULE.validate_queue_task_selection(all_owners, all_tasks)

    def test_every_real_single_and_pair_owner_source_change_rejects_queue_omissions(self) -> None:
        """R2.1 finite source-consumer closure: all 18 owner roots, every pair.

        This is a test of the actual native policy and tracked Git inputs,
        not a proof that unknown dynamic/installed consumers are complete.
        Extending the Owner universe deliberately requires requalifying this
        explicitly bounded one-/two-owner consumer closure.
        """
        root = MODULE_PATH.parents[2]
        tracked = subprocess.check_output(
            ["git", "--no-replace-objects", "ls-tree", "-r", "--name-only", "HEAD"],
            cwd=root, text=True,
        ).splitlines()
        samples = {}
        for owner in MODULE.affected_owners.OWNERS:
            real_paths = [path for path in tracked if path.startswith(owner.root)]
            self.assertTrue(real_paths, f"unmaterialized owner source: {owner.name}")
            code_paths = [
                path for path in real_paths
                if path.endswith((".rs", ".py", ".ts", ".go", ".json"))
                and "/test" not in path
            ]
            samples[owner.name] = (code_paths or real_paths)[0]
        self.assertEqual(len(samples), 18)
        self.assertEqual(len(samples), len(set(samples.values())))
        groups = [(name,) for name in samples] + list(combinations(samples, 2))
        self.assertEqual(len(groups), 18 + 153)
        checks = 0
        for group in groups:
            changed = [samples[name] for name in group]
            plan = MODULE.build_plan(changed_files=changed)
            owners = plan["verificationOwners"]
            tasks = plan["queueVerifyTasks"]
            self.assertTrue(tasks, f"no native task selected for real consumer {group}")
            with self.subTest(owner_group=group, case="exact-required"):
                MODULE.validate_queue_task_selection(owners, tasks, changed)
            checks += 1
            invalid = {
                "omit-first-task": (owners, tasks[1:]),
                "omit-all-consumers": ([], []),
                "add-unknown-task": (owners, tasks + ["forged:verify"]),
                "duplicate-task": (owners, tasks + [tasks[0]]),
                "omit-first-owner": (owners[1:], tasks),
            }
            if len(tasks) > 1:
                invalid["reorder"] = (owners, list(reversed(tasks)))
            for case, (selected, requested) in invalid.items():
                with self.subTest(owner_group=group, case=case):
                    with self.assertRaises(ValueError):
                        MODULE.validate_queue_task_selection(
                            selected, requested, changed
                        )
                checks += 1
        # 171 real source cohorts, 1191 exact positive/negative obligations
        # at the present 18-Owner source cut; no global coverage inference.
        self.assertEqual(checks, 1191)

    def test_root_and_formal_selection_reject_each_individual_missing_task(self) -> None:
        root_path = ["mise.toml"]
        root_plan = MODULE.build_plan(changed_files=root_path)
        all_tasks = root_plan["queueVerifyTasks"]
        # Current root policy can gain scoped Formal selection independently
        # of the 18-owner population. Derive the optional source obligation
        # instead of freezing a command-count implementation detail.
        formal_root = MODULE.affected_owners.requires_core_formal_verification(root_path)
        self.assertEqual(
            len(all_tasks), len(MODULE.affected_owners.OWNERS) + int(formal_root)
        )
        self.assertEqual(all_tasks.count("formal:verify"), int(formal_root))
        MODULE.validate_queue_task_selection(
            root_plan["verificationOwners"], all_tasks, root_path
        )
        for index in range(len(all_tasks)):
            with self.subTest(omitted_task=all_tasks[index]):
                with self.assertRaises(ValueError):
                    MODULE.validate_queue_task_selection(
                        root_plan["verificationOwners"],
                        all_tasks[:index] + all_tasks[index+1:],
                        root_path,
                    )
        changed = ["tools/formal/Proof.qnt"]
        formal = MODULE.build_plan(changed_files=changed)
        self.assertEqual(formal["queueVerifyTasks"], ["formal:verify"])
        MODULE.validate_queue_task_selection([], ["formal:verify"], changed)
        with self.assertRaises(ValueError):
            MODULE.validate_queue_task_selection([], [], changed)

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

    def test_selected_queue_tasks_must_resolve_in_current_root_mise_source(self) -> None:
        """An allowlisted queue task name is not enough if its runner disappears."""
        import unittest.mock
        import tomllib
        root = MODULE_PATH.parents[2]
        original = tomllib.loads((root / "mise.toml").read_text(encoding="utf-8"))
        declared = original["tasks"]
        expected = {o.queue_task for o in MODULE.affected_owners.OWNERS}
        expected.add("formal:verify")
        self.assertTrue(expected.issubset(declared.keys()))
        for name in expected:
            with self.subTest(working=name):
                self.assertTrue(declared[name].get("run") or declared[name].get("depends"))

        runtime_source = "services/runtime/crates/ordivon-runtime-core/src/lib.rs"
        formal_source = "tools/formal/RecursiveLegoRefinement.lean"

        def declared_task_manifest(task_names: list[str]) -> str:
            return "[tasks]\n" + "".join(
                f'[tasks."{task_name}"]\\nrun = "echo native task"\\n'
                for task_name in task_names
            ).replace("\\n", "\n")

        with tempfile.TemporaryDirectory() as directory:
            mock_file = Path(directory) / "mise.toml"
            for missing, changed in (
                ("runtime:verify", [runtime_source]),
                ("formal:verify", [formal_source]),
            ):
                plan = MODULE.build_plan(changed_files=changed)
                self.assertIn(missing, plan["queueVerifyTasks"])
                with self.subTest(missing=missing):
                    # Preserve every other CURRENT canonical consumer task,
                    # so a failure must be caused by the missing root runner.
                    still_available = [
                        task for task in plan["queueVerifyTasks"] if task != missing
                    ]
                    mock_file.write_text(
                        declared_task_manifest(still_available), encoding="utf-8"
                    )
                    with unittest.mock.patch.object(
                        MODULE, "ROOT_TASKS_PATH", mock_file, create=True
                    ):
                        with self.assertRaisesRegex(ValueError, "root mise runner"):
                            MODULE.validate_queue_task_selection(
                                plan["verificationOwners"],
                                plan["queueVerifyTasks"],
                                changed,
                            )
            for changed in ([runtime_source], [formal_source]):
                plan = MODULE.build_plan(changed_files=changed)
                mock_file.write_text(
                    declared_task_manifest(plan["queueVerifyTasks"]),
                    encoding="utf-8",
                )
                with unittest.mock.patch.object(
                    MODULE, "ROOT_TASKS_PATH", mock_file, create=True
                ):
                    MODULE.validate_queue_task_selection(
                        plan["verificationOwners"], plan["queueVerifyTasks"], changed
                    )

    def test_selected_queue_task_matches_native_mise_admission(self) -> None:
        """A truthy TOML field is not an executable task contract in real mise."""
        import unittest.mock

        changed = ["tools/formal/Proof.qnt"]
        cases = {
            "invalid-boolean-run": 'run = true\n',
            "invalid-integer-run": 'run = 42\n',
            "unknown-dependency": 'depends = ["missing:task"]\n',
            "empty-dependency": 'depends = [""]\n',
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task_path = root / "mise.toml"
            for name, body in cases.items():
                with self.subTest(name=name):
                    task_path.write_text(
                        '[tasks."formal:verify"]\n' + body, encoding="utf-8"
                    )
                    native = subprocess.run(
                        ["mise", "--cd", str(root), "tasks", "validate"],
                        capture_output=True, text=True, timeout=20,
                    )
                    self.assertNotEqual(native.returncode, 0)
                    with unittest.mock.patch.object(MODULE, "ROOT_TASKS_PATH", task_path):
                        with self.assertRaisesRegex(
                            ValueError, "native mise task validation"
                        ):
                            MODULE.validate_queue_task_selection(
                                [], ["formal:verify"], changed,
                            )

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
            (["composition", "runtime"], ["composition:verify", "runtime:verify"],
             ["services/runtime/crates/ordivon-runtime-core/src/lib.rs"], True),
            ([], [], ["services/runtime/crates/ordivon-runtime-core/src/lib.rs"], False),
            (["runtime"], ["runtime:verify"],
             ["services/runtime/crates/ordivon-runtime-core/src/lib.rs"], False),
            ([], [], ["tools/repo/owners.toml"], False),
            (["composition", "runtime"],
             ["composition:verify", "runtime:verify", "formal:verify"],
             ["services/runtime/crates/ordivon-runtime-core/src/lib.rs",
              "tools/formal/RecursiveLegoRefinement.lean"], True),
            ([], ["formal:verify"], ["docs/architecture/EXAMPLE.md"], False),
            ([], [], ["tools/formal/Proof.qnt"], False),
            (["runtime"], ["runtime:verify", "unexpected-task"],
             ["tools/formal/Proof.qnt"], False),
        )
        # Validate the *actual* GitHub inline consumer as well as the Python
        # producer for every tracked 18-Owner one-/two-owner source cohort.
        # This is still only a bounded source task contract, not runtime proof.
        git_paths = subprocess.check_output(
            ["git", "--no-replace-objects", "ls-tree", "-r", "--name-only", "HEAD"],
            cwd=root, text=True,
        ).splitlines()
        samples = {}
        for owner in MODULE.affected_owners.OWNERS:
            paths = [path for path in git_paths if path.startswith(owner.root)]
            self.assertTrue(paths)
            code_paths = [
                path for path in paths
                if path.endswith((".rs", ".py", ".ts", ".go", ".json"))
                and "/test" not in path
            ]
            samples[owner.name] = (code_paths or paths)[0]
        self.assertEqual(len(samples), 18)
        cohorts = [(name,) for name in samples] + list(combinations(samples, 2))
        self.assertEqual(len(cohorts), 171)
        original_cases = len(examples)
        for group in cohorts:
            changed = [samples[name] for name in group]
            selected = MODULE.build_plan(changed_files=changed)
            examples += (
                (selected["verificationOwners"], selected["queueVerifyTasks"], changed, True),
                ([], [], changed, False),
            )
        self.assertEqual(len(examples) - original_cases, 342)
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
