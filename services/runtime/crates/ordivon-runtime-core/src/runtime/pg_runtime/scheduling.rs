//! Durable pending work, atomic native allocation and fair dispatch.
//! Logic policy and physical resource observation live in separate modules.
use super::*;
mod failure_policy;
mod issue_writer;
mod native_capacity;
mod policy;
use crate::resource_scheduling::{
    NodeResources, ResourceRequest, ResourceScheduling, WorkspaceAccess,
};
use failure_policy::{decode_accepted_candidate, is_job_scoped_reconciliation_error};
use issue_writer::record_scheduler_issue;
use native_capacity::{native_resource_error, unspent_native_allocation};
pub(super) use policy::scheduling_readback;
use policy::{next_candidate, PendingCandidate, SchedulerPreflight};
use std::collections::{BTreeMap, BTreeSet};

// A current Attempt belongs to exactly one Job. The schema does not enforce
// uniqueness of jobs.current_attempt_id, so bind both identities at the query
// boundary instead of trusting a potentially stale/corrupted pointer.
const PENDING_JOBS_SQL: &str = "SELECT j.job_id,j.principal,j.execution_plan_json,a.attempt_id FROM jobs j JOIN attempts a ON a.attempt_id=j.current_attempt_id AND a.job_id=j.job_id WHERE j.resolution IS NULL AND j.desired_state='run' AND a.state='accepted' AND NOT EXISTS(SELECT 1 FROM job_runtime_release_effects r WHERE r.job_id=j.job_id) ORDER BY j.created_at_ms,j.job_id";

const SCHEDULING_READBACK_SQL: &str = "SELECT j.execution_plan_json,a.state,EXISTS(SELECT 1 FROM job_allocations x WHERE x.attempt_id=a.attempt_id AND x.state='active'),j.desired_state,j.resolution,a.attempt_id FROM jobs j LEFT JOIN attempts a ON a.attempt_id=COALESCE(j.current_attempt_id,(SELECT last.attempt_id FROM attempts last WHERE last.job_id=j.job_id ORDER BY last.attempt_number DESC LIMIT 1)) AND a.job_id=j.job_id WHERE j.job_id=$1";

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
        let node = NodeResources::observe()
            .map_err(|e| native_resource_error(e).with_operation_id(&a.job_id))?;
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
            let (memory, pids) = unspent_native_allocation(&group, &resources)
                .map_err(|e| e.with_operation_id(&a.job_id))?;
            unspent_memory = unspent_memory.saturating_add(memory);
            unspent_pids = unspent_pids.saturating_add(pids);
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
        let row = db
            .client
            .query_one(SCHEDULING_READBACK_SQL, &[&id])
            .map_err(io)?;
        // Corruption of one committed Job plan is an invalid Job record, not
        // PostgreSQL transport unavailability. Until the public Scheduling
        // schema can represent an unknown frozen request, fail visibly with
        // the existing typed error rather than fabricating a default budget.
        let plan = decode_accepted_candidate(&row.get::<_, String>(0))?;
        let spec = self.scheduling_contract(&plan)?;
        let attempt_state: Option<String> = row.get(1);
        let allocated: bool = row.get(2);
        let desired: String = row.get(3);
        let resolution: Option<String> = row.get(4);
        let current_attempt_id: Option<String> = row.get(5);
        let mut projection = scheduling_readback(
            spec,
            attempt_state.as_deref(),
            &desired,
            resolution.as_deref(),
            allocated,
        );
        // The existing public schema only offers cause_unobserved. When a
        // persisted Job event has a concrete failure, do not mislabel it as
        // an unobserved resource wait; clients can inspect exact job.get events.
        if projection["state"] == "pending" {
            if let Some(attempt_id) = current_attempt_id {
                let has_issue: bool = db.client.query_one(
                    "SELECT EXISTS(SELECT 1 FROM job_events WHERE job_id=$1 AND attempt_id=$2 AND event_type='SCHEDULER_ISSUE')",
                    &[&id, &attempt_id],
                ).map_err(io)?.get(0);
                if has_issue {
                    projection["pendingReason"] = serde_json::Value::Null;
                }
            }
        }
        value["scheduling"] = projection;
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
    fn invalid_accepted_plan_is_job_scoped_not_registry_unavailable() {
        let error = decode_accepted_candidate("{not-valid-json").unwrap_err();
        assert_eq!(error.code, RuntimeErrorCode::InvalidRequest);
        assert_eq!(error.field.as_deref(), Some("executionPlan"));
        assert!(!error.retryable);
    }

    #[test]
    fn global_failures_are_never_categorized_as_local_candidate_errors() {
        for code in [
            RuntimeErrorCode::RegistryUnavailable,
            RuntimeErrorCode::RegistryBusy,
            RuntimeErrorCode::RegistryCorrupt,
            RuntimeErrorCode::ToolFailed,
        ] {
            let error = RuntimeError::new(code, "global unknown", None, true);
            assert!(!is_job_scoped_reconciliation_error(&error));
        }
        let provider = RuntimeError::new(
            RuntimeErrorCode::ProviderStateMismatch,
            "native runner changed after admission",
            Some("executionProvider"),
            false,
        );
        assert!(is_job_scoped_reconciliation_error(&provider));
        assert!(!is_job_scoped_reconciliation_error(&native_resource_error(
            "missing cgroup controls"
        )));
    }

    #[test]
    fn missing_node_observation_is_not_resource_infeasible() {
        let error = native_resource_error("missing /proc/pressure/memory");
        assert_eq!(error.code, RuntimeErrorCode::ToolFailed);
        assert!(error.retryable);
        assert_eq!(error.field.as_deref(), Some("scheduling.resources"));
        assert!(!is_job_scoped_reconciliation_error(&error));
        assert!(!error
            .message
            .contains("resource pressure or workspace lease"));
    }

    #[test]
    fn native_allocation_missing_controller_is_unknown_not_zero_usage() {
        let root = std::env::temp_dir().join(format!(
            "ordivon-pg-native-observation-{}",
            uuid::Uuid::now_v7()
        ));
        fs::create_dir(&root).unwrap();
        let group = root.join("ordivon-pg-attempt.service");
        fs::create_dir(&group).unwrap();
        fs::write(group.join("memory.current"), "128\n").unwrap();
        let request = ResourceRequest {
            memory_bytes: 1024,
            pids: 16,
            ..Default::default()
        };
        let error = unspent_native_allocation(&group, &request)
            .expect_err("missing pids.current is UNKNOWN, not zero usage");
        assert_eq!(error.code, RuntimeErrorCode::ToolFailed);
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn native_allocation_missing_unit_reserves_full_budget_but_malformed_is_unknown() {
        let root = std::env::temp_dir().join(format!(
            "ordivon-pg-native-observation-{}",
            uuid::Uuid::now_v7()
        ));
        fs::create_dir(&root).unwrap();
        let group = root.join("not-yet-started.service");
        let request = ResourceRequest {
            memory_bytes: 1024,
            pids: 16,
            ..Default::default()
        };
        assert_eq!(
            unspent_native_allocation(&group, &request).unwrap(),
            (1024, 16)
        );
        fs::create_dir(&group).unwrap();
        fs::write(group.join("memory.current"), "malformed\n").unwrap();
        fs::write(group.join("pids.current"), "3\n").unwrap();
        let error = unspent_native_allocation(&group, &request)
            .expect_err("bad controller output must preserve UNKNOWN");
        assert_eq!(error.code, RuntimeErrorCode::ToolFailed);
        fs::write(group.join("memory.current"), "128\n").unwrap();
        assert_eq!(
            unspent_native_allocation(&group, &request).unwrap(),
            (896, 13)
        );
        fs::remove_dir_all(root).unwrap();
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

    #[test]
    #[ignore = "requires explicit disposable ORDIVON_PG_TEST_DSN"]
    fn native_pg_pending_requires_attempt_to_belong_to_its_job() {
        // This intentionally reproduces a cross-Job current_attempt_id link:
        // attempts.attempt_id is PK but jobs.current_attempt_id is not UNIQUE.
        // TEMP tables keep this test isolated from any persistent Registry.
        let dsn =
            std::env::var("ORDIVON_PG_TEST_DSN").expect("explicit disposable PG test DSN required");
        let mut db = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
        db.batch_execute(
            "CREATE TEMP TABLE jobs (
                job_id text PRIMARY KEY,
                principal text NOT NULL,
                execution_plan_json text NOT NULL,
                current_attempt_id text NOT NULL,
                resolution text,
                desired_state text NOT NULL,
                created_at_ms bigint NOT NULL
             );
             CREATE TEMP TABLE attempts (
                attempt_id text PRIMARY KEY,
                job_id text NOT NULL,
                state text NOT NULL
             );
             CREATE TEMP TABLE job_runtime_release_effects(job_id text PRIMARY KEY);
             INSERT INTO jobs VALUES
                ('job-a','principal-a','{}','attempt-a',NULL,'run',1),
                ('job-b','principal-b','{}','attempt-a',NULL,'run',2);
             INSERT INTO attempts VALUES ('attempt-a','job-a','accepted');",
        )
        .unwrap();
        let found = db.query(PENDING_JOBS_SQL, &[]).unwrap();
        assert_eq!(found.len(), 1);
        assert_eq!(found[0].get::<_, String>(0), "job-a");
        assert_eq!(found[0].get::<_, String>(3), "attempt-a");
    }

    #[test]
    fn scheduler_readback_does_not_invent_placement_failure_cause() {
        let req = ResourceScheduling::default();
        let pending = scheduling_readback(req.clone(), Some("accepted"), "run", None, false);
        assert_eq!(pending["state"], "pending");
        assert_eq!(pending["pendingReason"], "cause_unobserved");

        let cancelled =
            scheduling_readback(req.clone(), Some("accepted"), "cancelled", None, false);
        assert_eq!(cancelled["state"], "released");
        assert!(cancelled["pendingReason"].is_null());
        let resolved =
            scheduling_readback(req.clone(), Some("accepted"), "run", Some("lost"), false);
        assert_eq!(resolved["state"], "released");
        let starting = scheduling_readback(req.clone(), Some("starting"), "run", None, false);
        assert_eq!(starting["state"], "released");
        let allocated = scheduling_readback(req, Some("running"), "run", None, true);
        assert_eq!(allocated["state"], "allocated");
        assert!(allocated["pendingReason"].is_null());
    }

    #[test]
    #[ignore = "requires explicit disposable ORDIVON_PG_TEST_DSN"]
    fn native_pg_scheduling_uses_current_attempt_not_highest_attempt_number() {
        let dsn =
            std::env::var("ORDIVON_PG_TEST_DSN").expect("explicit disposable PG DSN required");
        let mut db = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
        db.batch_execute(
            "CREATE TEMP TABLE jobs (
               job_id text PRIMARY KEY, execution_plan_json text,
               current_attempt_id text, desired_state text, resolution text
             );
             CREATE TEMP TABLE attempts (
               attempt_id text PRIMARY KEY, job_id text, attempt_number bigint, state text
             );
             CREATE TEMP TABLE job_allocations (attempt_id text, state text);
             INSERT INTO jobs VALUES ('job-r3','{}','attempt-current','run',NULL);
             INSERT INTO attempts VALUES ('attempt-current','job-r3',1,'accepted'),
                 ('attempt-later','job-r3',2,'running');",
        )
        .unwrap();
        let row = db.query_one(SCHEDULING_READBACK_SQL, &[&"job-r3"]).unwrap();
        assert_eq!(row.get::<_, Option<String>>(1).as_deref(), Some("accepted"));
        assert_eq!(row.get::<_, String>(3), "run");
        assert!(row.get::<_, Option<String>>(4).is_none());
    }
}
