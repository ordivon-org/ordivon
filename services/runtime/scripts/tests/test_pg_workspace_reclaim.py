"""PG lifecycle adapter: only completed, quiet, known Workspace evidence is closable."""
from __future__ import annotations

from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
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

    def test_does_not_conflate_failed_or_lost_job_with_delivery(self):
        for resolution in ("failed", "lost", "timed_out", "cancelled", None):
            self.assertFalse(mod.eligible(**{**self.params, "latest_resolution": resolution}))

    def test_active_job_blocks(self):
        self.assertFalse(mod.eligible(**{**self.params, "unresolved": 1}))

    def test_no_job_proof_blocks(self):
        self.assertFalse(mod.eligible(**{**self.params, "latest_job_ms": None}))

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

    def policy_file(self, allow: bool, *, pinned: bool = False) -> Path:
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
            "rules": ([{"workspaceId": self.workspace.name, "class": "pinned"}]
                      if pinned else []),
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
                          pinned: bool = False, revoke_during_get: bool = False):
        import argparse
        from unittest.mock import patch
        import time

        future_ms = int((time.time() + 6 * 3600) * 1000)
        policy_path = self.policy_file(allow, pinned=pinned)
        args = argparse.Namespace(
            env_file=self.root / "mock-env",
            source_repo=self.repo,
            workspace_root=self.workspaces,
            min_age_hours=4,
            limit=25,
            apply=apply,
            policy_file=policy_path,
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
                        "dirty": False, "activeJobIds": [],
                        "sourceRepo": str(self.enclosing.repo.resolve()),
                        "currentHeadRevision": self.enclosing.head,
                        "createdAtMs": future_ms - 7 * 3600 * 1000,
                        "sourceStateDigest": "sha256:" + "f" * 64,
                    }
                if name == "workspace.close":
                    assert parameters["force"] is False
                    assert parameters["consumerReleased"] is False
                    assert parameters["expectedSourceStateDigest"] == "sha256:" + "f" * 64
                    self.enclosing.git(
                        "worktree", "remove", str(self.enclosing.workspace),
                    )
                    return {"closureDisposition": "removed"}
                raise AssertionError("unexpected call")

        client = RecordingRuntimeClient(self)
        with (
            patch.object(mod, "WORKSPACE_ROOT", self.workspaces.resolve()),
            patch.object(
                mod, "load_environment_file",
                return_value={"ORDIVON_PG_BIND": "127.0.0.1:0", "ORDIVON_PG_TOKEN": "test"},
            ),
            patch.object(mod, "_jobs", return_value={
                self.workspace.name: (
                    future_ms - 5 * 3600 * 1000, "succeeded", 0
                )
            }),
            patch.object(mod, "_active_process_cwds", return_value=[]),
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
