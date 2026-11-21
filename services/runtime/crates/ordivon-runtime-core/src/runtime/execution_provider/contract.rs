//! Provider guarantee and static typed SPI; no OS action or DB state.
use crate::runtime::{
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
