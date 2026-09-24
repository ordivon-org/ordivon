use super::authority_contract::AuthorityContract;
use super::{
    ExecutionProviderSnapshot, HostDependencyBinding, InputBindingRequest, JobRunRequest,
    RuntimeError, RuntimeExecutionPlan, RuntimeResult, SubmitRequest, RUNTIME_SCHEMA_VERSION,
};

/// Thin internal physical-execution circuit.
///
/// R08 intentionally reuses the already-enforced `SubmitRequest`/`RuntimeExecutionPlan` truth
/// instead of creating a second persisted execution schema. The compiler composes one new
/// ordinary admission only after exact replay and R07 authority compilation have already run.
/// Reduced and trusted immutable-input admission are the second and third strangler slices;
/// credential-bound and Runtime-release families remain on their current paths until they
/// independently prove parity.
#[derive(Debug)]
pub(crate) struct ExecutionCircuit {
    submit: SubmitRequest,
}

impl ExecutionCircuit {
    pub(crate) fn into_submit_request(self) -> SubmitRequest {
        self.submit
    }
}

pub(crate) struct OperationCircuitCompiler;

impl OperationCircuitCompiler {
    pub(crate) fn ordinary(
        authority: &AuthorityContract,
        request: &JobRunRequest,
        request_identity_digest: String,
        provider: ExecutionProviderSnapshot,
        host_dependencies: Vec<HostDependencyBinding>,
        plan: RuntimeExecutionPlan,
    ) -> RuntimeResult<ExecutionCircuit> {
        authority.validate_ordinary_realization(request, &host_dependencies)?;
        if plan.principal != request.principal
            || plan.execution_target != request.execution.execution_target
            || plan.execution_profile != request.execution.execution_profile
        {
            return Err(RuntimeError::invalid(
                "resolved execution plan does not match the admitted ordinary request",
                "executionCircuit",
            ));
        }

        Ok(ExecutionCircuit {
            submit: SubmitRequest {
                schema_version: RUNTIME_SCHEMA_VERSION,
                client_request_id: request.client_request_id.clone(),
                request_identity_digest: Some(request_identity_digest),
                execution_provider: Some(provider),
                runtime_release_effect: None,
                host_dependencies,
                plan,
                global_limit: request.global_limit,
            },
        })
    }

    pub(crate) fn immutable_input_reduced(
        authority: &AuthorityContract,
        request: &JobRunRequest,
        inputs: &[InputBindingRequest],
        request_identity_digest: String,
        provider: ExecutionProviderSnapshot,
        plan: RuntimeExecutionPlan,
    ) -> RuntimeResult<ExecutionCircuit> {
        authority.validate_immutable_input_reduced_realization(
            request,
            inputs,
            &plan.effective_inputs,
        )?;
        if plan.principal != request.principal
            || plan.execution_target != request.execution.execution_target
            || plan.execution_profile != request.execution.execution_profile
            || plan.input_set_id.is_none()
            || plan.effective_inputs.is_empty()
            || plan.credential_set_id.is_some()
        {
            return Err(RuntimeError::invalid(
                "resolved execution plan does not match the admitted reduced immutable-input request",
                "executionCircuit",
            ));
        }
        Ok(ExecutionCircuit {
            submit: SubmitRequest {
                schema_version: RUNTIME_SCHEMA_VERSION,
                client_request_id: request.client_request_id.clone(),
                request_identity_digest: Some(request_identity_digest),
                execution_provider: Some(provider),
                runtime_release_effect: None,
                host_dependencies: Vec::new(),
                plan,
                global_limit: request.global_limit,
            },
        })
    }

    pub(crate) fn immutable_input_trusted(
        authority: &AuthorityContract,
        request: &JobRunRequest,
        inputs: &[InputBindingRequest],
        request_identity_digest: String,
        provider: ExecutionProviderSnapshot,
        plan: RuntimeExecutionPlan,
    ) -> RuntimeResult<ExecutionCircuit> {
        authority.validate_immutable_input_trusted_realization(
            request,
            inputs,
            &plan.effective_inputs,
        )?;
        if plan.principal != request.principal
            || plan.execution_target != request.execution.execution_target
            || plan.execution_profile != request.execution.execution_profile
            || plan.input_set_id.is_none()
            || plan.effective_inputs.is_empty()
            || plan.credential_set_id.is_some()
        {
            return Err(RuntimeError::invalid(
                "resolved execution plan does not match the admitted trusted immutable-input request",
                "executionCircuit",
            ));
        }
        Ok(ExecutionCircuit {
            submit: SubmitRequest {
                schema_version: RUNTIME_SCHEMA_VERSION,
                client_request_id: request.client_request_id.clone(),
                request_identity_digest: Some(request_identity_digest),
                execution_provider: Some(provider),
                runtime_release_effect: None,
                host_dependencies: Vec::new(),
                plan,
                global_limit: request.global_limit,
            },
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::runtime::{
        EffectiveInputBinding, ExecutionBudget, ExecutionProfile, ExecutionProposal,
        ExecutionProviderContract, ExecutionStepProposal, ExecutionTarget, InputAccessMode,
        InputBindingRequest, JobRunProposal, RuntimeExecutionStep, UniversalExecutionRequest,
        UniversalExecutionStep, WindowsAuthority,
    };
    use std::collections::BTreeMap;

    fn proposal(profile: ExecutionProfile) -> JobRunProposal {
        JobRunProposal {
            schema_version: 1,
            client_request_id: "r08-ordinary-parity".to_string(),
            principal: "principal:r08".to_string(),
            global_limit: 4,
            execution: ExecutionProposal {
                workspace_id: "ws-r08".to_string(),
                executable: "/usr/bin/true".to_string(),
                args: vec!["--version".to_string()],
                cwd_relative: ".".to_string(),
                env: BTreeMap::new(),
                timeout_ms: Some(2_000),
                stdout_limit_bytes: Some(8_192),
                stderr_limit_bytes: Some(8_192),
                steps: vec![ExecutionStepProposal {
                    id: "step-1".to_string(),
                    executable: "/usr/bin/printf".to_string(),
                    args: vec!["ok".to_string()],
                    cwd_relative: ".".to_string(),
                    env: BTreeMap::new(),
                    timeout_ms: Some(1_000),
                    continue_on_error: false,
                }],
                budget: ExecutionBudget::default(),
                execution_profile: profile,
                execution_target: ExecutionTarget::LocalLinux,
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

    fn request(profile: ExecutionProfile) -> JobRunRequest {
        JobRunRequest {
            schema_version: 1,
            client_request_id: "r08-ordinary-parity".to_string(),
            principal: "principal:r08".to_string(),
            global_limit: 4,
            execution: UniversalExecutionRequest {
                workspace_id: "ws-r08".to_string(),
                executable: "/usr/bin/true".to_string(),
                args: vec!["--version".to_string()],
                cwd_relative: ".".to_string(),
                env: BTreeMap::new(),
                timeout_ms: 2_000,
                stdout_limit_bytes: 8_192,
                stderr_limit_bytes: 8_192,
                steps: vec![UniversalExecutionStep {
                    id: "step-1".to_string(),
                    executable: "/usr/bin/printf".to_string(),
                    args: vec!["ok".to_string()],
                    cwd_relative: ".".to_string(),
                    env: BTreeMap::new(),
                    timeout_ms: 1_000,
                    continue_on_error: false,
                }],
                budget: ExecutionBudget::default(),
                execution_profile: profile,
                execution_target: ExecutionTarget::LocalLinux,
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

    fn plan(profile: ExecutionProfile) -> RuntimeExecutionPlan {
        RuntimeExecutionPlan {
            schema_version: 1,
            workspace_id: "ws-r08".to_string(),
            workspace_path: "/tmp/ws-r08".to_string(),
            source_revision: "a".repeat(40),
            workspace_source_digest: Some(format!("sha256:{}", "b".repeat(64))),
            workspace_git_common_dir: Some("/tmp/repo/.git".to_string()),
            executable: "/usr/bin/true".to_string(),
            executable_digest: format!("sha256:{}", "c".repeat(64)),
            args: vec!["--version".to_string()],
            cwd: "/tmp/ws-r08".to_string(),
            env: BTreeMap::new(),
            timeout_ms: 2_000,
            stdout_limit_bytes: 8_192,
            stderr_limit_bytes: 8_192,
            steps: vec![RuntimeExecutionStep {
                id: "step-1".to_string(),
                executable: "/usr/bin/printf".to_string(),
                executable_digest: format!("sha256:{}", "d".repeat(64)),
                args: vec!["ok".to_string()],
                cwd: "/tmp/ws-r08".to_string(),
                env: BTreeMap::new(),
                timeout_ms: 1_000,
                continue_on_error: false,
            }],
            budget: ExecutionBudget::default(),
            execution_profile: profile,
            execution_target: ExecutionTarget::LocalLinux,
            windows_authority: WindowsAuthority::Limited,
            windows_context: None,
            windows_execution_context: None,
            foreign_references: Vec::new(),
            input_set_id: None,
            effective_inputs: Vec::new(),
            credential_set_id: None,
            principal: "principal:r08".to_string(),
        }
    }

    fn provider() -> ExecutionProviderSnapshot {
        ExecutionProviderSnapshot {
            contract: ExecutionProviderContract::LocalLinuxRunnerV1,
            executable_digest: format!("sha256:{}", "e".repeat(64)),
            wsl_distribution: None,
        }
    }

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
}
