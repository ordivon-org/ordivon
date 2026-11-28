//! Bound admission budgets and read existing immutable execution plan limits.
use super::super::{
    EffectiveExecutionLimits, EffectiveStepTimeout, ExecutionBudget, JobRunRequest, RuntimeError,
    RuntimeErrorCode, RuntimeExecutionPlan, RuntimeResult,
};

pub(in crate::runtime) fn validate_new_admission_policy(
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

pub(in crate::runtime) fn effective_limits_from_plan_json(
    execution_plan_json: &str,
) -> RuntimeResult<EffectiveExecutionLimits> {
    let plan: RuntimeExecutionPlan =
        serde_json::from_str(execution_plan_json).map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                format!("stored execution plan is invalid: {error}"),
                Some("executionPlan"),
                false,
            )
        })?;
    Ok(EffectiveExecutionLimits {
        timeout_ms: plan.timeout_ms,
        stdout_limit_bytes: plan.stdout_limit_bytes,
        stderr_limit_bytes: plan.stderr_limit_bytes,
        step_timeouts: plan
            .steps
            .into_iter()
            .map(|step| EffectiveStepTimeout {
                id: step.id,
                timeout_ms: step.timeout_ms,
            })
            .collect(),
    })
}

pub(super) fn validate_execution_budget(
    budget: &ExecutionBudget,
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
