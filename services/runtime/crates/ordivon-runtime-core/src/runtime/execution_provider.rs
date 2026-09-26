//! Internal execution-provider assume/guarantee seam.
//!
//! R09 freezes the obligations that Linux and Windows provider adapters must satisfy before
//! either OS-specific implementation is extracted from `Runtime`. This is deliberately not a
//! plugin registry or dynamic provider marketplace: provider selection remains statically owned
//! by Runtime and committed provider identity remains persisted in `ExecutionProviderSnapshot`.

use super::{
    AttemptRecord, ExecutionProviderContract, ExecutionProviderSnapshot, RuntimeError,
    RuntimeExecutionPlan, RuntimeExecutionTargetCapability, RuntimeResult,
};

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
