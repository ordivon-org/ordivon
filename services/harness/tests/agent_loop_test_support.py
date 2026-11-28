"""Backend-neutral fixtures shared by Harness Agent Loop consumer tests."""

from __future__ import annotations

from anc_canonical import canonical_digest

from ordivon_harness.core_contracts import HarnessBoundReference, HarnessRunContract
from ordivon_harness.ordivon.agent_bridge import NO_TOOL_AGENT_SURFACE_DIGEST
from ordivon_harness.ordivon.loop import RunBudget
from ordivon_harness.ordivon.model import (
    AgentRunConclusion,
    AgentTurnRequest,
    AgentTurnResult,
    ScriptedTurnAdapter,
    static_provider_request_digest,
)


DIGEST_A = "sha256:" + "a" * 64

DIGEST_B = "sha256:" + "b" * 64

class FixedClock:
    def __init__(self, value: int = 1_000) -> None:
        self.value = value

    def __call__(self) -> int:
        return self.value

class FailIfInvokedAdapter:
    adapter_id = ScriptedTurnAdapter.adapter_id
    model_id = ScriptedTurnAdapter.model_id
    provider_request_digest = static_provider_request_digest

    def __init__(self) -> None:
        self.requests: list[AgentTurnRequest] = []

    def invoke(self, request: AgentTurnRequest) -> AgentTurnResult:
        self.requests.append(request)
        raise AssertionError("durable Provider result should have replayed")

def contract(suffix: str) -> HarnessRunContract:
    return HarnessRunContract(
        harness_run_id=f"harness-run:p0-agent-loop-{suffix}",
        harness_implementation_id="ordivon-harness@0.7.0-dev",
        caller_id="caller:p0-independent-agent-loop",
        caller_run_ref=f"trial:p0-agent-loop-{suffix}",
        objective_ref=HarnessBoundReference(
            f"objective:p0-agent-loop-{suffix}", "objective", DIGEST_A
        ),
        context_refs=(
            HarnessBoundReference(f"context:p0-agent-loop-{suffix}", "context", DIGEST_B),
        ),
        provider_id="provider:scripted",
        adapter_id=ScriptedTurnAdapter.adapter_id,
        requested_model_id=ScriptedTurnAdapter.model_id,
        tool_catalog_digest=NO_TOOL_AGENT_SURFACE_DIGEST,
        tool_grant_digest=canonical_digest(
            {
                "schemaVersion": 1,
                "kind": "ordivon.no-tool-grant",
                "tools": [],
            }
        ),
        budget={
            "maxModelCalls": 2,
            "maxToolCalls": 1,
            "maxWallTimeMs": 10_000,
        },
        completion_contract={"mode": "record"},
        system_manifest_ref=HarnessBoundReference(
            f"system-manifest:p0-agent-loop-{suffix}",
            "system-manifest",
            DIGEST_A,
        ),
        created_at_ms=1_000,
    )

def budget() -> RunBudget:
    return RunBudget(
        max_model_calls=2,
        max_tool_calls=1,
        max_observation_bytes=16_384,
        max_wall_time_ms=10_000,
        max_total_tokens=10_000,
        max_model_retries=1,
    )

def completed_result(suffix: str) -> AgentTurnResult:
    return AgentTurnResult(
        model_call_id=f"model-call:p0-agent-loop-{suffix}",
        model_id=ScriptedTurnAdapter.model_id,
        content="completed",
        tool_calls=(),
        conclusion=AgentRunConclusion(
            status="candidate_completed",
            summary="Independent Agent Loop completed without Host state.",
        ),
        usage={"inputTokens": 12, "outputTokens": 4},
        finish_reason="stop",
        raw_response_digest=canonical_digest({"response": suffix}),
    )

def needs_input_result(suffix: str) -> AgentTurnResult:
    return AgentTurnResult(
        model_call_id=f"model-call:p0-agent-loop-{suffix}",
        model_id=ScriptedTurnAdapter.model_id,
        content="need one bounded answer",
        tool_calls=(),
        conclusion=AgentRunConclusion(
            status="needs_input",
            summary="One bounded caller answer is required.",
        ),
        usage={"inputTokens": 10, "outputTokens": 5},
        finish_reason="stop",
        raw_response_digest=canonical_digest({"response": suffix}),
    )
