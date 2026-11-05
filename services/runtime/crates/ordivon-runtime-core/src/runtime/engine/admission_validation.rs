// Request structure and admission policy qualification, separate from durable admission effects.
// No new policy authority, side effects, or public wire surface.
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

pub(crate) fn validate_run_proposal_structure(proposal: &super::JobRunProposal) -> RuntimeResult<()> {
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
            windows_context: proposal.execution.windows_context,
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
