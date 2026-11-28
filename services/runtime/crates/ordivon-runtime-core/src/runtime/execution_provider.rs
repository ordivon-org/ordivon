//! Internal execution-provider assume/guarantee seam.
//!
//! R09 freezes the obligations that Linux and Windows provider adapters must satisfy before
//! either OS-specific implementation is extracted from `Runtime`. This is deliberately not a
//! plugin registry or dynamic provider marketplace: provider selection remains statically owned
//! by Runtime and committed provider identity remains persisted in `ExecutionProviderSnapshot`.

use super::error::map_universal_error;
use super::platform::{observe_linux_process_owner, systemd_run, validate_runner, SystemdRunSpec};
use super::supervisor::{SupervisorIdentity, SupervisorObservation};
use super::{
    AttemptRecord, ExecutionProfile, ExecutionProviderContract, ExecutionProviderSnapshot,
    ExecutionTarget, RuntimeError, RuntimeErrorCode, RuntimeExecutionPlan,
    RuntimeExecutionTargetCapability, RuntimeNodePlatform, RuntimeResult,
};
use crate::universal::{sha256_file, UniversalExecutorConfig};
use std::path::Path;
use std::process::Output;

/// Current Local Linux provider descriptor/admission adapter.
///
/// R10-A1 moves Linux capability, immutable provider commitment, and plan-target validation out of
/// Engine's OS branch. Physical materialization remains owned by Runtime; later R10 slices move
/// systemd realization/observation/cancellation/reconciliation behind the SPI without weakening
/// late-evidence recovery semantics.
pub(crate) struct LocalLinuxProvider<'a> {
    node_platform: RuntimeNodePlatform,
    executor: &'a UniversalExecutorConfig,
}

pub(crate) struct LocalLinuxRealizationInputs<'a> {
    pub(crate) bundle_path: &'a Path,
    pub(crate) input_set_path: Option<&'a Path>,
    pub(crate) credential_source_root: Option<&'a Path>,
    pub(crate) credential_names: &'a [String],
}

/// Physical Linux supervisor observation bound to the persisted Attempt owner identity.
/// Runtime retains recovery classification and terminal-state authority; the provider only reads
/// the current OS facts needed for that classification.
pub(crate) struct LocalLinuxBoundObservation {
    pub(crate) expected: SupervisorIdentity,
    pub(crate) observed: SupervisorObservation,
}

impl<'a> LocalLinuxProvider<'a> {
    pub(crate) fn new(
        node_platform: RuntimeNodePlatform,
        executor: &'a UniversalExecutorConfig,
    ) -> Self {
        Self {
            node_platform,
            executor,
        }
    }

    fn ensure_linux_node(&self) -> RuntimeResult<()> {
        if self.node_platform != RuntimeNodePlatform::Linux {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ToolUnavailable,
                "local_linux execution is available only on a Linux Runtime node",
                Some("execution.executionTarget"),
                false,
            ));
        }
        Ok(())
    }

    pub(crate) fn configured(&self) -> bool {
        self.node_platform == RuntimeNodePlatform::Linux && self.executor.runner_path.is_some()
    }

    pub(crate) fn snapshot(&self) -> RuntimeResult<ExecutionProviderSnapshot> {
        self.ensure_linux_node()?;
        let runner_path = self.executor.runner_path.as_deref().ok_or_else(|| {
            RuntimeError::new(
                RuntimeErrorCode::ToolUnavailable,
                "local_linux runner is not configured on this Runtime node",
                Some("runnerPath"),
                false,
            )
        })?;
        let runner = validate_runner(runner_path)?;
        Ok(ExecutionProviderSnapshot {
            contract: ExecutionProviderContract::LocalLinuxRunnerV1,
            executable_digest: sha256_file(&runner).map_err(map_universal_error)?,
            wsl_distribution: None,
        })
    }

    pub(crate) fn capabilities(&self) -> RuntimeExecutionTargetCapability {
        let configured = self.configured();
        let provider = configured
            .then(|| self.snapshot())
            .transpose()
            .ok()
            .flatten();
        RuntimeExecutionTargetCapability {
            target: ExecutionTarget::LocalLinux,
            configured,
            available: provider.is_some(),
            execution_profiles: if configured {
                vec![
                    ExecutionProfile::TrustedLocal,
                    ExecutionProfile::ContainedLocal,
                ]
            } else {
                Vec::new()
            },
            windows_authorities: Vec::new(),
            windows_contexts: Vec::new(),
            windows_immutable_input_authorities: Vec::new(),
            windows_privileged_profiles: Vec::new(),
            windows_maintenance_fence_configured: false,
            structured_plan: configured,
            immutable_inputs: configured,
            host_dependency_commitments: configured,
            host_dependency_continuity_scope: configured
                .then(|| "runtime_host_namespace_path_witness".to_string()),
            execution_provider: provider.clone(),
            availability_issue: (configured && provider.is_none())
                .then(|| "EXECUTION_PROVIDER_UNAVAILABLE".to_string()),
        }
    }

    pub(crate) fn validate_plan(&self, plan: &RuntimeExecutionPlan) -> RuntimeResult<()> {
        if plan.execution_target != ExecutionTarget::LocalLinux {
            return Err(RuntimeError::invalid(
                "LocalLinuxProvider received a non-local_linux execution plan",
                "execution.executionTarget",
            ));
        }
        let _ = self.snapshot()?;
        Ok(())
    }

    pub(crate) fn realize_prepared(
        &self,
        plan: &RuntimeExecutionPlan,
        attempt: &AttemptRecord,
        inputs: LocalLinuxRealizationInputs<'_>,
    ) -> RuntimeResult<Output> {
        self.validate_plan(plan)?;
        let runner_path = self.executor.runner_path.as_deref().ok_or_else(|| {
            RuntimeError::new(
                RuntimeErrorCode::ToolUnavailable,
                "local_linux runner is not configured on this Runtime node",
                Some("runnerPath"),
                false,
            )
        })?;
        let runner = validate_runner(runner_path)?;
        let cargo_mount = super::build_target_contract::requires_native_cargo_target_mount(plan)
            .then(|| {
                self.executor
                    .workspace_build_cache_path(&plan.workspace_id)
                    .join("cargo")
            });
        systemd_run(&SystemdRunSpec {
            unit_name: &attempt.unit_name,
            runner: &runner,
            bundle_path: inputs.bundle_path,
            workspace_path: Path::new(&plan.workspace_path),
            workspace_git_common_dir: plan.workspace_git_common_dir.as_deref().map(Path::new),
            cargo_target_mount: cargo_mount.as_deref(),
            input_set_path: inputs.input_set_path,
            credential_source_root: inputs.credential_source_root,
            credential_names: inputs.credential_names,
            runtime_ceiling_ms: plan.timeout_ms.saturating_add(5_000),
            budget: &plan.budget,
            execution_profile: plan.execution_profile,
            environment: &plan.env,
        })
    }

    /// Read physical supervisor state for one persisted Linux Attempt.
    ///
    /// Observation deliberately does not require the currently configured Runner to exist or
    /// match the historical provider snapshot. Crash/restart recovery must remain able to inspect
    /// an already-owned Attempt after provider configuration drift.
    pub(crate) fn observe_bound_attempt(
        &self,
        attempt: &AttemptRecord,
    ) -> RuntimeResult<LocalLinuxBoundObservation> {
        self.ensure_linux_node()?;
        let (expected, observed) = observe_linux_process_owner(attempt)?;
        Ok(LocalLinuxBoundObservation { expected, observed })
    }
}

#[cfg(test)]
mod local_linux_adapter_tests {
    use super::*;
    use crate::runtime::{ExecutionBudget, WindowsAuthority};
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

    #[cfg(unix)]
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
    fn native_formal_runner_path_guard_rejects_directory_and_missing_runner() {
        // PG admission/recovery/describe and the historical provider snapshot
        // use the same actual filesystem guard. This is not an OS launch proof.
        let directory = tempfile::tempdir().unwrap();
        let missing = directory.path().join("missing-runner");
        let real_runner = std::fs::canonicalize(std::env::current_exe().unwrap()).unwrap();
        assert_eq!(validate_runner(&real_runner).unwrap(), real_runner);
        for path in [directory.path(), missing.as_path()] {
            assert!(validate_runner(path).is_err());
            let config = executor(Some(path.to_str().unwrap()));
            let provider = LocalLinuxProvider::new(RuntimeNodePlatform::Linux, &config);
            assert!(provider.snapshot().is_err());
        }
        let config = executor(None);
        let provider = LocalLinuxProvider::new(RuntimeNodePlatform::Linux, &config);
        assert_eq!(
            provider
                .validate_plan(&plan(ExecutionTarget::LocalLinux))
                .unwrap_err()
                .code,
            RuntimeErrorCode::ToolUnavailable
        );
    }
}
