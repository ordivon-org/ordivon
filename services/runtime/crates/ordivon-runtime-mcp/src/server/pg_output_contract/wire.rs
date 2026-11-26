//! Typed native PG scheduling state: unknown placement is not invented pressure.
use ordivon_runtime_core::resource_scheduling::ResourceScheduling;
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub(super) enum PgJobSchedulingState {
    Pending,
    Allocated,
    Released,
}

#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub(super) enum PgSchedulingPendingReason {
    /// No durable placement-failure cause is recorded. Do not turn unknown
    /// capacity, cgroup observation, or Workspace contention into a claim.
    CauseUnobserved,
}

#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(super) struct PgJobSchedulingReadback {
    state: PgJobSchedulingState,
    request: ResourceScheduling,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pending_reason: Option<PgSchedulingPendingReason>,
}
