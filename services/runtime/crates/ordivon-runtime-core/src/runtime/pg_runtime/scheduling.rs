//! Durable pending work, atomic native allocation and fair dispatch.
use super::*;
use crate::resource_scheduling::{
    NodeResources, ResourceRequest, ResourceScheduling, WorkspaceAccess,
};
use std::collections::{BTreeMap, BTreeSet};

/// Immutable PG candidate snapshot. Dominant shares are rescored after every
/// successful allocation; execution plans need not be queried or decoded again.
struct PendingCandidate {
    priority: i16,
    order: usize,
    job: String,
    principal: String,
    attempt_id: String,
    workspace_id: String,
    spec: ResourceScheduling,
}

/// An advisory snapshot for rejecting candidates that definitively cannot
/// fit the observed resources or conflict with an already committed lease.
/// This is never allocation authority: claim_resources rechecks PostgreSQL
/// under its existing transaction lock before admitting any new Attempt.
#[derive(Default)]
struct SchedulerPreflight {
    reserved_cpu: u64,
    // Claims made after the single native node observation this scheduling
    // pass are not yet reflected in MemAvailable / pids.current. Existing
    // allocations are already included in that OS observation and must not
    // be charged again here.
    newly_reserved_memory: u64,
    newly_reserved_pids: u64,
    active_attempts: BTreeSet<String>,
    leases: BTreeMap<String, Vec<WorkspaceAccess>>,
}

impl SchedulerPreflight {
    fn allows(&self, candidate: &PendingCandidate, node: &NodeResources) -> bool {
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
    fn retain_initially_feasible(
        &self,
        candidates: &mut Vec<PendingCandidate>,
        node: &NodeResources,
    ) {
        candidates.retain(|candidate| self.allows(candidate, node));
    }

    fn record_allocation(&mut self, candidate: &PendingCandidate) -> bool {
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
fn next_candidate(
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

impl PgRuntime {
    pub(super) fn scheduling_contract(
        &self,
        plan: &RuntimeExecutionPlan,
    ) -> RuntimeResult<ResourceScheduling> {
        let mut spec = plan.budget.scheduling.clone().unwrap_or_default();
        spec.validate()
            .map_err(|e| RuntimeError::invalid(e, "execution.budget.scheduling"))?;
        if spec.owner.is_empty() {
            spec.owner = plan.principal.clone();
        }
        Ok(spec)
    }
    /// Called under the existing PG global allocation transaction lock. Requests
    /// are reserved independently of native usage already included in MemAvailable.
    pub(super) fn claim_resources(
        &self,
        db: &mut PgAdmissionStore,
        a: &AttemptRecord,
        plan: &RuntimeExecutionPlan,
    ) -> RuntimeResult<bool> {
        let spec = self.scheduling_contract(plan)?;
        let mut tx = db
            .client
            .build_transaction()
            .isolation_level(postgres::IsolationLevel::ReadCommitted)
            .start()
            .map_err(io)?;
        tx.query_one("SELECT pg_advisory_xact_lock($1)", &[&79245017_i64])
            .map_err(io)?;
        self.require_qualified_writer_tx(&mut tx)?;
        let row=tx.query_one("SELECT a.state,j.desired_state,j.resolution FROM attempts a JOIN jobs j ON j.job_id=a.job_id WHERE a.attempt_id=$1 FOR UPDATE OF a,j",&[&a.attempt_id]).map_err(io)?;
        if row.get::<_, String>(0) != "accepted"
            || row.get::<_, String>(1) != "run"
            || row.get::<_, Option<String>>(2).is_some()
        {
            return Ok(false);
        }
        if tx
            .query_opt(
                "SELECT attempt_id FROM job_allocations WHERE attempt_id=$1 AND state='active'",
                &[&a.attempt_id],
            )
            .map_err(io)?
            .is_some()
        {
            tx.commit().map_err(io)?;
            return Ok(true);
        }
        let node = match NodeResources::observe() {
            Ok(v) => v,
            Err(_) => return Ok(false),
        };
        if !node.pressure_allows(&spec.resources) {
            return Ok(false);
        }
        let rows=tx.query("SELECT x.attempt_id,x.resources_json,x.workspace_access_json,j.workspace_id FROM job_allocations x JOIN attempts a ON a.attempt_id=x.attempt_id JOIN jobs j ON j.job_id=a.job_id WHERE x.state='active'",&[]).map_err(io)?;
        let mut cpu = 0_u64;
        let mut unspent_memory = 0_u64;
        let mut unspent_pids = 0_u64;
        for row in rows {
            let resources: ResourceRequest = decode(&row.get::<_, String>(1))?;
            let access: WorkspaceAccess = decode(&row.get::<_, String>(2))?;
            if row.get::<_, String>(3) == plan.workspace_id
                && access.conflicts(&spec.workspace_access)
            {
                return Ok(false);
            }
            cpu = cpu.saturating_add(u64::from(resources.cpu_millis));
            let attempt: String = row.get(0);
            let group = Path::new("/sys/fs/cgroup/system.slice")
                .join(format!("ordivon-pg-{attempt}.service"));
            let observed = |name: &str| {
                fs::read_to_string(group.join(name))
                    .ok()
                    .and_then(|v| v.trim().parse::<u64>().ok())
                    .unwrap_or(0)
            };
            unspent_memory = unspent_memory.saturating_add(
                resources
                    .memory_bytes
                    .saturating_sub(observed("memory.current")),
            );
            unspent_pids = unspent_pids
                .saturating_add(u64::from(resources.pids).saturating_sub(observed("pids.current")));
        }
        let reserve = (node.memory_total_bytes / 20).max(64 * 1024 * 1024);
        if !crate::resource_fit::fits(
            cpu,
            u64::from(spec.resources.cpu_millis),
            node.cpu_millis,
            spec.resources.memory_bytes,
            node.memory_available_bytes
                .saturating_sub(reserve)
                .saturating_sub(unspent_memory),
            u64::from(spec.resources.pids),
            node.pids_available
                .saturating_sub(unspent_pids)
                .saturating_sub(64),
        ) {
            return Ok(false);
        }
        tx.execute("INSERT INTO job_allocations(attempt_id,resources_json,workspace_access_json,owner,state,acquired_at_ms) VALUES($1,$2,$3,$4,'active',$5)",
            &[&a.attempt_id,&encode(&spec.resources)?,&encode(&spec.workspace_access)?,&spec.owner,&now()?]).map_err(io)?;
        tx.query_one(
            "SELECT pg_notify('ordivon_runtime_schedule',current_schema())",
            &[],
        )
        .map_err(io)?;
        tx.commit().map_err(io)?;
        Ok(true)
    }
    /// Resource-aware admission is independent of the caller's observation loop.
    /// Finite scan batches bound control-plane work, not running Job capacity.
    pub fn schedule_pending_jobs(&self) -> RuntimeResult<serde_json::Value> {
        let mut db = self.store()?;
        // Idle queue wakeups should not read host resources or every Allocation.
        let candidates=db.client.query("SELECT j.job_id,j.principal,j.execution_plan_json,a.attempt_id FROM jobs j JOIN attempts a ON a.attempt_id=j.current_attempt_id WHERE j.resolution IS NULL AND j.desired_state='run' AND a.state='accepted' AND NOT EXISTS(SELECT 1 FROM job_runtime_release_effects r WHERE r.job_id=j.job_id) ORDER BY j.created_at_ms,j.job_id",&[]).map_err(io)?;
        if candidates.is_empty() {
            return Ok(json!({"considered":0,"attempted":0}));
        }
        let node = NodeResources::observe().map_err(error)?;
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
        // Execution plans are immutable once accepted. Decode each candidate once.
        let mut ranked = Vec::with_capacity(candidates.len());
        for (order, row) in candidates.iter().enumerate() {
            let plan: RuntimeExecutionPlan = decode(&row.get::<_, String>(2))?;
            let spec = self.scheduling_contract(&plan)?;
            ranked.push(PendingCandidate {
                priority: spec.priority,
                order,
                job: row.get(0),
                principal: row.get(1),
                attempt_id: row.get(3),
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
            let candidate = ranked.remove(index);
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
            if self.reconcile_inner(&mut db, &job, true).is_ok() {
                let active: bool = db
                    .client
                    .query_one(
                        "SELECT EXISTS(SELECT 1 FROM job_allocations x JOIN attempts a ON a.attempt_id=x.attempt_id WHERE a.job_id=$1 AND x.state='active')",
                        &[&job],
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
    pub fn annotate_scheduling(
        &self,
        mut value: serde_json::Value,
    ) -> RuntimeResult<serde_json::Value> {
        let id = value.get("jobId").and_then(|v| v.as_str()).or_else(|| {
            value
                .get("job")
                .and_then(|j| j.get("jobId"))
                .and_then(|v| v.as_str())
        });
        let Some(id) = id.map(str::to_string) else {
            return Ok(value);
        };
        let mut db = self.store()?;
        let row=db.client.query_one("SELECT j.execution_plan_json,a.state,EXISTS(SELECT 1 FROM job_allocations x WHERE x.attempt_id=a.attempt_id AND x.state='active') FROM jobs j JOIN attempts a ON a.job_id=j.job_id WHERE j.job_id=$1 ORDER BY a.attempt_number DESC LIMIT 1",&[&id]).map_err(io)?;
        let plan: RuntimeExecutionPlan = decode(&row.get::<_, String>(0))?;
        let s = self.scheduling_contract(&plan)?;
        let state: String = row.get(1);
        let allocated: bool = row.get(2);
        value["scheduling"] = json!({"state":if allocated{"allocated"}else if state=="accepted"{"pending"}else{"released"},"request":s,"pendingReason":if state=="accepted"&&!allocated{Some("waiting_for_resources_pressure_or_workspace_lease")}else{None}});
        Ok(value)
    }
    /// One dedicated PG notification connection; a bounded timeout re-observes
    /// kernel pressure even when no database transition produces a notification.
    pub fn serve_scheduler(&self, shutdown: std::sync::Arc<std::sync::atomic::AtomicBool>) {
        use postgres::fallible_iterator::FallibleIterator;
        while !shutdown.load(std::sync::atomic::Ordering::Acquire) {
            if let Ok(mut db) = self.store() {
                if db
                    .client
                    .batch_execute("LISTEN ordivon_runtime_schedule")
                    .is_ok()
                {
                    while !shutdown.load(std::sync::atomic::Ordering::Acquire) {
                        if let Err(error) = self.reconcile_issued_jobs(100) {
                            eprintln!("PG native reconciliation error: {:?}", error.code);
                        }
                        if let Err(error) = self.schedule_pending_jobs() {
                            eprintln!("PG resource scheduling error: {:?}", error.code);
                        }
                        if db
                            .client
                            .notifications()
                            .timeout_iter(Duration::from_secs(1))
                            .next()
                            .is_err()
                        {
                            break;
                        }
                    }
                }
            }
            thread::sleep(Duration::from_secs(1));
        }
    }
}

#[cfg(test)]
mod scheduler_candidate_tests {
    use super::*;

    fn node() -> NodeResources {
        NodeResources {
            cpu_millis: 1_000,
            memory_total_bytes: 1_000,
            memory_available_bytes: 1_000,
            pid_capacity: 1_000,
            pids_available: 1_000,
            cpu_pressure: 0.0,
            memory_pressure: 0.0,
            io_pressure: 0.0,
        }
    }

    fn candidate(owner: &str, priority: i16, order: usize) -> PendingCandidate {
        let spec = ResourceScheduling {
            owner: owner.into(),
            priority,
            ..Default::default()
        };
        PendingCandidate {
            priority,
            order,
            job: format!("job-{order}"),
            principal: owner.into(),
            attempt_id: format!("attempt-{order}"),
            workspace_id: "workspace-test".into(),
            spec,
        }
    }

    fn realistic_node() -> NodeResources {
        NodeResources {
            cpu_millis: 1_000,
            memory_total_bytes: 2 * 1024 * 1024 * 1024,
            memory_available_bytes: 1024 * 1024 * 1024,
            pid_capacity: 10_000,
            pids_available: 9_000,
            cpu_pressure: 0.0,
            memory_pressure: 0.0,
            io_pressure: 0.0,
        }
    }

    #[test]
    fn preflight_filters_only_known_infeasible_candidates() {
        let node = realistic_node();
        let first = candidate("a", 0, 0);
        let second = candidate("b", 0, 1);
        let mut preflight = SchedulerPreflight::default();
        assert!(preflight.allows(&first, &node));
        assert!(preflight.record_allocation(&first));
        assert!(!preflight.record_allocation(&first));
        // Exclusive Workspace lease conflicts even when CPU is plentiful.
        assert!(!preflight.allows(&second, &node));
        // Existing Attempt must resume through the idempotent PG claim.
        assert!(preflight.allows(&first, &node));

        let mut elsewhere = candidate("b", 0, 2);
        elsewhere.workspace_id = "independent-workspace".into();
        assert!(preflight.allows(&elsewhere, &node));
        preflight.reserved_cpu = 950;
        assert!(!preflight.allows(&elsewhere, &node));

        preflight.reserved_cpu = 0;
        let mut pressured = realistic_node();
        pressured.memory_pressure = 6.0;
        assert!(!preflight.allows(&elsewhere, &pressured));
        assert!(preflight.allows(&first, &pressured));
        let mut no_memory = realistic_node();
        no_memory.memory_available_bytes = 1024;
        assert!(!preflight.allows(&elsewhere, &no_memory));
    }

    #[test]
    fn preflight_preserves_concurrent_readers() {
        let node = realistic_node();
        let mut first = candidate("a", 0, 0);
        first.spec.workspace_access.read_only = true;
        let mut second = candidate("b", 0, 1);
        second.spec.workspace_access.read_only = true;
        let mut preflight = SchedulerPreflight::default();
        assert!(preflight.record_allocation(&first));
        assert!(preflight.allows(&second, &node));
    }

    #[test]
    fn scheduler_preserves_priority_before_share_and_fifo() {
        let candidates = [
            candidate("a", 0, 0),
            candidate("b", 1, 1),
            candidate("c", 1, 2),
        ];
        let mut usage = BTreeMap::new();
        usage.insert("b".into(), (900, 0, 0));
        assert_eq!(next_candidate(&candidates, &usage, &node()), Some(2));
        usage.insert("c".into(), (900, 0, 0));
        assert_eq!(next_candidate(&candidates, &usage, &node()), Some(1));
    }

    #[test]
    fn scheduler_recomputes_owner_shares_after_allocation() {
        let candidates = [candidate("a", 0, 0), candidate("b", 0, 1)];
        let mut usage = BTreeMap::new();
        assert_eq!(next_candidate(&candidates, &usage, &node()), Some(0));
        usage.insert("a".into(), (100, 0, 0));
        assert_eq!(next_candidate(&candidates, &usage, &node()), Some(1));
        assert_eq!(next_candidate(&[], &usage, &node()), None);
    }

    #[test]
    fn preflight_accounts_for_new_claims_not_yet_visible_in_native_snapshot() {
        let node = realistic_node();
        let mut first = candidate("a", 0, 0);
        first.spec.resources.memory_bytes = 600 * 1024 * 1024;
        let mut second = candidate("b", 0, 1);
        second.workspace_id = "other-workspace".into();
        second.spec.resources.memory_bytes = 600 * 1024 * 1024;

        let mut preflight = SchedulerPreflight::default();
        assert!(preflight.allows(&first, &node));
        assert!(preflight.record_allocation(&first));
        assert_eq!(preflight.newly_reserved_memory, 600 * 1024 * 1024);
        // No second PG claim/cgroup scan for a capacity estimate already
        // contradicted by allocations made since the OS snapshot.
        assert!(!preflight.allows(&second, &node));
        // An already admitted Attempt must still resume idempotently.
        assert!(preflight.allows(&first, &node));
        assert!(!preflight.record_allocation(&first));
        assert_eq!(preflight.newly_reserved_memory, 600 * 1024 * 1024);

        let mut fresh = SchedulerPreflight::default();
        fresh.active_attempts.insert(first.attempt_id.clone());
        fresh.reserved_cpu = u64::from(first.spec.resources.cpu_millis);
        // Old active reservations already reflected by native observation
        // must not be double-charged to the newly reserved budget.
        assert!(fresh.allows(&second, &node));
    }

    #[test]
    fn preflight_accounts_for_unobserved_pid_reservations() {
        let node = realistic_node();
        let mut first = candidate("a", 0, 0);
        first.spec.resources.pids = 6_000;
        let mut second = candidate("b", 0, 1);
        second.workspace_id = "other-workspace".into();
        second.spec.resources.pids = 6_000;

        let mut preflight = SchedulerPreflight::default();
        assert!(preflight.allows(&first, &node));
        assert!(preflight.record_allocation(&first));
        assert_eq!(preflight.newly_reserved_pids, 6_000);
        assert!(!preflight.allows(&second, &node));
        assert!(preflight.allows(&first, &node));
        assert!(!preflight.record_allocation(&first));
        assert_eq!(preflight.newly_reserved_pids, 6_000);
    }

    #[test]
    fn initial_preflight_keeps_late_eligible_and_existing_idempotent_attempts() {
        let node = realistic_node();
        let mut preflight = SchedulerPreflight::default();
        preflight
            .leases
            .insert("busy".into(), vec![WorkspaceAccess::default()]);
        let mut ranked = (0..3_000)
            .map(|order| {
                let mut candidate = candidate("blocked", 0, order);
                candidate.workspace_id = "busy".into();
                candidate
            })
            .collect::<Vec<_>>();
        // Existing Allocation must be revisited even when a Workspace lease
        // would otherwise reject a second new claim.
        preflight
            .active_attempts
            .insert(ranked[0].attempt_id.clone());
        let mut tail = candidate("eligible", 10, 3_000);
        tail.workspace_id = "independent".into();
        ranked.push(tail);

        preflight.retain_initially_feasible(&mut ranked, &node);
        assert_eq!(ranked.len(), 2);
        assert_eq!(ranked[0].order, 0);
        assert_eq!(ranked[1].order, 3_000);
        assert_eq!(next_candidate(&ranked, &BTreeMap::new(), &node), Some(1));
    }

    #[test]
    fn initial_preflight_does_not_skip_candidates_later_blocked_by_new_claims() {
        let node = realistic_node();
        let mut preflight = SchedulerPreflight::default();
        let mut first = candidate("a", 1, 0);
        first.workspace_id = "workspace-1".into();
        first.spec.resources.memory_bytes = 600 * 1024 * 1024;
        let mut second = candidate("b", 0, 1);
        second.workspace_id = "workspace-2".into();
        second.spec.resources.memory_bytes = 600 * 1024 * 1024;
        let mut ranked = vec![first, second];

        // Both fit the initial OS snapshot. Removing either would violate
        // Priority/DRF/FIFO eligibility, even if only one can later commit.
        preflight.retain_initially_feasible(&mut ranked, &node);
        assert_eq!(ranked.len(), 2);
        assert_eq!(next_candidate(&ranked, &BTreeMap::new(), &node), Some(0));
        assert!(preflight.record_allocation(&ranked.remove(0)));
        assert!(!preflight.allows(&ranked[0], &node));
    }
}
