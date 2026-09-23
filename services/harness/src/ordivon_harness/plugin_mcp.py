from __future__ import annotations


from anc_canonical import JsonValue, canonical_digest
from .agent_plugin import AgentPluginMcpComponent
from .agent_tool_observation import HarnessToolObservation
from .ordivon.model import AgentToolCall, AgentToolDefinition
from .ordivon.tool_errors import ToolBridgeError, ToolBridgeErrorKind
from .mcp_http_client import HarnessMcpClient, OfficialMcpClient

OBSERVATION_ONLY_GATEWAY_TOOLS = frozenset(
    {
        "system.describe",
        "capability.describe",
        "continuity.get",
        "continuity.list",
        "continuity.find",
        "continuity.changes",
    }
)



class PluginMcpObservationBridge:
    """Observation-only ToolBridge projected from one Agent Plugin MCP component.

    Effectful Gateway tools are deliberately not admitted here. They require the
    Harness durable intent/receipt/recovery path and belong to the next composition
    slice rather than a generic synchronous MCP bridge.
    """

    def __init__(
        self,
        component: AgentPluginMcpComponent,
        client: HarnessMcpClient,
        *,
        allowed_tools: tuple[str, ...] | None = None,
    ) -> None:
        requested = tuple(sorted(allowed_tools or OBSERVATION_ONLY_GATEWAY_TOOLS))
        if not requested or len(requested) != len(set(requested)):
            raise ValueError("Plugin MCP observation Tool grant must be non-empty and unique")
        forbidden = set(requested) - OBSERVATION_ONLY_GATEWAY_TOOLS
        if forbidden:
            raise ValueError(
                f"Plugin MCP observation bridge refuses effectful/unknown Tools: {sorted(forbidden)}"
            )

        raw_tools = client.list_tools()
        definitions: dict[str, AgentToolDefinition] = {}
        for raw in raw_tools:
            name = raw.get("name")
            description = raw.get("description")
            schema = raw.get("inputSchema")
            if not isinstance(name, str) or not isinstance(schema, dict):
                raise ToolBridgeError(
                    "MCP tools/list returned an invalid Tool definition",
                    kind=ToolBridgeErrorKind.PROTOCOL_INVALID,
                )
            if name not in requested:
                continue
            definitions[name] = AgentToolDefinition(
                name=name,
                description=description if isinstance(description, str) and description else name,
                input_schema=dict(schema),
            )

        missing = sorted(set(requested) - set(definitions))
        if missing:
            raise ToolBridgeError(
                f"Agent Plugin MCP component omitted granted Tools: {missing}",
                kind=ToolBridgeErrorKind.PROTOCOL_INVALID,
            )

        self.component = component
        self.client = client
        self._definitions = tuple(definitions[name] for name in requested)
        self._allowed = frozenset(requested)
        self._definition_digests = {item.name: item.digest for item in self._definitions}
        surface: dict[str, JsonValue] = {
            "schemaVersion": 1,
            "kind": "ordivon.plugin-mcp-observation-tool-surface",
            "component": component.to_dict(),
            "tools": [item.to_dict() for item in self._definitions],
        }
        self.catalog_digest = canonical_digest(surface)
        grant: dict[str, JsonValue] = {
            "schemaVersion": 1,
            "kind": "ordivon.plugin-mcp-observation-tool-grant",
            "component": component.to_dict(),
            "allowedTools": list(requested),
            "effectClass": "observation-only",
        }
        self.grant_digest = canonical_digest(grant)

    def definitions(self) -> tuple[AgentToolDefinition, ...]:
        return self._definitions

    def validate_runtime_catalog(self) -> None:
        current: dict[str, str] = {}
        for raw in self.client.list_tools():
            name = raw.get("name")
            schema = raw.get("inputSchema")
            description = raw.get("description")
            if name not in self._allowed:
                continue
            if not isinstance(name, str) or not isinstance(schema, dict):
                raise ToolBridgeError(
                    "MCP tools/list returned an invalid granted Tool definition",
                    kind=ToolBridgeErrorKind.PROTOCOL_INVALID,
                )
            definition = AgentToolDefinition(
                name=name,
                description=description if isinstance(description, str) and description else name,
                input_schema=dict(schema),
            )
            current[name] = definition.digest
        if current != self._definition_digests:
            raise ToolBridgeError(
                "Agent Plugin MCP Tool catalog drifted after Run admission",
                kind=ToolBridgeErrorKind.PROTOCOL_INVALID,
            )

    def restore_current_attempt_tool_exchanges(
        self, observations: tuple[HarnessToolObservation, ...]
    ) -> tuple[dict[str, JsonValue], ...]:
        return tuple(item.to_model_message() for item in observations)

    def execute(self, call: AgentToolCall, *, step_id: str) -> HarnessToolObservation:
        if call.name not in self._allowed:
            raise ToolBridgeError(
                f"Agent Plugin MCP Tool is not granted: {call.name}",
                kind=ToolBridgeErrorKind.AUTHORITY_DENIED,
            )
        if call.argument_error is not None:
            raise ToolBridgeError(
                f"Agent Plugin MCP Tool arguments are invalid: {call.argument_error}",
                kind=ToolBridgeErrorKind.MODEL_CORRECTABLE,
            )
        try:
            is_error, content = self.client.call_tool(call.name, call.arguments)
        except ToolBridgeError:
            raise
        except Exception as exc:  # transport/protocol is not model-correctable
            raise ToolBridgeError(
                f"Agent Plugin MCP call failed: {type(exc).__name__}: {exc}",
                kind=ToolBridgeErrorKind.PROTOCOL_INVALID,
            ) from exc
        return HarnessToolObservation(
            tool_call_id=call.tool_call_id,
            tool_name=call.name,
            status="rejected" if is_error else "observed",
            structured_content=content,
            runtime_job_ref=None,
            artifact_refs=(),
            reconciled=False,
        )


__all__ = [
    "HarnessMcpClient",
    "OBSERVATION_ONLY_GATEWAY_TOOLS",
    "OfficialMcpClient",
    "PluginMcpObservationBridge",
]
