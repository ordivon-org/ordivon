#!/usr/bin/env python3
"""Second *process*: recover original Harness Run and native Claim after reply loss.

This is a disposable real-PG18/MCP acceptance consumer, not a runtime issuer.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from anc_canonical import canonical_digest
from ordivon_harness.agent_run import HarnessAgentRun
from ordivon_harness.mcp_http_client import LoopbackMcpEndpoint, OfficialMcpClient
from ordivon_harness.ordivon.model import (
    AgentRunConclusion, AgentTurnResult, ScriptedTurnAdapter,
)
from ordivon_harness.ordivon.run_continuity import EventSourcedRunContinuity
from ordivon_harness.postgres_store import PostgresHarnessStore


def main() -> None:
    dsn = os.environ["ORDIVON_R22_HARNESS_PG_DSN"]
    schema = "harness_r22_source"
    run_id = os.environ["ORDIVON_R22_EXPECT_RUN"]
    workspace = os.environ["ORDIVON_R22_RUNTIME_WORKSPACE"]
    request_key = os.environ["ORDIVON_R22_EXPECT_CLAIM_REQUEST_ID"]
    native = OfficialMcpClient(
        LoopbackMcpEndpoint(os.environ["ORDIVON_R22_NATIVE_MCP_URL"]),
        bearer_token_file=Path(os.environ["ORDIVON_R22_NATIVE_CLAIM_TOKEN_FILE"]),
    )
    with PostgresHarnessStore(dsn, schema=schema) as store:
        continuity = EventSourcedRunContinuity.open(store, run_id)
        contract = continuity.contract
        old_revision = store.load_run(run_id).revision
        assert store.load_run(run_id).status.value == "active"

    class OriginalToolSurface:
        catalog_digest = contract.tool_catalog_digest
        grant_digest = contract.tool_grant_digest

    scripted = AgentTurnResult(
        model_call_id="model-call:r22-unused-reconnect",
        model_id=ScriptedTurnAdapter.model_id,
        content="never re-run model or Tool",
        tool_calls=(),
        conclusion=AgentRunConclusion(
            status="candidate_completed", summary="Read-only reconnect only"
        ),
        usage={"inputTokens": 1, "outputTokens": 1},
        finish_reason="stop",
        raw_response_digest=canonical_digest({"mode": "reconnect-unexecuted"}),
    )
    resumed = HarnessAgentRun.open(
        dsn, schema, run_id,
        lambda _: ScriptedTurnAdapter((scripted,)),
        tool_bridge=OriginalToolSurface(),
        workspace_claim_client=native,
        workspace_claim_workspace_id=workspace,
    )
    claim = resumed.workspace_claim.require_held()
    assert resumed.workspace_claim.request_id == request_key
    assert claim["runRef"] == run_id and claim["workspaceId"] == workspace
    with PostgresHarnessStore(dsn, schema=schema) as store:
        assert store.load_run(run_id).revision == old_revision
        assert store.load_run(run_id).status.value == "active"
    # No run(), resume(), or Tool effect was dispatched in this process.
    print(json.dumps({
        "marker": "R22_NEW_PROCESS_REATTACHED_EXACT_ORIGINAL_RUN_AND_NATIVE_CLAIM",
        "runId": run_id,
        "claimId": claim["claimId"],
        "clientRequestId": request_key,
        "originalRunRevision": old_revision,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
