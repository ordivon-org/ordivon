"""Deterministic ToolProgram execution over already-admitted Harness Tools.

Public names remain import-compatible here, while versioned ToolProgram wire
values and validation live in tool_program_contract without executing Tools.
"""

from __future__ import annotations

from dataclasses import dataclass

from anc_canonical import JsonValue, canonical_digest, validate_json_value

from .agent_tool_observation import HarnessToolObservation
from .ordivon.model import AgentToolCall, AgentToolDefinition
from .ordivon.tool_bridge import ToolBridge
from .tool_program_contract import (
    _MAX_STEPS,
    _is_observation_ref,
    _parse_observation_ref,
    _text,
    HarnessToolProgram,
    HarnessToolProgramAction,
    HarnessToolProgramStep,
    observation_ref,
)


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
        return _lookup_path(observation.structured_content, path)
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


def project_tool_program_action_capability(
    *,
    admitted_tools: tuple[AgentToolDefinition, ...],
    remaining_tool_calls: int,
) -> dict[str, JsonValue]:
    """Project dormant program-composition capability without granting any Tool."""

    if type(remaining_tool_calls) is not int or remaining_tool_calls < 0:
        raise ValueError("ToolProgram capability remaining Tool budget must be non-negative")
    names = [definition.name for definition in admitted_tools]
    if len(names) != len(set(names)):
        raise ValueError("ToolProgram capability Tool names must be unique")
    value: dict[str, JsonValue] = {
        "schemaVersion": 1,
        "kind": "ordivon.harness-tool-program-action-capability",
        "truthRole": "derived-turn-composition-capability",
        "admittedToolNames": sorted(names),
        "maxProgramSteps": min(_MAX_STEPS, remaining_tool_calls),
        "physicalToolAccounting": "one-existing-tool-budget-unit-per-program-step",
        "executionAuthority": "existing-exact-turn-tool-surface-only",
        "runtimeTool": False,
    }
    validate_json_value(value)
    return value


@dataclass(frozen=True, slots=True)
class HarnessToolProgramResult:
    program_digest: str
    status: str
    observations: tuple[HarnessToolObservation, ...]
    output: dict[str, JsonValue]

    def __post_init__(self) -> None:
        if self.status not in {
            "completed",
            "rejected",
            "unknown",
            "cancel-requested",
            "cancelled",
        }:
            raise ValueError(f"unsupported ToolProgram result status: {self.status}")
        validate_json_value(self.output)
        if self.status == "completed" and any(
            observation.status != "observed" for observation in self.observations
        ):
            raise ValueError("completed ToolProgram contains a non-observed step")

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, JsonValue]:
        value: dict[str, JsonValue] = {
            "schemaVersion": 1,
            "kind": "ordivon.harness-tool-program-result",
            "programDigest": self.program_digest,
            "status": self.status,
            "observations": [observation.to_dict() for observation in self.observations],
            "output": self.output,
        }
        validate_json_value(value)
        return value

    def to_model_projection(self) -> dict[str, JsonValue]:
        """Project bounded program outcome without replaying intermediate content."""

        value: dict[str, JsonValue] = {
            "schemaVersion": 1,
            "kind": "ordivon.harness-tool-program-model-projection",
            "programDigest": self.program_digest,
            "status": self.status,
            "steps": [
                {
                    "toolCallId": observation.tool_call_id,
                    "toolName": observation.tool_name,
                    "status": observation.status,
                    "observationDigest": observation.digest,
                    "runtimeJobRef": observation.runtime_job_ref,
                    "artifactRefs": [item.to_dict() for item in observation.artifact_refs],
                    "reconciled": observation.reconciled,
                }
                for observation in self.observations
            ],
            "output": self.output,
        }
        validate_json_value(value)
        return value


class HarnessToolProgramExecutor:
    """Execute one bounded ToolProgram over one exact already-admitted Tool surface."""

    def __init__(
        self,
        bridge: ToolBridge,
        admitted_tools: tuple[AgentToolDefinition, ...],
    ) -> None:
        names = [definition.name for definition in admitted_tools]
        if len(names) != len(set(names)):
            raise ValueError("ToolProgram admitted Tool names must be unique")
        self.bridge = bridge
        self.admitted_tools = frozenset(names)

    def execute(
        self,
        program: HarnessToolProgram,
        *,
        remaining_tool_calls: int,
        step_prefix: str,
    ) -> HarnessToolProgramResult:
        if type(remaining_tool_calls) is not int or remaining_tool_calls < 0:
            raise ValueError("ToolProgram remaining Tool budget must be non-negative")
        _text(step_prefix, "ToolProgram step prefix", max_bytes=240)
        if len(program.steps) > remaining_tool_calls:
            raise ValueError("ToolProgram exceeds remaining Tool Call budget")
        denied = sorted({step.tool_name for step in program.steps} - self.admitted_tools)
        if denied:
            raise ValueError(
                "ToolProgram references Tools not admitted on the exact turn: "
                + ", ".join(denied)
            )

        observations_by_step: dict[str, HarnessToolObservation] = {}
        observations: list[HarnessToolObservation] = []
        token = program.digest[7:31]
        for index, step in enumerate(program.steps, start=1):
            resolved_arguments = _resolve_template(step.arguments, observations_by_step)
            if not isinstance(resolved_arguments, dict):
                raise ValueError("ToolProgram step arguments must resolve to an object")
            call = AgentToolCall(
                tool_call_id=f"tool-call:program:{token}:{index}",
                name=step.tool_name,
                arguments=resolved_arguments,
            )
            observation = self.bridge.execute(
                call,
                step_id=f"{step_prefix}:program:{token}:{index}:{step.step_id}",
            )
            if (
                observation.tool_call_id != call.tool_call_id
                or observation.tool_name != call.name
            ):
                raise ValueError("ToolProgram bridge returned an observation for a different Tool Call")
            observations.append(observation)
            observations_by_step[step.step_id] = observation
            if observation.status != "observed":
                return HarnessToolProgramResult(
                    program_digest=program.digest,
                    status=observation.status,
                    observations=tuple(observations),
                    output={},
                )

        resolved_output = _resolve_template(program.outputs, observations_by_step)
        if not isinstance(resolved_output, dict):
            raise ValueError("ToolProgram outputs must resolve to an object")
        return HarnessToolProgramResult(
            program_digest=program.digest,
            status="completed",
            observations=tuple(observations),
            output=resolved_output,
        )


__all__ = [
    "HarnessToolProgram",
    "HarnessToolProgramAction",
    "HarnessToolProgramExecutor",
    "HarnessToolProgramResult",
    "HarnessToolProgramStep",
    "observation_ref",
]
