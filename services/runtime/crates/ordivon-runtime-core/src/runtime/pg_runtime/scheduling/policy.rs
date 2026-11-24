//! Pure, advisory scheduling policy: fairness and pressure screening.
//! Actual allocation authority remains PostgreSQL `claim_resources`.
use crate::resource_scheduling::{NodeResources, ResourceScheduling, WorkspaceAccess};
use serde_json::json;
use std::collections::{BTreeMap, BTreeSet};

/// Immutable PG candidate snapshot. Dominant shares are rescored after every
/// successful allocation; execution plans need not be queried or decoded again.
pub(super) struct PendingCandidate {
    pub(super) priority: i16,
    pub(super) order: usize,
    pub(super) job: String,
    pub(super) principal: String,
    pub(super) attempt_id: String,
    pub(super) workspace_id: String,
    pub(super) spec: ResourceScheduling,
}

/// An advisory snapshot for rejecting candidates that definitively cannot
/// fit the observed resources or conflict with an already committed lease.
/// This is never allocation authority: claim_resources rechecks PostgreSQL
/// under its existing transaction lock before admitting any new Attempt.
#[derive(Default)]
pub(super) struct SchedulerPreflight {
    pub(super) reserved_cpu: u64,
    // Claims made after the single native node observation this scheduling
    // pass are not yet reflected in MemAvailable / pids.current. Existing
    // allocations are already included in that OS observation and must not
    // be charged again here.
    pub(super) newly_reserved_memory: u64,
    pub(super) newly_reserved_pids: u64,
    pub(super) active_attempts: BTreeSet<String>,
    pub(super) leases: BTreeMap<String, Vec<WorkspaceAccess>>,
}

impl SchedulerPreflight {
    pub(super) fn allows(&self, candidate: &PendingCandidate, node: &NodeResources) -> bool {
        // An accepted Attempt may already hold a durable Allocation across a
        // crash/restart. Let the existing idempotent claim resume that exact
        // Attempt; its own CPU and Workspace lease must not block recovery.
        if self.active_attempts.contains(&candidate.attempt_id) {
            return true;
        }
        if !node.pressure_allows(&candidate.spec.resources) {
            return false;
        }
        let memory_reserve = (node.memory_total_bytes / 20).max(64 * 1024 * 1024);
        if !crate::resource_fit::fits(
            self.reserved_cpu,
            u64::from(candidate.spec.resources.cpu_millis),
            node.cpu_millis,
            candidate.spec.resources.memory_bytes,
            node.memory_available_bytes
                .saturating_sub(memory_reserve)
                .saturating_sub(self.newly_reserved_memory),
            u64::from(candidate.spec.resources.pids),
            node.pids_available
                .saturating_sub(64)
                .saturating_sub(self.newly_reserved_pids),
        ) {
            return false;
        }
        !self
            .leases
            .get(&candidate.workspace_id)
            .is_some_and(|active| {
                active
                    .iter()
                    .any(|lease| lease.conflicts(&candidate.spec.workspace_access))
            })
    }

    /// One-pass filter of candidates already known to be infeasible in the
    /// current immutable native/PG snapshot. Subsequent allocations can only
    /// tighten this preflight; final authority remains the PG claim.
    pub(super) fn retain_initially_feasible(
        &self,
        candidates: &mut Vec<PendingCandidate>,
        node: &NodeResources,
    ) {
        candidates.retain(|candidate| self.allows(candidate, node));
    }

    pub(super) fn record_allocation(&mut self, candidate: &PendingCandidate) -> bool {
        if !self.active_attempts.insert(candidate.attempt_id.clone()) {
            return false;
        }
        self.reserved_cpu = self
            .reserved_cpu
            .saturating_add(u64::from(candidate.spec.resources.cpu_millis));
        self.newly_reserved_memory = self
            .newly_reserved_memory
            .saturating_add(candidate.spec.resources.memory_bytes);
        self.newly_reserved_pids = self
            .newly_reserved_pids
            .saturating_add(u64::from(candidate.spec.resources.pids));
        self.leases
            .entry(candidate.workspace_id.clone())
            .or_default()
            .push(candidate.spec.workspace_access.clone());
        true
    }
}

fn dominant_share(
    owner: &str,
    usage: &BTreeMap<String, (u64, u64, u64)>,
    node: &NodeResources,
) -> f64 {
    let (cpu, memory, pids) = usage.get(owner).copied().unwrap_or_default();
    (cpu as f64 / node.cpu_millis.max(1) as f64)
        .max(memory as f64 / node.memory_total_bytes.max(1) as f64)
        .max(pids as f64 / node.pid_capacity.max(1) as f64)
}

/// Highest priority, then lowest live dominant share, then FIFO order.
pub(super) fn next_candidate(
    candidates: &[PendingCandidate],
    usage: &BTreeMap<String, (u64, u64, u64)>,
    node: &NodeResources,
) -> Option<usize> {
    candidates
        .iter()
        .enumerate()
        .min_by(|(_, a), (_, b)| {
            b.priority
                .cmp(&a.priority)
                .then_with(|| {
                    dominant_share(&a.spec.owner, usage, node).total_cmp(&dominant_share(
                        &b.spec.owner,
                        usage,
                        node,
                    ))
                })
                .then_with(|| a.order.cmp(&b.order))
        })
        .map(|(index, _)| index)
}

// Testable projection: there is no durable, cause-specific placement
// result in PG, so readback must not pretend to know why Allocation waits.
pub(in super::super) fn scheduling_readback(
    request: ResourceScheduling,
    attempt_state: Option<&str>,
    desired_state: &str,
    resolution: Option<&str>,
    allocated: bool,
) -> serde_json::Value {
    let pending = attempt_state == Some("accepted")
        && desired_state == "run"
        && resolution.is_none()
        && !allocated;
    json!({
        "state": if allocated {"allocated"} else if pending {"pending"} else {"released"},
        "request": request,
        "pendingReason": if pending {Some("cause_unobserved")} else {None}
    })
}
