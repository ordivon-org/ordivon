"""Real PostgreSQL Harness Store consumer and CAS equivalence tests.

Supply HARNESS_PG_TEST_DSN pointing to an isolated test database.  These tests
create and drop only uniquely named schemas; they never modify Host/Runtime
schemas or rely on an SQLite fallback.
"""
from __future__ import annotations

from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import os
import unittest
import uuid

from anc_canonical import canonical_digest
from ordivon_harness.working_view import AgentWorkingSetTransitionProposal, compile_working_view
import tests.test_pc13_agent_owned_working_set as pc13_fixture
import tests.test_r3_supported_agent_run as supported_run_fixture
from ordivon_harness.agent_run import HarnessAgentRun
from ordivon_harness.ordivon.model import ScriptedTurnAdapter
import psycopg
from psycopg import sql

from ordivon_harness.postgres_store import PostgresHarnessStore
from ordivon_harness.store_errors import (
    HarnessEventConflict, HarnessLeaseHeld, HarnessRevisionConflict,
)
from ordivon_harness.protocol import (
    HarnessRecoveryConsequence, HarnessToolStepIntent, HarnessToolStepReceipt,
    HarnessToolStepStatus,
)
from ordivon_harness.ordivon.run_store_port import HarnessSuperseded
import tests.test_p0_sqlite_tool_store as tool_fixture
from ordivon_harness.store import (
    HarnessEventAdmission, HarnessEventWrite, HarnessStore,
)
from ordivon_harness.ordivon.run_continuity import EventSourcedRunContinuity
from tests.test_p0_sqlite_provider_store import MutableClock, contract, state


@unittest.skipUnless(os.environ.get("HARNESS_PG_TEST_DSN"), "real PG DSN not supplied")
class PostgresHarnessStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dsn = os.environ["HARNESS_PG_TEST_DSN"]
        self.schema = "hpg_" + uuid.uuid4().hex[:18]
        self.store = PostgresHarnessStore(self.dsn, schema=self.schema, initialize=True)
        self.addCleanup(self._cleanup_db)

    def _cleanup_db(self) -> None:
        self.store.close()
        with psycopg.connect(self.dsn, autocommit=True) as conn:
            conn.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(self.schema)))

    def test_native_cli_pg_only_run_status_inspect_and_recovery(self) -> None:
        """CLI is a real consumer: no SQLite file can be created in PG-only mode."""
        import contextlib
        import io
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from ordivon_harness.cli import main as cli_main
        from tests.test_p0_sqlite_agent_loop import (
            contract as cli_contract, needs_input_result, completed_result,
        )

        from ordivon_harness.core_contracts import HarnessPrivacyPolicy
        run = replace(
            cli_contract("pg-cli-first-class"),
            privacy=HarnessPrivacyPolicy(
                content_policy="bounded-private-content",
                allow_model_content=True,
                allow_tool_content=False,
            ),
        )
        with tempfile.TemporaryDirectory() as root_dir:
            root = Path(root_dir)
            contract_file = root / "contract.json"
            contract_file.write_text(json.dumps(run.to_dict()), encoding="utf-8")
            def invoke(*args: str):
                output = io.StringIO()
                error = io.StringIO()
                with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
                    code = cli_main(args)
                return code, json.loads(output.getvalue()) if output.getvalue() else None, error.getvalue()

            with patch.dict(os.environ, {
                "ORDIVON_HARNESS_PG_ONLY": "1",
                "ORDIVON_HARNESS_PG_DSN": self.dsn,
                "ORDIVON_HARNESS_PG_SCHEMA": self.schema,
            }):
                code, initialized, error = invoke("store-init")
                self.assertEqual(code, 0, error)
                self.assertEqual(initialized["backend"], "postgresql")
                with patch(
                    "ordivon_harness.independent_cli._adapter",
                    return_value=ScriptedTurnAdapter((needs_input_result("pg-cli-first-class-pause"),)),
                ):
                    code, paused, error = invoke("run", str(contract_file), "--message", "test")
                self.assertEqual(code, 0, error)
                self.assertEqual(paused["backend"], "postgresql")
                self.assertIsNone(paused["stateRoot"])
                self.assertEqual(paused["run"]["status"], "paused")
                code, status, error = invoke("status", run.harness_run_id)
                self.assertEqual(code, 0, error)
                self.assertEqual(status["run"]["status"], "paused")
                code, inspected, error = invoke("inspect", run.harness_run_id)
                self.assertEqual(code, 0, error)
                self.assertEqual(inspected["contract"]["harnessRunId"], run.harness_run_id)
                with patch(
                    "ordivon_harness.independent_cli._adapter",
                    return_value=ScriptedTurnAdapter((completed_result("pg-cli-first-class-resume"),)),
                ):
                    code, completed, error = invoke(
                        "resume", run.harness_run_id, "--message", "continuation"
                    )
                self.assertEqual(code, 0, error)
                self.assertEqual(completed["run"]["status"], "completed")
                self.assertEqual(completed["backend"], "postgresql")
                code, events, error = invoke("store-events", run.harness_run_id)
                self.assertEqual(code, 0, error)
                self.assertGreater(len(events["events"]), 2)
            self.assertEqual(sorted(p.name for p in root.iterdir()), ["contract.json"])

    def test_pg_only_cli_missing_dsn_fails_closed_before_sqlite(self) -> None:
        import contextlib
        import io
        from unittest.mock import patch
        from ordivon_harness.cli import main as cli_main
        with patch.dict(os.environ, {"ORDIVON_HARNESS_PG_ONLY": "1"}, clear=True):
            error = io.StringIO()
            with contextlib.redirect_stderr(error):
                code = cli_main(["store-init"])
            self.assertEqual(code, 1)
            self.assertIn("SQLite fallback prohibited", error.getvalue())

    def test_exact_contract_and_immutable_cas_object(self) -> None:
        self.assertIsInstance(self.store, HarnessStore)
        run = contract()
        self.assertEqual(self.store.create_run(run), HarnessEventAdmission.CREATED)
        self.assertEqual(self.store.create_run(run), HarnessEventAdmission.EXISTING)
        raw = {"message": "postgres only", "count": 7}
        obj = self.store.put_object(raw, kind="harness-test-data")
        self.assertEqual(self.store.inspect_object(obj.digest), obj)
        self.assertEqual(self.store.get_object(obj.digest, expected_kind="harness-test-data"), raw)
        self.assertEqual(self.store.load_run(run.harness_run_id).revision, 1)
        with self.assertRaises(HarnessEventConflict):
            self.store.create_run(replace(run, caller_run_ref="caller:another"))
        self.assertTrue(self.store.doctor()["healthy"])
        with PostgresHarnessStore(self.dsn, schema=self.schema) as reopened:
            self.assertEqual(reopened.get_object(obj.digest), raw)
            self.assertEqual(reopened.create_run(run), HarnessEventAdmission.EXISTING)

    def test_two_connections_lease_revision_cas_and_exact_response_loss_replay(self) -> None:
        run = contract()
        self.store.create_run(run)
        with PostgresHarnessStore(self.dsn, schema=self.schema) as rival:
            first = self.store.acquire_run_lease(
                run.harness_run_id, owner_id="worker:one", ttl_ms=5000, now_ms=10,
            )
            with self.assertRaises(HarnessLeaseHeld):
                rival.acquire_run_lease(run.harness_run_id, owner_id="worker:two", ttl_ms=5000, now_ms=11)
            event = HarnessEventWrite(
                event_id="event:pg-consumer-cas", event_kind="harness.trace-recorded",
                data={"trace": canonical_digest({"kind": "PG"})},
                recorded_at_ms=run.created_at_ms+1,
            )
            result = self.store.append_events(
                harness_run_id=run.harness_run_id, events=(event,),
                expected_revision=first.run_revision, lease=first,
                lease_checked_at_ms=11,
            )
            self.assertEqual(result, HarnessEventAdmission.CREATED)
            self.assertEqual(len(rival.list_run_events(run.harness_run_id)), 2)
            # Exact retry after a lost response is admitted even though the
            # original lease was atomically consumed.
            self.assertEqual(rival.append_events(
                harness_run_id=run.harness_run_id, events=(event,),
                expected_revision=first.run_revision, lease=first,
                lease_checked_at_ms=12,
            ), HarnessEventAdmission.EXISTING)
            with self.assertRaises(HarnessEventConflict):
                rival.append_events(
                    harness_run_id=run.harness_run_id,
                    events=(replace(event, data={"trace": "forged"}),),
                    expected_revision=first.run_revision, lease=first,
                    lease_checked_at_ms=12,
                )
            with self.assertRaises(HarnessRevisionConflict):
                rival.acquire_run_lease(
                    run.harness_run_id, owner_id="worker:two", ttl_ms=5000,
                    now_ms=12, expected_run_revision=1,
                )
            self.assertEqual(self.store.load_run(run.harness_run_id).revision, 2)
            self.assertEqual(self.store.doctor()["leases"], 0)
            self.assertTrue(rival.doctor()["healthy"])

    def test_existing_continuity_port_runs_on_postgres_without_sqlite_state(self) -> None:
        run = contract()
        self.store.create_run(run)
        clock = MutableClock()
        continuity = EventSourcedRunContinuity(self.store, run, clock_ms=clock)
        continuity.bind_state(state())
        self.assertTrue(continuity.binding)
        self.assertTrue(self.store.doctor()["healthy"])
        # New connection replays the exact persisted Agent continuity state.
        with PostgresHarnessStore(self.dsn, schema=self.schema) as reopened:
            resumed = EventSourcedRunContinuity.open(
                reopened, run.harness_run_id, clock_ms=clock,
            )
            self.assertEqual(resumed.binding, continuity.binding)
            self.assertTrue(reopened.doctor()["healthy"])

    def test_agent_working_set_three_revision_cas_replay_after_pg_reopen(self) -> None:
        run = pc13_fixture.cognition_contract("pg-pilot")
        self.store.create_run(run)
        clock = MutableClock()
        continuity = EventSourcedRunContinuity(self.store, run, clock_ms=clock)
        committed_source, pin_b, *_ = pc13_fixture.AgentOwnedWorkingSetTests.prepare(continuity)
        source_view_digest = compile_working_view(committed_source, self.store).digest
        proposal = AgentWorkingSetTransitionProposal(
            next_attempt_id="working-attempt:pg-h06-b",
            pins=(pin_b,),
            basis="native PostgreSQL replan/select/commit",
        )
        first = continuity.apply_working_set_transition(
            proposal,
            source_working_set_digest=committed_source.digest,
            source_model_view_digest=source_view_digest,
        )
        before = len(self.store.list_run_events(run.harness_run_id))
        self.assertEqual(first.pins, proposal.pins)
        with PostgresHarnessStore(self.dsn, schema=self.schema) as reopened:
            resumed = EventSourcedRunContinuity.open(reopened, run.harness_run_id, clock_ms=clock)
            self.assertEqual(resumed.load_current_working_set(), first)
            self.assertEqual(resumed.apply_working_set_transition(
                proposal,
                source_working_set_digest=committed_source.digest,
                source_model_view_digest=source_view_digest,
            ), first)
            self.assertEqual(len(reopened.list_run_events(run.harness_run_id)), before)
            self.assertTrue(resumed.doctor()["healthy"])

    def test_supported_agent_run_uses_postgres_for_create_pause_reopen_resume(self) -> None:
        """Complete caller surface, including recovery, without a SQLite file."""
        clock = supported_run_fixture.FixedClock()
        run = supported_run_fixture.contract("postgres-real")
        active = HarnessAgentRun.create(
            self.dsn, self.schema, run,
            lambda _value: ScriptedTurnAdapter((supported_run_fixture.needs_input(),)),
            clock_ms=clock, monotonic_ms=clock,
        )
        self.assertFalse(hasattr(active, "state_root"))
        paused = active.run(({"role": "user", "content": "start PG vertical slice"},))
        self.assertTrue(paused.paused)
        self.assertEqual(active.status()["status"], "paused")
        resumed = HarnessAgentRun.open(
            self.dsn, self.schema, run.harness_run_id,
            lambda _value: ScriptedTurnAdapter((supported_run_fixture.completed(),)),
            clock_ms=clock, monotonic_ms=clock,
        )
        done = resumed.resume(additional_messages=({"role": "user", "content": "answer"},))
        self.assertEqual(done.loop_result.stop_code.value, "candidate_completed")
        self.assertTrue(resumed.doctor()["healthy"])
        self.assertTrue(self.store.doctor()["healthy"])

    def test_pg_tool_intent_receipt_fencing_survives_reconnection(self) -> None:
        """H04 native Tool consumer, not just an abstract PG event Store."""
        run = tool_fixture.private_tool_contract()
        self.store.create_run(run)
        clock = MutableClock()
        continuity = EventSourcedRunContinuity(self.store, run, clock_ms=clock)
        continuity.bind_state(state())
        binding = continuity.binding
        intent = HarnessToolStepIntent(
            intent_id="harness-tool-step-intent:pg-proof-001",
            harness_run_id=run.harness_run_id,
            assignment_id=binding.assignment_id,
            assignment_generation=binding.assignment_generation,
            assignment_digest=binding.assignment_digest,
            turn_id="turn:pg-proof-001",
            tool_call_id="tool-call:pg-proof-001",
            tool_name="workspace.read",
            tool_call_digest=canonical_digest({"toolCall": "pg-proof"}),
            runtime_operation="workspace.read",
            runtime_arguments_digest=canonical_digest({"relativePath": "README.md"}),
            client_request_id="request:pg-proof-001",
            recovery_consequence=HarnessRecoveryConsequence.OBSERVATION_ONLY,
            created_at_ms=clock(),
        )
        continuity.prepare_tool_step(intent)
        current = continuity.load_current_tool_step()
        self.assertEqual(current.intent, intent)
        fence = current.fence
        assert fence is not None
        continuity.assert_dispatch_fence_current(fence)
        observation = {"schemaVersion": 1, "kind": "pg.test-observation", "status": "observed"}
        clock.advance()
        receipt = HarnessToolStepReceipt(
            receipt_id="harness-tool-step-receipt:pg-proof-001",
            intent_digest=intent.digest, harness_run_id=run.harness_run_id,
            tool_call_id=intent.tool_call_id,
            status=HarnessToolStepStatus.OBSERVED,
            runtime_job_ref="runtime-job:pg-proof-001",
            observation_digest=canonical_digest(observation),
            reconciled=False, created_at_ms=clock(),
        )
        continuity.record_tool_step_receipt(receipt, observation)
        continuity.record_tool_step_receipt(receipt, observation)
        with self.assertRaises(HarnessSuperseded):
            continuity.assert_dispatch_fence_current(fence)
        with PostgresHarnessStore(self.dsn, schema=self.schema) as reopened:
            replayed = EventSourcedRunContinuity.open(reopened, run.harness_run_id, clock_ms=clock)
            self.assertEqual(replayed.load_current_tool_step().receipt, receipt)
            self.assertTrue(replayed.doctor()["healthy"])

    def test_invalid_second_event_rolls_back_entire_pg_batch_and_keeps_lease(self) -> None:
        """A partial event commit must be impossible under native PG transaction."""
        run = contract()
        self.store.create_run(run)
        lease = self.store.acquire_run_lease(
            run.harness_run_id,owner_id="worker:pg-rollback",ttl_ms=2000,now_ms=1
        )
        safe = HarnessEventWrite(
            event_id="event:pg-rollback-first", event_kind="harness.trace-recorded",
            data={"point": "first"}, recorded_at_ms=run.created_at_ms+1,
        )
        invalid = HarnessEventWrite(
            event_id="event:pg-rollback-second",event_kind="harness.trace-recorded",
            data={"point": "second"},recorded_at_ms=run.created_at_ms+2,
            caused_by_event_id="event:does-not-exist",
        )
        with self.assertRaises(HarnessEventConflict):
            self.store.append_events(
                harness_run_id=run.harness_run_id,events=(safe,invalid),
                expected_revision=1,lease=lease,lease_checked_at_ms=2,
            )
        self.assertEqual(self.store.load_run(run.harness_run_id).revision,1)
        self.assertEqual(len(self.store.list_run_events(run.harness_run_id)),1)
        self.assertEqual(self.store.doctor()["leases"],1)
        self.assertEqual(self.store.append_events(
            harness_run_id=run.harness_run_id,events=(safe,),
            expected_revision=1,lease=lease,lease_checked_at_ms=2,
        ),HarnessEventAdmission.CREATED)
        self.assertEqual(self.store.doctor()["leases"],0)

    def test_concurrent_connections_allow_only_one_active_lease_owner(self) -> None:
        run = contract()
        self.store.create_run(run)
        barrier = Barrier(2)
        def claim(owner: str) -> str:
            with PostgresHarnessStore(self.dsn, schema=self.schema) as store:
                barrier.wait(timeout=5)
                try:
                    store.acquire_run_lease(run.harness_run_id,owner_id=owner,ttl_ms=2000,now_ms=1)
                    return "admitted"
                except HarnessLeaseHeld:
                    return "held"
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(claim,("worker:pg-a","worker:pg-b")))
        self.assertCountEqual(outcomes,["admitted","held"])
        self.assertEqual(self.store.doctor()["leases"],1)
