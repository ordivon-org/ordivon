"""Disposable original Harness PostgreSQL Run/Tool/Fence producer for Rust PG18 tests.

Opt-in tests only. Uses the actual PostgresHarnessStore + EventSourcedRunContinuity.
Never reads or writes installed PG; a caller provides disposable socket DSN/schema.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
import time

from anc_canonical import canonical_digest
from ordivon_harness.execution_binding import HarnessExecutionBinding
from ordivon_harness.ordivon.run_continuity import EventSourcedRunContinuity
from ordivon_harness.ordivon.runtime_bridge import HarnessRuntimeBridge
from ordivon_harness.ordivon.runtime_lowering import _build_workspace_exec_request
from ordivon_harness.postgres_store import PostgresHarnessStore
from ordivon_harness.protocol import (
    HarnessRecoveryConsequence,
    HarnessToolStepIntent,
    HarnessToolStepReceipt,
    HarnessToolStepStatus,
)

from tests.test_p0_sqlite_provider_store import state
from tests.test_p0_sqlite_tool_store import private_tool_contract


def now() -> int:
    return time.time_ns() // 1_000_000


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("issue", "revoke", "issue-next", "record-observed", "seal-unsubmitted", "inspect-issued"))
    parser.add_argument("--dsn", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--run", required=True)
    parser.add_argument("--workspace", required=True)
    # A deliberate collision in a disposable cross-Run test only. Normal
    # callers keep the existing execution-binding-derived key.
    parser.add_argument("--client-request-id", default=None)
    parser.add_argument("--observation-file", default=None)
    args = parser.parse_args()
    if args.action in ("issue", "issue-next"):
        store = PostgresHarnessStore(args.dsn, schema=args.schema, initialize=True)
        try:
            if args.action == "issue":
                contract = replace(
                    private_tool_contract(),
                    harness_run_id=args.run,
                    caller_run_ref=f"trial:{args.run}",
                )
                store.create_run(contract)
                cont = EventSourcedRunContinuity(store, contract, clock_ms=now)
                cont.bind_state(state())
            else:
                cont = EventSourcedRunContinuity.open(store, args.run, clock_ms=now)
                # This fixture uses the same controlled observation-only state.
                cont.bind_state(state())
            step = "r17-original" if args.action == "issue" else "r6-next"
            suffix = "r17" if args.action == "issue" else "r6-next"
            runtime_binding = HarnessExecutionBinding(
                harness_run_id=args.run,
                workspace_ref=args.workspace,
                runtime_references=(
                    {"namespace": "ordivon.harness", "type": "harness_run", "id": args.run},
                ),
            )
            original = _build_workspace_exec_request(
                runtime_binding,
                step_id="r17-source-original" if args.action == "issue" else "r6-source-next",
                executable="/usr/bin/printf",
                args=("r17-real-source" if args.action == "issue" else "r6-never-submitted",),
                timeout_ms=15_000,
                stdout_limit_bytes=1024,
                stderr_limit_bytes=1024,
            )
            if args.client_request_id is not None:
                original["clientRequestId"] = args.client_request_id
            assignment = cont.binding
            intent = HarnessToolStepIntent(
                intent_id=f"harness-tool-step-intent:{args.run.split(':', 1)[-1]}:{suffix}",
                harness_run_id=args.run,
                assignment_id=assignment.assignment_id,
                assignment_generation=assignment.assignment_generation,
                assignment_digest=assignment.assignment_digest,
                turn_id=f"turn:{step}",
                tool_call_id=f"tool-call:{step}",
                tool_name="exec_command",
                tool_call_digest=canonical_digest({"toolCall": step}),
                runtime_operation="workspace.exec",
                runtime_arguments_digest=canonical_digest(original),
                client_request_id=original["clientRequestId"],
                recovery_consequence=HarnessRecoveryConsequence.WORKSPACE_CHANGE_POSSIBLE,
                created_at_ms=now(),
            )
            cont.prepare_tool_step(intent, original_request=original)
            current = cont.load_current_tool_step()
            assert current.fence is not None
            cont.assert_dispatch_fence_current(current.fence)
            lowered = HarnessRuntimeBridge._with_dispatch_fence(original, current.fence)
            print(
                json.dumps(
                    {
                        "runId": args.run,
                        "issuerSchema": args.schema,
                        "clientRequestId": original["clientRequestId"],
                        "originalRequest": original,
                        "loweredRequest": lowered,
                        "fenceDigest": current.fence.digest,
                        "fenceGeneration": current.fence.run_revision,
                        "preparedRevision": store.load_run(args.run).revision,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
        finally:
            store.close()
    elif args.action in ("record-observed", "seal-unsubmitted", "inspect-issued"):
        from pathlib import Path

        store = PostgresHarnessStore(args.dsn, schema=args.schema)
        try:
            cont = EventSourcedRunContinuity.open(store, args.run, clock_ms=now)
            if args.action != "inspect-issued":
                current = cont.load_current_tool_step()
                if args.action == "record-observed":
                    assert args.observation_file is not None
                    observation = json.loads(Path(args.observation_file).read_text())
                    assert observation["executionDisposition"] == "succeeded"
                    assert observation["resultAvailable"] is True
                    job_ref = observation["jobId"]
                    assert isinstance(job_ref, str)
                    status = HarnessToolStepStatus.OBSERVED
                else:
                    # A fixture-owned local refusal *before submission*.
                    # This is not a proof from absent Runtime rows.
                    observation = {
                        "schemaVersion": 1,
                        "kind": "fixture.source-pre-submit-rejection",
                        "status": "rejected",
                        "clientRequestId": current.intent.client_request_id,
                    }
                    job_ref = None
                    status = HarnessToolStepStatus.REJECTED
                receipt = HarnessToolStepReceipt(
                    receipt_id=f"harness-tool-step-receipt:{args.run.split(':', 1)[-1]}:{args.action}",
                    intent_digest=current.intent.digest,
                    harness_run_id=args.run,
                    tool_call_id=current.intent.tool_call_id,
                    status=status,
                    runtime_job_ref=job_ref,
                    observation_digest=canonical_digest(observation),
                    reconciled=False,
                    created_at_ms=now(),
                )
                cont.record_tool_step_receipt(receipt, observation)
                if args.action == "seal-unsubmitted":
                    from ordivon_harness.store import HarnessEventWrite
                    at = now()
                    lease = store.acquire_run_lease(
                        args.run, owner_id="worker:r6-original-cut", ttl_ms=10_000, now_ms=at,
                    )
                    try:
                        store.append_events(
                            harness_run_id=args.run,
                            events=(HarnessEventWrite(
                                event_id=f"event:r6-terminal:{args.run.split(':', 1)[-1]}",
                                event_kind="harness.run-stopped",
                                data={"stopReason": "stopped"},
                                recorded_at_ms=at,
                            ),),
                            expected_revision=lease.run_revision,
                            lease=lease,
                            lease_checked_at_ms=at,
                        )
                    finally:
                        store.release_run_lease(lease)
            projection = store.load_run(args.run)
            print(json.dumps({
                "terminal": projection.status.terminal,
                "source": cont.inspect_issued_tool_sources(),
            }, sort_keys=True, separators=(",", ":")))
        finally:
            store.close()
    else:
        store = PostgresHarnessStore(args.dsn, schema=args.schema)
        try:
            cont = EventSourcedRunContinuity.open(store, args.run, clock_ms=now)
            current = cont.load_current_tool_step()
            observation = {
                "schemaVersion": 1,
                "kind": "r17-original-native-receiver-unknown",
                "status": "unknown",
            }
            receipt = HarnessToolStepReceipt(
                receipt_id=f"harness-tool-step-receipt:{args.run.split(':', 1)[-1]}:unknown",
                intent_digest=current.intent.digest,
                harness_run_id=args.run,
                tool_call_id=current.intent.tool_call_id,
                status=HarnessToolStepStatus.UNKNOWN,
                runtime_job_ref="runtime-job:r17-post-admission-unsettled",
                observation_digest=canonical_digest(observation),
                reconciled=False,
                created_at_ms=now(),
            )
            cont.record_tool_step_receipt(receipt, observation)
            print(
                json.dumps(
                    {
                        "sourceStanding": "unknown",
                        "runId": args.run,
                        "revision": store.load_run(args.run).revision,
                        "finalization": cont.inspect_finalization_source(),
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
        finally:
            store.close()


if __name__ == "__main__":
    main()
