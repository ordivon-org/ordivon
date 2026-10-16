from __future__ import annotations

import json
import unittest

from anc_canonical import canonical_digest

from ordivon_harness.ordivon.capacity import (
    CapacityAdmissionDecision,
    CapacityAdmissionStanding,
    ProviderCapacitySnapshot,
    ProviderCapacityStatus,
    ProviderCapacityWindow,
    SnapshotCapacityAdmissionGuard,
    snapshot_from_cc_switch_quota,
)
from ordivon_harness.ordivon.loop import OrdivonAgentLoop, RunBudget, RunStopCode
from ordivon_harness.ordivon.model import (
    AgentRunConclusion,
    AgentTurnRequest,
    AgentTurnResult,
    ScriptedTurnAdapter,
)


class DurableNoToolBridge:
    catalog_digest = canonical_digest({"surface": "capacity-admission"})
    durable_provider_calls_enabled = True

    def __init__(self) -> None:
        self.begins = 0
        self.admits = 0
        self.completes = 0

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
        self.completes += 1


class FixedGuard:
    def __init__(self, standing: CapacityAdmissionStanding) -> None:
        self.standing = standing
        self.calls = 0

    def check(self, request, *, request_token_upper_bound):
        del request, request_token_upper_bound
        self.calls += 1
        return CapacityAdmissionDecision(
            standing=self.standing,
            snapshot_digest="sha256:" + "a" * 64,
            reason=f"fixture {self.standing.value}",
        )


def _result() -> AgentTurnResult:
    return AgentTurnResult(
        model_call_id="model-call:capacity-admission",
        model_id=ScriptedTurnAdapter.model_id,
        content="done",
        tool_calls=(),
        conclusion=AgentRunConclusion(
            status="candidate_completed",
            summary="capacity-admission fixture complete",
        ),
        usage={"inputTokens": 3, "outputTokens": 2},
        finish_reason="stop",
        raw_response_digest=canonical_digest({"capacity": "result"}),
    )


def _budget() -> RunBudget:
    return RunBudget(
        max_model_calls=1,
        max_tool_calls=0,
        max_observation_bytes=16_384,
        max_wall_time_ms=10_000,
        max_total_tokens=10_000,
        max_model_retries=0,
    )


def _request() -> AgentTurnRequest:
    return AgentTurnRequest(
        harness_run_id="harness-run:capacity-request",
        turn_id="turn:capacity-request:1",
        sequence=1,
        assignment_id="assignment:capacity-request",
        context_digest=canonical_digest({"capacity": "context"}),
        tool_catalog_digest=canonical_digest({"capacity": "tools"}),
        messages=({"role": "user", "content": "capacity"},),
        tools=(),
        remaining_budget={"modelCalls": 1, "toolCalls": 0, "totalTokens": 4096},
    )


def _run(standing: CapacityAdmissionStanding):
    adapter = ScriptedTurnAdapter((_result(),))
    bridge = DurableNoToolBridge()
    guard = FixedGuard(standing)
    result = OrdivonAgentLoop(
        adapter,
        bridge,
        budget=_budget(),
        capacity_admission_guard=guard,
    ).run(
        harness_run_id="harness-run:capacity-admission",
        assignment_id="assignment:capacity-admission",
        context_digest=canonical_digest({"capacity": "context"}),
        initial_messages=({"role": "user", "content": "finish"},),
    )
    return result, adapter, bridge, guard


class ProviderCapacityAdmissionTests(unittest.TestCase):
    def test_cc_switch_not_available_is_unknown_capacity_not_zero(self) -> None:
        payload = {
            "app": "codex",
            "providerId": "codex-official",
            "providerName": "OpenAI Official",
            "target": None,
            "status": "not_available",
            "available": False,
            "queriedAt": 1_792_145_492_371,
            "result": None,
            "error": None,
        }
        snapshot = snapshot_from_cc_switch_quota(
            payload,
            principal_ref="principal:linux-service",
            source_node_ref="runtime:linux-local",
        )
        self.assertEqual(snapshot.status, ProviderCapacityStatus.NOT_AVAILABLE)
        self.assertEqual(snapshot.windows, ())
        self.assertNotIn("result", snapshot.to_dict())
        self.assertNotIn("error", snapshot.to_dict())

        guard = SnapshotCapacityAdmissionGuard(
            snapshot=snapshot,
            reserve_basis_points=1_000,
            max_staleness_ms=60_000,
            expected_principal_ref="principal:linux-service",
            clock_ms=lambda: payload["queriedAt"],
        )
        decision = guard.check(_request(), request_token_upper_bound=None)
        self.assertEqual(decision.standing, CapacityAdmissionStanding.UNKNOWN)
        self.assertIn("UNKNOWN is not zero", decision.reason)

    def test_cc_switch_raw_result_is_not_retained_in_capacity_snapshot(self) -> None:
        payload = {
            "app": "codex",
            "providerId": "codex-official",
            "providerName": "OpenAI Official",
            "target": None,
            "status": "available",
            "available": True,
            "queriedAt": 10_000,
            "result": {"access_token": "do-not-retain", "quota": "provider-specific"},
            "error": None,
        }
        snapshot = snapshot_from_cc_switch_quota(
            json.dumps(payload),
            principal_ref="principal:windows-active-user",
            source_node_ref="runtime:windows-main",
            windows=(
                ProviderCapacityWindow(
                    kind="subscription-window",
                    remaining_basis_points=8_000,
                    resets_at_ms=20_000,
                ),
            ),
        )
        serialized = json.dumps(snapshot.to_dict(), sort_keys=True)
        self.assertNotIn("do-not-retain", serialized)
        self.assertNotIn("access_token", serialized)
        self.assertEqual(snapshot.status, ProviderCapacityStatus.AVAILABLE)

    def test_watermark_policy_admits_holds_and_preserves_unknown(self) -> None:
        healthy = ProviderCapacitySnapshot(
            source="cc-switch-cli:v5.11.x",
            observed_at_ms=10_000,
            principal_ref="principal:windows-active-user",
            source_node_ref="runtime:windows-main",
            app="codex",
            provider_id="codex-official",
            provider_name="OpenAI Official",
            status=ProviderCapacityStatus.AVAILABLE,
            windows=(
                ProviderCapacityWindow("five-hour", 6_000, 20_000),
                ProviderCapacityWindow("weekly", 4_000, 50_000),
            ),
        )
        guard = SnapshotCapacityAdmissionGuard(
            snapshot=healthy,
            reserve_basis_points=2_000,
            max_staleness_ms=5_000,
            expected_principal_ref="principal:windows-active-user",
            clock_ms=lambda: 12_000,
        )
        self.assertEqual(
            guard.check(_request(), request_token_upper_bound=1_000).standing,
            CapacityAdmissionStanding.ADMIT,
        )

        held = SnapshotCapacityAdmissionGuard(
            snapshot=ProviderCapacitySnapshot(
                source=healthy.source,
                observed_at_ms=healthy.observed_at_ms,
                principal_ref=healthy.principal_ref,
                source_node_ref=healthy.source_node_ref,
                app=healthy.app,
                provider_id=healthy.provider_id,
                provider_name=healthy.provider_name,
                status=healthy.status,
                windows=(ProviderCapacityWindow("five-hour", 1_000, 20_000),),
            ),
            reserve_basis_points=2_000,
            max_staleness_ms=5_000,
            expected_principal_ref="principal:windows-active-user",
            clock_ms=lambda: 12_000,
        )
        self.assertEqual(
            held.check(_request(), request_token_upper_bound=None).standing,
            CapacityAdmissionStanding.HOLD,
        )

        stale = SnapshotCapacityAdmissionGuard(
            snapshot=healthy,
            reserve_basis_points=2_000,
            max_staleness_ms=1_000,
            expected_principal_ref="principal:windows-active-user",
            clock_ms=lambda: 12_000,
        )
        self.assertEqual(
            stale.check(_request(), request_token_upper_bound=None).standing,
            CapacityAdmissionStanding.UNKNOWN,
        )

        wrong_principal = SnapshotCapacityAdmissionGuard(
            snapshot=healthy,
            reserve_basis_points=2_000,
            max_staleness_ms=5_000,
            expected_principal_ref="principal:linux-service",
            clock_ms=lambda: 12_000,
        )
        self.assertEqual(
            wrong_principal.check(_request(), request_token_upper_bound=None).standing,
            CapacityAdmissionStanding.UNKNOWN,
        )

    def test_hold_stops_before_durable_provider_begin_or_invoke(self) -> None:
        result, adapter, bridge, guard = _run(CapacityAdmissionStanding.HOLD)
        self.assertEqual(result.stop_code, RunStopCode.PROVIDER_UNAVAILABLE)
        self.assertEqual(adapter.requests, [])
        self.assertEqual(bridge.begins, 0)
        self.assertEqual(bridge.admits, 0)
        self.assertEqual(guard.calls, 1)
        checks = [
            event for event in result.trace.events if event.kind == "provider_capacity_checked"
        ]
        self.assertEqual(len(checks), 1)
        self.assertEqual(checks[0].payload["standing"], "hold")

    def test_unknown_stops_without_becoming_zero_or_dispatching(self) -> None:
        result, adapter, bridge, _ = _run(CapacityAdmissionStanding.UNKNOWN)
        self.assertEqual(result.stop_code, RunStopCode.PROVIDER_STATE_UNKNOWN)
        self.assertEqual(adapter.requests, [])
        self.assertEqual(bridge.begins, 0)
        self.assertEqual(bridge.admits, 0)

    def test_admit_preserves_existing_provider_lifecycle(self) -> None:
        result, adapter, bridge, _ = _run(CapacityAdmissionStanding.ADMIT)
        self.assertEqual(result.stop_code, RunStopCode.CANDIDATE_COMPLETED)
        self.assertEqual(len(adapter.requests), 1)
        self.assertEqual(bridge.begins, 1)
        self.assertEqual(bridge.admits, 1)
        self.assertEqual(bridge.completes, 1)


if __name__ == "__main__":
    unittest.main()
