use rusqlite::{params, Connection, OpenFlags};
use schemars::JsonSchema;
use serde::Serialize;
use std::collections::BTreeMap;
use std::path::PathBuf;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use super::registry::{
    load_attempt, load_job, load_reservation, CONDITION_RETIREMENT_MIGRATION_VERSION,
    MAX_MIGRATION_VERSION,
};
use super::{
    AttemptState, AttemptTerminationIntent, JobDesiredState, JobResolution, ReservationState,
    RuntimeError, RuntimeErrorCode, RuntimeExecutionPlan, RuntimeResult,
};

pub const RUNTIME_INSPECTION_SCHEMA_VERSION: u32 = 2;
pub const DEFAULT_INSPECTION_EVENT_LIMIT: u32 = 200;
pub const MAX_INSPECTION_EVENT_LIMIT: u32 = 1_000;
const MAX_INSPECTION_ATTEMPTS: u32 = 32;

#[derive(Clone, Debug)]
pub struct RuntimeInspectionConfig {
    pub db_path: PathBuf,
    pub busy_timeout_ms: u64,
}

#[derive(Clone, Debug, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeJobInspection {
    pub schema_version: u32,
    pub generated_at_ms: u64,
    pub migration_version: i64,
    pub job: RuntimeInspectionJob,
    pub attempts: Vec<RuntimeInspectionAttempt>,
    pub attempts_truncated: bool,
    pub artifacts: RuntimeInspectionArtifactSummary,
    pub episodes: RuntimeInspectionEpisodes,
    pub timeline: Vec<RuntimeInspectionEvent>,
    pub events_truncated: bool,
}

#[derive(Clone, Debug, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeInspectionJob {
    pub job_id: String,
    pub client_request_id: String,
    pub operation_digest: String,
    pub workspace_id: String,
    /// Exact source revision frozen into the admitted execution plan.
    pub source_revision: String,
    /// Exact source-state digest frozen at admission, including dirty/untracked source state.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub workspace_source_digest: Option<String>,
    pub created_at_ms: u64,
    pub desired_state: JobDesiredState,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub resolution: Option<JobResolution>,
    pub mechanically_converged: bool,
    pub semantic_completion_evaluated: bool,
}

#[derive(Clone, Debug, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeInspectionAttempt {
    pub attempt_id: String,
    pub attempt_number: u32,
    pub state: AttemptState,
    pub termination_intent: AttemptTerminationIntent,
    pub created_at_ms: u64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub started_at_ms: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub finished_at_ms: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub duration_ms: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub exit_code: Option<i32>,
    pub result_available: bool,
    pub reservation_state: ReservationState,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub reservation_release_reason: Option<String>,
    pub conditions: Vec<RuntimeInspectionCondition>,
    pub artifact_count: u64,
    pub artifact_bytes: u64,
    pub truncated_artifacts: u64,
}

#[derive(Clone, Debug, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeInspectionCondition {
    pub condition_type: String,
    pub status: String,
    pub reason_code: String,
    pub observed_at_ms: u64,
}

#[derive(Clone, Debug, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeInspectionArtifactSummary {
    pub count: u64,
    pub bytes: u64,
    pub truncated: u64,
    pub by_kind: BTreeMap<String, u64>,
}

#[derive(Clone, Debug, Default, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeInspectionEpisodes {
    pub dispatches: u64,
    pub duplicate_dispatches: u64,
    pub stop_requests: u64,
    pub reconciliation_failures: u64,
    pub reconciliation_convergences: u64,
    pub runner_result_recoveries: u64,
    pub resolution_corrections: u64,
    pub administrative_repairs: u64,
}

#[derive(Clone, Debug, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeInspectionEvent {
    pub sequence: u64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub attempt_id: Option<String>,
    pub event_type: String,
    pub origin: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub previous_state: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub new_state: Option<String>,
    pub reason_code: String,
    pub observed_at_ms: u64,
    pub elapsed_ms: u64,
    pub delta_ms: u64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub detail: Option<serde_json::Value>,
}

include!("inspection/job.rs");
#[cfg(feature = "operator-tools")]
include!("inspection/operator.rs");
