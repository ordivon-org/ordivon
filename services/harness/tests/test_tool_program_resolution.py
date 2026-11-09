"""Pure ToolProgram reference resolution: no Runtime, Provider or external effects."""

from __future__ import annotations

import unittest

from ordivon_harness.agent_tool_observation import HarnessToolObservation
from ordivon_harness.tool_program_contract import observation_ref
from ordivon_harness.tool_program_resolution import _resolve_template


def observed(status: str = "observed") -> HarnessToolObservation:
    return HarnessToolObservation(
        tool_call_id="tool-call:resolution",
        tool_name="read_value",
        status=status,
        structured_content={"rows": [{"value": 7}, {"value": 11}]},
    )


class ToolProgramResolutionTests(unittest.TestCase):
    def test_nested_references_and_literals(self) -> None:
        value = {"items": [observation_ref("read", "rows", 1, "value"), "keep"]}
        self.assertEqual(_resolve_template(value, {"read": observed()}), {"items": [11, "keep"]})
        self.assertEqual(value["items"][1], "keep")

    def test_missing_step_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "already observed prior step"):
            _resolve_template(observation_ref("absent", "rows"), {})

    def test_unobserved_step_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "already observed prior step"):
            _resolve_template(observation_ref("read", "rows"), {"read": observed("unknown")})

    def test_mutable_observation_projection_cannot_redirect_next_tool(self) -> None:
        original = observed()
        original_digest = original.digest
        original.structured_content["rows"][1]["value"] = 999
        self.assertEqual(
            _resolve_template(observation_ref("read", "rows", 1, "value"), {"read": original}),
            11,
        )
        self.assertEqual(original.digest, original_digest)

    def test_bad_path_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "path is unavailable"):
            _resolve_template(observation_ref("read", "rows", 3, "value"), {"read": observed()})


if __name__ == "__main__":
    unittest.main()
