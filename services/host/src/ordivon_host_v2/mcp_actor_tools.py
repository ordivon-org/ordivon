"""Public MCP declaration adapter for Host Social ActorRefs (not IAM)."""
from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from mcp.server import MCPServer

from .mcp_domain_errors import _project_domain_errors
from .references.actor_contracts import ActorRefResponse
from .references.actor_inputs import ActorKind, ActorRefInput
from .references.actor_store import ActorReferenceStore


def register_actor_tools(
    mcp: MCPServer,
    actors: ActorReferenceStore,
    request_id: Callable[[str, object], str],
) -> None:
    """Register existing actor.declare without routing it through WorkStore."""

    @mcp.tool(name="actor.declare")
    @_project_domain_errors
    def actor_declare(
        actorRef: str,
        actorKind: Literal["unknown", "human", "agent", "service", "organization"],
    ) -> ActorRefResponse:
        value = ActorRefInput(actor_ref=actorRef, actor_kind=ActorKind(actorKind))
        request = value.model_dump(mode="json")
        return actors.declare_actor(
            value,
            client_request_id=request_id("actor-declare", request),
        )
