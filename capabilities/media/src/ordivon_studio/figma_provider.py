"""Figma provider routing without reimplementing Figma or MCP.

Studio owns only semantic backend selection. Figma owns node/file truth, OAuth,
permissions and provider-native tool behavior. `available` is caller-supplied current
provider evidence, never inferred from installation alone.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Mapping

_DESKTOP = "figma-desktop"
_REMOTE = "figma-remote"
_STATES = {"available", "unavailable", "unknown"}

# These are Studio semantic operations, not a copy of the provider Tool registry.
# remoteOnly reflects current official Figma MCP documentation and is intentionally
# explicit so a local desktop endpoint cannot silently claim broader authority.
_OPERATIONS: dict[str, dict[str, Any]] = {
    "design.context.read": {"desktop": True, "remote": True, "preference": "desktop"},
    "design.node.read": {"desktop": True, "remote": True, "preference": "desktop"},
    "design.variables.read": {"desktop": True, "remote": True, "preference": "desktop"},
    "design.selection.read": {"desktop": True, "remote": False, "preference": "desktop", "desktopOnlyReason": "selection-based context is local-desktop state"},
    "design.file.create": {"desktop": False, "remote": True, "preference": "remote", "providerTool": "create_new_file"},
    "design.asset.download": {"desktop": False, "remote": True, "preference": "remote", "providerTool": "download_assets"},
    "design.diagram.generate": {"desktop": False, "remote": True, "preference": "remote", "providerTool": "generate_diagram"},
    "design.canvas.write": {"desktop": False, "remote": True, "preference": "remote", "providerTool": "use_figma"},
    "design.code-connect.context": {"desktop": False, "remote": True, "preference": "remote", "providerTool": "get_context_for_code_connect"},
}


@dataclass(frozen=True)
class FigmaRoute:
    schemaVersion: int
    kind: str
    operation: str
    disposition: str
    backend: str | None
    providerTool: str | None
    endpointClass: str | None
    authorityRequired: str | None
    reason: str
    mcpIsProviderTransport: bool
    studioOwnsProviderTruth: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _state(value: str, label: str) -> str:
    if value not in _STATES:
        raise ValueError(f"{label} must be available, unavailable, or unknown")
    return value


def figma_provider_surface() -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.studio-figma-provider-surface",
        "backends": {
            _DESKTOP: {
                "transport": "provider-native-mcp",
                "endpointClass": "windows-loopback-desktop",
                "semanticStrength": "selection-and-link-context",
                "authenticationAuthority": "figma-desktop-session/provider",
                "broadestFeatureSet": False,
            },
            _REMOTE: {
                "transport": "provider-native-mcp",
                "endpointClass": "figma-hosted-remote",
                "semanticStrength": "broadest-current-figma-agent-surface",
                "authenticationAuthority": "figma-oauth/provider",
                "broadestFeatureSet": True,
            },
        },
        "operations": {name: dict(spec) for name, spec in _OPERATIONS.items()},
        "authorityBoundary": "Studio selects a backend from current caller-supplied provider evidence. Figma owns OAuth, permission, file/node truth and provider Tool semantics. MCP remains a provider-native transport, not an Ordivon capability authority.",
    }


def route_figma_operation(
    operation: str,
    *,
    desktop_state: str = "unknown",
    remote_state: str = "unknown",
    prefer_local: bool = True,
) -> FigmaRoute:
    desktop_state = _state(desktop_state, "desktop_state")
    remote_state = _state(remote_state, "remote_state")
    spec = _OPERATIONS.get(operation)
    if spec is None:
        raise ValueError(f"unsupported Studio Figma operation: {operation}")

    candidates: list[str] = []
    if spec.get("desktop"):
        candidates.append(_DESKTOP)
    if spec.get("remote"):
        candidates.append(_REMOTE)
    if prefer_local and _DESKTOP in candidates:
        candidates.sort(key=lambda value: 0 if value == _DESKTOP else 1)
    elif spec.get("preference") == "remote" and _REMOTE in candidates:
        candidates.sort(key=lambda value: 0 if value == _REMOTE else 1)

    states = {_DESKTOP: desktop_state, _REMOTE: remote_state}
    chosen = next((backend for backend in candidates if states[backend] == "available"), None)
    provider_tool = spec.get("providerTool")
    if chosen is not None:
        return FigmaRoute(
            1, "ordivon.studio-figma-provider-route", operation, "ready", chosen,
            provider_tool, "windows-loopback-desktop" if chosen == _DESKTOP else "figma-hosted-remote",
            None,
            "exact current backend evidence is available; execution still occurs through the provider-native Figma surface",
            True, False,
        )

    unknown = [backend for backend in candidates if states[backend] == "unknown"]
    if unknown:
        backend = unknown[0]
        authority = "prove-desktop-mcp-currentness" if backend == _DESKTOP else "complete/prove-figma-oauth-and-permission"
        return FigmaRoute(
            1, "ordivon.studio-figma-provider-route", operation, "requires-authority", backend,
            provider_tool, "windows-loopback-desktop" if backend == _DESKTOP else "figma-hosted-remote",
            authority,
            "provider currentness/authentication is not proven; no design read/write is claimed",
            True, False,
        )

    return FigmaRoute(
        1, "ordivon.studio-figma-provider-route", operation, "unavailable", None,
        provider_tool, None, None,
        "every backend that can satisfy this semantic operation is currently unavailable",
        True, False,
    )
