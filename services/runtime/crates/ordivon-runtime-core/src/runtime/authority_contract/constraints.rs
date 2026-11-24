//! Original family invariants and no-widening constraints on exact request shape.
use super::{AuthorityContract, ExecutionAuthorityFamily};
use crate::runtime::{
    ExecutionProfile, ExecutionTarget, RuntimeError, RuntimeResult, WindowsAuthority,
    WindowsExecutionIdentity, WindowsPayloadPrivilege,
};

impl AuthorityContract {
    pub(super) fn enforce(&self) -> RuntimeResult<()> {
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
