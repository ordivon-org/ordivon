// Durable control terminal commitment and terminal evidence owner.
impl Runtime {
    pub(crate) fn commit_control_terminal(
        &self,
        attempt: &AttemptRecord,
        state: AttemptState,
        reason_code: &str,
        detail: Option<String>,
    ) -> RuntimeResult<JobObservation> {
        self.commit_observed_control_terminal(attempt, state, reason_code, detail, None)
    }

    fn commit_observed_control_terminal(
        &self,
        attempt: &AttemptRecord,
        state: AttemptState,
        reason_code: &str,
        detail: Option<String>,
        observed_supervisor: Option<&SupervisorObservation>,
    ) -> RuntimeResult<JobObservation> {
        let control_terminal_guard = self.lock_control_terminal()?;
        let current = self.registry.get_attempt(&attempt.attempt_id)?;
        if current.state.is_terminal() {
            return self.observation_from_registry(&current.job_id, 0, 0);
        }
        // A Runner-owned result is a stronger terminal claimant than a
        // supervisor-side guess that dispatch was lost. Recheck *under* the
        // control-terminal serialization boundary: the earlier reconciliation
        // observation may precede the result file. Do not recurse when
        // quarantining an invalid result as Orphaned.
        if state != AttemptState::Orphaned
            && Path::new(&current.bundle_path).join(RESULT_FILE).is_file()
        {
            drop(control_terminal_guard);
            self.reconcile_runner_result(&current)?;
            return self.observation_from_registry(&current.job_id, 0, 0);
        }
        let observed_at_ms = now_ms()?;
        let evidence = ControlTerminalEvidence {
            schema_version: RUNTIME_SCHEMA_VERSION,
            job_id: current.job_id.clone(),
            attempt_id: current.attempt_id.clone(),
            status: state.as_db().to_string(),
            reason_code: reason_code.to_string(),
            detail: detail.clone(),
            observed_at_ms,
        };
        let evidence_path = Path::new(&current.bundle_path).join(CONTROL_RESULT_FILE);
        if let Some(parent) = evidence_path.parent() {
            fs::create_dir_all(parent)
                .map_err(|error| io_error("create control evidence directory", error))?;
        }
        write_json_atomic(&evidence_path, &evidence).map_err(map_universal_error)?;
        let result_digest = sha256_file(&evidence_path).map_err(map_universal_error)?;
        let mut artifacts = vec![ArtifactRegistration {
            artifact_id: format!("{}.control-result", current.attempt_id),
            kind: "control_result".to_string(),
            relative_path: CONTROL_RESULT_FILE.to_string(),
            digest: result_digest.clone(),
            media_type: "application/json".to_string(),
            byte_length: fs::metadata(&evidence_path)
                .map_err(|error| io_error("inspect control evidence", error))?
                .len(),
            truncated: false,
        }];
        if state != AttemptState::Orphaned {
            for (file_name, kind) in [(STDOUT_FILE, "stdout"), (STDERR_FILE, "stderr")] {
                let path = Path::new(&current.bundle_path).join(file_name);
                if path.is_file() {
                    artifacts.push(ArtifactRegistration {
                        artifact_id: format!("{}.{}", current.attempt_id, kind),
                        kind: kind.to_string(),
                        relative_path: file_name.to_string(),
                        digest: sha256_file(&path).map_err(map_universal_error)?,
                        media_type: "text/plain; charset=utf-8".to_string(),
                        byte_length: fs::metadata(&path)
                            .map_err(|error| io_error("inspect control output", error))?
                            .len(),
                        truncated: false,
                    });
                }
            }
        }
        let mut terminal = TerminalCommit {
            attempt_id: current.attempt_id.clone(),
            expected_row_version: current.row_version,
            state,
            result_digest,
            exit_code: None,
            infrastructure_error_digest: detail
                .as_deref()
                .map(|value| sha256_bytes(value.as_bytes())),
            finished_at_ms: observed_at_ms,
            artifacts,
            reason_code: reason_code.to_string(),
        };
        append_terminal_evidence_for_commit_with_observation(
            &self.registry,
            &current,
            &mut terminal,
            observed_supervisor,
        )?;
        let _ = self.registry.commit_terminal(&terminal)?;
        drop(control_terminal_guard);
        if state != AttemptState::Orphaned {
            self.release_attempt_supervisor(&current)?;
            self.cleanup_payload_view(&current.attempt_id)?;
        }
        self.observation_from_registry(&current.job_id, 4096, 4096)
    }

    pub(crate) fn append_terminal_evidence(
        &self,
        attempt: &AttemptRecord,
        terminal: &mut TerminalCommit,
    ) -> RuntimeResult<()> {
        append_terminal_evidence_for_commit(&self.registry, attempt, terminal)
    }
}
