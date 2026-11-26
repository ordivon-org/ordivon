"""Read-only Agent proof admission is an exact receipt query, not a new verifier."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

SOURCE = Path(__file__).resolve().parents[1] / "agent_evidence_admission.py"
spec = importlib.util.spec_from_file_location("runtime_agent_evidence_admission_test", SOURCE)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

SHA = "a" * 40
BASE = "b" * 40
NEXT = "c" * 40


def check(name="root-verification", status="completed", conclusion="success", sha=SHA, app="github-actions"):
    return {
        "name": name,
        "status": status,
        "conclusion": conclusion,
        "head_sha": sha,
        "app": {"slug": app},
        "details_url": "https://github.com/ordivon-org/ordivon/actions/runs/1/job/1",
    }


class EvidenceAdmissionTests(unittest.TestCase):
    def test_valid_exact_commit_check_run_is_observable(self):
        state, jobs = module._official_ci_at_cut({"check_runs": [check()], "total_count": 1}, SHA)
        self.assertEqual(state, "EXACT_CUT_SOURCE_CI_PASS")
        self.assertEqual(jobs[0]["name"], "root-verification")

    def test_missing_or_failed_or_pending_root_fails_closed(self):
        cases = [
            ([], 0, "NO_ROOT_VERIFICATION_RECEIPT"),
            ([check(status="in_progress", conclusion=None)], 1, "INCOMPLETE_OR_FAILED_CHECKS"),
            ([check(conclusion="failure")], 1, "INCOMPLETE_OR_FAILED_CHECKS"),
            ([check(name="repo-mechanics")], 1, "NO_ROOT_VERIFICATION_RECEIPT"),
            ([check(sha=NEXT)], 1, "UNKNOWN_CHECK_SET"),
        ]
        for jobs, count, wanted in cases:
            with self.subTest(wanted=wanted, jobs=jobs):
                state, _ = module._official_ci_at_cut({"check_runs": jobs, "total_count": count}, SHA)
                self.assertEqual(state, wanted)

    def test_truncated_or_reexecuted_check_runs_are_not_arbitrary_pass(self):
        for data, expected in [
            ({"check_runs": [check()], "total_count": 2}, "UNKNOWN_CHECK_SET"),
            ({"check_runs": [check(), check()], "total_count": 2}, "AMBIGUOUS_CHECK_RUNS"),
        ]:
            self.assertEqual(module._official_ci_at_cut(data, SHA)[0], expected)

    @staticmethod
    def fake_github(path: str):
        if path.startswith("pulls/"):
            return {
                "head": {"sha": SHA, "repo": {"full_name": module.REPOSITORY}},
                "base": {"sha": BASE, "repo": {"full_name": module.REPOSITORY}},
            }
        if path == "actions/jobs/1":
            return {
                "id": 1,
                "run_id": 1,
                "name": "root-verification",
                "workflow_name": "Monorepo Required",
                "head_sha": SHA,
                "status": "completed",
                "conclusion": "success",
            }
        if path == "actions/runs/1":
            return {
                "id": 1,
                "name": "Monorepo Required",
                "path": ".github/workflows/ci.yml",
                "head_sha": SHA,
                "status": "completed",
                "conclusion": "success",
            }
        return {"check_runs": [check()], "total_count": 1}

    @staticmethod
    def fake_git(*args):
        if args[0] == "rev-parse":
            return SHA if args[1] == f"{SHA}^{{commit}}" else NEXT
        if args[0] == "cat-file":
            return "commit"
        raise AssertionError(args)

    def test_real_official_check_at_exact_cut_skips_duplicate_source_run(self):
        with (
            patch.object(module, "_github", side_effect=self.fake_github),
            patch.object(module, "_git", side_effect=self.fake_git),
            patch.object(module.convergence_plan, "build_plan", return_value={"verificationOwners": ["runtime"]}),
        ):
            report = module.assess(pr=2177, owner="runtime", target=SHA)
        self.assertEqual(report["decision"], "EXACT_CUT_CI_OBSERVED")
        self.assertEqual(report["recommendedAction"], "REUSE_OFFICIAL_SOURCE_CI_RESULT_AT_THIS_CUT_NO_DUPLICATE_RUN")
        self.assertFalse(report["proofReuseAdmissible"])
        self.assertEqual(report["installedStanding"], "UNKNOWN")

    def test_missing_check_evidence_blocks_reuse_even_at_same_cut(self):
        with (
            patch.object(
                module,
                "_github",
                side_effect=lambda path: (
                    self.fake_github(path) if path.startswith("pulls/") else {"total_count": 0, "check_runs": []}
                ),
            ),
            patch.object(module, "_git", side_effect=self.fake_git),
            patch.object(module.convergence_plan, "build_plan", return_value={"verificationOwners": ["runtime"]}),
        ):
            report = module.assess(pr=2177, owner="runtime", target=SHA)
        self.assertEqual(report["decision"], "RECEIPT_UNKNOWN_OR_NOT_PASSED")
        self.assertFalse(report["proofReuseAdmissible"])

    def test_forged_same_named_check_from_other_workflow_is_not_reused(self):
        def wrong_workflow(path):
            row = self.fake_github(path)
            if path == "actions/runs/1":
                row = {**row, "path": ".github/workflows/unrelated.yml"}
            return row

        with (
            patch.object(module, "_github", side_effect=wrong_workflow),
            patch.object(module, "_git", side_effect=self.fake_git),
            patch.object(module.convergence_plan, "build_plan", return_value={"verificationOwners": ["runtime"]}),
        ):
            report = module.assess(pr=2177, owner="runtime", target=SHA)
        self.assertEqual(report["originalReceipt"], "UNKNOWN_ROOT_WORKFLOW_IDENTITY")
        self.assertEqual(report["decision"], "RECEIPT_UNKNOWN_OR_NOT_PASSED")
        self.assertFalse(report["proofReuseAdmissible"])

    def test_source_evolved_impacted_selects_target_original_task(self):
        with (
            patch.object(module, "_github", side_effect=self.fake_github),
            patch.object(module, "_git", side_effect=self.fake_git),
            patch.object(
                module.convergence_plan,
                "build_plan",
                side_effect=[
                    {"verificationOwners": ["runtime"]},
                    {"verificationOwners": ["runtime"]},
                ],
            ),
            patch.object(module.affected_owners, "changed_paths", return_value=("services/runtime/src/lib.rs",)),
            patch.object(module.subprocess, "run", return_value=SimpleNamespace(returncode=0)),
        ):
            report = module.assess(pr=2177, owner="runtime", target=NEXT)
        self.assertEqual(report["decision"], "CHANGED_CONSUMER_INPUT")
        self.assertEqual(report["changedTrackedGitPaths"], ["services/runtime/src/lib.rs"])

    def test_source_evolved_unaffected_reuses_source_observation_only(self):
        with (
            patch.object(module, "_github", side_effect=self.fake_github),
            patch.object(module, "_git", side_effect=self.fake_git),
            patch.object(
                module.convergence_plan,
                "build_plan",
                side_effect=[
                    {"verificationOwners": ["runtime"]},
                    {"verificationOwners": ["gateway", "harness"]},
                ],
            ),
            patch.object(module.affected_owners, "changed_paths", return_value=("docs/architecture/EXAMPLE.md",)),
            patch.object(module.subprocess, "run", return_value=SimpleNamespace(returncode=0)),
        ):
            report = module.assess(pr=2177, owner="runtime", target=NEXT)
        self.assertEqual(report["decision"], "SCOPED_SOURCE_NO_OWNER_RECHECK")
        self.assertFalse(report["proofReuseAdmissible"])

    def test_unrelated_target_remains_unknown_not_auto_full_replay(self):
        with (
            patch.object(module, "_github", side_effect=self.fake_github),
            patch.object(module, "_git", side_effect=self.fake_git),
            patch.object(module.convergence_plan, "build_plan", return_value={"verificationOwners": ["runtime"]}),
            patch.object(module.subprocess, "run", return_value=SimpleNamespace(returncode=1)),
        ):
            report = module.assess(pr=2177, owner="runtime", target=NEXT)
        self.assertEqual(report["decision"], "UNKNOWN_SOURCE_RELATION")
        self.assertEqual(report["recommendedAction"], "QUALIFY_MISSING_SOURCE_RELATION_NOT_BLANKET_REPLAY")

    @staticmethod
    def workflow_check(
        name: str,
        *,
        run: int,
        job: int,
        status: str = "completed",
        conclusion: str | None = "success",
    ) -> dict:
        return {
            "name": name,
            "status": status,
            "conclusion": conclusion,
            "head_sha": SHA,
            "app": {"slug": "github-actions"},
            "details_url": (f"https://github.com/ordivon-org/ordivon/actions/runs/{run}/job/{job}"),
        }

    def test_merge_queue_push_duplicate_names_preserve_completed_required_run(self):
        records = [
            self.workflow_check("root-verification", run=1, job=10),
            self.workflow_check("repo-preflight", run=1, job=11),
            self.workflow_check("repo-preflight", run=2, job=21, status="in_progress", conclusion=None),
            self.workflow_check("repo-mechanics", run=2, job=22, status="in_progress", conclusion=None),
        ]
        with (
            patch.object(module, "_github", return_value={"check_runs": records, "total_count": len(records)}),
            patch.object(module, "_native_root_workflow_matches", return_value=True) as qualified,
        ):
            standing, selected, root = module._qualified_original_source_ci(SHA)
        self.assertEqual(standing, "EXACT_CUT_REQUIRED_WORKFLOW_PASS")
        self.assertEqual(len(selected), 2)
        self.assertEqual(root["name"], "root-verification")
        self.assertTrue(all("/runs/1/" in item["url"] for item in selected))
        qualified.assert_called_once()

    def test_conflicting_finished_root_stands_unknown(self):
        records = [
            self.workflow_check("root-verification", run=1, job=10),
            self.workflow_check("root-verification", run=2, job=20, conclusion="failure"),
        ]
        with patch.object(module, "_github", return_value={"check_runs": records, "total_count": 2}):
            standing, selected, _ = module._qualified_original_source_ci(SHA)
        self.assertEqual(standing, "CONFLICTING_REQUIRED_WORKFLOW_RESULTS")
        self.assertEqual(selected, [])

    def test_pending_job_in_same_required_workflow_is_not_sufficient(self):
        records = [
            self.workflow_check("root-verification", run=1, job=10),
            self.workflow_check("repo-mechanics", run=1, job=11, status="in_progress", conclusion=None),
        ]
        with (
            patch.object(module, "_github", return_value={"check_runs": records, "total_count": 2}),
            patch.object(module, "_native_root_workflow_matches", return_value=True),
        ):
            standing, _, _ = module._qualified_original_source_ci(SHA)
        self.assertEqual(standing, "AMBIGUOUS_OR_UNQUALIFIED_REQUIRED_WORKFLOW")

    def test_same_named_root_from_wrong_workflow_is_not_promoted(self):
        records = [
            self.workflow_check("root-verification", run=1, job=10),
            self.workflow_check("repo-preflight", run=1, job=11),
            self.workflow_check("repo-preflight", run=2, job=21, status="in_progress", conclusion=None),
        ]
        with (
            patch.object(module, "_github", return_value={"check_runs": records, "total_count": 3}),
            patch.object(module, "_native_root_workflow_matches", return_value=False),
        ):
            standing, _, _ = module._qualified_original_source_ci(SHA)
        self.assertEqual(standing, "AMBIGUOUS_OR_UNQUALIFIED_REQUIRED_WORKFLOW")

    def test_exact_commit_ci_after_merge_queue_needs_no_pr_identity(self):
        with (
            patch.object(module, "_git", side_effect=self.fake_git),
            patch.object(
                module,
                "_qualified_original_source_ci",
                return_value=(
                    "EXACT_CUT_SOURCE_CI_PASS",
                    [{"name": "root-verification"}],
                    {"name": "root-verification", "status": "completed", "conclusion": "success"},
                ),
            ) as original,
        ):
            receipt = module.assess_commit(commit=SHA, owner="runtime", target=SHA)
        original.assert_called_once_with(SHA)
        self.assertIsNone(receipt["originalPr"])
        self.assertIsNone(receipt["originalBaseCut"])
        self.assertIsNone(receipt["originalOwnerInCurrentSelectorProjection"])
        self.assertEqual(receipt["decision"], "EXACT_CUT_CI_OBSERVED")
        self.assertFalse(receipt["proofReuseAdmissible"])

    def test_distinct_squash_commit_cannot_inherit_old_pr_ci(self):
        with (
            patch.object(module, "_git", side_effect=self.fake_git),
            patch.object(
                module,
                "_qualified_original_source_ci",
                return_value=("EXACT_CUT_SOURCE_CI_PASS", [], {"name": "root-verification"}),
            ),
        ):
            receipt = module.assess_commit(commit=SHA, owner="runtime", target=NEXT)
        self.assertEqual(receipt["decision"], "UNKNOWN_SOURCE_RELATION")
        self.assertEqual(receipt["sourceRelation"], "UNQUALIFIED_DISTINCT_SOURCE_CUTS")
        self.assertIn("EXACT_TARGET_CUT_RECEIPT", receipt["recommendedAction"])

    def test_commit_mode_cannot_promote_failed_or_unknown_original_ci(self):
        with (
            patch.object(module, "_git", side_effect=self.fake_git),
            patch.object(
                module,
                "_qualified_original_source_ci",
                return_value=("INCOMPLETE_OR_FAILED_CHECKS", [], None),
            ),
        ):
            receipt = module.assess_commit(commit=SHA, owner="runtime", target=SHA)
        self.assertEqual(receipt["decision"], "RECEIPT_UNKNOWN_OR_NOT_PASSED")

    def test_commit_mode_rejects_nonexact_input_and_unsupported_owner(self):
        with self.assertRaisesRegex(ValueError, "exact lowercase"):
            module.assess_commit(commit="HEAD", owner="runtime")
        with self.assertRaisesRegex(ValueError, "unknown natural"):
            module.assess_commit(commit=SHA, owner="invented")

    def test_rejects_unqualified_request_and_foreign_pr(self):
        with self.assertRaisesRegex(ValueError, "unknown natural"):
            module.assess(pr=2177, owner="invented")
        with (
            patch.object(
                module,
                "_github",
                return_value={
                    "head": {"sha": SHA, "repo": {"full_name": "foreign/other"}},
                    "base": {"sha": BASE, "repo": {"full_name": module.REPOSITORY}},
                },
            ),
        ):
            with self.assertRaisesRegex(ValueError, "expected GitHub repository"):
                module.assess(pr=2177, owner="runtime")
        with (
            patch.object(module, "_github", side_effect=self.fake_github),
        ):
            with self.assertRaisesRegex(ValueError, "HEAD or an exact Git commit"):
                module.assess(pr=2177, owner="runtime", target="--some-git-option")


if __name__ == "__main__":
    unittest.main()
