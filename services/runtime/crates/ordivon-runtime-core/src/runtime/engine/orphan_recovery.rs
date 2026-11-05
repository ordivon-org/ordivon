// Recovery of orphaned attempts with source and process identity evidence.
impl Runtime {
    fn reconcile_orphaned_attempt(&self, attempt: &AttemptRecord) -> RuntimeResult<bool> {
        let current = self.registry.get_attempt(&attempt.attempt_id)?;
        if current.state != AttemptState::Orphaned {
            return Ok(false);
        }
        if let Some(binding) = self.registry.runtime_release_effect_for_job(&current.job_id)? {
            let snapshot = self.registry.job_snapshot(&current.job_id)?;
            let receipt = ReleaseStateContract::inspect_receipt(
                &binding,
                snapshot.job.resolution,
                snapshot.attempt.as_ref().map(|attempt| attempt.state),
            )?;
            if receipt.disposition == RuntimeReleaseDisposition::Deployed && receipt.terminal {
                let result_digest = receipt.digest.ok_or_else(|| {
                    RuntimeError::new(
                        RuntimeErrorCode::RegistryCorrupt,
                        "terminal deployed Runtime Release receipt has no digest",
                        Some("runtimeReleaseEffect.receipt"),
                        false,
                    )
                })?;
                let observed_at_ms = current
                    .finished_at_ms
                    .unwrap_or(current.created_at_ms)
                    .saturating_add(1);
                let mut terminal = TerminalCommit {
                    attempt_id: current.attempt_id.clone(),
                    expected_row_version: current.row_version,
                    state: AttemptState::Succeeded,
                    result_digest,
                    exit_code: Some(0),
                    infrastructure_error_digest: None,
                    finished_at_ms: observed_at_ms,
                    artifacts: Vec::new(),
                    reason_code: "RUNTIME_RELEASE_RECEIPT_DEPLOYED".to_string(),
                };
                self.append_terminal_evidence(&current, &mut terminal)?;
                self.registry.recover_orphaned_terminal(&terminal)?;
                self.cleanup_payload_view(&current.attempt_id)?;
                return Ok(true);
            }
        }
        if Path::new(&current.bundle_path).join(RESULT_FILE).is_file() {
            return self.recover_orphaned_runner_result(&current);
        }
        if self.orphan_process_tree_alive(&current)? {
            return Ok(false);
        }
        if Path::new(&current.bundle_path).join(RESULT_FILE).is_file() {
            return self.recover_orphaned_runner_result(&current);
        }
        let job = self.registry.get_job(&current.job_id)?;
        let (state, reason) = match current.termination_intent {
            AttemptTerminationIntent::StopRequested => (
                AttemptState::Cancelled,
                "ORPHAN_CANCELLED_PROCESS_TREE_GONE",
            ),
            AttemptTerminationIntent::DeadlineExceeded => {
                (AttemptState::TimedOut, "ORPHAN_DEADLINE_PROCESS_TREE_GONE")
            }
            AttemptTerminationIntent::Natural
                if job.desired_state == JobDesiredState::Cancelled =>
            {
                (
                    AttemptState::Cancelled,
                    "ORPHAN_CANCELLED_PROCESS_TREE_GONE",
                )
            }
            AttemptTerminationIntent::Natural => (AttemptState::Lost, "ORPHANED_PROCESS_TREE_GONE"),
        };
        self.resolve_absent_orphan(&current, state, reason)?;
        Ok(true)
    }

    fn resolve_absent_orphan(
        &self,
        attempt: &AttemptRecord,
        state: AttemptState,
        reason_code: &str,
    ) -> RuntimeResult<()> {
        // Interactive reconciliation paths may inspect the same orphan concurrently. Derive
        // one stable logical observation time from the orphan terminal record so every writer
        // produces identical remediation evidence bytes and Digest.
        let observed_at_ms = attempt
            .finished_at_ms
            .unwrap_or(attempt.created_at_ms)
            .saturating_add(1);
        let evidence = ControlTerminalEvidence {
            schema_version: RUNTIME_SCHEMA_VERSION,
            job_id: attempt.job_id.clone(),
            attempt_id: attempt.attempt_id.clone(),
            status: state.as_db().to_string(),
            reason_code: reason_code.to_string(),
            detail: Some(
                "the persisted unit, process identity, and cgroup no longer own a live process tree"
                    .to_string(),
            ),
            observed_at_ms,
        };
        let evidence_path = Path::new(&attempt.bundle_path).join(ORPHAN_REMEDIATION_FILE);
        write_json_atomic(&evidence_path, &evidence).map_err(map_universal_error)?;
        let result_digest = sha256_file(&evidence_path).map_err(map_universal_error)?;
        let existing_artifacts = self
            .registry
            .job_snapshot(&attempt.job_id)?
            .projection
            .artifacts;
        let mut artifacts = vec![ArtifactRegistration {
            artifact_id: format!("{}.orphan-remediation", attempt.attempt_id),
            kind: "control_result".to_string(),
            relative_path: ORPHAN_REMEDIATION_FILE.to_string(),
            digest: result_digest.clone(),
            media_type: "application/json".to_string(),
            byte_length: fs::metadata(&evidence_path)
                .map_err(|error| io_error("inspect orphan remediation evidence", error))?
                .len(),
            truncated: false,
        }];
        for (file_name, kind) in [(STDOUT_FILE, "stdout"), (STDERR_FILE, "stderr")] {
            let artifact_id = format!("{}.{}", attempt.attempt_id, kind);
            let path = Path::new(&attempt.bundle_path).join(file_name);
            if path.is_file()
                && !existing_artifacts
                    .iter()
                    .any(|artifact| artifact.artifact_id == artifact_id)
            {
                artifacts.push(ArtifactRegistration {
                    artifact_id,
                    kind: kind.to_string(),
                    relative_path: file_name.to_string(),
                    digest: sha256_file(&path).map_err(map_universal_error)?,
                    media_type: "text/plain; charset=utf-8".to_string(),
                    byte_length: fs::metadata(&path)
                        .map_err(|error| io_error("inspect orphan output", error))?
                        .len(),
                    truncated: false,
                });
            }
        }
        let mut terminal = TerminalCommit {
            attempt_id: attempt.attempt_id.clone(),
            expected_row_version: attempt.row_version,
            state,
            result_digest,
            exit_code: None,
            infrastructure_error_digest: Some(sha256_bytes(reason_code.as_bytes())),
            finished_at_ms: observed_at_ms,
            artifacts,
            reason_code: reason_code.to_string(),
        };
        self.append_terminal_evidence(attempt, &mut terminal)?;
        self.registry.recover_orphaned_terminal(&terminal)?;
        self.cleanup_payload_view(&attempt.attempt_id)
    }

    fn recover_orphaned_runner_result(&self, attempt: &AttemptRecord) -> RuntimeResult<bool> {
        let current = self.registry.get_attempt(&attempt.attempt_id)?;
        if current.state != AttemptState::Orphaned
            || !Path::new(&current.bundle_path).join(RESULT_FILE).is_file()
            || self.orphan_process_tree_alive(&current)?
        {
            return Ok(false);
        }
        // Preserve the Runner-derived execution outcome reason. Recovery lineage is already
        // represented by the new terminal evidence superseding the prior orphan evidence; using
        // a recovery-process label here would erase PROCESS_EXIT_ZERO, HOST_DEPENDENCY_RUNTIME_DRIFT,
        // DEADLINE_EXCEEDED, and other outcome semantics that downstream evidence depends on.
        let mut terminal = self.prepare_runner_terminal(&current)?;
        self.append_terminal_evidence(&current, &mut terminal)?;
        self.registry.recover_orphaned_terminal(&terminal)?;
        self.release_attempt_supervisor(&current)?;
        self.cleanup_payload_view(&current.attempt_id)?;
        Ok(true)
    }

    fn orphan_process_tree_alive(&self, attempt: &AttemptRecord) -> RuntimeResult<bool> {
        if let Some(owner) = self
            .registry
            .attempt_supervisor_owner(&attempt.attempt_id)?
        {
            let windows = self.windows.as_ref().ok_or_else(|| {
                RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "Attempt Supervisor Owner exists without a configured Windows provider",
                    Some("attemptSupervisorOwner"),
                    false,
                )
            })?;
            let AttemptSupervisorOwner::WindowsLauncherV1 {
                launcher_process_id,
                launcher_process_creation_time_file_time,
                ..
            } = owner;
            let plan = self.registry.execution_plan(&attempt.job_id)?;
            let expected_broker_digest = plan
                .windows_execution_context
                .as_ref()
                .and_then(|context| context.privileged_broker_digest.as_deref());
            let observed = observe_windows_launcher_owner(
                windows,
                plan.windows_authority,
                expected_broker_digest,
                launcher_process_id,
            )?;
            return Ok(observed.process_alive
                && observed.process_creation_time_file_time
                    == Some(launcher_process_creation_time_file_time));
        }
        if attempt_process_tree_alive(attempt)? {
            return Ok(true);
        }

        // An Orphaned Linux Attempt may have been classified before Runner identity
        // became bindable. In that state there is intentionally no persisted PID/cgroup
        // identity for `attempt_process_tree_alive` to verify. The exact transient unit
        // still belongs to this unique Attempt, so an active unit or pending manager Job
        // is stronger evidence than the absence of a bound process identity. Keep the
        // orphan reservation held until systemd also says the dispatch is no longer live;
        // only then may result recovery or Lost convergence proceed. Never use this
        // fallback after a Runner identity was bound, where exact identity mismatch must
        // remain fail-closed.
        let never_bound = attempt.boot_id.is_none()
            && attempt.invocation_id.is_none()
            && attempt.control_group.is_none()
            && attempt.main_pid.is_none()
            && attempt.process_start_identity.is_none()
            && attempt.runner_start_digest.is_none();
        if never_bound {
            let properties = systemctl_show(&attempt.unit_name)?;
            return Ok(unit_is_active(&properties) || unit_has_pending_job(&properties));
        }
        Ok(false)
    }
}
