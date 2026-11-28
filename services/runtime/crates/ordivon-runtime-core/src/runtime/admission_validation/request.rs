//! Validate user request structure and target execution constraints, without storage effects.
use super::super::error::map_universal_error;
use super::super::{
    validate_client_request_id, validate_logical_id, ExecutionProfile, ExecutionTarget,
    JobRunRequest, RuntimeError, RuntimeResult, WindowsAuthority, MAX_TASK_TAIL_BYTES,
    MAX_TASK_WAIT_MS, RUNTIME_SCHEMA_VERSION,
};
use super::{environment::validate_contained_environment, limits::validate_execution_budget};
use crate::runtime::types::validate_bounded_text_id as validate_text_id;
use std::path::Path;

// Request structure and admission policy qualification, separate from durable admission effects.
// No new policy authority, side effects, or public wire surface.
pub(in crate::runtime) fn validate_run_request_structure(
    request: &JobRunRequest,
) -> RuntimeResult<()> {
    validate_run_request_structure_mode(request, true)
}
pub(super) fn validate_run_request_structure_mode(
    request: &JobRunRequest,
    legacy_count: bool,
) -> RuntimeResult<()> {
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
    if legacy_count && request.global_limit == 0 {
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
    if request.execution.execution_target == ExecutionTarget::LocalLinux
        && request.execution.windows_authority != WindowsAuthority::Limited
    {
        return Err(RuntimeError::invalid(
            "windowsAuthority=elevated requires executionTarget=windows_native",
            "execution.windowsAuthority",
        ));
    }
    if request.execution.execution_target == ExecutionTarget::WindowsNative {
        if request.execution.execution_profile != ExecutionProfile::TrustedLocal {
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
    if request.execution.execution_profile == ExecutionProfile::ContainedLocal {
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
        if request.execution.execution_profile == ExecutionProfile::ContainedLocal {
            validate_contained_environment(&step.env, &format!("execution.steps[{index}].env"))?;
        }
    }
    Ok(())
}

fn validate_exec_payload_for_target(
    target: ExecutionTarget,
    executable: &str,
    args: &[String],
    env: &std::collections::BTreeMap<String, String>,
    field: &str,
) -> RuntimeResult<()> {
    match target {
        ExecutionTarget::LocalLinux => {
            crate::universal::validate_exec_payload(args, env, field).map_err(map_universal_error)
        }
        ExecutionTarget::WindowsNative => {
            super::super::windows::validate_windows_exec_payload(executable, args, env, field)
        }
    }
}
