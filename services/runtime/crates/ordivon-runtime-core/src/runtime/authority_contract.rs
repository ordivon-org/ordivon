//! Same original request-family contract. Small immutable domain types and sibling proof obligations.
//! Normalize request -> compile contract -> constrain mode -> validate real execution.
use super::{
    ExecutionProfile, ExecutionTarget, HostDependencyBinding, WindowsAuthority,
    WindowsExecutionContextRequest,
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

mod compile;
mod constraints;
mod normalization;
mod realization;
mod windows;
use normalization::{sorted_host_dependencies, sorted_unique};
#[cfg(test)]
mod tests;
