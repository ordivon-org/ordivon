#!/usr/bin/env python3
"""Legacy opt-in disposable PG18 test: native HELD and test-only raw release.

The existing Gateway real-PG18 fixture consumes this exact script. It is NOT
a certified production recipient or independent Finalizer. The ordinary Run
MUST reject caller-authored ACK and callbacks. The final raw release is an
explicit privileged negative-control capability for this disposable fixture
ONLY, and must not be exposed to real Coding Agents or current ordinary MCP.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import secrets
import time

from anc_canonical import canonical_digest
from ordivon_harness.agent_run import HarnessAgentRun
from ordivon_harness.core_contracts import (
    HarnessBoundReference, HarnessPrivacyPolicy, HarnessRunContract,
)
from ordivon_harness.mcp_http_client import LoopbackMcpEndpoint, OfficialMcpClient
from ordivon_harness.postgres_store import PostgresHarnessStore
from ordivon_harness.runtime_port import HarnessWorkspaceAdmissionUnavailable
from ordivon_harness.ordivon.agent_bridge import (
    NO_TOOL_AGENT_GRANT_DIGEST, NO_TOOL_AGENT_SURFACE_DIGEST,
)
from ordivon_harness.ordivon.model import (
    AgentRunConclusion, AgentTurnResult, ScriptedTurnAdapter,
)


def sha(label: str) -> str:
    return canonical_digest({"kind": "real-native-ordinary-task", "label": label})


def physical(client: OfficialMcpClient, operation: str, payload: dict) -> dict:
    is_error, result = client.call_tool(operation, payload)
    if is_error:
        raise AssertionError(f"{operation}: {result}")
    return result


def main() -> None:
    dsn = os.environ["ORDIVON_R22_HARNESS_PG_DSN"]
    schema = "harness_r22_source"
    workspace = "ws-r22-ordinary-release-" + secrets.token_hex(4)
    runtime = OfficialMcpClient(
        LoopbackMcpEndpoint(os.environ["ORDIVON_R22_NATIVE_MCP_URL"]),
        bearer_token_file=Path(os.environ["ORDIVON_R22_NATIVE_CLAIM_TOKEN_FILE"]),
    )
    repository = os.environ["ORDIVON_R22_REAL_SOURCE_REPOSITORY"]
    delivered_to = Path(os.environ["ORDIVON_R22_REAL_RECIPIENT_PATH"])
    physical(runtime, "workspace.open", {
        "workspaceId": workspace, "sourceRepo": repository, "sourceRevision": "HEAD",
    })
    now = int(time.time() * 1000)
    run_id = "harness-run:r22-native-release-" + secrets.token_hex(6)
    # The real Harness Journal lives in a SECOND PostgreSQL database. Do not
    # create a same-DB test accident or rely on cross-database advisory locks.
    with PostgresHarnessStore(dsn, schema=schema, initialize=True):
        pass
    contract = HarnessRunContract(
        harness_run_id=run_id,
        harness_implementation_id="ordivon-harness@r22-physical-release",
        caller_id="caller:r22-native",
        caller_run_ref="trial:" + run_id.removeprefix("harness-run:"),
        objective_ref=HarnessBoundReference("objective:r22-release", "objective", sha("objective")),
        context_refs=(HarnessBoundReference("context:r22-release", "context", sha("context")),),
        provider_id="provider:scripted", adapter_id=ScriptedTurnAdapter.adapter_id,
        requested_model_id=ScriptedTurnAdapter.model_id,
        tool_catalog_digest=NO_TOOL_AGENT_SURFACE_DIGEST,
        tool_grant_digest=NO_TOOL_AGENT_GRANT_DIGEST,
        budget={
            "maxModelCalls": 2, "maxToolCalls": 0, "maxObservationBytes": 65536,
            "maxWallTimeMs": 60000, "maxTotalTokens": 4096,
            "maxModelRetries": 1, "maxToolCorrections": 1,
            "maxConclusionCorrections": 1, "maxObservationOnlyTurns": 2,
            "maxNoProgressTurns": 2,
        },
        completion_contract={"mode": "record"},
        system_manifest_ref=HarnessBoundReference(
            "manifest:r22-release", "system-manifest", sha("system-manifest"),
        ),
        created_at_ms=now,
        privacy=HarnessPrivacyPolicy(
            content_policy="bounded-private-content",
            allow_model_content=True, allow_tool_content=False,
        ),
    )
    response = AgentTurnResult(
        model_call_id="model-call:r22-completed",
        model_id=ScriptedTurnAdapter.model_id,
        content="ordinary task generated and delivered",
        tool_calls=(),
        conclusion=AgentRunConclusion(
            status="candidate_completed", summary="Ordinary task completed"
        ),
        usage={"inputTokens": 4, "outputTokens": 4},
        finish_reason="stop",
        raw_response_digest=sha("model-completed"),
    )
    run = HarnessAgentRun.create(
        dsn, schema, contract,
        lambda _: ScriptedTurnAdapter((response,)),
        workspace_claim_client=runtime,
        workspace_claim_workspace_id=workspace,
    )
    original_claim = run.workspace_claim.require_held()
    assert original_claim["runRef"] == run_id
    # One physical result file is produced inside the real mutable Workspace.
    payload = "R22_VERIFIED_ORDINARY_OUTPUT_" + run_id
    physical(runtime, "workspace.mutate", {
        "workspaceId": workspace,
        "mutations": [{"mode": "WRITE", "relativePath": "output.txt", "content": payload}],
    })
    # Record the output in Git before closing normally: Workspace.close must
    # not discard a unique, uncommitted file under consumerReleased=true.
    submitted = physical(runtime, "workspace.exec", {
        "clientRequestId": f"r22-native-output-commit-{run_id}",
        "execution": {
            "workspaceId": workspace,
            "executable": "/usr/bin/bash", "cwdRelative": ".",
            "args": ["-lc", (
                "git add output.txt && git -c user.name='Harness Fixture' "
                "-c user.email='fixture@example.invalid' commit -m 'r22 native ordinary output'"
            )],
        },
        "waitMs": 2000,
    })
    job_id = submitted["jobId"]
    job = submitted
    for _ in range(30):
        if job.get("executionTerminal") is True:
            break
        job = physical(runtime, "job.observe", {"jobId": job_id, "waitMs": 1000})
    assert job.get("executionTerminal") is True and job.get("exitCode") == 0, job
    state = physical(runtime, "workspace.get", {"workspaceId": workspace})
    assert state["activeJobIds"] == [], state
    assert state["dirty"] is False, state
    assert run.workspace_claim.require_held()["claimId"] == original_claim["claimId"]

    executed = run.run(({"role": "user", "content": "Deliver original output."},))
    assert executed.loop_result.stop_code.value == "candidate_completed"
    finalization = run.inspect_finalization_source()
    assert finalization["sourceStanding"] == "source-settled", finalization
    assert finalization["unsettledToolIntentDigests"] == []
    # The recipient is a physical path OUTSIDE the Native Workspace. Verify
    # exact bytes independently and never accept Job exit as domain receipt.
    original = physical(runtime, "workspace.read", {
        "workspaceId": workspace, "relativePath": "output.txt", "mode": "FULL",
        "maxBytes": 4096,
    })
    assert original["content"] == payload
    delivered_to.write_bytes(original["content"].encode("utf-8"))
    expected_sha = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    ack = {
        "harnessRunId": run_id,
        "runReceiptDigest": finalization["runReceiptDigest"],
        "accepted": True,
        "sha256": expected_sha,
    }
    blocked, blocked_result = runtime.call_tool("workspace.close", {
        "workspaceId": workspace, "force": False, "consumerReleased": True,
        "expectedSourceStateDigest": state["sourceStateDigest"],
    })
    assert blocked and blocked_result.get("error", {}).get("code") == "CONCURRENCY_LIMIT", blocked_result

    def verified(original_source: dict, consumer_ack: dict) -> bool:
        if original_source.get("sourceStanding") != "source-settled":
            return False
        physical_now = physical(runtime, "workspace.get", {"workspaceId": workspace})
        if physical_now["activeJobIds"] != []:
            return False
        if contract.tool_catalog_digest != NO_TOOL_AGENT_SURFACE_DIGEST:
            return False
        return (
            delivered_to.read_bytes() == payload.encode("utf-8")
            and hashlib.sha256(delivered_to.read_bytes()).hexdigest() == consumer_ack["sha256"]
        )

    assert verified(finalization, ack)
    try:
        run.release_workspace_after_delivery(
            recipient_ack=ack, verify_delivered_and_drained=verified,
        )
    except HarnessWorkspaceAdmissionUnavailable:
        pass
    else:
        raise AssertionError("caller ACK incorrectly promoted to real Finalizer")
    assert run.workspace_claim.require_held()["state"] == "held"
    print("R34_NORMAL_HARNESS_RUN_CANNOT_SELF_CERTIFY_CLAIM_RELEASE", flush=True)
    # Explicit TEST-ONLY raw action used by the older Gateway fixture.
    # This does not authenticate a production Domain receiver or OS fence.
    # Modern ordinary production MCP rightfully denies it altogether.
    released = physical(runtime, "workspace.claim.release", {
        "schemaVersion": 1,
        "clientRequestId": run.workspace_claim.request_id,
    })
    assert released["state"] == "released"
    closed = physical(runtime, "workspace.close", {
        "workspaceId": workspace, "force": False, "consumerReleased": True,
        "expectedSourceStateDigest": state["sourceStateDigest"],
    })
    assert closed.get("removed") is True, closed
    print(json.dumps({
        "marker": "R22_NORMAL_RUN_OUTPUT_DELIVERED_CLAIM_RELEASED_NATIVE_CLOSE_REMOVED",
        "runId": run_id,
        "claimId": original_claim["claimId"],
        "jobId": job_id,
        "sha256": expected_sha,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
