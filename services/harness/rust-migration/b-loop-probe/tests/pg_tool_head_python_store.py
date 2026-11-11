#!/usr/bin/env python3
"""Production Python Tool Intent/Fence/Receipt -> one disposable PG18.
All Tool events are synthetic. NO Runtime, Provider HTTP or physical effects.
"""

from __future__ import annotations
from dataclasses import replace
import json
import os
from pathlib import Path

from anc_canonical import canonical_digest
from ordivon_harness.core_contracts import HarnessPrivacyPolicy, HarnessRunContract
from ordivon_harness.ordivon.run_continuity import EventSourcedRunContinuity
from ordivon_harness.postgres_store import PostgresHarnessStore
from ordivon_harness.protocol import (
    HarnessRecoveryConsequence,
    HarnessToolStepIntent,
    HarnessToolStepReceipt,
    HarnessToolStepStatus,
)
from ordivon_harness.run_state import HarnessRunState

dsn = os.environ["HARNESS_RUST_TEST_PG_DSN"]
schema = os.environ["HARNESS_RUST_TEST_SCHEMA"]
path = Path(os.environ["HARNESS_RUST_TEST_FIXTURE_PATH"])
assert schema.startswith("hpg_rust_isolated_a_")
manifest = json.loads(path.read_text(encoding="utf-8"))
base_run = manifest["no_tool"]["runId"]
cases = {}


class Clock:
    def __init__(self, t=1000):
        self.t = t

    def __call__(self):
        return self.t

    def advance(self, n=1):
        self.t += n


with PostgresHarnessStore(dsn, schema=schema, initialize=False) as store:
    raw = store.get_object(
        store.load_run(base_run).contract_object_digest,
        expected_kind="harness-run-contract",
    )
    base = HarnessRunContract.from_dict(raw)

    for label in (
        "prepared",
        "unknown_redacted",
        "stale_revision",
        "bad_fence_digest",
        "extra_reference",
        "receipt_event_mismatch",
        "bad_snapshot_binding",
        "bad_snapshot_budget",
        "generic_no_intent",
        "cross_run",
    ):
        run_id = f"harness-run:tool-head-source-{label}"
        contract = replace(
            base,
            harness_run_id=run_id,
            caller_run_ref=f"tool-source-{label}",
            privacy=HarnessPrivacyPolicy(
                content_policy="bounded-private-content",
                allow_model_content=True,
                allow_tool_content=False,
            ),
        )
        assert store.create_run(contract).value == "created"
        clock = Clock()
        continuity = EventSourcedRunContinuity(store, contract, clock_ms=clock)
        continuity.bind_state(
            HarnessRunState(
                messages=(),
                observations=(),
                remaining_budget={"maxTurns": 2},
                requested_model_id=contract.requested_model_id,
                effective_model_id=None,
            )
        )
        binding = continuity.binding
        intent = HarnessToolStepIntent(
            intent_id=f"harness-tool-step-intent:source-{label}",
            harness_run_id=run_id,
            assignment_id=binding.assignment_id,
            assignment_generation=binding.assignment_generation,
            assignment_digest=binding.assignment_digest,
            turn_id=f"turn:source-{label}",
            tool_call_id=f"tool-call:source-{label}",
            tool_name="workspace.read",
            tool_call_digest=canonical_digest({"call": label}),
            runtime_operation="workspace.read",
            runtime_arguments_digest=canonical_digest({"relativePath": "README.md"}),
            client_request_id=f"runtime-client:source-{label}",
            recovery_consequence=HarnessRecoveryConsequence.OBSERVATION_ONLY,
            created_at_ms=clock(),
        )
        if label in {
            "prepared",
            "unknown_redacted",
            "stale_revision",
            "bad_fence_digest",
            "extra_reference",
            "receipt_event_mismatch",
            "bad_snapshot_binding",
            "bad_snapshot_budget",
        }:
            continuity.prepare_tool_step(intent)
            current = continuity.load_current_tool_step()
            assert current.intent == intent
            assert current.fence is not None
            continuity.assert_dispatch_fence_current(current.fence)
            if label in {"unknown_redacted", "receipt_event_mismatch"}:
                observation = {
                    "schemaVersion": 1,
                    "kind": "test-only-tool-observation",
                    "outcome": "unconfirmed",
                }
                clock.advance()
                receipt = HarnessToolStepReceipt(
                    receipt_id=f"harness-tool-step-receipt:source-{label}",
                    intent_digest=intent.digest,
                    harness_run_id=run_id,
                    tool_call_id=intent.tool_call_id,
                    status=HarnessToolStepStatus.UNKNOWN,
                    runtime_job_ref=None,
                    observation_digest=canonical_digest(observation),
                    reconciled=False,
                    created_at_ms=clock(),
                )
                continuity.record_tool_step_receipt(receipt, observation)
                current = continuity.load_current_tool_step()
                assert current.receipt == receipt
                assert current.observation is None, "Private Tool observation must remain redacted"
                try:
                    continuity.assert_dispatch_fence_current(current.fence)
                except Exception:
                    pass
                else:
                    raise AssertionError("Receipt must invalidate the prepared Run revision fence")
            if label == "stale_revision":
                from ordivon_harness.store import HarnessEventWrite

                lease = store.acquire_run_lease(
                    run_id,
                    owner_id="test:stale-prepared",
                    ttl_ms=30_000,
                    now_ms=clock(),
                    expected_run_revision=store.load_run(run_id).revision,
                )
                clock.advance()
                store.append_events(
                    harness_run_id=run_id,
                    expected_revision=lease.run_revision,
                    lease=lease,
                    lease_checked_at_ms=clock(),
                    events=(
                        HarnessEventWrite(
                            event_id="event:source-tool-stale-trace",
                            event_kind="harness.trace-recorded",
                            data={"test": "not a new Tool Head"},
                            recorded_at_ms=clock(),
                        ),
                    ),
                )
                try:
                    continuity.assert_dispatch_fence_current(current.fence)
                except Exception:
                    pass
                else:
                    raise AssertionError("Any new Run revision must invalidate old dispatch fence")
            if label in {"bad_snapshot_binding", "bad_snapshot_budget"}:
                # A complete, digest-valid generic Journal may still link
                # Python-invalid Snapshot data, including hidden fields.
                # CAS SHA, typed Fence and Run revision remain consistent;
                # recovering this as a ready Tool is not source-qualified.
                original = store.list_run_events(run_id)[-1]
                old_snapshot = original.data["snapshotObjectDigest"]
                raw_snapshot = store.get_object(old_snapshot, expected_kind="harness-run-snapshot")
                assert raw_snapshot["activeToolStepIntentDigests"] == [intent.digest]
                forged_snapshot = dict(raw_snapshot)
                if label == "bad_snapshot_binding":
                    forged_snapshot["activeToolStepIntentDigests"] = []
                else:
                    from ordivon_harness.protocol import HarnessRunSnapshot

                    forged_snapshot["remainingBudget"] = []
                    try:
                        HarnessRunSnapshot.from_dict(forged_snapshot)
                    except TypeError, ValueError:
                        pass
                    else:
                        raise AssertionError("Python accepts non-object Snapshot budget")
                snapshot_ref = store.put_object(forged_snapshot, kind="harness-run-snapshot")
                forged_data = dict(original.data)
                forged_data["snapshotDigest"] = snapshot_ref.digest
                forged_data["snapshotObjectDigest"] = snapshot_ref.digest
                new_payload = store.put_object(
                    {
                        "schemaVersion": 1,
                        "kind": "ordivon.harness-run-event-payload",
                        "eventKind": original.event_kind,
                        "data": forged_data,
                    },
                    kind="ordivon.harness-run-event-payload",
                )
                store.connection.execute(
                    "UPDATE run_events SET payload_digest=%s WHERE event_id=%s",
                    (new_payload.digest, original.event_id),
                )
                store.connection.execute(
                    "UPDATE run_object_refs SET digest=%s WHERE event_id=%s AND role='payload'",
                    (new_payload.digest, original.event_id),
                )
                store.connection.execute(
                    "UPDATE run_object_refs SET digest=%s "
                    "WHERE event_id=%s AND role='reference' AND digest=%s",
                    (snapshot_ref.digest, original.event_id, old_snapshot),
                )
            if label == "bad_fence_digest":
                from ordivon_harness.store import HarnessEventWrite

                prior = store.list_run_events(run_id)[-1]
                data = dict(prior.data)
                data["dispatchFenceDigest"] = canonical_digest({"forged": "fence"})
                refs = tuple(
                    store.inspect_object(value)
                    for key, value in prior.data.items()
                    if key.endswith("ObjectDigest") and isinstance(value, str)
                )
                lease = store.acquire_run_lease(
                    run_id,
                    owner_id=f"test:{label}",
                    ttl_ms=30000,
                    now_ms=clock(),
                    expected_run_revision=store.load_run(run_id).revision,
                )
                clock.advance()
                store.append_events(
                    harness_run_id=run_id,
                    expected_revision=lease.run_revision,
                    lease=lease,
                    lease_checked_at_ms=clock(),
                    events=(
                        HarnessEventWrite(
                            event_id=f"event:tool-falsify-{label}",
                            event_kind="harness.tool-step-prepared",
                            data=data,
                            recorded_at_ms=clock(),
                            referenced_objects=refs,
                        ),
                    ),
                )
            if label == "extra_reference":
                original = store.list_run_events(run_id)[-1]
                unrelated = store.put_object(
                    {"kind": "tool-extra-reference", "source": label},
                    kind="test-unrelated-object",
                )
                # Valid CAS and valid generic Journal schema, but the Tool
                # semantic edge set is not exactly source-authoritative.
                store.connection.execute(
                    "INSERT INTO run_object_refs "
                    "(harness_run_id,event_id,digest,role) VALUES(%s,%s,%s,%s)",
                    (run_id, original.event_id, unrelated.digest, "reference"),
                )
            if label == "receipt_event_mismatch":
                from ordivon_harness.store import HarnessEventWrite

                prior = store.list_run_events(run_id)[-1]
                refs = tuple(
                    store.inspect_object(value)
                    for key, value in prior.data.items()
                    if key.endswith("ObjectDigest") and isinstance(value, str)
                )
                lease = store.acquire_run_lease(
                    run_id,
                    owner_id=f"test:{label}",
                    ttl_ms=30000,
                    now_ms=clock(),
                    expected_run_revision=store.load_run(run_id).revision,
                )
                clock.advance()
                store.append_events(
                    harness_run_id=run_id,
                    expected_revision=lease.run_revision,
                    lease=lease,
                    lease_checked_at_ms=clock(),
                    events=(
                        HarnessEventWrite(
                            event_id=f"event:tool-falsify-{label}",
                            event_kind="harness.tool-step-recorded",
                            data=prior.data,
                            recorded_at_ms=clock(),
                            referenced_objects=refs,
                        ),
                    ),
                )
            store.validate_run_history(run_id)
            if label in {
                "bad_fence_digest",
                "extra_reference",
                "receipt_event_mismatch",
                "bad_snapshot_binding",
                "bad_snapshot_budget",
            }:
                cases[label] = {
                    "runId": run_id,
                    "revision": store.load_run(run_id).revision,
                    "expectedStanding": "rejected",
                }
                continue
            cases[label] = {
                "runId": run_id,
                "intentDigest": intent.digest,
                "fenceDigest": current.fence.digest,
                "clientRequestId": intent.client_request_id,
                "toolCallId": intent.tool_call_id,
                "revision": store.load_run(run_id).revision,
                "preparedRevision": 2,
                "expectedStanding": "unknown" if label == "unknown_redacted" else "prepared",
                "preparedRevisionCurrent": label == "prepared",
            }
            continue

        from ordivon_harness.store import HarnessEventWrite

        if label == "generic_no_intent":
            data = {}
            references = ()
        else:
            source = cases["prepared"]
            first_run = store.list_run_events(source["runId"])[-1]
            data = first_run.data
            refs = tuple(
                store.inspect_object(value)
                for field, value in data.items()
                if field.endswith("ObjectDigest") and isinstance(value, str)
            )
            references = refs
        lease = store.acquire_run_lease(
            run_id,
            owner_id=f"test:{label}",
            ttl_ms=30_000,
            now_ms=clock(),
            expected_run_revision=1,
        )
        clock.advance()
        store.append_events(
            harness_run_id=run_id,
            expected_revision=1,
            lease=lease,
            lease_checked_at_ms=clock(),
            events=(
                HarnessEventWrite(
                    event_id=f"event:source-tool-generic-{label}",
                    event_kind="harness.tool-step-prepared",
                    data=data,
                    recorded_at_ms=clock(),
                    referenced_objects=references,
                ),
            ),
        )
        # Generic Journal is structurally legal but Python Tool source is not.
        store.validate_run_history(run_id)
        try:
            continuity.load_current_tool_step()
        except KeyError, ValueError, TypeError:
            pass
        else:
            raise AssertionError(f"Python Tool Consumer unexpectedly accepted {label}")
        cases[label] = {"runId": run_id, "revision": 2, "expectedStanding": "rejected"}

manifest["rust_tool_heads"] = cases
path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
print("PYTHON_REAL_TOOL_INTENT_FENCE_RECEIPT_PG18_PRODUCER_READY", len(cases))
