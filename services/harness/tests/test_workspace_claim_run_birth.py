"""Original Harness PG Run birth → authenticated native Runtime Claim consumer.

The simulated native transport tests lost responses and business state. The
separate Runtime PG18 fixture proves the actual physical close barrier.
"""
from __future__ import annotations

from dataclasses import replace
import tempfile
from pathlib import Path
import unittest

from anc_canonical import canonical_digest
from ordivon_harness.agent_run import HarnessAgentRun
from ordivon_harness.runtime_port import HarnessWorkspaceAdmissionUnavailable
from ordivon_harness.ordivon.model import ScriptedTurnAdapter
from tests.pg_test_support import PostgresAgentRunCase
from tests.test_r3_supported_agent_run import (
    FakeRuntime, completed, contract, execution_binding,
)


class NativeClaimFixture:
    workspace_id = "ws-harness-native-run-birth"
    source_digest = canonical_digest({"original": "workspace source"})

    def __init__(self):
        self.claim: dict | None = None
        self.reserve_count = 0
        self.lost_reserve_reply = False
        self.response_gap = False
        self.fail_reserve_without_commit = False

    def call_tool(self, name, arguments):
        if name == "workspace.get":
            assert arguments["workspaceId"] == self.workspace_id
            return False, {"workspaceId": self.workspace_id, "sourceStateDigest": self.source_digest,
                           "activeJobIds": []}
        if name == "workspace.claim.get":
            if self.claim is None:
                return True, {"error": {"code": "WORKSPACE_NOT_FOUND",
                                        "commitState": "not_committed"}}
            return False, dict(self.claim)
        if name == "workspace.claim.reserve":
            if self.fail_reserve_without_commit:
                raise ConnectionError("native reserve unavailable before commit")
            assert arguments["workspaceId"] == self.workspace_id
            assert arguments["expectedSourceStateDigest"] == self.source_digest
            if self.claim is None:
                self.reserve_count += 1
                self.claim = {
                    "schemaVersion": 1,
                    "claimId": "wclaim-native-once",
                    "workspaceId": self.workspace_id,
                    "clientRequestId": arguments["clientRequestId"],
                    "runRef": arguments["runRef"],
                    "storeRoot": "/isolated/native/runtime/store",
                    "sourceStateDigestAtReserve": self.source_digest,
                    "state": "held",
                }
            if self.lost_reserve_reply:
                self.lost_reserve_reply = False
                raise ConnectionError("response lost after committed native reserve")
            return False, dict(self.claim)
        if name == "workspace.claim.release":
            assert self.claim is not None
            assert arguments["clientRequestId"] == self.claim["clientRequestId"]
            self.claim["state"] = "released"
            return False, dict(self.claim)
        raise AssertionError(f"unexpected native MCP tool {name}")

    def ordinary_close(self, original_file: Path) -> bool:
        if self.claim is not None and self.claim["state"] == "held":
            return False
        original_file.unlink()
        return True


class NativeWorkspaceClaimBirthTests(PostgresAgentRunCase, unittest.TestCase):
    def setUp(self):
        self.set_up_pg()

    def _create(self, suffix, client, *, runtime=None, adapter=None):
        value = contract(suffix, tools=True)
        binding = replace(execution_binding(value), workspace_ref=client.workspace_id)
        run = HarnessAgentRun.create(
            self.pg_dsn, self.pg_schema, value,
            lambda _: adapter or ScriptedTurnAdapter((completed(),)),
            execution_binding=binding,
            runtime=runtime or FakeRuntime(),
            workspace_claim_client=client,
        )
        return run, binding

    def test_active_run_after_terminal_job_keeps_mutable_workspace(self):
        native = NativeClaimFixture()
        value = contract("physical-pin", tools=True)
        binding = replace(execution_binding(value), workspace_ref=native.workspace_id)
        with self.assertRaises(HarnessWorkspaceAdmissionUnavailable):
            HarnessAgentRun.create(
                self.pg_dsn, self.pg_schema, value,
                lambda _: ScriptedTurnAdapter((completed(),)),
                execution_binding=binding, runtime=FakeRuntime(),
            )
        run, _ = self._create("physical-pin", native)
        assert run.status()["status"] == "created"
        # A finished/absent Job is never consumer relinquishment.
        with tempfile.TemporaryDirectory() as tmp:
            original = Path(tmp) / "unique_uncommitted.txt"
            original.write_text("only existing output", encoding="utf-8")
            self.assertFalse(native.ordinary_close(original))
            self.assertEqual(original.read_text(), "only existing output")
        self.assertEqual(native.claim["runRef"], run.harness_run_id)
        self.assertEqual(native.reserve_count, 1)

    def test_lost_commit_reply_reuses_same_original_run_and_native_claim(self):
        native = NativeClaimFixture()
        native.lost_reserve_reply = True
        run, binding = self._create("lost-reserve", native)
        original_id = native.claim["claimId"]
        self.assertEqual(native.reserve_count, 1)
        reopened = HarnessAgentRun.open(
            self.pg_dsn, self.pg_schema, run.harness_run_id,
            lambda _: ScriptedTurnAdapter((completed(),)),
            execution_binding=binding, runtime=FakeRuntime(),
            workspace_claim_client=native,
        )
        self.assertEqual(reopened.harness_run_id, run.harness_run_id)
        self.assertEqual(native.claim["claimId"], original_id)
        self.assertEqual(native.reserve_count, 1)
        # The original stable Run key rejects a swapped Workspace.
        swapped = replace(binding, workspace_ref="ws-wrong-other")
        with self.assertRaises(HarnessWorkspaceAdmissionUnavailable):
            HarnessAgentRun.open(
                self.pg_dsn, self.pg_schema, run.harness_run_id,
                lambda _: ScriptedTurnAdapter((completed(),)),
                execution_binding=swapped, runtime=FakeRuntime(),
                workspace_claim_client=native,
            )

    def test_normal_completion_can_release_after_verified_delivery(self):
        native = NativeClaimFixture()
        run, _ = self._create("release", native)
        with self.assertRaises(HarnessWorkspaceAdmissionUnavailable):
            run.release_workspace_after_delivery(
                recipient_ack={}, verify_delivered_and_drained=lambda *_: True,
            )
        result = run.run(({ "role": "user", "content": "finish" },))
        self.assertEqual(result.loop_result.stop_code.value, "candidate_completed")
        finalization = run.inspect_finalization_source()
        self.assertEqual(finalization["sourceStanding"], "source-settled")
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "delivered.txt"
            destination.write_text("accepted bytes", encoding="utf-8")
            output_digest = canonical_digest({"bytes": destination.read_text()})
            ack = {"harnessRunId": run.harness_run_id,
                   "runReceiptDigest": finalization["runReceiptDigest"],
                   "accepted": True, "outputDigest": output_digest}
            with self.assertRaises(HarnessWorkspaceAdmissionUnavailable):
                run.release_workspace_after_delivery(
                    recipient_ack=ack, verify_delivered_and_drained=lambda *_: False,
                )
            self.assertEqual(native.claim["state"], "held")
            released = run.release_workspace_after_delivery(
                recipient_ack=ack,
                verify_delivered_and_drained=lambda _source, proof: (
                    canonical_digest({"bytes": destination.read_text()}) == proof["outputDigest"]
                ),
            )
            self.assertEqual(released["state"], "released")
            marker = Path(tmp) / "original.txt"
            marker.write_text("releasable")
            self.assertTrue(native.ordinary_close(marker))
            self.assertFalse(marker.exists())

    def test_unconfirmed_reserve_never_exposes_executable_run_and_recovers_same_pg_run(self):
        native = NativeClaimFixture()
        native.fail_reserve_without_commit = True
        value = contract("pending-native-reserve", tools=True)
        binding = replace(execution_binding(value), workspace_ref=native.workspace_id)
        with self.assertRaises(HarnessWorkspaceAdmissionUnavailable):
            HarnessAgentRun.create(
                self.pg_dsn, self.pg_schema, value,
                lambda _: ScriptedTurnAdapter((completed(),)),
                execution_binding=binding, runtime=FakeRuntime(),
                workspace_claim_client=native,
            )
        # No native HELD Claim means NO PG Run birth, not a recoverable
        # caller-selected orphan. Retrying after native recovery is a true
        # first birth, not permission to rebind an existing original Run.
        from ordivon_harness.postgres_store import PostgresHarnessStore
        with PostgresHarnessStore(self.pg_dsn, schema=self.pg_schema) as store:
            with self.assertRaises(KeyError):
                store.load_run(value.harness_run_id)
        self.assertIsNone(native.claim)
        self.assertEqual(native.reserve_count, 0)
        native.fail_reserve_without_commit = False
        recovered = HarnessAgentRun.create(
            self.pg_dsn, self.pg_schema, value,
            lambda _: ScriptedTurnAdapter((completed(),)),
            execution_binding=binding, runtime=FakeRuntime(),
            workspace_claim_client=native,
        )
        self.assertEqual(recovered.harness_run_id, value.harness_run_id)
        self.assertEqual(native.claim["runRef"], value.harness_run_id)
        self.assertEqual(native.reserve_count, 1)
        with PostgresHarnessStore(self.pg_dsn, schema=self.pg_schema) as store:
            projection = store.load_run(value.harness_run_id)
            self.assertEqual(projection.revision, 1)
