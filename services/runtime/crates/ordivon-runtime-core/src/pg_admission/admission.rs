//! PostgreSQL admission owner: admission.
use super::*;

// PostgreSQL insertion columns, not another release semantic state owner.
// Only a transactional Runtime caller can construct the domain release object.
// Standalone PG admission needs no legacy Runtime module or SQLite dependency.
pub(super) struct PgReleaseInsert {
    pub(super) effect_id: String,
    pub(super) request_digest: String,
    pub(super) workspace_id: String,
    pub(super) commit: String,
    pub(super) candidate_manifest_digest: String,
    pub(super) expected_tool_count: i32,
    pub(super) receipt_path: String,
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

    pub(super) fn admit_inner(
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
        // A permanent gate row is mandatory for NEW Jobs. The row lock
        // invalidates stale SERIALIZABLE snapshots after a close commits.
        // Missing/malformed/closed all fail closed. Exact historical replay
        // above and existing terminal/cancellation paths do not use this gate.
        if !maintenance::new_job_admission_open(&mut tx)? {
            return Err(PgAdmissionError::MaintenanceClosed);
        }
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
