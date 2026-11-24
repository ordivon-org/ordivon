//! Original job observation domain wire contract and behavior.
use super::{
    default_schema_version, default_task_tail_bytes, is_false, ArtifactDescriptor, AttemptState,
    AttemptTerminationIntent, JobDesiredState, JobResolution, RuntimeDeliveryDisposition,
    MAX_TASK_TAIL_BYTES, MAX_TASK_WAIT_MS,
};

use schemars::JsonSchema;
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, Default, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum JobObserveWaitUntil {
    #[default]
    Terminal,
    ChangeOrTerminal,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct JobObserveRequest {
    #[schemars(range(min = 1, max = 1), extend("const" = 1))]
    #[serde(default = "default_schema_version")]
    pub schema_version: u32,
    pub job_id: String,
    #[serde(default)]
    #[schemars(range(max = MAX_TASK_WAIT_MS))]
    pub wait_ms: u64,
    #[serde(default)]
    pub wait_until: JobObserveWaitUntil,
    #[serde(default = "default_task_tail_bytes")]
    #[schemars(range(max = MAX_TASK_TAIL_BYTES))]
    pub stdout_tail_bytes: u64,
    #[serde(default = "default_task_tail_bytes")]
    #[schemars(range(max = MAX_TASK_TAIL_BYTES))]
    pub stderr_tail_bytes: u64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub stdout_offset: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub stderr_offset: Option<u64>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct JobCancelRequest {
    #[schemars(range(min = 1, max = 1), extend("const" = 1))]
    #[serde(default = "default_schema_version")]
    pub schema_version: u32,
    pub job_id: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct EffectiveStepTimeout {
    pub id: String,
    pub timeout_ms: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct EffectiveExecutionLimits {
    pub timeout_ms: u64,
    pub stdout_limit_bytes: u64,
    pub stderr_limit_bytes: u64,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub step_timeouts: Vec<EffectiveStepTimeout>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct JobObservation {
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
    /// Durable effective execution limits frozen into this Job at admission.
    pub effective_limits: EffectiveExecutionLimits,
    /// True when Runtime requires mechanical recovery/reconciliation for this Job.
    pub recovery_required: bool,
    /// Always false: Runtime does not judge Task/domain semantic completion.
    pub semantic_completion_evaluated: bool,
    /// A Runtime terminal result is durably available; this does not imply semantic completion.
    pub result_available: bool,
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub stdout_tail: String,
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub stderr_tail: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub stdout_offset: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub stdout_next_offset: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub stdout_available_bytes: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub stdout_eof: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub stderr_offset: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub stderr_next_offset: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub stderr_available_bytes: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub stderr_eof: Option<bool>,
    #[serde(default, skip_serializing_if = "is_false")]
    pub stdout_truncated: bool,
    #[serde(default, skip_serializing_if = "is_false")]
    pub stderr_truncated: bool,
    #[serde(default, skip_serializing_if = "is_false")]
    /// True only when at least one registered Runtime Artifact exists for this Job.
    pub artifacts_available: bool,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub artifacts: Vec<ArtifactDescriptor>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub poll_after_ms: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub elapsed_ms: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub last_output_at_ms: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub progress_revision: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub completed_steps: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub total_steps: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub current_step_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub current_step_index: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub current_step_elapsed_ms: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub failed_step_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub failed_step_index: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error_summary: Option<String>,
}

#[cfg(test)]
mod agent_job_observation_wire_tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn default_observe_and_cancel_protocol_remains_bounded_and_terminal_aware() {
        let observe: JobObserveRequest = serde_json::from_value(json!({
            "jobId": "job-original"
        }))
        .expect("the original MCP Job observation defaults are consumer stable");
        assert_eq!(observe.schema_version, 1);
        assert_eq!(observe.wait_ms, 0);
        assert_eq!(observe.wait_until, JobObserveWaitUntil::Terminal);
        assert_eq!(observe.stdout_tail_bytes, 4096);
        assert_eq!(observe.stderr_tail_bytes, 4096);
        assert_eq!(observe.stdout_offset, None);
        assert_eq!(observe.stderr_offset, None);

        let cancel: JobCancelRequest = serde_json::from_value(json!({
            "jobId": "job-original"
        }))
        .expect("the original cancellation message remains consumer stable");
        assert_eq!(cancel.schema_version, 1);
        assert_eq!(cancel.job_id, observe.job_id);
        assert!(
            serde_json::from_value::<JobCancelRequest>(json!({
                "jobId": "job-original",
                "unapprovedEffect": true
            }))
            .is_err(),
            "an unrelated extension cannot silently change cancel behavior"
        );

        let output = serde_json::to_value(&observe).unwrap();
        assert_eq!(
            output.pointer("/waitUntil").and_then(|v| v.as_str()),
            Some("terminal")
        );
        assert_eq!(
            output.pointer("/stdoutTailBytes").and_then(|v| v.as_u64()),
            Some(4096)
        );
    }
}
