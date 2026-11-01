"""Pure, versioned ToolProgram values independent of execution and ToolBridge.

The execution owner imports these contracts; AgentTurnResult may validate and
round-trip the action without importing the executor or opening a Tool surface.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from anc_canonical import JsonValue, canonical_bytes, canonical_digest, validate_json_value


_OBSERVATION_REF_KEY = "$harnessObservationRef"
_MAX_STEPS = 32
_MAX_PATH_SEGMENTS = 16
_MAX_PROGRAM_BYTES = 131_072
_MAX_STEP_ID_BYTES = 120
_MAX_OUTPUTS = 32


def _text(value: Any, label: str, *, max_bytes: int) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{label} must be non-empty and trimmed")
    if len(value.encode("utf-8")) > max_bytes:
        raise ValueError(f"{label} exceeds {max_bytes} UTF-8 bytes")
    return value


def _is_observation_ref(value: Any) -> bool:
    return isinstance(value, dict) and set(value) == {_OBSERVATION_REF_KEY}


def _parse_observation_ref(value: dict[str, Any]) -> tuple[str, tuple[str | int, ...]]:
    raw = value[_OBSERVATION_REF_KEY]
    if not isinstance(raw, dict) or set(raw) != {"stepId", "path"}:
        raise ValueError("ToolProgram observation reference fields differ")
    step_id = _text(raw["stepId"], "ToolProgram observation reference step", max_bytes=_MAX_STEP_ID_BYTES)
    path = raw["path"]
    if (
        not isinstance(path, list)
        or not path
        or len(path) > _MAX_PATH_SEGMENTS
        or any(
            (not isinstance(segment, str) or not segment or segment != segment.strip())
            if not isinstance(segment, int)
            else segment < 0
            for segment in path
        )
        or any(isinstance(segment, bool) for segment in path)
    ):
        raise ValueError("ToolProgram observation reference path is invalid")
    return step_id, tuple(path)


def observation_ref(step_id: str, *path: str | int) -> dict[str, JsonValue]:
    """Return the canonical JSON marker for one prior observation data reference.

    Paths are relative to ``HarnessToolObservation.structured_content``. The
    reference substitutes the exact JSON value at that path; string interpolation
    and arbitrary expressions are intentionally unsupported.
    """

    marker: dict[str, JsonValue] = {
        _OBSERVATION_REF_KEY: {
            "stepId": step_id,
            "path": list(path),
        }
    }
    _parse_observation_ref(marker)
    validate_json_value(marker)
    return marker


def _walk_refs(value: JsonValue) -> tuple[tuple[str, tuple[str | int, ...]], ...]:
    refs: list[tuple[str, tuple[str | int, ...]]] = []

    def walk(item: JsonValue) -> None:
        if _is_observation_ref(item):
            assert isinstance(item, dict)
            refs.append(_parse_observation_ref(item))
            return
        if isinstance(item, dict):
            for child in item.values():
                walk(child)
            return
        if isinstance(item, list):
            for child in item:
                walk(child)

    walk(value)
    return tuple(refs)



@dataclass(frozen=True, slots=True)
class HarnessToolProgramStep:
    step_id: str
    tool_name: str
    arguments: dict[str, JsonValue]

    def __post_init__(self) -> None:
        _text(self.step_id, "ToolProgram step identity", max_bytes=_MAX_STEP_ID_BYTES)
        _text(self.tool_name, "ToolProgram Tool name", max_bytes=120)
        validate_json_value(self.arguments)

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "stepId": self.step_id,
            "toolName": self.tool_name,
            "arguments": self.arguments,
        }


@dataclass(frozen=True, slots=True)
class HarnessToolProgram:
    steps: tuple[HarnessToolProgramStep, ...]
    outputs: dict[str, JsonValue]

    def __post_init__(self) -> None:
        if not self.steps or len(self.steps) > _MAX_STEPS:
            raise ValueError(f"ToolProgram requires 1..{_MAX_STEPS} steps")
        step_ids = [step.step_id for step in self.steps]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("ToolProgram step identities must be unique")
        if len(self.outputs) > _MAX_OUTPUTS:
            raise ValueError(f"ToolProgram outputs exceed {_MAX_OUTPUTS}")
        for name in self.outputs:
            _text(name, "ToolProgram output name", max_bytes=120)
        validate_json_value(self.outputs)

        available: set[str] = set()
        for step in self.steps:
            for ref_step, _ in _walk_refs(step.arguments):
                if ref_step not in available:
                    raise ValueError(
                        "ToolProgram step may reference only an already completed prior step"
                    )
            available.add(step.step_id)
        for ref_step, _ in _walk_refs(self.outputs):
            if ref_step not in available:
                raise ValueError("ToolProgram output references an unknown step")
        if len(canonical_bytes(self.to_dict())) > _MAX_PROGRAM_BYTES:
            raise ValueError(f"ToolProgram exceeds {_MAX_PROGRAM_BYTES} canonical bytes")

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, JsonValue]:
        value: dict[str, JsonValue] = {
            "schemaVersion": 1,
            "kind": "ordivon.harness-tool-program",
            "steps": [step.to_dict() for step in self.steps],
            "outputs": self.outputs,
        }
        validate_json_value(value)
        return value

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "HarnessToolProgram":
        if set(value) != {"schemaVersion", "kind", "steps", "outputs"}:
            raise ValueError("HarnessToolProgram fields differ")
        if (
            type(value["schemaVersion"]) is not int
            or value["schemaVersion"] != 1
            or value["kind"] != "ordivon.harness-tool-program"
        ):
            raise ValueError("HarnessToolProgram identity is invalid")
        raw_steps = value["steps"]
        raw_outputs = value["outputs"]
        if not isinstance(raw_steps, list) or any(not isinstance(item, dict) for item in raw_steps):
            raise ValueError("HarnessToolProgram steps are invalid")
        if not isinstance(raw_outputs, dict):
            raise ValueError("HarnessToolProgram outputs are invalid")
        steps: list[HarnessToolProgramStep] = []
        for raw in raw_steps:
            if set(raw) != {"stepId", "toolName", "arguments"} or not isinstance(raw["arguments"], dict):
                raise ValueError("HarnessToolProgramStep fields are invalid")
            steps.append(
                HarnessToolProgramStep(
                    step_id=raw["stepId"],
                    tool_name=raw["toolName"],
                    arguments=dict(raw["arguments"]),
                )
            )
        return cls(steps=tuple(steps), outputs=dict(raw_outputs))


@dataclass(frozen=True, slots=True)
class HarnessToolProgramAction:
    """One Harness-native program action over already-admitted Runtime/World Tools.

    This is deliberately not ``AgentToolCall``: one action may require many
    physical Tool Calls, and accounting/recovery must continue to see every inner
    effect rather than treating the envelope as one Runtime Tool.
    """

    action_call_id: str
    program: HarnessToolProgram

    def __post_init__(self) -> None:
        _text(self.action_call_id, "ToolProgram action Call identity", max_bytes=300)
        if not isinstance(self.program, HarnessToolProgram):
            raise TypeError("ToolProgram action requires HarnessToolProgram")

    @property
    def physical_tool_calls(self) -> int:
        return len(self.program.steps)

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, JsonValue]:
        value: dict[str, JsonValue] = {
            "schemaVersion": 1,
            "kind": "ordivon.harness-tool-program-action",
            "actionCallId": self.action_call_id,
            "program": self.program.to_dict(),
            "physicalToolCalls": self.physical_tool_calls,
        }
        validate_json_value(value)
        return value

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "HarnessToolProgramAction":
        if set(value) != {
            "schemaVersion",
            "kind",
            "actionCallId",
            "program",
            "physicalToolCalls",
        }:
            raise ValueError("HarnessToolProgramAction fields differ")
        if (
            type(value["schemaVersion"]) is not int
            or value["schemaVersion"] != 1
            or value["kind"] != "ordivon.harness-tool-program-action"
        ):
            raise ValueError("HarnessToolProgramAction identity is invalid")
        raw_program = value["program"]
        if not isinstance(raw_program, dict):
            raise ValueError("HarnessToolProgramAction program is invalid")
        action = cls(
            action_call_id=value["actionCallId"],
            program=HarnessToolProgram.from_dict(raw_program),
        )
        if (
            type(value["physicalToolCalls"]) is not int
            or value["physicalToolCalls"] != action.physical_tool_calls
        ):
            raise ValueError("HarnessToolProgramAction physical Tool count differs")
        return action
