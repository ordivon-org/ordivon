from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .agent_dependencies import dependency_proposal, dependency_status
from .agent_processing import processing_probe_plan, processing_profiles
from .agent_productions import _production_root, production_standing
from .agent_surface_contracts import surface_projection as surface_projection
from .agent_surface_contracts import tool_definitions
from .creative_index import build_creative_index, query_creative_index
from .equipment import load_equipment_world, propose_operation
from .learning_context import build_learning_context
from .production_context import build_production_context

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_OWNER_ROOT = Path("capabilities/artifact")


def execute_surface_action(name: str, arguments: Mapping[str, Any], *, root: Path = ROOT) -> dict[str, Any]:
    """Validate one advertised Studio schema before entering any Owner consumer."""
    tool = next((item for item in tool_definitions() if item["name"] == name), None)
    if tool is None:
        raise ValueError(f"unsupported Studio Agent surface action: {name}")
    if not isinstance(arguments, Mapping):
        raise ValueError(f"invalid arguments for {name}: expected an object")

    checked = dict(arguments)
    schema = tool["inputSchema"]
    # An exact empty-object schema is fully checkable by Python itself.
    # Keep no-argument observation LEGO usable before Studio dependency
    # materialization, without adding an alternative JSON Schema validator.
    if schema == {"type": "object", "properties": {}, "additionalProperties": False}:
        if checked:
            raise ValueError(f"invalid arguments for {name} at <root>: unexpected properties")
    else:
        from jsonschema import Draft202012Validator

        violation = next(iter(Draft202012Validator(schema).iter_errors(checked)), None)
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
    if name == "studio_processing_probe_plan":
        return processing_probe_plan(
            root,
            profile_id=str(arguments["profileId"]),
            expected_profile_digest=str(arguments["expectedProfileDigest"]),
            expected_adapter_digest=str(arguments["expectedAdapterDigest"]),
            input_path=str(arguments["inputPath"]),
            evidence_directory=str(arguments["evidenceDirectory"]),
        )
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
