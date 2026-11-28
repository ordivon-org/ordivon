"""Pure evidence-bound ToolProgram dataflow, no executor or Tool authority."""
from __future__ import annotations

from copy import deepcopy

from anc_canonical import JsonValue, validate_json_value

from .agent_tool_observation import HarnessToolObservation
from .tool_program_contract import _is_observation_ref, _parse_observation_ref


def _lookup_path(value: JsonValue, path: tuple[str | int, ...]) -> JsonValue:
    current: JsonValue = value
    for segment in path:
        if isinstance(segment, int):
            if not isinstance(current, list) or segment >= len(current):
                raise ValueError("ToolProgram observation reference path is unavailable")
            current = current[segment]
            continue
        if not isinstance(current, dict) or segment not in current:
            raise ValueError("ToolProgram observation reference path is unavailable")
        current = current[segment]
    return current


def resolve_template(
    value: JsonValue,
    observations: dict[str, HarnessToolObservation],
) -> JsonValue:
    """Substitute only committed values, independently for each reference.

    Decode each referenced observation once per resolution; copy only the
    chosen subtree for each use. Validate the complete resulting document
    once (not each enclosing subtree). This carries no dispatch authority.
    """
    committed: dict[str, dict[str, JsonValue]] = {}

    def visit(item: JsonValue) -> JsonValue:
        if _is_observation_ref(item):
            assert isinstance(item, dict)
            step_id, path = _parse_observation_ref(item)
            observation = observations.get(step_id)
            if observation is None or observation.status != "observed":
                raise ValueError(
                    "ToolProgram observation reference requires an already observed prior step"
                )
            if step_id not in committed:
                committed[step_id] = observation.committed_content()
            return deepcopy(_lookup_path(committed[step_id], path))
        if isinstance(item, dict):
            return {key: visit(child) for key, child in item.items()}
        if isinstance(item, list):
            return [visit(child) for child in item]
        return item

    result = visit(value)
    validate_json_value(result)
    return result
