from __future__ import annotations

import json
import unittest

from anc_canonical import canonical_digest

from ordivon_harness.api import DeepSeekSettings, DeepSeekTurnAdapter
from ordivon_harness.ordivon.loop import OrdivonAgentLoop, RunBudget, RunStopCode
from ordivon_harness.ordivon.model import (
    AgentRunConclusion,
    AgentToolDefinition,
    AgentTurnCapabilities,
    AgentTurnRequest,
    AgentTurnResult,
    ScriptedTurnAdapter,
)
from ordivon_harness.tool_program import HarnessToolProgramAction

from tests.test_deepseek_mixed_turn import SequenceTransport, response
from tests.test_p2_tool_program import Bridge, READ, dependent_program


def _program_turn(suffix: str) -> AgentTurnResult:
    action = HarnessToolProgramAction(
        action_call_id=f"program-action:p2-integration:{suffix}",
        program=dependent_program(),
    )
    return AgentTurnResult(
        model_call_id=f"model-call:p2-integration:{suffix}:program",
        model_id=ScriptedTurnAdapter.model_id,
        content="Plan one bounded ToolProgram.",
        tool_calls=(),
        conclusion=None,
        usage={"inputTokens": 10, "outputTokens": 5},
        finish_reason="tool_calls",
        raw_response_digest=canonical_digest(
            {"suffix": suffix, "programAction": action.to_dict()}
        ),
        tool_program_action=action,
    )


def _complete_turn(suffix: str) -> AgentTurnResult:
    return AgentTurnResult(
        model_call_id=f"model-call:p2-integration:{suffix}:complete",
        model_id=ScriptedTurnAdapter.model_id,
        content="complete",
        tool_calls=(),
        conclusion=AgentRunConclusion(
            status="candidate_completed",
            summary="The bounded dependent observations completed.",
        ),
        usage={"inputTokens": 10, "outputTokens": 5},
        finish_reason="stop",
        raw_response_digest=canonical_digest({"suffix": suffix, "complete": True}),
    )


def _budget() -> RunBudget:
    return RunBudget(
        max_model_calls=4,
        max_tool_calls=4,
        max_observation_bytes=262_144,
        max_wall_time_ms=60_000,
        max_total_tokens=100_000,
        max_model_retries=1,
        max_tool_corrections=1,
        max_conclusion_corrections=1,
        max_observation_only_turns=4,
        max_no_progress_turns=3,
    )


class ToolProgramProviderLoopIntegrationTests(unittest.TestCase):
    def test_agent_loop_executes_native_program_then_returns_to_provider(self) -> None:
        bridge = Bridge()
        adapter = ScriptedTurnAdapter(
            (_program_turn("loop"), _complete_turn("loop"))
        )
        result = OrdivonAgentLoop(
            adapter,
            bridge,
            budget=_budget(),
            clock_ms=lambda: 1_000,
            monotonic_ms=lambda: 1_000,
            tool_program_actions=True,
        ).run(
            harness_run_id="harness-run:p2-integration-loop",
            assignment_id="assignment:p2-integration-loop",
            context_digest="sha256:" + "a" * 64,
            initial_messages=({"role": "user", "content": "derive the dependent value"},),
        )
        self.assertEqual(result.stop_code, RunStopCode.CANDIDATE_COMPLETED)
        self.assertEqual(result.model_calls, 2)
        self.assertEqual(result.tool_calls, 2)
        self.assertEqual([call.name for call, _step in bridge.calls], ["read_value", "lookup_value"])
        self.assertEqual(len(adapter.requests), 2)
        self.assertTrue(adapter.requests[0].capabilities.tool_program)
        self.assertIn(
            "Harness ToolProgram result:",
            adapter.requests[1].messages[-1]["content"],
        )

    def test_agent_loop_unknown_program_step_stops_before_second_provider_turn(self) -> None:
        bridge = Bridge(stop_on="lookup_value", stop_status="unknown")
        adapter = ScriptedTurnAdapter(
            (_program_turn("unknown"), _complete_turn("unknown"))
        )
        result = OrdivonAgentLoop(
            adapter,
            bridge,
            budget=_budget(),
            clock_ms=lambda: 1_000,
            monotonic_ms=lambda: 1_000,
            tool_program_actions=True,
        ).run(
            harness_run_id="harness-run:p2-integration-unknown",
            assignment_id="assignment:p2-integration-unknown",
            context_digest="sha256:" + "b" * 64,
            initial_messages=({"role": "user", "content": "derive the dependent value"},),
        )
        self.assertEqual(result.stop_code, RunStopCode.RUNTIME_UNKNOWN)
        self.assertEqual(result.model_calls, 1)
        self.assertEqual(len(adapter.requests), 1)
        self.assertEqual([call.name for call, _step in bridge.calls], ["read_value", "lookup_value"])

    def test_deepseek_tool_program_control_is_exposed_and_decoded_only_when_admitted(self) -> None:
        tool = AgentToolDefinition(
            name="observe_fact",
            description="Observe one bounded fact.",
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {"key": {"type": "string"}},
                "required": ["key"],
            },
        )
        program_arguments = {
            "steps": [
                {
                    "step_id": "observe",
                    "tool_name": "observe_fact",
                    "arguments": {"key": "x"},
                }
            ],
            "outputs": {
                "value": {
                    "$harnessObservationRef": {
                        "stepId": "observe",
                        "path": ["value"],
                    }
                }
            },
        }
        provider_response = response(
            ("program-call:deepseek", "compose_tool_program", program_arguments)
        )
        transport = SequenceTransport([provider_response])
        adapter = DeepSeekTurnAdapter(
            DeepSeekSettings(api_key="k" * 40, max_output_tokens=512),
            transport=transport,
        )
        request = AgentTurnRequest(
            harness_run_id="harness-run:p2-deepseek-control",
            turn_id="turn:p2-deepseek-control:1",
            sequence=1,
            assignment_id="assignment:p2-deepseek-control",
            context_digest="sha256:" + "c" * 64,
            tool_catalog_digest="sha256:" + "d" * 64,
            messages=({"role": "user", "content": "compose the dependent observation"},),
            tools=(tool,),
            capabilities=AgentTurnCapabilities(tool_program=True),
            remaining_budget={"modelCalls": 2, "toolCalls": 1, "totalTokens": 4096},
        )
        result = adapter.invoke(request)
        assert result.tool_program_action is not None
        self.assertEqual(result.tool_program_action.action_call_id, "program-call:deepseek")
        self.assertEqual(result.tool_program_action.program.steps[0].tool_name, "observe_fact")
        body = transport.requests[0]
        tools = body["tools"]
        names = [item["function"]["name"] for item in tools]
        self.assertIn("compose_tool_program", names)
        program_schema = next(
            item["function"]["parameters"]
            for item in tools
            if item["function"]["name"] == "compose_tool_program"
        )
        self.assertEqual(
            program_schema["properties"]["steps"]["items"]["properties"]["tool_name"]["enum"],
            ["observe_fact"],
        )

        disabled = DeepSeekTurnAdapter(
            DeepSeekSettings(api_key="k" * 40, max_output_tokens=512),
            transport=SequenceTransport([provider_response]),
        )
        with self.assertRaisesRegex(ValueError, "unavailable ToolProgram control"):
            disabled.invoke(
                AgentTurnRequest(
                    harness_run_id=request.harness_run_id,
                    turn_id=request.turn_id,
                    sequence=request.sequence,
                    assignment_id=request.assignment_id,
                    context_digest=request.context_digest,
                    tool_catalog_digest=request.tool_catalog_digest,
                    messages=request.messages,
                    tools=request.tools,
                    remaining_budget=request.remaining_budget,
                )
            )

    def test_deepseek_reprojects_retained_program_action_and_compact_result(self) -> None:
        action = _program_turn("history").tool_program_action
        assert action is not None
        adapter = DeepSeekTurnAdapter(
            DeepSeekSettings(api_key="k" * 40, max_output_tokens=512)
        )
        request = AgentTurnRequest(
            harness_run_id="harness-run:p2-deepseek-history",
            turn_id="turn:p2-deepseek-history:2",
            sequence=2,
            assignment_id="assignment:p2-deepseek-history",
            context_digest="sha256:" + "e" * 64,
            tool_catalog_digest="sha256:" + "f" * 64,
            messages=(
                {
                    "role": "assistant",
                    "content": "planned bounded program",
                    "toolProgramAction": action.to_dict(),
                },
                {
                    "role": "user",
                    "content": "Harness ToolProgram result: {\"status\":\"completed\"}",
                },
            ),
            tools=(READ,),
            remaining_budget={"modelCalls": 1, "toolCalls": 0, "totalTokens": 2048},
        )
        _allowed, _digest, _headers, body = adapter._prepare_request(request)
        payload = json.loads(body)
        self.assertIn(
            "Retained Harness ToolProgram action:", payload["messages"][1]["content"]
        )
        self.assertIn(
            "Harness ToolProgram result:", payload["messages"][2]["content"]
        )


if __name__ == "__main__":
    unittest.main()
