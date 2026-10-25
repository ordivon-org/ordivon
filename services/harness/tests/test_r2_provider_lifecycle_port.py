from __future__ import annotations

import unittest

from anc_canonical import canonical_digest

from ordivon_harness.ordivon.control import CancellationToken, ExecutionControl, RunDeadline
from ordivon_harness.ordivon.model import (
    AgentRunConclusion,
    AgentTurnAdapterError,
    AgentTurnFailureCode,
    AgentTurnRequest,
    AgentTurnResult,
    ScriptedTurnAdapter,
)
from ordivon_harness.ordivon.provider_lifecycle import (
    ProviderCallLifecycle,
    ProviderLifecycleError,
)


def request() -> AgentTurnRequest:
    return AgentTurnRequest(
        harness_run_id="harness-run:r2-provider",
        turn_id="turn:r2-provider:1",
        sequence=1,
        assignment_id="assignment:r2-provider",
        context_digest=canonical_digest({"r2": "context"}),
        tool_catalog_digest=canonical_digest({"r2": "tools"}),
        messages=({"role": "user", "content": "provider"},),
        tools=(),
        remaining_budget={"modelCalls": 1, "toolCalls": 0},
    )


class IdentityAdapter:
    adapter_id = ScriptedTurnAdapter.adapter_id
    model_id = ScriptedTurnAdapter.model_id

    @staticmethod
    def provider_request_digest(req: AgentTurnRequest) -> str:
        return canonical_digest(
            {
                "adapterId": IdentityAdapter.adapter_id,
                "modelId": IdentityAdapter.model_id,
                "dispatchDigest": req.dispatch_digest,
            }
        )


class R2ProviderLifecyclePortTests(unittest.TestCase):
    def test_deadline_rejects_non_integer_or_non_positive_duration_before_clock(self) -> None:
        observed = []
        def clock() -> int:
            observed.append("clock_read")
            return 100

        for bad in (True, False, 0, -1, 1.0, 3.0, "3", float("nan"), float("inf")):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    RunDeadline.after(bad, monotonic_ms=clock)
        self.assertEqual(observed, [])
        self.assertEqual(RunDeadline.after(3, monotonic_ms=clock).expires_at_ms, 103)

    def test_direct_deadline_construction_cannot_bypass_timestamp_type(self) -> None:
        def clock() -> int:
            return 0

        for bad in (True, False, 1.0, 2.0, "1", float("nan"), float("inf")):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError, "expiry must be an exact integer"):
                    RunDeadline(bad, clock)
        with self.assertRaisesRegex(ValueError, "clock must be callable"):
            RunDeadline(100, None)
        # Absolute deadlines may already be expired, unlike relative durations.
        self.assertTrue(RunDeadline(0, clock).expired)
        self.assertFalse(RunDeadline(1, clock).expired)

    def test_provider_timeout_rejects_nonfinite_or_boolean_before_effect(self) -> None:
        control = ExecutionControl(
            CancellationToken(),
            RunDeadline.after(10000, monotonic_ms=lambda: 0),
        )
        for bad in (True, False, 0, -1, float("nan"), float("inf"), float("-inf"), "1"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    control.clamp_timeout_seconds(bad)
        self.assertEqual(control.clamp_timeout_seconds(2.5), 2.5)
        self.assertEqual(control.clamp_timeout_seconds(20), 10.0)

    def test_plain_tool_surface_has_no_durable_provider_authority(self) -> None:
        class PlainBridge:
            pass

        lifecycle = ProviderCallLifecycle(PlainBridge(), IdentityAdapter())
        value = request()
        self.assertFalse(lifecycle.durable)
        self.assertIsNone(lifecycle.request_digest(value))
        self.assertIsNone(lifecycle.begin(value, provider_request_digest=None))
        control = ExecutionControl(
            CancellationToken(),
            RunDeadline.after(1000, monotonic_ms=lambda: 0),
        )
        self.assertTrue(lifecycle.admit(value, control=control))
        lifecycle.retry(value)

    def test_durable_port_configures_and_forwards_exact_lifecycle(self) -> None:
        events = []
        replay = AgentTurnResult(
            model_call_id="model-call:r2-replay",
            model_id=IdentityAdapter.model_id,
            content="replay",
            tool_calls=(),
            conclusion=AgentRunConclusion(
                status="candidate_completed",
                summary="R2 Provider lifecycle replay fixture.",
            ),
            usage={},
            finish_reason="stop",
            raw_response_digest=canonical_digest({"r2": "raw"}),
        )

        class DurableBridge:
            durable_provider_calls_enabled = True

            def configure_provider_call(self, *, adapter_id, requested_model_id):
                events.append(("configure", adapter_id, requested_model_id))

            def begin_provider_call(self, req, *, provider_request_digest):
                events.append(("begin", req.dispatch_digest, provider_request_digest))
                return replay

            def admit_provider_call(self, req, *, control):
                events.append(("admit", req.dispatch_digest, control.stop_requested))
                return True

            def fail_provider_call(self, req, error, *, unknown):
                events.append(("fail", req.dispatch_digest, error.failure_code.value, unknown))

            def retry_provider_call(self, req):
                events.append(("retry", req.dispatch_digest))

            def complete_provider_call(self, req, result):
                events.append(("complete", req.dispatch_digest, result.digest))

        bridge = DurableBridge()
        lifecycle = ProviderCallLifecycle(bridge, IdentityAdapter())
        value = request()
        digest = lifecycle.request_digest(value)
        self.assertEqual(digest, IdentityAdapter.provider_request_digest(value))
        self.assertIs(
            lifecycle.begin(value, provider_request_digest=digest), replay
        )
        control = ExecutionControl(
            CancellationToken(),
            RunDeadline.after(1000, monotonic_ms=lambda: 0),
        )
        self.assertTrue(lifecycle.admit(value, control=control))
        error = AgentTurnAdapterError(
            "fixture", failure_code=AgentTurnFailureCode.FAILED
        )
        lifecycle.fail(value, error, unknown=False)
        lifecycle.retry(value)
        lifecycle.complete(value, replay)
        self.assertEqual(events[0], ("configure", IdentityAdapter.adapter_id, IdentityAdapter.model_id))
        self.assertEqual([event[0] for event in events[1:]], ["begin", "admit", "fail", "retry", "complete"])

    def test_durable_port_rejects_missing_or_invalid_provider_identity(self) -> None:
        class DurableBridge:
            durable_provider_calls_enabled = True

            def begin_provider_call(self, req, *, provider_request_digest):
                return None

        class MissingIdentityAdapter:
            adapter_id = "adapter:r2-missing"
            model_id = "model:r2-missing"

        class InvalidIdentityAdapter(MissingIdentityAdapter):
            @staticmethod
            def provider_request_digest(req):
                return "not-a-digest"

        with self.assertRaisesRegex(ProviderLifecycleError, "omitted provider_request_digest"):
            ProviderCallLifecycle(DurableBridge(), MissingIdentityAdapter()).request_digest(request())
        with self.assertRaisesRegex(ProviderLifecycleError, "sha256:<64 lowercase hex>"):
            ProviderCallLifecycle(DurableBridge(), InvalidIdentityAdapter()).request_digest(request())

    def test_durable_admission_rejects_truthy_or_falsey_non_boolean_receipts(self) -> None:
        class DurableBridge:
            durable_provider_calls_enabled = True

            def __init__(self, value):
                self.value = value
                self.calls = 0

            def begin_provider_call(self, req, *, provider_request_digest):
                return None

            def admit_provider_call(self, req, *, control):
                self.calls += 1
                return self.value

        control = ExecutionControl(
            CancellationToken(),
            RunDeadline.after(1000, monotonic_ms=lambda: 0),
        )
        for malformed in ("ALLOW", "DENY", 1, 0, {}, [], None):
            with self.subTest(malformed=malformed):
                bridge = DurableBridge(malformed)
                lifecycle = ProviderCallLifecycle(bridge, IdentityAdapter())
                with self.assertRaisesRegex(
                    ProviderLifecycleError, "exact boolean"
                ):
                    lifecycle.admit(request(), control=control)
                self.assertEqual(bridge.calls, 1)

        for admitted in (True, False):
            with self.subTest(admitted=admitted):
                lifecycle = ProviderCallLifecycle(DurableBridge(admitted), IdentityAdapter())
                self.assertIs(lifecycle.admit(request(), control=control), admitted)

    def test_durable_port_requires_dispatch_admission(self) -> None:
        class BeginOnlyBridge:
            durable_provider_calls_enabled = True

            def begin_provider_call(self, req, *, provider_request_digest):
                return None

        lifecycle = ProviderCallLifecycle(BeginOnlyBridge(), IdentityAdapter())
        control = ExecutionControl(
            CancellationToken(),
            RunDeadline.after(1000, monotonic_ms=lambda: 0),
        )
        with self.assertRaisesRegex(ProviderLifecycleError, "omitted dispatch admission"):
            lifecycle.admit(request(), control=control)


if __name__ == "__main__":
    unittest.main()
