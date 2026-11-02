"""Pure equipment actionability, selection and postcondition projections.

Catalog knowledge, installed presence, execution authority, and semantic completion
remain distinct; this module reads only caller-supplied values and grants no authority.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

_DIRECT_OPERATION_CAPABILITIES: dict[str, frozenset[str]] = {
    "typst": frozenset({"document.compile.pdf"}),
    "imagemagick": frozenset({"image.resize"}),
    "inkscape": frozenset({"vector.export"}),
    "aseprite": frozenset({"sprite.source.author", "sprite.runtime.export"}),
    "blender": frozenset({"scene.create", "scene.edit", "scene.render", "animation.render", "asset.export.gltf", "geometry.procedural", "camera.control", "material.control"}),
    "godot": frozenset({"interactive.run.headless", "interactive.script", "state.trace"}),
    "rsvg-convert": frozenset({"svg.rasterize"}),
    "reaper": frozenset({"audio.project.render"}),
    "kicad": frozenset({"pcb.drc", "pcb.export.svg", "pcb.export.gerber", "pcb.export.drill"}),
    "ngspice": frozenset({"circuit.simulate.transient"}),
    "cadquery": frozenset({"cad.script.author", "cad.export.step", "cad.export.stl"}),
    "duckdb": frozenset({"dataset.sql.execute", "dataset.query", "dataset.transform"}),
    "pyarrow": frozenset({"dataset.export.parquet"}),
    "gdal-ogr": frozenset({"geospatial.inspect", "geospatial.transform", "geospatial.export.geopackage"}),
    "warcio": frozenset({"web.capture.response.warc"}),
    "python-email": frozenset({"message.compose.rfc5322"}),
    "tiled": frozenset({"world2d.canonicalize.tmj", "world2d.render.preview"}),
}
_PROVIDER_MEDIATED_EQUIPMENT = frozenset({"davinci-resolve"})
_REAPER_PROVIDER_CAPABILITIES = frozenset({"audio.multitrack", "audio.edit", "audio.mix", "audio.master", "audio.automation", "midi.edit", "script.reascript", "control.osc"})
_STUDIO_NATIVE_CAPABILITIES: dict[str, frozenset[str]] = {
    "ffprobe": frozenset({"media.probe", "stream.inspect", "duration.inspect", "codec.inspect"}),
    "ffmpeg": frozenset({"media.probe", "media.transcode", "video.encode", "audio.transform", "image.extract", "timeline.compose-basic", "stream.capture-basic"}),
}


def operation_support(equipment_id: str, capability: str) -> str:
    """Classify whether one advertised capability has a mechanical Agent action path."""
    if equipment_id == "figma":
        return "AUTH_BLOCKED"
    if equipment_id == "touchdesigner":
        return "LICENSE_BLOCKED"
    if capability in _DIRECT_OPERATION_CAPABILITIES.get(equipment_id, frozenset()):
        return "DIRECTLY_INVOCABLE"
    if equipment_id in _PROVIDER_MEDIATED_EQUIPMENT:
        return "PROVIDER_MEDIATED"
    if equipment_id == "reaper" and capability in _REAPER_PROVIDER_CAPABILITIES:
        return "PROVIDER_MEDIATED"
    if capability in _STUDIO_NATIVE_CAPABILITIES.get(equipment_id, frozenset()):
        return "STUDIO_NATIVE"
    if equipment_id in {"stream-deck", "bhaptics"}:
        return "PHYSICAL_UNPROVEN"
    return "DESCRIPTIVE_ONLY"


def operational_readiness(equipment_id: str, present: bool | None, capability: str) -> str:
    """Project Studio operational readiness without converting physical presence into authority."""
    if present is False:
        return "ABSENT"
    if present is None:
        return "UNKNOWN"
    support = operation_support(equipment_id, capability)
    if support == "AUTH_BLOCKED":
        return "AUTH_REQUIRED"
    if support == "LICENSE_BLOCKED":
        return "LICENSE_REQUIRED"
    if support in {"PHYSICAL_UNPROVEN", "DESCRIPTIVE_ONLY"}:
        return "PRESENT_UNPROVEN"
    if equipment_id in {"davinci-resolve", "obs-studio"}:
        return "READY_WITH_STARTUP"
    if equipment_id == "reaper" and capability != "audio.project.render":
        return "READY_WITH_STARTUP"
    return "READY"


def capability_coverage(world: Mapping[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    for item in world.get("equipment", []):
        equipment_id = str(item["id"])
        for capability in item.get("capabilities", []):
            status = operation_support(equipment_id, capability)
            counts[status] = counts.get(status, 0) + 1
            rows.append({"equipmentId": equipment_id, "capability": capability, "actionability": status})
    return {
        "schemaVersion": 1,
        "kind": "ordivon.studio-equipment-capability-coverage",
        "counts": counts,
        "rows": rows,
        "boundary": "Catalog knowledge and executable affordance are distinct. Only DIRECTLY_INVOCABLE, STUDIO_NATIVE or PROVIDER_MEDIATED rows are mechanically actionable without an external authority transition.",
    }


def select_for_capability(world: Mapping[str, Any], capability: str, *, inventory: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    physical: dict[str, bool | None] | None = None
    if inventory is not None:
        physical = {item["id"]: item["present"] for item in inventory.get("equipment", [])}
    retention_order = {"core-equipment": 0, "external-workstation": 1, "specialist-on-demand": 2, "candidate": 3, "challenger": 4, "reject": 5}
    readiness_order = {"READY": 0, "READY_WITH_STARTUP": 1, "AUTH_REQUIRED": 2, "LICENSE_REQUIRED": 3, "PRESENT_UNPROVEN": 4, "UNKNOWN": 5, "ABSENT": 6}
    matches = []
    for item in world.get("equipment", []):
        if capability not in item.get("capabilities", []):
            continue
        equipment_id = str(item["id"])
        present = physical.get(equipment_id) if physical is not None else None
        actionability = operation_support(equipment_id, capability)
        readiness = operational_readiness(equipment_id, present, capability)
        selectable = readiness in {"READY", "READY_WITH_STARTUP"} and actionability in {"DIRECTLY_INVOCABLE", "STUDIO_NATIVE", "PROVIDER_MEDIATED"}
        matches.append(
            {
                "id": equipment_id,
                "family": item["family"],
                "retention": item.get("retention"),
                "present": present,
                "readiness": readiness,
                "actionability": actionability,
                "selectable": selectable,
                "reason": item.get("reason"),
            }
        )
    matches.sort(key=lambda item: (not item["selectable"], readiness_order.get(item["readiness"], 99), retention_order.get(item["retention"], 99), item["id"]))
    return matches


def external_authority_transition(equipment_id: str) -> dict[str, Any] | None:
    """Describe the external authority evidence needed to graduate a blocked provider.

    This is guidance to the owning boundary, not a credential flow and not authority itself.
    """
    if equipment_id == "figma":
        return {
            "owner": "user-plus-figma-auth-provider",
            "state": "AUTH_REQUIRED",
            "automatic": False,
            "requiredEvidence": [
                "fresh authenticated provider identity",
                "one bounded native design read",
                "one bounded native design write with post-write re-observation",
            ],
            "prohibited": ["inventing OAuth success", "moving access tokens into Studio source or Runtime argv"],
        }
    if equipment_id == "touchdesigner":
        return {
            "owner": "user-plus-derivative-license-authority",
            "state": "LICENSE_REQUIRED",
            "automatic": False,
            "requiredEvidence": [
                "fresh current TouchDesigner license/account state",
                "one bounded project open/create",
                "one machine-observable realtime output or operator-state postcondition",
            ],
            "prohibited": ["license bypass", "treating executable presence as licensed capability"],
        }
    return None


def verification_contract(equipment_id: str, capability: str, parameters: Mapping[str, Any]) -> dict[str, Any]:
    """Return the semantic completion evidence required after physical execution.

    The contract is intentionally owner-specific. It never claims completion itself and it
    never reduces provider-native state to process exit status.
    """
    if equipment_id == "cadquery":
        expected = [str(value) for value in parameters.get("expectedArtifacts", []) if str(value)]
        return {
            "kind": "DECLARED_CAD_ARTIFACTS",
            "required": True,
            "ready": bool(expected),
            "artifacts": expected,
            "reason": "CadQuery script/process success is not CAD semantic completion; every proposal must declare the source/export artifacts whose existence will be re-observed. STEP interchange conformance remains an Artifact-owned authority transition.",
        }
    if equipment_id == "blender":
        expected = [str(value) for value in parameters.get("expectedArtifacts", []) if str(value)]
        return {
            "kind": "DECLARED_ARTIFACTS",
            "required": True,
            "ready": bool(expected),
            "artifacts": expected,
            "reason": "Blender can report a Python traceback while exiting zero; every Agent proposal must name the artifacts/state whose existence will establish semantic completion.",
        }
    if equipment_id == "reaper" and capability == "audio.project.render":
        output = parameters.get("expectedOutput")
        return {
            "kind": "RENDER_ARTIFACT",
            "required": True,
            "ready": isinstance(output, str) and bool(output),
            "artifacts": [str(output)] if output else [],
            "reason": "REAPER process exit is insufficient; verify the independently reconstructed render artifact.",
        }
    if equipment_id == "reaper":
        return {
            "kind": "NATIVE_PROJECT_OR_SESSION_STATE",
            "required": True,
            "ready": True,
            "reason": "Observe the declared .rpp/session/ReaScript postcondition after provider action.",
        }
    if equipment_id == "obs-studio":
        return {
            "kind": "STATE_REOBSERVE_AND_RECOVER",
            "required": True,
            "ready": True,
            "reason": "Mutation acknowledgement is not convergence; re-observe intended OBS state and restore the exact prior default-off listener configuration after bounded use.",
        }
    if equipment_id == "davinci-resolve":
        return {
            "kind": "OPERATION_RESULT_RECONCILIATION",
            "required": True,
            "ready": True,
            "reason": "Read the operation-id-bound Resolve result and inspect declared project/artifact postconditions; do not redispatch after response loss.",
        }
    output = parameters.get("output")
    if isinstance(output, str) and output:
        return {
            "kind": "ARTIFACT_EXISTS",
            "required": True,
            "ready": True,
            "artifacts": [output],
            "reason": "Verify the declared deterministic output artifact after process completion.",
        }
    return {
        "kind": "PROCESS_PLUS_DOMAIN_OBSERVATION",
        "required": False,
        "ready": True,
        "reason": "No additional equipment-specific postcondition is required by this narrow plan; Runtime process evidence still does not itself assert Studio semantic quality.",
    }


_PROVIDER_MECHANICS: dict[str, dict[str, Any]] = {
    "davinci-resolve": {
        "transport": "studio.resolve-adapter",
        "stateAuthority": "davinci-resolve-project",
        "executionAuthority": "runtime-windows-native-plus-studio-adapter",
        "secretBoundary": "none-for-local-adapter",
        "convergence": "operation-result-plus-project/postcondition-inspection",
        "recovery": "operation-id-bound-result-read; restore prior project/cleanup when declared by adapter",
        "defaultLifecycle": "operator-workstation-state-preserved",
    },
    "obs-studio": {
        "transport": "authenticated-obs-websocket-on-windows-loopback",
        "stateAuthority": "obs-live-scene/source/recording-state",
        "executionAuthority": "runtime-windows-controller-process; Studio owns live semantics",
        "secretBoundary": "external-secret-bearing-authority; never Studio source or Runtime argv",
        "convergence": "mutation-response-is-not-convergence; re-observe intended OBS state",
        "recovery": "restore exact prior websocket configuration and verify listener closure",
        "defaultLifecycle": "websocket-server-disabled-by-default",
    },
    "reaper": {
        "transport": "reascript/osc/or-exact-process",
        "stateAuthority": "native-rpp-project-and-current-reaper-session",
        "executionAuthority": "runtime-process; Studio owns audio-project semantics",
        "secretBoundary": "none-by-default",
        "convergence": "inspect declared project/render/session postcondition",
        "recovery": "persist/reopen native .rpp; do not infer state from installer/process exit alone",
        "defaultLifecycle": "portable-specialist-on-demand",
    },
}


def local_provider_surface(world: Mapping[str, Any]) -> dict[str, Any]:
    """Project validated Studio-local provider mechanics without creating another Tool registry.

    The Equipment World remains the semantic source for capabilities. This projection only
    removes provider-folklore from callers; it neither discovers physical equipment nor
    grants execution authority.
    """
    by_id = {str(item.get("id")): item for item in world.get("equipment", [])}
    providers: list[dict[str, Any]] = []
    for equipment_id, mechanics in _PROVIDER_MECHANICS.items():
        item = by_id.get(equipment_id)
        if item is None:
            continue
        providers.append({
            "equipmentId": equipment_id,
            "capabilities": list(item.get("capabilities", [])),
            "retention": item.get("retention"),
            **mechanics,
        })
    return {
        "schemaVersion": 1,
        "kind": "ordivon.studio-local-provider-surface",
        "truthRole": "studio-semantic-provider-projection",
        "providers": providers,
        "runtimeOwnsPhysicalExecution": True,
        "workstationOwnsPhysicalEquipmentBinding": True,
        "mcpRequired": False,
        "authorityBoundary": "Studio selects and interprets medium-native providers; this surface does not prove physical presence, grant Runtime execution, expose secrets, or create external-provider truth.",
    }
