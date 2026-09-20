impl Runtime {
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

    pub fn read_artifact(
        &self,
        request: &ArtifactReadRequest,
    ) -> RuntimeResult<ArtifactReadResult> {
        if request.schema_version != RUNTIME_SCHEMA_VERSION {
            return Err(RuntimeError::invalid(
                "unsupported runtime schema version",
                "schemaVersion",
            ));
        }
        if request.max_bytes == 0 || request.max_bytes > MAX_ARTIFACT_READ_BYTES {
            return Err(RuntimeError::invalid(
                format!("maxBytes must be in 1..={MAX_ARTIFACT_READ_BYTES}"),
                "maxBytes",
            ));
        }
        let artifact = self
            .registry
            .get_artifact(&request.job_id, &request.artifact_id)?;
        let attempt = self.registry.get_attempt(&artifact.attempt_id)?;
        let bundle = canonical_directory(Path::new(&attempt.bundle_path), "bundlePath")
            .map_err(map_universal_error)?;
        let path = bundle.join(&artifact.relative_path);
        let metadata =
            fs::symlink_metadata(&path).map_err(|error| io_error("inspect Artifact", error))?;
        if metadata.file_type().is_symlink() || !metadata.is_file() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ArtifactIdentityConflict,
                "Artifact path is not a regular non-symlink file",
                Some("artifactId"),
                false,
            ));
        }
        let canonical =
            fs::canonicalize(&path).map_err(|error| io_error("canonicalize Artifact", error))?;
        if !canonical.starts_with(&bundle) {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ArtifactIdentityConflict,
                "Artifact escaped Attempt bundle",
                Some("artifactId"),
                false,
            ));
        }
        if sha256_file(&canonical).map_err(map_universal_error)? != artifact.digest
            || metadata.len() != artifact.byte_length
        {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ArtifactIdentityConflict,
                "Artifact digest or byte length changed",
                Some("artifactId"),
                false,
            ));
        }
        let range = read_utf8_range(
            &canonical,
            request.offset,
            request.max_bytes,
            artifact.byte_length,
            true,
            RangeFields {
                offset: "offset",
                max_bytes: "maxBytes",
            },
            "Artifact",
        )?;
        Ok(ArtifactReadResult {
            job_id: request.job_id.clone(),
            artifact_id: request.artifact_id.clone(),
            content: range.content,
            offset: request.offset,
            next_offset: range.next_offset,
            eof: range.next_offset >= artifact.byte_length,
            digest: artifact.digest,
        })
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

#[cfg(unix)]
fn configured_execution_path() -> RuntimeResult<String> {
    let value =
        std::env::var("ORDIVON_EXEC_PATH").unwrap_or_else(|_| DEFAULT_EXECUTION_PATH.to_string());
    if value.is_empty()
        || value.as_bytes().contains(&0)
        || crate::universal::validate_env(&BTreeMap::from([("PATH".to_string(), value.clone())]))
            .is_err()
        || value
            .split(':')
            .any(|entry| entry.is_empty() || !Path::new(entry).is_absolute())
    {
        return Err(RuntimeError::invalid(
            "ORDIVON_EXEC_PATH must fit the Linux execve per-string boundary and contain only absolute paths",
            "ORDIVON_EXEC_PATH",
        ));
    }
    Ok(value)
}

#[cfg(windows)]
fn configured_execution_path() -> RuntimeResult<String> {
    let value = std::env::var("ORDIVON_EXEC_PATH")
        .or_else(|_| std::env::var("PATH"))
        .map_err(|_| {
            RuntimeError::invalid(
                "ORDIVON_EXEC_PATH or PATH is required on native Windows Runtime",
                "ORDIVON_EXEC_PATH",
            )
        })?;
    let paths = std::env::split_paths(&value).collect::<Vec<_>>();
    if value.is_empty()
        || value.as_bytes().contains(&0)
        || crate::universal::validate_env(&BTreeMap::from([("PATH".to_string(), value.clone())]))
            .is_err()
        || paths.is_empty()
        || paths.iter().any(|entry| !entry.is_absolute())
    {
        return Err(RuntimeError::invalid(
            "native Windows execution PATH must contain only absolute Windows paths",
            "ORDIVON_EXEC_PATH",
        ));
    }
    Ok(value)
}

#[cfg(unix)]
fn configured_execution_home() -> RuntimeResult<String> {
    let value = std::env::var("ORDIVON_EXEC_HOME")
        .or_else(|_| std::env::var("HOME"))
        .unwrap_or_else(|_| DEFAULT_EXECUTION_HOME.to_string());
    if value.is_empty()
        || value.as_bytes().contains(&0)
        || crate::universal::validate_env(&BTreeMap::from([("HOME".to_string(), value.clone())]))
            .is_err()
        || !Path::new(&value).is_absolute()
    {
        return Err(RuntimeError::invalid(
            "ORDIVON_EXEC_HOME must fit the Linux execve per-string boundary and be an absolute path",
            "ORDIVON_EXEC_HOME",
        ));
    }
    Ok(value)
}

#[cfg(windows)]
fn configured_execution_home() -> RuntimeResult<String> {
    let value = std::env::var("ORDIVON_EXEC_HOME")
        .or_else(|_| std::env::var("USERPROFILE"))
        .map_err(|_| {
            RuntimeError::invalid(
                "ORDIVON_EXEC_HOME or USERPROFILE is required on native Windows Runtime",
                "ORDIVON_EXEC_HOME",
            )
        })?;
    if value.is_empty()
        || value.as_bytes().contains(&0)
        || crate::universal::validate_env(&BTreeMap::from([("HOME".to_string(), value.clone())]))
            .is_err()
        || !Path::new(&value).is_absolute()
    {
        return Err(RuntimeError::invalid(
            "native Windows execution home must be an absolute Windows path",
            "ORDIVON_EXEC_HOME",
        ));
    }
    Ok(value)
}

fn merge_environment(
    base: &BTreeMap<String, String>,
    explicit: &BTreeMap<String, String>,
) -> BTreeMap<String, String> {
    let mut merged = base.clone();
    merged.extend(
        explicit
            .iter()
            .map(|(name, value)| (name.clone(), value.clone())),
    );
    merged
}

fn artifact_descriptor(
    artifact: RuntimeArtifactRecord,
    result: Option<&RunnerResult>,
) -> ArtifactDescriptor {
    let dropped_bytes = match artifact.kind.as_str() {
        "stdout" => result.map(|result| result.stdout.dropped_bytes),
        "stderr" => result.map(|result| result.stderr.dropped_bytes),
        _ => None,
    };
    ArtifactDescriptor {
        artifact_id: artifact.artifact_id,
        kind: artifact.kind,
        digest: artifact.digest,
        retained_bytes: artifact.byte_length,
        dropped_bytes,
        truncated: artifact.truncated,
    }
}

pub(crate) fn append_terminal_evidence_for_commit(
    registry: &Registry,
    attempt: &AttemptRecord,
    terminal: &mut TerminalCommit,
) -> RuntimeResult<()> {
    append_terminal_evidence_for_commit_with_observation(registry, attempt, terminal, None)
}

fn append_terminal_evidence_for_commit_with_observation(
    registry: &Registry,
    attempt: &AttemptRecord,
    terminal: &mut TerminalCommit,
    observed_supervisor: Option<&SupervisorObservation>,
) -> RuntimeResult<()> {
    let job = registry.get_job(&attempt.job_id)?;
    let plan: RuntimeExecutionPlan =
        serde_json::from_str(&job.execution_plan_json).map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                format!("stored execution plan is invalid: {error}"),
                Some("executionPlan"),
                false,
            )
        })?;
    let previous_terminal_evidence = registry
        .list_artifacts(&attempt.job_id)?
        .into_iter()
        .rfind(|artifact| artifact.kind == "terminal_evidence")
        .map(|artifact| artifact.artifact_id);
    let (process_tree_disposition, process_tree_detail) = observe_terminal_process_tree(attempt);
    let cancellation_disposition = match attempt.termination_intent {
        AttemptTerminationIntent::Natural if job.desired_state == JobDesiredState::Cancelled => {
            "requested"
        }
        AttemptTerminationIntent::Natural => "not_requested",
        AttemptTerminationIntent::StopRequested => "requested",
        AttemptTerminationIntent::DeadlineExceeded => "deadline_exceeded",
    };
    let delivery_disposition = match terminal.state {
        AttemptState::Orphaned => "reconciliation_required",
        AttemptState::Lost => "unknown",
        _ => "committed",
    };
    let host_dependencies = registry.host_dependencies(&attempt.job_id)?;
    let host_dependency_continuity = if host_dependencies.is_empty() {
        None
    } else {
        match terminal.reason_code.as_str() {
            "HOST_DEPENDENCY_RUNTIME_DRIFT" => Some("runtime_path_drift_detected".to_string()),
            "PROCESS_EXIT_ZERO"
            | "PROCESS_EXIT_NONZERO"
            | "PROCESS_COMPLETED_BEFORE_STOP_EFFECTIVE"
            | "DEADLINE_EXCEEDED" => Some("no_runtime_path_drift_observed".to_string()),
            _ => None,
        }
    };
    let host_dependency_continuity_scope = host_dependency_continuity
        .as_ref()
        .map(|_| HOST_DEPENDENCY_CONTINUITY_SCOPE.to_string());
    let evidence = TerminalProcessEvidence {
        schema_version: RUNTIME_SCHEMA_VERSION,
        job_id: attempt.job_id.clone(),
        attempt_id: attempt.attempt_id.clone(),
        operation_digest: job.operation_digest,
        execution_plan_digest: job.execution_plan_digest,
        workspace_id: plan.workspace_id,
        source_revision: plan.source_revision,
        execution_profile: plan.execution_profile,
        execution_target: plan.execution_target,
        execution_provider: registry.execution_provider(&attempt.job_id)?,
        windows_authority: plan.windows_authority,
        windows_execution_context: plan.windows_execution_context,
        foreign_references: plan.foreign_references,
        host_dependencies,
        host_dependency_continuity,
        host_dependency_continuity_scope,
        input_set_id: plan.input_set_id,
        effective_inputs: plan.effective_inputs,
        executable: plan.executable,
        executable_digest: plan.executable_digest,
        args: plan.args,
        cwd: plan.cwd,
        supervisor: TerminalSupervisorEvidence {
            boot_id: attempt.boot_id.clone(),
            unit_name: attempt.unit_name.clone(),
            invocation_id: attempt.invocation_id.clone(),
            control_group: attempt.control_group.clone(),
            main_pid: attempt.main_pid,
            process_start_identity: attempt.process_start_identity.clone(),
            runner_start_digest: attempt.runner_start_digest.clone(),
        },
        observed_supervisor: observed_supervisor.map(ObservedSupervisorEvidence::from),
        start_disposition: if attempt.runner_start_digest.is_some() {
            "identity_bound".to_string()
        } else {
            "not_bound".to_string()
        },
        cancellation_disposition: cancellation_disposition.to_string(),
        execution_disposition: terminal.state.as_db().to_string(),
        delivery_disposition: delivery_disposition.to_string(),
        process_tree_disposition,
        process_tree_detail,
        reason_code: terminal.reason_code.clone(),
        terminal_artifact_ids: terminal
            .artifacts
            .iter()
            .map(|artifact| artifact.artifact_id.clone())
            .collect(),
        supersedes_artifact_id: previous_terminal_evidence,
        observed_at_ms: terminal.finished_at_ms,
    };
    let bytes = serde_json::to_vec_pretty(&evidence).map_err(|error| {
        RuntimeError::new(
            RuntimeErrorCode::RegistryCorrupt,
            format!("cannot serialize terminal evidence: {error}"),
            Some("terminalEvidence"),
            false,
        )
    })?;
    let digest = sha256_bytes(&bytes);
    let digest_hex = digest.strip_prefix("sha256:").ok_or_else(|| {
        RuntimeError::new(
            RuntimeErrorCode::RegistryCorrupt,
            "terminal evidence digest has an invalid prefix",
            Some("terminalEvidence"),
            false,
        )
    })?;
    let file_name = format!("{TERMINAL_EVIDENCE_FILE_PREFIX}{digest_hex}.json");
    let path = Path::new(&attempt.bundle_path).join(&file_name);
    if path.is_file() {
        let observed = sha256_file(&path).map_err(map_universal_error)?;
        if observed != digest {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ArtifactIdentityConflict,
                "content-addressed terminal evidence has conflicting bytes",
                Some("terminalEvidence"),
                false,
            ));
        }
    } else {
        write_bytes_atomic(&path, &bytes).map_err(map_universal_error)?;
    }
    terminal.artifacts.push(ArtifactRegistration {
        artifact_id: format!("{}.terminal-evidence.{digest_hex}", attempt.attempt_id),
        kind: "terminal_evidence".to_string(),
        relative_path: file_name,
        digest,
        media_type: "application/json".to_string(),
        byte_length: u64::try_from(bytes.len()).unwrap_or(u64::MAX),
        truncated: false,
    });
    Ok(())
}

fn observe_terminal_process_tree(attempt: &AttemptRecord) -> (String, Option<String>) {
    if attempt.control_group.is_none()
        && attempt.main_pid.is_none()
        && attempt.invocation_id.is_none()
    {
        return (
            "unknown".to_string(),
            Some("the Attempt never bound a supervisor process identity".to_string()),
        );
    }
    let deadline = Instant::now() + Duration::from_millis(500);
    let mut poll_index = 0;
    loop {
        match terminal_process_tree_alive(attempt) {
            Ok(false) => return ("terminal_clean".to_string(), None),
            Ok(true) if Instant::now() < deadline => {
                sleep_until_poll(deadline, &mut poll_index);
            }
            Ok(true) => {
                return (
                    "unexpected_residual".to_string(),
                    Some(
                        "the identity-bound PID or recursive cgroup remained populated after the terminal result"
                            .to_string(),
                    ),
                )
            }
            Err(error) => {
                return (
                    "unknown".to_string(),
                    Some(format!(
                        "post-terminal process-tree observation failed: {}",
                        error.message
                    )),
                )
            }
        }
    }
}

fn terminal_process_tree_alive(attempt: &AttemptRecord) -> RuntimeResult<bool> {
    let recorded_pid_alive = attempt.main_pid.is_some_and(|pid| {
        process_identity(pid)
            .as_deref()
            .zip(attempt.process_start_identity.as_deref())
            .is_some_and(|(observed, expected)| observed == expected)
    });
    if recorded_pid_alive {
        return Ok(true);
    }
    if let Some(control_group) = attempt.control_group.as_deref() {
        // Once Runner result evidence is terminal, recursive cgroup-v2 population is the
        // strongest direct process-tree fact. A clean owned cgroup plus a gone recorded
        // PID proves that the Attempt process tree is gone without depending on a
        // potentially slow systemd D-Bus query. systemd remains the fallback only for
        // historical Attempts that lack a committed cgroup identity.
        return cgroup_has_processes(control_group);
    }
    let properties = systemctl_show(&attempt.unit_name)?;
    Ok(unit_is_active(&properties)
        && attempt
            .invocation_id
            .as_deref()
            .zip(properties.get("InvocationID").map(String::as_str))
            .is_some_and(|(expected, observed)| expected == observed))
}

fn attempt_process_tree_alive(attempt: &AttemptRecord) -> RuntimeResult<bool> {
    let properties = systemctl_show(&attempt.unit_name)?;
    let matching_unit_active = unit_is_active(&properties)
        && attempt
            .invocation_id
            .as_deref()
            .zip(properties.get("InvocationID").map(String::as_str))
            .is_some_and(|(expected, observed)| expected == observed);
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
    Ok(matching_unit_active || recorded_pid_alive || cgroup_alive)
}

fn workspace_record_page(
    records: Vec<crate::universal::WorkspaceRecord>,
    limit: u32,
    cursor: Option<&super::RuntimeWorkspaceListCursor>,
) -> (
    Vec<crate::universal::WorkspaceRecord>,
    Option<super::RuntimeWorkspaceListCursor>,
) {
    let mut page = records
        .into_iter()
        .filter(|record| {
            let Some(cursor) = cursor else {
                return true;
            };
            record.created_unix_ms < u128::from(cursor.created_at_ms)
                || (record.created_unix_ms == u128::from(cursor.created_at_ms)
                    && record.workspace_id > cursor.workspace_id)
        })
        .take(limit as usize + 1)
        .collect::<Vec<_>>();
    if page.len() <= limit as usize {
        return (page, None);
    }
    page.truncate(limit as usize);
    let last = page.last().expect("non-empty page after limit validation");
    let next_cursor = super::RuntimeWorkspaceListCursor {
        created_at_ms: u64::try_from(last.created_unix_ms).unwrap_or(u64::MAX),
        workspace_id: last.workspace_id.clone(),
    };
    (page, Some(next_cursor))
}

fn verify_published_bundle(
    final_path: &Path,
    request_bytes: &[u8],
    plan_bytes: &[u8],
    manifest_bytes: &[u8],
) -> RuntimeResult<()> {
    let metadata = fs::symlink_metadata(final_path)
        .map_err(|error| io_error("inspect published Attempt bundle", error))?;
    if metadata.file_type().is_symlink() || !metadata.is_dir() {
        return Err(RuntimeError::new(
            RuntimeErrorCode::RegistryCorrupt,
            "published Attempt bundle is not a non-symlink directory",
            Some("bundlePath"),
            false,
        ));
    }
    for (name, expected) in [
        (RUNNER_REQUEST_FILE, request_bytes),
        (PLAN_FILE, plan_bytes),
        (BUNDLE_MANIFEST_FILE, manifest_bytes),
    ] {
        let path = final_path.join(name);
        let metadata = fs::symlink_metadata(&path)
            .map_err(|error| io_error("inspect published Attempt bundle file", error))?;
        if metadata.file_type().is_symlink() || !metadata.is_file() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "published Attempt bundle contains a non-regular file",
                Some("bundlePath"),
                false,
            ));
        }
        let observed = fs::read(&path)
            .map_err(|error| io_error("read published Attempt bundle file", error))?;
        if observed != expected {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "published Attempt bundle bytes do not match deterministic Attempt identity",
                Some("bundlePath"),
                false,
            ));
        }
    }
    Ok(())
}

fn canonical_input_binding_requests(
    inputs: &[InputBindingRequest],
) -> RuntimeResult<Vec<InputBindingRequest>> {
    if inputs.is_empty() {
        return Err(RuntimeError::invalid(
            "at least one immutable input is required",
            "inputs",
        ));
    }
    let mut canonical = Vec::with_capacity(inputs.len());
    let mut presentation_paths = BTreeSet::<PathBuf>::new();
    for (index, input) in inputs.iter().enumerate() {
        validate_input_authority_name(&input.authority, &format!("inputs[{index}].authority"))?;
        let object = validate_normal_relative_path(
            &input.relative_object,
            &format!("inputs[{index}].relativeObject"),
        )?;
        let presentation = validate_normal_relative_path(
            &input.presentation_relative_path,
            &format!("inputs[{index}].presentationRelativePath"),
        )?;
        validate_sha256_digest(
            &input.expected_digest,
            &format!("inputs[{index}].expectedDigest"),
        )?;
        for existing in &presentation_paths {
            if presentation == *existing
                || presentation.starts_with(existing)
                || existing.starts_with(&presentation)
            {
                return Err(RuntimeError::invalid(
                    "input presentation paths must not overlap as file/ancestor paths",
                    &format!("inputs[{index}].presentationRelativePath"),
                ));
            }
        }
        presentation_paths.insert(presentation.clone());
        canonical.push(InputBindingRequest {
            authority: input.authority.clone(),
            relative_object: object.to_string_lossy().into_owned(),
            expected_digest: input.expected_digest.to_ascii_lowercase(),
            presentation_relative_path: presentation.to_string_lossy().into_owned(),
        });
    }
    canonical.sort_by(|left, right| {
        (
            &left.presentation_relative_path,
            &left.authority,
            &left.relative_object,
            &left.expected_digest,
        )
            .cmp(&(
                &right.presentation_relative_path,
                &right.authority,
                &right.relative_object,
                &right.expected_digest,
            ))
    });
    Ok(canonical)
}

pub(super) fn canonical_credential_binding_requests(
    credentials: &[CredentialBindingRequest],
) -> RuntimeResult<Vec<CredentialBindingRequest>> {
    if credentials.is_empty() {
        return Err(RuntimeError::invalid(
            "at least one credential is required",
            "credentials",
        ));
    }
    let mut canonical = Vec::with_capacity(credentials.len());
    let mut names = BTreeSet::new();
    for (index, credential) in credentials.iter().enumerate() {
        validate_input_authority_name(
            &credential.authority,
            &format!("credentials[{index}].authority"),
        )?;
        validate_credential_name(
            &credential.credential,
            &format!("credentials[{index}].credential"),
        )?;
        if !names.insert(credential.credential.clone()) {
            return Err(RuntimeError::invalid(
                "credential names must be unique within one execution",
                &format!("credentials[{index}].credential"),
            ));
        }
        canonical.push(credential.clone());
    }
    canonical.sort_by(|left, right| {
        (&left.authority, &left.credential)
            .cmp(&(&right.authority, &right.credential))
    });
    Ok(canonical)
}

fn validate_credential_name(value: &str, field: &str) -> RuntimeResult<()> {
    if value.is_empty()
        || value.len() > 128
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b'-'))
        || matches!(value, "." | "..")
    {
        return Err(RuntimeError::invalid(
            "credential name must use 1-128 ASCII alphanumeric/._- characters and must not be . or ..",
            field,
        ));
    }
    Ok(())
}

fn validate_input_authority_name(value: &str, field: &str) -> RuntimeResult<()> {
    if value.is_empty()
        || value.len() > 128
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b'-'))
    {
        return Err(RuntimeError::invalid(
            "input authority name must use 1-128 ASCII alphanumeric/._- characters",
            field,
        ));
    }
    Ok(())
}

fn validate_normal_relative_path(value: &str, field: &str) -> RuntimeResult<PathBuf> {
    let path = Path::new(value);
    if value.is_empty() || value.as_bytes().contains(&0) || path.is_absolute() {
        return Err(RuntimeError::invalid(
            "path must be non-empty, relative, and NUL-free",
            field,
        ));
    }
    let mut normalized = PathBuf::new();
    for component in path.components() {
        match component {
            std::path::Component::Normal(value) => normalized.push(value),
            _ => {
                return Err(RuntimeError::invalid(
                    "path must contain only normal relative components",
                    field,
                ));
            }
        }
    }
    if normalized.as_os_str().is_empty() {
        return Err(RuntimeError::invalid("path must not be empty", field));
    }
    Ok(normalized)
}

fn validate_sha256_digest(value: &str, field: &str) -> RuntimeResult<()> {
    let Some(hex) = value.strip_prefix("sha256:") else {
        return Err(RuntimeError::invalid("digest must use sha256:<hex>", field));
    };
    if hex.len() != 64 || !hex.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err(RuntimeError::invalid(
            "digest must be 32-byte SHA-256 hex",
            field,
        ));
    }
    Ok(())
}

fn open_authority_file(root_file: &File, relative: &str, index: usize) -> RuntimeResult<File> {
    let relative_path =
        validate_normal_relative_path(relative, &format!("inputs[{index}].relativeObject"))?;
    open_regular_file_beneath(root_file, &relative_path, true).map_err(|error| {
        RuntimeError::invalid(
            format!("cannot resolve input object inside authority: {error}"),
            &format!("inputs[{index}].relativeObject"),
        )
    })
}


fn open_credential_file(root_file: &File, name: &str, index: usize) -> RuntimeResult<File> {
    validate_credential_name(name, &format!("credentials[{index}].credential"))?;
    open_regular_file_beneath(root_file, Path::new(name), true).map_err(|_| {
        RuntimeError::invalid(
            "credential is unavailable from the selected authority",
            &format!("credentials[{index}].credential"),
        )
    })
}

fn copy_input_and_digest(mut source: File, target: &Path) -> RuntimeResult<String> {
    let mut output_options = OpenOptions::new();
    output_options.write(true).create_new(true);
    configure_private_create(&mut output_options, 0o600);
    let mut output = output_options
        .open(target)
        .map_err(|error| io_error("create materialized input", error))?;
    std::io::copy(&mut source, &mut output)
        .map_err(|error| io_error("copy input object", error))?;
    output
        .sync_all()
        .map_err(|error| io_error("sync materialized input", error))?;
    sha256_file(target).map_err(map_universal_error)
}

fn collect_materialized_files(
    root: &Path,
    current: &Path,
    files: &mut BTreeSet<PathBuf>,
) -> RuntimeResult<()> {
    for entry in
        fs::read_dir(current).map_err(|error| io_error("scan materialized input set", error))?
    {
        let entry = entry.map_err(|error| io_error("read materialized input entry", error))?;
        let path = entry.path();
        let metadata = fs::symlink_metadata(&path)
            .map_err(|error| io_error("inspect materialized input entry", error))?;
        if metadata.file_type().is_symlink() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::WorkspaceStateMismatch,
                "materialized input set contains a symlink",
                Some("effectiveInputs"),
                false,
            ));
        }
        if metadata.is_dir() {
            collect_materialized_files(root, &path, files)?;
        } else if metadata.is_file() {
            let relative = path.strip_prefix(root).map_err(|_| {
                RuntimeError::new(
                    RuntimeErrorCode::WorkspaceStateMismatch,
                    "materialized input escaped its set root",
                    Some("effectiveInputs"),
                    false,
                )
            })?;
            files.insert(relative.to_path_buf());
        } else {
            return Err(RuntimeError::new(
                RuntimeErrorCode::WorkspaceStateMismatch,
                "materialized input set contains a non-file entry",
                Some("effectiveInputs"),
                false,
            ));
        }
    }
    Ok(())
}

fn verify_effective_input_set(
    root: &Path,
    inputs: &[InputBindingRequest],
) -> RuntimeResult<Vec<EffectiveInputBinding>> {
    let root_metadata = fs::symlink_metadata(root)
        .map_err(|error| io_error("inspect materialized input set", error))?;
    if root_metadata.file_type().is_symlink() || !root_metadata.is_dir() {
        return Err(RuntimeError::new(
            RuntimeErrorCode::WorkspaceStateMismatch,
            "materialized input set root is not a non-symlink directory",
            Some("effectiveInputs"),
            false,
        ));
    }
    let expected = inputs
        .iter()
        .map(|input| PathBuf::from(&input.presentation_relative_path))
        .collect::<BTreeSet<_>>();
    let mut observed = BTreeSet::new();
    collect_materialized_files(root, root, &mut observed)?;
    if observed != expected {
        return Err(RuntimeError::new(
            RuntimeErrorCode::WorkspaceStateMismatch,
            "materialized input set file inventory differs from the committed binding set",
            Some("effectiveInputs"),
            false,
        ));
    }
    let mut effective = Vec::with_capacity(inputs.len());
    for (index, input) in inputs.iter().enumerate() {
        let path = root.join(&input.presentation_relative_path);
        let metadata =
            fs::metadata(&path).map_err(|error| io_error("inspect materialized input", error))?;
        let digest = sha256_file(&path).map_err(map_universal_error)?;
        if digest != input.expected_digest {
            let field = format!("effectiveInputs[{index}].digest");
            return Err(RuntimeError::new(
                RuntimeErrorCode::WorkspaceStateMismatch,
                "materialized input digest does not match the committed binding",
                Some(&field),
                false,
            ));
        }
        effective.push(EffectiveInputBinding {
            authority: input.authority.clone(),
            relative_object: input.relative_object.clone(),
            digest,
            byte_length: metadata.len(),
            presentation_relative_path: input.presentation_relative_path.clone(),
            access: InputAccessMode::ReadOnly,
        });
    }
    Ok(effective)
}

fn inspect_credential_snapshot(root: &Path) -> RuntimeResult<(String, Vec<String>)> {
    let root_metadata = fs::symlink_metadata(root)
        .map_err(|error| io_error("inspect encrypted credential snapshot set", error))?;
    if root_metadata.file_type().is_symlink() || !root_metadata.is_dir() {
        return Err(RuntimeError::new(
            RuntimeErrorCode::WorkspaceStateMismatch,
            "encrypted credential snapshot root is not a non-symlink directory",
            Some("credentialSetId"),
            false,
        ));
    }
    let mut entries = Vec::new();
    for entry in fs::read_dir(root)
        .map_err(|error| io_error("enumerate encrypted credential snapshot", error))?
    {
        let entry = entry
            .map_err(|error| io_error("read encrypted credential snapshot entry", error))?;
        let metadata = fs::symlink_metadata(entry.path())
            .map_err(|error| io_error("inspect encrypted credential snapshot entry", error))?;
        if metadata.file_type().is_symlink() || !metadata.is_file() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::WorkspaceStateMismatch,
                "encrypted credential snapshot contains a non-regular entry",
                Some("credentialSetId"),
                false,
            ));
        }
        let name = entry.file_name().into_string().map_err(|_| {
            RuntimeError::new(
                RuntimeErrorCode::WorkspaceStateMismatch,
                "encrypted credential snapshot contains a non-UTF-8 credential name",
                Some("credentialSetId"),
                false,
            )
        })?;
        validate_credential_name(&name, "credentialSetId")?;
        entries.push(CredentialSnapshotEntry {
            name,
            digest: sha256_file(&entry.path()).map_err(map_universal_error)?,
            byte_length: metadata.len(),
        });
    }
    entries.sort_by(|left, right| left.name.cmp(&right.name));
    let manifest = serde_json::to_vec(&entries).map_err(|error| {
        RuntimeError::new(
            RuntimeErrorCode::RegistryCorrupt,
            format!("cannot serialize encrypted credential snapshot manifest: {error}"),
            Some("credentialSetId"),
            false,
        )
    })?;
    let set_id = sha256_bytes(&manifest);
    let names = entries.into_iter().map(|entry| entry.name).collect();
    Ok((set_id, names))
}

pub(super) fn verify_credential_snapshot(
    root: &Path,
    expected_set_id: &str,
) -> RuntimeResult<Vec<String>> {
    let (observed_set_id, names) = inspect_credential_snapshot(root)?;
    if observed_set_id != expected_set_id {
        return Err(RuntimeError::new(
            RuntimeErrorCode::WorkspaceStateMismatch,
            "encrypted credential snapshot does not match the committed credential set",
            Some("credentialSetId"),
            false,
        ));
    }
    Ok(names)
}

fn effective_input_requests_from_plan(
    plan: &RuntimeExecutionPlan,
) -> RuntimeResult<Vec<InputBindingRequest>> {
    canonical_input_binding_requests(
        &plan
            .effective_inputs
            .iter()
            .map(|input| InputBindingRequest {
                authority: input.authority.clone(),
                relative_object: input.relative_object.clone(),
                expected_digest: input.digest.clone(),
                presentation_relative_path: input.presentation_relative_path.clone(),
            })
            .collect::<Vec<_>>(),
    )
}

const MAX_RUNTIME_RELEASE_RECEIPT_BYTES: u64 = 1_048_576;

struct RuntimeReleaseReceiptProjection {
    disposition: RuntimeReleaseDisposition,
    terminal: bool,
    available: bool,
    digest: Option<String>,
    deployed_tool_count: Option<u32>,
    tool_catalog_digest: Option<String>,
    rollback_status: Option<String>,
    issue: Option<String>,
}

fn validate_runtime_release_request(request: &RuntimeReleaseRequest) -> RuntimeResult<()> {
    if request.schema_version != RUNTIME_SCHEMA_VERSION {
        return Err(RuntimeError::invalid(
            "unsupported runtime schema version",
            "schemaVersion",
        ));
    }
    validate_client_request_id(&request.client_request_id, "clientRequestId")?;
    if request.expected_tool_count == 0 {
        return Err(RuntimeError::invalid(
            "Runtime Release expectedToolCount must be positive",
            "expectedToolCount",
        ));
    }
    if request.commit.len() != 40
        || !request
            .commit
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
    {
        return Err(RuntimeError::invalid(
            "Runtime Release commit must be exactly 40 lowercase hexadecimal characters",
            "commit",
        ));
    }
    let manifest = request
        .candidate_manifest_digest
        .strip_prefix("sha256:")
        .ok_or_else(|| {
            RuntimeError::invalid(
                "candidate manifest digest must use sha256",
                "candidateManifestDigest",
            )
        })?;
    if manifest.len() != 64
        || !manifest
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
    {
        return Err(RuntimeError::invalid(
            "candidate manifest digest must contain 64 lowercase hexadecimal characters",
            "candidateManifestDigest",
        ));
    }
    Ok(())
}

fn validate_release_binding_matches_request(
    binding: &RuntimeReleaseEffectBinding,
    request: &RuntimeReleaseRequest,
) -> RuntimeResult<()> {
    let expected_request_digest = runtime_release_request_identity_digest(request)?;
    let expected_effect_id = runtime_release_effect_id(request);
    if binding.contract != RuntimeReleaseContract::RuntimeReleaseV1
        || binding.effect_id != expected_effect_id
        || binding.request_digest != expected_request_digest
        || binding.workspace_id != request.workspace_id
        || binding.commit != request.commit
        || binding.candidate_manifest_digest != request.candidate_manifest_digest
        || binding.expected_tool_count != request.expected_tool_count
    {
        return Err(RuntimeError::new(
            RuntimeErrorCode::RegistryCorrupt,
            "stored Runtime Release side truth does not match the request identity",
            Some("runtimeReleaseEffect"),
            false,
        ));
    }
    Ok(())
}

fn release_receipt_json(path: &Path) -> Result<Option<(serde_json::Value, String)>, String> {
    let metadata = match fs::symlink_metadata(path) {
        Ok(metadata) => metadata,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(None),
        Err(_) => return Err("RELEASE_RECEIPT_METADATA_UNAVAILABLE".to_string()),
    };
    if metadata.file_type().is_symlink() || !metadata.is_file() {
        return Err("RELEASE_RECEIPT_FILE_UNSAFE".to_string());
    }
    if metadata.len() > MAX_RUNTIME_RELEASE_RECEIPT_BYTES {
        return Err("RELEASE_RECEIPT_FILE_TOO_LARGE".to_string());
    }
    let mut file = open_regular_file_nofollow(path)
        .map_err(|_| "RELEASE_RECEIPT_OPEN_FAILED".to_string())?;
    let mut bytes = Vec::new();
    std::io::Read::by_ref(&mut file)
        .take(MAX_RUNTIME_RELEASE_RECEIPT_BYTES + 1)
        .read_to_end(&mut bytes)
        .map_err(|_| "RELEASE_RECEIPT_READ_FAILED".to_string())?;
    if bytes.len() as u64 > MAX_RUNTIME_RELEASE_RECEIPT_BYTES {
        return Err("RELEASE_RECEIPT_FILE_TOO_LARGE".to_string());
    }
    let value = serde_json::from_slice::<serde_json::Value>(&bytes)
        .map_err(|_| "RELEASE_RECEIPT_JSON_INVALID".to_string())?;
    if !value.is_object() {
        return Err("RELEASE_RECEIPT_JSON_INVALID".to_string());
    }
    Ok(Some((value, sha256_bytes(&bytes))))
}

fn release_effect_json_matches(
    value: &serde_json::Value,
    binding: &RuntimeReleaseEffectBinding,
) -> bool {
    let Some(object) = value.as_object() else {
        return false;
    };
    object.get("contract").and_then(|value| value.as_str()) == Some("runtime_release_v1")
        && object.get("effectId").and_then(|value| value.as_str())
            == Some(binding.effect_id.as_str())
        && object.get("requestDigest").and_then(|value| value.as_str())
            == Some(binding.request_digest.as_str())
        && object.get("commit").and_then(|value| value.as_str()) == Some(binding.commit.as_str())
        && object
            .get("candidateManifestDigest")
            .and_then(|value| value.as_str())
            == Some(binding.candidate_manifest_digest.as_str())
        && object
            .get("expectedToolCount")
            .and_then(|value| value.as_u64())
            == Some(u64::from(binding.expected_tool_count))
}

fn unresolved_release_projection(snapshot: &JobSnapshot) -> RuntimeReleaseReceiptProjection {
    let admitted = snapshot
        .attempt
        .as_ref()
        .is_some_and(|attempt| attempt.state == AttemptState::Accepted);
    RuntimeReleaseReceiptProjection {
        disposition: if admitted {
            RuntimeReleaseDisposition::Admitted
        } else {
            RuntimeReleaseDisposition::InProgress
        },
        terminal: false,
        available: false,
        digest: None,
        deployed_tool_count: None,
        tool_catalog_digest: None,
        rollback_status: None,
        issue: None,
    }
}

fn release_reconciliation_projection(issue: &str) -> RuntimeReleaseReceiptProjection {
    RuntimeReleaseReceiptProjection {
        disposition: RuntimeReleaseDisposition::ReconciliationRequired,
        terminal: false,
        available: false,
        digest: None,
        deployed_tool_count: None,
        tool_catalog_digest: None,
        rollback_status: None,
        issue: Some(issue.to_string()),
    }
}

fn inspect_runtime_release_receipt(
    binding: &RuntimeReleaseEffectBinding,
    snapshot: &JobSnapshot,
) -> RuntimeResult<RuntimeReleaseReceiptProjection> {
    let receipt = Path::new(&binding.receipt_path);
    let directory = match fs::symlink_metadata(receipt) {
        Ok(metadata) => Some(metadata),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => None,
        Err(_) => {
            return Ok(release_reconciliation_projection(
                "RELEASE_RECEIPT_DIRECTORY_UNAVAILABLE",
            ));
        }
    };
    let Some(directory) = directory else {
        return if snapshot.job.resolution.is_none() {
            Ok(unresolved_release_projection(snapshot))
        } else {
            Ok(release_reconciliation_projection(
                "RELEASE_RECEIPT_MISSING_AFTER_JOB_TERMINAL",
            ))
        };
    };
    if directory.file_type().is_symlink() || !directory.is_dir() {
        return Ok(release_reconciliation_projection(
            "RELEASE_RECEIPT_DIRECTORY_UNSAFE",
        ));
    }

    let effect_request = match release_receipt_json(&receipt.join("effect-request.json")) {
        Ok(Some((value, _))) => value,
        Ok(None) if snapshot.job.resolution.is_none() => {
            return Ok(unresolved_release_projection(snapshot))
        }
        Ok(None) => {
            return Ok(release_reconciliation_projection(
                "RELEASE_EFFECT_REQUEST_MISSING_AFTER_JOB_TERMINAL",
            ));
        }
        Err(issue) => return Ok(release_reconciliation_projection(&issue)),
    };
    if !release_effect_json_matches(&effect_request, binding) {
        return Ok(release_reconciliation_projection(
            "RELEASE_EFFECT_REQUEST_MISMATCH",
        ));
    }

    let result = match release_receipt_json(&receipt.join("result.json")) {
        Ok(Some(value)) => value,
        Ok(None) if snapshot.job.resolution.is_none() => {
            return Ok(unresolved_release_projection(snapshot))
        }
        Ok(None) => {
            return Ok(release_reconciliation_projection(
                "RELEASE_RESULT_MISSING_AFTER_JOB_TERMINAL",
            ));
        }
        Err(issue) => return Ok(release_reconciliation_projection(&issue)),
    };
    let (result, result_digest) = result;
    if result.get("commit").and_then(|value| value.as_str()) != Some(binding.commit.as_str())
        || !result
            .get("releaseEffect")
            .is_some_and(|value| release_effect_json_matches(value, binding))
    {
        return Ok(release_reconciliation_projection("RELEASE_RESULT_MISMATCH"));
    }

    let rollback = match release_receipt_json(&receipt.join("rollback-result.json")) {
        Ok(Some((value, _))) => value
            .get("status")
            .and_then(|status| status.as_str())
            .map(str::to_string),
        Ok(None) => None,
        Err(issue) => return Ok(release_reconciliation_projection(&issue)),
    };
    if rollback.as_deref() == Some("restored_previous") {
        return Ok(RuntimeReleaseReceiptProjection {
            disposition: RuntimeReleaseDisposition::RolledBack,
            terminal: true,
            available: true,
            digest: Some(result_digest),
            deployed_tool_count: result
                .pointer("/probe/toolCount")
                .and_then(|value| value.as_u64())
                .and_then(|value| u32::try_from(value).ok()),
            tool_catalog_digest: result
                .pointer("/probe/toolCatalogDigest")
                .and_then(|value| value.as_str())
                .map(str::to_string),
            rollback_status: rollback,
            issue: None,
        });
    }

    let status = result.get("status").and_then(|value| value.as_str());
    let deployed_tool_count = result
        .pointer("/probe/toolCount")
        .and_then(|value| value.as_u64())
        .and_then(|value| u32::try_from(value).ok());
    let tool_catalog_digest = result
        .pointer("/probe/toolCatalogDigest")
        .and_then(|value| value.as_str())
        .map(str::to_string);
    if status == Some("deployed") && deployed_tool_count != Some(binding.expected_tool_count) {
        return Ok(release_reconciliation_projection(
            "RELEASE_RESULT_TOOL_COUNT_MISMATCH",
        ));
    }
    let (disposition, terminal, issue) = match status {
        Some("deployed") => (RuntimeReleaseDisposition::Deployed, true, None),
        Some("not_committed") => (RuntimeReleaseDisposition::NotCommitted, true, None),
        Some("rolled_back") => (RuntimeReleaseDisposition::RolledBack, true, None),
        Some("rollback_failed") => (
            RuntimeReleaseDisposition::ReconciliationRequired,
            false,
            Some("RELEASE_ROLLBACK_FAILED".to_string()),
        ),
        Some("recovery_failed") => (
            RuntimeReleaseDisposition::ReconciliationRequired,
            false,
            Some("RELEASE_RECOVERY_FAILED".to_string()),
        ),
        _ => (
            RuntimeReleaseDisposition::ReconciliationRequired,
            false,
            Some("RELEASE_RESULT_STATUS_UNKNOWN".to_string()),
        ),
    };
    Ok(RuntimeReleaseReceiptProjection {
        disposition,
        terminal,
        available: true,
        digest: Some(result_digest),
        deployed_tool_count,
        tool_catalog_digest,
        rollback_status: rollback,
        issue,
    })
}

fn validate_run_request_structure(request: &JobRunRequest) -> RuntimeResult<()> {
    if request.schema_version != RUNTIME_SCHEMA_VERSION {
        return Err(RuntimeError::invalid(
            "unsupported runtime schema version",
            "schemaVersion",
        ));
    }
    validate_client_request_id(&request.client_request_id, "clientRequestId")?;
    for (value, field) in [
        (&request.principal, "principal"),
        (&request.execution.workspace_id, "execution.workspaceId"),
    ] {
        validate_text_id(value, field)?;
    }
    if request.global_limit == 0 {
        return Err(RuntimeError::invalid(
            "concurrency limits must be positive",
            "globalLimit",
        ));
    }
    if request.wait_ms > MAX_TASK_WAIT_MS
        || request.stdout_tail_bytes > MAX_TASK_TAIL_BYTES
        || request.stderr_tail_bytes > MAX_TASK_TAIL_BYTES
    {
        return Err(RuntimeError::invalid(
            "wait or tail bounds exceed the runtime compact limit",
            "waitMs",
        ));
    }
    if request.execution.executable.is_empty()
        || !Path::new(&request.execution.executable).is_absolute()
        || request.execution.cwd_relative.is_empty()
        || Path::new(&request.execution.cwd_relative).is_absolute()
    {
        return Err(RuntimeError::invalid(
            "executable must be absolute and cwdRelative must be relative",
            "execution",
        ));
    }
    if request
        .execution
        .cwd_relative
        .split('/')
        .any(|part| part == "..")
    {
        return Err(RuntimeError::invalid(
            "cwdRelative cannot contain parent traversal",
            "execution.cwdRelative",
        ));
    }
    if request.execution.timeout_ms == 0
        || request.execution.stdout_limit_bytes == 0
        || request.execution.stderr_limit_bytes == 0
    {
        return Err(RuntimeError::invalid(
            "runtime and output limits must be positive",
            "execution",
        ));
    }
    validate_execution_budget(&request.execution.budget, "execution.budget")?;
    if request.execution.execution_target == super::ExecutionTarget::LocalLinux
        && request.execution.windows_authority != super::WindowsAuthority::Limited
    {
        return Err(RuntimeError::invalid(
            "windowsAuthority=elevated requires executionTarget=windows_native",
            "execution.windowsAuthority",
        ));
    }
    if request.execution.execution_target == super::ExecutionTarget::WindowsNative {
        if request.execution.execution_profile != super::ExecutionProfile::TrustedLocal {
            return Err(RuntimeError::invalid(
                "windows_native currently supports trusted_local only",
                "execution.executionProfile",
            ));
        }
        if !request.execution.steps.is_empty() {
            return Err(RuntimeError::invalid(
                "windows_native currently supports one command only",
                "execution.steps",
            ));
        }
    }
    validate_exec_payload_for_target(
        request.execution.execution_target,
        &request.execution.executable,
        &request.execution.args,
        &request.execution.env,
        "execution",
    )?;
    let mut foreign_reference_keys = std::collections::BTreeSet::new();
    for (index, reference) in request.execution.foreign_references.iter().enumerate() {
        for (value, suffix) in [
            (&reference.namespace, "namespace"),
            (&reference.reference_type, "type"),
            (&reference.id, "id"),
        ] {
            validate_logical_id(
                value,
                &format!("execution.foreignReferences[{index}].{suffix}"),
            )?;
        }
        if let Some(generation) = &reference.generation {
            validate_logical_id(
                generation,
                &format!("execution.foreignReferences[{index}].generation"),
            )?;
        }
        if let Some(digest) = &reference.digest {
            validate_logical_id(
                digest,
                &format!("execution.foreignReferences[{index}].digest"),
            )?;
        }
        let key = (
            reference.namespace.as_str(),
            reference.reference_type.as_str(),
            reference.id.as_str(),
        );
        if !foreign_reference_keys.insert(key) {
            return Err(RuntimeError::invalid(
                "foreignReferences must be unique by namespace, type, and id",
                &format!("execution.foreignReferences[{index}]"),
            ));
        }
    }
    if request.execution.execution_profile == super::ExecutionProfile::ContainedLocal {
        validate_contained_environment(&request.execution.env, "execution.env")?;
    }
    let mut step_ids = std::collections::BTreeSet::new();
    for (index, step) in request.execution.steps.iter().enumerate() {
        validate_logical_id(&step.id, &format!("execution.steps[{index}].id"))?;
        if !step_ids.insert(&step.id) {
            return Err(RuntimeError::invalid(
                "step ids must be unique",
                &format!("execution.steps[{index}].id"),
            ));
        }
        if step.executable.is_empty()
            || !Path::new(&step.executable).is_absolute()
            || step.cwd_relative.is_empty()
            || Path::new(&step.cwd_relative).is_absolute()
            || step.cwd_relative.split('/').any(|part| part == "..")
        {
            return Err(RuntimeError::invalid(
                "step executable must be absolute and cwdRelative must be relative",
                &format!("execution.steps[{index}]"),
            ));
        }
        if step.timeout_ms == 0 {
            return Err(RuntimeError::invalid(
                "step timeoutMs must be positive",
                &format!("execution.steps[{index}].timeoutMs"),
            ));
        }
        validate_exec_payload_for_target(
            request.execution.execution_target,
            &step.executable,
            &step.args,
            &step.env,
            &format!("execution.steps[{index}]"),
        )?;
        if request.execution.execution_profile == super::ExecutionProfile::ContainedLocal {
            validate_contained_environment(&step.env, &format!("execution.steps[{index}].env"))?;
        }
    }
    Ok(())
}

fn validate_exec_payload_for_target(
    target: super::ExecutionTarget,
    executable: &str,
    args: &[String],
    env: &std::collections::BTreeMap<String, String>,
    field: &str,
) -> RuntimeResult<()> {
    match target {
        super::ExecutionTarget::LocalLinux => {
            crate::universal::validate_exec_payload(args, env, field).map_err(map_universal_error)
        }
        super::ExecutionTarget::WindowsNative => {
            super::windows::validate_windows_exec_payload(executable, args, env, field)
        }
    }
}

fn validate_run_proposal_structure(proposal: &super::JobRunProposal) -> RuntimeResult<()> {
    let validation_request = JobRunRequest {
        schema_version: proposal.schema_version,
        client_request_id: proposal.client_request_id.clone(),
        principal: proposal.principal.clone(),
        global_limit: proposal.global_limit,
        execution: super::UniversalExecutionRequest {
            workspace_id: proposal.execution.workspace_id.clone(),
            executable: proposal.execution.executable.clone(),
            args: proposal.execution.args.clone(),
            cwd_relative: proposal.execution.cwd_relative.clone(),
            env: proposal.execution.env.clone(),
            timeout_ms: proposal.execution.timeout_ms.unwrap_or(1),
            stdout_limit_bytes: proposal.execution.stdout_limit_bytes.unwrap_or(1),
            stderr_limit_bytes: proposal.execution.stderr_limit_bytes.unwrap_or(1),
            steps: proposal
                .execution
                .steps
                .iter()
                .map(|step| super::UniversalExecutionStep {
                    id: step.id.clone(),
                    executable: step.executable.clone(),
                    args: step.args.clone(),
                    cwd_relative: step.cwd_relative.clone(),
                    env: step.env.clone(),
                    timeout_ms: step.timeout_ms.unwrap_or(1),
                    continue_on_error: step.continue_on_error,
                })
                .collect(),
            budget: proposal.execution.budget.clone(),
            execution_profile: proposal.execution.execution_profile,
            execution_target: proposal.execution.execution_target,
            windows_authority: proposal.execution.windows_authority,
            foreign_references: proposal.execution.foreign_references.clone(),
            host_dependencies: Vec::new(),
        },
        wait_ms: proposal.wait_ms,
        stdout_tail_bytes: proposal.stdout_tail_bytes,
        stderr_tail_bytes: proposal.stderr_tail_bytes,
    };
    validate_run_request_structure(&validation_request)
}

fn validate_new_admission_policy(
    request: &JobRunRequest,
    max_runtime_ms: u64,
    max_output_bytes: u64,
) -> RuntimeResult<()> {
    if request.execution.timeout_ms > max_runtime_ms {
        return Err(RuntimeError::invalid(
            format!("timeoutMs exceeds configured maximum {max_runtime_ms}"),
            "execution.timeoutMs",
        ));
    }
    if request.execution.stdout_limit_bytes > max_output_bytes {
        return Err(RuntimeError::invalid(
            format!("stdoutLimitBytes exceeds configured maximum {max_output_bytes}"),
            "execution.stdoutLimitBytes",
        ));
    }
    if request.execution.stderr_limit_bytes > max_output_bytes {
        return Err(RuntimeError::invalid(
            format!("stderrLimitBytes exceeds configured maximum {max_output_bytes}"),
            "execution.stderrLimitBytes",
        ));
    }
    Ok(())
}

fn effective_limits_from_plan_json(
    execution_plan_json: &str,
) -> RuntimeResult<super::EffectiveExecutionLimits> {
    let plan: RuntimeExecutionPlan =
        serde_json::from_str(execution_plan_json).map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                format!("stored execution plan is invalid: {error}"),
                Some("executionPlan"),
                false,
            )
        })?;
    Ok(super::EffectiveExecutionLimits {
        timeout_ms: plan.timeout_ms,
        stdout_limit_bytes: plan.stdout_limit_bytes,
        stderr_limit_bytes: plan.stderr_limit_bytes,
        step_timeouts: plan
            .steps
            .into_iter()
            .map(|step| super::EffectiveStepTimeout {
                id: step.id,
                timeout_ms: step.timeout_ms,
            })
            .collect(),
    })
}

fn validate_execution_budget(
    budget: &super::ExecutionBudget,
    field_prefix: &str,
) -> RuntimeResult<()> {
    if budget.memory_max_bytes == Some(0) {
        return Err(RuntimeError::invalid(
            "memoryMaxBytes must be positive",
            &format!("{field_prefix}.memoryMaxBytes"),
        ));
    }
    if budget.tasks_max == Some(0) {
        return Err(RuntimeError::invalid(
            "tasksMax must be positive",
            &format!("{field_prefix}.tasksMax"),
        ));
    }
    if budget.cpu_quota_percent == Some(0) {
        return Err(RuntimeError::invalid(
            "cpuQuotaPercent must be positive",
            &format!("{field_prefix}.cpuQuotaPercent"),
        ));
    }
    Ok(())
}

fn validate_contained_environment(
    environment: &BTreeMap<String, String>,
    field: &str,
) -> RuntimeResult<()> {
    if let Some(name) = CONTAINED_RUNTIME_ENVIRONMENT
        .iter()
        .find(|name| environment.contains_key(**name))
    {
        let environment_field = format!("{field}.{name}");
        return Err(RuntimeError::invalid(
            format!("{name} is owned by the contained-local Runtime profile"),
            &environment_field,
        ));
    }
    Ok(())
}

fn validate_observe_request(request: &JobObserveRequest) -> RuntimeResult<()> {
    if request.schema_version != RUNTIME_SCHEMA_VERSION {
        return Err(RuntimeError::invalid(
            "unsupported runtime schema version",
            "schemaVersion",
        ));
    }
    if request.wait_ms > MAX_TASK_WAIT_MS
        || request.stdout_tail_bytes > MAX_TASK_TAIL_BYTES
        || request.stderr_tail_bytes > MAX_TASK_TAIL_BYTES
    {
        return Err(RuntimeError::invalid(
            "observe bounds exceed runtime limits",
            "waitMs",
        ));
    }
    Ok(())
}

#[derive(Clone, Debug, Eq, PartialEq)]
struct JobActivitySignature {
    status: String,
    stdout_bytes: u64,
    stderr_bytes: u64,
    progress_revision: u64,
}

fn job_activity_signature(
    attempt: Option<&AttemptRecord>,
    projection: &super::JobProjection,
) -> RuntimeResult<JobActivitySignature> {
    let Some(attempt) = attempt else {
        return Ok(JobActivitySignature {
            status: projection.status.clone(),
            stdout_bytes: 0,
            stderr_bytes: 0,
            progress_revision: 0,
        });
    };
    let bundle = Path::new(&attempt.bundle_path);
    let stdout_bytes = file_length_if_present(&bundle.join(STDOUT_FILE))?;
    let stderr_bytes = file_length_if_present(&bundle.join(STDERR_FILE))?;
    let progress_revision = load_runner_progress_if_present(attempt)?
        .map(|progress| progress.revision)
        .unwrap_or(0);
    Ok(JobActivitySignature {
        status: projection.status.clone(),
        stdout_bytes,
        stderr_bytes,
        progress_revision,
    })
}

fn file_length_if_present(path: &Path) -> RuntimeResult<u64> {
    match fs::metadata(path) {
        Ok(metadata) => Ok(metadata.len()),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(0),
        Err(error) => Err(io_error(&format!("inspect {}", path.display()), error)),
    }
}

pub(crate) fn load_runner_progress_if_present(
    attempt: &AttemptRecord,
) -> RuntimeResult<Option<RunnerProgress>> {
    let path = Path::new(&attempt.bundle_path).join(PROGRESS_FILE);
    if !path.exists() {
        return Ok(None);
    }
    let bytes = fs::read(&path).map_err(|error| io_error("read Runner progress", error))?;
    serde_json::from_slice(&bytes).map(Some).map_err(|error| {
        RuntimeError::new(
            RuntimeErrorCode::RegistryCorrupt,
            format!("invalid Runner progress: {error}"),
            Some("progress"),
            false,
        )
    })
}

pub(crate) fn latest_output_modified_ms(attempt: &AttemptRecord) -> RuntimeResult<Option<u64>> {
    let bundle = Path::new(&attempt.bundle_path);
    let mut latest = None;
    for path in [bundle.join(STDOUT_FILE), bundle.join(STDERR_FILE)] {
        let metadata = match fs::metadata(&path) {
            Ok(metadata) => metadata,
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => continue,
            Err(error) => return Err(io_error(&format!("inspect {}", path.display()), error)),
        };
        if metadata.len() == 0 {
            continue;
        }
        let modified = metadata
            .modified()
            .map_err(|error| io_error(&format!("read {} mtime", path.display()), error))?;
        let millis = modified
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_millis();
        let millis = u64::try_from(millis).unwrap_or(u64::MAX);
        latest = Some(latest.map_or(millis, |value: u64| value.max(millis)));
    }
    Ok(latest)
}

fn load_control_error_summary_if_present(attempt: &AttemptRecord) -> RuntimeResult<Option<String>> {
    let path = Path::new(&attempt.bundle_path).join(CONTROL_RESULT_FILE);
    if !path.exists() {
        return Ok(None);
    }
    let bytes = fs::read(&path).map_err(|error| io_error("read control result", error))?;
    let evidence: ControlTerminalEvidence = serde_json::from_slice(&bytes).map_err(|error| {
        RuntimeError::new(
            RuntimeErrorCode::RegistryCorrupt,
            format!("invalid control result: {error}"),
            Some("controlResult"),
            false,
        )
    })?;
    if evidence.job_id != attempt.job_id || evidence.attempt_id != attempt.attempt_id {
        return Err(RuntimeError::new(
            RuntimeErrorCode::ResultIdentityConflict,
            "control result identity does not match Attempt",
            Some("controlResult"),
            false,
        ));
    }
    Ok(evidence.detail)
}

fn load_runner_result_if_present(
    attempt: &AttemptRecord,
) -> RuntimeResult<Option<RunnerResult>> {
    let path = Path::new(&attempt.bundle_path).join(RESULT_FILE);
    if !path.exists() {
        return Ok(None);
    }
    let bytes = fs::read(&path).map_err(|error| io_error("read Runner result", error))?;
    serde_json::from_slice(&bytes).map(Some).map_err(|error| {
        RuntimeError::new(
            RuntimeErrorCode::RegistryCorrupt,
            format!("invalid Runner result: {error}"),
            Some("result"),
            false,
        )
    })
}
