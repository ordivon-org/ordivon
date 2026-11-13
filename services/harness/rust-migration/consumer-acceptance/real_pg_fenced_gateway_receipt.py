#!/usr/bin/env python3
"""Persist response-loss UNKNOWN and an authenticated native Owner successor.

This is a disposable-PG18 test-only consumer, NOT a new Runtime client or
execution adapter. Owner facts are verified from the *same* native PG Job,
not trusted from the caller's receipt label.
"""

from __future__ import annotations

import json
import os

import psycopg
from anc_canonical import canonical_digest
from ordivon_harness.ordivon.run_continuity import EventSourcedRunContinuity
from ordivon_harness.postgres_store import PostgresHarnessStore
from ordivon_harness.protocol import HarnessToolStepReceipt, HarnessToolStepStatus

dsn = os.environ["ORDIVON_R22_HARNESS_PG_DSN"]
run_id = os.environ["ORDIVON_R22_EXPECT_RUN"]
mode = os.environ["ORDIVON_R22_RECEIPT_STAGE"]
expected_request = os.environ["ORDIVON_R22_EXPECT_REQUEST"]
refs = json.loads(os.environ["ORDIVON_R22_EXPECT_REFS_JSON"])
assert mode in {"unknown", "reconcile"}
assert isinstance(refs, list) and len(refs) == 4
assert refs[-1]["type"] == "dispatch_fence"
assert refs[-1]["namespace"] == "ordivon.harness"

with PostgresHarnessStore(dsn, schema="harness_r22_source", initialize=False) as store:
    store.validate_run_history(run_id)
    c = EventSourcedRunContinuity.open(store, run_id, clock_ms=lambda: 1_000_000_000_001)
    current = c.load_current_tool_step()
    assert current.intent.client_request_id == expected_request
    assert current.intent.harness_run_id == run_id
    assert current.fence is not None
    assert refs[-1]["digest"] == current.fence.digest
    assert refs[-1]["generation"] == str(current.fence.authority_generation)
    assert refs[0] == {"namespace": "ordivon.harness", "type": "harness_run", "id": run_id}
    assert refs[1]["digest"] == c.contract.digest
    assert refs[2]["digest"] == c.contract.tool_grant_digest
    assert current.intent.recovery_consequence.value == "process-or-external-effect-possible"
    if mode == "unknown":
        assert current.receipt is None
        observation = {
            "schemaVersion": 1,
            "kind": "r22-native-physical-effect-unknown-observation",
            "clientRequestId": expected_request,
            "delivery": "response-lost-after-owner-submit",
        }
        receipt = HarnessToolStepReceipt(
            receipt_id=f"harness-tool-step-receipt:r22-unknown-{expected_request[-16:]}",
            intent_digest=current.intent.digest,
            harness_run_id=run_id,
            tool_call_id=current.intent.tool_call_id,
            status=HarnessToolStepStatus.UNKNOWN,
            runtime_job_ref=None,
            observation_digest=canonical_digest(observation),
            reconciled=False,
            created_at_ms=1_000_000_000_001,
        )
        c.record_tool_step_receipt(receipt, observation)
        current = c.load_current_tool_step()
        assert current.receipt == receipt
        assert current.observation is None
        print(json.dumps({"runId": run_id, "standing": "UNKNOWN", "receiptDigest": receipt.digest}))
    else:
        assert current.receipt is not None
        assert current.receipt.status is HarnessToolStepStatus.UNKNOWN
        owner_job = os.environ["ORDIVON_R22_OWNER_JOB"]
        owner_observation = json.loads(os.environ["ORDIVON_R22_OWNER_OBSERVATION"])
        assert owner_observation["jobId"] == owner_job
        assert owner_observation["clientRequestId"] == expected_request
        assert owner_observation["executionTerminal"] is True
        assert owner_observation["deliveryDisposition"] == "committed"
        assert owner_observation["exitCode"] == 0
        # Crucial: independently verify *real* Runtime PG Owner evidence,
        # not merely the caller-supplied 'success' JSON.
        with psycopg.connect(dsn, autocommit=True) as conn:
            row = conn.execute(
                "SELECT principal,client_request_id,execution_plan_json,resolution "
                "FROM fresh.jobs WHERE job_id=%s",
                (owner_job,),
            ).fetchone()
            assert row is not None
            principal, request_id, plan_json, resolution = row
            # Native Runtime chooses a principal from the authenticated ingress
            # profile; a caller-supplied Job ID cannot stand in for identity.
            expected_principal = os.getenv("ORDIVON_R22_OWNER_PRINCIPAL", "pg-consumer")
            assert principal == expected_principal
            if request_id != expected_request:
                raise ValueError("OWNER_SOURCE_IDENTITY_MISMATCH: runtime clientRequestId differs")
            assert resolution == "succeeded"
            plan = json.loads(plan_json)
            assert plan["foreignReferences"] == refs
            assert plan["workspaceId"] == os.environ["ORDIVON_R22_RUNTIME_WORKSPACE"]
            dispatches = conn.execute(
                "SELECT count(*) FROM fresh.job_events "
                "WHERE job_id=%s AND event_type='DISPATCH_ISSUED'",
                (owner_job,),
            ).fetchone()[0]
            assert dispatches == 1
            native_results = conn.execute(
                "SELECT count(*) FROM fresh.artifacts WHERE job_id=%s AND kind='execution_result'",
                (owner_job,),
            ).fetchone()[0]
            assert native_results == 1
        observation = {
            "schemaVersion": 1,
            "kind": "r22-native-physical-effect-owner-evidence",
            "clientRequestId": expected_request,
            "runtimeJobId": owner_job,
            "nativeExecutionTerminal": True,
            "deliveryDisposition": "committed",
            "physicalDisposition": "succeeded",
            "semanticCompletionEvaluated": False,
        }
        receipt = HarnessToolStepReceipt(
            receipt_id=f"harness-tool-step-receipt:r22-settled-{expected_request[-16:]}",
            intent_digest=current.intent.digest,
            harness_run_id=run_id,
            tool_call_id=current.intent.tool_call_id,
            status=HarnessToolStepStatus.OBSERVED,
            runtime_job_ref=owner_job,
            observation_digest=canonical_digest(observation),
            reconciled=True,
            previous_receipt_digest=current.receipt.digest,
            created_at_ms=1_000_000_000_002,
        )
        c.record_tool_step_receipt(receipt, observation)
        settled = c.load_current_tool_step()
        assert settled.previous_receipt == current.receipt
        assert settled.receipt == receipt
        assert settled.observation is None
        store.validate_run_history(run_id)
        events = store.list_run_events(run_id)
        assert [e.event_kind for e in events if e.event_kind.startswith("harness.tool-step-")] == [
            "harness.tool-step-prepared",
            "harness.tool-step-unknown",
            "harness.tool-step-reconciled",
        ]
        print(
            json.dumps(
                {
                    "runId": run_id,
                    "standing": "OWNER_CONFIRMED_RECEIPT",
                    "jobId": owner_job,
                    "receiptDigest": receipt.digest,
                    "previousReceiptDigest": current.receipt.digest,
                    "dispatchCount": 1,
                    "semanticCompletionEvaluated": False,
                }
            )
        )
