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
    parser.add_argument("action", choices=("issue", "revoke"))
    parser.add_argument("--dsn", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--run", required=True)
    parser.add_argument("--workspace", required=True)
    # A deliberate collision in a disposable cross-Run test only. Normal
    # callers keep the existing execution-binding-derived key.
    parser.add_argument("--client-request-id", default=None)
    args = parser.parse_args()
    if args.action == "issue":
        store = PostgresHarnessStore(args.dsn, schema=args.schema, initialize=True)
        try:
            contract = replace(
                private_tool_contract(),
                harness_run_id=args.run,
                caller_run_ref=f"trial:{args.run}",
            )
            store.create_run(contract)
            cont = EventSourcedRunContinuity(store, contract, clock_ms=now)
            cont.bind_state(state())
            runtime_binding = HarnessExecutionBinding(
                harness_run_id=args.run,
                workspace_ref=args.workspace,
                runtime_references=(
                    {"namespace": "ordivon.harness", "type": "harness_run", "id": args.run},
                ),
            )
            original = _build_workspace_exec_request(
                runtime_binding,
                step_id="r17-source-original",
                executable="/usr/bin/printf",
                args=("r17-real-source",),
                timeout_ms=15_000,
                stdout_limit_bytes=1024,
                stderr_limit_bytes=1024,
            )
            if args.client_request_id is not None:
                original["clientRequestId"] = args.client_request_id
            assignment = cont.binding
            intent = HarnessToolStepIntent(
                intent_id=f"harness-tool-step-intent:{args.run.split(':', 1)[-1]}:r17",
                harness_run_id=args.run,
                assignment_id=assignment.assignment_id,
                assignment_generation=assignment.assignment_generation,
                assignment_digest=assignment.assignment_digest,
                turn_id="turn:r17-original",
                tool_call_id="tool-call:r17-original",
                tool_name="exec_command",
                tool_call_digest=canonical_digest({"toolCall": "r17-original"}),
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
