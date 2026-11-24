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
    HarnessEventConflict, HarnessLeaseHeld, HarnessObjectCorrupt, HarnessRevisionConflict,
    HarnessTerminalConflict,
)
from ordivon_harness.protocol import (
    HarnessRecoveryConsequence, HarnessToolStepIntent, HarnessToolStepReceipt,
    HarnessToolStepStatus,
)
from ordivon_harness.ordivon.run_store_port import HarnessProviderCallRecoveryRequired, HarnessSuperseded
import tests.test_p0_sqlite_tool_store as tool_fixture
from ordivon_harness.store import (
    HarnessEventAdmission, HarnessEventWrite, HarnessStore,
)
from ordivon_harness.ordivon.run_continuity import EventSourcedRunContinuity
from tests.test_p0_sqlite_provider_store import (
    MutableClock, contract, state, failure as provider_failure, result as provider_result,
)


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

    def test_event_read_avoids_n_plus_one_queries_without_losing_cas_checks(self) -> None:
        run = contract()
        self.store.create_run(run)
        lease = self.store.acquire_run_lease(
            run.harness_run_id, owner_id="worker:bulk-read", ttl_ms=5000, now_ms=10,
        )
        new_event = HarnessEventWrite(
            event_id="event:pg-bulk-read",
            event_kind="harness.trace-recorded",
            data={"trace": "bulk"},
            recorded_at_ms=run.created_at_ms + 1,
        )
        self.store.append_events(
            harness_run_id=run.harness_run_id,
            events=(new_event,),
            expected_revision=lease.run_revision,
            lease=lease,
            lease_checked_at_ms=11,
        )

        class CountingConnection:
            def __init__(self, connection):
                self.connection = connection
                self.statements = []

            def execute(self, query, params=None):
                self.statements.append(str(query))
                return self.connection.execute(query, params)

        original = self.store.connection
        counted = CountingConnection(original)
        try:
            self.store.connection = counted
            records = self.store.list_run_events(run.harness_run_id)
        finally:
            self.store.connection = original
        self.assertEqual(len(counted.statements), 2)
        self.assertIn("JOIN objects", counted.statements[1])
        self.assertEqual([record.event_id for record in records][-1], new_event.event_id)
        self.assertEqual(
            [record.event_id for record in self.store.list_run_events(
                run.harness_run_id, after_sequence=records[0].sequence,
            )],
            [new_event.event_id],
        )

        # Corruption must still fail closed despite the query optimization.
        original.execute(
            "UPDATE objects SET content=%s WHERE digest=%s",
            (b"{}", records[-1].payload_digest),
        )
        with self.assertRaises(HarnessObjectCorrupt):
            self.store.list_run_events(run.harness_run_id)

    def test_continuity_heads_cache_rechecks_store_revision_after_external_write(self) -> None:
        from unittest.mock import patch

        run = contract()
        self.store.create_run(run)
        with patch.object(self.store, "list_run_events", wraps=self.store.list_run_events) as reads:
            continuity = EventSourcedRunContinuity(self.store, run)
            first = continuity._heads()
            initial_reads = reads.call_count
            self.assertIs(first, continuity._heads())
            self.assertEqual(reads.call_count, initial_reads)

            # The existing continuity object must observe a different Store
            # connection's committed Run revision, not preserve stale heads.
            with PostgresHarnessStore(self.dsn, schema=self.schema) as rival:
                lease = rival.acquire_run_lease(
                    run.harness_run_id, owner_id="worker:external", ttl_ms=5000, now_ms=10,
                )
                rival.append_events(
                    harness_run_id=run.harness_run_id,
                    events=(HarnessEventWrite(
                        event_id="event:cache-revision-change",
                        event_kind="harness.trace-recorded",
                        data={"trace": "new revision"},
                        recorded_at_ms=run.created_at_ms + 1,
                    ),),
                    expected_revision=lease.run_revision,
                    lease=lease,
                    lease_checked_at_ms=11,
                )
            new_heads = continuity._heads()
            self.assertIsNot(first, new_heads)
            self.assertEqual(reads.call_count, initial_reads + 1)
            self.assertIs(new_heads, continuity._heads())
            self.assertEqual(reads.call_count, initial_reads + 1)

    def test_pg_working_set_history_corrupt_older_committed_payload_does_not_disappear(self) -> None:
        """A corrupt CAS payload must not hide a committed earlier selection.

        SQL pushdown may filter a valid immutable uncommitted record, but a
        digest/byte-length/kind-invalid payload must reach the exact CAS decoder
        rather than silently disappearing from the Agent's history catalog.
        """
        import json
        from tests.test_pc15_epistemic_control import private_contract
        from tests.test_pc18_historical_cognition_recall import HistoricalCognitionRecallTests

        run = private_contract(
            "pg-history-corrupt-candidate", max_model_calls=1, max_tool_calls=0
        )
        self.store.create_run(run)
        continuity = EventSourcedRunContinuity(self.store, run)
        HistoricalCognitionRecallTests.seed_history(self.store, continuity)
        before = continuity.inspect_working_set_history(limit=10)
        self.assertGreaterEqual(len(before["selections"]), 2)
        victim = next(
            event
            for event in self.store.list_run_events(run.harness_run_id)
            if event.event_kind == "harness.working-set-recorded"
            and event.data.get("committed") is True
            and event.sequence != before["currentWorkingSetEventSequence"]
        )
        row = self.store.connection.execute(
            "SELECT content FROM objects WHERE digest=%s",
            (victim.payload_digest,),
        ).fetchone()
        document = json.loads(bytes(row["content"]))
        self.assertIs(document["data"]["committed"], True)
        # Physical corruption of the immutable source object, restricted to
        # this test-only PostgreSQL schema. Stored claimed digest unchanged.
        document["data"]["committed"] = False
        modified = json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
        self.store.connection.execute(
            "UPDATE objects SET content=%s,byte_length=%s WHERE digest=%s",
            (modified, len(modified), victim.payload_digest),
        )
        with self.assertRaises(HarnessObjectCorrupt):
            continuity.inspect_working_set_history(limit=10)

    def test_pg_working_set_history_malformed_older_payload_fails_with_original_cas_error(self) -> None:
        """Invalid UTF-8/JSON must not escape into SQL parser or get silently filtered.

        The current head is intact. Historical CAS payload damage is a Store
        integrity failure, not an agent-visible missing Working Set or a raw
        PostgreSQL JSON/encoding exception.
        """
        from tests.test_pc15_epistemic_control import private_contract
        from tests.test_pc18_historical_cognition_recall import HistoricalCognitionRecallTests

        run = private_contract("pg-history-bad-bytes", max_model_calls=1, max_tool_calls=0)
        self.store.create_run(run)
        continuity = EventSourcedRunContinuity(self.store, run)
        HistoricalCognitionRecallTests.seed_history(self.store, continuity)
        current = continuity.inspect_working_set_history(limit=10)
        victim = next(
            event
            for event in self.store.list_run_events(run.harness_run_id)
            if event.event_kind == "harness.working-set-recorded"
            and event.data.get("committed") is True
            and event.sequence != current["currentWorkingSetEventSequence"]
        )
        row = self.store.connection.execute(
            "SELECT content FROM objects WHERE digest=%s", (victim.payload_digest,)
        ).fetchone()
        original = bytes(row["content"])
        for suffix, malformed in (
            ("not-utf8", b"\xff\xfe"),
            ("not-json", b"{this is not valid JSON"),
        ):
            with self.subTest(suffix=suffix):
                try:
                    self.store.connection.execute(
                        "UPDATE objects SET content=%s,byte_length=%s WHERE digest=%s",
                        (malformed, len(malformed), victim.payload_digest),
                    )
                    with self.assertRaises(HarnessObjectCorrupt):
                        continuity.inspect_working_set_history(limit=10)
                    with self.assertRaises(HarnessObjectCorrupt):
                        self.store.find_working_set_event_sequence(
                            run.harness_run_id,
                            working_set_digest=current["currentWorkingSetDigest"],
                        )
                finally:
                    self.store.connection.execute(
                        "UPDATE objects SET content=%s,byte_length=%s WHERE digest=%s",
                        (original, len(original), victim.payload_digest),
                    )
                self.assertEqual(
                    continuity.inspect_working_set_history(limit=10), current
                )

    def test_pg_working_set_history_bounded_page_matches_legacy_and_concurrent_append(self) -> None:
        """The original PG consumer must not fetch all events for each history page."""
        from unittest.mock import patch
        from tests.test_pc15_epistemic_control import private_contract
        from tests.test_pc18_historical_cognition_recall import HistoricalCognitionRecallTests

        run = private_contract("pg-history-bounded", max_model_calls=1, max_tool_calls=0)
        self.store.create_run(run)
        continuity = EventSourcedRunContinuity(self.store, run)
        HistoricalCognitionRecallTests.seed_history(self.store, continuity)

        with (
            patch.object(self.store, "list_committed_working_set_events", None),
            patch.object(self.store, "find_working_set_event_sequence", None),
        ):
            baseline_one = continuity.inspect_working_set_history(limit=1)
            baseline_two = continuity.inspect_working_set_history(
                limit=1, before_sequence=baseline_one["nextBeforeSequence"]
            )
            baseline_empty = continuity.inspect_working_set_history(limit=10, before_sequence=1)
        with patch.object(
            self.store,
            "list_run_events",
            side_effect=AssertionError("full Journal scan forbidden on warm history page"),
        ):
            one = continuity.inspect_working_set_history(limit=1)
            two = continuity.inspect_working_set_history(
                limit=1, before_sequence=one["nextBeforeSequence"]
            )
            empty = continuity.inspect_working_set_history(limit=10, before_sequence=1)
        self.assertEqual((one, two, empty), (baseline_one, baseline_two, baseline_empty))
        self.assertEqual(len(one["selections"]), 1)
        self.assertEqual(len(two["selections"]), 1)
        self.assertIsNone(two["nextBeforeSequence"])
        self.assertEqual(empty["selections"], [])

        # Another PG process commits a non-Working Set tail. Hot continuity
        # must read only that delta and preserve history/control semantics.
        with PostgresHarnessStore(self.dsn, schema=self.schema) as rival:
            append_at = rival.load_run(run.harness_run_id).updated_at_ms + 1
            lease = rival.acquire_run_lease(
                run.harness_run_id,
                owner_id="worker:history-append",
                ttl_ms=5000,
                now_ms=10,
            )
            rival.append_events(
                harness_run_id=run.harness_run_id,
                events=(
                    HarnessEventWrite(
                        event_id="event:history-concurrent-trace",
                        event_kind="harness.trace-recorded",
                        data={"trace": "committed by another process"},
                        recorded_at_ms=append_at,
                    ),
                ),
                expected_revision=lease.run_revision,
                lease=lease,
                lease_checked_at_ms=11,
            )
        self.assertEqual(continuity.inspect_working_set_history(limit=1), one)
        with PostgresHarnessStore(self.dsn, schema=self.schema) as cold_store:
            cold = EventSourcedRunContinuity.open(cold_store, run.harness_run_id)
            self.assertEqual(cold.inspect_working_set_history(limit=1), one)

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

    def test_same_pg_issuer_cut_is_admission_only_after_unknown_tool(self) -> None:
        """A real read-only Runtime SQL role gets a current original Run cut.

        Once its transaction ends, OriginalPG can record UNKNOWN while a
        previously issued OS request remains potentially pending. The later
        SQL denial is not NoFutureSpawn or a Domain delivery ACK.
        """
        from psycopg import errors

        run = tool_fixture.private_tool_contract()
        self.store.create_run(run)
        clock = MutableClock()
        continuity = EventSourcedRunContinuity(self.store, run, clock_ms=clock)
        continuity.bind_state(state())
        binding = continuity.binding
        intent = HarnessToolStepIntent(
            intent_id="harness-tool-step-intent:pg-native-cut-r24",
            harness_run_id=run.harness_run_id,
            assignment_id=binding.assignment_id,
            assignment_generation=binding.assignment_generation,
            assignment_digest=binding.assignment_digest,
            turn_id="turn:pg-native-cut-r24",
            tool_call_id="tool-call:pg-native-cut-r24",
            tool_name="workspace.read",
            tool_call_digest=canonical_digest({"toolCall": "pg-native-cut-r24"}),
            runtime_operation="workspace.read",
            runtime_arguments_digest=canonical_digest({"relativePath": "README.md"}),
            client_request_id="request:pg-native-cut-r24",
            recovery_consequence=HarnessRecoveryConsequence.OBSERVATION_ONLY,
            created_at_ms=clock(),
        )
        continuity.prepare_tool_step(intent)
        fence = continuity.load_current_tool_step().fence
        self.assertIsNotNone(fence)
        assert fence is not None

        # Independently emulate the Native Runtime's least-privileged SQL
        # role against the exact source function, not an Agent-supplied hint.
        role = "rt_cut_" + uuid.uuid4().hex[:12]
        grant = sql.SQL("GRANT EXECUTE ON FUNCTION {}.harness_current_dispatch_cut(text,bigint,text) TO {}").format(
            sql.Identifier(self.schema), sql.Identifier(role)
        )
        query = sql.SQL("SELECT * FROM {}.harness_current_dispatch_cut(%s,%s,%s)").format(
            sql.Identifier(self.schema)
        )
        with psycopg.connect(self.dsn, autocommit=True) as operator:
            operator.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(role)))
            try:
                operator.execute(
                    sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                        sql.Identifier(self.schema), sql.Identifier(role)
                    )
                )
                operator.execute(grant)
                with psycopg.connect(self.dsn, autocommit=True) as runtime:
                    runtime.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(role)))
                    # Runtime must not read Harness private rows as its own role.
                    with self.assertRaises(errors.InsufficientPrivilege):
                        runtime.execute(
                            sql.SQL("SELECT * FROM {}.runs").format(sql.Identifier(self.schema))
                        )
                    with runtime.transaction():
                        qualified = runtime.execute(
                            query,
                            (run.harness_run_id, fence.run_revision, fence.digest),
                        ).fetchall()
                        self.assertEqual(len(qualified), 1)
                        self.assertEqual(qualified[0][0], "harness.tool-step-prepared")
                        self.assertEqual(qualified[0][1], self.store.list_run_events(run.harness_run_id)[-1].payload_digest)
                        self.assertEqual(qualified[0][8], continuity.load_current_tool_step().intent_object.digest)
                    self.assertEqual(
                        runtime.execute(
                            query,
                            (run.harness_run_id, fence.run_revision + 1, fence.digest),
                        ).fetchall(),
                        [],
                    )
                    self.assertEqual(
                        runtime.execute(
                            query,
                            (run.harness_run_id, fence.run_revision, "sha256:" + "0" * 64),
                        ).fetchall(),
                        [],
                    )

                    # The admission transaction has committed here. An
                    # issued, delayed native launch is NOT fenced by this
                    # past result. Preserve explicit UNKNOWN on source.
                    clock.advance()
                    unknown_observation = {
                        "schemaVersion": 1,
                        "kind": "pg.native-receiver-unknown",
                        "status": "unknown",
                    }
                    unknown = HarnessToolStepReceipt(
                        receipt_id="harness-tool-step-receipt:pg-native-cut-unknown",
                        intent_digest=intent.digest,
                        harness_run_id=run.harness_run_id,
                        tool_call_id=intent.tool_call_id,
                        status=HarnessToolStepStatus.UNKNOWN,
                        runtime_job_ref="runtime-job:pg-native-cut-issued",
                        observation_digest=canonical_digest(unknown_observation),
                        reconciled=False,
                        created_at_ms=clock(),
                    )
                    continuity.record_tool_step_receipt(unknown, unknown_observation)
                    self.assertEqual(
                        runtime.execute(
                            query,
                            (run.harness_run_id, fence.run_revision, fence.digest),
                        ).fetchall(),
                        [],
                    )
                    source = EventSourcedRunContinuity.open(
                        self.store, run.harness_run_id, clock_ms=clock
                    ).inspect_finalization_source()
                    self.assertEqual(source["sourceStanding"], "blocked")
                    self.assertIn("tool_unsettled", source["blockers"])
                    self.assertEqual(source["unsettledToolIntentDigests"], [intent.digest])
                    self.assertEqual(source["runtimeClaimStanding"], "unknown")
                    self.assertEqual(source["externalDeliveryStanding"], "unknown")
            finally:
                operator.execute(
                    sql.SQL("REVOKE ALL ON SCHEMA {} FROM {}").format(
                        sql.Identifier(self.schema), sql.Identifier(role)
                    )
                )
                operator.execute(
                    sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role))
                )
                operator.execute(
                    sql.SQL("DROP ROLE {}").format(sql.Identifier(role))
                )

    def test_finalization_projection_does_not_claim_external_delivery(self) -> None:
        """An original PAUSED Run holds the source; a terminal Run is not a NativeClose receipt."""
        clock = supported_run_fixture.FixedClock()
        run = supported_run_fixture.contract("pg-finalizer-source")
        active = HarnessAgentRun.create(
            self.dsn, self.schema, run,
            lambda _value: ScriptedTurnAdapter((supported_run_fixture.needs_input(),)),
            clock_ms=clock, monotonic_ms=clock,
        )
        paused = active.run(({"role": "user", "content": "finalizer source"},))
        self.assertTrue(paused.paused)
        with PostgresHarnessStore(self.dsn, schema=self.schema) as opened:
            read = EventSourcedRunContinuity.open(
                opened, run.harness_run_id, clock_ms=clock
            ).inspect_finalization_source()
        self.assertEqual(read["sourceStanding"], "blocked")
        self.assertIn("run_not_terminal", read["blockers"])
        resumed = HarnessAgentRun.open(
            self.dsn, self.schema, run.harness_run_id,
            lambda _value: ScriptedTurnAdapter((supported_run_fixture.completed(),)),
            clock_ms=clock, monotonic_ms=clock,
        )
        result = resumed.resume(additional_messages=({"role": "user", "content": "continue"},))
        self.assertEqual(result.loop_result.stop_code.value, "candidate_completed")
        with PostgresHarnessStore(self.dsn, schema=self.schema) as reopened:
            done = EventSourcedRunContinuity.open(
                reopened, run.harness_run_id, clock_ms=clock
            ).inspect_finalization_source()
        self.assertEqual(done["sourceStanding"], "source-settled")
        self.assertEqual(done["contractDigest"], run.digest)
        self.assertEqual(done["toolGrantDigest"], run.tool_grant_digest)
        self.assertIsInstance(done["runReceiptDigest"], str)
        self.assertEqual(done["blockers"], [])
        self.assertEqual(done["externalDeliveryStanding"], "unknown")
        self.assertEqual(done["runtimeClaimStanding"], "unknown")
        self.assertIsNotNone(done["terminalEventId"])

    def test_nonterminal_finalizer_reports_actual_pending_tool_sources(self) -> None:
        """PAUSED/nonterminal is blocked, but its original PG pending Tool
        identity must remain visible for a future authenticated Owner lookup.
        """
        run = tool_fixture.private_tool_contract()
        self.store.create_run(run)
        clock = MutableClock()
        continuity = EventSourcedRunContinuity(self.store, run, clock_ms=clock)
        continuity.bind_state(state())
        binding = continuity.binding
        intent = HarnessToolStepIntent(
            intent_id="harness-tool-step-intent:pg-nonterminal-inspection",
            harness_run_id=run.harness_run_id,
            assignment_id=binding.assignment_id,
            assignment_generation=binding.assignment_generation,
            assignment_digest=binding.assignment_digest,
            turn_id="turn:pg-nonterminal-inspection",
            tool_call_id="tool-call:pg-nonterminal-inspection",
            tool_name="workspace.read",
            tool_call_digest=canonical_digest({"call": "pg-nonterminal-inspection"}),
            runtime_operation="workspace.read",
            runtime_arguments_digest=canonical_digest({"relativePath": "README.md"}),
            client_request_id="request:pg-nonterminal-inspection",
            recovery_consequence=HarnessRecoveryConsequence.OBSERVATION_ONLY,
            created_at_ms=clock(),
        )
        continuity.prepare_tool_step(intent)
        with PostgresHarnessStore(self.dsn, schema=self.schema) as reopened:
            resumed = EventSourcedRunContinuity.open(
                reopened, run.harness_run_id, clock_ms=clock
            )
            source = resumed.inspect_finalization_source()
            self.assertEqual(source["sourceStanding"], "blocked")
            self.assertIn("run_not_terminal", source["blockers"])
            self.assertIn("tool_unsettled", source["blockers"])
            self.assertEqual(source["unsettledProviderCallIds"], [])
            self.assertEqual(source["unsettledToolIntentDigests"], [intent.digest])
            self.assertEqual(source["runtimeClaimStanding"], "unknown")
            self.assertEqual(source["externalDeliveryStanding"], "unknown")

    def test_nonterminal_finalizer_reports_actual_pending_provider_sources(self) -> None:
        """A model provider CLAIMED before completion must be part of the
        same full-history diagnostic even when Run is not terminal.
        """
        run = contract()
        self.store.create_run(run)
        clock = MutableClock()
        continuity = EventSourcedRunContinuity(self.store, run, clock_ms=clock)
        continuity.bind_state(state())
        claimed = continuity.claim_provider_call(
            source=continuity.assignment_provider_source(),
            turn_id="turn:pg-nonterminal-provider",
            turn_sequence=1,
            request_digest=canonical_digest({"provider": "pending-before-finalizer"}),
            provider_request_digest=canonical_digest({"wire": "pending-before-finalizer"}),
            adapter_id=run.adapter_id,
            requested_model_id=run.requested_model_id,
            holder_id="holder:pg-nonterminal-provider",
            ttl_ms=10000,
        )
        with PostgresHarnessStore(self.dsn, schema=self.schema) as reopened:
            resumed = EventSourcedRunContinuity.open(
                reopened, run.harness_run_id, clock_ms=clock
            )
            source = resumed.inspect_finalization_source()
            self.assertEqual(source["sourceStanding"], "blocked")
            self.assertIn("run_not_terminal", source["blockers"])
            self.assertIn("provider_unsettled", source["blockers"])
            self.assertEqual(
                source["unsettledProviderCallIds"],
                [claimed.record.provider_call_id],
            )
            self.assertEqual(source["unsettledToolIntentDigests"], [])
            self.assertEqual(source["runtimeClaimStanding"], "unknown")
            self.assertEqual(source["externalDeliveryStanding"], "unknown")

    def test_nonterminal_finalizer_rejects_intervening_pg_writer(self) -> None:
        """An original PG writer that appends after the first Source read
        must force the diagnostic to reject its mixed-version projection.
        """
        from unittest.mock import patch

        run = contract()
        self.store.create_run(run)
        clock = MutableClock()
        continuity = EventSourcedRunContinuity(self.store, run, clock_ms=clock)
        continuity.bind_state(state())
        original = self.store.list_run_events
        once = False

        def interleaved_events(run_id: str):
            nonlocal once
            events = original(run_id)
            if not once:
                once = True
                with PostgresHarnessStore(self.dsn, schema=self.schema) as rival:
                    now = events[-1].recorded_at_ms + 2
                    lease = rival.acquire_run_lease(
                        run_id,
                        owner_id="worker:interleaved-finalizer",
                        ttl_ms=10_000,
                        now_ms=now,
                    )
                    rival.append_events(
                        harness_run_id=run_id,
                        events=(
                            HarnessEventWrite(
                                event_id="event:pg-interleaved-after-source-read",
                                event_kind="harness.trace-recorded",
                                data={"trace": canonical_digest({"interleaved": True})},
                                recorded_at_ms=now + 1,
                            ),
                        ),
                        expected_revision=lease.run_revision,
                        lease=lease,
                        lease_checked_at_ms=now,
                    )
            return events

        with patch.object(
            self.store, "list_run_events", side_effect=interleaved_events
        ):
            with self.assertRaises(HarnessRevisionConflict):
                continuity.inspect_finalization_source()
        self.assertEqual(
            self.store.load_run(run.harness_run_id).revision,
            len(self.store.list_run_events(run.harness_run_id)),
        )

    def test_unknown_stop_is_terminal_but_not_release_safe(self) -> None:
        """A STOPPED projection must not erase an epistemically UNKNOWN outcome."""
        from ordivon_harness.independent_result import IndependentRunRecorder
        from ordivon_harness.ordivon.events import HarnessRunEvent, HarnessTrace
        from ordivon_harness.ordivon.run_contract import AgentLoopResult, RunStopCode

        run = supported_run_fixture.contract("unknown-stop-finalizer")
        self.store.create_run(run)
        clock = supported_run_fixture.FixedClock()
        continuity = EventSourcedRunContinuity(self.store, run, clock_ms=clock)
        trace = HarnessTrace(
            run.harness_run_id,
            (
                HarnessRunEvent(
                    sequence=1,
                    kind="run_stopped",
                    occurred_at_ms=run.created_at_ms + 1,
                    payload={"reason": "provider response lost"},
                ),
            ),
        )
        unknown = AgentLoopResult(
            harness_run_id=run.harness_run_id,
            stop_code=RunStopCode.PROVIDER_STATE_UNKNOWN,
            trace=trace,
            conclusion=None,
            messages=(),
            observations=(),
            model_calls=0,
            tool_calls=0,
            observation_bytes=0,
            usage={},
        )
        recorder = IndependentRunRecorder(
            self.store, run, continuity.binding, clock_ms=clock
        )
        recorder.record_result(
            unknown,
            started_at_ms=run.created_at_ms,
            finished_at_ms=run.created_at_ms + 2,
        )
        self.assertEqual(self.store.load_run(run.harness_run_id).status.value, "stopped")
        with PostgresHarnessStore(self.dsn, schema=self.schema) as reopened:
            assessment = EventSourcedRunContinuity.open(
                reopened, run.harness_run_id, clock_ms=clock
            ).inspect_finalization_source()
        self.assertEqual(assessment["sourceStanding"], "blocked")
        self.assertIn("unknown_run_stop", assessment["blockers"])
        self.assertEqual(assessment["externalDeliveryStanding"], "unknown")

    def test_original_pg_terminal_blocks_new_event_and_preserves_exact_old_replay(self) -> None:
        """PG terminal row serializes new Event admission; no extra SealStore.
        This Store-only Event test does not constitute a qualified RunReceipt
        or authorize external Runtime Claim release.
        """
        run = contract()
        self.store.create_run(run)
        first_lease = self.store.acquire_run_lease(
            run.harness_run_id,
            owner_id="worker:terminal-original-trace",
            ttl_ms=10_000,
            now_ms=run.created_at_ms,
        )
        before_terminal = HarnessEventWrite(
            event_id="event:pg-before-terminal-exact-replay",
            event_kind="harness.trace-recorded",
            data={"trace": canonical_digest({"original": "before-terminal"})},
            recorded_at_ms=run.created_at_ms + 1,
        )
        self.assertEqual(
            self.store.append_events(
                harness_run_id=run.harness_run_id,
                events=(before_terminal,),
                expected_revision=first_lease.run_revision,
                lease=first_lease,
                lease_checked_at_ms=run.created_at_ms,
            ),
            HarnessEventAdmission.CREATED,
        )
        terminal_lease = self.store.acquire_run_lease(
            run.harness_run_id,
            owner_id="worker:terminal-event",
            ttl_ms=10_000,
            now_ms=run.created_at_ms + 2,
        )
        stopped_event = HarnessEventWrite(
            event_id="event:pg-terminal-run-stopped",
            event_kind="harness.run-stopped",
            data={"stopReason": "unknown"},
            recorded_at_ms=run.created_at_ms + 3,
        )
        self.assertEqual(
            self.store.append_events(
                harness_run_id=run.harness_run_id,
                events=(stopped_event,),
                expected_revision=terminal_lease.run_revision,
                lease=terminal_lease,
                lease_checked_at_ms=run.created_at_ms + 2,
            ),
            HarnessEventAdmission.CREATED,
        )
        terminal = self.store.load_run(run.harness_run_id)
        self.assertTrue(terminal.status.terminal)
        events = self.store.list_run_events(run.harness_run_id)
        self.assertEqual(len(events), terminal.revision)
        self.assertEqual(events[-1].event_id, terminal.terminal_event_id)
        with PostgresHarnessStore(self.dsn, schema=self.schema) as reopened:
            with self.assertRaises(HarnessTerminalConflict):
                reopened.acquire_run_lease(
                    run.harness_run_id,
                    owner_id="worker:post-terminal",
                    ttl_ms=10_000,
                    now_ms=run.created_at_ms + 4,
                )
            with self.assertRaises(HarnessTerminalConflict):
                reopened.append_events(
                    harness_run_id=run.harness_run_id,
                    events=(
                        replace(
                            before_terminal,
                            event_id="event:pg-after-terminal-must-reject",
                            recorded_at_ms=run.created_at_ms + 4,
                        ),
                    ),
                    expected_revision=terminal.revision,
                    lease=terminal_lease,
                    lease_checked_at_ms=run.created_at_ms + 4,
                )
            with self.assertRaises(HarnessEventConflict):
                reopened.append_events(
                    harness_run_id=run.harness_run_id,
                    events=(replace(before_terminal, data={"trace": "forged"}),),
                    expected_revision=first_lease.run_revision,
                    lease=first_lease,
                    lease_checked_at_ms=run.created_at_ms + 4,
                )
            # Same old Event identity and immutable bytes after response loss:
            # source replay succeeds with no event, lease, or revision added.
            self.assertEqual(
                reopened.append_events(
                    harness_run_id=run.harness_run_id,
                    events=(before_terminal,),
                    expected_revision=first_lease.run_revision,
                    lease=first_lease,
                    lease_checked_at_ms=run.created_at_ms + 4,
                ),
                HarnessEventAdmission.EXISTING,
            )
            self.assertEqual(reopened.load_run(run.harness_run_id).revision, terminal.revision)
            self.assertEqual(reopened.list_run_events(run.harness_run_id), events)
            reopened.validate_run_history(run.harness_run_id)

    def test_terminal_unknown_with_pending_tool_requires_original_owner(self) -> None:
        """Terminal is only a Run Event fence, not evidence that a previously
        prepared physical Tool completed or that its Workspace may close.
        """
        from ordivon_harness.independent_result import IndependentRunRecorder
        from ordivon_harness.ordivon.events import HarnessRunEvent, HarnessTrace
        from ordivon_harness.ordivon.run_contract import AgentLoopResult, RunStopCode

        run = tool_fixture.private_tool_contract()
        self.store.create_run(run)
        clock = MutableClock()
        continuity = EventSourcedRunContinuity(self.store, run, clock_ms=clock)
        continuity.bind_state(state())
        binding = continuity.binding
        intent = HarnessToolStepIntent(
            intent_id="harness-tool-step-intent:stopped-unknown-owner",
            harness_run_id=run.harness_run_id,
            assignment_id=binding.assignment_id,
            assignment_generation=binding.assignment_generation,
            assignment_digest=binding.assignment_digest,
            turn_id="turn:stopped-unknown-owner",
            tool_call_id="tool-call:stopped-unknown-owner",
            tool_name="workspace.read",
            tool_call_digest=canonical_digest({"call": "stopped-unknown-owner"}),
            runtime_operation="workspace.read",
            runtime_arguments_digest=canonical_digest({"path": "README.md"}),
            client_request_id="request:stopped-unknown-owner",
            recovery_consequence=HarnessRecoveryConsequence.OBSERVATION_ONLY,
            created_at_ms=clock(),
        )
        continuity.prepare_tool_step(intent)
        clock.advance(3)
        unknown = AgentLoopResult(
            harness_run_id=run.harness_run_id,
            stop_code=RunStopCode.PROVIDER_STATE_UNKNOWN,
            trace=HarnessTrace(
                run.harness_run_id,
                (
                    HarnessRunEvent(
                        sequence=1,
                        kind="run_stopped",
                        occurred_at_ms=run.created_at_ms + 2,
                        payload={"reason": "an unresolved Tool must not be released"},
                    ),
                ),
            ),
            conclusion=None,
            messages=(),
            observations=(),
            model_calls=0,
            tool_calls=0,
            observation_bytes=0,
            usage={},
        )
        IndependentRunRecorder(
            self.store, run, continuity.binding, clock_ms=clock
        ).record_result(
            unknown,
            started_at_ms=run.created_at_ms,
            finished_at_ms=run.created_at_ms + 3,
        )
        with PostgresHarnessStore(self.dsn, schema=self.schema) as reopened:
            projection = reopened.load_run(run.harness_run_id)
            self.assertTrue(projection.status.terminal)
            resumed = EventSourcedRunContinuity.open(
                reopened, run.harness_run_id, clock_ms=clock
            )
            standing = resumed.inspect_finalization_source()
            self.assertEqual(standing["sourceStanding"], "blocked")
            self.assertIn("tool_unsettled", standing["blockers"])
            self.assertIn("unknown_run_stop", standing["blockers"])
            self.assertEqual(standing["unsettledToolIntentDigests"], [intent.digest])
            self.assertEqual(standing["runtimeClaimStanding"], "unknown")
            self.assertEqual(standing["externalDeliveryStanding"], "unknown")
            # This is the exact liveness cost of immutable Terminal PG.
            # Even a later real Owner observation cannot become a new Run
            # Receipt Event: OriginalPG is terminal, so Release stays HOLD
            # unless a separate, explicitly reviewed recovery policy exists.
            observation = {"schemaVersion": 1, "kind": "pg.late-tool", "status": "observed"}
            receipt = HarnessToolStepReceipt(
                receipt_id="harness-tool-step-receipt:late-after-terminal",
                intent_digest=intent.digest,
                harness_run_id=run.harness_run_id,
                tool_call_id=intent.tool_call_id,
                status=HarnessToolStepStatus.OBSERVED,
                runtime_job_ref="runtime-job:late-after-terminal",
                observation_digest=canonical_digest(observation),
                reconciled=True,
                created_at_ms=clock(),
            )
            with self.assertRaises(HarnessTerminalConflict):
                resumed.record_tool_step_receipt(receipt, observation)
            self.assertEqual(reopened.load_run(run.harness_run_id).revision, projection.revision)
            self.assertEqual(
                EventSourcedRunContinuity.open(
                    reopened, run.harness_run_id, clock_ms=clock
                ).inspect_finalization_source()["sourceStanding"],
                "blocked",
            )

    def test_original_pg_terminal_writer_accepts_clean_run_and_exact_replay(self) -> None:
        """Nonvacuous positive: clean Run may terminal, old exact readback
        after response loss creates no second Event or revision.
        """
        run = contract()
        self.store.create_run(run)
        before = self.store.load_run(run.harness_run_id)
        now = before.updated_at_ms + 1
        lease = self.store.acquire_run_lease(
            run.harness_run_id, owner_id="worker:terminal-clean",
            ttl_ms=10_000, now_ms=now,
        )
        terminal = HarnessEventWrite(
            event_id="event:pg-clean-original-terminal",
            event_kind="harness.run-completed",
            data={"stopReason": "completed"},
            recorded_at_ms=now + 1,
        )
        self.assertEqual(
            self.store.append_events(
                harness_run_id=run.harness_run_id, events=(terminal,),
                expected_revision=lease.run_revision, lease=lease,
                lease_checked_at_ms=now,
            ),
            HarnessEventAdmission.CREATED,
        )
        after = self.store.load_run(run.harness_run_id)
        self.assertTrue(after.status.terminal)
        with PostgresHarnessStore(self.dsn, schema=self.schema) as reopened:
            self.assertEqual(
                reopened.append_events(
                    harness_run_id=run.harness_run_id, events=(terminal,),
                    expected_revision=lease.run_revision, lease=lease,
                    lease_checked_at_ms=now + 2,
                ),
                HarnessEventAdmission.EXISTING,
            )
            self.assertEqual(reopened.load_run(run.harness_run_id).revision, after.revision)
            reopened.validate_run_history(run.harness_run_id)

    def test_terminal_admission_rejects_detached_original_payload_edge(self) -> None:
        from ordivon_harness.store_errors import HarnessJournalCorruption

        run = contract()
        self.store.create_run(run)
        original = self.store.load_run(run.harness_run_id)
        now = original.updated_at_ms + 1
        lease = self.store.acquire_run_lease(
            run.harness_run_id, owner_id="worker:terminal-detached",
            ttl_ms=10_000, now_ms=now,
        )
        created = self.store.list_run_events(run.harness_run_id)[0]
        self.store.connection.execute(
            "DELETE FROM run_object_refs WHERE event_id=%s AND role='payload'",
            (created.event_id,),
        )
        terminal = HarnessEventWrite(
            event_id="event:terminal-detached-source",
            event_kind="harness.run-completed",
            data={"stopReason": "completed"},
            recorded_at_ms=now + 1,
        )
        with self.assertRaises(HarnessJournalCorruption):
            self.store.append_events(
                harness_run_id=run.harness_run_id, events=(terminal,),
                expected_revision=lease.run_revision, lease=lease,
                lease_checked_at_ms=now,
            )
        self.assertEqual(self.store.load_run(run.harness_run_id), original)
        self.assertTrue(self.store.release_run_lease(lease))

    def test_original_pg_terminal_writer_rejects_pending_provider(self) -> None:
        """A model Provider CLAIMED is a real unresolved external effect."""
        from ordivon_harness.store_errors import HarnessTerminalConflict

        run = contract()
        self.store.create_run(run)
        clock = MutableClock()
        continuity = EventSourcedRunContinuity(self.store, run, clock_ms=clock)
        continuity.bind_state(state())
        claimed = continuity.claim_provider_call(
            source=continuity.assignment_provider_source(),
            turn_id="turn:pg-terminal-claimed-provider",
            turn_sequence=1,
            request_digest=canonical_digest({"request": "pending-provider"}),
            provider_request_digest=canonical_digest({"wire": "pending-provider"}),
            adapter_id=run.adapter_id,
            requested_model_id=run.requested_model_id,
            holder_id="holder:terminal-pending-provider",
            ttl_ms=10_000,
        )
        before = self.store.load_run(run.harness_run_id)
        now = before.updated_at_ms + 1
        lease = self.store.acquire_run_lease(
            run.harness_run_id, owner_id="worker:terminal-pending-provider",
            ttl_ms=10_000, now_ms=now,
        )
        with self.assertRaises(HarnessTerminalConflict):
            self.store.append_events(
                harness_run_id=run.harness_run_id,
                events=(HarnessEventWrite(
                    event_id="event:pg-terminal-while-provider-pending",
                    event_kind="harness.run-failed",
                    data={"stopReason": "failed"},
                    recorded_at_ms=now + 1,
                ),),
                expected_revision=lease.run_revision,
                lease=lease,
                lease_checked_at_ms=now,
            )
        self.assertEqual(self.store.load_run(run.harness_run_id).revision, before.revision)
        self.assertFalse(self.store.load_run(run.harness_run_id).status.terminal)
        self.assertEqual(
            continuity.load_current_provider_call().record.provider_call_id,
            claimed.record.provider_call_id,
        )
        self.assertTrue(self.store.release_run_lease(lease))

    def test_original_pg_terminal_writer_rejects_pending_tool_without_consuming_lease(self) -> None:
        """Original PG Store, not pre-read Continuity, must refuse completion
        while the real immutable Tool Intent remains unsettled.
        """
        from ordivon_harness.store_errors import HarnessTerminalConflict

        run = tool_fixture.private_tool_contract()
        self.store.create_run(run)
        clock = MutableClock()
        continuity = EventSourcedRunContinuity(self.store, run, clock_ms=clock)
        continuity.bind_state(state())
        binding = continuity.binding
        intent = HarnessToolStepIntent(
            intent_id="harness-tool-step-intent:pg-terminal-prepared",
            harness_run_id=run.harness_run_id,
            assignment_id=binding.assignment_id,
            assignment_generation=binding.assignment_generation,
            assignment_digest=binding.assignment_digest,
            turn_id="turn:pg-terminal-prepared",
            tool_call_id="tool-call:pg-terminal-prepared",
            tool_name="workspace.read",
            tool_call_digest=canonical_digest({"tool": "pg-terminal-prepared"}),
            runtime_operation="workspace.read",
            runtime_arguments_digest=canonical_digest({"relativePath": "README.md"}),
            client_request_id="request:pg-terminal-prepared",
            recovery_consequence=HarnessRecoveryConsequence.OBSERVATION_ONLY,
            created_at_ms=clock(),
        )
        continuity.prepare_tool_step(intent)
        before = self.store.load_run(run.harness_run_id)
        now = before.updated_at_ms + 1
        lease = self.store.acquire_run_lease(
            run.harness_run_id,
            owner_id="worker:pg-terminal-pending-tool",
            ttl_ms=10_000,
            now_ms=now,
        )
        terminal = HarnessEventWrite(
            event_id="event:pg-terminal-while-tool-pending",
            event_kind="harness.run-completed",
            data={"stopReason": "completed"},
            recorded_at_ms=now + 1,
        )
        with self.assertRaises(HarnessTerminalConflict):
            self.store.append_events(
                harness_run_id=run.harness_run_id,
                events=(terminal,),
                expected_revision=lease.run_revision,
                lease=lease,
                lease_checked_at_ms=now,
            )
        self.assertEqual(self.store.load_run(run.harness_run_id).revision, before.revision)
        self.assertFalse(self.store.load_run(run.harness_run_id).status.terminal)
        self.assertEqual(self.store.doctor()["leases"], 1)
        self.assertEqual(
            continuity.inspect_unsettled_tool_sources()["unsettledIntents"][0]["intentDigest"],
            intent.digest,
        )
        # A partial projection must not convert unresolved history to
        # "no effects". Inject loss of the actual persisted pending Tool
        # event at the original Store admission boundary, not the facade.
        from unittest.mock import patch
        from ordivon_harness.store_errors import HarnessJournalCorruption

        full = self.store.list_run_events(run.harness_run_id)
        partial = tuple(e for e in full if e.event_kind != "harness.tool-step-prepared")
        self.assertLess(len(partial), len(full))
        with patch.object(self.store, "list_run_events", return_value=partial):
            with self.assertRaises((HarnessJournalCorruption, HarnessRevisionConflict, HarnessTerminalConflict)):
                self.store.append_events(
                    harness_run_id=run.harness_run_id, events=(terminal,),
                    expected_revision=lease.run_revision, lease=lease,
                    lease_checked_at_ms=now,
                )
        self.assertEqual(self.store.load_run(run.harness_run_id).revision, before.revision)
        self.assertFalse(self.store.load_run(run.harness_run_id).status.terminal)
        self.assertEqual(self.store.doctor()["leases"], 1)
        self.assertTrue(self.store.release_run_lease(lease))
        # A separate experimental Writer might bypass the Python admission
        # and commit a structurally contiguous completed Run. Doctor must use
        # the same typed full-history scanner and reject the still-prepared Tool.
        from ordivon_harness.store_errors import HarnessJournalCorruption

        event_id = "event:pg-doctor-foreign-completed-over-tool"
        at = self.store.load_run(run.harness_run_id).updated_at_ms + 1
        payload = self.store.put_object({
            "schemaVersion": 1,
            "kind": "ordivon.harness-run-event-payload",
            "eventKind": "harness.run-completed",
            "data": {"stopReason": "completed"},
        }, kind="ordivon.harness-run-event-payload")
        with self.store.connection.transaction():
            self.store.connection.execute(
                "INSERT INTO run_events(event_id,harness_run_id,run_revision,"
                "event_kind,payload_digest,recorded_at_ms) "
                "VALUES(%s,%s,%s,%s,%s,%s)",
                (event_id, run.harness_run_id, before.revision + 1,
                 "harness.run-completed", payload.digest, at),
            )
            self.store.connection.execute(
                "INSERT INTO run_object_refs(harness_run_id,event_id,digest,role) "
                "VALUES(%s,%s,%s,'payload')",
                (run.harness_run_id, event_id, payload.digest),
            )
            self.store.connection.execute(
                "UPDATE runs SET status='completed',revision=%s,updated_at_ms=%s,"
                "terminal_event_id=%s WHERE harness_run_id=%s",
                (before.revision + 1, at, event_id, run.harness_run_id),
            )
        with self.assertRaises(HarnessJournalCorruption):
            self.store.doctor()


    def test_original_recorder_cannot_claim_completed_with_pending_tool(self) -> None:
        """A candidate_completed answer is rejected, never emitted as a
        terminal receipt while the original Tool may still have an effect.
        """
        from ordivon_harness.independent_result import IndependentRunRecorder
        from ordivon_harness.ordivon.events import HarnessRunEvent, HarnessTrace
        from ordivon_harness.ordivon.run_contract import AgentLoopResult, RunStopCode
        from ordivon_harness.ordivon.model import AgentRunConclusion
        from ordivon_harness.store_errors import HarnessTerminalConflict

        run = tool_fixture.private_tool_contract()
        self.store.create_run(run)
        clock = MutableClock()
        continuity = EventSourcedRunContinuity(self.store, run, clock_ms=clock)
        continuity.bind_state(state())
        binding = continuity.binding
        intent = HarnessToolStepIntent(
            intent_id="harness-tool-step-intent:false-terminal-completed",
            harness_run_id=run.harness_run_id,
            assignment_id=binding.assignment_id,
            assignment_generation=binding.assignment_generation,
            assignment_digest=binding.assignment_digest,
            turn_id="turn:false-terminal-completed",
            tool_call_id="tool-call:false-terminal-completed",
            tool_name="workspace.read",
            tool_call_digest=canonical_digest({"toolCall": "false-terminal-completed"}),
            runtime_operation="workspace.read",
            runtime_arguments_digest=canonical_digest({"relativePath": "README.md"}),
            client_request_id="request:false-terminal-completed",
            recovery_consequence=HarnessRecoveryConsequence.OBSERVATION_ONLY,
            created_at_ms=clock(),
        )
        continuity.prepare_tool_step(intent)
        trace = HarnessTrace(
            run.harness_run_id,
            (HarnessRunEvent(
                sequence=1,
                kind="run_stopped",
                occurred_at_ms=run.created_at_ms + 1,
                payload={"reason": "unverified candidate"},
            ),),
        )
        result = AgentLoopResult(
            harness_run_id=run.harness_run_id,
            stop_code=RunStopCode.CANDIDATE_COMPLETED,
            trace=trace,
            conclusion=AgentRunConclusion(
                status="candidate_completed",
                summary="This is not proof the original Tool completed.",
            ),
            messages=(), observations=(),
            model_calls=0, tool_calls=0, observation_bytes=0, usage={},
        )
        recorder = IndependentRunRecorder(
            self.store, run, continuity.binding, clock_ms=clock
        )
        with self.assertRaises(HarnessTerminalConflict):
            recorder.record_result(
                result,
                started_at_ms=run.created_at_ms,
                finished_at_ms=run.created_at_ms + 3,
            )
        self.assertFalse(self.store.load_run(run.harness_run_id).status.terminal)
        self.assertEqual(
            continuity.inspect_unsettled_tool_sources()["unsettledIntents"][0]["intentDigest"],
            intent.digest,
        )

    def test_original_recorder_nonterminal_hold_preserves_unreceipted_tool(self) -> None:
        """A failed Run after a pre-dispatch Tool Intent must remain PAUSED,
        with its same original Intent and recoverable snapshot, not terminal.
        """
        from ordivon_harness.independent_result import IndependentRunRecorder
        from ordivon_harness.ordivon.events import HarnessRunEvent, HarnessTrace
        from ordivon_harness.ordivon.run_contract import AgentLoopResult, RunStopCode

        run = tool_fixture.private_tool_contract()
        self.store.create_run(run)
        clock = MutableClock()
        continuity = EventSourcedRunContinuity(self.store, run, clock_ms=clock)
        continuity.bind_state(state())
        binding = continuity.binding
        intent = HarnessToolStepIntent(
            intent_id="harness-tool-step-intent:failed-hold",
            harness_run_id=run.harness_run_id,
            assignment_id=binding.assignment_id,
            assignment_generation=binding.assignment_generation,
            assignment_digest=binding.assignment_digest,
            turn_id="turn:failed-hold",
            tool_call_id="tool-call:failed-hold",
            tool_name="workspace.read",
            tool_call_digest=canonical_digest({"toolCall": "failed-hold"}),
            runtime_operation="workspace.read",
            runtime_arguments_digest=canonical_digest({"relativePath": "README.md"}),
            client_request_id="request:failed-hold",
            recovery_consequence=HarnessRecoveryConsequence.OBSERVATION_ONLY,
            created_at_ms=clock(),
        )
        continuity.prepare_tool_step(intent)
        result = AgentLoopResult(
            harness_run_id=run.harness_run_id,
            stop_code=RunStopCode.HARNESS_FAILED,
            trace=HarnessTrace(
                run.harness_run_id,
                (HarnessRunEvent(
                    sequence=1,
                    kind="run_stopped",
                    occurred_at_ms=run.created_at_ms + 1,
                    payload={"reason": "effect handoff not independently observed"},
                ),),
            ),
            conclusion=None,
            messages=(), observations=(),
            model_calls=0, tool_calls=0, observation_bytes=0, usage={},
        )
        recorder = IndependentRunRecorder(
            self.store, run, continuity.binding, clock_ms=clock
        )
        self.assertIsNone(recorder.record_result(
            result, started_at_ms=run.created_at_ms,
            finished_at_ms=run.created_at_ms + 3,
        ))
        self.assertEqual(
            self.store.load_run(run.harness_run_id).status.value, "paused"
        )
        with PostgresHarnessStore(self.dsn, schema=self.schema) as reopened:
            resumed = EventSourcedRunContinuity.open(
                reopened, run.harness_run_id, clock_ms=clock
            )
            self.assertEqual(resumed.load_current_tool_step().intent.digest, intent.digest)
            self.assertEqual(
                resumed.load_current_snapshot().snapshot.active_tool_step_intent_digests,
                (intent.digest,),
            )
            self.assertEqual(
                resumed.inspect_unsettled_tool_sources()["unsettledIntents"][0]["intentDigest"],
                intent.digest,
            )

    def test_unknown_fault_terminal_is_quarantined_not_source_settled(self) -> None:
        """Unlike NORMAL completion, an explicit UNKNOWN STOPPED Run may
        remain immutable audit evidence with old pending Tool; never Release.
        """
        from ordivon_harness.independent_result import IndependentRunRecorder
        from ordivon_harness.ordivon.events import HarnessRunEvent, HarnessTrace
        from ordivon_harness.ordivon.run_contract import AgentLoopResult, RunStopCode
        from ordivon_harness.store_errors import HarnessTerminalConflict

        run = tool_fixture.private_tool_contract()
        self.store.create_run(run)
        clock = MutableClock()
        continuity = EventSourcedRunContinuity(self.store, run, clock_ms=clock)
        continuity.bind_state(state())
        binding = continuity.binding
        intent = HarnessToolStepIntent(
            intent_id="harness-tool-step-intent:pg-quarantine-unknown",
            harness_run_id=run.harness_run_id,
            assignment_id=binding.assignment_id,
            assignment_generation=binding.assignment_generation,
            assignment_digest=binding.assignment_digest,
            turn_id="turn:pg-quarantine-unknown",
            tool_call_id="tool-call:pg-quarantine-unknown",
            tool_name="workspace.read",
            tool_call_digest=canonical_digest({"tool": "pg-quarantine-unknown"}),
            runtime_operation="workspace.read",
            runtime_arguments_digest=canonical_digest({"path": "README.md"}),
            client_request_id="request:pg-quarantine-unknown",
            recovery_consequence=HarnessRecoveryConsequence.OBSERVATION_ONLY,
            created_at_ms=clock(),
        )
        continuity.prepare_tool_step(intent)
        unknown = AgentLoopResult(
            harness_run_id=run.harness_run_id,
            stop_code=RunStopCode.PROVIDER_STATE_UNKNOWN,
            trace=HarnessTrace(
                run.harness_run_id,
                (HarnessRunEvent(
                    sequence=1,
                    kind="run_stopped",
                    occurred_at_ms=run.created_at_ms + 2,
                    payload={"reason": "lost result with unresolved Tool"},
                ),),
            ),
            conclusion=None,
            messages=(), observations=(),
            model_calls=0, tool_calls=0, observation_bytes=0, usage={},
        )
        recorder = IndependentRunRecorder(self.store, run, continuity.binding, clock_ms=clock)
        outcome = recorder.record_result(
            unknown, started_at_ms=run.created_at_ms,
            finished_at_ms=run.created_at_ms + 3,
        )
        self.assertIsNotNone(outcome)
        self.assertEqual(outcome.receipt.stop_reason, "unknown")
        self.assertEqual(self.store.load_run(run.harness_run_id).status.value, "stopped")
        with PostgresHarnessStore(self.dsn, schema=self.schema) as reopened:
            observer = EventSourcedRunContinuity.open(
                reopened, run.harness_run_id, clock_ms=clock
            )
            assessment = observer.inspect_finalization_source()
            self.assertEqual(assessment["sourceStanding"], "blocked")
            self.assertIn("unknown_run_stop", assessment["blockers"])
            self.assertIn("tool_unsettled", assessment["blockers"])
            self.assertEqual(assessment["unsettledToolIntentDigests"], [intent.digest])
            self.assertEqual(assessment["runtimeClaimStanding"], "unknown")
            self.assertEqual(assessment["externalDeliveryStanding"], "unknown")
            pending_observation = {"schemaVersion": 1, "kind": "pg.late", "status": "observed"}
            late_receipt = HarnessToolStepReceipt(
                receipt_id="harness-tool-step-receipt:pg-quarantine-late",
                intent_digest=intent.digest,
                harness_run_id=run.harness_run_id,
                tool_call_id=intent.tool_call_id,
                status=HarnessToolStepStatus.OBSERVED,
                runtime_job_ref="runtime-job:pg-quarantine-late",
                observation_digest=canonical_digest(pending_observation),
                reconciled=True,
                created_at_ms=clock(),
            )
            with self.assertRaises(HarnessTerminalConflict):
                observer.record_tool_step_receipt(late_receipt, pending_observation)
            self.assertEqual(observer.inspect_finalization_source()["sourceStanding"], "blocked")
            self.store.validate_run_history(run.harness_run_id)
            self.assertTrue(self.store.doctor()["healthy"])

            # Foreign-Writer/DB operator tampering can remove just the
            # original terminal Event->Receipt edge while the CAS bytes and
            # Run projection still look perfectly valid. Structural checks
            # alone previously certified this as healthy.
            from ordivon_harness.store_errors import HarnessJournalCorruption

            terminal_event_id = self.store.load_run(run.harness_run_id).terminal_event_id
            typed_refs = self.store.connection.execute(
                "SELECT ref.digest FROM run_object_refs ref "
                "JOIN objects obj ON obj.digest=ref.digest "
                "WHERE ref.event_id=%s AND ref.role='reference' "
                "AND obj.kind='independent-harness-run-receipt'",
                (terminal_event_id,),
            ).fetchall()
            self.assertEqual(len(typed_refs), 1)
            typed_digest = typed_refs[0]["digest"]
            self.assertIsInstance(
                self.store.get_object(
                    typed_digest, expected_kind="independent-harness-run-receipt"
                ), dict
            )
            with self.store.connection.transaction():
                deleted = self.store.connection.execute(
                    "DELETE FROM run_object_refs WHERE event_id=%s "
                    "AND digest=%s AND role='reference'",
                    (terminal_event_id, typed_digest),
                ).rowcount
                self.assertEqual(deleted, 1)
            self.assertEqual(
                self.store.load_run(run.harness_run_id).status.value, "stopped"
            )
            with self.assertRaises(HarnessJournalCorruption):
                self.store.validate_run_history(run.harness_run_id)
            with self.assertRaises(HarnessJournalCorruption):
                self.store.doctor()

    def test_pg_history_doctor_rejects_structurally_valid_foreign_unknown_without_original_receipt(self) -> None:
        """A foreign writer can persist a structurally valid STOPPED event but
        cannot turn an ungrounded UNKNOWN stopCode into trusted history.
        """
        from ordivon_harness.store_errors import HarnessJournalCorruption

        run = contract()
        self.assertEqual(self.store.create_run(run), HarnessEventAdmission.CREATED)
        before = self.store.load_run(run.harness_run_id)
        event_id = "event:pg-doctor-unqualified-foreign-unknown"
        at = before.updated_at_ms + 1
        payload = self.store.put_object({
            "schemaVersion": 1,
            "kind": "ordivon.harness-run-event-payload",
            "eventKind": "harness.run-stopped",
            "data": {"stopCode": "runtime_unknown"},
        }, kind="ordivon.harness-run-event-payload")
        # Operator-only test injection models an external Rust writer
        # bypassing Python append_events; no business code can call this path.
        with self.store.connection.transaction():
            self.store.connection.execute(
                "INSERT INTO run_events(event_id,harness_run_id,run_revision,"
                "event_kind,payload_digest,recorded_at_ms) "
                "VALUES(%s,%s,%s,%s,%s,%s)",
                (event_id, run.harness_run_id, before.revision + 1,
                 "harness.run-stopped", payload.digest, at),
            )
            self.store.connection.execute(
                "INSERT INTO run_object_refs(harness_run_id,event_id,digest,role) "
                "VALUES(%s,%s,%s,'payload')",
                (run.harness_run_id, event_id, payload.digest),
            )
            self.store.connection.execute(
                "UPDATE runs SET status='stopped',revision=%s,updated_at_ms=%s,"
                "terminal_event_id=%s WHERE harness_run_id=%s",
                (before.revision + 1, at, event_id, run.harness_run_id),
            )
        self.assertEqual(self.store.load_run(run.harness_run_id).status.value, "stopped")
        with self.assertRaises(HarnessJournalCorruption):
            self.store.validate_run_history(run.harness_run_id)
        with self.assertRaises(HarnessJournalCorruption):
            self.store.doctor()

    def test_pg_doctor_rejects_foreign_completed_over_unsettled_original_provider(self) -> None:
        """A structurally valid foreign terminal cannot hide a real Provider
        CLAIMED in the immutable original Journal from Doctor consumers.
        """
        from ordivon_harness.store_errors import HarnessJournalCorruption

        run = contract()
        self.store.create_run(run)
        clock = MutableClock()
        continuity = EventSourcedRunContinuity(self.store, run, clock_ms=clock)
        continuity.bind_state(state())
        continuity.claim_provider_call(
            source=continuity.assignment_provider_source(),
            turn_id="turn:pg-foreign-completed-pending-provider",
            turn_sequence=1,
            request_digest=canonical_digest({"request": "foreign-pending-provider"}),
            provider_request_digest=canonical_digest({"wire": "foreign-pending-provider"}),
            adapter_id=run.adapter_id,
            requested_model_id=run.requested_model_id,
            holder_id="holder:foreign-pending-provider",
            ttl_ms=10_000,
        )
        before = self.store.load_run(run.harness_run_id)
        self.assertFalse(before.status.terminal)
        at = before.updated_at_ms + 1
        event_id = "event:pg-doctor-foreign-completed-over-provider"
        payload = self.store.put_object({
            "schemaVersion": 1,
            "kind": "ordivon.harness-run-event-payload",
            "eventKind": "harness.run-completed",
            "data": {"stopReason": "completed"},
        }, kind="ordivon.harness-run-event-payload")
        with self.store.connection.transaction():
            self.store.connection.execute(
                "INSERT INTO run_events(event_id,harness_run_id,run_revision,"
                "event_kind,payload_digest,recorded_at_ms) "
                "VALUES(%s,%s,%s,%s,%s,%s)",
                (event_id, run.harness_run_id, before.revision + 1,
                 "harness.run-completed", payload.digest, at),
            )
            self.store.connection.execute(
                "INSERT INTO run_object_refs(harness_run_id,event_id,digest,role) "
                "VALUES(%s,%s,%s,'payload')",
                (run.harness_run_id, event_id, payload.digest),
            )
            self.store.connection.execute(
                "UPDATE runs SET status='completed',revision=%s,updated_at_ms=%s,"
                "terminal_event_id=%s WHERE harness_run_id=%s",
                (before.revision + 1, at, event_id, run.harness_run_id),
            )
        self.assertEqual(
            self.store.load_run(run.harness_run_id).status.value, "completed"
        )
        # This is a Doctor semantic qualification: structural history alone
        # is not a certified normal terminal with old pending Provider effects.
        with self.assertRaises(HarnessJournalCorruption):
            self.store.doctor()

    def test_unqualified_unknown_fault_cannot_bypass_pg_terminal_guard(self) -> None:
        """A raw Event with a hand-written stopCode cannot spoof a qualified
        immutable UNKNOWN fault receipt to bypass normal Finalization.
        """
        from ordivon_harness.store_errors import HarnessTerminalConflict

        run = tool_fixture.private_tool_contract()
        self.store.create_run(run)
        clock = MutableClock()
        continuity = EventSourcedRunContinuity(self.store, run, clock_ms=clock)
        continuity.bind_state(state())
        binding = continuity.binding
        intent = HarnessToolStepIntent(
            intent_id="harness-tool-step-intent:spoofed-unknown",
            harness_run_id=run.harness_run_id,
            assignment_id=binding.assignment_id,
            assignment_generation=binding.assignment_generation,
            assignment_digest=binding.assignment_digest,
            turn_id="turn:spoofed-unknown",
            tool_call_id="tool-call:spoofed-unknown",
            tool_name="workspace.read",
            tool_call_digest=canonical_digest({"tool": "spoofed-unknown"}),
            runtime_operation="workspace.read",
            runtime_arguments_digest=canonical_digest({"path": "README.md"}),
            client_request_id="request:spoofed-unknown",
            recovery_consequence=HarnessRecoveryConsequence.OBSERVATION_ONLY,
            created_at_ms=clock(),
        )
        continuity.prepare_tool_step(intent)
        current = self.store.load_run(run.harness_run_id)
        now = current.updated_at_ms + 1
        lease = self.store.acquire_run_lease(
            run.harness_run_id,
            owner_id="worker:forged-unknown",
            ttl_ms=10_000, now_ms=now,
        )
        with self.assertRaises(HarnessTerminalConflict):
            self.store.append_events(
                harness_run_id=run.harness_run_id,
                events=(HarnessEventWrite(
                    event_id="event:unqualified-unknown-fault",
                    event_kind="harness.run-stopped",
                    data={"stopCode": "provider_state_unknown"},
                    recorded_at_ms=now + 1,
                ),),
                expected_revision=lease.run_revision,
                lease=lease,
                lease_checked_at_ms=now,
            )
        self.assertEqual(self.store.load_run(run.harness_run_id).revision, current.revision)
        self.assertTrue(self.store.release_run_lease(lease))

    def test_finalization_detects_pending_tool_across_pg_reopen_and_settlement(self) -> None:
        """A persisted Intent is a consumer even with no active Runtime Job."""
        from ordivon_harness.ordivon.continuity_guards import (
            inspect_all_unsettled_effect_sources,
        )

        run = tool_fixture.private_tool_contract()
        self.store.create_run(run)
        clock = MutableClock()
        continuity = EventSourcedRunContinuity(self.store, run, clock_ms=clock)
        continuity.bind_state(state())
        binding = continuity.binding
        intent = HarnessToolStepIntent(
            intent_id="harness-tool-step-intent:finalization-001",
            harness_run_id=run.harness_run_id,
            assignment_id=binding.assignment_id,
            assignment_generation=binding.assignment_generation,
            assignment_digest=binding.assignment_digest,
            turn_id="turn:finalization-001",
            tool_call_id="tool-call:finalization-001",
            tool_name="workspace.read",
            tool_call_digest=canonical_digest({"toolCall": "finalization-001"}),
            runtime_operation="workspace.read",
            runtime_arguments_digest=canonical_digest({"relativePath": "README.md"}),
            client_request_id="request:finalization-001",
            recovery_consequence=HarnessRecoveryConsequence.OBSERVATION_ONLY,
            created_at_ms=clock(),
        )
        continuity.prepare_tool_step(intent)
        with PostgresHarnessStore(self.dsn, schema=self.schema) as reopened:
            replayed = EventSourcedRunContinuity.open(
                reopened, run.harness_run_id, clock_ms=clock
            )
            provider_ids, tool_ids = inspect_all_unsettled_effect_sources(
                reopened.list_run_events(run.harness_run_id),
                store=reopened,
                harness_run_id=run.harness_run_id,
                binding=replayed.binding,
                allow_tool_content=run.privacy.allow_tool_content,
                provider_record_reader=replayed._load_provider_from_event,
            )
            self.assertEqual(provider_ids, ())
            self.assertEqual(tool_ids, (intent.digest,))
        observation = {
            "schemaVersion": 1,
            "kind": "pg.test-observation",
            "status": "observed",
        }
        clock.advance()
        receipt = HarnessToolStepReceipt(
            receipt_id="harness-tool-step-receipt:finalization-001",
            intent_digest=intent.digest, harness_run_id=run.harness_run_id,
            tool_call_id=intent.tool_call_id,
            status=HarnessToolStepStatus.OBSERVED,
            runtime_job_ref="runtime-job:finalization-001",
            observation_digest=canonical_digest(observation),
            reconciled=False, created_at_ms=clock(),
        )
        continuity.record_tool_step_receipt(receipt, observation)
        with PostgresHarnessStore(self.dsn, schema=self.schema) as reopened:
            provider_ids, tool_ids = inspect_all_unsettled_effect_sources(
                reopened.list_run_events(run.harness_run_id),
                store=reopened,
                harness_run_id=run.harness_run_id,
                binding=continuity.binding,
                allow_tool_content=run.privacy.allow_tool_content,
                provider_record_reader=continuity._load_provider_from_event,
            )
            self.assertEqual(provider_ids, ())
            self.assertEqual(tool_ids, ())

    def test_unresolved_tool_cannot_be_replaced_by_new_intent(self) -> None:
        """Original PG must not forget a pending or UNKNOWN physical Tool."""
        run = tool_fixture.private_tool_contract()
        self.store.create_run(run)
        clock = MutableClock()
        continuity = EventSourcedRunContinuity(self.store, run, clock_ms=clock)
        continuity.bind_state(state())
        binding = continuity.binding
        first = HarnessToolStepIntent(
            intent_id="harness-tool-step-intent:pg-unsettled-first",
            harness_run_id=run.harness_run_id,
            assignment_id=binding.assignment_id,
            assignment_generation=binding.assignment_generation,
            assignment_digest=binding.assignment_digest,
            turn_id="turn:pg-unsettled-first",
            tool_call_id="tool-call:pg-unsettled-first",
            tool_name="workspace.read",
            tool_call_digest=canonical_digest({"toolCall": "first"}),
            runtime_operation="workspace.read",
            runtime_arguments_digest=canonical_digest({"relativePath": "README.md"}),
            client_request_id="request:pg-unsettled-first",
            recovery_consequence=HarnessRecoveryConsequence.OBSERVATION_ONLY,
            created_at_ms=clock(),
        )
        continuity.prepare_tool_step(first)
        second = replace(
            first,
            intent_id="harness-tool-step-intent:pg-unsettled-second",
            turn_id="turn:pg-unsettled-second",
            tool_call_id="tool-call:pg-unsettled-second",
            tool_call_digest=canonical_digest({"toolCall": "second"}),
            client_request_id="request:pg-unsettled-second",
            created_at_ms=clock(),
        )
        with self.assertRaisesRegex(HarnessSuperseded, "unresolved Tool"):
            continuity.prepare_tool_step(second)
        observation = {
            "schemaVersion": 1, "kind": "pg.test-observation", "status": "unknown"
        }
        clock.advance()
        unknown = HarnessToolStepReceipt(
            receipt_id="harness-tool-step-receipt:pg-unsettled-unknown",
            intent_digest=first.digest, harness_run_id=run.harness_run_id,
            tool_call_id=first.tool_call_id,
            status=HarnessToolStepStatus.UNKNOWN,
            runtime_job_ref="runtime-job:pg-unsettled",
            observation_digest=canonical_digest(observation),
            reconciled=False, created_at_ms=clock(),
        )
        continuity.record_tool_step_receipt(unknown, observation)
        unknown_source = continuity.inspect_unsettled_tool_sources()
        self.assertEqual(unknown_source["sourceStanding"], "blocked")
        self.assertEqual(len(unknown_source["unsettledIntents"]), 1)
        self.assertEqual(
            unknown_source["unsettledIntents"][0]["lastRecordedStatus"],
            HarnessToolStepStatus.UNKNOWN.value,
        )
        # This is only the Job identity claimed in the Harness Journal.
        # The natural Runtime Owner must independently verify physical Job truth.
        self.assertEqual(
            unknown_source["unsettledIntents"][0]["sourceOwnerJobRef"],
            unknown.runtime_job_ref,
        )
        self.assertFalse(unknown_source["safeToDispatch"])
        with self.assertRaisesRegex(HarnessSuperseded, "unresolved Tool"):
            continuity.prepare_tool_step(second)
        observed = {
            "schemaVersion": 1, "kind": "pg.test-observation", "status": "observed"
        }
        clock.advance()
        successor = replace(
            unknown,
            receipt_id="harness-tool-step-receipt:pg-unsettled-reconciled",
            status=HarnessToolStepStatus.OBSERVED,
            observation_digest=canonical_digest(observed),
            reconciled=True,
            previous_receipt_digest=unknown.digest,
            created_at_ms=clock(),
        )
        continuity.record_tool_step_receipt(successor, observed)
        settled_source = continuity.inspect_unsettled_tool_sources()
        self.assertEqual(settled_source["sourceStanding"], "no-pending-tool-intent")
        self.assertEqual(settled_source["unsettledIntents"], [])
        self.assertFalse(settled_source["safeToDispatch"])
        continuity.prepare_tool_step(second)

        # A physical no-future-spawn ACK cannot enumerate ONLY unsettled Tool
        # heads. The already-observed first Intent is still an issuer-issued
        # identity, and the second prepared Intent has no receipt yet.
        unsettled = continuity.inspect_unsettled_tool_sources()
        self.assertEqual(
            [row["clientRequestId"] for row in unsettled["unsettledIntents"]],
            [second.client_request_id],
        )
        issued = continuity.inspect_issued_tool_sources()
        self.assertEqual(issued["originalRunIssuedCount"], 2)
        self.assertEqual(issued["kind"], "ordivon.harness-issued-tool-sources")
        self.assertEqual(issued["noFutureSpawnAckStanding"], "unknown")
        self.assertFalse(issued["safeToAcknowledgeNoFutureSpawn"])
        self.assertFalse(issued["safeToDispatch"])
        self.assertEqual(
            {row["clientRequestId"] for row in issued["issuedIntents"]},
            {first.client_request_id, second.client_request_id},
        )
        first_source = next(
            row for row in issued["issuedIntents"]
            if row["clientRequestId"] == first.client_request_id
        )
        self.assertEqual(first_source["lastRecordedStatus"], "observed")
        self.assertEqual(first_source["sourceOwnerJobRef"], unknown.runtime_job_ref)
        self.assertEqual(
            next(
                row for row in issued["issuedIntents"]
                if row["clientRequestId"] == second.client_request_id
            )["lastRecordedStatus"],
            None,
        )
        self.assertEqual(continuity.load_current_tool_step().intent, second)

        # Verify the real supported HarnessAgentRun API from a second PG
        # connection, not only an internal EventSourcedRunContinuity object.
        from types import SimpleNamespace
        from ordivon_harness.agent_run import structured_completion_contract_digest

        public_run = HarnessAgentRun.open(
            self.dsn,
            self.schema,
            run.harness_run_id,
            adapter_factory=lambda c: SimpleNamespace(
                adapter_id=c.adapter_id,
                model_id=c.requested_model_id,
                structured_completion_contract_digest=structured_completion_contract_digest(
                    c.completion_contract
                ),
            ),
            tool_bridge=SimpleNamespace(
                catalog_digest=run.tool_catalog_digest,
                grant_digest=run.tool_grant_digest,
            ),
        )
        public_source = public_run.inspect_issued_tool_sources()
        self.assertEqual(public_source["issuedIntents"], issued["issuedIntents"])
        self.assertFalse(public_source["safeToAcknowledgeNoFutureSpawn"])

    def test_effect_source_inspection_rejects_missing_original_history(self) -> None:
        """An intact latest revision cannot certify a truncated older Tool history."""
        from unittest.mock import patch
        from ordivon_harness.store_errors import HarnessJournalCorruption

        run = tool_fixture.private_tool_contract()
        self.store.create_run(run)
        clock = MutableClock()
        continuity = EventSourcedRunContinuity(self.store, run, clock_ms=clock)
        continuity.bind_state(state())
        binding = continuity.binding
        intent = HarnessToolStepIntent(
            intent_id="harness-tool-step-intent:source-cut-old",
            harness_run_id=run.harness_run_id,
            assignment_id=binding.assignment_id,
            assignment_generation=binding.assignment_generation,
            assignment_digest=binding.assignment_digest,
            turn_id="turn:source-cut-old",
            tool_call_id="tool-call:source-cut-old",
            tool_name="workspace.read",
            tool_call_digest=canonical_digest({"tool": "source-cut"}),
            runtime_operation="workspace.read",
            runtime_arguments_digest=canonical_digest({"path": "README.md"}),
            client_request_id="request:source-cut-old",
            recovery_consequence=HarnessRecoveryConsequence.OBSERVATION_ONLY,
            created_at_ms=clock(),
        )
        continuity.prepare_tool_step(intent)
        observation = {"schemaVersion": 1, "kind": "pg.test-observation", "status": "observed"}
        clock.advance()
        receipt = HarnessToolStepReceipt(
            receipt_id="harness-tool-step-receipt:source-cut-old",
            intent_digest=intent.digest, harness_run_id=run.harness_run_id,
            tool_call_id=intent.tool_call_id, status=HarnessToolStepStatus.OBSERVED,
            runtime_job_ref="runtime-job:source-cut-old",
            observation_digest=canonical_digest(observation),
            reconciled=False, created_at_ms=clock(),
        )
        continuity.record_tool_step_receipt(receipt, observation)
        lease = self.store.acquire_run_lease(
            run.harness_run_id, owner_id="worker:source-cut", ttl_ms=10000, now_ms=clock(),
        )
        self.store.append_event(
            event_id="event:source-cut-tail", harness_run_id=run.harness_run_id,
            event_kind="harness.trace-recorded", data={"trace": "tail"},
            expected_revision=lease.run_revision, recorded_at_ms=clock(),
            lease=lease, lease_checked_at_ms=clock(),
        )
        self.assertEqual(continuity.inspect_issued_tool_sources()["originalRunIssuedCount"], 1)
        history = self.store.list_run_events(run.harness_run_id)
        truncated = tuple(e for e in history if e.data.get("toolStepIntentDigest") != intent.digest)
        self.assertLess(len(truncated), len(history))
        self.assertEqual(truncated[-1], history[-1])
        # The real PG original is unchanged. Simulate a partial read projection
        # which loses the whole settled Intent/Receipt pair, but not its tail.
        with patch.object(self.store, "list_run_events", return_value=truncated):
            with self.assertRaises((HarnessJournalCorruption, HarnessRevisionConflict)):
                continuity.inspect_issued_tool_sources()
            with self.assertRaises((HarnessJournalCorruption, HarnessRevisionConflict)):
                continuity.inspect_unsettled_tool_sources()
        # The same missing source must block new admission, not only the
        # later diagnostic. A fresh request key is intentionally legitimate.
        later = replace(
            intent, intent_id="harness-tool-step-intent:source-cut-next",
            turn_id="turn:source-cut-next", tool_call_id="tool-call:source-cut-next",
            tool_call_digest=canonical_digest({"tool": "source-cut-next"}),
            client_request_id="request:source-cut-next", created_at_ms=clock(),
        )
        before = self.store.load_run(run.harness_run_id).revision
        with patch.object(self.store, "list_run_events", return_value=truncated):
            with self.assertRaises((HarnessJournalCorruption, HarnessRevisionConflict, HarnessSuperseded)):
                continuity.prepare_tool_step(later)
        self.assertEqual(self.store.load_run(run.harness_run_id).revision, before)
        # Real PG corruption: remove only the persisted payload reference,
        # leaving the Event and CAS object readable.
        prepared = next(e for e in history if e.event_kind == "harness.tool-step-prepared")
        self.store.connection.execute(
            "DELETE FROM run_object_refs WHERE event_id=%s AND role='payload'",
            (prepared.event_id,),
        )
        for inspect in (continuity.inspect_issued_tool_sources,
                        continuity.inspect_unsettled_tool_sources,
                        continuity.inspect_finalization_source):
            with self.assertRaises(HarnessJournalCorruption):
                inspect()

    def test_issued_epoch_rejects_reused_runtime_client_request_id(self) -> None:
        """A second prepared Intent cannot reuse the first Runtime Job key."""
        run = tool_fixture.private_tool_contract()
        self.store.create_run(run)
        clock = MutableClock()
        continuity = EventSourcedRunContinuity(self.store, run, clock_ms=clock)
        continuity.bind_state(state())
        binding = continuity.binding
        first = HarnessToolStepIntent(
            intent_id="harness-tool-step-intent:duplicate-epoch-a",
            harness_run_id=run.harness_run_id,
            assignment_id=binding.assignment_id,
            assignment_generation=binding.assignment_generation,
            assignment_digest=binding.assignment_digest,
            turn_id="turn:duplicate-epoch-a",
            tool_call_id="tool-call:duplicate-epoch-a",
            tool_name="workspace.read",
            tool_call_digest=canonical_digest({"call": "a"}),
            runtime_operation="workspace.read",
            runtime_arguments_digest=canonical_digest({"path": "first"}),
            client_request_id="request:duplicate-runtime-epoch",
            recovery_consequence=HarnessRecoveryConsequence.OBSERVATION_ONLY,
            created_at_ms=clock(),
        )
        continuity.prepare_tool_step(first)
        observed = {
            "schemaVersion": 1,
            "kind": "pg.test-observation",
            "status": "observed",
        }
        clock.advance()
        receipt = HarnessToolStepReceipt(
            receipt_id="harness-tool-step-receipt:duplicate-epoch-observed",
            intent_digest=first.digest,
            harness_run_id=run.harness_run_id,
            tool_call_id=first.tool_call_id,
            status=HarnessToolStepStatus.OBSERVED,
            runtime_job_ref="runtime-job:duplicate-epoch",
            observation_digest=canonical_digest(observed),
            reconciled=False,
            created_at_ms=clock(),
        )
        continuity.record_tool_step_receipt(receipt, observed)
        second = replace(
            first,
            intent_id="harness-tool-step-intent:duplicate-epoch-b",
            turn_id="turn:duplicate-epoch-b",
            tool_call_id="tool-call:duplicate-epoch-b",
            tool_call_digest=canonical_digest({"call": "b"}),
            runtime_arguments_digest=canonical_digest({"path": "second"}),
            created_at_ms=clock(),
        )
        before = self.store.load_run(run.harness_run_id).revision
        with self.assertRaisesRegex(HarnessSuperseded, "reuse a clientRequestId"):
            continuity.prepare_tool_step(second)
        self.assertEqual(self.store.load_run(run.harness_run_id).revision, before)
        self.assertEqual(continuity.inspect_issued_tool_sources()["originalRunIssuedCount"], 1)
        self.assertEqual(continuity.inspect_unsettled_tool_sources()["unsettledIntents"], [])
        # A distinct legitimate request still proceeds; denial is not a
        # blanket prohibition on subsequent Tool calls.
        distinct = replace(second, client_request_id="request:distinct-runtime-epoch")
        continuity.prepare_tool_step(distinct)
        self.assertEqual(continuity.inspect_issued_tool_sources()["originalRunIssuedCount"], 2)
        self.assertEqual(continuity.load_current_tool_step().intent, distinct)

        # Retain the original legacy-corruption read test with a real PG
        # Journal. Emulate only the old writer's missing identity guard.
        from inspect import getmodule
        from unittest.mock import patch

        clock.advance()
        continuity.record_tool_step_receipt(
            replace(
                receipt, receipt_id="harness-tool-step-receipt:distinct-observed",
                intent_digest=distinct.digest, tool_call_id=distinct.tool_call_id,
                runtime_job_ref="runtime-job:distinct", created_at_ms=clock(),
            ),
            observed,
        )
        legacy = replace(
            second, intent_id="harness-tool-step-intent:legacy-reused-key",
            tool_call_id="tool-call:legacy-reused-key",
            turn_id="turn:legacy-reused-key", created_at_ms=clock(),
        )
        admission_module = getmodule(continuity.prepare_tool_step)
        current_scan = admission_module.inspect_all_unsettled_effect_sources

        def legacy_scan(*args, **kwargs):
            kwargs.pop("new_tool_client_request_id", None)
            return current_scan(*args, **kwargs)

        with patch.object(admission_module, "inspect_all_unsettled_effect_sources", legacy_scan):
            continuity.prepare_tool_step(legacy)
        self.assertEqual(
            continuity.inspect_unsettled_tool_sources()["unsettledIntents"][0]["clientRequestId"],
            first.client_request_id,
        )
        with self.assertRaisesRegex(ValueError, "reuse a clientRequestId"):
            continuity.inspect_issued_tool_sources()

    def test_pending_provider_cannot_admit_new_tool_physical_intent(self) -> None:
        """A Provider CLAIMED/UNKNOWN is an unresolved source effect, even
        when no Tool event exists yet. Model and Tool effects cannot cross
        each other while original PG cannot certify the Provider outcome.
        """
        run = contract()
        self.store.create_run(run)
        clock = MutableClock()
        continuity = EventSourcedRunContinuity(self.store, run, clock_ms=clock)
        continuity.bind_state(state())
        claimed = continuity.claim_provider_call(
            source=continuity.assignment_provider_source(),
            turn_id="turn:pg-unsettled-provider",
            turn_sequence=1,
            request_digest=canonical_digest({"provider": "claim"}),
            provider_request_digest=canonical_digest({"provider": "wire"}),
            adapter_id=run.adapter_id,
            requested_model_id=run.requested_model_id,
            holder_id="holder:pg-unsettled-provider",
            ttl_ms=10_000,
        )
        self.assertEqual(claimed.record.status.value, "claimed")
        binding = continuity.binding
        intent = HarnessToolStepIntent(
            intent_id="harness-tool-step-intent:pg-while-provider-unsettled",
            harness_run_id=run.harness_run_id,
            assignment_id=binding.assignment_id,
            assignment_generation=binding.assignment_generation,
            assignment_digest=binding.assignment_digest,
            turn_id="turn:pg-while-provider-unsettled",
            tool_call_id="tool-call:pg-while-provider-unsettled",
            tool_name="workspace.read",
            tool_call_digest=canonical_digest({"toolCall": "while-provider-unsettled"}),
            runtime_operation="workspace.read",
            runtime_arguments_digest=canonical_digest({"relativePath": "README.md"}),
            client_request_id="request:pg-while-provider-unsettled",
            recovery_consequence=HarnessRecoveryConsequence.OBSERVATION_ONLY,
            created_at_ms=clock(),
        )
        revision = self.store.load_run(run.harness_run_id).revision
        with self.assertRaisesRegex(HarnessSuperseded, "unresolved Provider"):
            continuity.prepare_tool_step(intent)
        self.assertEqual(self.store.load_run(run.harness_run_id).revision, revision)
        dispatching = continuity.mark_provider_call_dispatching(claimed)
        self.assertEqual(dispatching.record.status.value, "dispatching")
        revision = self.store.load_run(run.harness_run_id).revision
        with self.assertRaisesRegex(HarnessSuperseded, "unresolved Provider"):
            continuity.prepare_tool_step(intent)
        self.assertEqual(self.store.load_run(run.harness_run_id).revision, revision)
        ambiguous = provider_failure(
            dispatching.record.provider_call_id,
            dispatching.record.request_digest,
            dispatching.record.provider_request_digest,
            safety="dispatch_ambiguous",
            suffix="pg-provider-before-tool",
        )
        unknown = continuity.fail_provider_call(dispatching, failure=ambiguous)
        self.assertEqual(unknown.record.status.value, "unknown")
        revision = self.store.load_run(run.harness_run_id).revision
        with self.assertRaisesRegex(HarnessSuperseded, "unresolved Provider"):
            continuity.prepare_tool_step(intent)
        self.assertEqual(self.store.load_run(run.harness_run_id).revision, revision)

    def test_settled_provider_does_not_block_normal_tool_admission(self) -> None:
        """A complete Provider is not an unresolved effect; no overblocking."""
        run = contract()
        self.store.create_run(run)
        clock = MutableClock()
        continuity = EventSourcedRunContinuity(self.store, run, clock_ms=clock)
        continuity.bind_state(state())
        claimed = continuity.claim_provider_call(
            source=continuity.assignment_provider_source(),
            turn_id="turn:pg-provider-completed",
            turn_sequence=1,
            request_digest=canonical_digest({"provider": "complete"}),
            provider_request_digest=canonical_digest({"provider": "wire-complete"}),
            adapter_id=run.adapter_id,
            requested_model_id=run.requested_model_id,
            holder_id="holder:pg-provider-completed",
            ttl_ms=10_000,
        )
        dispatching = continuity.mark_provider_call_dispatching(claimed)
        completed = continuity.complete_provider_call(
            dispatching, provider_result("pg-normal-before-tool")
        )
        self.assertEqual(completed.record.status.value, "completed")
        binding = continuity.binding
        intent = HarnessToolStepIntent(
            intent_id="harness-tool-step-intent:pg-after-provider-completed",
            harness_run_id=run.harness_run_id,
            assignment_id=binding.assignment_id,
            assignment_generation=binding.assignment_generation,
            assignment_digest=binding.assignment_digest,
            turn_id="turn:pg-after-provider-completed",
            tool_call_id="tool-call:pg-after-provider-completed",
            tool_name="workspace.read",
            tool_call_digest=canonical_digest({"toolCall": "after-provider-completed"}),
            runtime_operation="workspace.read",
            runtime_arguments_digest=canonical_digest({"relativePath": "README.md"}),
            client_request_id="request:pg-after-provider-completed",
            recovery_consequence=HarnessRecoveryConsequence.OBSERVATION_ONLY,
            created_at_ms=clock(),
        )
        continuity.prepare_tool_step(intent)
        self.assertEqual(continuity.load_current_tool_step().intent.digest, intent.digest)
        # Both real original effects settle. Terminal and Doctor must use
        # immutable evidence, not construct an executing Run command facade.
        from unittest.mock import patch

        observation = {"schemaVersion": 1, "kind": "pg.observed", "status": "observed"}
        clock.advance()
        continuity.record_tool_step_receipt(
            HarnessToolStepReceipt(
                receipt_id="harness-tool-step-receipt:pg-read-only-terminal",
                intent_digest=intent.digest, harness_run_id=run.harness_run_id,
                tool_call_id=intent.tool_call_id, status=HarnessToolStepStatus.OBSERVED,
                runtime_job_ref="runtime-job:pg-read-only-terminal",
                observation_digest=canonical_digest(observation), reconciled=False,
                created_at_ms=clock(),
            ), observation,
        )
        before = self.store.load_run(run.harness_run_id)
        now = before.updated_at_ms + 1
        lease = self.store.acquire_run_lease(
            run.harness_run_id, owner_id="worker:read-only-terminal",
            ttl_ms=10_000, now_ms=now,
        )
        with patch.object(
            EventSourcedRunContinuity, "open",
            side_effect=AssertionError("read-only integrity must not open command facade"),
        ):
            self.assertEqual(
                self.store.append_events(
                    harness_run_id=run.harness_run_id,
                    events=(HarnessEventWrite(
                        event_id="event:pg-read-only-terminal",
                        event_kind="harness.run-completed",
                        data={"stopReason": "completed"}, recorded_at_ms=now + 1,
                    ),),
                    expected_revision=lease.run_revision, lease=lease,
                    lease_checked_at_ms=now,
                ), HarnessEventAdmission.CREATED,
            )
            doctor = self.store.doctor()
        self.assertTrue(doctor["healthy"])
        self.assertEqual(doctor["leases"], 0)
        self.assertTrue(self.store.load_run(run.harness_run_id).status.terminal)

    def test_pending_tool_cannot_admit_new_provider_claim(self) -> None:
        """Provider may not dispatch while an older Tool effect is pending."""
        run = contract()
        self.store.create_run(run)
        clock = MutableClock()
        continuity = EventSourcedRunContinuity(self.store, run, clock_ms=clock)
        continuity.bind_state(state())
        binding = continuity.binding
        intent = HarnessToolStepIntent(
            intent_id="harness-tool-step-intent:pg-pending-before-provider",
            harness_run_id=run.harness_run_id,
            assignment_id=binding.assignment_id,
            assignment_generation=binding.assignment_generation,
            assignment_digest=binding.assignment_digest,
            turn_id="turn:pg-pending-before-provider",
            tool_call_id="tool-call:pg-pending-before-provider",
            tool_name="workspace.read",
            tool_call_digest=canonical_digest({"toolCall": "pending-before-provider"}),
            runtime_operation="workspace.read",
            runtime_arguments_digest=canonical_digest({"relativePath": "README.md"}),
            client_request_id="request:pg-pending-before-provider",
            recovery_consequence=HarnessRecoveryConsequence.OBSERVATION_ONLY,
            created_at_ms=clock(),
        )
        pending_snapshot = continuity.prepare_tool_step(intent)
        revision = self.store.load_run(run.harness_run_id).revision
        with self.assertRaisesRegex(
            HarnessProviderCallRecoveryRequired, "unresolved Tool"
        ):
            continuity.claim_provider_call(
                source=continuity.snapshot_provider_source(pending_snapshot),
                turn_id="turn:pg-after-pending-tool",
                turn_sequence=1,
                request_digest=canonical_digest({"request": "after-tool"}),
                provider_request_digest=canonical_digest({"wire": "after-tool"}),
                adapter_id=run.adapter_id,
                requested_model_id=run.requested_model_id,
                holder_id="holder:pg-after-pending-tool",
                ttl_ms=10_000,
            )
        self.assertEqual(self.store.load_run(run.harness_run_id).revision, revision)
        # A real settled original Tool permits the same legitimate Snapshot
        # Provider source; the guard must not turn safe recovery into deadlock.
        observation = {"schemaVersion": 1, "kind": "pg.after-tool", "status": "observed"}
        settled = HarnessToolStepReceipt(
            receipt_id="harness-tool-step-receipt:pg-pending-before-provider-observed",
            intent_digest=intent.digest,
            harness_run_id=run.harness_run_id,
            tool_call_id=intent.tool_call_id,
            status=HarnessToolStepStatus.OBSERVED,
            runtime_job_ref="runtime-job:pg-pending-before-provider-observed",
            observation_digest=canonical_digest(observation),
            reconciled=False,
            created_at_ms=clock(),
        )
        continuity.record_tool_step_receipt(settled, observation)
        claimed = continuity.claim_provider_call(
            source=continuity.snapshot_provider_source(pending_snapshot),
            turn_id="turn:pg-after-pending-tool",
            turn_sequence=1,
            request_digest=canonical_digest({"request": "after-tool"}),
            provider_request_digest=canonical_digest({"wire": "after-tool"}),
            adapter_id=run.adapter_id,
            requested_model_id=run.requested_model_id,
            holder_id="holder:pg-after-pending-tool",
            ttl_ms=10_000,
        )
        self.assertEqual(claimed.record.status.value, "claimed")

    def test_legacy_pending_tool_allows_exact_provider_readonly_replay(self) -> None:
        """Legacy Tool A pending + Provider B claimed: a read-only claim
        replay of the *same* B must not be blocked as a new physical effect.
        """
        from unittest.mock import patch

        run = contract()
        self.store.create_run(run)
        clock = MutableClock()
        legacy = EventSourcedRunContinuity(self.store, run, clock_ms=clock)
        legacy.bind_state(state())
        binding = legacy.binding
        intent = HarnessToolStepIntent(
            intent_id="harness-tool-step-intent:legacy-tool-before-provider",
            harness_run_id=run.harness_run_id,
            assignment_id=binding.assignment_id,
            assignment_generation=binding.assignment_generation,
            assignment_digest=binding.assignment_digest,
            turn_id="turn:legacy-tool-before-provider",
            tool_call_id="tool-call:legacy-tool-before-provider",
            tool_name="workspace.read",
            tool_call_digest=canonical_digest({"toolCall": "legacy-before-provider"}),
            runtime_operation="workspace.read",
            runtime_arguments_digest=canonical_digest({"relativePath": "README.md"}),
            client_request_id="request:legacy-before-provider",
            recovery_consequence=HarnessRecoveryConsequence.OBSERVATION_ONLY,
            created_at_ms=clock(),
        )
        snapshot = legacy.prepare_tool_step(intent)
        claim_args = dict(
            source=legacy.snapshot_provider_source(snapshot),
            turn_id="turn:legacy-provider-after-tool",
            turn_sequence=1,
            request_digest=canonical_digest({"request": "legacy-provider-after-tool"}),
            provider_request_digest=canonical_digest({"wire": "legacy-provider-after-tool"}),
            adapter_id=run.adapter_id,
            requested_model_id=run.requested_model_id,
            holder_id="holder:legacy-provider-after-tool",
            ttl_ms=10_000,
        )
        # Simulate only an old admission policy. The real original PostgreSQL
        # Writer persists the original B claim and A is still unreceipted.
        from inspect import getmodule

        with patch.object(
            getmodule(legacy.claim_provider_call),
            "inspect_all_unsettled_effect_sources",
            return_value=((), ()),
        ):
            claimed = legacy.claim_provider_call(**claim_args)
        self.assertEqual(claimed.record.status.value, "claimed")
        with PostgresHarnessStore(self.dsn, schema=self.schema) as reopened:
            resumed = EventSourcedRunContinuity.open(
                reopened, run.harness_run_id, clock_ms=clock
            )
            resumed.bind_state(state())
            revision = reopened.load_run(run.harness_run_id).revision
            replay = resumed.claim_provider_call(**claim_args)
            self.assertEqual(replay.record.digest, claimed.record.digest)
            self.assertEqual(reopened.load_run(run.harness_run_id).revision, revision)

    def test_legacy_hidden_pending_tool_still_blocks_next_prepare(self) -> None:
        """Old PG Journal: A prepared, B observed, A remains unresolved.

        Simulate the removed legacy admission guard only while preparing B.
        The actual PG writes and receipts still use the normal Store/Writer.
        A modern reopened consumer must not treat the latest B as global truth.
        """
        from unittest.mock import patch
        from ordivon_harness.ordivon.continuity_guards import (
            inspect_all_unsettled_effect_sources,
        )

        run = tool_fixture.private_tool_contract()
        self.store.create_run(run)
        clock = MutableClock()
        legacy = EventSourcedRunContinuity(self.store, run, clock_ms=clock)
        legacy.bind_state(state())
        binding = legacy.binding

        def intent_for(label: str) -> HarnessToolStepIntent:
            return HarnessToolStepIntent(
                intent_id=f"harness-tool-step-intent:legacy-{label}",
                harness_run_id=run.harness_run_id,
                assignment_id=binding.assignment_id,
                assignment_generation=binding.assignment_generation,
                assignment_digest=binding.assignment_digest,
                turn_id=f"turn:legacy-{label}",
                tool_call_id=f"tool-call:legacy-{label}",
                tool_name="workspace.read",
                tool_call_digest=canonical_digest({"legacyToolCall": label}),
                runtime_operation="workspace.read",
                runtime_arguments_digest=canonical_digest({"relativePath": label}),
                client_request_id=f"request:legacy-{label}",
                recovery_consequence=HarnessRecoveryConsequence.OBSERVATION_ONLY,
                created_at_ms=clock(),
            )

        first = intent_for("A")
        second = intent_for("B")
        third = intent_for("C")
        legacy.prepare_tool_step(first)
        # Legacy admission allowed B despite unresolved A. The real original
        # PostgreSQL Journal persists both effects, including B's receipt.
        from inspect import getmodule

        with (
            patch.object(legacy, "load_current_tool_step", side_effect=KeyError),
            patch.object(
                getmodule(legacy.prepare_tool_step),
                "inspect_all_unsettled_effect_sources",
                return_value=((), ()),
            ),
        ):
            legacy.prepare_tool_step(second)
        observation = {"schemaVersion": 1, "kind": "pg.legacy-observation", "status": "observed"}
        receipt = HarnessToolStepReceipt(
            receipt_id="harness-tool-step-receipt:legacy-B",
            intent_digest=second.digest,
            harness_run_id=run.harness_run_id,
            tool_call_id=second.tool_call_id,
            status=HarnessToolStepStatus.OBSERVED,
            runtime_job_ref="runtime-job:legacy-B",
            observation_digest=canonical_digest(observation),
            reconciled=False,
            created_at_ms=clock(),
        )
        legacy.record_tool_step_receipt(receipt, observation)
        with PostgresHarnessStore(self.dsn, schema=self.schema) as reopened:
            current = EventSourcedRunContinuity.open(
                reopened, run.harness_run_id, clock_ms=clock
            )
            self.assertEqual(
                current.load_current_tool_step().receipt.status,
                HarnessToolStepStatus.OBSERVED,
            )
            _, unsettled = inspect_all_unsettled_effect_sources(
                reopened.list_run_events(run.harness_run_id),
                store=reopened,
                harness_run_id=run.harness_run_id,
                binding=current.binding,
                allow_tool_content=run.privacy.allow_tool_content,
                provider_record_reader=current._load_provider_from_event,
            )
            self.assertEqual(unsettled, (first.digest,))
            recovery = current.inspect_unsettled_tool_sources()
            self.assertEqual(recovery["sourceStanding"], "blocked")
            self.assertEqual(recovery["runtimeOwnerProofStanding"], "unknown")
            self.assertFalse(recovery["safeToDispatch"])
            self.assertEqual(recovery["runtimeClaimReleaseStanding"], "unknown")
            self.assertEqual(recovery["contractDigest"], run.digest)
            self.assertEqual(recovery["toolGrantDigest"], run.tool_grant_digest)
            self.assertEqual(len(recovery["unsettledIntents"]), 1)
            source = recovery["unsettledIntents"][0]
            self.assertEqual(source["intentDigest"], first.digest)
            self.assertEqual(source["clientRequestId"], first.client_request_id)
            self.assertEqual(source["toolCallId"], first.tool_call_id)
            self.assertEqual(source["runtimeOperation"], first.runtime_operation)
            self.assertEqual(source["runtimeArgumentsDigest"], first.runtime_arguments_digest)
            self.assertIsNone(source["lastRecordedStatus"])
            self.assertIsNone(source["sourceOwnerJobRef"])
            self.assertNotIn("relativePath", str(recovery))
            self.assertNotIn("originalRequest", str(recovery))
            self.assertEqual(recovery["runRevision"], reopened.load_run(run.harness_run_id).revision)
            revision = reopened.load_run(run.harness_run_id).revision
            current.bind_state(state())
            with self.assertRaisesRegex(HarnessSuperseded, "unresolved Tool"):
                current.prepare_tool_step(third)
            self.assertEqual(reopened.load_run(run.harness_run_id).revision, revision)
            # Old Tool A remains unresolved even after Tool B is OBSERVED.
            # The terminal guard scans ALL historical effects, not only B.
            from ordivon_harness.store_errors import HarnessTerminalConflict

            now = reopened.load_run(run.harness_run_id).updated_at_ms + 1
            lease = reopened.acquire_run_lease(
                run.harness_run_id,
                owner_id="worker:legacy-old-A-normal-terminal",
                ttl_ms=10_000,
                now_ms=now,
            )
            with self.assertRaises(HarnessTerminalConflict):
                reopened.append_events(
                    harness_run_id=run.harness_run_id,
                    events=(HarnessEventWrite(
                        event_id="event:legacy-old-A-must-block-normal-terminal",
                        event_kind="harness.run-completed",
                        data={"stopCode": "candidate_completed"},
                        recorded_at_ms=now + 1,
                    ),),
                    expected_revision=lease.run_revision,
                    lease=lease,
                    lease_checked_at_ms=now,
                )
            self.assertEqual(reopened.load_run(run.harness_run_id).revision, revision)
            self.assertFalse(reopened.load_run(run.harness_run_id).status.terminal)
            self.assertTrue(reopened.release_run_lease(lease))

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


    def test_history_doctor_rejects_missing_ordinary_event_payload_edge(self) -> None:
        """A normal Event must retain its persisted payload edge, not just CAS bytes."""
        from ordivon_harness.store_errors import HarnessJournalCorruption

        run = contract()
        self.store.create_run(run)
        lease = self.store.acquire_run_lease(
            run.harness_run_id, owner_id="worker:ref-edge", ttl_ms=10000,
            now_ms=run.created_at_ms,
        )
        self.store.append_event(
            event_id="event:history-ordinary-payload-edge",
            harness_run_id=run.harness_run_id,
            event_kind="harness.trace-recorded",
            data={"trace": "ordinary"},
            expected_revision=lease.run_revision,
            recorded_at_ms=run.created_at_ms+1,
            lease=lease,
            lease_checked_at_ms=run.created_at_ms,
        )
        original = self.store.list_run_events(run.harness_run_id)[-1]
        self.store.connection.execute(
            "DELETE FROM run_object_refs WHERE event_id=%s AND role='payload'",
            (original.event_id,),
        )
        with self.assertRaises(HarnessJournalCorruption):
            self.store.validate_run_history(run.harness_run_id)

    def test_history_doctor_rejects_missing_original_contract_reference(self) -> None:
        """Created Event explicitly requires original contract CAS reference."""
        from ordivon_harness.store_errors import HarnessJournalCorruption

        run = contract()
        self.store.create_run(run)
        self.store.connection.execute(
            "DELETE FROM run_object_refs WHERE harness_run_id=%s AND role='reference'",
            (run.harness_run_id,),
        )
        with self.assertRaises(HarnessJournalCorruption):
            self.store.validate_run_history(run.harness_run_id)

    def test_history_doctor_rejects_cross_run_reference_ownership(self) -> None:
        """FK validity alone must not make another Run own this Event's edge."""
        from ordivon_harness.store_errors import HarnessJournalCorruption
        from dataclasses import replace

        first = contract()
        second = replace(first, harness_run_id="harness-run:ref-owner-foreign",
                         caller_run_ref="caller-run:ref-owner-foreign")
        self.store.create_run(first)
        self.store.create_run(second)
        original_event = self.store.list_run_events(first.harness_run_id)[0]
        self.store.connection.execute(
            "UPDATE run_object_refs SET harness_run_id=%s "
            "WHERE event_id=%s AND role='payload'",
            (second.harness_run_id, original_event.event_id),
        )
        with self.assertRaises(HarnessJournalCorruption):
            self.store.validate_run_history(first.harness_run_id)

    def test_history_doctor_single_pg_snapshot_avoids_concurrent_writer_false_corruption(self) -> None:
        """One valid concurrent Writer must not splice two committed revisions."""
        from unittest.mock import patch

        run = contract()
        self.store.create_run(run)
        load_before = self.store.load_run
        committed = False

        def race_after_initial_read(harness_run_id: str):
            nonlocal committed
            projection = load_before(harness_run_id)
            if not committed:
                committed = True
                with PostgresHarnessStore(self.dsn, schema=self.schema) as rival:
                    lease = rival.acquire_run_lease(
                        run.harness_run_id, owner_id="worker:concurrent-history",
                        ttl_ms=10000, now_ms=run.created_at_ms,
                    )
                    rival.append_event(
                        event_id="event:concurrent-valid-new-revision",
                        harness_run_id=run.harness_run_id,
                        event_kind="harness.trace-recorded",
                        data={"trace": "valid-concurrent-writer"},
                        expected_revision=lease.run_revision,
                        recorded_at_ms=run.created_at_ms+1,
                        lease=lease,
                        lease_checked_at_ms=run.created_at_ms,
                    )
            return projection

        with patch.object(self.store, "load_run", side_effect=race_after_initial_read):
            self.store.validate_run_history(run.harness_run_id)
        self.assertTrue(committed)
        self.assertEqual(self.store.load_run(run.harness_run_id).revision, 2)
        self.store.validate_run_history(run.harness_run_id)


    def test_full_doctor_counts_are_one_snapshot_during_valid_concurrent_append(self) -> None:
        """Even the global Doctor count must not mix a later Run revision."""
        from unittest.mock import patch

        run = contract()
        self.store.create_run(run)
        original_load = self.store.load_run
        committed = False

        def competing_read(harness_run_id: str):
            nonlocal committed
            before = original_load(harness_run_id)
            if not committed:
                committed = True
                with PostgresHarnessStore(self.dsn, schema=self.schema) as rival:
                    lease = rival.acquire_run_lease(
                        run.harness_run_id, owner_id="worker:doctor-global-race",
                        ttl_ms=10000, now_ms=run.created_at_ms,
                    )
                    rival.append_event(
                        event_id="event:doctor-valid-concurrent-append",
                        harness_run_id=run.harness_run_id,
                        event_kind="harness.trace-recorded",
                        data={"trace": "doctor-global"},
                        expected_revision=lease.run_revision,
                        recorded_at_ms=run.created_at_ms+1,
                        lease=lease,
                        lease_checked_at_ms=run.created_at_ms,
                    )
            return before

        with patch.object(self.store, "load_run", side_effect=competing_read):
            doctor = self.store.doctor()
        self.assertTrue(doctor["healthy"])
        self.assertTrue(committed)
        self.assertEqual(doctor["runs"], 1)
        self.assertEqual(doctor["events"], 1)
        self.assertEqual(self.store.load_run(run.harness_run_id).revision, 2)
        self.assertEqual(self.store.doctor()["events"], 2)

    def test_nested_writable_caller_transaction_doctor_remains_consistent(self) -> None:
        """A per-Run lock remains usable; global Doctor needs stable isolation."""
        run = contract()
        self.store.create_run(run)
        with self.store.connection.transaction():
            self.store.validate_run_history(run.harness_run_id)
            with self.assertRaisesRegex(HarnessRevisionConflict, "stable caller snapshot"):
                self.store.doctor()
            self.assertEqual(self.store.load_run(run.harness_run_id).revision, 1)
        with self.store.connection.transaction():
            self.store.connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
            self.store.validate_run_history(run.harness_run_id)
            doctor = self.store.doctor()
            self.assertTrue(doctor["healthy"])
            self.assertEqual(doctor["runs"], 1)
            self.assertEqual(doctor["events"], 1)

    def test_nested_read_committed_global_doctor_never_certifies_mixed_run_counts(self) -> None:
        """Existing-row locks cannot fence new original Runs in READ COMMITTED."""
        from unittest.mock import patch

        first = contract()
        second = replace(first, harness_run_id="harness-run:global-doctor-phantom",
                         caller_run_ref="caller-run:global-doctor-phantom")
        self.store.create_run(first)
        list_original = self.store.list_runs
        created = False

        def list_before_new_run():
            nonlocal created
            runs = list_original()
            if not created:
                created = True
                with PostgresHarnessStore(self.dsn, schema=self.schema) as rival:
                    rival.create_run(second)
            return runs

        with self.store.connection.transaction():
            with patch.object(self.store, "list_runs", side_effect=list_before_new_run):
                with self.assertRaises(HarnessRevisionConflict):
                    self.store.doctor()
        self.assertFalse(created)
        with self.store.connection.transaction():
            self.store.connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
            with patch.object(self.store, "list_runs", side_effect=list_before_new_run):
                doctor = self.store.doctor()
            self.assertTrue(doctor["healthy"])
            self.assertEqual((doctor["runs"], doctor["events"], doctor["objects"]), (1, 1, 2))
        self.assertTrue(created)
        self.assertEqual(self.store.doctor()["runs"], 2)

    def test_nested_read_uncommitted_is_not_a_stable_global_snapshot(self) -> None:
        run = contract()
        self.store.create_run(run)
        with self.store.connection.transaction():
            self.store.connection.execute("SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED")
            self.store.validate_run_history(run.harness_run_id)
            with self.assertRaisesRegex(HarnessRevisionConflict, "stable caller snapshot"):
                self.store.doctor()
