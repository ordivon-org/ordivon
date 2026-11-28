//! Original ordinary execution materialization with exact Host Dependency binding.
use super::{ExecutionCircuit, OperationCircuitCompiler};
use crate::runtime::authority_contract::AuthorityContract;
use crate::runtime::{
    ExecutionProviderSnapshot, HostDependencyBinding, JobRunRequest, RuntimeError,
    RuntimeExecutionPlan, RuntimeResult, SubmitRequest, RUNTIME_SCHEMA_VERSION,
};

impl OperationCircuitCompiler {
    pub(crate) fn ordinary(
        authority: &AuthorityContract,
        request: &JobRunRequest,
        request_identity_digest: String,
        provider: ExecutionProviderSnapshot,
        host_dependencies: Vec<HostDependencyBinding>,
        plan: RuntimeExecutionPlan,
    ) -> RuntimeResult<ExecutionCircuit> {
        authority.validate_ordinary_realization(request, &host_dependencies)?;
        if plan.principal != request.principal
            || plan.execution_target != request.execution.execution_target
            || plan.execution_profile != request.execution.execution_profile
        {
            return Err(RuntimeError::invalid(
                "resolved execution plan does not match the admitted ordinary request",
                "executionCircuit",
            ));
        }

        Ok(ExecutionCircuit {
            submit: SubmitRequest {
                schema_version: RUNTIME_SCHEMA_VERSION,
                client_request_id: request.client_request_id.clone(),
                request_identity_digest: Some(request_identity_digest),
                execution_provider: Some(provider),
                runtime_release_effect: None,
                host_dependencies,
                plan,
                global_limit: request.global_limit,
            },
        })
    }
}
