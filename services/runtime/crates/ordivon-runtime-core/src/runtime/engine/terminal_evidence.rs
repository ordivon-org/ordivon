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
    let runner_result_terminal = terminal
        .artifacts
        .iter()
        .any(|artifact| artifact.kind == "execution_result");
    let source_observation_required = plan.execution_target
        == super::ExecutionTarget::LocalLinux
        && plan.workspace_source_digest.is_some()
        && runner_result_terminal
        && (terminal.state == AttemptState::Succeeded
            || matches!(
            terminal.reason_code.as_str(),
            "PROCESS_EXIT_NONZERO"
                | "DEADLINE_EXCEEDED"
                | "WORKSPACE_SOURCE_PRECONDITION_DRIFT"
                | "INPUT_PRECONDITION_DRIFT"
                | "HOST_DEPENDENCY_RUNTIME_DRIFT"
                | "EXECUTABLE_RUNTIME_DRIFT"
        ));
    let source_observation = match validate_workspace_source_observation_artifact(
        attempt,
        plan.workspace_source_digest.as_deref(),
        source_observation_required,
        super::evidence::SourceObservationRequirement::for_terminal(
            terminal.state,
            &terminal.reason_code,
        ),
    ) {
        Ok(source_observation) => source_observation,
        Err(error)
            if terminal.reason_code == "RUNNER_RESULT_QUARANTINED"
                && matches!(
                    error.code,
                    RuntimeErrorCode::RegistryCorrupt
                        | RuntimeErrorCode::ResultIdentityConflict
                        | RuntimeErrorCode::ArtifactIdentityConflict
                        | RuntimeErrorCode::LaunchIdentityMismatch
                ) =>
        {
            None
        }
        Err(error) => return Err(error),
    };
    if let Some(source_observation) = source_observation {
        let duplicate = terminal
            .artifacts
            .iter()
            .any(|artifact| artifact.artifact_id == source_observation.artifact_id);
        if !duplicate {
            terminal.artifacts.push(source_observation);
        }
    }
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
