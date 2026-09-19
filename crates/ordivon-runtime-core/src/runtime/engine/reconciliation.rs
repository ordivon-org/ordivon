impl Runtime {
    pub fn observe_job(&self, request: &JobObserveRequest) -> RuntimeResult<JobObservation> {
        validate_observe_request(request)?;
        let deadline = Instant::now() + Duration::from_millis(request.wait_ms);
        let mut poll_index = 0;
        let mut initial_signature = None;
        loop {
            self.reconcile_job(&request.job_id)?;
            let snapshot = self.registry.job_snapshot(&request.job_id)?;
            let signature =
                job_activity_signature(snapshot.attempt.as_ref(), &snapshot.projection)?;
            let changed = initial_signature
                .as_ref()
                .is_some_and(|initial| initial != &signature);
            if initial_signature.is_none() {
                initial_signature = Some(signature);
            }
            if snapshot.projection.result_available
                || request.wait_ms == 0
                || Instant::now() >= deadline
                || (request.wait_until == JobObserveWaitUntil::ChangeOrTerminal && changed)
            {
                return self.observation_from_snapshot(snapshot, request);
            }
            sleep_until_poll(deadline, &mut poll_index);
        }
    }

    fn observation_from_registry(
        &self,
        job_id: &str,
        stdout_tail_bytes: u64,
        stderr_tail_bytes: u64,
    ) -> RuntimeResult<JobObservation> {
        let snapshot = self.registry.job_snapshot(job_id)?;
        let effective_limits = effective_limits_from_plan_json(&snapshot.job.execution_plan_json)?;
        self.observation_from_parts(
            snapshot.projection,
            snapshot.attempt,
            effective_limits,
            ObservationOutputRequest {
                stdout_tail_bytes,
                stderr_tail_bytes,
                stdout_offset: None,
                stderr_offset: None,
            },
        )
    }

    fn observation_from_snapshot(
        &self,
        snapshot: JobSnapshot,
        request: &JobObserveRequest,
    ) -> RuntimeResult<JobObservation> {
        let effective_limits = effective_limits_from_plan_json(&snapshot.job.execution_plan_json)?;
        self.observation_from_parts(
            snapshot.projection,
            snapshot.attempt,
            effective_limits,
            ObservationOutputRequest {
                stdout_tail_bytes: request.stdout_tail_bytes,
                stderr_tail_bytes: request.stderr_tail_bytes,
                stdout_offset: request.stdout_offset,
                stderr_offset: request.stderr_offset,
            },
        )
    }

    fn observation_from_parts(
        &self,
        projection: super::JobProjection,
        attempt: Option<AttemptRecord>,
        effective_limits: super::EffectiveExecutionLimits,
        output_request: ObservationOutputRequest,
    ) -> RuntimeResult<JobObservation> {
        let job_id = projection.job_id.clone();
        let terminal = projection.result_available;
        let now = now_ms()?;
        let progress = attempt
            .as_ref()
            .map(load_runner_progress_if_present)
            .transpose()?
            .flatten();
        // Orphaned is the quarantine state for invalid or identity-conflicting Runner
        // evidence. The corrupt file remains available for diagnosis, but observation must
        // project the committed control result instead of reparsing quarantined evidence.
        let result = if projection.status == "orphaned" {
            None
        } else {
            attempt
                .as_ref()
                .map(load_runner_result_if_present)
                .transpose()?
                .flatten()
        };
        let control_error_summary = if result.is_none() {
            attempt
                .as_ref()
                .map(load_control_error_summary_if_present)
                .transpose()?
                .flatten()
        } else {
            None
        };
        let (
            stdout_view,
            stderr_view,
            stdout_truncated,
            stderr_truncated,
            artifacts,
            error_summary,
            last_output_at_ms,
        ) = if let Some(attempt) = &attempt {
            let stdout_view = read_output_text(
                &Path::new(&attempt.bundle_path).join(STDOUT_FILE),
                output_request.stdout_offset,
                output_request.stdout_tail_bytes,
                terminal,
                "stdoutOffset",
                "stdoutTailBytes",
            )?;
            let stderr_view = read_output_text(
                &Path::new(&attempt.bundle_path).join(STDERR_FILE),
                output_request.stderr_offset,
                output_request.stderr_tail_bytes,
                terminal,
                "stderrOffset",
                "stderrTailBytes",
            )?;
            let stdout_truncated = result
                .as_ref()
                .is_some_and(|result| result.stdout.truncated);
            let stderr_truncated = result
                .as_ref()
                .is_some_and(|result| result.stderr.truncated);
            let artifacts = self
                .registry
                .list_artifacts(&job_id)?
                .into_iter()
                .map(|artifact| artifact_descriptor(artifact, result.as_ref()))
                .collect();
            let error_summary = result
                .as_ref()
                .and_then(|result| result.infrastructure_error.clone())
                .or(control_error_summary);
            let last_output_at_ms = latest_output_modified_ms(attempt)?;
            (
                stdout_view,
                stderr_view,
                stdout_truncated,
                stderr_truncated,
                artifacts,
                error_summary,
                last_output_at_ms,
            )
        } else {
            (
                OutputView::empty(output_request.stdout_offset, terminal),
                OutputView::empty(output_request.stderr_offset, terminal),
                false,
                false,
                Vec::new(),
                None,
                None,
            )
        };
        Ok(JobObservation {
            job_id,
            operation_digest: projection.operation_digest,
            status: projection.status,
            desired_state: projection.desired_state,
            attempt_id: attempt.as_ref().map(|attempt| attempt.attempt_id.clone()),
            attempt_state: projection.attempt_state,
            termination_intent: projection.termination_intent,
            exit_code: projection.exit_code,
            execution_terminal: projection.execution_terminal,
            execution_disposition: projection.execution_disposition,
            execution_reason_code: projection.execution_reason_code,
            delivery_disposition: projection.delivery_disposition,
            effective_limits,
            recovery_required: projection.recovery_required,
            semantic_completion_evaluated: projection.semantic_completion_evaluated,
            result_available: projection.result_available,
            stdout_tail: stdout_view.content,
            stderr_tail: stderr_view.content,
            stdout_offset: stdout_view.offset,
            stdout_next_offset: stdout_view.next_offset,
            stdout_available_bytes: stdout_view.available_bytes,
            stdout_eof: stdout_view.eof,
            stderr_offset: stderr_view.offset,
            stderr_next_offset: stderr_view.next_offset,
            stderr_available_bytes: stderr_view.available_bytes,
            stderr_eof: stderr_view.eof,
            stdout_truncated,
            stderr_truncated,
            artifacts_available: projection.artifacts_available,
            artifacts,
            poll_after_ms: projection.poll_after_ms,
            elapsed_ms: attempt.as_ref().map(|attempt| {
                let started_at_ms = attempt.started_at_ms.unwrap_or(attempt.created_at_ms);
                attempt
                    .finished_at_ms
                    .unwrap_or(now)
                    .saturating_sub(started_at_ms)
            }),
            last_output_at_ms,
            progress_revision: progress.as_ref().map(|progress| progress.revision),
            completed_steps: progress.as_ref().map(|progress| progress.completed_steps),
            total_steps: progress.as_ref().map(|progress| progress.total_steps),
            current_step_id: progress
                .as_ref()
                .and_then(|progress| progress.current_step_id.clone()),
            current_step_index: progress
                .as_ref()
                .and_then(|progress| progress.current_step_index),
            current_step_elapsed_ms: progress.as_ref().and_then(|progress| {
                progress
                    .current_step_started_unix_ms
                    .and_then(|started| u64::try_from(started).ok())
                    .map(|started| now.saturating_sub(started))
            }),
            failed_step_id: result
                .as_ref()
                .and_then(|result| result.failed_step_id.clone())
                .or_else(|| {
                    progress
                        .as_ref()
                        .and_then(|progress| progress.failed_step_id.clone())
                }),
            failed_step_index: result
                .as_ref()
                .and_then(|result| result.failed_step_index)
                .or_else(|| {
                    progress
                        .as_ref()
                        .and_then(|progress| progress.failed_step_index)
                }),
            error_summary,
        })
    }

    fn reconcile_job(&self, job_id: &str) -> RuntimeResult<()> {
        let snapshot = self.registry.job_snapshot(job_id)?;
        if snapshot.job.resolution.is_some() {
            if snapshot.job.resolution == Some(JobResolution::Orphaned) {
                if let Some(attempt) = snapshot.attempt {
                    let _ = self.reconcile_orphaned_attempt(&attempt)?;
                }
            }
            return Ok(());
        }
        let attempt = snapshot.attempt.ok_or_else(|| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "unresolved Job has no Attempt",
                Some("jobId"),
                false,
            )
        })?;
        if attempt.state == AttemptState::Accepted {
            return self.ensure_attempt_dispatched(&attempt);
        }
        self.reconcile_attempt(&attempt.attempt_id)
    }

    #[cfg(test)]
    pub(crate) fn reconcile_all(&self) -> RuntimeResult<ReconciliationReport> {
        let mut report = ReconciliationReport::default();
        self.reconcile_recoverable_orphans_into(&mut report)?;
        let attempts = self.registry.list_nonterminal_attempts()?;
        self.reconcile_candidates_into(attempts, &mut report)?;
        Ok(report)
    }

    pub(crate) fn reconcile_workspace(&self, workspace_id: &str) -> RuntimeResult<ReconciliationReport> {
        let attempts = self.registry.list_workspace_reconciliation_attempts(
            workspace_id,
            INTERACTIVE_RECONCILIATION_LIMIT,
        )?;
        let mut report = ReconciliationReport::default();
        self.reconcile_candidates_into(attempts, &mut report)?;
        Ok(report)
    }

    pub fn reconcile_maintenance_batch(&self, limit: u32) -> RuntimeResult<ReconciliationReport> {
        // Encrypted credentials are execution capabilities, not historical artifacts. Durable
        // Job resolution is sufficient authority to retire their Job-owned ciphertext without
        // inventing an age-based retention policy.
        self.reconcile_prepared_credential_sets(STALE_PREPARED_INPUT_AGE_MS)?;
        let attempts = self.registry.list_maintenance_attempts_bounded(limit)?;
        let mut report = ReconciliationReport::default();
        self.reconcile_candidates_into(attempts, &mut report)?;
        Ok(report)
    }

    pub(crate) fn reconcile_recoverable_orphans(&self) -> RuntimeResult<ReconciliationReport> {
        let mut report = ReconciliationReport::default();
        self.reconcile_recoverable_orphans_into(&mut report)?;
        Ok(report)
    }

    fn reconcile_recoverable_orphans_into(
        &self,
        report: &mut ReconciliationReport,
    ) -> RuntimeResult<()> {
        self.reconcile_prepared_input_sets(STALE_PREPARED_INPUT_AGE_MS)?;
        self.reconcile_prepared_credential_sets(STALE_PREPARED_INPUT_AGE_MS)?;
        let attempts = self.registry.list_held_orphaned_attempts()?;
        self.reconcile_candidates_into(attempts, report)
    }

    pub(super) fn reconcile_prepared_input_sets(&self, stale_age_ms: u64) -> RuntimeResult<()> {
        let root = self.executor.input_materializations_root();
        fs::create_dir_all(&root)
            .map_err(|error| io_error("create input materialization root", error))?;
        let now = SystemTime::now();
        for entry in
            fs::read_dir(&root).map_err(|error| io_error("enumerate prepared input sets", error))?
        {
            let entry = entry.map_err(|error| io_error("read prepared input set entry", error))?;
            let metadata = entry
                .metadata()
                .map_err(|error| io_error("inspect prepared input set", error))?;
            if !metadata.is_dir() {
                continue;
            }
            let name = entry.file_name();
            let Some(job_id) = name.to_str() else {
                continue;
            };
            if !job_id.starts_with("job-") {
                continue;
            }
            match self.registry.get_job(job_id) {
                Ok(job) => {
                    let plan: RuntimeExecutionPlan = serde_json::from_str(&job.execution_plan_json)
                        .map_err(|error| {
                            RuntimeError::new(
                                RuntimeErrorCode::RegistryCorrupt,
                                format!("stored execution plan is invalid: {error}"),
                                Some("executionPlan"),
                                false,
                            )
                        })?;
                    if plan.effective_inputs.is_empty() || plan.input_set_id.is_none() {
                        continue;
                    }
                    if self.ensure_job_input_ownership(job_id).is_err() {
                        // One corrupt Job must not block Runtime startup. Its Attempt owns
                        // deterministic failure/quarantine; never reopen current source authority.
                        continue;
                    }
                }
                Err(error) if error.code == RuntimeErrorCode::JobNotFound => {
                    let old_enough = metadata
                        .modified()
                        .ok()
                        .and_then(|modified| now.duration_since(modified).ok())
                        .is_some_and(|age| age.as_millis() >= u128::from(stale_age_ms));
                    if old_enough {
                        self.discard_prepared_input_set(&entry.path())?;
                    }
                }
                Err(error) => return Err(error),
            }
        }

        // Copy-in-progress state is guarded by a process-held flock. A hard crash releases
        // the lock automatically, allowing stale staging state to be collected without
        // guessing how long a valid large copy may take.
        for entry in fs::read_dir(&root)
            .map_err(|error| io_error("enumerate input staging leases", error))?
        {
            let entry = entry.map_err(|error| io_error("read input staging lease entry", error))?;
            let name = entry.file_name();
            let Some(job_id) = name
                .to_str()
                .and_then(|name| name.strip_prefix('.'))
                .and_then(|name| name.strip_suffix(".lease"))
                .filter(|job_id| job_id.starts_with("job-"))
            else {
                continue;
            };
            let metadata = fs::symlink_metadata(entry.path())
                .map_err(|error| io_error("inspect input staging lease", error))?;
            if metadata.file_type().is_symlink() || !metadata.is_file() {
                continue;
            }
            let old_enough = metadata
                .modified()
                .ok()
                .and_then(|modified| now.duration_since(modified).ok())
                .is_some_and(|age| age.as_millis() >= u128::from(stale_age_ms));
            if !old_enough {
                continue;
            }
            let lease = match OpenOptions::new().read(true).write(true).open(entry.path()) {
                Ok(lease) => lease,
                Err(_) => continue,
            };
            if lease.try_lock().is_err() {
                continue;
            }
            let prefix = format!(".{job_id}.staging-");
            for staging in fs::read_dir(&root)
                .map_err(|error| io_error("enumerate abandoned input staging directories", error))?
            {
                let staging = staging
                    .map_err(|error| io_error("read abandoned input staging entry", error))?;
                let staging_name = staging.file_name();
                if staging_name
                    .to_str()
                    .is_some_and(|name| name.starts_with(&prefix))
                    && staging
                        .file_type()
                        .map(|kind| kind.is_dir())
                        .unwrap_or(false)
                {
                    fs::remove_dir_all(staging.path()).map_err(|error| {
                        io_error("remove abandoned input staging directory", error)
                    })?;
                }
            }
            fs::remove_file(entry.path())
                .map_err(|error| io_error("remove abandoned input staging lease", error))?;
            drop(lease);
            sync_directory(&root)?;
        }
        Ok(())
    }

    pub(super) fn reconcile_prepared_credential_sets(
        &self,
        stale_age_ms: u64,
    ) -> RuntimeResult<()> {
        let root = self.executor.credential_materializations_root();
        fs::create_dir_all(&root)
            .map_err(|error| io_error("create credential materialization root", error))?;
        let now = SystemTime::now();

        for entry in fs::read_dir(&root)
            .map_err(|error| io_error("enumerate prepared credential sets", error))?
        {
            let entry =
                entry.map_err(|error| io_error("read prepared credential set entry", error))?;
            let metadata = entry
                .metadata()
                .map_err(|error| io_error("inspect prepared credential set", error))?;
            if !metadata.is_dir() {
                continue;
            }
            let name = entry.file_name();
            let Some(job_id) = name.to_str() else {
                continue;
            };
            if !job_id.starts_with("job-") {
                continue;
            }
            match self.registry.get_job(job_id) {
                Ok(job) => {
                    if job.resolution.is_some() {
                        self.discard_prepared_credential_set(&entry.path())?;
                        continue;
                    }
                    let plan: RuntimeExecutionPlan = serde_json::from_str(&job.execution_plan_json)
                        .map_err(|error| {
                            RuntimeError::new(
                                RuntimeErrorCode::RegistryCorrupt,
                                format!("stored execution plan is invalid: {error}"),
                                Some("executionPlan"),
                                false,
                            )
                        })?;
                    if plan.credential_set_id.is_none() {
                        continue;
                    }
                    if self.ensure_job_credential_ownership(job_id).is_err() {
                        // The committed unresolved Job owns its frozen encrypted credential
                        // snapshot. Never reopen the current credential authority during recovery.
                        continue;
                    }
                }
                Err(error) if error.code == RuntimeErrorCode::JobNotFound => {
                    let old_enough = metadata
                        .modified()
                        .ok()
                        .and_then(|modified| now.duration_since(modified).ok())
                        .is_some_and(|age| age.as_millis() >= u128::from(stale_age_ms));
                    if old_enough {
                        self.discard_prepared_credential_set(&entry.path())?;
                    }
                }
                Err(error) => return Err(error),
            }
        }

        let owned_root = self.executor.job_credentials_root();
        fs::create_dir_all(&owned_root)
            .map_err(|error| io_error("create Job credential ownership root", error))?;
        for entry in fs::read_dir(&owned_root)
            .map_err(|error| io_error("enumerate Job-owned encrypted credentials", error))?
        {
            let entry = entry
                .map_err(|error| io_error("read Job-owned encrypted credential entry", error))?;
            let metadata = entry
                .metadata()
                .map_err(|error| io_error("inspect Job-owned encrypted credential set", error))?;
            if !metadata.is_dir() {
                continue;
            }
            let name = entry.file_name();
            let Some(job_id) = name.to_str() else {
                continue;
            };
            if !job_id.starts_with("job-") {
                continue;
            }
            match self.registry.get_job(job_id) {
                Ok(job) if job.resolution.is_some() => {
                    fs::remove_dir_all(entry.path()).map_err(|error| {
                        io_error("retire resolved Job encrypted credentials", error)
                    })?;
                    sync_directory(&owned_root)?;
                }
                Ok(_) => {}
                Err(error) if error.code == RuntimeErrorCode::JobNotFound => {
                    let old_enough = metadata
                        .modified()
                        .ok()
                        .and_then(|modified| now.duration_since(modified).ok())
                        .is_some_and(|age| age.as_millis() >= u128::from(stale_age_ms));
                    if old_enough {
                        fs::remove_dir_all(entry.path()).map_err(|error| {
                            io_error("remove unowned Job encrypted credentials", error)
                        })?;
                        sync_directory(&owned_root)?;
                    }
                }
                Err(error) => return Err(error),
            }
        }

        for entry in fs::read_dir(&root)
            .map_err(|error| io_error("enumerate credential staging leases", error))?
        {
            let entry =
                entry.map_err(|error| io_error("read credential staging lease entry", error))?;
            let name = entry.file_name();
            let Some(job_id) = name
                .to_str()
                .and_then(|name| name.strip_prefix('.'))
                .and_then(|name| name.strip_suffix(".lease"))
                .filter(|job_id| job_id.starts_with("job-"))
            else {
                continue;
            };
            let metadata = fs::symlink_metadata(entry.path())
                .map_err(|error| io_error("inspect credential staging lease", error))?;
            if metadata.file_type().is_symlink() || !metadata.is_file() {
                continue;
            }
            let old_enough = metadata
                .modified()
                .ok()
                .and_then(|modified| now.duration_since(modified).ok())
                .is_some_and(|age| age.as_millis() >= u128::from(stale_age_ms));
            if !old_enough {
                continue;
            }
            let lease = match OpenOptions::new().read(true).write(true).open(entry.path()) {
                Ok(lease) => lease,
                Err(_) => continue,
            };
            if lease.try_lock().is_err() {
                continue;
            }
            let prefix = format!(".{job_id}.staging-");
            for staging in fs::read_dir(&root).map_err(|error| {
                io_error("enumerate abandoned credential staging directories", error)
            })? {
                let staging = staging
                    .map_err(|error| io_error("read abandoned credential staging entry", error))?;
                let staging_name = staging.file_name();
                if staging_name
                    .to_str()
                    .is_some_and(|name| name.starts_with(&prefix))
                    && staging
                        .file_type()
                        .map(|kind| kind.is_dir())
                        .unwrap_or(false)
                {
                    fs::remove_dir_all(staging.path()).map_err(|error| {
                        io_error("remove abandoned credential staging directory", error)
                    })?;
                }
            }
            fs::remove_file(entry.path())
                .map_err(|error| io_error("remove abandoned credential staging lease", error))?;
            drop(lease);
            sync_directory(&root)?;
        }
        Ok(())
    }

    fn reconcile_candidates_into(
        &self,
        attempts: Vec<AttemptRecord>,
        report: &mut ReconciliationReport,
    ) -> RuntimeResult<()> {
        for attempt in attempts {
            self.reconcile_candidate_into(&attempt, report)?;
        }
        Ok(())
    }

    fn reconcile_candidate_into(
        &self,
        attempt: &AttemptRecord,
        report: &mut ReconciliationReport,
    ) -> RuntimeResult<()> {
        report.inspected += 1;
        let before = attempt.state;
        let reconciling_orphan = attempt.state == AttemptState::Orphaned;
        let result = if reconciling_orphan {
            self.reconcile_orphaned_attempt(attempt)
        } else if attempt.state.is_terminal() {
            self.registry
                .converge_terminal_reservation(&attempt.attempt_id, now_ms()?)
        } else if attempt.state == AttemptState::Accepted {
            self.ensure_attempt_dispatched(attempt).map(|()| false)
        } else {
            self.reconcile_attempt(&attempt.attempt_id).map(|()| false)
        };
        match result {
            Ok(changed) => {
                let current = self.registry.get_attempt(&attempt.attempt_id)?;
                let orphan_converged =
                    reconciling_orphan && (changed || current.state != AttemptState::Orphaned);
                if orphan_converged {
                    report.recovered_orphans += 1;
                } else if current.state == AttemptState::Orphaned
                    && before != AttemptState::Orphaned
                {
                    report.quarantined += 1;
                } else if changed || current.state != before {
                    report.reconciled += 1;
                } else {
                    report.unchanged += 1;
                }
                if !reconciling_orphan || orphan_converged {
                    self.registry
                        .clear_reconciliation_failure(&attempt.attempt_id, now_ms()?)?;
                }
            }
            Err(error) => {
                self.record_isolated_reconciliation_failure(attempt, error, report)?;
            }
        }
        Ok(())
    }

    fn record_isolated_reconciliation_failure(
        &self,
        attempt: &AttemptRecord,
        error: RuntimeError,
        report: &mut ReconciliationReport,
    ) -> RuntimeResult<()> {
        if error.is_reconciliation_fatal() {
            return Err(error);
        }
        self.registry
            .record_reconciliation_failure(attempt, &error, now_ms()?)?;
        report.failed += 1;
        report.failures.push(ReconciliationFailure {
            attempt_id: attempt.attempt_id.clone(),
            job_id: attempt.job_id.clone(),
            code: error.code,
            message: error.message,
        });
        Ok(())
    }

    fn reconcile_orphaned_attempt(&self, attempt: &AttemptRecord) -> RuntimeResult<bool> {
        let current = self.registry.get_attempt(&attempt.attempt_id)?;
        if current.state != AttemptState::Orphaned {
            return Ok(false);
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
        let mut terminal = self.prepare_runner_terminal(&current)?;
        terminal.reason_code = "LATE_IDENTITY_BOUND_RUNNER_RESULT".to_string();
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

    pub(crate) fn reconcile_attempt(&self, attempt_id: &str) -> RuntimeResult<()> {
        let attempt = self.registry.get_attempt(attempt_id)?;
        if attempt.state.is_terminal() {
            return Ok(());
        }
        let result_path = Path::new(&attempt.bundle_path).join(RESULT_FILE);
        if result_path.exists() {
            return self.reconcile_runner_result(&attempt);
        }
        let plan = self.registry.execution_plan(&attempt.job_id)?;
        let start_path = Path::new(&attempt.bundle_path).join(match plan.execution_target {
            super::ExecutionTarget::LocalLinux => RUNNER_START_FILE,
            super::ExecutionTarget::WindowsNative => WINDOWS_START_FILE,
        });
        let native_unbound_stopping = attempt.state == AttemptState::Stopping
            && plan.execution_target == super::ExecutionTarget::WindowsNative
            && self
                .windows
                .as_ref()
                .is_some_and(|windows| windows.wsl_distribution.is_none())
            && self
                .registry
                .attempt_supervisor_owner(&attempt.attempt_id)?
                .is_none();
        if (attempt.state == AttemptState::Starting || native_unbound_stopping)
            && start_path.exists()
        {
            let bound = match self.bind_attempt_start(&attempt, plan.execution_target) {
                Ok(bound) => bound,
                Err(error) if transient_main_pid_observation_loss(&error) => {
                    if Path::new(&attempt.bundle_path).join(RESULT_FILE).exists() {
                        return self.reconcile_runner_result(&attempt);
                    }
                    let current = self.registry.get_attempt(&attempt.attempt_id)?;
                    if current.row_version != attempt.row_version || current.state != attempt.state
                    {
                        if Path::new(&current.bundle_path).join(RESULT_FILE).exists() {
                            return self.reconcile_runner_result(&current);
                        }
                        return Ok(());
                    }
                    let age_ms = now_ms()?.saturating_sub(current.created_at_ms);
                    if age_ms < self.startup_grace_ms {
                        return Ok(());
                    }
                    return Err(error);
                }
                Err(error) => return Err(error),
            };
            if Path::new(&bound.bundle_path).join(RESULT_FILE).exists() {
                return self.reconcile_runner_result(&bound);
            }
            if native_unbound_stopping {
                return self.reconcile_bound_attempt(&bound);
            }
            return Ok(());
        }
        if attempt.state == AttemptState::Starting || native_unbound_stopping {
            return self.reconcile_starting_without_token(&attempt);
        }
        self.reconcile_bound_attempt(&attempt)
    }

    fn reconcile_starting_without_token(&self, attempt: &AttemptRecord) -> RuntimeResult<()> {
        let plan = self.registry.execution_plan(&attempt.job_id)?;
        if plan.execution_target == super::ExecutionTarget::WindowsNative
            && self
                .windows
                .as_ref()
                .is_some_and(|windows| windows.wsl_distribution.is_none())
        {
            return self.reconcile_native_starting_without_target_evidence(attempt);
        }
        let properties = systemctl_show(&attempt.unit_name)?;
        let active = unit_is_active(&properties);
        let pending_manager_job = unit_has_pending_job(&properties);
        let age_ms = now_ms()?.saturating_sub(attempt.created_at_ms);
        let wsl_distribution_configured = self
            .windows
            .as_ref()
            .is_some_and(|windows| windows.wsl_distribution.is_some());
        // `systemd-run --no-block` returns after the start request is verified and
        // enqueued, not after startup completes. A manager Job therefore proves that
        // the dispatch outcome is still pending even if the unit is currently inactive
        // or has not yet published Runner identity evidence. Never collapse that
        // systemd-owned pending state into Lost.
        if pending_manager_job
            || (active && age_ms < self.startup_grace_ms)
            || wsl_backed_windows_live_unit_must_wait(
                plan.execution_target,
                wsl_distribution_configured,
                active,
            )
        {
            return Ok(());
        }
        if active {
            self.commit_control_terminal(
                attempt,
                AttemptState::Orphaned,
                "LIVE_UNIT_WITHOUT_LAUNCH_TOKEN_EVIDENCE",
                Some("systemd unit is live but runner-start identity is unavailable".to_string()),
            )?;
            return Ok(());
        }
        if age_ms < self.startup_grace_ms {
            return Ok(());
        }
        self.commit_control_terminal(
            attempt,
            AttemptState::Lost,
            "DISPATCH_OUTCOME_UNKNOWN",
            Some(
                "dispatch intent exists without matching unit, runner-start, or result evidence"
                    .to_string(),
            ),
        )?;
        Ok(())
    }

    fn enforce_native_windows_outer_deadline(
        &self,
        attempt: &AttemptRecord,
        plan: &RuntimeExecutionPlan,
        deadline_started_at_ms: u64,
        launcher_process_id: u32,
        launcher_process_creation_time_file_time: u64,
        pre_target_start: bool,
    ) -> RuntimeResult<bool> {
        let observed_at_ms = now_ms()?;
        let current = match attempt.termination_intent {
            AttemptTerminationIntent::Natural
                if native_windows_outer_deadline_due(
                    deadline_started_at_ms,
                    plan.timeout_ms,
                    observed_at_ms,
                ) =>
            {
                self.registry
                    .request_deadline_termination(&attempt.attempt_id, observed_at_ms)?
            }
            AttemptTerminationIntent::DeadlineExceeded => {
                self.registry.get_attempt(&attempt.attempt_id)?
            }
            AttemptTerminationIntent::Natural | AttemptTerminationIntent::StopRequested => {
                return Ok(false);
            }
        };
        if current.state.is_terminal() {
            return Ok(true);
        }
        if current.termination_intent != AttemptTerminationIntent::DeadlineExceeded {
            return Ok(false);
        }
        if Path::new(&current.bundle_path).join(RESULT_FILE).is_file() {
            self.reconcile_runner_result(&current)?;
            return Ok(true);
        }
        let windows = self.windows.as_ref().ok_or_else(|| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "native Windows deadline enforcement has no configured provider",
                Some("executionTarget"),
                true,
            )
        })?;
        if windows.wsl_distribution.is_some() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "direct native Windows deadline enforcement cannot use a WSL provider",
                Some("executionTarget"),
                false,
            ));
        }
        let expected_broker_digest = plan
            .windows_execution_context
            .as_ref()
            .and_then(|context| context.privileged_broker_digest.as_deref());
        let disposition = terminate_windows_launcher_owner_for_deadline(
            windows,
            plan.windows_authority,
            expected_broker_digest,
            launcher_process_id,
            launcher_process_creation_time_file_time,
        )?;
        let mut current = self.registry.get_attempt(&current.attempt_id)?;
        if Path::new(&current.bundle_path).join(RESULT_FILE).is_file() {
            self.reconcile_runner_result(&current)?;
            return Ok(true);
        }
        if pre_target_start
            && Path::new(&current.bundle_path)
                .join(WINDOWS_START_FILE)
                .is_file()
        {
            current = self.bind_attempt_start(&current, super::ExecutionTarget::WindowsNative)?;
            if Path::new(&current.bundle_path).join(RESULT_FILE).is_file() {
                self.reconcile_runner_result(&current)?;
                return Ok(true);
            }
        }
        let disposition = match disposition {
            WindowsDeadlineOwnerTerminationDisposition::Terminated => "terminated",
            WindowsDeadlineOwnerTerminationDisposition::AlreadyAbsent => "already_absent",
            WindowsDeadlineOwnerTerminationDisposition::IdentityMismatch => return Ok(false),
        };
        self.commit_control_terminal(
            &current,
            AttemptState::TimedOut,
            "NATIVE_WINDOWS_OUTER_DEADLINE_CONTROL_TERMINAL",
            Some(format!(
                "outer deadline intent was durably committed before exact launcher-owner termination; disposition={disposition}; no runner result was available. TimedOut is derived from the persisted outer deadline and proven loss of the exact owner, not from owner death alone"
            )),
        )?;
        Ok(true)
    }

    fn reconcile_native_starting_without_target_evidence(
        &self,
        attempt: &AttemptRecord,
    ) -> RuntimeResult<()> {
        let plan = self.registry.execution_plan(&attempt.job_id)?;
        let launcher_start_path = Path::new(&attempt.bundle_path).join(WINDOWS_LAUNCHER_START_FILE);
        if launcher_start_path.is_file() {
            let (evidence, _) = self.validate_windows_launcher_start_evidence(attempt)?;
            let windows = self.windows.as_ref().ok_or_else(|| {
                RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "native Windows Starting Attempt has no configured provider",
                    Some("executionTarget"),
                    true,
                )
            })?;
            let expected_broker_digest = plan
                .windows_execution_context
                .as_ref()
                .and_then(|context| context.privileged_broker_digest.as_deref());
            let observation = observe_windows_launcher_owner(
                windows,
                plan.windows_authority,
                expected_broker_digest,
                evidence.launcher_process_id,
            )?;
            if Path::new(&attempt.bundle_path).join(RESULT_FILE).is_file() {
                return self.reconcile_runner_result(attempt);
            }
            if Path::new(&attempt.bundle_path)
                .join(WINDOWS_START_FILE)
                .is_file()
            {
                let running =
                    self.bind_attempt_start(attempt, super::ExecutionTarget::WindowsNative)?;
                if Path::new(&running.bundle_path).join(RESULT_FILE).is_file() {
                    return self.reconcile_runner_result(&running);
                }
                return Ok(());
            }
            if observation.process_alive
                && observation.process_creation_time_file_time
                    == Some(evidence.launcher_process_creation_time_file_time)
            {
                if self.enforce_native_windows_outer_deadline(
                    attempt,
                    &plan,
                    evidence.observed_unix_ms,
                    evidence.launcher_process_id,
                    evidence.launcher_process_creation_time_file_time,
                    true,
                )? {
                    return Ok(());
                }
                return Ok(());
            }
            // windows-start.json is currently carried inside the target-writable Attempt bundle.
            // Its absence after launcher-owner loss therefore cannot prove that ResumeThread never
            // happened: a resumed target can delete this evidence before launcher result publication.
            // Preserve the nonterminal Attempt/capacity and require fresh recovery evidence; never
            // turn this ambiguity into a no-effect/redrive-safe terminal standing.
            return Err(native_windows_pre_target_evidence_gap());
        }
        let age_ms = now_ms()?.saturating_sub(attempt.created_at_ms);
        if age_ms < self.startup_grace_ms {
            return Ok(());
        }
        Err(RuntimeError::new(
            RuntimeErrorCode::LaunchIdentityMismatch,
            "native dispatch intent has no launcher-start, target-start, or result evidence; retain the Starting Attempt and capacity until new evidence appears or an operator reconciles it",
            Some("windowsLauncherStart"),
            true,
        ))
    }

    fn reconcile_provider_owned_attempt(
        &self,
        attempt: &AttemptRecord,
        plan: &RuntimeExecutionPlan,
        owner: &AttemptSupervisorOwner,
    ) -> RuntimeResult<()> {
        if plan.execution_target != super::ExecutionTarget::WindowsNative {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "Attempt Supervisor Owner is bound to a non-Windows execution target",
                Some("attemptSupervisorOwner"),
                false,
            ));
        }
        if Path::new(&attempt.bundle_path).join(RESULT_FILE).exists() {
            return self.reconcile_runner_result(attempt);
        }
        let windows = self.windows.as_ref().ok_or_else(|| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "provider-owned Windows Attempt has no configured Windows provider",
                Some("executionTarget"),
                true,
            )
        })?;
        if windows.wsl_distribution.is_some() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "native Attempt Supervisor Owner cannot be reconciled through a WSL provider",
                Some("attemptSupervisorOwner"),
                false,
            ));
        }
        let AttemptSupervisorOwner::WindowsLauncherV1 {
            launcher_process_id,
            launcher_process_creation_time_file_time,
            ..
        } = owner;
        let deadline_started_at_ms = attempt.started_at_ms.ok_or_else(|| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "native Attempt Supervisor Owner has no durable execution start time",
                Some("attemptSupervisorOwner"),
                false,
            )
        })?;
        if self.enforce_native_windows_outer_deadline(
            attempt,
            plan,
            deadline_started_at_ms,
            *launcher_process_id,
            *launcher_process_creation_time_file_time,
            false,
        )? {
            return Ok(());
        }
        let expected_broker_digest = plan
            .windows_execution_context
            .as_ref()
            .and_then(|context| context.privileged_broker_digest.as_deref());
        let observation = observe_windows_launcher_owner(
            windows,
            plan.windows_authority,
            expected_broker_digest,
            *launcher_process_id,
        )?;
        if Path::new(&attempt.bundle_path).join(RESULT_FILE).exists() {
            return self.reconcile_runner_result(attempt);
        }
        let intent = match attempt.termination_intent {
            AttemptTerminationIntent::Natural => TerminationIntent::Natural,
            AttemptTerminationIntent::StopRequested => TerminationIntent::StopRequested,
            AttemptTerminationIntent::DeadlineExceeded => TerminationIntent::DeadlineExceeded,
        };
        match classify_windows_launcher_recovery(owner, &observation, intent)? {
            SupervisorRecoveryDisposition::Running => Ok(()),
            SupervisorRecoveryDisposition::Terminal(state) => {
                let reason_code = match intent {
                    TerminationIntent::StopRequested => "STOP_REQUESTED_PROCESS_TREE_GONE",
                    TerminationIntent::DeadlineExceeded => "DEADLINE_EXCEEDED",
                    TerminationIntent::Natural => "WINDOWS_LAUNCHER_LINEAGE_GONE",
                };
                self.commit_control_terminal(
                    attempt,
                    state,
                    reason_code,
                    (intent == TerminationIntent::Natural).then(|| {
                        "native Windows launcher owner identity is gone; JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE makes the Attempt process tree definitively non-running and no result evidence exists".to_string()
                    }),
                )?;
                Ok(())
            }
            SupervisorRecoveryDisposition::Orphaned(reason) => {
                self.commit_control_terminal(
                    attempt,
                    AttemptState::Orphaned,
                    "SUPERVISOR_IDENTITY_ORPHANED",
                    Some(reason),
                )?;
                Ok(())
            }
            SupervisorRecoveryDisposition::Lost => Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "native Windows launcher classifier returned unsupported lost disposition",
                Some("attemptSupervisorOwner"),
                false,
            )),
        }
    }

    fn reconcile_bound_attempt(&self, attempt: &AttemptRecord) -> RuntimeResult<()> {
        let plan = self.registry.execution_plan(&attempt.job_id)?;
        if let Some(owner) = self
            .registry
            .attempt_supervisor_owner(&attempt.attempt_id)?
        {
            return self.reconcile_provider_owned_attempt(attempt, &plan, &owner);
        }
        let (expected, observation) = observe_linux_process_owner(attempt)?;
        let intent = match attempt.termination_intent {
            super::AttemptTerminationIntent::Natural => TerminationIntent::Natural,
            super::AttemptTerminationIntent::StopRequested => TerminationIntent::StopRequested,
            super::AttemptTerminationIntent::DeadlineExceeded => {
                TerminationIntent::DeadlineExceeded
            }
        };
        if Path::new(&attempt.bundle_path).join(RESULT_FILE).exists() {
            return self.reconcile_runner_result(attempt);
        }
        if windows_native_launcher_lineage_is_definite_failure(
            plan.execution_target,
            attempt.termination_intent,
            observation.unit_state,
            observation.recorded_pid_alive,
        ) {
            self.commit_observed_control_terminal(
                attempt,
                AttemptState::Failed,
                "WINDOWS_LAUNCHER_LINEAGE_GONE",
                Some(
                    "windows_native launcher unit and persisted launcher process identity are absent; the launcher is the sole owner of the JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE handle, so the native process tree cannot still be running and no result evidence exists"
                        .to_string(),
                ),
                Some(&observation),
            )?;
            return Ok(());
        }
        let disposition =
            classify_supervisor_recovery(&expected, &observation, intent).map_err(|error| {
                RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    format!("supervisor recovery classification failed: {error}"),
                    Some("attemptId"),
                    false,
                )
            })?;
        match disposition {
            SupervisorRecoveryDisposition::Running => Ok(()),
            SupervisorRecoveryDisposition::Terminal(state) => {
                let reason_code = match (observation.unit_state, intent) {
                    (SupervisorUnitState::NotFound, TerminationIntent::StopRequested) => {
                        "STOP_REQUESTED_PROCESS_TREE_GONE"
                    }
                    (SupervisorUnitState::NotFound, TerminationIntent::DeadlineExceeded) => {
                        "DEADLINE_EXCEEDED"
                    }
                    _ => "SUPERVISOR_TERMINAL_FALLBACK",
                };
                self.commit_observed_control_terminal(
                    attempt,
                    state,
                    reason_code,
                    None,
                    Some(&observation),
                )?;
                Ok(())
            }
            SupervisorRecoveryDisposition::Lost => {
                self.commit_observed_control_terminal(
                    attempt,
                    AttemptState::Lost,
                    "SUPERVISOR_EVIDENCE_LOST",
                    None,
                    Some(&observation),
                )?;
                Ok(())
            }
            SupervisorRecoveryDisposition::Orphaned(reason) => {
                self.commit_observed_control_terminal(
                    attempt,
                    AttemptState::Orphaned,
                    "SUPERVISOR_IDENTITY_ORPHANED",
                    Some(reason),
                    Some(&observation),
                )?;
                let current = self.registry.get_attempt(&attempt.attempt_id)?;
                if Path::new(&current.bundle_path).join(RESULT_FILE).exists() {
                    let _ = self.recover_orphaned_runner_result(&current)?;
                }
                Ok(())
            }
        }
    }

    fn commit_control_terminal(
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
