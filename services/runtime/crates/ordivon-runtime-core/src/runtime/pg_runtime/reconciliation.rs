//! PostgreSQL Attempt readback, native reconciliation, and Job result projection.
use super::*;

mod native_identity;
#[cfg(test)]
use native_identity::namespace_pid_from_host_status;
use native_identity::{native_running_witness, observed_namespace_pid, NativePidReadback};

/// Retain PostgreSQL's SQLSTATE across direct Client reads. The shared
/// PgAdmissionError adapter owns transaction-abort vs unavailable taxonomy;
/// generic io(Display) would erase SQLSTATE 40001/40P01 first.
fn pg_read_error(error: postgres::Error) -> RuntimeError {
    pg(PgAdmissionError::Database(error))
}
use crate::PgJobSnapshot;

// Keep the exact recovery current-Attempt selectors shared with native PG
// falsification tests; current is an explicit Job pointer, not MAX(number).
const RECOVERY_CURRENT_ATTEMPT_SQL: &str = "SELECT a.attempt_id,a.state,a.termination_intent,a.launch_token_digest,a.bundle_path,a.unit_name,a.created_at_ms,a.row_version,a.bundle_digest,j.execution_plan_json,j.operation_digest,a.attempt_number FROM jobs j JOIN attempts a ON a.attempt_id=j.current_attempt_id AND a.job_id=j.job_id WHERE j.job_id=$1";
const RELEASE_CURRENT_ATTEMPT_STATE_SQL: &str = "SELECT a.state FROM jobs j JOIN attempts a ON a.attempt_id=j.current_attempt_id AND a.job_id=j.job_id WHERE j.job_id=$1";

// Observation is not an external effect. A terminal PG Job intentionally
// clears current_attempt_id after its terminal Attempt and events are committed.
// Bind read-only projection to the exact Attempt already qualified by
// observe_job_readonly(), never to an unverified newest historical Attempt.
const READBACK_VERIFIED_ATTEMPT_SQL: &str = "SELECT a.attempt_id,a.state,a.termination_intent,a.launch_token_digest,a.bundle_path,a.unit_name,a.created_at_ms,a.row_version,a.bundle_digest,j.execution_plan_json,j.operation_digest,a.attempt_number FROM jobs j JOIN attempts a ON a.job_id=j.job_id AND a.attempt_id=$2 WHERE j.job_id=$1 AND j.row_version=$3 AND a.row_version=$4 AND j.resolution IS NOT DISTINCT FROM $5::TEXT AND (($5::TEXT IS NULL AND j.current_attempt_id=a.attempt_id) OR ($5::TEXT IS NOT NULL AND j.current_attempt_id IS NULL AND a.state=$5::TEXT))";
// Both native release control and normal native reconciliation use the
// existing one PG query to detect completed work. It never authorizes an
// external effect based on a historical Attempt.
const RECONCILIATION_STAGE_SQL: &str = "SELECT (SELECT resolution FROM jobs WHERE job_id=$1), EXISTS(SELECT 1 FROM job_runtime_release_effects WHERE job_id=$1)";

/// An absent or foreign current Attempt is an inconsistent committed
/// lifecycle identity, not PostgreSQL transport unavailability. Never infer
/// native effects or Runner custody from the highest historical Attempt.
fn require_recovery_current_attempt(
    row: Option<postgres::Row>,
    job: &str,
) -> RuntimeResult<postgres::Row> {
    row.ok_or_else(|| {
        RuntimeError::new(
            RuntimeErrorCode::ReconciliationRequired,
            "committed PG Job has no coherent current Attempt identity",
            Some("currentAttemptId"),
            false,
        )
        .with_operation_id(job)
    })
}

/// Negative evidence may be committed only after a *final* filesystem check.
/// Runner publishes result.json after completing its command; systemctl/cgroup
/// probes between an earlier file check and LOST commit can otherwise miss a
/// result that was durably written during the probes.
/// Match the PG Job-list recovery projection: a nonterminal issued Attempt
/// requiring a native startup, stop, or recovery witness must never be
/// advertised as recovery-free. A healthy running Job remains ordinary work.
fn needs_recovery_observation(state: AttemptState, terminal: bool) -> bool {
    !terminal
        && matches!(
            state,
            AttemptState::Starting | AttemptState::Stopping | AttemptState::Recovering
        )
}

mod output_projection;
use output_projection::{active_log_window, output_projection_relative_path};

fn runner_result_still_absent(path: &Path) -> RuntimeResult<bool> {
    match fs::symlink_metadata(path.join("result.json")) {
        Err(err) if err.kind() == std::io::ErrorKind::NotFound => Ok(true),
        Ok(metadata) if metadata.file_type().is_file() => Ok(false),
        Ok(_) => Err(error("Runner result path is not a regular file")),
        Err(err) => Err(io(err)),
    }
}

mod scan_epoch;
use scan_epoch::{
    advance_reconciliation_cursor, latest_reconciliation_key, next_reconciliation_cursor,
    scan_reconciliation_page,
};

impl PgRuntime {
    /// Service-owned recovery path. Does not admit commands or consume Job capacity.
    /// Each cancellation retains its original principal and exact durable Job identity.
    pub fn reconcile_cancelled_jobs(&self, limit: u32) -> RuntimeResult<serde_json::Value> {
        self.reconcile_committed_jobs(limit, true)
    }
    /// Reconcile already issued native work, never dispatch an unissued Job.
    pub fn reconcile_issued_jobs(&self, limit: u32) -> RuntimeResult<serde_json::Value> {
        self.reconcile_committed_jobs(limit, false)
    }
    fn reconcile_committed_jobs(
        &self,
        limit: u32,
        cancelled_only: bool,
    ) -> RuntimeResult<serde_json::Value> {
        if limit == 0 || limit > 100 {
            return Err(RuntimeError::invalid("limit must be 1..100", "limit"));
        }
        let mut db = self.store()?;
        // The oldest unresolved jobs can stay blocked on uncertain native
        // evidence indefinitely. A fixed LIMIT on the oldest rows prevents
        // later jobs from ever being reconciled. Use finite upper-fenced
        // keyset epochs, with independent cursors for cancellation and
        // general recovery; never let newly arriving Jobs extend an epoch. Never hold a cursor mutex across DB or
        // native OS calls.
        let previous = {
            let cursors = self
                .reconciliation_cursors
                .lock()
                .map_err(|_| error("reconciliation cursor mutex poisoned"))?;
            if cancelled_only {
                cursors.cancelled.clone()
            } else {
                cursors.issued.clone()
            }
        };
        // Only the first page of each epoch takes a new upper bound. The
        // subsequent bounded pages use that same fence even if new Jobs
        // arrive continuously; stale concurrent scans cannot rewrite it.
        let upper_fence = match previous.upper_fence.clone() {
            Some(key) => Some(key),
            None => {
                latest_reconciliation_key(&mut db.client, cancelled_only).map_err(pg_read_error)?
            }
        };
        let pending = match upper_fence.as_ref() {
            Some(upper) => scan_reconciliation_page(
                &mut db.client,
                limit,
                cancelled_only,
                previous.key.as_ref(),
                upper,
            )
            .map_err(pg_read_error)?,
            None => Vec::new(),
        };
        let (next_key, next_upper_fence) = match upper_fence.as_ref() {
            Some(upper) => next_reconciliation_cursor(&pending, limit, upper),
            None => (None, None),
        };
        let mut cursors = self
            .reconciliation_cursors
            .lock()
            .map_err(|_| error("reconciliation cursor mutex poisoned"))?;
        let slot = if cancelled_only {
            &mut cursors.cancelled
        } else {
            &mut cursors.issued
        };
        let _ =
            advance_reconciliation_cursor(slot, previous.generation, next_key, next_upper_fence);
        drop(cursors);
        drop(db);
        let mut terminal = 0_u32;
        let mut errors = 0_u32;
        for row in &pending {
            let request = JobCancelRequest {
                schema_version: 1,
                job_id: row.get(0),
            };
            let outcome = if row.get::<_, String>(2) == "cancelled" {
                self.cancel(&row.get::<_, String>(1), &request)
            } else {
                self.observe(
                    &row.get::<_, String>(1),
                    &JobObserveRequest {
                        schema_version: 1,
                        job_id: request.job_id,
                        wait_ms: 0,
                        wait_until: JobObserveWaitUntil::Terminal,
                        stdout_tail_bytes: 0,
                        stderr_tail_bytes: 0,
                        stdout_offset: None,
                        stderr_offset: None,
                    },
                )
            };
            match outcome {
                Ok(value) if value.execution_terminal => terminal += 1,
                Ok(_) => (),
                Err(_) => errors += 1,
            }
        }
        Ok(json!({"inspected":pending.len(),"terminal":terminal,"errors":errors}))
    }
    // One existing PG read, shared by regular reconciliation and cancellation.
    // An accepted STOP_REQUESTED Attempt needs qualified native identity but
    // no executable Plan: no OS dispatch may ever consume those Plan bytes.
    fn current_attempt_row(
        &self,
        db: &mut PgAdmissionStore,
        job: &str,
    ) -> RuntimeResult<postgres::Row> {
        require_recovery_current_attempt(
            db.client
                .query_opt(RECOVERY_CURRENT_ATTEMPT_SQL, &[&job])
                .map_err(pg_read_error)?,
            job,
        )
    }

    pub(super) fn attempt(
        &self,
        db: &mut PgAdmissionStore,
        job: &str,
    ) -> RuntimeResult<(AttemptRecord, RuntimeExecutionPlan, String)> {
        let r = self.current_attempt_row(db, job)?;
        self.decode_attempt_record(&r, job)
    }

    /// Read-only identity may be historical only after the existing PG
    /// repeatable-read lifecycle, reservation and terminal-event verifier
    /// supplied its exact Attempt identifier. Re-bind the row to its owner,
    /// job/attempt versions, resolution, and current-or-terminal identity in
    /// one new read snapshot; a concurrent transition must be inconclusive.
    pub(super) fn readback_attempt(
        &self,
        db: &mut PgAdmissionStore,
        snapshot: &PgJobSnapshot,
    ) -> RuntimeResult<(AttemptRecord, RuntimeExecutionPlan, String)> {
        let row = db
            .client
            .query_opt(
                READBACK_VERIFIED_ATTEMPT_SQL,
                &[
                    &snapshot.job_id,
                    &snapshot.attempt_id,
                    &snapshot.job_row_version,
                    &snapshot.attempt_row_version,
                    &snapshot.resolution,
                ],
            )
            .map_err(pg_read_error)?;
        let row = row.ok_or_else(|| {
            RuntimeError::new(
                RuntimeErrorCode::ReconciliationRequired,
                "verified PG lifecycle changed before Attempt readback",
                Some("jobId"),
                true,
            )
            .with_operation_id(&snapshot.job_id)
        })?;
        self.decode_attempt_record(&row, &snapshot.job_id)
    }

    /// A committed cancel is an OS control operation against the qualified
    /// current Attempt/Unit, not a new execution-plan dispatch. An invalid
    /// frozen Plan cannot block physical stop of an already running process.
    pub(super) fn cancel_attempt_identity(
        &self,
        db: &mut PgAdmissionStore,
        job: &str,
    ) -> RuntimeResult<AttemptRecord> {
        let row = require_recovery_current_attempt(
            db.client
                .query_opt(RECOVERY_CURRENT_ATTEMPT_SQL, &[&job])
                .map_err(pg_read_error)?,
            job,
        )?;
        self.decode_attempt_identity(&row, job)
    }

    fn decode_attempt_identity(
        &self,
        r: &postgres::Row,
        job: &str,
    ) -> RuntimeResult<AttemptRecord> {
        let a: AttemptRecord = serde_json::from_value(json!({"attemptId":r.get::<_,String>(0),"jobId":job,"attemptNumber":r.get::<_, i64>(11),"state":r.get::<_,String>(1),"terminationIntent":r.get::<_,String>(2),"launchTokenDigest":r.get::<_,String>(3),"bundlePath":r.get::<_,String>(4),"unitName":r.get::<_,String>(5),"createdAtMs":r.get::<_,i64>(6),"rowVersion":r.get::<_,i64>(7),"bundleDigest":r.get::<_,Option<String>>(8)})).map_err(io)?;
        let expected = self
            .config
            .executor
            .store_root
            .join("pg-attempts")
            .join(&a.attempt_id);
        if Path::new(&a.bundle_path) != expected {
            return Err(error("Attempt bundle outside PG store"));
        }
        Ok(a)
    }

    fn decode_attempt_record(
        &self,
        r: &postgres::Row,
        job: &str,
    ) -> RuntimeResult<(AttemptRecord, RuntimeExecutionPlan, String)> {
        let a = self.decode_attempt_identity(r, job)?;
        // A malformed frozen execution plan is a damaged Job record, not
        // PostgreSQL server unavailability. This is the first real job.get /
        // observe readback boundary, before the optional Scheduler annotation.
        let plan: RuntimeExecutionPlan =
            serde_json::from_str(&r.get::<_, String>(9)).map_err(|e| {
                RuntimeError::invalid(
                    format!("committed executionPlan is invalid: {e}"),
                    "executionPlan",
                )
            })?;
        Ok((a, plan, r.get(10)))
    }
    /// A PG-fenced accepted cancellation is already past the only boundary
    /// where this Attempt could be dispatched. Materialize the existing
    /// deterministic cancellation Artifact without decoding an executable
    /// Plan that must never run. The terminal PG CAS still arbitrates races.
    fn reconcile_accepted_cancel(
        &self,
        db: &mut PgAdmissionStore,
        job: &str,
        a: &AttemptRecord,
    ) -> RuntimeResult<()> {
        let path = PathBuf::from(&a.bundle_path);
        // STOP_REQUESTED fences eligible_attempt in the same PG authority.
        // Accepted means dispatch intent has not crossed its atomic boundary;
        // a concurrent dispatcher must fail its expected-row-version CAS.
        let cancelled_at: i64 = db.client.query_one(
            "SELECT min(observed_at_ms) FROM job_events WHERE attempt_id=$1 AND event_type='STOP_REQUESTED'",
            &[&a.attempt_id],
        ).map_err(pg_read_error)?.get::<_,Option<i64>>(0)
            .ok_or_else(|| error("cancelled admission omitted stop event"))?;
        let bytes = serde_json::to_vec(&json!({"schemaVersion":1,
            "jobId":job,"attemptId":a.attempt_id,"dispatchIssued":false,
            "terminalState":"cancelled","finishedAtMs":cancelled_at}))
        .map_err(io)?;
        prepare_private_pg_attempt_bundle(&path)?;
        let evidence_path = path.join("admission-cancel-evidence.json");
        // All bytes are deterministic from committed PG identity and its
        // first stop event, including across concurrent exact replays.
        if evidence_path.exists() {
            if fs::read(&evidence_path).map_err(io)? != bytes {
                return Err(error("admission cancel evidence mismatch"));
            }
        } else {
            universal::write_bytes_atomic(&evidence_path, &bytes).map_err(io)?;
        }
        let digest = universal::sha256_bytes(&bytes);
        db.commit_terminal_with_artifacts(
            &PgTerminalNoArtifacts {
                attempt_id: a.attempt_id.clone(),
                expected_row_version: a.row_version as i64,
                terminal_state: "cancelled".into(),
                result_digest: digest.clone(),
                reason_code: "CANCELLED_BEFORE_DISPATCH".into(),
                exit_code: None,
                finished_at_ms: cancelled_at,
                expected_source_sha256: self.config.source_sha256.clone(),
            },
            &[PgArtifactRegistration {
                artifact_id: format!("artifact-{}-admission-cancel", a.attempt_id),
                kind: "admission_cancel_evidence".into(),
                relative_path: "admission-cancel-evidence.json".into(),
                digest,
                media_type: "application/json".into(),
                byte_length: bytes.len() as i64,
                truncated: false,
                created_at_ms: cancelled_at,
            }],
        )
        .map_err(pg)?;
        Ok(())
    }

    pub(super) fn reconcile(&self, db: &mut PgAdmissionStore, job: &str) -> RuntimeResult<()> {
        self.reconcile_inner(db, job, false)
    }
    pub(super) fn reconcile_inner(
        &self,
        db: &mut PgAdmissionStore,
        job: &str,
        allow_dispatch: bool,
    ) -> RuntimeResult<()> {
        // Preserve the existing one-query ReleaseEffect classification, now
        // also reading the terminal flag. The atomic terminal PG transition
        // deliberately clears current_attempt_id. A resolved Job has no
        // remaining native effect to reconcile; ONLY project/get then verify
        // its lifecycle, reservation, exact Attempt, and terminal events.
        // This does not make a historical Attempt eligible for Runner effects.
        let stage = db
            .client
            .query_one(RECONCILIATION_STAGE_SQL, &[&job])
            .map_err(pg_read_error)?;
        if stage.get::<_, Option<String>>(0).is_some() {
            return Ok(());
        }
        let is_release: bool = stage.get(1);
        if is_release {
            // Accepted means no physical release dispatch occurred. Any other
            // Attempt state without a release-specific operator receipt is
            // inconsistent; never reconcile it through the generic Runner.
            let row = db
                .client
                .query_opt(RELEASE_CURRENT_ATTEMPT_STATE_SQL, &[&job])
                .map_err(pg_read_error)?;
            return match row.map(|value| value.get::<_, String>(0)).as_deref() {
                Some("accepted") => Ok(()),
                _ => Err(RuntimeError::new(
                    RuntimeErrorCode::ReconciliationRequired,
                    "ReleaseEffect requires operator receipt reconciliation",
                    Some("runtimeReleaseEffect"),
                    false,
                )
                .with_operation_id(job)),
            };
        }
        // Decode the *same* committed current-Attempt row just once.
        // A pre-dispatch STOP_REQUESTED is locally finalizable without
        // consulting the frozen execution Plan or mutable Provider snapshot.
        // All other states preserve the existing strict full-Plan readback.
        let row = self.current_attempt_row(db, job)?;
        if row.get::<_, String>(1) == "accepted" && row.get::<_, String>(2) == "stop_requested" {
            let a = self.decode_attempt_identity(&row, job)?;
            return self.reconcile_accepted_cancel(db, job, &a);
        }
        let (mut a, plan, operation) = self.decode_attempt_record(&row, job)?;
        let provider: serde_json::Value = decode(
            &db.client
                .query_one(
                    "SELECT workspace_snapshot_json FROM jobs WHERE job_id=$1",
                    &[&job],
                )
                .map_err(pg_read_error)?
                .get::<_, String>(0),
        )?;
        if a.state == AttemptState::Accepted
            && a.termination_intent == AttemptTerminationIntent::Natural
        {
            if !allow_dispatch {
                return Ok(());
            }
            let runner = self
                .config
                .executor
                .runner_path
                .as_deref()
                .ok_or_else(|| error("runner missing"))?;
            super::platform::validate_runner(runner)?;
            if provider["executionProvider"]["executableDigest"].as_str()
                != Some(&universal::sha256_file(runner).map_err(io)?)
            {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::ProviderStateMismatch,
                    "native runner changed after admission",
                    Some("executionProvider"),
                    false,
                )
                .with_operation_id(job));
            }
            // Revalidate the *committed* bytes before dispatch; Runner owns
            // continuous path-drift witnessing after it starts.
            super::host_dependency::verify_committed_bindings(&plan.host_dependencies)?;
            let token = universal::sha256_bytes(
                format!("runtime-launch-v1\0{}\0{operation}", a.attempt_id).as_bytes(),
            );
            if universal::sha256_bytes(token.as_bytes()) != a.launch_token_digest {
                return Err(error("launch token mismatch"));
            }
            // Derive the Workspace-private Cargo backing from the committed plan.
            // New plans bind it into one native systemd mount namespace; old
            // FD198 plans continue to use the original Runner compatibility path.
            // Do not rewrite a committed environment or its source identity.
            let build_target_backing =
                if crate::runtime::build_target_contract::requires_private_cargo_build_target(&plan)
                {
                    let backing = self
                        .config
                        .executor
                        .workspace_build_cache_path(&plan.workspace_id)
                        .join("cargo");
                    fs::create_dir_all(&backing).map_err(|error| {
                        RuntimeError::new(
                            RuntimeErrorCode::IoError,
                            format!("prepare Workspace-private Cargo cache: {error}"),
                            Some("workspaceId"),
                            false,
                        )
                    })?;
                    Some(backing.to_string_lossy().into_owned())
                } else {
                    None
                };
            if !self.claim_resources(db, &a, &plan)? {
                return Ok(());
            }
            let req = RunnerRequest {
                workspace_read_paths: plan.budget.scheduling.as_ref().and_then(|s| {
                    if s.workspace_access.read_paths.is_empty() {
                        None
                    } else {
                        Some(s.workspace_access.read_paths.clone())
                    }
                }),
                schema_version: 1,
                job_id: Some(job.into()),
                attempt_id: Some(a.attempt_id.clone()),
                launch_token: Some(token),
                unit_name: Some(a.unit_name.clone()),
                // Reuse the existing Unix Runner child privilege drop, leaving
                // the Runner's PG/result bundle under its original UID 0.
                // The task's Workspace identity comes only from the
                // operator-configured native owner, never a caller field.
                payload: if plan.execution_profile == ExecutionProfile::ContainedLocal {
                    let (Some(uid), Some(gid)) = (
                        self.config.executor.workspace_uid,
                        self.config.executor.workspace_gid,
                    ) else {
                        return Err(RuntimeError::invalid(
                            "contained_local requires configured nonroot task owner",
                            "execution.executionProfile",
                        ));
                    };
                    if uid == 0 || gid == 0 {
                        return Err(RuntimeError::invalid(
                            "contained_local task owner may not be root",
                            "execution.executionProfile",
                        ));
                    }
                    Some(universal::RunnerPayloadConfig {
                        uid,
                        gid,
                        workspace_view: plan.workspace_path.clone(),
                        cwd_view: plan.cwd.clone(),
                        runtime_view: self
                            .config
                            .executor
                            .workspace_cache_path(&plan.workspace_id)
                            .join("home")
                            .to_string_lossy()
                            .into_owned(),
                        cache_view: self
                            .config
                            .executor
                            .workspace_cache_path(&plan.workspace_id)
                            .to_string_lossy()
                            .into_owned(),
                    })
                } else {
                    None
                },
                // Ordinary trusted jobs preserve their historical
                // environment. The contained child must never inherit
                // control-plane environment from the trusted Runner.
                inherit_host_environment: plan.execution_profile
                    != ExecutionProfile::ContainedLocal,
                task_id: a.attempt_id.clone(),
                workspace_id: plan.workspace_id.clone(),
                workspace_path: plan.workspace_path.clone(),
                workspace_source_digest: plan.workspace_source_digest.clone(),
                build_target_backing,
                input_presentation_root: None,
                input_commitments: vec![],
                host_dependencies: plan
                    .host_dependencies
                    .iter()
                    .map(|binding| universal::RunnerHostDependencyCommitment {
                        path: binding.path.clone(),
                        digest: binding.expected_digest.clone(),
                    })
                    .collect(),
                executable: plan.executable.clone(),
                executable_digest: plan.executable_digest.clone(),
                args: plan.args.clone(),
                cwd: plan.cwd.clone(),
                env: plan.env.clone(),
                steps: plan
                    .steps
                    .iter()
                    .map(|step| universal::RunnerExecutionStep {
                        id: step.id.clone(),
                        executable: step.executable.clone(),
                        executable_digest: step.executable_digest.clone(),
                        args: step.args.clone(),
                        cwd: step.cwd.clone(),
                        env: step.env.clone(),
                        timeout_ms: step.timeout_ms,
                        continue_on_error: step.continue_on_error,
                    })
                    .collect(),
                timeout_ms: plan.timeout_ms,
                stdout_limit_bytes: plan.stdout_limit_bytes,
                stderr_limit_bytes: plan.stderr_limit_bytes,
            };
            prepare_private_pg_attempt_bundle(Path::new(&a.bundle_path))?;
            let request_path = Path::new(&a.bundle_path).join("request.json");
            let bytes = serde_json::to_vec(&req).map_err(io)?;
            // Existing published bytes must match; never replace a committed bundle.
            if request_path.exists() {
                if fs::read(&request_path).map_err(io)? != bytes {
                    return Err(error("bundle bytes differ"));
                }
            } else {
                universal::write_bytes_atomic(&request_path, &bytes).map_err(io)?;
            }
            let digest = universal::sha256_bytes(&bytes);
            if a.bundle_digest.is_none() {
                a.row_version = db
                    .commit_bundle_ready_pg(&PgBundleReady {
                        attempt_id: a.attempt_id.clone(),
                        expected_row_version: a.row_version as i64,
                        bundle_digest: digest.clone(),
                        observed_at_ms: now()?,
                        expected_source_sha256: self.config.source_sha256.clone(),
                    })
                    .map_err(pg)? as u64;
            } else if a.bundle_digest.as_deref() != Some(&digest) {
                return Err(error("bundle digest mismatch"));
            }
            // This commit is intent only. Never reissue a physical launch after this boundary.
            let (issuer_schema, issuer_principal) =
                if let Some((principal, schema)) = &self.config.harness_dispatch_issuer {
                    (Some(schema.as_str()), Some(principal.as_str()))
                } else {
                    (self.config.harness_issuer_schema.as_deref(), None)
                };
            let issued_version = db
                .mark_dispatch_issued_pg(
                    &PgDispatchIssued {
                        attempt_id: a.attempt_id.clone(),
                        expected_row_version: a.row_version as i64,
                        expected_bundle_digest: digest.clone(),
                        observed_at_ms: now()?,
                        expected_source_sha256: self.config.source_sha256.clone(),
                    },
                    issuer_schema,
                    issuer_principal,
                )
                .map_err(pg)?;
            // One issuer owns this at-most-once physical call. If a STOP
            // committed after DISPATCH_ISSUED but before we ever called
            // systemd, settle without inventing a Runner start/exit.
            // Never apply this fact from a recovering or different issuer.
            if db
                .settle_cancel_before_native_handoff(&PgDispatchIssued {
                    attempt_id: a.attempt_id.clone(),
                    expected_row_version: issued_version,
                    expected_bundle_digest: digest,
                    observed_at_ms: now()?,
                    expected_source_sha256: self.config.source_sha256.clone(),
                })
                .map_err(pg)?
            {
                return Ok(());
            }
            let output = super::platform::systemd_run(&super::platform::SystemdRunSpec {
                unit_name: &a.unit_name,
                runner: self
                    .config
                    .executor
                    .runner_path
                    .as_deref()
                    .ok_or_else(|| error("runner missing"))?,
                bundle_path: Path::new(&a.bundle_path),
                workspace_path: Path::new(&plan.workspace_path),
                workspace_git_common_dir: plan.workspace_git_common_dir.as_deref().map(Path::new),
                cargo_target_mount:
                    if crate::runtime::build_target_contract::requires_native_cargo_target_mount(
                        &plan,
                    ) {
                        req.build_target_backing.as_deref().map(Path::new)
                    } else {
                        None
                    },
                input_set_path: None,
                credential_source_root: None,
                credential_names: &[],
                runtime_ceiling_ms: plan
                    .timeout_ms
                    .checked_add(5000)
                    .ok_or_else(|| error("timeout overflow"))?,
                budget: &plan.budget,
                execution_profile: plan.execution_profile,
                environment: &plan.env,
            })?;
            if !output.status.success() {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::DispatchOutcomeUnknown,
                    format!(
                        "native launch not confirmed for Job {job}: {}",
                        String::from_utf8_lossy(&output.stderr)
                    ),
                    Some("jobId"),
                    false,
                )
                .with_operation_id(job.to_string()));
            }
            a = self.attempt(db, job)?.0;
            // A cancellation may win *after* the pre-handoff CAS and while
            // systemd-run delivers to the asynchronous Manager. Request an
            // exact Unit stop; the later OS+PG reconciliation alone may
            // certify terminal state. This is NOT a NoFutureSpawn ACK.
            if a.termination_intent == AttemptTerminationIntent::StopRequested
                && !a.state.is_terminal()
            {
                let _ = super::platform::stop_unit_no_block(&a.unit_name)?;
            }
        }
        let path = PathBuf::from(&a.bundle_path);
        // DISPATCH_ISSUED is intent, not a physical start. Only the native
        // Runner start receipt bound to the live systemd InvocationID, PID
        // and cgroup may advance this Attempt from starting to running.
        if a.state == AttemptState::Starting
            && a.termination_intent == AttemptTerminationIntent::Natural
        {
            let start_path = Path::new(&a.bundle_path).join("runner-start.json");
            match fs::symlink_metadata(&start_path) {
                Ok(metadata) if metadata.file_type().is_file() => {
                    let bytes = fs::read(&start_path).map_err(io)?;
                    let start: RunnerStartEvidence = serde_json::from_slice(&bytes).map_err(io)?;
                    let native = super::platform::systemctl_show(&a.unit_name)?;
                    // systemd MainPID is in the host namespace. PrivatePIDs
                    // may make RunnerStart.namespace_pid equal 1: never read
                    // host /proc/1 as though it were this Runner.
                    let host_pid = native
                        .get("MainPID")
                        .and_then(|pid| pid.parse::<u32>().ok())
                        .filter(|pid| *pid != 0);
                    let host_process_start = host_pid.and_then(super::platform::process_identity);
                    let namespace_pid = host_pid.and_then(observed_namespace_pid);
                    if native_running_witness(
                        &start,
                        &native,
                        job,
                        &a.attempt_id,
                        &a.launch_token_digest,
                        NativePidReadback {
                            host_pid,
                            namespace_pid,
                            process_start: host_process_start.as_deref(),
                        },
                        provider["executionProvider"]["executableDigest"]
                            .as_str()
                            .unwrap_or(""),
                    ) {
                        let input = crate::pg_admission::PgRunnerBound {
                            attempt_id: a.attempt_id.clone(),
                            expected_row_version: a.row_version as i64,
                            expected_bundle_digest: a
                                .bundle_digest
                                .clone()
                                .ok_or_else(|| error("issued Attempt omitted bundle digest"))?,
                            runner_start_digest: universal::sha256_bytes(&bytes),
                            native_invocation_id: start.invocation_id,
                            observed_at_ms: now()?,
                            expected_source_sha256: self.config.source_sha256.clone(),
                        };
                        match db.mark_runner_bound_pg(&input) {
                            Ok(new_version) => {
                                a.state = AttemptState::Running;
                                a.row_version = new_version as u64;
                            }
                            Err(PgAdmissionError::Blocked | PgAdmissionError::UnknownCommit) => {
                                // A concurrent cancellation/terminal won. Read its
                                // original PG Attempt; never redispatch or revive it.
                                a = self.attempt(db, job)?.0;
                            }
                            Err(err) => return Err(pg(err)),
                        }
                    }
                }
                Err(err) if err.kind() == std::io::ErrorKind::NotFound => {}
                Ok(_) => return Err(error("Runner start evidence is not a regular file")),
                Err(err) => return Err(io(err)),
            }
        }
        if !a.state.is_terminal() && path.join("result.json").exists() {
            // Reuse native identity, stdout/stderr digest and result validators.
            let start: RunnerStartEvidence =
                serde_json::from_slice(&fs::read(path.join("runner-start.json")).map_err(io)?)
                    .map_err(io)?;
            if start.job_id != job
                || start.attempt_id != a.attempt_id
                || start.launch_token_digest != a.launch_token_digest
                || start.unit_name != a.unit_name
                || start.invocation_id.is_empty()
            {
                return Err(error("runner start identity mismatch"));
            }
            let properties = super::platform::systemctl_show(&a.unit_name)?;
            if super::platform::unit_is_active(&properties)
                || super::platform::unit_has_pending_job(&properties)
            {
                return Ok(());
            }
            if super::platform::nonempty_property(&properties, "InvocationID")
                .is_some_and(|v| v != start.invocation_id)
                || super::platform::cgroup_has_processes(&start.control_group)?
            {
                return Err(error("runner process ownership has not converged"));
            }
            if start.runner_executable_digest.as_deref()
                != provider["executionProvider"]["executableDigest"].as_str()
            {
                return Err(error("runner evidence provider mismatch"));
            }
            let mut terminal = super::evidence::prepare_runner_terminal_from_bundle(&a)?;
            if let Some(artifact) = super::evidence::validate_workspace_source_observation_artifact(
                &a,
                plan.workspace_source_digest.as_deref(),
                true,
                super::evidence::SourceObservationRequirement::for_terminal(
                    terminal.state,
                    &terminal.reason_code,
                ),
            )? {
                terminal.artifacts.push(artifact);
            }
            let input = PgTerminalNoArtifacts {
                attempt_id: a.attempt_id.clone(),
                expected_row_version: a.row_version as i64,
                terminal_state: terminal.state.as_db().into(),
                result_digest: terminal.result_digest,
                reason_code: terminal.reason_code,
                exit_code: terminal.exit_code,
                finished_at_ms: terminal.finished_at_ms as i64,
                expected_source_sha256: self.config.source_sha256.clone(),
            };
            let artifacts = terminal
                .artifacts
                .into_iter()
                .map(|v| PgArtifactRegistration {
                    artifact_id: v.artifact_id,
                    kind: v.kind,
                    relative_path: v.relative_path,
                    digest: v.digest,
                    media_type: v.media_type,
                    byte_length: v.byte_length as i64,
                    truncated: v.truncated,
                    created_at_ms: input.finished_at_ms,
                })
                .collect::<Vec<_>>();
            db.commit_terminal_with_artifacts(&input, &artifacts)
                .map_err(pg)?;
            // Reuse Universal Runtime's existing terminal-only systemd cleanup.
            // Preserve the failed Unit/InvocationID until the durable PG
            // terminal+Artifact+reservation transaction has committed.
            super::platform::release_terminal_unit(&a.unit_name);
        } else if !a.state.is_terminal() {
            // The kernel may have terminated the systemd-owned process tree
            // before Runner could write result.json. A missing result file is
            // not evidence that the process is still alive. Observe the exact
            // native Unit and its cgroup instead of inventing PID-tree logic.
            if a.unit_name != format!("ordivon-pg-{}.service", a.attempt_id) {
                return Err(error("Attempt native unit identity mismatch"));
            }
            let properties = super::platform::systemctl_show(&a.unit_name)?;
            if super::platform::unit_is_active(&properties)
                || super::platform::unit_has_pending_job(&properties)
            {
                return Ok(());
            }
            let start_path = path.join("runner-start.json");
            let (runner_start, runner_start_digest): (Option<RunnerStartEvidence>, String) =
                if start_path.exists() {
                    let bytes = fs::read(&start_path).map_err(io)?;
                    let start: RunnerStartEvidence = serde_json::from_slice(&bytes).map_err(io)?;
                    if start.control_group != format!("/system.slice/{}", a.unit_name)
                        || start.job_id != job
                        || start.attempt_id != a.attempt_id
                        || start.launch_token_digest != a.launch_token_digest
                        || start.unit_name != a.unit_name
                        || start.invocation_id.is_empty()
                    {
                        return Err(error("Runner identity mismatch during native cancellation"));
                    }
                    if super::platform::nonempty_property(&properties, "InvocationID")
                        .is_some_and(|observed| observed != start.invocation_id)
                    {
                        return Err(error("Native Unit invocation changed during cancellation"));
                    }
                    (Some(start), universal::sha256_bytes(&bytes))
                } else {
                    // A transient Unit can be absent while systemd-run has not
                    // finished dispatch. Without a bound Runner start, its
                    // absence cannot fence a late physical launch.
                    return Ok(());
                };
            let observed_cgroup = super::platform::nonempty_property(&properties, "ControlGroup");
            let cgroup = runner_start
                .as_ref()
                .map(|start| start.control_group.as_str())
                .or(observed_cgroup.as_deref());
            let Some(cgroup) = cgroup else {
                return Ok(());
            };
            let population = super::platform::cgroup_population(cgroup)?;
            let removed = population == super::platform::CgroupPopulation::Removed;
            if !matches!(
                properties.get("ActiveState").map(String::as_str),
                Some("inactive" | "failed")
            ) || !matches!(
                properties.get("LoadState").map(String::as_str),
                Some("loaded" | "not-found")
            ) || runner_start
                .as_ref()
                .and_then(|start| start.runner_executable_digest.as_deref())
                != provider["executionProvider"]["executableDigest"].as_str()
            {
                return Ok(());
            }
            // CollectMode=inactive retains a *failed* transient even after
            // systemd has killed its cgroup. Do not reset-failed first: its
            // invocation identity is valuable evidence until PG commits LOST.
            // Only the exact Runner start + same systemd InvocationID + no
            // MainPID can authorize the failed/removed classification.
            let bound_failed_unit = runner_start.as_ref().is_some_and(|start| {
                super::native_stop::failed_unit_matches_runner(
                    properties.get("LoadState").map(String::as_str),
                    properties.get("ActiveState").map(String::as_str),
                    properties.get("InvocationID").map(String::as_str),
                    &start.invocation_id,
                    properties.get("MainPID").map(String::as_str),
                )
            });
            if super::native_stop::decide_native_stop(
                super::platform::unit_is_active(&properties),
                super::platform::unit_has_pending_job(&properties),
                properties
                    .get("LoadState")
                    .is_some_and(|state| state == "not-found"),
                bound_failed_unit,
                runner_start.is_some(),
                population,
            ) != super::native_stop::NativeStopDecision::CommitLost
            {
                return Ok(());
            }
            // A failed-but-retained Unit can be queried again while the cgroup
            // is gone. Confirm it still owns the same invocation and is still
            // failed, not a different process launched under the same name.
            if bound_failed_unit {
                let recheck = super::platform::systemctl_show(&a.unit_name)?;
                if !super::native_stop::failed_unit_matches_runner(
                    recheck.get("LoadState").map(String::as_str),
                    recheck.get("ActiveState").map(String::as_str),
                    recheck.get("InvocationID").map(String::as_str),
                    runner_start
                        .as_ref()
                        .map(|start| start.invocation_id.as_str())
                        .unwrap_or(""),
                    recheck.get("MainPID").map(String::as_str),
                ) || super::platform::unit_has_pending_job(&recheck)
                    || super::platform::cgroup_population(cgroup)?
                        != super::platform::CgroupPopulation::Removed
                {
                    return Ok(());
                }
            }
            // Kernel cgroup quiescence proves the bound process tree is gone.
            // Without a Runner result the execution outcome remains LOST,
            // not a fabricated successful cancellation or external effect.
            let (terminal_state, reason_code) =
                ("lost", "NATIVE_CGROUP_QUIESCENT_NO_TERMINAL_RESULT");
            let native_receipt = json!({
                "schemaVersion": 1,
                "jobId": job,
                "attemptId": a.attempt_id,
                "unitName": a.unit_name,
                "activeState": properties.get("ActiveState"),
                "loadState": properties.get("LoadState"),
                "controlGroup": cgroup,
                "runnerStartObserved": runner_start.is_some(),
                "runnerStartDigest": runner_start_digest,
                "nativeCgroupState": population.as_str(),
                "failedUnitInvocationBound": bound_failed_unit,
                "nativeUnitResult": properties.get("Result"),
                "kernelCgroupPopulated": population.observed_population(),
                "kernelCgroupRemoved": removed,
                "finishedAtMs": now()?,
                "terminalState": terminal_state
            });
            let proposed_bytes = serde_json::to_vec(&native_receipt).map_err(io)?;
            let receipt_path = path.join("native-stop-evidence.json");
            let receipt_lock = fs::OpenOptions::new()
                .create(true)
                .truncate(false)
                .write(true)
                .open(path.join("native-stop-evidence.lock"))
                .map_err(io)?;
            // Rust std locks this File as flock(LOCK_EX) on Unix and
            // LockFileEx on Windows. Keep the exclusive guard alive until
            // the native receipt and PG terminal+Artifact CAS are resolved.
            // The lock is relinquished automatically when File is dropped.
            receipt_lock.lock().map_err(io)?;
            // A result that arrived while systemctl/cgroup was being queried
            // must take the existing digest/identity-verified result path on
            // the *next* reconciliation. Do not commit an irreversible LOST
            // terminal when that stronger Runner receipt is now available.
            // At this point the bound native cgroup is already quiescent, so
            // the Runner cannot subsequently publish this file from the
            // same owned process tree.
            if !runner_result_still_absent(&path)? {
                return Ok(());
            }
            let receipt_bytes = if receipt_path.exists() {
                // A PG COMMIT acknowledgement can be lost after immutable
                // native evidence was written. Native Unit LoadState may
                // subsequently change from inactive to not-found: do not
                // re-author the original evidence or make a retry impossible.
                // Recheck kernel quiescence above and then replay the original
                // receipt only for the same exact Attempt/Runner identity.
                let retained = fs::read(&receipt_path).map_err(io)?;
                let prior: serde_json::Value = serde_json::from_slice(&retained).map_err(io)?;
                if prior["schemaVersion"].as_u64() != Some(1)
                    || prior["jobId"].as_str() != Some(job)
                    || prior["attemptId"].as_str() != Some(a.attempt_id.as_str())
                    || prior["unitName"].as_str() != Some(a.unit_name.as_str())
                    || prior["controlGroup"].as_str() != Some(cgroup)
                    || prior["runnerStartDigest"].as_str() != Some(runner_start_digest.as_str())
                    || prior["runnerStartObserved"].as_bool() != Some(true)
                    || !matches!(
                        prior["nativeCgroupState"].as_str(),
                        Some("unpopulated" | "removed")
                    )
                    || prior["terminalState"].as_str() != Some(terminal_state)
                {
                    return Err(error("native stop evidence identity mismatch"));
                }
                retained
            } else {
                universal::write_bytes_atomic(&receipt_path, &proposed_bytes).map_err(io)?;
                proposed_bytes
            };
            let receipt_digest = universal::sha256_bytes(&receipt_bytes);
            let retained: serde_json::Value = serde_json::from_slice(&receipt_bytes).map_err(io)?;
            let finished_at_ms = retained["finishedAtMs"]
                .as_i64()
                .ok_or_else(|| error("native stop receipt omitted finish time"))?;
            let terminal = PgTerminalNoArtifacts {
                attempt_id: a.attempt_id.clone(),
                expected_row_version: a.row_version as i64,
                terminal_state: terminal_state.to_string(),
                result_digest: receipt_digest.clone(),
                reason_code: reason_code.to_string(),
                exit_code: None,
                finished_at_ms,
                expected_source_sha256: self.config.source_sha256.clone(),
            };
            let artifact = PgArtifactRegistration {
                artifact_id: format!("artifact-{}-native-stop", a.attempt_id),
                kind: "native_stop_evidence".to_string(),
                relative_path: "native-stop-evidence.json".to_string(),
                digest: receipt_digest,
                media_type: "application/json".to_string(),
                byte_length: i64::try_from(receipt_bytes.len()).map_err(io)?,
                truncated: false,
                created_at_ms: finished_at_ms,
            };
            // Reuse the existing PG atomic terminal/reservation/Artifact
            // transaction. Kernel process absence is evidence of liveness,
            // not proof of a successful arbitrary external effect.
            db.commit_terminal_with_artifacts(&terminal, &[artifact])
                .map_err(pg)?;
            // Only now may systemd forget a failed transient. This ordering
            // keeps its positive failure/InvocationID evidence available for
            // the irreversible LOST decision and its durable receipt.
            super::platform::release_terminal_unit(&a.unit_name);
        }
        Ok(())
    }
    pub(super) fn project(
        &self,
        db: &mut PgAdmissionStore,
        request: &JobObserveRequest,
    ) -> RuntimeResult<JobObservation> {
        let snapshot = match db
            .observe_job_readonly(&request.job_id, &self.config.source_sha256)
            .map_err(pg)?
        {
            PgJobReadback::Observed(s) => s,
            PgJobReadback::Inconclusive => {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::ReconciliationRequired,
                    "committed PG Job lacks coherent exact lifecycle evidence",
                    Some("jobId"),
                    false,
                )
                .with_operation_id(&request.job_id))
            }
        };
        let (a, p, operation) = self.readback_attempt(db, &snapshot)?;
        let terminal = snapshot.resolution.is_some();
        let rows=db.client.query("SELECT artifact_id,kind,digest,byte_length,truncated,relative_path FROM artifacts WHERE job_id=$1 ORDER BY artifact_id", &[&request.job_id]).map_err(pg_read_error)?;
        let artifacts=rows.iter().map(|r|json!({"artifactId":r.get::<_,String>(0),"attemptId":a.attempt_id,"kind":r.get::<_,String>(1),"digest":r.get::<_,String>(2),"retainedBytes":r.get::<_,i64>(3),"truncated":r.get::<_,bool>(4)})).collect::<Vec<_>>();
        let exit: Option<i32> = db
            .client
            .query_one(
                "SELECT exit_code FROM attempts WHERE attempt_id=$1",
                &[&a.attempt_id],
            )
            .map_err(pg_read_error)?
            .get(0);
        // Preserve the existing projection for historical terminal variants.
        // An OS-only LOST reconciliation is the new explicit exception:
        // it has a committed native-stop Artifact, not a Runner result.json.
        let result_available = terminal
            && rows
                .iter()
                .any(|row| row.get::<_, String>(1) == "execution_result");
        let delivery = pg_delivery_disposition(snapshot.resolution.as_deref(), result_available);
        let mut value = json!({"jobId":request.job_id,"operationDigest":operation,"status":snapshot.resolution.clone().unwrap_or(snapshot.attempt_state.clone()),"desiredState":snapshot.desired_state,"attemptId":a.attempt_id,"attemptState":snapshot.attempt_state,"terminationIntent":snapshot.termination_intent,"exitCode":exit,"executionTerminal":terminal,"executionDisposition":snapshot.resolution,"deliveryDisposition":delivery,"effectiveLimits":{"timeoutMs":p.timeout_ms,"stdoutLimitBytes":p.stdout_limit_bytes,"stderrLimitBytes":p.stderr_limit_bytes},"recoveryRequired":needs_recovery_observation(a.state, terminal),"semanticCompletionEvaluated":false,"resultAvailable":result_available,"artifactsAvailable":!artifacts.is_empty(),"artifacts":artifacts});
        for (kind, limit, offset) in [
            ("stdout", request.stdout_tail_bytes, request.stdout_offset),
            ("stderr", request.stderr_tail_bytes, request.stderr_offset),
        ] {
            // Lost/orphaned or other no-Artifact terminal outcomes have no
            // committed stream bytes. Do not fail observation merely because
            // a log is absent, and never project unregistered terminal bytes.
            if terminal && !rows.iter().any(|row| row.get::<_, String>(1) == kind) {
                continue;
            }
            let registered = if terminal {
                rows.iter().find(|row| row.get::<_, String>(1) == kind)
            } else {
                None
            };
            let relative: Option<String> = registered.map(|row| row.get(5));
            let relative_path =
                output_projection_relative_path(kind, terminal, relative.as_deref())?;
            let path = Path::new(&a.bundle_path).join(&relative_path);
            if path.exists() {
                let (window, begin, end, available) = if terminal {
                    // The terminal log is immutable evidence. Verify the entire
                    // exact file against PostgreSQL before returning any bytes.
                    let bytes = {
                        use std::io::Read;
                        let dir = universal::open_directory_nofollow(Path::new(&a.bundle_path))
                            .map_err(io)?;
                        let file = universal::open_regular_file_beneath(&dir, &relative_path, true)
                            .map_err(io)?;
                        let mut bytes = vec![];
                        file.take(self.config.executor.max_output_bytes + 1)
                            .read_to_end(&mut bytes)
                            .map_err(io)?;
                        if bytes.len() as u64 > self.config.executor.max_output_bytes {
                            return Err(error("output exceeds retained ceiling"));
                        }
                        bytes
                    };
                    let available = bytes.len() as u64;
                    let begin = offset
                        .unwrap_or(available.saturating_sub(limit))
                        .min(available);
                    let end = begin.saturating_add(limit).min(available);
                    let expected = registered
                        .ok_or_else(|| error("terminal output Artifact registration missing"))?;
                    if expected.get::<_, i64>(3) != bytes.len() as i64
                        || expected.get::<_, String>(2) != universal::sha256_bytes(&bytes)
                    {
                        return Err(RuntimeError::new(
                            RuntimeErrorCode::ArtifactIdentityConflict,
                            "terminal output bytes disagree with PostgreSQL Artifact evidence",
                            Some("artifact"),
                            false,
                        ));
                    }
                    (
                        bytes[begin as usize..end as usize].to_vec(),
                        begin,
                        end,
                        available,
                    )
                } else {
                    active_log_window(&path, self.config.executor.max_output_bytes, offset, limit)?
                };
                value[format!("{kind}Tail")] = json!(String::from_utf8_lossy(&window));
                value[format!("{kind}Offset")] = json!(begin);
                value[format!("{kind}NextOffset")] = json!(end);
                value[format!("{kind}AvailableBytes")] = json!(available);
                value[format!("{kind}Eof")] = json!(end == available);
            } else if terminal {
                return Err(error("terminal output Artifact file missing"));
            }
        }
        serde_json::from_value(value).map_err(io)
    }
}

#[cfg(test)]
mod native_runner_start_tests;

#[cfg(test)]
mod late_runner_result_tests;

#[cfg(test)]
mod scan_fairness_tests;

#[cfg(test)]
mod active_log_window_tests;

#[cfg(test)]
mod recovery_projection_contract_tests;

#[cfg(test)]
mod pg_reconciliation_direct_error_tests;

#[cfg(test)]
mod native_stop_lock_portability_tests;
