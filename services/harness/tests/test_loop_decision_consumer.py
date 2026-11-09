"""Real OrdivonAgentLoop consumer witnesses for pure decision operators.

An in-memory scripted Provider and no-effect Tool surface make these tests
native Harness implementation traces; no SQLite or external Job is involved.
"""
from __future__ import annotations

import unittest
from unittest.mock import patch

from anc_canonical import canonical_digest
from ordivon_harness.ordivon.control import RunDeadline
from ordivon_harness.ordivon.loop import OrdivonAgentLoop, RunBudget, RunStopCode
from ordivon_harness.ordivon.model import (
    AgentRunConclusion,
    AgentTurnAdapterError,
    AgentTurnDispatchSafety,
    AgentTurnFailureCode,
    AgentTurnResult,
    ScriptedTurnAdapter,
    static_provider_request_digest,
)


class NoEffectBridge:
    catalog_digest = canonical_digest({"toolSurface": "no-effect"})

    def definitions(self):
        return ()

    def execute(self, call, *, step_id: str):
        raise AssertionError("No physical Tool dispatch expected")


def _budget() -> RunBudget:
    return RunBudget(
        max_model_calls=3,
        max_tool_calls=0,
        max_observation_bytes=16_384,
        max_wall_time_ms=2_000,
        max_total_tokens=10_000,
        max_model_retries=1,
        max_tool_corrections=0,
        max_conclusion_corrections=0,
    )


def _result() -> AgentTurnResult:
    return AgentTurnResult(
        model_call_id="model-call:loop-decisions",
        model_id=ScriptedTurnAdapter.model_id,
        content="done",
        tool_calls=(),
        conclusion=AgentRunConclusion(status="candidate_completed", summary="done"),
        usage={"inputTokens": 3, "outputTokens": 4},
        finish_reason="stop",
        raw_response_digest=canonical_digest({"trace": "loop-decisions"}),
    )


def _run(adapter, *, assignment_deadline_ms=None, external_expiry_ms=None):
    def clock() -> int:
        return 100
    loop = OrdivonAgentLoop(
        adapter,
        NoEffectBridge(),
        budget=_budget(),
        clock_ms=clock,
        monotonic_ms=clock,
        assignment_deadline_ms=assignment_deadline_ms,
    )
    deadline = None if external_expiry_ms is None else RunDeadline(external_expiry_ms, clock)
    return loop.run(
        harness_run_id="harness-run:loop-decisions",
        assignment_id="assignment:loop-decisions",
        context_digest=canonical_digest({"context": "loop-decisions"}),
        initial_messages=({"role": "user", "content": "complete"},),
        deadline=deadline,
    )


class FailOnceAdapter:
    adapter_id = ScriptedTurnAdapter.adapter_id
    model_id = ScriptedTurnAdapter.model_id
    provider_request_digest = staticmethod(static_provider_request_digest)

    def __init__(self, safety):
        self.safety = safety
        self.calls = 0

    def invoke(self, request):
        self.calls += 1
        if self.calls == 1:
            raise AgentTurnAdapterError(
                "synthetic provider transport failure",
                failure_code=AgentTurnFailureCode.TRANSPORT_FAILED,
                dispatch_safety=self.safety,
            )
        return _result()


class LoopDecisionConsumerTests(unittest.TestCase):
    def test_assignment_expiry_rejects_provider_dispatch(self):
        adapter = ScriptedTurnAdapter((_result(),))
        result = _run(adapter, assignment_deadline_ms=100)
        self.assertEqual(result.stop_code, RunStopCode.BUDGET_EXHAUSTED)
        self.assertEqual(adapter.requests, [])
        started = next(event for event in result.trace.events if event.kind == "run_started")
        self.assertEqual(started.payload["deadlineSource"], "assignment_deadline")
        self.assertEqual(started.payload["assignmentRemainingMs"], 0)

    def test_external_deadline_wins_earlier_expiry(self):
        adapter = ScriptedTurnAdapter((_result(),))
        result = _run(adapter, assignment_deadline_ms=900, external_expiry_ms=125)
        self.assertEqual(result.stop_code, RunStopCode.CANDIDATE_COMPLETED)
        self.assertEqual(len(adapter.requests), 1)
        started = next(event for event in result.trace.events if event.kind == "run_started")
        self.assertEqual(started.payload["deadlineSource"], "external_deadline")
        self.assertEqual(started.payload["deadlineMonotonicMs"], 125)

    def test_pre_dispatch_safe_error_retries_once(self):
        adapter = FailOnceAdapter(AgentTurnDispatchSafety.PRE_DISPATCH_SAFE)
        with patch("ordivon_harness.ordivon.loop.time.sleep", return_value=None):
            result = _run(adapter)
        self.assertEqual(result.stop_code, RunStopCode.CANDIDATE_COMPLETED)
        self.assertEqual(adapter.calls, 2)
        self.assertEqual(result.usage["modelRetries"], 1)

    def test_ambiguous_provider_effect_is_not_redispatched(self):
        adapter = FailOnceAdapter(AgentTurnDispatchSafety.DISPATCH_AMBIGUOUS)
        result = _run(adapter)
        self.assertEqual(result.stop_code, RunStopCode.PROVIDER_STATE_UNKNOWN)
        self.assertEqual(adapter.calls, 1)
        self.assertEqual(result.usage["modelRetries"], 0)


if __name__ == "__main__":
    unittest.main()
