"""Native Work receipt compatibility and replay tests for a disposable PG."""

from __future__ import annotations

import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import psycopg
from psycopg.types.json import Jsonb

from ordivon_host_v2.canonical_json import canonical_digest
from ordivon_host_v2.errors import ConflictError
from ordivon_host_v2.references.actor_store import ActorReferenceStore
from ordivon_host_v2.service import HostV2
from ordivon_host_v2.work_inputs import (
    ActorKind,
    ActorRefInput,
    WorkCreateInput,
    WorkSnapshotInput,
    WorkState,
)
from ordivon_host_v2.work_store import WorkStore

DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")


@unittest.skipUnless(DSN, "requires disposable Host PG")
class WorkReceiptTest(unittest.TestCase):
    def setUp(self):
        assert DSN is not None
        HostV2(DSN).initialize()
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
        with psycopg.connect(DSN) as conn:
            conn.execute(
                "UPDATE command_receipts SET response=%s WHERE client_request_id=%s",
                (Jsonb(response), self.key(suffix)),
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
        self.replace("second", {**tag, "envelope": {**tag["envelope"], "revision": True}})
        with self.assertRaisesRegex(RuntimeError, "reference differs"):
            self.commit("second", 1)
        self.replace("second", tag)
        with psycopg.connect(DSN) as conn:
            conn.execute(
                "UPDATE work_snapshots SET payload=jsonb_set(payload,'{frontier}',to_jsonb('bad'::text)) WHERE work_ref=%s AND revision=2",
                (self.work,),
            )
        with self.assertRaisesRegex(RuntimeError, "missing or changed"):
            self.commit("second", 1)
        self.replace("create", first)
        with psycopg.connect(DSN) as conn:
            conn.execute(
                "DELETE FROM work_snapshots WHERE work_ref=%s AND revision IN (1,2)", (self.work,)
            )
        with self.assertRaisesRegex(RuntimeError, "missing or changed"):
            self.commit("second", 1)
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
        self.replace("second", {**tag, "envelope": []})
        history_check(1)
        self.replace("second", [])
        history_check(1)
        self.replace("second", tag)
        history_check(0)
        # Only the disposable fixture loses rows; no real history mutation.
        with psycopg.connect(DSN) as conn:
            conn.execute(
                "DELETE FROM work_snapshots WHERE work_ref=%s AND revision IN (1,2)",
                (self.work,),
            )
        history_check(1)
        with self.assertRaisesRegex(RuntimeError, "missing or changed"):
            self.commit("second", 1)
        self.assert_replay(self.create(), first)
        self.replace("second", second)
        history_check(0)
        self.assert_replay(self.commit("second", 1), second)
        self.assertEqual(self.store.get_work(self.work)["revision"], 3)

    def tearDown(self):
        with psycopg.connect(DSN) as conn:
            conn.execute(
                "DELETE FROM command_receipts WHERE client_request_id LIKE %s",
                (self.prefix + ":%",),
            )
            conn.execute("DELETE FROM work_snapshots WHERE work_ref=%s", (self.work,))
            conn.execute("DELETE FROM works WHERE work_ref=%s", (self.work,))
            conn.execute("DELETE FROM actor_refs WHERE actor_ref=%s", (self.actor,))
