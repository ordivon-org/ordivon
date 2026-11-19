//! Native PostgreSQL Runtime admission contract, NOT production authority.
//! Explicitly opt-in until the full lifecycle/refinement/consumer proof exists.
use postgres::{Client, IsolationLevel, NoTls};
use sha2::{Digest, Sha256};
use std::collections::HashSet;
use uuid::Uuid;

mod cancel_contract;
#[path = "pg_dispatch.rs"]
mod dispatch;
mod input_contract;
#[path = "pg_issuer_guard.rs"]
mod issuer;
mod terminal_contract;
mod writer_authority;
use cancel_contract::cancel_detail;
pub use cancel_contract::{PgCancelIntent, PgCancelObservation, PgCancelOutcome};
pub(crate) use dispatch::PgRunnerBound;
pub use dispatch::{PgBundleReady, PgDispatchIssued};
use input_contract::unambiguous_json_object;
pub use input_contract::PgAdmissionInput;
use terminal_contract::terminal_transition;
pub(crate) use terminal_contract::{pg_artifact_manifest_digest, valid_pg_artifacts};
pub use terminal_contract::{PgArtifactRegistration, PgTerminalNoArtifacts, PgTerminalOutcome};
pub use writer_authority::pg_writer_epoch_digest;
pub(crate) use writer_authority::require_pg_writer_epoch;
use writer_authority::{exact_schema, qualified_schema_constraints};

#[derive(Debug)]
pub enum PgAdmissionError {
    InvalidInput,
    Unqualified,
    Capacity,
    IdempotencyConflict,
    PendingEffect,
    /// Workspace physical identity changed after a Job was planned, but before
    /// its PG admission acquired the global effect/admission lock.
    WorkspaceStale,
    IssuerNotCurrent,
    Blocked,
    UnknownCommit,
    Database(postgres::Error),
}
impl From<postgres::Error> for PgAdmissionError {
    fn from(error: postgres::Error) -> Self {
        Self::Database(error)
    }
}

#[derive(Debug, PartialEq, Eq)]
pub enum PgAdmissionOutcome {
    Created(String),
    Existing(String),
}

pub struct PgAdmissionStore {
    pub(crate) client: Client,
}
// Only retry a server-confirmed, fully aborted SERIALIZABLE transaction.
// An uncertain COMMIT or an external process effect is never eligible.
const MAX_ABORTED_TRANSACTION_ATTEMPTS: u32 = 8;
pub(crate) fn retry_aborted_transaction<T, E>(
    mut transaction: impl FnMut() -> Result<T, E>,
    is_serialization_abort: impl Fn(&E) -> bool,
    mut wait: impl FnMut(std::time::Duration),
) -> Result<T, E> {
    for attempt in 0..MAX_ABORTED_TRANSACTION_ATTEMPTS {
        match transaction() {
            Err(ref e)
                if is_serialization_abort(e) && attempt + 1 < MAX_ABORTED_TRANSACTION_ATTEMPTS =>
            {
                // 4,8,16,32,64,64,64ms; each retry re-enters the whole transaction.
                wait(std::time::Duration::from_millis(4_u64 << attempt.min(4)));
            }
            result => return result,
        }
    }
    unreachable!("last bounded attempt must return")
}
#[cfg(test)]
mod serializable_retry_tests {
    use super::*;
    #[derive(Clone, Copy, Debug, Eq, PartialEq)]
    enum Fault {
        Aborted,
        UnknownCommit,
        Other,
    }
    #[test]
    fn retries_complete_aborts_but_not_unknown_commit_or_other_errors() {
        let mut attempts = 0;
        let mut delays = Vec::new();
        let outcome = retry_aborted_transaction(
            || {
                attempts += 1;
                if attempts < 3 {
                    Err(Fault::Aborted)
                } else {
                    Ok(attempts)
                }
            },
            |e| *e == Fault::Aborted,
            |d| delays.push(d.as_millis() as u64),
        );
        assert_eq!(outcome, Ok(3));
        assert_eq!(delays, [4, 8]);
        for e in [Fault::UnknownCommit, Fault::Other] {
            let mut count = 0;
            let r: Result<(), Fault> = retry_aborted_transaction(
                || {
                    count += 1;
                    Err(e)
                },
                |e| *e == Fault::Aborted,
                |_| panic!("must never retry unknown or unrelated errors"),
            );
            assert_eq!(r, Err(e));
            assert_eq!(count, 1);
        }
    }
    #[test]
    fn bounded_exhaustion_preserves_serialization_error() {
        let mut count = 0;
        let mut delays = Vec::new();
        let r: Result<(), Fault> = retry_aborted_transaction(
            || {
                count += 1;
                Err(Fault::Aborted)
            },
            |e| *e == Fault::Aborted,
            |d| delays.push(d.as_millis() as u64),
        );
        assert_eq!(r, Err(Fault::Aborted));
        assert_eq!(count, 8);
        assert_eq!(delays, [4, 8, 16, 32, 64, 64, 64]);
    }
}
// PostgreSQL insertion columns, not another release semantic state owner.
// Only a transactional Runtime caller can construct the domain release object.
// Standalone PG admission needs no legacy Runtime module or SQLite dependency.
struct PgReleaseInsert {
    effect_id: String,
    request_digest: String,
    workspace_id: String,
    commit: String,
    candidate_manifest_digest: String,
    expected_tool_count: i32,
    receipt_path: String,
}

impl PgAdmissionStore {
    pub fn connect(dsn: &str, schema: &str) -> Result<Self, PgAdmissionError> {
        if !exact_schema(schema) {
            return Err(PgAdmissionError::InvalidInput);
        }
        let mut client = Client::connect(dsn, NoTls)?;
        client.query_one(
            "SELECT set_config('search_path',$1,false)",
            &[&format!("\"{schema}\"")],
        )?;
        let actual: Option<String> = client.query_one("SELECT current_schema()", &[])?.get(0);
        if actual.as_deref() != Some(schema) {
            return Err(PgAdmissionError::Unqualified);
        }
        qualified_schema_constraints(&mut client, schema)?;
        Ok(Self { client })
    }

    /// Internal PG-only release admission. No MCP caller can invoke this until
    /// an independently qualified operator installation/reconciliation contract
    /// exists. No filesystem or systemd effects occur in this transaction.
    pub fn admit_release_effect(
        &mut self,
        input: &PgAdmissionInput,
        request: &crate::runtime::RuntimeReleaseRequest,
        receipt_path: &std::path::Path,
    ) -> Result<PgAdmissionOutcome, PgAdmissionError> {
        use crate::runtime::{
            runtime_release_effect_id, runtime_release_request_identity_digest,
            ReleaseStateContract, RuntimeReleaseContract, RuntimeReleaseEffectBinding,
        };
        ReleaseStateContract::validate_request(request)
            .map_err(|_| PgAdmissionError::InvalidInput)?;
        let expected_tool_count = i32::try_from(request.expected_tool_count)
            .map_err(|_| PgAdmissionError::InvalidInput)?;
        if !receipt_path.is_absolute()
            || receipt_path
                .components()
                .any(|part| matches!(part, std::path::Component::ParentDir))
            || request.principal != input.principal
            || request.client_request_id != input.client_request_id
            || request.workspace_id != input.workspace_id
            || runtime_release_request_identity_digest(request)
                .map_err(|_| PgAdmissionError::InvalidInput)?
                != input.request_digest
        {
            return Err(PgAdmissionError::InvalidInput);
        }
        let binding = RuntimeReleaseEffectBinding {
            contract: RuntimeReleaseContract::RuntimeReleaseV1,
            effect_id: runtime_release_effect_id(request),
            request_digest: input.request_digest.clone(),
            workspace_id: request.workspace_id.clone(),
            commit: request.commit.clone(),
            candidate_manifest_digest: request.candidate_manifest_digest.clone(),
            expected_tool_count: request.expected_tool_count,
            receipt_path: receipt_path.to_string_lossy().into_owned(),
        };
        let json = serde_json::to_string(&binding).map_err(|_| PgAdmissionError::InvalidInput)?;
        let digest = format!("sha256:{}", hex::encode(Sha256::digest(json.as_bytes())));
        let snapshot: serde_json::Value = serde_json::from_str(&input.workspace_snapshot_json)
            .map_err(|_| PgAdmissionError::InvalidInput)?;
        if snapshot
            .get("runtimeReleaseEffectDigest")
            .and_then(serde_json::Value::as_str)
            != Some(digest.as_str())
        {
            return Err(PgAdmissionError::InvalidInput);
        }
        let columns = PgReleaseInsert {
            effect_id: binding.effect_id.clone(),
            request_digest: binding.request_digest.clone(),
            workspace_id: binding.workspace_id.clone(),
            commit: binding.commit.clone(),
            candidate_manifest_digest: binding.candidate_manifest_digest.clone(),
            expected_tool_count,
            receipt_path: binding.receipt_path.clone(),
        };
        self.admit_inner(input, Some((&columns, &digest)), None, None)
    }

    /// One atomic admission. No dispatch/terminal/repair effect is authorized.
    pub fn admit(&mut self, i: &PgAdmissionInput) -> Result<PgAdmissionOutcome, PgAdmissionError> {
        self.admit_inner(i, None, None, None)
    }

    /// Bind the physical Workspace identity at the actual durable Job
    /// admission linearization point, not while computing the plan beforehand.
    /// The callback is performed only for a NEW Job after exact replay is
    /// resolved; it must be read-only and may not make external side effects.
    /// It executes while the same global advisory lock guards close/mutate.
    pub(crate) fn admit_with_workspace_guard(
        &mut self,
        i: &PgAdmissionInput,
        guard: &dyn Fn() -> Result<(), PgAdmissionError>,
        issuer_schema: Option<&str>,
    ) -> Result<PgAdmissionOutcome, PgAdmissionError> {
        if issuer_schema.is_some_and(|schema| !exact_schema(schema)) {
            return Err(PgAdmissionError::Unqualified);
        }
        // Reuse ONE transaction for both Workspace lifecycle and issuer currentness.
        self.admit_inner(i, None, Some(guard), issuer_schema)
    }

    fn admit_inner(
        &mut self,
        i: &PgAdmissionInput,
        release: Option<(&PgReleaseInsert, &str)>,
        guard: Option<&dyn Fn() -> Result<(), PgAdmissionError>>,
        issuer_schema: Option<&str>,
    ) -> Result<PgAdmissionOutcome, PgAdmissionError> {
        // PostgreSQL SERIALIZABLE can abort at a row lock while the scheduler
        // updates its qualified epoch or an adjacent state transition. Retry
        // only an explicitly failed, pre-COMMIT transaction: its effects
        // have rolled back. Never replay an UNKNOWN COMMIT acknowledgement.
        retry_aborted_transaction(
            || self.admit_once(i, release, guard, issuer_schema),
            |e| {
                matches!(
                    e,
                    PgAdmissionError::Database(pg_error)
                        if pg_error.code()
                            == Some(&postgres::error::SqlState::T_R_SERIALIZATION_FAILURE)
                )
            },
            std::thread::sleep,
        )
    }

    fn admit_once(
        &mut self,
        i: &PgAdmissionInput,
        release: Option<(&PgReleaseInsert, &str)>,
        guard: Option<&dyn Fn() -> Result<(), PgAdmissionError>>,
        issuer_schema: Option<&str>,
    ) -> Result<PgAdmissionOutcome, PgAdmissionError> {
        i.validate()?;
        let mut tx = self
            .client
            .build_transaction()
            .isolation_level(IsolationLevel::Serializable)
            .start()?;
        // Serialize admission identity and lifecycle effect fencing.
        tx.query_one("SELECT pg_advisory_xact_lock($1)", &[&79245017_i64])?;
        let authority = tx.query_opt(
            "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='source' FOR UPDATE", &[]
        )?;
        let Some(authority) = authority else {
            return Err(PgAdmissionError::Unqualified);
        };
        let state: String = authority.get(0);
        let source: String = authority.get(1);
        let permitted: bool = authority.get(2);
        if state != "QUALIFIED_WRITER" || !permitted || source != i.expected_source_sha256 {
            return Err(PgAdmissionError::Unqualified);
        }
        require_pg_writer_epoch(&mut tx, &i.expected_source_sha256, true)?;
        if let Some(row) = tx.query_opt(
            "SELECT k.job_id,j.request_digest FROM idempotency_keys k \
             JOIN jobs j ON j.job_id=k.job_id AND j.principal=k.principal \
                AND j.client_request_id=k.client_request_id \
                AND j.operation_digest=k.operation_digest \
             WHERE k.principal=$1 AND k.client_request_id=$2",
            &[&i.principal, &i.client_request_id],
        )? {
            let job_id: String = row.get(0);
            let request_digest: String = row.get(1);
            // Exact replay binds the proposal, not current Workspace bytes,
            // resolved plan, or provider identity. Those facts belong to
            // the original committed Operation, not this second admission.
            if request_digest != i.request_digest {
                return Err(PgAdmissionError::IdempotencyConflict);
            }
            let existing = tx.query_opt(
                "SELECT effect_id,request_digest,workspace_id,commit_revision,candidate_manifest_digest,expected_tool_count,receipt_path,binding_digest FROM job_runtime_release_effects WHERE job_id=$1",
                &[&job_id],
            )?;
            match (release, existing) {
                (None, None) => (),
                (Some((binding, digest)), Some(row))
                    if row.get::<_, String>(0) == binding.effect_id
                        && row.get::<_, String>(1) == binding.request_digest
                        && row.get::<_, String>(2) == binding.workspace_id
                        && row.get::<_, String>(3) == binding.commit
                        && row.get::<_, String>(4) == binding.candidate_manifest_digest
                        && row.get::<_, i32>(5) == binding.expected_tool_count
                        && row.get::<_, String>(6) == binding.receipt_path
                        && row.get::<_, String>(7) == digest => {}
                _ => return Err(PgAdmissionError::IdempotencyConflict),
            }
            tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
            return Ok(PgAdmissionOutcome::Existing(job_id));
        }
        // Exact historical replay above is not a new physical Job grant.
        if let Some(schema) = issuer_schema {
            issuer::require_current_harness_issuer_for_new_job(&mut tx, i, schema)?;
        }
        if release.is_some() {
            // release is a separately operator-qualified capability.
            // The app role only has SELECT on _stage_control and cannot grant
            // itself this authority even if it owns the Job and its contents.
            let qualified = tx.query_opt(
                "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='release' FOR SHARE",
                &[],
            )?;
            let approved = qualified.is_some_and(|row| {
                row.get::<_, String>(0) == "QUALIFIED_RELEASE"
                    && row.get::<_, String>(1) == i.expected_source_sha256
                    && row.get::<_, bool>(2)
            });
            if !approved {
                return Err(PgAdmissionError::Unqualified);
            }
        }
        // This predicate fences new writer effects, not read-only replay of a
        // previously committed identity. Resolving the exact idempotency key
        // must precede transient pending-Effect and capacity admission gates.
        let pending:bool=tx.query_one(
            "SELECT EXISTS(SELECT 1 FROM job_runtime_release_effects r JOIN jobs j ON j.job_id=r.job_id WHERE j.resolution IS NULL OR EXISTS(SELECT 1 FROM attempts a JOIN concurrency_reservations c ON c.attempt_id=a.attempt_id WHERE a.job_id=j.job_id AND c.state IN ('active','held_orphaned')))",&[])?.get(0);
        if pending {
            return Err(PgAdmissionError::PendingEffect);
        }
        // All PG Workspace open/close/mutate operations hold advisory 79245017
        // across physical Git/FS effects. This guard therefore observes the
        // exact Workspace identity after any preceding close/reopen committed,
        // and before this Job creates a durable Attempt and active reservation.
        // Existing idempotent replay bypasses this mutable-state guard.
        if let Some(guard) = guard {
            guard()?;
        }
        // Admission is durable intent, never a physical execution slot.
        // Resource allocation and Workspace access leases are claimed at dispatch.
        tx.execute(
            "INSERT INTO jobs(job_id,principal,client_request_id,request_digest,operation_digest,workspace_id,workspace_snapshot_json,execution_plan_json,execution_plan_digest,created_at_ms,desired_state,resolution,current_attempt_id,row_version) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,'run',NULL,NULL,0)",
            &[&i.job_id,&i.principal,&i.client_request_id,&i.request_digest,&i.operation_digest,
              &i.workspace_id,&i.workspace_snapshot_json,&i.execution_plan_json,
              &i.execution_plan_digest,&i.created_at_ms])?;
        tx.execute(
            "INSERT INTO attempts(attempt_id,job_id,attempt_number,state,termination_intent,launch_token_digest,bundle_path,unit_name,created_at_ms,row_version) VALUES($1,$2,1,'accepted','natural',$3,$4,$5,$6,0)",
            &[&i.attempt_id,&i.job_id,&i.launch_token_digest,&i.bundle_path,&i.unit_name,&i.created_at_ms])?;
        tx.execute(
            "UPDATE jobs SET current_attempt_id=$1 WHERE job_id=$2",
            &[&i.attempt_id, &i.job_id],
        )?;
        tx.execute(
            "INSERT INTO idempotency_keys(principal,client_request_id,operation_digest,job_id,created_at_ms) VALUES($1,$2,$3,$4,$5)",
            &[&i.principal,&i.client_request_id,&i.operation_digest,&i.job_id,&i.created_at_ms])?;
        tx.execute(
            "INSERT INTO concurrency_reservations(reservation_id,attempt_id,global_limit,state,acquired_at_ms,state_observed_at_ms) VALUES($1,$2,$3,'active',$4,$4)",
            &[&i.reservation_id,&i.attempt_id,&i64::from(i.global_limit),&i.created_at_ms])?;
        if let Some((binding, digest)) = release {
            // Exact ReleaseEffect side truth and Job must COMMIT atomically.
            // Normal Job admission, native dispatch and reconciliation are
            // independently fenced from these release-specific Accepted Jobs.
            tx.execute(
                "INSERT INTO job_runtime_release_effects(job_id,effect_id,contract,request_digest,workspace_id,commit_revision,candidate_manifest_digest,expected_tool_count,receipt_path,binding_digest) VALUES($1,$2,'runtime_release_v1',$3,$4,$5,$6,$7,$8,$9)",
                &[&i.job_id,&binding.effect_id,&binding.request_digest,&binding.workspace_id,
                  &binding.commit,&binding.candidate_manifest_digest,
                  &binding.expected_tool_count,&binding.receipt_path,&digest],
            )?;
        }
        let events = [
            (
                "REQUEST_RECEIVED",
                "REQUEST_ACCEPTED",
                None,
                serde_json::json!({"requestDigest":i.request_digest}),
            ),
            (
                "JOB_RECORD_CREATED",
                "JOB_CREATED",
                None,
                serde_json::json!({"operationDigest":i.operation_digest}),
            ),
            (
                "ATTEMPT_CREATED",
                "ATTEMPT_ACCEPTED",
                Some("accepted"),
                serde_json::json!({"attemptNumber":1}),
            ),
        ];
        for (idx, (event_type, reason, next_state, detail)) in events.iter().enumerate() {
            let encoded = detail.to_string();
            let digest = format!("sha256:{}", hex::encode(Sha256::digest(encoded.as_bytes())));
            tx.execute(
                "INSERT INTO job_events(event_id,job_id,attempt_id,event_sequence,event_type,origin,previous_state,new_state,reason_code,detail_json,detail_digest,observed_at_ms) VALUES($1,$2,$3,$4,$5,'SYSTEM_DERIVED',NULL,$6,$7,$8,$9,$10)",
                &[&format!("event-{}",Uuid::now_v7()),&i.job_id,&i.attempt_id,
                  &((idx+1) as i64),event_type,next_state,reason,&encoded,&digest,&i.created_at_ms])?;
        }
        // A failed COMMIT is UNKNOWN, not a retryable assertion of no effect.
        tx.query_one(
            "SELECT pg_notify('ordivon_runtime_schedule',current_schema())",
            &[],
        )?;
        tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
        Ok(PgAdmissionOutcome::Created(i.job_id.clone()))
    }
}

/// Read-only witness for a potentially committed admission whose response was lost.
///
/// Inconclusive is deliberately NOT equivalent to "the write did not commit".
/// The witness binds the exact submitted identity, its initial Attempt and
/// capacity reservation, and all three admission events. It does not assert
/// dispatch, runner activity, terminal completion, or installed PG authority.
#[derive(Debug, PartialEq, Eq)]
pub enum PgAdmissionObservation {
    Confirmed(String),
    Inconclusive,
}

impl PgAdmissionStore {
    pub fn observe_admission(
        &mut self,
        i: &PgAdmissionInput,
    ) -> Result<PgAdmissionObservation, PgAdmissionError> {
        i.validate()?;
        let mut tx = self
            .client
            .build_transaction()
            .isolation_level(IsolationLevel::RepeatableRead)
            .read_only(true)
            .start()?;
        let authority = tx.query_opt(
            "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='source'",
            &[],
        )?.ok_or(PgAdmissionError::Unqualified)?;
        let state: String = authority.get(0);
        let source: String = authority.get(1);
        let permitted: bool = authority.get(2);
        if state != "QUALIFIED_WRITER" || !permitted || source != i.expected_source_sha256 {
            return Err(PgAdmissionError::Unqualified);
        }
        require_pg_writer_epoch(&mut tx, &i.expected_source_sha256, false)?;

        // A key by itself is insufficient: require the original immutable Job,
        // first Attempt and capacity reservation to be mutually consistent.
        // Mutable lifecycle/desired-state columns must NOT be pinned to their
        // initial values: the original admission stays true after progression.
        let row = tx.query_opt(
            "SELECT j.job_id,j.request_digest,j.operation_digest,j.workspace_id, \
                    j.workspace_snapshot_json,j.execution_plan_json,j.execution_plan_digest, \
                    j.created_at_ms,a.attempt_id,a.attempt_number,a.launch_token_digest, \
                    a.bundle_path,a.unit_name,a.created_at_ms, \
                    r.reservation_id,r.global_limit,r.acquired_at_ms \
             FROM idempotency_keys k \
             JOIN jobs j ON j.job_id=k.job_id AND j.principal=k.principal \
                AND j.client_request_id=k.client_request_id \
             JOIN attempts a ON a.job_id=j.job_id AND a.attempt_number=1 \
             JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id \
             WHERE k.principal=$1 AND k.client_request_id=$2 \
                AND k.operation_digest=j.operation_digest",
            &[&i.principal, &i.client_request_id],
        )?;
        let Some(row) = row else {
            return Ok(PgAdmissionObservation::Inconclusive);
        };
        let matches = row.get::<_, String>(0) == i.job_id
            && row.get::<_, String>(1) == i.request_digest
            && row.get::<_, String>(2) == i.operation_digest
            && row.get::<_, String>(3) == i.workspace_id
            && row.get::<_, String>(4) == i.workspace_snapshot_json
            && row.get::<_, String>(5) == i.execution_plan_json
            && row.get::<_, String>(6) == i.execution_plan_digest
            && row.get::<_, i64>(7) == i.created_at_ms
            && row.get::<_, String>(8) == i.attempt_id
            && row.get::<_, i64>(9) == 1
            && row.get::<_, String>(10) == i.launch_token_digest
            && row.get::<_, String>(11) == i.bundle_path
            && row.get::<_, String>(12) == i.unit_name
            && row.get::<_, i64>(13) == i.created_at_ms
            && row.get::<_, String>(14) == i.reservation_id
            && row.get::<_, i64>(15) == i64::from(i.global_limit)
            && row.get::<_, i64>(16) == i.created_at_ms;
        if !matches {
            return Ok(PgAdmissionObservation::Inconclusive);
        }

        let rows = tx.query(
            "SELECT event_sequence,event_type,origin,previous_state,new_state, \
                    reason_code,detail_json,detail_digest,observed_at_ms,attempt_id \
             FROM job_events WHERE job_id=$1 AND event_sequence BETWEEN 1 AND 3 \
             ORDER BY event_sequence",
            &[&i.job_id],
        )?;
        if rows.len() != 3 {
            return Ok(PgAdmissionObservation::Inconclusive);
        }
        let expected = [
            (
                "REQUEST_RECEIVED",
                "REQUEST_ACCEPTED",
                None,
                serde_json::json!({"requestDigest":i.request_digest}),
            ),
            (
                "JOB_RECORD_CREATED",
                "JOB_CREATED",
                None,
                serde_json::json!({"operationDigest":i.operation_digest}),
            ),
            (
                "ATTEMPT_CREATED",
                "ATTEMPT_ACCEPTED",
                Some("accepted"),
                serde_json::json!({"attemptNumber":1}),
            ),
        ];
        for (index, (row, (event_type, reason, new_state, detail))) in
            rows.iter().zip(expected.iter()).enumerate()
        {
            let encoded = detail.to_string();
            let digest = format!("sha256:{}", hex::encode(Sha256::digest(encoded.as_bytes())));
            if row.get::<_, i64>(0) != (index + 1) as i64
                || row.get::<_, String>(1) != *event_type
                || row.get::<_, String>(2) != "SYSTEM_DERIVED"
                || row.get::<_, Option<String>>(3).is_some()
                || row.get::<_, Option<String>>(4).as_deref() != *new_state
                || row.get::<_, String>(5) != *reason
                || row.get::<_, String>(6) != encoded
                || row.get::<_, String>(7) != digest
                || row.get::<_, i64>(8) != i.created_at_ms
                || row.get::<_, Option<String>>(9).as_deref() != Some(i.attempt_id.as_str())
            {
                return Ok(PgAdmissionObservation::Inconclusive);
            }
        }
        tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
        Ok(PgAdmissionObservation::Confirmed(i.job_id.clone()))
    }
}

impl PgAdmissionStore {
    /// Exact no-Artifact terminal/Job/reservation/event atomicity, no runner or
    /// external output effect. Arbitrary Artifact-bearing terminal commits are
    /// deliberately unsupported until a complete consumer-owned transaction.
    pub fn commit_terminal_no_artifacts(
        &mut self,
        i: &PgTerminalNoArtifacts,
    ) -> Result<PgTerminalOutcome, PgAdmissionError> {
        self.commit_terminal_artifacts_impl(i, &[])
    }
    pub fn commit_terminal_with_artifacts(
        &mut self,
        i: &PgTerminalNoArtifacts,
        artifacts: &[PgArtifactRegistration],
    ) -> Result<PgTerminalOutcome, PgAdmissionError> {
        if artifacts.is_empty() {
            return Err(PgAdmissionError::InvalidInput);
        }
        self.commit_terminal_artifacts_impl(i, artifacts)
    }
    fn commit_terminal_artifacts_impl(
        &mut self,
        i: &PgTerminalNoArtifacts,
        artifacts: &[PgArtifactRegistration],
    ) -> Result<PgTerminalOutcome, PgAdmissionError> {
        if !valid_pg_artifacts(artifacts) {
            return Err(PgAdmissionError::InvalidInput);
        }
        if i.attempt_id.is_empty()
            || i.result_digest.is_empty()
            || i.reason_code.is_empty()
            || i.finished_at_ms < 0
            || i.expected_row_version < 0
            || i.expected_source_sha256.len() != 64
            || !i
                .expected_source_sha256
                .bytes()
                .all(|b| b.is_ascii_hexdigit())
            || !matches!(
                i.terminal_state.as_str(),
                "succeeded" | "failed" | "timed_out" | "cancelled" | "lost" | "orphaned"
            )
        {
            return Err(PgAdmissionError::InvalidInput);
        }
        let mut tx = self
            .client
            .build_transaction()
            .isolation_level(IsolationLevel::Serializable)
            .start()?;
        tx.query_one("SELECT pg_advisory_xact_lock($1)", &[&79245017_i64])?;
        let auth=tx.query_opt(
            "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='source' FOR UPDATE",&[])?;
        let Some(auth) = auth else {
            return Err(PgAdmissionError::Unqualified);
        };
        let status: String = auth.get(0);
        let seal: String = auth.get(1);
        let permitted: bool = auth.get(2);
        if status != "QUALIFIED_WRITER" || !permitted || seal != i.expected_source_sha256 {
            return Err(PgAdmissionError::Unqualified);
        }
        require_pg_writer_epoch(&mut tx, &i.expected_source_sha256, true)?;
        let current=tx.query_opt(
            "SELECT job_id,state,result_digest,row_version FROM attempts WHERE attempt_id=$1 FOR UPDATE",
            &[&i.attempt_id])?.ok_or(PgAdmissionError::InvalidInput)?;
        let job_id: String = current.get(0);
        let previous: String = current.get(1);
        let digest: Option<String> = current.get(2);
        let version: i64 = current.get(3);
        let job = tx.query_one(
            "SELECT resolution,current_attempt_id FROM jobs WHERE job_id=$1 FOR UPDATE",
            &[&job_id],
        )?;
        let job_resolution: Option<String> = job.get(0);
        let current_attempt: Option<String> = job.get(1);
        let existing = tx.query(
            "SELECT artifact_id,kind,relative_path,digest,media_type,byte_length,truncated,created_at_ms FROM artifacts WHERE attempt_id=$1 ORDER BY artifact_id",
            &[&i.attempt_id],
        )?;
        if artifacts.is_empty() && !existing.is_empty() {
            return Err(PgAdmissionError::Blocked);
        }
        let mut sorted = artifacts.to_vec();
        sorted.sort_by(|a, b| a.artifact_id.cmp(&b.artifact_id));
        let same_artifacts = existing.len() == sorted.len()
            && existing.iter().zip(&sorted).all(|(row, a)| {
                row.get::<_, String>(0) == a.artifact_id
                    && row.get::<_, String>(1) == a.kind
                    && row.get::<_, String>(2) == a.relative_path
                    && row.get::<_, String>(3) == a.digest
                    && row.get::<_, String>(4) == a.media_type
                    && row.get::<_, i64>(5) == a.byte_length
                    && row.get::<_, bool>(6) == a.truncated
                    && row.get::<_, i64>(7) == a.created_at_ms
            });
        if matches!(
            previous.as_str(),
            "succeeded" | "failed" | "timed_out" | "cancelled" | "lost" | "orphaned"
        ) {
            if previous == i.terminal_state
                && digest.as_deref() == Some(&i.result_digest)
                && job_resolution.as_deref() == Some(&i.terminal_state)
                && same_artifacts
            {
                tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
                return Ok(PgTerminalOutcome::Existing(job_id));
            }
            return Err(PgAdmissionError::IdempotencyConflict);
        }
        if !existing.is_empty() {
            return Err(PgAdmissionError::Blocked);
        }
        // The Job's current Attempt is the only Attempt allowed to commit a
        // fresh terminal effect. A superseded Attempt may not resolve the Job,
        // release another Attempt's capacity, or append terminal events.
        // Completed exact replay above remains legal after the Job clears
        // current_attempt_id.
        if current_attempt.as_deref() != Some(i.attempt_id.as_str()) {
            return Err(PgAdmissionError::Blocked);
        }
        if version != i.expected_row_version
            || !terminal_transition(&previous, &i.terminal_state)
            || job_resolution.is_some()
        {
            return Err(PgAdmissionError::Blocked);
        }
        let changed=tx.execute(
            "UPDATE attempts SET state=$1,result_digest=$2,exit_code=$3,finished_at_ms=$4,row_version=row_version+1 WHERE attempt_id=$5 AND row_version=$6 AND state=$7",
            &[&i.terminal_state,&i.result_digest,&i.exit_code,&i.finished_at_ms,
              &i.attempt_id,&i.expected_row_version,&previous])?;
        if changed != 1 {
            return Err(PgAdmissionError::Blocked);
        }
        for a in artifacts {
            tx.execute(
                "INSERT INTO artifacts(artifact_id,job_id,attempt_id,kind,relative_path,digest,media_type,byte_length,truncated,created_at_ms) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)",
                &[&a.artifact_id,&job_id,&i.attempt_id,&a.kind,&a.relative_path,
                &a.digest,&a.media_type,&a.byte_length,&a.truncated,&a.created_at_ms],
            )?;
        }
        if i.terminal_state == "orphaned" {
            let count=tx.execute(
                "UPDATE concurrency_reservations SET state='held_orphaned',release_reason=$1,state_observed_at_ms=$2 WHERE attempt_id=$3 AND state IN ('active','held_orphaned')",
                &[&i.reason_code,&i.finished_at_ms,&i.attempt_id])?;
            if count != 1 {
                return Err(PgAdmissionError::Blocked);
            }
        } else {
            let count=tx.execute(
                "UPDATE concurrency_reservations SET state='released',released_at_ms=$1,release_reason=$2,state_observed_at_ms=$1 WHERE attempt_id=$3 AND state IN ('active','held_orphaned')",
                &[&i.finished_at_ms,&i.reason_code,&i.attempt_id])?;
            if count != 1 {
                return Err(PgAdmissionError::Blocked);
            }
        }
        tx.execute("UPDATE job_allocations SET state='released',released_at_ms=$1 WHERE attempt_id=$2 AND state='active'", &[&i.finished_at_ms,&i.attempt_id])?;
        tx.query_one(
            "SELECT pg_notify('ordivon_runtime_schedule',current_schema())",
            &[],
        )?;
        let changed=tx.execute(
            "UPDATE jobs SET resolution=$1,current_attempt_id=NULL,row_version=row_version+1 WHERE job_id=$2 AND resolution IS NULL",
            &[&i.terminal_state,&job_id])?;
        if changed != 1 {
            return Err(PgAdmissionError::Blocked);
        }
        let start: i64 = tx
            .query_one(
                "SELECT COALESCE(MAX(event_sequence),0)+1 FROM job_events WHERE job_id=$1",
                &[&job_id],
            )?
            .get(0);
        let items = [
            (
                "PROCESS_EXITED",
                "SYSTEM_OBSERVED",
                if artifacts.is_empty() {
                    serde_json::json!({"resultDigest":i.result_digest,"exitCode":i.exit_code})
                } else {
                    serde_json::json!({
                        "resultDigest":i.result_digest,
                        "exitCode":i.exit_code,
                        "artifactSetDigest":pg_artifact_manifest_digest(artifacts)
                    })
                },
            ),
            (
                "JOB_TERMINAL",
                "SYSTEM_DERIVED",
                serde_json::json!({"resolution":i.terminal_state}),
            ),
        ];
        for (n, (event_type, origin, detail)) in items.iter().enumerate() {
            let encoded = detail.to_string();
            let digest = format!("sha256:{}", hex::encode(Sha256::digest(encoded.as_bytes())));
            tx.execute(
                "INSERT INTO job_events(event_id,job_id,attempt_id,event_sequence,event_type,origin,previous_state,new_state,reason_code,detail_json,detail_digest,observed_at_ms) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)",
                &[&format!("event-{}",Uuid::now_v7()),&job_id,&i.attempt_id,
                  &(start+n as i64),event_type,origin,&previous,&i.terminal_state,
                  &i.reason_code,&encoded,&digest,&i.finished_at_ms])?;
        }
        tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
        Ok(PgTerminalOutcome::Committed(job_id))
    }
}

impl PgAdmissionStore {
    /// Persist only a cancel/stop intent. Do not infer that a runner has
    /// stopped, release capacity, or resolve an accepted Job without an
    /// independently observed dispatch fence and terminal receipt.
    pub fn request_cancel_intent(
        &mut self,
        i: &PgCancelIntent,
    ) -> Result<PgCancelOutcome, PgAdmissionError> {
        if i.job_id.is_empty()
            || i.observed_at_ms < 0
            || i.expected_source_sha256.len() != 64
            || !i
                .expected_source_sha256
                .bytes()
                .all(|b| b.is_ascii_hexdigit())
        {
            return Err(PgAdmissionError::InvalidInput);
        }

        let mut tx = self
            .client
            .build_transaction()
            .isolation_level(IsolationLevel::Serializable)
            .start()?;
        // Same serialization boundary as admission and terminal CAS.
        tx.query_one("SELECT pg_advisory_xact_lock($1)", &[&79245017_i64])?;
        let authority = tx.query_opt(
            "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='source' FOR UPDATE",
            &[],
        )?.ok_or(PgAdmissionError::Unqualified)?;
        let state: String = authority.get(0);
        let source: String = authority.get(1);
        let permitted: bool = authority.get(2);
        if state != "QUALIFIED_WRITER" || !permitted || source != i.expected_source_sha256 {
            return Err(PgAdmissionError::Unqualified);
        }
        require_pg_writer_epoch(&mut tx, &i.expected_source_sha256, true)?;

        let job = tx.query_opt(
            "SELECT resolution,desired_state,current_attempt_id FROM jobs WHERE job_id=$1 FOR UPDATE",
            &[&i.job_id],
        )?.ok_or(PgAdmissionError::InvalidInput)?;
        let resolution: Option<String> = job.get(0);
        let desired: String = job.get(1);
        let current_attempt: Option<String> = job.get(2);

        if resolution.is_some() && resolution.as_deref() != Some("orphaned") {
            tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
            return Ok(PgCancelOutcome::Existing(i.job_id.clone()));
        }
        let attempt_id = if resolution.as_deref() == Some("orphaned") {
            // A resolved orphan has no current_attempt_id; use the latest
            // durable Attempt and prove the reservation is still held.
            tx.query_opt(
                "SELECT attempt_id FROM attempts WHERE job_id=$1 ORDER BY attempt_number DESC LIMIT 1",
                &[&i.job_id],
            )?.ok_or(PgAdmissionError::Blocked)?.get::<_, String>(0)
        } else {
            current_attempt.ok_or(PgAdmissionError::Blocked)?
        };
        let attempt = tx.query_opt(
            "SELECT state,termination_intent FROM attempts WHERE attempt_id=$1 AND job_id=$2 FOR UPDATE",
            &[&attempt_id,&i.job_id],
        )?.ok_or(PgAdmissionError::Blocked)?;
        let previous: String = attempt.get(0);
        let stop_intent: String = attempt.get(1);

        // Never treat a lifecycle projection alone as evidence that a
        // stopped/terminal attempt released its real capacity.
        let reservation = tx
            .query_opt(
                "SELECT state FROM concurrency_reservations WHERE attempt_id=$1 FOR UPDATE",
                &[&attempt_id],
            )?
            .ok_or(PgAdmissionError::Blocked)?;
        let reservation_state: String = reservation.get(0);
        let is_orphan = resolution.as_deref() == Some("orphaned");
        if is_orphan {
            if previous != "orphaned" || reservation_state != "held_orphaned" {
                return Err(PgAdmissionError::Blocked);
            }
        } else if !matches!(
            previous.as_str(),
            "accepted" | "starting" | "running" | "recovering" | "stopping"
        ) || reservation_state != "active"
        {
            return Err(PgAdmissionError::Blocked);
        }

        if desired == "cancelled"
            && stop_intent == "stop_requested"
            && (is_orphan || matches!(previous.as_str(), "accepted" | "stopping"))
        {
            tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
            return Ok(PgCancelOutcome::Existing(i.job_id.clone()));
        }
        if !matches!(desired.as_str(), "run" | "cancelled")
            || !matches!(stop_intent.as_str(), "natural" | "stop_requested")
        {
            return Err(PgAdmissionError::Blocked);
        }

        // First record the Job intent, even when its Attempt has not yet
        // started. An accepted Attempt stays accepted until dispatch fencing
        // and terminal ownership prove that early cancellation completed.
        if desired != "cancelled" {
            let changed = tx.execute(
                "UPDATE jobs SET desired_state='cancelled',row_version=row_version+1 WHERE job_id=$1 AND desired_state='run'",
                &[&i.job_id],
            )?;
            if changed != 1 {
                return Err(PgAdmissionError::Blocked);
            }
        }
        let next_state = if matches!(previous.as_str(), "starting" | "running" | "recovering") {
            "stopping"
        } else {
            previous.as_str()
        };
        let changed = tx.execute(
            "UPDATE attempts SET state=$1,termination_intent='stop_requested',row_version=row_version+1 WHERE attempt_id=$2 AND state=$3 AND termination_intent=$4",
            &[&next_state,&attempt_id,&previous,&stop_intent],
        )?;
        if changed != 1 {
            return Err(PgAdmissionError::Blocked);
        }
        let next_sequence: i64 = tx
            .query_one(
                "SELECT COALESCE(MAX(event_sequence),0)+1 FROM job_events WHERE job_id=$1",
                &[&i.job_id],
            )?
            .get(0);
        let reason = if is_orphan {
            "ORPHAN_CANCEL_INTENT_COMMITTED"
        } else if previous == "accepted" {
            "CANCEL_INTENT_AWAITING_DISPATCH_FENCE"
        } else {
            "CANCEL_INTENT_COMMITTED"
        };
        let detail = cancel_detail(i);
        let digest = format!("sha256:{}", hex::encode(Sha256::digest(detail.as_bytes())));
        tx.execute(
            "INSERT INTO job_events(event_id,job_id,attempt_id,event_sequence,event_type,origin,previous_state,new_state,reason_code,detail_json,detail_digest,observed_at_ms) VALUES($1,$2,$3,$4,'STOP_REQUESTED','SYSTEM_DERIVED',$5,$6,$7,$8,$9,$10)",
            &[&format!("event-{}", Uuid::now_v7()),&i.job_id,&attempt_id,&next_sequence,
                &previous,&next_state,&reason,&detail,&digest,&i.observed_at_ms],
        )?;
        // No capacity release, no resolved Job, no runner side effects.
        tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
        Ok(PgCancelOutcome::IntentRecorded(i.job_id.clone()))
    }
}

impl PgAdmissionStore {
    /// Reconcile a lost COMMIT acknowledgement using a NEW qualified PG
    /// connection. Only an exact durable STOP_REQUESTED event plus coherent
    /// Job/Attempt/Reservation state proves this particular cancel intent.
    /// Absence is INCONCLUSIVE, never proof that a mutation did not commit.
    pub fn observe_cancel_intent(
        &mut self,
        i: &PgCancelIntent,
    ) -> Result<PgCancelObservation, PgAdmissionError> {
        if i.job_id.is_empty()
            || i.observed_at_ms < 0
            || i.expected_source_sha256.len() != 64
            || !i
                .expected_source_sha256
                .bytes()
                .all(|b| b.is_ascii_hexdigit())
        {
            return Err(PgAdmissionError::InvalidInput);
        }
        let mut tx = self
            .client
            .build_transaction()
            .isolation_level(IsolationLevel::RepeatableRead)
            .read_only(true)
            .start()?;
        let authority = tx.query_opt(
            "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='source'",
            &[],
        )?.ok_or(PgAdmissionError::Unqualified)?;
        let state: String = authority.get(0);
        let source: String = authority.get(1);
        let permitted: bool = authority.get(2);
        if state != "QUALIFIED_WRITER" || !permitted || source != i.expected_source_sha256 {
            return Err(PgAdmissionError::Unqualified);
        }
        require_pg_writer_epoch(&mut tx, &i.expected_source_sha256, false)?;
        let Some(job) = tx.query_opt(
            "SELECT desired_state,resolution,current_attempt_id FROM jobs WHERE job_id=$1",
            &[&i.job_id],
        )?
        else {
            return Ok(PgCancelObservation::Inconclusive);
        };
        let desired: String = job.get(0);
        let resolution: Option<String> = job.get(1);
        let current_attempt: Option<String> = job.get(2);
        if desired != "cancelled" {
            return Ok(PgCancelObservation::Inconclusive);
        }
        let attempt_id = if resolution.is_some() {
            tx.query_opt(
                "SELECT attempt_id FROM attempts WHERE job_id=$1 ORDER BY attempt_number DESC LIMIT 1",
                &[&i.job_id],
            )?.map(|row| row.get::<_, String>(0))
        } else {
            current_attempt
        };
        let Some(attempt_id) = attempt_id else {
            return Ok(PgCancelObservation::Inconclusive);
        };
        let Some(attempt) = tx.query_opt(
            "SELECT state,termination_intent FROM attempts WHERE attempt_id=$1 AND job_id=$2",
            &[&attempt_id, &i.job_id],
        )?
        else {
            return Ok(PgCancelObservation::Inconclusive);
        };
        let attempt_state: String = attempt.get(0);
        let intent: String = attempt.get(1);
        if intent != "stop_requested" {
            return Ok(PgCancelObservation::Inconclusive);
        }
        let Some(reservation) = tx.query_opt(
            "SELECT state FROM concurrency_reservations WHERE attempt_id=$1",
            &[&attempt_id],
        )?
        else {
            return Ok(PgCancelObservation::Inconclusive);
        };
        let reservation_state: String = reservation.get(0);
        let coherent = if resolution.as_deref() == Some("orphaned") {
            attempt_state == "orphaned" && reservation_state == "held_orphaned"
        } else if resolution.is_some() {
            matches!(
                attempt_state.as_str(),
                "succeeded" | "failed" | "timed_out" | "cancelled" | "lost"
            ) && reservation_state == "released"
        } else {
            matches!(attempt_state.as_str(), "accepted" | "stopping")
                && reservation_state == "active"
        };
        if !coherent {
            return Ok(PgCancelObservation::Inconclusive);
        }
        let detail = cancel_detail(i);
        let event_digest = format!("sha256:{}", hex::encode(Sha256::digest(detail.as_bytes())));
        let event_exists: bool = tx.query_one(
            "SELECT EXISTS(SELECT 1 FROM job_events WHERE job_id=$1 AND attempt_id=$2 AND event_type='STOP_REQUESTED' AND origin='SYSTEM_DERIVED' AND detail_digest=$3 AND detail_json=$4 AND observed_at_ms=$5 AND reason_code IN ('CANCEL_INTENT_AWAITING_DISPATCH_FENCE','CANCEL_INTENT_COMMITTED','ORPHAN_CANCEL_INTENT_COMMITTED'))",
            &[&i.job_id,&attempt_id,&event_digest,&detail,&i.observed_at_ms],
        )?.get(0);
        if !event_exists {
            return Ok(PgCancelObservation::Inconclusive);
        }
        tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
        Ok(PgCancelObservation::Confirmed(i.job_id.clone()))
    }
}

#[cfg(test)]
mod tests {

    #[test]
    fn physical_epoch_fingerprint_is_domain_and_timeline_bound() {
        let source = "a".repeat(64);
        let previous = pg_writer_epoch_digest(&source, "77123", 1);
        assert_eq!(previous.len(), 64);
        assert_ne!(previous, pg_writer_epoch_digest(&source, "77123", 2));
        assert_ne!(previous, pg_writer_epoch_digest(&source, "77124", 1));
        assert_ne!(
            previous,
            pg_writer_epoch_digest(&"b".repeat(64), "77123", 1)
        );
        assert_eq!(previous, pg_writer_epoch_digest(&source, "77123", 1));
    }

    use super::*;
    #[test]
    fn schema_boundary_fails_closed() {
        for name in ["", "public", "pg_catalog", "_secret", "x;DROP SCHEMA"] {
            assert!(!exact_schema(name), "unsafe {name}");
        }
        assert!(exact_schema("runtime_pg_qualified_r1"));
    }
    #[test]
    fn non_object_durable_json_is_rejected_before_postgres_effects() {
        // RuntimeExecutionPlan and Workspace snapshots are records. Parsing as
        // arbitrary JSON Value would accept a scalar/array that a consumer
        // cannot decode as a valid durable state object.
        let qualified = PgAdmissionInput {
            job_id: "job".into(),
            attempt_id: "attempt".into(),
            reservation_id: "reservation".into(),
            principal: "principal".into(),
            client_request_id: "request".into(),
            request_digest: "sha256:r".into(),
            operation_digest: "sha256:o".into(),
            workspace_id: "ws".into(),
            workspace_snapshot_json: "{}".into(),
            execution_plan_json: "{}".into(),
            execution_plan_digest: "sha256:plan".into(),
            launch_token_digest: "sha256:l".into(),
            bundle_path: "/tmp/test".into(),
            unit_name: "unit".into(),
            global_limit: 1,
            created_at_ms: 1,
            expected_source_sha256: "a".repeat(64),
        };
        assert!(qualified.validate().is_ok(), "fixture must be admitted");
        for raw in ["null", "true", "false", "[]", "42", "\"text\""] {
            let mut invalid_snapshot = qualified.clone();
            invalid_snapshot.workspace_snapshot_json = raw.into();
            assert!(
                matches!(
                    invalid_snapshot.validate(),
                    Err(PgAdmissionError::InvalidInput)
                ),
                "workspace_snapshot_json accepted non-object {raw}"
            );
            let mut invalid_plan = qualified.clone();
            invalid_plan.execution_plan_json = raw.into();
            assert!(
                matches!(invalid_plan.validate(), Err(PgAdmissionError::InvalidInput)),
                "execution_plan_json accepted non-object {raw}"
            );
        }
    }

    #[test]
    fn duplicate_nested_json_keys_are_rejected_before_durable_pg_effects() {
        let qualified = PgAdmissionInput {
            job_id: "job".into(),
            attempt_id: "attempt".into(),
            reservation_id: "reservation".into(),
            principal: "principal".into(),
            client_request_id: "request".into(),
            request_digest: "sha256:r".into(),
            operation_digest: "sha256:o".into(),
            workspace_id: "ws".into(),
            workspace_snapshot_json: r#"{"snapshot":{"revision":1}}"#.into(),
            execution_plan_json: r#"{"plan":{"timeoutMs":1000}}"#.into(),
            execution_plan_digest: "sha256:plan".into(),
            launch_token_digest: "sha256:l".into(),
            bundle_path: "/tmp/test".into(),
            unit_name: "unit".into(),
            global_limit: 1,
            created_at_ms: 1,
            expected_source_sha256: "a".repeat(64),
        };
        assert!(
            qualified.validate().is_ok(),
            "ordinary nested objects qualify"
        );
        for raw in [
            r#"{"revision":1,"revision":2}"#,
            r#"{"snapshot":{"revision":1,"revision":2}}"#,
            r#"{"snapshots":[{"revision":1,"revision":2}]}"#,
            r#"{"\u0061":1,"a":2}"#,
        ] {
            let mut invalid_snapshot = qualified.clone();
            invalid_snapshot.workspace_snapshot_json = raw.into();
            assert!(
                matches!(
                    invalid_snapshot.validate(),
                    Err(PgAdmissionError::InvalidInput)
                ),
                "workspace_snapshot_json admitted ambiguous JSON {raw}"
            );
            let mut invalid_plan = qualified.clone();
            invalid_plan.execution_plan_json = raw.into();
            assert!(
                matches!(invalid_plan.validate(), Err(PgAdmissionError::InvalidInput)),
                "execution_plan_json admitted ambiguous JSON {raw}"
            );
        }
    }

    #[test]
    fn source_identity_must_be_present() {
        let i = PgAdmissionInput {
            job_id: "j".into(),
            attempt_id: "a".into(),
            reservation_id: "r".into(),
            principal: "p".into(),
            client_request_id: "c".into(),
            request_digest: "sha256:r".into(),
            operation_digest: "sha256:o".into(),
            workspace_id: "ws".into(),
            workspace_snapshot_json: "{}".into(),
            execution_plan_json: "{}".into(),
            execution_plan_digest: "sha256:plan".into(),
            launch_token_digest: "sha256:l".into(),
            bundle_path: "/tmp/test".into(),
            unit_name: "unit".into(),
            global_limit: 1,
            created_at_ms: 1,
            expected_source_sha256: String::new(),
        };
        assert!(matches!(i.validate(), Err(PgAdmissionError::InvalidInput)));
    }
}

#[cfg(all(test, feature = "postgres-registry-admission"))]
mod live_pg_tests {
    use super::*;
    use std::sync::{Arc, Barrier};
    use std::thread;

    fn physical_pg_test_dsn() -> String {
        std::env::var("ORDIVON_PG_TEST_DSN").expect(
            "physical PostgreSQL tests require ORDIVON_PG_TEST_DSN; run the dedicated mise task",
        )
    }

    fn historical_pg_stage_test_dsn() -> String {
        std::env::var("ORDIVON_PG_STAGE_TEST_DSN").expect(
            "historical stage qualification requires ORDIVON_PG_STAGE_TEST_DSN; run the dedicated stage task",
        )
    }

    // An operator supplies an isolated PostgreSQL DSN for physical tests.
    // No environment value means the ordinary CI suite never mutates PG.
    const SCHEMA: &str = include_str!("../sql/pg_fresh_epoch.sql");

    struct Scratch {
        admin: Client,
        name: String,
    }
    impl Scratch {
        fn new(dsn: &str) -> Self {
            let name = format!("test_admit_{}", Uuid::now_v7().simple());
            let mut admin = Client::connect(dsn, NoTls).expect("test PG18 connection");
            admin
                .batch_execute(&format!("CREATE SCHEMA \"{name}\""))
                .expect("private test schema");
            admin
                .query_one(
                    "SELECT set_config('search_path',$1,false)",
                    &[&format!("\"{name}\"")],
                )
                .expect("test-only search path");
            admin
                .batch_execute(SCHEMA)
                .expect("native PG fixture constraints");
            admin
                .execute(
                    "INSERT INTO _stage_control VALUES('source','VERIFIED_NON_AUTHORITY',$1,false)",
                    &[&"a".repeat(64)],
                )
                .expect("non-authority fixture");
            Self { admin, name }
        }
        fn qualify(&mut self) {
            self.admin.execute(
                "UPDATE _stage_control SET state='QUALIFIED_WRITER',promotion_allowed=true WHERE id='source'",
                &[]
            ).expect("test-only synthetic qualifier");
            let pg = self.admin.query_one(
                "SELECT (SELECT system_identifier::text FROM pg_control_system()),                         (SELECT timeline_id FROM pg_control_checkpoint())",
                &[],
            ).expect("native physical PostgreSQL epoch");
            let digest = pg_writer_epoch_digest(
                &"a".repeat(64),
                &pg.get::<_, String>(0),
                pg.get::<_, i32>(1),
            );
            self.admin.execute(
                "INSERT INTO _stage_control VALUES('epoch','QUALIFIED_EPOCH',$1,true)                  ON CONFLICT(id) DO UPDATE SET state='QUALIFIED_EPOCH',source_sha256=EXCLUDED.source_sha256,promotion_allowed=true",
                &[&digest],
            ).expect("operator-owned epoch fixture");
        }
        fn count(&mut self, table: &str) -> i64 {
            self.admin
                .query_one(&format!("SELECT count(*) FROM {table}"), &[])
                .unwrap()
                .get(0)
        }
    }
    impl Drop for Scratch {
        fn drop(&mut self) {
            // A dedicated scratch namespace, never an installed Runtime
            // schema; do not retain test effects across test runs.
            let _ = self.admin.batch_execute(&format!(
                "SET search_path TO public; DROP SCHEMA IF EXISTS \"{}\" CASCADE",
                self.name
            ));
        }
    }
    fn allocate_fixture(scratch: &mut Scratch, input: &PgAdmissionInput) {
        // Test-only scheduling decision. These SQL tests qualify transaction
        // fencing, not a native-resource probe or physical process launch.
        scratch.admin.execute("INSERT INTO job_allocations(attempt_id,resources_json,workspace_access_json,owner,state,acquired_at_ms) VALUES($1,'{}','{}',$2,'active',$3)",&[&input.attempt_id,&input.principal,&input.created_at_ms]).unwrap();
    }
    fn payload(client_key: &str, job: &str, workspace: &str, cap: i32) -> PgAdmissionInput {
        PgAdmissionInput {
            job_id: job.to_string(),
            attempt_id: format!("attempt-{job}"),
            reservation_id: format!("reservation-{job}"),
            principal: "pg-native-test".into(),
            client_request_id: client_key.to_string(),
            request_digest: format!("sha256:request-{client_key}"),
            operation_digest: format!("sha256:operation-{client_key}"),
            workspace_id: workspace.into(),
            workspace_snapshot_json: "{}".into(),
            execution_plan_json: "{}".into(),
            execution_plan_digest: "sha256:test-plan".into(),
            launch_token_digest: "sha256:launch".into(),
            bundle_path: "/nonproduction/pg-test".into(),
            unit_name: format!("{job}.service"),
            global_limit: cap,
            created_at_ms: 1234567,
            expected_source_sha256: "a".repeat(64),
        }
    }

    /// Independent Windows native evidence reader consumes exact PostgreSQL
    /// admission rows. A qualified PG row alone must NOT imply OS launch.
    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn windows_pg_bundle_consumer_reads_real_admission_without_claiming_process() {
        use crate::pg_windows_evidence::{
            inspect_admitted_windows_pg_bundle, PgWindowsWitnessPhase,
        };
        use std::fs;
        let dsn = physical_pg_test_dsn();
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        let temp = tempfile::tempdir().unwrap();
        let mut input = payload("win-native-witness", "job-win-witness", "workspace-win", 2);
        let attempt = input.attempt_id.clone();
        let bundle = temp.path().join("pg-attempts").join(&attempt);
        fs::create_dir_all(&bundle).unwrap();
        input.bundle_path = bundle.to_string_lossy().into_owned();
        input.unit_name = format!("Ordivon.{attempt}");
        input.launch_token_digest = format!("sha256:{}", "a".repeat(64));
        input.workspace_snapshot_json = serde_json::json!({
            "executionProvider": {
                "contract":"windows_native_launcher_v1",
                "executableDigest":format!("sha256:{}", "c".repeat(64))
            }
        })
        .to_string();
        let request = b"immutable-Windows-Runner-request-v1";
        fs::write(bundle.join("request.json"), request).unwrap();
        let digest = format!("sha256:{}", hex::encode(Sha256::digest(request)));
        let mut owner = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        assert!(matches!(
            owner.admit(&input).unwrap(),
            PgAdmissionOutcome::Created(_)
        ));
        // A current PG reservation/allocation is required before BUNDLE_READY.
        // Reuse the exact same physical fixture contract as the Linux PG tests;
        // a Job row alone must never authorize a launch.
        allocate_fixture(&mut scratch, &input);
        // Absence of a PG-admitted bundle readiness receipt fails closed.
        assert!(inspect_admitted_windows_pg_bundle(
            &dsn,
            &scratch.name,
            &"a".repeat(64),
            &input.principal,
            &input.job_id,
            temp.path()
        )
        .is_err());
        let version: i64 = owner
            .client
            .query_one(
                "SELECT row_version FROM attempts WHERE attempt_id=$1",
                &[&attempt],
            )
            .unwrap()
            .get(0);
        owner
            .commit_bundle_ready_pg(&crate::pg_admission::PgBundleReady {
                attempt_id: attempt.clone(),
                expected_row_version: version,
                bundle_digest: digest.clone(),
                observed_at_ms: input.created_at_ms + 1,
                expected_source_sha256: "a".repeat(64),
            })
            .unwrap();
        let missing = inspect_admitted_windows_pg_bundle(
            &dsn,
            &scratch.name,
            &"a".repeat(64),
            &input.principal,
            &input.job_id,
            temp.path(),
        )
        .unwrap();
        assert_eq!(missing.phase, PgWindowsWitnessPhase::NoLauncherWitness);
        assert!(!missing.terminal_proven);
        // RED before guard: latest Attempt remained readable even when the
        // unresolved Job had no matching current_attempt_id.
        scratch
            .admin
            .execute(
                "UPDATE jobs SET current_attempt_id=NULL WHERE job_id=$1",
                &[&input.job_id],
            )
            .unwrap();
        assert!(inspect_admitted_windows_pg_bundle(
            &dsn,
            &scratch.name,
            &"a".repeat(64),
            &input.principal,
            &input.job_id,
            temp.path(),
        )
        .unwrap_err()
        .contains("current Attempt"));
        scratch
            .admin
            .execute(
                "UPDATE jobs SET current_attempt_id=$1 WHERE job_id=$2",
                &[&input.attempt_id, &input.job_id],
            )
            .unwrap();
        // Resolution also clears the current pointer; a contradictory
        // terminal+current pair must be rejected instead of borrowed.
        scratch
            .admin
            .execute(
                "UPDATE jobs SET resolution='succeeded' WHERE job_id=$1",
                &[&input.job_id],
            )
            .unwrap();
        assert!(inspect_admitted_windows_pg_bundle(
            &dsn,
            &scratch.name,
            &"a".repeat(64),
            &input.principal,
            &input.job_id,
            temp.path(),
        )
        .unwrap_err()
        .contains("resolved PG Job retains"));
        scratch
            .admin
            .execute(
                "UPDATE jobs SET resolution=NULL WHERE job_id=$1",
                &[&input.job_id],
            )
            .unwrap();
        assert!(inspect_admitted_windows_pg_bundle(
            &dsn,
            &scratch.name,
            &"a".repeat(64),
            "another-principal",
            &input.job_id,
            temp.path()
        )
        .is_err());
        fs::write(bundle.join("request.json"), b"tampered").unwrap();
        assert!(inspect_admitted_windows_pg_bundle(
            &dsn,
            &scratch.name,
            &"a".repeat(64),
            &input.principal,
            &input.job_id,
            temp.path()
        )
        .unwrap_err()
        .contains("request digest"));
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_rejects_synthetic_writer_without_event_sequence_uniqueness() {
        let dsn = physical_pg_test_dsn();
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        assert!(PgAdmissionStore::connect(&dsn, &scratch.name).is_ok());
        scratch
            .admin
            .batch_execute(
                "ALTER TABLE job_events DROP CONSTRAINT job_events_job_id_event_sequence_key",
            )
            .expect("test-only weakened catalog");
        assert!(matches!(
            PgAdmissionStore::connect(&dsn, &scratch.name),
            Err(PgAdmissionError::Unqualified)
        ));
        assert_eq!(scratch.count("jobs"), 0);
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_rejects_foreign_key_that_points_at_wrong_pg_target() {
        let dsn = physical_pg_test_dsn();
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        assert!(PgAdmissionStore::connect(&dsn, &scratch.name).is_ok());
        scratch
            .admin
            .batch_execute(
                "CREATE TABLE unrelated_jobs(job_id text PRIMARY KEY);
             ALTER TABLE attempts DROP CONSTRAINT attempts_job_id_fkey;
             ALTER TABLE attempts ADD CONSTRAINT attempts_job_id_fkey
               FOREIGN KEY(job_id) REFERENCES unrelated_jobs(job_id)",
            )
            .expect("test-only misdirected foreign key");
        assert!(matches!(
            PgAdmissionStore::connect(&dsn, &scratch.name),
            Err(PgAdmissionError::Unqualified)
        ));
        assert_eq!(scratch.count("jobs"), 0);
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_rejects_shallow_release_and_artifact_owner_constraints() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification required");
        let mut release = Scratch::new(&dsn);
        release.qualify();
        assert!(PgAdmissionStore::connect(&dsn, &release.name).is_ok());
        release.admin.batch_execute(
            "ALTER TABLE job_runtime_release_effects DROP CONSTRAINT job_runtime_release_effects_effect_id_key"
        ).expect("test-only weakened release uniqueness");
        assert!(matches!(
            PgAdmissionStore::connect(&dsn, &release.name),
            Err(PgAdmissionError::Unqualified)
        ));

        let mut artifact = Scratch::new(&dsn);
        artifact.qualify();
        assert!(PgAdmissionStore::connect(&dsn, &artifact.name).is_ok());
        artifact
            .admin
            .batch_execute(
                "ALTER TABLE artifacts DROP CONSTRAINT artifacts_attempt_id_kind_relative_path_key",
            )
            .expect("test-only weakened artifact uniqueness");
        assert!(matches!(
            PgAdmissionStore::connect(&dsn, &artifact.name),
            Err(PgAdmissionError::Unqualified)
        ));
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_native_atomic_admission_replay_fence_and_rollback() {
        let dsn = physical_pg_test_dsn();
        let mut scratch = Scratch::new(&dsn);
        let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        let a = payload("request-A", "job-A", "workspace-A", 2);
        assert!(matches!(
            store.admit(&a),
            Err(PgAdmissionError::Unqualified)
        ));
        assert_eq!(scratch.count("jobs"), 0, "no write before PG qualification");
        scratch.qualify();
        for (name, raw) in [
            ("workspace", "null"),
            ("plan", "[]"),
            ("workspace", r#"{"revision":1,"revision":2}"#),
            ("plan", r#"{"plan":{"timeoutMs":1000,"timeoutMs":2000}}"#),
            ("workspace", r#"{"nested":[{"a":1,"a":2}]}"#),
        ] {
            let mut invalid = a.clone();
            if name == "workspace" {
                invalid.workspace_snapshot_json = raw.into();
            } else {
                invalid.execution_plan_json = raw.into();
            }
            assert!(matches!(
                store.admit(&invalid),
                Err(PgAdmissionError::InvalidInput)
            ));
            assert_eq!(scratch.count("jobs"), 0, "invalid JSON persisted a PG Job");
        }
        assert_eq!(
            store.admit(&a).unwrap(),
            PgAdmissionOutcome::Created("job-A".into())
        );
        assert_eq!(
            store.admit(&a).unwrap(),
            PgAdmissionOutcome::Existing("job-A".into())
        );
        assert_eq!(scratch.count("jobs"), 1);
        assert_eq!(scratch.count("attempts"), 1);
        assert_eq!(scratch.count("concurrency_reservations"), 1);
        assert_eq!(scratch.count("idempotency_keys"), 1);
        assert_eq!(scratch.count("job_events"), 3);
        // A release Effect attached to the same ordinary Job is conflicting
        // provenance, NOT an unrelated Effect or a valid ordinary replay.
        // Preserve exact operation identity instead of accepting corruption.
        scratch
            .admin
            .execute(
                "INSERT INTO job_runtime_release_effects(job_id,effect_id,contract,request_digest,workspace_id,commit_revision,candidate_manifest_digest,expected_tool_count,receipt_path,binding_digest) VALUES($1,'effect-fixture','release-v1','test-request','ws-fixture','revision-fixture','manifest-fixture',0,'effect-receipt','effect-binding')",
                &[&a.job_id],
            )
            .unwrap();
        assert!(matches!(
            store.admit(&a),
            Err(PgAdmissionError::IdempotencyConflict)
        ));
        let mut conflicting_during_effect = a.clone();
        conflicting_during_effect.request_digest = "sha256:other-request".into();
        assert!(matches!(
            store.admit(&conflicting_during_effect),
            Err(PgAdmissionError::IdempotencyConflict)
        ));
        assert!(matches!(
            store.admit(&payload(
                "new-during-effect",
                "job-forbidden",
                "other-ws",
                2
            )),
            Err(PgAdmissionError::PendingEffect)
        ));
        assert_eq!(scratch.count("jobs"), 1);
        assert_eq!(scratch.count("job_events"), 3);
        scratch
            .admin
            .execute(
                "DELETE FROM job_runtime_release_effects WHERE job_id=$1",
                &[&a.job_id],
            )
            .unwrap();
        let mut conflict = a.clone();
        conflict.request_digest = "sha256:different-request".into();
        assert!(matches!(
            store.admit(&conflict),
            Err(PgAdmissionError::IdempotencyConflict)
        ));
        assert!(matches!(
            store.admit(&payload("request-B", "job-B", "workspace-A", 2)),
            Ok(PgAdmissionOutcome::Created(_))
        ));
        assert!(matches!(
            store.admit(&payload(
                "request-B-global",
                "job-B-global",
                "workspace-B",
                1
            )),
            Ok(PgAdmissionOutcome::Created(_))
        ));
        assert_eq!(
            scratch.count("job_allocations"),
            0,
            "pending Jobs consumed physical resources"
        );

        // A row uniqueness error after inserting Job must rollback every
        // consumer-visible part of this admission.
        let mut duplicate_attempt = payload("request-C", "job-C", "workspace-B", 2);
        duplicate_attempt.attempt_id = a.attempt_id.clone();
        assert!(matches!(
            store.admit(&duplicate_attempt),
            Err(PgAdmissionError::Database(_))
        ));
        assert_eq!(scratch.count("jobs"), 3);
        assert_eq!(scratch.count("attempts"), 3);
        assert_eq!(scratch.count("idempotency_keys"), 3);
        assert_eq!(scratch.count("job_events"), 9);
        assert_eq!(
            store
                .admit(&payload("request-D", "job-D", "workspace-B", 2))
                .unwrap(),
            PgAdmissionOutcome::Created("job-D".into())
        );
        assert_eq!(scratch.count("jobs"), 4);
        assert_eq!(scratch.count("job_events"), 12);
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_terminal_cas_replay_orphan_hold_and_atomic_rollback() {
        let dsn = physical_pg_test_dsn();
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        let input = payload("terminal-one", "job-terminal", "workspace-term", 2);
        store.admit(&input).unwrap();
        let terminal = PgTerminalNoArtifacts {
            attempt_id: input.attempt_id.clone(),
            expected_row_version: 0,
            terminal_state: "failed".into(),
            result_digest: "sha256:result".into(),
            reason_code: "NATIVE_PG_TEST".into(),
            exit_code: Some(3),
            finished_at_ms: 1234578,
            expected_source_sha256: input.expected_source_sha256.clone(),
        };
        let mut stale = terminal.clone();
        stale.expected_row_version = 1;
        assert!(matches!(
            store.commit_terminal_no_artifacts(&stale),
            Err(PgAdmissionError::Blocked)
        ));
        assert_eq!(scratch.count("job_events"), 3);
        assert_eq!(
            store.commit_terminal_no_artifacts(&terminal).unwrap(),
            PgTerminalOutcome::Committed(input.job_id.clone())
        );
        assert_eq!(
            store.commit_terminal_no_artifacts(&terminal).unwrap(),
            PgTerminalOutcome::Existing(input.job_id.clone())
        );
        assert_eq!(scratch.count("job_events"), 5);
        let state: String = scratch
            .admin
            .query_one(
                "SELECT state FROM concurrency_reservations WHERE attempt_id=$1",
                &[&input.attempt_id],
            )
            .unwrap()
            .get(0);
        assert_eq!(state, "released");
        let mut conflicting = terminal.clone();
        conflicting.result_digest = "sha256:other".into();
        assert!(matches!(
            store.commit_terminal_no_artifacts(&conflicting),
            Err(PgAdmissionError::IdempotencyConflict)
        ));
        assert_eq!(scratch.count("job_events"), 5);

        let orphan = payload("orphan", "job-orphan", "workspace-term", 2);
        store.admit(&orphan).unwrap();
        let hold = PgTerminalNoArtifacts {
            attempt_id: orphan.attempt_id.clone(),
            expected_row_version: 0,
            terminal_state: "orphaned".into(),
            result_digest: "sha256:orphan".into(),
            reason_code: "ORPHAN".into(),
            exit_code: None,
            finished_at_ms: 1234580,
            expected_source_sha256: input.expected_source_sha256.clone(),
        };
        store.commit_terminal_no_artifacts(&hold).unwrap();
        let held: String = scratch
            .admin
            .query_one(
                "SELECT state FROM concurrency_reservations WHERE attempt_id=$1",
                &[&orphan.attempt_id],
            )
            .unwrap()
            .get(0);
        assert_eq!(held, "held_orphaned");
        assert!(matches!(
            store.admit(&payload("after-orphan", "job-after", "workspace-term", 2)),
            Ok(PgAdmissionOutcome::Created(_))
        ));
        assert_eq!(scratch.count("jobs"), 3);
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_stale_attempt_cannot_terminalize_current_job() {
        let dsn = physical_pg_test_dsn();
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        let input = payload("stale-terminal", "job-stale-terminal", "workspace-stale", 2);
        store.admit(&input).unwrap();
        scratch.admin.execute(
            "INSERT INTO attempts(attempt_id,job_id,attempt_number,state,termination_intent,launch_token_digest,bundle_path,unit_name,created_at_ms,row_version) VALUES($1,$2,2,'accepted','natural','launch-new','/nonproduction/new','newer.service',$3,0)",
            &[&"attempt-newer", &input.job_id, &input.created_at_ms],
        ).unwrap();
        scratch
            .admin
            .execute(
                "UPDATE jobs SET current_attempt_id='attempt-newer' WHERE job_id=$1",
                &[&input.job_id],
            )
            .unwrap();

        let old_attempt = PgTerminalNoArtifacts {
            attempt_id: input.attempt_id.clone(),
            expected_row_version: 0,
            terminal_state: "failed".into(),
            result_digest: "sha256:stale".into(),
            reason_code: "STALE_ATTEMPT".into(),
            exit_code: Some(5),
            finished_at_ms: input.created_at_ms + 1,
            expected_source_sha256: input.expected_source_sha256.clone(),
        };
        assert!(matches!(
            store.commit_terminal_no_artifacts(&old_attempt),
            Err(PgAdmissionError::Blocked)
        ));
        assert_eq!(scratch.count("job_events"), 3, "no stale terminal event");
        let state: String = scratch
            .admin
            .query_one(
                "SELECT state FROM attempts WHERE attempt_id=$1",
                &[&input.attempt_id],
            )
            .unwrap()
            .get(0);
        assert_eq!(state, "accepted", "old Attempt must remain unchanged");
        let job = scratch
            .admin
            .query_one(
                "SELECT resolution,current_attempt_id FROM jobs WHERE job_id=$1",
                &[&input.job_id],
            )
            .unwrap();
        let resolution: Option<String> = job.get(0);
        let current: Option<String> = job.get(1);
        assert_eq!((resolution, current), (None, Some("attempt-newer".into())));
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_artifact_bearing_terminal_is_denied_until_full_owner_exists() {
        let dsn = physical_pg_test_dsn();
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        let input = payload("has-artifact", "job-artifact", "workspace-artifact", 1);
        store.admit(&input).unwrap();
        scratch
            .admin
            .execute(
                "INSERT INTO artifacts(artifact_id,job_id,attempt_id) VALUES('artifact-test',$1,$2)",
                &[&input.job_id, &input.attempt_id],
            )
            .unwrap();
        let terminal = PgTerminalNoArtifacts {
            attempt_id: input.attempt_id.clone(),
            expected_row_version: 0,
            terminal_state: "failed".into(),
            result_digest: "sha256:result".into(),
            reason_code: "ARTIFACT_STOP".into(),
            exit_code: Some(1),
            finished_at_ms: 1234599,
            expected_source_sha256: input.expected_source_sha256.clone(),
        };
        assert!(matches!(
            store.commit_terminal_no_artifacts(&terminal),
            Err(PgAdmissionError::Blocked)
        ));
        let standing: String = scratch
            .admin
            .query_one(
                "SELECT state FROM attempts WHERE attempt_id=$1",
                &[&input.attempt_id],
            )
            .unwrap()
            .get(0);
        assert_eq!(standing, "accepted");
        assert_eq!(scratch.count("job_events"), 3);
        assert_eq!(scratch.count("concurrency_reservations"), 1);
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_STAGE_TEST_DSN historical-stage qualification"]
    fn historical_pg_stage_is_not_an_admission_authority() {
        let dsn = historical_pg_stage_test_dsn();
        let mut inspector = Client::connect(&dsn, NoTls).unwrap();
        let before: i64 = inspector
            .query_one("SELECT count(*) FROM rw12_stage_cutover_r1.jobs", &[])
            .unwrap()
            .get(0);
        let row=inspector.query_one(
            "SELECT state,source_sha256,promotion_allowed FROM rw12_stage_cutover_r1._stage_control WHERE id='source'",
            &[]).unwrap();
        let state: String = row.get(0);
        let source: String = row.get(1);
        let permitted: bool = row.get(2);
        assert_eq!(state, "VERIFIED_NON_AUTHORITY");
        assert!(!permitted);
        assert_eq!(source.len(), 64, "staged source identity exists");
        // A historical row-exact import is not a durable writer schema:
        // fail at connect before any operation can even be admitted.
        assert!(matches!(
            PgAdmissionStore::connect(&dsn, "rw12_stage_cutover_r1"),
            Err(PgAdmissionError::Unqualified)
        ));
        let after: i64 = inspector
            .query_one("SELECT count(*) FROM rw12_stage_cutover_r1.jobs", &[])
            .unwrap()
            .get(0);
        assert_eq!(before, after);
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_cancel_commit_readback_is_exact_and_fail_closed_after_ack_loss() {
        let dsn = physical_pg_test_dsn();
        let mut scratch = Scratch::new(&dsn);
        let mut writer = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        let mut observer = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        let input = payload("readback-cancel", "job-readback", "ws-readback", 1);
        let intent = PgCancelIntent {
            job_id: input.job_id.clone(),
            observed_at_ms: 1234600,
            expected_source_sha256: input.expected_source_sha256.clone(),
        };
        assert!(matches!(
            observer.observe_cancel_intent(&intent),
            Err(PgAdmissionError::Unqualified)
        ));
        scratch.qualify();
        writer.admit(&input).unwrap();
        assert_eq!(
            observer.observe_cancel_intent(&intent).unwrap(),
            PgCancelObservation::Inconclusive
        );
        writer.request_cancel_intent(&intent).unwrap();
        // Reconcile on a separate native PG connection after a simulated
        // loss of the write-side acknowledgement.
        assert_eq!(
            observer.observe_cancel_intent(&intent).unwrap(),
            PgCancelObservation::Confirmed(input.job_id.clone())
        );
        let mut wrong_request = intent.clone();
        wrong_request.observed_at_ms += 1;
        assert_eq!(
            observer.observe_cancel_intent(&wrong_request).unwrap(),
            PgCancelObservation::Inconclusive
        );
        scratch
            .admin
            .execute(
                "UPDATE concurrency_reservations SET state='held_orphaned' WHERE attempt_id=$1",
                &[&input.attempt_id],
            )
            .unwrap();
        assert_eq!(
            observer.observe_cancel_intent(&intent).unwrap(),
            PgCancelObservation::Inconclusive
        );
        scratch
            .admin
            .execute(
                "UPDATE concurrency_reservations SET state='active' WHERE attempt_id=$1",
                &[&input.attempt_id],
            )
            .unwrap();
        scratch.admin.execute(
            "UPDATE job_events SET detail_digest='sha256:tampered' WHERE job_id=$1 AND event_type='STOP_REQUESTED'",
            &[&input.job_id],
        ).unwrap();
        assert_eq!(
            observer.observe_cancel_intent(&intent).unwrap(),
            PgCancelObservation::Inconclusive
        );
        assert_eq!(scratch.count("job_events"), 4);
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_cancel_intent_is_atomic_replayable_and_never_implies_dispatch_stopped() {
        let dsn = physical_pg_test_dsn();
        let mut scratch = Scratch::new(&dsn);
        let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        let first = payload("cancel-before-dispatch", "job-cancel-accepted", "ws-a", 2);
        let cancel = PgCancelIntent {
            job_id: first.job_id.clone(),
            observed_at_ms: 1234569,
            expected_source_sha256: first.expected_source_sha256.clone(),
        };
        assert!(matches!(
            store.request_cancel_intent(&cancel),
            Err(PgAdmissionError::Unqualified)
        ));
        scratch.qualify();
        store.admit(&first).unwrap();
        assert_eq!(
            store.request_cancel_intent(&cancel).unwrap(),
            PgCancelOutcome::IntentRecorded(first.job_id.clone())
        );
        assert_eq!(
            store.request_cancel_intent(&cancel).unwrap(),
            PgCancelOutcome::Existing(first.job_id.clone())
        );
        let row = scratch.admin.query_one(
            "SELECT j.desired_state,j.resolution,a.state,a.termination_intent,r.state FROM jobs j JOIN attempts a ON a.job_id=j.job_id JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id WHERE j.job_id=$1",
            &[&first.job_id],
        ).unwrap();
        assert_eq!(row.get::<_, String>(0), "cancelled");
        assert_eq!(row.get::<_, Option<String>>(1), None);
        assert_eq!(row.get::<_, String>(2), "accepted");
        assert_eq!(row.get::<_, String>(3), "stop_requested");
        assert_eq!(row.get::<_, String>(4), "active");
        assert_eq!(scratch.count("job_events"), 4);
        assert!(matches!(
            store.admit(&payload("new-job", "new-job", "ws-a", 2)),
            Ok(PgAdmissionOutcome::Created(_))
        ));
        let wrong_source = PgCancelIntent {
            expected_source_sha256: "b".repeat(64),
            ..cancel
        };
        assert!(matches!(
            store.request_cancel_intent(&wrong_source),
            Err(PgAdmissionError::Unqualified)
        ));
        assert_eq!(scratch.count("job_events"), 7);
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_cancel_intent_running_orphan_and_missing_reservation_fences() {
        let dsn = physical_pg_test_dsn();
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        let running = payload("cancel-running", "job-running", "ws-a", 3);
        store.admit(&running).unwrap();
        scratch
            .admin
            .execute(
                "UPDATE attempts SET state='running',row_version=row_version+1 WHERE attempt_id=$1",
                &[&running.attempt_id],
            )
            .unwrap();
        let cancel = PgCancelIntent {
            job_id: running.job_id.clone(),
            observed_at_ms: 1234570,
            expected_source_sha256: running.expected_source_sha256.clone(),
        };
        assert_eq!(
            store.request_cancel_intent(&cancel).unwrap(),
            PgCancelOutcome::IntentRecorded(running.job_id.clone())
        );
        let state: String = scratch
            .admin
            .query_one(
                "SELECT state FROM attempts WHERE attempt_id=$1",
                &[&running.attempt_id],
            )
            .unwrap()
            .get(0);
        assert_eq!(state, "stopping");
        assert_eq!(
            store.request_cancel_intent(&cancel).unwrap(),
            PgCancelOutcome::Existing(running.job_id.clone())
        );
        let terminal = PgTerminalNoArtifacts {
            attempt_id: running.attempt_id.clone(),
            expected_row_version: 2,
            terminal_state: "cancelled".into(),
            result_digest: "sha256:stopped-by-runner".into(),
            reason_code: "PG_CANCEL_RUNNER_OBSERVED".into(),
            exit_code: None,
            finished_at_ms: 1234571,
            expected_source_sha256: running.expected_source_sha256.clone(),
        };
        assert_eq!(
            store.commit_terminal_no_artifacts(&terminal).unwrap(),
            PgTerminalOutcome::Committed(running.job_id.clone())
        );
        assert_eq!(
            store.request_cancel_intent(&cancel).unwrap(),
            PgCancelOutcome::Existing(running.job_id.clone())
        );
        let released: String = scratch
            .admin
            .query_one(
                "SELECT state FROM concurrency_reservations WHERE attempt_id=$1",
                &[&running.attempt_id],
            )
            .unwrap()
            .get(0);
        assert_eq!(released, "released");

        let orphan = payload("cancel-orphan", "job-orphan", "ws-a", 3);
        store.admit(&orphan).unwrap();
        store
            .commit_terminal_no_artifacts(&PgTerminalNoArtifacts {
                attempt_id: orphan.attempt_id.clone(),
                expected_row_version: 0,
                terminal_state: "orphaned".into(),
                result_digest: "sha256:orphan".into(),
                reason_code: "ORPHAN_OBSERVED".into(),
                exit_code: None,
                finished_at_ms: 1234572,
                expected_source_sha256: orphan.expected_source_sha256.clone(),
            })
            .unwrap();
        let orphan_cancel = PgCancelIntent {
            job_id: orphan.job_id.clone(),
            observed_at_ms: 1234573,
            expected_source_sha256: orphan.expected_source_sha256.clone(),
        };
        assert_eq!(
            store.request_cancel_intent(&orphan_cancel).unwrap(),
            PgCancelOutcome::IntentRecorded(orphan.job_id.clone())
        );
        let orphan_row=scratch.admin.query_one(
            "SELECT j.resolution,j.desired_state,a.state,a.termination_intent,r.state FROM jobs j JOIN attempts a ON a.job_id=j.job_id JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id WHERE j.job_id=$1",
            &[&orphan.job_id],
        ).unwrap();
        assert_eq!(orphan_row.get::<_, String>(0), "orphaned");
        assert_eq!(orphan_row.get::<_, String>(1), "cancelled");
        assert_eq!(orphan_row.get::<_, String>(2), "orphaned");
        assert_eq!(orphan_row.get::<_, String>(3), "stop_requested");
        assert_eq!(orphan_row.get::<_, String>(4), "held_orphaned");
        assert_eq!(
            store.request_cancel_intent(&orphan_cancel).unwrap(),
            PgCancelOutcome::Existing(orphan.job_id.clone())
        );

        let invalid = payload("missing-reservation", "job-missing", "ws-b", 3);
        store.admit(&invalid).unwrap();
        scratch
            .admin
            .execute(
                "DELETE FROM concurrency_reservations WHERE attempt_id=$1",
                &[&invalid.attempt_id],
            )
            .unwrap();
        let before = scratch.count("job_events");
        let failed = PgCancelIntent {
            job_id: invalid.job_id.clone(),
            observed_at_ms: 1234574,
            expected_source_sha256: invalid.expected_source_sha256.clone(),
        };
        assert!(matches!(
            store.request_cancel_intent(&failed),
            Err(PgAdmissionError::Blocked)
        ));
        let desired: String = scratch
            .admin
            .query_one(
                "SELECT desired_state FROM jobs WHERE job_id=$1",
                &[&invalid.job_id],
            )
            .unwrap()
            .get(0);
        assert_eq!(desired, "run");
        assert_eq!(scratch.count("job_events"), before);
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_admission_readback_is_exact_and_never_claims_absence() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification required");
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        let a = payload("ack-lost", "job-ack-lost", "ws-ack-lost", 2);
        let mut observer = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        assert_eq!(
            observer.observe_admission(&a).unwrap(),
            PgAdmissionObservation::Inconclusive,
            "absence must not prove that the original COMMIT did not happen"
        );

        let mut writer = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        assert_eq!(
            writer.admit(&a).unwrap(),
            PgAdmissionOutcome::Created(a.job_id.clone())
        );
        // Treat writer COMMIT acknowledgement as lost. Read back on an
        // independent qualified connection without issuing a second write.
        assert_eq!(
            observer.observe_admission(&a).unwrap(),
            PgAdmissionObservation::Confirmed(a.job_id.clone())
        );
        assert_eq!(scratch.count("jobs"), 1);
        assert_eq!(scratch.count("attempts"), 1);
        assert_eq!(scratch.count("job_events"), 3);

        let mut conflicting = a.clone();
        conflicting.request_digest = "sha256:altered-request".into();
        assert_eq!(
            observer.observe_admission(&conflicting).unwrap(),
            PgAdmissionObservation::Inconclusive
        );
        conflicting = a.clone();
        conflicting.operation_digest = "sha256:altered-operation".into();
        assert_eq!(
            observer.observe_admission(&conflicting).unwrap(),
            PgAdmissionObservation::Inconclusive
        );
        conflicting = a.clone();
        conflicting.attempt_id = "attempt-unrelated".into();
        assert_eq!(
            observer.observe_admission(&conflicting).unwrap(),
            PgAdmissionObservation::Inconclusive
        );

        // A missing capacity reservation is independently disqualifying,
        // even while the complete original event sequence remains intact.
        scratch
            .admin
            .execute(
                "DELETE FROM concurrency_reservations WHERE attempt_id=$1",
                &[&a.attempt_id],
            )
            .unwrap();
        assert_eq!(
            observer.observe_admission(&a).unwrap(),
            PgAdmissionObservation::Inconclusive
        );
        scratch.admin.execute(
            "INSERT INTO concurrency_reservations(reservation_id,attempt_id,global_limit,state,acquired_at_ms,state_observed_at_ms) VALUES($1,$2,$3,'active',$4,$4)",
            &[&a.reservation_id,&a.attempt_id,&i64::from(a.global_limit),&a.created_at_ms],
        ).unwrap();
        assert_eq!(
            observer.observe_admission(&a).unwrap(),
            PgAdmissionObservation::Confirmed(a.job_id.clone()),
            "restoring the original reservation must restore the complete witness"
        );

        // Conversely, the key/Job/Attempt/reservation rows are not sufficient
        // without all original admission events.
        scratch
            .admin
            .execute(
                "DELETE FROM job_events WHERE job_id=$1 AND event_sequence=2",
                &[&a.job_id],
            )
            .unwrap();
        assert_eq!(
            observer.observe_admission(&a).unwrap(),
            PgAdmissionObservation::Inconclusive
        );
        assert_eq!(scratch.count("jobs"), 1);
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_runner_bound_exact_dispatch_becomes_running() {
        let dsn = physical_pg_test_dsn();
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        let input = payload("bound", "job-bound", "ws-bound", 2);
        store.admit(&input).unwrap();
        allocate_fixture(&mut scratch, &input);
        let bundle = format!("sha256:{}", "b".repeat(64));
        store
            .commit_bundle_ready_pg(&PgBundleReady {
                attempt_id: input.attempt_id.clone(),
                expected_row_version: 0,
                bundle_digest: bundle.clone(),
                observed_at_ms: input.created_at_ms + 1,
                expected_source_sha256: input.expected_source_sha256.clone(),
            })
            .unwrap();
        store
            .mark_dispatch_issued_pg(
                &PgDispatchIssued {
                    attempt_id: input.attempt_id.clone(),
                    expected_row_version: 1,
                    expected_bundle_digest: bundle.clone(),
                    observed_at_ms: input.created_at_ms + 2,
                    expected_source_sha256: input.expected_source_sha256.clone(),
                },
                None,
                None,
            )
            .unwrap();
        let witness = PgRunnerBound {
            attempt_id: input.attempt_id.clone(),
            expected_row_version: 2,
            expected_bundle_digest: bundle,
            runner_start_digest: format!("sha256:{}", "c".repeat(64)),
            native_invocation_id: "invocation-one".into(),
            observed_at_ms: input.created_at_ms + 3,
            expected_source_sha256: input.expected_source_sha256.clone(),
        };
        let mut invalid = witness.clone();
        invalid.expected_source_sha256 = "f".repeat(64);
        assert!(matches!(
            store.mark_runner_bound_pg(&invalid),
            Err(PgAdmissionError::Unqualified)
        ));
        assert_eq!(store.mark_runner_bound_pg(&witness).unwrap(), 3);
        let row = scratch
            .admin
            .query_one(
                "SELECT state,row_version,started_at_ms FROM attempts WHERE attempt_id=$1",
                &[&input.attempt_id],
            )
            .unwrap();
        assert_eq!(row.get::<_, String>(0), "running");
        assert_eq!(row.get::<_, i64>(1), 3);
        assert_eq!(row.get::<_, Option<i64>>(2), Some(witness.observed_at_ms));
        let event = scratch.admin.query_one(
            "SELECT event_type,origin,previous_state,new_state,reason_code,detail_json FROM job_events WHERE job_id=$1 AND event_sequence=6",
            &[&input.job_id],
        ).unwrap();
        assert_eq!(event.get::<_, String>(0), "RUNNER_BOUND");
        assert_eq!(event.get::<_, String>(1), "SYSTEM_OBSERVED");
        assert_eq!(
            event.get::<_, Option<String>>(2).as_deref(),
            Some("starting")
        );
        assert_eq!(
            event.get::<_, Option<String>>(3).as_deref(),
            Some("running")
        );
        assert_eq!(event.get::<_, String>(4), "SUPERVISOR_OWNER_MATCHED");
        let detail: serde_json::Value = serde_json::from_str(&event.get::<_, String>(5)).unwrap();
        assert_eq!(detail["runnerStartDigest"], witness.runner_start_digest);
        assert_eq!(detail["invocationId"], witness.native_invocation_id);
        assert_eq!(scratch.count("job_events"), 6);
        assert!(matches!(
            store.mark_runner_bound_pg(&witness),
            Err(PgAdmissionError::Blocked)
        ));
        assert_eq!(scratch.count("job_events"), 6);

        // Existing terminal CAS, reservation release and replay must retain
        // their original semantics after the new positive native start.
        let terminal = PgTerminalNoArtifacts {
            attempt_id: input.attempt_id.clone(),
            expected_row_version: 3,
            terminal_state: "succeeded".into(),
            result_digest: format!("sha256:{}", "d".repeat(64)),
            reason_code: "PROCESS_EXIT_ZERO".into(),
            exit_code: Some(0),
            finished_at_ms: witness.observed_at_ms + 1,
            expected_source_sha256: input.expected_source_sha256.clone(),
        };
        assert_eq!(
            store.commit_terminal_no_artifacts(&terminal).unwrap(),
            PgTerminalOutcome::Committed(input.job_id.clone()),
        );
        assert_eq!(
            store.commit_terminal_no_artifacts(&terminal).unwrap(),
            PgTerminalOutcome::Existing(input.job_id.clone()),
        );
        let final_state = scratch
            .admin
            .query_one(
                "SELECT j.resolution,j.current_attempt_id,r.state FROM jobs j \
             JOIN attempts a ON a.job_id=j.job_id \
             JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id WHERE j.job_id=$1",
                &[&input.job_id],
            )
            .unwrap();
        assert_eq!(
            final_state.get::<_, Option<String>>(0).as_deref(),
            Some("succeeded")
        );
        assert_eq!(final_state.get::<_, Option<String>>(1), None);
        assert_eq!(final_state.get::<_, String>(2), "released");
        assert_eq!(scratch.count("job_events"), 8);

        // Cancellation between dispatch intent and positive start must win:
        // even a guessed current row version cannot revive the Attempt.
        let cancelled = payload(
            "cancel-after-issue",
            "job-cancel-after",
            "ws-cancel-after",
            2,
        );
        store.admit(&cancelled).unwrap();
        allocate_fixture(&mut scratch, &cancelled);
        let cancelled_bundle = format!("sha256:{}", "e".repeat(64));
        store
            .commit_bundle_ready_pg(&PgBundleReady {
                attempt_id: cancelled.attempt_id.clone(),
                expected_row_version: 0,
                bundle_digest: cancelled_bundle.clone(),
                observed_at_ms: cancelled.created_at_ms + 1,
                expected_source_sha256: cancelled.expected_source_sha256.clone(),
            })
            .unwrap();
        store
            .mark_dispatch_issued_pg(
                &PgDispatchIssued {
                    attempt_id: cancelled.attempt_id.clone(),
                    expected_row_version: 1,
                    expected_bundle_digest: cancelled_bundle.clone(),
                    observed_at_ms: cancelled.created_at_ms + 2,
                    expected_source_sha256: cancelled.expected_source_sha256.clone(),
                },
                None,
                None,
            )
            .unwrap();
        store
            .request_cancel_intent(&PgCancelIntent {
                job_id: cancelled.job_id.clone(),
                observed_at_ms: cancelled.created_at_ms + 3,
                expected_source_sha256: cancelled.expected_source_sha256.clone(),
            })
            .unwrap();
        let revoked = PgRunnerBound {
            attempt_id: cancelled.attempt_id.clone(),
            expected_row_version: 3,
            expected_bundle_digest: cancelled_bundle,
            runner_start_digest: format!("sha256:{}", "c".repeat(64)),
            native_invocation_id: "invocation-cancelled".into(),
            observed_at_ms: cancelled.created_at_ms + 4,
            expected_source_sha256: cancelled.expected_source_sha256.clone(),
        };
        assert!(matches!(
            store.mark_runner_bound_pg(&revoked),
            Err(PgAdmissionError::Blocked),
        ));
        let cancelled_state = scratch
            .admin
            .query_one(
                "SELECT a.state,COUNT(e.event_id) FILTER(WHERE e.event_type='RUNNER_BOUND') \
             FROM attempts a LEFT JOIN job_events e ON e.attempt_id=a.attempt_id \
             WHERE a.attempt_id=$1 GROUP BY a.state",
                &[&cancelled.attempt_id],
            )
            .unwrap();
        assert_eq!(cancelled_state.get::<_, String>(0), "stopping");
        assert_eq!(cancelled_state.get::<_, i64>(1), 0);
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_bundle_and_dispatch_commit_before_external_effect() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification required");
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        let a = payload("dispatch-request", "dispatch-job", "dispatch-ws", 2);
        assert_eq!(
            store.admit(&a).unwrap(),
            PgAdmissionOutcome::Created(a.job_id.clone())
        );
        allocate_fixture(&mut scratch, &a);
        let digest = format!("sha256:{}", "b".repeat(64));
        let issued = PgDispatchIssued {
            attempt_id: a.attempt_id.clone(),
            expected_row_version: 1,
            expected_bundle_digest: digest.clone(),
            observed_at_ms: a.created_at_ms + 2,
            expected_source_sha256: a.expected_source_sha256.clone(),
        };
        assert!(matches!(
            store.mark_dispatch_issued_pg(&issued, None, None),
            Err(PgAdmissionError::Blocked)
        ));
        assert_eq!(scratch.count("job_events"), 3);
        let prepared = PgBundleReady {
            attempt_id: a.attempt_id.clone(),
            expected_row_version: 0,
            bundle_digest: digest.clone(),
            observed_at_ms: a.created_at_ms + 1,
            expected_source_sha256: a.expected_source_sha256.clone(),
        };
        assert_eq!(store.commit_bundle_ready_pg(&prepared).unwrap(), 1);
        assert!(matches!(
            store.commit_bundle_ready_pg(&prepared),
            Err(PgAdmissionError::Blocked)
        ));
        assert_eq!(scratch.count("job_events"), 4);
        // Wrong source cut and missing original bundle evidence must never
        // permit an attempted dispatch, even when the Attempt row looks ready.
        let mut wrong_source = issued.clone();
        wrong_source.expected_source_sha256 = "f".repeat(64);
        assert!(matches!(
            store.mark_dispatch_issued_pg(&wrong_source, None, None),
            Err(PgAdmissionError::Unqualified)
        ));
        let original_detail = serde_json::json!({"bundleDigest": digest}).to_string();
        let original_digest = format!(
            "sha256:{}",
            hex::encode(Sha256::digest(original_detail.as_bytes()))
        );
        scratch.admin.execute(
            "UPDATE job_events SET detail_digest='sha256:tampered'              WHERE job_id=$1 AND event_type='BUNDLE_READY'",
            &[&a.job_id],
        ).unwrap();
        assert!(matches!(
            store.mark_dispatch_issued_pg(&issued, None, None),
            Err(PgAdmissionError::Blocked)
        ));
        assert_eq!(scratch.count("job_events"), 4);
        scratch.admin.execute(
            "UPDATE job_events SET detail_digest=$1              WHERE job_id=$2 AND event_type='BUNDLE_READY'",
            &[&original_digest, &a.job_id],
        ).unwrap();
        assert_eq!(
            store.mark_dispatch_issued_pg(&issued, None, None).unwrap(),
            2
        );
        assert_eq!(scratch.count("job_events"), 5);
        assert!(matches!(
            store.mark_dispatch_issued_pg(&issued, None, None),
            Err(PgAdmissionError::Blocked)
        ));
        assert_eq!(scratch.count("job_events"), 5);
        let row = scratch
            .admin
            .query_one(
                "SELECT state,row_version,bundle_digest FROM attempts WHERE attempt_id=$1",
                &[&a.attempt_id],
            )
            .unwrap();
        assert_eq!(row.get::<_, String>(0), "starting");
        assert_eq!(row.get::<_, i64>(1), 2);
        assert_eq!(
            row.get::<_, Option<String>>(2).as_deref(),
            Some(digest.as_str())
        );
        let event = scratch.admin.query_one(
            "SELECT origin,reason_code,previous_state,new_state FROM job_events WHERE job_id=$1 AND event_sequence=5",
            &[&a.job_id],
        ).unwrap();
        assert_eq!(event.get::<_, String>(0), "SYSTEM_DERIVED");
        assert_eq!(event.get::<_, String>(1), "AT_MOST_ONCE_BOUNDARY_COMMITTED");
        assert_eq!(
            event.get::<_, Option<String>>(2).as_deref(),
            Some("accepted")
        );
        assert_eq!(
            event.get::<_, Option<String>>(3).as_deref(),
            Some("starting")
        );
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_cancellation_blocks_unissued_dispatch_without_false_terminal() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification required");
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        let a = payload("cancel-pre-dispatch", "cancel-job", "cancel-ws", 2);
        assert_eq!(
            store.admit(&a).unwrap(),
            PgAdmissionOutcome::Created(a.job_id.clone())
        );
        allocate_fixture(&mut scratch, &a);
        let digest = format!("sha256:{}", "d".repeat(64));
        let ready = PgBundleReady {
            attempt_id: a.attempt_id.clone(),
            expected_row_version: 0,
            bundle_digest: digest.clone(),
            observed_at_ms: a.created_at_ms + 1,
            expected_source_sha256: a.expected_source_sha256.clone(),
        };
        assert_eq!(store.commit_bundle_ready_pg(&ready).unwrap(), 1);
        assert_eq!(
            store
                .request_cancel_intent(&PgCancelIntent {
                    job_id: a.job_id.clone(),
                    observed_at_ms: a.created_at_ms + 2,
                    expected_source_sha256: a.expected_source_sha256.clone(),
                })
                .unwrap(),
            PgCancelOutcome::IntentRecorded(a.job_id.clone())
        );
        let issued = PgDispatchIssued {
            attempt_id: a.attempt_id.clone(),
            expected_row_version: 2,
            expected_bundle_digest: digest.clone(),
            observed_at_ms: a.created_at_ms + 3,
            expected_source_sha256: a.expected_source_sha256.clone(),
        };
        assert!(matches!(
            store.mark_dispatch_issued_pg(&issued, None, None),
            Err(PgAdmissionError::Blocked)
        ));
        let row = scratch.admin.query_one(
            "SELECT a.state,j.desired_state,j.resolution,r.state FROM attempts a JOIN jobs j ON j.job_id=a.job_id JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id WHERE a.attempt_id=$1",
            &[&a.attempt_id],
        ).unwrap();
        assert_eq!(row.get::<_, String>(0), "accepted");
        assert_eq!(row.get::<_, String>(1), "cancelled");
        assert_eq!(row.get::<_, Option<String>>(2), None);
        assert_eq!(row.get::<_, String>(3), "active");
        assert_eq!(scratch.count("job_events"), 5);
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_clean_epoch_needs_no_old_sqlite_requests() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification required");
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        let mut pg = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        // This was an old SQLite request ID, but the owner explicitly
        // retired all old history. In a NEW PG epoch it is simply a new key.
        let request = payload("formerly-old-key", "new-pg-job", "new-workspace", 2);
        assert_eq!(
            pg.admit(&request).unwrap(),
            PgAdmissionOutcome::Created(request.job_id.clone())
        );
        assert_eq!(
            pg.admit(&request).unwrap(),
            PgAdmissionOutcome::Existing(request.job_id.clone())
        );
        let mut changed = request.clone();
        // A changed resolved physical Operation cannot redefine an existing
        // request key: the original replay is valid even after source drift.
        changed.operation_digest = "sha256:different-current-epoch-operation".into();
        assert_eq!(
            pg.admit(&changed).unwrap(),
            PgAdmissionOutcome::Existing(request.job_id.clone())
        );
        changed.request_digest = "sha256:different-current-epoch-request".into();
        assert!(matches!(
            pg.admit(&changed),
            Err(PgAdmissionError::IdempotencyConflict)
        ));
        assert_eq!(scratch.count("jobs"), 1);
        assert_eq!(scratch.count("attempts"), 1);
        assert_eq!(scratch.count("concurrency_reservations"), 1);
        assert_eq!(scratch.count("job_events"), 3);
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_readonly_job_projection_fences_stage_and_incoherent_terminal() {
        use crate::PgJobReadback;
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification required");
        let mut scratch = Scratch::new(&dsn);
        let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        let input = payload("readback-req", "readback-job", "readback-workspace", 2);
        assert!(matches!(
            store.observe_job_readonly(&input.job_id, &input.expected_source_sha256),
            Err(PgAdmissionError::Unqualified)
        ));
        scratch.qualify();
        assert_eq!(
            store
                .observe_job_readonly(&input.job_id, &input.expected_source_sha256)
                .unwrap(),
            PgJobReadback::Inconclusive,
        );
        store.admit(&input).unwrap();
        let events_before = scratch.count("job_events");
        let first = store
            .observe_job_readonly(&input.job_id, &input.expected_source_sha256)
            .unwrap();
        let PgJobReadback::Observed(first) = first else {
            panic!("admitted PG job must be read coherently");
        };
        assert_eq!(first.attempt_id, input.attempt_id);
        assert_eq!(first.attempt_state, "accepted");
        assert_eq!(first.resolution, None);
        assert_eq!(first.reservation_state, "active");
        // Source is still QUALIFIED_WRITER, but its physical epoch is no
        // longer operator-qualified. A restored/historical Job must not be
        // advertised through this API as current authoritative state.
        scratch
            .admin
            .execute(
                "UPDATE _stage_control SET promotion_allowed=false WHERE id='epoch'",
                &[],
            )
            .unwrap();
        assert!(matches!(
            store.observe_job_readonly(&input.job_id, &input.expected_source_sha256),
            Err(PgAdmissionError::Unqualified)
        ));
        scratch
            .admin
            .execute(
                "UPDATE _stage_control SET promotion_allowed=true WHERE id='epoch'",
                &[],
            )
            .unwrap();
        let true_epoch: String = scratch
            .admin
            .query_one(
                "SELECT source_sha256 FROM _stage_control WHERE id='epoch'",
                &[],
            )
            .unwrap()
            .get(0);
        scratch
            .admin
            .execute(
                "UPDATE _stage_control SET source_sha256=$1 WHERE id='epoch'",
                &[&"f".repeat(64)],
            )
            .unwrap();
        assert!(matches!(
            store.observe_job_readonly(&input.job_id, &input.expected_source_sha256),
            Err(PgAdmissionError::Unqualified)
        ));
        scratch
            .admin
            .execute(
                "UPDATE _stage_control SET source_sha256=$1 WHERE id='epoch'",
                &[&true_epoch],
            )
            .unwrap();
        assert!(matches!(
            store.observe_job_readonly(&input.job_id, &input.expected_source_sha256),
            Ok(PgJobReadback::Observed(_))
        ));
        assert_eq!(
            scratch.count("job_events"),
            events_before,
            "readback must not append effects"
        );
        assert!(matches!(
            store.observe_job_readonly(&input.job_id, &"f".repeat(64)),
            Err(PgAdmissionError::Unqualified)
        ));
        let cancel = PgCancelIntent {
            job_id: input.job_id.clone(),
            observed_at_ms: 1234570,
            expected_source_sha256: input.expected_source_sha256.clone(),
        };
        store.request_cancel_intent(&cancel).unwrap();
        let cancelling = store
            .observe_job_readonly(&input.job_id, &input.expected_source_sha256)
            .unwrap();
        let PgJobReadback::Observed(cancelling) = cancelling else {
            panic!("cancel intent must not erase the active Attempt");
        };
        assert_eq!(cancelling.desired_state, "cancelled");
        assert_eq!(cancelling.resolution, None);
        assert_eq!(cancelling.reservation_state, "active");
        store
            .commit_terminal_no_artifacts(&PgTerminalNoArtifacts {
                attempt_id: input.attempt_id.clone(),
                expected_row_version: 1,
                terminal_state: "cancelled".into(),
                result_digest: "sha256:terminal".into(),
                reason_code: "READBACK_TEST".into(),
                exit_code: None,
                finished_at_ms: 1234571,
                expected_source_sha256: input.expected_source_sha256.clone(),
            })
            .unwrap();
        let terminal = store
            .observe_job_readonly(&input.job_id, &input.expected_source_sha256)
            .unwrap();
        let PgJobReadback::Observed(terminal) = terminal else {
            panic!("verified PG terminal transaction must be projected");
        };
        assert_eq!(terminal.resolution.as_deref(), Some("cancelled"));
        assert_eq!(terminal.reservation_state, "released");
        assert_eq!(terminal.current_attempt_id, None);
        let original_digest: String = scratch
            .admin
            .query_one(
                "SELECT detail_digest FROM job_events WHERE job_id=$1 AND event_type='JOB_TERMINAL'",
                &[&input.job_id],
            )
            .unwrap()
            .get(0);
        scratch.admin.execute(
            "UPDATE job_events SET detail_digest='sha256:tampered' WHERE job_id=$1 AND event_type='JOB_TERMINAL'",
            &[&input.job_id],
        ).unwrap();
        assert_eq!(
            store
                .observe_job_readonly(&input.job_id, &input.expected_source_sha256)
                .unwrap(),
            PgJobReadback::Inconclusive,
        );
        scratch.admin.execute(
            "UPDATE job_events SET detail_digest=$1 WHERE job_id=$2 AND event_type='JOB_TERMINAL'",
            &[&original_digest, &input.job_id],
        ).unwrap();

        // A corrupt durable reservation must never yield a successful readback.
        scratch
            .admin
            .execute(
                "UPDATE concurrency_reservations SET state='active' WHERE attempt_id=$1",
                &[&input.attempt_id],
            )
            .unwrap();
        assert_eq!(
            store
                .observe_job_readonly(&input.job_id, &input.expected_source_sha256)
                .unwrap(),
            PgJobReadback::Inconclusive,
        );
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_artifact_metadata_terminal_is_atomic_replayable_and_rejects_corruption() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification required");
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        let first = payload(
            "artifact-request-one",
            "artifact-job-one",
            "artifact-workspace",
            2,
        );
        store.admit(&first).unwrap();
        let artifact = PgArtifactRegistration {
            artifact_id: "artifact-A".into(),
            kind: "stdout".into(),
            relative_path: "output/stdout.txt".into(),
            digest: format!("sha256:{}", "a".repeat(64)),
            media_type: "text/plain".into(),
            byte_length: 14,
            truncated: false,
            created_at_ms: 1234568,
        };
        let terminal = PgTerminalNoArtifacts {
            attempt_id: first.attempt_id.clone(),
            expected_row_version: 0,
            terminal_state: "failed".into(),
            result_digest: "sha256:result-with-artifact".into(),
            reason_code: "PG_ARTIFACT_TERMINAL_TEST".into(),
            exit_code: Some(1),
            finished_at_ms: 1234569,
            expected_source_sha256: first.expected_source_sha256.clone(),
        };
        let mut invalid = artifact.clone();
        invalid.relative_path = "../outside".into();
        assert!(matches!(
            store.commit_terminal_with_artifacts(&terminal, &[invalid]),
            Err(PgAdmissionError::InvalidInput)
        ));
        assert_eq!(scratch.count("artifacts"), 0);
        assert_eq!(scratch.count("job_events"), 3);
        assert_eq!(
            store
                .commit_terminal_with_artifacts(&terminal, std::slice::from_ref(&artifact))
                .unwrap(),
            PgTerminalOutcome::Committed(first.job_id.clone())
        );
        assert_eq!(scratch.count("artifacts"), 1);
        assert_eq!(scratch.count("job_events"), 5);
        assert_eq!(
            store
                .commit_terminal_with_artifacts(&terminal, std::slice::from_ref(&artifact))
                .unwrap(),
            PgTerminalOutcome::Existing(first.job_id.clone()),
            "identical replay never writes duplicate Artifact"
        );
        assert!(matches!(
            store.commit_terminal_no_artifacts(&terminal),
            Err(PgAdmissionError::Blocked)
        ));
        let mut corrupted = artifact.clone();
        corrupted.digest = format!("sha256:{}", "b".repeat(64));
        assert!(matches!(
            store.commit_terminal_with_artifacts(&terminal, &[corrupted]),
            Err(PgAdmissionError::IdempotencyConflict)
        ));
        let observed = store
            .observe_job_readonly(&first.job_id, &first.expected_source_sha256)
            .unwrap();
        assert!(matches!(observed, crate::PgJobReadback::Observed(_)));
        let current: String = scratch
            .admin
            .query_one(
                "SELECT digest FROM artifacts WHERE artifact_id=$1",
                &[&"artifact-A"],
            )
            .unwrap()
            .get(0);
        scratch
            .admin
            .execute(
                "UPDATE artifacts SET digest=$1 WHERE artifact_id=$2",
                &[&format!("sha256:{}", "c".repeat(64)), &"artifact-A"],
            )
            .unwrap();
        assert_eq!(
            store
                .observe_job_readonly(&first.job_id, &first.expected_source_sha256)
                .unwrap(),
            crate::PgJobReadback::Inconclusive,
            "existing terminal event must bind the exact Artifact manifest"
        );
        scratch
            .admin
            .execute(
                "UPDATE artifacts SET digest=$1 WHERE artifact_id=$2",
                &[&current, &"artifact-A"],
            )
            .unwrap();
        let second = payload(
            "artifact-request-two",
            "artifact-job-two",
            "another-workspace",
            2,
        );
        store.admit(&second).unwrap();
        let second_terminal = PgTerminalNoArtifacts {
            attempt_id: second.attempt_id.clone(),
            expected_row_version: 0,
            terminal_state: "failed".into(),
            result_digest: "sha256:second-result".into(),
            reason_code: "PG_DUPLICATE_ARTIFACT".into(),
            exit_code: Some(1),
            finished_at_ms: 1234570,
            expected_source_sha256: second.expected_source_sha256.clone(),
        };
        // Global Artifact ID collision rejects the WHOLE terminal transaction.
        assert!(matches!(
            store.commit_terminal_with_artifacts(&second_terminal, &[artifact]),
            Err(PgAdmissionError::Database(_))
        ));
        assert_eq!(scratch.count("artifacts"), 1);
        assert_eq!(
            scratch.count("job_events"),
            8,
            "second Job keeps only its 3 admission events"
        );
        let projection = store
            .observe_job_readonly(&second.job_id, &second.expected_source_sha256)
            .unwrap();
        let crate::PgJobReadback::Observed(projection) = projection else {
            panic!("failed artifact insert must not terminalize Attempt or free capacity");
        };
        assert_eq!(projection.resolution, None);
        assert_eq!(projection.attempt_state, "accepted");
        assert_eq!(projection.reservation_state, "active");
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_composed_admit_dispatch_artifact_terminal_is_one_consumer_chain() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification required");
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        let request = payload("chain-request", "chain-job", "chain-workspace", 2);
        assert_eq!(
            store.admit(&request).unwrap(),
            PgAdmissionOutcome::Created(request.job_id.clone())
        );
        allocate_fixture(&mut scratch, &request);
        let bundle = PgBundleReady {
            attempt_id: request.attempt_id.clone(),
            expected_row_version: 0,
            bundle_digest: format!("sha256:{}", "b".repeat(64)),
            observed_at_ms: 1234568,
            expected_source_sha256: request.expected_source_sha256.clone(),
        };
        assert_eq!(store.commit_bundle_ready_pg(&bundle).unwrap(), 1);
        let dispatch = PgDispatchIssued {
            attempt_id: request.attempt_id.clone(),
            expected_row_version: 1,
            expected_bundle_digest: bundle.bundle_digest,
            observed_at_ms: 1234569,
            expected_source_sha256: request.expected_source_sha256.clone(),
        };
        assert_eq!(
            store
                .mark_dispatch_issued_pg(&dispatch, None, None)
                .unwrap(),
            2
        );
        assert!(matches!(
            store.mark_dispatch_issued_pg(&dispatch, None, None),
            Err(PgAdmissionError::Blocked),
        ));
        let artifact = PgArtifactRegistration {
            artifact_id: "chain-artifact".into(),
            kind: "stdout".into(),
            relative_path: "output/chain.txt".into(),
            digest: format!("sha256:{}", "c".repeat(64)),
            media_type: "text/plain".into(),
            byte_length: 8,
            truncated: false,
            created_at_ms: 1234570,
        };
        let terminal = PgTerminalNoArtifacts {
            attempt_id: request.attempt_id.clone(),
            expected_row_version: 2,
            terminal_state: "failed".into(),
            result_digest: "sha256:chain-result".into(),
            reason_code: "CHAIN_TEST".into(),
            exit_code: Some(1),
            finished_at_ms: 1234571,
            expected_source_sha256: request.expected_source_sha256.clone(),
        };
        assert_eq!(
            store
                .commit_terminal_with_artifacts(&terminal, std::slice::from_ref(&artifact))
                .unwrap(),
            PgTerminalOutcome::Committed(request.job_id.clone()),
        );
        assert_eq!(
            scratch.count("job_events"),
            7,
            "admission 3, dispatch 2, terminal 2"
        );
        assert_eq!(scratch.count("artifacts"), 1);
        let outcome = store
            .observe_job_readonly(&request.job_id, &request.expected_source_sha256)
            .unwrap();
        let crate::PgJobReadback::Observed(snapshot) = outcome else {
            panic!("full PG lifecycle must remain coherently observable");
        };
        assert_eq!(snapshot.resolution.as_deref(), Some("failed"));
        assert_eq!(snapshot.reservation_state, "released");
        assert_eq!(snapshot.attempt_row_version, 3);
        assert_eq!(
            store
                .commit_terminal_with_artifacts(&terminal, &[artifact])
                .unwrap(),
            PgTerminalOutcome::Existing(request.job_id.clone()),
        );
        assert_eq!(
            scratch.count("job_events"),
            7,
            "retry may not append a second terminal"
        );
        assert_eq!(scratch.count("artifacts"), 1);
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_concurrent_duplicate_never_creates_second_job() {
        let dsn = physical_pg_test_dsn();
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        let gate = Arc::new(Barrier::new(5));
        let mut workers = Vec::new();
        for n in 0..4 {
            let dsn = dsn.clone();
            let schema = scratch.name.clone();
            let gate = gate.clone();
            workers.push(thread::spawn(move || {
                let mut store = PgAdmissionStore::connect(&dsn, &schema).unwrap();
                let request = payload("same-key", &format!("job-{n}"), "workspace-one", 2);
                gate.wait();
                store.admit(&request)
            }));
        }
        gate.wait();
        let mut created = 0usize;
        for worker in workers {
            match worker.join().unwrap() {
                Ok(PgAdmissionOutcome::Created(_)) => created += 1,
                Ok(PgAdmissionOutcome::Existing(_)) => (),
                Err(PgAdmissionError::Database(error))
                    if error.code()
                        == Some(&postgres::error::SqlState::T_R_SERIALIZATION_FAILURE) => {}
                unexpected => panic!("unsafe concurrent admission result: {unexpected:?}"),
            }
        }
        assert_eq!(created, 1);
        assert_eq!(scratch.count("jobs"), 1);
        assert_eq!(scratch.count("idempotency_keys"), 1);
        assert_eq!(scratch.count("attempts"), 1);
        assert_eq!(scratch.count("concurrency_reservations"), 1);
    }

    /// The same original PG issue cut must remain current at the later
    /// DISPATCH_ISSUED commit. Uses two actual PG connections and an isolated
    /// issuer SQL fixture, not a simulated in-memory flag or a native ACK.
    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_harness_issuer_current_at_dispatch_after_admission() {
        fn encoded(value: &serde_json::Value) -> (String, Vec<u8>) {
            let bytes = serde_json::to_vec(value).unwrap();
            (
                format!("sha256:{}", hex::encode(Sha256::digest(&bytes))),
                bytes,
            )
        }
        let dsn = physical_pg_test_dsn();
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        scratch
            .admin
            .batch_execute(
                "CREATE TABLE issuer_cut_fixture (
                run_id text NOT NULL, generation bigint NOT NULL,
                fence_digest text NOT NULL, live boolean NOT NULL,
                payload_digest text NOT NULL, payload_raw bytea NOT NULL,
                fence_raw bytea NOT NULL, intent_digest text NOT NULL,
                intent_raw bytea NOT NULL
            );
            CREATE FUNCTION harness_current_dispatch_cut(text,bigint,text)
            RETURNS TABLE(
                event_kind text,payload_digest text,payload_kind text,
                payload_size bigint,payload_raw bytea,
                fence_kind text,fence_size bigint,fence_raw bytea,
                intent_object_digest text,intent_kind text,intent_len bigint,
                intent_raw bytea
            ) LANGUAGE SQL AS $issuer$
                SELECT 'harness.tool-step-prepared'::text,
                       f.payload_digest, 'ordivon.harness-run-event-payload'::text,
                       octet_length(f.payload_raw)::bigint, f.payload_raw,
                       'harness-dispatch-fence'::text,
                       octet_length(f.fence_raw)::bigint, f.fence_raw,
                       f.intent_digest, 'harness-tool-step-intent'::text,
                       octet_length(f.intent_raw)::bigint, f.intent_raw
                  FROM issuer_cut_fixture f
                 WHERE f.run_id=$1 AND f.generation=$2
                   AND f.fence_digest=$3 AND f.live
            $issuer$;",
            )
            .unwrap();

        let mut harness = payload("original-tool", "original-harness-job", "ws-harness", 2);
        harness.principal = "original-harness-principal".into();
        let run_id = "harness-run:dispatch-current-pg18";
        let fence_id = "harness-dispatch-fence:dispatch-current-pg18";
        let other_ref = serde_json::json!({
            "namespace":"ordivon.harness","type":"harness_run","id":run_id
        });
        let (intent_digest, intent_raw) = encoded(&serde_json::json!({
            "schemaVersion":1,"kind":"ordivon.harness-tool-step-intent",
            "harnessRunId":run_id,"runtimeOperation":"workspace.exec",
            "runtimeArgumentsDigest":format!("sha256:{}", "a".repeat(64)),
            "clientRequestId":harness.client_request_id
        }));
        let (fence_digest, fence_raw) = encoded(&serde_json::json!({
            "schemaVersion":2,"kind":"ordivon.harness-dispatch-fence",
            "fenceId":fence_id,"harnessRunId":run_id,"runRevision":1,
            "clientRequestId":harness.client_request_id,
            "runtimeOperation":"workspace.exec","intentDigest":intent_digest,
            "issuedAtMs":0_i64,"expiresAtMs":32_503_680_000_000_i64
        }));
        let fence_ref = serde_json::json!({
            "namespace":"ordivon.harness","type":"dispatch_fence",
            "id":fence_id,"digest":fence_digest,"generation":"1"
        });
        let (physical_digest, _) = encoded(&serde_json::json!({
            "workspaceId":harness.workspace_id,
            "executable":"/usr/bin/echo","args":["harmless"],
            "cwdRelative":".","env":{},
            "timeoutMs":1000,"stdoutLimitBytes":1024,"stderrLimitBytes":1024,
            "foreignReferences":[other_ref.clone()]
        }));
        let (payload_digest, payload_raw) = encoded(&serde_json::json!({
            "schemaVersion":1,"kind":"ordivon.harness-run-event-payload",
            "eventKind":"harness.tool-step-prepared",
            "data":{
                "dispatchFenceDigest":fence_digest,
                "dispatchFenceObjectDigest":fence_digest,
                "toolStepIntentDigest":intent_digest,
                "toolStepIntentObjectDigest":intent_digest,
                "physicalExecutionDigest":physical_digest
            }
        }));
        harness.execution_plan_json = serde_json::json!({
            "workspaceId":harness.workspace_id,"workspacePath":"/tmp/pg-issuer-fixture",
            "cwd":"/tmp/pg-issuer-fixture",
            "executable":"/usr/bin/echo","args":["harmless"],"env":{},
            "timeoutMs":1000,"stdoutLimitBytes":1024,"stderrLimitBytes":1024,
            "executionProfile":"trusted_local","executionTarget":"local_linux",
            "foreignReferences":[other_ref,fence_ref]
        })
        .to_string();

        scratch
            .admin
            .execute(
                "INSERT INTO issuer_cut_fixture VALUES($1,$2,$3,true,$4,$5,$6,$7,$8)",
                &[
                    &run_id,
                    &1_i64,
                    &fence_digest,
                    &payload_digest,
                    &payload_raw,
                    &fence_raw,
                    &intent_digest,
                    &intent_raw,
                ],
            )
            .unwrap();
        let mut db = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        assert_eq!(
            db.admit_with_workspace_guard(&harness, &|| Ok(()), Some(&scratch.name),)
                .unwrap(),
            PgAdmissionOutcome::Created(harness.job_id.clone())
        );
        allocate_fixture(&mut scratch, &harness);
        let digest = format!("sha256:{}", "b".repeat(64));
        db.commit_bundle_ready_pg(&PgBundleReady {
            attempt_id: harness.attempt_id.clone(),
            expected_row_version: 0,
            bundle_digest: digest.clone(),
            observed_at_ms: harness.created_at_ms + 1,
            expected_source_sha256: harness.expected_source_sha256.clone(),
        })
        .unwrap();
        let issued = PgDispatchIssued {
            attempt_id: harness.attempt_id.clone(),
            expected_row_version: 1,
            expected_bundle_digest: digest,
            observed_at_ms: harness.created_at_ms + 2,
            expected_source_sha256: harness.expected_source_sha256.clone(),
        };

        // An independent source writer revokes the original Run after admission,
        // before the durable dispatch transaction commits.
        let mut source = Client::connect(&dsn, NoTls).unwrap();
        source
            .execute(
                &format!(
                    "UPDATE \"{}\".issuer_cut_fixture SET live=false WHERE run_id=$1",
                    scratch.name
                ),
                &[&run_id],
            )
            .unwrap();
        assert!(matches!(
            db.mark_dispatch_issued_pg(
                &issued,
                Some(&scratch.name),
                Some("original-harness-principal"),
            ),
            Err(PgAdmissionError::IssuerNotCurrent)
        ));
        let state: String = scratch
            .admin
            .query_one(
                "SELECT state FROM attempts WHERE attempt_id=$1",
                &[&harness.attempt_id],
            )
            .unwrap()
            .get(0);
        assert_eq!(
            state, "accepted",
            "failed currentness must roll back PG dispatch"
        );
        assert_eq!(scratch.count("job_events"), 4, "no durable dispatch event");

        // The same original source resumes authority, and dispatch is admitted
        // once. This positive is PG-only; no OS Unit or Domain effect is claimed.
        source
            .execute(
                &format!(
                    "UPDATE \"{}\".issuer_cut_fixture SET live=true WHERE run_id=$1",
                    scratch.name
                ),
                &[&run_id],
            )
            .unwrap();
        assert_eq!(
            db.mark_dispatch_issued_pg(
                &issued,
                Some(&scratch.name),
                Some("original-harness-principal"),
            )
            .unwrap(),
            2
        );
        assert_eq!(scratch.count("job_events"), 5);

        // The one ordinary scheduler must still dispatch unrelated Jobs.
        let ordinary = payload("ordinary-request", "ordinary-job", "ws-ordinary", 2);
        db.admit(&ordinary).unwrap();
        allocate_fixture(&mut scratch, &ordinary);
        let ordinary_digest = format!("sha256:{}", "c".repeat(64));
        db.commit_bundle_ready_pg(&PgBundleReady {
            attempt_id: ordinary.attempt_id.clone(),
            expected_row_version: 0,
            bundle_digest: ordinary_digest.clone(),
            observed_at_ms: ordinary.created_at_ms + 1,
            expected_source_sha256: ordinary.expected_source_sha256.clone(),
        })
        .unwrap();
        assert_eq!(
            db.mark_dispatch_issued_pg(
                &PgDispatchIssued {
                    attempt_id: ordinary.attempt_id,
                    expected_row_version: 1,
                    expected_bundle_digest: ordinary_digest,
                    observed_at_ms: ordinary.created_at_ms + 2,
                    expected_source_sha256: ordinary.expected_source_sha256,
                },
                Some(&scratch.name),
                Some("original-harness-principal")
            )
            .unwrap(),
            2
        );
    }

    /// Real PG two-connection admission->revoke->dispatch experiment.
    /// SQL fixture only models the original Harness source cut, never OS ACK.
    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_original_harness_dispatch_current_two_connections() {
        fn enc(v: serde_json::Value) -> (String, Vec<u8>) {
            let raw = serde_json::to_vec(&v).unwrap();
            (format!("sha256:{}", hex::encode(Sha256::digest(&raw))), raw)
        }
        let dsn = physical_pg_test_dsn();
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        scratch
            .admin
            .batch_execute(
                "CREATE TABLE issuer_cut_fixture(
                run_id text, generation bigint, digest text, live boolean,
                payload_hash text, payload bytea, fence bytea,
                intent_hash text, intent bytea
            );
            CREATE FUNCTION harness_current_dispatch_cut(text,bigint,text)
            RETURNS TABLE(event_kind text,payload_digest text,payload_kind text,
                payload_size bigint,payload_raw bytea,fence_kind text,
                fence_size bigint,fence_raw bytea,intent_object_digest text,
                intent_kind text,intent_len bigint,intent_raw bytea)
            LANGUAGE SQL AS $cut$
                SELECT 'harness.tool-step-prepared'::text,
                    f.payload_hash,'ordivon.harness-run-event-payload'::text,
                    octet_length(f.payload)::bigint,f.payload,
                    'harness-dispatch-fence'::text,
                    octet_length(f.fence)::bigint,f.fence,
                    f.intent_hash,'harness-tool-step-intent'::text,
                    octet_length(f.intent)::bigint,f.intent
                FROM issuer_cut_fixture f
                WHERE f.run_id=$1 AND f.generation=$2 AND f.digest=$3 AND f.live
            $cut$;",
            )
            .unwrap();
        let mut h = payload("original-tool", "harness-dispatch", "harness-ws", 2);
        h.principal = "harness-issuer".into();
        let run = "harness-run:pg18-current";
        let fence_id = "harness-dispatch-fence:pg18-current";
        let other = serde_json::json!({
            "namespace":"ordivon.harness","type":"harness_run","id":run
        });
        let (intent_hash, intent_raw) = enc(serde_json::json!({
            "schemaVersion":1,"kind":"ordivon.harness-tool-step-intent",
            "harnessRunId":run,"runtimeOperation":"workspace.exec",
            "runtimeArgumentsDigest":format!("sha256:{}", "a".repeat(64)),
            "clientRequestId":h.client_request_id
        }));
        let (fence_hash, fence_raw) = enc(serde_json::json!({
            "schemaVersion":2,"kind":"ordivon.harness-dispatch-fence",
            "fenceId":fence_id,"harnessRunId":run,"runRevision":1,
            "clientRequestId":h.client_request_id,"runtimeOperation":"workspace.exec",
            "intentDigest":intent_hash,"issuedAtMs":0_i64,
            "expiresAtMs":32_503_680_000_000_i64
        }));
        let (physical_hash, _) = enc(serde_json::json!({
            "workspaceId":h.workspace_id,"executable":"/usr/bin/echo",
            "args":["harmless"],"cwdRelative":".","env":{},
            "timeoutMs":1000,"stdoutLimitBytes":1024,"stderrLimitBytes":1024,
            "foreignReferences":[other.clone()]
        }));
        let (payload_hash, payload_raw) = enc(serde_json::json!({
            "schemaVersion":1,"kind":"ordivon.harness-run-event-payload",
            "eventKind":"harness.tool-step-prepared","data":{
                "dispatchFenceDigest":fence_hash,
                "dispatchFenceObjectDigest":fence_hash,
                "toolStepIntentDigest":intent_hash,
                "toolStepIntentObjectDigest":intent_hash,
                "physicalExecutionDigest":physical_hash
            }
        }));
        h.execution_plan_json = serde_json::json!({
            "workspaceId":h.workspace_id,"workspacePath":"/tmp/pg18-current",
            "cwd":"/tmp/pg18-current","executable":"/usr/bin/echo",
            "args":["harmless"],"env":{},"timeoutMs":1000,
            "stdoutLimitBytes":1024,"stderrLimitBytes":1024,
            "executionProfile":"trusted_local","executionTarget":"local_linux",
            "foreignReferences":[other,{
                "namespace":"ordivon.harness","type":"dispatch_fence",
                "id":fence_id,"digest":fence_hash,"generation":"1"
            }]
        })
        .to_string();
        scratch
            .admin
            .execute(
                "INSERT INTO issuer_cut_fixture VALUES($1,1,$2,true,$3,$4,$5,$6,$7)",
                &[
                    &run,
                    &fence_hash,
                    &payload_hash,
                    &payload_raw,
                    &fence_raw,
                    &intent_hash,
                    &intent_raw,
                ],
            )
            .unwrap();
        let mut runtime = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        assert_eq!(
            runtime
                .admit_with_workspace_guard(&h, &|| Ok(()), Some(&scratch.name))
                .unwrap(),
            PgAdmissionOutcome::Created(h.job_id.clone())
        );
        allocate_fixture(&mut scratch, &h);
        let digest = format!("sha256:{}", "b".repeat(64));
        runtime
            .commit_bundle_ready_pg(&PgBundleReady {
                attempt_id: h.attempt_id.clone(),
                expected_row_version: 0,
                bundle_digest: digest.clone(),
                observed_at_ms: h.created_at_ms + 1,
                expected_source_sha256: h.expected_source_sha256.clone(),
            })
            .unwrap();
        let issued = PgDispatchIssued {
            attempt_id: h.attempt_id.clone(),
            expected_row_version: 1,
            expected_bundle_digest: digest,
            observed_at_ms: h.created_at_ms + 2,
            expected_source_sha256: h.expected_source_sha256.clone(),
        };
        let mut source = Client::connect(&dsn, NoTls).unwrap();
        let update = format!(
            "UPDATE \"{}\".issuer_cut_fixture SET live=$1 WHERE run_id=$2",
            scratch.name
        );
        source.execute(&update, &[&false, &run]).unwrap();
        assert!(matches!(
            runtime.mark_dispatch_issued_pg(&issued, Some(&scratch.name), Some("harness-issuer")),
            Err(PgAdmissionError::IssuerNotCurrent)
        ));
        assert_eq!(
            scratch
                .admin
                .query_one(
                    "SELECT state FROM attempts WHERE attempt_id=$1",
                    &[&h.attempt_id],
                )
                .unwrap()
                .get::<_, String>(0),
            "accepted"
        );
        assert_eq!(scratch.count("job_events"), 4);

        source.execute(&update, &[&true, &run]).unwrap();
        assert_eq!(
            runtime
                .mark_dispatch_issued_pg(&issued, Some(&scratch.name), Some("harness-issuer"))
                .unwrap(),
            2
        );
        assert_eq!(scratch.count("job_events"), 5);
        // Normal Jobs are never subject to a foreign Run cut.
        let ordinary = payload("ordinary", "ordinary-dispatch", "ordinary-ws", 2);
        runtime.admit(&ordinary).unwrap();
        allocate_fixture(&mut scratch, &ordinary);
        let normal_digest = format!("sha256:{}", "c".repeat(64));
        runtime
            .commit_bundle_ready_pg(&PgBundleReady {
                attempt_id: ordinary.attempt_id.clone(),
                expected_row_version: 0,
                bundle_digest: normal_digest.clone(),
                observed_at_ms: ordinary.created_at_ms + 1,
                expected_source_sha256: ordinary.expected_source_sha256.clone(),
            })
            .unwrap();
        assert_eq!(
            runtime
                .mark_dispatch_issued_pg(
                    &PgDispatchIssued {
                        attempt_id: ordinary.attempt_id,
                        expected_row_version: 1,
                        expected_bundle_digest: normal_digest,
                        observed_at_ms: 1234569,
                        expected_source_sha256: ordinary.expected_source_sha256,
                    },
                    Some(&scratch.name),
                    Some("harness-issuer")
                )
                .unwrap(),
            2
        );
    }

    /// Real original Harness PG Store/Continuity → same-PG restricted Runtime
    /// admission → original source UNKNOWN → later PG dispatch must fail closed.
    /// Unlike the synthetic issuer SQL test, all Tool/Fence/payload bytes here
    /// come from the production Harness Python publisher, not Rust test JSON.
    /// This is a PG/Journal boundary test, not an OS spawn or Domain ACK.
    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_original_harness_store_real_issuer_same_job_late_revoke() {
        use std::{path::PathBuf, process::Command};
        let dsn = physical_pg_test_dsn();
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        let stamp = Uuid::now_v7().simple().to_string();
        let issuer_schema = format!("r17_hpg_{}", &stamp[..19]);
        let role = format!("r17_role_{}", &stamp[..19]);
        let run_id = format!("harness-run:r17-original-{}", &stamp[..19]);
        let workspace_id = format!("r17-test-{}", &stamp[..19]);
        let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../../../");
        let fixture = root.join("services/harness/tests/original_pg_issuer_native_fixture.py");
        assert!(
            fixture.is_file(),
            "real Harness Python source fixture missing"
        );
        let python = std::env::var("HARNESS_PG_PYTHON").unwrap_or_else(|_| "python3".into());
        let pythonpath = format!(
            "{}:{}",
            root.join("services/harness/src").display(),
            root.join("services/harness").display()
        );
        let invoke = |verb: &str| -> serde_json::Value {
            let run = Command::new(&python)
                .arg(&fixture)
                .arg(verb)
                .arg("--dsn")
                .arg(&dsn)
                .arg("--schema")
                .arg(&issuer_schema)
                .arg("--run")
                .arg(&run_id)
                .arg("--workspace")
                .arg(&workspace_id)
                .env("PYTHONPATH", &pythonpath)
                .output()
                .expect("source Harness Python interpreter");
            assert!(
                run.status.success(),
                "original Harness {verb}: {}",
                String::from_utf8_lossy(&run.stderr)
            );
            serde_json::from_slice(&run.stdout).expect("actual source publisher reports exact JSON")
        };
        let original = invoke("issue");
        assert_eq!(original["runId"], run_id);
        assert_eq!(original["fenceGeneration"], 2);
        assert_eq!(
            original["loweredRequest"]["execution"]["foreignReferences"]
                .as_array()
                .unwrap()
                .len(),
            2
        );
        scratch.admin.batch_execute(
            &format!(
                "CREATE ROLE \"{role}\" LOGIN;
                 GRANT USAGE ON SCHEMA \"{runtime}\",\"{issuer_schema}\" TO \"{role}\";
                 GRANT ALL ON ALL TABLES IN SCHEMA \"{runtime}\" TO \"{role}\";
                 GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA \"{runtime}\" TO \"{role}\";
                 REVOKE ALL ON \"{runtime}\"._stage_control FROM \"{role}\";
                 GRANT SELECT,UPDATE(id) ON \"{runtime}\"._stage_control TO \"{role}\";
                 GRANT EXECUTE ON FUNCTION \"{issuer_schema}\".harness_current_dispatch_cut(text,bigint,text)
                     TO \"{role}\";",
                runtime=scratch.name
            )
        ).unwrap();
        // PostgreSQL's truly limited Runtime SQL role must not read or write
        // the source-owned private Harness tables, only execute its issuer cut.
        let limited_dsn = format!("{dsn} user={role}");
        let mut limited_pg =
            Client::connect(&limited_dsn, NoTls).expect("real restricted Runtime SQL role");
        let current_user: String = limited_pg
            .query_one("SELECT current_user", &[])
            .unwrap()
            .get(0);
        assert_eq!(current_user, role);
        let denied = limited_pg.query(&format!("SELECT * FROM \"{issuer_schema}\".runs"), &[]);
        assert!(
            denied.is_err(),
            "limited Runtime principal can read private Harness PG"
        );
        // A failed permission statement outside an explicit transaction
        // leaves this session usable by the existing runtime PG writer.
        let e = &original["loweredRequest"]["execution"];
        let workspace_root = "/tmp/r17-pg-source-verifier".to_string();
        let plan = serde_json::json!({
            "workspaceId":e["workspaceId"],
            "workspacePath":workspace_root,
            "cwd":workspace_root,
            "executable":e["executable"],
            "args":e["args"],
            "env":e["env"],
            "timeoutMs":e["timeoutMs"],
            "stdoutLimitBytes":e["stdoutLimitBytes"],
            "stderrLimitBytes":e["stderrLimitBytes"],
            "foreignReferences":e["foreignReferences"],
            "executionProfile":"trusted_local",
            "executionTarget":"local_linux"
        });
        let mut original_job = payload("r17-original-client", "job-r17-original", "r17-test-ws", 2);
        original_job.principal = "r17-dedicated-issuer-principal".into();
        original_job.workspace_id = workspace_id.clone();
        original_job.client_request_id = original["clientRequestId"].as_str().unwrap().into();
        original_job.execution_plan_json = serde_json::to_string(&plan).unwrap();
        // The actual PG source gate requires the same immutable ClientRequestId,
        // original Physical Execution and Fence on admission AND later dispatch.
        let mut runtime = PgAdmissionStore::connect(&limited_dsn, &scratch.name).unwrap();
        assert_eq!(
            runtime
                .admit_with_workspace_guard(&original_job, &|| Ok(()), Some(&issuer_schema))
                .unwrap(),
            PgAdmissionOutcome::Created(original_job.job_id.clone())
        );
        allocate_fixture(&mut scratch, &original_job);
        let bundle = format!("sha256:{}", "b".repeat(64));
        runtime
            .commit_bundle_ready_pg(&PgBundleReady {
                attempt_id: original_job.attempt_id.clone(),
                expected_row_version: 0,
                bundle_digest: bundle.clone(),
                observed_at_ms: original_job.created_at_ms + 1,
                expected_source_sha256: original_job.expected_source_sha256.clone(),
            })
            .unwrap();
        // The *real* original Harness Store emits the UNKNOWN receipt after
        // a valid new-Job admission. This invalidates its source Run revision.
        let revoked = invoke("revoke");
        assert_eq!(revoked["sourceStanding"], "unknown");
        assert_eq!(revoked["finalization"]["sourceStanding"], "blocked");
        assert_eq!(revoked["revision"], 3);
        let issued = PgDispatchIssued {
            attempt_id: original_job.attempt_id.clone(),
            expected_row_version: 1,
            expected_bundle_digest: bundle,
            observed_at_ms: original_job.created_at_ms + 2,
            expected_source_sha256: original_job.expected_source_sha256.clone(),
        };
        assert!(
            matches!(
                runtime.mark_dispatch_issued_pg(
                    &issued,
                    Some(&issuer_schema),
                    Some("r17-dedicated-issuer-principal")
                ),
                Err(PgAdmissionError::IssuerNotCurrent)
            ),
            "a genuine original Harness Run revoked after admission cannot issue PG dispatch"
        );
        let state: String = scratch
            .admin
            .query_one(
                "SELECT state FROM attempts WHERE attempt_id=$1",
                &[&original_job.attempt_id],
            )
            .unwrap()
            .get(0);
        assert_eq!(state, "accepted");
        let dispatches: i64 = scratch
            .admin
            .query_one(
                "SELECT count(*) FROM job_events
             WHERE job_id=$1 AND event_type='DISPATCH_ISSUED'",
                &[&original_job.job_id],
            )
            .unwrap()
            .get(0);
        assert_eq!(dispatches, 0);
        scratch
            .admin
            .batch_execute(&format!("DROP SCHEMA \"{issuer_schema}\" CASCADE;"))
            .unwrap();
    }
}
