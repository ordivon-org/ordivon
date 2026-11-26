//! Original runner protocol behavior and native data contract.

use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct RunnerPayloadConfig {
    pub uid: u32,
    pub gid: u32,
    pub workspace_view: String,
    pub cwd_view: String,
    pub runtime_view: String,
    pub cache_view: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct RunnerExecutionStep {
    pub id: String,
    pub executable: String,
    pub executable_digest: String,
    #[serde(default)]
    pub args: Vec<String>,
    pub cwd: String,
    #[serde(default)]
    pub env: BTreeMap<String, String>,
    pub timeout_ms: u64,
    #[serde(default)]
    pub continue_on_error: bool,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct RunnerHostDependencyCommitment {
    pub path: String,
    pub digest: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct RunnerInputCommitment {
    pub presentation_path: String,
    pub digest: String,
    pub byte_length: u64,
}

/// Only the operator-owned PG Runtime may materialize this binding.
/// It contains a credential FILE reference, never its contents.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct RunnerIssuerSpawnFence {
    pub dsn_file: String,
    pub runtime_schema: String,
    pub issuer_schema: String,
    pub source_sha256: String,
    pub principal: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct RunnerRequest {
    pub schema_version: u32,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub issuer_spawn_fence: Option<RunnerIssuerSpawnFence>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub job_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub attempt_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub launch_token: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub unit_name: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub payload: Option<RunnerPayloadConfig>,
    #[serde(default)]
    pub inherit_host_environment: bool,
    pub task_id: String,
    pub workspace_id: String,
    pub workspace_path: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub workspace_source_digest: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub workspace_read_paths: Option<Vec<String>>,

    /// Runtime-owned private backing for a stable compiler-visible target path.
    /// This is internal execution realization, not caller-authored authority.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub build_target_backing: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub input_presentation_root: Option<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub input_commitments: Vec<RunnerInputCommitment>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub host_dependencies: Vec<RunnerHostDependencyCommitment>,
    pub executable: String,
    pub executable_digest: String,
    pub args: Vec<String>,
    pub cwd: String,
    pub env: BTreeMap<String, String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub steps: Vec<RunnerExecutionStep>,
    pub timeout_ms: u64,
    pub stdout_limit_bytes: u64,
    pub stderr_limit_bytes: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct RunnerStartEvidence {
    pub schema_version: u32,
    pub job_id: String,
    pub attempt_id: String,
    pub launch_token_digest: String,
    pub unit_name: String,
    pub invocation_id: String,
    pub control_group: String,
    pub namespace_pid: u32,
    pub namespace_process_start_identity: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub payload_uid: Option<u32>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub payload_gid: Option<u32>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub observed_workspace_source_digest: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub runner_executable_digest: Option<String>,
    pub observed_unix_ms: u128,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub(crate) enum RunnerTerminalStatus {
    Completed,
    Failed,
    Cancelled,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct CapturedOutput {
    pub artifact_id: String,
    pub file_name: String,
    pub digest: String,
    pub retained_bytes: u64,
    pub dropped_bytes: u64,
    pub truncated: bool,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct RunnerStepResult {
    pub id: String,
    pub index: u32,
    pub status: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub exit_code: Option<i32>,
    pub timed_out: bool,
    pub continued: bool,
    pub started_unix_ms: u128,
    pub finished_unix_ms: u128,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct RunnerProgress {
    pub schema_version: u32,
    pub task_id: String,
    pub revision: u64,
    pub status: String,
    pub completed_steps: u32,
    pub total_steps: u32,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub current_step_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub current_step_index: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub current_step_started_unix_ms: Option<u128>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub failed_step_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub failed_step_index: Option<u32>,
    pub updated_unix_ms: u128,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct RunnerResult {
    pub schema_version: u32,
    pub task_id: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub job_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub attempt_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub launch_token_digest: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub payload_uid: Option<u32>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub payload_gid: Option<u32>,
    pub status: RunnerTerminalStatus,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub exit_code: Option<i32>,
    pub timed_out: bool,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub infrastructure_error_code: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub infrastructure_error: Option<String>,
    pub started_unix_ms: u128,
    pub finished_unix_ms: u128,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub steps: Vec<RunnerStepResult>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub failed_step_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub failed_step_index: Option<u32>,
    pub stdout: CapturedOutput,
    pub stderr: CapturedOutput,
}
