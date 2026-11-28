from __future__ import annotations

import unittest

from anc_canonical import canonical_digest

from ordivon_harness.protocol import (
    HarnessDispatchFence,
    HarnessProtocolError,
    HarnessProviderCallFailureReceipt,
    HarnessRecoveryConsequence,
    HarnessRunPauseReason,
    HarnessRunSnapshot,
    HarnessToolStepIntent,
    HarnessToolStepReceipt,
    HarnessToolStepStatus,
)
from tests.test_provider_call_protocol import _initial_record


def _digest(label: str) -> str:
    return canonical_digest({"wire-version-fixture": label})


def _carriers() -> tuple[object, ...]:
    return (
        HarnessProviderCallFailureReceipt(
            provider_call_id="provider-call:wire-version",
            request_digest=_digest("request"),
            provider_request_digest=_digest("provider-request"),
            failure_code="provider_transport_failed",
            dispatch_safety="pre_dispatch_safe",
            detail="wire-version fixture",
        ),
        _initial_record(),
        HarnessToolStepIntent(
            intent_id="harness-tool-step-intent:wire-version",
            harness_run_id="harness-run:wire-version",
            assignment_id="assignment:wire-version",
            assignment_generation=1,
            assignment_digest=_digest("assignment"),
            turn_id="turn:wire-version",
            tool_call_id="tool-call:wire-version",
            tool_name="exec_command",
            tool_call_digest=_digest("tool-call"),
            runtime_operation="workspace.exec",
            runtime_arguments_digest=_digest("runtime-arguments"),
            client_request_id="request:wire-version",
            recovery_consequence=HarnessRecoveryConsequence.WORKSPACE_CHANGE_POSSIBLE,
            created_at_ms=1,
        ),
        HarnessToolStepReceipt(
            receipt_id="harness-tool-step-receipt:wire-version",
            intent_digest=_digest("intent"),
            harness_run_id="harness-run:wire-version",
            tool_call_id="tool-call:wire-version",
            status=HarnessToolStepStatus.OBSERVED,
            runtime_job_ref="runtime-job:wire-version",
            observation_digest=_digest("observation"),
            reconciled=False,
            created_at_ms=2,
        ),
        HarnessDispatchFence(
            fence_id="harness-dispatch-fence:wire-version",
            task_id="task:wire-version",
            task_revision=1,
            harness_run_id="harness-run:wire-version",
            assignment_id="assignment:wire-version",
            assignment_generation=1,
            assignment_digest=_digest("assignment"),
            intent_digest=_digest("intent"),
            runtime_operation="workspace.exec",
            client_request_id="request:wire-version",
            issued_at_ms=1,
            expires_at_ms=100,
        ),
        HarnessRunSnapshot(
            snapshot_id="harness-run-snapshot:wire-version",
            harness_run_id="harness-run:wire-version",
            assignment_id="assignment:wire-version",
            assignment_generation=1,
            assignment_digest=_digest("assignment"),
            sequence=1,
            tool_catalog_digest=_digest("tools"),
            requested_model_id="model:wire-version",
            effective_model_id=None,
            messages_digest=_digest("messages"),
            observation_digests=(),
            active_tool_step_intent_digests=(_digest("intent"),),
            remaining_budget={},
            pause_reason=HarnessRunPauseReason.EFFECT_DISPATCH_PENDING,
            created_at_ms=3,
        ),
    )


class ProtocolWireSchemaVersionTests(unittest.TestCase):
    def test_v1_decoders_reject_python_numeric_aliases(self) -> None:
        for value in _carriers():
            decoder = type(value).from_dict
            encoded = value.to_dict()
            with self.subTest(carrier=type(value).__name__, schema_version=1):
                self.assertEqual(decoder(encoded), value)
            for invalid in (1.0, True):
                malformed = dict(encoded)
                malformed["schemaVersion"] = invalid
                with self.subTest(
                    carrier=type(value).__name__,
                    schema_version=repr(invalid),
                ):
                    with self.assertRaisesRegex(
                        HarnessProtocolError,
                        "version or kind is invalid",
                    ):
                        decoder(malformed)


if __name__ == "__main__":
    unittest.main()
