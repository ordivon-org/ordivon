"""Behavioral regression at the native PG reclaim operator seam.

The Runtime/MCP and PostgreSQL providers are mocked only at their public IO
boundaries; source retention is exercised against an actual isolated Git repo.
No production Workspace or Registry is mutated.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack
from pathlib import Path
import runpy
import sys
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "ordivon-runtime-pg-reclaim"
PG_WORKSPACE_ROOT = Path("/var/lib/ordivon/pg-candidate/workspaces")
FOUR_HOURS_MS = 4 * 60 * 60 * 1000
# runpy does not add the un-suffixed script parent to sys.path.
sys.path.insert(0, str(SCRIPT.parent))


def git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True, text=True, capture_output=True,
    )
    return completed.stdout.strip()


class FakeRuntime:
    def __init__(self, repo: Path, workspace_id: str, head: str, created_ms: int,
                 *, active_job_ids: list[str] | None = None, dirty: bool = False):
        self.workspace = {
            "workspaceId": workspace_id,
            "sourceRepo": str(repo),
            "currentHeadRevision": head,
            "createdAtMs": created_ms,
            "sourceStateDigest": "sha256:" + "f" * 64,
            "activeJobIds": active_job_ids or [],
            "dirty": dirty,
        }
        self.closes = []

    def call_tool(self, name, arguments):
        if name == "workspace.get":
            return dict(self.workspace)
        if name == "workspace.close":
            self.closes.append(dict(arguments))
            return {"closureDisposition": "removed"}
        raise AssertionError("unexpected Runtime Tool: " + name)


class PgNativeReclaimContract(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="runtime-pg-reclaim-spec-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(self.root))
        git(self.root, "init", "-q", "-b", "main")
        git(self.root, "config", "user.name", "Runtime Test")
        git(self.root, "config", "user.email", "runtime-test@example.invalid")
        (self.root / "README").write_text("base\n")
        git(self.root, "add", "README")
        git(self.root, "commit", "-q", "-m", "base")
        self.base = git(self.root, "rev-parse", "HEAD")
        git(self.root, "switch", "-q", "-c", "durable-feature")
        (self.root / "README").write_text("feature\n")
        git(self.root, "commit", "-q", "-am", "feature")
        self.head = git(self.root, "rev-parse", "HEAD")
        git(self.root, "switch", "-q", "main")
        # Not actually under the production Workspace root: this is substituted
        # at the public operator IO seam, never physically passed to Runtime.
        self.workspace_path = self.root / "ws-reclaim-contract"
        git(self.root, "worktree", "add", "-q", "--detach", str(self.workspace_path), self.head)
        self.runtime = FakeRuntime(
            self.root, self.workspace_path.name, self.head,
            int(time.time() * 1000) - 6 * FOUR_HOURS_MS,
        )
        self.module = runpy.run_path(str(SCRIPT), run_name="pg_reclaim_test")

    def invoke(self, jobs=None, *, apply=False, runtime=None, jobs_after=None):
        module_globals = self.module["run"].__globals__
        current = runtime or self.runtime
        args = argparse.Namespace(
            env_file=self.root / "env",
            source_repo=self.root,
            workspace_root=PG_WORKSPACE_ROOT,
            receipt_root=self.root / "receipts",
            lock_file=self.root / "lock",
            min_age_hours=4,
            limit=25,
            apply=apply,
        )
        with ExitStack() as stack:
            snapshots = iter([jobs or {}, jobs_after]) if jobs_after is not None else None
            read_jobs = (lambda _env: next(snapshots)) if snapshots is not None else (lambda _env: jobs or {})
            stack.enter_context(patch.dict(module_globals, {
                "load_environment_file": lambda _path: {
                    "ORDIVON_PG_BIND": "127.0.0.1:9999",
                    "ORDIVON_PG_TOKEN": "test-token",
                },
                "_jobs": read_jobs,
                "_worktrees": lambda _repo, _root: [(self.workspace_path, self.head)],
                "_active_process_cwds": lambda _root: [],
                "connect_compatible": lambda *a, **kw: current,
            }))
            return self.module["run"](args)

    def test_old_clean_workspace_without_any_job_eventually_reclaims(self):
        result = self.invoke(apply=True)
        self.assertEqual(result["closed"], [self.workspace_path.name])
        self.assertEqual(result["errors"], [])
        self.assertEqual(len(self.runtime.closes), 1)

    def test_failed_terminal_job_does_not_permanently_hold_workspace(self):
        old_ms = int(time.time() * 1000) - 5 * FOUR_HOURS_MS
        result = self.invoke({self.workspace_path.name: (old_ms, "failed", 0)}, apply=True)
        self.assertEqual(result["closed"], [self.workspace_path.name])

    def test_lost_terminal_job_does_not_claim_semantic_failure_or_hold_workspace(self):
        old_ms = int(time.time() * 1000) - 5 * FOUR_HOURS_MS
        result = self.invoke({self.workspace_path.name: (old_ms, "lost", 0)}, apply=True)
        self.assertEqual(result["closed"], [self.workspace_path.name])

    def test_nonterminal_job_never_reclaims(self):
        old_ms = int(time.time() * 1000) - 5 * FOUR_HOURS_MS
        result = self.invoke({self.workspace_path.name: (old_ms, None, 1)}, apply=True)
        self.assertEqual(result["closed"], [])
        self.assertEqual(self.runtime.closes, [])

    def test_active_runtime_job_never_reclaims(self):
        self.runtime.workspace["activeJobIds"] = ["job-still-active"]
        result = self.invoke(apply=True)
        self.assertEqual(result["closed"], [])
        self.assertEqual(self.runtime.closes, [])

    def test_recent_created_workspace_never_reclaims(self):
        self.runtime.workspace["createdAtMs"] = int(time.time() * 1000) - 30_000
        result = self.invoke(apply=True)
        self.assertEqual(result["closed"], [])

    def test_non_main_but_durably_referenced_git_head_is_preserved(self):
        self.assertNotEqual(self.base, self.head)
        self.assertEqual(git(self.root, "rev-parse", "main"), self.base)
        result = self.invoke(apply=True)
        self.assertEqual(result["closed"], [self.workspace_path.name])

    def test_unanchored_detached_commit_is_not_reclaimed(self):
        git(self.root, "branch", "-D", "durable-feature")
        result = self.invoke(apply=True)
        self.assertEqual(result["closed"], [])
        self.assertEqual(self.runtime.closes, [])

    def test_recent_directory_ctime_is_not_retention_authority(self):
        # The freshly created directory's st_ctime is recent; the Runtime
        # committed createdAtMs is old and no consumer currently owns it.
        self.assertGreater(self.workspace_path.stat().st_ctime, time.time() - 60)
        result = self.invoke(apply=True)
        self.assertEqual(result["closed"], [self.workspace_path.name])


    def test_pg_job_projection_change_during_apply_cannot_reclaim(self):
        new_job_ms = int(time.time() * 1000) - 500
        result = self.invoke(
            apply=True,
            jobs_after={self.workspace_path.name: (new_job_ms, "failed", 0)},
        )
        self.assertEqual(result["closed"], [])
        self.assertEqual(self.runtime.closes, [])

    def test_runtime_source_digest_drift_cannot_reclaim(self):
        class ChangedRuntime(FakeRuntime):
            reads = 0

            def call_tool(self, name, arguments):
                if name == "workspace.get":
                    self.reads += 1
                    if self.reads == 2:
                        self.workspace["sourceStateDigest"] = "sha256:" + "a" * 64
                return super().call_tool(name, arguments)

        changed = ChangedRuntime(self.root, self.workspace_path.name, self.head,
                                 self.runtime.workspace["createdAtMs"])
        result = self.invoke(runtime=changed, apply=True)
        self.assertEqual(result["closed"], [])
        self.assertEqual(changed.closes, [])

    def test_runtime_observation_failure_is_error_not_closure(self):
        class UnavailableRuntime:
            def call_tool(self, name, arguments):
                raise RuntimeError("Runtime unavailable")

        result = self.invoke(runtime=UnavailableRuntime(), apply=True)
        self.assertEqual(result["closed"], [])
        self.assertEqual(len(result["errors"]), 1)

    def test_dirty_runtime_workspace_cannot_reclaim(self):
        self.runtime.workspace["dirty"] = True
        result = self.invoke(apply=True)
        self.assertEqual(result["closed"], [])
        self.assertEqual(self.runtime.closes, [])


if __name__ == "__main__":
    unittest.main()
