from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ordivon_harness.api import HarnessAgentRun
from ordivon_harness.ordivon.model import AgentTurnCapabilities, ScriptedTurnAdapter
from ordivon_harness.workbench import build_durable_workbench_projection

from tests.test_r1_single_capability_truth import request
from tests.test_r3_supported_agent_run import (
    FakeRuntime,
    FixedClock,
    contract,
    execution_binding,
    needs_input,
)


class CompositionProjectionTests(unittest.TestCase):
    def test_exact_turn_request_projects_only_bound_actions(self) -> None:
        base = request()
        projection = build_durable_workbench_projection(
            run={"status": "running"},
            contract=contract("workbench-turn"),
            provider_call={"status": "completed"},
            provider_request=base,
            snapshot=None,
            recovery=None,
            run_receipt=None,
            completion_proposal=None,
        )["currentActionSurface"]["projection"]
        self.assertEqual(projection["stage"], "turn-admitted")
        self.assertEqual(projection["nativeActions"], ["conclusion"])
        self.assertFalse(projection["callerIngressAddressable"])

        expanded_request = request(
            capabilities=AgentTurnCapabilities(
                conclusion=True,
                working_set_transition=True,
                caller_ingress_promotion=False,
                working_set_history=True,
            )
        )
        expanded = build_durable_workbench_projection(
            run={"status": "running"},
            contract=contract("workbench-expanded"),
            provider_call={"status": "completed"},
            provider_request=expanded_request,
            snapshot=None,
            recovery=None,
            run_receipt=None,
            completion_proposal=None,
        )["currentActionSurface"]["projection"]
        self.assertEqual(
            expanded["nativeActions"],
            ["conclusion", "working-set-transition", "working-set-history"],
        )

    def test_exact_turn_projection_includes_admitted_tool_program_action(self) -> None:
        tool_program_request = request(
            capabilities=AgentTurnCapabilities(tool_program=True)
        )
        projection = build_durable_workbench_projection(
            run={"status": "running"},
            contract=contract("workbench-tool-program"),
            provider_call={"status": "completed"},
            provider_request=tool_program_request,
            snapshot=None,
            recovery=None,
            run_receipt=None,
            completion_proposal=None,
        )["currentActionSurface"]["projection"]
        self.assertEqual(projection["nativeActions"], ["conclusion", "tool-program"])

    def test_in_process_explain_reports_exact_supported_surfaces_without_liveness_claims(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            clock = FixedClock()
            value = contract("p0-explain")
            run = HarnessAgentRun.create(
                Path(directory) / "state",
                value,
                lambda _contract: ScriptedTurnAdapter((needs_input("model-call:p0-explain"),)),
                clock_ms=clock,
                monotonic_ms=clock,
            )
            explanation = run.explain()
            process = explanation["processLocal"]
            self.assertFalse(process["runtimeClient"]["supplied"])
            self.assertEqual(process["runtimeClient"]["liveness"], "not-probed")
            self.assertEqual(process["adapter"]["liveness"], "not-probed")
            self.assertEqual(
                explanation["run"]["toolSurface"]["surfaceId"],
                "harness.execution.no-tool.v1",
            )

        with tempfile.TemporaryDirectory() as directory:
            value = contract("p0-runtime-explain", tools=True)
            run = HarnessAgentRun.create(
                Path(directory) / "state",
                value,
                lambda _contract: ScriptedTurnAdapter((needs_input("model-call:p0-runtime"),)),
                execution_binding=execution_binding(value),
                runtime=FakeRuntime(),
            )
            explanation = run.explain()
            process = explanation["processLocal"]
            self.assertTrue(process["runtimeClient"]["supplied"])
            self.assertEqual(process["runtimeClient"]["liveness"], "not-probed")
            self.assertTrue(process["executionBinding"]["supplied"])
            self.assertEqual(
                explanation["run"]["toolSurface"]["surfaceId"],
                "harness.execution.runtime-search.v1",
            )


if __name__ == "__main__":
    unittest.main()
