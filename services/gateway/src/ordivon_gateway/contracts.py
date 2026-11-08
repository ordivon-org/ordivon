from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


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
    context_mode: Literal["none", "provider-defined-string", "provider-defined-json"]
    contexts: list[Any] = Field(default_factory=list)
    owner_node_id: str | None = None
    owner_node_ids: list[str] = Field(default_factory=list)
    observation_error: str | None = None
    truth_boundary: str
    description: str = ""
    tags: list[str] = Field(default_factory=list)

    readiness_state: Literal["ready", "not_ready", "unknown"] = "unknown"

    @model_validator(mode="after")
    def derive_readiness_state(self) -> CapabilityDescriptor:
        """Single truth rule, represented as a normal MCP-schema field.

        MCP's tool response validation uses the validation-mode JSON Schema.
        Pydantic computed fields appear only in the serialization schema and
        would be rejected by MCP as extra output: derive a declared field here.
        """
        if self.available:
            self.readiness_state = "ready"
        elif self.observation_error is not None:
            # Configuration is a distinct fact. A failed observation does not
            # establish the natural Owner's operational readiness either way.
            self.readiness_state = "unknown"
        else:
            self.readiness_state = "not_ready"
        return self


class CapabilitySearchMatch(StrictModel):
    match_kind: Literal["exact", "prefix", "token", "substring"]
    capability: CapabilityDescriptor


class CapabilitySearchProjection(StrictModel):
    schema_version: Literal[1] = 1
    kind: Literal["ordivon.gateway-capability-search"] = "ordivon.gateway-capability-search"
    truth_role: Literal["rebuildable-non-authoritative-discovery-projection"] = (
        "rebuildable-non-authoritative-discovery-projection"
    )
    query: str
    projection_digest: str
    route_digest: str | None = None
    total_matches: int
    matches: list[CapabilitySearchMatch]


class SystemDescription(StrictModel):
    schema_version: Literal[1] = 1
    kind: Literal["ordivon.gateway-system-description"] = "ordivon.gateway-system-description"
    gateway_version: str
    route_digest: str | None = None
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
    route_digest: str | None = None
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


class ExecutionResolution(StrictModel):
    schema_version: Literal[1] = 1
    kind: Literal["ordivon.gateway-execution-resolution"] = "ordivon.gateway-execution-resolution"
    request_id: str
    capability: str
    owner_id: str
    resolution: Literal["found", "absent", "ambiguous"]
    operation_ref: str | None = None
    native_id: str | None = None
    # Exact Runtime job.list workspace identity. None means unqualified legacy
    # resolution, not proof that the caller's requested workspace matches.
    workspace_id: str | None = None


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


class CapabilityInvocationRecipe(StrictModel):
    recipe_id: str
    kind: Literal["skill", "mise-task", "owner-cli"]
    owner_id: str
    command: list[str] = Field(default_factory=list)
    note: str = ""


class CapabilitySkillBinding(StrictModel):
    ref: str
    skill_id: str
    name: str
    instruction_digest: str
    package_revision: str
    snapshot_revision: str
    instruction_authority: str


class CapabilityResolution(StrictModel):
    schema_version: Literal[1] = 1
    kind: Literal["ordivon.gateway-capability-resolution"] = "ordivon.gateway-capability-resolution"
    truth_role: Literal["non-authoritative-composition-route"] = (
        "non-authoritative-composition-route"
    )
    capability: str
    semantic_owner: str
    completion_owner: str
    execution_capability: str | None = None
    study_types: list[str] = Field(default_factory=list)
    skill_candidates: list[str] = Field(default_factory=list)
    selected_skill: CapabilitySkillBinding | None = None
    invocation_recipes: list[CapabilityInvocationRecipe] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    observation_errors: list[str] = Field(default_factory=list)
    non_claims: list[str] = Field(default_factory=list)
    resolution_digest: str
