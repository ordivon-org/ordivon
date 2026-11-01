from __future__ import annotations

import unittest

from anc_canonical import canonical_digest

from ordivon_harness.domain_tools import (
    AgentToolDefinition, DomainToolCatalog, DomainToolLoopPlan, DomainToolLoopRunner, RunBudget,
)
from ordivon_harness.ordivon.model import (
    AgentRunConclusion, AgentToolCall, AgentTurnResult, ScriptedTurnAdapter,
)
from ordivon_harness.ordivon.loop import RunStopCode

from ordivon_harness.agent_tool_observation import HarnessToolObservation


def observation(content: dict) -> HarnessToolObservation:
    return HarnessToolObservation(
        tool_call_id="tool-call:seal",
        tool_name="search_workspace",
        status="observed",
        structured_content=content,
        runtime_job_ref="job:seal",
        reconciled=True,
    )


class ToolObservationEvidenceSealTests(unittest.TestCase):
    def test_input_alias_does_not_rewrite_admitted_observation(self) -> None:
        raw = {"result": {"status": "unknown", "hits": [{"claim": "unverified"}]}}
        item = observation(raw)
        original = item.to_dict()
        digest = item.digest
        raw["result"]["hits"][0]["claim"] = "verified"
        raw["result"]["status"] = "observed"
        self.assertEqual(item.to_dict(), original)
        self.assertEqual(item.digest, digest)

    def test_observation_accessor_mutation_does_not_change_evidence_identity(self) -> None:
        item = observation({"result": {"status": "unknown"}})
        original = item.to_dict()
        digest = item.digest
        item.structured_content["result"]["status"] = "verified"
        self.assertEqual(item.to_dict(), original)
        self.assertEqual(item.digest, digest)
        self.assertEqual(hash(item), hash(observation({"result": {"status": "unknown"}})))

    def test_model_message_and_dict_mutations_do_not_rewrite_source(self) -> None:
        item = observation({"result": {"status": "unknown", "hits": ["a"]}})
        initial = item.to_dict()
        message = item.to_model_message()
        message["observation"]["content"]["result"]["hits"].append("b")
        encoded = item.to_dict()
        encoded["structuredContent"]["result"]["status"] = "verified"
        self.assertEqual(item.to_dict(), initial)
        self.assertEqual(item.to_model_message()["observation"]["content"], initial["structuredContent"])

    def test_bounded_truncation_preserves_original_source_digest(self) -> None:
        original = {"result": {"payload": "x" * 10_000}}
        item = observation(original)
        digest = item.digest
        bounded = item.bounded(512)
        self.assertEqual(bounded.structured_content["originalContentDigest"], canonical_digest(original))
        self.assertEqual(item.digest, digest)
        original["result"]["payload"] = "tampered"
        self.assertEqual(item.digest, digest)
        self.assertEqual(bounded.structured_content["originalContentDigest"], canonical_digest({"result": {"payload": "x" * 10_000}}))

    def test_post_admission_alias_does_not_change_equality(self) -> None:
        raw = {"result": {"status": "unknown"}}
        left = observation(raw)
        right = observation({"result": {"status": "unknown"}})
        self.assertEqual(left, right)
        raw["result"]["status"] = "verified"
        self.assertEqual(left, right)

    def test_real_domain_loop_projects_sealed_observation_after_alias_mutation(self) -> None:
        # A physical Tool Bridge may still own the original dictionary. Its
        # mutation must not rewrite the observed evidence seen by the next turn.
        class MutatingSourceBridge:
            catalog = DomainToolCatalog(
                domain_id="domain:seal-test",
                revision="seal-v1",
                tools=(AgentToolDefinition(
                    name="observe_fact",
                    description="Return one harmless observation.",
                    input_schema={"type": "object", "additionalProperties": False},
                ),),
            )
            bridge_identity = {"bridgeId": "bridge:seal-test"}

            def __init__(self) -> None:
                self.called = 0

            def execute(self, call: AgentToolCall, *, step_id: str) -> HarnessToolObservation:
                self.called += 1
                raw = {"result": {"standing": "UNKNOWN", "source": "tool"}}
                item = HarnessToolObservation(
                    tool_call_id=call.tool_call_id,
                    tool_name=call.name,
                    status="observed",
                    structured_content=raw,
                )
                raw["result"]["standing"] = "VERIFIED"
                return item

        def turn(suffix: str, *, calls=(), conclusion=None):
            return AgentTurnResult(
                model_call_id=f"model-call:seal:{suffix}",
                model_id=ScriptedTurnAdapter.model_id,
                content=None,
                tool_calls=calls,
                conclusion=conclusion,
                usage={"total_tokens": 10},
                finish_reason="tool_calls" if calls else "stop",
                raw_response_digest=canonical_digest({"seal": suffix}),
            )

        adapter = ScriptedTurnAdapter((
            turn("tool", calls=(AgentToolCall("tool-call:seal:1", "observe_fact", {}),)),
            turn("end", conclusion=AgentRunConclusion(
                status="candidate_completed",
                summary="Only the caller can verify the domain result.",
                unresolved_unknowns=("The Tool observation did not verify domain success.",),
            )),
        ))
        bridge = MutatingSourceBridge()
        plan = DomainToolLoopPlan(
            harness_run_id="harness-run:seal-consumer",
            assignment_id="assignment:seal-consumer",
            context_digest=canonical_digest({"task": "observe"}),
            initial_messages=({"role": "user", "content": "Observe evidence."},),
            allowed_tools=("observe_fact",),
            budget=RunBudget(3, 2, 32768, 30000),
        )
        outcome = DomainToolLoopRunner(adapter, bridge).run(plan)
        self.assertEqual(outcome.stop_code, RunStopCode.CANDIDATE_COMPLETED)
        self.assertEqual(bridge.called, 1)
        self.assertEqual(len(adapter.requests), 2)
        observations = [
            message for message in adapter.requests[1].messages
            if message.get("role") == "tool"
        ]
        self.assertEqual(len(observations), 1)
        self.assertEqual(
            observations[0]["observation"]["content"]["result"]["standing"], "UNKNOWN"
        )
        self.assertEqual(outcome.observations[0].digest, canonical_digest(
            outcome.observations[0].to_dict()
        ))
        self.assertEqual(outcome.conclusion.unresolved_unknowns, (
            "The Tool observation did not verify domain success.",
        ))


if __name__ == "__main__":
    unittest.main()
