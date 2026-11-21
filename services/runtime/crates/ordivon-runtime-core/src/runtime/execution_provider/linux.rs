//! Local Linux Runner provider: immutable source commitment, systemd launch, process observation.
use super::contract::{validate_provider_guarantees, ExecutionProviderGuarantees};
use crate::runtime::error::map_universal_error;
use crate::runtime::platform::{
    observe_linux_process_owner, systemd_run, validate_runner, SystemdRunSpec,
};
use crate::runtime::supervisor::{SupervisorIdentity, SupervisorObservation};
use crate::runtime::{
    AttemptRecord, ExecutionProfile, ExecutionProviderContract, ExecutionProviderSnapshot,
    ExecutionTarget, RuntimeError, RuntimeErrorCode, RuntimeExecutionPlan,
    RuntimeExecutionTargetCapability, RuntimeNodePlatform, RuntimeResult,
};
use crate::universal::{sha256_file, UniversalExecutorConfig};
use std::{path::Path, process::Output};

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

    pub(in crate::runtime::execution_provider) fn ensure_linux_node(&self) -> RuntimeResult<()> {
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
        let cargo_mount =
            crate::runtime::build_target_contract::requires_native_cargo_target_mount(plan).then(
                || {
                    self.executor
                        .workspace_build_cache_path(&plan.workspace_id)
                        .join("cargo")
                },
            );
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
