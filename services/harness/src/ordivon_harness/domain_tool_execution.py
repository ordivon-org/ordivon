"""Domain Tool execution: bind a caller-approved subset to one Agent Turn loop.

The Domain remains owner of actual Tool effects. This module only filters
what the Provider may see and enforces authorization before forwarding calls.
Original public imports stay in domain_tools; no second registry or Owner.
"""

from __future__ import annotations

from collections.abc import Callable

from anc_canonical import JsonValue, validate_json_value

from .agent_tool_observation import HarnessToolObservation
from .domain_tool_contracts import DomainToolBridge, DomainToolLoopPlan
from .ordivon.control import CancellationToken as _CancellationToken, RunDeadline
from .ordivon.events import HarnessRunEvent
from .ordivon.loop import AgentLoopResult as _AgentLoopResult, OrdivonAgentLoop
from .ordivon.model import AgentToolCall as _AgentToolCall, AgentToolDefinition
from .ordivon.model import AgentTurnAdapter as _AgentTurnAdapter
from .ordivon.tool_errors import ToolBridgeError, ToolBridgeErrorKind
from .version import package_version


class _GrantedDomainToolBridge:
    def __init__(self, bridge: DomainToolBridge, allowed_tools: tuple[str, ...]) -> None:
        validate_json_value(bridge.bridge_identity)
        if not bridge.bridge_identity:
            raise ValueError("domain Tool Bridge identity must be non-empty")
        self.bridge = bridge
        self._definitions = bridge.catalog._select(allowed_tools)
        self._allowed = frozenset(tool.name for tool in self._definitions)
        self.catalog_digest = bridge.catalog._granted_digest(allowed_tools)

    def definitions(self) -> tuple[AgentToolDefinition, ...]:
        return self._definitions

    def execute(self, call: _AgentToolCall, *, step_id: str) -> HarnessToolObservation:
        if call.name not in self._allowed:
            raise ToolBridgeError(
                f"domain Tool is not granted: {call.name}",
                kind=ToolBridgeErrorKind.AUTHORITY_DENIED,
            )
        return self.bridge.execute(call, step_id=step_id)


class DomainToolLoopRunner:
    """Run one bounded Provider-neutral loop through a domain-owned Tool bridge.

    Domain code remains responsible for durable Actor/Task state, admission,
    external effect truth, and result verification. Use the independent Harness
    Run APIs when Provider/Runtime continuity must be durably retained.
    """

    def __init__(
        self,
        adapter: _AgentTurnAdapter,
        bridge: DomainToolBridge,
        *,
        clock_ms: Callable[[], int] | None = None,
        monotonic_ms: Callable[[], int] | None = None,
        event_sink: Callable[[HarnessRunEvent], None] | None = None,
    ) -> None:
        validate_json_value(bridge.bridge_identity)
        if not bridge.bridge_identity:
            raise ValueError("domain Tool Bridge identity must be non-empty")
        self.adapter = adapter
        self.bridge = bridge
        self.clock_ms = clock_ms
        self.monotonic_ms = monotonic_ms
        self.event_sink = event_sink

    def execution_identity(self, plan: DomainToolLoopPlan) -> dict[str, JsonValue]:
        granted = self.bridge.catalog._select(plan.allowed_tools)
        identity: dict[str, JsonValue] = {
            "schemaVersion": 1,
            "kind": "ordivon.domain-tool-loop-identity",
            "harness": {
                "package": "ordivon-harness",
                "version": package_version(),
                "loopRevision": "domain-tool-loop-v1",
                "schedulingMode": "sequential",
            },
            "provider": {
                "adapterId": self.adapter.adapter_id,
                "requestedModelId": self.adapter.model_id,
            },
            "domain": {
                "domainId": self.bridge.catalog.domain_id,
                "catalogRevision": self.bridge.catalog.revision,
                "catalogDigest": self.bridge.catalog.digest,
                "grantedCatalogDigest": self.bridge.catalog._granted_digest(plan.allowed_tools),
                "allowedTools": [tool.name for tool in granted],
                "bridgeIdentity": self.bridge.bridge_identity,
            },
            "budget": plan.budget.to_contract_dict(),
        }
        validate_json_value(identity)
        return identity

    def run(
        self,
        plan: DomainToolLoopPlan,
        *,
        cancellation: _CancellationToken | None = None,
        deadline: RunDeadline | None = None,
    ) -> _AgentLoopResult:
        bound_bridge = _GrantedDomainToolBridge(self.bridge, plan.allowed_tools)
        loop = OrdivonAgentLoop(
            self.adapter,
            bound_bridge,
            budget=plan.budget,
            clock_ms=self.clock_ms,
            monotonic_ms=self.monotonic_ms,
            assignment_deadline_ms=plan.assignment_deadline_ms,
            event_sink=self.event_sink,
        )
        return loop.run(
            harness_run_id=plan.harness_run_id,
            assignment_id=plan.assignment_id,
            context_digest=plan.context_digest,
            initial_messages=plan.initial_messages,
            cancellation=cancellation,
            deadline=deadline,
        )
