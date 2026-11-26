"""Opt-in source PG18 + installed Gateway fault-injection consumer.

The physical execution is genuine. Only the *client's response* and first
owner reconciliation are dropped. The Provider is scripted, not a paid model.
The original PostgreSQL Run must resume through the exact existing Owner.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import replace
from pathlib import Path

import pytest

from ordivon_harness import independent_cli
from ordivon_harness.cli import build_parser
from ordivon_harness.mcp_http_client import LoopbackMcpEndpoint, OfficialMcpClient
from ordivon_harness.ordivon.model import AgentToolCall, ScriptedTurnAdapter
from ordivon_harness.ordivon.run_continuity import EventSourcedRunContinuity
from ordivon_harness.plugin_gateway_effect import (
    PluginGatewayExecutionBridgeFactory,
    PluginGatewayExecutionGrant,
)
from ordivon_harness.postgres_store import PostgresHarnessStore
from tests.test_plugin_gateway_effect import FixedClock, _adapter, _contract


@pytest.mark.node_qualification
@pytest.mark.skipif(
    os.environ.get("HARNESS_REAL_GATEWAY_UNKNOWN_TEST") != "1",
    reason="requires existing authenticated Gateway, separate Workspace and disposable PG18",
)
def test_real_gateway_reply_loss_recovers_one_original_owner_effect(
    monkeypatch, pg_schema, tmp_path: Path
) -> None:
    url = os.environ["HARNESS_REAL_GATEWAY_URL"]
    wsid = os.environ["HARNESS_REAL_GATEWAY_WORKSPACE_ID"]
    token_path = Path(os.environ["HARNESS_REAL_GATEWAY_BEARER_TOKEN_FILE"])
    endpoint = LoopbackMcpEndpoint(url, name="ordivon-gateway")
    official = OfficialMcpClient(endpoint, bearer_token_file=token_path)

    class LostReplyClient:
        submit_count = 0
        resolution_offline = True
        original_owner_job_id: str | None = None
        original_request_id: str | None = None

        def list_tools(self):
            return official.list_tools()

        def call_tool(self, name, arguments):
            if name == "execution.submit":
                self.submit_count += 1
                assert self.submit_count == 1, "physical effect must never redispatch"
                error, body = official.call_tool(name, arguments)
                assert error is False, body
                self.original_owner_job_id = body["native_id"]
                self.original_request_id = arguments["requestId"]
                # Exactly one physical Owner admission occurred; drop only its reply.
                raise ConnectionError("test-injected response loss AFTER physical owner admission")
            if name == "execution.resolve" and self.resolution_offline:
                raise ConnectionError("test-injected temporary reconciliation outage")
            return official.call_tool(name, arguments)

    client = LostReplyClient()
    grant = PluginGatewayExecutionGrant(
        capability="execution.linux",
        workspace_id=wsid,
        executable_allowlist=("/usr/bin/python3",),
        env_allowlist=(),
        max_timeout_ms=120_000,
    )
    factory = PluginGatewayExecutionBridgeFactory(endpoint, client, grant)
    run_id = "harness-run:real-unknown-" + uuid.uuid4().hex[:16]
    source = replace(
        _contract(factory),
        harness_run_id=run_id,
        caller_run_ref="trial:real-owner-unknown-" + run_id.split(":")[-1],
        budget={
            "maxModelCalls": 2,
            "maxToolCalls": 1,
            "maxObservationBytes": 65536,
            "maxWallTimeMs": 150000,
            "maxTotalTokens": 4096,
            "maxModelRetries": 0,
            "maxToolCorrections": 1,
            "maxConclusionCorrections": 1,
            "maxObservationOnlyTurns": 2,
            "maxNoProgressTurns": 2,
        },
    )
    contract_file = tmp_path / "source-run.json"
    contract_file.write_text(json.dumps(source.to_dict()), encoding="utf-8")
    monkeypatch.setattr(independent_cli, "configured_postgres", lambda: pg_schema)
    monkeypatch.setattr(independent_cli, "OfficialMcpClient", lambda *args, **kwargs: client)

    first, last = _adapter()._results
    tool = AgentToolCall(
        tool_call_id="tool-call:real-owner-loss",
        name="execution_submit",
        arguments={
            "executable": "/usr/bin/python3",
            "args": ["-c", "print('R45_LIVE_OWNER_SINGLE_EFFECT')"],
            "cwdRelative": ".",
            "timeoutMs": 45_000,
        },
    )
    first = replace(first, tool_calls=(tool,))
    adapter_invocations = 0

    def scripted_provider(*_args, **_kwargs):
        nonlocal adapter_invocations
        adapter_invocations += 1
        return ScriptedTurnAdapter((first, last) if adapter_invocations == 1 else (last,))

    monkeypatch.setattr(independent_cli, "_adapter", scripted_provider)
    cli_args = [
        "--gateway-url",
        url,
        "--gateway-bearer-token-file",
        str(token_path),
        "--gateway-workspace-id",
        wsid,
        "--gateway-executable",
        "/usr/bin/python3",
        "--gateway-max-timeout-ms",
        "120000",
    ]
    clock = FixedClock()
    paused = independent_cli.dispatch(
        build_parser().parse_args(
            ["run", str(contract_file), "--message", "Observe the Owner once", *cli_args]
        ),
        clock_ms=clock,
    )
    assert paused["stopCode"] == "runtime_unknown"
    assert paused["run"]["status"] == "paused"
    assert client.submit_count == 1
    assert client.original_owner_job_id is not None

    with PostgresHarnessStore(pg_schema[0], schema=pg_schema[1]) as store:
        continuity = EventSourcedRunContinuity.open(store, run_id)
        step = continuity.load_current_tool_step()
        assert step.receipt is not None and step.receipt.status.value == "unknown"
        assert step.intent.client_request_id == client.original_request_id
        snapshot = continuity.load_current_snapshot()
        assert snapshot.snapshot.pause_reason.value == "effect-dispatch-pending"
        store.validate_run_history(run_id)

    client.resolution_offline = False
    recovered = independent_cli.dispatch(
        build_parser().parse_args(
            ["resume", run_id, "--message", "Use prior physical Owner evidence", *cli_args]
        ),
        clock_ms=clock,
    )
    assert recovered["stopCode"] == "candidate_completed"
    assert recovered["run"]["status"] == "completed"
    assert client.submit_count == 1

    with PostgresHarnessStore(pg_schema[0], schema=pg_schema[1]) as store:
        continuity = EventSourcedRunContinuity.open(store, run_id)
        step = continuity.load_current_tool_step()
        assert step.receipt is not None and step.receipt.status.value == "observed"
        assert step.receipt.reconciled is True
        assert step.receipt.runtime_job_ref == client.original_owner_job_id
        store.validate_run_history(run_id)

    # The genuine Owner's request index is independent from Harness success.
    error, owner = official.call_tool(
        "execution.resolve",
        {"capability": "execution.linux", "requestId": client.original_request_id},
    )
    assert error is False, owner
    assert owner["resolution"] == "found"
    assert owner["native_id"] == client.original_owner_job_id
    assert owner["workspace_id"] == wsid
    print(
        json.dumps(
            {
                "kind": "harness.live-owner-unknown-recovery",
                "provider": "scripted",
                "owner": "installed-gateway-runtime-linux",
                "runId": run_id,
                "originalJobId": client.original_owner_job_id,
                "physicalSubmitCount": client.submit_count,
                "pausedOnUnknown": True,
                "resumedFromOriginalOwner": True,
                "sourcePgHistoryValidated": True,
                "semanticTaskSolved": "not_evaluated",
            },
            sort_keys=True,
        )
    )
