from __future__ import annotations

from dataclasses import replace
import unittest

from anc_canonical import canonical_digest

from ordivon_harness.core_contracts import HarnessPrivacyPolicy
from ordivon_harness.ordivon.loop import OrdivonAgentLoop
from ordivon_harness.ordivon.model import (
    AgentTurnAdapterError,
    AgentTurnDispatchSafety,
    AgentTurnFailureCode,
    ScriptedTurnAdapter,
)
from ordivon_harness.ordivon.agent_bridge import HarnessAgentBridge
from ordivon_harness.ordivon.run_continuity import EventSourcedRunContinuity
from ordivon_harness.ordivon.runtime_bridge import HarnessRuntimeBridge
from tests.pg_fixture import PgTestSchema, pg_test_schema
from ordivon_harness.standalone import StandaloneHarnessRunner

from tests.test_p0_sqlite_agent_loop import (
    FixedClock,
    budget,
    completed_result,
    contract,
    needs_input_result,
)
from tests.test_p0_sqlite_runtime_bridge import (
    FakeRuntime,
    budget as runtime_budget,
    completed_turn,
    contract as runtime_contract,
    execution_binding,
    tool_turn,
)


MODEL_SENTINEL = "PRIVATE-MODEL-SENTINEL-PC12A"
RESULT_SENTINEL = "PRIVATE-PROVIDER-RESULT-SENTINEL-PC12A"
TOOL_ARGUMENT_SENTINEL = "PRIVATE-TOOL-ARGUMENT-SENTINEL-PC12A"
TOOL_OBSERVATION_SENTINEL = "PRIVATE-TOOL-OBSERVATION-SENTINEL-PC12A"
PROVIDER_ERROR_SENTINEL = "PRIVATE-PROVIDER-ERROR-SENTINEL-PC12A"


def private_contract(suffix: str):
    return replace(
        contract(suffix),
        privacy=HarnessPrivacyPolicy(
            content_policy="bounded-private-content",
            allow_model_content=True,
            allow_tool_content=False,
        ),
    )


class PrivacyAuthorityStateTests(unittest.TestCase):
    @staticmethod
    def run_once(database: PgTestSchema, run_contract, adapter, clock: FixedClock):
        store = database.open(initialize=True)
        store.create_run(run_contract)
        continuity = EventSourcedRunContinuity(store, run_contract, clock_ms=clock)
        bridge = HarnessAgentBridge(run_contract, continuity)
        result = OrdivonAgentLoop(
            adapter,
            bridge,
            budget=budget(),
            clock_ms=clock,
            monotonic_ms=clock,
        ).run(
            harness_run_id=run_contract.harness_run_id,
            assignment_id=continuity.binding.assignment_id,
            context_digest=run_contract.context_refs[0].digest,
            initial_messages=({"role": "user", "content": MODEL_SENTINEL},),
        )
        return store, continuity, result

    def test_pg_logical_row_scanner_detects_actual_persisted_content(self) -> None:
        sentinel = "PG-PRIVACY-TEST-POSITIVE-CONTROL"
        with pg_test_schema() as database:
            with database.connect(initialize=True) as store:
                store.put_object({"content": sentinel}, kind="privacy-test-control")
            self.assertIn(("objects", "content", sentinel), database.persisted_sentinel_hits((sentinel,)))

    def test_metadata_only_provider_state_retains_digest_not_model_content(self) -> None:
        with pg_test_schema() as database:
            clock = FixedClock()
            run_contract = contract("pc12a-metadata-state")
            store, continuity, result = self.run_once(
                database,
                run_contract,
                ScriptedTurnAdapter((completed_result("pc12a-metadata-state"),)),
                clock,
            )
            self.assertTrue(result.candidate_completed)
            retained = continuity.load_current_provider_call()
            self.assertFalse(retained.state.messages_retained)
            self.assertEqual(retained.state.messages, ())
            self.assertEqual(
                retained.state.messages_digest,
                canonical_digest([{"role": "user", "content": MODEL_SENTINEL}]),
            )
            raw = store.get_object(
                retained.state_object.digest,
                expected_kind="harness-run-state",
            )
            self.assertIsInstance(raw, dict)
            assert isinstance(raw, dict)
            self.assertEqual(raw["schemaVersion"], 3)
            self.assertIsNone(raw["messages"])
            self.assertNotIn(MODEL_SENTINEL, str(raw))
            store.close()

    def test_metadata_only_provider_result_retains_digest_not_result_content(self) -> None:
        with pg_test_schema() as database:
            clock = FixedClock()
            run_contract = contract("pc12a-metadata-result")
            provider_result = replace(
                completed_result("pc12a-metadata-result"),
                content=RESULT_SENTINEL,
            )
            store, continuity, execution = self.run_once(
                database,
                run_contract,
                ScriptedTurnAdapter((provider_result,)),
                clock,
            )
            self.assertTrue(execution.candidate_completed)
            self.assertTrue(
                any(message.get("content") == RESULT_SENTINEL for message in execution.messages)
            )
            retained = continuity.load_current_provider_call()
            self.assertEqual(retained.record.to_dict()["schemaVersion"], 4)
            self.assertEqual(retained.record.result_digest, provider_result.digest)
            self.assertIsNone(retained.record.result_object_digest)
            self.assertIsNone(retained.result)
            self.assertIsNone(retained.result_object)
            provider_events = [
                event
                for event in store.list_run_events(run_contract.harness_run_id)
                if event.event_kind.startswith("harness.provider-call-")
            ]
            self.assertTrue(
                all(event.data.get("resultObjectDigest") is None for event in provider_events)
            )
            self.assertNotIn(RESULT_SENTINEL, str([event.data for event in provider_events]))
            store.close()

    def test_metadata_only_full_run_has_no_durable_content_side_channel(self) -> None:
        class SentinelRuntime(FakeRuntime):
            def terminal(self):
                value = super().terminal()
                value["stdoutTail"] = (
                    '{"type":"match","data":{"path":{"text":"src/demo.py"},'
                    f'"lines":{{"text":"{TOOL_OBSERVATION_SENTINEL}\\n"}},'
                    '"line_number":12,"absolute_offset":180,'
                    '"submatches":[{"start":0,"end":4}]}}\n'
                )
                return value

        with pg_test_schema() as database:
            clock = FixedClock()
            runtime = SentinelRuntime()
            run_contract = runtime_contract("pc12a-full-root-scan")
            store = database.open(initialize=True)
            store.create_run(run_contract)
            continuity = EventSourcedRunContinuity(
                store,
                run_contract,
                clock_ms=clock,
            )
            bridge = HarnessRuntimeBridge(
                run_contract,
                continuity,
                execution_binding(run_contract, continuity),
                runtime,
            )
            first = tool_turn("pc12a-full-root-scan")
            selected_call = replace(
                first.tool_calls[0],
                arguments={
                    "query": TOOL_ARGUMENT_SENTINEL,
                    "relativePath": "src",
                    "maxMatches": 20,
                },
            )
            first = replace(first, tool_calls=(selected_call,))
            final = completed_turn("pc12a-full-root-scan")
            assert final.conclusion is not None
            final = replace(
                final,
                content=RESULT_SENTINEL,
                conclusion=replace(final.conclusion, summary=RESULT_SENTINEL),
            )
            execution = StandaloneHarnessRunner(
                run_contract,
                continuity,
                ScriptedTurnAdapter((first, final)),
                bridge,
                budget=runtime_budget(),
                clock_ms=clock,
                monotonic_ms=clock,
            ).run(({"role": "user", "content": MODEL_SENTINEL},))
            self.assertTrue(execution.loop_result.candidate_completed)
            self.assertEqual(execution.loop_result.conclusion.summary, RESULT_SENTINEL)
            self.assertEqual(runtime.workspace_exec_count, 1)
            assert execution.terminal_result is not None
            self.assertIsNone(execution.terminal_result.conclusion)
            self.assertIsNone(execution.terminal_result.completion_proposal)
            self.assertEqual(execution.terminal_result.observations, ())
            self.assertIsNotNone(execution.terminal_result.receipt.conclusion_digest)
            store.close()

            sentinels = (
                MODEL_SENTINEL,
                RESULT_SENTINEL,
                TOOL_ARGUMENT_SENTINEL,
                TOOL_OBSERVATION_SENTINEL,
            )
            self.assertEqual(database.persisted_sentinel_hits(sentinels), [])

    def test_model_only_policy_does_not_persist_tool_projection_channels(self) -> None:
        class SentinelRuntime(FakeRuntime):
            def terminal(self):
                value = super().terminal()
                value["stdoutTail"] = (
                    '{"type":"match","data":{"path":{"text":"src/demo.py"},'
                    f'"lines":{{"text":"{TOOL_OBSERVATION_SENTINEL}\\n"}},'
                    '"line_number":12,"absolute_offset":180,'
                    '"submatches":[{"start":0,"end":4}]}}\n'
                )
                return value

        with pg_test_schema() as database:
            clock = FixedClock()
            runtime = SentinelRuntime()
            run_contract = replace(
                runtime_contract("pc12a-model-only-tool-projection"),
                privacy=HarnessPrivacyPolicy(
                    content_policy="bounded-private-content",
                    allow_model_content=True,
                    allow_tool_content=False,
                ),
            )
            store = database.open(initialize=True)
            store.create_run(run_contract)
            continuity = EventSourcedRunContinuity(
                store,
                run_contract,
                clock_ms=clock,
            )
            bridge = HarnessRuntimeBridge(
                run_contract,
                continuity,
                execution_binding(run_contract, continuity),
                runtime,
            )
            first = tool_turn("pc12a-model-only-tool-projection")
            selected_call = replace(
                first.tool_calls[0],
                arguments={
                    "query": TOOL_ARGUMENT_SENTINEL,
                    "relativePath": "src",
                    "maxMatches": 20,
                },
            )
            first = replace(first, tool_calls=(selected_call,))
            execution = StandaloneHarnessRunner(
                run_contract,
                continuity,
                ScriptedTurnAdapter(
                    (
                        first,
                        completed_turn("pc12a-model-only-tool-projection"),
                    )
                ),
                bridge,
                budget=runtime_budget(),
                clock_ms=clock,
                monotonic_ms=clock,
            ).run(({"role": "user", "content": MODEL_SENTINEL},))
            self.assertTrue(execution.loop_result.candidate_completed)
            self.assertEqual(runtime.workspace_exec_count, 1)
            store.close()

            self.assertEqual(database.persisted_sentinel_hits(
                (TOOL_ARGUMENT_SENTINEL, TOOL_OBSERVATION_SENTINEL)
            ), [])

    def test_metadata_only_provider_failure_redacts_dynamic_detail(self) -> None:
        class ErrorAdapter(ScriptedTurnAdapter):
            def invoke(self, request):
                self.requests.append(request)
                raise AgentTurnAdapterError(
                    PROVIDER_ERROR_SENTINEL,
                    failure_code=AgentTurnFailureCode.TRANSPORT_FAILED,
                    dispatch_safety=AgentTurnDispatchSafety.PRE_DISPATCH_SAFE,
                )

        with pg_test_schema() as database:
            clock = FixedClock()
            run_contract = contract("pc12a-provider-error-redaction")
            adapter = ErrorAdapter((completed_result("unused-provider-error"),))
            store, continuity, execution = self.run_once(
                database,
                run_contract,
                adapter,
                clock,
            )
            self.assertEqual(execution.stop_code.value, "provider_transport_failed")
            retained = continuity.load_current_provider_call()
            assert retained.failure is not None
            self.assertTrue(
                retained.failure.detail.startswith("redacted-provider-detail:sha256:")
            )
            self.assertNotIn(PROVIDER_ERROR_SENTINEL, retained.failure.detail)
            store.close()
            self.assertEqual(database.persisted_sentinel_hits((PROVIDER_ERROR_SENTINEL,)), [])

    def test_private_content_provider_state_retains_exact_model_content(self) -> None:
        with pg_test_schema() as database:
            clock = FixedClock()
            run_contract = private_contract("pc12a-private-state")
            store, continuity, result = self.run_once(
                database,
                run_contract,
                ScriptedTurnAdapter((completed_result("pc12a-private-state"),)),
                clock,
            )
            self.assertTrue(result.candidate_completed)
            retained = continuity.load_current_provider_call()
            self.assertTrue(retained.state.messages_retained)
            self.assertEqual(retained.state.messages[0]["content"], MODEL_SENTINEL)
            store.close()

    def test_metadata_only_pause_is_digest_recoverable_but_not_content_replayable(self) -> None:
        with pg_test_schema() as database:
            clock = FixedClock()
            run_contract = contract("pc12a-redacted-pause")
            store, continuity, paused = self.run_once(
                database,
                run_contract,
                ScriptedTurnAdapter((needs_input_result("pc12a-redacted-pause"),)),
                clock,
            )
            self.assertEqual(paused.stop_code.value, "needs_input")
            retained = continuity.load_current_snapshot()
            self.assertFalse(retained.state.messages_retained)
            self.assertEqual(retained.state.messages, ())
            self.assertEqual(retained.snapshot.messages_digest, retained.state.messages_digest)
            store.close()

            with database.connect() as reopened_store:
                reopened = EventSourcedRunContinuity.open(
                    reopened_store,
                    run_contract.harness_run_id,
                    clock_ms=clock,
                )
                retained = reopened.load_current_snapshot()
                bridge = HarnessAgentBridge(
                    run_contract,
                    reopened,
                    provider_source=reopened.snapshot_provider_source(retained),
                )
                loop = OrdivonAgentLoop(
                    ScriptedTurnAdapter((completed_result("should-not-dispatch"),)),
                    bridge,
                    budget=budget(),
                    clock_ms=clock,
                    monotonic_ms=clock,
                )
                with self.assertRaisesRegex(ValueError, "rehydration"):
                    loop.resume(
                        retained=retained,
                        assignment_id=reopened.binding.assignment_id,
                        context_digest=run_contract.context_refs[0].digest,
                        additional_messages=(
                            {"role": "user", "content": "new answer only"},
                        ),
                    )


if __name__ == "__main__":
    unittest.main()
