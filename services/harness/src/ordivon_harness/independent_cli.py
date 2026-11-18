from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from anc_canonical import JsonValue, validate_json_value

from .agent_run import HarnessAgentRun
from .agent_plugin import AgentPluginMcpComponent
from .mcp_http_client import LoopbackMcpEndpoint, OfficialMcpClient
from .plugin_gateway_effect import (
    PluginGatewayExecutionBridgeFactory,
    PluginGatewayExecutionGrant,
)
from .core_contracts import HarnessRunContract
from .independent_result import IndependentRunRecorder, StoredIndependentRunResult
from .ordivon.deepseek import DeepSeekSettings, DeepSeekTurnAdapter
from .ordivon.model import AgentTurnAdapter
from .ordivon.agent_bridge import (
    NO_TOOL_AGENT_GRANT_DIGEST,
    NO_TOOL_AGENT_SURFACE_DIGEST,
)
from .ordivon.run_continuity import EventSourcedRunContinuity
from .postgres_store import PostgresHarnessStore, configured_postgres
from .standalone import HarnessAgentExecution
from .store import HarnessRunStatus


def dispatch(args, *, clock_ms) -> dict[str, object]:
    command = args.command
    if command == "gateway-profile":
        gateway = _gateway_factory(args, required=True)
        assert gateway is not None
        return {
            "ok": True,
            "kind": "ordivon.harness-gateway-execution-profile",
            "toolCatalogDigest": gateway.catalog_digest,
            "toolGrantDigest": gateway.grant_digest,
            "modelToolDefinition": gateway._definition.to_dict(),
            "proofBoundary": (
                "current authenticated MCP Tool schema and caller grant only; "
                "not a committed Harness Run or permission for physical effects"
            ),
        }

    # Verify the selected Gateway Tool surface before touching PG. Incomplete
    # configurations cannot create a stray Run or make an ambient send.
    gateway = _gateway_factory(args) if command in {"run", "resume"} else None
    native_claim = _native_claim_client(args, gateway) if command in {"run", "resume"} else None
    dsn, schema = configured_postgres()

    def store_factory() -> PostgresHarnessStore:
        return PostgresHarnessStore(dsn, schema=schema)

    if command == "doctor":
        with store_factory() as store:
            return {
                "ok": True,
                "authority": "independent-harness-run",
                "backend": "postgresql",
                "stateRoot": None,
                "storageBackend": "postgresql",
                "schema": schema,
                "store": store.doctor(full=True),
            }
    if command == "status":
        with store_factory() as store:
            return {
                "ok": True,
                "authority": "independent-harness-run",
                "backend": "postgresql",
                "stateRoot": None,
                "storageBackend": "postgresql",
                "schema": schema,
                "run": store.load_run(args.harness_run_id).to_dict(),
            }
    if command == "inspect":
        with store_factory() as store:
            return _inspect(store, args.harness_run_id, schema=schema, clock_ms=clock_ms)
    if command == "explain":
        with store_factory() as store:
            inspected = _inspect(store, args.harness_run_id, schema=schema, clock_ms=clock_ms)
            inspected["proofBoundaries"] = {
                "durable": (
                    "Run/Contract/Provider/Snapshot/Recovery objects are exact Harness "
                    "Journal/CAS projections"
                ),
                "processLocal": (
                    "fresh durable inspection does not infer whether an application-owned "
                    "Adapter or Runtime client is currently live; use HarnessAgentRun.explain() "
                    "for validated in-process composition"
                ),
                "external": "Provider/Runtime/domain liveness and world truth are not claimed",
            }
            return inspected
    if command == "run":
        contract = _load_contract(args.contract)
        if gateway is None:
            if (
                contract.tool_catalog_digest != NO_TOOL_AGENT_SURFACE_DIGEST
                or contract.tool_grant_digest != NO_TOOL_AGENT_GRANT_DIGEST
            ):
                raise ValueError(
                    "Tool-bearing independent Runs need an explicit authenticated Gateway "
                    "configuration; no implicit execution authority is granted"
                )
        else:
            _require_matching_gateway_contract(contract, gateway)
        messages = _load_messages(args)
        if not messages:
            raise ValueError("independent run requires at least one input message")
        handle = HarnessAgentRun.create(
            dsn,
            schema,
            contract,
            lambda exact_contract: _adapter(exact_contract, args),
            tool_bridge_factory=gateway,
            workspace_claim_client=native_claim,
            clock_ms=clock_ms,
            monotonic_ms=clock_ms,
        )
        status = handle.status()
        if status["status"] in {
            HarnessRunStatus.STOPPED.value,
            HarnessRunStatus.COMPLETED.value,
            HarnessRunStatus.FAILED.value,
        }:
            with store_factory() as store:
                return _inspect(store, contract.harness_run_id, schema=schema, clock_ms=clock_ms)
        if status["status"] == HarnessRunStatus.PAUSED.value:
            raise ValueError("paused independent Harness Run requires resume")
        execution = handle.run(messages)
        with store_factory() as store:
            return _execution_value(execution, schema=schema, store=store)
    if command == "resume":
        handle = HarnessAgentRun.open(
            dsn,
            schema,
            args.harness_run_id,
            lambda exact_contract: _adapter(exact_contract, args),
            tool_bridge_factory=gateway,
            workspace_claim_client=native_claim,
            clock_ms=clock_ms,
            monotonic_ms=clock_ms,
        )
        execution = handle.resume(additional_messages=_load_messages(args))
        with store_factory() as store:
            return _execution_value(execution, schema=schema, store=store)
    raise ValueError(f"unsupported independent Harness command: {command}")


def _native_claim_client(args, gateway: PluginGatewayExecutionBridgeFactory | None):
    """Use an independently authenticated Runtime physical owner, not Gateway routing.

    No bearer or native authority is copied into the Harness PG, Gateway
    execution projection, or the model-facing Tool grant.
    """
    url = getattr(args, "runtime_claim_url", None)
    bearer = getattr(args, "runtime_claim_bearer_token_file", None)
    if gateway is None:
        if url is not None or bearer is not None:
            raise ValueError("native Workspace Claim requires a Workspace-bearing Gateway Run")
        return None
    if not url or bearer is None:
        raise ValueError(
            "Gateway Workspace Run requires --runtime-claim-url and "
            "--runtime-claim-bearer-token-file; no unprotected fallback"
        )
    component = (
        LoopbackMcpEndpoint(url, name="ordivon-runtime-native-claim")
        if url.startswith("http://")
        else AgentPluginMcpComponent(
            name="ordivon-runtime-native-claim", transport="streamable-http", url=url,
        )
    )
    return OfficialMcpClient(component, bearer_token_file=bearer)


def _gateway_factory(args, *, required: bool = False) -> PluginGatewayExecutionBridgeFactory | None:
    url = getattr(args, "gateway_url", None)
    workspace = getattr(args, "gateway_workspace_id", None)
    executables = getattr(args, "gateway_executable", ())
    env_variables = getattr(args, "gateway_env_variable", ())
    bearer_file = getattr(args, "gateway_bearer_token_file", None)
    context = getattr(args, "gateway_context", None)
    timeout_ms = getattr(args, "gateway_max_timeout_ms", 300_000)
    if not url:
        if required or workspace or executables or env_variables or bearer_file or context:
            raise ValueError(
                "Gateway execution configuration is incomplete: --gateway-url is required"
            )
        return None
    if not workspace or not executables or bearer_file is None:
        raise ValueError(
            "Gateway execution needs --gateway-workspace-id, --gateway-executable "
            "and --gateway-bearer-token-file"
        )
    # Reuse the existing exact 127.0.0.1 MCP endpoint for a first-party
    # installed Gateway. External Agent Plugin endpoints stay HTTPS-only.
    component = (
        LoopbackMcpEndpoint(url, name="ordivon-gateway")
        if url.startswith("http://")
        else AgentPluginMcpComponent(
            name="ordivon-gateway",
            transport="streamable-http",
            url=url,
        )
    )
    grant = PluginGatewayExecutionGrant(
        capability="execution.linux",
        workspace_id=workspace,
        executable_allowlist=tuple(sorted(executables)),
        env_allowlist=tuple(sorted(env_variables)),
        context=context,
        max_timeout_ms=timeout_ms,
    )
    # Reuse the current official SDK-backed MCP client and existing
    # private token-file reader; NEVER place bearer bytes in PG, CLI JSON,
    # logs, plugin metadata or Agent model context.
    client = OfficialMcpClient(component, bearer_token_file=bearer_file)
    return PluginGatewayExecutionBridgeFactory(component, client, grant)


def _require_matching_gateway_contract(
    contract: HarnessRunContract,
    gateway: PluginGatewayExecutionBridgeFactory,
) -> None:
    if (
        contract.tool_catalog_digest != gateway.catalog_digest
        or contract.tool_grant_digest != gateway.grant_digest
    ):
        raise ValueError(
            "Gateway Tool surface/grant changed or belongs to another Run Contract; "
            "use gateway-profile to inspect the current source before Run admission"
        )


def _load_contract(path: Path) -> HarnessRunContract:
    raw = _load_json(path)
    if not isinstance(raw, dict):
        raise ValueError("Harness Run Contract file must contain one JSON object")
    return HarnessRunContract.from_dict(raw)


def _load_messages(args) -> tuple[dict[str, JsonValue], ...]:
    values: list[dict[str, JsonValue]] = []
    path = getattr(args, "messages_json", None)
    if path is not None:
        raw = _load_json(path)
        if not isinstance(raw, list) or any(not isinstance(item, dict) for item in raw):
            raise ValueError("messages JSON must contain an array of objects")
        for item in raw:
            value = dict(item)
            validate_json_value(value)
            values.append(value)
    for message in getattr(args, "message", ()):
        value: dict[str, JsonValue] = {"role": "user", "content": message}
        validate_json_value(value)
        values.append(value)
    return tuple(values)


def _load_json(path: Path) -> Any:
    resolved = path.expanduser().resolve()
    return json.loads(resolved.read_text(encoding="utf-8"))


def _adapter(contract: HarnessRunContract, args) -> AgentTurnAdapter:
    if contract.adapter_id != DeepSeekTurnAdapter.adapter_id:
        raise ValueError(
            "independent CLI execution currently supports only "
            f"{DeepSeekTurnAdapter.adapter_id}; use the Host-free Python API for another Adapter"
        )
    return DeepSeekTurnAdapter(
        DeepSeekSettings.from_secret_file(args.deepseek_secret),
        completion_contract=contract.completion_contract,
    )


def _execution_value(
    execution: HarnessAgentExecution,
    *,
    schema: str,
    store: PostgresHarnessStore,
) -> dict[str, object]:
    projection = store.load_run(execution.loop_result.harness_run_id)
    terminal = execution.terminal_result
    return {
        "ok": True,
        "authority": "independent-harness-run",
        "backend": "postgresql",
        "stateRoot": None,
        "storageBackend": "postgresql",
        "schema": schema,
        "run": projection.to_dict(),
        "stopCode": execution.loop_result.stop_code.value,
        "usage": execution.loop_result.usage,
        "runReceipt": None if terminal is None else terminal.receipt.to_dict(),
        "completionProposal": (
            None
            if terminal is None or terminal.completion_proposal is None
            else terminal.completion_proposal.to_dict()
        ),
    }


def _inspect(
    store: PostgresHarnessStore,
    harness_run_id: str,
    *,
    schema: str,
    clock_ms,
) -> dict[str, object]:
    projection = store.load_run(harness_run_id)
    continuity = EventSourcedRunContinuity.open(
        store,
        harness_run_id,
        clock_ms=clock_ms,
    )
    recorder = IndependentRunRecorder(
        store,
        continuity.contract,
        continuity.binding,
        clock_ms=clock_ms,
    )
    provider: dict[str, JsonValue] | None = None
    try:
        retained_provider = continuity.load_current_provider_call()
        provider = retained_provider.record.to_dict()
    except KeyError:
        pass
    snapshot: dict[str, JsonValue] | None = None
    try:
        snapshot = continuity.load_current_snapshot().snapshot.to_dict()
    except KeyError:
        pass
    terminal: StoredIndependentRunResult | None = None
    if projection.status.terminal:
        try:
            terminal = recorder.load_terminal_result()
        except KeyError:
            pass
    run_value = projection.to_dict()
    run_receipt = None if terminal is None else terminal.receipt.to_dict()
    completion_proposal = (
        None
        if terminal is None or terminal.completion_proposal is None
        else terminal.completion_proposal.to_dict()
    )
    return {
        "ok": True,
        "authority": "independent-harness-run",
        "backend": "postgresql",
        "stateRoot": None,
        "storageBackend": "postgresql",
        "schema": schema,
        "run": run_value,
        "contract": continuity.contract.to_dict(),
        "providerCall": provider,
        "snapshot": snapshot,
        "runReceipt": run_receipt,
        "completionProposal": completion_proposal,
    }


__all__ = ["dispatch"]
