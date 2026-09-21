from __future__ import annotations

from pathlib import Path
import tempfile

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
from ordivon_harness.ordivon.sqlite_run_store import SQLiteHarnessRunContinuityStore
from ordivon_harness.plugin_gateway_effect import (
    PluginGatewayExecutionBridgeFactory,
    PluginGatewayExecutionGrant,
)
from ordivon_harness.sqlite_store import SQLiteHarnessStore


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


def _adapter() -> ScriptedTurnAdapter:
    return ScriptedTurnAdapter(
        (
            AgentTurnResult(
                model_call_id="model-call:plugin-h2-tool",
                model_id=ScriptedTurnAdapter.model_id,
                content="execute",
                tool_calls=(
                    AgentToolCall(
                        tool_call_id="tool-call:plugin-h2",
                        name="execution.submit",
                        arguments={
                            "executable": "/usr/bin/rg",
                            "args": ["needle", "."],
                            "cwdRelative": ".",
                            "env": {"ORDIVON_TEST": "1"},
                            "timeoutMs": 5_000,
                        },
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


def test_gateway_effect_bridge_commits_intent_and_fence_before_physical_dispatch() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        observed_pre_dispatch = {"checked": False}

        def probe(arguments) -> None:
            with SQLiteHarnessStore(root) as store:
                continuity = SQLiteHarnessRunContinuityStore.open(store, "harness-run:plugin-h2")
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
            root,
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
        assert names == ["execution.submit", "execution.get"]
        submit = client.calls[0][1]
        assert submit["capability"] == "execution.linux"
        assert submit["workspaceId"] == "ws-plugin-h2"
        assert submit["executable"] == "/usr/bin/rg"
        assert submit["requestId"].startswith("request:harness-gateway:")


def test_gateway_effect_bridge_reconciles_response_loss_without_redispatch() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        client = GatewayExecutionFixture(response_loss=True)
        factory = _factory(client)
        contract = _contract(factory)
        clock = FixedClock()
        adapter = _adapter()
        run = HarnessAgentRun.create(
            root,
            contract,
            lambda _contract: adapter,
            tool_bridge_factory=factory,
            clock_ms=clock,
            monotonic_ms=clock,
        )
        result = run.run(())

        assert result.loop_result.stop_code.value == "candidate_completed"
        names = [name for name, _ in client.calls]
        assert names == ["execution.submit", "execution.resolve", "execution.get"]
        assert names.count("execution.submit") == 1
        assert client.calls[1][1]["requestId"] == client.calls[0][1]["requestId"]

        with SQLiteHarnessStore(root) as store:
            continuity = SQLiteHarnessRunContinuityStore.open(store, "harness-run:plugin-h2")
            step = continuity.load_current_tool_step()
            assert step.receipt is not None
            assert step.receipt.reconciled is True
            assert step.receipt.runtime_job_ref == "job-h2"

        tool_messages = [
            message for message in adapter.requests[1].messages if message.get("role") == "tool"
        ]
        assert len(tool_messages) == 1
        assert tool_messages[0]["observation"]["status"] == "observed"


def test_gateway_effect_bridge_propagates_cooperative_control_cancellation() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        clock = FixedClock()
        cancellation = CancellationToken(monotonic_ms=clock)
        client = GatewayExecutionFixture(cancellation=cancellation)
        factory = _factory(client)
        contract = _contract(factory)
        adapter = _adapter()
        run = HarnessAgentRun.create(
            root,
            contract,
            lambda _contract: adapter,
            tool_bridge_factory=factory,
            clock_ms=clock,
            monotonic_ms=clock,
        )
        result = run.run((), cancellation=cancellation)

        names = [name for name, _ in client.calls]
        assert names == ["execution.submit", "execution.cancel"]
        assert result.loop_result.stop_code.value == "cancel_unknown"

        with SQLiteHarnessStore(root) as store:
            continuity = SQLiteHarnessRunContinuityStore.open(store, "harness-run:plugin-h2")
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
