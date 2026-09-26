//! Internal execution-provider assume/guarantee seam.
//!
//! R09 freezes the obligations that Linux and Windows provider adapters must satisfy before
//! either OS-specific implementation is extracted from `Runtime`. This is deliberately not a
//! plugin registry or dynamic provider marketplace: provider selection remains statically owned
//! by Runtime and committed provider identity remains persisted in `ExecutionProviderSnapshot`.

use super::engine::map_universal_error;
use super::platform::{systemd_run, validate_runner, SystemdRunSpec};
use super::{
    AttemptRecord, ExecutionProfile, ExecutionProviderContract, ExecutionProviderSnapshot,
    ExecutionTarget, RuntimeError, RuntimeErrorCode, RuntimeExecutionPlan,
    RuntimeExecutionTargetCapability, RuntimeNodePlatform, RuntimeResult,
};
use crate::universal::{sha256_file, UniversalExecutorConfig};
use std::path::Path;
use std::process::Output;

/// Guarantees every R1 execution provider must preserve. A later provider replacement may add
/// stronger internal mechanisms, but it may not weaken any of these obligations.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) struct ExecutionProviderGuarantees {
    pub exact_committed_provider_identity: bool,
    pub single_physical_attempt_owner: bool,
    pub terminal_observation: bool,
    pub process_tree_cancellation: bool,
    pub crash_restart_reconciliation: bool,
    pub scoped_evidence: bool,
}

impl ExecutionProviderGuarantees {
    pub(crate) const REQUIRED_R1: Self = Self {
        exact_committed_provider_identity: true,
        single_physical_attempt_owner: true,
        terminal_observation: true,
        process_tree_cancellation: true,
        crash_restart_reconciliation: true,
        scoped_evidence: true,
    };
}

/// Fail closed if a proposed provider adapter weakens an R1 guarantee. This validation is kept
/// independent from OS mechanism so Local Linux and Windows Native can use different ownership
/// and evidence types while satisfying the same Runtime-level contract.
pub(crate) fn validate_provider_guarantees(
    guarantees: ExecutionProviderGuarantees,
) -> RuntimeResult<()> {
    let required = ExecutionProviderGuarantees::REQUIRED_R1;
    if guarantees != required {
        return Err(RuntimeError::invalid(
            "execution provider does not satisfy the complete R1 assume/guarantee contract",
            "executionProvider",
        ));
    }
    Ok(())
}

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

    pub(crate) fn configured(&self) -> bool {
        self.node_platform == RuntimeNodePlatform::Linux && self.executor.runner_path.is_some()
    }

    pub(crate) fn snapshot(&self) -> RuntimeResult<ExecutionProviderSnapshot> {
        if self.node_platform != RuntimeNodePlatform::Linux {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ToolUnavailable,
                "local_linux execution is available only on a Linux Runtime node",
                Some("execution.executionTarget"),
                false,
            ));
        }
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
        validate_provider_guarantees(ExecutionProviderGuarantees::REQUIRED_R1)?;
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
        systemd_run(&SystemdRunSpec {
            unit_name: &attempt.unit_name,
            runner: &runner,
            bundle_path: inputs.bundle_path,
            workspace_path: Path::new(&plan.workspace_path),
            workspace_git_common_dir: plan.workspace_git_common_dir.as_deref().map(Path::new),
            input_set_path: inputs.input_set_path,
            credential_source_root: inputs.credential_source_root,
            credential_names: inputs.credential_names,
            runtime_ceiling_ms: plan.timeout_ms.saturating_add(5_000),
            budget: &plan.budget,
            execution_profile: plan.execution_profile,
            environment: &plan.env,
        })
    }
}

/// Static, internal SPI for physical execution providers.
///
/// Associated owner/observation/evidence types are intentional: the SPI shares obligations, not
/// Linux systemd or Windows Job Object implementation shape. R10/R11 will move current physical
/// mechanisms behind this seam without changing public Tool schemas or adding dynamic discovery.
pub(crate) trait ExecutionProviderSpi {
    type Owner;
    type Observation;
    type Evidence;

    fn contract(&self) -> ExecutionProviderContract;
    fn guarantees(&self) -> ExecutionProviderGuarantees;
    fn capabilities(&self) -> RuntimeResult<RuntimeExecutionTargetCapability>;
    fn snapshot(&self) -> RuntimeResult<ExecutionProviderSnapshot>;
    fn validate(&self, plan: &RuntimeExecutionPlan) -> RuntimeResult<()>;
    fn realize(
        &self,
        plan: &RuntimeExecutionPlan,
        attempt: &AttemptRecord,
    ) -> RuntimeResult<Self::Owner>;
    fn observe(&self, owner: &Self::Owner) -> RuntimeResult<Self::Observation>;
    fn cancel(&self, owner: &Self::Owner) -> RuntimeResult<()>;
    fn reconcile(
        &self,
        owner: &Self::Owner,
        evidence: &Self::Evidence,
    ) -> RuntimeResult<Self::Observation>;
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::runtime::{
        ExecutionProfile, ExecutionTarget, WindowsExecutionContextRequest,
        WindowsExecutionIdentity, WindowsPayloadPrivilege,
    };

    #[derive(Clone, Debug, Eq, PartialEq)]
    struct LinuxOwner {
        unit_name: String,
    }

    #[derive(Clone, Debug, Eq, PartialEq)]
    struct WindowsOwner {
        job_name: String,
        launcher_pid: u32,
    }

    struct LinuxContractProbe;
    struct WindowsContractProbe;

    fn linux_capability() -> RuntimeExecutionTargetCapability {
        RuntimeExecutionTargetCapability {
            target: ExecutionTarget::LocalLinux,
            configured: true,
            available: true,
            execution_profiles: vec![
                ExecutionProfile::TrustedLocal,
                ExecutionProfile::ContainedLocal,
            ],
            windows_authorities: Vec::new(),
            windows_contexts: Vec::new(),
            windows_immutable_input_authorities: Vec::new(),
            structured_plan: true,
            immutable_inputs: true,
            host_dependency_commitments: true,
            host_dependency_continuity_scope: Some(
                "runtime_host_namespace_path_witness".to_string(),
            ),
            execution_provider: None,
            availability_issue: None,
        }
    }

    fn windows_capability() -> RuntimeExecutionTargetCapability {
        RuntimeExecutionTargetCapability {
            target: ExecutionTarget::WindowsNative,
            configured: true,
            available: true,
            execution_profiles: vec![ExecutionProfile::TrustedLocal],
            windows_authorities: Vec::new(),
            windows_contexts: vec![WindowsExecutionContextRequest::new(
                WindowsExecutionIdentity::Service,
                WindowsPayloadPrivilege::Limited,
            )],
            windows_immutable_input_authorities: Vec::new(),
            structured_plan: false,
            immutable_inputs: true,
            host_dependency_commitments: false,
            host_dependency_continuity_scope: None,
            execution_provider: None,
            availability_issue: None,
        }
    }

    impl ExecutionProviderSpi for LinuxContractProbe {
        type Owner = LinuxOwner;
        type Observation = &'static str;
        type Evidence = &'static str;

        fn contract(&self) -> ExecutionProviderContract {
            ExecutionProviderContract::LocalLinuxRunnerV1
        }
        fn guarantees(&self) -> ExecutionProviderGuarantees {
            ExecutionProviderGuarantees::REQUIRED_R1
        }
        fn capabilities(&self) -> RuntimeResult<RuntimeExecutionTargetCapability> {
            Ok(linux_capability())
        }
        fn snapshot(&self) -> RuntimeResult<ExecutionProviderSnapshot> {
            unreachable!()
        }
        fn validate(&self, _: &RuntimeExecutionPlan) -> RuntimeResult<()> {
            unreachable!()
        }
        fn realize(
            &self,
            _: &RuntimeExecutionPlan,
            _: &AttemptRecord,
        ) -> RuntimeResult<Self::Owner> {
            unreachable!()
        }
        fn observe(&self, _: &Self::Owner) -> RuntimeResult<Self::Observation> {
            unreachable!()
        }
        fn cancel(&self, _: &Self::Owner) -> RuntimeResult<()> {
            unreachable!()
        }
        fn reconcile(
            &self,
            _: &Self::Owner,
            _: &Self::Evidence,
        ) -> RuntimeResult<Self::Observation> {
            unreachable!()
        }
    }

    impl ExecutionProviderSpi for WindowsContractProbe {
        type Owner = WindowsOwner;
        type Observation = u32;
        type Evidence = Vec<u8>;

        fn contract(&self) -> ExecutionProviderContract {
            ExecutionProviderContract::WindowsNativeLauncherV1
        }
        fn guarantees(&self) -> ExecutionProviderGuarantees {
            ExecutionProviderGuarantees::REQUIRED_R1
        }
        fn capabilities(&self) -> RuntimeResult<RuntimeExecutionTargetCapability> {
            Ok(windows_capability())
        }
        fn snapshot(&self) -> RuntimeResult<ExecutionProviderSnapshot> {
            unreachable!()
        }
        fn validate(&self, _: &RuntimeExecutionPlan) -> RuntimeResult<()> {
            unreachable!()
        }
        fn realize(
            &self,
            _: &RuntimeExecutionPlan,
            _: &AttemptRecord,
        ) -> RuntimeResult<Self::Owner> {
            unreachable!()
        }
        fn observe(&self, _: &Self::Owner) -> RuntimeResult<Self::Observation> {
            unreachable!()
        }
        fn cancel(&self, _: &Self::Owner) -> RuntimeResult<()> {
            unreachable!()
        }
        fn reconcile(
            &self,
            _: &Self::Owner,
            _: &Self::Evidence,
        ) -> RuntimeResult<Self::Observation> {
            unreachable!()
        }
    }

    #[test]
    fn linux_and_windows_share_obligations_without_sharing_owner_shape() {
        let linux = LinuxContractProbe;
        let windows = WindowsContractProbe;
        assert_eq!(
            linux.contract(),
            ExecutionProviderContract::LocalLinuxRunnerV1
        );
        assert_eq!(
            windows.contract(),
            ExecutionProviderContract::WindowsNativeLauncherV1
        );
        validate_provider_guarantees(linux.guarantees()).unwrap();
        validate_provider_guarantees(windows.guarantees()).unwrap();
        assert_eq!(
            linux.capabilities().unwrap().target,
            ExecutionTarget::LocalLinux
        );
        assert_eq!(
            windows.capabilities().unwrap().target,
            ExecutionTarget::WindowsNative
        );
        let _: Option<LinuxOwner> = None;
        let _: Option<WindowsOwner> = None;
    }

    #[test]
    fn provider_replacement_cannot_weaken_r1_guarantees() {
        let weakened = ExecutionProviderGuarantees {
            crash_restart_reconciliation: false,
            ..ExecutionProviderGuarantees::REQUIRED_R1
        };
        let error = validate_provider_guarantees(weakened).unwrap_err();
        assert_eq!(error.field.as_deref(), Some("executionProvider"));
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
        let executor = executor(Some("/usr/bin/true"));
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
            sha256_file(std::path::Path::new("/usr/bin/true")).unwrap()
        );
    }
}
