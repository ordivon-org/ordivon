"""Read-only Provider token-counter coverage over existing Harness receipts.

The unit cases are hermetic. The PostgreSQL case reuses the original
HarnessAgentRun public create -> run -> open -> resume -> inspect_terminal
flow and is qualified only with an explicitly supplied real test DSN.
"""

from __future__ import annotations

from dataclasses import replace
from itertools import product
from pathlib import Path
import unittest

from anc_canonical import canonical_digest

from ordivon_harness.ordivon.loop import (
    OrdivonAgentLoop,
    _provider_token_counter_coverage,
    _usage_total_tokens,
)
from ordivon_harness.ordivon.control import CancellationToken
from ordivon_harness.ordivon.model import AgentToolCall, ScriptedTurnAdapter
from ordivon_harness.postgres_store import PostgresHarnessStore
from tests.pg_test_support import PostgresAgentRunCase
from tests.test_conclusion_correction_separation import ConclusionGateBridge, budget, turn
from tests.test_r3_supported_agent_run import (
    FakeRuntime,
    FixedClock,
    completed,
    contract,
    digest,
    execution_binding,
    needs_input,
)


class ProviderTokenCounterCoverageTests(unittest.TestCase):
    def test_no_completed_calls_is_not_a_zero_cost_invoice(self) -> None:
        self.assertEqual(
            _provider_token_counter_coverage([]),
            {
                "status": "no_completed_calls",
                "completedCalls": 0,
                "countableCalls": 0,
                "uncountableCalls": 0,
            },
        )

    def test_explicit_zero_is_countable_but_missing_is_not(self) -> None:
        self.assertEqual(
            _provider_token_counter_coverage([{"totalTokens": 0}, {}, {"inputTokens": 2}]),
            {
                "status": "partially_countable",
                "completedCalls": 3,
                "countableCalls": 1,
                "uncountableCalls": 2,
            },
        )

    def test_complete_pair_is_countable_and_subsets_are_not_added(self) -> None:
        usage = {
            "totalTokens": 0,
            "inputTokens": 90,
            "outputTokens": 60,
            "cacheReadTokens": 80,
            "reasoningTokens": 30,
        }
        self.assertEqual(_usage_total_tokens(usage), 150)
        self.assertEqual(
            _provider_token_counter_coverage([usage]),
            {
                "status": "all_countable",
                "completedCalls": 1,
                "countableCalls": 1,
                "uncountableCalls": 0,
            },
        )

    def test_bool_negative_partial_and_nested_only_are_not_reported_zero(self) -> None:
        unusable = [
            {"totalTokens": True},
            {"total_tokens": -1},
            {"inputTokens": 1},
            {"outputTokens": 1},
            {"cacheReadTokens": 11, "reasoningTokens": 3},
            {"usage": {"totalTokens": 15}},
        ]
        self.assertEqual(
            _provider_token_counter_coverage(unusable),
            {
                "status": "none_countable",
                "completedCalls": len(unusable),
                "countableCalls": 0,
                "uncountableCalls": len(unusable),
            },
        )


    def test_async_drain_preserves_known_observation_without_consumption(self) -> None:
        for stop in ("cancelled", "budget_exhausted", "assignment_deadline"):
            for outcome in ("result", "pending", "error"):
                with self.subTest(stop=stop, outcome=outcome):
                    clock = FixedClock()
                    wall = FixedClock()
                    cancellation = CancellationToken(monotonic_ms=clock)
                    returned = turn("drain", "candidate")

                    class Handle:
                        polls = 0
                        cancels = 0

                        def poll(self, timeout_seconds):
                            self.polls += 1
                            if self.polls == 1:
                                if stop == "cancelled":
                                    cancellation.cancel()
                                elif stop == "assignment_deadline":
                                    wall.value += 101
                                else:
                                    clock.value += 10_001
                                return None
                            if stop == "assignment_deadline":
                                wall.value -= 101
                            if outcome == "error":
                                raise RuntimeError("synthetic drain failure")
                            return returned if outcome == "result" else None

                        def cancel(self):
                            self.cancels += 1

                    handle = Handle()

                    class Adapter(ScriptedTurnAdapter):
                        def start_invoke(self, request, control):
                            self.requests.append(request)
                            return handle

                    adapter = Adapter((returned,))
                    bridge = ConclusionGateBridge(set())
                    result = OrdivonAgentLoop(
                        adapter, bridge, budget=budget(conclusion_corrections=0),
                        clock_ms=wall, monotonic_ms=clock,
                        assignment_deadline_ms=1100 if stop == "assignment_deadline" else None,
                    ).run(
                        harness_run_id="harness-run:async-drain",
                        assignment_id="assignment:async-drain",
                        context_digest=canonical_digest({"context": "async-drain"}),
                        initial_messages=({"role": "user", "content": "candidate"},),
                        cancellation=cancellation,
                    )
                    observed = outcome == "result"
                    known_stop = "cancelled" if stop == "cancelled" else "budget_exhausted"
                    expected_stop = known_stop if observed else (
                        "cancel_unknown" if stop == "cancelled" else "provider_state_unknown"
                    )
                    self.assertEqual(result.stop_code.value, expected_stop)
                    self.assertEqual(result.model_calls, int(observed))
                    self.assertEqual(result.usage["totalTokens"], 15 if observed else 0)
                    self.assertEqual(
                        result.usage["tokenCounterCoverage"]["status"],
                        "all_countable" if observed else "no_completed_calls",
                    )
                    self.assertEqual(len(adapter.requests), 1)
                    self.assertEqual((handle.polls, handle.cancels), (2, 1))
                    self.assertIsNone(result.conclusion)
                    self.assertEqual(result.tool_calls, 0)
                    self.assertEqual(bridge.validated, [])
                    kinds = [event.kind for event in result.trace.events]
                    self.assertEqual(kinds.count("model_call_completed"), int(observed))
                    self.assertEqual(kinds[-1], "run_stopped")


class ProviderTokenCounterCoveragePgTests(PostgresAgentRunCase, unittest.TestCase):
    def setUp(self) -> None:
        self.set_up_pg()

    def test_public_pg_pause_resume_terminal_receipt_coverage(self) -> None:
        clock = FixedClock()
        value = contract("token-coverage-r4")
        first_turn = replace(needs_input("model-call:coverage-missing"), usage={})
        first = self.create_pg(
            Path("."),
            value,
            lambda _contract: ScriptedTurnAdapter((first_turn,)),
            clock_ms=clock,
            monotonic_ms=clock,
        )
        paused = first.run(({"role": "user", "content": "start"},))
        self.assertTrue(paused.paused)
        self.assertEqual(paused.loop_result.usage["totalTokens"], 0)
        self.assertEqual(
            paused.loop_result.usage["tokenCounterCoverage"]["status"],
            "none_countable",
        )

        second_turn = replace(
            completed("model-call:coverage-reported"),
            usage={"inputTokens": 2, "outputTokens": 3},
        )
        reopened = self.open_pg(
            Path("."),
            value.harness_run_id,
            lambda _contract: ScriptedTurnAdapter((second_turn,)),
            clock_ms=clock,
            monotonic_ms=clock,
        )
        finished = reopened.resume(additional_messages=({"role": "user", "content": "answer"},))
        self.assertEqual(finished.loop_result.stop_code.value, "candidate_completed")
        coverage = {
            "status": "partially_countable",
            "completedCalls": 2,
            "countableCalls": 1,
            "uncountableCalls": 1,
        }
        self.assertEqual(finished.loop_result.usage["tokenCounterCoverage"], coverage)
        self.assertEqual(finished.loop_result.usage["totalTokens"], 5)
        self.assertEqual(
            [item.get("inputTokens") for item in finished.loop_result.usage["providerUsage"]],
            [None, 2],
        )
        terminal = reopened.inspect_terminal()
        self.assertEqual(terminal.receipt.usage["tokenCounterCoverage"], coverage)
        self.assertEqual(terminal.receipt.usage["totalTokens"], 5)

    def test_terminal_stop_retains_reported_provider_usage(self) -> None:
        for stop in ("cancelled", "budget_exhausted"):
            for async_drain in (False, True):
                with self.subTest(stop=stop, async_drain=async_drain):
                    clock = FixedClock()
                    monotonic = FixedClock()
                    cancellation = CancellationToken(monotonic_ms=monotonic)
                    turn = replace(
                        completed("model-call:coverage-terminal-" + stop),
                        usage={"inputTokens": 10, "outputTokens": 5},
                    )

                    def request_stop():
                        if stop == "cancelled":
                            cancellation.cancel()
                        else:
                            monotonic.value += 10_001

                    class StopOnReturnAdapter(ScriptedTurnAdapter):
                        def invoke(self, request):
                            result = super().invoke(request)
                            request_stop()
                            return result

                    class DrainHandle:
                        polls = 0

                        def poll(self, timeout_seconds):
                            self.polls += 1
                            if self.polls == 1:
                                request_stop()
                                return None
                            return turn

                        def cancel(self):
                            pass

                    class StopOnDrainAdapter(ScriptedTurnAdapter):
                        def start_invoke(self, request, control):
                            self.requests.append(request)
                            return DrainHandle()

                    adapter_class = StopOnDrainAdapter if async_drain else StopOnReturnAdapter
                    adapter = adapter_class((turn,))
                    run = self.create_pg(
                        Path("."), contract(f"coverage-terminal-{stop}-{async_drain}"), lambda _: adapter,
                        clock_ms=clock, monotonic_ms=monotonic,
                    )
                    result = run.run(
                        ({"role": "user", "content": "start"},), cancellation=cancellation
                    ).loop_result
                    self.assertEqual(result.stop_code.value, stop)
                    self.assertIsNone(result.conclusion)
                    self.assertEqual(result.tool_calls, 0)
                    self.assertEqual(len(adapter.requests), 1)
                    self.assertEqual(result.usage["totalTokens"], 15)
                    self.assertEqual(result.model_calls, 1)
                    self.assertEqual(
                        result.usage["tokenCounterCoverage"],
                        {
                            "status": "all_countable",
                            "completedCalls": 1,
                            "countableCalls": 1,
                            "uncountableCalls": 0,
                        },
                    )
                    terminal = run.inspect_terminal()
                    self.assertEqual(terminal.receipt.usage["totalTokens"], 15)
                    self.assertEqual(
                        terminal.receipt.usage["tokenCounterCoverage"],
                        result.usage["tokenCounterCoverage"],
                    )
                    self.assertTrue(run.doctor()["healthy"])

    def test_stopped_return_preserves_privacy_and_no_tool_effect(self) -> None:
        cases = (
            (True, True, False),
            (True, False, False),
            (False, True, False),
            (False, False, False),
            (True, True, True),
        )
        for stop, (allow_model, allow_tool, paused_first), async_drain in product(
            ("cancelled", "budget_exhausted"), cases, (False, True)
        ):
            with self.subTest(
                stop=stop, allow_model=allow_model, allow_tool=allow_tool,
                paused_first=paused_first, async_drain=async_drain,
            ):
                tag = f"k8-privacy-{stop}-{int(allow_model)}{int(allow_tool)}{int(paused_first)}-{int(async_drain)}"
                clock = FixedClock()
                monotonic = FixedClock()
                cancellation = CancellationToken(monotonic_ms=monotonic)
                value = contract(
                    tag, tools=True, allow_model_content=allow_model,
                    allow_tool_content=allow_tool,
                )
                call = AgentToolCall(
                    tool_call_id="tool-call:" + tag, name="search_workspace",
                    arguments={"query": "fixture-only-private-marker"},
                )
                turn = replace(
                    completed("model-call:" + tag),
                    content="fixture-only-model-marker",
                    tool_calls=(call,), conclusion=None, finish_reason="tool_calls",
                    usage={"inputTokens": 10, "outputTokens": 5},
                    raw_response_digest=digest(tag),
                )

                class NoEffectRuntime(FakeRuntime):
                    def __init__(self):
                        self.calls = []

                    def call_tool(self, name, arguments):
                        self.calls.append(name)
                        raise AssertionError("no Runtime effect expected")

                def request_stop():
                    if stop == "cancelled":
                        cancellation.cancel()
                    else:
                        monotonic.value += 10_001

                class StopOnReturnAdapter(ScriptedTurnAdapter):
                    def invoke(self, request):
                        result = super().invoke(request)
                        request_stop()
                        return result

                class DrainHandle:
                    polls = 0

                    def poll(self, timeout_seconds):
                        self.polls += 1
                        if self.polls == 1:
                            request_stop()
                            return None
                        return turn

                    def cancel(self):
                        pass

                class StopOnDrainAdapter(ScriptedTurnAdapter):
                    def start_invoke(self, request, control):
                        self.requests.append(request)
                        return DrainHandle()

                runtime = NoEffectRuntime()
                adapter_class = StopOnDrainAdapter if async_drain else StopOnReturnAdapter
                adapter = adapter_class((turn,))
                kwargs = dict(
                    clock_ms=clock, monotonic_ms=monotonic,
                    execution_binding=execution_binding(value), runtime=runtime,
                )
                if paused_first:
                    initial = self.create_pg(
                        Path("."), value,
                        lambda _: ScriptedTurnAdapter((needs_input("model-call:pause-" + tag),)),
                        **kwargs,
                    )
                    self.assertTrue(initial.run(({"role": "user", "content": "start"},)).paused)
                    run = self.open_pg(
                        Path("."), value.harness_run_id, lambda _: adapter, **kwargs,
                    )
                    result = run.resume(
                        additional_messages=({"role": "user", "content": "continue"},),
                        cancellation=cancellation,
                    ).loop_result
                else:
                    run = self.create_pg(Path("."), value, lambda _: adapter, **kwargs)
                    result = run.run(
                        ({"role": "user", "content": "start"},), cancellation=cancellation,
                    ).loop_result
                terminal = run.inspect_terminal()
                with PostgresHarnessStore(self.pg_dsn, schema=self.pg_schema) as store:
                    store.validate_run_history(value.harness_run_id)
                    events = store.list_run_events(value.harness_run_id)
                provider_events = [
                    event for event in events
                    if event.event_kind == "harness.provider-call-completed"
                ]
                completed_trace = [
                    event for event in terminal.trace.events if event.kind == "model_call_completed"
                ]
                self.assertEqual(result.stop_code.value, stop)
                self.assertIsNone(result.conclusion)
                self.assertEqual(result.tool_calls, 0)
                self.assertEqual(runtime.calls, [])
                self.assertFalse(any(
                    event.kind == "tool_call_proposed" for event in terminal.trace.events
                ))
                self.assertEqual(terminal.receipt.usage["totalTokens"], 15 + 2 * paused_first)
                self.assertEqual(terminal.receipt.usage["modelCalls"], 1 + int(paused_first))
                self.assertEqual(len(provider_events), 1 + int(paused_first))
                self.assertEqual(len(completed_trace), 1 + int(paused_first))
                retained = allow_model and allow_tool
                self.assertEqual(
                    provider_events[-1].data["resultObjectDigest"] is not None, retained,
                )
                self.assertEqual("normalizedResult" in completed_trace[-1].payload, retained)
                self.assertTrue(run.doctor()["healthy"])
