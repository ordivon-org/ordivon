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


    def test_self_bootstrap_source_delta_selects_exact_real_verification_consumers(self) -> None:
        """Phase1→Phase2: source delta LEGO composes with native task selector.

        Two immutable Git cuts → exact changed source refs → bounded consumer
        tasks. A task recommendation is NOT proof execution or admission.
        """
        import source_history_legos

        with tempfile.TemporaryDirectory(prefix="ordivon-self-bootstrap-") as temp:
            repo = Path(temp)
            def git(*args: str) -> str:
                return subprocess.check_output(
                    ["git", "-c", "maintenance.auto=false", "-C", str(repo), *args],
                    text=True, stderr=subprocess.PIPE,
                ).strip()
            git("init", "-q", "-b", "main")
            git("config", "user.name", "Ordivon Self Bootstrap Fixture")
            git("config", "user.email", "test@invalid.example")
            formal = repo / "tools/formal/Proof.qnt"
            runtime = repo / "services/runtime/crates/runtime.rs"
            docs = repo / "docs/README.md"
            for path, data in (
                (formal, "module Proof { val invariant = true }\\n"),
                (runtime, "fn invariant() -> bool { true }\\n"),
                (docs, "example\\n"),
            ):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(data)
            git("add", ".")
            git("commit", "-qm", "baseline source consumers")
            before = git("rev-parse", "HEAD")

            formal.write_text("module Proof { val invariant = false }\\n")
            runtime.write_text("fn invariant() -> bool { false }\\n")
            git("add", ".")
            git("commit", "-qm", "change proof and its Runtime implementation")
            after = git("rev-parse", "HEAD")

            formal_delta = source_history_legos.source_membership_delta(
                repo, before, after, "tools/formal/"
            )
            runtime_delta = source_history_legos.source_membership_delta(
                repo, before, after, "services/runtime/"
            )
            self.assertEqual(formal_delta["changedValuePaths"], ["tools/formal/Proof.qnt"])
            self.assertEqual(runtime_delta["changedValuePaths"], [
                "services/runtime/crates/runtime.rs"
            ])
            self.assertFalse(formal_delta["proofReuseAdmissible"])
            self.assertFalse(runtime_delta["proofReuseAdmissible"])
            changed = sorted(set(
                formal_delta["changedValuePaths"] + runtime_delta["changedValuePaths"]
            ))
            plan = MODULE.build_plan(changed_files=changed)
            self.assertEqual(plan["directOwners"], ["runtime"])
            self.assertEqual(plan["queueVerifyTasks"], [
                "composition:verify", "runtime:verify", "formal:verify"
            ])
            MODULE.validate_queue_task_selection(
                plan["verificationOwners"], plan["queueVerifyTasks"], changed
            )
            with self.assertRaisesRegex(ValueError, "canonical owner tasks"):
                MODULE.validate_queue_task_selection(
                    plan["verificationOwners"], plan["queueVerifyTasks"][:-1], changed
                )
            with self.assertRaisesRegex(ValueError, "unknown"):
                MODULE.validate_queue_task_selection(
                    ["fictional"], plan["queueVerifyTasks"], changed
                )

            docs.write_text("example changed, no Runtime or Formal source delta\\n")
            git("add", ".")
            git("commit", "-qm", "unrelated docs")
            latest = git("rev-parse", "HEAD")
            undisturbed = source_history_legos.compact_source_impact(
                source_history_legos.source_membership_delta(
                    repo, after, latest, "tools/formal/"
                )
            )
            self.assertEqual(undisturbed["sourceDisposition"], "SOURCE_SCOPE_UNCHANGED")
            self.assertFalse(undisturbed["proofReuseAdmissible"])
            self.assertIn(
                "formal_evidence_and_proof_checker_assumptions",
                undisturbed["missingQualification"],
            )
            docs_plan = MODULE.build_plan(changed_files=["docs/README.md"])
            self.assertEqual(docs_plan["queueVerifyTasks"], [])

            new_proof = repo / "tools/formal/NewInvariant.lean"
            new_proof.write_text("theorem safe : True := True.intro\\n")
            git("add", ".")
            git("commit", "-qm", "new proof namespace member")
            with_member = git("rev-parse", "HEAD")
            member_delta = source_history_legos.source_membership_delta(
                repo, latest, with_member, "tools/formal/"
            )
            self.assertEqual(member_delta["addedPaths"], [
                "tools/formal/NewInvariant.lean"
            ])
            self.assertTrue(member_delta["membershipChanged"])
            self.assertIn(member_delta["membershipRef"], member_delta["changedRefs"])
            self.assertEqual(
                MODULE.build_plan(changed_files=member_delta["addedPaths"])[
                    "queueVerifyTasks"
                ],
                ["formal:verify"],
            )


    def test_first_party_scoped_git_source_to_verification_cli_real_main(self) -> None:
        """One callable Phase2 circuit: native source history -> selected tasks.

        The current HEAD may evolve, but the most recent committed Formal
        source edit gives an immutable ancestor witness in this same Git DAG.
        """
        repo = Path(__file__).resolve().parents[2]
        def git(*args: str) -> str:
            return subprocess.check_output(
                ["git", "--no-replace-objects", "-C", str(repo), *args],
                text=True, stderr=subprocess.PIPE,
            ).strip()
        head = git("rev-parse", "HEAD")
        latest_formal = git("log", "-1", "--format=%H", "HEAD", "--",
                            "tools/formal/mise.toml")
        self.assertTrue(latest_formal)
        before = git("rev-parse", latest_formal + "^")
        plan = MODULE.build_scoped_source_impact_plan(
            base=before, head=head, prefixes=["tools/formal/"]
        )
        self.assertEqual(plan["kind"],
                         "ordivon.phase2.self-bootstrap-source-verification-selection")
        self.assertEqual(plan["observedPrefixes"], ["tools/formal/"])
        self.assertEqual(plan["sourceCuts"]["current"], head)
        self.assertIn("tools/formal/mise.toml", plan["selectedChangedPaths"])
        self.assertEqual(plan["queueVerifyTasks"], ["formal:verify"])
        self.assertEqual(plan["verifyTasks"], ["formal:verify"])
        self.assertEqual(plan["verificationPlan"]["directOwners"], [])
        self.assertEqual(plan["verificationStanding"],
                         "TASK_SELECTION_ONLY_ACTUAL_RUN_PENDING")
        self.assertFalse(plan["proofReuseAdmissible"])
        self.assertEqual(plan["uninspectedSourceAndDynamicConsumers"], "UNKNOWN")
        static = plan["staticConsumerImpact"]
        self.assertIsNotNone(static)
        self.assertEqual(static["mandatoryQueueVerifyTasks"], ["formal:verify"])
        self.assertEqual(static["candidateVerifyTasks"], ["formal:verify"])
        self.assertEqual(static["runtimeCallStanding"], "UNKNOWN")
        self.assertFalse(static["impactClosureEstablished"])
        self.assertFalse(static["deletionAuthorized"])
        cli = [sys.executable, str(MODULE_PATH), "--base", before,
               "--head", head, "--impact-prefix", "tools/formal/"]
        self.assertEqual(
            subprocess.check_output([*cli, "--format", "queue-tasks"], text=True).strip(),
            "formal:verify",
        )
        self.assertEqual(
            subprocess.check_output([*cli, "--format", "scopes"], text=True).strip(),
            "",
        )
        projected = __import__("json").loads(subprocess.check_output(cli, text=True))
        self.assertEqual(projected["queueVerifyTasks"], ["formal:verify"])

        # A namespace without observed changes must not silently request a
        # full-repository plan or pretend that its neighbors were unchanged.
        unchanged = MODULE.build_scoped_source_impact_plan(
            base=before, head=head, prefixes=["tools/formal/not-an-existing-subtree/"]
        )
        self.assertIsNone(unchanged["verificationPlan"])
        self.assertEqual(unchanged["queueVerifyTasks"], [])
        self.assertFalse(unchanged["proofReuseAdmissible"])

        for kwargs, match in (
            ({"base": before, "head": before, "prefixes": ["tools/formal/"]},
             "current Git HEAD"),
            ({"base": before, "head": head,
              "prefixes": ["tools/formal/", "tools/formal/"]},
             "distinct exact"),
            ({"base": before, "head": head, "prefixes": ["../unscoped/"]},
             "canonical"),
        ):
            with self.assertRaisesRegex(ValueError, match):
                MODULE.build_scoped_source_impact_plan(**kwargs)
        forged = subprocess.run(
            [*cli, "--changed-file", "docs/architecture/EXAMPLE.md"],
            text=True, capture_output=True, check=False,
        )
        self.assertNotEqual(forged.returncode, 0)
        self.assertIn("no --changed-file", forged.stderr)

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

    def test_phase2_bootstrap_reuses_actual_c04_to_c06_source_consumer(self) -> None:
        """Exact Git import -> candidate consumer -> existing Composition verify."""
        import json

        cut = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
        provider = (
            "packages/composition/src/ordivon_composition/"
            "verification_obligation_r1.py"
        )
        consumer = (
            "packages/composition/src/ordivon_composition/"
            "effect_reconciliation_r1.py"
        )
        plan = MODULE.build_plan(changed_files=[provider])
        projection = MODULE.explain_source_impact(
            source_cut=cut, changed_paths=plan["changedPaths"], base_plan=plan
        )
        self.assertEqual(projection["sourceCut"], cut)
        matches = [link for link in projection["directStaticImportCandidates"]
                   if link["consumerPath"] == consumer
                   and link["providerPath"] == provider]
        self.assertEqual(len(matches), 1)
        self.assertEqual(
            matches[0]["relation"], "STATIC_PYTHON_IMPORT_CANDIDATE_NOT_RUNTIME_CALL"
        )
        self.assertIn("composition:verify", projection["candidateVerifyTasks"])
        self.assertEqual(projection["runtimeCallStanding"], "UNKNOWN")
        self.assertFalse(projection["proofReuseAdmissible"])
        self.assertFalse(projection["impactClosureEstablished"])
        self.assertFalse(projection["deletionAuthorized"])
        self.assertEqual(projection["changedSourceUnindexedPaths"], [])
        self.assertNotIn("formal:verify", projection["candidateVerifyTasks"])

        cli = subprocess.run([
            sys.executable, str(MODULE_PATH),
            "--changed-file", provider, "--source-cut", cut,
            "--explain-source-impact"
        ], capture_output=True, text=True, timeout=40)
        self.assertEqual(cli.returncode, 0, cli.stderr)
        from_cli = json.loads(cli.stdout)
        self.assertEqual(
            from_cli["sourceImpact"]["directStaticImportCandidates"],
            projection["directStaticImportCandidates"]
        )
        self.assertEqual(from_cli["queueVerifyTasks"], plan["queueVerifyTasks"])
        self.assertIn("composition:verify", from_cli["queueVerifyTasks"])
        self.assertEqual(
            from_cli["sourceImpact"]["mandatoryQueueVerifyTasks"],
            plan["queueVerifyTasks"],
        )

    def test_phase2_bootstrap_does_not_silently_close_unknown_languages(self) -> None:
        cut = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
        path = "services/runtime/crates/ordivon-runtime-core/src/lib.rs"
        plan = MODULE.build_plan(changed_files=[path])
        projection = MODULE.explain_source_impact(
            source_cut=cut, changed_paths=[path], base_plan=plan
        )
        self.assertEqual(projection["analysisStanding"], "STATIC_PYTHON_ONLY")
        self.assertEqual(projection["nonPythonCallCoverage"], "NOT_ANALYZED")
        self.assertIn("runtime:verify", projection["candidateVerifyTasks"])
        self.assertIn("composition:verify", projection["candidateVerifyTasks"])
        self.assertFalse(projection["proofReuseAdmissible"])

    def test_phase2_bootstrap_formal_source_keeps_mathematical_verifier(self) -> None:
        cut = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
        path = "tools/formal/RecursiveLegoRefinement.lean"
        plan = MODULE.build_plan(changed_files=[path])
        projection = MODULE.explain_source_impact(
            source_cut=cut, changed_paths=[path], base_plan=plan
        )
        self.assertEqual(projection["mandatoryQueueVerifyTasks"], ["formal:verify"])
        self.assertEqual(projection["candidateVerifyTasks"], ["formal:verify"])
        self.assertEqual(projection["directStaticImportCandidates"], [])
        self.assertEqual(projection["nonPythonCallCoverage"], "NOT_ANALYZED")
        self.assertFalse(projection["impactClosureEstablished"])

    def test_phase2_bootstrap_rejects_wrong_source_cut(self) -> None:
        path = "packages/composition/src/ordivon_composition/verification_obligation_r1.py"
        plan = MODULE.build_plan(changed_files=[path])
        with self.assertRaisesRegex(ValueError, "exact.*SourceCut|source cut"):
            MODULE.explain_source_impact(
                source_cut="0" * 40, changed_paths=[path], base_plan=plan
            )

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
