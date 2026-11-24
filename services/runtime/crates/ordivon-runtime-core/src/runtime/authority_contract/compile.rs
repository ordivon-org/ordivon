//! Compiles typed request family into one existing AuthorityContract; no side-effect issuer.
use super::{sorted_host_dependencies, sorted_unique, AuthorityContract, ExecutionAuthorityFamily};
use crate::runtime::{
    CredentialBindingRequest, ExecutionProfile, ExecutionTarget, InputBindingRequest,
    JobRunProposal, RuntimeError, RuntimeResult,
};

impl AuthorityContract {
    pub(crate) fn ordinary(proposal: &JobRunProposal) -> RuntimeResult<Self> {
        Self::compile(ExecutionAuthorityFamily::Ordinary, proposal, &[], &[])
    }

    pub(crate) fn immutable_inputs(
        proposal: &JobRunProposal,
        inputs: &[InputBindingRequest],
    ) -> RuntimeResult<Self> {
        let family = match (
            proposal.execution.execution_target,
            proposal.execution.execution_profile,
        ) {
            (ExecutionTarget::LocalLinux, ExecutionProfile::ContainedLocal) => {
                ExecutionAuthorityFamily::ImmutableInputReduced
            }
            (ExecutionTarget::LocalLinux, ExecutionProfile::TrustedLocal) => {
                ExecutionAuthorityFamily::ImmutableInputTrusted
            }
            (ExecutionTarget::WindowsNative, ExecutionProfile::TrustedLocal) => {
                ExecutionAuthorityFamily::ImmutableInputReduced
            }
            (ExecutionTarget::WindowsNative, ExecutionProfile::ContainedLocal) => {
                return Err(RuntimeError::invalid(
                    "windows_native immutable input bindings require trusted_local execution",
                    "execution.executionProfile",
                ));
            }
        };
        Self::compile(family, proposal, inputs, &[])
    }

    pub(crate) fn credential_bound_trusted(
        proposal: &JobRunProposal,
        credentials: &[CredentialBindingRequest],
    ) -> RuntimeResult<Self> {
        Self::compile(
            ExecutionAuthorityFamily::CredentialBoundTrusted,
            proposal,
            &[],
            credentials,
        )
    }

    fn compile(
        family: ExecutionAuthorityFamily,
        proposal: &JobRunProposal,
        inputs: &[InputBindingRequest],
        credentials: &[CredentialBindingRequest],
    ) -> RuntimeResult<Self> {
        let execution = &proposal.execution;
        let windows_context = match execution.execution_target {
            ExecutionTarget::LocalLinux => {
                if execution.windows_context.is_some() {
                    return Err(RuntimeError::invalid(
                        "windowsContext is valid only for windows_native execution",
                        "execution.windowsContext",
                    ));
                }
                None
            }
            ExecutionTarget::WindowsNative => {
                let context = execution
                    .windows_context
                    .unwrap_or_else(|| execution.windows_authority.canonical_context());
                if execution.windows_context.is_some()
                    && !context.compatible_with_legacy(execution.windows_authority)
                {
                    return Err(RuntimeError::invalid(
                        "windowsContext conflicts with the non-default legacy windowsAuthority",
                        "execution.windowsContext",
                    ));
                }
                Some(context)
            }
        };

        let contract = Self {
            family,
            principal: proposal.principal.clone(),
            execution_target: execution.execution_target,
            execution_profile: execution.execution_profile,
            legacy_windows_authority: execution.windows_authority,
            windows_context,
            executable_paths: sorted_unique(
                std::iter::once(execution.executable.as_str())
                    .chain(execution.steps.iter().map(|step| step.executable.as_str())),
            ),
            input_authorities: sorted_unique(inputs.iter().map(|input| input.authority.as_str())),
            credential_authorities: sorted_unique(
                credentials
                    .iter()
                    .map(|credential| credential.authority.as_str()),
            ),
            host_dependencies: sorted_host_dependencies(&execution.host_dependencies),
        };
        contract.enforce()?;
        Ok(contract)
    }
}
