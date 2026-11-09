"""Bounded ToolProgram model-to-Python trace refinement.

This deliberately keeps the real HarnessToolProgramExecutor in the test. It
checks its observable ToolBridge trace and result against ToolProgramSafetyR1,
rather than checking a separate reimplementation of the production loop.
The finite three-step domain is NOT a universal implementation proof.
"""

from __future__ import annotations

from itertools import product
import unittest

from ordivon_harness.agent_tool_observation import HarnessToolObservation
from ordivon_harness.ordivon.model import AgentToolCall, AgentToolDefinition
from ordivon_harness.tool_program import (
    HarnessToolProgram,
    HarnessToolProgramExecutor,
    HarnessToolProgramStep,
)


READ = AgentToolDefinition(
    "read_value",
    "Read one value.",
    {
        "type": "object",
        "additionalProperties": False,
        "properties": {"key": {"type": "string"}},
        "required": ["key"],
    },
)

OUTCOMES = ("observed", "rejected", "unknown", "cancel-requested", "cancelled")


def _three_steps() -> HarnessToolProgram:
    return HarnessToolProgram(
        steps=tuple(
            HarnessToolProgramStep(
                step_id=f"step-{i}",
                tool_name="read_value",
                arguments={"key": f"k{i}"},
            )
            for i in range(3)
        ),
        outputs={},
    )


class _SequenceBridge:
    def __init__(self, outcomes: tuple[str, ...]) -> None:
        self.outcomes = outcomes
        self.calls: list[AgentToolCall] = []

    def execute(self, call: AgentToolCall, *, step_id: str) -> HarnessToolObservation:
        index = len(self.calls)
        self.calls.append(call)
        return HarnessToolObservation(
            tool_call_id=call.tool_call_id,
            tool_name=call.name,
            status=self.outcomes[index],
            structured_content={"step": index, "stepId": step_id},
        )


class ToolProgramModelRefinementTests(unittest.TestCase):
    def test_bounded_three_step_model_trace_refines_actual_executor(self) -> None:
        program = _three_steps()
        checked = 0
        for admitted, budget, outcomes in product(
            (False, True), range(4), product(OUTCOMES, repeat=3)
        ):
            bridge = _SequenceBridge(outcomes)
            executor = HarnessToolProgramExecutor(
                bridge, (READ,) if admitted else ()
            )
            if not admitted or budget < 3:
                with self.assertRaises(ValueError):
                    executor.execute(program, remaining_tool_calls=budget, step_prefix="formal")
                self.assertEqual(bridge.calls, [])
            else:
                result = executor.execute(
                    program, remaining_tool_calls=budget, step_prefix="formal"
                )
                first_unobserved = next(
                    (i for i, status in enumerate(outcomes) if status != "observed"), 3
                )
                expected_issued = min(3, first_unobserved + 1)
                self.assertEqual(len(bridge.calls), expected_issued)
                self.assertEqual(len(result.observations), expected_issued)
                self.assertEqual(
                    result.status,
                    "completed" if first_unobserved == 3 else outcomes[first_unobserved],
                )
                self.assertEqual(
                    [x.status for x in result.observations],
                    list(outcomes[:expected_issued]),
                )
                self.assertEqual(
                    result.output,
                    {},
                    "No model-terminal output is produced by a partial ToolProgram",
                )
                self.assertLessEqual(expected_issued, budget)
            checked += 1
        self.assertEqual(checked, 1000)


if __name__ == "__main__":
    unittest.main()
