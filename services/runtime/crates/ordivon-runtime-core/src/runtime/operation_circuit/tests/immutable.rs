//! Execution family behavioral tests: valid parity and real negative drift cases.
use super::*;
fn reduced_input() -> InputBindingRequest {
    InputBindingRequest {
        authority: "fixtures".to_string(),
        relative_object: "input.bin".to_string(),
        expected_digest: format!("sha256:{}", "f".repeat(64)),
        presentation_relative_path: "input.bin".to_string(),
    }
}
fn plan_with_reduced_input() -> RuntimeExecutionPlan {
    let mut value = plan(ExecutionProfile::ContainedLocal);
    value.input_set_id = Some("input-set-r08".to_string());
    value.effective_inputs = vec![EffectiveInputBinding {
        authority: "fixtures".to_string(),
        relative_object: "input.bin".to_string(),
        digest: format!("sha256:{}", "f".repeat(64)),
        byte_length: 7,
        presentation_relative_path: "input.bin".to_string(),
        access: InputAccessMode::ReadOnly,
    }];
    value
}
#[test]
fn reduced_immutable_input_compiler_is_exact_submit_request_parity() {
    let inputs = vec![reduced_input()];
    let proposal = proposal(ExecutionProfile::ContainedLocal);
    let authority = AuthorityContract::immutable_inputs(&proposal, &inputs).unwrap();
    let request = request(ExecutionProfile::ContainedLocal);
    let plan = plan_with_reduced_input();
    let provider = provider();
    let identity = "runtime-request-input-v2:sha256:parity".to_string();
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
    let compiled = OperationCircuitCompiler::immutable_input_reduced(
        &authority, &request, &inputs, identity, provider, plan,
    )
    .unwrap()
    .into_submit_request();
    assert_eq!(compiled, expected);
}
#[test]
fn reduced_immutable_input_compiler_rejects_trusted_input_family() {
    let inputs = vec![reduced_input()];
    let proposal = proposal(ExecutionProfile::TrustedLocal);
    let authority = AuthorityContract::immutable_inputs(&proposal, &inputs).unwrap();
    let mut trusted_plan = plan_with_reduced_input();
    trusted_plan.execution_profile = ExecutionProfile::TrustedLocal;
    let error = OperationCircuitCompiler::immutable_input_reduced(
        &authority,
        &request(ExecutionProfile::TrustedLocal),
        &inputs,
        "runtime-request-input-v2:sha256:trusted-remains-unmigrated".to_string(),
        provider(),
        trusted_plan,
    )
    .unwrap_err();
    assert_eq!(error.field.as_deref(), Some("authorityContract"));
}
#[test]
fn reduced_immutable_input_compiler_fails_closed_on_materialized_input_drift() {
    let inputs = vec![reduced_input()];
    let proposal = proposal(ExecutionProfile::ContainedLocal);
    let authority = AuthorityContract::immutable_inputs(&proposal, &inputs).unwrap();
    let mut drifted_plan = plan_with_reduced_input();
    drifted_plan.effective_inputs[0].digest = format!("sha256:{}", "a".repeat(64));
    let error = OperationCircuitCompiler::immutable_input_reduced(
        &authority,
        &request(ExecutionProfile::ContainedLocal),
        &inputs,
        "runtime-request-input-v2:sha256:drift".to_string(),
        provider(),
        drifted_plan,
    )
    .unwrap_err();
    assert_eq!(error.field.as_deref(), Some("authorityContract"));
}
#[test]
fn trusted_immutable_input_compiler_is_exact_submit_request_parity() {
    let inputs = vec![reduced_input()];
    let proposal = proposal(ExecutionProfile::TrustedLocal);
    let authority = AuthorityContract::immutable_inputs(&proposal, &inputs).unwrap();
    let request = request(ExecutionProfile::TrustedLocal);
    let mut trusted_plan = plan_with_reduced_input();
    trusted_plan.execution_profile = ExecutionProfile::TrustedLocal;
    let provider = provider();
    let identity = "runtime-request-input-v2:sha256:trusted-parity".to_string();
    let expected = SubmitRequest {
        schema_version: RUNTIME_SCHEMA_VERSION,
        client_request_id: request.client_request_id.clone(),
        request_identity_digest: Some(identity.clone()),
        execution_provider: Some(provider.clone()),
        runtime_release_effect: None,
        host_dependencies: Vec::new(),
        plan: trusted_plan.clone(),
        global_limit: request.global_limit,
    };
    let compiled = OperationCircuitCompiler::immutable_input_trusted(
        &authority,
        &request,
        &inputs,
        identity,
        provider,
        trusted_plan,
    )
    .unwrap()
    .into_submit_request();
    assert_eq!(compiled, expected);
}

#[test]
fn trusted_immutable_input_compiler_rejects_reduced_input_family() {
    let inputs = vec![reduced_input()];
    let proposal = proposal(ExecutionProfile::ContainedLocal);
    let authority = AuthorityContract::immutable_inputs(&proposal, &inputs).unwrap();
    let error = OperationCircuitCompiler::immutable_input_trusted(
        &authority,
        &request(ExecutionProfile::ContainedLocal),
        &inputs,
        "runtime-request-input-v2:sha256:reduced-remains-reduced".to_string(),
        provider(),
        plan_with_reduced_input(),
    )
    .unwrap_err();
    assert_eq!(error.field.as_deref(), Some("authorityContract"));
}

#[test]
fn trusted_immutable_input_compiler_fails_closed_on_materialized_input_drift() {
    let inputs = vec![reduced_input()];
    let proposal = proposal(ExecutionProfile::TrustedLocal);
    let authority = AuthorityContract::immutable_inputs(&proposal, &inputs).unwrap();
    let mut trusted_plan = plan_with_reduced_input();
    trusted_plan.execution_profile = ExecutionProfile::TrustedLocal;
    trusted_plan.effective_inputs[0].digest = format!("sha256:{}", "a".repeat(64));
    let error = OperationCircuitCompiler::immutable_input_trusted(
        &authority,
        &request(ExecutionProfile::TrustedLocal),
        &inputs,
        "runtime-request-input-v2:sha256:trusted-drift".to_string(),
        provider(),
        trusted_plan,
    )
    .unwrap_err();
    assert_eq!(error.field.as_deref(), Some("authorityContract"));
}

#[test]
fn reduced_immutable_input_compiler_requires_materialized_plan_identity() {
    let inputs = vec![reduced_input()];
    let proposal = proposal(ExecutionProfile::ContainedLocal);
    let authority = AuthorityContract::immutable_inputs(&proposal, &inputs).unwrap();
    let mut missing_set = plan_with_reduced_input();
    missing_set.input_set_id = None;
    let error = OperationCircuitCompiler::immutable_input_reduced(
        &authority,
        &request(ExecutionProfile::ContainedLocal),
        &inputs,
        "runtime-request-input-v2:sha256:no-set".to_string(),
        provider(),
        missing_set,
    )
    .unwrap_err();
    assert_eq!(error.field.as_deref(), Some("executionCircuit"));
}
