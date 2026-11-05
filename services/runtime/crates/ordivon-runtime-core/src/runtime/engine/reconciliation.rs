impl Runtime {
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
            && self.windows.is_some()
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
                    let dispatch_issued_at_ms = self
                        .registry
                        .dispatch_issued_at_ms(&current.attempt_id)?;
                    let age_ms = now_ms()?.saturating_sub(dispatch_issued_at_ms);
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
            && self.windows.is_some()
        {
            return self.reconcile_native_starting_without_target_evidence(attempt);
        }
        let properties = systemctl_show(&attempt.unit_name)?;
        let active = unit_is_active(&properties);
        let pending_manager_job = unit_has_pending_job(&properties);
        let dispatch_issued_at_ms = self
            .registry
            .dispatch_issued_at_ms(&attempt.attempt_id)?;
        let age_ms = now_ms()?.saturating_sub(dispatch_issued_at_ms);
        // `systemd-run --no-block` returns after the start request is verified and
        // enqueued, not after startup completes. A manager Job therefore proves that
        // the dispatch outcome is still pending even if the unit is currently inactive
        // or has not yet published Runner identity evidence. Never collapse that
        // systemd-owned pending state into Lost.
        if pending_manager_job
            || (active && age_ms < self.startup_grace_ms)
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
        let dispatch_issued_at_ms = self
            .registry
            .dispatch_issued_at_ms(&attempt.attempt_id)?;
        let age_ms = now_ms()?.saturating_sub(dispatch_issued_at_ms);
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
        let linux_observation = LocalLinuxProvider::new(
            self.node_identity.platform,
            &self.executor,
        )
        .observe_bound_attempt(attempt)?;
        let expected = linux_observation.expected;
        let observation = linux_observation.observed;
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
                let reason_code = linux_supervisor_terminal_reason(
                    observation.unit_state,
                    intent,
                    state,
                    observation.result.as_deref(),
                );
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


}


// This is the same consumer's durable reason-code contract, not a second
// lifecycle. Keep the terminal outcome and its control evidence consistent.
fn linux_supervisor_terminal_reason(
    unit_state: SupervisorUnitState,
    intent: TerminationIntent,
    state: AttemptState,
    result: Option<&str>,
) -> &'static str {
    match (unit_state, intent) {
        (SupervisorUnitState::NotFound, TerminationIntent::StopRequested) => {
            "STOP_REQUESTED_PROCESS_TREE_GONE"
        }
        (SupervisorUnitState::NotFound, TerminationIntent::DeadlineExceeded) => {
            "DEADLINE_EXCEEDED"
        }
        (SupervisorUnitState::Terminal, TerminationIntent::Natural)
            if result == Some("timeout") && state == AttemptState::TimedOut =>
        {
            // Consumer-visible control evidence must agree with systemd's
            // RuntimeMaxSec deadline; an unrelated failure stays a fallback.
            "DEADLINE_EXCEEDED"
        }
        _ => "SUPERVISOR_TERMINAL_FALLBACK",
    }
}

#[cfg(test)]
mod linux_supervisor_terminal_reason_contract_tests {
    use super::*;

    #[test]
    fn native_timeout_reason_matches_timed_out_state_and_stop_precedence() {
        for (unit, intent, state, result, expected) in [
            (
                SupervisorUnitState::Terminal,
                TerminationIntent::Natural,
                AttemptState::TimedOut,
                Some("timeout"),
                "DEADLINE_EXCEEDED",
            ),
            (
                SupervisorUnitState::Terminal,
                TerminationIntent::Natural,
                AttemptState::Failed,
                Some("exit-code"),
                "SUPERVISOR_TERMINAL_FALLBACK",
            ),
            (
                SupervisorUnitState::NotFound,
                TerminationIntent::StopRequested,
                AttemptState::Cancelled,
                None,
                "STOP_REQUESTED_PROCESS_TREE_GONE",
            ),
            (
                SupervisorUnitState::NotFound,
                TerminationIntent::DeadlineExceeded,
                AttemptState::TimedOut,
                None,
                "DEADLINE_EXCEEDED",
            ),
            (
                SupervisorUnitState::Terminal,
                TerminationIntent::StopRequested,
                AttemptState::Cancelled,
                Some("timeout"),
                "SUPERVISOR_TERMINAL_FALLBACK",
            ),
        ] {
            assert_eq!(
                linux_supervisor_terminal_reason(unit, intent, state, result),
                expected,
                "unit={unit:?}, intent={intent:?}, state={state:?}"
            );
        }
    }
}
