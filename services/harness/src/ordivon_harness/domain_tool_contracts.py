"""Domain Tool contract: valid catalog, allowed subset and immutable Run plan.

Only the actual Tool catalog must contain entries. An empty *authorized subset*
means cognition without tool effects, not authorization failure or wildcard.
No Provider, OS, Runtime or Domain persistence effects live in this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from anc_canonical import JsonValue, canonical_digest, validate_json_value

from .agent_tool_observation import HarnessToolObservation
from .ordivon.model import AgentToolCall as _AgentToolCall, AgentToolDefinition
from .ordivon.run_contract import RunBudget


def _text(value: str, label: str, *, prefix: str | None = None) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{label} must be non-empty and trimmed")
    if len(value.encode("utf-8")) > 300:
        raise ValueError(f"{label} exceeds 300 UTF-8 bytes")
    if prefix is not None and not value.startswith(prefix + ":"):
        raise ValueError(f"{label} must start with {prefix}:")
    return value


def _digest(value: str, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 71
        or not value.startswith("sha256:")
        or any(character not in "0123456789abcdef" for character in value[7:])
    ):
        raise ValueError(f"{label} must be sha256:<64 lowercase hex>")
    return value


@dataclass(frozen=True, slots=True)
class DomainToolCatalog:
    """One immutable domain-owned model Tool surface."""

    domain_id: str
    revision: str
    tools: tuple[AgentToolDefinition, ...]

    def __post_init__(self) -> None:
        _text(self.domain_id, "domain identity", prefix="domain")
        _text(self.revision, "domain Tool catalog revision")
        names = [tool.name for tool in self.tools]
        if not names or len(names) != len(set(names)):
            raise ValueError("domain Tool names must be non-empty and unique")

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def _granted_digest(self, allowed_tools: tuple[str, ...]) -> str:
        selected = self._select(allowed_tools)
        return canonical_digest(
            {
                "schemaVersion": 1,
                "kind": "ordivon.domain-tool-catalog-grant",
                "catalogDigest": self.digest,
                "allowedTools": [tool.name for tool in selected],
            }
        )

    def _select(self, allowed_tools: tuple[str, ...]) -> tuple[AgentToolDefinition, ...]:
        if len(allowed_tools) != len(set(allowed_tools)):
            raise ValueError("domain Tool grant names must be unique")
        available = {tool.name: tool for tool in self.tools}
        missing = sorted(set(allowed_tools) - set(available))
        if missing:
            raise ValueError(f"domain Tool grant references unknown Tools: {missing}")
        allowed = set(allowed_tools)
        return tuple(tool for tool in self.tools if tool.name in allowed)

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.domain-tool-catalog",
            "domainId": self.domain_id,
            "revision": self.revision,
            "tools": [tool.to_dict() for tool in self.tools],
        }


class DomainToolBridge(Protocol):
    """Domain-owned admission and execution below the generic Harness loop."""

    catalog: DomainToolCatalog
    bridge_identity: dict[str, JsonValue]

    def execute(self, call: _AgentToolCall, *, step_id: str) -> HarnessToolObservation: ...


@dataclass(frozen=True, slots=True)
class DomainToolLoopPlan:
    harness_run_id: str
    assignment_id: str
    context_digest: str
    initial_messages: tuple[dict[str, JsonValue], ...]
    allowed_tools: tuple[str, ...]
    budget: RunBudget
    assignment_deadline_ms: int | None = None

    def __post_init__(self) -> None:
        _text(self.harness_run_id, "Harness Run identity", prefix="harness-run")
        _text(self.assignment_id, "Assignment identity", prefix="assignment")
        _digest(self.context_digest, "domain loop Context digest")
        if not self.initial_messages:
            raise ValueError("domain loop requires at least one initial message")
        for message in self.initial_messages:
            validate_json_value(message)
        if len(self.allowed_tools) != len(set(self.allowed_tools)):
            raise ValueError("domain loop allowed Tool names must be unique")
        if self.assignment_deadline_ms is not None and self.assignment_deadline_ms < 0:
            raise ValueError("domain loop deadline must be non-negative")
