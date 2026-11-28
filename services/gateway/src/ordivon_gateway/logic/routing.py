from __future__ import annotations

from ..contracts import CapabilityRoute as CapabilityRoute
from .research_routes import research_capabilities


def default_routes() -> dict[str, CapabilityRoute]:
    routes = [
        CapabilityRoute(
            capability="execution.linux",
            owner_id="runtime.linux",
            category="execution",
            owner_tool="workspace.exec",
            context_mode="provider-defined-string",
            truth_boundary="Runtime owns Workspace/Job/Attempt/process/artifact physical truth.",
            description="Execute bounded physical work through the Linux Runtime owner.",
            tags=("execution", "job", "linux", "runtime", "workspace"),
            execution_target="local_linux",
            default_context="trusted_local",
        ),
        # A distinct authenticated PostgreSQL Runtime principal/endpoint for
        # Harness-issuer-bound effects. The physical owner remains Runtime;
        # it shares PG/Runner with execution.linux, not an independent Registry.
        # When not configured, capability discovery reports unavailable.
        CapabilityRoute(
            capability="execution.harness",
            owner_id="runtime.harness",
            category="execution",
            owner_tool="workspace.exec",
            context_mode="provider-defined-string",
            truth_boundary=(
                "Same PostgreSQL Runtime and native Runner; dedicated authenticated "
                "Harness principal requires current issuer before NEW Job admission."
            ),
            description="Execute issuer-authorized Harness Tool effects through Runtime.",
            tags=("execution", "harness", "issuer", "runtime"),
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
            description="Execute bounded physical work through the Windows Runtime owner.",
            tags=("execution", "job", "runtime", "windows", "workspace"),
            execution_target="windows_native",
            default_context="limited",
        ),
        # Discover the native Linux ReleaseEffect without confusing it with
        # execution.linux.  Observation is NOT a Security grant, and the MCP
        # tool/installed service remains separately discoverable.
        CapabilityRoute(
            capability="runtime.release.linux",
            owner_id="runtime.linux",
            category="release",
            owner_tool="release.apply",
            context_mode="none",
            truth_boundary=(
                "Runtime owns qualified PG ReleaseEffect, operator install, "
                "receipt and the original clientRequestId. Security owns "
                "release authorization; Gateway only forwards native MCP."
            ),
            description=(
                "Find the Linux Runtime structured release route; actual "
                "runtime.release.apply/get requires an installed Gateway Tool, "
                "authenticated operator AuthZEN grant and qualified Runtime candidate."
            ),
            tags=("release", "runtime", "linux", "deploy", "operator", "effect"),
            execution_target="local_linux",
        ),
        CapabilityRoute(
            capability="continuity.external",
            owner_id="host",
            category="continuity",
            owner_tool=None,
            context_mode="none",
            truth_boundary="Host owns external semantic continuity and collaboration state only.",
            description="Project Host-owned semantic Work, Social, and Attention continuity.",
            tags=("attention", "continuity", "host", "social", "work"),
        ),
        CapabilityRoute(
            capability="artifact.runtime",
            owner_id="runtime.dynamic",
            category="artifact",
            owner_tool="artifact.read",
            context_mode="none",
            truth_boundary="Artifact bytes and physical production evidence remain Runtime-owned.",
            description="Read Runtime-owned artifacts by stable execution operation reference.",
            tags=("artifact", "evidence", "read", "runtime"),
        ),
    ]
    research = research_capabilities()
    existing = {route.capability for route in routes}
    overlap = existing.intersection(spec.capability for spec in research.values())
    if overlap:
        names = ", ".join(sorted(overlap))
        raise ValueError(f"duplicate default capability route: {names}")
    for spec in research.values():
        routes.append(
            CapabilityRoute(
                capability=spec.capability,
                owner_id="research.composition",
                category="research",
                owner_tool=None,
                context_mode="none",
                truth_boundary=spec.truth_boundary,
                description=spec.description,
                tags=spec.tags,
            )
        )
    return {route.capability: route for route in routes}
