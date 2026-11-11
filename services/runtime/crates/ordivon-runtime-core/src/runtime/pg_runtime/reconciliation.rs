//! PostgreSQL Attempt readback, native reconciliation, and Job result projection.
use super::*;

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

/// Read at most one physical page. A cursor beyond the last unresolved row
/// wraps to the oldest candidate, so one permanently blocked head cannot
/// prevent future records from receiving an observation.
fn scan_reconciliation_page(
    client: &mut postgres::Client,
    limit: u32,
    cancelled_only: bool,
    cursor: Option<&(i64, String)>,
) -> Result<Vec<postgres::Row>, postgres::Error> {
    const SQL: &str = r#"
        SELECT j.job_id, j.principal, j.desired_state, j.created_at_ms
        FROM jobs j
        JOIN attempts a ON a.attempt_id = j.current_attempt_id
        WHERE j.resolution IS NULL
          AND (j.desired_state = 'cancelled'
               OR (NOT $2 AND a.state IN ('starting','running','stopping','recovering')))
          AND ($3::BIGINT IS NULL
               OR (j.created_at_ms, j.job_id) > ($3::BIGINT, $4::TEXT))
        ORDER BY j.created_at_ms, j.job_id
        LIMIT $1
    "#;
    let (at, id) = cursor
        .map(|(at, id)| (Some(*at), Some(id.as_str())))
        .unwrap_or((None, None));
    let mut rows = client.query(SQL, &[&i64::from(limit), &cancelled_only, &at, &id])?;
    if rows.is_empty() && cursor.is_some() {
        let no_at: Option<i64> = None;
        let no_id: Option<&str> = None;
        rows = client.query(SQL, &[&i64::from(limit), &cancelled_only, &no_at, &no_id])?;
    }
    Ok(rows)
}

/// A short page has reached the eligible queue's observed tail. Restart at
/// the oldest unresolved Job on the next tick; otherwise a trickle of newer
/// Jobs can keep the cursor moving forever and starve delayed native evidence.
fn next_reconciliation_cursor(pending: &[postgres::Row], limit: u32) -> Option<(i64, String)> {
    if pending.len() < limit as usize {
        return None;
    }
    pending
        .last()
        .map(|last| (last.get::<_, i64>(3), last.get::<_, String>(0)))
}

/// Commit cursor progress only if no other scan advanced this lane while SQL
/// ran. Key equality alone is insufficient: wraparound can revisit the same
/// key or None (ABA) while an older scanner is still outstanding.
fn advance_reconciliation_cursor(
    slot: &mut ReconciliationCursor,
    observed_generation: u64,
    next: Option<(i64, String)>,
) -> bool {
    if slot.generation != observed_generation {
        return false;
    }
    let Some(generation) = slot.generation.checked_add(1) else {
        return false;
    };
    slot.key = next;
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
        // later jobs from ever being reconciled. Use a bounded, wraparound
        // keyset scan, with independent cursors for the cancellation and
        // general recovery consumers. Never hold a cursor mutex across DB or
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
        let pending =
            scan_reconciliation_page(&mut db.client, limit, cancelled_only, previous.key.as_ref())
                .map_err(io)?;
        let next = next_reconciliation_cursor(&pending, limit);
        let mut cursors = self
            .reconciliation_cursors
            .lock()
            .map_err(|_| error("reconciliation cursor mutex poisoned"))?;
        let slot = if cancelled_only {
            &mut cursors.cancelled
        } else {
            &mut cursors.issued
        };
        let _ = advance_reconciliation_cursor(slot, previous.generation, next);
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
        let r=db.client.query_one("SELECT a.attempt_id,a.state,a.termination_intent,a.launch_token_digest,a.bundle_path,a.unit_name,a.created_at_ms,a.row_version,a.bundle_digest,j.execution_plan_json,j.operation_digest FROM attempts a JOIN jobs j ON j.job_id=a.job_id WHERE j.job_id=$1 ORDER BY a.attempt_number DESC LIMIT 1", &[&job]).map_err(io)?;
        let a:AttemptRecord=serde_json::from_value(json!({"attemptId":r.get::<_,String>(0),"jobId":job,"attemptNumber":1,"state":r.get::<_,String>(1),"terminationIntent":r.get::<_,String>(2),"launchTokenDigest":r.get::<_,String>(3),"bundlePath":r.get::<_,String>(4),"unitName":r.get::<_,String>(5),"createdAtMs":r.get::<_,i64>(6),"rowVersion":r.get::<_,i64>(7),"bundleDigest":r.get::<_,Option<String>>(8)})).map_err(io)?;
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
        // ReleaseEffect identity is not a normal process Task. Until the
        // operator-qualified PG release installer owns its separate dispatch
        // and receipt, NEVER send this Job to the generic native Runner.
        let is_release: bool = db
            .client
            .query_one(
                "SELECT EXISTS(SELECT 1 FROM job_runtime_release_effects WHERE job_id=$1)",
                &[&job],
            )
            .map_err(io)?
            .get(0);
        if is_release {
            // Accepted means no physical release dispatch occurred. Any other
            // Attempt state without a release-specific operator receipt is
            // inconsistent; never reconcile it through the generic Runner.
            let row = db.client.query_opt(
                "SELECT state FROM attempts WHERE job_id=$1 ORDER BY attempt_number DESC LIMIT 1",
                &[&job],
            ).map_err(io)?;
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
                .map_err(io)?
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
                build_target_backing: None,
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
            ).map_err(io)?.get::<_,Option<i64>>(0)
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
        let (a, p, operation) = self.attempt(db, &request.job_id)?;
        let terminal = snapshot.resolution.is_some();
        let rows=db.client.query("SELECT artifact_id,kind,digest,byte_length,truncated,relative_path FROM artifacts WHERE job_id=$1 ORDER BY artifact_id", &[&request.job_id]).map_err(io)?;
        let artifacts=rows.iter().map(|r|json!({"artifactId":r.get::<_,String>(0),"attemptId":a.attempt_id,"kind":r.get::<_,String>(1),"digest":r.get::<_,String>(2),"retainedBytes":r.get::<_,i64>(3),"truncated":r.get::<_,bool>(4)})).collect::<Vec<_>>();
        let exit: Option<i32> = db
            .client
            .query_one(
                "SELECT exit_code FROM attempts WHERE attempt_id=$1",
                &[&a.attempt_id],
            )
            .map_err(io)?
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
    fn stale_scan_cannot_regress_cursor_after_concurrent_advance_and_aba() {
        let x = (10, "job-010".to_string());
        let y = (110, "job-110".to_string());
        let z = (210, "job-210".to_string());
        let mut cursor = ReconciliationCursor {
            key: Some(x.clone()),
            generation: 0,
        };
        let stale_a = cursor.clone();
        assert!(advance_reconciliation_cursor(
            &mut cursor,
            0,
            Some(y.clone())
        ));
        assert!(advance_reconciliation_cursor(
            &mut cursor,
            1,
            Some(z.clone())
        ));
        assert!(!advance_reconciliation_cursor(
            &mut cursor,
            stale_a.generation,
            Some(y)
        ));
        assert_eq!(cursor.key, Some(z.clone()));

        // Valid wrap to x cannot authorize stale work that also saw x.
        assert!(advance_reconciliation_cursor(
            &mut cursor,
            2,
            Some(x.clone())
        ));
        assert!(!advance_reconciliation_cursor(
            &mut cursor,
            stale_a.generation,
            Some(z)
        ));
        assert_eq!(cursor.key, Some(x));

        // A short-page reset may also revisit exactly None.
        assert!(advance_reconciliation_cursor(&mut cursor, 3, None));
        let old_reset = cursor.clone();
        assert!(advance_reconciliation_cursor(
            &mut cursor,
            4,
            Some((1, "a".into()))
        ));
        assert!(advance_reconciliation_cursor(&mut cursor, 5, None));
        assert!(!advance_reconciliation_cursor(
            &mut cursor,
            old_reset.generation,
            Some((2, "b".into()))
        ));
        assert!(cursor.key.is_none());
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
             CREATE TEMP TABLE attempts (attempt_id text, state text); \
             INSERT INTO jobs \
                SELECT 'job-' || lpad(n::text,3,'0'), 'owner', 'run', NULL, \
                       'attempt-' || n, n::bigint \
                FROM generate_series(1,101) n; \
             INSERT INTO attempts \
                SELECT 'attempt-' || n, 'running' \
                FROM generate_series(1,101) n;",
        )
        .unwrap();
        let first = scan_reconciliation_page(&mut db, 100, false, None).unwrap();
        assert_eq!(first.len(), 100);
        assert_eq!(first.last().unwrap().get::<_, String>(0), "job-100");
        let cursor = (
            first.last().unwrap().get::<_, i64>(3),
            first.last().unwrap().get::<_, String>(0),
        );
        let second = scan_reconciliation_page(&mut db, 100, false, Some(&cursor)).unwrap();
        assert_eq!(second.len(), 1);
        assert_eq!(second[0].get::<_, String>(0), "job-101");
        let cursor = (second[0].get::<_, i64>(3), second[0].get::<_, String>(0));
        let wrapped = scan_reconciliation_page(&mut db, 100, false, Some(&cursor)).unwrap();
        assert_eq!(wrapped.len(), 100);
        assert_eq!(wrapped[0].get::<_, String>(0), "job-001");

        // A single new Job can arrive after every scan. The old last-row
        // cursor would follow only those new Jobs forever, never revisiting
        // an older unresolved Job after its native terminal evidence arrives.
        db.batch_execute(
            "INSERT INTO jobs VALUES ('job-102','owner','run',NULL,'attempt-102',102);
             INSERT INTO attempts VALUES ('attempt-102','running');",
        )
        .unwrap();
        let after_partial = next_reconciliation_cursor(&second, 100);
        let revisited =
            scan_reconciliation_page(&mut db, 100, false, after_partial.as_ref()).unwrap();
        assert_eq!(
            revisited[0].get::<_, String>(0),
            "job-001",
            "a partial page must let older unresolved Jobs be revisited"
        );
        db.execute(
            "UPDATE jobs SET desired_state='cancelled' WHERE job_id IN ('job-004','job-101')",
            &[],
        )
        .unwrap();
        let cancelled = scan_reconciliation_page(&mut db, 100, true, None).unwrap();
        assert_eq!(cancelled.len(), 2);
        assert_eq!(cancelled[0].get::<_, String>(0), "job-004");
        assert_eq!(cancelled[1].get::<_, String>(0), "job-101");
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
