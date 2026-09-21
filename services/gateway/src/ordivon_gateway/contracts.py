from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class OwnerDescriptor(StrictModel):
    owner_id: str
    role: str
    configured: bool


class CapabilityDescriptor(StrictModel):
    capability: str
    owner_id: str
    category: str
    configured: bool
    context_mode: Literal["none", "provider-defined-string"]
    truth_boundary: str


class SystemDescription(StrictModel):
    schema_version: Literal[1] = 1
    kind: Literal["ordivon.gateway-system-description"] = "ordivon.gateway-system-description"
    gateway_version: str = "0.1.0"
    truth_role: Literal["non-authoritative-routing-projection"] = (
        "non-authoritative-routing-projection"
    )
    owners: list[OwnerDescriptor]
    capabilities: list[str]


class CapabilityProjection(StrictModel):
    schema_version: Literal[1] = 1
    kind: Literal["ordivon.gateway-capability-projection"] = "ordivon.gateway-capability-projection"
    truth_role: Literal["rebuildable-non-authoritative-projection"] = (
        "rebuildable-non-authoritative-projection"
    )
    capabilities: list[CapabilityDescriptor]


class ExecutionReceipt(StrictModel):
    schema_version: Literal[1] = 1
    kind: Literal["ordivon.gateway-execution-receipt"] = "ordivon.gateway-execution-receipt"
    operation_ref: str
    capability: str
    owner_id: str
    native_id: str
    state: str
    terminal: bool
    delivery_disposition: str | None = None


class ExecutionObservation(ExecutionReceipt):
    kind: Literal["ordivon.gateway-execution-observation"] = "ordivon.gateway-execution-observation"
    execution_disposition: str | None = None
    exit_code: int | None = None
    recovery_required: bool | None = None
    artifact_count: int | None = None
    artifact_ids: list[str] = Field(default_factory=list)


class ArtifactChunk(StrictModel):
    schema_version: Literal[1] = 1
    kind: Literal["ordivon.gateway-artifact-chunk"] = "ordivon.gateway-artifact-chunk"
    operation_ref: str
    owner_id: str
    native_id: str
    artifact_id: str
    offset: int
    next_offset: int
    eof: bool
    digest: str
    content: str


class ContinuityItem(StrictModel):
    task_id: str
    goal_id: str | None = None
    revision: int
    state: str
    checkpoint_digest: str | None = None


class ContinuityObservation(ContinuityItem):
    schema_version: Literal[1] = 1
    kind: Literal["ordivon.gateway-continuity-observation"] = (
        "ordivon.gateway-continuity-observation"
    )
    truth_role: Literal["host-continuity-projection"] = "host-continuity-projection"
    checkpoint: dict[str, Any]
    truth_boundary: str | None = None


class ContinuityPage(StrictModel):
    schema_version: Literal[1] = 1
    kind: Literal["ordivon.gateway-continuity-page"] = "ordivon.gateway-continuity-page"
    truth_role: Literal["host-continuity-projection"] = "host-continuity-projection"
    items: list[ContinuityItem]
    has_more: bool
    next_cursor: str | None = None
