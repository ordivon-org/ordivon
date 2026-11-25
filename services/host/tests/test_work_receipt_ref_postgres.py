"""Native Work receipt compatibility and replay tests for a disposable PG."""

from __future__ import annotations

import os
import subprocess
import sys
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from queue import Queue
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from ordivon_host_v2.canonical_json import canonical_digest
from ordivon_host_v2.errors import ConflictError
from ordivon_host_v2.health.receipt_roots import count_invalid_work_receipt_roots
from ordivon_host_v2.references.actor_store import ActorReferenceStore
from ordivon_host_v2.service import HostV2
from ordivon_host_v2.work_inputs import (
    ActorKind,
    ActorRefInput,
    WorkCreateInput,
    WorkSnapshotInput,
    WorkState,
)
from ordivon_host_v2.work_receipt_retention import expand_work_receipts_and_fence
from ordivon_host_v2.work_receipts import replay_work_receipt
from ordivon_host_v2.work_store import WorkStore

DSN = os.environ.get("ORDIVON_HOST_V2_RECEIPT_TEST_DSN")


def _database_identity(dsn: str) -> tuple[str, str]:
    # Native identity, not a textual DSN comparison. A test role that cannot
    # establish this identity fails closed; no mutation has yet been issued.
    with psycopg.connect(dsn) as conn:
        row = conn.execute(
            "SELECT current_database(), (pg_control_system()).system_identifier::text"
        ).fetchone()
        if row is None:
            raise RuntimeError("receipt test database identity unobservable")
        return row


def _require_distinct_receipt_database(receipt_dsn: str, ordinary_dsn: str | None) -> None:
    if ordinary_dsn and (
        receipt_dsn == ordinary_dsn
        or _database_identity(receipt_dsn) == _database_identity(ordinary_dsn)
    ):
        raise RuntimeError("receipt lifecycle tests require a distinct database")


@unittest.skipUnless(DSN, "requires dedicated disposable receipt lifecycle PG")
class WorkReceiptTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if DSN is None:
            raise RuntimeError("receipt test database not configured")
        _require_distinct_receipt_database(DSN, os.environ.get("ORDIVON_HOST_V2_TEST_DSN"))

    def setUp(self):
        HostV2(DSN).initialize()
        self.gate_open = False
        self.prefix = f"receipt:{uuid4().hex}"
        self.actor = f"actor:agent:{self.prefix}"
        self.work = f"work:{self.prefix}"
        self.store = WorkStore(DSN)
        ActorReferenceStore(DSN).declare_actor(
            ActorRefInput(actor_ref=self.actor, actor_kind=ActorKind.AGENT),
            client_request_id=f"{self.prefix}:actor",
        )
        self.initial = WorkSnapshotInput(
            objective="synthetic", frontier="r1", established=["repeat", "repeat"]
        )
        self.create_input = WorkCreateInput(
            work_ref=self.work, kind="test", actor_ref=self.actor, initial_snapshot=self.initial
        )

    def key(self, suffix):
        return f"{self.prefix}:{suffix}"

    def create(self, suffix="create"):
        return self.store.create_work(self.create_input, client_request_id=self.key(suffix))

    def commit(self, suffix, revision, state=WorkState.OPEN):
        return self.store.commit_snapshot(
            self.work,
            expected_revision=revision,
            snapshot=WorkSnapshotInput(
                objective="synthetic", frontier=f"r{revision + 1}", established=["a", "a", "b"]
            ),
            actor_ref=self.actor,
            state=state,
            client_request_id=self.key(suffix),
        )

    def stored(self, suffix):
        with psycopg.connect(DSN) as conn:
            return conn.execute(
                "SELECT response FROM command_receipts WHERE client_request_id=%s",
                (self.key(suffix),),
            ).fetchone()[0]

    def replace(self, suffix, response):
        envelope = response.get("envelope") if isinstance(response, dict) else None
        tagged = (
            isinstance(response, dict)
            and response.get("kind") == "ordivon.host-work-receipt-ref-v1"
        )
        root = envelope.get("workRef") if tagged and isinstance(envelope, dict) else None
        revision = envelope.get("revision") if tagged and isinstance(envelope, dict) else None
        with psycopg.connect(DSN) as conn:
            if tagged and not self.gate_open:
                conn.execute(
                    "ALTER TABLE command_receipts DROP CONSTRAINT command_receipt_legacy_only"
                )
                self.gate_open = True
            conn.execute(
                "UPDATE command_receipts SET response=%s,receipt_work_ref=%s,receipt_work_revision=%s "
                "WHERE client_request_id=%s",
                (Jsonb(response), root, revision, self.key(suffix)),
            )

    def tag(self, suffix, response):
        # Construct a versioned fixture independently of the source codec.
        norm = {**response, "admission": "existing"}
        tag = {
            "kind": "ordivon.host-work-receipt-ref-v1",
            "envelope": {k: v for k, v in norm.items() if k != "snapshot"},
            "responseDigest": canonical_digest(norm),
        }
        self.replace(suffix, tag)
        return tag

    def assert_replay(self, actual, original):
        self.assertEqual(actual, {**original, "admission": "existing"})

    def test_mixed_receipts_and_historical_head(self):
        first = self.create()
        second = self.commit("second", 1)
        later_create = self.create("later_create")
        self.assertEqual(later_create["revision"], 2)
        self.assertEqual(later_create["snapshot"], second["snapshot"])
        self.tag("second", second)
        self.tag("later_create", later_create)
        self.replace("create", first)  # old full receipt even under new writer
        self.commit("terminal", 2, WorkState.COMPLETED)
        self.assert_replay(self.create(), first)
        self.assert_replay(self.commit("second", 1), second)
        self.assert_replay(self.create("later_create"), later_create)
        self.assertEqual(self.store.get_work(self.work)["state"], "completed")
        self.assertEqual(self.store.get_work(self.work)["revision"], 3)
        with self.assertRaises(ConflictError):
            self.commit("second", 1, WorkState.COMPLETED)

    def test_corrupt_missing_and_legacy_pruned(self):
        first = self.create()
        second = self.commit("second", 1)
        third = self.commit("third", 2)
        tag = self.tag("second", second)
        self.replace("second", {**tag, "envelope": {**tag["envelope"], "updatedAt": "changed"}})
        with self.assertRaisesRegex(RuntimeError, "response digest differs"):
            self.commit("second", 1)
        # The schema now rejects malformed typed roots before the decoder runs.
        malformed = {**tag, "envelope": {**tag["envelope"], "revision": "2"}}
        with self.assertRaises(psycopg.errors.CheckViolation):
            self.replace("second", malformed)
        with psycopg.connect(DSN, row_factory=dict_row) as conn:
            with self.assertRaisesRegex(RuntimeError, "reference differs"):
                replay_work_receipt(conn, malformed, work_ref=self.work)
        self.replace("second", tag)
        with psycopg.connect(DSN) as conn:
            conn.execute(
                "UPDATE work_snapshots SET payload=jsonb_set(payload,'{frontier}',to_jsonb('bad'::text)) WHERE work_ref=%s AND revision=2",
                (self.work,),
            )
        with self.assertRaisesRegex(RuntimeError, "missing or changed"):
            self.commit("second", 1)
        self.replace("create", first)
        with self.assertRaises(
            (psycopg.errors.ForeignKeyViolation, psycopg.errors.RestrictViolation)
        ):
            with psycopg.connect(DSN) as conn:
                conn.execute(
                    "DELETE FROM work_snapshots WHERE work_ref=%s AND revision=2", (self.work,)
                )
        with psycopg.connect(DSN) as conn:
            conn.execute(
                "DELETE FROM work_snapshots WHERE work_ref=%s AND revision=1", (self.work,)
            )
        self.assert_replay(self.create(), first)
        self.assertEqual(self.store.get_work(self.work)["revision"], third["revision"])

    def test_writer_and_parallel_duplicate(self):
        first = self.create()
        with ThreadPoolExecutor(max_workers=4) as pool:
            responses = list(pool.map(lambda _: self.commit("parallel", 1), range(4)))
        self.assertEqual(sum(r["admission"] == "committed" for r in responses), 1)
        for r in responses:
            self.assertEqual(
                {**r, "admission": "existing"}, {**responses[0], "admission": "existing"}
            )
        self.assertEqual(self.store.get_work(self.work)["revision"], 2)
        for suffix in ("create", "parallel"):
            stored = self.stored(suffix)
            self.assertEqual(stored["kind"], "ordivon.host-work")
            self.assertIn("snapshot", stored)
        self.assert_replay(self.create(), first)

    def test_history_diagnostic_tracks_only_compact_receipt_roots(self):
        first = self.create()
        second = self.commit("second", 1)
        self.commit("third", 2)
        status = HostV2(DSN)
        before_regular = status.status(detail="integrity")["doctor"]
        before_history = status.status(detail="history")["doctor"]
        before_checks = {c["name"]: c["status"] for c in before_regular["checks"]}
        baseline_check = {c["name"]: c for c in before_history["checks"]}[
            "work.receipt_history_roots"
        ]
        baseline_invalid = int(baseline_check["detail"].removeprefix("invalid="))
        tag = self.tag("second", second)

        def history_check(expected_delta):
            regular = status.status(detail="integrity")["doctor"]
            history = status.status(detail="history")["doctor"]
            # Other disposable-suite tests may retain unrelated negative controls.
            # This test measures precisely the effect of its own receipt root.
            self.assertEqual({c["name"]: c["status"] for c in regular["checks"]}, before_checks)
            self.assertEqual(regular["healthy"], before_regular["healthy"])
            self.assertNotIn("work.receipt_history_roots", before_checks)
            check = {c["name"]: c for c in history["checks"]}["work.receipt_history_roots"]
            expected = baseline_invalid + expected_delta
            self.assertEqual(check["detail"], f"invalid={expected}")
            self.assertEqual(check["status"], "error" if expected else "ok")
            if expected_delta:
                self.assertFalse(history["healthy"])
            else:
                self.assertEqual(history["healthy"], before_history["healthy"])

        history_check(0)
        self.replace("second", {**tag, "responseDigest": "sha256:" + "0" * 64})
        history_check(1)
        with self.assertRaises(psycopg.errors.CheckViolation):
            self.replace("second", {**tag, "envelope": []})
        history_check(1)
        self.replace("second", [])
        history_check(1)
        self.replace("second", tag)
        history_check(0)
        # A pinned root cannot disappear. Exact expansion releases only its
        # physical dependency and restores the legacy-only format fence.
        with self.assertRaises(
            (psycopg.errors.ForeignKeyViolation, psycopg.errors.RestrictViolation)
        ):
            with psycopg.connect(DSN) as conn:
                conn.execute(
                    "DELETE FROM work_snapshots WHERE work_ref=%s AND revision=2", (self.work,)
                )
        history_check(0)
        with psycopg.connect(DSN, row_factory=dict_row) as conn:
            self.assertEqual(expand_work_receipts_and_fence(conn), 1)
        self.gate_open = False
        with psycopg.connect(DSN) as conn:
            conn.execute(
                "DELETE FROM work_snapshots WHERE work_ref=%s AND revision IN (1,2)", (self.work,)
            )
        history_check(0)
        self.assert_replay(self.create(), first)
        self.assert_replay(self.commit("second", 1), second)
        with psycopg.connect(DSN, row_factory=dict_row) as conn:
            with self.assertRaisesRegex(RuntimeError, "missing or changed"):
                replay_work_receipt(conn, tag, work_ref=self.work)
        self.assertEqual(self.store.get_work(self.work)["revision"], 3)

    def test_native_guard_and_alembic_rollback(self):
        original = self.create()
        self.commit("second", 1)
        norm = {**original, "admission": "existing"}
        tag = {
            "kind": "ordivon.host-work-receipt-ref-v1",
            "envelope": {k: v for k, v in norm.items() if k != "snapshot"},
            "responseDigest": canonical_digest(norm),
        }
        # A correctly formed, existing root still cannot be stored while gated.
        with self.assertRaises(psycopg.errors.CheckViolation):
            with psycopg.connect(DSN) as conn:
                conn.execute(
                    "UPDATE command_receipts SET response=%s,receipt_work_ref=%s,"
                    "receipt_work_revision=1 WHERE client_request_id=%s",
                    (Jsonb(tag), self.work, self.key("create")),
                )
        self.assert_replay(self.create(), original)

        env = {k: v for k, v in os.environ.items() if k != "ORDIVON_HOST_V2_SQLALCHEMY_URL"}
        env["ORDIVON_HOST_V2_DSN"] = DSN

        def alembic(action, revision):
            return subprocess.run(
                [sys.executable, "-m", "alembic", action, revision],
                env=env,
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

        self.tag("create", original)
        rejected = alembic("downgrade", "0016")
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("restore the validated legacy-only receipt fence", rejected.stderr)
        HostV2(DSN).initialize()
        self.assert_replay(self.create(), original)

        # A same-name but weaker constraint is not the exact rollback fence.
        with psycopg.connect(DSN) as conn:
            conn.execute(
                "ALTER TABLE command_receipts ADD CONSTRAINT command_receipt_legacy_only CHECK (true)"
            )
        try:
            rejected = alembic("downgrade", "0016")
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("restore the validated legacy-only receipt fence", rejected.stderr)
        finally:
            with psycopg.connect(DSN) as conn:
                conn.execute(
                    "ALTER TABLE command_receipts DROP CONSTRAINT command_receipt_legacy_only"
                )

        with psycopg.connect(DSN, row_factory=dict_row) as conn:
            self.assertEqual(expand_work_receipts_and_fence(conn), 1)
        self.gate_open = False
        downgraded = alembic("downgrade", "0016")
        self.assertEqual(downgraded.returncode, 0, downgraded.stderr)
        try:
            with psycopg.connect(DSN) as conn:
                self.assertEqual(
                    conn.execute("SELECT schema_version FROM host_v2_schema").fetchone(), (16,)
                )
                self.assertEqual(
                    conn.execute(
                        "SELECT count(*) FROM information_schema.columns "
                        "WHERE table_name='command_receipts' AND column_name LIKE 'receipt_work_%'"
                    ).fetchone(),
                    (0,),
                )
                conn.execute(
                    "DELETE FROM work_snapshots WHERE work_ref=%s AND revision=1", (self.work,)
                )
            self.assert_replay(self.create(), original)
        finally:
            upgraded = alembic("upgrade", "head")
            self.assertEqual(upgraded.returncode, 0, upgraded.stderr)
        HostV2(DSN).initialize()
        self.assert_replay(self.create(), original)

    def test_already_fenced_is_noop(self):
        original = self.create()
        with psycopg.connect(DSN, row_factory=dict_row) as conn:
            self.assertEqual(expand_work_receipts_and_fence(conn), 0)
        self.assert_replay(self.create(), original)

    def test_expansion_retry_and_caught_failure_are_atomic(self):
        first = self.create()
        second = self.commit("second", 1)
        self.commit("third", 2)
        self.tag("create", first)
        tag = self.tag("second", second)
        self.replace("second", {**tag, "responseDigest": "sha256:" + "0" * 64})
        before = (self.stored("create"), self.stored("second"))
        # A caller may catch a domain error and commit unrelated work.
        # The maintenance operation itself must still be all-or-nothing.
        with psycopg.connect(DSN, row_factory=dict_row) as conn:
            with self.assertRaisesRegex(RuntimeError, "response digest differs"):
                expand_work_receipts_and_fence(conn)
            self.assertEqual(conn.execute("SELECT 1 AS n").fetchone()["n"], 1)
        self.assertEqual((self.stored("create"), self.stored("second")), before)
        self.replace("second", tag)
        with psycopg.connect(DSN, row_factory=dict_row) as conn:
            self.assertEqual(expand_work_receipts_and_fence(conn), 2)
        self.gate_open = False
        with psycopg.connect(DSN, row_factory=dict_row) as conn:
            self.assertEqual(expand_work_receipts_and_fence(conn), 0)
        self.assert_replay(self.create(), first)
        self.assert_replay(self.commit("second", 1), second)

    def test_maintenance_rejects_weak_fence_and_autocommit(self):
        original = self.create()
        self.tag("create", original)
        before = self.stored("create")
        with psycopg.connect(DSN, row_factory=dict_row) as conn:
            conn.execute(
                "ALTER TABLE command_receipts ADD CONSTRAINT command_receipt_legacy_only CHECK (true)"
            )
            try:
                with self.assertRaisesRegex(
                    RuntimeError, "existing legacy-only receipt fence differs"
                ):
                    expand_work_receipts_and_fence(conn)
                self.assertEqual(conn.execute("SELECT 1 AS n").fetchone()["n"], 1)
            finally:
                conn.execute(
                    "ALTER TABLE command_receipts DROP CONSTRAINT command_receipt_legacy_only"
                )
        self.assertEqual(self.stored("create"), before)
        with psycopg.connect(DSN, row_factory=dict_row, autocommit=True) as conn:
            with self.assertRaisesRegex(RuntimeError, "caller-owned transaction"):
                expand_work_receipts_and_fence(conn)
        self.assertEqual(self.stored("create"), before)

    def test_native_database_alias_is_rejected_before_mutation(self):
        # Different connection strings can still select the same authority.
        alias = psycopg.conninfo.make_conninfo(DSN, application_name="receipt-alias-control")
        self.assertNotEqual(alias, DSN)
        with self.assertRaisesRegex(RuntimeError, "require a distinct database"):
            _require_distinct_receipt_database(DSN, alias)
        with self.assertRaisesRegex(RuntimeError, "require a distinct database"):
            _require_distinct_receipt_database(DSN, DSN)

    def test_native_root_shape_mutations_and_foreign_key(self):
        # Independent SQL oracle: no source encoder and no weakening of the
        # production schema. Each negative statement has its own savepoint.
        first = self.create()
        self.commit("second", 1)
        tag = self.tag("create", first)
        with psycopg.connect(DSN, row_factory=dict_row) as conn:
            cases = [
                ("missing pair", tag, None, None, "work.create", "23514"),
                ("half pair", tag, self.work, None, "work.create", "23514"),
                ("wrong revision", tag, self.work, 2, "work.create", "23514"),
                ("wrong work", tag, self.work + ":other", 1, "work.create", "23514"),
                ("wrong operation", tag, self.work, 1, "message.post", "23514"),
                ("legacy with pin", first, self.work, 1, "work.create", "23514"),
                ("missing envelope", {"kind": tag["kind"]}, self.work, 1, "work.create", "23514"),
                (
                    "boolean revision",
                    {**tag, "envelope": {**tag["envelope"], "revision": True}},
                    self.work,
                    1,
                    "work.create",
                    "23514",
                ),
                (
                    "fractional representation",
                    {**tag, "envelope": {**tag["envelope"], "revision": 1.0}},
                    self.work,
                    1,
                    "work.create",
                    "23514",
                ),
                (
                    "missing target",
                    {**tag, "envelope": {**tag["envelope"], "revision": 99}},
                    self.work,
                    99,
                    "work.create",
                    "23503",
                ),
            ]
            for label, response, ref, rev, operation, expected in cases:
                with self.subTest(label=label):
                    with (
                        self.assertRaises(psycopg.Error) as caught,
                        conn.transaction(force_rollback=True),
                    ):
                        conn.execute(
                            "UPDATE command_receipts SET response=%s,receipt_work_ref=%s,"
                            "receipt_work_revision=%s,operation=%s WHERE client_request_id=%s",
                            (Jsonb(response), ref, rev, operation, self.key("create")),
                        )
                    self.assertEqual(caught.exception.sqlstate, expected)
                    actual = conn.execute(
                        "SELECT response,receipt_work_ref,receipt_work_revision,operation "
                        "FROM command_receipts WHERE client_request_id=%s",
                        (self.key("create"),),
                    ).fetchone()
                    self.assertEqual(
                        actual,
                        {
                            "response": tag,
                            "receipt_work_ref": self.work,
                            "receipt_work_revision": 1,
                            "operation": "work.create",
                        },
                    )
        self.assert_replay(self.create(), first)

    def test_native_root_delete_and_pin_both_lock_orders(self):
        first = self.create()
        second = self.commit("second", 1)
        self.commit("third", 2)
        # Gate is open only in the dedicated DB; leave the two candidates full
        # initially. Run real lock races, rather than sleep-based ordering.
        self.tag("create", first)
        self.replace("create", first)
        for suffix, original, pin_first in (("create", first, True), ("second", second, False)):
            with self.subTest(pin_first=pin_first):
                rev = original["revision"]
                norm = {**original, "admission": "existing"}
                tag = {
                    "kind": "ordivon.host-work-receipt-ref-v1",
                    "envelope": {k: v for k, v in norm.items() if k != "snapshot"},
                    "responseDigest": canonical_digest(norm),
                }

                def pin(conn):
                    conn.execute(
                        "UPDATE command_receipts SET response=%s,receipt_work_ref=%s,"
                        "receipt_work_revision=%s WHERE client_request_id=%s",
                        (Jsonb(tag), self.work, rev, self.key(suffix)),
                    )

                def erase(conn):
                    conn.execute(
                        "DELETE FROM work_snapshots WHERE work_ref=%s AND revision=%s",
                        (self.work, rev),
                    )

                pids = Queue()

                def contender():
                    try:
                        with psycopg.connect(DSN) as conn:
                            conn.execute("SET LOCAL lock_timeout='5s'")
                            pids.put(conn.info.backend_pid)
                            (erase if pin_first else pin)(conn)
                    except psycopg.Error as exc:
                        return exc.sqlstate
                    return "committed"

                with ThreadPoolExecutor(max_workers=1) as pool:
                    with psycopg.connect(DSN) as holder:
                        (pin if pin_first else erase)(holder)
                        future = pool.submit(contender)
                        pid = pids.get(timeout=3)
                        with psycopg.connect(DSN, autocommit=True) as observer:
                            deadline = time.monotonic() + 3
                            while time.monotonic() < deadline:
                                blocked = observer.execute(
                                    "SELECT %s=ANY(pg_blocking_pids(%s))",
                                    (holder.info.backend_pid, pid),
                                ).fetchone()[0]
                                if blocked:
                                    break
                                time.sleep(0.01)
                            else:
                                self.fail("native contender did not block on exact holder")
                    self.assertIn(future.result(timeout=6), {"23503", "23001"})
                if pin_first:
                    self.assertEqual(self.stored(suffix), tag)
                    self.assert_replay(self.create(), original)
                    # Release the pin so later fixture cleanup does not need it.
                    self.replace(suffix, original)
                else:
                    self.assertEqual(self.stored(suffix), original)
                    self.assert_replay(self.commit("second", 1), original)

    def test_joined_root_audit_matches_point_oracle_and_checks_native_coordinates(self):
        first = self.create()
        second = self.commit("second", 1)
        self.commit("third", 2)
        tag = self.tag("create", first)
        self.tag("second", second)

        def old_oracle(conn):
            count = 0
            with conn.cursor(name="independent_old_root_oracle") as cursor:
                cursor.execute(
                    "SELECT response FROM command_receipts "
                    "WHERE operation IN ('work.create','work.snapshot.commit') "
                    "AND response IS NOT NULL "
                    "AND response->>'kind' IS DISTINCT FROM 'ordivon.host-work'"
                )
                for row in cursor:
                    try:
                        r = row["response"]
                        replay_work_receipt(conn, r, work_ref=r["envelope"]["workRef"])
                    except RuntimeError, ValueError, TypeError, KeyError:
                        count += 1
            return count

        with psycopg.connect(DSN, row_factory=dict_row) as conn:
            baseline = count_invalid_work_receipt_roots(conn)
            self.assertEqual(old_oracle(conn), baseline)
            with conn.transaction(force_rollback=True):
                conn.execute(
                    "UPDATE command_receipts SET response=jsonb_set(response,'{responseDigest}',"
                    "to_jsonb('invalid'::text)) WHERE client_request_id=%s",
                    (self.key("create"),),
                )
                self.assertEqual(old_oracle(conn), baseline + 1)
                self.assertEqual(count_invalid_work_receipt_roots(conn), baseline + 1)

            # Controlled corruption in a private transaction; the old oracle
            # follows only the JSON envelope, so cannot observe a wrong pin.
            for label, sql, params in [
                ("wrong pin", "receipt_work_revision=2", ()),
                ("absent pin", "receipt_work_ref=NULL,receipt_work_revision=NULL", ()),
                ("foreign operation", "operation='message.post'", ()),
                ("legacy with pin", "response=%s", (Jsonb(first),)),
                (
                    "missing target",
                    "receipt_work_revision=99,response=%s",
                    (Jsonb({**tag, "envelope": {**tag["envelope"], "revision": 99}}),),
                ),
            ]:
                with self.subTest(label=label), conn.transaction(force_rollback=True):
                    conn.execute(
                        "ALTER TABLE command_receipts DROP CONSTRAINT command_receipt_work_root_shape"
                    )
                    conn.execute(
                        "ALTER TABLE command_receipts DROP CONSTRAINT command_receipt_work_root_fk"
                    )
                    conn.execute(
                        "UPDATE command_receipts SET " + sql + " WHERE client_request_id=%s",
                        (*params, self.key("create")),
                    )
                    self.assertEqual(count_invalid_work_receipt_roots(conn), baseline + 1)
                    if label in ("wrong pin", "absent pin", "foreign operation", "legacy with pin"):
                        self.assertEqual(old_oracle(conn), baseline)
            self.assertEqual(count_invalid_work_receipt_roots(conn), baseline)
        self.assert_replay(self.create(), first)
        self.assert_replay(self.commit("second", 1), second)

    def tearDown(self):
        with psycopg.connect(DSN) as conn:
            conn.execute(
                "DELETE FROM command_receipts WHERE client_request_id LIKE %s",
                (self.prefix + ":%",),
            )
            conn.execute("DELETE FROM work_snapshots WHERE work_ref=%s", (self.work,))
            conn.execute("DELETE FROM works WHERE work_ref=%s", (self.work,))
            conn.execute("DELETE FROM actor_refs WHERE actor_ref=%s", (self.actor,))
            if self.gate_open:
                conn.execute(
                    "ALTER TABLE command_receipts ADD CONSTRAINT command_receipt_legacy_only "
                    "CHECK (response->>'kind' IS DISTINCT FROM 'ordivon.host-work-receipt-ref-v1')"
                )
