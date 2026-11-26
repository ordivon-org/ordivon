from __future__ import annotations

import unittest

from anc_canonical import canonical_digest

from ordivon_harness.ordivon.loop import RunStopCode
from ordivon_harness.ordivon.model import AgentRunConclusion, AgentToolCall
import ordivon_harness.domain_tools as domain_tools
from ordivon_harness.domain_tools import (
    AgentToolDefinition,
    DomainToolCatalog,
    DomainToolLoopPlan,
    DomainToolLoopRunner,
    RunBudget,
    HarnessToolObservation,
)
from ordivon_harness.ordivon.model import AgentTurnResult, ScriptedTurnAdapter


class _SecurityPlanBridge:
    catalog = DomainToolCatalog(
        domain_id="domain:security-test",
        revision="team-plans-v1",
        tools=(
            AgentToolDefinition(
                "select_team_plan",
                "Select one admitted side-level plan for this Contest tick.",
                {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "plan": {
                            "type": "string",
                            "enum": ["native-policy", "sleep"],
                        }
                    },
                    "required": ["plan"],
                },
            ),
            AgentToolDefinition(
                "inspect_hidden_truth",
                "Test-only Tool that must not be granted to the Actor.",
                {"type": "object", "additionalProperties": False},
            ),
        ),
    )
    bridge_identity = {
        "bridgeId": "bridge:security-plan-test",
        "revision": "1",
    }

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def execute(self, call: AgentToolCall, *, step_id: str) -> HarnessToolObservation:
        self.calls.append((step_id, call.name))
        return HarnessToolObservation(
            tool_call_id=call.tool_call_id,
            tool_name=call.name,
            status="observed",
            structured_content={
                "admitted": True,
                "plan": call.arguments["plan"],
            },
        )


def _result(
    suffix: str,
    *,
    calls: tuple[AgentToolCall, ...] = (),
    conclusion: AgentRunConclusion | None = None,
) -> AgentTurnResult:
    return AgentTurnResult(
        model_call_id=f"model-call:domain:{suffix}",
        model_id="ordivon.scripted-model.v1",
        content=None,
        tool_calls=calls,
        conclusion=conclusion,
        usage={"total_tokens": 10},
        finish_reason="tool_calls" if calls else "stop",
        raw_response_digest=canonical_digest({"result": suffix}),
    )


class DomainToolBridgeTests(unittest.TestCase):
    def test_secondary_agent_control_reexports_are_retired(self) -> None:
        for name in (
            "AgentLoopResult",
            "AgentRunConclusion",
            "AgentToolCall",
            "AgentTurnAdapter",
            "CancellationToken",
            "RunStopCode",
        ):
            self.assertFalse(hasattr(domain_tools, name), name)

    def _plan(self, *, allowed_tools: tuple[str, ...] = ("select_team_plan",)):
        return DomainToolLoopPlan(
            harness_run_id="harness-run:security:test",
            assignment_id="assignment:security:test",
            context_digest=canonical_digest({"context": "actor-specific-observation"}),
            initial_messages=(
                {"role": "system", "content": "Choose one granted plan."},
                {"role": "user", "content": "The current observation is bounded."},
            ),
            allowed_tools=allowed_tools,
            budget=RunBudget(4, 2, 100_000, 60_000),
        )

    def test_generic_domain_bridge_runs_through_harness_loop(self) -> None:
        bridge = _SecurityPlanBridge()
        adapter = ScriptedTurnAdapter(
            (
                _result(
                    "tool",
                    calls=(
                        AgentToolCall(
                            "tool-call:security:1",
                            "select_team_plan",
                            {"plan": "sleep"},
                        ),
                    ),
                ),
                _result(
                    "done",
                    conclusion=AgentRunConclusion(
                        "candidate_completed",
                        "Submitted the admitted side-level plan.",
                    ),
                ),
            )
        )
        runner = DomainToolLoopRunner(adapter, bridge)
        plan = self._plan()

        result = runner.run(plan)

        self.assertIs(result.stop_code, RunStopCode.CANDIDATE_COMPLETED)
        self.assertEqual(result.tool_calls, 1)
        self.assertEqual(len(result.observations), 1)
        self.assertEqual(bridge.calls[0][1], "select_team_plan")
        self.assertEqual(
            tuple(tool.name for tool in adapter.requests[0].tools),
            ("select_team_plan",),
        )
        identity = runner.execution_identity(plan)
        self.assertEqual(identity["domain"]["domainId"], "domain:security-test")
        self.assertEqual(
            identity["provider"]["requestedModelId"],
            "ordivon.scripted-model.v1",
        )

    def test_unknown_granted_tool_is_rejected_before_provider_call(self) -> None:
        bridge = _SecurityPlanBridge()
        adapter = ScriptedTurnAdapter(
            (
                _result(
                    "unused",
                    conclusion=AgentRunConclusion(
                        "candidate_completed",
                        "This result must not be consumed.",
                    ),
                ),
            )
        )
        runner = DomainToolLoopRunner(adapter, bridge)

        with self.assertRaisesRegex(ValueError, "unknown Tools"):
            runner.run(self._plan(allowed_tools=("missing_tool",)))
        self.assertEqual(adapter.requests, [])

    def test_no_granted_tool_runs_normal_cognition_without_any_effect(self) -> None:
        """A valid domain catalog does not force an Agent to execute a Tool."""
        bridge = _SecurityPlanBridge()
        adapter = ScriptedTurnAdapter((
            _result(
                "cognition-only",
                conclusion=AgentRunConclusion(
                    "candidate_completed",
                    "Summarized the observation without requiring a Tool.",
                ),
            ),
        ))
        plan = self._plan(allowed_tools=())
        from dataclasses import replace
        plan = replace(plan, budget=RunBudget(3, 0, 4096, 60_000))
        runner = DomainToolLoopRunner(adapter, bridge)

        result = runner.run(plan)

        self.assertIs(result.stop_code, RunStopCode.CANDIDATE_COMPLETED)
        self.assertEqual(result.tool_calls, 0)
        self.assertEqual(bridge.calls, [])
        self.assertEqual(len(adapter.requests), 1)
        self.assertEqual(tuple(adapter.requests[0].tools), ())
        identity = runner.execution_identity(plan)
        self.assertEqual(identity["domain"]["allowedTools"], [])
        self.assertEqual(
            identity["domain"]["grantedCatalogDigest"],
            bridge.catalog._granted_digest(()),
        )

    def test_no_granted_tool_cannot_execute_catalogued_effect(self) -> None:
        """The empty grant is legitimate cognition, not wildcard authority."""
        bridge = _SecurityPlanBridge()
        denied = domain_tools._GrantedDomainToolBridge(bridge, ())
        from ordivon_harness.ordivon.tool_errors import ToolBridgeErrorKind
        from ordivon_harness.ordivon.tool_errors import ToolBridgeError
        with self.assertRaises(ToolBridgeError) as observed:
            denied.execute(
                AgentToolCall("tool-call:zero-grant:denied", "select_team_plan", {"plan": "sleep"}),
                step_id="step:domain:no-tool",
            )
        self.assertEqual(observed.exception.kind, ToolBridgeErrorKind.AUTHORITY_DENIED)
        self.assertEqual(bridge.calls, [])
        self.assertEqual(denied.definitions(), ())

    def test_duplicate_and_unknown_grants_stay_denied(self) -> None:
        catalog = _SecurityPlanBridge.catalog
        with self.assertRaisesRegex(ValueError, "unique"):
            catalog._select(("select_team_plan", "select_team_plan"))
        with self.assertRaisesRegex(ValueError, "unknown Tools"):
            catalog._select(("unregistered_tool",))
        with self.assertRaisesRegex(ValueError, "non-empty"):
            DomainToolCatalog("domain:no-tools", "r1", ())

    def test_catalog_digest_binds_revision_and_tool_shape(self) -> None:
        first = _SecurityPlanBridge.catalog
        second = DomainToolCatalog(
            domain_id=first.domain_id,
            revision="team-plans-v2",
            tools=first.tools,
        )
        self.assertNotEqual(first.digest, second.digest)
        self.assertNotEqual(
            first._granted_digest(("select_team_plan",)),
            second._granted_digest(("select_team_plan",)),
        )
        self.assertEqual(
            first._granted_digest(("select_team_plan",)),
            first._granted_digest(("select_team_plan",)),
        )


if __name__ == "__main__":
    unittest.main()
