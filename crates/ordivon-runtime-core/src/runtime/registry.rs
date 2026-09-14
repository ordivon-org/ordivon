use rusqlite::{
    params, Connection, OpenFlags, OptionalExtension, Transaction, TransactionBehavior,
};
use sha2::{Digest, Sha256};
use std::fs::{self, File, OpenOptions};
use std::os::unix::fs::OpenOptionsExt;
use std::os::unix::fs::PermissionsExt;
use std::path::{Path, PathBuf};
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use uuid::Uuid;

#[cfg(feature = "operator-tools")]
use super::repair::{AdminRepairAudit, AdminRepairOperation};
use super::supervisor::{validate_attempt_supervisor_owner, AttemptSupervisorOwner};
use super::{
    operation_request_identity_digest_from_plan, validate_client_request_id, AdmissionOutcome,
    ArtifactRegistration, AttemptRecord, AttemptState, AttemptTerminationIntent, CreatedAdmission,
    ExecutionProviderContract, ExecutionProviderSnapshot, HostDependencyBinding, JobDesiredState,
    JobProjection, JobResolution, ReservationRecord, ReservationState, RunnerIdentity,
    RuntimeArtifactRecord, RuntimeDeliveryDisposition, RuntimeError, RuntimeErrorCode,
    RuntimeExecutionPlan, RuntimeInvariantViolation, RuntimeJobListCursor, RuntimeJobListRequest,
    RuntimeJobListResult, RuntimeJobRecord, RuntimeJobSummary, RuntimeReleaseContract,
    RuntimeReleaseEffectBinding, RuntimeResult, SubmitRequest, TerminalCommit,
    MAX_RUNTIME_LIST_LIMIT, RUNTIME_SCHEMA_VERSION,
};

const MIGRATION_V1: i64 = 1;
const MIGRATION_V1_NAME: &str = "0001_runtime";
const MIGRATION_V1_SQL: &str = include_str!("../../migrations/runtime/0001_runtime.sql");
pub const RUNTIME_MIGRATION_CHECKSUM: &str =
    "sha256:9c5e0ccf94b0c3efa9b671a9300cfe00e4539d0c880e6a8df8982df9fa8826ac";
const MIGRATION_V2: i64 = 2;
const MIGRATION_V2_NAME: &str = "0002_orphan_recovery";
const MIGRATION_V2_SQL: &str = include_str!("../../migrations/runtime/0002_orphan_recovery.sql");
pub const RUNTIME_ORPHAN_RECOVERY_MIGRATION_CHECKSUM: &str =
    "sha256:08361881c9f589254e5e9fad089fcbf756bd8613352e995437fb7a616e9ce500";
const MIGRATION_V3: i64 = 3;
const MIGRATION_V3_NAME: &str = "0003_terminal_repair";
const MIGRATION_V3_SQL: &str = include_str!("../../migrations/runtime/0003_terminal_repair.sql");
pub const RUNTIME_TERMINAL_REPAIR_MIGRATION_CHECKSUM: &str =
    "sha256:464c9b769dacd10f7302d7a371f5b36a7553eda0b0b112bae35b901d00a67f0d";
const MIGRATION_V4: i64 = 4;
const MIGRATION_V4_NAME: &str = "0004_orphan_reclaim";
const MIGRATION_V4_SQL: &str = include_str!("../../migrations/runtime/0004_orphan_reclaim.sql");
pub const RUNTIME_ORPHAN_RECLAIM_MIGRATION_CHECKSUM: &str =
    "sha256:b76afbfaf70645b60456b08ad257e5ac2be1f63499f24a555cbf0157791e19ad";
pub(crate) const CONDITION_RETIREMENT_MIGRATION_VERSION: i64 = 5;
const MIGRATION_V5_NAME: &str = "0005_condition_retirement";
const MIGRATION_V5_SQL: &str =
    include_str!("../../migrations/runtime/0005_condition_retirement.sql");
pub const RUNTIME_CONDITION_RETIREMENT_MIGRATION_CHECKSUM: &str =
    "sha256:ae8e45dde797715492d383a01a1802c9a4d5a4c2f77042fe40379052eb06d097";
pub(crate) const MAX_MIGRATION_VERSION: i64 = 5;
const REDUNDANT_EVENT_SEQUENCE_INDEX: &str = "idx_events_job_sequence";
const DROP_REDUNDANT_EVENT_SEQUENCE_INDEX_SQL: &str =
    "DROP INDEX IF EXISTS idx_events_job_sequence";
const WORKSPACE_PATCH_STORAGE_SQL: &str = include_str!("workspace_patch_storage.sql");
const WORKSPACE_PATCH_TABLE: &str = "workspace_patch_operations";
const WORKSPACE_PATCH_INDEX: &str = "idx_workspace_patch_operations_workspace";
const EXECUTION_PROVIDER_STORAGE_SQL: &str = include_str!("execution_provider_storage.sql");
const EXECUTION_PROVIDER_TABLE: &str = "job_execution_providers";
const ATTEMPT_SUPERVISOR_OWNER_STORAGE_SQL: &str =
    include_str!("attempt_supervisor_owner_storage.sql");
const ATTEMPT_SUPERVISOR_OWNER_TABLE: &str = "attempt_supervisor_owners";
const HOST_DEPENDENCY_STORAGE_SQL: &str = include_str!("host_dependency_storage.sql");
const HOST_DEPENDENCY_TABLE: &str = "job_host_dependencies";
const RUNTIME_RELEASE_STORAGE_SQL: &str = include_str!("runtime_release_storage.sql");
const RUNTIME_RELEASE_TABLE: &str = "job_runtime_release_effects";
const RUNTIME_RELEASE_INDEX: &str = "idx_runtime_release_effect_request";
const JOB_CLIENT_REQUEST_LOOKUP_INDEX: &str = "idx_jobs_client_request_id_created";
const JOB_CLIENT_REQUEST_LOOKUP_INDEX_SQL: &str =
    "CREATE INDEX IF NOT EXISTS idx_jobs_client_request_id_created ON jobs(client_request_id, created_at_ms, job_id)";
const JOB_WORKSPACE_LOOKUP_INDEX: &str = "idx_jobs_workspace_created";
const JOB_WORKSPACE_LOOKUP_INDEX_SQL: &str =
    "CREATE INDEX IF NOT EXISTS idx_jobs_workspace_created ON jobs(workspace_id, created_at_ms, job_id)";
const ARTIFACT_JOB_LOOKUP_INDEX: &str = "idx_artifacts_job";
const ARTIFACT_JOB_LOOKUP_INDEX_SQL: &str =
    "CREATE INDEX IF NOT EXISTS idx_artifacts_job ON artifacts(job_id)";
const WORKSPACE_EXECUTION_LIMIT: u32 = 1;

#[cfg(test)]
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum TestCommitPoint {
    Admission,
    Cancel,
    Terminal,
}

#[cfg(test)]
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum TestCommitFault {
    CommitThenError,
    RollbackThenError,
    DeferredConstraint,
}

#[cfg(test)]
thread_local! {
    static TEST_COMMIT_FAULT: std::cell::RefCell<Option<(TestCommitPoint, TestCommitFault)>> = const {
        std::cell::RefCell::new(None)
    };
}

#[cfg(test)]
pub(crate) fn set_test_commit_fault(point: TestCommitPoint, fault: TestCommitFault) {
    TEST_COMMIT_FAULT.with(|slot| {
        let previous = slot.replace(Some((point, fault)));
        assert!(previous.is_none(), "test commit fault already armed");
    });
}

#[cfg(test)]
fn commit_with_test_fault(
    transaction: Transaction<'_>,
    point: TestCommitPoint,
) -> rusqlite::Result<()> {
    let fault = TEST_COMMIT_FAULT.with(|slot| {
        let mut slot = slot.borrow_mut();
        match *slot {
            Some((armed_point, fault)) if armed_point == point => {
                *slot = None;
                Some(fault)
            }
            _ => None,
        }
    });
    match fault {
        None => transaction.commit(),
        Some(TestCommitFault::CommitThenError) => {
            transaction.commit()?;
            Err(rusqlite::Error::InvalidQuery)
        }
        Some(TestCommitFault::RollbackThenError) => {
            transaction.rollback()?;
            Err(rusqlite::Error::InvalidQuery)
        }
        Some(TestCommitFault::DeferredConstraint) => {
            transaction.execute(
                "INSERT INTO idempotency_keys(principal,client_request_id,operation_digest,job_id,created_at_ms) VALUES('__test_fault__',?1,'__test_fault__','__missing_job__',0)",
                [format!("fault:{}", Uuid::now_v7())],
            )?;
            transaction.commit()
        }
    }
}

#[derive(Clone, Debug)]
pub struct RegistryConfig {
    pub db_path: PathBuf,
    pub store_root: PathBuf,
    pub busy_timeout_ms: u64,
}

#[derive(Clone, Debug)]
pub struct Registry {
    config: RegistryConfig,
}

#[derive(Clone, Debug)]
pub(crate) struct JobSnapshot {
    pub job: RuntimeJobRecord,
    pub attempt: Option<AttemptRecord>,
    pub projection: JobProjection,
}

#[derive(Clone, Debug)]
pub(super) struct PreallocatedAdmissionIds {
    pub job_id: String,
    pub attempt_id: String,
    pub reservation_id: String,
}

impl RegistryConfig {
    pub fn validate(&self) -> RuntimeResult<()> {
        if !self.db_path.is_absolute() {
            return Err(RuntimeError::invalid(
                "database path must be absolute",
                "dbPath",
            ));
        }
        if !self.store_root.is_absolute() {
            return Err(RuntimeError::invalid(
                "store root must be absolute",
                "storeRoot",
            ));
        }
        if self.busy_timeout_ms == 0 {
            return Err(RuntimeError::invalid(
                "busy timeout must be positive",
                "busyTimeoutMs",
            ));
        }
        Ok(())
    }

    pub fn attempts_root(&self) -> PathBuf {
        self.store_root.join("attempts")
    }

    pub fn attempt_path(&self, attempt_id: &str) -> PathBuf {
        self.attempts_root().join(attempt_id)
    }

    pub fn admission_fence_path(&self) -> PathBuf {
        self.store_root.join("admission.lock")
    }
}

fn capacity_holders(
    transaction: &Transaction<'_>,
    workspace_id: Option<&str>,
    limit: u32,
) -> RuntimeResult<(Vec<String>, Vec<String>)> {
    let mut statement = transaction
        .prepare(
            "SELECT DISTINCT j.job_id,j.workspace_id FROM concurrency_reservations r JOIN attempts a ON a.attempt_id=r.attempt_id JOIN jobs j ON j.job_id=a.job_id WHERE r.state IN ('active','held_orphaned') AND (?1 IS NULL OR j.workspace_id=?1) ORDER BY r.acquired_at_ms ASC,j.job_id ASC LIMIT ?2",
        )
        .map_err(|error| RuntimeError::from_sql(error, "cannot prepare capacity-holder query"))?;
    let rows = statement
        .query_map(params![workspace_id, limit], |row| {
            Ok((row.get::<_, String>(0)?, row.get::<_, String>(1)?))
        })
        .map_err(|error| RuntimeError::from_sql(error, "cannot query capacity holders"))?;
    let mut job_ids = Vec::new();
    let mut workspace_ids = Vec::new();
    for row in rows {
        let (job_id, holder_workspace_id) =
            row.map_err(|error| RuntimeError::from_sql(error, "cannot decode capacity holder"))?;
        job_ids.push(job_id);
        if !workspace_ids.contains(&holder_workspace_id) {
            workspace_ids.push(holder_workspace_id);
        }
    }
    Ok((job_ids, workspace_ids))
}

include!("registry/storage.rs");
include!("registry/admission.rs");
include!("registry/query.rs");
include!("registry/lifecycle.rs");
include!("registry/recovery.rs");
include!("registry/reconciliation.rs");
fn validate_migration_checksum(
    connection: &Connection,
    version: i64,
    expected: &str,
    label: &str,
) -> RuntimeResult<()> {
    let checksum: String = connection
        .query_row(
            "SELECT checksum FROM schema_migrations WHERE version=?1",
            [version],
            |row| row.get(0),
        )
        .optional()
        .map_err(|error| RuntimeError::from_sql(error, "cannot read migration checksum"))?
        .ok_or_else(|| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                format!("required {label} is missing"),
                None,
                false,
            )
        })?;
    if checksum != expected {
        return Err(RuntimeError::new(
            RuntimeErrorCode::MigrationChecksumMismatch,
            format!("{label} checksum does not match the compiled migration"),
            None,
            false,
        ));
    }
    Ok(())
}

fn safe_same_request_sql_error(error: rusqlite::Error, context: &str) -> RuntimeError {
    let mut mapped = RuntimeError::from_sql(error, context);
    if matches!(
        mapped.code,
        RuntimeErrorCode::RegistryUnavailable | RuntimeErrorCode::RegistryBusy
    ) {
        mapped.retryable = true;
    }
    mapped
}

fn unknown_commit_outcome(
    context: &str,
    commit_error: &RuntimeError,
    reconcile: Option<&RuntimeError>,
) -> RuntimeError {
    let suffix = reconcile
        .map(|error| {
            format!(
                "; reconciliation failed: {}: {}",
                error.code.as_str(),
                error.message
            )
        })
        .unwrap_or_default();
    RuntimeError::new(
        RuntimeErrorCode::DispatchOutcomeUnknown,
        format!("{context}: {}{suffix}", commit_error.message),
        None,
        true,
    )
}

fn committed_reconciliation(job_id: &str, context: &str) -> RuntimeError {
    RuntimeError::new(
        RuntimeErrorCode::ReconciliationRequired,
        context,
        None,
        true,
    )
    .with_operation_id(job_id.to_string())
}

fn immediate<'a>(connection: &'a mut Connection, context: &str) -> RuntimeResult<Transaction<'a>> {
    connection
        .transaction_with_behavior(TransactionBehavior::Immediate)
        .map_err(|error| safe_same_request_sql_error(error, &format!("cannot begin {context}")))
}

struct RawJob {
    job_id: String,
    principal: String,
    client_request_id: String,
    request_digest: String,
    operation_digest: String,
    workspace_id: String,
    workspace_snapshot_json: String,
    execution_plan_json: String,
    execution_plan_digest: String,
    created_at_ms: u64,
    desired_state: String,
    resolution: Option<String>,
    current_attempt_id: Option<String>,
    row_version: u64,
}

impl RawJob {
    fn into_record(self) -> RuntimeResult<RuntimeJobRecord> {
        Ok(RuntimeJobRecord {
            job_id: self.job_id,
            principal: self.principal,
            client_request_id: self.client_request_id,
            request_digest: self.request_digest,
            operation_digest: self.operation_digest,
            workspace_id: self.workspace_id,
            workspace_snapshot_json: self.workspace_snapshot_json,
            execution_plan_json: self.execution_plan_json,
            execution_plan_digest: self.execution_plan_digest,
            created_at_ms: self.created_at_ms,
            desired_state: JobDesiredState::parse(&self.desired_state)?,
            resolution: self
                .resolution
                .as_deref()
                .map(JobResolution::parse)
                .transpose()?,
            current_attempt_id: self.current_attempt_id,
            row_version: self.row_version,
        })
    }
}

fn raw_job_from_row(row: &rusqlite::Row<'_>) -> rusqlite::Result<RawJob> {
    Ok(RawJob {
        job_id: row.get(0)?,
        principal: row.get(1)?,
        client_request_id: row.get(2)?,
        request_digest: row.get(3)?,
        operation_digest: row.get(4)?,
        workspace_id: row.get(5)?,
        workspace_snapshot_json: row.get(6)?,
        execution_plan_json: row.get(7)?,
        execution_plan_digest: row.get(8)?,
        created_at_ms: row.get(9)?,
        desired_state: row.get(10)?,
        resolution: row.get(11)?,
        current_attempt_id: row.get(12)?,
        row_version: row.get(13)?,
    })
}

pub(crate) fn load_job(connection: &Connection, job_id: &str) -> RuntimeResult<RuntimeJobRecord> {
    connection
        .query_row(
            "SELECT job_id,principal,client_request_id,request_digest,operation_digest,workspace_id,workspace_snapshot_json,execution_plan_json,execution_plan_digest,created_at_ms,desired_state,resolution,current_attempt_id,row_version FROM jobs WHERE job_id=?1",
            [job_id],
            raw_job_from_row,
        )
        .optional()
        .map_err(|error| RuntimeError::from_sql(error, "cannot load Job"))?
        .ok_or_else(|| {
            RuntimeError::new(RuntimeErrorCode::JobNotFound, "Job not found", Some("jobId"), false)
        })?
        .into_record()
}

struct RawAttempt {
    attempt_id: String,
    job_id: String,
    attempt_number: u32,
    state: String,
    termination_intent: String,
    launch_token_digest: String,
    bundle_path: String,
    bundle_digest: Option<String>,
    boot_id: Option<String>,
    unit_name: String,
    invocation_id: Option<String>,
    control_group: Option<String>,
    main_pid: Option<u32>,
    process_start_identity: Option<String>,
    runner_start_digest: Option<String>,
    result_digest: Option<String>,
    exit_code: Option<i32>,
    infrastructure_error_digest: Option<String>,
    created_at_ms: u64,
    started_at_ms: Option<u64>,
    finished_at_ms: Option<u64>,
    row_version: u64,
}

impl RawAttempt {
    fn into_record(self) -> RuntimeResult<AttemptRecord> {
        Ok(AttemptRecord {
            attempt_id: self.attempt_id,
            job_id: self.job_id,
            attempt_number: self.attempt_number,
            state: AttemptState::parse(&self.state)?,
            termination_intent: AttemptTerminationIntent::parse(&self.termination_intent)?,
            launch_token_digest: self.launch_token_digest,
            bundle_path: self.bundle_path,
            bundle_digest: self.bundle_digest,
            boot_id: self.boot_id,
            unit_name: self.unit_name,
            invocation_id: self.invocation_id,
            control_group: self.control_group,
            main_pid: self.main_pid,
            process_start_identity: self.process_start_identity,
            runner_start_digest: self.runner_start_digest,
            result_digest: self.result_digest,
            exit_code: self.exit_code,
            infrastructure_error_digest: self.infrastructure_error_digest,
            created_at_ms: self.created_at_ms,
            started_at_ms: self.started_at_ms,
            finished_at_ms: self.finished_at_ms,
            row_version: self.row_version,
        })
    }
}

fn raw_attempt_from_row(row: &rusqlite::Row<'_>) -> rusqlite::Result<RawAttempt> {
    Ok(RawAttempt {
        attempt_id: row.get(0)?,
        job_id: row.get(1)?,
        attempt_number: row.get(2)?,
        state: row.get(3)?,
        termination_intent: row.get(4)?,
        launch_token_digest: row.get(5)?,
        bundle_path: row.get(6)?,
        bundle_digest: row.get(7)?,
        boot_id: row.get(8)?,
        unit_name: row.get(9)?,
        invocation_id: row.get(10)?,
        control_group: row.get(11)?,
        main_pid: row.get(12)?,
        process_start_identity: row.get(13)?,
        runner_start_digest: row.get(14)?,
        result_digest: row.get(15)?,
        exit_code: row.get(16)?,
        infrastructure_error_digest: row.get(17)?,
        created_at_ms: row.get(18)?,
        started_at_ms: row.get(19)?,
        finished_at_ms: row.get(20)?,
        row_version: row.get(21)?,
    })
}

pub(crate) fn load_attempt(
    connection: &Connection,
    attempt_id: &str,
) -> RuntimeResult<AttemptRecord> {
    connection
        .query_row(
            "SELECT attempt_id,job_id,attempt_number,state,termination_intent,launch_token_digest,bundle_path,bundle_digest,boot_id,unit_name,invocation_id,control_group,main_pid,process_start_identity,runner_start_digest,result_digest,exit_code,infrastructure_error_digest,created_at_ms,started_at_ms,finished_at_ms,row_version FROM attempts WHERE attempt_id=?1",
            [attempt_id],
            raw_attempt_from_row,
        )
        .optional()
        .map_err(|error| RuntimeError::from_sql(error, "cannot load Attempt"))?
        .ok_or_else(|| {
            RuntimeError::new(
                RuntimeErrorCode::AttemptNotFound,
                "Attempt not found",
                Some("attemptId"),
                false,
            )
        })?
        .into_record()
}

struct RawReservation {
    reservation_id: String,
    attempt_id: String,
    global_limit: u32,
    state: String,
    acquired_at_ms: u64,
    released_at_ms: Option<u64>,
    release_reason: Option<String>,
}

pub(crate) fn load_reservation(
    connection: &Connection,
    attempt_id: &str,
) -> RuntimeResult<ReservationRecord> {
    let raw = connection
        .query_row(
            "SELECT reservation_id,attempt_id,global_limit,state,acquired_at_ms,released_at_ms,release_reason FROM concurrency_reservations WHERE attempt_id=?1",
            [attempt_id],
            |row| {
                Ok(RawReservation {
                    reservation_id: row.get(0)?,
                    attempt_id: row.get(1)?,
                    global_limit: row.get(2)?,
                    state: row.get(3)?,
                    acquired_at_ms: row.get(4)?,
                    released_at_ms: row.get(5)?,
                    release_reason: row.get(6)?,
                })
            },
        )
        .optional()
        .map_err(|error| RuntimeError::from_sql(error, "cannot load reservation"))?
        .ok_or_else(|| {
            RuntimeError::new(
                RuntimeErrorCode::ReservationStateConflict,
                "Attempt has no reservation",
                Some("attemptId"),
                false,
            )
        })?;
    Ok(ReservationRecord {
        reservation_id: raw.reservation_id,
        attempt_id: raw.attempt_id,
        global_limit: raw.global_limit,
        state: ReservationState::parse(&raw.state)?,
        acquired_at_ms: raw.acquired_at_ms,
        released_at_ms: raw.released_at_ms,
        release_reason: raw.release_reason,
    })
}

#[allow(clippy::too_many_arguments)]
fn append_event(
    transaction: &Transaction<'_>,
    job_id: &str,
    attempt_id: Option<&str>,
    event_type: &str,
    origin: &str,
    previous_state: Option<AttemptState>,
    new_state: Option<AttemptState>,
    reason_code: &str,
    detail: serde_json::Value,
    observed_at_ms: u64,
) -> RuntimeResult<()> {
    let sequence: u64 = transaction
        .query_row(
            "SELECT COALESCE(MAX(event_sequence),0)+1 FROM job_events WHERE job_id=?1",
            [job_id],
            |row| row.get(0),
        )
        .map_err(|error| RuntimeError::from_sql(error, "cannot allocate event sequence"))?;
    let detail_json = serde_json::to_string(&detail).map_err(|error| {
        RuntimeError::new(
            RuntimeErrorCode::RegistryUnavailable,
            format!("cannot serialize event detail: {error}"),
            None,
            false,
        )
    })?;
    let detail_digest = sha256_bytes(detail_json.as_bytes());
    let event_id = format!("event-{}", Uuid::now_v7());
    transaction
        .execute(
            "INSERT INTO job_events(event_id,job_id,attempt_id,event_sequence,event_type,origin,previous_state,new_state,reason_code,detail_json,detail_digest,observed_at_ms) VALUES(?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11,?12)",
            params![
                event_id,
                job_id,
                attempt_id,
                sequence,
                event_type,
                origin,
                previous_state.map(AttemptState::as_db),
                new_state.map(AttemptState::as_db),
                reason_code,
                detail_json,
                detail_digest,
                observed_at_ms,
            ],
        )
        .map_err(|error| RuntimeError::from_sql(error, "cannot append Job event"))?;
    Ok(())
}

fn release_reservation(
    transaction: &Transaction<'_>,
    attempt_id: &str,
    released_at_ms: u64,
    reason: &str,
) -> RuntimeResult<()> {
    let changed = transaction
        .execute(
            "UPDATE concurrency_reservations SET state='released',released_at_ms=?1,release_reason=?2,state_observed_at_ms=?1 WHERE attempt_id=?3 AND state IN ('active','held_orphaned')",
            params![released_at_ms, reason, attempt_id],
        )
        .map_err(|error| RuntimeError::from_sql(error, "cannot release reservation"))?;
    if changed == 0 {
        let current: String = transaction
            .query_row(
                "SELECT state FROM concurrency_reservations WHERE attempt_id=?1",
                [attempt_id],
                |row| row.get(0),
            )
            .optional()
            .map_err(|error| RuntimeError::from_sql(error, "cannot inspect reservation state"))?
            .ok_or_else(|| {
                RuntimeError::new(
                    RuntimeErrorCode::ReservationStateConflict,
                    "reservation is missing",
                    Some("attemptId"),
                    false,
                )
            })?;
        if current != "released" {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ReservationStateConflict,
                format!("reservation cannot be released from {current}"),
                Some("attemptId"),
                false,
            ));
        }
    }
    Ok(())
}
fn hold_orphaned_reservation(
    transaction: &Transaction<'_>,
    attempt_id: &str,
    observed_at_ms: u64,
    reason: &str,
) -> RuntimeResult<()> {
    let changed = transaction
        .execute(
            "UPDATE concurrency_reservations SET state='held_orphaned',released_at_ms=NULL,release_reason=?1,state_observed_at_ms=?2 WHERE attempt_id=?3 AND state IN ('active','held_orphaned')",
            params![reason, observed_at_ms, attempt_id],
        )
        .map_err(|error| RuntimeError::from_sql(error, "cannot hold orphaned reservation"))?;
    if changed != 1 {
        return Err(RuntimeError::new(
            RuntimeErrorCode::ReservationStateConflict,
            "orphaned Attempt has no active reservation",
            Some("attemptId"),
            false,
        ));
    }
    Ok(())
}

#[cfg(feature = "operator-tools")]
fn repair_terminal_admin_transaction(
    transaction: &Transaction<'_>,
    request: &TerminalCommit,
    audit: &AdminRepairAudit,
) -> RuntimeResult<()> {
    validate_digest(&request.result_digest, "resultDigest")?;
    for artifact in &request.artifacts {
        validate_artifact_registration(artifact)?;
    }
    let attempt = load_attempt(transaction, &request.attempt_id)?;
    let job = load_job(transaction, &attempt.job_id)?;
    let reservation = load_reservation(transaction, &attempt.attempt_id)?;
    let runner_terminal = matches!(
        request.state,
        AttemptState::Succeeded
            | AttemptState::Failed
            | AttemptState::TimedOut
            | AttemptState::Cancelled
    );
    let allowed = (matches!(attempt.state, AttemptState::Lost | AttemptState::Orphaned)
        && runner_terminal)
        || (attempt.state == AttemptState::Lost && request.state == AttemptState::Lost);
    if !allowed {
        return Err(RuntimeError::new(
            RuntimeErrorCode::OrphanRemediationDenied,
            "administrative repair cannot rewrite this terminal state",
            Some("attemptId"),
            false,
        ));
    }
    let source_resolution = resolution_for_state(attempt.state)?;
    if attempt.row_version != request.expected_row_version
        || job.row_version != audit.expected_job_row_version
        || job.resolution != Some(source_resolution)
        || job.current_attempt_id != audit.expected_current_attempt_id
        || reservation.state != audit.expected_reservation_state
    {
        return Err(RuntimeError::new(
            RuntimeErrorCode::ReconciliationRequired,
            "Runtime state changed after the Doctor plan was created",
            Some("caseFingerprint"),
            false,
        ));
    }
    let changed = transaction
        .execute(
            "UPDATE attempts SET state=?1,result_digest=?2,exit_code=?3,infrastructure_error_digest=?4,finished_at_ms=?5,row_version=row_version+1 WHERE attempt_id=?6 AND row_version=?7 AND state=?8",
            params![
                request.state.as_db(),
                request.result_digest,
                request.exit_code,
                request.infrastructure_error_digest,
                request.finished_at_ms,
                request.attempt_id,
                request.expected_row_version,
                attempt.state.as_db(),
            ],
        )
        .map_err(|error| RuntimeError::from_sql(error, "cannot repair terminal Attempt"))?;
    if changed != 1 {
        return Err(state_conflict(
            "Attempt changed during administrative repair",
        ));
    }
    for artifact in &request.artifacts {
        transaction
            .execute(
                "INSERT INTO artifacts(artifact_id,job_id,attempt_id,kind,relative_path,digest,media_type,byte_length,truncated,created_at_ms) VALUES(?1,?2,?3,?4,?5,?6,?7,?8,?9,?10)",
                params![
                    artifact.artifact_id,
                    attempt.job_id,
                    attempt.attempt_id,
                    artifact.kind,
                    artifact.relative_path,
                    artifact.digest,
                    artifact.media_type,
                    artifact.byte_length,
                    i64::from(artifact.truncated),
                    request.finished_at_ms,
                ],
            )
            .map_err(|error| {
                RuntimeError::new(
                    RuntimeErrorCode::ArtifactIdentityConflict,
                    format!(
                        "cannot register administrative repair Artifact {}: {error}",
                        artifact.artifact_id
                    ),
                    Some("artifacts"),
                    false,
                )
            })?;
    }
    transaction
        .execute(
            "UPDATE attempts SET recovery_required=0,recovery_reason_code='ADMIN_REPAIR_COMPLETED',recovery_evidence_digest=?1,recovery_observed_at_ms=?2 WHERE attempt_id=?3",
            params![audit.case_fingerprint, audit.observed_at_ms, attempt.attempt_id],
        )
        .map_err(|error| RuntimeError::from_sql(error, "cannot record administrative recovery convergence"))?;
    release_reservation(
        transaction,
        &attempt.attempt_id,
        audit.observed_at_ms,
        "ADMIN_RUNTIME_REPAIR",
    )?;
    let resolution = resolution_for_state(request.state)?;
    let job_changed = transaction
        .execute(
            "UPDATE jobs SET resolution=?1,current_attempt_id=NULL,row_version=row_version+1 WHERE job_id=?2 AND row_version=?3",
            params![resolution.as_db(), attempt.job_id, audit.expected_job_row_version],
        )
        .map_err(|error| RuntimeError::from_sql(error, "cannot repair Job terminal state"))?;
    if job_changed != 1 {
        return Err(state_conflict("Job changed during administrative repair"));
    }
    let detail = serde_json::json!({
        "action": audit.action,
        "principal": audit.principal,
        "reportFingerprint": audit.report_fingerprint,
        "caseFingerprint": audit.case_fingerprint,
        "snapshotPath": audit.snapshot_path,
        "snapshotDigest": audit.snapshot_digest,
        "resultDigest": request.result_digest,
        "exitCode": request.exit_code,
    });
    append_event(
        transaction,
        &attempt.job_id,
        Some(&attempt.attempt_id),
        "ADMIN_TERMINAL_REPAIR",
        "SYSTEM_OBSERVED",
        Some(attempt.state),
        Some(request.state),
        &request.reason_code,
        detail.clone(),
        audit.observed_at_ms,
    )?;
    append_event(
        transaction,
        &attempt.job_id,
        Some(&attempt.attempt_id),
        "JOB_RESOLUTION_ADMIN_CORRECTED",
        "SYSTEM_DERIVED",
        Some(attempt.state),
        Some(request.state),
        &request.reason_code,
        detail,
        audit.observed_at_ms,
    )?;
    Ok(())
}

#[cfg(feature = "operator-tools")]
fn repair_terminal_reservation_admin_transaction(
    transaction: &Transaction<'_>,
    attempt_id: &str,
    expected_attempt_row_version: u64,
    audit: &AdminRepairAudit,
) -> RuntimeResult<()> {
    let attempt = load_attempt(transaction, attempt_id)?;
    let job = load_job(transaction, &attempt.job_id)?;
    let reservation = load_reservation(transaction, attempt_id)?;
    if attempt.row_version != expected_attempt_row_version
        || job.row_version != audit.expected_job_row_version
        || job.current_attempt_id != audit.expected_current_attempt_id
        || reservation.state != audit.expected_reservation_state
    {
        return Err(RuntimeError::new(
            RuntimeErrorCode::ReconciliationRequired,
            "Runtime state changed after the Doctor plan was created",
            Some("caseFingerprint"),
            false,
        ));
    }
    let target = terminal_reservation_target(&attempt, &job)?;
    if target == reservation.state {
        return Ok(());
    }
    if target == ReservationState::HeldOrphaned {
        hold_orphaned_reservation(
            transaction,
            attempt_id,
            audit.observed_at_ms,
            "ADMIN_RUNTIME_REPAIR",
        )?;
    } else {
        release_reservation(
            transaction,
            attempt_id,
            audit.observed_at_ms,
            "ADMIN_RUNTIME_REPAIR",
        )?;
    }
    append_event(
        transaction,
        &attempt.job_id,
        Some(attempt_id),
        "ADMIN_RESERVATION_REPAIR",
        "SYSTEM_OBSERVED",
        Some(attempt.state),
        Some(attempt.state),
        "ADMIN_RUNTIME_REPAIR",
        serde_json::json!({
            "action": audit.action,
            "principal": audit.principal,
            "reportFingerprint": audit.report_fingerprint,
            "caseFingerprint": audit.case_fingerprint,
            "snapshotPath": audit.snapshot_path,
            "snapshotDigest": audit.snapshot_digest,
            "previousReservationState": reservation.state.as_db(),
            "newReservationState": target.as_db(),
        }),
        audit.observed_at_ms,
    )?;
    Ok(())
}

fn terminal_reservation_target(
    attempt: &AttemptRecord,
    job: &RuntimeJobRecord,
) -> RuntimeResult<ReservationState> {
    if !attempt.state.is_terminal() {
        return Err(RuntimeError::new(
            RuntimeErrorCode::ReconciliationRequired,
            "Attempt is not terminal while repairing terminal reservation",
            Some("attemptId"),
            false,
        ));
    }
    let expected_resolution = resolution_for_state(attempt.state)?;
    let evidence_complete = attempt.result_digest.is_some()
        && attempt.finished_at_ms.is_some()
        && job.resolution == Some(expected_resolution)
        && job.current_attempt_id.is_none();
    if !evidence_complete {
        return Err(RuntimeError::new(
            RuntimeErrorCode::ReconciliationRequired,
            "terminal Attempt lacks complete result, Job resolution, or current-Attempt evidence",
            Some("attemptId"),
            false,
        ));
    }
    if attempt.state == AttemptState::Orphaned {
        Ok(ReservationState::HeldOrphaned)
    } else {
        Ok(ReservationState::Released)
    }
}

fn resolution_for_state(state: AttemptState) -> RuntimeResult<JobResolution> {
    match state {
        AttemptState::Succeeded => Ok(JobResolution::Succeeded),
        AttemptState::Failed => Ok(JobResolution::Failed),
        AttemptState::TimedOut => Ok(JobResolution::TimedOut),
        AttemptState::Cancelled => Ok(JobResolution::Cancelled),
        AttemptState::Lost => Ok(JobResolution::Lost),
        AttemptState::Orphaned => Ok(JobResolution::Orphaned),
        _ => Err(RuntimeError::invalid(
            "Attempt state is not terminal",
            "state",
        )),
    }
}

pub(crate) fn inspect_runtime_invariants_connection(
    connection: &Connection,
) -> RuntimeResult<Vec<RuntimeInvariantViolation>> {
    let mut violations = Vec::new();
    let mut collect = |sql: &str, code: &str, detail: &str| -> RuntimeResult<()> {
        let mut statement = connection
            .prepare(sql)
            .map_err(|error| RuntimeError::from_sql(error, "cannot prepare invariant query"))?;
        let rows = statement
            .query_map([], |row| {
                Ok((
                    row.get::<_, Option<String>>(0)?,
                    row.get::<_, Option<String>>(1)?,
                ))
            })
            .map_err(|error| RuntimeError::from_sql(error, "cannot query Runtime invariants"))?;
        for row in rows {
            let (job_id, attempt_id) =
                row.map_err(|error| RuntimeError::from_sql(error, "cannot decode invariant row"))?;
            violations.push(RuntimeInvariantViolation {
                code: code.to_string(),
                job_id,
                attempt_id,
                detail: detail.to_string(),
            });
        }
        Ok(())
    };
    collect(
        "SELECT job_id,NULL FROM jobs WHERE resolution IS NULL AND current_attempt_id IS NULL",
        "UNRESOLVED_JOB_WITHOUT_CURRENT_ATTEMPT",
        "unresolved Job must reference its current Attempt",
    )?;
    collect(
        "SELECT job_id,current_attempt_id FROM jobs WHERE resolution IS NOT NULL AND current_attempt_id IS NOT NULL",
        "RESOLVED_JOB_WITH_CURRENT_ATTEMPT",
        "resolved Job must not retain current_attempt_id",
    )?;
    collect(
        "SELECT j.job_id,a.attempt_id FROM jobs j JOIN attempts a ON a.attempt_id=j.current_attempt_id WHERE j.resolution IS NULL AND a.state IN ('succeeded','failed','timed_out','cancelled','lost','orphaned')",
        "UNRESOLVED_JOB_POINTS_TO_TERMINAL_ATTEMPT",
        "unresolved Job must not reference a terminal Attempt",
    )?;
    collect(
        "SELECT j.job_id,a.attempt_id FROM jobs j JOIN attempts a ON a.job_id=j.job_id WHERE j.resolution IS NOT NULL AND NOT EXISTS (SELECT 1 FROM attempts newer WHERE newer.job_id=a.job_id AND newer.attempt_number>a.attempt_number) AND ((j.resolution='succeeded' AND a.state!='succeeded') OR (j.resolution='failed' AND a.state!='failed') OR (j.resolution='timed_out' AND a.state!='timed_out') OR (j.resolution='cancelled' AND a.state!='cancelled') OR (j.resolution='lost' AND a.state!='lost') OR (j.resolution='orphaned' AND a.state!='orphaned'))",
        "JOB_RESOLUTION_ATTEMPT_STATE_MISMATCH",
        "resolved Job must agree with its latest terminal Attempt",
    )?;
    collect(
        "SELECT a.job_id,a.attempt_id FROM attempts a JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id WHERE a.state IN ('succeeded','failed','timed_out','cancelled','lost') AND r.state!='released'",
        "TERMINAL_ATTEMPT_HOLDS_RESERVATION",
        "non-orphan terminal Attempt must release its reservation",
    )?;
    collect(
        "SELECT a.job_id,a.attempt_id FROM attempts a JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id WHERE a.state='orphaned' AND r.state!='held_orphaned'",
        "ORPHAN_RESERVATION_NOT_HELD",
        "orphaned Attempt must hold its reservation",
    )?;
    collect(
        "SELECT job_id,attempt_id FROM attempts WHERE state IN ('succeeded','failed','timed_out','cancelled','lost','orphaned') AND (result_digest IS NULL OR finished_at_ms IS NULL)",
        "TERMINAL_ATTEMPT_MISSING_EVIDENCE",
        "terminal Attempt must retain result digest and finish time",
    )?;
    Ok(violations)
}

fn job_execution_reason_code(
    connection: &Connection,
    job_id: &str,
    resolved: bool,
) -> RuntimeResult<Option<String>> {
    if !resolved {
        return Ok(None);
    }
    connection
        .query_row(
            "SELECT reason_code FROM job_events WHERE job_id=?1 AND (event_type IN ('JOB_TERMINAL','JOB_RESOLUTION_CORRECTED','JOB_RESOLUTION_ADMIN_CORRECTED') OR (event_type='STOP_REQUESTED' AND new_state='cancelled')) ORDER BY event_sequence DESC LIMIT 1",
            [job_id],
            |row| row.get(0),
        )
        .optional()
        .map_err(|error| RuntimeError::from_sql(error, "cannot read Job execution reason"))
}

fn attempt_recovery_condition_active(
    connection: &Connection,
    attempt_id: &str,
) -> RuntimeResult<bool> {
    connection
        .query_row(
            "SELECT COALESCE(recovery_required,0) FROM attempts WHERE attempt_id=?1",
            [attempt_id],
            |row| row.get(0),
        )
        .map_err(|error| RuntimeError::from_sql(error, "cannot inspect Attempt recovery state"))
}

fn load_job_snapshot(connection: &Connection, job_id: &str) -> RuntimeResult<JobSnapshot> {
    let transaction = connection.unchecked_transaction().map_err(|error| {
        RuntimeError::from_sql(error, "cannot begin Job projection read snapshot")
    })?;
    let snapshot = load_job_snapshot_in(&transaction, job_id)?;
    transaction.commit().map_err(|error| {
        RuntimeError::from_sql(error, "cannot close Job projection read snapshot")
    })?;
    Ok(snapshot)
}

fn load_job_snapshot_in(connection: &Connection, job_id: &str) -> RuntimeResult<JobSnapshot> {
    let job = load_job(connection, job_id)?;
    let attempt = match job.current_attempt_id.as_deref() {
        Some(attempt_id) => Some(load_attempt(connection, attempt_id)?),
        None => {
            let attempt_id: Option<String> = connection
                .query_row(
                    "SELECT attempt_id FROM attempts WHERE job_id=?1 ORDER BY attempt_number DESC LIMIT 1",
                    [job_id],
                    |row| row.get(0),
                )
                .optional()
                .map_err(|error| RuntimeError::from_sql(error, "cannot find latest Attempt"))?;
            attempt_id
                .map(|attempt_id| load_attempt(connection, &attempt_id))
                .transpose()?
        }
    };
    let recovery_condition_active = attempt
        .as_ref()
        .map(|attempt| attempt_recovery_condition_active(connection, &attempt.attempt_id))
        .transpose()?
        .unwrap_or(false);
    let artifacts_available: bool = connection
        .query_row(
            "SELECT EXISTS(SELECT 1 FROM artifacts WHERE job_id=?1)",
            [&job.job_id],
            |row| row.get(0),
        )
        .map_err(|error| RuntimeError::from_sql(error, "cannot inspect Job Artifacts"))?;
    let execution_reason_code =
        job_execution_reason_code(connection, &job.job_id, job.resolution.is_some())?;
    let projection = project_job(
        &job,
        attempt.as_ref(),
        recovery_condition_active,
        artifacts_available,
        execution_reason_code,
    );
    Ok(JobSnapshot {
        job,
        attempt,
        projection,
    })
}

fn project_job(
    job: &RuntimeJobRecord,
    attempt: Option<&AttemptRecord>,
    recovery_condition_active: bool,
    artifacts_available: bool,
    execution_reason_code: Option<String>,
) -> JobProjection {
    let status = if let Some(resolution) = job.resolution {
        resolution.as_db().to_string()
    } else if let Some(attempt) = attempt {
        match attempt.state {
            AttemptState::Accepted | AttemptState::Starting => "queued".to_string(),
            AttemptState::Running | AttemptState::Stopping | AttemptState::Recovering => {
                "working".to_string()
            }
            terminal => terminal.as_db().to_string(),
        }
    } else {
        "unknown".to_string()
    };
    let execution_terminal = job.resolution.is_some();
    let recovery_required = recovery_condition_active
        || attempt.is_some_and(|attempt| {
            matches!(
                attempt.state,
                AttemptState::Recovering | AttemptState::Orphaned
            )
        });
    let delivery_disposition = if recovery_required {
        RuntimeDeliveryDisposition::ReconciliationRequired
    } else {
        match job.resolution {
            None => RuntimeDeliveryDisposition::InProgress,
            Some(JobResolution::Orphaned) => RuntimeDeliveryDisposition::ReconciliationRequired,
            Some(JobResolution::Lost) => RuntimeDeliveryDisposition::Unknown,
            Some(_) => RuntimeDeliveryDisposition::Committed,
        }
    };
    let poll_after_ms = matches!(
        delivery_disposition,
        RuntimeDeliveryDisposition::InProgress | RuntimeDeliveryDisposition::ReconciliationRequired
    )
    .then_some(250);
    JobProjection {
        job_id: job.job_id.clone(),
        operation_digest: job.operation_digest.clone(),
        status,
        desired_state: job.desired_state,
        attempt_id: attempt.map(|attempt| attempt.attempt_id.clone()),
        attempt_state: attempt.map(|attempt| attempt.state),
        termination_intent: attempt.map(|attempt| attempt.termination_intent),
        exit_code: attempt.and_then(|attempt| attempt.exit_code),
        execution_terminal,
        execution_disposition: job.resolution,
        execution_reason_code,
        delivery_disposition,
        recovery_required,
        semantic_completion_evaluated: false,
        result_available: job.resolution.is_some(),
        artifacts_available,
        artifacts: Vec::new(),
        poll_after_ms,
    }
}

fn job_request_identity_digest(job: &RuntimeJobRecord) -> RuntimeResult<String> {
    if job
        .request_digest
        .starts_with(super::REQUEST_IDENTITY_PREFIX)
        || job
            .request_digest
            .starts_with(super::PROPOSAL_IDENTITY_PREFIX)
        || job
            .request_digest
            .starts_with(super::INPUT_BOUND_IDENTITY_PREFIX)
        || job
            .request_digest
            .starts_with(super::INPUT_BOUND_PROPOSAL_IDENTITY_PREFIX)
        || job
            .request_digest
            .starts_with(super::RUNTIME_RELEASE_IDENTITY_PREFIX)
    {
        validate_request_identity_digest(&job.request_digest)?;
        return Ok(job.request_digest.clone());
    }
    let plan: RuntimeExecutionPlan =
        serde_json::from_str(&job.execution_plan_json).map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                format!("stored execution plan is invalid: {error}"),
                Some("executionPlan"),
                false,
            )
        })?;
    operation_request_identity_digest_from_plan(&plan)
}

fn validate_request_identity_digest(value: &str) -> RuntimeResult<()> {
    let digest = value
        .strip_prefix(super::REQUEST_IDENTITY_PREFIX)
        .or_else(|| value.strip_prefix(super::PROPOSAL_IDENTITY_PREFIX))
        .or_else(|| value.strip_prefix(super::INPUT_BOUND_IDENTITY_PREFIX))
        .or_else(|| value.strip_prefix(super::INPUT_BOUND_PROPOSAL_IDENTITY_PREFIX))
        .or_else(|| value.strip_prefix(super::RUNTIME_RELEASE_IDENTITY_PREFIX))
        .ok_or_else(|| {
            RuntimeError::invalid(
                "unsupported request identity digest",
                "requestIdentityDigest",
            )
        })?;
    validate_digest(digest, "requestIdentityDigest")
}

fn idempotency_conflict() -> RuntimeError {
    RuntimeError::new(
        RuntimeErrorCode::IdempotencyConflict,
        "clientRequestId is already bound to a different operation request",
        Some("clientRequestId"),
        false,
    )
}

fn validate_execution_provider_snapshot(
    snapshot: &ExecutionProviderSnapshot,
    field: &str,
) -> RuntimeResult<()> {
    validate_digest(
        &snapshot.executable_digest,
        &format!("{field}.executableDigest"),
    )?;
    match snapshot.contract {
        ExecutionProviderContract::LocalLinuxRunnerV1 => {
            if snapshot.wsl_distribution.is_some() {
                return Err(RuntimeError::invalid(
                    "local Linux execution provider cannot carry a WSL distribution",
                    &format!("{field}.wslDistribution"),
                ));
            }
        }
        ExecutionProviderContract::WindowsNativeLauncherV1 => {
            let distribution = snapshot.wsl_distribution.as_deref().ok_or_else(|| {
                RuntimeError::invalid(
                    "Windows execution provider requires a WSL distribution",
                    &format!("{field}.wslDistribution"),
                )
            })?;
            if distribution.is_empty()
                || !distribution
                    .bytes()
                    .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_' | b'.'))
            {
                return Err(RuntimeError::invalid(
                    "Windows execution provider has an invalid WSL distribution",
                    &format!("{field}.wslDistribution"),
                ));
            }
        }
    }
    Ok(())
}

fn validate_host_dependency_bindings(
    bindings: &[HostDependencyBinding],
    field: &str,
) -> RuntimeResult<()> {
    let mut previous_path: Option<&str> = None;
    for (index, binding) in bindings.iter().enumerate() {
        let binding_field = format!("{field}[{index}]");
        let path = Path::new(&binding.path);
        if !path.is_absolute() || binding.path.as_bytes().contains(&0) {
            return Err(RuntimeError::invalid(
                "Host Dependency path must be absolute and NUL-free",
                &format!("{binding_field}.path"),
            ));
        }
        validate_digest(
            &binding.expected_digest,
            &format!("{binding_field}.expectedDigest"),
        )?;
        if previous_path.is_some_and(|previous| previous >= binding.path.as_str()) {
            return Err(RuntimeError::invalid(
                "Host Dependencies must be sorted by unique path",
                field,
            ));
        }
        previous_path = Some(&binding.path);
    }
    Ok(())
}

fn validate_runtime_release_effect_binding(
    release: &RuntimeReleaseEffectBinding,
    request: &SubmitRequest,
) -> RuntimeResult<()> {
    if release.contract != RuntimeReleaseContract::RuntimeReleaseV1 {
        return Err(RuntimeError::invalid(
            "unsupported Runtime Release contract",
            "runtimeReleaseEffect.contract",
        ));
    }
    if release.effect_id.len() != 64
        || !release
            .effect_id
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
    {
        return Err(RuntimeError::invalid(
            "Runtime Release effectId must be 64 lowercase hexadecimal characters",
            "runtimeReleaseEffect.effectId",
        ));
    }
    if !release
        .request_digest
        .starts_with(super::RUNTIME_RELEASE_IDENTITY_PREFIX)
    {
        return Err(RuntimeError::invalid(
            "Runtime Release request digest has the wrong contract prefix",
            "runtimeReleaseEffect.requestDigest",
        ));
    }
    validate_request_identity_digest(&release.request_digest)?;
    if request.request_identity_digest.as_deref() != Some(release.request_digest.as_str()) {
        return Err(RuntimeError::invalid(
            "Runtime Release side truth must match the committed request identity",
            "runtimeReleaseEffect.requestDigest",
        ));
    }
    if release.workspace_id != request.plan.workspace_id {
        return Err(RuntimeError::invalid(
            "Runtime Release workspace does not match the execution plan",
            "runtimeReleaseEffect.workspaceId",
        ));
    }
    if release.commit.len() != 40
        || !release
            .commit
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
    {
        return Err(RuntimeError::invalid(
            "Runtime Release commit must be exactly 40 lowercase hexadecimal characters",
            "runtimeReleaseEffect.commit",
        ));
    }
    validate_digest(
        &release.candidate_manifest_digest,
        "runtimeReleaseEffect.candidateManifestDigest",
    )?;
    if !Path::new(&release.receipt_path).is_absolute()
        || release.receipt_path.as_bytes().contains(&0)
    {
        return Err(RuntimeError::invalid(
            "Runtime Release receipt path must be absolute and NUL-free",
            "runtimeReleaseEffect.receiptPath",
        ));
    }
    if request.plan.execution_target != super::ExecutionTarget::LocalLinux
        || request.plan.execution_profile != super::ExecutionProfile::TrustedLocal
    {
        return Err(RuntimeError::invalid(
            "Runtime Release v1 requires trusted_local local_linux execution",
            "runtimeReleaseEffect.contract",
        ));
    }
    if !matches!(
        request
            .execution_provider
            .as_ref()
            .map(|provider| provider.contract),
        Some(ExecutionProviderContract::LocalLinuxRunnerV1)
    ) {
        return Err(RuntimeError::invalid(
            "Runtime Release v1 requires a committed local Linux Runner",
            "executionProvider",
        ));
    }
    Ok(())
}

fn validate_submit(request: &SubmitRequest) -> RuntimeResult<()> {
    if request.schema_version != RUNTIME_SCHEMA_VERSION
        || request.plan.schema_version != RUNTIME_SCHEMA_VERSION
    {
        return Err(RuntimeError::invalid(
            "unsupported runtime schema version",
            "schemaVersion",
        ));
    }
    validate_client_request_id(&request.client_request_id, "clientRequestId")?;
    if let Some(digest) = request.request_identity_digest.as_deref() {
        validate_request_identity_digest(digest)?;
    }
    validate_identifier(&request.plan.principal, "plan.principal")?;
    validate_identifier(&request.plan.workspace_id, "plan.workspaceId")?;
    if request.global_limit == 0 {
        return Err(RuntimeError::invalid(
            "globalLimit must be positive",
            "globalLimit",
        ));
    }
    if let Some(provider) = request.execution_provider.as_ref() {
        validate_execution_provider_snapshot(provider, "executionProvider")?;
        let target_matches = matches!(
            (request.plan.execution_target, provider.contract),
            (
                super::ExecutionTarget::LocalLinux,
                ExecutionProviderContract::LocalLinuxRunnerV1
            ) | (
                super::ExecutionTarget::WindowsNative,
                ExecutionProviderContract::WindowsNativeLauncherV1
            )
        );
        if !target_matches {
            return Err(RuntimeError::invalid(
                "execution provider contract does not match execution target",
                "executionProvider.contract",
            ));
        }
    }
    validate_host_dependency_bindings(&request.host_dependencies, "hostDependencies")?;
    if !request.host_dependencies.is_empty() {
        if request.plan.execution_target != super::ExecutionTarget::LocalLinux
            || request.plan.execution_profile != super::ExecutionProfile::TrustedLocal
        {
            return Err(RuntimeError::invalid(
                "Host Dependencies require trusted_local local_linux execution",
                "hostDependencies",
            ));
        }
        if request.runtime_release_effect.is_some() {
            return Err(RuntimeError::invalid(
                "Host Dependencies cannot be attached to Runtime Release Jobs",
                "hostDependencies",
            ));
        }
        if !matches!(
            request
                .execution_provider
                .as_ref()
                .map(|provider| provider.contract),
            Some(ExecutionProviderContract::LocalLinuxRunnerV1)
        ) {
            return Err(RuntimeError::invalid(
                "Host Dependencies require a committed local Linux Runner",
                "executionProvider",
            ));
        }
    }
    if let Some(release) = request.runtime_release_effect.as_ref() {
        validate_runtime_release_effect_binding(release, request)?;
    } else if request
        .request_identity_digest
        .as_deref()
        .is_some_and(|digest| digest.starts_with(super::RUNTIME_RELEASE_IDENTITY_PREFIX))
    {
        return Err(RuntimeError::invalid(
            "Runtime Release request identity requires Runtime Release side truth",
            "runtimeReleaseEffect",
        ));
    }

    for (path, field) in [
        (&request.plan.workspace_path, "plan.workspacePath"),
        (&request.plan.executable, "plan.executable"),
        (&request.plan.cwd, "plan.cwd"),
    ] {
        if !Path::new(path).is_absolute() || path.as_bytes().contains(&0) {
            return Err(RuntimeError::invalid(
                format!("{field} must be an absolute NUL-free path"),
                field,
            ));
        }
    }
    if !Path::new(&request.plan.cwd).starts_with(&request.plan.workspace_path) {
        return Err(RuntimeError::invalid(
            "plan.cwd must remain inside workspacePath",
            "plan.cwd",
        ));
    }
    validate_digest(&request.plan.executable_digest, "plan.executableDigest")?;
    if let Some(digest) = request.plan.workspace_source_digest.as_deref() {
        validate_digest(digest, "plan.workspaceSourceDigest")?;
    }
    match (
        request.plan.input_set_id.as_deref(),
        request.plan.effective_inputs.is_empty(),
    ) {
        (None, true) => {}
        (Some(input_set_id), false) => {
            if input_set_id.len() != 64
                || !input_set_id.bytes().all(|byte| byte.is_ascii_hexdigit())
                || input_set_id.bytes().any(|byte| byte.is_ascii_uppercase())
            {
                return Err(RuntimeError::invalid(
                    "plan.inputSetId must be lowercase 32-byte SHA-256 hex",
                    "plan.inputSetId",
                ));
            }
            match request.plan.execution_target {
                super::ExecutionTarget::LocalLinux => {
                    // Immutable input identity/presentation is independent of the
                    // local Linux authority profile. Public admission decides whether
                    // contained_local or trusted_local is appropriate.
                }
                super::ExecutionTarget::WindowsNative => {
                    if request.plan.execution_profile != super::ExecutionProfile::TrustedLocal {
                        return Err(RuntimeError::invalid(
                            "windows_native effective inputs require trusted_local execution",
                            "plan.executionProfile",
                        ));
                    }
                    if request.plan.windows_authority != super::WindowsAuthority::Limited {
                        return Err(RuntimeError::invalid(
                            "windows_native effective inputs require limited authority",
                            "plan.windowsAuthority",
                        ));
                    }
                }
            }
        }
        (Some(_), true) => {
            return Err(RuntimeError::invalid(
                "plan.inputSetId requires effectiveInputs",
                "plan.inputSetId",
            ));
        }
        (None, false) => {
            return Err(RuntimeError::invalid(
                "effectiveInputs require plan.inputSetId",
                "plan.inputSetId",
            ));
        }
    }
    if request.plan.execution_target == super::ExecutionTarget::WindowsNative {
        super::windows::validate_windows_input_relative_paths(
            request
                .plan
                .effective_inputs
                .iter()
                .map(|input| input.presentation_relative_path.as_str()),
        )?;
    }
    let mut input_paths = std::collections::BTreeSet::<PathBuf>::new();
    for (index, input) in request.plan.effective_inputs.iter().enumerate() {
        validate_identifier(
            &input.authority,
            &format!("plan.effectiveInputs[{index}].authority"),
        )?;
        validate_digest(
            &input.digest,
            &format!("plan.effectiveInputs[{index}].digest"),
        )?;
        let object = Path::new(&input.relative_object);
        let presentation = Path::new(&input.presentation_relative_path);
        for (path, field) in [
            (
                object,
                format!("plan.effectiveInputs[{index}].relativeObject"),
            ),
            (
                presentation,
                format!("plan.effectiveInputs[{index}].presentationRelativePath"),
            ),
        ] {
            if path.is_absolute()
                || path.as_os_str().is_empty()
                || path
                    .components()
                    .any(|component| !matches!(component, std::path::Component::Normal(_)))
            {
                return Err(RuntimeError::invalid(
                    "effective input paths must contain only normal relative components",
                    &field,
                ));
            }
        }
        if request.plan.execution_target == super::ExecutionTarget::WindowsNative {
            super::windows::validate_windows_input_relative_path(
                &input.presentation_relative_path,
                index,
            )?;
        }
        for existing in &input_paths {
            if presentation == existing
                || presentation.starts_with(existing)
                || existing.starts_with(presentation)
            {
                return Err(RuntimeError::invalid(
                    "effective input presentation paths must not overlap",
                    &format!("plan.effectiveInputs[{index}].presentationRelativePath"),
                ));
            }
        }
        input_paths.insert(presentation.to_path_buf());
    }

    if request.plan.source_revision.is_empty() || request.plan.source_revision.len() > 256 {
        return Err(RuntimeError::invalid(
            "sourceRevision must be non-empty and bounded",
            "plan.sourceRevision",
        ));
    }
    if request.plan.timeout_ms == 0
        || request.plan.stdout_limit_bytes == 0
        || request.plan.stderr_limit_bytes == 0
    {
        return Err(RuntimeError::invalid(
            "runtime and output limits must be positive",
            "plan",
        ));
    }
    validate_plan_budget(&request.plan.budget)?;
    validate_exec_payload_for_plan(&request.plan.args, &request.plan.env, "plan")?;
    for (index, step) in request.plan.steps.iter().enumerate() {
        validate_exec_payload_for_plan(&step.args, &step.env, &format!("plan.steps[{index}]"))?;
    }
    Ok(())
}

fn validate_exec_payload_for_plan(
    args: &[String],
    env: &std::collections::BTreeMap<String, String>,
    field: &str,
) -> RuntimeResult<()> {
    crate::universal::validate_exec_payload(args, env, field).map_err(|error| {
        let error_field = error.field.unwrap_or_else(|| field.to_string());
        RuntimeError::invalid(error.message, &error_field)
    })
}

fn validate_plan_budget(budget: &super::ExecutionBudget) -> RuntimeResult<()> {
    if budget.memory_max_bytes == Some(0) {
        return Err(RuntimeError::invalid(
            "plan memoryMaxBytes must be positive",
            "plan.budget.memoryMaxBytes",
        ));
    }
    if budget.tasks_max == Some(0) {
        return Err(RuntimeError::invalid(
            "plan tasksMax must be positive",
            "plan.budget.tasksMax",
        ));
    }
    if budget.cpu_quota_percent == Some(0) {
        return Err(RuntimeError::invalid(
            "plan cpuQuotaPercent must be positive",
            "plan.budget.cpuQuotaPercent",
        ));
    }
    Ok(())
}

fn attempt_runner_identity_matches(attempt: &AttemptRecord, identity: &RunnerIdentity) -> bool {
    attempt.unit_name == identity.unit_name
        && attempt.boot_id.as_deref() == Some(identity.boot_id.as_str())
        && attempt.invocation_id.as_deref() == Some(identity.invocation_id.as_str())
        && attempt.control_group.as_deref() == Some(identity.control_group.as_str())
        && attempt.main_pid == Some(identity.main_pid)
        && attempt.process_start_identity.as_deref()
            == Some(identity.process_start_identity.as_str())
        && attempt.runner_start_digest.as_deref() == Some(identity.runner_start_digest.as_str())
}

fn validate_runner_identity(identity: &RunnerIdentity) -> RuntimeResult<()> {
    for (value, field) in [
        (&identity.boot_id, "bootId"),
        (&identity.unit_name, "unitName"),
        (&identity.invocation_id, "invocationId"),
        (&identity.process_start_identity, "processStartIdentity"),
    ] {
        validate_identifier(value, field)?;
    }
    if !identity.unit_name.ends_with(".service") || identity.main_pid == 0 {
        return Err(RuntimeError::invalid(
            "invalid Runner unit or PID",
            "runnerIdentity",
        ));
    }
    if !Path::new(&identity.control_group).is_absolute() {
        return Err(RuntimeError::invalid(
            "controlGroup must be absolute",
            "controlGroup",
        ));
    }
    validate_digest(&identity.runner_start_digest, "runnerStartDigest")
}

fn validate_artifact_registration(artifact: &ArtifactRegistration) -> RuntimeResult<()> {
    validate_identifier(&artifact.artifact_id, "artifactId")?;
    validate_identifier(&artifact.kind, "artifact.kind")?;
    validate_digest(&artifact.digest, "artifact.digest")?;
    if artifact.relative_path.is_empty()
        || Path::new(&artifact.relative_path).is_absolute()
        || artifact
            .relative_path
            .split('/')
            .any(|segment| segment == "..")
    {
        return Err(RuntimeError::invalid(
            "Artifact path must be a bounded relative path",
            "artifact.relativePath",
        ));
    }
    if artifact.media_type.is_empty() || artifact.media_type.len() > 256 {
        return Err(RuntimeError::invalid(
            "Artifact mediaType must be non-empty and bounded",
            "artifact.mediaType",
        ));
    }
    Ok(())
}

fn validate_identifier(value: &str, field: &str) -> RuntimeResult<()> {
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

fn validate_digest(value: &str, field: &str) -> RuntimeResult<()> {
    let valid = value
        .strip_prefix("sha256:")
        .is_some_and(|hex| hex.len() == 64 && hex.bytes().all(|byte| byte.is_ascii_hexdigit()));
    if !valid {
        return Err(RuntimeError::invalid(
            format!("{field} must be a SHA-256 digest"),
            field,
        ));
    }
    Ok(())
}

fn state_conflict(message: impl Into<String>) -> RuntimeError {
    RuntimeError::new(
        RuntimeErrorCode::AttemptStateConflict,
        message,
        Some("attemptId"),
        false,
    )
}

fn sha256_bytes(bytes: &[u8]) -> String {
    format!("sha256:{}", hex::encode(Sha256::digest(bytes)))
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

fn create_private_directory(path: &Path) -> RuntimeResult<()> {
    fs::create_dir_all(path).map_err(|error| {
        RuntimeError::new(
            RuntimeErrorCode::IoError,
            format!("cannot create {}: {error}", path.display()),
            Some("storeRoot"),
            false,
        )
    })?;
    fs::set_permissions(path, fs::Permissions::from_mode(0o700)).map_err(|error| {
        RuntimeError::new(
            RuntimeErrorCode::IoError,
            format!("cannot protect {}: {error}", path.display()),
            Some("storeRoot"),
            false,
        )
    })
}

fn set_private_file(path: &Path) -> RuntimeResult<()> {
    fs::set_permissions(path, fs::Permissions::from_mode(0o600)).map_err(|error| {
        RuntimeError::new(
            RuntimeErrorCode::IoError,
            format!("cannot protect {}: {error}", path.display()),
            Some("dbPath"),
            false,
        )
    })
}
