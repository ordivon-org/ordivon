//! PostgreSQL Attempt readback, native reconciliation, and Job result projection.
use super::*;

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

fn runner_result_still_absent(path: &Path) -> RuntimeResult<bool> {
    match fs::symlink_metadata(path.join("result.json")) {
        Err(err) if err.kind() == std::io::ErrorKind::NotFound => Ok(true),
        Ok(metadata) if metadata.file_type().is_file() => Ok(false),
        Ok(_) => Err(error("Runner result path is not a regular file")),
        Err(err) => Err(io(err)),
    }
}

/// One reconciliation epoch has a fixed upper sort key. Fresh jobs beyond
/// this bound wait for the next epoch instead of continually extending the
/// current scan and starving an older unresolved job.
/// PostgreSQL state, not this in-memory cursor, remains the authority.
fn latest_reconciliation_key(
    client: &mut postgres::Client,
    cancelled_only: bool,
) -> Result<Option<(i64, String)>, postgres::Error> {
    const SQL: &str = r#"
        SELECT j.created_at_ms, j.job_id
        FROM jobs j
        JOIN attempts a ON a.attempt_id = j.current_attempt_id
          AND a.job_id = j.job_id
        WHERE j.resolution IS NULL
          AND (j.desired_state = 'cancelled'
               OR (NOT $1 AND a.state IN ('starting','running','stopping','recovering')))
        ORDER BY j.created_at_ms DESC, j.job_id DESC
        LIMIT 1
    "#;
    Ok(client
        .query_opt(SQL, &[&cancelled_only])?
        .map(|row| (row.get::<_, i64>(0), row.get::<_, String>(1))))
}

/// A bounded keyset page never crosses the epoch fence. A newly inserted
/// backdated row can be observed during a later epoch; an epoch is not a
/// repeatable-read snapshot, and the key is not a PostgreSQL commit sequence.
fn scan_reconciliation_page(
    client: &mut postgres::Client,
    limit: u32,
    cancelled_only: bool,
    cursor: Option<&(i64, String)>,
    upper_fence: &(i64, String),
) -> Result<Vec<postgres::Row>, postgres::Error> {
    const SQL: &str = r#"
        SELECT j.job_id, j.principal, j.desired_state, j.created_at_ms
        FROM jobs j
        JOIN attempts a ON a.attempt_id = j.current_attempt_id
          AND a.job_id = j.job_id
        WHERE j.resolution IS NULL
          AND (j.desired_state = 'cancelled'
               OR (NOT $2 AND a.state IN ('starting','running','stopping','recovering')))
          AND ($3::BIGINT IS NULL
               OR (j.created_at_ms, j.job_id) > ($3::BIGINT, $4::TEXT))
          AND (j.created_at_ms, j.job_id) <= ($5::BIGINT, $6::TEXT)
        ORDER BY j.created_at_ms, j.job_id
        LIMIT $1
    "#;
    let (at, id) = cursor
        .map(|(at, id)| (Some(*at), Some(id.as_str())))
        .unwrap_or((None, None));
    client.query(
        SQL,
        &[
            &i64::from(limit),
            &cancelled_only,
            &at,
            &id,
            &upper_fence.0,
            &upper_fence.1,
        ],
    )
}

/// A partial page or reaching the exact epoch upper fence completes a sweep.
/// Reset both fields together so a new epoch can include freshly arrived jobs.
type ReconciliationNextPage = (Option<(i64, String)>, Option<(i64, String)>);

fn next_reconciliation_cursor(
    pending: &[postgres::Row],
    limit: u32,
    upper_fence: &(i64, String),
) -> ReconciliationNextPage {
    let Some(last) = pending.last() else {
        return (None, None);
    };
    let key = (last.get::<_, i64>(3), last.get::<_, String>(0));
    // Use equality, not Rust's lexical >=: a PostgreSQL text collation can
    // order job_id strings differently from Rust's bytewise String order.
    if pending.len() < limit as usize || key == *upper_fence {
        (None, None)
    } else {
        (Some(key), Some(upper_fence.clone()))
    }
}

/// Version-stamped cursor/fence progress guards against concurrent scans and
/// ABA even when an epoch wraps to an earlier row or to None.
fn advance_reconciliation_cursor(
    slot: &mut ReconciliationCursor,
    observed_generation: u64,
    next_key: Option<(i64, String)>,
    next_upper_fence: Option<(i64, String)>,
) -> bool {
    if slot.generation != observed_generation {
        return false;
    }
    let Some(generation) = slot.generation.checked_add(1) else {
        return false;
    };
    slot.key = next_key;
    slot.upper_fence = next_upper_fence;
    slot.generation = generation;
    true
}

/// Active Runner logs are an evolving preview, not a committed Artifact.
/// Seek directly to the requested window instead of reading up to the full
/// output ceiling on every Job observation. Terminal logs use the independent
/// Artifact digest check in project() and must still verify all committed bytes.
fn active_log_window(
    path: &Path,
    output_ceiling: u64,
    offset: Option<u64>,
    limit: u64,
) -> RuntimeResult<(Vec<u8>, u64, u64, u64)> {
    use std::io::{Read, Seek, SeekFrom};

    let mut file = fs::File::open(path).map_err(io)?;
    let available = file.seek(SeekFrom::End(0)).map_err(io)?;
    if available > output_ceiling {
        return Err(error("output exceeds retained ceiling"));
    }
    let begin = offset
        .unwrap_or(available.saturating_sub(limit))
        .min(available);
    let end = begin.saturating_add(limit).min(available);
    file.seek(SeekFrom::Start(begin)).map_err(io)?;
    let mut window = vec![0; usize::try_from(end - begin).map_err(io)?];
    file.read_exact(&mut window).map_err(io)?;
    Ok((window, begin, end, available))
}

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
    pub(super) fn attempt(
        &self,
        db: &mut PgAdmissionStore,
        job: &str,
    ) -> RuntimeResult<(AttemptRecord, RuntimeExecutionPlan, String)> {
        let r = require_recovery_current_attempt(
            db.client
                .query_opt(RECOVERY_CURRENT_ATTEMPT_SQL, &[&job])
                .map_err(pg_read_error)?,
            job,
        )?;
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

    fn decode_attempt_record(
        &self,
        r: &postgres::Row,
        job: &str,
    ) -> RuntimeResult<(AttemptRecord, RuntimeExecutionPlan, String)> {
        let a:AttemptRecord=serde_json::from_value(json!({"attemptId":r.get::<_,String>(0),"jobId":job,"attemptNumber":r.get::<_, i64>(11),"state":r.get::<_,String>(1),"terminationIntent":r.get::<_,String>(2),"launchTokenDigest":r.get::<_,String>(3),"bundlePath":r.get::<_,String>(4),"unitName":r.get::<_,String>(5),"createdAtMs":r.get::<_,i64>(6),"rowVersion":r.get::<_,i64>(7),"bundleDigest":r.get::<_,Option<String>>(8)})).map_err(io)?;
        let expected = self
            .config
            .executor
            .store_root
            .join("pg-attempts")
            .join(&a.attempt_id);
        if Path::new(&a.bundle_path) != expected {
            return Err(error("Attempt bundle outside PG store"));
        }
        Ok((a, decode(&r.get::<_, String>(9))?, r.get(10)))
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
        let (mut a, plan, operation) = self.attempt(db, job)?;
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
                return Err(error("native runner changed after admission"));
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
            // Reuse the existing native Runner FD presentation and Workspace-
            // private cache. The PG plan already froze the effective env at
            // admission; reconstruct only its deterministic physical backing.
            // Old committed plans without the FD keep their original behavior.
            let build_target_backing =
                if crate::runtime::engine::requires_private_cargo_build_target(&plan) {
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
                payload: None,
                inherit_host_environment: true,
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
            fs::create_dir_all(&a.bundle_path).map_err(io)?;
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
            db.mark_dispatch_issued_pg(&PgDispatchIssued {
                attempt_id: a.attempt_id.clone(),
                expected_row_version: a.row_version as i64,
                expected_bundle_digest: digest,
                observed_at_ms: now()?,
                expected_source_sha256: self.config.source_sha256.clone(),
            })
            .map_err(pg)?;
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
        }
        let path = Path::new(&a.bundle_path);
        if a.state == AttemptState::Accepted
            && a.termination_intent == AttemptTerminationIntent::StopRequested
        {
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
            fs::create_dir_all(path).map_err(io)?;
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
            return Ok(());
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
            if super::native_stop::decide_native_stop(
                super::platform::unit_is_active(&properties),
                super::platform::unit_has_pending_job(&properties),
                properties
                    .get("LoadState")
                    .is_some_and(|state| state == "not-found"),
                runner_start.is_some(),
                population,
            ) != super::native_stop::NativeStopDecision::CommitLost
            {
                return Ok(());
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
            use std::os::fd::AsRawFd;
            // SAFETY: the open File owns a valid descriptor; the lock is released on drop.
            if unsafe { libc::flock(receipt_lock.as_raw_fd(), libc::LOCK_EX) } != 0 {
                return Err(io(std::io::Error::last_os_error()));
            }
            // A result that arrived while systemctl/cgroup was being queried
            // must take the existing digest/identity-verified result path on
            // the *next* reconciliation. Do not commit an irreversible LOST
            // terminal when that stronger Runner receipt is now available.
            // At this point the bound native cgroup is already quiescent, so
            // the Runner cannot subsequently publish this file from the
            // same owned process tree.
            if !runner_result_still_absent(path)? {
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
        let mut value = json!({"jobId":request.job_id,"operationDigest":operation,"status":snapshot.resolution.clone().unwrap_or(snapshot.attempt_state.clone()),"desiredState":snapshot.desired_state,"attemptId":a.attempt_id,"attemptState":snapshot.attempt_state,"terminationIntent":snapshot.termination_intent,"exitCode":exit,"executionTerminal":terminal,"executionDisposition":snapshot.resolution,"deliveryDisposition":if terminal {"committed"} else {"in_progress"},"effectiveLimits":{"timeoutMs":p.timeout_ms,"stdoutLimitBytes":p.stdout_limit_bytes,"stderrLimitBytes":p.stderr_limit_bytes},"recoveryRequired":needs_recovery_observation(a.state, terminal),"semanticCompletionEvaluated":false,"resultAvailable":result_available,"artifactsAvailable":!artifacts.is_empty(),"artifacts":artifacts});
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
            let path = Path::new(&a.bundle_path).join(format!("{kind}.log"));
            if path.exists() {
                let (window, begin, end, available) = if terminal {
                    // The terminal log is immutable evidence. Verify the entire
                    // exact file against PostgreSQL before returning any bytes.
                    let bytes = {
                        use std::io::Read;
                        let file = fs::File::open(&path).map_err(io)?;
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
                    let expected = rows
                        .iter()
                        .find(|row| row.get::<_, String>(1) == kind)
                        .ok_or_else(|| error("terminal output Artifact registration missing"))?;
                    if expected.get::<_, String>(5) != format!("{kind}.log")
                        || expected.get::<_, i64>(3) != bytes.len() as i64
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
mod late_runner_result_tests {
    use super::*;

    #[test]
    fn post_quiescence_recheck_prevents_false_os_only_lost() {
        // A first probe sees no result; the actual Runner writes it while
        // an independent systemctl/cgroup probe is in flight. The final
        // negative-evidence gate MUST reject LOST in that second state.
        let root =
            std::env::temp_dir().join(format!("ordivon-pg-late-result-{}", uuid::Uuid::now_v7()));
        fs::create_dir(&root).unwrap();
        assert!(runner_result_still_absent(&root).unwrap());
        fs::write(root.join("result.json"), b"native runner terminal bytes").unwrap();
        assert!(!runner_result_still_absent(&root).unwrap());
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn post_quiescence_missing_result_still_allows_native_lost() {
        let root =
            std::env::temp_dir().join(format!("ordivon-pg-absent-result-{}", uuid::Uuid::now_v7()));
        fs::create_dir(&root).unwrap();
        assert!(runner_result_still_absent(&root).unwrap());
        fs::remove_dir_all(root).unwrap();
    }

    #[cfg(target_family = "unix")]
    #[test]
    fn suspicious_runner_result_path_fails_closed() {
        let root = std::env::temp_dir().join(format!(
            "ordivon-pg-result-topology-{}",
            uuid::Uuid::now_v7()
        ));
        fs::create_dir(&root).unwrap();
        fs::create_dir(root.join("result.json")).unwrap();
        assert!(runner_result_still_absent(&root).is_err());
        fs::remove_dir(root.join("result.json")).unwrap();
        std::os::unix::fs::symlink("/dev/null", root.join("result.json")).unwrap();
        assert!(runner_result_still_absent(&root).is_err());
        fs::remove_dir_all(root).unwrap();
    }
}

#[cfg(test)]
mod scan_fairness_tests {
    use super::*;

    #[test]
    fn stale_scan_cannot_regress_fence_after_concurrent_advance_and_aba() {
        let x = (10, "job-010".to_string());
        let y = (110, "job-110".to_string());
        let z = (210, "job-210".to_string());
        let mut cursor = ReconciliationCursor {
            key: Some(x.clone()),
            upper_fence: Some(z.clone()),
            generation: 0,
        };
        let stale = cursor.clone();
        assert!(advance_reconciliation_cursor(
            &mut cursor,
            0,
            Some(y.clone()),
            Some(z.clone())
        ));
        assert!(advance_reconciliation_cursor(
            &mut cursor,
            1,
            Some(z.clone()),
            Some(z.clone())
        ));
        assert!(!advance_reconciliation_cursor(
            &mut cursor,
            stale.generation,
            None,
            None
        ));
        assert_eq!(cursor.key, Some(z.clone()));
        assert_eq!(cursor.upper_fence, Some(z.clone()));

        // Exact fence reached: the next epoch starts at the oldest row.
        assert!(advance_reconciliation_cursor(&mut cursor, 2, None, None));
        let old_reset = cursor.clone();
        assert!(advance_reconciliation_cursor(
            &mut cursor,
            3,
            Some(x.clone()),
            Some(z.clone())
        ));
        assert!(advance_reconciliation_cursor(&mut cursor, 4, None, None));
        assert!(!advance_reconciliation_cursor(
            &mut cursor,
            old_reset.generation,
            Some(y),
            Some(z)
        ));
        assert!(cursor.key.is_none());
        assert!(cursor.upper_fence.is_none());
    }

    /// CurrentAttempt is a committed Job pointer: a newer numbered attempt
    /// can exist without owning the current native Runner / terminal decision.
    #[test]
    #[ignore = "requires explicit disposable ORDIVON_PG_TEST_DSN"]
    fn native_pg_recovery_requires_current_attempt_not_highest_attempt_number() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("dedicated disposable PostgreSQL cluster required");
        let mut db = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
        db.batch_execute(
            "CREATE TEMP TABLE jobs (
               job_id text PRIMARY KEY, current_attempt_id text,
               execution_plan_json text, operation_digest text);
             CREATE TEMP TABLE attempts (
               attempt_id text PRIMARY KEY, job_id text,
               attempt_number bigint, state text, termination_intent text,
               launch_token_digest text, bundle_path text, unit_name text,
               created_at_ms bigint, row_version bigint, bundle_digest text);
             INSERT INTO jobs VALUES
               ('job-a','attempt-current','{}','operation-a');
             INSERT INTO attempts VALUES
               ('attempt-current','job-a',4,'running','natural','launch-a',
                '/tmp/current','unit-current',10,9,NULL),
               ('attempt-future','job-a',5,'failed','natural','launch-b',
                '/tmp/future','unit-future',20,10,NULL);",
        )
        .unwrap();
        let selected = db
            .query_one(RECOVERY_CURRENT_ATTEMPT_SQL, &[&"job-a"])
            .unwrap();
        assert_eq!(
            selected.get::<_, String>(0),
            "attempt-current",
            "recovery must never substitute a higher-numbered Attempt"
        );
        assert_eq!(selected.len(), 12, "real AttemptNumber must be selected");
        assert_eq!(selected.get::<_, i64>(11), 4);
        db.execute(
            "UPDATE jobs SET current_attempt_id=NULL WHERE job_id='job-a'",
            &[],
        )
        .unwrap();
        let absent = db
            .query_opt(RECOVERY_CURRENT_ATTEMPT_SQL, &[&"job-a"])
            .unwrap();
        assert!(
            absent.is_none(),
            "missing authoritative current Attempt must not fall back to history"
        );
        let unresolved = require_recovery_current_attempt(absent, "job-a").unwrap_err();
        assert_eq!(unresolved.code, RuntimeErrorCode::ReconciliationRequired);
        assert_eq!(unresolved.field.as_deref(), Some("currentAttemptId"));
        db.execute(
            "UPDATE jobs SET current_attempt_id='attempt-alien' WHERE job_id='job-a'",
            &[],
        )
        .unwrap();
        db.execute(
            "INSERT INTO jobs VALUES ('job-other','attempt-alien','{}','operation-other')",
            &[],
        )
        .unwrap();
        db.execute(
            "INSERT INTO attempts VALUES ('attempt-alien','job-other',1,'running',
               'natural','alien','/tmp/alien','unit-alien',30,0,NULL)",
            &[],
        )
        .unwrap();
        let foreign = db
            .query_opt(RECOVERY_CURRENT_ATTEMPT_SQL, &[&"job-a"])
            .unwrap();
        assert_eq!(
            require_recovery_current_attempt(foreign, "job-a")
                .unwrap_err()
                .code,
            RuntimeErrorCode::ReconciliationRequired,
            "foreign current Attempt must be reconciliation-required, not registry unavailable"
        );
    }

    /// A terminal Job commits resolution and *clears* current_attempt_id.
    /// Only the already verified snapshot Attempt may be shown to readers.
    /// Generic native release/reconcile effects must still require current.
    #[test]
    #[ignore = "requires explicit disposable ORDIVON_PG_TEST_DSN"]
    fn native_pg_terminal_verified_readback_does_not_reauthorize_historical_effects() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("dedicated disposable PostgreSQL cluster required");
        let mut db = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
        db.batch_execute(
            "CREATE TEMP TABLE jobs (
                job_id text PRIMARY KEY, current_attempt_id text,
                resolution text, row_version bigint, execution_plan_json text,
                operation_digest text);
             CREATE TEMP TABLE job_runtime_release_effects (job_id text PRIMARY KEY);
             INSERT INTO job_runtime_release_effects VALUES ('terminal-a');
             CREATE TEMP TABLE attempts (
                attempt_id text PRIMARY KEY, job_id text,
                attempt_number bigint, state text, termination_intent text,
                launch_token_digest text, bundle_path text, unit_name text,
                created_at_ms bigint, row_version bigint, bundle_digest text);
             INSERT INTO jobs VALUES
                ('terminal-a',NULL,'succeeded',8,'{}','op-a'),
                ('accepted-b','attempt-b',NULL,2,'{}','op-b');
             INSERT INTO attempts VALUES
                ('terminal-verified','terminal-a',4,'succeeded','natural',
                    'launch-a','/tmp/a','unit-a',10,7,NULL),
                ('later-unverified','terminal-a',5,'running','natural',
                    'launch-future','/tmp/future','unit-future',11,0,NULL),
                ('attempt-b','accepted-b',1,'accepted','natural',
                    'launch-b','/tmp/b','unit-b',12,0,NULL);",
        )
        .unwrap();

        // The existing dispatch/reconciliation entry must not try to
        // reauthorize a terminal ReleaseEffect after its PG current pointer
        // was atomically cleared. Unresolved accepted work still requires
        // strict current identity and stays eligible for normal reconciliation.
        let release_terminal = db
            .query_one(RECONCILIATION_STAGE_SQL, &[&"terminal-a"])
            .unwrap();
        assert_eq!(
            release_terminal.get::<_, Option<String>>(0).as_deref(),
            Some("succeeded")
        );
        assert!(release_terminal.get::<_, bool>(1));
        let unresolved_stage = db
            .query_one(RECONCILIATION_STAGE_SQL, &[&"accepted-b"])
            .unwrap();
        assert!(unresolved_stage.get::<_, Option<String>>(0).is_none());
        assert!(!unresolved_stage.get::<_, bool>(1));

        // In this fixture, the lifecycle/event verifier has already
        // established exact terminal-verified; a later historical Attempt
        // must not silently become the effect or readback authority.
        let verified: Option<String> = Some("succeeded".into());
        let row = db
            .query_one(
                READBACK_VERIFIED_ATTEMPT_SQL,
                &[
                    &"terminal-a",
                    &"terminal-verified",
                    &8_i64,
                    &7_i64,
                    &verified,
                ],
            )
            .unwrap();
        assert_eq!(row.get::<_, String>(0), "terminal-verified");
        assert_eq!(row.get::<_, i64>(11), 4);
        assert!(
            db.query_opt(RECOVERY_CURRENT_ATTEMPT_SQL, &[&"terminal-a"])
                .unwrap()
                .is_none(),
            "cleared terminal pointer must remain ineligible for native effects"
        );

        assert!(
            db.query_opt(
                READBACK_VERIFIED_ATTEMPT_SQL,
                &[
                    &"terminal-a",
                    &"later-unverified",
                    &8_i64,
                    &0_i64,
                    &verified
                ],
            )
            .unwrap()
            .is_none(),
            "later historical running Attempt cannot be projected as terminal"
        );
        assert!(
            db.query_opt(
                READBACK_VERIFIED_ATTEMPT_SQL,
                &[
                    &"accepted-b",
                    &"terminal-verified",
                    &2_i64,
                    &7_i64,
                    &None::<String>
                ],
            )
            .unwrap()
            .is_none(),
            "Attempt must belong to requested Job"
        );
        assert!(
            db.query_opt(
                READBACK_VERIFIED_ATTEMPT_SQL,
                &[
                    &"terminal-a",
                    &"terminal-verified",
                    &7_i64,
                    &7_i64,
                    &verified
                ],
            )
            .unwrap()
            .is_none(),
            "stale Job row-version is inconclusive"
        );
        assert!(
            db.query_opt(
                READBACK_VERIFIED_ATTEMPT_SQL,
                &[
                    &"terminal-a",
                    &"terminal-verified",
                    &8_i64,
                    &6_i64,
                    &verified
                ],
            )
            .unwrap()
            .is_none(),
            "stale Attempt row-version is inconclusive"
        );

        let pending: Option<String> = None;
        let current = db
            .query_one(
                READBACK_VERIFIED_ATTEMPT_SQL,
                &[&"accepted-b", &"attempt-b", &2_i64, &0_i64, &pending],
            )
            .unwrap();
        assert_eq!(current.get::<_, String>(0), "attempt-b");
        db.execute(
            "UPDATE jobs SET current_attempt_id=NULL WHERE job_id='accepted-b'",
            &[],
        )
        .unwrap();
        assert!(
            db.query_opt(
                READBACK_VERIFIED_ATTEMPT_SQL,
                &[&"accepted-b", &"attempt-b", &2_i64, &0_i64, &pending],
            )
            .unwrap()
            .is_none(),
            "unresolved missing current remains fail closed"
        );
    }

    #[test]
    #[ignore = "requires explicit disposable ORDIVON_PG_TEST_DSN"]
    fn native_pg_release_effect_uses_current_attempt_for_dispatch_boundary() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("dedicated disposable PostgreSQL cluster required");
        let mut db = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
        db.batch_execute(
            "CREATE TEMP TABLE jobs (
                job_id text PRIMARY KEY, current_attempt_id text);
             CREATE TEMP TABLE attempts (
                attempt_id text PRIMARY KEY, job_id text,
                attempt_number bigint, state text);
             INSERT INTO jobs VALUES ('release-a','release-current');
             INSERT INTO attempts VALUES
                ('release-current','release-a',1,'accepted'),
                ('release-future','release-a',2,'running');",
        )
        .unwrap();
        let row = db
            .query_one(RELEASE_CURRENT_ATTEMPT_STATE_SQL, &[&"release-a"])
            .unwrap();
        assert_eq!(row.get::<_, String>(0), "accepted");
        db.execute(
            "UPDATE jobs SET current_attempt_id=NULL WHERE job_id='release-a'",
            &[],
        )
        .unwrap();
        assert!(
            db.query_opt(RELEASE_CURRENT_ATTEMPT_STATE_SQL, &[&"release-a"])
                .unwrap()
                .is_none(),
            "missing release current pointer cannot borrow a historical Attempt"
        );
    }

    /// PostgreSQL allows current_attempt_id to refer to an Attempt belonging
    /// to another Job; a foreign key on attempts.job_id does not close this
    /// inverse identity edge. Recovery must not borrow another Job's state.
    #[test]
    #[ignore = "requires explicit disposable ORDIVON_PG_TEST_DSN"]
    fn native_postgres_recovery_rejects_cross_job_attempt_binding() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("use a dedicated disposable PostgreSQL cluster");
        let mut db = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
        db.batch_execute(
            "CREATE TEMP TABLE jobs (
                job_id text PRIMARY KEY, principal text, desired_state text,
                resolution text, current_attempt_id text, created_at_ms bigint
             );
             CREATE TEMP TABLE attempts (
                attempt_id text PRIMARY KEY, job_id text NOT NULL, state text
             );
             INSERT INTO jobs VALUES
               ('job-a','owner','run',NULL,'attempt-a',1),
               ('job-b','owner','run',NULL,'attempt-a',2);
             INSERT INTO attempts VALUES ('attempt-a','job-a','running');",
        )
        .unwrap();
        // The adversarial job-b references a real Attempt, but it belongs to
        // job-a; both the epoch fence and the page selector must reject it.
        let newest = latest_reconciliation_key(&mut db, false).unwrap().unwrap();
        assert_eq!(newest.1, "job-a");
        let page = scan_reconciliation_page(&mut db, 100, false, None, &newest).unwrap();
        assert_eq!(page.len(), 1);
        assert_eq!(page[0].get::<_, String>(0), "job-a");
        db.execute(
            "UPDATE jobs SET desired_state='cancelled' WHERE job_id='job-b'",
            &[],
        )
        .unwrap();
        let cancelled = latest_reconciliation_key(&mut db, true).unwrap();
        assert!(
            cancelled.is_none(),
            "cancelled lane also requires attempt ownership"
        );
    }

    /// Real SQL and >100 unresolved Jobs in an explicitly disposable PG.
    #[test]
    #[ignore = "requires explicit disposable ORDIVON_PG_TEST_DSN"]
    fn native_postgres_scan_advances_beyond_blocked_oldest_page() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("use a dedicated disposable PostgreSQL cluster");
        let mut db = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
        db.batch_execute(
            "CREATE TEMP TABLE jobs (job_id text, principal text, desired_state text, \
                resolution text, current_attempt_id text, created_at_ms bigint); \
             CREATE TEMP TABLE attempts (attempt_id text, job_id text, state text); \
             INSERT INTO jobs \
                SELECT 'job-' || lpad(n::text,3,'0'), 'owner', 'run', NULL, \
                       'attempt-' || n, n::bigint \
                FROM generate_series(1,101) n; \
             INSERT INTO attempts \
                SELECT 'attempt-' || n, 'job-' || lpad(n::text,3,'0'), 'running' \
                FROM generate_series(1,101) n;",
        )
        .unwrap();
        let upper = latest_reconciliation_key(&mut db, false).unwrap().unwrap();
        assert_eq!(upper.1, "job-101");
        let first = scan_reconciliation_page(&mut db, 100, false, None, &upper).unwrap();
        assert_eq!(first.len(), 100);
        assert_eq!(first.last().unwrap().get::<_, String>(0), "job-100");
        let (next, same_fence) = next_reconciliation_cursor(&first, 100, &upper);
        assert_eq!(same_fence.as_ref(), Some(&upper));
        let second = scan_reconciliation_page(&mut db, 100, false, next.as_ref(), &upper).unwrap();
        assert_eq!(second.len(), 1);
        assert_eq!(second[0].get::<_, String>(0), "job-101");
        assert_eq!(
            next_reconciliation_cursor(&second, 100, &upper),
            (None, None)
        );

        db.batch_execute(
            "INSERT INTO jobs VALUES ('job-102','owner','run',NULL,'attempt-102',102);
             INSERT INTO attempts VALUES ('attempt-102','job-102','running');",
        )
        .unwrap();
        let fresh_upper = latest_reconciliation_key(&mut db, false).unwrap().unwrap();
        let revisited = scan_reconciliation_page(&mut db, 100, false, None, &fresh_upper).unwrap();
        assert_eq!(revisited[0].get::<_, String>(0), "job-001");

        db.execute(
            "UPDATE jobs SET desired_state='cancelled' WHERE job_id IN ('job-004','job-101')",
            &[],
        )
        .unwrap();
        let cancelled_upper = latest_reconciliation_key(&mut db, true).unwrap().unwrap();
        let cancelled =
            scan_reconciliation_page(&mut db, 100, true, None, &cancelled_upper).unwrap();
        assert_eq!(cancelled.len(), 2);
        assert_eq!(cancelled[0].get::<_, String>(0), "job-004");
        assert_eq!(cancelled[1].get::<_, String>(0), "job-101");
    }

    /// Every tick admits MORE than a full page of newer eligible Jobs.
    /// The previous short-page solution never wraps in this workload.
    #[test]
    #[ignore = "requires explicit disposable ORDIVON_PG_TEST_DSN"]
    fn native_postgres_sustained_full_pages_cannot_starve_oldest_epoch() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("use a dedicated disposable PostgreSQL cluster");
        let mut db = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
        db.batch_execute(
            "CREATE TEMP TABLE jobs (job_id text, principal text, desired_state text, \
                resolution text, current_attempt_id text, created_at_ms bigint); \
             CREATE TEMP TABLE attempts (attempt_id text, job_id text, state text); \
             INSERT INTO jobs \
                SELECT 'job-' || lpad(n::text,4,'0'), 'owner', 'run', NULL, \
                       'attempt-' || n, n::bigint \
                FROM generate_series(1,300) n; \
             INSERT INTO attempts \
                SELECT 'attempt-' || n, 'job-' || lpad(n::text,4,'0'), 'running' \
                FROM generate_series(1,300) n;",
        )
        .unwrap();
        let original_fence = latest_reconciliation_key(&mut db, false).unwrap().unwrap();
        assert_eq!(original_fence.1, "job-0300");
        let mut cursor: Option<(i64, String)> = None;
        for page in 0..3 {
            let rows =
                scan_reconciliation_page(&mut db, 100, false, cursor.as_ref(), &original_fence)
                    .unwrap();
            assert_eq!(rows.len(), 100, "all three original epoch pages are full");
            assert_eq!(
                rows[0].get::<_, String>(0),
                format!("job-{:04}", 1 + page * 100)
            );
            let (next, fence) = next_reconciliation_cursor(&rows, 100, &original_fence);
            assert_eq!(fence.is_some(), page != 2);
            cursor = next;
            // A fresh 150 eligible Jobs after EVERY full page. Their sort
            // keys exceed original_fence and cannot prolong this epoch.
            let start = 301 + page * 150;
            let end = start + 149;
            db.batch_execute(&format!(
                "INSERT INTO jobs SELECT 'job-' || lpad(n::text,4,'0'), \
                    'owner','run',NULL,'attempt-' || n,n::bigint \
                   FROM generate_series({start},{end}) n; \
                 INSERT INTO attempts SELECT 'attempt-' || n, \
                      'job-' || lpad(n::text,4,'0'),'running' \
                   FROM generate_series({start},{end}) n;"
            ))
            .unwrap();
        }
        assert!(cursor.is_none(), "the full last page closes the epoch");
        // Directly falsify the old unbounded keyset behaviour in this same
        // real PostgreSQL: its next page would follow freshly admitted Jobs,
        // instead of revisiting the unresolved oldest row.
        let old_next: String = db
            .query_one(
                "SELECT j.job_id FROM jobs j JOIN attempts a                  ON a.attempt_id=j.current_attempt_id AND a.job_id=j.job_id                  WHERE j.resolution IS NULL AND a.state='running'                  AND (j.created_at_ms,j.job_id) > (300,'job-0300')                  ORDER BY j.created_at_ms,j.job_id LIMIT 1",
                &[],
            )
            .unwrap()
            .get(0);
        assert_eq!(old_next, "job-0301");
        let fresh_fence = latest_reconciliation_key(&mut db, false).unwrap().unwrap();
        assert_eq!(fresh_fence.1, "job-0750");
        let revisited = scan_reconciliation_page(&mut db, 100, false, None, &fresh_fence).unwrap();
        assert_eq!(
            revisited[0].get::<_, String>(0),
            "job-0001",
            "continuous >=limit arrivals cannot prevent the oldest retry"
        );
    }
}

#[cfg(test)]
mod active_log_window_tests {
    use super::*;
    use std::io::Write;

    #[test]
    fn active_log_tail_and_incremental_offsets_preserve_observation_contract() {
        let path =
            std::env::temp_dir().join(format!("ordivon-pg-active-log-{}", uuid::Uuid::now_v7()));
        let mut initial = vec![b'x'; 1024 * 1024];
        initial.extend_from_slice(b"first");
        fs::write(&path, &initial).unwrap();
        let ceiling = (initial.len() + 16) as u64;

        let (tail, begin, end, available) = active_log_window(&path, ceiling, None, 5).unwrap();
        assert_eq!(tail, b"first");
        assert_eq!(end, available);
        assert_eq!(end - begin, 5);

        let mut file = fs::OpenOptions::new().append(true).open(&path).unwrap();
        file.write_all(b"second").unwrap();
        drop(file);
        let (delta, delta_begin, delta_end, later) =
            active_log_window(&path, ceiling, Some(end), 16).unwrap();
        assert_eq!(delta, b"second");
        assert_eq!(delta_begin, end);
        assert_eq!(delta_end, later);

        let (empty, start, next, total) =
            active_log_window(&path, ceiling, Some(later + 100), 16).unwrap();
        assert!(empty.is_empty());
        assert_eq!((start, next, total), (later, later, later));

        assert!(active_log_window(&path, 16, None, 5).is_err());
        fs::remove_file(path).unwrap();
    }
}

#[cfg(test)]
mod recovery_projection_contract_tests {
    use super::*;

    #[test]
    fn nonterminal_native_transition_requires_reconciliation() {
        for state in [
            AttemptState::Starting,
            AttemptState::Stopping,
            AttemptState::Recovering,
        ] {
            assert!(needs_recovery_observation(state, false));
            assert!(!needs_recovery_observation(state, true));
        }
        for state in [
            AttemptState::Accepted,
            AttemptState::Running,
            AttemptState::Succeeded,
            AttemptState::Failed,
            AttemptState::TimedOut,
            AttemptState::Cancelled,
            AttemptState::Lost,
            AttemptState::Orphaned,
        ] {
            assert!(!needs_recovery_observation(state, false));
        }
    }
}

#[cfg(test)]
mod pg_reconciliation_direct_error_tests {
    use super::*;

    /// Exercise actual PostgreSQL, not a fabricated SQLSTATE.
    #[test]
    #[ignore = "requires explicitly disposable ORDIVON_PG_TEST_DSN and #2123 typed mapper"]
    fn native_postgres_recovery_keeps_server_transaction_abort_sqlstate() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("dedicated disposable PostgreSQL cluster is required");
        let mut db = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
        for (state, busy) in [("40001", true), ("40P01", true), ("23505", false)] {
            let source_error = db
                .batch_execute(&format!(
                    "DO $$ BEGIN RAISE EXCEPTION SQLSTATE '{state}'; END $$;"
                ))
                .unwrap_err();
            let projected = pg_read_error(source_error);
            assert_eq!(
                projected.code,
                if busy {
                    RuntimeErrorCode::RegistryBusy
                } else {
                    RuntimeErrorCode::RegistryUnavailable
                },
                "SQLSTATE {state} must retain typed classification"
            );
            assert_eq!(projected.retryable, busy);
            if busy {
                assert_eq!(projected.retry_after_ms, Some(250));
            }
        }
    }
}
