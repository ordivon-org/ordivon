use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};
use std::fs::{self, File, OpenOptions};
use std::io::{Read, Seek, SeekFrom, Write};
#[cfg(unix)]
use std::os::unix::fs::{DirBuilderExt, MetadataExt, OpenOptionsExt, PermissionsExt};
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex, MutexGuard};
use std::thread;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};
use uuid::Uuid;

use super::evidence::prepare_runner_terminal_from_bundle;
use super::patch::{
    durable_patch_request_digest, validate_durable_patch_request, validate_patch_status_request,
};
use super::physical_provider::{
    dispatch_linux, dispatch_windows_native, dispatch_windows_via_wsl, observe_linux_process_owner,
    observe_windows_process_owner, release_linux_process_owner,
};
use super::platform::*;
use super::registry::JobSnapshot;
use super::supervisor::{
    classify_supervisor_recovery, classify_windows_launcher_recovery, AttemptSupervisorOwner,
    SupervisorObservation, SupervisorRecoveryDisposition, SupervisorUnitState, TerminationIntent,
};
use super::windows::*;
use super::{
    runtime_release_effect_id, runtime_release_request_identity_digest, validate_client_request_id,
    validate_logical_id, AdmissionOutcome, ArtifactDescriptor, ArtifactReadRequest,
    ArtifactReadResult, ArtifactRegistration, AttemptRecord, AttemptState,
    AttemptTerminationIntent, DurableWorkspacePatchRequest, DurableWorkspacePatchResult,
    EffectiveInputBinding, ExecutionProviderContract, ExecutionProviderSnapshot,
    HostDependencyBinding, InputAccessMode, InputAuthority, InputBindingRequest, JobDesiredState,
    JobResolution, Registry, RegistryConfig, RunnerIdentity, RuntimeArtifactRecord,
    RuntimeCapabilities, RuntimeError, RuntimeErrorCode, RuntimeExecutionPlan,
    RuntimeExecutionStep, RuntimeExecutionTargetCapability, RuntimeJobListRequest,
    RuntimeJobListResult, RuntimeReleaseAdmission, RuntimeReleaseContract,
    RuntimeReleaseDisposition, RuntimeReleaseEffectBinding, RuntimeReleaseGetRequest,
    RuntimeReleaseProjection, RuntimeReleaseRequest, RuntimeResult, RuntimeWorkspaceGetRequest,
    RuntimeWorkspaceIssue, RuntimeWorkspaceIssueStage, RuntimeWorkspaceListRequest,
    RuntimeWorkspaceListResult, RuntimeWorkspaceSummary, SubmitRequest, TaskCancelRequest,
    TaskObservation, TaskObserveRequest, TaskObserveWaitUntil, TaskRunRequest, TerminalCommit,
    WorkspacePatchOperationState, WorkspacePatchOperationStatus, WorkspacePatchStatusRequest,
    MAX_ARTIFACT_READ_BYTES, MAX_TASK_TAIL_BYTES, MAX_TASK_WAIT_MS, RUNTIME_SCHEMA_VERSION,
};
use crate::universal::{
    canonical_directory, create_git_workspace_compact, inspect_workspace_patch_plan,
    list_open_workspace_record_inventory, load_workspace_record, mutate_workspace,
    open_directory_nofollow, open_regular_file_beneath, patch_workspace, plan_workspace_patch,
    remove_git_workspace, rename_path_durable, resolve_workspace_cwd,
    result_from_workspace_patch_plan, sha256_bytes, sha256_file,
    sync_directory as sync_universal_directory, workspace_cleanup_dependents,
    workspace_git_common_dir_at, workspace_head_and_dirty_at, workspace_head_revision,
    workspace_source_state_digest, write_bytes_atomic, write_json_atomic,
    CompactWorkspaceOpenResult, GitWorkspaceCreateRequest, RunnerExecutionStep,
    RunnerHostDependencyCommitment, RunnerInputCommitment, RunnerPayloadConfig,
    RunnerStartEvidence, RunnerTaskProgress, RunnerTaskRequest, RunnerTaskResult,
    UniversalExecutorConfig, WorkspaceCloseRequest, WorkspaceCloseResult, WorkspaceDiffRequest,
    WorkspaceMutateRequest, WorkspaceMutateResult, WorkspacePatchPlanState, WorkspacePatchRequest,
    WorkspacePatchResult, UNIVERSAL_EXEC_SCHEMA_VERSION,
};

const RUNNER_REQUEST_FILE: &str = "request.json";
const PLAN_FILE: &str = "plan.json";
const BUNDLE_MANIFEST_FILE: &str = "bundle-manifest.json";
const RUNNER_START_FILE: &str = "runner-start.json";
const WINDOWS_LAUNCHER_START_FILE: &str = "windows-launcher-start.json";
const WINDOWS_START_FILE: &str = "windows-start.json";
const RESULT_FILE: &str = "result.json";
const STDOUT_FILE: &str = "stdout.log";
const STDERR_FILE: &str = "stderr.log";
const PROGRESS_FILE: &str = "progress.json";
const CANCEL_FILE: &str = "cancel-requested.json";
const CONTROL_RESULT_FILE: &str = "control-result.json";
const ORPHAN_REMEDIATION_FILE: &str = "orphan-remediation.json";
const TERMINAL_EVIDENCE_FILE_PREFIX: &str = "terminal-evidence-";
const INTERACTIVE_RECONCILIATION_LIMIT: u32 = 32;
const ADAPTIVE_POLL_DELAYS_MS: [u64; 5] = [2, 5, 10, 20, 50];
#[cfg(unix)]
const DEFAULT_EXECUTION_PATH: &str = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin";
#[cfg(unix)]
const DEFAULT_EXECUTION_HOME: &str = "/root";
const STALE_PREPARED_INPUT_AGE_MS: u64 = 60_000;
const WINDOWS_NATIVE_OUTER_DEADLINE_GRACE_MS: u64 = 5_000;
const HOST_DEPENDENCY_CONTINUITY_SCOPE: &str = "runtime_host_namespace_path_witness";
const TRUSTED_BUILD_TARGET_PRESENTATION: &str = "/proc/self/fd/198";
const WINDOWS_INPUT_PRESENTATION_COMPONENTS: [&str; 1] = ["OrdivonImmutableInputs"];
const CONTAINED_RUNTIME_ENVIRONMENT: [&str; 15] = [
    "HOME",
    "TMPDIR",
    "XDG_CACHE_HOME",
    "CARGO_TARGET_DIR",
    "UV_CACHE_DIR",
    "PIP_CACHE_DIR",
    "npm_config_cache",
    "PNPM_HOME",
    "COREPACK_HOME",
    "BUN_INSTALL_CACHE_DIR",
    "GOMODCACHE",
    "GOCACHE",
    "GIT_OPTIONAL_LOCKS",
    "ORDIVON_PAYLOAD_UID",
    "ORDIVON_PAYLOAD_GID",
];

fn set_environment_value_case_insensitive(
    environment: &mut BTreeMap<String, String>,
    name: &str,
    value: String,
) {
    if let Some(existing) = environment
        .keys()
        .find(|existing| existing.eq_ignore_ascii_case(name))
        .cloned()
    {
        environment.remove(&existing);
    }
    environment.insert(name.to_string(), value);
}

fn required_environment_value_case_insensitive<'a>(
    environment: &'a BTreeMap<String, String>,
    name: &str,
    field: &str,
) -> RuntimeResult<&'a str> {
    environment
        .iter()
        .find(|(actual, value)| actual.eq_ignore_ascii_case(name) && !value.is_empty())
        .map(|(_, value)| value.as_str())
        .ok_or_else(|| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                format!("committed Windows environment omitted {name}"),
                Some(field),
                false,
            )
        })
}

fn windows_input_presentation_root(
    plan: &RuntimeExecutionPlan,
    input_set_id: &str,
) -> RuntimeResult<String> {
    let program_data =
        required_environment_value_case_insensitive(&plan.env, "ProgramData", "executionPlan.env")?;
    let mut root = program_data.trim_end_matches(['\\', '/']).to_string();
    for component in WINDOWS_INPUT_PRESENTATION_COMPONENTS {
        root.push('\\');
        root.push_str(component);
    }
    root.push('\\');
    root.push_str(input_set_id);
    Ok(root)
}

pub(crate) fn windows_input_bindings_digest(inputs: &[EffectiveInputBinding]) -> String {
    let mut ordered = inputs.iter().collect::<Vec<_>>();
    ordered.sort_by(|left, right| {
        left.presentation_relative_path
            .cmp(&right.presentation_relative_path)
    });
    let mut directories = BTreeSet::<String>::new();
    for input in &ordered {
        let components = input
            .presentation_relative_path
            .split('/')
            .collect::<Vec<_>>();
        for end in 1..components.len() {
            directories.insert(components[..end].join("/"));
        }
    }
    let mut bytes = b"windows-immutable-input-tree-v2\0".to_vec();
    for directory in directories {
        bytes.extend_from_slice(b"D\0");
        bytes.extend_from_slice(directory.as_bytes());
        bytes.push(0);
    }
    for input in ordered {
        bytes.extend_from_slice(b"F\0");
        bytes.extend_from_slice(input.presentation_relative_path.as_bytes());
        bytes.push(0);
        bytes.extend_from_slice(input.digest.as_bytes());
        bytes.push(0);
        bytes.extend_from_slice(input.byte_length.to_string().as_bytes());
        bytes.push(0);
    }
    sha256_bytes(&bytes)
}

pub(crate) fn transient_main_pid_observation_loss(error: &RuntimeError) -> bool {
    error.code == RuntimeErrorCode::LaunchIdentityMismatch
        && error.field.as_deref() == Some("mainPid")
        && (error.message == "systemd MainPID has no observable host process identity"
            || error.message
                == "Windows launcher systemd MainPID has no observable host process identity"
            || error.message == "systemd omitted MainPID")
}

fn adaptive_poll_delay(poll_index: usize) -> Duration {
    Duration::from_millis(
        ADAPTIVE_POLL_DELAYS_MS[poll_index.min(ADAPTIVE_POLL_DELAYS_MS.len() - 1)],
    )
}

fn sleep_until_poll(deadline: Instant, poll_index: &mut usize) {
    let remaining = deadline.saturating_duration_since(Instant::now());
    if remaining.is_zero() {
        return;
    }
    thread::sleep(adaptive_poll_delay(*poll_index).min(remaining));
    *poll_index = poll_index.saturating_add(1);
}

#[derive(Clone, Debug)]
pub struct RuntimeConfig {
    pub node_id: String,
    pub registry: RegistryConfig,
    pub executor: UniversalExecutorConfig,
    pub startup_grace_ms: u64,
    pub windows: Option<WindowsExecutionConfig>,
}

#[derive(Clone, Debug)]
struct OpenedInputAuthority {
    root: Arc<File>,
}

#[derive(Debug)]
struct PreparedInputSet {
    input_set_id: String,
    prepared_root: PathBuf,
    effective_inputs: Vec<EffectiveInputBinding>,
}

#[derive(Clone, Debug)]
pub struct Runtime {
    node_identity: super::RuntimeNodeIdentity,
    registry: Registry,
    executor: UniversalExecutorConfig,
    default_runtime_ms: u64,
    startup_grace_ms: u64,
    execution_path: String,
    execution_home: String,
    windows: Option<WindowsExecutionConfig>,
    input_authorities: BTreeMap<String, OpenedInputAuthority>,
    lifecycle_lock: Arc<Mutex<()>>,
    control_terminal_lock: Arc<Mutex<()>>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ReconciliationFailure {
    pub attempt_id: String,
    pub job_id: String,
    pub code: RuntimeErrorCode,
    pub message: String,
}

#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub struct ReconciliationReport {
    pub inspected: usize,
    pub reconciled: usize,
    pub recovered_orphans: usize,
    pub quarantined: usize,
    pub unchanged: usize,
    pub failed: usize,
    pub failures: Vec<ReconciliationFailure>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct BundleManifest {
    schema_version: u32,
    job_id: String,
    attempt_id: String,
    request_digest: String,
    plan_digest: String,
    launch_token_digest: String,
    created_at_ms: u64,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct ControlTerminalEvidence {
    schema_version: u32,
    job_id: String,
    attempt_id: String,
    status: String,
    reason_code: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    detail: Option<String>,
    observed_at_ms: u64,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct TerminalSupervisorEvidence {
    #[serde(skip_serializing_if = "Option::is_none")]
    boot_id: Option<String>,
    unit_name: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    invocation_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    control_group: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    main_pid: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    process_start_identity: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    runner_start_digest: Option<String>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct ObservedSupervisorEvidence {
    boot_id: String,
    unit_state: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    invocation_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    control_group: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    main_pid: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    main_process_start_identity: Option<String>,
    recorded_pid_alive: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    recorded_pid_start_identity: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    result: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    exec_main_code: Option<i32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    exec_main_status: Option<i32>,
}

impl From<&SupervisorObservation> for ObservedSupervisorEvidence {
    fn from(observation: &SupervisorObservation) -> Self {
        Self {
            boot_id: observation.boot_id.clone(),
            unit_state: match observation.unit_state {
                SupervisorUnitState::Running => "running",
                SupervisorUnitState::Terminal => "terminal",
                SupervisorUnitState::NotFound => "not_found",
            }
            .to_string(),
            invocation_id: observation.invocation_id.clone(),
            control_group: observation.control_group.clone(),
            main_pid: observation.main_pid,
            main_process_start_identity: observation.main_process_start_identity.clone(),
            recorded_pid_alive: observation.recorded_pid_alive,
            recorded_pid_start_identity: observation.recorded_pid_start_identity.clone(),
            result: observation.result.clone(),
            exec_main_code: observation.exec_main_code,
            exec_main_status: observation.exec_main_status,
        }
    }
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct TerminalProcessEvidence {
    schema_version: u32,
    job_id: String,
    attempt_id: String,
    operation_digest: String,
    execution_plan_digest: String,
    workspace_id: String,
    source_revision: String,
    execution_profile: super::ExecutionProfile,
    #[serde(default, skip_serializing_if = "super::ExecutionTarget::is_default")]
    execution_target: super::ExecutionTarget,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    execution_provider: Option<ExecutionProviderSnapshot>,
    #[serde(default)]
    windows_authority: super::WindowsAuthority,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    windows_execution_context: Option<super::WindowsExecutionContext>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    foreign_references: Vec<super::ForeignReference>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    host_dependencies: Vec<HostDependencyBinding>,
    #[serde(skip_serializing_if = "Option::is_none")]
    host_dependency_continuity: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    host_dependency_continuity_scope: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    input_set_id: Option<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    effective_inputs: Vec<EffectiveInputBinding>,
    executable: String,
    executable_digest: String,
    args: Vec<String>,
    cwd: String,
    supervisor: TerminalSupervisorEvidence,
    #[serde(skip_serializing_if = "Option::is_none")]
    observed_supervisor: Option<ObservedSupervisorEvidence>,
    start_disposition: String,
    cancellation_disposition: String,
    execution_disposition: String,
    delivery_disposition: String,
    process_tree_disposition: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    process_tree_detail: Option<String>,
    reason_code: String,
    terminal_artifact_ids: Vec<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    supersedes_artifact_id: Option<String>,
    observed_at_ms: u64,
}

#[derive(Clone, Copy)]
struct ObservationOutputRequest {
    stdout_tail_bytes: u64,
    stderr_tail_bytes: u64,
    stdout_offset: Option<u64>,
    stderr_offset: Option<u64>,
}

include!("engine/construction.rs");
include!("engine/admission.rs");
include!("engine/release.rs");
include!("engine/workspace.rs");
include!("engine/execution.rs");
include!("engine/reconciliation.rs");
include!("engine/control_query.rs");
#[derive(Debug)]
struct OutputView {
    content: String,
    offset: Option<u64>,
    next_offset: Option<u64>,
    available_bytes: Option<u64>,
    eof: Option<bool>,
}

impl OutputView {
    fn empty(offset: Option<u64>, terminal: bool) -> Self {
        Self {
            content: String::new(),
            offset,
            next_offset: offset,
            available_bytes: offset.map(|_| 0),
            eof: offset.map(|value| terminal && value == 0),
        }
    }
}

#[derive(Debug)]
struct TextRange {
    content: String,
    next_offset: u64,
}

#[derive(Clone, Copy)]
struct RangeFields<'a> {
    offset: &'a str,
    max_bytes: &'a str,
}

fn read_utf8_range(
    path: &Path,
    offset: u64,
    max_bytes: u64,
    available: u64,
    terminal: bool,
    fields: RangeFields<'_>,
    context: &str,
) -> RuntimeResult<TextRange> {
    if offset > available {
        return Err(RuntimeError::invalid(
            format!("{} exceeds retained byte length {available}", fields.offset),
            fields.offset,
        ));
    }
    if max_bytes == 0 || offset == available {
        return Ok(TextRange {
            content: String::new(),
            next_offset: offset,
        });
    }
    let read_limit = max_bytes.min(available.saturating_sub(offset));
    let mut file =
        File::open(path).map_err(|error| io_error(&format!("open {context} range"), error))?;
    file.seek(SeekFrom::Start(offset))
        .map_err(|error| io_error(&format!("seek {context} range"), error))?;
    let mut bytes = vec![0_u8; usize::try_from(read_limit).unwrap_or(usize::MAX)];
    let read = file
        .read(&mut bytes)
        .map_err(|error| io_error(&format!("read {context} range"), error))?;
    bytes.truncate(read);
    if offset > 0 && bytes.first().is_some_and(|byte| byte & 0xc0 == 0x80) {
        return Err(RuntimeError::invalid(
            format!("{} must point to a UTF-8 character boundary", fields.offset),
            fields.offset,
        ));
    }
    let safe_len = match std::str::from_utf8(&bytes) {
        Ok(_) => bytes.len(),
        Err(error) if error.error_len().is_none() => error.valid_up_to(),
        Err(_) => bytes.len(),
    };
    if safe_len == 0 && !bytes.is_empty() {
        if !terminal && offset.saturating_add(bytes.len() as u64) >= available {
            return Ok(TextRange {
                content: String::new(),
                next_offset: offset,
            });
        }
        return Err(RuntimeError::invalid(
            format!(
                "{} is too small for the next UTF-8 character; use at least 4 bytes",
                fields.max_bytes
            ),
            fields.max_bytes,
        ));
    }
    bytes.truncate(safe_len);
    Ok(TextRange {
        content: String::from_utf8_lossy(&bytes).into_owned(),
        next_offset: offset.saturating_add(safe_len as u64),
    })
}

fn read_output_text(
    path: &Path,
    offset: Option<u64>,
    max_bytes: u64,
    terminal: bool,
    offset_field: &str,
    max_bytes_field: &str,
) -> RuntimeResult<OutputView> {
    let Some(offset) = offset else {
        return Ok(OutputView {
            content: read_tail_text(path, max_bytes)?,
            offset: None,
            next_offset: None,
            available_bytes: None,
            eof: None,
        });
    };
    let available = if path.exists() {
        fs::metadata(path)
            .map_err(|error| io_error("inspect output range", error))?
            .len()
    } else {
        0
    };
    if offset > available {
        return Err(RuntimeError::invalid(
            format!("{offset_field} exceeds retained output length {available}"),
            offset_field,
        ));
    }
    if max_bytes == 0 || !path.exists() {
        return Ok(OutputView {
            content: String::new(),
            offset: Some(offset),
            next_offset: Some(offset),
            available_bytes: Some(available),
            eof: Some(terminal && offset >= available),
        });
    }
    let range = read_utf8_range(
        path,
        offset,
        max_bytes,
        available,
        terminal,
        RangeFields {
            offset: offset_field,
            max_bytes: max_bytes_field,
        },
        "output",
    )?;
    Ok(OutputView {
        content: range.content,
        offset: Some(offset),
        next_offset: Some(range.next_offset),
        available_bytes: Some(available),
        eof: Some(terminal && range.next_offset >= available),
    })
}

fn read_tail_text(path: &Path, max_bytes: u64) -> RuntimeResult<String> {
    if max_bytes == 0 || !path.exists() {
        return Ok(String::new());
    }
    let mut file = File::open(path).map_err(|error| io_error("open output tail", error))?;
    let length = file
        .metadata()
        .map_err(|error| io_error("inspect output tail", error))?
        .len();
    let offset = length.saturating_sub(max_bytes);
    file.seek(SeekFrom::Start(offset))
        .map_err(|error| io_error("seek output tail", error))?;
    let mut bytes = Vec::with_capacity(usize::try_from(max_bytes.min(length)).unwrap_or(0));
    file.take(max_bytes)
        .read_to_end(&mut bytes)
        .map_err(|error| io_error("read output tail", error))?;
    Ok(String::from_utf8_lossy(&bytes).into_owned())
}

fn native_windows_outer_deadline_due(
    execution_started_at_ms: u64,
    timeout_ms: u64,
    observed_at_ms: u64,
) -> bool {
    observed_at_ms
        >= execution_started_at_ms
            .saturating_add(timeout_ms)
            .saturating_add(WINDOWS_NATIVE_OUTER_DEADLINE_GRACE_MS)
}

fn windows_native_launcher_lineage_is_definite_failure(
    execution_target: super::ExecutionTarget,
    termination_intent: super::AttemptTerminationIntent,
    unit_state: SupervisorUnitState,
    recorded_pid_alive: bool,
) -> bool {
    execution_target == super::ExecutionTarget::WindowsNative
        && termination_intent == super::AttemptTerminationIntent::Natural
        && unit_state == SupervisorUnitState::NotFound
        && !recorded_pid_alive
}

fn wsl_backed_windows_live_unit_must_wait(
    execution_target: super::ExecutionTarget,
    wsl_distribution_configured: bool,
    unit_active: bool,
) -> bool {
    execution_target == super::ExecutionTarget::WindowsNative
        && wsl_distribution_configured
        && unit_active
}

#[cfg(test)]
mod windows_lineage_tests {
    use super::*;

    #[test]
    fn native_windows_outer_deadline_uses_durable_start_time_and_outer_grace() {
        assert!(!native_windows_outer_deadline_due(200, 1_000, 6_199));
        assert!(native_windows_outer_deadline_due(200, 1_000, 6_200));
        assert!(!native_windows_outer_deadline_due(
            100,
            u64::MAX,
            u64::MAX - 1
        ));
    }

    #[test]
    fn wsl_backed_windows_live_unit_remains_starting_without_target_evidence() {
        assert!(wsl_backed_windows_live_unit_must_wait(
            crate::runtime::ExecutionTarget::WindowsNative,
            true,
            true,
        ));
        assert!(!wsl_backed_windows_live_unit_must_wait(
            crate::runtime::ExecutionTarget::WindowsNative,
            true,
            false,
        ));
        assert!(!wsl_backed_windows_live_unit_must_wait(
            crate::runtime::ExecutionTarget::WindowsNative,
            false,
            true,
        ));
        assert!(!wsl_backed_windows_live_unit_must_wait(
            crate::runtime::ExecutionTarget::LocalLinux,
            true,
            true,
        ));
    }

    #[test]
    fn missing_windows_launcher_lineage_is_failed_only_for_natural_windows_execution() {
        assert!(windows_native_launcher_lineage_is_definite_failure(
            crate::runtime::ExecutionTarget::WindowsNative,
            crate::runtime::AttemptTerminationIntent::Natural,
            SupervisorUnitState::NotFound,
            false,
        ));
        assert!(!windows_native_launcher_lineage_is_definite_failure(
            crate::runtime::ExecutionTarget::LocalLinux,
            crate::runtime::AttemptTerminationIntent::Natural,
            SupervisorUnitState::NotFound,
            false,
        ));
        assert!(!windows_native_launcher_lineage_is_definite_failure(
            crate::runtime::ExecutionTarget::WindowsNative,
            crate::runtime::AttemptTerminationIntent::StopRequested,
            SupervisorUnitState::NotFound,
            false,
        ));
        assert!(!windows_native_launcher_lineage_is_definite_failure(
            crate::runtime::ExecutionTarget::WindowsNative,
            crate::runtime::AttemptTerminationIntent::DeadlineExceeded,
            SupervisorUnitState::NotFound,
            false,
        ));
        assert!(!windows_native_launcher_lineage_is_definite_failure(
            crate::runtime::ExecutionTarget::WindowsNative,
            crate::runtime::AttemptTerminationIntent::Natural,
            SupervisorUnitState::Running,
            false,
        ));
        assert!(!windows_native_launcher_lineage_is_definite_failure(
            crate::runtime::ExecutionTarget::WindowsNative,
            crate::runtime::AttemptTerminationIntent::Natural,
            SupervisorUnitState::NotFound,
            true,
        ));
    }
}

#[cfg(test)]
mod output_tail_tests {
    use super::*;

    #[test]
    fn tail_lossy_decode_preserves_valid_text_around_invalid_bytes() {
        let root = std::env::temp_dir().join(format!(
            "ordivon-tail-test-{}-{}",
            std::process::id(),
            now_ms().unwrap()
        ));
        fs::create_dir_all(&root).unwrap();
        let path = root.join("output.log");
        fs::write(&path, b"0123456789alpha\xffomega").unwrap();
        let observed = read_tail_text(&path, 11).unwrap();
        assert!(
            observed.contains("alpha"),
            "valid prefix was discarded: {observed:?}"
        );
        assert!(
            observed.contains("omega"),
            "valid suffix was discarded: {observed:?}"
        );
        fs::remove_dir_all(root).unwrap();
    }
}

fn configure_private_create(options: &mut OpenOptions, mode: u32) {
    #[cfg(unix)]
    {
        options.mode(mode);
    }
    #[cfg(not(unix))]
    {
        let _ = (options, mode);
    }
}

#[cfg(unix)]
fn protect_posix_path(path: &Path, mode: u32, operation: &str) -> RuntimeResult<()> {
    fs::set_permissions(path, fs::Permissions::from_mode(mode))
        .map_err(|error| io_error(operation, error))
}

#[cfg(windows)]
fn protect_posix_path(path: &Path, mode: u32, operation: &str) -> RuntimeResult<()> {
    if mode == 0o700 && path.is_dir() {
        return crate::windows_security::protect_private_directory(path).map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::IoError,
                format!("{operation}: cannot apply native Windows private-directory ACL: {error}"),
                None,
                false,
            )
        });
    }
    Err(RuntimeError::new(
        RuntimeErrorCode::ToolUnavailable,
        format!(
            "{operation}: no native Windows ACL realization is defined for Unix mode {mode:#o}"
        ),
        None,
        false,
    ))
}

#[cfg(not(any(unix, windows)))]
fn protect_posix_path(_path: &Path, mode: u32, operation: &str) -> RuntimeResult<()> {
    Err(RuntimeError::new(
        RuntimeErrorCode::ToolUnavailable,
        format!("{operation}: platform permission realization is unavailable for mode {mode:#o}"),
        None,
        false,
    ))
}

#[cfg(unix)]
fn open_regular_file_nofollow(path: &Path) -> std::io::Result<File> {
    OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_NOFOLLOW)
        .open(path)
}

#[cfg(not(unix))]
fn open_regular_file_nofollow(_path: &Path) -> std::io::Result<File> {
    Err(std::io::Error::new(
        std::io::ErrorKind::Unsupported,
        "secure no-follow regular-file open is not implemented for this platform",
    ))
}

fn write_bytes_synced(path: &Path, bytes: &[u8]) -> RuntimeResult<()> {
    let mut file = OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(path)
        .map_err(|error| io_error("create bundle file", error))?;
    file.write_all(bytes)
        .map_err(|error| io_error("write bundle file", error))?;
    file.sync_all()
        .map_err(|error| io_error("sync bundle file", error))
}

fn sync_directory(path: &Path) -> RuntimeResult<()> {
    sync_universal_directory(path).map_err(map_universal_error)
}

fn durable_runtime_rename(
    source: &Path,
    destination: &Path,
    replace_existing: bool,
    operation: &str,
) -> RuntimeResult<()> {
    rename_path_durable(source, destination, replace_existing, operation)
        .map_err(map_universal_error)
}

fn now_ms() -> RuntimeResult<u64> {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryUnavailable,
                format!("system clock precedes Unix epoch: {error}"),
                None,
                false,
            )
        })?
        .as_millis()
        .try_into()
        .map_err(|_| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryUnavailable,
                "current time does not fit u64 milliseconds",
                None,
                false,
            )
        })
}

fn validate_text_id(value: &str, field: &str) -> RuntimeResult<()> {
    if value.trim().is_empty()
        || value.len() > 256
        || value.as_bytes().contains(&0)
        || value.chars().any(char::is_control)
    {
        return Err(RuntimeError::invalid(
            format!("{field} must be non-empty, bounded, and control-free"),
            field,
        ));
    }
    Ok(())
}

fn serialization_error(error: serde_json::Error) -> RuntimeError {
    RuntimeError::new(
        RuntimeErrorCode::RegistryUnavailable,
        format!("cannot serialize runtime bundle: {error}"),
        None,
        false,
    )
}

fn workspace_issue(
    workspace_id: &str,
    stage: RuntimeWorkspaceIssueStage,
    error: RuntimeError,
) -> RuntimeWorkspaceIssue {
    RuntimeWorkspaceIssue {
        workspace_id: workspace_id.to_string(),
        stage,
        code: error.code.as_str().to_string(),
        message: error.message,
        retryable: error.retryable,
    }
}

pub(crate) fn map_universal_error(error: crate::UniversalExecError) -> RuntimeError {
    use crate::UniversalExecErrorCode as UniversalCode;

    let code = match error.code {
        UniversalCode::InvalidRequest => RuntimeErrorCode::InvalidRequest,
        UniversalCode::WorkspaceExists => RuntimeErrorCode::WorkspaceExists,
        UniversalCode::WorkspaceNotFound => RuntimeErrorCode::WorkspaceNotFound,
        UniversalCode::WorkspacePathNotFound => RuntimeErrorCode::WorkspacePathNotFound,
        UniversalCode::WorkspaceDirty => RuntimeErrorCode::WorkspaceDirty,
        UniversalCode::WorkspacePathDenied => RuntimeErrorCode::WorkspacePathDenied,
        UniversalCode::RevisionNotFound => RuntimeErrorCode::RevisionNotFound,
        UniversalCode::RevisionMismatch => RuntimeErrorCode::RevisionMismatch,
        UniversalCode::WorkspaceStateMismatch
        | UniversalCode::InputStateMismatch
        | UniversalCode::HostDependencyRuntimeDrift
        | UniversalCode::ExecutableRuntimeDrift => RuntimeErrorCode::WorkspaceStateMismatch,
        UniversalCode::WorkspaceMutationIncomplete => RuntimeErrorCode::ReconciliationRequired,
        UniversalCode::TaskExists => RuntimeErrorCode::IdempotencyConflict,
        UniversalCode::TaskNotFound => RuntimeErrorCode::JobNotFound,
        UniversalCode::TaskStartFailed => RuntimeErrorCode::ToolFailed,
        UniversalCode::TaskStateUnavailable => RuntimeErrorCode::ReconciliationRequired,
        UniversalCode::ArtifactNotFound => RuntimeErrorCode::ArtifactNotFound,
        UniversalCode::ArtifactNotUtf8 => RuntimeErrorCode::ArtifactNotUtf8,
        UniversalCode::OutputLimitExceeded => RuntimeErrorCode::OutputLimitExceeded,
        UniversalCode::ToolUnavailable => RuntimeErrorCode::ToolUnavailable,
        UniversalCode::ToolFailed => RuntimeErrorCode::ToolFailed,
        UniversalCode::IoError => RuntimeErrorCode::IoError,
        UniversalCode::WorkspaceCapacityExceeded => RuntimeErrorCode::WorkspaceCapacityExceeded,
        UniversalCode::MetadataCorrupt => RuntimeErrorCode::MetadataCorrupt,
    };
    RuntimeError::new(code, error.message, error.field.as_deref(), error.retryable)
}

fn io_error(context: &str, error: std::io::Error) -> RuntimeError {
    RuntimeError::new(
        RuntimeErrorCode::IoError,
        format!("{context}: {error}"),
        None,
        false,
    )
}

#[cfg(test)]
mod trusted_systemd_command_tests {
    use super::*;
    use crate::{
        ExecutionBudget, ExecutionProfile, ExecutionProposal, ExecutionStepProposal,
        TaskRunProposal, UniversalExecutionRequest,
    };
    use proptest::prelude::*;

    proptest! {
        #[test]
        fn incremental_output_ranges_reconstruct_retained_bytes(
            chunks in prop::collection::vec(
                prop::collection::vec(any::<char>(), 0..16)
                    .prop_map(|chars| chars.into_iter().collect::<String>()),
                1..30,
            ),
            chunk_size in 4u64..64,
        ) {
            let root = std::env::temp_dir().join(format!(
                "ordivon-output-range-property-{}-{}",
                std::process::id(),
                SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos()
            ));
            fs::create_dir_all(&root).unwrap();
            let path = root.join("stdout.log");
            let expected = chunks.concat();
            fs::write(&path, expected.as_bytes()).unwrap();
            let mut offset = 0u64;
            let mut reconstructed = String::new();
            loop {
                let view = read_output_text(
                    &path,
                    Some(offset),
                    chunk_size,
                    true,
                    "stdoutOffset",
                    "stdoutTailBytes",
                ).unwrap();
                reconstructed.push_str(&view.content);
                offset = view.next_offset.unwrap();
                if view.eof == Some(true) {
                    break;
                }
            }
            prop_assert_eq!(reconstructed, expected);
            prop_assert_eq!(offset, fs::metadata(&path).unwrap().len());
            fs::remove_dir_all(root).unwrap();
        }
    }

    #[test]
    fn concurrent_materialization_keeps_physical_prepared_state_job_scoped() {
        let root = std::env::temp_dir().join(format!(
            "ordivon-input-publish-race-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        let authority_root = root.join("authority");
        fs::create_dir_all(&authority_root).unwrap();
        let bytes = vec![b'F'; 2 * 1024 * 1024];
        fs::write(authority_root.join("fragment.bin"), &bytes).unwrap();
        let expected_digest = sha256_bytes(&bytes);
        let request = TaskRunRequest {
            schema_version: RUNTIME_SCHEMA_VERSION,
            client_request_id: "request:input-publish-race".to_string(),
            principal: "principal:test".to_string(),
            global_limit: 4,
            execution: UniversalExecutionRequest {
                workspace_id: "workspace-input-publish-race".to_string(),
                executable: "/usr/bin/true".to_string(),
                args: Vec::new(),
                cwd_relative: ".".to_string(),
                env: BTreeMap::new(),
                timeout_ms: 5_000,
                stdout_limit_bytes: 4_096,
                stderr_limit_bytes: 4_096,
                steps: Vec::new(),
                budget: ExecutionBudget::default(),
                execution_profile: ExecutionProfile::ContainedLocal,
                execution_target: crate::runtime::ExecutionTarget::LocalLinux,
                windows_authority: crate::runtime::WindowsAuthority::Limited,
                foreign_references: Vec::new(),
                host_dependencies: Vec::new(),
            },
            wait_ms: 0,
            stdout_tail_bytes: 0,
            stderr_tail_bytes: 0,
        };
        let inputs = canonical_input_binding_requests(&[InputBindingRequest {
            authority: "finance".to_string(),
            relative_object: "fragment.bin".to_string(),
            expected_digest: expected_digest.clone(),
            presentation_relative_path: "data/fragment.bin".to_string(),
        }])
        .unwrap();
        let identity =
            super::super::input_bound_request_identity_digest(&request, &inputs).unwrap();
        let barrier = Arc::new(std::sync::Barrier::new(2));
        let mut handles = Vec::new();
        for index in 0..2 {
            let root = root.clone();
            let authority_root = authority_root.clone();
            let request = request.clone();
            let inputs = inputs.clone();
            let identity = identity.clone();
            let barrier = barrier.clone();
            handles.push(std::thread::spawn(move || {
                let runtime = Runtime::new_with_input_authorities(
                    RuntimeConfig {
                        node_id: "test-node".to_string(),
                        registry: RegistryConfig {
                            db_path: root.join(format!("registry-{index}/registry.sqlite3")),
                            store_root: root.join(format!("registry-{index}")),
                            busy_timeout_ms: 5_000,
                        },
                        executor: UniversalExecutorConfig {
                            store_root: root.join("runtime"),
                            workspace_root: None,
                            workspace_uid: None,
                            workspace_gid: None,
                            runner_path: Some(PathBuf::from("/usr/bin/true")),
                            allowed_executable_roots: vec![PathBuf::from("/usr/bin")],
                            max_runtime_ms: 60_000,
                            max_output_bytes: 1_048_576,
                        },
                        startup_grace_ms: 2_000,
                        windows: None,
                    },
                    vec![InputAuthority {
                        name: "finance".to_string(),
                        root: authority_root,
                    }],
                )
                .unwrap();
                barrier.wait();
                let job_id = format!("job-{}", Uuid::now_v7());
                runtime
                    .materialize_input_bindings(&request, &identity, &job_id, &inputs)
                    .unwrap()
            }));
        }
        let left = handles.remove(0).join().unwrap();
        let right = handles.remove(0).join().unwrap();
        assert_eq!(left.input_set_id, right.input_set_id);
        assert_eq!(left.effective_inputs, right.effective_inputs);
        assert_ne!(left.prepared_root, right.prepared_root);
        assert!(left.prepared_root.is_dir());
        assert!(right.prepared_root.is_dir());
        assert_eq!(left.effective_inputs[0].digest, expected_digest);
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn materialized_input_verification_fails_closed_after_tamper() {
        let root = std::env::temp_dir().join(format!(
            "ordivon-input-tamper-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        fs::create_dir_all(root.join("data")).unwrap();
        fs::write(root.join("data/input.bin"), b"S0").unwrap();
        let request = InputBindingRequest {
            authority: "finance".to_string(),
            relative_object: "fragment.bin".to_string(),
            expected_digest: sha256_bytes(b"S0"),
            presentation_relative_path: "data/input.bin".to_string(),
        };
        let first = verify_effective_input_set(&root, std::slice::from_ref(&request)).unwrap();
        assert_eq!(first[0].byte_length, 2);
        assert_eq!(first[0].digest, sha256_bytes(b"S0"));

        fs::write(root.join("data/input.bin"), b"S1").unwrap();
        let error = verify_effective_input_set(&root, std::slice::from_ref(&request)).unwrap_err();
        assert_eq!(error.code, RuntimeErrorCode::WorkspaceStateMismatch);
        assert!(error.message.contains("digest mismatch"));

        fs::write(root.join("data/input.bin"), b"S0").unwrap();
        fs::write(root.join("unexpected.bin"), b"extra").unwrap();
        let error = verify_effective_input_set(&root, &[request]).unwrap_err();
        assert_eq!(error.code, RuntimeErrorCode::WorkspaceStateMismatch);
        assert!(error.message.contains("file inventory differs"));
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn contained_input_set_is_read_only_bound_at_fixed_runtime_path() {
        let root = std::env::temp_dir().join(format!(
            "ordivon-contained-input-command-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        let workspace = root.join("workspace");
        let bundle = root.join("bundle");
        let inputs = root.join("inputs");
        let cache = root.join("cache");
        for path in [&workspace, &bundle, &inputs, &cache] {
            fs::create_dir_all(path).unwrap();
        }
        let environment = BTreeMap::from([
            (
                "HOME".to_string(),
                cache.join("home").to_string_lossy().into_owned(),
            ),
            (
                "TMPDIR".to_string(),
                cache.join("tmp").to_string_lossy().into_owned(),
            ),
        ]);
        for value in environment.values() {
            fs::create_dir_all(value).unwrap();
        }
        let budget = ExecutionBudget::default();
        let contained = build_systemd_run_command(&SystemdRunSpec {
            unit_name: "ordivon-input-contained.service",
            runner: Path::new("/usr/bin/true"),
            bundle_path: &bundle,
            workspace_path: &workspace,
            workspace_git_common_dir: None,
            input_set_path: Some(&inputs),
            runtime_ceiling_ms: 10_000,
            budget: &budget,
            execution_profile: ExecutionProfile::ContainedLocal,
            environment: &environment,
        })
        .unwrap();
        let contained_args = contained
            .get_args()
            .map(|value| value.to_string_lossy().into_owned())
            .collect::<Vec<_>>()
            .join(" ");
        assert!(contained_args.contains(&format!(
            "BindReadOnlyPaths={}:{CONTAINED_INPUT_ROOT}",
            inputs.display()
        )));

        let trusted = build_systemd_run_command(&SystemdRunSpec {
            unit_name: "ordivon-input-trusted.service",
            runner: Path::new("/usr/bin/true"),
            bundle_path: &bundle,
            workspace_path: &workspace,
            workspace_git_common_dir: None,
            input_set_path: Some(&inputs),
            runtime_ceiling_ms: 10_000,
            budget: &budget,
            execution_profile: ExecutionProfile::TrustedLocal,
            environment: &BTreeMap::new(),
        })
        .unwrap();
        let trusted_args = trusted
            .get_args()
            .map(|value| value.to_string_lossy().into_owned())
            .collect::<Vec<_>>()
            .join(" ");
        assert!(trusted_args.contains(&format!(
            "BindReadOnlyPaths={}:{CONTAINED_INPUT_ROOT}",
            inputs.display()
        )));
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn observed_supervisor_evidence_preserves_reconciliation_facts() {
        let missing = SupervisorObservation {
            boot_id: "boot-a".to_string(),
            unit_state: SupervisorUnitState::NotFound,
            invocation_id: None,
            control_group: None,
            main_pid: None,
            main_process_start_identity: None,
            recorded_pid_alive: false,
            recorded_pid_start_identity: None,
            result: Some("success".to_string()),
            exec_main_code: Some(0),
            exec_main_status: Some(0),
        };
        let mut rebooted = missing.clone();
        rebooted.boot_id = "boot-b".to_string();

        let missing = serde_json::to_value(ObservedSupervisorEvidence::from(&missing)).unwrap();
        let rebooted = serde_json::to_value(ObservedSupervisorEvidence::from(&rebooted)).unwrap();
        assert_eq!(missing["unitState"], "not_found");
        assert_eq!(missing["recordedPidAlive"], false);
        assert_eq!(missing["result"], "success");
        assert_eq!(missing["execMainCode"], 0);
        assert_eq!(missing["execMainStatus"], 0);
        assert_eq!(missing["bootId"], "boot-a");
        assert_eq!(rebooted["bootId"], "boot-b");
        assert_ne!(missing, rebooted);
    }

    fn proposal_runtime(label: &str, max_runtime_ms: u64, max_output_bytes: u64) -> Runtime {
        proposal_runtime_with_default(label, max_runtime_ms, max_runtime_ms, max_output_bytes)
    }

    fn proposal_runtime_with_default(
        label: &str,
        default_runtime_ms: u64,
        max_runtime_ms: u64,
        max_output_bytes: u64,
    ) -> Runtime {
        let root = std::env::temp_dir().join(format!(
            "ordivon-proposal-resolution-{label}-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        let store = root.join("store");
        let registry = super::RegistryConfig {
            db_path: store.join("registry.sqlite3"),
            store_root: store.clone(),
            busy_timeout_ms: 5_000,
        };
        Runtime::new_with_input_authorities_and_default_runtime(
            super::RuntimeConfig {
                node_id: "test-node".to_string(),
                registry,
                executor: UniversalExecutorConfig {
                    store_root: root.join("runtime"),
                    workspace_root: None,
                    workspace_uid: None,
                    workspace_gid: None,
                    runner_path: Some(PathBuf::from("/usr/bin/true")),
                    allowed_executable_roots: vec![PathBuf::from("/")],
                    max_runtime_ms,
                    max_output_bytes,
                },
                startup_grace_ms: 2_000,
                windows: None,
            },
            Vec::new(),
            default_runtime_ms,
        )
        .unwrap()
    }

    fn proposal(step_timeouts: &[Option<u64>]) -> TaskRunProposal {
        TaskRunProposal {
            schema_version: RUNTIME_SCHEMA_VERSION,
            client_request_id: "request:proposal-resolution".to_string(),
            principal: "principal:test".to_string(),
            global_limit: 4,
            execution: ExecutionProposal {
                workspace_id: "workspace:test".to_string(),
                executable: "/usr/bin/true".to_string(),
                args: Vec::new(),
                cwd_relative: ".".to_string(),
                env: BTreeMap::new(),
                timeout_ms: None,
                stdout_limit_bytes: None,
                stderr_limit_bytes: None,
                steps: step_timeouts
                    .iter()
                    .enumerate()
                    .map(|(index, timeout_ms)| ExecutionStepProposal {
                        id: format!("step-{index}"),
                        executable: "/usr/bin/true".to_string(),
                        args: Vec::new(),
                        cwd_relative: ".".to_string(),
                        env: BTreeMap::new(),
                        timeout_ms: *timeout_ms,
                        continue_on_error: false,
                    })
                    .collect(),
                budget: ExecutionBudget::default(),
                execution_profile: ExecutionProfile::TrustedLocal,
                execution_target: crate::runtime::ExecutionTarget::LocalLinux,
                windows_authority: crate::runtime::WindowsAuthority::Limited,
                foreign_references: Vec::new(),
                host_dependencies: Vec::new(),
            },
            wait_ms: 0,
            stdout_tail_bytes: 0,
            stderr_tail_bytes: 0,
        }
    }

    #[test]
    fn proposal_resolution_only_fills_omitted_limits_and_preserves_explicit_constraints() {
        let runtime = proposal_runtime_with_default("limits", 4_000, 10_000, 1_048_576);
        let omitted = proposal(&[]);
        let resolved = runtime.resolve_proposal(&omitted);
        assert_eq!(resolved.execution.timeout_ms, 4_000);
        assert_eq!(resolved.execution.stdout_limit_bytes, 1_048_576);
        assert_eq!(resolved.execution.stderr_limit_bytes, 1_048_576);

        let mut explicit = omitted;
        explicit.execution.timeout_ms = Some(2_000);
        explicit.execution.stdout_limit_bytes = Some(4_096);
        explicit.execution.stderr_limit_bytes = Some(8_192);
        let resolved = runtime.resolve_proposal(&explicit);
        assert_eq!(resolved.execution.timeout_ms, 2_000);
        assert_eq!(resolved.execution.stdout_limit_bytes, 4_096);
        assert_eq!(resolved.execution.stderr_limit_bytes, 8_192);

        explicit.execution.timeout_ms = Some(8_000);
        let resolved = runtime.resolve_proposal(&explicit);
        assert_eq!(resolved.execution.timeout_ms, 8_000);
        validate_new_admission_policy(&resolved, 10_000, 1_048_576).unwrap();

        explicit.execution.timeout_ms = Some(99_000);
        let resolved = runtime.resolve_proposal(&explicit);
        assert_eq!(resolved.execution.timeout_ms, 99_000);
        let error = validate_new_admission_policy(&resolved, 10_000, 1_048_576).unwrap_err();
        assert_eq!(error.field.as_deref(), Some("execution.timeoutMs"));
    }

    #[test]
    fn proposal_plan_uses_shared_overall_deadline_without_rewriting_explicit_step_limits() {
        let runtime = proposal_runtime("plan", 10_000, 1_048_576);
        let fully_explicit = proposal(&[Some(2_000), Some(3_000)]);
        let resolved = runtime.resolve_proposal(&fully_explicit);
        assert_eq!(resolved.execution.timeout_ms, 10_000);
        assert_eq!(
            resolved
                .execution
                .steps
                .iter()
                .map(|step| step.timeout_ms)
                .collect::<Vec<_>>(),
            vec![2_000, 3_000]
        );

        let mixed = proposal(&[Some(2_000), None]);
        let resolved = runtime.resolve_proposal(&mixed);
        assert_eq!(resolved.execution.timeout_ms, 10_000);
        assert_eq!(
            resolved
                .execution
                .steps
                .iter()
                .map(|step| step.timeout_ms)
                .collect::<Vec<_>>(),
            vec![2_000, 10_000]
        );

        let over_sum = proposal(&[Some(8_000), Some(8_000)]);
        let resolved = runtime.resolve_proposal(&over_sum);
        assert_eq!(resolved.execution.timeout_ms, 10_000);
        assert_eq!(
            resolved
                .execution
                .steps
                .iter()
                .map(|step| step.timeout_ms)
                .collect::<Vec<_>>(),
            vec![8_000, 8_000]
        );
        validate_run_request_structure(&resolved).unwrap();
    }

    #[test]
    fn utf8_ranges_respect_hard_byte_bounds() {
        let root = std::env::temp_dir().join(format!(
            "ordivon-utf8-hard-bound-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        fs::create_dir_all(&root).unwrap();
        let path = root.join("stdout.log");
        fs::write(&path, "🙂x".as_bytes()).unwrap();
        let error = read_utf8_range(
            &path,
            0,
            3,
            5,
            true,
            RangeFields {
                offset: "stdoutOffset",
                max_bytes: "stdoutTailBytes",
            },
            "output",
        )
        .unwrap_err();
        assert_eq!(error.code, RuntimeErrorCode::InvalidRequest);
        assert_eq!(error.field.as_deref(), Some("stdoutTailBytes"));
        let first = read_utf8_range(
            &path,
            0,
            4,
            5,
            true,
            RangeFields {
                offset: "stdoutOffset",
                max_bytes: "stdoutTailBytes",
            },
            "output",
        )
        .unwrap();
        assert_eq!(first.content, "🙂");
        assert_eq!(first.next_offset, 4);
        let second = read_utf8_range(
            &path,
            4,
            1,
            5,
            true,
            RangeFields {
                offset: "stdoutOffset",
                max_bytes: "stdoutTailBytes",
            },
            "output",
        )
        .unwrap();
        assert_eq!(second.content, "x");
        assert_eq!(second.next_offset, 5);
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn configured_output_limit_is_enforced_before_admission() {
        let request = TaskRunRequest {
            schema_version: RUNTIME_SCHEMA_VERSION,
            client_request_id: "request:output-limit".to_string(),
            principal: "principal:test".to_string(),
            global_limit: 1,
            execution: UniversalExecutionRequest {
                workspace_id: "workspace-output-limit".to_string(),
                executable: "/usr/bin/true".to_string(),
                args: Vec::new(),
                cwd_relative: ".".to_string(),
                env: BTreeMap::new(),
                timeout_ms: 1_000,
                stdout_limit_bytes: 1_025,
                stderr_limit_bytes: 1_024,
                steps: Vec::new(),
                budget: crate::ExecutionBudget::default(),
                execution_profile: crate::runtime::ExecutionProfile::TrustedLocal,
                execution_target: crate::runtime::ExecutionTarget::LocalLinux,
                windows_authority: crate::runtime::WindowsAuthority::Limited,
                foreign_references: Vec::new(),
                host_dependencies: Vec::new(),
            },
            wait_ms: 0,
            stdout_tail_bytes: 0,
            stderr_tail_bytes: 0,
        };
        validate_run_request_structure(&request).unwrap();
        let error = validate_new_admission_policy(&request, 60_000, 1_024).unwrap_err();
        assert_eq!(error.code, RuntimeErrorCode::InvalidRequest);
        assert_eq!(error.field.as_deref(), Some("execution.stdoutLimitBytes"));
    }

    #[test]
    fn contained_runtime_paths_cannot_be_overridden_by_request_or_step_environment() {
        let mut request = TaskRunRequest {
            schema_version: RUNTIME_SCHEMA_VERSION,
            client_request_id: "request:contained-env".to_string(),
            principal: "principal:test".to_string(),
            global_limit: 1,
            execution: UniversalExecutionRequest {
                workspace_id: "workspace-contained-env".to_string(),
                executable: "/usr/bin/true".to_string(),
                args: Vec::new(),
                cwd_relative: ".".to_string(),
                env: BTreeMap::from([("CARGO_TARGET_DIR".to_string(), "/etc".to_string())]),
                timeout_ms: 1_000,
                stdout_limit_bytes: 1_024,
                stderr_limit_bytes: 1_024,
                steps: Vec::new(),
                budget: crate::ExecutionBudget::default(),
                execution_profile: crate::runtime::ExecutionProfile::ContainedLocal,
                execution_target: crate::runtime::ExecutionTarget::LocalLinux,
                windows_authority: crate::runtime::WindowsAuthority::Limited,
                foreign_references: Vec::new(),
                host_dependencies: Vec::new(),
            },
            wait_ms: 0,
            stdout_tail_bytes: 0,
            stderr_tail_bytes: 0,
        };
        let error = validate_run_request_structure(&request).unwrap_err();
        assert_eq!(
            error.field.as_deref(),
            Some("execution.env.CARGO_TARGET_DIR")
        );

        request.execution.env.clear();
        request.execution.steps.push(crate::UniversalExecutionStep {
            id: "step".to_string(),
            executable: "/usr/bin/true".to_string(),
            args: Vec::new(),
            cwd_relative: ".".to_string(),
            env: BTreeMap::from([("HOME".to_string(), "/etc".to_string())]),
            timeout_ms: 1_000,
            continue_on_error: false,
        });
        let error = validate_run_request_structure(&request).unwrap_err();
        assert_eq!(error.field.as_deref(), Some("execution.steps[0].env.HOME"));
    }

    #[test]
    fn adaptive_polling_starts_fast_and_caps_at_fifty_milliseconds() {
        let observed = (0..8)
            .map(|index| adaptive_poll_delay(index).as_millis())
            .collect::<Vec<_>>();
        assert_eq!(observed, vec![2, 5, 10, 20, 50, 50, 50, 50]);
    }

    #[test]
    fn trusted_runtime_accepts_temporary_storage_roots() {
        let root = std::env::temp_dir().join(format!(
            "ordivon-runtime-temp-root-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        let runtime = Runtime::new(RuntimeConfig {
            node_id: "test-node".to_string(),
            registry: RegistryConfig {
                db_path: root.join("registry/registry.sqlite3"),
                store_root: root.join("registry"),
                busy_timeout_ms: 5_000,
            },
            executor: UniversalExecutorConfig {
                store_root: root.join("runtime"),
                workspace_root: None,
                workspace_uid: None,
                workspace_gid: None,
                runner_path: Some(PathBuf::from("/usr/bin/true")),
                allowed_executable_roots: vec![PathBuf::from("/")],
                max_runtime_ms: 60_000,
                max_output_bytes: 1_048_576,
            },
            startup_grace_ms: 2_000,
            windows: None,
        })
        .unwrap();
        drop(runtime);
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn runtime_builds_explicit_minimal_environment_and_external_cache_paths() {
        let root = std::env::temp_dir().join(format!(
            "ordivon-runtime-environment-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        let runtime = Runtime::new(RuntimeConfig {
            node_id: "test-node".to_string(),
            registry: RegistryConfig {
                db_path: root.join("registry/registry.sqlite3"),
                store_root: root.join("registry"),
                busy_timeout_ms: 5_000,
            },
            executor: UniversalExecutorConfig {
                store_root: root.join("runtime"),
                workspace_root: None,
                workspace_uid: None,
                workspace_gid: None,
                runner_path: Some(PathBuf::from("/usr/bin/true")),
                allowed_executable_roots: vec![PathBuf::from("/")],
                max_runtime_ms: 60_000,
                max_output_bytes: 1_048_576,
            },
            startup_grace_ms: 2_000,
            windows: None,
        })
        .unwrap();
        let record = crate::universal::WorkspaceRecord {
            schema_version: UNIVERSAL_EXEC_SCHEMA_VERSION,
            workspace_id: "workspace-env".to_string(),
            source_repo: root.join("source-a").to_string_lossy().into_owned(),
            source_revision: "a".repeat(40),
            workspace_path: root
                .join("runtime/workspaces/workspace-env")
                .to_string_lossy()
                .into_owned(),
            created_unix_ms: 1,
        };
        let peer = crate::universal::WorkspaceRecord {
            workspace_id: "workspace-peer".to_string(),
            workspace_path: root
                .join("runtime/workspaces/workspace-peer")
                .to_string_lossy()
                .into_owned(),
            ..record.clone()
        };
        let other = crate::universal::WorkspaceRecord {
            workspace_id: "workspace-other".to_string(),
            source_repo: root.join("source-b").to_string_lossy().into_owned(),
            workspace_path: root
                .join("runtime/workspaces/workspace-other")
                .to_string_lossy()
                .into_owned(),
            ..record.clone()
        };
        let environment = runtime
            .execution_environment(&record, crate::runtime::ExecutionProfile::TrustedLocal)
            .unwrap();
        let peer_environment = runtime
            .execution_environment(&peer, crate::runtime::ExecutionProfile::TrustedLocal)
            .unwrap();
        let other_environment = runtime
            .execution_environment(&other, crate::runtime::ExecutionProfile::TrustedLocal)
            .unwrap();
        assert!(!runtime.inherit_host_environment());
        assert_eq!(
            environment.get("PATH").map(String::as_str),
            Some(runtime.execution_path.as_str())
        );
        assert_eq!(
            environment.get("HOME").map(String::as_str),
            Some(runtime.execution_home.as_str())
        );
        assert_eq!(
            environment.get("CARGO_TARGET_DIR").map(String::as_str),
            Some(TRUSTED_BUILD_TARGET_PRESENTATION)
        );
        assert_eq!(
            peer_environment.get("CARGO_TARGET_DIR"),
            environment.get("CARGO_TARGET_DIR")
        );
        assert_eq!(
            other_environment.get("CARGO_TARGET_DIR"),
            environment.get("CARGO_TARGET_DIR")
        );
        for workspace_id in ["workspace-env", "workspace-peer", "workspace-other"] {
            let backing = runtime
                .executor
                .workspace_build_cache_path(workspace_id)
                .join("cargo");
            assert!(backing.is_dir());
            assert_ne!(
                backing.to_string_lossy().as_ref(),
                TRUSTED_BUILD_TARGET_PRESENTATION
            );
        }
        for name in [
            "UV_CACHE_DIR",
            "PIP_CACHE_DIR",
            "npm_config_cache",
            "PNPM_HOME",
            "COREPACK_HOME",
            "BUN_INSTALL_CACHE_DIR",
            "GOMODCACHE",
            "GOCACHE",
        ] {
            assert_eq!(environment.get(name), peer_environment.get(name));
            assert!(Path::new(environment.get(name).unwrap())
                .starts_with(root.join("runtime/cache/shared")));
        }
        let workspace_root = root.join("runtime/workspaces/workspace-env");
        let cache_path = Path::new(environment.get("XDG_CACHE_HOME").unwrap());
        assert!(cache_path.starts_with(root.join("runtime/cache")));
        assert!(!cache_path.starts_with(&workspace_root));
        assert!(cache_path.is_dir());

        let trusted_tmp = Path::new(environment.get("TMPDIR").unwrap());
        let peer_tmp = Path::new(peer_environment.get("TMPDIR").unwrap());
        let other_tmp = Path::new(other_environment.get("TMPDIR").unwrap());
        assert!(trusted_tmp.to_string_lossy().starts_with("/tmp/ordivon-t/"));
        assert!(peer_tmp.to_string_lossy().starts_with("/tmp/ordivon-t/"));
        assert!(other_tmp.to_string_lossy().starts_with("/tmp/ordivon-t/"));
        assert_eq!(trusted_tmp.as_os_str().len(), 35);
        assert_eq!(peer_tmp.as_os_str().len(), 35);
        assert_eq!(other_tmp.as_os_str().len(), 35);
        assert_ne!(trusted_tmp, peer_tmp);
        assert_ne!(trusted_tmp, other_tmp);
        // The nested test root may itself be spelled through an outer trusted TMPDIR
        // presentation symlink. The trusted presentation authority is the canonical
        // backing target, not the raw spelling used to construct this test Runtime.
        assert_eq!(
            fs::read_link(trusted_tmp).unwrap(),
            runtime
                .executor
                .canonical_workspace_tmp_path("workspace-env")
                .unwrap()
        );
        assert_eq!(
            fs::read_link(peer_tmp).unwrap(),
            runtime
                .executor
                .canonical_workspace_tmp_path("workspace-peer")
                .unwrap()
        );
        assert_eq!(
            fs::read_link(other_tmp).unwrap(),
            runtime
                .executor
                .canonical_workspace_tmp_path("workspace-other")
                .unwrap()
        );
        assert!(trusted_tmp.is_dir());
        let vector_store = UniversalExecutorConfig {
            store_root: PathBuf::from("/tmp"),
            ..runtime.executor.clone()
        };
        assert_eq!(
            vector_store
                .workspace_tmp_presentation_path("workspace-env")
                .unwrap(),
            PathBuf::from("/tmp/ordivon-t/3536fc95f765287c720c")
        );
        let deep_store = UniversalExecutorConfig {
            store_root: root.join("deep/".repeat(80)),
            ..runtime.executor.clone()
        };
        fs::create_dir_all(&deep_store.store_root).unwrap();
        let deep_tmp = deep_store
            .workspace_tmp_presentation_path("workspace-env")
            .unwrap();
        assert_eq!(deep_tmp.as_os_str().len(), 35);
        assert_ne!(deep_tmp, trusted_tmp);
        let sibling_store = UniversalExecutorConfig {
            store_root: root.join("runtime-sibling"),
            ..runtime.executor.clone()
        };
        fs::create_dir_all(&sibling_store.store_root).unwrap();
        assert_ne!(
            sibling_store
                .workspace_tmp_presentation_path("workspace-env")
                .unwrap(),
            trusted_tmp
        );
        let store_alias = root.join("runtime-alias");
        std::os::unix::fs::symlink(&runtime.executor.store_root, &store_alias).unwrap();
        let alias_store = UniversalExecutorConfig {
            store_root: store_alias,
            ..runtime.executor.clone()
        };
        assert_eq!(
            alias_store
                .workspace_tmp_presentation_path("workspace-env")
                .unwrap(),
            trusted_tmp
        );

        let contained = runtime
            .execution_environment(&record, crate::runtime::ExecutionProfile::ContainedLocal)
            .unwrap();
        assert!(Path::new(contained.get("CARGO_TARGET_DIR").unwrap())
            .starts_with(root.join("runtime/cache/build/workspace-env")));
        assert!(Path::new(contained.get("UV_CACHE_DIR").unwrap())
            .starts_with(root.join("runtime/cache/workspaces/workspace-env/tooling")));
        assert_eq!(
            Path::new(contained.get("TMPDIR").unwrap()),
            runtime.executor.workspace_tmp_path("workspace-env")
        );

        fs::remove_file(other_tmp).unwrap();
        std::os::unix::fs::symlink(
            runtime.executor.workspace_tmp_path("workspace-env"),
            other_tmp,
        )
        .unwrap();
        let mismatch = runtime
            .execution_environment(&other, crate::runtime::ExecutionProfile::TrustedLocal)
            .unwrap_err();
        assert_eq!(mismatch.code, RuntimeErrorCode::WorkspaceStateMismatch);
        assert!(mismatch.message.contains("points at"));
        for path in [trusted_tmp, peer_tmp, other_tmp] {
            let _ = fs::remove_file(path);
        }
        drop(runtime);
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn trusted_command_keeps_only_process_ownership_and_lifecycle_properties() {
        let budget = crate::ExecutionBudget::default();
        let environment = BTreeMap::new();
        let command = build_systemd_run_command(&SystemdRunSpec {
            unit_name: "ordivon-test.service",
            runner: Path::new("/usr/bin/true"),
            bundle_path: Path::new("/var/lib/ordivon/attempts/attempt-test"),
            workspace_path: Path::new("/root/projects/ordivon-runtime"),
            workspace_git_common_dir: None,
            input_set_path: None,
            runtime_ceiling_ms: 10_000,
            budget: &budget,
            execution_profile: crate::runtime::ExecutionProfile::TrustedLocal,
            environment: &environment,
        })
        .unwrap();
        let args = command
            .get_args()
            .map(|value| value.to_string_lossy().into_owned())
            .collect::<Vec<_>>()
            .join(" ");
        for forbidden in [
            "PrivateNetwork",
            "ProtectSystem",
            "InaccessiblePaths",
            "CapabilityBoundingSet",
            "NoNewPrivileges",
            "ReadWritePaths",
            "MemoryMax",
            "TasksMax",
            "CPUQuota",
            "UMask",
        ] {
            assert!(
                !args.contains(forbidden),
                "trusted command contains {forbidden}"
            );
        }
        assert!(args.contains("KillMode=control-group"));
        assert!(args.contains("CollectMode=inactive"));
        assert!(!args.split_whitespace().any(|value| value == "--collect"));
        assert!(args.contains("RuntimeMaxSec=10000ms"));
        assert!(valid_environment_name("GITHUB_TOKEN"));
        assert!(valid_environment_name("CARGO_BIN_EXE_ordivon_job_fixture"));
        assert!(!valid_environment_name(
            "CARGO_BIN_EXE_ordivon-runtime-job-fixture"
        ));
    }

    #[test]
    fn execution_budget_maps_to_systemd_resource_properties() {
        let budget = crate::ExecutionBudget {
            memory_max_bytes: Some(512 * 1024 * 1024),
            tasks_max: Some(64),
            cpu_quota_percent: Some(250),
        };
        let environment = BTreeMap::new();
        let command = build_systemd_run_command(&SystemdRunSpec {
            unit_name: "ordivon-budget.service",
            runner: Path::new("/usr/bin/true"),
            bundle_path: Path::new("/var/lib/ordivon/attempts/attempt-budget"),
            workspace_path: Path::new("/root/projects/ordivon-runtime"),
            workspace_git_common_dir: None,
            input_set_path: None,
            runtime_ceiling_ms: 10_000,
            budget: &budget,
            execution_profile: crate::runtime::ExecutionProfile::TrustedLocal,
            environment: &environment,
        })
        .unwrap();
        let args = command
            .get_args()
            .map(|value| value.to_string_lossy().into_owned())
            .collect::<Vec<_>>()
            .join(" ");
        assert!(args.contains("MemoryMax=536870912"));
        assert!(args.contains("TasksMax=64"));
        assert!(args.contains("CPUQuota=250%"));
    }
    #[test]
    fn contained_command_is_explicitly_isolated_without_trusted_environment() {
        let root =
            std::env::temp_dir().join(format!("ordivon-contained-command-{}", std::process::id()));
        let workspace = root.join("workspace");
        let bundle = root.join("bundle");
        let cache = root.join("cache");
        for path in [&workspace, &bundle, &cache] {
            fs::create_dir_all(path).unwrap();
        }
        let environment = BTreeMap::from([
            (
                "HOME".to_string(),
                cache.join("home").to_string_lossy().into_owned(),
            ),
            (
                "TMPDIR".to_string(),
                cache.join("tmp").to_string_lossy().into_owned(),
            ),
        ]);
        for value in environment.values() {
            fs::create_dir_all(value).unwrap();
        }
        let budget = crate::ExecutionBudget::default();
        let command = build_systemd_run_command(&SystemdRunSpec {
            unit_name: "ordivon-contained-test.service",
            runner: Path::new("/usr/bin/true"),
            bundle_path: &bundle,
            workspace_path: &workspace,
            workspace_git_common_dir: None,
            input_set_path: None,
            runtime_ceiling_ms: 10_000,
            budget: &budget,
            execution_profile: crate::runtime::ExecutionProfile::ContainedLocal,
            environment: &environment,
        })
        .unwrap();
        let args = command
            .get_args()
            .map(|value| value.to_string_lossy().into_owned())
            .collect::<Vec<_>>();
        let joined = args.join(" ");
        for required in [
            "ProtectSystem=strict",
            "ProtectHome=tmpfs",
            "PrivateNetwork=yes",
            "NoNewPrivileges=yes",
            "CapabilityBoundingSet=",
            "ProtectControlGroups=yes",
            "RestrictAddressFamilies=AF_UNIX",
            "TemporaryFileSystem=/run:ro",
            "TemporaryFileSystem=/var:ro",
        ] {
            assert!(joined.contains(required), "missing {required}");
        }
        assert!(joined.contains(&format!(
            "BindPaths={}:{}",
            workspace.display(),
            workspace.display()
        )));
        assert!(joined.contains("BindReadOnlyPaths=/usr/bin/true:/usr/bin/true"));
        assert!(!joined.contains("GITHUB_TOKEN"));
        assert!(!args
            .iter()
            .any(|arg| arg.starts_with("--setenv=GITHUB_TOKEN=")));
        assert!(joined.contains("--setenv=GIT_OPTIONAL_LOCKS=0"));
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn universal_error_mapping_preserves_agent_control_semantics() {
        let cases = [
            (
                crate::UniversalExecErrorCode::WorkspaceNotFound,
                RuntimeErrorCode::WorkspaceNotFound,
            ),
            (
                crate::UniversalExecErrorCode::RevisionMismatch,
                RuntimeErrorCode::RevisionMismatch,
            ),
            (
                crate::UniversalExecErrorCode::MetadataCorrupt,
                RuntimeErrorCode::MetadataCorrupt,
            ),
            (
                crate::UniversalExecErrorCode::WorkspaceMutationIncomplete,
                RuntimeErrorCode::ReconciliationRequired,
            ),
            (
                crate::UniversalExecErrorCode::TaskStateUnavailable,
                RuntimeErrorCode::ReconciliationRequired,
            ),
        ];
        for (source, expected) in cases {
            let mapped = map_universal_error(crate::UniversalExecError::new(
                source,
                "test",
                Some("field"),
                false,
            ));
            assert_eq!(mapped.code, expected);
        }
    }

    #[test]
    fn cgroup_events_population_is_recursive_and_fail_closed() {
        assert!(parse_cgroup_populated("populated 1\nfrozen 0\n").unwrap());
        assert!(!parse_cgroup_populated("populated 0\nfrozen 0\n").unwrap());
        for invalid in ["frozen 0\n", "populated 2\n", "populated 1 extra\n"] {
            let error = parse_cgroup_populated(invalid).unwrap_err();
            assert_eq!(error.code, RuntimeErrorCode::RegistryCorrupt);
        }
    }
}
