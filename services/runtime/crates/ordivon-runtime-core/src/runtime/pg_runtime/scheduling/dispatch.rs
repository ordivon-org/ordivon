//! Pending queue ranking, preflight, original reconciliation and dispatch.
use super::failure_policy::{decode_accepted_candidate, is_job_scoped_reconciliation_error};
use super::issue_writer::record_scheduler_issue;
use super::native_capacity::native_resource_error;
use super::policy::{next_candidate, PendingCandidate, SchedulerPreflight};
use super::{
    decode, io, json, JobCancelRequest, PgRuntime, RuntimeErrorCode, RuntimeExecutionPlan,
    RuntimeResult, PENDING_JOBS_SQL,
};
use crate::resource_scheduling::{
    NodeResources, ResourceRequest, ResourceScheduling, WorkspaceAccess,
};
use std::collections::BTreeMap;

impl PgRuntime {
    /// Resource-aware admission is independent of the caller's observation loop.
    /// Finite scan batches bound control-plane work, not running Job capacity.
    pub fn schedule_pending_jobs(&self) -> RuntimeResult<serde_json::Value> {
        let mut db = self.store()?;
        // Idle queue wakeups should not read host resources or every Allocation.
        let candidates = db.client.query(PENDING_JOBS_SQL, &[]).map_err(io)?;
        if candidates.is_empty() {
            return Ok(json!({"considered":0,"attempted":0}));
        }
        let node = NodeResources::observe().map_err(native_resource_error)?;
        let active = db
            .client
            .query(
                "SELECT x.owner,x.resources_json,x.attempt_id,x.workspace_access_json,j.workspace_id FROM job_allocations x JOIN attempts a ON a.attempt_id=x.attempt_id JOIN jobs j ON j.job_id=a.job_id WHERE x.state='active'",
                &[],
            )
            .map_err(io)?;
        let mut usage: BTreeMap<String, (u64, u64, u64)> = BTreeMap::new();
        let mut preflight = SchedulerPreflight::default();
        for row in active {
            let r: ResourceRequest = decode(&row.get::<_, String>(1))?;
            let access: WorkspaceAccess = decode(&row.get::<_, String>(3))?;
            let attempt_id: String = row.get(2);
            let workspace_id: String = row.get(4);
            preflight.active_attempts.insert(attempt_id);
            preflight.reserved_cpu = preflight
                .reserved_cpu
                .saturating_add(u64::from(r.cpu_millis));
            preflight
                .leases
                .entry(workspace_id)
                .or_default()
                .push(access);
            let v = usage.entry(row.get(0)).or_default();
            v.0 = v.0.saturating_add(u64::from(r.cpu_millis));
            v.1 = v.1.saturating_add(r.memory_bytes);
            v.2 = v.2.saturating_add(u64::from(r.pids));
        }
        // A single corrupted accepted plan must not poison unrelated healthy
        // Jobs. Admission normally validates plans; corruption here is
        // injected/stale state and must stay visible, never silently repaired.
        let mut ranked = Vec::with_capacity(candidates.len());
        for (order, row) in candidates.iter().enumerate() {
            let job: String = row.get(0);
            let attempt_id: String = row.get(3);
            let decoded: RuntimeResult<(RuntimeExecutionPlan, ResourceScheduling)> =
                decode_accepted_candidate(&row.get::<_, String>(2))
                    .and_then(|plan| self.scheduling_contract(&plan).map(|spec| (plan, spec)));
            let (plan, spec) = match decoded {
                Ok(decoded) => decoded,
                Err(error) => {
                    record_scheduler_issue(
                        self,
                        &mut db,
                        &job,
                        &attempt_id,
                        "SCHEDULER_CANDIDATE_INVALID",
                        &error,
                    )?;
                    continue;
                }
            };
            ranked.push(PendingCandidate {
                priority: spec.priority,
                order,
                job,
                principal: row.get(1),
                attempt_id,
                workspace_id: plan.workspace_id,
                spec,
            });
        }
        // Drop candidates that cannot fit this snapshot before repeated
        // priority/DRF rescoring. A new committed Allocation only tightens
        // the preflight; the inner loop must still recheck after each grant.
        preflight.retain_initially_feasible(&mut ranked, &node);
        let mut dispatched = 0_u32;
        while dispatched < 32 && !ranked.is_empty() {
            let Some(index) = next_candidate(&ranked, &usage, &node) else {
                break;
            };
            // FIFO is an explicit immutable order key, not vector position.
            let candidate = ranked.swap_remove(index);
            // Fast, side-effect-free rejection for known pressure, capacity
            // and Workspace conflicts. The PG transaction remains the only
            // authority that can actually grant a new Allocation.
            if !preflight.allows(&candidate, &node) {
                continue;
            }
            let PendingCandidate {
                job,
                principal,
                spec,
                attempt_id,
                workspace_id,
                ..
            } = candidate;
            self.authorize(&mut db, &job, &principal)?;
            let reconciled = match self.reconcile_inner(&mut db, &job, true) {
                Ok(()) => true,
                Err(error) if error.code == RuntimeErrorCode::AuthorizationDenied => {
                    // An original Harness source cut was definitively revoked
                    // after admission but BEFORE any DISPATCH_ISSUED event.
                    // Reuse the existing PG-fenced accepted cancellation and
                    // resource-release path; never poison unrelated Jobs or
                    // strand a permanent active Allocation on every retry.
                    // A PG/OS UNKNOWN is NOT an AuthorizationDenied result.
                    // Keep the reason separate from a user's cancel intent:
                    // existing Job consumers can trace why it was settled.
                    record_scheduler_issue(
                        self,
                        &mut db,
                        &job,
                        &attempt_id,
                        "HARNESS_ISSUER_NOT_CURRENT_AT_DISPATCH",
                        &error,
                    )?;
                    self.cancel(
                        &principal,
                        &JobCancelRequest {
                            schema_version: 1,
                            job_id: job.clone(),
                        },
                    )?;
                    false
                }
                Err(error) if is_job_scoped_reconciliation_error(&error) => {
                    record_scheduler_issue(
                        self,
                        &mut db,
                        &job,
                        &attempt_id,
                        "SCHEDULER_RECONCILIATION_BLOCKED",
                        &error,
                    )?;
                    false
                }
                // PostgreSQL/qualified-writer and node visibility errors are
                // global UNKNOWN, never normal per-Job resource deferrals.
                Err(error) => return Err(error),
            };
            if reconciled {
                let active: bool = db
                    .client
                    .query_one(
                        super::CONFIRMED_CURRENT_ALLOCATION_SQL,
                        &[&job, &attempt_id],
                    )
                    .map_err(io)?
                    .get(0);
                if active {
                    let confirmed = PendingCandidate {
                        priority: spec.priority,
                        order: 0,
                        job: job.clone(),
                        principal,
                        attempt_id,
                        workspace_id,
                        spec,
                    };
                    if preflight.record_allocation(&confirmed) {
                        let u = usage.entry(confirmed.spec.owner.clone()).or_default();
                        u.0 =
                            u.0.saturating_add(u64::from(confirmed.spec.resources.cpu_millis));
                        u.1 = u.1.saturating_add(confirmed.spec.resources.memory_bytes);
                        u.2 = u.2.saturating_add(u64::from(confirmed.spec.resources.pids));
                    }
                    dispatched += 1;
                }
            }
        }
        Ok(json!({"considered":candidates.len(),"attempted":dispatched}))
    }
}
