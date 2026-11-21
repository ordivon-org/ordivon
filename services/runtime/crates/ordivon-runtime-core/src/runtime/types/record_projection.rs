//! Original record projection domain wire contract and behavior.
use super::{
    AttemptState, AttemptTerminationIntent, JobDesiredState, JobResolution, ReservationState,
};

use schemars::JsonSchema;
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct RuntimeJobRecord {
    pub job_id: String,
    pub principal: String,
    pub client_request_id: String,
    pub request_digest: String,
    pub operation_digest: String,
    pub workspace_id: String,
    pub workspace_snapshot_json: String,
    pub execution_plan_json: String,
    pub execution_plan_digest: String,
    pub created_at_ms: u64,
    pub desired_state: JobDesiredState,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub resolution: Option<JobResolution>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub current_attempt_id: Option<String>,
    pub row_version: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct AttemptRecord {
    pub attempt_id: String,
    pub job_id: String,
    pub attempt_number: u32,
    pub state: AttemptState,
    pub termination_intent: AttemptTerminationIntent,
    pub launch_token_digest: String,
    pub bundle_path: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub bundle_digest: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub boot_id: Option<String>,
    pub unit_name: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub invocation_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub control_group: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub main_pid: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub process_start_identity: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub runner_start_digest: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub result_digest: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub exit_code: Option<i32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub infrastructure_error_digest: Option<String>,
    pub created_at_ms: u64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub started_at_ms: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub finished_at_ms: Option<u64>,
    pub row_version: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct ReservationRecord {
    pub reservation_id: String,
    pub attempt_id: String,
    pub global_limit: u32,
    pub state: ReservationState,
    pub acquired_at_ms: u64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub released_at_ms: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub release_reason: Option<String>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct CreatedAdmission {
    pub job: RuntimeJobRecord,
    pub attempt: AttemptRecord,
    pub reservation: ReservationRecord,
    pub launch_token: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", tag = "outcome")]
pub(crate) enum AdmissionOutcome {
    Created(Box<CreatedAdmission>),
    Existing { job: Box<RuntimeJobRecord> },
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct ArtifactRegistration {
    pub artifact_id: String,
    pub kind: String,
    pub relative_path: String,
    pub digest: String,
    pub media_type: String,
    pub byte_length: u64,
    pub truncated: bool,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct ArtifactDescriptor {
    pub artifact_id: String,
    pub attempt_id: String,
    pub kind: String,
    pub digest: String,
    pub retained_bytes: u64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub dropped_bytes: Option<u64>,
    pub truncated: bool,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct RuntimeArtifactRecord {
    pub artifact_id: String,
    pub job_id: String,
    pub attempt_id: String,
    pub kind: String,
    pub relative_path: String,
    pub digest: String,
    pub media_type: String,
    pub byte_length: u64,
    pub truncated: bool,
    pub created_at_ms: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct TerminalCommit {
    pub attempt_id: String,
    pub expected_row_version: u64,
    pub state: AttemptState,
    pub result_digest: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub exit_code: Option<i32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub infrastructure_error_digest: Option<String>,
    pub finished_at_ms: u64,
    pub artifacts: Vec<ArtifactRegistration>,
    pub reason_code: String,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "snake_case")]
/// Runtime certainty about delivery of the physical execution result.
/// This is not a Task/domain semantic-completion judgment.
pub enum RuntimeDeliveryDisposition {
    /// The Runtime Job has not reached a terminal execution resolution.
    InProgress,
    /// Runtime has committed a conclusive execution result.
    Committed,
    /// Runtime has a result/state that still requires reconciliation before mechanical convergence.
    ReconciliationRequired,
    /// Runtime cannot prove a conclusive execution result; callers must not infer effect-safe redispatch.
    Unknown,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct JobProjection {
    pub job_id: String,
    /// Stable identity of the committed Runtime Operation represented by this Job.
    pub operation_digest: String,
    /// Compatibility summary only. Use the explicit semantic fields below for control decisions.
    pub status: String,
    /// Persisted Runtime Job intent (`run` or `cancelled`).
    pub desired_state: JobDesiredState,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub attempt_id: Option<String>,
    /// Exact current or latest Runtime Attempt state; never collapsed into queued/working.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub attempt_state: Option<AttemptState>,
    /// Exact current/latest Attempt termination intent, including stop and deadline intent.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub termination_intent: Option<AttemptTerminationIntent>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub exit_code: Option<i32>,
    /// True only when Runtime has committed a terminal Job resolution.
    pub execution_terminal: bool,
    /// Terminal physical execution resolution; absent while execution is unresolved.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub execution_disposition: Option<JobResolution>,
    /// Stable machine reason for the current terminal execution resolution, when recorded.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub execution_reason_code: Option<String>,
    /// Runtime certainty/reconciliation class for the physical result.
    pub delivery_disposition: RuntimeDeliveryDisposition,
    /// True when Runtime requires mechanical recovery/reconciliation for this Job.
    pub recovery_required: bool,
    /// Always false: Runtime does not judge Task/domain semantic completion.
    pub semantic_completion_evaluated: bool,
    /// A Runtime terminal result is durably available; this does not imply semantic completion.
    pub result_available: bool,
    /// True only when at least one registered Runtime Artifact exists for this Job.
    pub artifacts_available: bool,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub artifacts: Vec<ArtifactDescriptor>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub poll_after_ms: Option<u64>,
}
