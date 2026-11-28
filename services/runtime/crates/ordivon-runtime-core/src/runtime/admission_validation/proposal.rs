//! Convert a proposal to the existing request shape, then reuse the one validator.
use super::super::{
    JobRunProposal, JobRunRequest, RuntimeResult, UniversalExecutionRequest, UniversalExecutionStep,
};
use super::request::validate_run_request_structure_mode;

pub(in crate::runtime) fn validate_run_proposal_structure(
    proposal: &JobRunProposal,
) -> RuntimeResult<()> {
    validate_run_proposal_mode(proposal, true)
}
#[cfg(feature = "postgres-registry-admission")]
pub(crate) fn validate_resource_run_proposal_structure(
    proposal: &JobRunProposal,
) -> RuntimeResult<()> {
    validate_run_proposal_mode(proposal, false)
}
fn validate_run_proposal_mode(proposal: &JobRunProposal, legacy_count: bool) -> RuntimeResult<()> {
    let validation_request = JobRunRequest {
        schema_version: proposal.schema_version,
        client_request_id: proposal.client_request_id.clone(),
        principal: proposal.principal.clone(),
        global_limit: proposal.global_limit,
        execution: UniversalExecutionRequest {
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
                .map(|step| UniversalExecutionStep {
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
    validate_run_request_structure_mode(&validation_request, legacy_count)
}
