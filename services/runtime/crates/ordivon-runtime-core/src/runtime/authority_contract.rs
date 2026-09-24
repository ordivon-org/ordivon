use std::collections::BTreeSet;

use super::{
    CredentialBindingRequest, EffectiveInputBinding, ExecutionProfile, ExecutionTarget,
    HostDependencyBinding, InputAccessMode, InputBindingRequest, JobRunProposal, JobRunRequest,
    RuntimeError, RuntimeResult, WindowsAuthority, WindowsExecutionContextRequest,
    WindowsExecutionIdentity, WindowsPayloadPrivilege,
};

/// Internal authority composition selected by one already-typed Runtime execution family.
///
/// This is not a grant, IAM decision, or secret/provider capability. It makes the authority
/// already requested by Runtime's public execution families explicit before a *new* durable
/// admission. Exact replay remains outside this boundary and therefore is not reinterpreted.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum ExecutionAuthorityFamily {
    Ordinary,
    ImmutableInputReduced,
    ImmutableInputTrusted,
    CredentialBoundTrusted,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct AuthorityContract {
    family: ExecutionAuthorityFamily,
    principal: String,
    execution_target: ExecutionTarget,
    execution_profile: ExecutionProfile,
    legacy_windows_authority: WindowsAuthority,
    windows_context: Option<WindowsExecutionContextRequest>,
    executable_paths: Vec<String>,
    input_authorities: Vec<String>,
    credential_authorities: Vec<String>,
    host_dependencies: Vec<HostDependencyBinding>,
}

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

    fn enforce(&self) -> RuntimeResult<()> {
        if self.principal.is_empty() || self.executable_paths.is_empty() {
            return Err(RuntimeError::invalid(
                "authority contract requires principal and executable identity",
                "authorityContract",
            ));
        }
        if self.execution_target == ExecutionTarget::LocalLinux
            && self.legacy_windows_authority != WindowsAuthority::Limited
        {
            return Err(RuntimeError::invalid(
                "windowsAuthority is valid only for windows_native execution",
                "execution.windowsAuthority",
            ));
        }

        match self.execution_target {
            ExecutionTarget::LocalLinux if self.windows_context.is_some() => {
                return Err(RuntimeError::invalid(
                    "windowsContext is valid only for windows_native execution",
                    "execution.windowsContext",
                ));
            }
            ExecutionTarget::WindowsNative if self.windows_context.is_none() => {
                return Err(RuntimeError::invalid(
                    "windows_native authority requires an effective Windows context",
                    "execution.windowsContext",
                ));
            }
            _ => {}
        }

        match self.family {
            ExecutionAuthorityFamily::Ordinary => {
                if !self.input_authorities.is_empty() || !self.credential_authorities.is_empty() {
                    return Err(RuntimeError::invalid(
                        "ordinary execution cannot carry bound input or credential authorities",
                        "authorityContract",
                    ));
                }
                if !self.host_dependencies.is_empty()
                    && (self.execution_target != ExecutionTarget::LocalLinux
                        || self.execution_profile != ExecutionProfile::TrustedLocal)
                {
                    return Err(RuntimeError::invalid(
                        "Host Dependencies require trusted_local local_linux execution",
                        "execution.hostDependencies",
                    ));
                }
            }
            ExecutionAuthorityFamily::ImmutableInputReduced => {
                self.require_inputs_without_other_bindings()?;
                match self.execution_target {
                    ExecutionTarget::LocalLinux => {
                        if self.execution_profile != ExecutionProfile::ContainedLocal {
                            return Err(RuntimeError::invalid(
                                "reduced-authority Linux immutable inputs require contained_local execution",
                                "execution.executionProfile",
                            ));
                        }
                    }
                    ExecutionTarget::WindowsNative => {
                        if self.legacy_windows_authority != WindowsAuthority::Limited {
                            return Err(RuntimeError::invalid(
                                "windows_native immutable input bindings do not support elevated or active-user legacy authority",
                                "execution.windowsAuthority",
                            ));
                        }
                        let context = self
                            .windows_context
                            .expect("Windows context compiled above");
                        if self.execution_profile != ExecutionProfile::TrustedLocal
                            || context.identity != WindowsExecutionIdentity::Service
                            || context.privilege != WindowsPayloadPrivilege::Limited
                        {
                            return Err(RuntimeError::invalid(
                                "windows_native immutable input bindings support trusted_local service/limited authority only",
                                "execution.windowsContext",
                            ));
                        }
                    }
                }
            }
            ExecutionAuthorityFamily::ImmutableInputTrusted => {
                self.require_inputs_without_other_bindings()?;
                if self.execution_target != ExecutionTarget::LocalLinux
                    || self.execution_profile != ExecutionProfile::TrustedLocal
                {
                    return Err(RuntimeError::invalid(
                        "trusted immutable-input execution requires trusted_local local_linux",
                        "execution.executionProfile",
                    ));
                }
            }
            ExecutionAuthorityFamily::CredentialBoundTrusted => {
                if self.credential_authorities.is_empty()
                    || !self.input_authorities.is_empty()
                    || !self.host_dependencies.is_empty()
                {
                    return Err(RuntimeError::invalid(
                        "credential-bound execution requires credentials and cannot widen through inputs or Host Dependencies",
                        "authorityContract",
                    ));
                }
                if self.execution_target != ExecutionTarget::LocalLinux
                    || self.execution_profile != ExecutionProfile::TrustedLocal
                {
                    return Err(RuntimeError::invalid(
                        "credential-bound execution requires trusted_local local_linux",
                        "execution.executionProfile",
                    ));
                }
            }
        }
        Ok(())
    }

    fn require_inputs_without_other_bindings(&self) -> RuntimeResult<()> {
        if self.input_authorities.is_empty()
            || !self.credential_authorities.is_empty()
            || !self.host_dependencies.is_empty()
        {
            return Err(RuntimeError::invalid(
                "immutable-input execution requires inputs and cannot widen through credentials or Host Dependencies",
                "authorityContract",
            ));
        }
        Ok(())
    }
}

fn sorted_unique<'a>(values: impl Iterator<Item = &'a str>) -> Vec<String> {
    values
        .map(str::to_owned)
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect()
}

fn sorted_host_dependencies(values: &[HostDependencyBinding]) -> Vec<HostDependencyBinding> {
    let mut values = values.to_vec();
    values.sort_by(|left, right| {
        left.path
            .cmp(&right.path)
            .then_with(|| left.expected_digest.cmp(&right.expected_digest))
    });
    values.dedup();
    values
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::runtime::{
        ExecutionBudget, ExecutionProposal, ExecutionStepProposal, HostDependencyBinding,
        WindowsAuthority,
    };
    use std::collections::BTreeMap;

    fn proposal(target: ExecutionTarget, profile: ExecutionProfile) -> JobRunProposal {
        JobRunProposal {
            schema_version: 1,
            client_request_id: "r07-authority-contract-test".to_string(),
            principal: "principal:test".to_string(),
            global_limit: 4,
            execution: ExecutionProposal {
                workspace_id: "workspace-r07".to_string(),
                executable: "/usr/bin/true".to_string(),
                args: Vec::new(),
                cwd_relative: ".".to_string(),
                env: BTreeMap::new(),
                timeout_ms: Some(1_000),
                stdout_limit_bytes: Some(4_096),
                stderr_limit_bytes: Some(4_096),
                steps: Vec::new(),
                budget: ExecutionBudget::default(),
                execution_profile: profile,
                execution_target: target,
                windows_authority: WindowsAuthority::Limited,
                windows_context: None,
                foreign_references: Vec::new(),
                host_dependencies: Vec::new(),
            },
            wait_ms: 0,
            stdout_tail_bytes: 0,
            stderr_tail_bytes: 0,
        }
    }

    fn input(authority: &str) -> InputBindingRequest {
        InputBindingRequest {
            authority: authority.to_string(),
            relative_object: "object.bin".to_string(),
            expected_digest: format!("sha256:{}", "0".repeat(64)),
            presentation_relative_path: "data/object.bin".to_string(),
        }
    }

    fn credential(authority: &str) -> CredentialBindingRequest {
        CredentialBindingRequest {
            authority: authority.to_string(),
            credential: "token".to_string(),
        }
    }

    #[test]
    fn ordinary_trusted_linux_records_host_dependency_authority() {
        let mut p = proposal(ExecutionTarget::LocalLinux, ExecutionProfile::TrustedLocal);
        p.execution.host_dependencies.push(HostDependencyBinding {
            path: "/usr/bin/true".to_string(),
            expected_digest: format!("sha256:{}", "0".repeat(64)),
        });
        let contract = AuthorityContract::ordinary(&p).expect("ordinary authority");
        assert_eq!(contract.family, ExecutionAuthorityFamily::Ordinary);
        assert_eq!(contract.host_dependencies.len(), 1);
        assert_eq!(contract.host_dependencies[0].path, "/usr/bin/true");
        assert_eq!(
            contract.host_dependencies[0].expected_digest,
            format!("sha256:{}", "0".repeat(64))
        );
    }

    #[test]
    fn ordinary_contained_linux_rejects_host_dependency_widening() {
        let mut p = proposal(
            ExecutionTarget::LocalLinux,
            ExecutionProfile::ContainedLocal,
        );
        p.execution.host_dependencies.push(HostDependencyBinding {
            path: "/usr/bin/true".to_string(),
            expected_digest: format!("sha256:{}", "0".repeat(64)),
        });
        assert!(AuthorityContract::ordinary(&p).is_err());
    }

    #[test]
    fn immutable_linux_compiles_reduced_and_trusted_families() {
        let reduced = proposal(
            ExecutionTarget::LocalLinux,
            ExecutionProfile::ContainedLocal,
        );
        let reduced_contract =
            AuthorityContract::immutable_inputs(&reduced, &[input("finance")]).unwrap();
        assert_eq!(
            reduced_contract.family,
            ExecutionAuthorityFamily::ImmutableInputReduced
        );

        let trusted = proposal(ExecutionTarget::LocalLinux, ExecutionProfile::TrustedLocal);
        let trusted_contract =
            AuthorityContract::immutable_inputs(&trusted, &[input("research")]).unwrap();
        assert_eq!(
            trusted_contract.family,
            ExecutionAuthorityFamily::ImmutableInputTrusted
        );
    }

    #[test]
    fn immutable_windows_rejects_active_user_context() {
        let mut p = proposal(
            ExecutionTarget::WindowsNative,
            ExecutionProfile::TrustedLocal,
        );
        p.execution.windows_context = Some(WindowsExecutionContextRequest::new(
            WindowsExecutionIdentity::ActiveUser,
            WindowsPayloadPrivilege::Limited,
        ));
        assert!(AuthorityContract::immutable_inputs(&p, &[input("artifact")]).is_err());
    }

    #[test]
    fn credential_bound_records_authority_names_without_granting_them() {
        let p = proposal(ExecutionTarget::LocalLinux, ExecutionProfile::TrustedLocal);
        let contract = AuthorityContract::credential_bound_trusted(
            &p,
            &[credential("provider-b"), credential("provider-a")],
        )
        .unwrap();
        assert_eq!(
            contract.family,
            ExecutionAuthorityFamily::CredentialBoundTrusted
        );
        assert_eq!(
            contract.credential_authorities,
            vec!["provider-a", "provider-b"]
        );
    }

    #[test]
    fn bound_families_reject_host_dependency_widening() {
        let mut p = proposal(ExecutionTarget::LocalLinux, ExecutionProfile::TrustedLocal);
        p.execution.host_dependencies.push(HostDependencyBinding {
            path: "/usr/bin/true".to_string(),
            expected_digest: format!("sha256:{}", "0".repeat(64)),
        });
        assert!(AuthorityContract::immutable_inputs(&p, &[input("finance")]).is_err());
        assert!(
            AuthorityContract::credential_bound_trusted(&p, &[credential("provider")]).is_err()
        );
    }

    #[test]
    fn local_execution_rejects_windows_context() {
        let mut p = proposal(ExecutionTarget::LocalLinux, ExecutionProfile::TrustedLocal);
        p.execution.windows_context = Some(WindowsExecutionContextRequest::new(
            WindowsExecutionIdentity::Service,
            WindowsPayloadPrivilege::Limited,
        ));
        assert!(AuthorityContract::ordinary(&p).is_err());
    }

    #[test]
    fn local_execution_rejects_legacy_windows_authority() {
        let mut p = proposal(ExecutionTarget::LocalLinux, ExecutionProfile::TrustedLocal);
        p.execution.windows_authority = WindowsAuthority::Elevated;
        assert!(AuthorityContract::ordinary(&p).is_err());
    }

    #[test]
    fn contract_records_all_executable_identity_paths() {
        let mut p = proposal(ExecutionTarget::LocalLinux, ExecutionProfile::TrustedLocal);
        p.execution.steps.push(ExecutionStepProposal {
            id: "second".to_string(),
            executable: "/usr/bin/printf".to_string(),
            args: Vec::new(),
            cwd_relative: ".".to_string(),
            env: BTreeMap::new(),
            timeout_ms: Some(1_000),
            continue_on_error: false,
        });
        let contract = AuthorityContract::ordinary(&p).unwrap();
        assert_eq!(
            contract.executable_paths,
            vec!["/usr/bin/printf", "/usr/bin/true"]
        );
    }
}
