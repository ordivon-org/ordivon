//! Execution family behavioral tests: valid parity and real negative drift cases.
use super::*;
#[test]
fn ordinary_compiler_is_exact_submit_request_parity() {
    let proposal = proposal(ExecutionProfile::TrustedLocal);
    let authority = AuthorityContract::ordinary(&proposal).unwrap();
    let request = request(ExecutionProfile::TrustedLocal);
    let plan = plan(ExecutionProfile::TrustedLocal);
    let provider = provider();
    let identity = "runtime-request-v2:sha256:parity".to_string();
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

    let compiled = OperationCircuitCompiler::ordinary(
        &authority,
        &request,
        identity,
        provider,
        Vec::new(),
        plan,
    )
    .unwrap()
    .into_submit_request();
    assert_eq!(compiled, expected);
}

#[test]
fn ordinary_compiler_rejects_nonordinary_authority_family() {
    let proposal = proposal(ExecutionProfile::ContainedLocal);
    let authority = AuthorityContract::immutable_inputs(
        &proposal,
        &[crate::runtime::InputBindingRequest {
            authority: "fixtures".to_string(),
            relative_object: "input.bin".to_string(),
            expected_digest: format!("sha256:{}", "f".repeat(64)),
            presentation_relative_path: "input.bin".to_string(),
        }],
    )
    .unwrap();
    let error = OperationCircuitCompiler::ordinary(
        &authority,
        &request(ExecutionProfile::ContainedLocal),
        "runtime-request-v2:sha256:wrong-family".to_string(),
        provider(),
        Vec::new(),
        plan(ExecutionProfile::ContainedLocal),
    )
    .unwrap_err();
    assert_eq!(error.field.as_deref(), Some("authorityContract"));
}

#[test]
fn ordinary_compiler_fails_closed_when_request_no_longer_matches_authority() {
    let proposal = proposal(ExecutionProfile::TrustedLocal);
    let authority = AuthorityContract::ordinary(&proposal).unwrap();
    let mut request = request(ExecutionProfile::TrustedLocal);
    request.principal = "principal:other".to_string();
    let error = OperationCircuitCompiler::ordinary(
        &authority,
        &request,
        "runtime-request-v2:sha256:authority-drift".to_string(),
        provider(),
        Vec::new(),
        plan(ExecutionProfile::TrustedLocal),
    )
    .unwrap_err();
    assert_eq!(error.field.as_deref(), Some("authorityContract"));
}

#[test]
fn ordinary_compiler_fails_closed_on_request_plan_authority_drift() {
    let proposal = proposal(ExecutionProfile::TrustedLocal);
    let authority = AuthorityContract::ordinary(&proposal).unwrap();
    let request = request(ExecutionProfile::TrustedLocal);
    let mismatched = plan(ExecutionProfile::ContainedLocal);
    let error = OperationCircuitCompiler::ordinary(
        &authority,
        &request,
        "runtime-request-v2:sha256:drift".to_string(),
        provider(),
        Vec::new(),
        mismatched,
    )
    .unwrap_err();
    assert_eq!(error.field.as_deref(), Some("executionCircuit"));
}
