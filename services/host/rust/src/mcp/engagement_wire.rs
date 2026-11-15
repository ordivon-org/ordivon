//! Versioned, typed northbound MCP contracts for A-owned Work Engagement.
//!
//! A's actual Work domain Serde types ALSO own the JSON Schema for
//! action/phase/delivery/review/engagement. Only MCP-specific response
//! envelopes are declared here; no duplicate command enum or state machine.
//! No extra Work table/queue or Python runtime dependency is introduced.
#![allow(dead_code)]
use std::sync::Arc;

use rmcp::handler::server::tool::schema_for_output;
use rmcp::model::JsonObject;
use schemars::JsonSchema;
use serde::Deserialize;

use crate::work::engagement::{EngagementAction, Phase, WorkEngagement};

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct AdvanceRequest {
    pub work_ref: String,
    pub expected_revision: i64,
    pub actor_ref: String,
    /// Explicit caller intent ID: real response loss must preserve reply identity.
    pub client_request_id: String,
    pub action: EngagementAction,
}

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct ListRequest {
    #[serde(default)]
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
struct WorkSnapshotEngagedShape {
    objective: String,
    frontier: String,
    established: Vec<String>,
    unresolved: Vec<String>,
    rejected: Vec<String>,
    constraints: Vec<String>,
    next_actions: Vec<String>,
    reference_refs: Vec<String>,
    engagement: WorkEngagement,
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
    engagement: WorkEngagement,
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
