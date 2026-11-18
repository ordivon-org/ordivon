from __future__ import annotations

import tempfile

import pytest

from anc_canonical import canonical_digest

from ordivon_harness.agent_plugin import AgentPluginMcpComponent
from ordivon_harness.agent_run import HarnessAgentRun
from ordivon_harness.core_contracts import (
    HarnessBoundReference,
    HarnessPrivacyPolicy,
    HarnessRunContract,
)
from ordivon_harness.ordivon.control import CancellationToken
from ordivon_harness.ordivon.model import (
    AgentRunConclusion,
    AgentToolCall,
    AgentTurnResult,
    ScriptedTurnAdapter,
)
from ordivon_harness.ordivon.run_continuity import EventSourcedRunContinuity
from ordivon_harness.plugin_gateway_effect import (
    GatewayMcpRuntimeAdapter,
    PluginGatewayExecutionBridgeFactory,
    PluginGatewayExecutionGrant,
)
from ordivon_harness.postgres_store import PostgresHarnessStore
from ordivon_harness.runtime_port import (
    HarnessRuntimeClientError,
    HarnessWorkspaceAdmissionUnavailable,
)


class FixedClock:
    def __init__(self) -> None:
        self.value = 20_000

    def __call__(self) -> int:
        self.value += 1
        return self.value


def _digest(label: str) -> str:
    return canonical_digest({"harness-plugin-h2": label})


class GatewayExecutionFixture:
    def __init__(
        self,
        *,
        response_loss: bool = False,
        pre_dispatch_probe=None,
        cancellation: CancellationToken | None = None,
    ) -> None:
        self.response_loss = response_loss
        self.pre_dispatch_probe = pre_dispatch_probe
        self.cancellation = cancellation
        self.calls: list[tuple[str, dict]] = []
        self.operation_ref = "ordivon-exec:v1:runtime.linux:job-h2"
        self.native_id = "job-h2"

    def list_tools(self):
        def tool(name: str):
            return {
                "name": name,
                "description": name,
                "inputSchema": {"type": "object", "additionalProperties": True},
                "outputSchema": {"type": "object"},
            }

        return tuple(
            tool(name)
            for name in (
                "execution.submit",
                "execution.resolve",
                "execution.get",
                "execution.cancel",
            )
        )

    def call_tool(self, name, arguments):
        self.calls.append((name, dict(arguments)))
        if name == "execution.submit":
            if self.pre_dispatch_probe is not None:
                self.pre_dispatch_probe(arguments)
            if self.cancellation is not None:
                self.cancellation.cancel()
            if self.response_loss:
                self.response_loss = False
                raise RuntimeError("simulated response loss after owner admission")
            return False, {
                "schema_version": 1,
                "kind": "ordivon.gateway-execution-receipt",
                "operation_ref": self.operation_ref,
                "capability": "execution.linux",
                "owner_id": "runtime.linux",
                "native_id": self.native_id,
                "state": "working",
                "terminal": False,
                "delivery_disposition": "in_progress",
            }
        if name == "execution.resolve":
            return False, {
                "schema_version": 1,
                "kind": "ordivon.gateway-execution-resolution",
                "request_id": arguments["requestId"],
                "capability": "execution.linux",
                "owner_id": "runtime.linux",
                "resolution": "found",
                "operation_ref": self.operation_ref,
                "native_id": self.native_id,
                "workspace_id": "ws-plugin-h2",
            }
        if name == "execution.cancel":
            return False, {
                "schema_version": 1,
                "kind": "ordivon.gateway-execution-receipt",
                "operation_ref": self.operation_ref,
                "capability": "execution.linux",
                "owner_id": "runtime.linux",
                "native_id": self.native_id,
                "state": "cancelling",
                "terminal": False,
                "delivery_disposition": "in_progress",
            }
        if name == "execution.get":
            return False, {
                "schema_version": 1,
                "kind": "ordivon.gateway-execution-observation",
                "operation_ref": self.operation_ref,
                "capability": "execution.linux",
                "owner_id": "runtime.linux",
                "native_id": self.native_id,
                "state": "succeeded",
                "terminal": True,
                "delivery_disposition": "committed",
                "execution_disposition": "succeeded",
                "exit_code": 0,
                "recovery_required": False,
                "artifacts_available": False,
                "artifact_ids": [],
                "artifact_count": 0,
                "artifact_projection_complete": True,
            }
        raise AssertionError(f"unexpected Gateway Tool: {name}")


def _factory(client: GatewayExecutionFixture) -> PluginGatewayExecutionBridgeFactory:
    return PluginGatewayExecutionBridgeFactory(
        AgentPluginMcpComponent(
            name="ordivon-gateway",
            transport="streamable-http",
            url="https://gateway-mcp.ordivon.com/mcp",
        ),
        client,
        PluginGatewayExecutionGrant(
            capability="execution.linux",
            workspace_id="ws-plugin-h2",
            executable_allowlist=("/usr/bin/rg",),
            env_allowlist=("ORDIVON_TEST",),
            max_timeout_ms=10_000,
        ),
    )


def _contract(factory: PluginGatewayExecutionBridgeFactory) -> HarnessRunContract:
    return HarnessRunContract(
        harness_run_id="harness-run:plugin-h2",
        harness_implementation_id="ordivon-harness@plugin-h2",
        caller_id="caller:plugin-h2",
        caller_run_ref="trial:plugin-h2",
        objective_ref=HarnessBoundReference(
            "objective:plugin-h2", "objective", _digest("objective")
        ),
        context_refs=(HarnessBoundReference("context:plugin-h2", "context", _digest("context")),),
        provider_id="provider:scripted",
        adapter_id=ScriptedTurnAdapter.adapter_id,
        requested_model_id=ScriptedTurnAdapter.model_id,
        tool_catalog_digest=factory.catalog_digest,
        tool_grant_digest=factory.grant_digest,
        budget={
            "maxModelCalls": 2,
            "maxToolCalls": 1,
            "maxObservationBytes": 65_536,
            "maxWallTimeMs": 30_000,
            "maxTotalTokens": 4_096,
            "maxModelRetries": 0,
            "maxToolCorrections": 1,
            "maxConclusionCorrections": 1,
            "maxObservationOnlyTurns": 2,
            "maxNoProgressTurns": 2,
        },
        completion_contract={"mode": "record"},
        system_manifest_ref=HarnessBoundReference(
            "manifest:plugin-h2", "system-manifest", _digest("manifest")
        ),
        created_at_ms=20_000,
        privacy=HarnessPrivacyPolicy(
            content_policy="bounded-private-content",
            allow_model_content=True,
            allow_tool_content=True,
        ),
    )


def _adapter(timeout_ms: int | None = 5_000) -> ScriptedTurnAdapter:
    arguments = {
        "executable": "/usr/bin/rg",
        "args": ["needle", "."],
        "cwdRelative": ".",
        "env": {"ORDIVON_TEST": "1"},
    }
    if timeout_ms is not None:
        arguments["timeoutMs"] = timeout_ms
    return ScriptedTurnAdapter(
        (
            AgentTurnResult(
                model_call_id="model-call:plugin-h2-tool",
                model_id=ScriptedTurnAdapter.model_id,
                content="execute",
                tool_calls=(
                    AgentToolCall(
                        tool_call_id="tool-call:plugin-h2",
                        name="execution_submit",
                        arguments=arguments,
                    ),
                ),
                conclusion=None,
                usage={"inputTokens": 1, "outputTokens": 1},
                finish_reason="tool_calls",
                raw_response_digest=_digest("tool-turn"),
            ),
            AgentTurnResult(
                model_call_id="model-call:plugin-h2-done",
                model_id=ScriptedTurnAdapter.model_id,
                content="done",
                tool_calls=(),
                conclusion=AgentRunConclusion(
                    status="candidate_completed",
                    summary="Gateway execution observed.",
                ),
                usage={"inputTokens": 1, "outputTokens": 1},
                finish_reason="stop",
                raw_response_digest=_digest("done-turn"),
            ),
        )
    )



class GatewayTextArtifacts(GatewayExecutionFixture):
    """Existing Gateway execution+artifact ports in one bounded test client."""

    stdout = "A中文B🙂C\n"

    def __init__(self, *, tamper: str | None = None):
        super().__init__()
        self.tamper = tamper

    def list_tools(self):
        return (
            *super().list_tools(),
            {
                "name": "artifact.read",
                "description": "Read exact Owner Artifact bytes",
                "inputSchema": {"type": "object"},
                "outputSchema": {"type": "object"},
            },
        )

    def call_tool(self, name, arguments):
        if name == "artifact.read":
            self.calls.append((name, dict(arguments)))
            assert arguments["maxBytes"] == 4096
            assert arguments["requestId"]
            assert arguments["capability"] == "execution.linux"
            assert arguments["operationRef"] == self.operation_ref
            assert arguments["offset"] == 0
            artifact_id = arguments["artifactId"]
            assert artifact_id in {"attempt-h2.stdout", "attempt-h2.stderr"}
            content = self.stdout if artifact_id.endswith(".stdout") else ""
            payload = {
                "operation_ref": self.operation_ref,
                "owner_id": "runtime.linux",
                "native_id": self.native_id,
                "artifact_id": artifact_id,
                "offset": 0,
                "next_offset": len(content.encode("utf-8")),
                "eof": True,
                "content": content,
                "digest": "sha256:" + "a" * 64,
            }
            if self.tamper == "wrong_job":
                payload["native_id"] = "job-unrelated"
            if self.tamper == "wrong_operation":
                payload["operation_ref"] = "ordivon-exec:v1:runtime.linux:job-unrelated"
            if self.tamper == "wrong_owner":
                payload["owner_id"] = "runtime.windows"
            if self.tamper == "zero_progress" and artifact_id.endswith(".stdout"):
                payload.update(next_offset=0, eof=False, content="")
            return False, payload
        is_error, payload = super().call_tool(name, arguments)
        if name == "execution.get":
            payload = dict(payload)
            payload["artifact_ids"] = ["attempt-h2.stdout", "attempt-h2.stderr"]
            payload["artifact_count"] = 2
        return is_error, payload


def test_gateway_observes_real_text_artifacts_for_next_model_turn() -> None:
    """Do not erase the content of the Owner Tool; text is UTF-8 byte-bounded."""
    client = GatewayTextArtifacts()
    factory = _factory(client)
    adapter = GatewayMcpRuntimeAdapter(
        factory.component,
        client,
        factory.execution_grant,
        artifact_read_enabled=True,
    )
    adapter._operation_requests[client.native_id] = "request:text-artifact"
    observed = adapter._observe_operation(client.operation_ref, client.native_id, wait_ms=0)
    assert observed["resultAvailable"] is True
    assert observed["outputPreviews"]["stdout"]["text"] == client.stdout
    assert observed["artifactMetadataStatus"] == "unqualified_ids_only"
    assert observed["outputPreviews"]["stdout"]["eof"] is True
    assert observed["outputPreviews"]["stderr"]["text"] == ""
    assert [name for name, _ in client.calls] == [
        "execution.get",
        "execution.resolve",
        "artifact.read",
        "artifact.read",
    ]


@pytest.mark.parametrize("tamper", ("wrong_job", "wrong_operation", "wrong_owner", "zero_progress"))
def test_gateway_rejects_artifact_window_not_owned_by_job(tamper: str) -> None:
    client = GatewayTextArtifacts(tamper=tamper)
    factory = _factory(client)
    adapter = GatewayMcpRuntimeAdapter(
        factory.component,
        client,
        factory.execution_grant,
        artifact_read_enabled=True,
    )
    adapter._operation_requests[client.native_id] = "request:tampered-artifact"
    with pytest.raises(HarnessRuntimeClientError, match="Artifact read"):
        adapter._observe_operation(client.operation_ref, client.native_id, wait_ms=0)


def test_gateway_artifact_text_reaches_next_model_turn_and_original_pg(pg_schema) -> None:
    """Real PostgreSQL ToolStep/Run persists one bounded Owner output observation."""
    client = GatewayTextArtifacts()
    factory = _factory(client)
    model = _adapter()
    clock = FixedClock()
    contract = _contract(factory)
    run = HarnessAgentRun.create(
        pg_schema[0],
        pg_schema[1],
        contract,
        lambda _: model,
        tool_bridge_factory=factory,
        clock_ms=clock,
        monotonic_ms=clock,
    )
    result = run.run(())
    assert result.loop_result.stop_code.value == "candidate_completed"
    model_messages = [
        msg for msg in model.requests[1].messages if msg.get("role") == "tool"
    ]
    assert len(model_messages) == 1
    model_content = model_messages[0]["observation"]["content"]
    assert model_content["outputPreviews"]["stdout"]["text"] == client.stdout
    assert model_content["artifactMetadataStatus"] == "unqualified_ids_only"
    assert model_content["outputPreviews"]["stderr"]["text"] == ""
    with PostgresHarnessStore(pg_schema[0], schema=pg_schema[1]) as store:
        step = EventSourcedRunContinuity.open(
            store, contract.harness_run_id
        ).load_current_tool_step()
        assert step.receipt is not None
        assert step.receipt.status.value == "observed"
        assert step.observation["structuredContent"]["outputPreviews"]["stdout"]["text"] == client.stdout


def test_effect_gateway_factory_rejects_duplicate_required_tool_names() -> None:
    from ordivon_harness.ordivon.tool_errors import ToolBridgeError

    class DuplicateRequired(GatewayExecutionFixture):
        def list_tools(self):
            tools = super().list_tools()
            duplicate = dict(tools[0])
            duplicate["inputSchema"] = {"type": "object", "maxProperties": 0}
            return (*tools, duplicate)

    with pytest.raises(ToolBridgeError, match="duplicate"):
        _factory(DuplicateRequired())


def test_effect_gateway_runtime_validation_rejects_duplicate_required_tool_names(
    pg_schema,
) -> None:
    from ordivon_harness.ordivon.tool_errors import ToolBridgeError

    class DuplicateAfterAdmission(GatewayExecutionFixture):
        def __init__(self):
            super().__init__()
            self.duplicated = False

        def list_tools(self):
            tools = super().list_tools()
            if self.duplicated:
                return (*tools, dict(tools[-1]))
            return tools

    client = DuplicateAfterAdmission()
    factory = _factory(client)
    contract = _contract(factory)
    clock = FixedClock()
    HarnessAgentRun.create(
        pg_schema[0],
        pg_schema[1],
        contract,
        lambda _: _adapter(),
        tool_bridge_factory=factory,
        clock_ms=clock,
        monotonic_ms=clock,
    )
    with PostgresHarnessStore(pg_schema[0], schema=pg_schema[1]) as store:
        continuity = EventSourcedRunContinuity.open(store, contract.harness_run_id)
        bridge = factory.build(contract, continuity)
        bridge.validate_runtime_catalog()
        client.duplicated = True
        with pytest.raises(ToolBridgeError, match="duplicate"):
            bridge.validate_runtime_catalog()


def test_effect_gateway_rejects_tool_schema_drift_after_run_preflight_before_intent(
    pg_schema,
) -> None:
    class MutatedAfterLoopCheck(GatewayExecutionFixture):
        def __init__(self):
            super().__init__()
            self.list_calls = 0

        def list_tools(self):
            self.list_calls += 1
            tools = list(super().list_tools())
            if self.list_calls >= 3:
                tools[0]["inputSchema"] = {"type": "object", "maxProperties": 0}
            return tuple(tools)

    client = MutatedAfterLoopCheck()
    factory = _factory(client)
    clock = FixedClock()
    run = HarnessAgentRun.create(
        pg_schema[0],
        pg_schema[1],
        _contract(factory),
        lambda _: _adapter(),
        tool_bridge_factory=factory,
        clock_ms=clock,
        monotonic_ms=clock,
    )
    result = run.run(())
    assert result.loop_result.stop_code.value == "invalid_tool_call", (
        result.loop_result.stop_code.value,
        [e.payload for e in result.loop_result.trace.events if e.kind == "run_stopped"],
    )
    assert client.list_calls >= 3
    assert client.calls == []
    with PostgresHarnessStore(pg_schema[0], schema=pg_schema[1]) as store:
        continuity = EventSourcedRunContinuity.open(store, "harness-run:plugin-h2")
        # A stale MCP schema is rejected before any prepared durable effect.
        with pytest.raises(KeyError, match="no current Tool Step"):
            continuity.load_current_tool_step()


def test_effect_gateway_catalog_transport_loss_before_intent_is_typed_and_non_dispatching(
    pg_schema,
) -> None:
    class ListTransportLoss(GatewayExecutionFixture):
        def __init__(self):
            super().__init__()
            self.catalog_reads = 0

        def list_tools(self):
            self.catalog_reads += 1
            if self.catalog_reads >= 3:
                raise ConnectionError("MCP catalog session lost before ToolStep intent")
            return super().list_tools()

    client = ListTransportLoss()
    factory = _factory(client)
    clock = FixedClock()
    run = HarnessAgentRun.create(
        pg_schema[0],
        pg_schema[1],
        _contract(factory),
        lambda _: _adapter(),
        tool_bridge_factory=factory,
        clock_ms=clock,
        monotonic_ms=clock,
    )
    result = run.run(())
    assert result.loop_result.stop_code.value == "invalid_tool_call", (
        result.loop_result.stop_code.value,
        client.catalog_reads,
        [e.payload for e in result.loop_result.trace.events if e.kind == "run_stopped"],
    )
    assert client.catalog_reads >= 3
    assert client.calls == []
    with PostgresHarnessStore(pg_schema[0], schema=pg_schema[1]) as store:
        continuity = EventSourcedRunContinuity.open(store, "harness-run:plugin-h2")
        with pytest.raises(KeyError, match="no current Tool Step"):
            continuity.load_current_tool_step()


def test_effect_gateway_real_mcp_http_schema_drift_before_pg_intent_never_dispatches(
    pg_schema,
) -> None:
    """SDK-native Streamable HTTP tool catalog changes between two real Run stages."""
    import asyncio
    import socket
    import threading
    import time

    import uvicorn
    from mcp import types
    from mcp.server import MCPServer

    from ordivon_harness.mcp_http_client import LoopbackMcpEndpoint, OfficialMcpClient

    owner = MCPServer("h2-native-gateway-mcp-catalog-drift")
    tool_names = ("execution.submit", "execution.get", "execution.resolve", "execution.cancel")

    for tool_name in tool_names:

        @owner.tool(name=tool_name)
        def owner_execution_tool(arguments: dict | None = None) -> dict[str, str]:
            return {"owner": "simulation", "requested": str(arguments)}

    listing_count = [0]
    dispatched = []

    async def list_current_tools(context, params: types.PaginatedRequestParams):
        listing_count[0] += 1
        all_tools = list(await owner.list_tools())
        assert {tool.name for tool in all_tools} == set(tool_names)
        if listing_count[0] >= 3:
            all_tools = [
                tool.model_copy(update={"input_schema": {"type": "object", "maxProperties": 0}})
                if tool.name == "execution.submit"
                else tool
                for tool in all_tools
            ]
        return types.ListToolsResult(tools=all_tools)

    async def call_never_expected(context, params: types.CallToolRequestParams):
        dispatched.append(params.name)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text="unexpected owner call")],
            structured_content={"unexpected": True},
        )

    owner._lowlevel_server.add_request_handler(
        "tools/list", types.PaginatedRequestParams, list_current_tools
    )
    owner._lowlevel_server.add_request_handler(
        "tools/call", types.CallToolRequestParams, call_never_expected
    )
    app = owner.streamable_http_app(stateless_http=True, json_response=True)
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", log_level="error"))
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    sock.listen(8)
    port = sock.getsockname()[1]
    thread = threading.Thread(target=lambda: asyncio.run(server.serve(sockets=[sock])), daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 10
        while not server.started and time.monotonic() < deadline:
            time.sleep(0.01)
        assert server.started
        # Real local transport is distinct from the canonical Plugin's
        # externally declared HTTPS endpoint. This fixture does not authorize
        # Runtime physical execution or use a production Gateway.
        client = OfficialMcpClient(LoopbackMcpEndpoint(f"http://127.0.0.1:{port}/mcp"))
        factory = _factory(client)
        clock = FixedClock()
        run = HarnessAgentRun.create(
            pg_schema[0],
            pg_schema[1],
            _contract(factory),
            lambda _: _adapter(),
            tool_bridge_factory=factory,
            clock_ms=clock,
            monotonic_ms=clock,
        )
        result = run.run(())
        assert listing_count[0] >= 3
        assert result.loop_result.stop_code.value == "invalid_tool_call", (
            result.loop_result.stop_code.value,
            [e.payload for e in result.loop_result.trace.events if e.kind == "run_stopped"],
        )
        assert dispatched == []
        with PostgresHarnessStore(pg_schema[0], schema=pg_schema[1]) as store:
            continuity = EventSourcedRunContinuity.open(store, "harness-run:plugin-h2")
            with pytest.raises(KeyError, match="no current Tool Step"):
                continuity.load_current_tool_step()
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        sock.close()
        assert not thread.is_alive()


def test_omitted_timeout_is_bounded_by_actual_harness_grant(pg_schema) -> None:
    """A valid optional tool input must not acquire Runtime's wider default."""
    with tempfile.TemporaryDirectory():
        client = GatewayExecutionFixture()
        factory = _factory(client)  # exact caller grant: 10,000ms
        clock = FixedClock()
        run = HarnessAgentRun.create(
            pg_schema[0],
            pg_schema[1],
            _contract(factory),
            lambda _contract: _adapter(timeout_ms=None),
            tool_bridge_factory=factory,
            clock_ms=clock,
            monotonic_ms=clock,
        )
        result = run.run(())
        assert result.loop_result.stop_code.value == "candidate_completed"
        calls = [(name, args) for name, args in client.calls if name == "execution.submit"]
        assert len(calls) == 1
        # Gateway's public typed execution.submit MUST carry an explicit
        # limit, otherwise Runtime's own default can exceed the caller grant.
        assert calls[0][1]["timeoutMs"] == 10_000


def test_gateway_effect_bridge_commits_intent_and_fence_before_physical_dispatch(pg_schema) -> None:
    with tempfile.TemporaryDirectory():
        observed_pre_dispatch = {"checked": False}

        def probe(arguments) -> None:
            with PostgresHarnessStore(pg_schema[0], schema=pg_schema[1]) as store:
                continuity = EventSourcedRunContinuity.open(store, "harness-run:plugin-h2")
                step = continuity.load_current_tool_step()
                assert step.receipt is None
                assert step.fence is not None
                assert step.intent.runtime_operation == "workspace.exec"
                refs = arguments["authorityReferences"]
                assert any(
                    ref.get("type") == "dispatch_fence" and ref.get("digest") == step.fence.digest
                    for ref in refs
                )
                observed_pre_dispatch["checked"] = True

        client = GatewayExecutionFixture(pre_dispatch_probe=probe)
        factory = _factory(client)
        contract = _contract(factory)
        clock = FixedClock()
        run = HarnessAgentRun.create(
            pg_schema[0],
            pg_schema[1],
            contract,
            lambda _contract: _adapter(),
            tool_bridge_factory=factory,
            clock_ms=clock,
            monotonic_ms=clock,
        )
        result = run.run(())

        assert result.loop_result.stop_code.value == "candidate_completed"
        assert observed_pre_dispatch["checked"] is True
        names = [name for name, _ in client.calls]
        assert names == ["execution.submit", "execution.get", "execution.resolve"]
        assert client.calls[1][1]["requestId"] == client.calls[0][1]["requestId"]
        assert client.calls[2][1]["requestId"] == client.calls[0][1]["requestId"]
        assert client.calls[2][1]["capability"] == "execution.linux"
        assert names.count("execution.submit") == 1
        assert client.calls[1][1]["capability"] == "execution.linux"
        submit = client.calls[0][1]
        assert submit["capability"] == "execution.linux"
        assert submit["workspaceId"] == "ws-plugin-h2"
        assert submit["executable"] == "/usr/bin/rg"
        assert submit["timeoutMs"] == 5_000  # explicitly admitted value is unchanged
        assert submit["stdoutLimitBytes"] == 262_144
        assert submit["stderrLimitBytes"] == 262_144
        assert submit["requestId"].startswith("request:harness-gateway:")


@pytest.mark.parametrize("tamper", ("request_id", "capability"))
def test_gateway_resolution_mismatched_identity_never_attaches_job(tamper: str, pg_schema) -> None:
    with tempfile.TemporaryDirectory():
        client = GatewayExecutionFixture(response_loss=True)
        original = client.call_tool

        def mismatched_owner_result(name, arguments):
            error, payload = original(name, arguments)
            if name == "execution.resolve":
                payload = dict(payload)
                payload[tamper] = "unrelated-owner-result"
            return error, payload

        client.call_tool = mismatched_owner_result
        factory = _factory(client)
        clock = FixedClock()
        run = HarnessAgentRun.create(
            pg_schema[0],
            pg_schema[1],
            _contract(factory),
            lambda _contract: _adapter(),
            tool_bridge_factory=factory,
            clock_ms=clock,
            monotonic_ms=clock,
        )
        result = run.run(())
        assert result.loop_result.stop_code.value == "runtime_unknown"
        names = [name for name, _ in client.calls]
        assert names == ["execution.submit", "execution.resolve"]


@pytest.mark.parametrize(
    "tamper",
    (
        "executable",
        "arguments",
        "client_request_id",
        "omit_run_contract_grant",
        "wrong_fence_digest",
        "duplicate_fence",
    ),
)
def test_durable_effect_handoff_rejects_post_intent_mutation_before_owner_call(
    tamper: str, pg_schema, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Real PG18 Intent/Fence must bind exact physical request, not merely its ID.

    This is a malicious/buggy gateway adapter's handoff mutation, not a model
    permission test: the frozen physical request has already been journaled.
    No execution.submit may occur if its bytes or the bound fence drift.
    """
    from ordivon_harness.plugin_gateway_effect import PluginGatewayExecutionBridge
    from ordivon_harness.ordivon.tool_errors import ToolBridgeError

    original = PluginGatewayExecutionBridge._with_dispatch_fence

    def mutate_after_preparation(request, fence):
        result = original(request, fence)
        execution = dict(result["execution"])
        refs = [dict(value) for value in execution["foreignReferences"]]
        if tamper == "executable":
            execution["executable"] = "/usr/bin/false"
        elif tamper == "arguments":
            execution["args"] = ["forged", "."]
        elif tamper == "client_request_id":
            result["clientRequestId"] = "request:forged-after-prepare"
        elif tamper == "omit_run_contract_grant":
            refs = [value for value in refs if value.get("type") != "tool_grant"]
        elif tamper == "wrong_fence_digest":
            refs[-1]["digest"] = canonical_digest({"forged": "fence"})
        elif tamper == "duplicate_fence":
            refs.append(dict(refs[-1]))
        execution["foreignReferences"] = refs
        result["execution"] = execution
        return result

    monkeypatch.setattr(
        PluginGatewayExecutionBridge, "_with_dispatch_fence", staticmethod(mutate_after_preparation)
    )
    client = GatewayExecutionFixture()
    factory = _factory(client)
    clock = FixedClock()
    run = HarnessAgentRun.create(
        pg_schema[0],
        pg_schema[1],
        _contract(factory),
        lambda _contract: _adapter(),
        tool_bridge_factory=factory,
        clock_ms=clock,
        monotonic_ms=clock,
    )
    try:
        run.run(())
    except ToolBridgeError:
        pass
    assert not [name for name, _ in client.calls if name == "execution.submit"], (
        f"{tamper}: a request different from committed Tool Intent reached its Owner"
    )


def test_gateway_effect_bridge_reconciles_response_loss_without_redispatch(pg_schema) -> None:
    with tempfile.TemporaryDirectory():
        client = GatewayExecutionFixture(response_loss=True)
        factory = _factory(client)
        contract = _contract(factory)
        clock = FixedClock()
        adapter = _adapter()
        run = HarnessAgentRun.create(
            pg_schema[0],
            pg_schema[1],
            contract,
            lambda _contract: adapter,
            tool_bridge_factory=factory,
            clock_ms=clock,
            monotonic_ms=clock,
        )
        result = run.run(())

        assert result.loop_result.stop_code.value == "candidate_completed"
        names = [name for name, _ in client.calls]
        assert names == [
            "execution.submit",
            "execution.resolve",
            "execution.get",
            "execution.resolve",
        ]
        for index in (1, 2, 3):
            assert client.calls[index][1]["requestId"] == client.calls[0][1]["requestId"]
            assert client.calls[index][1]["capability"] == "execution.linux"
        assert names.count("execution.submit") == 1

        with PostgresHarnessStore(pg_schema[0], schema=pg_schema[1]) as store:
            continuity = EventSourcedRunContinuity.open(store, "harness-run:plugin-h2")
            step = continuity.load_current_tool_step()
            assert step.receipt is not None
            assert step.receipt.reconciled is True
            assert step.receipt.runtime_job_ref == "job-h2"

        tool_messages = [
            message for message in adapter.requests[1].messages if message.get("role") == "tool"
        ]
        assert len(tool_messages) == 1
        assert tool_messages[0]["observation"]["status"] == "observed"


@pytest.mark.parametrize("mutation", ("missing_workspace", "wrong_workspace"))
def test_gateway_recovery_requires_owner_observed_workspace(mutation: str, pg_schema) -> None:
    with tempfile.TemporaryDirectory():
        client = GatewayExecutionFixture(response_loss=True)
        original_call_tool = client.call_tool

        def forged_resolution(name, arguments):
            failed, payload = original_call_tool(name, arguments)
            if name == "execution.resolve":
                payload = dict(payload)
                if mutation == "missing_workspace":
                    payload.pop("workspace_id")
                else:
                    payload["workspace_id"] = "ws-different-job"
            return failed, payload

        client.call_tool = forged_resolution  # type: ignore[method-assign]
        factory = _factory(client)
        run = HarnessAgentRun.create(
            pg_schema[0],
            pg_schema[1],
            _contract(factory),
            lambda _contract: _adapter(),
            tool_bridge_factory=factory,
            clock_ms=FixedClock(),
            monotonic_ms=FixedClock(),
        )
        result = run.run(())
        assert result.loop_result.stop_code.value == "runtime_unknown"
        names = [name for name, _ in client.calls]
        assert names == ["execution.submit", "execution.resolve"]


@pytest.mark.parametrize("field", ("stdoutLimitBytes", "stderrLimitBytes"))
@pytest.mark.parametrize("invalid", (True, 0, -1, 1.0, "262144"))
def test_gateway_adapter_refuses_non_integer_native_output_caps_before_owner_call(
    field: str, invalid: object
) -> None:
    """An invalid caller output bound must not be silently defaulted."""
    client = GatewayExecutionFixture()
    factory = _factory(client)
    adapter = GatewayMcpRuntimeAdapter(factory.component, client, factory.execution_grant)
    execution = {
        "workspaceId": "ws-plugin-h2",
        "foreignReferences": [],
        "executable": "/usr/bin/rg",
        "args": ["needle"],
        "cwdRelative": ".",
        field: invalid,
    }
    with pytest.raises(HarnessRuntimeClientError, match="invalid"):
        adapter.call_tool(
            "workspace.exec",
            {"clientRequestId": "request:output-bound", "execution": execution},
        )
    assert client.calls == []


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("budget", {"memoryBytes": 500_000_000}),
        ("hostDependencies", []),
        ("steps", [{"id": "first"}]),
        ("executionTarget", "windows_native"),
        ("executionProfile", "contained_local"),
        ("windowsAuthority", "active_user"),
        ("stdin", "uncommitted"),
    ),
)
def test_gateway_refuses_frozen_physical_fields_it_cannot_represent(
    field: str, value: object
) -> None:
    """Fail before Owner call; no silent request corruption at the adapter."""
    client = GatewayExecutionFixture()
    factory = _factory(client)
    adapter = GatewayMcpRuntimeAdapter(factory.component, client, factory.execution_grant)
    with pytest.raises(HarnessRuntimeClientError, match="cannot faithfully lower"):
        adapter.call_tool(
            "workspace.exec",
            {
                "clientRequestId": "request:physical-unsupported",
                "execution": {
                    "workspaceId": "ws-plugin-h2",
                    "executable": "/usr/bin/rg",
                    "foreignReferences": [],
                    field: value,
                },
            },
        )
    assert client.calls == []


def test_gateway_refuses_frozen_native_output_bound_outside_u64() -> None:
    client = GatewayExecutionFixture()
    factory = _factory(client)
    adapter = GatewayMcpRuntimeAdapter(factory.component, client, factory.execution_grant)
    with pytest.raises(HarnessRuntimeClientError, match="invalid stdoutLimitBytes"):
        adapter.call_tool(
            "workspace.exec",
            {
                "clientRequestId": "request:physical-overflow",
                "execution": {
                    "workspaceId": "ws-plugin-h2",
                    "executable": "/usr/bin/rg",
                    "foreignReferences": [],
                    "stdoutLimitBytes": 2**65,
                },
            },
        )
    assert client.calls == []


def test_gateway_native_job_identity_cannot_rebind_to_another_request() -> None:
    # The same native job must not be attached to a different durable request
    # after a late submit receipt or a recovered resolution.
    client = GatewayExecutionFixture()
    factory = _factory(client)
    adapter = GatewayMcpRuntimeAdapter(factory.component, client, factory.execution_grant)

    def submit(request_id: str) -> dict:
        return {
            "clientRequestId": request_id,
            "execution": {
                "workspaceId": "ws-plugin-h2",
                "foreignReferences": [],
                "executable": "/usr/bin/rg",
                "args": ["needle"],
                "cwdRelative": ".",
            },
        }

    first = adapter.call_tool("workspace.exec", submit("request:one"))
    assert first["jobId"] == client.native_id
    with pytest.raises(HarnessRuntimeClientError, match="binding|identity|request"):
        adapter.call_tool("workspace.exec", submit("request:other"))
    assert adapter._operation_requests[client.native_id] == "request:one"
    with pytest.raises(HarnessRuntimeClientError, match="binding|identity|request"):
        adapter.call_tool(
            "task.list",
            {"workspaceId": "ws-plugin-h2", "clientRequestId": "request:other"},
        )
    assert adapter._operation_requests[client.native_id] == "request:one"
    # Exact idempotent replay is still accepted.
    second = adapter.call_tool("workspace.exec", submit("request:one"))
    assert second["jobId"] == first["jobId"]


def test_gateway_same_request_cannot_rebind_to_different_native_operation() -> None:
    client = GatewayExecutionFixture()
    factory = _factory(client)
    adapter = GatewayMcpRuntimeAdapter(factory.component, client, factory.execution_grant)
    args = {
        "clientRequestId": "request:one",
        "execution": {
            "workspaceId": "ws-plugin-h2",
            "foreignReferences": [],
            "executable": "/usr/bin/rg",
        },
    }
    original_native = client.native_id
    original_ref = client.operation_ref
    adapter.call_tool("workspace.exec", args)
    client.native_id = "job-other"
    client.operation_ref = "ordivon-exec:v1:runtime.linux:job-other"
    with pytest.raises(HarnessRuntimeClientError, match="binding|identity|request"):
        adapter.call_tool("workspace.exec", args)
    assert adapter._operation_requests == {original_native: "request:one"}
    assert adapter._operation_refs == {original_native: original_ref}


def test_gateway_operation_ref_cannot_attach_to_a_different_job() -> None:
    client = GatewayExecutionFixture()
    factory = _factory(client)
    adapter = GatewayMcpRuntimeAdapter(factory.component, client, factory.execution_grant)

    def submit(request_id: str) -> dict:
        return {
            "clientRequestId": request_id,
            "execution": {
                "workspaceId": "ws-plugin-h2",
                "foreignReferences": [],
                "executable": "/usr/bin/rg",
            },
        }

    original_job = client.native_id
    adapter.call_tool("workspace.exec", submit("request:one"))
    client.native_id = "job-alias"
    with pytest.raises(HarnessRuntimeClientError, match="binding"):
        adapter.call_tool("workspace.exec", submit("request:other"))
    assert adapter._operation_requests == {original_job: "request:one"}
    assert adapter._operation_refs == {original_job: client.operation_ref}


@pytest.mark.parametrize("invalid", ("terminal", "state"))
def test_gateway_rejected_submit_receipt_does_not_poison_operation_map(invalid: str) -> None:
    client = GatewayExecutionFixture()
    original = client.call_tool

    def forged(name, arguments):
        is_error, receipt = original(name, arguments)
        if name == "execution.submit":
            receipt = dict(receipt)
            if invalid == "terminal":
                receipt["terminal"] = None
            else:
                receipt.pop("state")
        return is_error, receipt

    client.call_tool = forged
    factory = _factory(client)
    adapter = GatewayMcpRuntimeAdapter(factory.component, client, factory.execution_grant)
    with pytest.raises(HarnessRuntimeClientError):
        adapter.call_tool(
            "workspace.exec",
            {
                "clientRequestId": "request:untrusted",
                "execution": {
                    "workspaceId": "ws-plugin-h2",
                    "foreignReferences": [],
                    "executable": "/usr/bin/rg",
                },
            },
        )
    assert adapter._operation_refs == {}
    assert adapter._operation_requests == {}


def test_gateway_effect_bridge_propagates_cooperative_control_cancellation(pg_schema) -> None:
    with tempfile.TemporaryDirectory():
        clock = FixedClock()
        cancellation = CancellationToken(monotonic_ms=clock)
        client = GatewayExecutionFixture(cancellation=cancellation)
        factory = _factory(client)
        contract = _contract(factory)
        adapter = _adapter()
        run = HarnessAgentRun.create(
            pg_schema[0],
            pg_schema[1],
            contract,
            lambda _contract: adapter,
            tool_bridge_factory=factory,
            clock_ms=clock,
            monotonic_ms=clock,
        )
        result = run.run((), cancellation=cancellation)

        names = [name for name, _ in client.calls]
        assert names == ["execution.submit", "execution.cancel"]
        assert client.calls[1][1]["requestId"] == client.calls[0][1]["requestId"]
        assert client.calls[1][1]["capability"] == "execution.linux"
        assert result.loop_result.stop_code.value == "cancel_unknown"

        with PostgresHarnessStore(pg_schema[0], schema=pg_schema[1]) as store:
            continuity = EventSourcedRunContinuity.open(store, "harness-run:plugin-h2")
            step = continuity.load_current_tool_step()
            assert step.receipt is not None
            assert step.receipt.status.value == "cancel-requested"
            assert step.receipt.runtime_job_ref == "job-h2"
            assert step.observation is not None
            assert step.observation["status"] == "cancel-requested"
            assert step.observation["structuredContent"]["cancellationAcknowledged"] is True


def test_gateway_effect_grant_rejects_ambient_execution_authority() -> None:
    client = GatewayExecutionFixture()
    factory = _factory(client)
    definition = factory._definition
    schema = definition.input_schema
    assert set(schema["properties"]) == {
        "executable",
        "args",
        "cwdRelative",
        "env",
        "timeoutMs",
    }
    assert "capability" not in schema["properties"]
    assert "workspaceId" not in schema["properties"]
    assert "requestId" not in schema["properties"]
    assert "context" not in schema["properties"]


@pytest.mark.parametrize(
    ("mutation", "label"),
    (
        (lambda payload: payload.pop("delivery_disposition"), "delivery"),
        (lambda payload: payload.update(delivery_disposition="definitely"), "delivery"),
        (
            lambda payload: payload.update(operation_ref="ordivon-exec:v1:runtime.linux:other"),
            "operation",
        ),
        (lambda payload: payload.pop("artifact_projection_complete"), "artifact"),
        (lambda payload: payload.update(artifact_count=1), "artifact"),
    ),
)
def test_gateway_adapter_rejects_unproven_committed_terminal(mutation, label) -> None:
    """CEGAR: physical terminal cannot launder missing Gateway delivery/artifact proof."""

    class ForgedTerminal(GatewayExecutionFixture):
        def call_tool(self, name, arguments):
            is_error, payload = super().call_tool(name, arguments)
            if name == "execution.get":
                payload["artifact_projection_complete"] = True
                payload["artifact_count"] = 0
                mutation(payload)
            return is_error, payload

    client = ForgedTerminal()
    adapter = GatewayMcpRuntimeAdapter(
        AgentPluginMcpComponent(
            name="ordivon-gateway",
            transport="streamable-http",
            url="https://gateway-mcp.ordivon.com/mcp",
        ),
        client,
        _factory(client).execution_grant,
    )
    # This focused terminal verifier is invoked directly, bypassing the normal
    # Gateway submission/recovery step. Supply its otherwise durable request key
    # explicitly instead of weakening the new fail-closed consumer boundary.
    adapter._operation_requests[client.native_id] = "request:terminal-falsifier"
    with pytest.raises(HarnessRuntimeClientError, match=label):
        adapter._observe_operation(client.operation_ref, client.native_id, wait_ms=0)


def test_gateway_adapter_waits_for_committed_but_incomplete_artifact_projection() -> None:
    """A durable physical result is not an exact consumer artifact inventory."""

    class PendingArtifacts(GatewayExecutionFixture):
        def call_tool(self, name, arguments):
            is_error, payload = super().call_tool(name, arguments)
            if name == "execution.get":
                payload.update(
                    artifact_projection_complete=False,
                    artifact_count=2,
                    artifact_ids=[],
                )
            return is_error, payload

    client = PendingArtifacts()
    adapter = GatewayMcpRuntimeAdapter(
        AgentPluginMcpComponent(
            name="ordivon-gateway",
            transport="streamable-http",
            url="https://gateway-mcp.ordivon.com/mcp",
        ),
        client,
        _factory(client).execution_grant,
    )
    adapter._operation_requests[client.native_id] = "request:artifact-falsifier"
    observed = adapter._observe_operation(client.operation_ref, client.native_id, wait_ms=0)
    assert observed["deliveryDisposition"] == "reconciliation_required"
    assert observed["recoveryRequired"] is True
    assert observed["resultAvailable"] is False


def test_gateway_native_stop_unknown_lost_does_not_invent_runner_result() -> None:
    """Gateway artifact projection != native execution result availability."""

    class NativeStopOnly(GatewayExecutionFixture):
        def call_tool(self, name, arguments):
            is_error, record = super().call_tool(name, arguments)
            if name == "execution.get":
                record.update(
                    state="lost",
                    execution_disposition="lost",
                    delivery_disposition="unknown",
                    terminal=True,
                    exit_code=None,
                    recovery_required=False,
                    artifact_ids=["artifact-attempt-native-stop"],
                    artifact_count=1,
                    artifact_projection_complete=True,
                )
            return is_error, record

    client = NativeStopOnly()
    adapter = GatewayMcpRuntimeAdapter(
        AgentPluginMcpComponent(
            name="ordivon-gateway",
            transport="streamable-http",
            url="https://gateway-mcp.ordivon.com/mcp",
        ),
        client,
        _factory(client).execution_grant,
    )
    adapter._operation_requests[client.native_id] = "request:native-stop-recovery"
    observed = adapter._observe_operation(client.operation_ref, client.native_id, wait_ms=0)
    assert observed["executionTerminal"] is True
    assert observed["executionDisposition"] == "lost"
    assert observed["deliveryDisposition"] == "unknown"
    assert observed["resultAvailable"] is False
    assert observed["semanticCompletionEvaluated"] is False


@pytest.mark.parametrize("invalid", [None, True, False, 0, -1, 10_001, "10"])
def test_schema_invalid_timeout_is_rejected_on_real_agent_run(invalid: object, pg_schema) -> None:
    """An invalid canonical JSON value must not reach Gateway execution.submit."""
    from dataclasses import replace

    from jsonschema import Draft202012Validator

    client = GatewayExecutionFixture()
    factory = _factory(client)
    adapter = _adapter(timeout_ms=None)
    first, second = adapter._results
    call = first.tool_calls[0]
    invalid_arguments = {**call.arguments, "timeoutMs": invalid}
    assert list(
        Draft202012Validator(factory._definition.input_schema).iter_errors(invalid_arguments)
    )
    adapter._results = (
        replace(first, tool_calls=(replace(call, arguments=invalid_arguments),)),
        second,
    )

    with tempfile.TemporaryDirectory():
        clock = FixedClock()
        run = HarnessAgentRun.create(
            pg_schema[0],
            pg_schema[1],
            _contract(factory),
            lambda _contract: adapter,
            tool_bridge_factory=factory,
            clock_ms=clock,
            monotonic_ms=clock,
        )
        run.run(())
        assert not [arguments for name, arguments in client.calls if name == "execution.submit"], (
            "schema-illegal timeout reached actual Gateway submission"
        )


def test_canonical_json_timeout_input_is_narrower_than_json_schema_numeric_integer() -> None:
    """A source-observed representation gap must not be mistaken for wire equivalence."""
    from jsonschema import Draft202012Validator

    factory = _factory(GatewayExecutionFixture())
    schema = factory._definition.input_schema
    raw = {
        "executable": "/usr/bin/rg",
        "args": ["needle", "."],
        "timeoutMs": 1000.0,
    }
    assert Draft202012Validator(schema).is_valid(raw)
    assert "canonical JSON integer token" in schema["properties"]["timeoutMs"]["description"]
    with pytest.raises(ValueError, match="floating-point values are forbidden"):
        AgentToolCall(
            tool_call_id="tool-call:noncanonical-timeout",
            name="execution.submit",
            arguments=raw,
        )


@pytest.mark.parametrize(
    ("path", "mutation"),
    [
        ("submit", "unhashable_list"),
        ("submit", "unhashable_dict"),
        ("submit", "wrong_owner"),
        ("submit", "wrong_capability"),
        ("submit", "wrong_operation_job"),
        ("observe", "unhashable_list"),
        ("observe", "unhashable_dict"),
        ("observe", "wrong_owner"),
        ("observe", "wrong_capability"),
        ("observe", "wrong_operation_job"),
        ("resolve", "wrong_owner"),
        ("resolve", "wrong_operation_job"),
        ("cancel", "wrong_owner"),
        ("cancel", "wrong_operation_job"),
    ],
)
def test_gateway_owner_receipt_identity_and_type_boundary_fails_closed(
    path: str, mutation: str
) -> None:
    """A Gateway payload's fields must describe ONE owner Job before attachment.

    This test replays the production adapter with a malicious/buggy source
    response. The effect is already handled by the Owner; none of these
    negative cases permits a new physical dispatch or attaches foreign
    Job evidence to the saved Harness request.
    """
    client = GatewayExecutionFixture()
    original = client.call_tool

    def tamper(name, arguments):
        is_error, payload = original(name, arguments)
        expected_tool = {
            "submit": "execution.submit",
            "observe": "execution.get",
            "resolve": "execution.resolve",
            "cancel": "execution.cancel",
        }[path]
        if name == expected_tool:
            payload = dict(payload)
            if mutation == "unhashable_list":
                payload["delivery_disposition"] = ["committed"]
            elif mutation == "unhashable_dict":
                payload["delivery_disposition"] = {"state": "committed"}
            elif mutation == "wrong_owner":
                payload["owner_id"] = "runtime.windows"
            elif mutation == "wrong_capability":
                payload["capability"] = "execution.windows"
            elif mutation == "wrong_operation_job":
                payload["operation_ref"] = "ordivon-exec:v1:runtime.linux:job:foreign"
        return is_error, payload

    client.call_tool = tamper  # type: ignore[method-assign]
    factory = _factory(client)
    adapter = GatewayMcpRuntimeAdapter(factory.component, client, factory.execution_grant)
    request_id = "request:owner-evidence"
    submission = {
        "clientRequestId": request_id,
        "execution": {
            "workspaceId": "ws-plugin-h2",
            "foreignReferences": [],
            "executable": "/usr/bin/rg",
            "args": ["needle", "."],
        },
    }
    if path == "submit":
        with pytest.raises(HarnessRuntimeClientError):
            adapter.call_tool("workspace.exec", submission)
        assert adapter._operation_refs == {}
        assert adapter._operation_requests == {}
    elif path == "resolve":
        with pytest.raises(HarnessRuntimeClientError):
            adapter.call_tool(
                "task.list",
                {"workspaceId": "ws-plugin-h2", "clientRequestId": request_id},
            )
        assert adapter._operation_refs == {}
        assert adapter._operation_requests == {}
    else:
        # A trusted earlier request was observed, so only the later
        # untrusted Owner observation/cancel result is changed.
        adapter._operation_refs[client.native_id] = client.operation_ref
        adapter._operation_requests[client.native_id] = request_id
        if path == "observe":
            with pytest.raises(HarnessRuntimeClientError):
                adapter.call_tool("task.observe", {"jobId": client.native_id, "waitMs": 0})
        else:
            with pytest.raises(HarnessRuntimeClientError):
                adapter.cancel_job(client.native_id)
        assert adapter._operation_refs == {client.native_id: client.operation_ref}
        assert adapter._operation_requests == {client.native_id: request_id}


@pytest.mark.parametrize(
    ("path", "shadow_field", "shadow_value"),
    (
        ("submit", "ownerId", "runtime.windows"),
        ("submit", "operationRef", "ordivon-exec:v1:runtime.linux:job-unrelated"),
        ("submit", "nativeId", "job-unrelated"),
        ("submit", "deliveryDisposition", "unknown"),
        ("resolve", "ownerId", "runtime.windows"),
        ("resolve", "operationRef", "ordivon-exec:v1:runtime.linux:job-unrelated"),
        ("resolve", "nativeId", "job-unrelated"),
        ("resolve", "workspaceId", "ws-unrelated"),
        ("observe", "ownerId", "runtime.windows"),
        ("observe", "operationRef", "ordivon-exec:v1:runtime.linux:job-unrelated"),
        ("observe", "nativeId", "job-unrelated"),
        ("observe", "deliveryDisposition", "unknown"),
        # Python considers 0 == False; JSON does not. Both aliases present
        # with unequal token TYPES are a source contradiction, not equality.
        ("observe", "artifactCount", False),
        ("observe", "recoveryRequired", 0),
        ("cancel", "ownerId", "runtime.windows"),
        ("cancel", "operationRef", "ordivon-exec:v1:runtime.linux:job-unrelated"),
        ("cancel", "nativeId", "job-unrelated"),
        ("cancel", "deliveryDisposition", "unknown"),
    ),
)
def test_gateway_owner_shadow_alias_conflict_must_not_bind_foreign_job(
    path: str, shadow_field: str, shadow_value: str
) -> None:
    """Both valid wire aliases with conflicting values cannot express one Owner fact.

    This falsifies the shared source decoder, not just one endpoint's
    validation. Exact existing snake_case Gateway receipts stay admissible.
    """
    client = GatewayExecutionFixture()
    original = client.call_tool
    operation_name = {
        "submit": "execution.submit",
        "resolve": "execution.resolve",
        "observe": "execution.get",
        "cancel": "execution.cancel",
    }[path]

    def shadow(name, arguments):
        is_error, payload = original(name, arguments)
        if name == operation_name:
            payload = {**payload, shadow_field: shadow_value}
        return is_error, payload

    client.call_tool = shadow  # type: ignore[method-assign]
    factory = _factory(client)
    adapter = GatewayMcpRuntimeAdapter(factory.component, client, factory.execution_grant)
    request_id = "request:shadow-owner"
    submission = {
        "clientRequestId": request_id,
        "execution": {
            "workspaceId": "ws-plugin-h2",
            "foreignReferences": [],
            "executable": "/usr/bin/rg",
            "args": ["needle", "."],
        },
    }
    if path == "submit":
        with pytest.raises(HarnessRuntimeClientError, match="conflicting"):
            adapter.call_tool("workspace.exec", submission)
        assert adapter._operation_refs == {}
        assert adapter._operation_requests == {}
    elif path == "resolve":
        with pytest.raises(HarnessRuntimeClientError, match="conflicting"):
            adapter.call_tool(
                "task.list",
                {"workspaceId": "ws-plugin-h2", "clientRequestId": request_id},
            )
        assert adapter._operation_refs == {}
        assert adapter._operation_requests == {}
    else:
        adapter._operation_refs[client.native_id] = client.operation_ref
        adapter._operation_requests[client.native_id] = request_id
        with pytest.raises(HarnessRuntimeClientError, match="conflicting"):
            if path == "observe":
                adapter.call_tool("task.observe", {"jobId": client.native_id, "waitMs": 0})
            else:
                adapter.cancel_job(client.native_id)
        assert adapter._operation_refs == {client.native_id: client.operation_ref}
        assert adapter._operation_requests == {client.native_id: request_id}


@pytest.mark.parametrize("path", ("submit", "resolve", "observe", "cancel"))
def test_gateway_equal_wire_aliases_preserve_one_source_fact(path: str) -> None:
    """A redundant alias with an identical JSON value is not schema drift."""
    client = GatewayExecutionFixture()
    base = client.call_tool
    endpoint = {
        "submit": "execution.submit",
        "resolve": "execution.resolve",
        "observe": "execution.get",
        "cancel": "execution.cancel",
    }[path]

    def equal_wire_aliases(name, arguments):
        is_error, payload = base(name, arguments)
        if name == endpoint:
            payload = {
                **payload,
                "ownerId": payload["owner_id"],
                "nativeId": payload["native_id"],
                "operationRef": payload["operation_ref"],
            }
        return is_error, payload

    client.call_tool = equal_wire_aliases  # type: ignore[method-assign]
    factory = _factory(client)
    adapter = GatewayMcpRuntimeAdapter(factory.component, client, factory.execution_grant)
    request_id = "request:equal-owner-source"
    if path == "submit":
        reply = adapter.call_tool(
            "workspace.exec",
            {
                "clientRequestId": request_id,
                "execution": {
                    "workspaceId": "ws-plugin-h2",
                    "foreignReferences": [],
                    "executable": "/usr/bin/rg",
                },
            },
        )
        assert reply["jobId"] == client.native_id
    elif path == "resolve":
        reply = adapter.call_tool(
            "task.list",
            {"workspaceId": "ws-plugin-h2", "clientRequestId": request_id},
        )
        assert reply["jobs"][0]["jobId"] == client.native_id
    else:
        adapter._operation_refs[client.native_id] = client.operation_ref
        adapter._operation_requests[client.native_id] = request_id
        if path == "observe":
            reply = adapter.call_tool("task.observe", {"jobId": client.native_id, "waitMs": 0})
            assert reply["jobId"] == client.native_id
        else:
            _, reply = adapter.cancel_job(client.native_id)
            assert reply["jobId"] == client.native_id


@pytest.mark.parametrize("path", ("submit_nonterminal", "submit_terminal", "cancel"))
def test_gateway_owner_optional_delivery_is_still_source_compatible(path: str) -> None:
    """The Gateway DTO permits None; a present malformed value must not pass."""
    client = GatewayExecutionFixture()
    original = client.call_tool

    def source_optional(name, arguments):
        is_error, payload = original(name, arguments)
        payload = dict(payload)
        if name == "execution.submit":
            payload["delivery_disposition"] = None
            if path == "submit_terminal":
                payload["terminal"] = True
                payload["state"] = "succeeded"
        if name == "execution.cancel":
            payload["delivery_disposition"] = None
        return is_error, payload

    client.call_tool = source_optional  # type: ignore[method-assign]
    factory = _factory(client)
    adapter = GatewayMcpRuntimeAdapter(factory.component, client, factory.execution_grant)
    source_request = {
        "clientRequestId": "request:source-optional",
        "execution": {
            "workspaceId": "ws-plugin-h2",
            "foreignReferences": [],
            "executable": "/usr/bin/rg",
        },
    }
    first = adapter.call_tool("workspace.exec", source_request)
    if path == "submit_nonterminal":
        assert first["deliveryDisposition"] == "in_progress"
    elif path == "submit_terminal":
        assert first["deliveryDisposition"] == "committed"
        assert first["resultAvailable"] is True
    else:
        result, payload = adapter.cancel_job(client.native_id)
        assert result == "cancel-requested"
        assert payload["jobId"] == client.native_id


@pytest.mark.parametrize(
    "tamper",
    ("wrong_owner", "wrong_capability", "wrong_operation_job", "unhashable_delivery"),
)
def test_real_pg_harness_stays_unknown_when_gateway_owner_identity_cannot_be_proven(
    tamper: str, pg_schema
) -> None:
    """Actual Python Harness Postgres source never attaches a foreign Job receipt.

    This test deliberately does NOT execute a physical Owner effect. A real
    Gateway with Runtime Owner credential is a separate authorization
    boundary. The source PG Run/Intent and UNKNOWN recovery are real.
    """
    client = GatewayExecutionFixture()
    original = client.call_tool

    def forge(name, arguments):
        is_error, payload = original(name, arguments)
        if name in {"execution.submit", "execution.resolve"}:
            payload = dict(payload)
            if tamper == "wrong_owner":
                payload["owner_id"] = "runtime.windows"
            elif tamper == "wrong_capability":
                payload["capability"] = "execution.windows"
            elif tamper == "wrong_operation_job":
                payload["operation_ref"] = "ordivon-exec:v1:runtime.linux:job:other"
            elif name == "execution.submit":
                payload["delivery_disposition"] = ["committed"]
            else:
                payload["owner_id"] = "runtime.windows"
        return is_error, payload

    client.call_tool = forge  # type: ignore[method-assign]
    factory = _factory(client)
    run = HarnessAgentRun.create(
        pg_schema[0],
        pg_schema[1],
        _contract(factory),
        lambda _contract: _adapter(),
        tool_bridge_factory=factory,
        clock_ms=FixedClock(),
        monotonic_ms=FixedClock(),
    )
    result = run.run(())
    assert result.loop_result.stop_code.value == "runtime_unknown"
    names = [name for name, _ in client.calls]
    assert names.count("execution.submit") == 1
    assert names.count("execution.resolve") == 1
    assert "execution.get" not in names
    with PostgresHarnessStore(pg_schema[0], schema=pg_schema[1]) as store:
        continuity = EventSourcedRunContinuity.open(store, "harness-run:plugin-h2")
        step = continuity.load_current_tool_step()
        assert step.fence is not None
        assert step.receipt is None or step.receipt.status.value != "observed"


@pytest.mark.parametrize("forged", ["ws-another-agent", "", 1, False])
def test_terminal_observation_rejects_wrong_runtime_workspace_resolution(forged: object) -> None:
    class ForeignResolution(GatewayExecutionFixture):
        def call_tool(self, name, arguments):
            error, payload = super().call_tool(name, arguments)
            if name == "execution.resolve":
                payload = dict(payload)
                payload["workspace_id"] = forged
            return error, payload

    client = ForeignResolution()
    adapter = GatewayMcpRuntimeAdapter(
        AgentPluginMcpComponent(
            name="ordivon-gateway",
            transport="streamable-http",
            url="https://gateway-mcp.ordivon.com/mcp",
        ),
        client,
        _factory(client).execution_grant,
    )
    adapter._operation_refs[client.native_id] = client.operation_ref
    adapter._operation_requests[client.native_id] = "req-owned"
    with pytest.raises(HarnessRuntimeClientError):
        adapter.call_tool("task.observe", {"jobId": client.native_id, "waitMs": 0})
    assert [x[0] for x in client.calls] == ["execution.get", "execution.resolve"]


def test_terminal_observation_absent_resolution_remains_unknown() -> None:
    class MissingResolution(GatewayExecutionFixture):
        def call_tool(self, name, arguments):
            error, payload = super().call_tool(name, arguments)
            if name == "execution.resolve":
                payload = dict(payload)
                payload["resolution"] = "absent"
            return error, payload

    client = MissingResolution()
    adapter = GatewayMcpRuntimeAdapter(
        AgentPluginMcpComponent(
            name="ordivon-gateway",
            transport="streamable-http",
            url="https://gateway-mcp.ordivon.com/mcp",
        ),
        client,
        _factory(client).execution_grant,
    )
    adapter._operation_refs[client.native_id] = client.operation_ref
    adapter._operation_requests[client.native_id] = "req-owned"
    result = adapter.call_tool("task.observe", {"jobId": client.native_id, "waitMs": 0})
    assert result["executionTerminal"] is True
    assert result["deliveryDisposition"] == "reconciliation_required"
    assert result["recoveryRequired"] is True
    assert result["resultAvailable"] is False


def test_terminal_observation_confirms_original_grant_without_new_gateway_schema() -> None:
    client = GatewayExecutionFixture()
    adapter = GatewayMcpRuntimeAdapter(
        AgentPluginMcpComponent(
            name="ordivon-gateway",
            transport="streamable-http",
            url="https://gateway-mcp.ordivon.com/mcp",
        ),
        client,
        _factory(client).execution_grant,
    )
    adapter._operation_refs[client.native_id] = client.operation_ref
    adapter._operation_requests[client.native_id] = "req-owned"
    result = adapter.call_tool("task.observe", {"jobId": client.native_id, "waitMs": 0})
    assert result["resultAvailable"] is True
    assert not result["recoveryRequired"]
    assert [x[0] for x in client.calls] == ["execution.get", "execution.resolve"]


def test_two_real_pg_harness_runs_share_workspace_without_cross_run_release(pg_schema) -> None:
    from dataclasses import replace

    # Native Runtime's Workspace grant is not an exclusive long-lived consumer
    # claim. Independent PG Run histories can refer to the same Workspace.
    # Completing A MUST NOT be treated as authority to close it for B.
    client = GatewayExecutionFixture()
    factory = _factory(client)
    original = _contract(factory)
    overlapping = replace(
        original,
        harness_run_id="harness-run:plugin-h2-second-consumer",
        caller_run_ref="trial:plugin-h2-second-consumer",
    )
    clock = FixedClock()
    first = HarnessAgentRun.create(
        pg_schema[0],
        pg_schema[1],
        original,
        lambda _contract: _adapter(),
        tool_bridge_factory=factory,
        clock_ms=clock,
        monotonic_ms=clock,
    )
    second = HarnessAgentRun.create(
        pg_schema[0],
        pg_schema[1],
        overlapping,
        lambda _contract: _adapter(),
        tool_bridge_factory=factory,
        clock_ms=clock,
        monotonic_ms=clock,
    )
    assert first.harness_run_id != second.harness_run_id
    assert factory.execution_grant.workspace_id == "ws-plugin-h2"

    result_a = first.run(())
    assert result_a.loop_result.stop_code.value == "candidate_completed"
    assert first.inspect_terminal().receipt.harness_run_id == original.harness_run_id
    with pytest.raises(KeyError, match="no independent terminal result"):
        second.inspect_terminal()
    # B's lack of a terminal record is durable PG readback, not authorization
    # for a cross-Run consumerReleased=true.
    with PostgresHarnessStore(pg_schema[0], schema=pg_schema[1]) as store:
        projection = store.load_run(second.harness_run_id)
        assert projection.status.terminal is False


# R8 B: source-only Workspace-bound admission consumer contract.  These
# fixtures prove control flow and non-dispatch only; they are NOT a trusted
# RuntimePG Claim issuer or proof that the installed native Owner is HELD.


class _SourceOnlyWorkspaceAdmission:
    def __init__(self, *, deny_turn: bool = False, deny_effect: bool = False) -> None:
        self.deny_turn = deny_turn
        self.deny_effect = deny_effect
        self.turns: list[dict[str, str]] = []
        self.effects: list[dict[str, str]] = []

    def require_turn_ready(self, **kwargs) -> None:
        self.turns.append(kwargs)
        if self.deny_turn:
            raise HarnessWorkspaceAdmissionUnavailable("no qualified RuntimePG HELD claim")

    def require_effect_ready(self, **kwargs) -> None:
        self.effects.append(kwargs)
        if self.deny_effect:
            raise HarnessWorkspaceAdmissionUnavailable("original Runtime issuer claim revoked")


def _effect_request_for_claim_contract() -> dict:
    return {
        "clientRequestId": "request:harness-r8-b-source-only",
        "execution": {
            "workspaceId": "ws-plugin-h2",
            "executable": "/usr/bin/rg",
            "args": [],
            "foreignReferences": [],
        },
    }


def test_r8_strict_gateway_submission_refuses_missing_native_claim_port() -> None:
    client = GatewayExecutionFixture()
    factory = _factory(client)
    adapter = GatewayMcpRuntimeAdapter(
        factory.component,
        client,
        factory.execution_grant,
        run_ref="harness-run:plugin-h2",
        grant_digest=factory.grant_digest,
        require_workspace_admission=True,
    )
    with pytest.raises(HarnessWorkspaceAdmissionUnavailable, match="certified"):
        adapter.call_tool("workspace.exec", _effect_request_for_claim_contract())
    assert client.calls == []


def test_r8_gateway_owner_call_not_dispatched_when_qualified_port_denies() -> None:
    client = GatewayExecutionFixture()
    factory = _factory(client)
    admission = _SourceOnlyWorkspaceAdmission(deny_effect=True)
    adapter = GatewayMcpRuntimeAdapter(
        factory.component,
        client,
        factory.execution_grant,
        run_ref="harness-run:plugin-h2",
        grant_digest=factory.grant_digest,
        workspace_admission=admission,
        require_workspace_admission=True,
    )
    with pytest.raises(HarnessWorkspaceAdmissionUnavailable, match="revoked"):
        adapter.call_tool("workspace.exec", _effect_request_for_claim_contract())
    assert client.calls == []
    assert admission.effects == [
        {
            "run_ref": "harness-run:plugin-h2",
            "workspace_id": "ws-plugin-h2",
            "tool_grant_digest": factory.grant_digest,
            "runtime_operation": "workspace.exec",
            "client_request_id": "request:harness-r8-b-source-only",
        }
    ]


def test_r8_workspace_bound_bridge_turn_hook_has_exact_frozen_grant(pg_schema) -> None:
    client = GatewayExecutionFixture()
    factory = _factory(client)
    contract = _contract(factory)
    clock = FixedClock()
    HarnessAgentRun.create(
        pg_schema[0], pg_schema[1], contract, lambda _: _adapter(),
        tool_bridge_factory=factory, clock_ms=clock, monotonic_ms=clock,
    )
    with PostgresHarnessStore(pg_schema[0], schema=pg_schema[1]) as store:
        continuity = EventSourcedRunContinuity.open(store, contract.harness_run_id)
        legacy_bridge = factory.build(contract, continuity)
        with pytest.raises(HarnessWorkspaceAdmissionUnavailable, match="not installed"):
            legacy_bridge.require_workspace_turn_ready(turn_id="turn:r8-b-first")
    admission = _SourceOnlyWorkspaceAdmission()
    strict_factory = PluginGatewayExecutionBridgeFactory(
        factory.component, client, factory.execution_grant,
        workspace_admission=admission, require_workspace_admission=True,
    )
    with PostgresHarnessStore(pg_schema[0], schema=pg_schema[1]) as store:
        continuity = EventSourcedRunContinuity.open(store, contract.harness_run_id)
        strict_bridge = strict_factory.build(contract, continuity)
        strict_bridge.require_workspace_turn_ready(turn_id="turn:r8-b-first")
        strict_bridge.require_workspace_turn_ready()  # A Loop PreTurn needs no fabricated TurnId.
    assert admission.turns == [
        {
            "run_ref": contract.harness_run_id,
            "workspace_id": factory.execution_grant.workspace_id,
            "tool_grant_digest": contract.tool_grant_digest,
            "turn_id": turn_id,
        }
        for turn_id in ("turn:r8-b-first", None)
    ]
    assert client.calls == []


def test_r8_pg_tool_intent_is_rejected_without_remote_dispatch_on_claim_loss(pg_schema) -> None:
    client = GatewayExecutionFixture()
    original = _factory(client)
    admission = _SourceOnlyWorkspaceAdmission(deny_effect=True)
    strict_factory = PluginGatewayExecutionBridgeFactory(
        original.component, client, original.execution_grant,
        workspace_admission=admission, require_workspace_admission=True,
    )
    contract = _contract(strict_factory)
    clock = FixedClock()
    run = HarnessAgentRun.create(
        pg_schema[0], pg_schema[1], contract, lambda _: _adapter(),
        tool_bridge_factory=strict_factory, clock_ms=clock, monotonic_ms=clock,
    )
    run.run(())
    assert not any(name == "execution.submit" for name, _ in client.calls)
    assert len(admission.effects) == 1
    with PostgresHarnessStore(pg_schema[0], schema=pg_schema[1]) as store:
        current = EventSourcedRunContinuity.open(
            store, contract.harness_run_id
        ).load_current_tool_step()
        assert current.receipt is not None
        assert current.receipt.status.value == "rejected"
        assert current.observation["structuredContent"]["physicalDispatch"] is False


def test_r8_port_transport_loss_before_gateway_send_is_not_runtime_response_loss() -> None:
    client = GatewayExecutionFixture()
    factory = _factory(client)
    admission = _SourceOnlyWorkspaceAdmission()

    def lost_owner_readback(**_kwargs) -> None:
        raise HarnessRuntimeClientError("MCP claim.get response unknown")

    admission.require_effect_ready = lost_owner_readback
    adapter = GatewayMcpRuntimeAdapter(
        factory.component,
        client,
        factory.execution_grant,
        workspace_admission=admission,
        require_workspace_admission=True,
        run_ref="harness-run:plugin-h2",
        grant_digest=factory.grant_digest,
    )
    with pytest.raises(
        HarnessWorkspaceAdmissionUnavailable, match="qualification unavailable"
    ):
        adapter.call_tool("workspace.exec", _effect_request_for_claim_contract())
    assert client.calls == []


def test_r8_pg_owner_readback_error_refuses_effect_without_job_reconciliation(pg_schema) -> None:
    client = GatewayExecutionFixture()
    original = _factory(client)
    admission = _SourceOnlyWorkspaceAdmission()

    def lost_owner_readback(**_kwargs) -> None:
        raise HarnessRuntimeClientError("native PG claim.get timed out")

    admission.require_effect_ready = lost_owner_readback
    strict_factory = PluginGatewayExecutionBridgeFactory(
        original.component,
        client,
        original.execution_grant,
        workspace_admission=admission,
        require_workspace_admission=True,
    )
    contract = _contract(strict_factory)
    clock = FixedClock()
    run = HarnessAgentRun.create(
        pg_schema[0], pg_schema[1], contract, lambda _: _adapter(),
        tool_bridge_factory=strict_factory, clock_ms=clock, monotonic_ms=clock,
    )
    run.run(())
    # The trusted Claim Port did not send physical execution. Looking up a Job
    # here would conflate a pre-submit auth uncertainty with a post-submit
    # ambiguous effect and could attach unrelated Owner effects.
    assert client.calls == []
    with PostgresHarnessStore(pg_schema[0], schema=pg_schema[1]) as store:
        step = EventSourcedRunContinuity.open(
            store, contract.harness_run_id
        ).load_current_tool_step()
        assert step.receipt is not None
        assert step.receipt.status.value == "rejected"
        assert step.observation["structuredContent"]["physicalDispatch"] is False


def test_r8_qualified_gateway_timeout_projection_remains_exact_before_submit() -> None:
    """The same frozen timeout must reach Gateway after a claim readback.

    This Source TestDouble is NOT a native issuer. The existing formal AST
    observer currently rejects the post-projection claim guard; Formal Owner
    must refine the exact guarded-effect source frame independently.
    """
    client = GatewayExecutionFixture()
    factory = _factory(client)
    admission = _SourceOnlyWorkspaceAdmission()
    adapter = GatewayMcpRuntimeAdapter(
        factory.component,
        client,
        factory.execution_grant,
        workspace_admission=admission,
        require_workspace_admission=True,
        run_ref="harness-run:plugin-h2",
        grant_digest=factory.grant_digest,
    )
    request = _effect_request_for_claim_contract()
    request["execution"]["timeoutMs"] = 1_234
    result = adapter.call_tool("workspace.exec", request)
    assert isinstance(result, dict)
    assert len(admission.effects) == 1
    assert len(client.calls) == 1
    operation, args = client.calls[0]
    assert operation == "execution.submit"
    assert args["timeoutMs"] == 1_234
    assert args["requestId"] == request["clientRequestId"]
    assert args["workspaceId"] == factory.execution_grant.workspace_id
    assert request["execution"]["timeoutMs"] == 1_234


def test_r8_bogus_bool_workspace_admission_is_not_native_qualification() -> None:
    """An externally injected TestDouble returning False cannot mint HELD."""
    client = GatewayExecutionFixture()
    factory = _factory(client)
    admission = _SourceOnlyWorkspaceAdmission()
    admission.require_effect_ready = lambda **_kwargs: False
    adapter = GatewayMcpRuntimeAdapter(
        factory.component,
        client,
        factory.execution_grant,
        workspace_admission=admission,
        require_workspace_admission=True,
        run_ref="harness-run:plugin-h2",
        grant_digest=factory.grant_digest,
    )
    with pytest.raises(HarnessWorkspaceAdmissionUnavailable, match="unauthenticated"):
        adapter.call_tool("workspace.exec", _effect_request_for_claim_contract())
    assert client.calls == []


@pytest.mark.parametrize(
    ("inventory_fault", "expected_error"),
    (
        ("missing-total", "artifactCount"),
        ("repeated-identity", "artifact"),
    ),
)
def test_gateway_committed_inventory_cannot_forge_complete_artifact_id_set(
    inventory_fault: str, expected_error: str
) -> None:
    """An upstream summary Boolean alone cannot certify a complete identity set.

    The current Gateway Owner normally checks duplicate IDs and supplies the
    count. Harden the Harness consumer against partial/mixed-version Owner
    projections without inventing any Artifact type or digest.
    """
    class IncompleteIdentityProjection(GatewayExecutionFixture):
        def call_tool(self, name, arguments):
            is_error, payload = super().call_tool(name, arguments)
            if name == "execution.get":
                payload["artifact_projection_complete"] = True
                payload["delivery_disposition"] = "committed"
                if inventory_fault == "missing-total":
                    payload.pop("artifact_count")
                else:
                    payload["artifact_ids"] = ["same-artifact", "same-artifact"]
                    payload["artifact_count"] = 2
            return is_error, payload

    client = IncompleteIdentityProjection()
    adapter = GatewayMcpRuntimeAdapter(
        _factory(client).component, client, _factory(client).execution_grant
    )
    adapter._operation_requests[client.native_id] = "request:exact-inventory-p0"
    with pytest.raises(HarnessRuntimeClientError, match=expected_error):
        adapter._observe_operation(client.operation_ref, client.native_id, wait_ms=0)


@pytest.mark.parametrize(
    ("fault", "reason"),
    (
        ("missing-recovery", "recoveryRequired"),
        ("null-recovery", "recoveryRequired"),
        ("missing-execution", "executionDisposition"),
        ("uncertain-execution", "executionDisposition"),
        ("unknown-enum", "executionDisposition"),
    ),
)
def test_gateway_terminal_committed_needs_complete_conclusive_runtime_status_before_artifact_read(
    fault: str, reason: str
) -> None:
    """An incomplete Runtime projection must not be promoted to Tool success.

    The Gateway wire observation's two Optional fields are unknown until
    established by the physical Runtime Owner. No model preview read should
    occur under terminal/committed/complete projection alone.
    """

    class UnqualifiedTerminal(GatewayTextArtifacts):
        def call_tool(self, name, arguments):
            is_error, payload = super().call_tool(name, arguments)
            if name == "execution.get":
                payload = dict(payload)
                if fault == "missing-recovery":
                    payload.pop("recovery_required")
                elif fault == "null-recovery":
                    payload["recovery_required"] = None
                elif fault == "missing-execution":
                    payload.pop("execution_disposition")
                elif fault == "uncertain-execution":
                    payload["execution_disposition"] = "lost"
                else:
                    payload["execution_disposition"] = "fake_succeeded"
            return is_error, payload

    client = UnqualifiedTerminal()
    factory = _factory(client)
    adapter = GatewayMcpRuntimeAdapter(
        factory.component,
        client,
        factory.execution_grant,
        artifact_read_enabled=True,
    )
    adapter._operation_requests[client.native_id] = "request:strict-physical-terminal-evidence"
    with pytest.raises(HarnessRuntimeClientError, match=reason):
        adapter._observe_operation(client.operation_ref, client.native_id, wait_ms=0)
    assert [name for name, _ in client.calls] == ["execution.get", "execution.resolve"]


@pytest.mark.parametrize(
    ("fault", "reason"),
    (
        ("queued-terminal", "state"),
        ("working-terminal", "state"),
        ("failed-status-success-disposition", "state"),
        ("succeeded-status-failed-disposition", "state"),
        ("nonzero-success-exit", "exitCode"),
        ("missing-success-exit", "exitCode"),
        ("boolean-success-exit", "exitCode"),
    ),
)
def test_gateway_terminal_owner_state_and_exit_evidence_cannot_launder_tool_success(
    fault: str, reason: str
) -> None:
    """The native Job Owner reports status from the same committed resolution.

    A mixed-version/stale Gateway state or missing/nonzero OS success exit
    must not become a successful Harness Tool message or trigger artifact.read.
    This consumer test does not claim the installed Gateway has emitted such
    a mixed record.
    """

    class ContradictoryOwnerTerminal(GatewayTextArtifacts):
        def call_tool(self, name, arguments):
            is_error, payload = super().call_tool(name, arguments)
            if name == "execution.get":
                payload = dict(payload)
                if fault == "queued-terminal":
                    payload["state"] = "queued"
                elif fault == "working-terminal":
                    payload["state"] = "working"
                elif fault == "failed-status-success-disposition":
                    payload["state"] = "failed"
                elif fault == "succeeded-status-failed-disposition":
                    payload["execution_disposition"] = "failed"
                elif fault == "nonzero-success-exit":
                    payload["exit_code"] = 7
                elif fault == "missing-success-exit":
                    payload.pop("exit_code")
                else:
                    payload["exit_code"] = True
            return is_error, payload

    client = ContradictoryOwnerTerminal()
    factory = _factory(client)
    adapter = GatewayMcpRuntimeAdapter(
        factory.component,
        client,
        factory.execution_grant,
        artifact_read_enabled=True,
    )
    adapter._operation_requests[client.native_id] = "request:owner-terminal-truth"
    with pytest.raises(HarnessRuntimeClientError, match=reason):
        adapter._observe_operation(client.operation_ref, client.native_id, wait_ms=0)
    assert [name for name, _ in client.calls] == ["execution.get", "execution.resolve"]


def test_gateway_bound_request_replay_never_resubmits_before_existing_owner_readback() -> None:
    """A known ToolIntent/Job binding must not produce a second physical submit.

    Different authenticated Gateway principals intentionally namespace the
    *same public requestId* into distinct native request keys. The local
    binding is not an across-process proof, but it must prevent a second
    submit before discovering that the original Owner identity changed.
    """
    client = GatewayExecutionFixture()
    factory = _factory(client)
    adapter = GatewayMcpRuntimeAdapter(factory.component, client, factory.execution_grant)
    execution = {
        "clientRequestId": "request:bound-principal-original",
        "execution": {
            "workspaceId": "ws-plugin-h2",
            "foreignReferences": [],
            "executable": "/usr/bin/rg",
            "args": ["needle"],
            "cwdRelative": ".",
        },
    }
    first = adapter.call_tool("workspace.exec", execution)
    assert first["jobId"] == client.native_id
    replay = adapter.call_tool("workspace.exec", execution)
    assert replay["jobId"] == first["jobId"]
    assert [name for name, _ in client.calls].count("execution.submit") == 1
    assert [name for name, _ in client.calls].count("execution.resolve") >= 1


def test_gateway_bound_request_missing_under_current_principal_is_unknown_without_second_submit() -> None:
    """A changed auth scope can hide the previous Native Job without deleting it.

    No new Gateway submit is permitted when the old local physical Job is
    known but the current verified principal resolves the public key absent.
    """

    class PrincipalChangedGateway(GatewayExecutionFixture):
        hidden_under_new_principal = False

        def call_tool(self, name, arguments):
            if name == "execution.resolve" and self.hidden_under_new_principal:
                self.calls.append((name, dict(arguments)))
                return False, {
                    "schema_version": 1,
                    "kind": "ordivon.gateway-execution-resolution",
                    "request_id": arguments["requestId"],
                    "capability": "execution.linux",
                    "owner_id": "runtime.linux",
                    "resolution": "absent",
                }
            return super().call_tool(name, arguments)

    client = PrincipalChangedGateway()
    factory = _factory(client)
    adapter = GatewayMcpRuntimeAdapter(factory.component, client, factory.execution_grant)
    execution = {
        "clientRequestId": "request:bound-before-auth-scope-change",
        "execution": {
            "workspaceId": "ws-plugin-h2",
            "foreignReferences": [],
            "executable": "/usr/bin/rg",
            "args": ["needle"],
        },
    }
    first = adapter.call_tool("workspace.exec", execution)
    assert first["jobId"] == client.native_id
    client.hidden_under_new_principal = True
    with pytest.raises(HarnessRuntimeClientError, match="bound|existing|original|absent"):
        adapter.call_tool("workspace.exec", execution)
    assert [name for name, _ in client.calls].count("execution.submit") == 1
    assert adapter._operation_requests == {client.native_id: execution["clientRequestId"]}


@pytest.mark.parametrize("strict_guard", ("missing_port", "revoked_port"))
def test_bound_replay_cannot_observe_legacy_job_before_required_workspace_admission(
    strict_guard: str,
) -> None:
    """Gateway GET may reconcile or dispatch in some Legacy Runtime owners.

    No locally bound replay may bypass the required Native effect admission
    just because it avoids a second execution.submit. Unlike the Fresh PG
    observe path, the historical Runtime observe can dispatch an Accepted
    Job. This test is a source-side negative, not an installed OS guarantee.
    """

    class RevokedPort:
        def require_effect_ready(self, **_kwargs):
            raise HarnessWorkspaceAdmissionUnavailable("revoked Native claim")

    client = GatewayExecutionFixture()
    factory = _factory(client)
    adapter = GatewayMcpRuntimeAdapter(
        factory.component,
        client,
        factory.execution_grant,
        workspace_admission=(None if strict_guard == "missing_port" else RevokedPort()),
        require_workspace_admission=True,
        run_ref="run:original-claim" if strict_guard == "revoked_port" else None,
        grant_digest=_digest("original-native-grant") if strict_guard == "revoked_port" else None,
    )
    request_id = "request:strict-bound-original-native-job"
    adapter._operation_requests[client.native_id] = request_id
    adapter._operation_refs[client.native_id] = client.operation_ref
    with pytest.raises(HarnessWorkspaceAdmissionUnavailable):
        adapter.call_tool(
            "workspace.exec",
            {
                "clientRequestId": request_id,
                "execution": {
                    "workspaceId": "ws-plugin-h2",
                    "foreignReferences": [],
                    "executable": "/usr/bin/rg",
                    "args": ["needle"],
                },
            },
        )
    assert client.calls == []


@pytest.mark.parametrize(
    "replay_mutation",
    ("args", "executable", "timeout", "foreignReferences"),
)
def test_gateway_bound_original_job_rejects_same_request_id_but_changed_physical_bytes(
    replay_mutation: str,
) -> None:
    """A local replay must preserve the Owner's exact operation identity.

    The original Runtime would reject idempotency-key reuse with different
    physical request bytes. Replacing submit with resolve/get must not
    silently skip that predicate and return the old Job as if it ran the
    mutated command. This remains an ephemeral source guard; original PG
    durable ToolIntent is the cross-process authority.
    """
    client = GatewayExecutionFixture()
    factory = _factory(client)
    adapter = GatewayMcpRuntimeAdapter(factory.component, client, factory.execution_grant)
    original = {
        "clientRequestId": "request:bound-exact-original-physical-command",
        "execution": {
            "workspaceId": "ws-plugin-h2",
            "foreignReferences": [],
            "executable": "/usr/bin/rg",
            "args": ["needle"],
            "cwdRelative": ".",
            "timeoutMs": 1000,
        },
    }
    first = adapter.call_tool("workspace.exec", original)
    assert first["jobId"] == client.native_id
    replay = {
        "clientRequestId": original["clientRequestId"],
        "execution": dict(original["execution"]),
    }
    changed = replay["execution"]
    if replay_mutation == "args":
        changed["args"] = ["different-search"]
    elif replay_mutation == "executable":
        changed["executable"] = "/usr/bin/false"
    elif replay_mutation == "timeout":
        changed["timeoutMs"] = 900
    else:
        changed["foreignReferences"] = [{
            "namespace": "ordivon.fake",
            "type": "source",
            "id": "unrelated",
            "generation": "1",
            "digest": _digest("foreign"),
        }]
    with pytest.raises(HarnessRuntimeClientError, match="original|bytes|request|digest"):
        adapter.call_tool("workspace.exec", replay)
    assert [name for name, _ in client.calls].count("execution.submit") == 1
    assert [name for name, _ in client.calls].count("execution.get") == 0


def test_gateway_original_run_contract_rejects_factory_workspace_rebind_before_build() -> None:
    """Frozen Run Contract W1 may not construct W2 under the original Tool Grant digest.

    A mutable Factory field is not the authenticated Native issuer. This
    Source-level preflight should reject before even allocating a Tool bridge.
    """
    from dataclasses import replace

    from ordivon_harness.ordivon.tool_errors import ToolBridgeError

    client = GatewayExecutionFixture()
    factory = _factory(client)
    contract = _contract(factory)
    original_digest = contract.tool_grant_digest
    factory.execution_grant = replace(factory.execution_grant, workspace_id="ws-w2-foreign")
    assert factory.grant_digest == original_digest
    assert factory.execution_grant.workspace_id == "ws-w2-foreign"
    from types import SimpleNamespace

    with pytest.raises(ToolBridgeError, match="frozen|drift|Grant|grant"):
        factory.build(contract, SimpleNamespace(harness_run_id=contract.harness_run_id))
    assert [name for name, _ in client.calls if name == "execution.submit"] == []


def test_gateway_paused_original_pg_run_rejects_mutated_factory_workspace_before_tool(
    pg_schema,
) -> None:
    """Real OriginalPG Run Born with W1 must not execute W2 after Factory mutation.

    The Native Tool is a fixture, NOT an observed OS Job: this is a concrete
    Source/PG exposure test pending authenticated Runtime Native Root Birth.
    """
    from dataclasses import replace

    client = GatewayExecutionFixture()
    factory = _factory(client)
    contract = _contract(factory)
    clock = FixedClock()
    run = HarnessAgentRun.create(
        pg_schema[0],
        pg_schema[1],
        contract,
        lambda _contract: _adapter(),
        tool_bridge_factory=factory,
        clock_ms=clock,
        monotonic_ms=clock,
    )
    factory.execution_grant = replace(factory.execution_grant, workspace_id="ws-w2-foreign")
    from ordivon_harness.ordivon.tool_errors import ToolBridgeError

    with pytest.raises(ToolBridgeError, match="frozen|drift|Grant|grant"):
        run.run(())
    assert [args for name, args in client.calls if name == "execution.submit"] == []
    with PostgresHarnessStore(pg_schema[0], schema=pg_schema[1]) as store:
        source = store.load_run(contract.harness_run_id)
        assert source.contract_digest == contract.digest


@pytest.mark.parametrize(
    "grant_field",
    ("workspace_id", "capability", "context", "executable_allowlist", "env_allowlist", "max_timeout_ms"),
)
def test_gateway_factory_rejects_all_material_grant_drift_before_bridge(
    grant_field: str,
) -> None:
    """All caller authority changes must invalidate the *one original* Grant.

    No new store, issuer or extra digest; reuse source canonical grant schema.
    """
    from dataclasses import replace
    from types import SimpleNamespace

    from ordivon_harness.ordivon.tool_errors import ToolBridgeError

    client = GatewayExecutionFixture()
    factory = _factory(client)
    contract = _contract(factory)
    changes = {
        "workspace_id": "ws-w2-rebound",
        "capability": "execution.windows",
        "context": "context:rebound",
        "executable_allowlist": ("/usr/bin/false",),
        "env_allowlist": ("ORDIVON_DIFFERENT",),
        "max_timeout_ms": 9_000,
    }
    factory.execution_grant = replace(factory.execution_grant, **{grant_field: changes[grant_field]})
    assert factory.grant_digest == contract.tool_grant_digest
    with pytest.raises(ToolBridgeError, match="frozen|drift|Grant|grant"):
        factory.build(contract, SimpleNamespace(harness_run_id=contract.harness_run_id))
    assert client.calls == []


@pytest.mark.parametrize("catalog_part", ("remote_recovery_tool", "component_route", "model_tool"))
def test_gateway_factory_rejects_frozen_catalog_drift_before_model_or_tool(
    catalog_part: str,
) -> None:
    """The *same* immutable Run Surface must reach Model and Gateway Tools."""
    from dataclasses import replace
    from types import SimpleNamespace

    from ordivon_harness.ordivon.tool_errors import ToolBridgeError

    client = GatewayExecutionFixture()
    factory = _factory(client)
    contract = _contract(factory)
    if catalog_part == "remote_recovery_tool":
        factory._remote_tool_digests["execution.get"] = _digest("unrelated-tool-spec")
    elif catalog_part == "component_route":
        factory.component = replace(
            factory.component, url="https://other-gateway.ordivon.com/mcp"
        )
    else:
        factory._definition = replace(factory._definition, description="a different model tool")
    assert factory.catalog_digest == contract.tool_catalog_digest
    with pytest.raises(ToolBridgeError, match="frozen|drift|Grant|catalog"):
        factory.build(contract, SimpleNamespace(harness_run_id=contract.harness_run_id))
    assert client.calls == []


def test_gateway_factory_build_uses_one_original_grant_snapshot_after_binding_hook(
    pg_schema, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An adversarial mid-build W1->W2 mutation cannot mix the same RunRoot.

    Source race injection deliberately swaps the mutable Factory attribute
    after the first W1 HarnessExecutionBinding is constructed, but before
    Runtime adapter/bridge construction. A real Native issuer certificate
    is not implied by this Source-level consistency negative.
    """
    from dataclasses import replace

    import ordivon_harness.plugin_gateway_effect as effect

    client = GatewayExecutionFixture()
    factory = _factory(client)
    contract = _contract(factory)
    old_binding_constructor = effect.HarnessExecutionBinding
    original_remote_get_digest = factory._remote_tool_digests["execution.get"]
    original_gateway_url = factory.component.url
    mutations = []

    def swap_factory_after_binding(*args, **kwargs):
        original_binding = old_binding_constructor(*args, **kwargs)
        factory.execution_grant = replace(
            factory.execution_grant, workspace_id="ws-w2-midbuild"
        )
        factory.component = replace(factory.component, url="https://untrusted.example/mcp")
        factory._remote_tool_digests["execution.get"] = _digest("recovery-catalog-midbuild")
        factory._definition.input_schema["properties"]["executable"]["enum"] = ["/usr/bin/false"]
        factory._definition = replace(factory._definition, description="changed after original guard")
        factory.client = GatewayExecutionFixture()
        mutations.append(factory.execution_grant.workspace_id)
        return original_binding

    monkeypatch.setattr(effect, "HarnessExecutionBinding", swap_factory_after_binding)
    with PostgresHarnessStore(pg_schema[0], schema=pg_schema[1]) as store:
        store.create_run(contract)
        continuity = EventSourcedRunContinuity.open(store, contract.harness_run_id)
        bridge = factory.build(contract, continuity)
        assert mutations == ["ws-w2-midbuild"]
        assert bridge.execution_binding.workspace_ref == "ws-plugin-h2"
        assert bridge.runtime.grant.workspace_id == "ws-plugin-h2"
        assert bridge.gateway_grant.workspace_id == "ws-plugin-h2"
        assert bridge.runtime.component.url == original_gateway_url
        assert bridge.runtime.client is client
        assert bridge.gateway_remote_tool_digests["execution.get"] == original_remote_get_digest
        assert bridge.definitions()[0].input_schema["properties"]["executable"]["enum"] == [
            "/usr/bin/rg"
        ]
        assert bridge.definitions()[0].description != "changed after original guard"
        assert bridge.contract.tool_grant_digest == contract.tool_grant_digest
        assert client.calls == []
