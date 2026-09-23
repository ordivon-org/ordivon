use rusqlite::{Connection, OptionalExtension};

use super::{
    AttemptRecord, AttemptState, AttemptTerminationIntent, JobDesiredState, JobResolution,
    ReservationRecord, ReservationState, RuntimeError, RuntimeErrorCode, RuntimeJobRecord,
    RuntimeResult,
};

/// Narrow read-side SQLite persistence boundary for durable Runtime state records.
///
/// This module reconstructs typed state records from the Registry representation. It does not
/// decide state transitions, replay, reservation policy, reconciliation, or semantic completion.
pub(crate) struct RegistryStorageBoundary;

impl RegistryStorageBoundary {
    pub(crate) fn decode_job_row(row: &rusqlite::Row<'_>) -> rusqlite::Result<StoredJobRow> {
        raw_job_from_row(row)
    }

    pub(crate) fn decode_attempt_row(
        row: &rusqlite::Row<'_>,
    ) -> rusqlite::Result<StoredAttemptRow> {
        raw_attempt_from_row(row)
    }

    pub(crate) fn load_job(
        connection: &Connection,
        job_id: &str,
    ) -> RuntimeResult<RuntimeJobRecord> {
        load_job_record(connection, job_id)
    }

    pub(crate) fn load_attempt(
        connection: &Connection,
        attempt_id: &str,
    ) -> RuntimeResult<AttemptRecord> {
        load_attempt_record(connection, attempt_id)
    }

    pub(crate) fn load_reservation(
        connection: &Connection,
        attempt_id: &str,
    ) -> RuntimeResult<ReservationRecord> {
        load_reservation_record(connection, attempt_id)
    }
}

pub(crate) struct StoredJobRow {
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

impl StoredJobRow {
    pub(crate) fn into_record(self) -> RuntimeResult<RuntimeJobRecord> {
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

fn raw_job_from_row(row: &rusqlite::Row<'_>) -> rusqlite::Result<StoredJobRow> {
    Ok(StoredJobRow {
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

fn load_job_record(connection: &Connection, job_id: &str) -> RuntimeResult<RuntimeJobRecord> {
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

pub(crate) struct StoredAttemptRow {
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

impl StoredAttemptRow {
    pub(crate) fn into_record(self) -> RuntimeResult<AttemptRecord> {
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

fn raw_attempt_from_row(row: &rusqlite::Row<'_>) -> rusqlite::Result<StoredAttemptRow> {
    Ok(StoredAttemptRow {
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

fn load_attempt_record(connection: &Connection, attempt_id: &str) -> RuntimeResult<AttemptRecord> {
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

fn load_reservation_record(
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
