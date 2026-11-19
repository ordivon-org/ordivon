"""Public MCP presentation of Owner failures; no credential or policy authority.

Only the already-typed Host domain envelope may contribute bounded diagnostic
fields to user-visible text. Other upstream content remains opaque.
"""

from __future__ import annotations

import re
from typing import Any

from mcp_types import CallToolResult, TextContent

from ..logic.owner_protocol import OwnerCallError

_SAFE_TOKEN = re.compile(r"^[A-Za-z0-9_.:-]{1,96}$")
_HOST_PUBLIC_FIELDS = ("code", "reason", "resourceKind", "suggestedAction", "evidenceBoundary")
_HOST_PUBLIC_NUMBERS = ("requestedAfterSequence", "observedTopicHighSequence")


def _host_error_summary(owner_id: str | None, error: dict[str, Any]) -> str | None:
    if owner_id not in {"host", "host.read"}:
        return None
    if (
        error.get("kind") != "ordivon.host-domain-error"
        or type(error.get("schemaVersion")) is not int
        or error["schemaVersion"] != 1
    ):
        return None
    code = error.get("code")
    if not isinstance(code, str) or _SAFE_TOKEN.fullmatch(code) is None:
        return None
    parts: list[str] = []
    for field in _HOST_PUBLIC_FIELDS:
        value = error.get(field)
        if isinstance(value, str) and _SAFE_TOKEN.fullmatch(value):
            parts.append(f"{field}={value}")
    for field in _HOST_PUBLIC_NUMBERS:
        value = error.get(field)
        if type(value) is int and 0 <= value <= 2**63 - 1:
            parts.append(f"{field}={value}")
    return "Host domain error: " + "; ".join(parts)


def owner_error_result(exc: OwnerCallError) -> CallToolResult:
    """Preserve the wire envelope while emitting a safe Host-error summary."""
    error = (
        dict(exc.error)
        if exc.error is not None
        else {
            "code": "OWNER_CALL_FAILED",
            "message": str(exc),
            "origin": "gateway_adapter",
        }
    )
    structured: dict[str, Any] = {"error": error}
    if exc.owner_id is not None:
        structured["gatewayOwnerId"] = exc.owner_id
    if exc.tool_name is not None:
        structured["gatewayOwnerTool"] = exc.tool_name
    message = _host_error_summary(exc.owner_id, error) or str(exc)
    return CallToolResult(
        content=[TextContent(type="text", text=message)],
        structuredContent=structured,
        isError=True,
    )


# Previously imported from the Security façade; transport remains the owner.
_owner_error_result = owner_error_result
