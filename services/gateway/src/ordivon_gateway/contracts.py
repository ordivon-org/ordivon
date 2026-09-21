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
    available: bool
    context_mode: Literal["none", "provider-defined-string"]
    contexts: list[str] = Field(default_factory=list)
    owner_node_id: str | None = None
    owner_node_ids: list[str] = Field(default_factory=list)
    observation_error: str | None = None
    truth_boundary: str


class SystemDescription(StrictModel):
    schema_version: Literal[1] = 1
    kind: Literal["ordivon.gateway-system-description"] = "ordivon.gateway-system-description"
    gateway_version: str
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
    projection_digest: str
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
    artifacts_available: bool | None = None
    artifact_count: int | None = None
    artifact_ids: list[str] = Field(default_factory=list)
    artifact_projection_complete: bool | None = None


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


class ContinuityEvent(StrictModel):
    revision: int
    event_type: str
    state: str
    created_at: str


class ContinuityObserved(ContinuityObservation):
    kind: Literal["ordivon.gateway-continuity-observed"] = "ordivon.gateway-continuity-observed"
    recent_events: list[ContinuityEvent] = Field(default_factory=list)


class ContinuityMutationReceipt(ContinuityObservation):
    kind: Literal["ordivon.gateway-continuity-mutation"] = "ordivon.gateway-continuity-mutation"
    admission: str
    writer_label: str | None = None


class ContinuityAttention(StrictModel):
    schema_version: Literal[1] = 1
    kind: Literal["ordivon.gateway-continuity-attention"] = "ordivon.gateway-continuity-attention"
    truth_role: Literal["host-navigation-projection"] = "host-navigation-projection"
    board_fence: dict[str, Any]
    summary: dict[str, Any]
    routed_tasks: list[dict[str, Any]]
    unrouted_messages: list[dict[str, Any]]
    truth_boundary: str | None = None


class CollaborationMessage(StrictModel):
    sequence: int
    client_message_id: str
    author_label: str
    author_identity_role: str
    message_kind: str
    topic: str | None = None
    message: str
    reply_to_client_message_id: str | None = None
    task_id: str | None = None
    recorded_at_ms: int
    message_digest: str
    truth_role: str


class CollaborationPostReceipt(StrictModel):
    schema_version: Literal[1] = 1
    kind: Literal["ordivon.gateway-collaboration-post"] = "ordivon.gateway-collaboration-post"
    truth_role: Literal["host-collaboration-projection"] = "host-collaboration-projection"
    admission: str
    message: CollaborationMessage
    truth_boundary: str | None = None


class CollaborationPage(StrictModel):
    schema_version: Literal[1] = 1
    kind: Literal["ordivon.gateway-collaboration-page"] = "ordivon.gateway-collaboration-page"
    truth_role: Literal["host-collaboration-projection"] = "host-collaboration-projection"
    messages: list[CollaborationMessage]
    last_sequence: int
    next_after_sequence: int
    has_more: bool
    truth_boundary: str | None = None


class CollaborationSearchHit(StrictModel):
    sequence: int
    client_message_id: str


class CollaborationSearch(StrictModel):
    schema_version: Literal[1] = 1
    kind: Literal["ordivon.gateway-collaboration-search"] = "ordivon.gateway-collaboration-search"
    truth_role: Literal["host-navigation-projection"] = "host-navigation-projection"
    source_snapshot_high_water: int
    live_high_water: int
    negative_result_authoritative: bool
    requires_exact_source_reentry: bool
    results: list[CollaborationSearchHit]
