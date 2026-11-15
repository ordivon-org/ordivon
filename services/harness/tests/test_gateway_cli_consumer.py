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
    assert profile["modelToolDefinition"]["name"] == "execution.submit"
    assert "bearer" not in json.dumps(profile).lower()


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
