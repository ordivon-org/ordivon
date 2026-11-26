/// Independently launched fresh-PG MCP adapter. The SQLite Engine is never constructed.
/// Operator-owned release configuration; never supplied in MCP request JSON.
#[derive(Clone, Debug)]
pub struct PgReleaseOperatorConfig {
    pub source_repo: PathBuf,
    pub operator_executable: PathBuf,
    pub receipt_root: PathBuf,
    /// The independent systemd timer is a durable consumer of accepted effects.
    pub dispatcher_timer: String,
}

use pg_runtime_ingress::{
    ClaimReleaseIngress, CLAIM_ONLY_TOOL_NAMES, claim_only_route_guard,
    claim_release_route_guard, profile_omitted_from_raw_tool_arguments,
    project_ingress_execution_profiles, restrict_new_effect_catalog,
    run_pg_direct_implicit_profile,
};

#[path = "pg_server/ingress.rs"]
mod pg_runtime_ingress;
#[path = "pg_server/catalog.rs"]
mod pg_runtime_catalog;
#[path = "pg_server/dispatch.rs"]
mod pg_runtime_dispatch;
#[path = "pg_server/protocol.rs"]
mod pg_runtime_protocol;
#[cfg(test)]
#[path = "pg_server/tests.rs"]
mod pg_runtime_contract_tests;

#[derive(Clone)]
pub struct PgRuntimeServer {
    runtime: ordivon_runtime_core::PgRuntime,
    execution: ExecutionContext,
    release: Option<PgReleaseOperatorConfig>,
    // The ordinary execution bearer is not authority to relinquish another
    // domain's still-held Workspace. The protected Harness/Finalizer route
    // alone may expose the original principal-scoped release operation.
    claim_release_ingress: ClaimReleaseIngress,
    // Authentication-bound NEW-Job policy, never a tools/call argument.
    // Core performs historical exact-key recovery before this check.
    required_new_execution_profile: Option<ExecutionProfile>,
}

impl PgRuntimeServer {
    pub fn new(runtime: ordivon_runtime_core::PgRuntime, execution: ExecutionContext) -> Self {
        Self {
            runtime,
            execution,
            release: None,
            claim_release_ingress: ClaimReleaseIngress::Ordinary,
            required_new_execution_profile: None,
        }
    }
    pub fn with_release(
        runtime: ordivon_runtime_core::PgRuntime,
        execution: ExecutionContext,
        release: Option<PgReleaseOperatorConfig>,
    ) -> Self {
        Self {
            runtime,
            execution,
            release,
            claim_release_ingress: ClaimReleaseIngress::Ordinary,
            required_new_execution_profile: None,
        }
    }
    /// This is ONLY called for a separately authenticated Harness ingress.
    /// Authentication permits original Job/Claim operations, not releasing an
    /// original Run's physical pin. Domain complete-receiver and all-issued
    /// native OS finalization remain unimplemented, so raw release is denied.
    /// A distinct principal must never inherit a prior HELD Claim.
    pub fn for_authenticated_harness_finalizer(mut self) -> Self {
        self.claim_release_ingress = ClaimReleaseIngress::DedicatedFinalizer;
        self
    }

    /// A separately authenticated Claim owner may reserve/read original
    /// physical pins, not execute, cancel, release, or close. A bearer alone
    /// is not proof of original recipient bytes or Native NoFutureSpawn.
    pub fn for_authenticated_claim_only_finalizer(mut self) -> Self {
        self.claim_release_ingress = ClaimReleaseIngress::DedicatedClaimOnly;
        self
    }

    /// Operator-selected ordinary Agent ingress. An authenticated caller
    /// cannot upgrade a new contained Job by supplying trusted_local in JSON.
    /// The old trusted operator ingress remains the default until cutover.
    pub fn restrict_ordinary_jobs_to_contained(mut self) -> Self {
        self.required_new_execution_profile = Some(ExecutionProfile::ContainedLocal);
        self
    }

    fn require_claim_release_authority(&self, name: &str) -> Result<(), McpError> {
        claim_release_route_guard(self.claim_release_ingress.may_release(), name)
    }

}
