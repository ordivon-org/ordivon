//! Original immutable-input reduced/trusted Circuit consumers of one qualified contract.
use super::{ExecutionCircuit, OperationCircuitCompiler};
use crate::runtime::authority_contract::AuthorityContract;
use crate::runtime::{
    ExecutionProviderSnapshot, InputBindingRequest, JobRunRequest, RuntimeError,
    RuntimeExecutionPlan, RuntimeResult, SubmitRequest, RUNTIME_SCHEMA_VERSION,
};

impl OperationCircuitCompiler {
    pub(crate) fn immutable_input_reduced(
        authority: &AuthorityContract,
        request: &JobRunRequest,
        inputs: &[InputBindingRequest],
        request_identity_digest: String,
        provider: ExecutionProviderSnapshot,
        plan: RuntimeExecutionPlan,
    ) -> RuntimeResult<ExecutionCircuit> {
        authority.validate_immutable_input_reduced_realization(
            request,
            inputs,
            &plan.effective_inputs,
        )?;
        if plan.principal != request.principal
            || plan.execution_target != request.execution.execution_target
            || plan.execution_profile != request.execution.execution_profile
            || plan.input_set_id.is_none()
            || plan.effective_inputs.is_empty()
            || plan.credential_set_id.is_some()
        {
            return Err(RuntimeError::invalid(
                "resolved execution plan does not match the admitted reduced immutable-input request",
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
                host_dependencies: Vec::new(),
                plan,
                global_limit: request.global_limit,
            },
        })
    }

    pub(crate) fn immutable_input_trusted(
        authority: &AuthorityContract,
        request: &JobRunRequest,
        inputs: &[InputBindingRequest],
        request_identity_digest: String,
        provider: ExecutionProviderSnapshot,
        plan: RuntimeExecutionPlan,
    ) -> RuntimeResult<ExecutionCircuit> {
        authority.validate_immutable_input_trusted_realization(
            request,
            inputs,
            &plan.effective_inputs,
        )?;
        if plan.principal != request.principal
            || plan.execution_target != request.execution.execution_target
            || plan.execution_profile != request.execution.execution_profile
            || plan.input_set_id.is_none()
            || plan.effective_inputs.is_empty()
            || plan.credential_set_id.is_some()
        {
            return Err(RuntimeError::invalid(
                "resolved execution plan does not match the admitted trusted immutable-input request",
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
                host_dependencies: Vec::new(),
                plan,
                global_limit: request.global_limit,
            },
        })
    }
}
