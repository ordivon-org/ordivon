//! Original provider contract and OS owner shape behavior tests.
use super::contract::{
    validate_provider_guarantees, ExecutionProviderGuarantees, ExecutionProviderSpi,
};
use crate::runtime::{
    AttemptRecord, ExecutionProviderContract, ExecutionProviderSnapshot, RuntimeExecutionPlan,
    RuntimeExecutionTargetCapability, RuntimeResult,
};
use crate::runtime::{
    ExecutionProfile, ExecutionTarget, WindowsExecutionContextRequest, WindowsExecutionIdentity,
    WindowsPayloadPrivilege,
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
        windows_privileged_profiles: Vec::new(),
        windows_maintenance_fence_configured: false,
        structured_plan: true,
        immutable_inputs: true,
        host_dependency_commitments: true,
        host_dependency_continuity_scope: Some("runtime_host_namespace_path_witness".to_string()),
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
        windows_privileged_profiles: Vec::new(),
        windows_maintenance_fence_configured: false,
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
    fn realize(&self, _: &RuntimeExecutionPlan, _: &AttemptRecord) -> RuntimeResult<Self::Owner> {
        unreachable!()
    }
    fn observe(&self, _: &Self::Owner) -> RuntimeResult<Self::Observation> {
        unreachable!()
    }
    fn cancel(&self, _: &Self::Owner) -> RuntimeResult<()> {
        unreachable!()
    }
    fn reconcile(&self, _: &Self::Owner, _: &Self::Evidence) -> RuntimeResult<Self::Observation> {
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
    fn realize(&self, _: &RuntimeExecutionPlan, _: &AttemptRecord) -> RuntimeResult<Self::Owner> {
        unreachable!()
    }
    fn observe(&self, _: &Self::Owner) -> RuntimeResult<Self::Observation> {
        unreachable!()
    }
    fn cancel(&self, _: &Self::Owner) -> RuntimeResult<()> {
        unreachable!()
    }
    fn reconcile(&self, _: &Self::Owner, _: &Self::Evidence) -> RuntimeResult<Self::Observation> {
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
