//! Versioned, typed northbound MCP contracts for A-owned Work Engagement.
//!
//! The action is decoded by A's original Rust serde/domain type; schema-only
//! mirrors below describe the wire and response, not another state machine.
//! No extra Work table/queue or Python runtime dependency is introduced.
#![allow(dead_code)]
use std::sync::Arc;

use rmcp::handler::server::tool::schema_for_output;
use rmcp::model::JsonObject;
use schemars::JsonSchema;
use serde::Deserialize;

use crate::work::engagement::{EngagementAction, Phase};

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct AdvanceRequest {
    pub work_ref: String,
    pub expected_revision: i64,
    pub actor_ref: String,
    /// Explicit caller intent ID: real response loss must preserve reply identity.
    pub client_request_id: String,
    #[schemars(with = "ActionShape")]
    pub action: EngagementAction,
}

#[derive(JsonSchema)]
#[serde(
    tag = "type",
    rename_all = "snake_case",
    rename_all_fields = "camelCase"
)]
enum ActionShape {
    Offer {
        consumer_actor_ref: String,
        acceptance_criteria: Vec<String>,
    },
    Claim,
    Release {
        reason: String,
    },
    Submit {
        claim_epoch: i64,
        delivery_ref: String,
        summary: String,
        output_refs: Vec<String>,
        evidence_refs: Vec<String>,
    },
    Review {
        claim_epoch: i64,
        decision: ReviewDecisionShape,
        rationale: String,
        verification_refs: Vec<String>,
    },
    Cancel {
        reason: String,
    },
}

#[derive(JsonSchema)]
#[serde(rename_all = "snake_case")]
enum ReviewDecisionShape {
    Accepted,
    Returned,
}

#[derive(JsonSchema)]
#[serde(rename_all = "snake_case")]
enum PhaseShape {
    Offered,
    Claimed,
    Submitted,
    Returned,
    Accepted,
    Cancelled,
}

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct ListRequest {
    #[serde(default)]
    #[schemars(with = "Option<PhaseShape>")]
    pub phase: Option<Phase>,
    #[serde(default)]
    pub assignee_actor_ref: Option<String>,
    #[serde(default)]
    pub consumer_actor_ref: Option<String>,
    #[serde(default = "default_limit")]
    pub limit: usize,
    #[serde(default = "default_max_bytes")]
    pub max_bytes: usize,
    #[serde(default)]
    pub before_updated_at: Option<String>,
    #[serde(default)]
    pub before_work_ref: Option<String>,
}

const fn default_limit() -> usize {
    50
}
const fn default_max_bytes() -> usize {
    262_144
}

#[derive(JsonSchema)]
#[serde(rename_all = "snake_case")]
enum WorkStanding {
    Open,
    Completed,
    Abandoned,
}

#[derive(JsonSchema)]
#[serde(rename_all = "snake_case")]
enum ReceiptAdmission {
    Committed,
    Existing,
}

#[derive(JsonSchema)]
#[serde(rename_all = "camelCase")]
struct DeliveryShape {
    delivery_ref: String,
    summary: String,
    output_refs: Vec<String>,
    evidence_refs: Vec<String>,
}

#[derive(JsonSchema)]
#[serde(rename_all = "camelCase")]
struct ReviewShape {
    decision: ReviewDecisionShape,
    rationale: String,
    verification_refs: Vec<String>,
}

/// The versioned immutable payload stored by A's existing Work Snapshot CAS.
#[derive(JsonSchema)]
#[serde(rename_all = "camelCase")]
struct EngagementShape {
    schema_version: u8,
    phase: PhaseShape,
    requested_by_actor_ref: String,
    consumer_actor_ref: String,
    acceptance_criteria: Vec<String>,
    claim_epoch: i64,
    #[serde(skip_serializing_if = "Option::is_none")]
    assignee_actor_ref: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    delivery: Option<DeliveryShape>,
    #[serde(skip_serializing_if = "Option::is_none")]
    review: Option<ReviewShape>,
    #[serde(skip_serializing_if = "Option::is_none")]
    transition_note: Option<String>,
}

#[derive(JsonSchema)]
#[serde(rename_all = "camelCase")]
struct WorkSnapshotEngagedShape {
    objective: String,
    frontier: String,
    established: Vec<String>,
    unresolved: Vec<String>,
    rejected: Vec<String>,
    constraints: Vec<String>,
    next_actions: Vec<String>,
    reference_refs: Vec<String>,
    engagement: EngagementShape,
}

#[derive(JsonSchema)]
#[serde(rename_all = "camelCase")]
struct AdvanceOutput {
    schema_version: u32,
    #[schemars(extend("const" = "ordivon.host-work"))]
    kind: String,
    admission: ReceiptAdmission,
    work_ref: String,
    work_kind: String,
    state: WorkStanding,
    revision: i64,
    snapshot_digest: String,
    snapshot: WorkSnapshotEngagedShape,
    writer_actor_ref: String,
    created_by_actor_ref: String,
    created_at: String,
    updated_at: String,
    truth_boundary: String,
}

#[derive(JsonSchema)]
#[serde(rename_all = "camelCase")]
struct EngagementListItem {
    work_ref: String,
    work_kind: String,
    state: WorkStanding,
    revision: i64,
    snapshot_digest: String,
    updated_at: String,
    engagement: EngagementShape,
}

#[derive(JsonSchema)]
#[serde(rename_all = "camelCase")]
struct EngagementCursor {
    before_updated_at: String,
    before_work_ref: String,
}

#[derive(JsonSchema)]
#[serde(rename_all = "camelCase")]
struct ListOutput {
    schema_version: u32,
    #[schemars(extend("const" = "ordivon.host-work-engagement-list"))]
    kind: String,
    engagements: Vec<EngagementListItem>,
    has_more: bool,
    next_cursor: Option<EngagementCursor>,
    ranking_applied: bool,
    truth_boundary: String,
}

/// Official rmcp's native typed output helper; no invented permissive schemas.
pub fn advance_output_schema() -> Arc<JsonObject> {
    schema_for_output::<AdvanceOutput>()
}
pub fn list_output_schema() -> Arc<JsonObject> {
    schema_for_output::<ListOutput>()
}
