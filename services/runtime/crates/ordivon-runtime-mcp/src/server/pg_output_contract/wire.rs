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

/// Committed PG allocation timestamps for the same exact Attempt. Not
/// physical start/stop or a reason for waiting in the admission queue.
#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct PgAllocationObservation {
    attempt_id: String,
    acquired_at_ms: u64,
    released_at_ms: Option<u64>,
}

#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(super) struct PgJobSchedulingReadback {
    state: PgJobSchedulingState,
    request: ResourceScheduling,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pending_reason: Option<PgSchedulingPendingReason>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    allocation_observation: Option<PgAllocationObservation>,
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn exact_pg_allocation_observation_remains_optional_and_typed() {
        let request = serde_json::to_value(ResourceScheduling::default()).unwrap();
        let old = json!({"state": "released", "request": request});
        let typed: PgJobSchedulingReadback = serde_json::from_value(old.clone()).unwrap();
        assert_eq!(serde_json::to_value(typed).unwrap(), old);
        let allocation = json!({
            "state": "released", "request": request,
            "allocationObservation": {"attemptId":"a","acquiredAtMs":100,"releasedAtMs":150}
        });
        let typed: PgJobSchedulingReadback = serde_json::from_value(allocation.clone()).unwrap();
        assert_eq!(serde_json::to_value(typed).unwrap(), allocation);
        let mut invalid = allocation.clone();
        invalid["allocationObservation"]["acquiredAtMs"] = json!(-1);
        assert!(serde_json::from_value::<PgJobSchedulingReadback>(invalid).is_err());
        let mut foreign = allocation;
        foreign["allocationObservation"]["inventedProof"] = json!(true);
        assert!(serde_json::from_value::<PgJobSchedulingReadback>(foreign).is_err());
        let schema = serde_json::to_value(schemars::schema_for!(PgJobSchedulingReadback)).unwrap();
        assert_eq!(schema["additionalProperties"], false);
        assert!(schema["properties"]["allocationObservation"].is_object());
        assert!(!schema["required"].as_array().unwrap().contains(&json!("allocationObservation")));
        assert_eq!(schema["$defs"]["PgAllocationObservation"]["additionalProperties"], false);
    }
}
