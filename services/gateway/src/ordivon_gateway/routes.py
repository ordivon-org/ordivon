from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CapabilityRoute:
    capability: str
    owner_id: str
    category: str
    owner_tool: str | None
    context_mode: str
    truth_boundary: str
    execution_target: str | None = None
    default_context: str | None = None


def default_routes() -> dict[str, CapabilityRoute]:
    routes = [
        CapabilityRoute(
            capability="execution.linux",
            owner_id="runtime.linux",
            category="execution",
            owner_tool="workspace.exec",
            context_mode="provider-defined-string",
            truth_boundary="Runtime owns Workspace/Job/Attempt/process/artifact physical truth.",
            execution_target="local_linux",
            default_context="trusted_local",
        ),
        CapabilityRoute(
            capability="execution.windows",
            owner_id="runtime.windows",
            category="execution",
            owner_tool="workspace.exec",
            context_mode="provider-defined-json",
            truth_boundary="Windows Runtime owns Workspace/Job/Attempt/process/artifact physical truth.",
            execution_target="windows_native",
            default_context="limited",
        ),
        CapabilityRoute(
            capability="continuity.external",
            owner_id="host",
            category="continuity",
            owner_tool=None,
            context_mode="none",
            truth_boundary="Host owns external semantic continuity and collaboration state only.",
        ),
        CapabilityRoute(
            capability="artifact.runtime",
            owner_id="runtime.dynamic",
            category="artifact",
            owner_tool="artifact.read",
            context_mode="none",
            truth_boundary="Artifact bytes and physical production evidence remain Runtime-owned.",
        ),
    ]
    return {route.capability: route for route in routes}
