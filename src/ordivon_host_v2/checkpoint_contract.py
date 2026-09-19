from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, WithJsonSchema


class WorkingCheckpointRuntime(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspaceId: str = Field(min_length=1, max_length=512)
    relevantJobIds: list[str] = Field(max_length=64)
    observedHeadRevision: str | None = Field(default=None, max_length=512)


class WorkingCheckpoint(BaseModel):
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
    schema = _inline_schema(WorkingCheckpoint)
    schema["description"] = (
        "A complete Host semantic working checkpoint. Host validates and persists this caller "
        "claim but does not interpret it as priority, ownership, execution authority, or foreign "
        "Runtime/domain truth."
    )
    return schema


WorkingCheckpointInput = Annotated[
    dict[str, Any],
    WithJsonSchema(full_checkpoint_schema()),
]


def validate_full_checkpoint(task_id: str, value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError("checkpoint must be an object")
    parsed = WorkingCheckpoint.model_validate(value)
    encoded = parsed.model_dump(mode="json")
    if encoded["taskId"] != task_id:
        raise ValueError("checkpoint taskId must equal taskId")
    return encoded
