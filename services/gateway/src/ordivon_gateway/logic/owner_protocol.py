from __future__ import annotations

from typing import Any, Protocol

from .execution_refs import GatewayError


class OwnerCallError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        owner_id: str | None = None,
        tool_name: str | None = None,
        error: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.owner_id = owner_id
        self.tool_name = tool_name
        self.error = dict(error) if error is not None else None


class OwnerToolCaller(Protocol):
    """Minimal natural-Owner MCP port; transport lives in upstream.py."""

    async def call_tool(
        self, owner_id: str, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]: ...

    def is_configured(self, owner_id: str) -> bool: ...


def _configured(caller: OwnerToolCaller, owner_id: str) -> bool:
    probe = getattr(caller, "is_configured", None)
    if callable(probe):
        return bool(probe(owner_id))
    return True


def _configuration_error(caller: OwnerToolCaller, owner_id: str) -> str | None:
    probe = getattr(caller, "configuration_error", None)
    if callable(probe):
        value = probe(owner_id)
        return str(value) if value else None
    return None


def _required_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise GatewayError(f"owner response omitted {key}")
    return value


def _required_bool(payload: dict[str, Any], key: str) -> bool:
    """Runtime is the physical state owner; reject non-JSON-boolean terminality."""
    value = payload.get(key)
    if type(value) is not bool:
        raise GatewayError(f"Runtime owner response requires boolean {key}")
    return value


def _owner_receipt_state(response: dict[str, Any]) -> str:
    """Project Runtime's Job status; validate distinct Attempt state independently.

    The Runtime producer explicitly calls status a compatibility summary:
    accepted/starting -> queued and running/stopping/recovering -> working.
    attemptState is the native Attempt lifecycle state, never a status alias.
    """
    for field in ("status", "attemptState"):
        if field in response:
            value = response[field]
            if not isinstance(value, str) or not value:
                raise GatewayError(f"Runtime owner response requires string {field}")
    return response.get("status", response.get("attemptState", "unknown"))


def _owner_optional_disposition(response: dict[str, Any], field: str) -> str | None:
    """One typed Owner wire rule for command and observation disposition."""
    if field not in ("deliveryDisposition", "executionDisposition"):
        raise ValueError("unsupported Runtime disposition field")
    value = response.get(field)
    if value is not None and (not isinstance(value, str) or not value):
        raise GatewayError(f"Runtime owner response requires string {field}")
    return value
