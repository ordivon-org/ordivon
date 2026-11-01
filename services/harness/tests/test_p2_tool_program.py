from __future__ import annotations

import subprocess
import sys
import unittest
from unittest.mock import patch

from anc_canonical import canonical_digest

from ordivon_harness.agent_tool_observation import HarnessToolObservation
from ordivon_harness.ordivon.model import AgentToolCall, AgentToolDefinition, AgentTurnResult
from ordivon_harness.tool_program import (
    HarnessToolProgram,
    HarnessToolProgramAction,
    HarnessToolProgramExecutor,
    HarnessToolProgramResult,
    HarnessToolProgramStep,
    observation_ref,
    project_tool_program_action_capability,
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
LOOKUP = AgentToolDefinition(
    "lookup_value",
    "Lookup a value by an exact query.",
    {
        "type": "object",
        "additionalProperties": False,
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    },
)
WRITE = AgentToolDefinition(
    "write_value",
    "Mutate one value.",
    {
        "type": "object",
        "additionalProperties": False,
        "properties": {"value": {"type": "string"}},
        "required": ["value"],
    },
)


class Bridge:
    catalog_digest = canonical_digest({"tools": ["read_value", "lookup_value", "write_value"]})

    def __init__(self, *, stop_on: str | None = None, stop_status: str = "unknown") -> None:
        self.calls: list[tuple[AgentToolCall, str]] = []
        self.stop_on = stop_on
        self.stop_status = stop_status

    def definitions(self):
        return (READ, LOOKUP, WRITE)

    def execute(self, call: AgentToolCall, *, step_id: str) -> HarnessToolObservation:
        self.calls.append((call, step_id))
        if call.name == self.stop_on:
            return HarnessToolObservation(
                tool_call_id=call.tool_call_id,
                tool_name=call.name,
                status=self.stop_status,
                structured_content={"terminal": self.stop_status},
            )
        if call.name == "read_value":
            content = {"value": "needle", "digest": "sha256:" + "a" * 64}
        elif call.name == "lookup_value":
            content = {"query": call.arguments["query"], "matches": ["m1", "m2"]}
        elif call.name == "write_value":
            content = {"written": call.arguments["value"]}
        else:
            raise AssertionError(call.name)
        return HarnessToolObservation(
            tool_call_id=call.tool_call_id,
            tool_name=call.name,
            status="observed",
            structured_content=content,
        )


def dependent_program() -> HarnessToolProgram:
    return HarnessToolProgram(
        steps=(
            HarnessToolProgramStep("read", "read_value", {"key": "source"}),
            HarnessToolProgramStep(
                "lookup",
                "lookup_value",
                {"query": observation_ref("read", "value")},
            ),
        ),
        outputs={
            "query": observation_ref("lookup", "query"),
            "matches": observation_ref("lookup", "matches"),
            "sourceDigest": observation_ref("read", "digest"),
        },
    )


class ToolProgramP2Tests(unittest.TestCase):
    def test_fresh_model_import_does_not_load_tool_executor(self) -> None:
        """Verify the real import boundary from a fresh Python process."""
        code = (
            "import sys\n"
            "from ordivon_harness.ordivon.model import AgentTurnResult\n"
            "assert 'ordivon_harness.tool_program' not in sys.modules\n"
            "from ordivon_harness.tool_program_contract import HarnessToolProgramAction\n"
            "assert 'ordivon_harness.tool_program' not in sys.modules\n"
            "assert AgentTurnResult.__annotations__['tool_program_action'] == "
            "'HarnessToolProgramAction | None'\n"
        )
        subprocess.run(
            [sys.executable, "-c", code],
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        )

    def test_action_wire_contract_does_not_require_executor_import(self) -> None:
        """The model consumes the pure contract, not the Tool executor module."""
        from ordivon_harness.tool_program_contract import HarnessToolProgramAction as ContractAction

        self.assertIs(HarnessToolProgramAction, ContractAction)
        action = HarnessToolProgramAction(
            action_call_id="program-action:p2:contract-boundary",
            program=dependent_program(),
        )
        turn = AgentTurnResult(
            model_call_id="model-call:p2:contract-boundary",
            model_id="test-model",
            content=None,
            tool_calls=(),
            conclusion=None,
            usage={},
            finish_reason="tool_calls",
            raw_response_digest="sha256:" + "f" * 64,
            tool_program_action=action,
        )
        # Fail if a future refactor makes the domain model import the executor.
        # Production callers still use the pre-existing public tool_program path.
        with patch.dict(sys.modules, {"ordivon_harness.tool_program": None}):
            encoded = turn.to_dict()
            decoded = AgentTurnResult.from_dict(encoded)
        self.assertEqual(decoded, turn)
        self.assertEqual(decoded.digest, turn.digest)

    def test_round_trip_digest_and_prior_observation_dataflow_are_deterministic(self) -> None:
        program = dependent_program()
        self.assertEqual(HarnessToolProgram.from_dict(program.to_dict()), program)
        self.assertEqual(program.digest, HarnessToolProgram.from_dict(program.to_dict()).digest)

        bridge = Bridge()
        result = HarnessToolProgramExecutor(bridge, (READ, LOOKUP)).execute(
            program,
            remaining_tool_calls=2,
            step_prefix="turn-p2",
        )
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.output["query"], "needle")
        self.assertEqual(result.output["matches"], ["m1", "m2"])
        self.assertEqual(bridge.calls[1][0].arguments, {"query": "needle"})
        self.assertTrue(bridge.calls[0][0].tool_call_id.startswith("tool-call:program:"))
        self.assertNotEqual(bridge.calls[0][0].tool_call_id, bridge.calls[1][0].tool_call_id)

    def test_program_execution_uses_one_validated_snapshot_across_effects(self) -> None:
        program = HarnessToolProgram(
            steps=(
                HarnessToolProgramStep("read", "read_value", {"key": "source"}),
                HarnessToolProgramStep("write", "write_value", {"value": "authorized"}),
            ),
            outputs={"written": observation_ref("write", "written")},
        )
        initial_digest = program.digest

        class MutatingBridge(Bridge):
            def execute(self, call: AgentToolCall, *, step_id: str) -> HarnessToolObservation:
                observation = super().execute(call, step_id=step_id)
                if call.name == "read_value":
                    # Adversarial callback mutates caller-owned JSON while
                    # an already-validated program is mid-execution.
                    program.steps[1].arguments["value"] = "tampered"
                    program.outputs["invalid"] = observation_ref("missing", "written")
                return observation

        bridge = MutatingBridge()
        result = HarnessToolProgramExecutor(bridge, (READ, WRITE)).execute(
            program, remaining_tool_calls=2, step_prefix="snapshot"
        )
        self.assertEqual(result.status, "completed")
        self.assertEqual(bridge.calls[-1][0].arguments["value"], "authorized")
        self.assertEqual(result.output, {"written": "authorized"})
        self.assertEqual(result.program_digest, initial_digest)

    def test_invalid_mutation_before_execution_cannot_emit_tool_effect(self) -> None:
        program = HarnessToolProgram(
            steps=(HarnessToolProgramStep("write", "write_value", {"value": "protected"}),),
            outputs={},
        )
        program.outputs["unsafe"] = observation_ref("missing", "written")
        bridge = Bridge()
        with self.assertRaisesRegex(ValueError, "unknown step"):
            HarnessToolProgramExecutor(bridge, (WRITE,)).execute(
                program, remaining_tool_calls=1, step_prefix="reject-before-effect"
            )
        self.assertEqual(bridge.calls, [])

    def test_program_cannot_reference_future_or_unknown_observation(self) -> None:
        with self.assertRaisesRegex(ValueError, "already completed prior step"):
            HarnessToolProgram(
                steps=(
                    HarnessToolProgramStep(
                        "first",
                        "lookup_value",
                        {"query": observation_ref("later", "value")},
                    ),
                    HarnessToolProgramStep("later", "read_value", {"key": "x"}),
                ),
                outputs={},
            )
        with self.assertRaisesRegex(ValueError, "unknown step"):
            HarnessToolProgram(
                steps=(HarnessToolProgramStep("read", "read_value", {"key": "x"}),),
                outputs={"x": observation_ref("missing", "value")},
            )

    def test_program_cannot_expand_exact_turn_tool_authority(self) -> None:
        bridge = Bridge()
        program = HarnessToolProgram(
            steps=(HarnessToolProgramStep("write", "write_value", {"value": "x"}),),
            outputs={},
        )
        with self.assertRaisesRegex(ValueError, "not admitted on the exact turn"):
            HarnessToolProgramExecutor(bridge, (READ, LOOKUP)).execute(
                program,
                remaining_tool_calls=1,
                step_prefix="turn-p2",
            )
        self.assertEqual(bridge.calls, [])

    def test_program_requires_budget_for_every_physical_tool_before_dispatch(self) -> None:
        bridge = Bridge()
        with self.assertRaisesRegex(ValueError, "remaining Tool Call budget"):
            HarnessToolProgramExecutor(bridge, (READ, LOOKUP)).execute(
                dependent_program(),
                remaining_tool_calls=1,
                step_prefix="turn-p2",
            )
        self.assertEqual(bridge.calls, [])

    def test_unknown_stops_program_and_never_dispatches_pending_step(self) -> None:
        bridge = Bridge(stop_on="lookup_value", stop_status="unknown")
        program = HarnessToolProgram(
            steps=(
                *dependent_program().steps,
                HarnessToolProgramStep("write", "write_value", {"value": "must-not-run"}),
            ),
            outputs={"never": observation_ref("write", "written")},
        )
        result = HarnessToolProgramExecutor(bridge, (READ, LOOKUP, WRITE)).execute(
            program,
            remaining_tool_calls=3,
            step_prefix="turn-p2",
        )
        self.assertEqual(result.status, "unknown")
        self.assertEqual([call.name for call, _ in bridge.calls], ["read_value", "lookup_value"])
        self.assertEqual(result.output, {})

    def test_program_result_digest_and_model_projection_are_sealed_after_return(self) -> None:
        result = HarnessToolProgramExecutor(Bridge(), (READ, LOOKUP)).execute(
            dependent_program(), remaining_tool_calls=2, step_prefix="result-snapshot"
        )
        original = result.to_dict()
        model_projection = result.to_model_projection()
        digest = result.digest
        self.assertEqual(result.status, "completed")

        # A caller must not forge durable result evidence or model-visible
        # content merely by mutating the public convenience JSON mapping.
        result.output["matches"].append("forged")
        result.output["query"] = "forged"
        self.assertEqual(result.digest, digest)
        self.assertEqual(result.to_dict(), original)
        self.assertEqual(result.to_model_projection(), model_projection)

        emitted = result.to_dict()
        emitted["output"]["matches"].append("forged-serialization")
        self.assertEqual(result.to_dict(), original)

    def test_program_result_output_does_not_alias_constructor_input(self) -> None:
        original = HarnessToolProgramExecutor(Bridge(), (READ, LOOKUP)).execute(
            dependent_program(), remaining_tool_calls=2, step_prefix="constructor-snapshot"
        )
        output = {"nested": {"items": ["trusted"]}}
        result = HarnessToolProgramResult(
            program_digest=original.program_digest,
            status=original.status,
            observations=original.observations,
            output=output,
        )
        expected_digest = result.digest
        output["nested"]["items"].append("untrusted")
        self.assertEqual(result.output, {"nested": {"items": ["trusted"]}})
        self.assertEqual(result.digest, expected_digest)

    def test_model_projection_keeps_exact_step_evidence_but_not_intermediate_content(self) -> None:
        result = HarnessToolProgramExecutor(Bridge(), (READ, LOOKUP)).execute(
            dependent_program(),
            remaining_tool_calls=2,
            step_prefix="turn-p2",
        )
        projection = result.to_model_projection()
        self.assertEqual(projection["output"], result.output)
        self.assertEqual(len(projection["steps"]), 2)
        encoded = repr(projection)
        self.assertNotIn("'value': 'needle'", encoded)
        self.assertIn("observationDigest", encoded)

    def test_references_are_exact_value_substitution_not_string_code(self) -> None:
        program = HarnessToolProgram(
            steps=(
                HarnessToolProgramStep("read", "read_value", {"key": "source"}),
                HarnessToolProgramStep(
                    "lookup",
                    "lookup_value",
                    {"query": observation_ref("read", "value")},
                ),
            ),
            outputs={"digest": observation_ref("read", "digest")},
        )
        result = HarnessToolProgramExecutor(Bridge(), (READ, LOOKUP)).execute(
            program,
            remaining_tool_calls=2,
            step_prefix="turn-p2",
        )
        self.assertEqual(result.output["digest"], "sha256:" + "a" * 64)

    def test_native_action_envelope_counts_inner_physical_tools_and_is_not_runtime_tool(
        self,
    ) -> None:
        action = HarnessToolProgramAction(
            action_call_id="program-action:p2:1",
            program=dependent_program(),
        )
        self.assertEqual(action.physical_tool_calls, 2)
        self.assertEqual(HarnessToolProgramAction.from_dict(action.to_dict()), action)
        self.assertNotEqual(action.physical_tool_calls, 1)

        capability = project_tool_program_action_capability(
            admitted_tools=(READ, LOOKUP),
            remaining_tool_calls=1,
        )
        self.assertFalse(capability["runtimeTool"])
        self.assertEqual(capability["maxProgramSteps"], 1)
        self.assertEqual(
            capability["physicalToolAccounting"],
            "one-existing-tool-budget-unit-per-program-step",
        )
        self.assertEqual(capability["admittedToolNames"], ["lookup_value", "read_value"])

    def test_wire_action_and_program_reject_noninteger_identity_and_accounting(self) -> None:
        """Bool/float are not wire integers, even when Python says True == 1."""
        action = HarnessToolProgramAction(
            action_call_id="program-action:p2:type-boundary",
            program=HarnessToolProgram(
                steps=(HarnessToolProgramStep("read", "read_value", {"key": "x"}),),
                outputs={},
            ),
        )
        original = action.to_dict()
        for field, invalid in (
            ("schemaVersion", True),
            ("schemaVersion", 1.0),
            ("physicalToolCalls", True),
            ("physicalToolCalls", 1.0),
        ):
            with self.subTest(field=field, invalid=invalid):
                forged = {**original, field: invalid}
                with self.assertRaises(ValueError):
                    HarnessToolProgramAction.from_dict(forged)
        for invalid in (True, 1.0):
            with self.subTest(program_version=invalid):
                forged = {
                    **original,
                    "program": {**original["program"], "schemaVersion": invalid},
                }
                with self.assertRaises(ValueError):
                    HarnessToolProgramAction.from_dict(forged)

    def test_action_round_trip_rejects_forged_physical_tool_count(self) -> None:
        raw = HarnessToolProgramAction(
            action_call_id="program-action:p2:forged-count",
            program=dependent_program(),
        ).to_dict()
        raw["physicalToolCalls"] = 1
        with self.assertRaisesRegex(ValueError, "physical Tool count differs"):
            HarnessToolProgramAction.from_dict(raw)


if __name__ == "__main__":
    unittest.main()
