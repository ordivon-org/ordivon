from __future__ import annotations

import hashlib
import json
import unittest

from anc_canonical import canonical_bytes

from ordivon_harness.api import DeepSeekSettings, DeepSeekTurnAdapter, RunBudget
from ordivon_harness.ordivon.model import AgentToolCall
from ordivon_harness.domain_tools import (
    AgentToolDefinition,
    DomainToolCatalog,
    DomainToolLoopPlan,
    DomainToolLoopRunner,
    HarnessToolObservation,
)


TOOL = AgentToolDefinition(
    name="observe_fact",
    description="Observe one harmless test fact.",
    input_schema={
        "type": "object",
        "additionalProperties": False,
        "properties": {"key": {"type": "string"}},
        "required": ["key"],
    },
)
COMPLETION = {
    "mode": "structured-result-v1",
    "resultKind": "mixed-turn-test",
    "resultSchema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {"answer": {"type": "string"}},
        "required": ["answer"],
    },
}


class SequenceTransport:
    def __init__(self, responses: list[bytes]) -> None:
        self.responses = list(responses)
        self.requests: list[dict[str, object]] = []

    def post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes,
        timeout_seconds: float,
        max_response_bytes: int,
    ) -> bytes:
        self.requests.append(json.loads(body))
        if not self.responses:
            raise AssertionError("unexpected Provider call")
        return self.responses.pop(0)


class CountingBridge:
    catalog = DomainToolCatalog(
        domain_id="domain:mixed-turn-test",
        revision="mixed-turn-test-v1",
        tools=(TOOL,),
    )
    bridge_identity = {
        "schemaVersion": 1,
        "kind": "mixed-turn-counting-bridge",
    }

    def __init__(self) -> None:
        self.executions = 0

    def execute(self, call: AgentToolCall, *, step_id: str) -> HarnessToolObservation:
        self.executions += 1
        return HarnessToolObservation(
            call.tool_call_id, call.name, "observed", {"value": "physical-observation"}
        )


def response(*calls: tuple[str, str, dict[str, object]]) -> bytes:
    return canonical_bytes(
        {
            "id": "provider-call:" + hashlib.sha256(repr(calls).encode()).hexdigest()[:12],
            "model": "deepseek-v4-flash",
            "choices": [
                {
                    "finish_reason": "tool_calls",
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": call_id,
                                "type": "function",
                                "function": {
                                    "name": name,
                                    "arguments": json.dumps(arguments, separators=(",", ":")),
                                },
                            }
                            for call_id, name, arguments in calls
                        ],
                    },
                }
            ],
            "usage": {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30},
        }
    )


class DeepSeekMixedTurnTests(unittest.TestCase):
    def test_default_request_model_is_current_canonical_but_legacy_remains_explicit(self) -> None:
        current = DeepSeekSettings(api_key="k" * 40)
        self.assertEqual(current.model, "deepseek-flash")
        legacy = DeepSeekSettings(api_key="k" * 40, model="deepseek-v4-flash")
        self.assertEqual(legacy.model, "deepseek-v4-flash")

    def test_control_is_rechecked_after_request_preparation(self) -> None:
        from unittest.mock import patch
        from ordivon_harness.api import AgentTurnRequest
        from ordivon_harness.ordivon.control import (
            CancellationToken, ExecutionControl, RunDeadline,
        )
        from ordivon_harness.ordivon.model import (
            AgentTurnAdapterError, AgentTurnDispatchSafety, AgentTurnFailureCode,
        )

        request = AgentTurnRequest(
            harness_run_id="harness-run:prepare-stop",
            turn_id="turn:prepare-stop:1",
            sequence=1,
            assignment_id="assignment:prepare-stop",
            context_digest="sha256:" + "a" * 64,
            tool_catalog_digest="sha256:" + "b" * 64,
            messages=({"role": "user", "content": "test"},),
            tools=(TOOL,),
            remaining_budget={"modelCalls": 2, "toolCalls": 1, "totalTokens": 4096},
        )
        raw = response(("call:observe", "observe_fact", {"key": "x"}))

        class RecordingTransport(SequenceTransport):
            def __init__(self):
                super().__init__([raw])
                self.timeouts = []

            def post(self, url, **kwargs):
                self.timeouts.append(kwargs["timeout_seconds"])
                return super().post(url, **kwargs)

        class RecordingHandleTransport(RecordingTransport):
            def start_post(self, url, **kwargs):
                result = self.post(url, **kwargs)

                class Handle:
                    def poll(self, timeout_seconds):
                        return result

                    def cancel(self):
                        pass

                return Handle()

        for use_handle in (False, True):
            for outcome in ("normal", "shortened", "cancelled", "deadline"):
                with self.subTest(use_handle=use_handle, outcome=outcome):
                    transport = (
                        RecordingHandleTransport() if use_handle else RecordingTransport()
                    )
                    adapter = DeepSeekTurnAdapter(
                        DeepSeekSettings(api_key="k" * 40, max_output_tokens=512),
                        transport=transport,
                    )
                    now = [1000]
                    def clock():
                        return now[0]

                    cancellation = CancellationToken(monotonic_ms=clock)
                    control = ExecutionControl(
                        cancellation, RunDeadline(expires_at_ms=11_000, monotonic_ms=clock),
                    )
                    prepare = adapter._prepare_request

                    def prepare_then_change_control(value):
                        result = prepare(value)
                        if outcome == "cancelled":
                            cancellation.cancel()
                        elif outcome == "deadline":
                            now[0] = 11_000
                        elif outcome == "shortened":
                            now[0] = 9000
                        return result

                    with patch.object(
                        adapter, "_prepare_request", side_effect=prepare_then_change_control
                    ) as prepared:
                        if outcome in ("cancelled", "deadline"):
                            with self.assertRaises(AgentTurnAdapterError) as caught:
                                adapter.invoke_with_control(request, control)
                            self.assertEqual(
                                caught.exception.dispatch_safety,
                                AgentTurnDispatchSafety.PRE_DISPATCH_SAFE,
                            )
                            self.assertEqual(
                                caught.exception.failure_code, AgentTurnFailureCode.TIMEOUT,
                            )
                            self.assertEqual(transport.requests, [])
                            self.assertEqual(transport.timeouts, [])
                        else:
                            result = adapter.invoke_with_control(request, control)
                            self.assertEqual(len(result.tool_calls), 1)
                            self.assertEqual(len(transport.requests), 1)
                            self.assertEqual(
                                transport.timeouts, [2.0 if outcome == "shortened" else 10.0]
                            )
                        self.assertEqual(prepared.call_count, 1)

    def test_adapter_marks_mixed_tool_and_conclusion_as_model_correctable(self) -> None:
        mixed = response(
            ("call:observe", "observe_fact", {"key": "x"}),
            (
                "call:conclude",
                "submit_run_conclusion",
                {
                    "status": "candidate_completed",
                    "result": {"answer": "premature"},
                    "artifact_refs": [],
                    "evidence_refs": [],
                    "unresolved_unknowns": [],
                },
            ),
        )
        transport = SequenceTransport([mixed])
        adapter = DeepSeekTurnAdapter(
            DeepSeekSettings(api_key="k" * 40, max_output_tokens=512),
            transport=transport,
            completion_contract=COMPLETION,
        )
        from ordivon_harness.api import AgentTurnRequest

        result = adapter.invoke(
            AgentTurnRequest(
                harness_run_id="harness-run:mixed-adapter",
                turn_id="turn:mixed-adapter:1",
                sequence=1,
                assignment_id="assignment:mixed-adapter",
                context_digest="sha256:" + "a" * 64,
                tool_catalog_digest="sha256:" + "b" * 64,
                messages=({"role": "user", "content": "test"},),
                tools=(TOOL,),
                remaining_budget={"modelCalls": 2, "toolCalls": 1, "totalTokens": 4096},
            )
        )
        self.assertIsNone(result.conclusion)
        self.assertEqual(len(result.tool_calls), 1)
        self.assertEqual(result.tool_calls[0].name, "observe_fact")
        self.assertEqual(result.tool_calls[0].argument_error, "mixed_with_conclusion")

    def test_loop_corrects_mixed_turn_without_executing_physical_tool(self) -> None:
        mixed = response(
            ("call:observe", "observe_fact", {"key": "x"}),
            (
                "call:conclude",
                "submit_run_conclusion",
                {
                    "status": "candidate_completed",
                    "result": {"answer": "premature"},
                    "artifact_refs": [],
                    "evidence_refs": [],
                    "unresolved_unknowns": [],
                },
            ),
        )
        corrected = response(
            (
                "call:conclude:corrected",
                "submit_run_conclusion",
                {
                    "status": "candidate_completed",
                    "result": {"answer": "corrected"},
                    "artifact_refs": [],
                    "evidence_refs": [],
                    "unresolved_unknowns": [],
                },
            )
        )
        transport = SequenceTransport([mixed, corrected])
        adapter = DeepSeekTurnAdapter(
            DeepSeekSettings(api_key="k" * 40, max_output_tokens=512),
            transport=transport,
            completion_contract=COMPLETION,
        )
        bridge = CountingBridge()
        result = DomainToolLoopRunner(adapter, bridge).run(
            DomainToolLoopPlan(
                harness_run_id="harness-run:mixed-loop",
                assignment_id="assignment:mixed-loop",
                context_digest="sha256:" + "c" * 64,
                initial_messages=({"role": "user", "content": "choose one action"},),
                allowed_tools=("observe_fact",),
                budget=RunBudget(
                    max_model_calls=3,
                    max_tool_calls=2,
                    max_observation_bytes=32768,
                    max_wall_time_ms=30000,
                    max_total_tokens=8192,
                    max_tool_corrections=2,
                ),
            )
        )
        self.assertEqual(result.stop_code.value, "candidate_completed")
        self.assertEqual(bridge.executions, 0)
        self.assertEqual(result.tool_calls, 1)
        self.assertEqual(result.observations[0].status, "rejected")
        error = result.observations[0].structured_content["error"]
        self.assertEqual(error["kind"], "model_correctable")
        self.assertTrue(error["safeToCorrect"])
        self.assertIsNotNone(result.conclusion)
        assert result.conclusion is not None
        assert result.conclusion.structured_result is not None
        self.assertEqual(
            result.conclusion.structured_result.value,
            {"answer": "corrected"},
        )
        self.assertTrue(result.conclusion.summary.startswith("Structured result sha256:"))
        self.assertEqual(len(transport.requests), 2)

    def test_standard_schema_dialect_is_local_annotation_not_provider_parameter(self) -> None:
        from ordivon_harness.api import AgentTurnRequest
        from ordivon_harness.structured_result_conformance import (
            JSON_SCHEMA_DRAFT_2020_12_URI,
        )

        completion = {
            "mode": "structured-result-v1",
            "resultKind": "standard-dialect-provider-boundary",
            "resultSchema": {
                "$schema": JSON_SCHEMA_DRAFT_2020_12_URI,
                "type": "object",
                "additionalProperties": False,
                "properties": {"answer": {"type": "string"}},
                "required": ["answer"],
            },
        }
        transport = SequenceTransport(
            [
                response(
                    (
                        "call:standard-dialect",
                        "submit_run_conclusion",
                        {
                            "status": "candidate_completed",
                            "result": {"answer": "ok"},
                            "artifact_refs": [],
                            "evidence_refs": [],
                            "unresolved_unknowns": [],
                        },
                    )
                )
            ]
        )
        adapter = DeepSeekTurnAdapter(
            DeepSeekSettings(api_key="k" * 40, max_output_tokens=512),
            transport=transport,
            completion_contract=completion,
        )
        result = adapter.invoke(
            AgentTurnRequest(
                harness_run_id="harness-run:standard-dialect-provider-boundary",
                turn_id="turn:standard-dialect-provider-boundary:1",
                sequence=1,
                assignment_id="assignment:standard-dialect-provider-boundary",
                context_digest="sha256:" + "d" * 64,
                tool_catalog_digest="sha256:" + "e" * 64,
                messages=({"role": "user", "content": "return the structured result"},),
                tools=(),
                remaining_budget={"modelCalls": 1, "toolCalls": 0, "totalTokens": 4096},
            )
        )
        self.assertIsNotNone(result.conclusion)
        request = transport.requests[0]
        conclusion_tool = next(
            tool
            for tool in request["tools"]
            if tool["function"]["name"] == "submit_run_conclusion"
        )
        provider_result_schema = conclusion_tool["function"]["parameters"]["properties"]["result"]
        self.assertNotIn("$schema", provider_result_schema)
        self.assertEqual(provider_result_schema["type"], "object")
        self.assertEqual(provider_result_schema["required"], ["answer"])


if __name__ == "__main__":
    unittest.main()
