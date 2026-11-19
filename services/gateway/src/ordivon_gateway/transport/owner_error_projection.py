"""Public MCP presentation of Owner failures; no credential or policy authority.

Only the already-typed Host domain envelope may contribute bounded diagnostic
fields to user-visible text. Other upstream content remains opaque.
"""

from __future__ import annotations

from typing import Any

from mcp_types import CallToolResult, TextContent

from ..logic.owner_protocol import OwnerCallError


def _host_cursor_recovery_text(exc: OwnerCallError) -> str | None:
    """Expose only verified, nonsecret Host navigation facts in MCP text.

    Some connected MCP clients surface an isError result's text but discard
    structuredContent. Avoid embedding arbitrary Owner details, refs, stack
    traces, or private credentials. All unknown shapes remain opaque.
    This is a presentation-only projection, not a new trust/authorization rule.
    """
    if exc.owner_id != "host" or exc.tool_name != "topic.resume":
        return None
    error = exc.error
    if not isinstance(error, dict):
        return None
    if (
        error.get("kind") != "ordivon.host-domain-error"
        or type(error.get("schemaVersion")) is not int
        or error["schemaVersion"] != 1
        or error.get("code") != "CONFLICT"
        or error.get("reason") != "topic_resume_cursor_ahead"
        or error.get("resourceKind") != "topic"
        or error.get("retryable") is not False
        or error.get("suggestedAction") != "reread-topic-horizon-and-check-cursor-domain"
    ):
        return None
    requested = error.get("requestedAfterSequence")
    observed = error.get("observedTopicHighSequence")
    if (
        type(requested) is not int
        or type(observed) is not int
        or not (0 <= observed < requested <= 2**63 - 1)
    ):
        return None
    return (
        "owner tool returned error: host/topic.resume; "
        "code=CONFLICT reason=topic_resume_cursor_ahead "
        f"requestedAfterSequence={requested} "
        f"observedTopicHighSequence={observed} "
        "suggestedAction=reread-topic-horizon-and-check-cursor-domain "
        "retryable=false"
    )


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
    message = _host_cursor_recovery_text(exc) or str(exc)
    return CallToolResult(
        content=[TextContent(type="text", text=message)],
        structuredContent=structured,
        isError=True,
    )


# Previously imported from the Security façade; transport remains the owner.
_owner_error_result = owner_error_result
