"""Focused source-level falsifiers for the PostgreSQL build-cache eviction fence.

These pure tests never connect to production PG, dispatch work or remove a real
Runtime cache. They validate admission/identity conditions, not physical
concurrency, systemd process identity or installed source currentness.
"""
from __future__ import annotations

from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "ordivon-runtime-pg-buildcache-evict"
sys.path.insert(0, str(SCRIPT.parent))
loader = SourceFileLoader("ordivon_pg_buildcache_eviction_contract", str(SCRIPT))
spec = spec_from_loader(loader.name, loader)
assert spec is not None
evict = module_from_spec(spec)
loader.exec_module(evict)

HEAD = "a" * 40
DIGEST = "sha256:" + "b" * 64


class BuildCacheEvictionContractTests(unittest.TestCase):
    def test_valid_exact_source_identity(self):
        evict.validate_identity("ws-safe_01", HEAD, DIGEST)

    def test_rejects_malformed_or_pathlike_workspace_identity(self):
        for ident in ("", "../outside", "/absolute", "has space", "x" * 97):
            with self.subTest(ident=ident), self.assertRaises(ValueError):
                evict.validate_identity(ident, HEAD, DIGEST)

    def test_rejects_unqualified_git_and_digest(self):
        for head, digest in (("main", DIGEST), (HEAD, "sha256:abc"), (HEAD.upper(), DIGEST)):
            with self.subTest(head=head[:8], digest=digest[:12]), self.assertRaises(ValueError):
                evict.validate_identity("ws-safe", head, digest)

    def test_exact_four_hour_boundary_is_eligible_only_when_settled(self):
        now = 1_000_000_000
        quiet = now - evict.MIN_QUIET_MS
        self.assertTrue(evict.qualified_quiet(quiet, now, 0, 0, "succeeded"))
        self.assertFalse(evict.qualified_quiet(quiet + 1, now, 0, 0, "succeeded"))

    def test_unresolved_held_and_non_success_fail_closed(self):
        now = 1_000_000_000
        quiet = now - evict.MIN_QUIET_MS - 1
        for unresolved, held, resolution in (
            (1, 0, "succeeded"), (0, 1, "succeeded"),
            (0, 0, "failed"), (0, 0, "lost"), (0, 0, None)
        ):
            with self.subTest(case=(unresolved, held, resolution)):
                self.assertFalse(
                    evict.qualified_quiet(quiet, now, unresolved, held, resolution)
                )

    def test_missing_and_future_activity_fail_closed(self):
        now = 1_000_000_000
        for last in (0, -1, now + 1):
            with self.subTest(last=last):
                self.assertFalse(evict.qualified_quiet(last, now, 0, 0, "succeeded"))

    def test_symlink_cache_carrier_is_not_admitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            real = root / "real"
            real.mkdir()
            link = root / "alias"
            link.symlink_to(real, target_is_directory=True)
            self.assertEqual(evict.direct_directory(real), real)
            with self.assertRaises(RuntimeError):
                evict.direct_directory(link)

    def test_git_source_readback_ignores_inherited_foreign_git_authority(self):
        """A foreign GIT_DIR must not make another Git repo the source witness."""
        import os
        import subprocess
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "workspace"
            other = Path(tmp) / "foreign"
            for repo, message in ((first, "expected-workspace"), (other, "attacker")):
                repo.mkdir()
                subprocess.run(["/usr/bin/git", "-C", str(repo), "init", "-q"],
                               check=True, capture_output=True)
                subprocess.run(
                    ["/usr/bin/git", "-C", str(repo),
                     "-c", "user.name=Temporary Test",
                     "-c", "user.email=temporary@local.invalid",
                     "commit", "-q", "--allow-empty", "-m", message],
                    check=True, capture_output=True,
                )
            correct_head = evict.git(first, "rev-parse", "HEAD")
            foreign_head = evict.git(other, "rev-parse", "HEAD")
            self.assertNotEqual(correct_head, foreign_head)
            with patch.dict(os.environ, {
                "GIT_DIR": str(other / ".git"),
                "GIT_WORK_TREE": str(other),
                "GIT_INDEX_FILE": str(other / ".git" / "index"),
            }):
                self.assertEqual(evict.git(first, "rev-parse", "HEAD"), correct_head)
                self.assertEqual(
                    evict.git(first, "status", "--porcelain", "--untracked-files=normal"),
                    "",
                )

    def test_receipt_is_immutable_and_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt = Path(tmp) / "owned" / "plan.json"
            evict.atomic_receipt(receipt, {"effect": "prepared"})
            original = receipt.read_bytes()
            with self.assertRaises(RuntimeError):
                evict.atomic_receipt(receipt, {"effect": "overwritten"})
            self.assertEqual(receipt.read_bytes(), original)


class OpenFdConsumerTests(unittest.TestCase):
    def test_open_fd_inside_cache_is_visible_even_when_cwd_is_elsewhere(self):
        """Observe a real kernel FD without enumerating unrelated CI processes."""
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "build"
            cache.mkdir()
            artifact = cache / "held-output.o"
            artifact.write_bytes(b"compiler-output")

            # The isolated /proc view contains only this test process. The FD
            # directory itself is the real kernel-owned /proc/<pid>/fd.
            pid = str(__import__("os").getpid())
            proc_root = Path(tmp) / "proc"
            proc = proc_root / pid
            proc.mkdir(parents=True)
            (proc / "cwd").symlink_to(Path.cwd(), target_is_directory=True)
            (proc / "fd").symlink_to(Path("/proc") / pid / "fd", target_is_directory=True)
            with artifact.open("rb"):
                consumers = evict.external_processes_using(cache, proc_root)
                self.assertIn(pid, consumers)


class NativePgReclamationRootTests(unittest.TestCase):
    """Opt-in isolated PostgreSQL oracle, using the actual writer schema.

    No production DSN fallback. Terminal Job resolution is not a complete
    census of its Attempts, reservations or physical allocations.
    """

    def test_every_attempt_and_allocation_must_be_settled(self):
        import os
        import uuid

        dsn = os.environ.get("ORDIVON_PG_BUILDCACHE_TEST_DSN")
        if not dsn:
            self.skipTest("explicit private PG build-cache fixture required")
        import psycopg
        from psycopg import sql

        schema = "cache_test_" + uuid.uuid4().hex
        source = "a" * 64
        old = 1
        with psycopg.connect(dsn, autocommit=True) as conn:
            self.assertEqual(conn.info.dbname, "ordivon_buildcache_test")
            conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
            try:
                conn.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
                ddl = SCRIPT.parent.parent / "crates/ordivon-runtime-core/sql/pg_fresh_epoch.sql"
                conn.execute(ddl.read_text())
                conn.execute("INSERT INTO _stage_control VALUES ('source','QUALIFIED_WRITER',%s,true)", (source,))
                conn.execute("""INSERT INTO jobs VALUES
                    ('j','p','req','rd','od','ws','{}','{}','ed',%s,'run','succeeded',NULL,0)""", (old,))
                conn.execute("""INSERT INTO attempts
                    (attempt_id,job_id,attempt_number,state,termination_intent,launch_token_digest,bundle_path,unit_name,created_at_ms,result_digest,finished_at_ms)
                    VALUES ('latest','j',2,'succeeded','natural','ld','b','u2',%s,'result',%s),
                           ('earlier','j',1,'lost','natural','ld','b','u1',%s,'result',%s)""",
                    (old, old, old, old))
                conn.execute("""INSERT INTO concurrency_reservations
                    (reservation_id,attempt_id,global_limit,state,acquired_at_ms,state_observed_at_ms,released_at_ms)
                    VALUES ('r2','latest',1,'released',%s,%s,%s),('r1','earlier',1,'released',%s,%s,%s)""",
                    (old, old, old, old, old, old))
                evict.pg_qualification(conn, schema, source, "ws")
                for label, change, restore in (
                    ("older running", "UPDATE attempts SET state='running' WHERE attempt_id='earlier'", "UPDATE attempts SET state='lost' WHERE attempt_id='earlier'"),
                    ("unknown state", "UPDATE attempts SET state='future_state' WHERE attempt_id='earlier'", "UPDATE attempts SET state='lost' WHERE attempt_id='earlier'"),
                    ("orphaned released", "UPDATE attempts SET state='orphaned' WHERE attempt_id='earlier'", "UPDATE attempts SET state='lost' WHERE attempt_id='earlier'"),
                    ("missing reservation", "DELETE FROM concurrency_reservations WHERE attempt_id='earlier'", "INSERT INTO concurrency_reservations VALUES ('r1','earlier',1,'released',1,1,1,NULL)"),
                    ("unknown reservation", "UPDATE concurrency_reservations SET state='future_state' WHERE attempt_id='earlier'", "UPDATE concurrency_reservations SET state='released' WHERE attempt_id='earlier'"),
                    ("active allocation", "INSERT INTO job_allocations VALUES ('earlier','{}','{}','owner','active',1,NULL)", "DELETE FROM job_allocations WHERE attempt_id='earlier'"),
                    ("missing terminal timestamp", "UPDATE attempts SET finished_at_ms=NULL WHERE attempt_id='earlier'", "UPDATE attempts SET finished_at_ms=1 WHERE attempt_id='earlier'"),
                    ("missing result witness", "UPDATE attempts SET result_digest=NULL WHERE attempt_id='earlier'", "UPDATE attempts SET result_digest='result' WHERE attempt_id='earlier'"),
                    ("empty result witness", "UPDATE attempts SET result_digest='' WHERE attempt_id='earlier'", "UPDATE attempts SET result_digest='result' WHERE attempt_id='earlier'"),
                    ("missing reservation release", "UPDATE concurrency_reservations SET released_at_ms=NULL WHERE attempt_id='earlier'", "UPDATE concurrency_reservations SET released_at_ms=1 WHERE attempt_id='earlier'"),
                    ("missing allocation release", "INSERT INTO job_allocations VALUES ('earlier','{}','{}','owner','released',1,NULL)", "DELETE FROM job_allocations WHERE attempt_id='earlier'"),
                    ("terminal job retains current pointer", "UPDATE jobs SET current_attempt_id='latest' WHERE job_id='j'", "UPDATE jobs SET current_attempt_id=NULL WHERE job_id='j'"),
                    ("latest attempt contradicts job", "UPDATE attempts SET state='failed' WHERE attempt_id='latest'", "UPDATE attempts SET state='succeeded' WHERE attempt_id='latest'"),
                    ("resolved job without attempts", "INSERT INTO jobs VALUES ('j0','p','req0','rd','od','ws','{}','{}','ed',1,'run','succeeded',NULL,0)", "DELETE FROM jobs WHERE job_id='j0'"),
                    ("recent reservation release", "UPDATE concurrency_reservations SET released_at_ms=(EXTRACT(EPOCH FROM clock_timestamp())*1000)::bigint WHERE attempt_id='earlier'", "UPDATE concurrency_reservations SET released_at_ms=1 WHERE attempt_id='earlier'"),
                    ("recent allocation release", "INSERT INTO job_allocations VALUES ('earlier','{}','{}','owner','released',1,(EXTRACT(EPOCH FROM clock_timestamp())*1000)::bigint)", "DELETE FROM job_allocations WHERE attempt_id='earlier'"),
                ):
                    with self.subTest(case=label):
                        conn.execute(change)
                        try:
                            with self.assertRaises(RuntimeError):
                                evict.pg_qualification(conn, schema, source, "ws")
                        finally:
                            conn.execute(restore)
                        evict.pg_qualification(conn, schema, source, "ws")
                self.assert_post_lock_snapshot(conn, dsn, schema, source)
                self.assert_source_identity_after_lock(conn, dsn, schema, source)
            finally:
                conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


    def assert_post_lock_snapshot(self, conn, dsn, schema, source):
        """Real two-connection admission race; filesystem/MCP effect is not invoked."""
        from concurrent.futures import ThreadPoolExecutor
        from types import SimpleNamespace
        from unittest.mock import patch
        import time
        import psycopg
        from psycopg.conninfo import make_conninfo

        # A deployment may override the session isolation default. A waiting
        # RR transaction can freeze its snapshot before the lock is granted.
        rr_dsn = make_conninfo(dsn, options=r"-c default_transaction_isolation=repeatable\ read")
        with psycopg.connect(rr_dsn, autocommit=True) as probe:
            self.assertEqual(probe.execute("SHOW default_transaction_isolation").fetchone()[0],
                             "repeatable read")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("cache/build", "workspace-records", "workspaces"):
                (root / name).mkdir(parents=True)
            cache = root / "cache/build/ws"
            cache.mkdir()
            args = SimpleNamespace(workspace_id="ws", expected_head=HEAD,
                expected_source_state_digest=DIGEST, env_file=root / "unused",
                env_overlay=[], store_root=root, apply=False)
            env = {"ORDIVON_PG_STORE_ROOT": str(root), "ORDIVON_PG_SOURCE_SHA256": source,
                   "ORDIVON_PG_DSN": rr_dsn, "ORDIVON_PG_SCHEMA": schema}
            with (patch.object(evict, "effective_environment", return_value=env),
                  patch.object(evict, "native_workspace_snapshot"),
                  patch.object(evict, "assert_source_and_cache", return_value=cache),
                  patch.object(evict, "external_processes_using", return_value=[]),
                  ThreadPoolExecutor(max_workers=1) as pool):
                with conn.transaction():
                    conn.execute("SELECT pg_advisory_xact_lock(%s)", (evict.ADMISSION_LOCK,))
                    conn.execute("UPDATE attempts SET state='running' WHERE attempt_id='earlier'")
                    future = pool.submit(evict.run, args)
                    with psycopg.connect(dsn, autocommit=True) as monitor:
                        deadline = time.monotonic() + 8
                        while True:
                            waiters = monitor.execute(
                                "SELECT count(*) FROM pg_locks WHERE locktype='advisory' AND NOT granted"
                            ).fetchone()[0]
                            if waiters:
                                break
                            if time.monotonic() >= deadline:
                                self.fail("candidate never waited on the native admission lock")
                            time.sleep(0.02)
                # Writer commits while the candidate waits; qualification
                # must see the newly live Attempt, not the prior settled row.
                try:
                    with self.assertRaisesRegex(RuntimeError, "unqualified PG"):
                        future.result(timeout=10)
                finally:
                    conn.execute("UPDATE attempts SET state='lost' WHERE attempt_id='earlier'")
                self.assertTrue(cache.is_dir())
                self.assertEqual(evict.run(args)["effect"], "not_requested")


    def assert_source_identity_after_lock(self, conn, dsn, schema, source):
        """A current source observation must not precede the admission fence."""
        from concurrent.futures import ThreadPoolExecutor
        from types import SimpleNamespace
        from unittest.mock import patch
        import time
        import psycopg

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("cache/build/ws", "workspace-records", "workspaces/ws"):
                (root / name).mkdir(parents=True)
            cache = root / "cache/build/ws"
            args = SimpleNamespace(workspace_id="ws", expected_head=HEAD,
                expected_source_state_digest=DIGEST, env_file=root / "unused",
                env_overlay=[], store_root=root, apply=False)
            env = {"ORDIVON_PG_STORE_ROOT": str(root), "ORDIVON_PG_SOURCE_SHA256": source,
                   "ORDIVON_PG_DSN": dsn, "ORDIVON_PG_SCHEMA": schema,
                   "ORDIVON_PG_BIND": "fixture", "ORDIVON_PG_TOKEN": "fixture"}
            observed = {"workspaceId": "ws", "currentHeadRevision": HEAD,
                        "sourceStateDigest": DIGEST, "dirty": False,
                        "activeJobIds": [], "sourceRepo": str(root)}

            def read_source(tool, request):
                self.assertEqual(tool, "workspace.get")
                self.assertEqual(request["workspaceId"], "ws")
                return dict(observed)

            with (patch.object(evict, "effective_environment", return_value=env),
                  patch.object(evict, "connect_compatible",
                               return_value=SimpleNamespace(call_tool=read_source)),
                  patch.object(evict, "assert_source_and_cache", return_value=cache),
                  patch.object(evict, "external_processes_using", return_value=[]),
                  ThreadPoolExecutor(max_workers=1) as pool):
                # A different source digest can coexist with the same HEAD and
                # clean projection (e.g. changed Git index flags). The original
                # source observation is stale once this holder commits.
                with conn.transaction():
                    conn.execute("SELECT pg_advisory_xact_lock(%s)", (evict.ADMISSION_LOCK,))
                    future = pool.submit(evict.run, args)
                    with psycopg.connect(dsn, autocommit=True) as monitor:
                        deadline = time.monotonic() + 8
                        while True:
                            waiters = monitor.execute(
                                "SELECT count(*) FROM pg_locks WHERE locktype='advisory' AND NOT granted"
                            ).fetchone()[0]
                            if waiters:
                                break
                            if time.monotonic() >= deadline:
                                self.fail("candidate never waited on the native admission lock")
                            time.sleep(0.02)
                    observed["sourceStateDigest"] = "sha256:" + "f" * 64
                    self.assertNotEqual(observed["sourceStateDigest"], DIGEST)
                with self.assertRaisesRegex(RuntimeError, "Workspace witness changed"):
                    future.result(timeout=10)
                self.assertTrue(cache.is_dir())
                observed["sourceStateDigest"] = DIGEST
                self.assertEqual(evict.run(args)["effect"], "not_requested")


if __name__ == "__main__":
    unittest.main()
