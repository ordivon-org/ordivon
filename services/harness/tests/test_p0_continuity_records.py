from __future__ import annotations

import json
from pathlib import Path
import unittest

import ordivon_harness.ordivon as ordivon_package
import ordivon_harness.ordivon.continuity_records as continuity_records

from ordivon_harness.ordivon.continuity_records import (
    HarnessDispatchFenceV2,
    HarnessProviderCallRecordV3,
    HarnessProviderCallRecordV4,
)
from ordivon_harness.ordivon.run_store_port import (
    HarnessDispatchFenceView,
    HarnessProviderCallRecordView,
    HarnessRunStoreBinding,
)
from ordivon_harness.protocol import (
    HarnessDispatchFence,
    HarnessProviderCallRecord,
    HarnessProviderCallSource,
    HarnessProviderCallStatus,
)

DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64
DIGEST_C = "sha256:" + "c" * 64
DIGEST_D = "sha256:" + "d" * 64
DIGEST_E = "sha256:" + "e" * 64


def binding() -> HarnessRunStoreBinding:
    return HarnessRunStoreBinding(
        harness_run_id="harness-run:p0-v2-001",
        assignment_id="assignment:p0-v2-001",
        assignment_generation=1,
        assignment_digest=DIGEST_A,
    )


def provider_v1() -> HarnessProviderCallRecord:
    return HarnessProviderCallRecord(
        record_id="harness-provider-call-record:p0-v1-001",
        provider_call_id="provider-call:p0-v1-001",
        task_id="task:p0-v1-001",
        harness_run_id="harness-run:p0-v1-001",
        assignment_id="assignment:p0-v1-001",
        assignment_generation=1,
        assignment_digest=DIGEST_A,
        source_kind=HarnessProviderCallSource.ASSIGNMENT,
        source_digest=DIGEST_B,
        source_object_digest=DIGEST_C,
        state_object_digest=DIGEST_D,
        turn_id="turn:p0-v1-001",
        turn_sequence=1,
        request_digest=DIGEST_A,
        provider_request_digest=DIGEST_B,
        adapter_id="adapter:test",
        requested_model_id="model:test",
        holder_id="worker:test",
        claim_generation=1,
        status=HarnessProviderCallStatus.CLAIMED,
        result_digest=None,
        result_object_digest=None,
        failure_digest=None,
        failure_object_digest=None,
        previous_record_digest=None,
        issued_at_ms=1_000,
        expires_at_ms=2_000,
        recorded_at_ms=1_000,
    )


def provider_v3() -> HarnessProviderCallRecordV3:
    return HarnessProviderCallRecordV3(
        record_id="harness-provider-call-record:p0-v3-001",
        provider_call_id="provider-call:p0-v3-001",
        harness_run_id=binding().harness_run_id,
        binding_digest=binding().digest,
        source_kind=HarnessProviderCallSource.ASSIGNMENT,
        source_digest=DIGEST_B,
        source_object_digest=DIGEST_C,
        state_object_digest=DIGEST_D,
        turn_id="turn:p0-v3-001",
        turn_sequence=1,
        request_digest=DIGEST_A,
        provider_request_digest=DIGEST_B,
        adapter_id="adapter:test",
        requested_model_id="model:test",
        holder_id="worker:test",
        claim_generation=1,
        status=HarnessProviderCallStatus.CLAIMED,
        result_digest=None,
        result_object_digest=None,
        failure_digest=None,
        failure_object_digest=None,
        previous_record_digest=None,
        issued_at_ms=1_000,
        expires_at_ms=2_000,
        recorded_at_ms=1_000,
        request_object_digest=DIGEST_E,
    )


class ContinuityRecordTests(unittest.TestCase):
    def test_binding_digest_is_deterministic(self) -> None:
        value = binding()
        self.assertEqual(value.digest, binding().digest)
        self.assertEqual(value.to_dict()["kind"], "ordivon.harness-run-store-binding")

    def test_compatibility_facades_are_retired_from_current_surfaces(self) -> None:
        self.assertFalse(hasattr(continuity_records, "HarnessProviderCallRecordV2"))
        self.assertEqual(ordivon_package.__all__, [])
        self.assertFalse(hasattr(ordivon_package, "HarnessProviderCallRecordV2"))
        self.assertFalse(hasattr(ordivon_package, "HarnessDispatchFenceV2"))

    def test_frozen_s0_provider_v3_remains_byte_semantically_readable(self) -> None:
        fixture = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "provider-call-v3-s0-frozen.json"
        )
        payload = json.loads(fixture.read_text(encoding="utf-8"))
        value = HarnessProviderCallRecordV3.from_dict(payload)
        self.assertEqual(value.to_dict(), payload)
        self.assertEqual(
            value.digest,
            "sha256:4220370980de94fcf03a4f91065a3f619f43e82bfe401c027a26d5f2a095931b",
        )
        self.assertEqual(value.status, HarnessProviderCallStatus.DISPATCHING)

    def test_provider_v3_round_trip_has_no_host_task_fields(self) -> None:
        value = provider_v3()
        encoded = value.to_dict()
        self.assertEqual(encoded["schemaVersion"], 3)
        self.assertNotIn("taskId", encoded)
        self.assertNotIn("taskRevision", encoded)
        self.assertEqual(encoded["bindingDigest"], binding().digest)
        self.assertEqual(HarnessProviderCallRecordV3.from_dict(encoded), value)
        self.assertEqual(HarnessProviderCallRecordV3.from_dict(encoded).digest, value.digest)

    def test_provider_v4_round_trip_allows_digest_only_completed_result(self) -> None:
        value = HarnessProviderCallRecordV4(
            record_id="harness-provider-call-record:p0-v4-001",
            provider_call_id="provider-call:p0-v4-001",
            harness_run_id=binding().harness_run_id,
            binding_digest=binding().digest,
            source_kind=HarnessProviderCallSource.ASSIGNMENT,
            source_digest=DIGEST_B,
            source_object_digest=DIGEST_C,
            state_object_digest=DIGEST_D,
            turn_id="turn:p0-v4-001",
            turn_sequence=1,
            request_digest=DIGEST_A,
            provider_request_digest=DIGEST_B,
            adapter_id="adapter:test",
            requested_model_id="model:test",
            holder_id="worker:test",
            claim_generation=1,
            status=HarnessProviderCallStatus.COMPLETED,
            result_digest=DIGEST_E,
            result_object_digest=None,
            failure_digest=None,
            failure_object_digest=None,
            previous_record_digest=DIGEST_A,
            issued_at_ms=1_000,
            expires_at_ms=2_000,
            recorded_at_ms=1_100,
            request_object_digest=None,
        )
        encoded = value.to_dict()
        self.assertEqual(encoded["schemaVersion"], 4)
        self.assertEqual(encoded["resultDigest"], DIGEST_E)
        self.assertIsNone(encoded["resultObjectDigest"])
        self.assertIsNone(encoded["requestObjectDigest"])
        self.assertEqual(HarnessProviderCallRecordV4.from_dict(encoded), value)
        strict_v3 = provider_v3().to_dict()
        strict_v3["status"] = HarnessProviderCallStatus.COMPLETED.value
        strict_v3["previousRecordDigest"] = DIGEST_A
        strict_v3["resultDigest"] = DIGEST_E
        with self.assertRaisesRegex(ValueError, "both result references"):
            HarnessProviderCallRecordV3.from_dict(strict_v3)

    def test_provider_v1_codec_remains_exact(self) -> None:
        value = provider_v1()
        encoded = value.to_dict()
        self.assertEqual(encoded["schemaVersion"], 1)
        self.assertEqual(encoded["taskId"], "task:p0-v1-001")
        self.assertEqual(HarnessProviderCallRecord.from_dict(encoded), value)
        self.assertEqual(HarnessProviderCallRecord.from_dict(encoded).digest, value.digest)

    def test_retained_provider_generations_satisfy_execution_view(self) -> None:
        self.assertIsInstance(provider_v1(), HarnessProviderCallRecordView)
        self.assertIsInstance(provider_v3(), HarnessProviderCallRecordView)

    def test_fence_v2_round_trip_uses_run_revision(self) -> None:
        value = HarnessDispatchFenceV2(
            fence_id="harness-dispatch-fence:p0-v2-001",
            harness_run_id=binding().harness_run_id,
            run_revision=7,
            binding_digest=binding().digest,
            intent_digest=DIGEST_E,
            runtime_operation="workspace.exec",
            client_request_id="request:p0-v2-001",
            issued_at_ms=1_000,
            expires_at_ms=2_000,
        )
        encoded = value.to_dict()
        self.assertEqual(encoded["schemaVersion"], 2)
        self.assertEqual(value.authority_namespace, "ordivon.harness")
        self.assertEqual(value.authority_type, "dispatch_fence")
        self.assertEqual(value.authority_generation, 7)
        self.assertNotIn("taskId", encoded)
        self.assertNotIn("taskRevision", encoded)
        self.assertEqual(HarnessDispatchFenceV2.from_dict(encoded), value)
        self.assertIsInstance(value, HarnessDispatchFenceView)

    def test_fence_v1_keeps_bytes_but_exposes_structural_generation(self) -> None:
        value = HarnessDispatchFence(
            fence_id="harness-dispatch-fence:p0-v1-001",
            task_id="task:p0-v1-001",
            task_revision=9,
            harness_run_id="harness-run:p0-v1-001",
            assignment_id="assignment:p0-v1-001",
            assignment_generation=1,
            assignment_digest=DIGEST_A,
            intent_digest=DIGEST_E,
            runtime_operation="workspace.exec",
            client_request_id="request:p0-v1-001",
            issued_at_ms=1_000,
            expires_at_ms=2_000,
        )
        encoded = value.to_dict()
        self.assertEqual(encoded["schemaVersion"], 1)
        self.assertEqual(encoded["taskRevision"], 9)
        self.assertEqual(value.authority_namespace, "ordivon.host")
        self.assertEqual(value.authority_type, "dispatch_fence")
        self.assertEqual(value.authority_generation, 9)
        self.assertEqual(HarnessDispatchFence.from_dict(encoded), value)
        self.assertIsInstance(value, HarnessDispatchFenceView)

    def test_v3_decoder_rejects_host_field_injection(self) -> None:
        provider = provider_v3().to_dict()
        provider["taskId"] = "task:injected"
        with self.assertRaisesRegex(ValueError, "fields differ"):
            HarnessProviderCallRecordV3.from_dict(provider)

        fence = HarnessDispatchFenceV2(
            fence_id="harness-dispatch-fence:p0-v2-002",
            harness_run_id=binding().harness_run_id,
            run_revision=2,
            binding_digest=binding().digest,
            intent_digest=DIGEST_E,
            runtime_operation="workspace.exec",
            client_request_id="request:p0-v2-002",
            issued_at_ms=1_000,
            expires_at_ms=2_000,
        ).to_dict()
        fence["taskRevision"] = 2
        with self.assertRaisesRegex(ValueError, "fields differ"):
            HarnessDispatchFenceV2.from_dict(fence)


if __name__ == "__main__":
    unittest.main()
