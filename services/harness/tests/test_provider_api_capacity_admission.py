from __future__ import annotations

import unittest

from anc_canonical import canonical_digest

from ordivon_harness.ordivon.api_capacity import (
    ApiCapacityAdmissionGuard,
    ApiCapacityFailureKind,
    ApiRateLimitKind,
    ApiSpendStanding,
    ProviderApiCapacitySnapshot,
    ProviderApiRateLimit,
    ProviderApiSpendCapacity,
    classify_openai_api_capacity_error,
)
from ordivon_harness.ordivon.capacity import ProviderCapacityStatus
from ordivon_harness.ordivon.loop import OrdivonAgentLoop, RunBudget, RunStopCode
from ordivon_harness.ordivon.model import (
    AgentRunConclusion,
    AgentTurnRequest,
    AgentTurnResult,
    ScriptedTurnAdapter,
)


class DurableNoToolBridge:
    catalog_digest = canonical_digest({"surface": "api-capacity-admission"})
    durable_provider_calls_enabled = True

    def __init__(self) -> None:
        self.begins = 0
        self.admits = 0

    def definitions(self):
        return ()

    def configure_provider_call(self, *, adapter_id, requested_model_id):
        self.adapter_id = adapter_id
        self.requested_model_id = requested_model_id

    def begin_provider_call(self, request, *, provider_request_digest):
        del request, provider_request_digest
        self.begins += 1
        return None

    def admit_provider_call(self, request, *, control):
        del request, control
        self.admits += 1
        return True

    def complete_provider_call(self, request, result):
        del request, result


def _request() -> AgentTurnRequest:
    return AgentTurnRequest(
        harness_run_id="harness-run:api-capacity-request",
        turn_id="turn:api-capacity-request:1",
        sequence=1,
        assignment_id="assignment:api-capacity-request",
        context_digest=canonical_digest({"api-capacity": "context"}),
        tool_catalog_digest=canonical_digest({"api-capacity": "tools"}),
        messages=({"role": "user", "content": "capacity"},),
        tools=(),
        remaining_budget={"modelCalls": 1, "toolCalls": 0, "totalTokens": 4096},
    )


def _snapshot(
    *,
    rate_limits: tuple[ProviderApiRateLimit, ...] = (),
    spend: ProviderApiSpendCapacity | None = None,
    status: ProviderCapacityStatus = ProviderCapacityStatus.AVAILABLE,
) -> ProviderApiCapacitySnapshot:
    return ProviderApiCapacitySnapshot(
        source="provider-api-observation:test",
        observed_at_ms=10_000,
        principal_ref="principal:api-project",
        source_node_ref="runtime:linux-local",
        provider_id="openai-api",
        model_id="model:test",
        account_ref="project:opaque",
        status=status,
        rate_limits=rate_limits,
        spend=spend,
    )


def _result() -> AgentTurnResult:
    return AgentTurnResult(
        model_call_id="model-call:api-capacity-admission",
        model_id=ScriptedTurnAdapter.model_id,
        content="done",
        tool_calls=(),
        conclusion=AgentRunConclusion(
            status="candidate_completed",
            summary="api-capacity fixture complete",
        ),
        usage={"inputTokens": 3, "outputTokens": 2},
        finish_reason="stop",
        raw_response_digest=canonical_digest({"api-capacity": "result"}),
    )


class ProviderApiCapacityAdmissionTests(unittest.TestCase):
    def test_api_rate_and_spend_are_distinct_facets(self) -> None:
        snapshot = _snapshot(
            rate_limits=(
                ProviderApiRateLimit(ApiRateLimitKind.REQUESTS, 100, 40, 20_000),
                ProviderApiRateLimit(ApiRateLimitKind.TOKENS, 100_000, 50_000, 20_000),
            ),
            spend=ProviderApiSpendCapacity(
                ApiSpendStanding.AVAILABLE,
                remaining_microusd=25_000_000,
                resets_at_ms=50_000,
            ),
        )
        encoded = snapshot.to_dict()
        self.assertEqual(encoded["rateLimits"][0]["kind"], "requests")
        self.assertEqual(encoded["spend"]["standing"], "available")
        self.assertNotEqual(encoded["rateLimits"], encoded["spend"])

    def test_request_and_token_capacity_admit_one_dispatch(self) -> None:
        guard = ApiCapacityAdmissionGuard(
            snapshot=_snapshot(
                rate_limits=(
                    ProviderApiRateLimit(ApiRateLimitKind.REQUESTS, 100, 40, 20_000),
                    ProviderApiRateLimit(ApiRateLimitKind.TOKENS, 100_000, 50_000, 20_000),
                ),
                spend=ProviderApiSpendCapacity(ApiSpendStanding.AVAILABLE),
            ),
            max_staleness_ms=5_000,
            expected_principal_ref="principal:api-project",
            required_rate_kinds=(
                ApiRateLimitKind.REQUESTS,
                ApiRateLimitKind.TOKENS,
            ),
            reserve_requests=2,
            reserve_tokens=5_000,
            require_spend_capacity=True,
            clock_ms=lambda: 12_000,
        )
        decision = guard.check(_request(), request_token_upper_bound=20_000)
        self.assertEqual(decision.standing.value, "admit")

    def test_token_bucket_that_cannot_fit_request_holds(self) -> None:
        guard = ApiCapacityAdmissionGuard(
            snapshot=_snapshot(
                rate_limits=(
                    ProviderApiRateLimit(ApiRateLimitKind.TOKENS, 100_000, 21_000, 20_000),
                ),
            ),
            max_staleness_ms=5_000,
            expected_principal_ref="principal:api-project",
            required_rate_kinds=(ApiRateLimitKind.TOKENS,),
            reserve_tokens=2_000,
            clock_ms=lambda: 12_000,
        )
        decision = guard.check(_request(), request_token_upper_bound=20_000)
        self.assertEqual(decision.standing.value, "hold")
        self.assertIn("cannot fit", decision.reason)

    def test_spend_exhaustion_holds_even_when_rate_bucket_is_healthy(self) -> None:
        guard = ApiCapacityAdmissionGuard(
            snapshot=_snapshot(
                rate_limits=(ProviderApiRateLimit(ApiRateLimitKind.REQUESTS, 100, 90, 20_000),),
                spend=ProviderApiSpendCapacity(
                    ApiSpendStanding.EXHAUSTED,
                    reason_code="project_spend_limit_exceeded",
                ),
            ),
            max_staleness_ms=5_000,
            expected_principal_ref="principal:api-project",
            required_rate_kinds=(ApiRateLimitKind.REQUESTS,),
            require_spend_capacity=True,
            clock_ms=lambda: 12_000,
        )
        decision = guard.check(_request(), request_token_upper_bound=100)
        self.assertEqual(decision.standing.value, "hold")
        self.assertIn("project_spend_limit_exceeded", decision.reason)

    def test_missing_required_spend_or_rate_evidence_is_unknown_not_zero(self) -> None:
        guard = ApiCapacityAdmissionGuard(
            snapshot=_snapshot(
                rate_limits=(ProviderApiRateLimit(ApiRateLimitKind.REQUESTS, 100, 90, 20_000),),
            ),
            max_staleness_ms=5_000,
            expected_principal_ref="principal:api-project",
            required_rate_kinds=(
                ApiRateLimitKind.REQUESTS,
                ApiRateLimitKind.TOKENS,
            ),
            require_spend_capacity=True,
            clock_ms=lambda: 12_000,
        )
        decision = guard.check(_request(), request_token_upper_bound=100)
        self.assertEqual(decision.standing.value, "unknown")

    def test_component_token_limit_fails_closed_until_component_bounds_exist(self) -> None:
        guard = ApiCapacityAdmissionGuard(
            snapshot=_snapshot(
                rate_limits=(
                    ProviderApiRateLimit(ApiRateLimitKind.INPUT_TOKENS, 100_000, 90_000, 20_000),
                ),
            ),
            max_staleness_ms=5_000,
            expected_principal_ref="principal:api-project",
            required_rate_kinds=(ApiRateLimitKind.INPUT_TOKENS,),
            clock_ms=lambda: 12_000,
        )
        decision = guard.check(_request(), request_token_upper_bound=100)
        self.assertEqual(decision.standing.value, "unknown")
        self.assertIn("component", decision.reason)

    def test_openai_429_capacity_codes_are_not_collapsed(self) -> None:
        self.assertIs(
            classify_openai_api_capacity_error("rate_limit_exceeded"),
            ApiCapacityFailureKind.TRANSIENT_RATE_LIMIT,
        )
        self.assertIs(
            classify_openai_api_capacity_error("credit_balance_exhausted"),
            ApiCapacityFailureKind.CREDIT_EXHAUSTED,
        )
        self.assertIs(
            classify_openai_api_capacity_error("organization_usage_limit_exceeded"),
            ApiCapacityFailureKind.USAGE_LIMIT_EXCEEDED,
        )
        for code in (
            "organization_spend_limit_exceeded",
            "project_spend_limit_exceeded",
        ):
            with self.subTest(code=code):
                self.assertIs(
                    classify_openai_api_capacity_error(code),
                    ApiCapacityFailureKind.SPEND_LIMIT_EXCEEDED,
                )

    def test_api_hold_stops_before_provider_lifecycle_and_physical_invoke(self) -> None:
        adapter = ScriptedTurnAdapter((_result(),))
        bridge = DurableNoToolBridge()
        guard = ApiCapacityAdmissionGuard(
            snapshot=_snapshot(
                rate_limits=(ProviderApiRateLimit(ApiRateLimitKind.REQUESTS, 100, 0, 20_000),),
            ),
            max_staleness_ms=5_000,
            expected_principal_ref="principal:api-project",
            required_rate_kinds=(ApiRateLimitKind.REQUESTS,),
            clock_ms=lambda: 12_000,
        )
        result = OrdivonAgentLoop(
            adapter,
            bridge,
            budget=RunBudget(
                max_model_calls=1,
                max_tool_calls=0,
                max_observation_bytes=16_384,
                max_wall_time_ms=10_000,
                max_total_tokens=10_000,
                max_model_retries=0,
            ),
            capacity_admission_guard=guard,
        ).run(
            harness_run_id="harness-run:api-capacity-admission",
            assignment_id="assignment:api-capacity-admission",
            context_digest=canonical_digest({"api-capacity": "context"}),
            initial_messages=({"role": "user", "content": "finish"},),
        )
        self.assertEqual(result.stop_code, RunStopCode.PROVIDER_UNAVAILABLE)
        self.assertEqual(adapter.requests, [])
        self.assertEqual(bridge.begins, 0)
        self.assertEqual(bridge.admits, 0)


if __name__ == "__main__":
    unittest.main()
