//! Original Linux provider capability, runner identity and invalid plan behavior tests.
use super::contract::ExecutionProviderSpi;
use super::linux::LocalLinuxProvider;
use crate::runtime::WindowsAuthority;
use crate::runtime::{
    AttemptRecord, ExecutionBudget, ExecutionProfile, ExecutionProviderContract, ExecutionTarget,
    RuntimeErrorCode, RuntimeExecutionPlan, RuntimeNodePlatform, RuntimeResult,
};
use crate::universal::{sha256_file, UniversalExecutorConfig};
use std::collections::BTreeMap;
use std::path::PathBuf;

fn executor(runner: Option<&str>) -> UniversalExecutorConfig {
    UniversalExecutorConfig {
        store_root: PathBuf::from("/tmp/ordivon-provider-adapter-test"),
        workspace_root: None,
        workspace_uid: None,
        workspace_gid: None,
        runner_path: runner.map(PathBuf::from),
        allowed_executable_roots: vec![PathBuf::from("/")],
        max_runtime_ms: 60_000,
        max_output_bytes: 1_048_576,
    }
}

fn plan(target: ExecutionTarget) -> RuntimeExecutionPlan {
    RuntimeExecutionPlan {
        schema_version: 1,
        workspace_id: "workspace:r10-a1".to_string(),
        workspace_path: "/tmp/workspace-r10-a1".to_string(),
        source_revision: "source-r10-a1".to_string(),
        workspace_source_digest: None,
        workspace_git_common_dir: None,
        executable: "/usr/bin/true".to_string(),
        executable_digest: format!("sha256:{}", "0".repeat(64)),
        args: Vec::new(),
        cwd: "/tmp/workspace-r10-a1".to_string(),
        env: BTreeMap::new(),
        timeout_ms: 1_000,
        stdout_limit_bytes: 1_024,
        stderr_limit_bytes: 1_024,
        steps: Vec::new(),
        budget: ExecutionBudget::default(),
        execution_profile: ExecutionProfile::TrustedLocal,
        execution_target: target,
        windows_authority: WindowsAuthority::Limited,
        windows_context: None,
        windows_execution_context: None,
        foreign_references: Vec::new(),
        host_dependencies: Vec::new(),
        input_set_id: None,
        effective_inputs: Vec::new(),
        credential_set_id: None,
        principal: "principal:r10-a1".to_string(),
    }
}

#[test]
fn local_linux_provider_fails_closed_off_linux_node() {
    let executor = executor(Some("/usr/bin/true"));
    let provider = LocalLinuxProvider::new(RuntimeNodePlatform::Windows, &executor);
    assert!(!provider.configured());
    let error = provider.snapshot().unwrap_err();
    assert_eq!(error.code, RuntimeErrorCode::ToolUnavailable);
}

#[test]
fn historical_linux_observation_admission_does_not_require_current_runner_configuration() {
    let executor = executor(None);
    let provider = LocalLinuxProvider::new(RuntimeNodePlatform::Linux, &executor);
    assert!(!provider.configured());
    provider.ensure_linux_node().unwrap();
}

#[test]
fn local_linux_provider_rejects_non_linux_plan_before_realization() {
    let executor = executor(Some("/usr/bin/true"));
    let provider = LocalLinuxProvider::new(RuntimeNodePlatform::Linux, &executor);
    let error = provider
        .validate_plan(&plan(ExecutionTarget::WindowsNative))
        .unwrap_err();
    assert_eq!(error.code, RuntimeErrorCode::InvalidRequest);
    assert_eq!(error.field.as_deref(), Some("execution.executionTarget"));
}

#[test]
fn local_linux_provider_snapshot_binds_exact_runner_digest() {
    // The CI host may expose /usr/bin/true as a symlink to a multicall
    // binary. The production contract correctly rejects runner symlinks;
    // a positive fixture must select the real, non-symlink executable.
    let real_runner = std::fs::canonicalize("/usr/bin/true").unwrap();
    let executor = executor(Some(real_runner.to_str().unwrap()));
    let provider = LocalLinuxProvider::new(RuntimeNodePlatform::Linux, &executor);
    provider
        .validate_plan(&plan(ExecutionTarget::LocalLinux))
        .unwrap();
    let snapshot = provider.snapshot().unwrap();
    assert_eq!(
        snapshot.contract,
        ExecutionProviderContract::LocalLinuxRunnerV1
    );
    assert_eq!(
        snapshot.executable_digest,
        sha256_file(&real_runner).unwrap()
    );
}

#[test]
fn local_linux_provider_rejects_symlink_runner_without_relaxing_contract() {
    use std::os::unix::fs::symlink;

    let real_runner = std::fs::canonicalize("/usr/bin/true").unwrap();
    let link = std::env::temp_dir().join(format!(
        "ordivon-provider-symlink-fixture-{}-{}",
        std::process::id(),
        uuid::Uuid::now_v7()
    ));
    symlink(&real_runner, &link).unwrap();
    let executor = executor(Some(link.to_str().unwrap()));
    let provider = LocalLinuxProvider::new(RuntimeNodePlatform::Linux, &executor);
    let result = provider.snapshot();
    std::fs::remove_file(&link).unwrap();
    let error = result.unwrap_err();
    assert_eq!(error.code, RuntimeErrorCode::InvalidRequest);
    assert_eq!(error.field.as_deref(), Some("runnerPath"));
}

#[test]
fn native_formal_execution_provider_spi_contract() {
    // The generic body is typechecked against the SPI contract even
    // before choosing any concrete Linux/Windows implementation.
    #[allow(dead_code)]
    fn check<T: ExecutionProviderSpi>() {
        let _: fn(&T, &RuntimeExecutionPlan, &AttemptRecord) -> RuntimeResult<T::Owner> =
            T::realize;
    }
}
