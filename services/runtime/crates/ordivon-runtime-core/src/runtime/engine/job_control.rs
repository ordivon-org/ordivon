use sha2::Digest;

impl Runtime {
    pub fn authorize_job_principal(&self, job_id: &str, principal: &str) -> RuntimeResult<()> {
        let job = self.registry.get_job(job_id)?;
        if job.principal != principal {
            return Err(RuntimeError::new(
                RuntimeErrorCode::AuthorizationDenied,
                "authenticated principal is not authorized for this Runtime Job",
                Some("jobId"),
                false,
            ));
        }
        Ok(())
    }

    pub fn list_jobs_for_principal(
        &self,
        request: &RuntimeJobListRequest,
        principal: &str,
    ) -> RuntimeResult<RuntimeJobListResult> {
        self.registry.list_jobs_for_principal(request, principal)
    }

    pub fn cancel_job(&self, request: &JobCancelRequest) -> RuntimeResult<JobObservation> {
        if request.schema_version != RUNTIME_SCHEMA_VERSION {
            return Err(RuntimeError::invalid(
                "unsupported runtime schema version",
                "schemaVersion",
            ));
        }
        let snapshot = self.registry.job_snapshot(&request.job_id)?;
        if snapshot.job.resolution == Some(JobResolution::Orphaned) {
            if let Some(attempt) = snapshot.attempt.as_ref() {
                if Path::new(&attempt.bundle_path).join(RESULT_FILE).is_file()
                    && self.recover_orphaned_runner_result(attempt)?
                {
                    return self.observation_from_registry(&request.job_id, 4096, 4096);
                }
                let _ = self.registry.request_cancel(&request.job_id, now_ms()?)?;
                let current = self.registry.get_attempt(&attempt.attempt_id)?;
                if !self.orphan_process_tree_alive(&current)? {
                    if Path::new(&current.bundle_path).join(RESULT_FILE).is_file() {
                        let _ = self.recover_orphaned_runner_result(&current)?;
                    } else {
                        self.resolve_absent_orphan(
                            &current,
                            AttemptState::Cancelled,
                            "ORPHAN_CANCELLED_PROCESS_TREE_GONE",
                        )?;
                    }
                }
                return self.observation_from_registry(&request.job_id, 4096, 4096);
            }
        }
        let cancel_plan = self.registry.execution_plan(&request.job_id)?;
        let native_direct = cancel_plan.execution_target == super::ExecutionTarget::WindowsNative
            && self.windows.is_some();
        match self.reconcile_job(&request.job_id) {
            Ok(()) => {}
            Err(error)
                if native_direct && error.code == RuntimeErrorCode::LaunchIdentityMismatch => {}
            Err(error) if error.code == RuntimeErrorCode::LaunchIdentityMismatch => {
                let attempt = snapshot.attempt.as_ref().ok_or_else(|| {
                    RuntimeError::new(
                        RuntimeErrorCode::RegistryCorrupt,
                        "unresolved Job has no Attempt while cancelling after launch identity mismatch",
                        Some("jobId"),
                        false,
                    )
                })?;
                if !launch_identity_mismatch_cancel_target_absent(attempt)? {
                    return Err(error);
                }
            }
            Err(error) => return Err(error),
        }
        let projection = self.registry.request_cancel(&request.job_id, now_ms()?)?;
        if projection.result_available {
            return self.observation_from_registry(&request.job_id, 4096, 4096);
        }
        let attempt = self
            .registry
            .get_latest_attempt(&request.job_id)?
            .ok_or_else(|| {
                RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "cancelled Job has no Attempt",
                    Some("jobId"),
                    false,
                )
            })?;
        write_json_atomic(
            &Path::new(&attempt.bundle_path).join(CANCEL_FILE),
            &serde_json::json!({
                "schemaVersion": RUNTIME_SCHEMA_VERSION,
                "jobId": request.job_id,
                "attemptId": attempt.attempt_id,
                "requestedAtMs": now_ms()?,
            }),
        )
        .map_err(map_universal_error)?;
        if native_direct {
            return self.cancel_native_windows_attempt(&request.job_id, &attempt);
        }
        let output = stop_unit_no_block(&attempt.unit_name)?;
        let deadline = Instant::now() + Duration::from_secs(3);
        let mut poll_index = 0;
        loop {
            if Path::new(&attempt.bundle_path).join(RESULT_FILE).exists() {
                return self.commit_runner_result(&attempt);
            }
            let properties = systemctl_show(&attempt.unit_name)?;
            let recorded_alive =
                attempt
                    .main_pid
                    .and_then(process_identity)
                    .is_some_and(|identity| {
                        attempt.process_start_identity.as_deref() == Some(identity.as_str())
                    });
            if !unit_is_active(&properties) && !recorded_alive {
                return self.commit_control_terminal(
                    &attempt,
                    AttemptState::Cancelled,
                    "STOP_REQUESTED_PROCESS_TREE_GONE",
                    (!output.status.success())
                        .then(|| String::from_utf8_lossy(&output.stderr).trim().to_string()),
                );
            }
            if Instant::now() >= deadline {
                break;
            }
            sleep_until_poll(deadline, &mut poll_index);
        }
        self.reconcile_attempt(&attempt.attempt_id)?;
        self.observation_from_registry(&request.job_id, 4096, 4096)
    }

    fn cancel_native_windows_attempt(
        &self,
        job_id: &str,
        attempt: &AttemptRecord,
    ) -> RuntimeResult<JobObservation> {
        let plan = self.registry.execution_plan(job_id)?;
        let expected_broker_digest = plan
            .windows_execution_context
            .as_ref()
            .and_then(|context| context.privileged_broker_digest.as_deref());
        let deadline = Instant::now() + Duration::from_secs(3);
        let mut poll_index = 0;
        loop {
            let current = self.registry.get_attempt(&attempt.attempt_id)?;
            if Path::new(&current.bundle_path).join(RESULT_FILE).exists() {
                return self.commit_runner_result(&current);
            }
            if self
                .registry
                .attempt_supervisor_owner(&current.attempt_id)?
                .is_some()
            {
                if !self.orphan_process_tree_alive(&current)? {
                    if Path::new(&current.bundle_path).join(RESULT_FILE).exists() {
                        return self.commit_runner_result(&current);
                    }
                    return self.commit_control_terminal(
                        &current,
                        AttemptState::Cancelled,
                        "STOP_REQUESTED_PROCESS_TREE_GONE",
                        Some(
                            "native Windows launcher owner identity is gone after committed cancel intent; JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE makes the Attempt process tree definitively non-running"
                                .to_string(),
                        ),
                    );
                }
            } else {
                let target_start = Path::new(&current.bundle_path).join(WINDOWS_START_FILE);
                if target_start.is_file() {
                    let _ =
                        self.bind_attempt_start(&current, super::ExecutionTarget::WindowsNative)?;
                    continue;
                }
                let launcher_start =
                    Path::new(&current.bundle_path).join(WINDOWS_LAUNCHER_START_FILE);
                if launcher_start.is_file() {
                    let (evidence, _) = self.validate_windows_launcher_start_evidence(&current)?;
                    let windows = self.windows.as_ref().ok_or_else(|| {
                        RuntimeError::new(
                            RuntimeErrorCode::RegistryCorrupt,
                            "native Windows cancel has no configured provider",
                            Some("executionTarget"),
                            true,
                        )
                    })?;
                    let observed = observe_windows_launcher_owner(
                        windows,
                        plan.windows_authority,
                        expected_broker_digest,
                        evidence.launcher_process_id,
                    )?;
                    if target_start.is_file() {
                        continue;
                    }
                    let original_launcher_alive = observed.process_alive
                        && observed.process_creation_time_file_time
                            == Some(evidence.launcher_process_creation_time_file_time);
                    if !original_launcher_alive {
                        if target_start.is_file() {
                            continue;
                        }
                        // Preserve the committed cancel intent and Stopping reservation. The
                        // missing target-start carrier is target-mutable, so launcher-owner loss
                        // does not prove that the target never executed. The reconciliation below
                        // returns the same evidence-gap standing and cancel keeps it nonterminal.
                        break;
                    }
                }
            }
            if Instant::now() >= deadline {
                break;
            }
            sleep_until_poll(deadline, &mut poll_index);
        }
        match self.reconcile_attempt(&attempt.attempt_id) {
            Ok(()) => {}
            Err(error) if error.code == RuntimeErrorCode::LaunchIdentityMismatch => {}
            Err(error) => return Err(error),
        }
        self.observation_from_registry(job_id, 4096, 4096)
    }

    pub fn list_jobs(
        &self,
        request: &RuntimeJobListRequest,
    ) -> RuntimeResult<RuntimeJobListResult> {
        self.registry.list_jobs(request)
    }

    fn release_attempt_supervisor(&self, attempt: &AttemptRecord) -> RuntimeResult<()> {
        let plan = self.registry.execution_plan(&attempt.job_id)?;
        if plan.execution_target == super::ExecutionTarget::WindowsNative
            && self.windows.is_some()
        {
            return Ok(());
        }
        if self
            .registry
            .attempt_supervisor_owner(&attempt.attempt_id)?
            .is_none()
        {
            release_terminal_unit(&attempt.unit_name);
        }
        Ok(())
    }

    fn cleanup_payload_view(&self, _attempt_id: &str) -> RuntimeResult<()> {
        Ok(())
    }

    fn payload_config(
        &self,
        _attempt_id: &str,
        _plan: &RuntimeExecutionPlan,
    ) -> RuntimeResult<Option<RunnerPayloadConfig>> {
        Ok(None)
    }

    fn payload_evidence_matches(&self, uid: Option<u32>, gid: Option<u32>) -> bool {
        uid.is_none() && gid.is_none()
    }
}

pub(super) fn launch_identity_mismatch_cancel_target_absent(
    attempt: &AttemptRecord,
) -> RuntimeResult<bool> {
    let properties = systemctl_show(&attempt.unit_name)?;
    let unit_active = unit_is_active(&properties);
    let recorded_pid_alive = attempt.main_pid.is_some_and(|pid| {
        process_identity(pid)
            .as_deref()
            .zip(attempt.process_start_identity.as_deref())
            .is_some_and(|(observed, expected)| observed == expected)
    });
    let cgroup_alive = attempt
        .control_group
        .as_deref()
        .map(cgroup_has_processes)
        .transpose()?
        .unwrap_or(false);
    Ok(cancel_after_launch_identity_mismatch_is_safe(
        unit_active,
        recorded_pid_alive,
        cgroup_alive,
    ))
}

pub(super) fn cancel_after_launch_identity_mismatch_is_safe(
    unit_active: bool,
    recorded_pid_alive: bool,
    cgroup_alive: bool,
) -> bool {
    !unit_active && !recorded_pid_alive && !cgroup_alive
}

pub(super) fn native_windows_pre_target_evidence_gap() -> RuntimeError {
    RuntimeError::new(
        RuntimeErrorCode::LaunchIdentityMismatch,
        "native launcher owner is gone while target-start/result evidence is absent; target execution is unknown because windows-start evidence is target-mutable. Retain the Attempt and capacity and do not redrive automatically",
        Some("windowsStart"),
        true,
    )
}
