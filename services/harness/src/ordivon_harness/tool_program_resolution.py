"""Resolve ToolProgram observation references without running external Tools.

This deterministic LEGO consumes only validated prior observations and JSON
reference markers. It neither admits Tool authority nor performs side effects.
"""

from __future__ import annotations

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
    validate_json_value(current)
    return current


def _resolve_template(
    value: JsonValue,
    observations: dict[str, HarnessToolObservation],
) -> JsonValue:
    if _is_observation_ref(value):
        assert isinstance(value, dict)
        step_id, path = _parse_observation_ref(value)
        observation = observations.get(step_id)
        if observation is None or observation.status != "observed":
            raise ValueError(
                "ToolProgram observation reference requires an already observed prior step"
            )
        # HarnessToolObservation.sealed bytes, not its mutable convenience view,
        # are the authority. A bridge or caller may mutate structured_content
        # after return; that must not redirect a later physical Tool Call or
        # disagree with the retained observation digest.
        return _lookup_path(observation.to_dict()["structuredContent"], path)
    if isinstance(value, dict):
        resolved = {key: _resolve_template(child, observations) for key, child in value.items()}
        validate_json_value(resolved)
        return resolved
    if isinstance(value, list):
        resolved_list = [_resolve_template(child, observations) for child in value]
        validate_json_value(resolved_list)
        return resolved_list
    validate_json_value(value)
    return value
