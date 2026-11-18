from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from . import equipment_capabilities as capability_projection
from .equipment_plan import (
    EquipmentPlan,
    _first_existing,
    _require_existing,
)
from .equipment_plan import (
    compile_operation as _compile_operation,
)

DEFAULT_WORLD = Path("research/equipment/equipment-world.json")


def load_equipment_world(path: Path = DEFAULT_WORLD) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schemaVersion") != 1 or value.get("id") != "studio.equipment-world":
        raise ValueError("unsupported equipment world")
    ids = [item["id"] for item in value.get("equipment", [])]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate equipment id")
    return value


from .equipment_discovery import (
    _binding_environment,
    _workstation_equipment_binding,
    discover_equipment,
)


def equipment_by_id(world: Mapping[str, Any], equipment_id: str) -> Mapping[str, Any]:
    for item in world.get("equipment", []):
        if item.get("id") == equipment_id:
            return item
    raise KeyError(equipment_id)


def discover_equipment_for_capability(world: Mapping[str, Any], capability: str) -> dict[str, Any]:
    """Observe only physical candidates relevant to one Studio capability.

    This is deliberately not a cache: every returned candidate is freshly observed, but
    irrelevant Windows/GUI equipment is not probed merely because it exists in the world.
    """
    scoped = dict(world)
    scoped["equipment"] = [
        item for item in world.get("equipment", [])
        if capability in item.get("capabilities", [])
    ]
    return discover_equipment(scoped)



def propose_operation(
    world: Mapping[str, Any],
    capability: str,
    parameters: Mapping[str, Any],
    *,
    equipment_id: str | None = None,
    local: bool = True,
) -> dict[str, Any]:
    """Compile one truthful Agent-facing proposal without executing it.

    Selection, physical currentness, actionability, exact plan and completion contract are
    projected together so callers do not reconstruct Studio/Workstation folklore.
    """
    inventory = discover_equipment_for_capability(world, capability) if local else None
    matches = capability_projection.select_for_capability(world, capability, inventory=inventory)
    if equipment_id is not None:
        matches = [item for item in matches if item["id"] == equipment_id]
    if not matches:
        raise ValueError(f"no equipment advertises capability: {capability}")
    candidate = matches[0]
    proposal: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.studio-equipment-operation-proposal",
        "capability": capability,
        "candidate": candidate,
        "plan": None,
        "verification": None,
        "authorityTransition": None,
        "ready": False,
        "blockers": [],
    }
    if not candidate["selectable"]:
        proposal["blockers"].append(candidate["readiness"])
        if candidate["actionability"] not in {"DIRECTLY_INVOCABLE", "STUDIO_NATIVE", "PROVIDER_MEDIATED"}:
            proposal["blockers"].append(candidate["actionability"])
        proposal["authorityTransition"] = capability_projection.external_authority_transition(candidate["id"])
        return proposal
    if candidate["actionability"] == "STUDIO_NATIVE":
        proposal["blockers"].append("USE_STUDIO_NATIVE_COMMAND")
        return proposal
    plan = compile_operation(candidate["id"], capability, parameters)
    if candidate["id"] == "davinci-resolve" and plan.executable is None:
        proposal["plan"] = plan.as_dict()
        proposal["blockers"].append("EXACT_RESOLVE_NATIVE_SOURCE_AND_EXECUTION_BINDING_REQUIRED")
        return proposal
    verification = capability_projection.verification_contract(candidate["id"], capability, parameters)
    proposal["plan"] = plan.as_dict()
    proposal["verification"] = verification
    if verification.get("ready") is not True:
        proposal["blockers"].append("VERIFICATION_CONTRACT_INCOMPLETE")
        return proposal
    proposal["ready"] = True
    return proposal


def compile_operation(equipment_id: str, capability: str, parameters: Mapping[str, Any]) -> EquipmentPlan:
    """Produce a plan through the stable Studio API; Runtime owns execution."""
    return _compile_operation(
        equipment_id,
        capability,
        parameters,
        require_existing=_require_existing,
        first_existing=_first_existing,
        workstation_binding=_workstation_equipment_binding,
        binding_environment=_binding_environment,
    )
