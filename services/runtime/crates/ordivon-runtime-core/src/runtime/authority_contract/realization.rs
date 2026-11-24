//! Compares already-qualified execution, inputs, credentials, and host path witnesses.
use super::{sorted_host_dependencies, sorted_unique, AuthorityContract, ExecutionAuthorityFamily};
use crate::runtime::{
    CredentialBindingRequest, EffectiveInputBinding, ExecutionTarget, HostDependencyBinding,
    InputAccessMode, InputBindingRequest, JobRunRequest, RuntimeError, RuntimeResult,
    WindowsExecutionContextRequest,
};

impl AuthorityContract {
    pub(crate) fn validate_ordinary_realization(
        &self,
        request: &JobRunRequest,
        validated_host_dependencies: &[HostDependencyBinding],
    ) -> RuntimeResult<()> {
        if self.family != ExecutionAuthorityFamily::Ordinary {
            return Err(RuntimeError::invalid(
                "ordinary execution circuit requires ordinary AuthorityContract",
                "authorityContract",
            ));
        }
        let execution = &request.execution;
        let effective_windows_context = match execution.execution_target {
            ExecutionTarget::LocalLinux => None,
            ExecutionTarget::WindowsNative => Some(
                execution
                    .windows_context
                    .unwrap_or_else(|| execution.windows_authority.canonical_context()),
            ),
        };
        let executable_paths = sorted_unique(
            std::iter::once(execution.executable.as_str())
                .chain(execution.steps.iter().map(|step| step.executable.as_str())),
        );
        let declared_host_dependencies = sorted_host_dependencies(&execution.host_dependencies);
        let validated_host_dependencies = sorted_host_dependencies(validated_host_dependencies);
        if self.principal != request.principal
            || self.execution_target != execution.execution_target
            || self.execution_profile != execution.execution_profile
            || self.legacy_windows_authority != execution.windows_authority
            || self.windows_context != effective_windows_context
            || self.executable_paths != executable_paths
            || self.host_dependencies != declared_host_dependencies
            || self.host_dependencies != validated_host_dependencies
        {
            return Err(RuntimeError::invalid(
                "ordinary execution realization drifted from its AuthorityContract",
                "authorityContract",
            ));
        }
        Ok(())
    }

    pub(crate) fn is_immutable_input_reduced(&self) -> bool {
        self.family == ExecutionAuthorityFamily::ImmutableInputReduced
    }

    pub(crate) fn effective_windows_context(&self) -> Option<WindowsExecutionContextRequest> {
        self.windows_context
    }

    pub(crate) fn validate_immutable_input_reduced_realization(
        &self,
        request: &JobRunRequest,
        inputs: &[InputBindingRequest],
        effective_inputs: &[EffectiveInputBinding],
    ) -> RuntimeResult<()> {
        if self.family != ExecutionAuthorityFamily::ImmutableInputReduced {
            return Err(RuntimeError::invalid(
                "reduced immutable-input circuit requires reduced immutable-input AuthorityContract",
                "authorityContract",
            ));
        }
        let execution = &request.execution;
        let effective_windows_context = match execution.execution_target {
            ExecutionTarget::LocalLinux => None,
            ExecutionTarget::WindowsNative => Some(
                execution
                    .windows_context
                    .unwrap_or_else(|| execution.windows_authority.canonical_context()),
            ),
        };
        let executable_paths = sorted_unique(
            std::iter::once(execution.executable.as_str())
                .chain(execution.steps.iter().map(|step| step.executable.as_str())),
        );
        let input_authorities = sorted_unique(inputs.iter().map(|input| input.authority.as_str()));
        let declared_host_dependencies = sorted_host_dependencies(&execution.host_dependencies);
        let inputs_match = inputs.len() == effective_inputs.len()
            && inputs
                .iter()
                .zip(effective_inputs)
                .all(|(input, effective)| {
                    input.authority == effective.authority
                        && input.relative_object == effective.relative_object
                        && input.expected_digest == effective.digest
                        && input.presentation_relative_path == effective.presentation_relative_path
                        && effective.access == InputAccessMode::ReadOnly
                });
        if self.principal != request.principal
            || self.execution_target != execution.execution_target
            || self.execution_profile != execution.execution_profile
            || self.legacy_windows_authority != execution.windows_authority
            || self.windows_context != effective_windows_context
            || self.executable_paths != executable_paths
            || self.input_authorities != input_authorities
            || self.host_dependencies != declared_host_dependencies
            || !inputs_match
        {
            return Err(RuntimeError::invalid(
                "reduced immutable-input realization drifted from its AuthorityContract",
                "authorityContract",
            ));
        }
        Ok(())
    }

    pub(crate) fn validate_immutable_input_trusted_realization(
        &self,
        request: &JobRunRequest,
        inputs: &[InputBindingRequest],
        effective_inputs: &[EffectiveInputBinding],
    ) -> RuntimeResult<()> {
        if self.family != ExecutionAuthorityFamily::ImmutableInputTrusted {
            return Err(RuntimeError::invalid(
                "trusted immutable-input circuit requires trusted immutable-input AuthorityContract",
                "authorityContract",
            ));
        }
        let execution = &request.execution;
        let executable_paths = sorted_unique(
            std::iter::once(execution.executable.as_str())
                .chain(execution.steps.iter().map(|step| step.executable.as_str())),
        );
        let input_authorities = sorted_unique(inputs.iter().map(|input| input.authority.as_str()));
        let declared_host_dependencies = sorted_host_dependencies(&execution.host_dependencies);
        let inputs_match = inputs.len() == effective_inputs.len()
            && inputs
                .iter()
                .zip(effective_inputs)
                .all(|(input, effective)| {
                    input.authority == effective.authority
                        && input.relative_object == effective.relative_object
                        && input.expected_digest == effective.digest
                        && input.presentation_relative_path == effective.presentation_relative_path
                        && effective.access == InputAccessMode::ReadOnly
                });
        if self.principal != request.principal
            || self.execution_target != execution.execution_target
            || self.execution_profile != execution.execution_profile
            || self.legacy_windows_authority != execution.windows_authority
            || self.windows_context.is_some()
            || self.executable_paths != executable_paths
            || self.input_authorities != input_authorities
            || self.host_dependencies != declared_host_dependencies
            || !inputs_match
        {
            return Err(RuntimeError::invalid(
                "trusted immutable-input realization drifted from its AuthorityContract",
                "authorityContract",
            ));
        }
        Ok(())
    }

    pub(crate) fn validate_credential_bound_trusted_realization(
        &self,
        request: &JobRunRequest,
        credentials: &[CredentialBindingRequest],
    ) -> RuntimeResult<()> {
        if self.family != ExecutionAuthorityFamily::CredentialBoundTrusted {
            return Err(RuntimeError::invalid(
                "credential-bound circuit requires credential-bound AuthorityContract",
                "authorityContract",
            ));
        }
        let execution = &request.execution;
        let executable_paths = sorted_unique(
            std::iter::once(execution.executable.as_str())
                .chain(execution.steps.iter().map(|step| step.executable.as_str())),
        );
        let credential_authorities = sorted_unique(
            credentials
                .iter()
                .map(|credential| credential.authority.as_str()),
        );
        let declared_host_dependencies = sorted_host_dependencies(&execution.host_dependencies);
        if self.principal != request.principal
            || self.execution_target != execution.execution_target
            || self.execution_profile != execution.execution_profile
            || self.legacy_windows_authority != execution.windows_authority
            || self.windows_context.is_some()
            || self.executable_paths != executable_paths
            || self.credential_authorities != credential_authorities
            || !self.input_authorities.is_empty()
            || self.host_dependencies != declared_host_dependencies
        {
            return Err(RuntimeError::invalid(
                "credential-bound realization drifted from its AuthorityContract",
                "authorityContract",
            ));
        }
        Ok(())
    }
}
