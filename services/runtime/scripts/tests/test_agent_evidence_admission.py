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
