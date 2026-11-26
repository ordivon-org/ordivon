//! Execution family behavioral tests: valid parity and real negative drift cases.
use super::*;
fn credential(authority: &str, name: &str) -> CredentialBindingRequest {
    CredentialBindingRequest {
        authority: authority.to_string(),
        credential: name.to_string(),
    }
}

fn plan_with_credentials() -> RuntimeExecutionPlan {
    let mut value = plan(ExecutionProfile::TrustedLocal);
    value.credential_set_id = Some("credential-set-r08".to_string());
    value
}

#[test]
fn credential_bound_compiler_is_exact_submit_request_parity() {
    let credentials = vec![credential("provider", "api-key")];
    let proposal = proposal(ExecutionProfile::TrustedLocal);
    let authority = AuthorityContract::credential_bound_trusted(&proposal, &credentials).unwrap();
    let request = request(ExecutionProfile::TrustedLocal);
    let plan = plan_with_credentials();
    let provider = provider();
    let identity = "runtime-request-credential-v1:sha256:parity".to_string();
    let expected = SubmitRequest {
        schema_version: RUNTIME_SCHEMA_VERSION,
        client_request_id: request.client_request_id.clone(),
        request_identity_digest: Some(identity.clone()),
        execution_provider: Some(provider.clone()),
        runtime_release_effect: None,
        host_dependencies: Vec::new(),
        plan: plan.clone(),
        global_limit: request.global_limit,
    };
    let compiled = OperationCircuitCompiler::credential_bound_trusted(
        &authority,
        &request,
        &credentials,
        identity,
        provider,
        plan,
    )
    .unwrap()
    .into_submit_request();
    assert_eq!(compiled, expected);
}

#[test]
fn credential_bound_compiler_rejects_ordinary_family() {
    let credentials = vec![credential("provider", "api-key")];
    let proposal = proposal(ExecutionProfile::TrustedLocal);
    let authority = AuthorityContract::ordinary(&proposal).unwrap();
    let error = OperationCircuitCompiler::credential_bound_trusted(
        &authority,
        &request(ExecutionProfile::TrustedLocal),
        &credentials,
        "runtime-request-credential-v1:sha256:wrong-family".to_string(),
        provider(),
        plan_with_credentials(),
    )
    .unwrap_err();
    assert_eq!(error.field.as_deref(), Some("authorityContract"));
}

#[test]
fn credential_bound_compiler_fails_closed_on_authority_drift() {
    let credentials = vec![credential("provider-a", "api-key")];
    let proposal = proposal(ExecutionProfile::TrustedLocal);
    let authority = AuthorityContract::credential_bound_trusted(&proposal, &credentials).unwrap();
    let drifted = vec![credential("provider-b", "api-key")];
    let error = OperationCircuitCompiler::credential_bound_trusted(
        &authority,
        &request(ExecutionProfile::TrustedLocal),
        &drifted,
        "runtime-request-credential-v1:sha256:authority-drift".to_string(),
        provider(),
        plan_with_credentials(),
    )
    .unwrap_err();
    assert_eq!(error.field.as_deref(), Some("authorityContract"));
}

#[test]
fn credential_bound_compiler_requires_materialized_plan_identity() {
    let credentials = vec![credential("provider", "api-key")];
    let proposal = proposal(ExecutionProfile::TrustedLocal);
    let authority = AuthorityContract::credential_bound_trusted(&proposal, &credentials).unwrap();
    let mut missing_set = plan_with_credentials();
    missing_set.credential_set_id = None;
    let error = OperationCircuitCompiler::credential_bound_trusted(
        &authority,
        &request(ExecutionProfile::TrustedLocal),
        &credentials,
        "runtime-request-credential-v1:sha256:no-set".to_string(),
        provider(),
        missing_set,
    )
    .unwrap_err();
    assert_eq!(error.field.as_deref(), Some("executionCircuit"));
}
