// Job observation and bounded evidence projection. Projection does not create execution authority.
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
}
