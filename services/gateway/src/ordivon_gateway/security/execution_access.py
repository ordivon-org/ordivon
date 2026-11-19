"""Trusted HTTP principal scope for Runtime operation IDs and reattachment.

Request context is verified by Cloudflare Access or the explicitly authorized
local service token; caller-supplied ActorRefs and operationRefs cannot mint it.
"""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

from mcp.server.mcpserver import Context
from mcp.server.mcpserver.exceptions import ToolError

from ..execution_refs import GatewayError
from .ingress_identity import identity_from_state, tool_context_state

if TYPE_CHECKING:
    from ..service import GatewayService


def verified_execution_scope(context: Context | None) -> tuple[str, str] | None:
    identity = identity_from_state(tool_context_state(context))
    return (identity.issuer, identity.principal) if identity is not None else None


def require_http_execution_identity(context: Context | None) -> None:
    if verified_execution_scope(context) is None:
        raise ToolError("HTTP execution requires verified ingress Principal identity")


def verified_execution_request_id(
    public_request_id: str,
    capability: str,
    context: Context | None,
) -> str:
    verified = verified_execution_scope(context)
    if verified is None:
        return public_request_id
    issuer, principal = verified
    canonical = json.dumps(
        [
            "ordivon.gateway-principal-scoped-execution-request.v1",
            issuer,
            principal,
            capability,
            public_request_id,
        ],
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "request:gw-principal:" + hashlib.sha256(canonical).hexdigest()


async def qualify_gateway_operation_ref(
    gateway: GatewayService,
    operation_ref: str,
    capability: str | None,
    public_request_id: str | None,
    context: Context | None,
) -> None:
    """Match observe/cancel/read against the submitting Principal's exact request."""
    if verified_execution_scope(context) is None:
        return  # Legacy stdio remains unchanged.
    if not isinstance(public_request_id, str) or not public_request_id:
        raise ToolError("verified operation requires original requestId")
    if not isinstance(capability, str) or not capability:
        raise ToolError("verified operation requires original capability")
    owner_request_id = verified_execution_request_id(public_request_id, capability, context)
    try:
        recovered = await gateway.execution_resolve(
            capability=capability, request_id=owner_request_id
        )
    except GatewayError as exc:
        raise ToolError("operationRef cannot be qualified for this principal") from exc
    if recovered.resolution != "found" or recovered.operation_ref != operation_ref:
        raise ToolError("operationRef cannot be qualified for this principal")
