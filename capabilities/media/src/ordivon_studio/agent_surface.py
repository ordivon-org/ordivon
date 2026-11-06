from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .agent_dependencies import dependency_proposal, dependency_status
from .agent_processing import processing_profiles
from .agent_productions import _production_root, production_standing
from .creative_index import build_creative_index, query_creative_index
from .equipment import load_equipment_world, propose_operation
from .learning_context import build_learning_context
from .production_context import build_production_context

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_OWNER_ROOT = Path("capabilities/artifact")


def tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "name": "studio_dependencies_status",
            "description": "Observe whether Studio JavaScript, core Python, and Resolve Python dependencies are exactly materialized in this Workspace. This never installs anything.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "studio_dependencies_propose",
            "description": "Compile an explicit dependency-materialization proposal for one missing Studio capability. It does not execute the acquisition; ordinary execution must never acquire implicitly.",
            "inputSchema": {
                "type": "object",
                "properties": {"target": {"type": "string", "enum": ["js", "python", "resolve"]}},
                "required": ["target"],
                "additionalProperties": False,
            },
        },
        {
            "name": "studio_production_standing",
            "description": "Read the bounded owner-native Production index and whether Studio has established a unique current Production. This does not infer priority or invent current intent; when no current Production is grounded, caller/owner intent must select one before Production-specific work.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "studio_production_context",
            "description": "Read one current Studio Production as a bounded owner-native context projection: intent, audiences, source bindings, Claims, Outputs, and mechanical source-binding relation. This does not render, edit, publish, or infer semantic currentness.",
            "inputSchema": {
                "type": "object",
                "properties": {"productionId": {"type": "string", "minLength": 1}},
                "required": ["productionId"],
                "additionalProperties": False,
            },
        },
        {
            "name": "studio_learning_context",
            "description": "Hydrate scoped retained learning from real Studio Productions together with the current Creative Alpha holdout/OOS boundary and promotion path. This is read-only evidence for future production decisions, not a universal quality model or approval gate.",
            "inputSchema": {
                "type": "object",
                "properties": {"currentProductionId": {"type": "string", "minLength": 1}},
                "additionalProperties": False,
            },
        },
        {
            "name": "studio_creative_index_query",
            "description": "Query the rebuildable Creative Index for one term and return matching entities plus their one-hop relations. The index is navigation/cache data pinned to source revisions; it is not source authority and does not infer current physical availability.",
            "inputSchema": {
                "type": "object",
                "properties": {"term": {"type": "string", "minLength": 1}},
                "required": ["term"],
                "additionalProperties": False,
            },
        },
        {
            "name": "studio_processing_profiles",
            "description": "Discover source-owned FFprobe/FFmpeg/OTIO/timed-text processing profiles and exact adapter paths with content digests. This is a read-only LEGO catalog projection; external tool readiness and effect authority remain with Workstation/Runtime.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "studio_equipment_propose",
            "description": "Select freshly observed equipment for one exact Studio capability and compile a truthful operation proposal with readiness, blockers, exact physical plan, and owner-specific verification contract. This does not execute the effect.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "capability": {"type": "string", "minLength": 1},
                    "equipmentId": {"type": "string", "minLength": 1},
                    "parameters": {"type": "object"},
                },
                "required": ["capability", "parameters"],
                "additionalProperties": False,
            },
        },
    ]


def execute_surface_action(name: str, arguments: Mapping[str, Any], *, root: Path = ROOT) -> dict[str, Any]:
    """Validate one advertised Studio schema before entering any Owner consumer."""
    tool = next((item for item in tool_definitions() if item["name"] == name), None)
    if tool is None:
        raise ValueError(f"unsupported Studio Agent surface action: {name}")
    if not isinstance(arguments, Mapping):
        raise ValueError(f"invalid arguments for {name}: expected an object")

    # The dependency is already owned and locked by Studio. Keep discovery
    # dependency-free; validate only at the actual action execution boundary.
    from jsonschema import Draft202012Validator

    checked = dict(arguments)
    violation = next(iter(Draft202012Validator(tool["inputSchema"]).iter_errors(checked)), None)
    if violation is not None:
        location = "/".join(map(str, violation.absolute_path)) or "<root>"
        raise ValueError(f"invalid arguments for {name} at {location}: {violation.message}")
    arguments = checked

    if name == "studio_dependencies_status":
        return dependency_status(root)
    if name == "studio_dependencies_propose":
        return dependency_proposal(str(arguments["target"]), root)
    if name == "studio_production_standing":
        return production_standing(root)
    if name == "studio_production_context":
        production_id = str(arguments["productionId"])
        return build_production_context(_production_root(root, production_id))
    if name == "studio_learning_context":
        current = arguments.get("currentProductionId")
        if current is not None:
            _production_root(root, current)
        return build_learning_context(root, current_production_id=current)
    if name == "studio_creative_index_query":
        artifact_candidate = Path(
            os.environ.get("ORDIVON_ARTIFACT_ROOT", str(root.parents[1] / ARTIFACT_OWNER_ROOT))
        )
        creative_library_candidate = Path(os.environ.get("ORDIVON_CREATIVE_LIBRARY_ROOT", str(root)))
        index = build_creative_index(
            root,
            artifact_root=artifact_candidate if artifact_candidate.exists() else None,
            creative_library_root=(
                creative_library_candidate if creative_library_candidate.exists() else None
            ),
        )
        return query_creative_index(index, str(arguments["term"]))
    if name == "studio_processing_profiles":
        return processing_profiles(root)
    if name == "studio_equipment_propose":
        world = load_equipment_world(root / "research/equipment/equipment-world.json")
        equipment_id = arguments.get("equipmentId")
        parameters = arguments["parameters"]
        return propose_operation(
            world,
            str(arguments["capability"]),
            dict(parameters),
            equipment_id=equipment_id,
            local=True,
        )
    raise ValueError(f"unsupported Studio Agent surface action: {name}")


def surface_projection() -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.studio-agent-tool-surface",
        "truthRole": "studio-domain-semantic-actions",
        "domainId": "domain:ordivon-studio",
        "revision": "studio-agent-surface-processing-profiles-v1",
        "tools": tool_definitions(),
        "runtimeOwnsPhysicalExecution": True,
        "harnessMayAdmitSubsetOnly": True,
        "mcpRequired": False,
        "boundary": "Studio owns readiness, dependency and medium semantics. Harness may bind these definitions into a turn but does not gain Studio authority; Runtime remains the physical executor of compiled plans.",
    }
