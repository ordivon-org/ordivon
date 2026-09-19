from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, WithJsonSchema


class WorkingCheckpointRuntime(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspaceId: str = Field(min_length=1, max_length=512)
    relevantJobIds: list[str] = Field(max_length=64)
    observedHeadRevision: str | None = Field(default=None, max_length=512)


class WorkingCheckpointWake(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["ANY", "ALL", "NONE", "UNKNOWN"]
    conditions: list[str] = Field(max_length=8)


class WorkingCheckpointStanding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schemaVersion: Literal[1]
    truthRole: Literal["checkpoint-authored-work-standing"]
    attention: Literal["ACTIVE", "BACKGROUND", "WAIT", "HOLD", "NONE", "UNSPECIFIED"]
    executionAdmission: Literal[
        "ADMITTED_NOW", "REENTRY_REQUIRED", "BLOCKED", "NOT_APPLICABLE", "UNKNOWN"
    ]
    valueNow: Literal["POSITIVE_VALUE_NOW", "NO_POSITIVE_VALUE_NOW", "UNKNOWN"]
    progress: Literal["OPEN_FRONTIER", "SATURATED", "LOCALLY_COMPLETE", "UNKNOWN"]
    lineage: Literal["SELF_STANDING", "SUBSUMED", "SUPERSEDED", "UNKNOWN"]
    relatedTaskIds: list[str] = Field(max_length=8)
    blockerKinds: list[
        Literal[
            "EVENT",
            "OWNER",
            "CONSUMER",
            "HUMAN",
            "DEPENDENCY",
            "SOURCE_CHANGE",
            "AUTHORITY",
            "RESOURCE",
            "POLICY",
            "OTHER",
            "UNKNOWN",
        ]
    ] = Field(max_length=8)
    wake: WorkingCheckpointWake
    carrier: Literal["RETAIN", "CLOSE_CLEAN", "DIRTY_HANDOFF", "UNSPECIFIED"]


class WorkingCheckpointV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schemaVersion: Literal[1]
    kind: Literal["ordivon.host-working-checkpoint"]
    truthRole: Literal["semantic-working-claim"]
    taskId: str = Field(min_length=6, max_length=4096, pattern=r"^task:")
    objective: str = Field(min_length=1, max_length=4096)
    frontier: str = Field(min_length=1, max_length=4096)
    established: list[str] = Field(max_length=64)
    unresolved: list[str] = Field(max_length=64)
    rejected: list[str] = Field(max_length=64)
    constraints: list[str] = Field(max_length=64)
    nextActions: list[str] = Field(max_length=64)
    runtime: WorkingCheckpointRuntime | None


class WorkingCheckpointV2(WorkingCheckpointV1):
    schemaVersion: Literal[2]
    workStanding: WorkingCheckpointStanding


def _inline_schema(model: type[BaseModel]) -> dict[str, Any]:
    schema = model.model_json_schema()
    definitions = schema.pop("$defs", {})

    def inline(node: object) -> object:
        if isinstance(node, list):
            return [inline(item) for item in node]
        if not isinstance(node, dict):
            return node
        reference = node.get("$ref")
        if isinstance(reference, str) and reference.startswith("#/$defs/"):
            name = reference.removeprefix("#/$defs/")
            definition = definitions.get(name)
            if not isinstance(definition, dict):
                raise TypeError(f"checkpoint schema definition missing: {name}")
            return inline(definition)
        return {key: inline(value) for key, value in node.items()}

    result = inline(schema)
    if not isinstance(result, dict):
        raise TypeError("checkpoint schema is not an object")
    return result


def full_checkpoint_schema() -> dict[str, Any]:
    return {
        "oneOf": [_inline_schema(WorkingCheckpointV1), _inline_schema(WorkingCheckpointV2)],
        "description": (
            "A complete Host semantic working checkpoint. v2 adds caller-authored workStanding; "
            "Host validates and persists that claim shape but does not interpret it as priority, "
            "ownership, execution authority, or foreign Runtime/domain truth."
        ),
    }


WorkingCheckpointInput = Annotated[
    dict[str, Any],
    WithJsonSchema(full_checkpoint_schema()),
]


def validate_full_checkpoint(task_id: str, value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError("checkpoint must be an object")
    version = value.get("schemaVersion")
    if version == 1:
        parsed: BaseModel = WorkingCheckpointV1.model_validate(value)
    elif version == 2:
        parsed = WorkingCheckpointV2.model_validate(value)
    else:
        raise ValueError("checkpoint schemaVersion must be 1 or 2")
    encoded = parsed.model_dump(mode="json")
    if encoded["taskId"] != task_id:
        raise ValueError("checkpoint taskId must equal taskId")
    return encoded
