#!/usr/bin/env python3
"""Real Python PG18 Store writer + pure production Provider V4 record constructors.

Creates *no real Provider effect*: every record explicitly belongs to this
scratch SourceCut. Exercises exactly the Provider CAS/Event reference edge that
A's PG Reader verifies and B's real read-only recovery consumer must interpret.
"""
from __future__ import annotations

from dataclasses import replace
import json
import os
import sys
from pathlib import Path

from anc_canonical import digest_bytes
from ordivon_harness.core_contracts import HarnessRunContract
from ordivon_harness.ordivon.continuity_records import (
    HarnessProviderCallRecordV3,
    build_provider_call_record_v4,
)
from ordivon_harness.postgres_store import PostgresHarnessStore
from ordivon_harness.protocol import (
    HarnessProviderCallFailureReceipt,
    HarnessProviderCallSource,
    HarnessProviderCallStatus,
)
from ordivon_harness.run_state import HarnessRunState


dsn = os.environ["HARNESS_RUST_TEST_PG_DSN"]
schema = os.environ["HARNESS_RUST_TEST_SCHEMA"]
path = Path(os.environ["HARNESS_RUST_TEST_FIXTURE_PATH"])
assert schema.startswith("hpg_rust_isolated_a_")

if len(sys.argv) > 1 and sys.argv[1] == "verify-native":
    fixture = json.loads(path.read_text(encoding="utf-8"))
    native = fixture["rust_native_provider"]
    with PostgresHarnessStore(dsn, schema=schema, initialize=False) as store:
        store.validate_run_history(native["runId"])
        run = store.load_run(native["runId"])
        assert run.revision == 4
        for entry in native["events"]:
            assert any(
                event.event_id == entry["eventId"]
                and event.event_kind == entry["eventKind"]
                for event in store.list_run_events(native["runId"])
            )
    print("PYTHON_VALIDATED_RUST_NATIVE_PROVIDER_UNKNOWN_JOURNAL_PASS")
    sys.exit(0)
all_cases = json.loads(path.read_text(encoding="utf-8"))
base_run = all_cases["no_tool"]["runId"]
cases = {}


def id_digest(label: str) -> str:
    return digest_bytes(f"provider-fixture:{label}".encode())


with PostgresHarnessStore(dsn, schema=schema, initialize=False) as store:
    raw_base = store.get_object(
        store.load_run(base_run).contract_object_digest,
        expected_kind="harness-run-contract",
    )
    base = HarnessRunContract.from_dict(raw_base)
    for scenario in (
        "claimed", "unknown", "completed_redacted", "cleared", "wrong_digest",
        "v3_legacy", "wrong_kind", "tampered_cas",
        "wrong_state", "extra_reference", "wrong_event_status",
    ):
        run_id = f"harness-run:test-pg-provider-{scenario}"
        contract = replace(
            base, harness_run_id=run_id,
            caller_run_ref=f"test-run-provider-{scenario}",
        )
        assert store.create_run(contract).value == "created"
        state = HarnessRunState(
            messages=(), observations=(), remaining_budget={"maxTurns": 2},
            requested_model_id=contract.requested_model_id,
            effective_model_id=None,
        )
        state_ref = store.put_object(
            state.to_dict(run_id), kind="harness-run-state"
        )
        source_ref = store.put_object(
            {"kind": "test-only-provider-source", "runId": run_id},
            kind="test-provider-source",
        )
        provider_call_id = f"provider-call:test-{scenario}"
        failure = HarnessProviderCallFailureReceipt(
            provider_call_id=provider_call_id,
            request_digest=id_digest(f"{scenario}:request"),
            provider_request_digest=id_digest(f"{scenario}:provider-request"),
            failure_code="provider_transport_failed",
            dispatch_safety="dispatch_ambiguous",
            detail="Synthetic test: physical effect was NEVER sent",
        )
        failure_ref = store.put_object(
            failure.to_dict(), kind="harness-provider-call-failure"
        )

        def append(status: HarnessProviderCallStatus, time: int, previous=None,
                   *, corrupt_digest=False, version3=False):
            record = build_provider_call_record_v4(
                provider_call_id=provider_call_id,
                harness_run_id=run_id,
                binding_digest=id_digest(f"{scenario}:binding"),
                source_kind=HarnessProviderCallSource.ASSIGNMENT,
                source_digest=source_ref.digest,
                source_object_digest=source_ref.digest,
                state_object_digest=state_ref.digest,
                turn_id=f"turn:test-{scenario}",
                turn_sequence=1,
                request_digest=failure.request_digest,
                request_object_digest=None,
                provider_request_digest=failure.provider_request_digest,
                adapter_id=contract.adapter_id,
                requested_model_id=contract.requested_model_id,
                holder_id=f"test-holder:{scenario}",
                generation=1,
                status=status,
                result_digest=(id_digest(f"{scenario}:redacted-result")
                               if status is HarnessProviderCallStatus.COMPLETED else None),
                result_object_digest=None,
                failure_digest=(failure.digest if status is HarnessProviderCallStatus.UNKNOWN else None),
                failure_object_digest=(failure_ref.digest if status is HarnessProviderCallStatus.UNKNOWN else None),
                previous_record_digest=(previous.digest if previous is not None else None),
                issued_at_ms=1001,
                expires_at_ms=50000,
                recorded_at_ms=time,
            )
            request_ref = None
            if version3:
                # The genuine historical V3 codec *requires* retained request
                # content; unlike V4 it cannot represent an absent request.
                request_ref = store.put_object(
                    {"kind": "synthetic-historical-request", "runId": run_id},
                    kind="agent-turn-request",
                )
                raw = record.to_dict()
                raw["schemaVersion"] = 3
                raw["requestObjectDigest"] = request_ref.digest
                record = HarnessProviderCallRecordV3.from_dict(raw)
            record_obj = store.put_object(
                record.to_dict(), kind="harness-provider-call-record"
            )
            name = {
                HarnessProviderCallStatus.CLAIMED: "claimed",
                HarnessProviderCallStatus.DISPATCHING: "dispatching",
                HarnessProviderCallStatus.UNKNOWN: "unknown",
                HarnessProviderCallStatus.COMPLETED: "completed",
            }[status]
            references = (record_obj, state_ref)
            if request_ref is not None:
                references += (request_ref,)
            if status is HarnessProviderCallStatus.UNKNOWN:
                references += (failure_ref,)
            if scenario == "extra_reference":
                extra_ref = store.put_object(
                    {"kind": "test-only-extra-provider-ref", "runId": run_id},
                    kind="unrelated-extra",
                )
                references += (extra_ref,)
            data = {
                "providerCallRecordDigest": (
                    id_digest("wrong-provider-head-digest") if corrupt_digest else record.digest
                ),
                "providerCallRecordObjectDigest": record_obj.digest,
                "stateObjectDigest": (
                    id_digest("wrong-state-not-linked")
                    if scenario == "wrong_state" else state_ref.digest
                ),
                "requestObjectDigest": (
                    request_ref.digest if request_ref is not None else None
                ),
                "resultObjectDigest": None,
                "failureObjectDigest": (
                    failure_ref.digest if status is HarnessProviderCallStatus.UNKNOWN else None
                ),
            }
            lease = store.acquire_run_lease(
                run_id, owner_id=f"test:lease:{scenario}:{time}", ttl_ms=30_000,
                now_ms=time, expected_run_revision=store.load_run(run_id).revision,
            )
            store.append_event(
                event_id=f"event:test-provider:{scenario}:{time}",
                harness_run_id=run_id,
                event_kind=(
                    "harness.provider-call-completed"
                    if scenario == "wrong_event_status"
                    else f"harness.provider-call-{name}"
                ),
                data=data, expected_revision=lease.run_revision,
                recorded_at_ms=time, lease=lease, lease_checked_at_ms=time,
                referenced_objects=references,
            )
            return record

        claimed = append(
            HarnessProviderCallStatus.CLAIMED, 1002,
            corrupt_digest=scenario == "wrong_digest",
            version3=scenario == "v3_legacy",
        )
        latest = claimed
        if scenario in {"unknown", "completed_redacted", "cleared"}:
            dispatched = append(
                HarnessProviderCallStatus.DISPATCHING, 1003, previous=claimed
            )
            latest = dispatched
            if scenario in {"unknown", "cleared"}:
                latest = append(
                    HarnessProviderCallStatus.UNKNOWN, 1004, previous=dispatched
                )
            else:
                latest = append(
                    HarnessProviderCallStatus.COMPLETED, 1004, previous=dispatched
                )
        if scenario == "cleared":
            lease = store.acquire_run_lease(
                run_id, owner_id=f"test:lease:{scenario}:pause", ttl_ms=30_000,
                now_ms=1005, expected_run_revision=store.load_run(run_id).revision,
            )
            store.append_event(
                event_id=f"event:test-provider:{scenario}:pause",
                harness_run_id=run_id, event_kind="harness.run-paused", data={},
                expected_revision=lease.run_revision,
                recorded_at_ms=1005, lease=lease, lease_checked_at_ms=1005,
            )
        store.validate_run_history(run_id)
        if scenario == "wrong_kind":
            store.connection.execute(
                "UPDATE objects SET kind=%s WHERE digest=%s",
                ("unrecognized-provider-record-kind", latest.digest),
            )
        if scenario == "tampered_cas":
            store.connection.execute(
                "UPDATE objects SET content=content || %s WHERE digest=%s",
                (b" ", latest.digest),
            )
        cases[scenario] = {
            "runId": run_id,
            "expectedStatus": None if scenario == "cleared" else latest.status.value,
            "expectedRecordDigest": latest.digest,
            "expectedResultDigest": latest.result_digest,
            "sourceVersion": 3 if scenario == "v3_legacy" else 4,
        }

    # The decisive cross-owner consumer: Python *only* authors legitimate
    # Contract/State/ProviderCallV4 CAS documents. Rust must acquire the
    # one native Lease, atomically commit all three Provider Event transitions,
    # then recover the UNKNOWN head from A's verified PG references.
    # No Python append_event and no external Provider transport occurs here.
    native_id = "harness-run:test-pg-native-provider-unknown"
    native = replace(
        base,
        harness_run_id=native_id,
        caller_run_ref="test-run-native-provider-unknown",
    )
    assert store.create_run(native).value == "created"
    native_state = HarnessRunState(
        messages=(), observations=(), remaining_budget={"maxTurns": 2},
        requested_model_id=native.requested_model_id,
        effective_model_id=None,
    )
    native_state_ref = store.put_object(
        native_state.to_dict(native_id), kind="harness-run-state"
    )
    native_source_ref = store.put_object(
        {"kind": "test-only-native-provider-source", "runId": native_id},
        kind="test-provider-source",
    )
    native_call_id = "provider-call:test-native-rust-writer"
    native_failure = HarnessProviderCallFailureReceipt(
        provider_call_id=native_call_id,
        request_digest=id_digest("native-provider-request"),
        provider_request_digest=id_digest("native-provider-transport-request"),
        failure_code="provider_transport_failed",
        dispatch_safety="dispatch_ambiguous",
        detail="Synthetic unknown; no Provider API was contacted",
    )
    native_failure_ref = store.put_object(
        native_failure.to_dict(), kind="harness-provider-call-failure"
    )
    native_events = []
    prior = None
    for status, when in (
        (HarnessProviderCallStatus.CLAIMED, 1010),
        (HarnessProviderCallStatus.DISPATCHING, 1011),
        (HarnessProviderCallStatus.UNKNOWN, 1012),
    ):
        record = build_provider_call_record_v4(
            provider_call_id=native_call_id,
            harness_run_id=native_id,
            binding_digest=id_digest("native-provider-binding"),
            source_kind=HarnessProviderCallSource.ASSIGNMENT,
            source_digest=native_source_ref.digest,
            source_object_digest=native_source_ref.digest,
            state_object_digest=native_state_ref.digest,
            turn_id="turn:test-native-provider",
            turn_sequence=1,
            request_digest=native_failure.request_digest,
            request_object_digest=None,
            provider_request_digest=native_failure.provider_request_digest,
            adapter_id=native.adapter_id,
            requested_model_id=native.requested_model_id,
            holder_id="test-holder:native-provider",
            generation=1,
            status=status,
            result_digest=None,
            result_object_digest=None,
            failure_digest=(
                native_failure.digest
                if status is HarnessProviderCallStatus.UNKNOWN else None
            ),
            failure_object_digest=(
                native_failure_ref.digest
                if status is HarnessProviderCallStatus.UNKNOWN else None
            ),
            previous_record_digest=prior.digest if prior is not None else None,
            issued_at_ms=1009,
            expires_at_ms=50000,
            recorded_at_ms=when,
        )
        record_ref = store.put_object(
            record.to_dict(), kind="harness-provider-call-record"
        )
        references = [record_ref, native_state_ref]
        if status is HarnessProviderCallStatus.UNKNOWN:
            references.append(native_failure_ref)
        data = {
            "providerCallRecordDigest": record.digest,
            "providerCallRecordObjectDigest": record_ref.digest,
            "stateObjectDigest": native_state_ref.digest,
            "requestObjectDigest": None,
            "resultObjectDigest": None,
            "failureObjectDigest": (
                native_failure_ref.digest
                if status is HarnessProviderCallStatus.UNKNOWN else None
            ),
        }
        native_events.append({
            "eventId": f"event:rust-native-provider-{status.value}",
            "eventKind": f"harness.provider-call-{status.value}",
            "recordedAtMs": when,
            "data": data,
            "references": [item.to_dict() for item in references],
        })
        prior = record
    all_cases["rust_native_provider"] = {
        "runId": native_id,
        "expectedRecordDigest": prior.digest,
        "events": native_events,
    }

all_cases["provider_records"] = cases
path.write_text(json.dumps(all_cases, ensure_ascii=False, sort_keys=True), encoding="utf-8")
print("PYTHON_PG_REAL_PROVIDER_V4_EVENT_REFERENCES_READY", len(cases))
