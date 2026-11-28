//! Physical systemd/Runner reconciliation and irreversible native terminal evidence.
use super::{
    decode, error, fs, io, native_running_witness, now, observed_namespace_pid, pg, pg_read_error,
    universal, AttemptState, AttemptTerminationIntent, NativePidReadback, PgAdmissionError,
    PgAdmissionStore, PgArtifactRegistration, PgRuntime, PgTerminalNoArtifacts,
    RunnerStartEvidence, RuntimeError, RuntimeErrorCode, RuntimeResult, RECONCILIATION_STAGE_SQL,
    RELEASE_CURRENT_ATTEMPT_STATE_SQL,
};
use std::path::{Path, PathBuf};

impl PgRuntime {
    pub(in crate::runtime::pg_runtime) fn reconcile(
        &self,
        db: &mut PgAdmissionStore,
        job: &str,
    ) -> RuntimeResult<()> {
        self.reconcile_inner(db, job, false)
    }
    pub(in crate::runtime::pg_runtime) fn reconcile_inner(
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
        if !self.dispatch_accepted_attempt(
            db,
            &mut a,
            &plan,
            &provider,
            &operation,
            allow_dispatch,
        )? {
            return Ok(());
        }
        #[cfg(windows)]
        {
            if a.state == AttemptState::Accepted {
                return Ok(());
            }
            return self.reconcile_native_windows_attempt(db, &a, &plan);
        }
        #[cfg(not(windows))]
        {
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
                        let start: RunnerStartEvidence =
                            serde_json::from_slice(&bytes).map_err(io)?;
                        let native = super::platform::systemctl_show(&a.unit_name)?;
                        // systemd MainPID is in the host namespace. PrivatePIDs
                        // may make RunnerStart.namespace_pid equal 1: never read
                        // host /proc/1 as though it were this Runner.
                        let host_pid = native
                            .get("MainPID")
                            .and_then(|pid| pid.parse::<u32>().ok())
                            .filter(|pid| *pid != 0);
                        let host_process_start =
                            host_pid.and_then(super::platform::process_identity);
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
                                Err(
                                    PgAdmissionError::Blocked | PgAdmissionError::UnknownCommit,
                                ) => {
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
                if let Some(artifact) =
                    super::evidence::validate_workspace_source_observation_artifact(
                        &a,
                        plan.workspace_source_digest.as_deref(),
                        true,
                        super::evidence::SourceObservationRequirement::for_terminal(
                            terminal.state,
                            &terminal.reason_code,
                        ),
                    )?
                {
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
                self.reconcile_absent_runner_result(db, job, &a, &provider, &path)?;
            }
            Ok(())
        }
    }
}
