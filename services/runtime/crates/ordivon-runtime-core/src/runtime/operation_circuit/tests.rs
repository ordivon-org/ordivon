//! Original executable parity and negative authority drift, grouped by execution family.
use super::*;
use crate::runtime::authority_contract::AuthorityContract;
use crate::runtime::{
    CredentialBindingRequest, EffectiveInputBinding, ExecutionBudget, ExecutionProfile,
    ExecutionProposal, ExecutionProviderContract, ExecutionStepProposal, ExecutionTarget,
    InputAccessMode, InputBindingRequest, JobRunProposal, RuntimeExecutionStep,
    UniversalExecutionRequest, UniversalExecutionStep, WindowsAuthority,
};
use crate::runtime::{
    ExecutionProviderSnapshot, JobRunRequest, RuntimeExecutionPlan, RUNTIME_SCHEMA_VERSION,
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
        host_dependencies: Vec::new(),
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

mod credential;
mod immutable;
mod ordinary;
