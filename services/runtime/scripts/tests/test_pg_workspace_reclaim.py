"""PG lifecycle: integrated source + value/consumer fences, not Job success alone."""
from __future__ import annotations

from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
import os
import sys
import unittest

ENTRY = Path(__file__).resolve().parents[1] / "ordivon-runtime-pg-reclaim"
sys.path.insert(0, str(ENTRY.parent))
loader = SourceFileLoader("ordivon_runtime_pg_reclaim", str(ENTRY))
spec = spec_from_loader(loader.name, loader)
assert spec is not None
mod = module_from_spec(spec)
loader.exec_module(mod)


class PgWorkspaceReclaimTests(unittest.TestCase):
    def setUp(self):
        self.params = dict(now_ms=10_000_000, created_ms=1_000_000,
                           latest_job_ms=5_000_000, latest_resolution="succeeded",
                           unresolved=0, min_age_ms=3_000_000)

    def test_reclaims_only_old_terminal_success(self):
        self.assertTrue(mod.eligible(**self.params))

    def test_terminal_failure_is_reclaimable_only_after_independent_guards(self):
        # Git value, process and NativeClose checks remain separate guards.
        for resolution in ("failed", "timed_out", "cancelled"):
            self.assertTrue(mod.eligible(**{**self.params, "latest_resolution": resolution}))

    def test_lost_or_unknown_job_never_becomes_a_reclaim_hint(self):
        for resolution in ("lost", "orphaned", "running", None):
            self.assertFalse(mod.eligible(**{**self.params, "latest_resolution": resolution}))

    def test_active_job_blocks(self):
        self.assertFalse(mod.eligible(**{**self.params, "unresolved": 1}))

    def test_no_job_is_not_permanently_pinned_by_missing_success(self):
        self.assertTrue(mod.eligible(**{
            **self.params, "latest_job_ms": None, "latest_resolution": None,
        }))
        self.assertFalse(mod.eligible(**{
            **self.params, "latest_job_ms": None, "latest_resolution": "succeeded",
        }))
        self.assertFalse(mod.eligible(**{
            **self.params, "latest_job_ms": None, "latest_resolution": None,
            "created_ms": 9_000_000,
        }))

    def test_grace_counts_last_job_not_only_creation(self):
        self.assertFalse(mod.eligible(**{**self.params, "latest_job_ms": 8_000_000}))

    def test_boolean_and_future_creation_not_valid_times(self):
        self.assertFalse(mod.eligible(**{**self.params, "created_ms": True}))
        self.assertFalse(mod.eligible(**{**self.params, "created_ms": 20_000_000}))

    def test_identity_must_precede_job(self):
        self.assertFalse(mod.eligible(**{**self.params, "created_ms": 6_000_000}))


if __name__ == "__main__":
    unittest.main()


class PgOperatorRetentionPolicyTests(unittest.TestCase):
    """Reuse the actual Git storage and retention contract, not fake a close."""

    def setUp(self):
        from tempfile import TemporaryDirectory
        self.temp = TemporaryDirectory(prefix="ordivon-pg-retention-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "source"
        self.repo.mkdir()
        self.workspaces = self.root / "workspaces"
        self.workspaces.mkdir()
        import subprocess

        def git(*argv, cwd=None):
            result = subprocess.run(
                ["git", "-C", str(cwd or self.repo), *argv],
                capture_output=True, text=True, check=True,
            )
            return result.stdout.strip()

        self.git = git
        git("init", "-q", "-b", "main")
        git("config", "user.name", "Test Operator")
        git("config", "user.email", "test-operator@example.invalid")
        (self.repo / "initial").write_text("initial")
        git("add", "initial")
        git("commit", "-qm", "initial")
        self.base = git("rev-parse", "HEAD")
        git("update-ref", "refs/remotes/origin/main", self.base)
        self.workspace = self.workspaces / "ws-clean-unintegrated-test"
        git("worktree", "add", "--detach", str(self.workspace), "HEAD")
        (self.workspace / "new-work").write_text("valuable isolated research work")
        git("add", "new-work", cwd=self.workspace)
        git("commit", "-qm", "valuable work", cwd=self.workspace)
        self.head = git("rev-parse", "HEAD", cwd=self.workspace)
        self.assertNotEqual(self.base, self.head)

    def policy_file(
        self, allow: bool, *, pinned: bool = False, released: bool = False
    ) -> Path:
        import json

        content = {
            "schemaVersion": 1, "defaultClass": "ephemeral",
            "classes": {
                "ephemeral": {
                    "retentionHours": 4,
                    "forceCloseUnintegratedAfterRetention": allow,
                },
                "pinned": {
                    "retentionHours": None,
                    "forceCloseUnintegratedAfterRetention": False,
                },
            },
            "rules": (
                ([{"workspaceId": self.workspace.name, "class": "pinned"}]
                 if pinned else [])
                + ([{"workspaceId": self.workspace.name, "class": "ephemeral",
                     "operatorConsumerReleased": True}] if released else [])
            ),
        }
        path = self.root / "policy.json"
        path.write_text(json.dumps(content))
        return path

    def test_policy_absent_or_operator_disabled_means_no_unintegrated_close(self):
        self.assertEqual(mod._workspace_retention(None, self.workspace.name, 4),
                         (14_400_000, False))
        config = mod._retention_policy(self.policy_file(False))
        self.assertEqual(mod._workspace_retention(config, self.workspace.name, 4),
                         (14_400_000, False))
        config = mod._retention_policy(self.policy_file(True, pinned=True))
        self.assertEqual(mod._workspace_retention(config, self.workspace.name, 4),
                         (None, False))

    def test_class_retention_never_shortens_installed_minimum(self):
        config = mod._retention_policy(self.policy_file(True))
        self.assertEqual(mod._workspace_retention(config, self.workspace.name, 8),
                         (28_800_000, True))

    def test_installed_policy_requires_controlled_file_and_directory(self):
        """A world-writable policy cannot authorize deleting unpublished work."""
        path = self.policy_file(True)
        self.assertTrue(mod._workspace_retention(
            mod._retention_policy(path), self.workspace.name, 4
        )[1])
        try:
            path.chmod(0o666)
            with self.assertRaisesRegex(ValueError, "retention policy"):
                mod._retention_policy(path)
            path.chmod(0o644)
            path.parent.chmod(0o777)
            with self.assertRaisesRegex(ValueError, "retention policy"):
                mod._retention_policy(path)
        finally:
            path.parent.chmod(0o700)
            path.chmod(0o644)
        if os.geteuid() == 0:
            try:
                os.chown(path, 65534, -1)
                with self.assertRaisesRegex(ValueError, "retention policy"):
                    mod._retention_policy(path)
            finally:
                os.chown(path, 0, -1)

    def test_malformed_operator_policy_blocks_instead_of_falling_back(self):
        invalid = self.root / "policy.json"
        invalid.write_text('{"schemaVersion":1,"defaultClass":"not-existing","classes":{}}')
        with self.assertRaises(ValueError):
            mod._retention_policy(invalid)
        with self.assertRaises(ValueError):
            mod._retention_policy(Path("relative-policy.json"))

    def test_unintegrated_head_has_native_git_retention_ref_and_replay(self):
        digest = "sha256:" + "d" * 64
        first = mod._preserve_unintegrated_head(
            self.repo, self.workspace.name, self.head, digest
        )
        self.assertEqual(first["disposition"], "created")
        second = mod._preserve_unintegrated_head(
            self.repo, self.workspace.name, self.head, digest
        )
        self.assertEqual(second["disposition"], "existing")
        self.git("worktree", "remove", "--force", str(self.workspace))
        self.assertEqual(self.git("rev-parse", first["retentionRef"]), self.head)
        self.assertEqual(self.git("show", f'{self.head}:new-work'),
                         "valuable isolated research work")

    def test_existing_retention_ref_mismatch_never_overwritten(self):
        digest = "sha256:" + "e" * 64
        ref = f"refs/ordivon/retention/{self.workspace.name}/" + "e" * 64
        self.git("update-ref", ref, self.base)
        with self.assertRaisesRegex(RuntimeError, "collides"):
            mod._preserve_unintegrated_head(
                self.repo, self.workspace.name, self.head, digest
            )
        self.assertEqual(self.git("rev-parse", ref), self.base)

    def test_git_queries_remain_bound_to_owner_despite_foreign_git_environment(self):
        import subprocess
        from unittest.mock import patch

        foreign = self.root / "foreign"
        foreign.mkdir()
        clean_env = {key: value for key, value in os.environ.items()
                     if not key.startswith("GIT_")}
        for argv in (
            ("init", "-q"),
            ("config", "user.name", "Foreign"),
            ("config", "user.email", "foreign@example.invalid"),
        ):
            subprocess.run(["git", "-C", str(foreign), *argv],
                           env=clean_env, check=True, capture_output=True)
        (foreign / "different").write_text("foreign git identity")
        for argv in (("add", "."), ("commit", "-qm", "foreign")):
            subprocess.run(["git", "-C", str(foreign), *argv],
                           env=clean_env, check=True, capture_output=True)

        for field, value in (
            ("GIT_DIR", str(foreign / ".git")),
            ("GIT_OBJECT_DIRECTORY", str(foreign / ".git" / "objects")),
        ):
            with self.subTest(field=field), patch.dict(os.environ, {field: value}):
                # Prove the counterexample actually poisons a raw Git call.
                raw = subprocess.run(
                    ["git", "-C", str(self.repo), "cat-file", "-t", self.head],
                    capture_output=True, text=True,
                )
                self.assertNotEqual(raw.returncode, 0)

                # The existing reclaim Git reader must never cross the owner.
                qualified = mod._git(self.repo, "cat-file", "-t", self.head)
                self.assertEqual(qualified.returncode, 0, qualified.stderr)
                self.assertEqual(qualified.stdout.strip(), "commit")
                self.assertTrue(mod._unintegrated_head(self.repo, self.head))
                self.assertIn(
                    (self.workspace, self.head),
                    mod._worktrees(self.repo, self.workspaces),
                )

    def test_git_membership_error_cannot_be_misread_as_policy_unintegrated(self):
        from unittest.mock import patch
        import subprocess

        original = mod._git

        def fail_membership(repo, *args, **kwargs):
            if args and args[0] == "merge-base":
                return subprocess.CompletedProcess(args=args, returncode=128,
                                                   stdout="", stderr="unknown Git state")
            return original(repo, *args, **kwargs)

        with patch.object(mod, "_git", side_effect=fail_membership):
            self.assertIsNone(mod._unintegrated_head(self.repo, self.head))

    def run_operator_plan(self, *, allow: bool, apply: bool = False,
                          pinned: bool = False, revoke_during_get: bool = False,
                          process_enters_during_get: bool = False,
                          ignored_emerges_during_get: bool = False,
                          close_transport_uncertain: bool = False,
                          job_case: str = "succeeded",
                          owner_released: bool = False,
                          active_at_get: bool = False,
                          integration_ref: str = "refs/remotes/origin/main"):
        import argparse
        from unittest.mock import patch
        import time

        future_ms = int((time.time() + 6 * 3600) * 1000)
        policy_path = self.policy_file(
            allow, pinned=pinned, released=owner_released
        )
        args = argparse.Namespace(
            env_file=self.root / "mock-env",
            source_repo=self.repo,
            workspace_root=self.workspaces,
            min_age_hours=4,
            limit=25,
            apply=apply,
            policy_file=policy_path,
            integration_ref=integration_ref,
        )
        # Isolated PG projection only. Real Git worktrees, status, commits and
        # durable retention refs are used. Native PG close is a separate owner.
        class RecordingRuntimeClient:
            def __init__(self, enclosing):
                self.enclosing = enclosing
                self.calls = []

            def call_tool(self, name, parameters):
                self.calls.append(name)
                if name == "workspace.get":
                    if process_enters_during_get:
                        process_cwd_after_get.append(str(self.enclosing.workspace / "source"))
                    if ignored_emerges_during_get:
                        (self.enclosing.workspace / "ignored-cache").mkdir(exist_ok=True)
                        (self.enclosing.workspace / "ignored-cache" / "result").write_text("keep")
                    if revoke_during_get:
                        policy_path.write_text(
                            __import__("json").dumps({
                                "schemaVersion": 1,
                                "defaultClass": "ephemeral",
                                "classes": {"ephemeral": {
                                    "retentionHours": 4,
                                    "forceCloseUnintegratedAfterRetention": False,
                                }},
                                "rules": [],
                            })
                        )
                    return {
                        "workspaceId": self.enclosing.workspace.name,
                        "dirty": False,
                        "activeJobIds": (["job-new"] if active_at_get else []),
                        "sourceRepo": str(self.enclosing.repo.resolve()),
                        "currentHeadRevision": self.enclosing.head,
                        "createdAtMs": future_ms - 7 * 3600 * 1000,
                        "sourceStateDigest": "sha256:" + "f" * 64,
                    }
                if name == "workspace.close":
                    assert parameters["force"] is False
                    assert parameters["consumerReleased"] is False
                    assert parameters["expectedSourceStateDigest"] == "sha256:" + "f" * 64
                    if close_transport_uncertain:
                        raise TimeoutError("the test transport has no effect receipt")
                    self.enclosing.git(
                        "worktree", "remove", str(self.enclosing.workspace),
                    )
                    return {"closureDisposition": "removed"}
                raise AssertionError("unexpected call")

        client = RecordingRuntimeClient(self)
        process_cwd_after_get = []
        assert job_case in {"succeeded", "failed", "timed_out", "cancelled",
                            "lost", "orphaned", "no_job", "active"}
        job_rows = {} if job_case == "no_job" else {
            self.workspace.name: (
                future_ms - 5 * 3600 * 1000,
                job_case if job_case != "active" else None,
                1 if job_case == "active" else 0,
            )
        }
        with (
            patch.object(mod, "WORKSPACE_ROOT", self.workspaces.resolve()),
            patch.object(
                mod, "load_environment_file",
                return_value={"ORDIVON_PG_BIND": "127.0.0.1:0", "ORDIVON_PG_TOKEN": "test"},
            ),
            patch.object(mod, "_jobs", return_value=job_rows),
            patch.object(mod, "_active_process_cwds",
                         side_effect=lambda _: process_cwd_after_get.copy()),
            patch.object(mod.time, "time", return_value=future_ms / 1000),
            patch.object(mod, "connect_compatible", return_value=client),
        ):
            report = mod.run(args)
        return report, client

    def test_real_git_dry_run_respects_installed_unintegrated_policy(self):
        disabled, _ = self.run_operator_plan(allow=False)
        self.assertEqual(disabled["eligible"], 0)
        self.assertEqual(disabled["skipped"].get("head_not_in_main"), 1)
        allowed, _ = self.run_operator_plan(allow=True)
        self.assertEqual(allowed["eligible"], 1)
        self.assertEqual(allowed["eligibleUnintegrated"], 1)
        self.assertEqual(allowed["candidates"], [self.workspace.name])
        self.assertTrue(self.workspace.exists())
        pinned, _ = self.run_operator_plan(allow=True, pinned=True)
        self.assertEqual(pinned["eligible"], 0)
        self.assertEqual(pinned["skipped"].get("policy_pinned"), 1)

    def test_known_terminal_failure_with_merged_clean_source_is_candidate(self):
        self.git("update-ref", "refs/remotes/origin/main", self.head)
        for outcome in ("failed", "timed_out", "cancelled"):
            with self.subTest(outcome=outcome):
                report, _ = self.run_operator_plan(
                    allow=False, job_case=outcome, owner_released=True
                )
                self.assertEqual(report["eligible"], 1, report)
                self.assertEqual(report["candidates"], [self.workspace.name])

    def test_idle_no_job_or_failed_needs_exact_owner_release(self):
        # Native PG Job/cwd state is insufficient when a separate Harness Run
        # may be paused before or after its first Job.
        self.git("update-ref", "refs/remotes/origin/main", self.head)
        for outcome in ("no_job", "failed", "timed_out", "cancelled"):
            with self.subTest(outcome=outcome):
                report, client = self.run_operator_plan(
                    allow=False, job_case=outcome, apply=True
                )
                self.assertEqual(report["eligible"], 0)
                self.assertEqual(
                    report["skipped"].get("needs_owner_disposition"), 1
                )
                self.assertEqual(report["needsOwnerDisposition"], [self.workspace.name])
                self.assertEqual(client.calls, [])
                self.assertTrue(self.workspace.exists())

    def test_broad_prefix_cannot_assert_consumer_released(self):
        import json
        policy = self.policy_file(True)
        data = json.loads(policy.read_text())
        data["rules"] = [
            {"prefix": "ws-", "class": "ephemeral",
             "operatorConsumerReleased": True}
        ]
        policy.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "owner release"):
            mod._retention_policy(policy)

    def test_duplicate_exact_operator_releases_fail_closed(self):
        import json
        policy = self.policy_file(True, released=True)
        data = json.loads(policy.read_text())
        data["rules"].append({
            "workspaceId": self.workspace.name, "class": "ephemeral",
            "operatorConsumerReleased": False,
        })
        policy.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "duplicate exact owner release"):
            mod._retention_policy(policy)

    def test_explicit_release_revoked_during_get_refuses_close(self):
        self.git("update-ref", "refs/remotes/origin/main", self.head)
        report, client = self.run_operator_plan(
            allow=False, job_case="no_job", owner_released=True,
            revoke_during_get=True, apply=True,
        )
        self.assertEqual(report["closed"], [])
        self.assertEqual(client.calls, ["workspace.get"])
        self.assertEqual(report["skipped"].get("owner_disposition_revoked"), 1)
        self.assertTrue(self.workspace.exists())

    def test_no_job_merged_clean_carrier_is_closed_only_through_runtime(self):
        self.git("update-ref", "refs/remotes/origin/main", self.head)
        report, client = self.run_operator_plan(
            allow=False, apply=True, job_case="no_job",
            owner_released=True,
        )
        self.assertEqual(report["closed"], [self.workspace.name], report)
        self.assertEqual(client.calls, ["workspace.get", "workspace.close"])
        self.assertFalse(self.workspace.exists())

    def test_no_job_or_failed_unmerged_head_is_not_assumed_delivered(self):
        for outcome in ("failed", "no_job", "lost", "orphaned", "active"):
            with self.subTest(outcome=outcome):
                report, client = self.run_operator_plan(
                    allow=True, apply=True, job_case=outcome,
                    owner_released=True,
                )
                self.assertEqual(report["closed"], [], report)
                self.assertEqual(client.calls, [])
                self.assertTrue(self.workspace.exists())

    def test_new_job_observed_by_runtime_get_blocks_candidate(self):
        self.git("update-ref", "refs/remotes/origin/main", self.head)
        report, client = self.run_operator_plan(
            allow=False, apply=True, job_case="failed",
            owner_released=True, active_at_get=True,
        )
        self.assertEqual(report["closed"], [], report)
        self.assertEqual(client.calls, ["workspace.get"])
        self.assertTrue(self.workspace.exists())

    def test_no_job_does_not_erase_ignored_outputs(self):
        self.git("update-ref", "refs/remotes/origin/main", self.head)
        exclude = self.repo / ".git" / "info" / "exclude"
        exclude.write_text(exclude.read_text() + "\nignored-cache/\n")
        (self.workspace / "ignored-cache").mkdir()
        (self.workspace / "ignored-cache" / "release.zip").write_bytes(b"not archived")
        report, client = self.run_operator_plan(
            allow=False, apply=True, job_case="no_job",
            owner_released=True,
        )
        self.assertEqual(report["closed"], [], report)
        self.assertEqual(client.calls, [])
        self.assertEqual(report["needsOwnerDisposition"], [])
        self.assertTrue((self.workspace / "ignored-cache" / "release.zip").exists())

    def test_local_only_main_proves_integrated_source_without_origin(self):
        # Research and Paper2 use local Git repositories without origin/main.
        self.git("update-ref", "refs/heads/main", self.head)
        self.git("update-ref", "-d", "refs/remotes/origin/main")
        report, _ = self.run_operator_plan(
            allow=False, integration_ref="refs/heads/main"
        )
        self.assertEqual(report["eligible"], 1)
        self.assertEqual(report["eligibleUnintegrated"], 0)
        self.assertEqual(report["candidates"], [self.workspace.name])
        with self.assertRaisesRegex(ValueError, "configured GC integration ref"):
            self.run_operator_plan(allow=False)

    def test_local_main_cannot_override_repository_with_remote(self):
        self.git("remote", "add", "origin", "file:///unreachable-test")
        with self.assertRaisesRegex(ValueError, "without remotes"):
            self.run_operator_plan(
                allow=False, integration_ref="refs/heads/main"
            )
        self.assertTrue(self.workspace.exists())

    def test_local_main_does_not_license_unmerged_source(self):
        self.git("update-ref", "-d", "refs/remotes/origin/main")
        report, _ = self.run_operator_plan(
            allow=False, integration_ref="refs/heads/main"
        )
        self.assertEqual(report["eligible"], 0)
        self.assertEqual(report["skipped"].get("head_not_in_main"), 1)

    def test_installed_service_source_scans_three_git_roots(self):
        unit = (Path(__file__).resolve().parents[2] /
                "packaging/systemd/ordivon-runtime-lifecycle.service").read_text()
        starts = [line for line in unit.splitlines()
                  if line.startswith("ExecStart=")]
        self.assertEqual(len(starts), 3)
        self.assertIn("--source-repo /root/projects/ordivon ",
                      starts[0])
        self.assertIn("--source-repo /root/projects/ordivon-research-v2 ",
                      starts[1])
        self.assertIn("--source-repo /root/projects/ordivon-paper2 ",
                      starts[2])
        for line in starts:
            self.assertIn("--policy-file /etc/ordivon/workspace-retention.json ", line)
        for line in starts[1:]:
            self.assertIn("--integration-ref refs/heads/main ", line)
            self.assertIn("--min-age-hours 4 ", line)
            self.assertNotIn("--force", line)

    def test_other_git_source_repo_workspace_is_not_unknown_directory(self):
        """One Runtime root can host unrelated Git repos; neither is an orphan."""
        import json
        other = self.root / "another-source-repo"
        other.mkdir()
        self.git("init", "-q", "-b", "main", cwd=other)
        self.git("config", "user.name", "Other Operator", cwd=other)
        self.git("config", "user.email", "other@example.invalid", cwd=other)
        (other / "main.txt").write_text("distinct Git authority")
        self.git("add", "main.txt", cwd=other)
        self.git("commit", "-qm", "other root", cwd=other)
        other_workspace = self.workspaces / "ws-other-source"
        self.git("worktree", "add", "--detach", str(other_workspace), "HEAD", cwd=other)
        records = self.root / "workspace-records"
        records.mkdir()
        (records / (other_workspace.name + ".json")).write_text(
            json.dumps({
                "schemaVersion": 1,
                "workspaceId": other_workspace.name,
                "sourceRepo": str(other.resolve()),
                "sourceRevision": self.git("rev-parse", "HEAD", cwd=other_workspace),
                "workspacePath": str(other_workspace.resolve()),
                "createdUnixMs": 1,
            })
        )
        report, client = self.run_operator_plan(allow=False)
        self.assertEqual(report["otherSourceRepoManagedWorkspaceCount"], 1)
        self.assertEqual(report["otherSourceRepoManagedWorkspaceSample"],
                         [other_workspace.name])
        self.assertEqual(report["unregisteredDirectoryCount"], 1)
        self.assertEqual(report["unclassifiedDirectoryCount"], 0)
        self.assertEqual(report["eligible"], 0)
        self.assertTrue(other_workspace.exists())
        self.assertEqual(client.calls, [])

    def test_unproven_cross_repo_record_remains_unknown_without_deletion(self):
        """An untrusted record is not enough to declare an orphan or a consumer."""
        import json
        other_workspace = self.workspaces / "ws-unproven-source"
        other_workspace.mkdir()
        records = self.root / "workspace-records"
        records.mkdir()
        # The record points at a genuine *other Git repository*, but Git
        # never registered this directory as its worktree. Metadata alone
        # must not make the directory appear safely owned or disposable.
        foreign_repo = self.root / "unrelated-source"
        foreign_repo.mkdir()
        self.git("init", "-q", "-b", "main", cwd=foreign_repo)
        (records / (other_workspace.name + ".json")).write_text(
            json.dumps({
                "schemaVersion": 1,
                "workspaceId": other_workspace.name,
                "sourceRepo": str(foreign_repo.resolve()),
                "workspacePath": str(other_workspace.resolve()),
            })
        )
        report, client = self.run_operator_plan(allow=True)
        self.assertEqual(report["otherSourceRepoManagedWorkspaceCount"], 0)
        self.assertEqual(report["unregisteredDirectoryCount"], 1)
        self.assertEqual(report["unclassifiedDirectoryCount"], 1)
        self.assertEqual(report["unregisteredDirectorySample"],
                         [other_workspace.name])
        self.assertEqual(report["eligible"], 1)  # unrelated source repo W is eligible
        self.assertTrue(other_workspace.exists())
        self.assertEqual(client.calls, [])

    def test_ignored_workspace_output_never_qualifies_for_deletion(self):
        # Git status --porcelain reports clean, but ordinary worktree remove
        # would still remove this cache or data under ignore rules.
        exclude = self.repo / ".git" / "info" / "exclude"
        exclude.write_text(exclude.read_text() + "\nignored-cache/\n")
        (self.workspace / "ignored-cache").mkdir()
        (self.workspace / "ignored-cache" / "result").write_text("valuable ignored bytes")
        report, client = self.run_operator_plan(allow=True, apply=True)
        self.assertEqual(client.calls, [])
        self.assertEqual(report["closed"], [])
        self.assertEqual(report["skipped"].get("ignored_files_or_git_error"), 1)
        self.assertTrue((self.workspace / "ignored-cache" / "result").exists())

    def test_ignored_output_created_during_sweep_blocks_native_close(self):
        exclude = self.repo / ".git" / "info" / "exclude"
        exclude.write_text(exclude.read_text() + "\nignored-cache/\n")
        report, client = self.run_operator_plan(
            allow=True, apply=True, ignored_emerges_during_get=True
        )
        self.assertEqual(client.calls, ["workspace.get"])
        self.assertEqual(report["closed"], [])
        self.assertEqual(report["skipped"].get("ignored_files_at_close"), 1)
        self.assertTrue((self.workspace / "ignored-cache" / "result").exists())

    def test_process_enters_workspace_after_scan_and_prevents_close(self):
        report, client = self.run_operator_plan(
            allow=True, apply=True, process_enters_during_get=True
        )
        self.assertEqual(client.calls, ["workspace.get"])
        self.assertEqual(report["closed"], [])
        self.assertEqual(report["preserved"], [])
        self.assertEqual(report["skipped"].get("process_cwd_active_at_close"), 1)
        self.assertTrue(self.workspace.exists())

    def test_native_close_timeout_keeps_accurate_unknown_and_preserved_head(self):
        report, client = self.run_operator_plan(
            allow=True, apply=True, close_transport_uncertain=True
        )
        self.assertEqual(client.calls, ["workspace.get", "workspace.close"])
        self.assertEqual(report["closed"], [])
        self.assertEqual(len(report["errors"]), 1)
        self.assertEqual(report["errors"][0]["physicalCloseStanding"], "UNKNOWN")
        self.assertTrue(report["errors"][0]["recoveryRequired"])
        self.assertEqual(len(report["preserved"]), 1)
        self.assertEqual(
            self.git("rev-parse", report["preserved"][0]["retentionRef"]), self.head
        )

    def test_operator_revocation_during_sweep_prevents_closure(self):
        report, client = self.run_operator_plan(
            allow=True, apply=True, revoke_during_get=True
        )
        self.assertEqual(client.calls, ["workspace.get"])
        self.assertEqual(report["closed"], [])
        self.assertEqual(report["preserved"], [])
        self.assertEqual(report["skipped"].get("retention_policy_changed"), 1)
        self.assertTrue(self.workspace.exists())

    def test_real_git_apply_preserves_unmerged_source_before_native_close(self):
        report, client = self.run_operator_plan(allow=True, apply=True)
        self.assertEqual(report["closed"], [self.workspace.name])
        self.assertEqual(report["eligibleUnintegrated"], 1)
        self.assertEqual(client.calls, ["workspace.get", "workspace.close"])
        self.assertFalse(self.workspace.exists())
        self.assertEqual(len(report["preserved"]), 1)
        self.assertEqual(
            self.git("rev-parse", report["preserved"][0]["retentionRef"]), self.head
        )
        self.assertEqual(self.git("show", f"{self.head}:new-work"),
                         "valuable isolated research work")
