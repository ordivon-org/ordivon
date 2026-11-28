"""Opt-in native PG/FS effect acceptance for the existing cache operator.

Uses a disposable socket-only database and real files. Native MCP replies
and proc inventory are controlled fixtures; no production effect is admitted.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import uuid

from test_pg_buildcache_eviction_contract import DIGEST, SCRIPT, evict


@unittest.skipUnless(os.environ.get("ORDIVON_PG_BUILDCACHE_TEST_DSN"),
                     "requires explicit disposable socket-only PostgreSQL fixture")
class NativeBuildCacheEvictionTests(unittest.TestCase):
    def test_native_pg_fence_and_cache_only_effect(self):
        """Use canonical PG DDL and real files; the MCP reply is a fixture."""
        import psycopg
        from psycopg import sql
        from psycopg.conninfo import conninfo_to_dict

        dsn = os.environ["ORDIVON_PG_BUILDCACHE_TEST_DSN"]
        host = conninfo_to_dict(dsn).get("host", "")
        self.assertTrue(Path(host).is_absolute(), "only a private Unix socket is admissible")
        schema = "test_buildcache_" + uuid.uuid4().hex
        source = "a" * 64
        with psycopg.connect(dsn, autocommit=True) as db:
            self.assertEqual(db.info.dbname, "ordivon_buildcache_test")
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
                    "created_at_ms,finished_at_ms,result_digest) VALUES('a','j',1,'succeeded','natural',"
                    "'launch','test','unit',%s,%s,'result')", (old, old),
                )
                db.execute(
                    "INSERT INTO concurrency_reservations(reservation_id,attempt_id,"
                    "global_limit,state,acquired_at_ms,state_observed_at_ms,released_at_ms) "
                    "VALUES('res','a',1,'released',%s,%s,%s)", (old, old, old),
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

                        # Native mapped consumer survives closing its original FD.
                        import mmap
                        pid = str(os.getpid())
                        proc = root / "proc" / pid
                        proc.mkdir()
                        for name in ("cwd", "fd", "exe", "maps"):
                            (proc / name).symlink_to(Path("/proc") / pid / name)
                        with (cache / "object.o").open("rb") as stream:
                            mapping = mmap.mmap(
                                stream.fileno(), 0, access=mmap.ACCESS_READ, trackfd=False
                            )
                        with mapping:
                            self.assertEqual(mapping[:], b"rebuildable")
                            with self.assertRaisesRegex(RuntimeError, "external process"):
                                evict.run(args)
                            self.assertTrue(cache.is_dir())
                            self.assertEqual(list((root / "lifecycle-receipts").iterdir()), [])
                        self.assertEqual(original_scan(cache, root / "proc"), [])
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
