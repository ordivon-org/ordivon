//! Tests original request authority behavior, not source layout.
use super::*;
use crate::runtime::{
    CredentialBindingRequest, InputBindingRequest, JobRunProposal, RuntimeErrorCode,
    WindowsExecutionIdentity, WindowsPayloadPrivilege,
};
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
    assert!(AuthorityContract::credential_bound_trusted(&p, &[credential("provider")]).is_err());
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
fn generic_windows_elevation_requires_operator_authorized_principal() {
    let mut p = proposal(
        ExecutionTarget::WindowsNative,
        ExecutionProfile::TrustedLocal,
    );
    p.execution.windows_authority = WindowsAuthority::Elevated;
    let contract = AuthorityContract::ordinary(&p).unwrap();
    let denied = contract.authorize_windows_elevation(&[]).unwrap_err();
    assert_eq!(denied.code, RuntimeErrorCode::AuthorizationDenied);
    assert_eq!(
        denied.field.as_deref(),
        Some("execution.windowsContext.privilege")
    );
    contract
        .authorize_windows_elevation(&["principal:test".to_string()])
        .unwrap();
}

#[test]
fn limited_windows_context_does_not_require_elevation_grant() {
    let p = proposal(
        ExecutionTarget::WindowsNative,
        ExecutionProfile::TrustedLocal,
    );
    AuthorityContract::ordinary(&p)
        .unwrap()
        .authorize_windows_elevation(&[])
        .unwrap();
}

#[test]
fn active_user_elevated_context_uses_same_principal_gate() {
    let mut p = proposal(
        ExecutionTarget::WindowsNative,
        ExecutionProfile::TrustedLocal,
    );
    p.execution.windows_context = Some(WindowsExecutionContextRequest::new(
        WindowsExecutionIdentity::ActiveUser,
        WindowsPayloadPrivilege::Elevated,
    ));
    let contract = AuthorityContract::ordinary(&p).unwrap();
    assert_eq!(
        contract.authorize_windows_elevation(&[]).unwrap_err().code,
        RuntimeErrorCode::AuthorizationDenied
    );
    contract
        .authorize_windows_elevation(&["principal:test".to_string()])
        .unwrap();
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
