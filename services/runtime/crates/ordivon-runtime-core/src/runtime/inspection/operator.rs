use rusqlite::OptionalExtension;
use sha2::{Digest, Sha256};
use std::path::Path;

use super::engine::{
    latest_output_modified_ms, load_runner_progress_if_present, map_universal_error,
};
use crate::universal::{
    load_workspace_record, workspace_change_projection_at, workspace_head_revision_at,
    UniversalExecutorConfig,
};
use super::supervisor::{validate_attempt_supervisor_owner, AttemptSupervisorOwner};
use super::types::{RuntimeReleaseContract, RuntimeReleaseEffectBinding};

pub const DEFAULT_WORKSPACE_INSPECTION_JOB_LIMIT: u32 = 20;
pub const MAX_WORKSPACE_INSPECTION_JOB_LIMIT: u32 = 100;

#[derive(Clone, Debug)]
pub struct RuntimeWorkspaceInspectionConfig {
    pub db_path: PathBuf,
    pub store_root: PathBuf,
    pub busy_timeout_ms: u64,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeWorkspaceInspection {
    pub schema_version: u32,
    pub generated_at_ms: u64,
    pub migration_version: i64,
    pub workspace_id: String,
    pub source_repo: String,
    pub source_revision: String,
    pub current_head_revision: String,
    pub dirty: bool,
    pub changed_paths: Vec<String>,
    pub modified_paths: Vec<String>,
    pub added_paths: Vec<String>,
    pub deleted_paths: Vec<String>,
    pub renamed_paths: Vec<crate::WorkspaceRenamedPath>,
    pub untracked_paths: Vec<String>,
    pub active_job_ids: Vec<String>,
    pub recent_jobs: Vec<RuntimeWorkspaceInspectionJob>,
    pub recent_jobs_truncated: bool,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeWorkspaceInspectionJob {
    pub created_at_ms: u64,
    pub client_request_id: String,
    pub job_id: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub attempt_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub attempt_state: Option<AttemptState>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub execution_disposition: Option<JobResolution>,
    pub recovery_required: bool,
    pub duration_ms: u64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub last_output_at_ms: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub progress_revision: Option<u64>,
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
    pub artifact_count: u64,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeExperienceSummary {
    pub schema_version: u32,
    pub generated_at_ms: u64,
    pub migration_version: i64,
    pub since_ms: u64,
    pub jobs: RuntimeExperienceJobSummary,
    pub resolutions: BTreeMap<String, u64>,
    pub attempts: BTreeMap<String, u64>,
    pub reservations: BTreeMap<String, u64>,
    pub recovery: RuntimeExperienceRecoverySummary,
    pub dispatch: RuntimeExperienceDispatchSummary,
    pub cancellation: RuntimeExperienceCancellationSummary,
    pub mechanical_latency_ms: RuntimeExperienceMechanicalLatencySummary,
    pub duration_ms: RuntimeExperienceDurationSummary,
    pub artifacts: RuntimeExperienceArtifactSummary,
    pub event_types: BTreeMap<String, u64>,
    pub terminal_reasons: BTreeMap<String, u64>,
    pub semantic_completion_evaluated: bool,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeExperienceJobSummary {
    pub total: u64,
    pub converged: u64,
    pub unresolved: u64,
    pub recovery_required: u64,
    pub capacity_held: u64,
    pub convergence_rate_basis_points: u64,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeExperienceRecoverySummary {
    pub jobs_with_reconciliation_failure: u64,
    pub jobs_with_automatic_recovery: u64,
    pub jobs_with_administrative_repair: u64,
    pub automatic_recovery_rate_basis_points: u64,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeExperienceDispatchSummary {
    pub dispatches: u64,
    pub jobs_with_duplicate_dispatch: u64,
    pub duplicate_dispatches: u64,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeExperienceCancellationSummary {
    pub requested: u64,
    pub resolved_cancelled: u64,
    pub resolved_other: u64,
    pub unresolved: u64,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeExperienceDurationSummary {
    pub samples: u64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub p50: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub p95: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub max: Option<u64>,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeExperienceMechanicalLatencySummary {
    pub admission_to_dispatch: RuntimeExperienceDurationSummary,
    pub dispatch_to_runner_bound: RuntimeExperienceDurationSummary,
    pub runner_bound_to_terminal: RuntimeExperienceDurationSummary,
    pub cancellation_to_terminal: RuntimeExperienceDurationSummary,
    pub reconciliation_to_convergence: RuntimeExperienceDurationSummary,
}

#[derive(Default)]
struct RuntimeMechanicalLatencySamples {
    admission_to_dispatch: Vec<u64>,
    dispatch_to_runner_bound: Vec<u64>,
    runner_bound_to_terminal: Vec<u64>,
    cancellation_to_terminal: Vec<u64>,
    reconciliation_to_convergence: Vec<u64>,
}

#[derive(Default)]
struct RuntimeJobLatencyState {
    created_at_ms: u64,
    dispatch_at_ms: Option<u64>,
    runner_bound_at_ms: Option<u64>,
    cancellation_at_ms: Option<u64>,
    reconciliation_failed_at_ms: Option<u64>,
    terminal_at_ms: Option<u64>,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeExperienceArtifactSummary {
    pub count: u64,
    pub bytes: u64,
    pub truncated: u64,
}


#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeOperatorAttemptSupervisorOwner {
    pub contract: String,
    pub launcher_process_id: u32,
    pub launcher_process_creation_time_file_time: u64,
    pub launcher_image_digest: String,
    pub job_name: String,
    pub start_evidence_digest: String,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeOperatorRegistryInspection {
    pub schema_version: u32,
    pub generated_at_ms: u64,
    pub migration_version: i64,
    pub active_job_ids: Vec<String>,
    pub active_workspaces: Vec<RuntimeOperatorActiveWorkspace>,
    pub held_workspace_ids: Vec<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub resolved_attempt_job_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub resolved_attempt_supervisor_owner: Option<RuntimeOperatorAttemptSupervisorOwner>,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeOperatorActiveWorkspace {
    pub workspace_id: String,
    pub active_job_ids: Vec<String>,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeOperatorRegistryActivityInspection {
    pub schema_version: u32,
    pub generated_at_ms: u64,
    pub migration_version: i64,
    pub workspaces: Vec<RuntimeOperatorWorkspaceLastActivity>,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeOperatorRegistryMarkersInspection {
    pub schema_version: u32,
    pub generated_at_ms: u64,
    pub migration_version: i64,
    pub workspaces: Vec<RuntimeOperatorWorkspaceMarker>,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeOperatorWorkspaceMarker {
    pub workspace_id: String,
    pub activity_marker: String,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeOperatorRegistryStatusInspection {
    pub schema_version: u32,
    pub generated_at_ms: u64,
    pub migration_version: i64,
    pub jobs_total: u64,
    pub jobs_active: u64,
    pub nonterminal_attempts: u64,
    pub active_reservations: u64,
    pub held_reservations: u64,
    pub recovery_required: u64,
    pub held_workspace_ids: Vec<String>,
    pub jobs: RuntimeOperatorDashboardJobs,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeOperatorDashboardJobs {
    pub active: Vec<RuntimeOperatorDashboardJob>,
    pub recent: Vec<RuntimeOperatorDashboardJob>,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeOperatorDashboardJob {
    pub job_id: String,
    pub workspace_id: String,
    pub resolution: Option<String>,
    pub execution_plan_json: Option<String>,
    pub created_at_ms: Option<u64>,
    pub projected_attempt_id: Option<String>,
    pub attempt_state: Option<String>,
    pub started_at_ms: Option<u64>,
    pub finished_at_ms: Option<u64>,
    pub exit_code: Option<i64>,
    pub bundle_path: Option<String>,
    pub recovery_required: bool,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeOperatorWorkspaceLastActivity {
    pub workspace_id: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub last_activity_ms: Option<u64>,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeOperatorWorkspaceActivityInspection {
    pub schema_version: u32,
    pub generated_at_ms: u64,
    pub migration_version: i64,
    pub workspace: RuntimeOperatorWorkspaceActivity,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeOperatorWorkspaceActivity {
    pub workspace_id: String,
    pub active_job_ids: Vec<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub last_activity_ms: Option<u64>,
    pub activity_marker: String,
}

fn registry_table_columns(
    connection: &Connection,
    table: &str,
) -> RuntimeResult<std::collections::BTreeSet<String>> {
    let sql = format!("PRAGMA table_info({table})");
    let mut statement = connection
        .prepare(&sql)
        .map_err(|error| RuntimeError::from_sql(error, "prepare Registry capability inspection"))?;
    let rows = statement
        .query_map([], |row| row.get::<_, String>(1))
        .map_err(|error| RuntimeError::from_sql(error, "query Registry capabilities"))?;
    rows.map(|row| {
        row.map_err(|error| RuntimeError::from_sql(error, "decode Registry capability"))
    })
    .collect()
}

fn validate_operator_registry_capabilities(
    connection: &Connection,
    require_workspace_activity: bool,
) -> RuntimeResult<()> {
    let mut required = vec![
        ("jobs", vec!["job_id", "workspace_id", "resolution"]),
        ("attempts", vec!["attempt_id", "job_id"]),
        ("concurrency_reservations", vec!["attempt_id", "state"]),
    ];
    if require_workspace_activity {
        required = vec![
            ("jobs", vec!["job_id", "workspace_id", "resolution", "created_at_ms"]),
            ("attempts", vec!["attempt_id", "job_id"]),
            ("concurrency_reservations", vec!["attempt_id", "state"]),
        ];
    }
    let mut missing = Vec::<String>::new();
    for (table, columns) in required {
        let present = registry_table_columns(connection, table)?;
        if present.is_empty() {
            missing.push(format!("table:{table}"));
            continue;
        }
        for column in columns {
            if !present.contains(column) {
                missing.push(format!("column:{table}.{column}"));
            }
        }
    }
    if !missing.is_empty() {
        return Err(RuntimeError::new(
            RuntimeErrorCode::SchemaVersionUnsupported,
            format!(
                "Runtime Registry lacks operator inspection capabilities: {}",
                missing.join(", ")
            ),
            None,
            false,
        ));
    }
    Ok(())
}

fn validate_registry_marker_capabilities(connection: &Connection) -> RuntimeResult<()> {
    let required = [
        ("jobs", ["workspace_id", "job_id", "resolution"].as_slice()),
        ("attempts", ["attempt_id", "job_id"].as_slice()),
    ];
    let mut missing = Vec::<String>::new();
    for (table, columns) in required {
        let present = registry_table_columns(connection, table)?;
        if present.is_empty() {
            missing.push(format!("table:{table}"));
            continue;
        }
        for column in columns {
            if !present.contains(*column) {
                missing.push(format!("column:{table}.{column}"));
            }
        }
    }
    if !missing.is_empty() {
        return Err(RuntimeError::new(
            RuntimeErrorCode::SchemaVersionUnsupported,
            format!(
                "Runtime Registry lacks marker inspection capabilities: {}",
                missing.join(", ")
            ),
            None,
            false,
        ));
    }
    Ok(())
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeOperatorReleaseEffectInspection {
    pub job_id: String,
    pub effect_id: String,
    pub request_digest: String,
    pub workspace_id: String,
    pub commit: String,
    pub candidate_manifest_digest: String,
    pub expected_tool_count: u32,
    pub receipt_path: String,
    pub binding_digest: String,
}

pub fn inspect_runtime_release_effect(
    config: &RuntimeInspectionConfig,
    effect_id: &str,
) -> RuntimeResult<Option<RuntimeOperatorReleaseEffectInspection>> {
    if effect_id.len() != 64
        || !effect_id
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(RuntimeError::invalid(
            "effectId must be 64 lowercase hexadecimal characters",
            "effectId",
        ));
    }
    let (connection, _) = open_operator_read_only(config)?;
    let row = connection
        .query_row(
            "SELECT r.job_id,r.contract,r.request_digest,r.workspace_id,r.commit_revision,r.candidate_manifest_digest,r.expected_tool_count,r.receipt_path,r.binding_digest,j.workspace_snapshot_json FROM job_runtime_release_effects r JOIN jobs j ON j.job_id=r.job_id WHERE r.effect_id=?1",
            [effect_id],
            |row| {
                Ok((
                    row.get::<_, String>(0)?,
                    row.get::<_, String>(1)?,
                    row.get::<_, String>(2)?,
                    row.get::<_, String>(3)?,
                    row.get::<_, String>(4)?,
                    row.get::<_, String>(5)?,
                    row.get::<_, u32>(6)?,
                    row.get::<_, String>(7)?,
                    row.get::<_, String>(8)?,
                    row.get::<_, String>(9)?,
                ))
            },
        )
        .optional()
        .map_err(|error| RuntimeError::from_sql(error, "inspect Runtime Release effect"))?;
    let Some((
        job_id,
        contract,
        request_digest,
        workspace_id,
        commit,
        candidate_manifest_digest,
        expected_tool_count,
        receipt_path,
        binding_digest,
        workspace_snapshot_json,
    )) = row
    else {
        return Ok(None);
    };
    if contract != "runtime_release_v1" {
        return Err(RuntimeError::new(
            RuntimeErrorCode::RegistryCorrupt,
            "stored Runtime Release contract is unsupported",
            Some("runtimeReleaseEffect.contract"),
            false,
        ));
    }
    let binding = RuntimeReleaseEffectBinding {
        contract: RuntimeReleaseContract::RuntimeReleaseV1,
        effect_id: effect_id.to_string(),
        request_digest: request_digest.clone(),
        workspace_id: workspace_id.clone(),
        commit: commit.clone(),
        candidate_manifest_digest: candidate_manifest_digest.clone(),
        expected_tool_count,
        receipt_path: receipt_path.clone(),
    };
    let encoded = serde_json::to_string(&binding).map_err(|error| {
        RuntimeError::new(
            RuntimeErrorCode::RegistryCorrupt,
            format!("cannot serialize stored Runtime Release effect: {error}"),
            Some("runtimeReleaseEffect"),
            false,
        )
    })?;
    let observed_digest = format!("sha256:{:x}", Sha256::digest(encoded.as_bytes()));
    if observed_digest != binding_digest {
        return Err(RuntimeError::new(
            RuntimeErrorCode::RegistryCorrupt,
            "stored Runtime Release effect digest does not match side truth",
            Some("runtimeReleaseEffect"),
            false,
        ));
    }
    let snapshot: serde_json::Value =
        serde_json::from_str(&workspace_snapshot_json).map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                format!("stored Workspace snapshot is invalid: {error}"),
                Some("workspaceSnapshot"),
                false,
            )
        })?;
    if snapshot
        .get("runtimeReleaseEffectDigest")
        .and_then(serde_json::Value::as_str)
        != Some(binding_digest.as_str())
    {
        return Err(RuntimeError::new(
            RuntimeErrorCode::RegistryCorrupt,
            "Runtime Release Job commitment does not match side truth",
            Some("workspaceSnapshot.runtimeReleaseEffectDigest"),
            false,
        ));
    }
    Ok(Some(RuntimeOperatorReleaseEffectInspection {
        job_id,
        effect_id: effect_id.to_string(),
        request_digest,
        workspace_id,
        commit,
        candidate_manifest_digest,
        expected_tool_count,
        receipt_path,
        binding_digest,
    }))
}

pub fn inspect_runtime_release_effect_owner(
    config: &RuntimeInspectionConfig,
    effect_id: &str,
) -> RuntimeResult<Option<String>> {
    Ok(inspect_runtime_release_effect(config, effect_id)?.map(|effect| effect.job_id))
}

pub fn inspect_registry(
    config: &RuntimeInspectionConfig,
    resolve_attempt_id: Option<&str>,
) -> RuntimeResult<RuntimeOperatorRegistryInspection> {
    let (connection, migration_version) = open_operator_read_only(config)?;
    validate_operator_registry_capabilities(&connection, false)?;
    let mut active_job_ids = Vec::<String>::new();
    let mut active_by_workspace = BTreeMap::<String, Vec<String>>::new();
    {
        let job_columns = registry_table_columns(&connection, "jobs")?;
        let has_created_at = job_columns.contains("created_at_ms");
        let active_sql = if has_created_at {
            "SELECT workspace_id,job_id,created_at_ms FROM jobs WHERE resolution IS NULL UNION SELECT jobs.workspace_id,jobs.job_id,jobs.created_at_ms FROM concurrency_reservations JOIN attempts ON attempts.attempt_id=concurrency_reservations.attempt_id JOIN jobs ON jobs.job_id=attempts.job_id WHERE concurrency_reservations.state IN ('active','held_orphaned') ORDER BY workspace_id,created_at_ms DESC,job_id DESC"
        } else {
            "SELECT workspace_id,job_id,0 AS created_at_ms FROM jobs WHERE resolution IS NULL UNION SELECT jobs.workspace_id,jobs.job_id,0 AS created_at_ms FROM concurrency_reservations JOIN attempts ON attempts.attempt_id=concurrency_reservations.attempt_id JOIN jobs ON jobs.job_id=attempts.job_id WHERE concurrency_reservations.state IN ('active','held_orphaned') ORDER BY workspace_id,job_id"
        };
        let mut statement = connection
            .prepare(active_sql)
            .map_err(|error| RuntimeError::from_sql(error, "prepare active Registry Jobs"))?;
        let rows = statement
            .query_map([], |row| {
                Ok((
                    row.get::<_, String>(0)?,
                    row.get::<_, String>(1)?,
                    row.get::<_, u64>(2)?,
                ))
            })
            .map_err(|error| RuntimeError::from_sql(error, "query active Registry Jobs"))?;
        for row in rows {
            let (workspace_id, job_id, _created_at_ms) =
                row.map_err(|error| RuntimeError::from_sql(error, "decode active Registry Job"))?;
            active_by_workspace
                .entry(workspace_id)
                .or_default()
                .push(job_id.clone());
            active_job_ids.push(job_id);
        }
    }
    active_job_ids.sort();
    active_job_ids.dedup();
    let active_workspaces = active_by_workspace
        .into_iter()
        .map(|(workspace_id, active_job_ids)| RuntimeOperatorActiveWorkspace {
            workspace_id,
            active_job_ids,
        })
        .collect();

    let mut held_workspace_ids = Vec::<String>::new();
    {
        let mut statement = connection
            .prepare(
                "SELECT DISTINCT jobs.workspace_id FROM concurrency_reservations JOIN attempts ON attempts.attempt_id=concurrency_reservations.attempt_id JOIN jobs ON jobs.job_id=attempts.job_id WHERE concurrency_reservations.state IN ('active','held_orphaned') ORDER BY jobs.workspace_id",
            )
            .map_err(|error| RuntimeError::from_sql(error, "prepare held Workspace inspection"))?;
        let rows = statement
            .query_map([], |row| row.get::<_, String>(0))
            .map_err(|error| RuntimeError::from_sql(error, "query held Workspaces"))?;
        for row in rows {
            held_workspace_ids.push(
                row.map_err(|error| RuntimeError::from_sql(error, "decode held Workspace"))?,
            );
        }
    }

    let resolved_attempt_job_id = resolve_attempt_id
        .map(|attempt_id| {
            connection
                .query_row(
                    "SELECT job_id FROM attempts WHERE attempt_id=?1",
                    [attempt_id],
                    |row| row.get::<_, String>(0),
                )
                .optional()
                .map_err(|error| RuntimeError::from_sql(error, "resolve Attempt Job identity"))
        })
        .transpose()?
        .flatten();

    let supervisor_owner_table_exists = connection
        .query_row(
            "SELECT EXISTS(SELECT 1 FROM sqlite_master WHERE type='table' AND name='attempt_supervisor_owners')",
            [],
            |row| row.get::<_, bool>(0),
        )
        .map_err(|error| {
            RuntimeError::from_sql(error, "inspect Attempt Supervisor Owner storage")
        })?;
    let resolved_attempt_supervisor_owner = if supervisor_owner_table_exists {
        resolve_attempt_id
            .map(|attempt_id| {
                connection
                    .query_row(
                        "SELECT owner_json,owner_digest FROM attempt_supervisor_owners WHERE attempt_id=?1",
                        [attempt_id],
                        |row| Ok((row.get::<_, String>(0)?, row.get::<_, String>(1)?)),
                    )
                    .optional()
                    .map_err(|error| {
                        RuntimeError::from_sql(error, "inspect Attempt Supervisor Owner")
                    })
            })
            .transpose()?
            .flatten()
    } else {
        None
    }
    .map(|(owner_json, owner_digest)| -> RuntimeResult<_> {
            let observed_digest = format!("sha256:{:x}", Sha256::digest(owner_json.as_bytes()));
            if observed_digest != owner_digest {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "stored Attempt Supervisor Owner digest does not match side truth",
                    Some("attemptSupervisorOwner"),
                    false,
                ));
            }
            let owner: AttemptSupervisorOwner =
                serde_json::from_str(&owner_json).map_err(|error| {
                    RuntimeError::new(
                        RuntimeErrorCode::RegistryCorrupt,
                        format!("stored Attempt Supervisor Owner is invalid: {error}"),
                        Some("attemptSupervisorOwner"),
                        false,
                    )
                })?;
            validate_attempt_supervisor_owner(&owner)?;
            let AttemptSupervisorOwner::WindowsLauncherV1 {
                launcher_process_id,
                launcher_process_creation_time_file_time,
                launcher_image_digest,
                job_name,
                start_evidence_digest,
            } = owner;
            Ok(RuntimeOperatorAttemptSupervisorOwner {
                contract: "windows_launcher_v1".to_string(),
                launcher_process_id,
                launcher_process_creation_time_file_time,
                launcher_image_digest,
                job_name,
                start_evidence_digest,
            })
        })
        .transpose()?;

    Ok(RuntimeOperatorRegistryInspection {
        schema_version: RUNTIME_INSPECTION_SCHEMA_VERSION,
        generated_at_ms: now_ms()?,
        migration_version,
        active_job_ids,
        active_workspaces,
        held_workspace_ids,
        resolved_attempt_job_id,
        resolved_attempt_supervisor_owner,
    })
}

pub fn inspect_registry_status(
    config: &RuntimeInspectionConfig,
    job_limit: u32,
) -> RuntimeResult<RuntimeOperatorRegistryStatusInspection> {
    let (connection, migration_version) = open_operator_read_only(config)?;
    let jobs_columns = registry_table_columns(&connection, "jobs")?;
    let attempts_columns = registry_table_columns(&connection, "attempts")?;
    let reservation_columns = registry_table_columns(&connection, "concurrency_reservations")?;
    let required_jobs = [
        "job_id",
        "workspace_id",
        "resolution",
        "execution_plan_json",
        "created_at_ms",
        "current_attempt_id",
    ];
    let required_attempts = [
        "attempt_id",
        "job_id",
        "attempt_number",
        "state",
        "started_at_ms",
        "finished_at_ms",
        "exit_code",
        "bundle_path",
    ];
    let required_reservations = ["attempt_id", "state"];
    let mut missing = Vec::<String>::new();
    for column in required_jobs {
        if !jobs_columns.contains(column) {
            missing.push(format!("column:jobs.{column}"));
        }
    }
    for column in required_attempts {
        if !attempts_columns.contains(column) {
            missing.push(format!("column:attempts.{column}"));
        }
    }
    for column in required_reservations {
        if !reservation_columns.contains(column) {
            missing.push(format!("column:concurrency_reservations.{column}"));
        }
    }
    let recovery_expression = if migration_version >= 5 {
        if !attempts_columns.contains("recovery_required") {
            missing.push("column:attempts.recovery_required".to_string());
        }
        "COALESCE(a.recovery_required,0)"
    } else {
        let condition_columns = registry_table_columns(&connection, "attempt_conditions")?;
        for column in ["attempt_id", "condition_type", "status"] {
            if !condition_columns.contains(column) {
                missing.push(format!("column:attempt_conditions.{column}"));
            }
        }
        "EXISTS(SELECT 1 FROM attempt_conditions c WHERE c.attempt_id=COALESCE(j.current_attempt_id,a.attempt_id) AND c.condition_type='recovery_required' AND c.status='true')"
    };
    if !missing.is_empty() {
        return Err(RuntimeError::new(
            RuntimeErrorCode::SchemaVersionUnsupported,
            format!(
                "Runtime Registry lacks status inspection capabilities: {}",
                missing.join(", ")
            ),
            None,
            false,
        ));
    }

    let jobs_total: u64 = connection
        .query_row("SELECT COUNT(*) FROM jobs", [], |row| row.get(0))
        .map_err(|error| RuntimeError::from_sql(error, "count Registry Jobs for status"))?;
    let jobs_active: u64 = connection
        .query_row(
            "SELECT COUNT(*) FROM jobs WHERE resolution IS NULL",
            [],
            |row| row.get(0),
        )
        .map_err(|error| RuntimeError::from_sql(error, "count active Registry Jobs for status"))?;
    let nonterminal_attempts: u64 = connection
        .query_row(
            "SELECT COUNT(*) FROM attempts WHERE state NOT IN ('succeeded','failed','timed_out','cancelled','lost','orphaned')",
            [],
            |row| row.get(0),
        )
        .map_err(|error| RuntimeError::from_sql(error, "count nonterminal Attempts for status"))?;
    let active_reservations: u64 = connection
        .query_row(
            "SELECT COUNT(*) FROM concurrency_reservations WHERE state='active'",
            [],
            |row| row.get(0),
        )
        .map_err(|error| RuntimeError::from_sql(error, "count active reservations for status"))?;
    let held_reservations: u64 = connection
        .query_row(
            "SELECT COUNT(*) FROM concurrency_reservations WHERE state='held_orphaned'",
            [],
            |row| row.get(0),
        )
        .map_err(|error| RuntimeError::from_sql(error, "count held reservations for status"))?;
    let recovery_required_sql = if migration_version >= 5 {
        "SELECT COUNT(*) FROM attempts WHERE recovery_required=1"
    } else {
        "SELECT COUNT(*) FROM attempt_conditions WHERE condition_type='recovery_required' AND status='true'"
    };
    let recovery_required: u64 = connection
        .query_row(recovery_required_sql, [], |row| row.get(0))
        .map_err(|error| RuntimeError::from_sql(error, "count recovery-required Attempts for status"))?;

    let mut held_workspace_ids = Vec::<String>::new();
    {
        let mut statement = connection
            .prepare(
                "SELECT DISTINCT jobs.workspace_id FROM jobs JOIN attempts ON attempts.job_id=jobs.job_id JOIN concurrency_reservations ON concurrency_reservations.attempt_id=attempts.attempt_id WHERE concurrency_reservations.state IN ('active','held_orphaned') ORDER BY jobs.workspace_id",
            )
            .map_err(|error| RuntimeError::from_sql(error, "prepare held Workspace status"))?;
        let rows = statement
            .query_map([], |row| row.get::<_, String>(0))
            .map_err(|error| RuntimeError::from_sql(error, "query held Workspace status"))?;
        for row in rows {
            held_workspace_ids.push(
                row.map_err(|error| RuntimeError::from_sql(error, "decode held Workspace status"))?,
            );
        }
    }

    fn load_dashboard_rows(
        connection: &Connection,
        recovery_expression: &str,
        terminal: bool,
        limit: u32,
    ) -> RuntimeResult<Vec<RuntimeOperatorDashboardJob>> {
        if limit == 0 {
            return Ok(Vec::new());
        }
        let resolution_predicate = if terminal {
            "j.resolution IS NOT NULL"
        } else {
            "j.resolution IS NULL"
        };
        let sql = format!(
            "SELECT j.job_id,j.workspace_id,j.resolution,j.execution_plan_json,j.created_at_ms,a.attempt_id,a.state,a.started_at_ms,a.finished_at_ms,a.exit_code,a.bundle_path,{recovery_expression} AS recovery_required FROM jobs j LEFT JOIN attempts a ON a.attempt_id=COALESCE(j.current_attempt_id,(SELECT latest.attempt_id FROM attempts latest WHERE latest.job_id=j.job_id ORDER BY latest.attempt_number DESC LIMIT 1)) WHERE {resolution_predicate} ORDER BY j.created_at_ms DESC LIMIT ?1"
        );
        let mut statement = connection
            .prepare(&sql)
            .map_err(|error| RuntimeError::from_sql(error, "prepare dashboard Job status"))?;
        let rows = statement
            .query_map([limit], |row| {
                Ok(RuntimeOperatorDashboardJob {
                    job_id: row.get(0)?,
                    workspace_id: row.get(1)?,
                    resolution: row.get(2)?,
                    execution_plan_json: row.get(3)?,
                    created_at_ms: row.get(4)?,
                    projected_attempt_id: row.get(5)?,
                    attempt_state: row.get(6)?,
                    started_at_ms: row.get(7)?,
                    finished_at_ms: row.get(8)?,
                    exit_code: row.get(9)?,
                    bundle_path: row.get(10)?,
                    recovery_required: row.get::<_, i64>(11)? != 0,
                })
            })
            .map_err(|error| RuntimeError::from_sql(error, "query dashboard Job status"))?;
        rows.map(|row| {
            row.map_err(|error| RuntimeError::from_sql(error, "decode dashboard Job status"))
        })
        .collect()
    }

    let active = load_dashboard_rows(&connection, recovery_expression, false, job_limit)?;
    let recent = load_dashboard_rows(&connection, recovery_expression, true, job_limit)?;
    Ok(RuntimeOperatorRegistryStatusInspection {
        schema_version: RUNTIME_INSPECTION_SCHEMA_VERSION,
        generated_at_ms: now_ms()?,
        migration_version,
        jobs_total,
        jobs_active,
        nonterminal_attempts,
        active_reservations,
        held_reservations,
        recovery_required,
        held_workspace_ids,
        jobs: RuntimeOperatorDashboardJobs { active, recent },
    })
}

pub fn inspect_registry_markers(
    config: &RuntimeInspectionConfig,
    workspace_id: Option<&str>,
) -> RuntimeResult<RuntimeOperatorRegistryMarkersInspection> {
    if let Some(workspace_id) = workspace_id {
        crate::universal::validate_id(workspace_id, "workspaceId")
            .map_err(|error| RuntimeError::invalid(error.message, "workspaceId"))?;
    }
    let (connection, migration_version) = open_operator_read_only(config)?;
    validate_registry_marker_capabilities(&connection)?;
    let mut digests = BTreeMap::<String, Sha256>::new();

    if let Some(workspace_id) = workspace_id {
        let mut statement = connection
            .prepare(
                "SELECT job_id,resolution FROM jobs WHERE workspace_id=?1 ORDER BY job_id",
            )
            .map_err(|error| RuntimeError::from_sql(error, "prepare Workspace marker Jobs"))?;
        let rows = statement
            .query_map([workspace_id], |row| {
                Ok((row.get::<_, String>(0)?, row.get::<_, Option<String>>(1)?))
            })
            .map_err(|error| RuntimeError::from_sql(error, "query Workspace marker Jobs"))?;
        let digest = digests.entry(workspace_id.to_string()).or_default();
        for row in rows {
            let (job_id, resolution) = row
                .map_err(|error| RuntimeError::from_sql(error, "decode Workspace marker Job"))?;
            digest.update(b"J\0");
            digest.update(job_id.as_bytes());
            digest.update(b"\0");
            if let Some(resolution) = resolution {
                digest.update(resolution.as_bytes());
            }
            digest.update(b"\0");
        }
        let mut statement = connection
            .prepare(
                "SELECT attempts.attempt_id FROM attempts JOIN jobs ON jobs.job_id=attempts.job_id WHERE jobs.workspace_id=?1 ORDER BY attempts.attempt_id",
            )
            .map_err(|error| RuntimeError::from_sql(error, "prepare Workspace marker Attempts"))?;
        let rows = statement
            .query_map([workspace_id], |row| row.get::<_, String>(0))
            .map_err(|error| RuntimeError::from_sql(error, "query Workspace marker Attempts"))?;
        let digest = digests.entry(workspace_id.to_string()).or_default();
        for row in rows {
            let attempt_id = row
                .map_err(|error| RuntimeError::from_sql(error, "decode Workspace marker Attempt"))?;
            digest.update(b"A\0");
            digest.update(attempt_id.as_bytes());
            digest.update(b"\0");
        }
    } else {
        let mut statement = connection
            .prepare("SELECT workspace_id,job_id,resolution FROM jobs ORDER BY workspace_id,job_id")
            .map_err(|error| RuntimeError::from_sql(error, "prepare Registry marker Jobs"))?;
        let rows = statement
            .query_map([], |row| {
                Ok((
                    row.get::<_, String>(0)?,
                    row.get::<_, String>(1)?,
                    row.get::<_, Option<String>>(2)?,
                ))
            })
            .map_err(|error| RuntimeError::from_sql(error, "query Registry marker Jobs"))?;
        for row in rows {
            let (workspace_id, job_id, resolution) = row
                .map_err(|error| RuntimeError::from_sql(error, "decode Registry marker Job"))?;
            let digest = digests.entry(workspace_id).or_default();
            digest.update(b"J\0");
            digest.update(job_id.as_bytes());
            digest.update(b"\0");
            if let Some(resolution) = resolution {
                digest.update(resolution.as_bytes());
            }
            digest.update(b"\0");
        }
        let mut statement = connection
            .prepare(
                "SELECT jobs.workspace_id,attempts.attempt_id FROM attempts JOIN jobs ON jobs.job_id=attempts.job_id ORDER BY jobs.workspace_id,attempts.attempt_id",
            )
            .map_err(|error| RuntimeError::from_sql(error, "prepare Registry marker Attempts"))?;
        let rows = statement
            .query_map([], |row| Ok((row.get::<_, String>(0)?, row.get::<_, String>(1)?)))
            .map_err(|error| RuntimeError::from_sql(error, "query Registry marker Attempts"))?;
        for row in rows {
            let (workspace_id, attempt_id) = row
                .map_err(|error| RuntimeError::from_sql(error, "decode Registry marker Attempt"))?;
            let digest = digests.entry(workspace_id).or_default();
            digest.update(b"A\0");
            digest.update(attempt_id.as_bytes());
            digest.update(b"\0");
        }
    }

    let workspaces = digests
        .into_iter()
        .map(|(workspace_id, digest)| RuntimeOperatorWorkspaceMarker {
            workspace_id,
            activity_marker: format!("sha256:{}", hex::encode(digest.finalize())),
        })
        .collect();
    Ok(RuntimeOperatorRegistryMarkersInspection {
        schema_version: RUNTIME_INSPECTION_SCHEMA_VERSION,
        generated_at_ms: now_ms()?,
        migration_version,
        workspaces,
    })
}

pub fn inspect_registry_activity(
    config: &RuntimeInspectionConfig,
) -> RuntimeResult<RuntimeOperatorRegistryActivityInspection> {
    let (connection, migration_version) = open_operator_read_only(config)?;
    validate_operator_registry_capabilities(&connection, true)?;
    let attempt_columns = registry_table_columns(&connection, "attempts")?;
    let rich_attempt_time = ["created_at_ms", "started_at_ms", "finished_at_ms"]
        .iter()
        .all(|column| attempt_columns.contains(*column));
    let sql = if rich_attempt_time {
        "SELECT jobs.workspace_id,MAX(CASE WHEN attempts.finished_at_ms IS NOT NULL THEN attempts.finished_at_ms WHEN attempts.started_at_ms IS NOT NULL THEN attempts.started_at_ms WHEN attempts.created_at_ms IS NOT NULL THEN attempts.created_at_ms ELSE jobs.created_at_ms END) FROM jobs LEFT JOIN attempts ON attempts.job_id=jobs.job_id GROUP BY jobs.workspace_id ORDER BY jobs.workspace_id"
    } else {
        "SELECT workspace_id,MAX(created_at_ms) FROM jobs GROUP BY workspace_id ORDER BY workspace_id"
    };
    let mut statement = connection
        .prepare(sql)
        .map_err(|error| RuntimeError::from_sql(error, "prepare Registry Workspace activity"))?;
    let rows = statement
        .query_map([], |row| {
            Ok(RuntimeOperatorWorkspaceLastActivity {
                workspace_id: row.get(0)?,
                last_activity_ms: row.get(1)?,
            })
        })
        .map_err(|error| RuntimeError::from_sql(error, "query Registry Workspace activity"))?;
    let workspaces = rows
        .map(|row| row.map_err(|error| RuntimeError::from_sql(error, "decode Registry Workspace activity")))
        .collect::<RuntimeResult<Vec<_>>>()?;
    Ok(RuntimeOperatorRegistryActivityInspection {
        schema_version: RUNTIME_INSPECTION_SCHEMA_VERSION,
        generated_at_ms: now_ms()?,
        migration_version,
        workspaces,
    })
}

pub fn inspect_registry_workspace_activity(
    config: &RuntimeInspectionConfig,
    workspace_id: &str,
) -> RuntimeResult<RuntimeOperatorWorkspaceActivityInspection> {
    crate::universal::validate_id(workspace_id, "workspaceId")
        .map_err(|error| RuntimeError::invalid(error.message, "workspaceId"))?;
    let (connection, migration_version) = open_operator_read_only(config)?;
    validate_operator_registry_capabilities(&connection, true)?;
    let mut active_job_ids = Vec::<String>::new();
    {
        let mut statement = connection
            .prepare(
                "SELECT jobs.job_id FROM jobs WHERE jobs.workspace_id=?1 AND (jobs.resolution IS NULL OR EXISTS(SELECT 1 FROM attempts JOIN concurrency_reservations ON concurrency_reservations.attempt_id=attempts.attempt_id WHERE attempts.job_id=jobs.job_id AND concurrency_reservations.state IN ('active','held_orphaned'))) ORDER BY jobs.created_at_ms DESC,jobs.job_id DESC",
            )
            .map_err(|error| RuntimeError::from_sql(error, "prepare active Workspace Jobs"))?;
        let rows = statement
            .query_map([workspace_id], |row| row.get::<_, String>(0))
            .map_err(|error| RuntimeError::from_sql(error, "query active Workspace Jobs"))?;
        for row in rows {
            active_job_ids.push(
                row.map_err(|error| RuntimeError::from_sql(error, "decode active Workspace Job"))?,
            );
        }
    }
    let attempt_columns = registry_table_columns(&connection, "attempts")?;
    let rich_attempt_time = ["created_at_ms", "started_at_ms", "finished_at_ms"]
        .iter()
        .all(|column| attempt_columns.contains(*column));
    let last_activity_sql = if rich_attempt_time {
        "SELECT MAX(CASE WHEN attempts.finished_at_ms IS NOT NULL THEN attempts.finished_at_ms WHEN attempts.started_at_ms IS NOT NULL THEN attempts.started_at_ms WHEN attempts.created_at_ms IS NOT NULL THEN attempts.created_at_ms ELSE jobs.created_at_ms END) FROM jobs LEFT JOIN attempts ON attempts.job_id=jobs.job_id WHERE jobs.workspace_id=?1"
    } else {
        "SELECT MAX(created_at_ms) FROM jobs WHERE workspace_id=?1"
    };
    let last_activity_ms = connection
        .query_row(last_activity_sql, [workspace_id], |row| {
            row.get::<_, Option<u64>>(0)
        })
        .map_err(|error| RuntimeError::from_sql(error, "query Workspace last activity"))?;

    let mut digest = Sha256::new();
    {
        let mut statement = connection
            .prepare("SELECT job_id,resolution FROM jobs WHERE workspace_id=?1 ORDER BY job_id")
            .map_err(|error| RuntimeError::from_sql(error, "prepare Workspace Job activity identity"))?;
        let rows = statement
            .query_map([workspace_id], |row| {
                Ok((row.get::<_, String>(0)?, row.get::<_, Option<String>>(1)?))
            })
            .map_err(|error| RuntimeError::from_sql(error, "query Workspace Job activity identity"))?;
        for row in rows {
            let (job_id, resolution) = row
                .map_err(|error| RuntimeError::from_sql(error, "decode Workspace Job activity identity"))?;
            digest.update(b"J\0");
            digest.update(job_id.as_bytes());
            digest.update(b"\0");
            if let Some(resolution) = resolution {
                digest.update(resolution.as_bytes());
            }
            digest.update(b"\0");
        }
    }
    {
        let mut statement = connection
            .prepare(
                "SELECT attempts.attempt_id FROM attempts JOIN jobs ON jobs.job_id=attempts.job_id WHERE jobs.workspace_id=?1 ORDER BY attempts.attempt_id",
            )
            .map_err(|error| RuntimeError::from_sql(error, "prepare Workspace Attempt activity identity"))?;
        let rows = statement
            .query_map([workspace_id], |row| row.get::<_, String>(0))
            .map_err(|error| RuntimeError::from_sql(error, "query Workspace Attempt activity identity"))?;
        for row in rows {
            let attempt_id = row.map_err(|error| {
                RuntimeError::from_sql(error, "decode Workspace Attempt activity identity")
            })?;
            digest.update(b"A\0");
            digest.update(attempt_id.as_bytes());
            digest.update(b"\0");
        }
    }

    Ok(RuntimeOperatorWorkspaceActivityInspection {
        schema_version: RUNTIME_INSPECTION_SCHEMA_VERSION,
        generated_at_ms: now_ms()?,
        migration_version,
        workspace: RuntimeOperatorWorkspaceActivity {
            workspace_id: workspace_id.to_string(),
            active_job_ids,
            last_activity_ms,
            activity_marker: format!("sha256:{}", hex::encode(digest.finalize())),
        },
    })
}

pub fn inspect_workspace(
    config: &RuntimeWorkspaceInspectionConfig,
    workspace_id: &str,
    job_limit: u32,
) -> RuntimeResult<RuntimeWorkspaceInspection> {
    if !config.store_root.is_absolute() {
        return Err(RuntimeError::invalid(
            "store root must be absolute",
            "storeRoot",
        ));
    }
    if job_limit == 0 || job_limit > MAX_WORKSPACE_INSPECTION_JOB_LIMIT {
        return Err(RuntimeError::invalid(
            format!("jobLimit must be in 1..={MAX_WORKSPACE_INSPECTION_JOB_LIMIT}"),
            "jobLimit",
        ));
    }
    crate::universal::validate_id(workspace_id, "workspaceId")
        .map_err(|error| RuntimeError::invalid(error.message, "workspaceId"))?;
    let (connection, migration_version) = open_read_only(&RuntimeInspectionConfig {
        db_path: config.db_path.clone(),
        busy_timeout_ms: config.busy_timeout_ms,
    })?;
    let executor = projection_executor(&config.store_root);
    let record = load_workspace_record(&executor, workspace_id).map_err(map_universal_error)?;
    let current_head_revision = workspace_head_revision_at(Path::new(&record.workspace_path))
        .map_err(map_universal_error)?;
    let changes = workspace_change_projection_at(Path::new(&record.workspace_path))
        .map_err(map_universal_error)?;
    let dirty = !changes.changed.is_empty() || !changes.untracked.is_empty();
    let active_job_ids = load_active_workspace_job_ids(&connection, workspace_id)?;
    let registry_store_root = config
        .db_path
        .parent()
        .ok_or_else(|| RuntimeError::invalid("database has no parent directory", "database"))?;
    let (recent_jobs, recent_jobs_truncated) = load_recent_workspace_jobs(
        &connection,
        registry_store_root,
        workspace_id,
        job_limit,
        migration_version,
    )?;
    Ok(RuntimeWorkspaceInspection {
        schema_version: RUNTIME_INSPECTION_SCHEMA_VERSION,
        generated_at_ms: now_ms()?,
        migration_version,
        workspace_id: record.workspace_id,
        source_repo: record.source_repo,
        source_revision: record.source_revision,
        current_head_revision,
        dirty,
        changed_paths: changes.changed,
        modified_paths: changes.modified,
        added_paths: changes.added,
        deleted_paths: changes.deleted,
        renamed_paths: changes.renamed,
        untracked_paths: changes.untracked,
        active_job_ids,
        recent_jobs,
        recent_jobs_truncated,
    })
}

pub fn summarize_experience(
    config: &RuntimeInspectionConfig,
    since_ms: u64,
) -> RuntimeResult<RuntimeExperienceSummary> {
    let (connection, migration_version) = open_read_only(config)?;
    let jobs_total = count(
        &connection,
        "SELECT COUNT(*) FROM jobs WHERE created_at_ms>=?1",
        since_ms,
        "count summary Jobs",
    )?;
    let jobs_unresolved = count(
        &connection,
        "SELECT COUNT(*) FROM jobs WHERE created_at_ms>=?1 AND resolution IS NULL",
        since_ms,
        "count unresolved summary Jobs",
    )?;
    let recovery_required_summary_sql = if migration_version
        >= CONDITION_RETIREMENT_MIGRATION_VERSION
    {
        "SELECT COUNT(DISTINCT j.job_id) FROM jobs j JOIN attempts a ON a.job_id=j.job_id WHERE j.created_at_ms>=?1 AND a.recovery_required=1"
    } else {
        "SELECT COUNT(DISTINCT j.job_id) FROM jobs j JOIN attempts a ON a.job_id=j.job_id JOIN attempt_conditions c ON c.attempt_id=a.attempt_id WHERE j.created_at_ms>=?1 AND c.condition_type='recovery_required' AND c.status='true'"
    };
    let jobs_recovery_required = count(
        &connection,
        recovery_required_summary_sql,
        since_ms,
        "count recovery-required summary Jobs",
    )?;
    let jobs_capacity_held = count(
        &connection,
        "SELECT COUNT(DISTINCT j.job_id) FROM jobs j JOIN attempts a ON a.job_id=j.job_id JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id WHERE j.created_at_ms>=?1 AND r.state!='released'",
        since_ms,
        "count capacity-held summary Jobs",
    )?;
    let converged_summary_sql = if migration_version >= CONDITION_RETIREMENT_MIGRATION_VERSION {
        "SELECT COUNT(*) FROM jobs j WHERE j.created_at_ms>=?1 AND j.resolution IS NOT NULL AND NOT EXISTS(SELECT 1 FROM attempts a WHERE a.job_id=j.job_id AND a.state NOT IN ('succeeded','failed','timed_out','cancelled','lost','orphaned')) AND NOT EXISTS(SELECT 1 FROM attempts a JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id WHERE a.job_id=j.job_id AND r.state!='released') AND NOT EXISTS(SELECT 1 FROM attempts a WHERE a.job_id=j.job_id AND a.recovery_required=1)"
    } else {
        "SELECT COUNT(*) FROM jobs j WHERE j.created_at_ms>=?1 AND j.resolution IS NOT NULL AND NOT EXISTS(SELECT 1 FROM attempts a WHERE a.job_id=j.job_id AND a.state NOT IN ('succeeded','failed','timed_out','cancelled','lost','orphaned')) AND NOT EXISTS(SELECT 1 FROM attempts a JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id WHERE a.job_id=j.job_id AND r.state!='released') AND NOT EXISTS(SELECT 1 FROM attempts a JOIN attempt_conditions c ON c.attempt_id=a.attempt_id WHERE a.job_id=j.job_id AND c.condition_type='recovery_required' AND c.status='true')"
    };
    let jobs_converged = count(
        &connection,
        converged_summary_sql,
        since_ms,
        "count converged summary Jobs",
    )?;

    let resolutions = grouped_counts(
        &connection,
        "SELECT COALESCE(resolution,'unresolved'),COUNT(*) FROM jobs WHERE created_at_ms>=?1 GROUP BY COALESCE(resolution,'unresolved') ORDER BY 1",
        since_ms,
        "group Job resolutions",
    )?;
    let attempts = grouped_counts(
        &connection,
        "SELECT a.state,COUNT(*) FROM attempts a JOIN jobs j ON j.job_id=a.job_id WHERE j.created_at_ms>=?1 GROUP BY a.state ORDER BY a.state",
        since_ms,
        "group Attempt states",
    )?;
    let reservations = grouped_counts(
        &connection,
        "SELECT r.state,COUNT(*) FROM concurrency_reservations r JOIN attempts a ON a.attempt_id=r.attempt_id JOIN jobs j ON j.job_id=a.job_id WHERE j.created_at_ms>=?1 GROUP BY r.state ORDER BY r.state",
        since_ms,
        "group reservation states",
    )?;

    let recovery_failures = count(
        &connection,
        "SELECT COUNT(DISTINCT e.job_id) FROM job_events e JOIN jobs j ON j.job_id=e.job_id WHERE j.created_at_ms>=?1 AND e.event_type='RECONCILIATION_FAILED'",
        since_ms,
        "count Jobs with reconciliation failure",
    )?;
    let automatic_recoveries = count(
        &connection,
        "SELECT COUNT(*) FROM jobs j WHERE j.created_at_ms>=?1 AND EXISTS(SELECT 1 FROM job_events failure WHERE failure.job_id=j.job_id AND failure.event_type='RECONCILIATION_FAILED') AND EXISTS(SELECT 1 FROM job_events recovery WHERE recovery.job_id=j.job_id AND recovery.event_type IN ('RECONCILIATION_CONVERGED','RUNNER_RESULT_RECOVERED','JOB_RESOLUTION_CORRECTED') AND recovery.event_sequence>(SELECT MIN(failure.event_sequence) FROM job_events failure WHERE failure.job_id=j.job_id AND failure.event_type='RECONCILIATION_FAILED')) AND NOT EXISTS(SELECT 1 FROM job_events repair WHERE repair.job_id=j.job_id AND repair.event_type='ADMIN_TERMINAL_REPAIR')",
        since_ms,
        "count automatically recovered Jobs",
    )?;
    let admin_repairs = count(
        &connection,
        "SELECT COUNT(DISTINCT e.job_id) FROM job_events e JOIN jobs j ON j.job_id=e.job_id WHERE j.created_at_ms>=?1 AND e.event_type='ADMIN_TERMINAL_REPAIR'",
        since_ms,
        "count administratively repaired Jobs",
    )?;

    let dispatches = count(
        &connection,
        "SELECT COUNT(*) FROM job_events e JOIN jobs j ON j.job_id=e.job_id WHERE j.created_at_ms>=?1 AND e.event_type='DISPATCH_ISSUED'",
        since_ms,
        "count dispatch events",
    )?;
    let (jobs_with_duplicate_dispatch, duplicate_dispatches): (u64, u64) = connection
        .query_row(
            "SELECT COUNT(*),COALESCE(SUM(extra),0) FROM (SELECT e.job_id,e.attempt_id,COUNT(*)-1 extra FROM job_events e JOIN jobs j ON j.job_id=e.job_id WHERE j.created_at_ms>=?1 AND e.event_type='DISPATCH_ISSUED' GROUP BY e.job_id,e.attempt_id HAVING COUNT(*)>1)",
            [since_ms],
            |row| Ok((row.get(0)?, row.get(1)?)),
        )
        .map_err(|error| RuntimeError::from_sql(error, "summarize duplicate dispatches"))?;

    let cancellation_requested = count(
        &connection,
        "SELECT COUNT(*) FROM jobs WHERE created_at_ms>=?1 AND desired_state='cancelled'",
        since_ms,
        "count cancellation requests",
    )?;
    let cancellation_cancelled = count(
        &connection,
        "SELECT COUNT(*) FROM jobs WHERE created_at_ms>=?1 AND desired_state='cancelled' AND resolution='cancelled'",
        since_ms,
        "count cancelled resolutions",
    )?;
    let cancellation_other = count(
        &connection,
        "SELECT COUNT(*) FROM jobs WHERE created_at_ms>=?1 AND desired_state='cancelled' AND resolution IS NOT NULL AND resolution!='cancelled'",
        since_ms,
        "count cancellation races resolved otherwise",
    )?;
    let cancellation_unresolved = cancellation_requested
        .saturating_sub(cancellation_cancelled)
        .saturating_sub(cancellation_other);

    let mechanical_latency = collect_mechanical_latency_samples(&connection, since_ms)?;

    let mut durations: Vec<u64> = Vec::new();
    let mut statement = connection
        .prepare(
            "SELECT a.finished_at_ms-j.created_at_ms FROM jobs j JOIN attempts a ON a.job_id=j.job_id WHERE j.created_at_ms>=?1 AND a.attempt_number=(SELECT MAX(latest.attempt_number) FROM attempts latest WHERE latest.job_id=j.job_id) AND a.finished_at_ms IS NOT NULL ORDER BY 1",
        )
        .map_err(|error| RuntimeError::from_sql(error, "prepare Job duration summary"))?;
    let rows = statement
        .query_map([since_ms], |row| row.get(0))
        .map_err(|error| RuntimeError::from_sql(error, "query Job durations"))?;
    for row in rows {
        durations.push(row.map_err(|error| RuntimeError::from_sql(error, "decode Job duration"))?);
    }

    let (artifact_count, artifact_bytes, truncated_artifacts): (u64, u64, u64) = connection
        .query_row(
            "SELECT COUNT(*),COALESCE(SUM(ar.byte_length),0),COALESCE(SUM(ar.truncated),0) FROM artifacts ar JOIN jobs j ON j.job_id=ar.job_id WHERE j.created_at_ms>=?1",
            [since_ms],
            |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?)),
        )
        .map_err(|error| RuntimeError::from_sql(error, "summarize Runtime Artifacts"))?;

    let event_types = grouped_counts(
        &connection,
        "SELECT e.event_type,COUNT(*) FROM job_events e JOIN jobs j ON j.job_id=e.job_id WHERE j.created_at_ms>=?1 GROUP BY e.event_type ORDER BY e.event_type",
        since_ms,
        "group Runtime event types",
    )?;
    let terminal_reasons = grouped_counts(
        &connection,
        "SELECT e.reason_code,COUNT(*) FROM job_events e JOIN jobs j ON j.job_id=e.job_id WHERE j.created_at_ms>=?1 AND e.event_type='JOB_TERMINAL' GROUP BY e.reason_code ORDER BY e.reason_code",
        since_ms,
        "group terminal reasons",
    )?;

    Ok(RuntimeExperienceSummary {
        schema_version: RUNTIME_INSPECTION_SCHEMA_VERSION,
        generated_at_ms: now_ms()?,
        migration_version,
        since_ms,
        jobs: RuntimeExperienceJobSummary {
            total: jobs_total,
            converged: jobs_converged,
            unresolved: jobs_unresolved,
            recovery_required: jobs_recovery_required,
            capacity_held: jobs_capacity_held,
            convergence_rate_basis_points: rate_basis_points(jobs_converged, jobs_total),
        },
        resolutions,
        attempts,
        reservations,
        recovery: RuntimeExperienceRecoverySummary {
            jobs_with_reconciliation_failure: recovery_failures,
            jobs_with_automatic_recovery: automatic_recoveries,
            jobs_with_administrative_repair: admin_repairs,
            automatic_recovery_rate_basis_points: rate_basis_points(
                automatic_recoveries,
                recovery_failures,
            ),
        },
        dispatch: RuntimeExperienceDispatchSummary {
            dispatches,
            jobs_with_duplicate_dispatch,
            duplicate_dispatches,
        },
        cancellation: RuntimeExperienceCancellationSummary {
            requested: cancellation_requested,
            resolved_cancelled: cancellation_cancelled,
            resolved_other: cancellation_other,
            unresolved: cancellation_unresolved,
        },
        mechanical_latency_ms: RuntimeExperienceMechanicalLatencySummary {
            admission_to_dispatch: duration_summary(&mechanical_latency.admission_to_dispatch),
            dispatch_to_runner_bound: duration_summary(
                &mechanical_latency.dispatch_to_runner_bound,
            ),
            runner_bound_to_terminal: duration_summary(
                &mechanical_latency.runner_bound_to_terminal,
            ),
            cancellation_to_terminal: duration_summary(
                &mechanical_latency.cancellation_to_terminal,
            ),
            reconciliation_to_convergence: duration_summary(
                &mechanical_latency.reconciliation_to_convergence,
            ),
        },
        duration_ms: duration_summary(&durations),
        artifacts: RuntimeExperienceArtifactSummary {
            count: artifact_count,
            bytes: artifact_bytes,
            truncated: truncated_artifacts,
        },
        event_types,
        terminal_reasons,
        semantic_completion_evaluated: false,
    })
}

fn collect_mechanical_latency_samples(
    connection: &Connection,
    since_ms: u64,
) -> RuntimeResult<RuntimeMechanicalLatencySamples> {
    let mut statement = connection
        .prepare(
            "SELECT e.job_id,j.created_at_ms,e.event_type,e.observed_at_ms FROM job_events e JOIN jobs j ON j.job_id=e.job_id WHERE j.created_at_ms>=?1 ORDER BY e.job_id,e.event_sequence",
        )
        .map_err(|error| RuntimeError::from_sql(error, "prepare mechanical latency events"))?;
    let rows = statement
        .query_map([since_ms], |row| {
            Ok((
                row.get::<_, String>(0)?,
                row.get::<_, u64>(1)?,
                row.get::<_, String>(2)?,
                row.get::<_, u64>(3)?,
            ))
        })
        .map_err(|error| RuntimeError::from_sql(error, "query mechanical latency events"))?;

    let mut samples = RuntimeMechanicalLatencySamples::default();
    let mut current_job: Option<String> = None;
    let mut state = RuntimeJobLatencyState::default();
    for row in rows {
        let (job_id, created_at_ms, event_type, observed_at_ms) =
            row.map_err(|error| RuntimeError::from_sql(error, "decode mechanical latency event"))?;
        if current_job.as_deref() != Some(job_id.as_str()) {
            if current_job.is_some() {
                append_job_latency_samples(&state, &mut samples);
            }
            current_job = Some(job_id);
            state = RuntimeJobLatencyState {
                created_at_ms,
                ..RuntimeJobLatencyState::default()
            };
        }
        match event_type.as_str() {
            "DISPATCH_ISSUED" => {
                state.dispatch_at_ms.get_or_insert(observed_at_ms);
            }
            "RUNNER_BOUND" => {
                state.runner_bound_at_ms.get_or_insert(observed_at_ms);
            }
            "STOP_REQUESTED" => {
                state.cancellation_at_ms.get_or_insert(observed_at_ms);
            }
            "RECONCILIATION_FAILED" => {
                state
                    .reconciliation_failed_at_ms
                    .get_or_insert(observed_at_ms);
            }
            "JOB_TERMINAL" => {
                state.terminal_at_ms.get_or_insert(observed_at_ms);
            }
            "RECONCILIATION_CONVERGED" | "RUNNER_RESULT_RECOVERED" | "JOB_RESOLUTION_CORRECTED" => {
                if let Some(failed_at_ms) = state.reconciliation_failed_at_ms.take() {
                    append_interval(
                        failed_at_ms,
                        Some(observed_at_ms),
                        &mut samples.reconciliation_to_convergence,
                    );
                }
            }
            _ => {}
        }
    }
    if current_job.is_some() {
        append_job_latency_samples(&state, &mut samples);
    }
    for values in [
        &mut samples.admission_to_dispatch,
        &mut samples.dispatch_to_runner_bound,
        &mut samples.runner_bound_to_terminal,
        &mut samples.cancellation_to_terminal,
        &mut samples.reconciliation_to_convergence,
    ] {
        values.sort_unstable();
    }
    Ok(samples)
}

fn append_job_latency_samples(
    state: &RuntimeJobLatencyState,
    samples: &mut RuntimeMechanicalLatencySamples,
) {
    append_interval(
        state.created_at_ms,
        state.dispatch_at_ms,
        &mut samples.admission_to_dispatch,
    );
    if let Some(dispatch_at_ms) = state.dispatch_at_ms {
        append_interval(
            dispatch_at_ms,
            state.runner_bound_at_ms,
            &mut samples.dispatch_to_runner_bound,
        );
    }
    if let Some(runner_bound_at_ms) = state.runner_bound_at_ms {
        append_interval(
            runner_bound_at_ms,
            state.terminal_at_ms,
            &mut samples.runner_bound_to_terminal,
        );
    }
    if let Some(cancellation_at_ms) = state.cancellation_at_ms {
        append_interval(
            cancellation_at_ms,
            state.terminal_at_ms,
            &mut samples.cancellation_to_terminal,
        );
    }
}

fn append_interval(start_ms: u64, end_ms: Option<u64>, values: &mut Vec<u64>) {
    if let Some(end_ms) = end_ms.filter(|end_ms| *end_ms >= start_ms) {
        values.push(end_ms - start_ms);
    }
}

fn duration_summary(values: &[u64]) -> RuntimeExperienceDurationSummary {
    RuntimeExperienceDurationSummary {
        samples: values.len() as u64,
        p50: percentile(values, 50),
        p95: percentile(values, 95),
        max: values.last().copied(),
    }
}

fn projection_executor(store_root: &Path) -> UniversalExecutorConfig {
    UniversalExecutorConfig {
        store_root: store_root.to_path_buf(),
        workspace_root: None,
        workspace_uid: None,
        workspace_gid: None,
        runner_path: Some(PathBuf::from("/usr/bin/true")),
        allowed_executable_roots: vec![PathBuf::from("/")],
        max_runtime_ms: 1,
        max_output_bytes: 1,
    }
}

fn load_active_workspace_job_ids(
    connection: &Connection,
    workspace_id: &str,
) -> RuntimeResult<Vec<String>> {
    let mut statement = connection
        .prepare(
            "SELECT DISTINCT jobs.job_id FROM jobs LEFT JOIN attempts ON attempts.job_id=jobs.job_id LEFT JOIN concurrency_reservations ON concurrency_reservations.attempt_id=attempts.attempt_id WHERE jobs.workspace_id=?1 AND (jobs.resolution IS NULL OR concurrency_reservations.state IN ('active','held_orphaned')) ORDER BY jobs.created_at_ms DESC,jobs.job_id DESC",
        )
        .map_err(|error| RuntimeError::from_sql(error, "prepare active Workspace Job inspection"))?;
    let rows = statement
        .query_map([workspace_id], |row| row.get::<_, String>(0))
        .map_err(|error| RuntimeError::from_sql(error, "query active Workspace Jobs"))?;
    rows.map(|row| {
        row.map_err(|error| RuntimeError::from_sql(error, "decode active Workspace Job"))
    })
    .collect()
}

fn load_recent_workspace_jobs(
    connection: &Connection,
    registry_store_root: &Path,
    workspace_id: &str,
    limit: u32,
    migration_version: i64,
) -> RuntimeResult<(Vec<RuntimeWorkspaceInspectionJob>, bool)> {
    let mut statement = connection
        .prepare(
            "SELECT job_id FROM jobs WHERE workspace_id=?1 ORDER BY created_at_ms DESC,job_id DESC LIMIT ?2",
        )
        .map_err(|error| RuntimeError::from_sql(error, "prepare recent Workspace Job inspection"))?;
    let rows = statement
        .query_map(params![workspace_id, limit + 1], |row| {
            row.get::<_, String>(0)
        })
        .map_err(|error| RuntimeError::from_sql(error, "query recent Workspace Jobs"))?;
    let mut job_ids = rows
        .map(|row| {
            row.map_err(|error| RuntimeError::from_sql(error, "decode recent Workspace Job"))
        })
        .collect::<RuntimeResult<Vec<_>>>()?;
    let truncated = job_ids.len() > limit as usize;
    job_ids.truncate(limit as usize);
    let observed_at_ms = now_ms()?;
    let mut jobs = Vec::with_capacity(job_ids.len());
    for job_id in job_ids {
        let job = RegistryStorageBoundary::load_job(connection, &job_id)?;
        let latest_attempt_id = connection
            .query_row(
                "SELECT attempt_id FROM attempts WHERE job_id=?1 ORDER BY attempt_number DESC LIMIT 1",
                [&job.job_id],
                |row| row.get::<_, String>(0),
            )
            .optional()
            .map_err(|error| RuntimeError::from_sql(error, "query latest Workspace Job Attempt"))?;
        let attempt_id = job
            .current_attempt_id
            .as_ref()
            .or(latest_attempt_id.as_ref());
        let attempt = attempt_id
            .map(|attempt_id| RegistryStorageBoundary::load_attempt(connection, attempt_id))
            .transpose()?;
        let recovery_required = if let Some(attempt) = attempt.as_ref() {
            let recovery_sql = if migration_version >= CONDITION_RETIREMENT_MIGRATION_VERSION {
                "SELECT COALESCE(recovery_required,0) FROM attempts WHERE attempt_id=?1"
            } else {
                "SELECT EXISTS(SELECT 1 FROM attempt_conditions WHERE attempt_id=?1 AND condition_type='recovery_required' AND status='true')"
            };
            let condition: bool = connection
                .query_row(recovery_sql, [&attempt.attempt_id], |row| row.get(0))
                .map_err(|error| {
                    RuntimeError::from_sql(error, "inspect Workspace Job recovery state")
                })?;
            condition
                || matches!(
                    attempt.state,
                    AttemptState::Recovering | AttemptState::Orphaned
                )
        } else {
            false
        };
        let artifact_count: u64 = connection
            .query_row(
                "SELECT COUNT(*) FROM artifacts WHERE job_id=?1",
                [&job.job_id],
                |row| row.get(0),
            )
            .map_err(|error| RuntimeError::from_sql(error, "count Workspace Job Artifacts"))?;
        let (progress, last_output_at_ms) = if let Some(attempt) = attempt.as_ref() {
            let expected_bundle = registry_store_root
                .join("attempts")
                .join(&attempt.attempt_id);
            if Path::new(&attempt.bundle_path) != expected_bundle {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "Attempt bundle path is outside the canonical Runtime store",
                    Some("bundlePath"),
                    false,
                ));
            }
            (
                load_runner_progress_if_present(attempt)?,
                latest_output_modified_ms(attempt)?,
            )
        } else {
            (None, None)
        };
        let duration_start = attempt
            .as_ref()
            .and_then(|attempt| attempt.started_at_ms)
            .unwrap_or(job.created_at_ms);
        let duration_end = attempt
            .as_ref()
            .and_then(|attempt| attempt.finished_at_ms)
            .unwrap_or(observed_at_ms);
        jobs.push(RuntimeWorkspaceInspectionJob {
            created_at_ms: job.created_at_ms,
            client_request_id: job.client_request_id,
            job_id: job.job_id,
            attempt_id: attempt.as_ref().map(|attempt| attempt.attempt_id.clone()),
            attempt_state: attempt.as_ref().map(|attempt| attempt.state),
            execution_disposition: job.resolution,
            recovery_required,
            duration_ms: duration_end.saturating_sub(duration_start),
            last_output_at_ms,
            progress_revision: progress.as_ref().map(|progress| progress.revision),
            current_step_id: progress
                .as_ref()
                .and_then(|progress| progress.current_step_id.clone()),
            current_step_index: progress
                .as_ref()
                .and_then(|progress| progress.current_step_index),
            current_step_elapsed_ms: progress.as_ref().and_then(|progress| {
                progress
                    .current_step_started_unix_ms
                    .and_then(|started| u64::try_from(started).ok())
                    .map(|started| observed_at_ms.saturating_sub(started))
            }),
            failed_step_id: progress
                .as_ref()
                .and_then(|progress| progress.failed_step_id.clone()),
            failed_step_index: progress
                .as_ref()
                .and_then(|progress| progress.failed_step_index),
            artifact_count,
        });
    }
    Ok((jobs, truncated))
}

fn grouped_counts(
    connection: &Connection,
    sql: &str,
    since_ms: u64,
    context: &str,
) -> RuntimeResult<BTreeMap<String, u64>> {
    let mut statement = connection
        .prepare(sql)
        .map_err(|error| RuntimeError::from_sql(error, context))?;
    let rows = statement
        .query_map([since_ms], |row| {
            Ok((row.get::<_, String>(0)?, row.get::<_, u64>(1)?))
        })
        .map_err(|error| RuntimeError::from_sql(error, context))?;
    let mut counts = BTreeMap::new();
    for row in rows {
        let (key, value) = row.map_err(|error| RuntimeError::from_sql(error, context))?;
        counts.insert(key, value);
    }
    Ok(counts)
}

fn count(connection: &Connection, sql: &str, since_ms: u64, context: &str) -> RuntimeResult<u64> {
    connection
        .query_row(sql, [since_ms], |row| row.get(0))
        .map_err(|error| RuntimeError::from_sql(error, context))
}

fn rate_basis_points(numerator: u64, denominator: u64) -> u64 {
    numerator
        .saturating_mul(10_000)
        .checked_div(denominator)
        .unwrap_or(0)
}

fn percentile(sorted: &[u64], percentile: usize) -> Option<u64> {
    if sorted.is_empty() {
        return None;
    }
    let rank = percentile.saturating_mul(sorted.len()).div_ceil(100);
    sorted.get(rank.saturating_sub(1)).copied()
}

include!("operator/archive.rs");
