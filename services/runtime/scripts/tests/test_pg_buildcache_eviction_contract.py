"""Focused source-level falsifiers for the PostgreSQL build-cache eviction fence.

The default tests qualify admission and identity conditions. The opt-in native
fixture uses canonical PG DDL and disposable files to verify the physical
cache-only effect and advisory-lock ordering with a controlled MCP response.
Neither lane uses production PG or claims installed source currentness.
"""
from __future__ import annotations

from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import uuid


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


@unittest.skipUnless(os.environ.get("ORDIVON_PG_TEST_DSN"),
                     "requires explicit disposable socket-only PostgreSQL fixture")
class NativeBuildCacheEvictionTests(unittest.TestCase):
    def test_native_pg_fence_and_cache_only_effect(self):
        """Use canonical PG DDL and real files; the MCP reply is a fixture."""
        import psycopg
        from psycopg import sql
        from psycopg.conninfo import conninfo_to_dict

        dsn = os.environ["ORDIVON_PG_TEST_DSN"]
        host = conninfo_to_dict(dsn).get("host", "")
        self.assertTrue(Path(host).is_absolute(), "only a private Unix socket is admissible")
        schema = "test_buildcache_" + uuid.uuid4().hex
        source = "a" * 64
        with psycopg.connect(dsn, autocommit=True) as db:
            self.assertEqual(db.execute("SHOW listen_addresses").fetchone()[0], "")
            db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
            try:
                db.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
                ddl = SCRIPT.parents[1] / "crates/ordivon-runtime-core/sql/pg_fresh_epoch.sql"
                db.execute(ddl.read_text(encoding="utf-8"))
                db.execute(
                    "INSERT INTO _stage_control VALUES ('source','QUALIFIED_WRITER',%s,true)",
                    (source,),
                )
                old = db.execute(
                    "SELECT (EXTRACT(EPOCH FROM clock_timestamp())*1000)::bigint - %s",
                    (5 * 60 * 60 * 1000,),
                ).fetchone()[0]
                db.execute(
                    "INSERT INTO jobs(job_id,principal,client_request_id,request_digest,"
                    "operation_digest,workspace_id,workspace_snapshot_json,execution_plan_json,"
                    "execution_plan_digest,created_at_ms,desired_state,resolution) "
                    "VALUES('j','test','r','request','operation','ws-cache','{}','{}',"
                    "'plan',%s,'run','succeeded')", (old,),
                )
                db.execute(
                    "INSERT INTO attempts(attempt_id,job_id,attempt_number,state,"
                    "termination_intent,launch_token_digest,bundle_path,unit_name,"
                    "created_at_ms,finished_at_ms) VALUES('a','j',1,'succeeded','natural',"
                    "'launch','test','unit',%s,%s)", (old, old),
                )
                db.execute(
                    "INSERT INTO concurrency_reservations(reservation_id,attempt_id,"
                    "global_limit,state,acquired_at_ms,state_observed_at_ms) "
                    "VALUES('res','a',1,'released',%s,%s)", (old, old),
                )
                with tempfile.TemporaryDirectory(prefix="pg-cache-effect-") as tmp:
                    root = Path(tmp)
                    work = root / "workspaces/ws-cache"
                    cache = root / "cache/build/ws-cache"
                    other = root / "cache/build/other"
                    for path in (work, cache, other, root / "workspace-records",
                                 root / "lifecycle-receipts", root / "artifacts",
                                 root / "proc"):
                        path.mkdir(parents=True)
                    (work / "source.txt").write_text("source", encoding="utf-8")
                    (work / ".gitignore").write_text("ignored.out\n", encoding="utf-8")
                    subprocess.run(["/usr/bin/git", "-C", str(work), "init", "-q"],
                                   check=True)
                    subprocess.run(["/usr/bin/git", "-C", str(work), "add", "."], check=True)
                    subprocess.run(
                        ["/usr/bin/git", "-C", str(work), "-c", "user.name=Test",
                         "-c", "user.email=test@local.invalid", "commit", "-qm", "fixture"],
                        check=True,
                    )
                    (work / "ignored.out").write_bytes(b"unique output")
                    (cache / "object.o").write_bytes(b"rebuildable")
                    (other / "object.o").write_bytes(b"other cache")
                    (root / "artifacts/result.bin").write_bytes(b"retained artifact")
                    head = evict.git(work, "rev-parse", "HEAD")
                    (root / "workspace-records/ws-cache.json").write_text(
                        json.dumps({"workspaceId": "ws-cache", "state": "open"}),
                        encoding="utf-8",
                    )
                    env = root / "fixture.env"
                    env.write_text(
                        f"ORDIVON_PG_STORE_ROOT={root}\nORDIVON_PG_SOURCE_SHA256={source}\n"
                        f"ORDIVON_PG_DSN={dsn}\nORDIVON_PG_SCHEMA={schema}\n"
                        "ORDIVON_PG_BIND=127.0.0.1:1\nORDIVON_PG_TOKEN=fixture\n",
                        encoding="utf-8",
                    )
                    args = SimpleNamespace(
                        workspace_id="ws-cache", expected_head=head,
                        expected_source_state_digest=DIGEST, env_file=env, env_overlay=[],
                        store_root=root, apply=False,
                    )
                    reply = {"workspaceId": "ws-cache", "currentHeadRevision": head,
                             "sourceStateDigest": DIGEST, "dirty": False,
                             "activeJobIds": [], "sourceRepo": str(work)}
                    client = SimpleNamespace(call_tool=lambda *_: reply)
                    original_rename, original_rmtree = os.rename, shutil.rmtree
                    original_scan = evict.external_processes_using
                    observations = []

                    def lock_available():
                        with psycopg.connect(dsn) as probe:
                            return probe.execute("SELECT pg_try_advisory_xact_lock(%s)",
                                                 (evict.ADMISSION_LOCK,)).fetchone()[0]

                    def rename_under_fence(src, dst):
                        observations.append(("detach", lock_available()))
                        original_rename(src, dst)

                    def unlink_outside_fence(path):
                        observations.append(("unlink", lock_available()))
                        original_rmtree(path)

                    with (
                        patch.dict(os.environ),
                        patch.object(evict, "connect_compatible", return_value=client),
                        patch.object(evict, "external_processes_using",
                                     side_effect=lambda path: original_scan(path, root / "proc")),
                    ):
                        self.assertEqual(evict.run(args)["effect"], "not_requested")
                        self.assertTrue(cache.is_dir())
                        self.assertEqual(list((root / "lifecycle-receipts").iterdir()), [])
                        args.apply = True
                        db.execute("UPDATE concurrency_reservations SET state='held_orphaned'")
                        with self.assertRaisesRegex(RuntimeError, "recent, unresolved, held"):
                            evict.run(args)
                        self.assertTrue(cache.is_dir())
                        db.execute("UPDATE concurrency_reservations SET state='released'")
                        db.execute("UPDATE jobs SET resolution=NULL")
                        with self.assertRaisesRegex(RuntimeError, "recent, unresolved, held"):
                            evict.run(args)
                        self.assertTrue(cache.is_dir())
                        db.execute("UPDATE jobs SET resolution='succeeded'")
                        self.assertEqual(list((root / "lifecycle-receipts").iterdir()), [])
                        with (
                            patch.object(evict.os, "rename", side_effect=rename_under_fence),
                            patch.object(evict.shutil, "rmtree", side_effect=unlink_outside_fence),
                        ):
                            result = evict.run(args)
                    self.assertEqual(observations, [("detach", False), ("unlink", True)])
                    self.assertEqual(result["effect"], "evicted")
                    self.assertFalse(cache.exists())
                    self.assertFalse(Path(result["detachedPath"]).exists())
                    self.assertEqual((work / "source.txt").read_bytes(), b"source")
                    self.assertEqual((work / "ignored.out").read_bytes(), b"unique output")
                    self.assertEqual((other / "object.o").read_bytes(), b"other cache")
                    self.assertEqual((root / "artifacts/result.bin").read_bytes(), b"retained artifact")
                    self.assertEqual(evict.git(work, "rev-parse", "HEAD"), head)
                    receipt = Path(result["receipt"])
                    self.assertEqual(json.loads((receipt / "plan.json").read_text())["effect"],
                                     "prepared")
                    self.assertEqual(json.loads((receipt / "result.json").read_text()), result)
                    self.assertEqual(db.execute("SELECT resolution FROM jobs").fetchone()[0],
                                     "succeeded")
                    self.assertEqual(db.execute(
                        "SELECT state FROM concurrency_reservations").fetchone()[0], "released")
            finally:
                db.execute("SET search_path TO public")
                db.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


if __name__ == "__main__":
    unittest.main()
