"""Disposable native PostgreSQL primitive witnesses, not a Web persistence adapter."""
from __future__ import annotations

import json
import os
from pathlib import Path
import pwd
import queue
import shutil
import subprocess
import tempfile
import threading
import unittest

SCHEMA = """
CREATE TABLE grants(id text PRIMARY KEY, quota bigint NOT NULL CHECK(quota >= 0), revision bigint NOT NULL);
CREATE TABLE receipts(id text PRIMARY KEY, digest text NOT NULL, grant_id text NOT NULL REFERENCES grants(id));
CREATE TABLE notes(id text PRIMARY KEY, effect_id text NOT NULL REFERENCES receipts(id));
CREATE TABLE audits(id text PRIMARY KEY, effect_id text NOT NULL REFERENCES receipts(id));
CREATE TABLE approvals(id text PRIMARY KEY, consumed_at bigint);
"""
SEED = """
TRUNCATE notes, audits, receipts, grants, approvals;
INSERT INTO grants VALUES ('a',2,1),('b',2,1);
INSERT INTO approvals VALUES ('publish',NULL);
"""


class Cluster:
    """Private Unix socket; never inherits a production PG connection target."""
    def __init__(self):
        self.root = Path(tempfile.mkdtemp(prefix="ordivon-web-pg-"))
        self.data = self.root / "data"
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("PG")}
        self.prefix: list[str] = []
        self.started = False
        if os.geteuid() == 0:
            owner = pwd.getpwnam("postgres")
            os.chown(self.root, owner.pw_uid, owner.pw_gid)
            self.prefix = ["runuser", "-u", "postgres", "--"]
            self.user = "postgres"
        else:
            self.user = pwd.getpwuid(os.geteuid()).pw_name
        self.psql = ["psql", "-X", "-qAt", "-h", str(self.root), "-p", "59439",
                     "-U", self.user, "-d", "postgres", "-v", "ON_ERROR_STOP=0"]

    def native(self, *args: str, check=True):
        return subprocess.run(self.prefix + list(args), env=self.env, cwd="/tmp",
                              text=True, capture_output=True, timeout=30, check=check)

    def start(self):
        self.native("initdb", "-D", str(self.data), "-U", self.user,
                    "--auth-local=trust", "--auth-host=reject", "--no-instructions", "--no-locale", "--encoding=UTF8")
        self.native("pg_ctl", "-D", str(self.data), "-l", str(self.root / "postgres.log"),
                    "-o", f"-h '' -k {self.root} -p 59439 -c unix_socket_permissions=0700 -c shared_buffers=16MB -c max_connections=12",
                    "-w", "start")
        self.started = True

    def close(self):
        # Even an unacknowledged start may have created a live postmaster.
        if self.started or (self.data / "postmaster.pid").exists():
            stop = self.native("pg_ctl", "-D", str(self.data), "-m", "fast", "-w", "stop", check=False)
            if stop.returncode or (self.data / "postmaster.pid").exists():
                raise RuntimeError(f"stop not confirmed; preserve {self.root}: {stop.stderr}")
        shutil.rmtree(self.root)
        print("disposable PG stopped and removed", flush=True)


class Session:
    def __init__(self, cluster: Cluster):
        self.proc = subprocess.Popen(cluster.psql, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, env=cluster.env, cwd="/tmp",
                                     text=True, bufsize=1)
        self.lines: queue.Queue[str | None] = queue.Queue()
        def pump():
            assert self.proc.stdout is not None
            for line in self.proc.stdout:
                self.lines.put(line.rstrip("\n"))
            self.lines.put(None)
        self.thread = threading.Thread(target=pump, daemon=True)
        self.thread.start()
        self.step = 0

    def sql(self, statement: str, state="00000") -> list[str]:
        self.step += 1
        marker = f"__END_{self.step}__"
        assert self.proc.stdin is not None
        self.proc.stdin.write(statement.rstrip(";") + ";\n\\echo __STATE__ :SQLSTATE\n\\echo " + marker + "\n")
        self.proc.stdin.flush()
        lines = []
        while True:
            line = self.lines.get(timeout=10)
            if line is None:
                raise RuntimeError("psql exited: " + repr(lines))
            if line == marker:
                break
            lines.append(line)
        states = [x for x in lines if x.startswith("__STATE__ ")]
        if states != ["__STATE__ " + state]:
            raise AssertionError(f"{statement}: expected {state}, got {lines}")
        if state == "00000" and any(x.startswith("ERROR:") for x in lines):
            raise AssertionError(f"unexpected earlier SQL error: {lines}")
        return [x for x in lines if not x.startswith(("__STATE__ ", "ERROR:", "DETAIL:", "HINT:"))]

    def close(self):
        if self.proc.poll() is None:
            assert self.proc.stdin is not None
            try:
                self.proc.stdin.write("\\q\n")
                self.proc.stdin.flush()
                self.proc.wait(timeout=5)
            except (OSError, subprocess.TimeoutExpired):
                self.proc.kill()
                self.proc.wait(timeout=5)
        if self.proc.stdin:
            self.proc.stdin.close()
        if self.proc.stdout:
            self.proc.stdout.close()
        self.thread.join(timeout=2)


def begin(s: Session):
    s.sql("BEGIN ISOLATION LEVEL READ COMMITTED")


def identity(s: Session, effect: str) -> str:
    # Constant namespace prefix separates this experiment's lock keys. Hash
    # collision can conservatively reject unrelated work, never grant ownership.
    assert effect in ("E", "F", "G", "publish")
    return s.sql(f"SELECT pg_try_advisory_xact_lock(hashtextextended('web-r1:' || '{effect}',0))")[0]


def grant(s: Session, g: str, state="00000"):
    assert g in ("a", "b")
    return s.sql(f"SELECT quota,revision FROM grants WHERE id='{g}' FOR UPDATE NOWAIT", state)


def receipt(s: Session, effect: str):
    assert effect in ("E", "F", "G", "publish")
    return s.sql(f"SELECT digest,grant_id FROM receipts WHERE id='{effect}'")


def write(s: Session, effect: str, g: str, revision: int, digest="d"):
    assert effect in ("E", "F", "G", "publish") and g in ("a", "b") and digest in ("d", "other")
    # SQL primitive witness: only the exact grant revision may be consumed.
    assert s.sql(f"UPDATE grants SET quota=quota-1,revision=revision+1 WHERE id='{g}' "
                 f"AND revision={revision} AND quota>0 RETURNING revision") == [str(revision + 1)]
    s.sql(f"INSERT INTO receipts VALUES ('{effect}','{digest}','{g}')")
    s.sql(f"INSERT INTO notes VALUES ('note:{effect}','{effect}')")
    s.sql(f"INSERT INTO audits VALUES ('audit:{effect}','{effect}')")


def observe(s: Session):
    return s.sql("""SELECT (SELECT count(*) FROM receipts),(SELECT count(*) FROM notes),
        (SELECT count(*) FROM audits),(SELECT quota FROM grants WHERE id='a'),
        (SELECT revision FROM grants WHERE id='a'),(SELECT quota FROM grants WHERE id='b'),
        (SELECT revision FROM grants WHERE id='b')""")[0]


class NativeContract(unittest.TestCase):
    cluster: Cluster

    def setUp(self):
        self.a = Session(self.cluster)
        self.addCleanup(self.a.close)
        self.b = Session(self.cluster)
        self.addCleanup(self.b.close)
        self.a.sql(SEED)
        self.assertEqual(observe(self.b), "0|0|0|2|1|2|1")

    def test_grant_only_lock_is_not_effect_identity_fence(self):
        begin(self.a)
        begin(self.b)
        self.assertEqual(grant(self.a, "a"), ["2|1"])
        self.assertEqual(grant(self.b, "b"), ["2|1"])
        self.assertEqual(receipt(self.a, "E"), [])
        self.assertEqual(receipt(self.b, "E"), [])
        write(self.a, "E", "a", 1)
        self.a.sql("COMMIT")
        # The second grant lock did not prevent a stale identity miss.
        self.b.sql("UPDATE grants SET quota=quota-1,revision=revision+1 WHERE id='b'")
        self.b.sql("INSERT INTO receipts VALUES ('E','d','b')", "23505")
        self.b.sql("ROLLBACK")
        self.assertEqual(observe(self.a), "1|1|1|1|2|2|1")
        self.assertEqual(receipt(self.b, "E"), ["d|a"])

    def test_identity_fence_across_grants_and_observe_after_release(self):
        begin(self.a)
        self.assertEqual(identity(self.a, "E"), "t")
        self.assertEqual(grant(self.a, "a"), ["2|1"])
        write(self.a, "E", "a", 1)
        begin(self.b)
        self.assertEqual(identity(self.b, "E"), "f")
        self.assertEqual(receipt(self.b, "E"), [])
        self.b.sql("ROLLBACK")
        self.a.sql("COMMIT")
        begin(self.b)
        self.assertEqual(identity(self.b, "E"), "t")
        self.assertEqual(receipt(self.b, "E"), ["d|a"])
        self.b.sql("ROLLBACK")
        self.assertEqual(observe(self.a), "1|1|1|1|2|2|1")

    def test_disjoint_identity_and_grant_progress(self):
        begin(self.a)
        self.assertEqual(identity(self.a, "E"), "t")
        self.assertEqual(grant(self.a, "a"), ["2|1"])
        write(self.a, "E", "a", 1)
        begin(self.b)
        self.assertEqual(identity(self.b, "F"), "t")
        self.assertEqual(grant(self.b, "b"), ["2|1"])
        write(self.b, "F", "b", 1)
        self.b.sql("COMMIT")
        self.a.sql("COMMIT")
        self.assertEqual(observe(self.b), "2|2|2|1|2|1|2")

    def test_shared_grant_contention_and_stale_revision(self):
        begin(self.a)
        self.assertEqual(identity(self.a, "E"), "t")
        self.assertEqual(grant(self.a, "a"), ["2|1"])
        write(self.a, "E", "a", 1)
        begin(self.b)
        self.assertEqual(identity(self.b, "F"), "t")
        grant(self.b, "a", "55P03")
        self.b.sql("ROLLBACK")
        self.a.sql("COMMIT")
        begin(self.b)
        self.assertEqual(identity(self.b, "F"), "t")
        self.assertEqual(grant(self.b, "a"), ["1|2"])
        self.assertEqual(self.b.sql("UPDATE grants SET quota=quota-1,revision=revision+1 WHERE id='a' AND revision=1 RETURNING revision"), [])
        self.b.sql("ROLLBACK")
        self.assertEqual(observe(self.a), "1|1|1|1|2|2|1")

    def test_rollback_and_release_and_ack_observation(self):
        begin(self.a)
        self.assertEqual(identity(self.a, "publish"), "t")
        self.assertEqual(grant(self.a, "a"), ["2|1"])
        self.a.sql("SELECT id FROM approvals WHERE id='publish' FOR UPDATE NOWAIT")
        self.a.sql("UPDATE approvals SET consumed_at=7 WHERE id='publish' AND consumed_at IS NULL")
        write(self.a, "publish", "a", 1)
        self.assertEqual(observe(self.b), "0|0|0|2|1|2|1")
        self.assertEqual(self.b.sql("SELECT consumed_at IS NULL FROM approvals"), ["t"])
        self.a.sql("ROLLBACK")
        self.assertEqual(observe(self.b), "0|0|0|2|1|2|1")
        begin(self.b)
        self.assertEqual(identity(self.b, "publish"), "t")
        self.assertEqual(grant(self.b, "a"), ["2|1"])
        self.b.sql("UPDATE approvals SET consumed_at=7 WHERE id='publish' AND consumed_at IS NULL")
        write(self.b, "publish", "a", 1)
        self.b.sql("COMMIT")
        # Independent committed observation, not a claim about actual lost network ACK.
        self.assertEqual(receipt(self.a, "publish"), ["d|a"])
        self.assertEqual(self.a.sql("SELECT consumed_at FROM approvals"), ["7"])
        self.assertEqual(observe(self.a), "1|1|1|1|2|2|1")

    def test_selected_sequential_trace_matches_real_sqlite_owner(self):
        trace = [("E","a",1,"d"),("E","b",1,"d"),("E","b",1,"other"),
                 ("F","a",1,"d"),("F","a",2,"d"),("E","a",1,"d"),
                 ("G","a",3,"d"),("G","b",1,"d")]
        actual = []
        for effect, g, revision, digest in trace:
            begin(self.a)
            self.assertEqual(identity(self.a, effect), "t")
            existing = receipt(self.a, effect)
            if existing:
                outcome = "replay" if existing[0].split("|")[0] == digest else "effect-conflict"
                self.a.sql("ROLLBACK")
            else:
                quota, current = map(int, grant(self.a, g)[0].split("|"))
                if quota <= 0 or current != revision:
                    outcome = "agent-grant-changed"
                    self.a.sql("ROLLBACK")
                else:
                    write(self.a, effect, g, revision, digest)
                    self.a.sql("COMMIT")
                    outcome = "new"
            actual.append({"outcome": outcome, "state": observe(self.b)})
        reference = subprocess.run(
            [os.environ.get("NODE", "node"), str(Path(__file__).with_name("sqlite-reference.ts"))],
            text=True, capture_output=True, check=True, timeout=15)
        expected = json.loads(reference.stdout)
        self.assertEqual(actual, expected)
        self.assertEqual([x["outcome"] for x in actual],
                         ["new","replay","effect-conflict","agent-grant-changed","new",
                          "replay","agent-grant-changed","new"])
        print("SQLite/PG selected trace: 8 matching outcomes and committed projections", flush=True)

    def test_exact_text_bytes_are_not_jsonb_normalization(self):
        # Receipt identity uses exact serialized bytes in the SQLite owner.
        result = self.a.sql("""SELECT
          convert_to('{"b":2, "a":1}'::text,'UTF8') =
            convert_to('{"b":2, "a":1}'::text,'UTF8'),
          convert_to('{"b":2, "a":1}'::jsonb::text,'UTF8') =
            convert_to('{"b":2, "a":1}'::text,'UTF8')""")
        self.assertEqual(result, ["t|f"])

    def test_snapshot_after_initial_miss_requires_fresh_read(self):
        self.a.sql("BEGIN ISOLATION LEVEL REPEATABLE READ")
        self.assertEqual(receipt(self.a, "E"), [])
        begin(self.b)
        self.assertEqual(identity(self.b, "E"), "t")
        self.assertEqual(grant(self.b, "a"), ["2|1"])
        write(self.b, "E", "a", 1)
        self.b.sql("COMMIT")
        self.assertEqual(identity(self.a, "E"), "t")
        self.assertEqual(receipt(self.a, "E"), []) # stale snapshot despite acquired lock
        self.a.sql("ROLLBACK")
        begin(self.a)
        self.assertEqual(identity(self.a, "E"), "t")
        self.assertEqual(receipt(self.a, "E"), ["d|a"])
        self.a.sql("ROLLBACK")

    def test_read_committed_recheck_after_initial_miss(self):
        begin(self.a)
        self.assertEqual(receipt(self.a, "E"), [])
        begin(self.b)
        self.assertEqual(identity(self.b, "E"), "t")
        self.assertEqual(grant(self.b, "a"), ["2|1"])
        write(self.b, "E", "a", 1)
        self.b.sql("COMMIT")
        self.assertEqual(identity(self.a, "E"), "t")
        self.assertEqual(receipt(self.a, "E"), ["d|a"])
        self.a.sql("ROLLBACK")
        self.assertEqual(observe(self.b), "1|1|1|1|2|2|1")


if __name__ == "__main__":
    cluster = Cluster()
    try:
        cluster.start()
        setup = Session(cluster)
        try:
            print("native PostgreSQL", setup.sql("SHOW server_version")[0], flush=True)
            setup.sql(SCHEMA)
        finally:
            setup.close()
        NativeContract.cluster = cluster
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(NativeContract))
    finally:
        cluster.close()
    raise SystemExit(0 if result.wasSuccessful() else 1)
