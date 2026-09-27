from __future__ import annotations

from dataclasses import replace
import unittest

from anc_canonical import canonical_digest

from ordivon_harness.protocol import (
    HarnessProviderCallFailureReceipt,
)
from ordivon_harness.ordivon.model import (
    AgentRunConclusion,
    AgentToolCall,
    AgentToolDefinition,
    AgentTurnAdapterError,
    AgentTurnDispatchSafety,
    AgentTurnFailureCode,
    AgentTurnRequest,
    AgentTurnResult,
)
from ordivon_harness.protocol import HarnessProtocolError


def _digest(label: str) -> str:
    return canonical_digest({"fixture": label})


class HarnessProviderCallFailureReceiptTests(unittest.TestCase):
    def test_failure_receipt_round_trips_with_a_stable_digest(self) -> None:
        receipt = HarnessProviderCallFailureReceipt(
            provider_call_id="provider-call:fixture:turn-1",
            request_digest=_digest("request"),
            provider_request_digest=_digest("provider-request"),
            failure_code="provider_transport_failed",
            dispatch_safety="pre_dispatch_safe",
            detail="connection refused before request dispatch",
        )

        decoded = HarnessProviderCallFailureReceipt.from_dict(receipt.to_dict())

        self.assertEqual(decoded, receipt)
        self.assertEqual(decoded.digest, canonical_digest(receipt.to_dict()))

    def test_failure_receipt_rejects_unbounded_or_unknown_fields(self) -> None:
        receipt = HarnessProviderCallFailureReceipt(
            provider_call_id="provider-call:fixture:turn-1",
            request_digest=_digest("request"),
            provider_request_digest=_digest("provider-request"),
            failure_code="provider_rejected",
            dispatch_safety="provider_rejected",
            detail="quota rejected",
        )
        malformed = []
        extra = receipt.to_dict()
        extra["retryable"] = True
        malformed.append(extra)
        invalid_code = receipt.to_dict()
        invalid_code["failureCode"] = "maybe"
        malformed.append(invalid_code)
        invalid_safety = receipt.to_dict()
        invalid_safety["dispatchSafety"] = "probably_safe"
        malformed.append(invalid_safety)
        oversized = receipt.to_dict()
        oversized["detail"] = "界" * 683
        malformed.append(oversized)

        for index, value in enumerate(malformed):
            with self.subTest(case=index):
                with self.assertRaises(HarnessProtocolError):
                    HarnessProviderCallFailureReceipt.from_dict(value)


class AgentTurnPersistenceModelTests(unittest.TestCase):
    def test_dispatch_digest_ignores_dynamic_dispatch_control_budgets(self) -> None:
        request = AgentTurnRequest(
            harness_run_id="harness-run:fixture",
            turn_id="turn:fixture:1",
            sequence=1,
            assignment_id="assignment:fixture:g1",
            context_digest=_digest("context"),
            tool_catalog_digest=_digest("tool-catalog"),
            messages=({"role": "user", "content": "Inspect the repository."},),
            tools=(
                AgentToolDefinition(
                    name="workspace_read",
                    description="Read a workspace file.",
                    input_schema={
                        "type": "object",
                        "properties": {"path": {"type": "string"}},
                    },
                ),
            ),
            remaining_budget={
                "modelCalls": 3,
                "toolCalls": 4,
                "modelRetries": 2,
                "wallTimeMs": 30_000,
            },
        )
        later_wall_clock = replace(
            request,
            remaining_budget={
                "modelCalls": 3,
                "toolCalls": 4,
                "modelRetries": 1,
                "wallTimeMs": 20_000,
            },
        )
        fewer_model_calls = replace(
            request,
            remaining_budget={
                "modelCalls": 2,
                "toolCalls": 4,
                "modelRetries": 2,
                "wallTimeMs": 30_000,
            },
        )

        self.assertNotEqual(request.digest, later_wall_clock.digest)
        self.assertEqual(request.dispatch_digest, later_wall_clock.dispatch_digest)
        self.assertNotEqual(request.dispatch_digest, fewer_model_calls.dispatch_digest)
        self.assertEqual(request.remaining_budget["wallTimeMs"], 30_000)

    def test_tool_call_round_trips_with_optional_provider_arguments(self) -> None:
        normalized = AgentToolCall(
            tool_call_id="tool-call:fixture:malformed",
            name="workspace_read",
            arguments={},
            argument_error="arguments were not valid JSON",
            raw_arguments_digest=_digest("raw-provider-arguments"),
            raw_arguments_preview="{broken",
        )
        ordinary = AgentToolCall(
            tool_call_id="tool-call:fixture:ordinary",
            name="workspace_read",
            arguments={"path": "README.md"},
        )

        self.assertEqual(AgentToolCall.from_dict(normalized.to_dict()), normalized)
        self.assertEqual(AgentToolCall.from_dict(ordinary.to_dict()), ordinary)

    def test_conclusion_and_results_round_trip_with_optional_effective_model(self) -> None:
        conclusion = AgentRunConclusion(
            status="needs_input",
            summary="Need the operator to select a target.",
            artifact_refs=("artifact:fixture",),
            evidence_refs=("evidence:fixture",),
            unresolved_unknowns=("target repository",),
        )
        concluded = AgentTurnResult(
            model_call_id="model-call:fixture:conclusion",
            model_id="requested-model",
            content=None,
            tool_calls=(),
            conclusion=conclusion,
            usage={"inputTokens": 10, "outputTokens": 5},
            finish_reason="tool_calls",
            raw_response_digest=_digest("conclusion-response"),
        )
        tool_result = AgentTurnResult(
            model_call_id="model-call:fixture:tool",
            model_id="requested-model",
            effective_model_id="effective-model",
            content="Inspecting the repository.",
            tool_calls=(
                AgentToolCall(
                    tool_call_id="tool-call:fixture:read",
                    name="workspace_read",
                    arguments={"path": "README.md"},
                ),
            ),
            conclusion=None,
            usage={"inputTokens": 20, "outputTokens": 8},
            finish_reason="tool_calls",
            raw_response_digest=_digest("tool-response"),
        )

        self.assertEqual(
            AgentRunConclusion.from_dict(conclusion.to_dict()),
            conclusion,
        )
        self.assertNotIn("effectiveModelId", concluded.to_dict())
        self.assertEqual(AgentTurnResult.from_dict(concluded.to_dict()), concluded)
        self.assertEqual(AgentTurnResult.from_dict(tool_result.to_dict()), tool_result)

    def test_malformed_normalized_results_are_rejected(self) -> None:
        call = AgentToolCall(
            tool_call_id="tool-call:fixture:read",
            name="workspace_read",
            arguments={"path": "README.md"},
        )
        result = AgentTurnResult(
            model_call_id="model-call:fixture:tool",
            model_id="requested-model",
            content=None,
            tool_calls=(call,),
            conclusion=None,
            usage={},
            finish_reason="tool_calls",
            raw_response_digest=_digest("tool-response"),
        )

        extra_call_field = call.to_dict()
        extra_call_field["unexpected"] = True
        partial_diagnostics = call.to_dict()
        partial_diagnostics["providerArguments"] = {
            "error": "bad",
            "rawDigest": _digest("raw"),
        }
        null_diagnostics = call.to_dict()
        null_diagnostics["providerArguments"] = None
        invalid_conclusion = AgentRunConclusion(
            "needs_input",
            "Need input.",
        ).to_dict()
        invalid_conclusion["artifactRefs"] = "artifact:not-a-list"
        extra_result_field = result.to_dict()
        extra_result_field["unexpected"] = True
        boolean_schema = result.to_dict()
        boolean_schema["schemaVersion"] = True
        object_tool_calls = result.to_dict()
        object_tool_calls["toolCalls"] = {}
        invalid_content = result.to_dict()
        invalid_content["content"] = 42
        invalid_effective_model = result.to_dict()
        invalid_effective_model["effectiveModelId"] = 42
        invalid_nested_call = result.to_dict()
        invalid_nested_call["toolCalls"] = [partial_diagnostics]

        cases = (
            (AgentToolCall.from_dict, extra_call_field),
            (AgentToolCall.from_dict, partial_diagnostics),
            (AgentToolCall.from_dict, null_diagnostics),
            (AgentRunConclusion.from_dict, invalid_conclusion),
            (AgentTurnResult.from_dict, extra_result_field),
            (AgentTurnResult.from_dict, boolean_schema),
            (AgentTurnResult.from_dict, object_tool_calls),
            (AgentTurnResult.from_dict, invalid_content),
            (AgentTurnResult.from_dict, invalid_effective_model),
            (AgentTurnResult.from_dict, invalid_nested_call),
        )
        for index, (decoder, value) in enumerate(cases):
            with self.subTest(case=index):
                with self.assertRaises(ValueError):
                    decoder(value)

    def test_adapter_error_defaults_to_ambiguous_dispatch(self) -> None:
        ambiguous = AgentTurnAdapterError("fixture failure")
        safe = AgentTurnAdapterError(
            "fixture pre-dispatch rejection",
            failure_code=AgentTurnFailureCode.REJECTED,
            dispatch_safety=AgentTurnDispatchSafety.PRE_DISPATCH_SAFE,
        )
        rejected = AgentTurnAdapterError(
            "fixture Provider rejection",
            dispatch_safety=AgentTurnDispatchSafety.PROVIDER_REJECTED,
        )

        self.assertEqual(
            ambiguous.dispatch_safety,
            AgentTurnDispatchSafety.DISPATCH_AMBIGUOUS,
        )
        self.assertEqual(safe.failure_code, AgentTurnFailureCode.REJECTED)
        self.assertEqual(
            safe.dispatch_safety,
            AgentTurnDispatchSafety.PRE_DISPATCH_SAFE,
        )
        self.assertEqual(
            rejected.dispatch_safety,
            AgentTurnDispatchSafety.PROVIDER_REJECTED,
        )


if __name__ == "__main__":
    unittest.main()
