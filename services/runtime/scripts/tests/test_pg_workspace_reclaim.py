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


class PgReclaimReceiptTests(unittest.TestCase):
    def test_collision_preserves_original_exact_receipt(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as d:
            root = Path(d) / "receipts"
            first = {"observedAtMs": 42, "closed": ["ws-first"]}
            target = Path(mod._store_receipt(root, first))
            original = target.read_bytes()
            with self.assertRaises(FileExistsError):
                mod._store_receipt(root, {"observedAtMs": 42, "closed": ["ws-second"]})
            self.assertEqual(target.read_bytes(), original)
            self.assertEqual(list(root.iterdir()), [target])

    def test_file_sync_failure_leaves_no_named_receipt(self):
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        with TemporaryDirectory() as d:
            root = Path(d) / "receipts"
            with patch.object(mod.os, "fsync", side_effect=OSError("sync failed")):
                with self.assertRaises(OSError):
                    mod._store_receipt(root, {"observedAtMs": 42})
            self.assertEqual(list(root.iterdir()), [])

    def test_post_link_directory_sync_failure_preserves_uncertain_bytes(self):
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        import json
        with TemporaryDirectory() as d:
            root = Path(d) / "receipts"
            original_sync = os.fsync
            def fail_directory(fd):
                import stat
                if stat.S_ISDIR(os.fstat(fd).st_mode):
                    raise OSError("directory sync failed")
                original_sync(fd)
            with patch.object(mod.os, "fsync", side_effect=fail_directory):
                with self.assertRaises(OSError):
                    mod._store_receipt(root, {"observedAtMs": 42, "closed": ["ws-done"]})
            target = root / "pg-reclaim-42.json"
            self.assertEqual(json.loads(target.read_bytes())["closed"], ["ws-done"])
            with self.assertRaises(FileExistsError):
                mod._store_receipt(root, {"observedAtMs": 42, "closed": []})

    def test_receipt_root_alias_and_bad_coordinates_rejected(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as d:
            root = Path(d) / "receipts"
            root.mkdir(mode=0o700)
            alias = Path(d) / "alias"
            alias.symlink_to(root, target_is_directory=True)
            with self.assertRaises(ValueError):
                mod._store_receipt(alias, {"observedAtMs": 42})
            for value in (True, -1, "../outside"):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    mod._store_receipt(root, {"observedAtMs": value})
            self.assertEqual(list(root.iterdir()), [])

    def test_invalid_receipt_namespace_rejected_before_sweep(self):
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from contextlib import redirect_stderr
        from io import StringIO
        with TemporaryDirectory() as d:
            root = Path(d)
            receipts = root / "receipts"
            receipts.mkdir(mode=0o755)
            args = ["reclaim", "--env-file", str(root / "env"),
                    "--source-repo", str(root), "--workspace-root", str(root),
                    "--receipt-root", str(receipts),
                    "--lock-file", str(root / "lock"), "--apply"]
            with patch.object(sys, "argv", args), patch.object(mod, "run") as run, redirect_stderr(StringIO()):
                self.assertNotEqual(mod.main(), 0)
                run.assert_not_called()

    def test_publication_failure_does_not_erase_observed_close(self):
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from contextlib import redirect_stdout, redirect_stderr
        from io import StringIO
        import json
        with TemporaryDirectory() as d:
            root = Path(d)
            args = ["reclaim", "--env-file", str(root / "env"),
                    "--source-repo", str(root), "--workspace-root", str(root),
                    "--receipt-root", str(root / "receipts"),
                    "--lock-file", str(root / "lock"), "--apply"]
            stdout, stderr = StringIO(), StringIO()
            with patch.object(sys, "argv", args), patch.object(mod, "run",
                    return_value={"closed": ["ws-done"], "errors": []}), patch.object(
                    mod, "_store_receipt", side_effect=OSError("disk full")), redirect_stdout(
                    stdout), redirect_stderr(stderr):
                code = mod.main()
            self.assertNotEqual(code, 0)
            result = json.loads(stdout.getvalue())
            self.assertEqual(result["closed"], ["ws-done"])
            self.assertEqual(result["receiptPublicationStanding"], "UNKNOWN")
            self.assertTrue(result["recoveryRequired"])

class PgEnvironmentBindingTests(unittest.TestCase):
    """The input is the ordered native EnvironmentFiles, not a shadow config."""

    def test_later_native_environment_file_overrides_base(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as d:
            root = Path(d)
            base, one, two = (root / name for name in ("base", "one", "two"))
            base.write_text("SOURCE=old\nKEEP=base\n")
            one.write_text("SOURCE=middle\nEXTRA=one\n")
            two.write_text("SOURCE=current\n")
            self.assertEqual(
                mod.effective_environment(base, (one, two)),
                {"SOURCE": "current", "KEEP": "base", "EXTRA": "one"},
            )
            with self.assertRaises(Exception):
                mod.effective_environment(base, (root / "missing",))

    def test_native_property_preserves_order_and_requires_exact_base(self):
        base = Path("/etc/ordivon/base.env")
        overlay = Path("/etc/ordivon/overlay.env")
        obj = {"type": "a(sb)", "data": [[str(base), False], [str(overlay), False]]}
        self.assertEqual(mod.native_environment_files(obj, base), (base, overlay))
        for invalid in (
            {"type": "as", "data": obj["data"]},
            {"type": "a(sb)", "data": [[str(overlay), False], [str(base), False]]},
            {"type": "a(sb)", "data": [[str(base), False], [str(overlay), True]]},
            {"type": "a(sb)", "data": [[str(base), False], ["relative", False]]},
            {"type": "a(sb)", "data": [[str(base), False], ["/etc/*.env", False]]},
            {"type": "a(sb)", "data": [[str(base), False], [str(base), False]]},
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                mod.native_environment_files(invalid, base)

    def test_writer_qualification_binds_effective_source(self):
        old, current = "a" * 64, "b" * 64
        self.assertTrue(mod.qualified_writer(("QUALIFIED_WRITER", current, True), current))
        for row, source in (
            (("QUALIFIED_WRITER", current, True), old),
            (("QUALIFIED_WRITER", current, False), current),
            (("UNQUALIFIED", current, True), current),
            (None, current),
            (("QUALIFIED_WRITER", "bad", True), "bad"),
        ):
            self.assertFalse(mod.qualified_writer(row, source))


class PgWorkspaceReclaimTests(unittest.TestCase):
    def setUp(self):
        self.params = dict(now_ms=10_000_000, created_ms=1_000_000,
                           latest_job_ms=5_000_000, latest_resolution="succeeded",
                           unresolved=0, min_age_ms=3_000_000)

    def test_external_open_file_is_a_workspace_consumer(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory(prefix="ordivon-consumer-fd-") as root:
            workspace = Path(root) / "ws"
            workspace.mkdir()
            payload = workspace / "retained-result"
            payload.write_text("native consumer")
            self.assertFalse(str(Path.cwd()).startswith(str(workspace)))
            with payload.open("rb"):
                self.assertIn(str(payload), mod._observe_process_paths(Path(root), [Path("/proc") / str(os.getpid())]))
            self.assertNotIn(str(payload), mod._observe_process_paths(Path(root), [Path("/proc") / str(os.getpid())]))

    def test_file_mapping_survives_original_descriptor_close(self):
        import mmap
        from tempfile import TemporaryDirectory

        with TemporaryDirectory(prefix="ordivon-consumer-mmap-") as root:
            workspace = Path(root) / "ws"
            workspace.mkdir()
            payload = workspace / "mapped-result"
            payload.write_bytes(b"native mapped consumer")
            with payload.open("rb") as handle:
                mapping = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ,
                                    trackfd=False)
            try:
                self.assertEqual(mapping[:], b"native mapped consumer")
                self.assertIn(str(payload), mod._observe_process_paths(Path(root), [Path("/proc") / str(os.getpid())]))
            finally:
                mapping.close()
            self.assertNotIn(str(payload), mod._observe_process_paths(Path(root), [Path("/proc") / str(os.getpid())]))

    def test_mapping_path_with_whitespace_and_newline_is_not_omitted(self):
        import mmap
        from tempfile import TemporaryDirectory

        with TemporaryDirectory(prefix="ordivon-mapped-path-") as root:
            workspace = Path(root) / "ws"
            workspace.mkdir()
            payload = workspace / "with space\nand newline"
            payload.write_bytes(b"mapped bytes")
            with payload.open("rb") as handle:
                mapping = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ,
                                    trackfd=False)
            try:
                self.assertIn(str(payload), mod._observe_process_paths(Path(root), [Path("/proc") / str(os.getpid())]))
            finally:
                mapping.close()

    def test_mapping_outside_exact_root_is_not_a_workspace_consumer(self):
        import mmap
        from tempfile import TemporaryDirectory

        with TemporaryDirectory(prefix="ordivon-mapped-sibling-") as root:
            workspace = Path(root) / "ws"
            workspace.mkdir()
            other = Path(root) / "ws-other"
            other.mkdir()
            payload = other / "mapped-result"
            payload.write_bytes(b"other bytes")
            with payload.open("rb") as handle:
                mapping = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ,
                                    trackfd=False)
            try:
                self.assertEqual(mod._observe_process_paths(workspace, [Path("/proc") / str(os.getpid())]), [])
            finally:
                mapping.close()

    def test_external_consumer_unknown_is_not_an_empty_census(self):
        from unittest.mock import patch

        own = Path("/proc") / str(os.getpid())
        with patch.object(mod.os, "readlink", side_effect=PermissionError("denied")):
            with self.assertRaises(PermissionError):
                mod._observe_process_paths(Path("/nonexistent-workspace-root"), [own])

    def test_production_process_inventory_failure_is_unknown(self):
        from unittest.mock import patch
        # Path.glob may suppress directory enumeration OSError. Simulate that
        # incomplete legacy projection and require explicit iterdir failure.
        with patch.object(Path, "glob", return_value=iter([])), patch.object(
                Path, "iterdir", side_effect=PermissionError("proc root unreadable")):
            with self.assertRaises(PermissionError):
                mod._active_process_paths(Path("/nonexistent-workspace-root"))

    def test_production_process_census_does_not_hide_denied_pid(self):
        from unittest.mock import patch
        own = Path("/proc") / str(os.getpid())
        with patch.object(Path, "iterdir", side_effect=[
                iter([own]), PermissionError("denied")]) as census:
            with self.assertRaises(PermissionError):
                mod._active_process_paths(Path("/nonexistent-workspace-root"))
            self.assertEqual(census.call_count, 2)

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


class PgReleaseActivityProjectionTests(unittest.TestCase):
    """Explicit scratch-only check against the actual native PG schema."""

    def test_scoped_activity_recheck_matches_global_projection(self):
        dsn = os.getenv("ORDIVON_RECLAIM_TEST_DSN")
        if not dsn:
            self.skipTest("requires disposable reclaim_fixture PostgreSQL database")
        import psycopg
        schema = "reclaim_fixture"
        env = {"ORDIVON_PG_DSN": dsn, "ORDIVON_PG_SCHEMA": schema,
               "ORDIVON_PG_SOURCE_SHA256": "a" * 64}
        with psycopg.connect(dsn, autocommit=True) as conn:
            self.assertEqual(conn.execute("select current_database()").fetchone()[0],
                             "reclaim_fixture")
            self.assertIsNone(conn.execute("select to_regnamespace(%s)", (schema,)).fetchone()[0])
            conn.execute("create schema reclaim_fixture")
            conn.execute("set search_path to reclaim_fixture")
            native_schema = ENTRY.parents[1] / "crates/ordivon-runtime-core/sql/pg_fresh_epoch.sql"
            conn.execute(native_schema.read_text(encoding="utf-8"))
            with self.assertRaisesRegex(RuntimeError, "writer SourceCut"):
                mod._jobs(env, "ws-a")
            conn.execute("""
                INSERT INTO _stage_control(id,state,source_sha256,promotion_allowed)
                VALUES('source','QUALIFIED_WRITER',%s,true)
            """, (env["ORDIVON_PG_SOURCE_SHA256"],))
            def job(job_id, workspace, created, resolution):
                conn.execute("""
                    INSERT INTO jobs(job_id,principal,client_request_id,request_digest,
                        operation_digest,workspace_id,workspace_snapshot_json,
                        execution_plan_json,execution_plan_digest,created_at_ms,
                        desired_state,resolution)
                    VALUES(%s,'fixture',%s,'r','o',%s,'{}','{}','p',%s,'run',%s)
                """, (job_id, job_id, workspace, created, resolution))
            job("old", "ws-a", 10, "succeeded")
            job("foreign", "ws-b", 100, None)
            conn.execute("""
                INSERT INTO job_events(event_id,job_id,event_sequence,event_type,
                    origin,reason_code,detail_json,detail_digest,observed_at_ms)
                VALUES('e','old',1,'fixture','fixture','fixture','{}','d',20)
            """)
            first = mod._jobs(env)
            self.assertEqual(first, {"ws-a": (20, "succeeded", 0),
                                     "ws-b": (100, None, 1)})
            self.assertEqual(mod._jobs(env, "ws-a"), {"ws-a": first["ws-a"]})
            self.assertEqual(mod._jobs(env, "missing"), {})
            job("new", "ws-a", 30, "succeeded")
            self.assertEqual(mod._jobs(env, "ws-a"), {"ws-a": (30, "succeeded", 0)})
            self.assertNotEqual(mod._jobs(env, "ws-a")["ws-a"], first["ws-a"])


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
                          owner_released: bool = True,
                          active_at_get: bool = False,
                          release_binding_override: dict | None = None,
                          later_job_activity: bool = False,
                          inspect_release_subjects: bool = False,
                          inspect_workspace_ids: tuple[str, ...] = (),
                          real_process_observation: bool = False,
                          integration_ref: str = "refs/remotes/origin/main"):
        import argparse
        from unittest.mock import patch
        import time

        future_ms = int((time.time() + 6 * 3600) * 1000)
        policy_path = self.policy_file(
            allow, pinned=pinned, released=owner_released
        )
        if owner_released:
            import json
            data = json.loads(policy_path.read_text())
            rule = next(rule for rule in data["rules"] if rule.get("operatorConsumerReleased"))
            rule["operatorReleaseBinding"] = {
                "createdAtMs": future_ms - 7 * 3600 * 1000,
                "sourceStateDigest": "sha256:" + "f" * 64,
                "latestJobActivityMs": None if job_case == "no_job" else future_ms - 5 * 3600 * 1000,
            }
            if release_binding_override is not None:
                rule["operatorReleaseBinding"].update(release_binding_override)
            policy_path.write_text(json.dumps(data))
        args = argparse.Namespace(
            env_file=self.root / "mock-env",
            source_repo=self.repo,
            workspace_root=self.workspaces,
            min_age_hours=4,
            limit=25,
            apply=apply,
            inspect_release_subjects=inspect_release_subjects,
            inspect_workspace_ids=inspect_workspace_ids,
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
        def observe_processes(root):
            if real_process_observation:
                return mod._observe_process_paths(root, [Path("/proc") / str(os.getpid())])
            return process_cwd_after_get.copy()
        with (
            patch.object(mod, "WORKSPACE_ROOT", self.workspaces.resolve()),
            patch.object(
                mod, "load_environment_file",
                return_value={"ORDIVON_PG_BIND": "127.0.0.1:0", "ORDIVON_PG_TOKEN": "test"},
            ),
            patch.object(mod, "_jobs", side_effect=(
                [job_rows, {self.workspace.name: (future_ms - 4 * 3600 * 1000 - 1,
                                                "succeeded", 0)}]
                if later_job_activity else lambda *_: job_rows
            )),
            patch.object(mod, "_active_process_paths",
                         side_effect=observe_processes),
            patch.object(mod.time, "time", return_value=future_ms / 1000),
            patch.object(mod, "connect_compatible", return_value=client),
        ):
            report = mod.run(args)
        return report, client

    def test_disposition_recheck_uses_each_candidate_not_last_scanned_job(self):
        """Exact release is scoped to one workspace, including at close.

        Interleaving another successful or failed workspace must not change
        whether this workspace's revoked release blocks physical deletion.
        """
        import argparse
        import json
        import time
        from unittest.mock import patch

        self.git("update-ref", "refs/remotes/origin/main", self.head)
        second = self.workspaces / "ws-z-second-candidate"
        self.git("worktree", "add", "--detach", str(second), self.head)
        future_ms = int((time.time() + 6 * 3600) * 1000)
        policy_path = self.policy_file(False, released=True)
        original = json.loads(policy_path.read_text())
        original["rules"].append({
            "workspaceId": second.name, "class": "ephemeral",
            "operatorConsumerReleased": True,
        })
        for rule in original["rules"]:
            rule["operatorReleaseBinding"] = {
                "createdAtMs": future_ms - 7 * 3600 * 1000,
                "sourceStateDigest": "sha256:" + "f" * 64,
                "latestJobActivityMs": future_ms - 5 * 3600 * 1000,
            }
        for first_resolution, second_resolution in (
            ("failed", "succeeded"), ("succeeded", "failed"),
            ("failed", "failed"), ("succeeded", "succeeded"),
        ):
            with self.subTest(first=first_resolution, second=second_resolution):
                policy_path.write_text(json.dumps(original))
                for workspace in (self.workspace, second):
                    if not workspace.exists():
                        self.git("worktree", "add", "--detach", str(workspace), self.head)
                args = argparse.Namespace(
                    env_file=self.root / "mock-env",
                    source_repo=self.repo, workspace_root=self.workspaces,
                    min_age_hours=4, limit=25, apply=True,
                    policy_file=policy_path,
                    integration_ref="refs/remotes/origin/main",
                )
                job_rows = {
                    self.workspace.name: (future_ms - 5 * 3600 * 1000, first_resolution, 0),
                    second.name: (future_ms - 5 * 3600 * 1000, second_resolution, 0),
                }
                closed = []
                def call(name, parameters):
                    workspace_id = parameters["workspaceId"]
                    if name == "workspace.get":
                        # At first candidate's final authorization check,
                        # revoke ONLY its owner disposition.
                        if workspace_id == self.workspace.name:
                            updated = json.loads(policy_path.read_text())
                            updated["rules"][0]["operatorConsumerReleased"] = False
                            policy_path.write_text(json.dumps(updated))
                        return {
                            "workspaceId": workspace_id, "dirty": False,
                            "activeJobIds": [], "sourceRepo": str(self.repo.resolve()),
                            "currentHeadRevision": self.head,
                            "createdAtMs": future_ms - 7 * 3600 * 1000,
                            "sourceStateDigest": "sha256:" + "f" * 64,
                        }
                    self.assertEqual(name, "workspace.close")
                    self.assertFalse(parameters["force"])
                    self.assertFalse(parameters["consumerReleased"])
                    self.git("worktree", "remove", str(self.workspaces / workspace_id))
                    closed.append(workspace_id)
                    return {"closureDisposition": "removed"}

                from unittest.mock import Mock
                client = Mock()
                client.call_tool.side_effect = call
                with (
                    patch.object(mod, "WORKSPACE_ROOT", self.workspaces.resolve()),
                    patch.object(mod, "load_environment_file", return_value={
                        "ORDIVON_PG_BIND": "127.0.0.1:0", "ORDIVON_PG_TOKEN": "test",
                    }),
                    patch.object(mod, "_jobs", return_value=job_rows),
                    patch.object(mod, "_active_process_paths", return_value=[]),
                    patch.object(mod.time, "time", return_value=future_ms / 1000),
                    patch.object(mod, "connect_compatible", return_value=client),
                ):
                    report = mod.run(args)
                expected = [second.name]
                self.assertCountEqual(closed, expected)
                self.assertCountEqual(report["closed"], expected)
                self.assertTrue(self.workspace.exists())
                self.assertFalse(second.exists())

    def test_reason_bearing_git_lock_is_a_protected_root(self):
        # Native Git's lock reason is arbitrary metadata, not a change in
        # the lock's authority. The locked worktree must not be a candidate.
        self.git("update-ref", "refs/remotes/origin/main", self.head)
        for reason in (None, "paused consumer", "multi-line\nreason"):
            with self.subTest(reason=reason):
                args = ["worktree", "lock"]
                if reason is not None:
                    args += ["--reason", reason]
                self.git(*args, str(self.workspace))
                try:
                    self.assertNotIn(
                        (self.workspace, self.head),
                        mod._worktrees(self.repo, self.workspaces),
                    )
                finally:
                    self.git("worktree", "unlock", str(self.workspace))
        self.assertIn((self.workspace, self.head),
                      mod._worktrees(self.repo, self.workspaces))

    def test_reclaim_membership_ignores_local_replace_and_graft_overlays(self):
        # The candidate is not an ancestor of the canonical main.
        # Local replacement/graft overlays must not reverse that result.
        import subprocess

        self.assertTrue(mod._unintegrated_head(self.repo, self.head))
        # Replace the protected main with a synthetic commit whose parent is the
        # unintegrated candidate. The ordinary Git view now says integrated.
        tree = self.git("rev-parse", f"{self.base}^{{tree}}")
        canonical = subprocess.check_output(
            ["git", "-C", str(self.repo), "commit-tree", tree, "-p", self.base],
            input="independent protected main\n", text=True,
        ).strip()
        self.git("update-ref", "refs/remotes/origin/main", canonical)
        replacement = subprocess.check_output(
            ["git", "-C", str(self.repo), "commit-tree", tree, "-p", self.head],
            input="synthetic ancestry overlay\n", text=True,
        ).strip()
        self.git("replace", canonical, replacement)
        try:
            self.assertEqual(subprocess.run(
                ["git", "-C", str(self.repo), "merge-base", "--is-ancestor",
                 self.head, "refs/remotes/origin/main"],
                capture_output=True,
            ).returncode, 0)
            self.assertTrue(mod._unintegrated_head(self.repo, self.head))
        finally:
            self.git("replace", "-d", canonical)

        graft = self.repo / ".git" / "info" / "grafts"
        graft.write_text(f"{canonical} {self.head}\n", encoding="ascii")
        try:
            self.assertEqual(subprocess.run(
                ["git", "-C", str(self.repo),
                 "merge-base", "--is-ancestor", self.head,
                 "refs/remotes/origin/main"], capture_output=True,
            ).returncode, 0)
            self.assertTrue(mod._unintegrated_head(self.repo, self.head))
        finally:
            graft.unlink()

    def test_git_lock_added_during_runtime_get_blocks_close(self):
        # Simulate a consumer creating a native lock after the scan, while
        # the Runtime source-state read is in progress.
        from unittest.mock import patch
        self.git("update-ref", "refs/remotes/origin/main", self.head)
        original = mod._operator_release_binding
        calls = []
        def release(policy, workspace_id):
            answer = original(policy, workspace_id)
            calls.append(workspace_id)
            if len(calls) == 2:
                self.git("worktree", "lock", "--reason", "new consumer",
                         str(self.workspace))
            return answer
        try:
            with patch.object(mod, "_operator_release_binding",
                              side_effect=release):
                report, client = self.run_operator_plan(
                    allow=False, job_case="failed",
                    owner_released=True, apply=True,
                )
            self.assertEqual(report["closed"], [])
            self.assertEqual(client.calls, ["workspace.get"])
            self.assertTrue(self.workspace.exists())
        finally:
            if self.workspace.exists():
                self.git("worktree", "unlock", str(self.workspace))

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
                    allow=False, job_case=outcome, apply=True, owner_released=False
                )
                self.assertEqual(report["eligible"], 0)
                self.assertEqual(
                    report["skipped"].get("needs_owner_disposition"), 1
                )
                self.assertEqual(report["needsOwnerDisposition"], [self.workspace.name])
                self.assertEqual(client.calls, [])
                self.assertTrue(self.workspace.exists())

    def test_successful_job_without_consumer_release_is_not_a_close_candidate(self):
        # A consumer can be paused after a successful tool call, for longer
        # than the quiet period. Integration or a retention ref is not release.
        for integrated in (False, True):
            with self.subTest(integrated=integrated):
                if integrated:
                    self.git("update-ref", "refs/remotes/origin/main", self.head)
                report, client = self.run_operator_plan(
                    allow=True, job_case="succeeded", owner_released=False
                )
                self.assertEqual(report["eligible"], 0)
                self.assertEqual(report["skipped"].get("needs_owner_disposition"), 1)
                self.assertEqual(client.calls, [])
                self.assertTrue(self.workspace.exists())

    def test_successful_job_release_revoked_during_get_blocks_close(self):
        self.git("update-ref", "refs/remotes/origin/main", self.head)
        report, client = self.run_operator_plan(
            allow=False, job_case="succeeded", owner_released=True,
            revoke_during_get=True, apply=True,
        )
        self.assertEqual(report["closed"], [])
        self.assertEqual(report["skipped"].get("owner_disposition_revoked"), 1)
        self.assertEqual(client.calls, ["workspace.get"])
        self.assertTrue(self.workspace.exists())

    def test_release_cannot_authorize_a_different_source_or_generation(self):
        self.git("update-ref", "refs/remotes/origin/main", self.head)
        for changed in ({"sourceStateDigest": "sha256:" + "0" * 64},
                        {"createdAtMs": 1}):
            with self.subTest(changed=changed):
                report, client = self.run_operator_plan(
                    allow=False, apply=True, release_binding_override=changed
                )
                self.assertEqual(report["closed"], [])
                self.assertNotIn("workspace.close", client.calls)
                self.assertTrue(self.workspace.exists())

    def test_later_terminal_job_invalidates_old_release(self):
        self.git("update-ref", "refs/remotes/origin/main", self.head)
        report, client = self.run_operator_plan(
            allow=False, apply=True, later_job_activity=True
        )
        self.assertEqual(report["closed"], [])
        self.assertNotIn("workspace.close", client.calls)
        self.assertTrue(self.workspace.exists())

    def test_inspect_release_subject_is_not_a_release_or_close(self):
        self.git("update-ref", "refs/remotes/origin/main", self.head)
        report, client = self.run_operator_plan(
            allow=False, owner_released=False, inspect_release_subjects=True
        )
        self.assertEqual(report["eligible"], 0)
        self.assertEqual(report["closed"], [])
        self.assertEqual(client.calls, ["workspace.get"])
        self.assertTrue(self.workspace.exists())
        subject, = report["observedReleaseSubjects"]
        self.assertEqual(subject["workspaceId"], self.workspace.name)
        self.assertEqual(subject["operatorReleaseBinding"]["sourceStateDigest"], "sha256:" + "f" * 64)
        self.assertEqual(subject["standing"], "OBSERVED_SUBJECT_NOT_CONSUMER_RELEASE")
        self.assertIs(subject["existingPolicyMatches"], False)
        self.assertNotIn("operatorConsumerReleased", subject)

    def test_targeted_inspection_does_not_observe_unrequested_workspace(self):
        self.git("update-ref", "refs/remotes/origin/main", self.head)
        report, client = self.run_operator_plan(
            allow=False, owner_released=False, inspect_release_subjects=True,
            inspect_workspace_ids=("ws-other-owner",),
        )
        self.assertEqual(client.calls, [])
        self.assertEqual(report["observedReleaseSubjects"], [])
        self.assertEqual(report["unobservedRequestedWorkspaceIds"], ["ws-other-owner"])
        self.assertEqual(report["closed"], [])
        self.assertTrue(self.workspace.exists())

    def test_targeted_inspection_returns_exact_requested_subject(self):
        self.git("update-ref", "refs/remotes/origin/main", self.head)
        report, client = self.run_operator_plan(
            allow=False, owner_released=False, inspect_release_subjects=True,
            inspect_workspace_ids=(self.workspace.name,),
        )
        self.assertEqual(client.calls, ["workspace.get"])
        self.assertEqual([x["workspaceId"] for x in report["observedReleaseSubjects"]],
                         [self.workspace.name])
        self.assertEqual(report["unobservedRequestedWorkspaceIds"], [])
        self.assertEqual(report["eligible"], 0)
        self.assertTrue(self.workspace.exists())

    def test_targeted_inspection_rejects_invalid_scope_before_effect(self):
        from argparse import Namespace
        for apply, inspect, ids in (
            (True, True, ("ws-a",)), (False, False, ("ws-a",)),
            (False, True, ("ws-a", "ws-a")), (False, True, ("../outside",)),
            (False, True, ("ws-a", "ws-b", "ws-c")),
        ):
            with self.subTest(apply=apply, inspect=inspect, ids=ids):
                with self.assertRaises(ValueError):
                    mod._requested_inspection_ids(Namespace(
                        apply=apply, inspect_release_subjects=inspect,
                        inspect_workspace_ids=ids, limit=2,
                    ))

    def test_inspect_changed_activity_returns_no_release_subject(self):
        self.git("update-ref", "refs/remotes/origin/main", self.head)
        report, client = self.run_operator_plan(
            allow=False, owner_released=False, inspect_release_subjects=True,
            later_job_activity=True,
        )
        self.assertEqual(report["observedReleaseSubjects"], [])
        self.assertEqual(report["skipped"].get("release_subject_changed"), 1)
        self.assertEqual(client.calls, ["workspace.get"])
        self.assertTrue(self.workspace.exists())

    def test_legacy_unbound_release_is_not_a_grant(self):
        config = mod._retention_policy(self.policy_file(True, released=True))
        self.assertIsNone(mod._operator_release_binding(config, self.workspace.name))

    def test_boolean_or_malformed_release_binding_is_rejected(self):
        import json
        path = self.policy_file(True, released=True)
        data = json.loads(path.read_text())
        for bad in (True, {"createdAtMs": True, "sourceStateDigest": "sha256:" + "f" * 64,
                           "latestJobActivityMs": None}):
            with self.subTest(binding=bad):
                data["rules"][0]["operatorReleaseBinding"] = bad
                path.write_text(json.dumps(data))
                with self.assertRaisesRegex(ValueError, "release binding"):
                    mod._retention_policy(path)

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

    def test_real_external_file_consumer_blocks_reclamation_decision(self):
        # Real file descriptor, native /proc and Git worktree; only PG/close
        # transport is isolated by the existing operator-plan fixture.
        with (self.workspace / "new-work").open("rb"):
            report, client = self.run_operator_plan(
                allow=True, apply=True, real_process_observation=True,
            )
        self.assertEqual(client.calls, [])
        self.assertEqual(report["closed"], [])
        self.assertEqual(report["skipped"].get("process_path_active"), 1)
        self.assertTrue(self.workspace.exists())

    def test_process_enters_workspace_after_scan_and_prevents_close(self):
        report, client = self.run_operator_plan(
            allow=True, apply=True, process_enters_during_get=True
        )
        self.assertEqual(client.calls, ["workspace.get"])
        self.assertEqual(report["closed"], [])
        self.assertEqual(report["preserved"], [])
        self.assertEqual(report["skipped"].get("process_path_active_at_close"), 1)
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
