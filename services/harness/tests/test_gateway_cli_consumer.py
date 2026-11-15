"""Source PG consumer: one public CLI Run -> existing Gateway Tool bridge.

This uses a deterministic Gateway fixture (NOT an installed live Gateway)
and a scripted Provider (NOT a paid model); the original PostgreSQL Store,
Tool Intent/Fence/OwnerReceipt, and independent CLI entrypoint are real.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from ordivon_harness.cli import build_parser
from ordivon_harness import independent_cli
from ordivon_harness.ordivon.run_continuity import EventSourcedRunContinuity
from ordivon_harness.postgres_store import PostgresHarnessStore
from tests.test_plugin_gateway_effect import (
    GatewayExecutionFixture,
    FixedClock,
    _adapter,
    _contract,
    _factory,
)

GATEWAY = "https://gateway-mcp.ordivon.com/mcp"


def gateway_args() -> list[str]:
    return [
        "--gateway-url",
        GATEWAY,
        "--gateway-workspace-id",
        "ws-plugin-h2",
        "--gateway-executable",
        "/usr/bin/rg",
        "--gateway-env-variable",
        "ORDIVON_TEST",
        "--gateway-max-timeout-ms",
        "10000",
        "--gateway-bearer-token-file",
        "/tmp/r45-test-fake-credential-not-read",
    ]


def test_gateway_cli_profile_is_existing_tool_surface_and_does_not_open_pg(monkeypatch):
    client = GatewayExecutionFixture()
    expected = _factory(client)
    monkeypatch.setattr(
        independent_cli,
        "OfficialMcpClient",
        lambda *args, **kwargs: client,
        raising=False,
    )
    monkeypatch.setattr(
        independent_cli,
        "configured_postgres",
        lambda: (_ for _ in ()).throw(AssertionError("profile opened PostgreSQL")),
    )
    args = build_parser().parse_args(["gateway-profile", *gateway_args()])
    profile = independent_cli.dispatch(args, clock_ms=FixedClock())
    assert profile["toolCatalogDigest"] == expected.catalog_digest
    assert profile["toolGrantDigest"] == expected.grant_digest
    # DeepSeek/OpenAI Chat Completions function names forbid dots.
    assert profile["modelToolDefinition"]["name"] == "execution_submit"
    assert "bearer" not in json.dumps(profile).lower()


def test_gateway_cli_uses_existing_authenticated_loopback_mcp_without_pg(monkeypatch):
    """Accept only exact first-party loopback; remote HTTP is never authorized."""
    client = GatewayExecutionFixture()
    monkeypatch.setattr(
        independent_cli, "OfficialMcpClient", lambda *args, **kwargs: client,
        raising=False,
    )
    monkeypatch.setattr(
        independent_cli, "configured_postgres",
        lambda: (_ for _ in ()).throw(AssertionError("profile accessed PG")),
    )
    arguments = gateway_args()
    arguments[arguments.index(GATEWAY)] = "http://127.0.0.1:8899/mcp"
    profile = independent_cli.dispatch(
        build_parser().parse_args(["gateway-profile", *arguments]),
        clock_ms=FixedClock(),
    )
    assert profile["modelToolDefinition"]["name"] == "execution_submit"
    assert profile["toolCatalogDigest"].startswith("sha256:")
    assert "http://127.0.0.1:8899/mcp" not in profile.get("proofBoundary", "")
    arguments[arguments.index("http://127.0.0.1:8899/mcp")] = "http://localhost:8899/mcp"
    with pytest.raises((ValueError, Exception)):
        independent_cli.dispatch(
            build_parser().parse_args(["gateway-profile", *arguments]),
            clock_ms=FixedClock(),
        )


def test_gateway_cli_existing_run_retains_owner_tool_receipt_in_original_pg(
    monkeypatch, pg_schema, tmp_path: Path
):
    client = GatewayExecutionFixture()
    factory = _factory(client)
    source = _contract(factory)
    contract_file = tmp_path / "gateway-run.json"
    contract_file.write_text(json.dumps(source.to_dict()), encoding="utf-8")
    monkeypatch.setattr(independent_cli, "configured_postgres", lambda: pg_schema)
    monkeypatch.setattr(
        independent_cli, "OfficialMcpClient", lambda *args, **kwargs: client, raising=False
    )
    monkeypatch.setattr(independent_cli, "_adapter", lambda _contract, _args: _adapter())
    args = build_parser().parse_args(
        [
            "run",
            str(contract_file),
            "--message",
            "Run the admitted tool",
            *gateway_args(),
        ]
    )
    result = independent_cli.dispatch(args, clock_ms=FixedClock())
    assert result["stopCode"] == "candidate_completed"
    assert result["run"]["status"] == "completed"
    names = [name for name, _ in client.calls]
    assert names == ["execution.submit", "execution.get"]
    with PostgresHarnessStore(pg_schema[0], schema=pg_schema[1]) as store:
        continuity = EventSourcedRunContinuity.open(store, source.harness_run_id)
        tool = continuity.load_current_tool_step()
        assert tool.fence is not None
        assert tool.receipt is not None
        assert tool.receipt.status.value == "observed"
        assert tool.receipt.harness_run_id == source.harness_run_id
        assert tool.receipt.runtime_job_ref == "job-h2"
        assert tool.observation is not None
        assert tool.observation["status"] == "observed"
        assert tool.observation["structuredContent"]["jobId"] == "job-h2"
        assert store.load_run(source.harness_run_id).status.value == "completed"
        store.validate_run_history(source.harness_run_id)


def test_gateway_cli_rejects_incomplete_options_before_run(monkeypatch, tmp_path: Path):
    client = GatewayExecutionFixture()
    factory = _factory(client)
    source = _contract(factory)
    contract_file = tmp_path / "contract.json"
    contract_file.write_text(json.dumps(source.to_dict()), encoding="utf-8")
    args = build_parser().parse_args(
        [
            "run",
            str(contract_file),
            "--message",
            "x",
            "--gateway-url",
            GATEWAY,
        ]
    )
    with pytest.raises(ValueError, match="Gateway|gateway"):
        independent_cli.dispatch(args, clock_ms=FixedClock())


def test_gateway_cli_runs_real_bounded_local_process_after_original_pg_intent(
    monkeypatch,
    pg_schema,
    tmp_path: Path,
):
    # The Gateway MCP service is intentionally a source-shaped test client,
    # NOT the installed live Gateway. Its *process* is real and its receipt
    # is tied to the exact original PG Run/ToolStep; no fake process success
    # is accepted for this focused local business consumer.
    (tmp_path / "source.txt").write_text("needle was really found here\\n", encoding="utf-8")

    class LocalPhysicalGateway(GatewayExecutionFixture):
        physical: subprocess.CompletedProcess[str] | None = None
        dispatches = 0
        pre_dispatch_passed = False

        def call_tool(self, name, arguments):
            if name == "execution.submit":
                with PostgresHarnessStore(pg_schema[0], schema=pg_schema[1]) as store:
                    continuity = EventSourcedRunContinuity.open(store, "harness-run:plugin-h2")
                    step = continuity.load_current_tool_step()
                    assert step.fence is not None
                    assert step.receipt is None
                    assert step.intent.runtime_operation == "workspace.exec"
                    assert any(
                        ref.get("type") == "dispatch_fence"
                        and ref.get("digest") == step.fence.digest
                        for ref in arguments["authorityReferences"]
                    )
                    self.pre_dispatch_passed = True
                assert arguments["workspaceId"] == "ws-plugin-h2"
                assert arguments["executable"] == "/usr/bin/rg"
                assert arguments["args"] == ["needle", "."]
                self.dispatches += 1
                self.physical = subprocess.run(
                    [arguments["executable"], *arguments["args"]],
                    cwd=tmp_path,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
            error, payload = super().call_tool(name, arguments)
            if name == "execution.get":
                assert self.physical is not None
                payload.update(
                    state="succeeded" if self.physical.returncode == 0 else "failed",
                    execution_disposition=(
                        "succeeded" if self.physical.returncode == 0 else "failed"
                    ),
                    exit_code=self.physical.returncode,
                    artifact_count=0,
                    artifact_projection_complete=True,
                )
            return error, payload

    client = LocalPhysicalGateway()
    factory = _factory(client)
    source = _contract(factory)
    contract_file = tmp_path / "source-run.json"
    contract_file.write_text(json.dumps(source.to_dict()), encoding="utf-8")
    monkeypatch.setattr(independent_cli, "configured_postgres", lambda: pg_schema)
    monkeypatch.setattr(
        independent_cli,
        "OfficialMcpClient",
        lambda *args, **kwargs: client,
    )
    monkeypatch.setattr(
        independent_cli,
        "_adapter",
        lambda _contract, _args: _adapter(),
    )
    cli = build_parser().parse_args(
        [
            "run",
            str(contract_file),
            "--message",
            "Find the source marker",
            *gateway_args(),
        ]
    )
    result = independent_cli.dispatch(cli, clock_ms=FixedClock())
    assert result["stopCode"] == "candidate_completed"
    assert client.pre_dispatch_passed
    assert client.dispatches == 1
    assert client.physical is not None and client.physical.returncode == 0
    assert "needle was really found here" in client.physical.stdout
    with PostgresHarnessStore(pg_schema[0], schema=pg_schema[1]) as store:
        history = EventSourcedRunContinuity.open(store, source.harness_run_id)
        step = history.load_current_tool_step()
        assert step.receipt is not None
        assert step.receipt.status.value == "observed"
        assert step.receipt.harness_run_id == source.harness_run_id
        assert step.observation is not None
        assert step.observation["structuredContent"]["executionDisposition"] == "succeeded"
        store.validate_run_history(source.harness_run_id)


def test_gateway_cli_rejects_foreign_tool_grant_before_pg_birth(
    monkeypatch,
    pg_schema,
    tmp_path: Path,
):
    client = GatewayExecutionFixture()
    factory = _factory(client)
    source = replace(
        _contract(factory),
        tool_grant_digest="sha256:" + "f" * 64,
    )
    contract_file = tmp_path / "mismatched-grant.json"
    contract_file.write_text(json.dumps(source.to_dict()), encoding="utf-8")
    monkeypatch.setattr(independent_cli, "configured_postgres", lambda: pg_schema)
    monkeypatch.setattr(independent_cli, "OfficialMcpClient", lambda *args, **kwargs: client)
    args = build_parser().parse_args(
        [
            "run",
            str(contract_file),
            "--message",
            "No source grant",
            *gateway_args(),
        ]
    )
    with pytest.raises(ValueError, match="source|Gateway"):
        independent_cli.dispatch(args, clock_ms=FixedClock())
    with PostgresHarnessStore(pg_schema[0], schema=pg_schema[1]) as store:
        with pytest.raises(KeyError):
            store.load_run(source.harness_run_id)
    assert client.calls == []


def test_gateway_cli_resume_after_unknown_owner_response_without_redispatch(
    monkeypatch,
    pg_schema,
    tmp_path: Path,
):
    # The first live process sends a physical request, loses its reply and
    # cannot reconcile. A *new* CLI invocation must read the one original PG
    # Intent and use execution.resolve/get, never submit the same effect again.
    from ordivon_harness.ordivon.model import ScriptedTurnAdapter

    class LostUntilRestart(GatewayExecutionFixture):
        resolution_offline = True

        def call_tool(self, name, arguments):
            if name == "execution.resolve" and self.resolution_offline:
                self.calls.append((name, dict(arguments)))
                raise ConnectionError("owner reconciliation temporarily unreachable")
            return super().call_tool(name, arguments)

    client = LostUntilRestart(response_loss=True)
    factory = _factory(client)
    source = _contract(factory)
    contract_file = tmp_path / "source-resume.json"
    contract_file.write_text(json.dumps(source.to_dict()), encoding="utf-8")
    monkeypatch.setattr(independent_cli, "configured_postgres", lambda: pg_schema)
    monkeypatch.setattr(independent_cli, "OfficialMcpClient", lambda *args, **kwargs: client)
    adapter_calls = {"value": 0}

    def scripted_provider(contract, args):
        adapter_calls["value"] += 1
        # After the source UNKNOWN is reconciled, the Caller supplies a fresh
        # Adapter capable of concluding from Owner evidence. Never blind retry.
        turns = _adapter()._results
        return ScriptedTurnAdapter(turns if adapter_calls["value"] == 1 else (turns[1],))

    monkeypatch.setattr(independent_cli, "_adapter", scripted_provider)
    clock = FixedClock()
    first = build_parser().parse_args(
        [
            "run",
            str(contract_file),
            "--message",
            "Try the tool once",
            *gateway_args(),
        ]
    )
    stopped = independent_cli.dispatch(first, clock_ms=clock)
    assert stopped["stopCode"] == "runtime_unknown"
    assert stopped["run"]["status"] == "paused"
    assert [name for name, _ in client.calls] == [
        "execution.submit",
        "execution.resolve",
    ]
    with PostgresHarnessStore(pg_schema[0], schema=pg_schema[1]) as store:
        step = EventSourcedRunContinuity.open(
            store,
            source.harness_run_id,
        ).load_current_tool_step()
        assert step.receipt is not None
        assert step.receipt.status.value == "unknown"
        snapshot = EventSourcedRunContinuity.open(
            store, source.harness_run_id
        ).load_current_snapshot()
        assert snapshot.snapshot.pause_reason.value == "effect-dispatch-pending"
        assert snapshot.snapshot.active_tool_step_intent_digests == (step.intent.digest,)

    client.resolution_offline = False
    second = build_parser().parse_args(
        [
            "resume",
            source.harness_run_id,
            "--message",
            "Use existing Owner outcome",
            *gateway_args(),
        ]
    )
    recovered = independent_cli.dispatch(second, clock_ms=clock)
    assert recovered["stopCode"] == "candidate_completed"
    assert recovered["run"]["status"] == "completed"
    names = [name for name, _ in client.calls]
    assert names.count("execution.submit") == 1
    assert names.count("execution.resolve") >= 2
    assert "execution.get" in names
    with PostgresHarnessStore(pg_schema[0], schema=pg_schema[1]) as store:
        continuity = EventSourcedRunContinuity.open(store, source.harness_run_id)
        step = continuity.load_current_tool_step()
        assert step.receipt is not None
        assert step.receipt.status.value == "observed"
        assert step.receipt.reconciled is True
        assert step.receipt.runtime_job_ref == "job-h2"
        store.validate_run_history(source.harness_run_id)


@pytest.mark.node_qualification
@pytest.mark.skipif(
    __import__("os").environ.get("HARNESS_REAL_GATEWAY_TOOL_TEST") != "1",
    reason="explicit billable Provider + installed Gateway/Runtime acceptance only",
)
def test_live_deepseek_gateway_tool_one_original_pg_run(pg_schema, monkeypatch, tmp_path: Path):
    """Real DeepSeek -> public CLI -> installed Gateway -> native Job -> original PG ToolStep.

    The test node selects an already authorized Workspace, Gateway address and
    private bearer file; no fixture grants execution, mints credentials or
    substitutes a Scripted Provider/Gateway response.
    """
    import os
    import sys
    import time
    import uuid

    from anc_canonical import canonical_digest
    from ordivon_harness.core_contracts import (
        HarnessBoundReference, HarnessPrivacyPolicy, HarnessRunContract,
    )
    from ordivon_harness.mcp_http_client import LoopbackMcpEndpoint, OfficialMcpClient
    from ordivon_harness.ordivon.deepseek import DeepSeekSettings, DeepSeekTurnAdapter

    url = os.environ["HARNESS_REAL_GATEWAY_URL"]
    workspace_id = os.environ["HARNESS_REAL_GATEWAY_WORKSPACE_ID"]
    token_file = os.environ["HARNESS_REAL_GATEWAY_BEARER_TOKEN_FILE"]
    secret = os.environ.get("HARNESS_REAL_DEEPSEEK_SECRET_FILE")
    settings = (
        DeepSeekSettings.from_secret_file(secret)
        if secret else DeepSeekSettings.from_secret_file()
    )
    monkeypatch.setenv("HARNESS_PG_DSN", pg_schema[0])
    monkeypatch.setenv("HARNESS_PG_SCHEMA", pg_schema[1])
    gateway = [
        "--gateway-url", url,
        "--gateway-bearer-token-file", token_file,
        "--gateway-workspace-id", workspace_id,
        "--gateway-executable", "/usr/bin/python3",
        "--gateway-max-timeout-ms", "120000",
    ]

    def cli(*arguments: str) -> dict[str, object]:
        result = subprocess.run(
            [sys.executable, "-m", "ordivon_harness.cli", *arguments],
            capture_output=True, text=True, timeout=230,
            check=False,
        )
        assert result.returncode == 0, result.stderr[-1200:]
        value = json.loads(result.stdout)
        assert value["ok"]
        return value

    profile = cli("gateway-profile", *gateway)
    assert profile["modelToolDefinition"]["name"] == "execution_submit"
    run_id = "harness-run:live-owner-" + uuid.uuid4().hex[:16]

    def ref(kind: str) -> HarnessBoundReference:
        return HarnessBoundReference(
            f"{kind}:r46-live-owner", kind,
            canonical_digest({"liveGatewayTest": kind}),
        )

    contract = HarnessRunContract(
        harness_run_id=run_id,
        harness_implementation_id="ordivon-harness@live-owner-acceptance",
        caller_id="caller:live-gateway-acceptance",
        caller_run_ref="trial:one-real-model-tool",
        objective_ref=ref("objective"),
        context_refs=(ref("context"),),
        provider_id="provider:deepseek",
        adapter_id=DeepSeekTurnAdapter.adapter_id,
        requested_model_id=settings.model,
        tool_catalog_digest=profile["toolCatalogDigest"],
        tool_grant_digest=profile["toolGrantDigest"],
        budget={
            "maxModelCalls": 3, "maxToolCalls": 1,
            "maxObservationBytes": 65536, "maxWallTimeMs": 200000,
            "maxTotalTokens": 18000, "maxModelRetries": 0,
            "maxToolCorrections": 1, "maxConclusionCorrections": 1,
            "maxObservationOnlyTurns": 2, "maxNoProgressTurns": 2,
        },
        completion_contract={"mode": "record"},
        system_manifest_ref=ref("system-manifest"),
        created_at_ms=int(time.time() * 1000),
        privacy=HarnessPrivacyPolicy(
            content_policy="bounded-private-content",
            allow_model_content=True,
            allow_tool_content=True,
        ),
    )
    source = tmp_path / "contract.json"
    source.write_text(json.dumps(contract.to_dict()), encoding="utf-8")
    prompt = (
        "必须先调用已授权的 execution_submit 工具一次，指定 "
        "executable=/usr/bin/python3，args=[\"-c\", "
        "\"print('ORDIVON_LIVE_HARNESS_GATEWAY_TOOL_OK')\"]，"
        "cwdRelative='.'，timeoutMs=45000；等待工具结果，再提交结论。"
    )
    requested = ["run", str(source), "--message", prompt, *gateway]
    if secret:
        requested.extend(["--deepseek-secret", secret])
    result = cli(*requested)
    assert result["stopCode"] == "candidate_completed"
    assert result["run"]["status"] == "completed"
    assert result["usage"]["modelCalls"] >= 2
    assert result["usage"]["toolCalls"] == 1
    assert result["runReceipt"] is not None
    assert result["completionProposal"] is not None
    assert cli("status", run_id)["run"]["status"] == "completed"
    assert cli("inspect", run_id)["run"]["status"] == "completed"

    with PostgresHarnessStore(pg_schema[0], schema=pg_schema[1]) as store:
        continuity = EventSourcedRunContinuity.open(store, run_id)
        step = continuity.load_current_tool_step()
        assert step.fence is not None
        assert step.receipt is not None and step.receipt.status.value == "observed"
        assert step.receipt.harness_run_id == run_id
        assert step.observation is not None
        assert step.observation["structuredContent"]["executionDisposition"] == "succeeded"
        job_id = step.receipt.runtime_job_ref
        request_id = step.intent.client_request_id
        assert job_id is not None
        store.validate_run_history(run_id)

    # Observe the real Owner through the same authenticated Gateway, not a
    # second trust layer. This check is separate from model self-report.
    if url.startswith("http://"):
        endpoint = LoopbackMcpEndpoint(url)
    else:
        from ordivon_harness.agent_plugin import AgentPluginMcpComponent
        endpoint = AgentPluginMcpComponent(
            name="ordivon-gateway", transport="streamable-http", url=url
        )
    client = OfficialMcpClient(endpoint, bearer_token_file=Path(token_file))
    error, owner = client.call_tool("execution.get", {
        "operationRef": f"ordivon-exec:v1:runtime.linux:{job_id}",
        "requestId": request_id,
        "capability": "execution.linux",
        "eventLimit": 10,
        "waitMs": 0,
    })
    assert error is False
    assert owner["native_id"] == job_id
    assert owner["terminal"] is True
    assert owner["execution_disposition"] == "succeeded"
    assert owner["delivery_disposition"] == "committed"
    assert owner["exit_code"] == 0
