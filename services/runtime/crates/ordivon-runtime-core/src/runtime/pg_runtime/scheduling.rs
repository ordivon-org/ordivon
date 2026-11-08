//! Durable pending work, atomic native allocation and fair dispatch.
use super::*;
use crate::resource_scheduling::{
    NodeResources, ResourceRequest, ResourceScheduling, WorkspaceAccess,
};
use std::collections::BTreeMap;

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
        let node = NodeResources::observe().map_err(error)?;
        let mut db = self.store()?;
        let active = db
            .client
            .query(
                "SELECT owner,resources_json FROM job_allocations WHERE state='active'",
                &[],
            )
            .map_err(io)?;
        let mut usage: BTreeMap<String, (u64, u64, u64)> = BTreeMap::new();
        for row in active {
            let r: ResourceRequest = decode(&row.get::<_, String>(1))?;
            let v = usage.entry(row.get(0)).or_default();
            v.0 = v.0.saturating_add(u64::from(r.cpu_millis));
            v.1 = v.1.saturating_add(r.memory_bytes);
            v.2 = v.2.saturating_add(u64::from(r.pids));
        }
        let candidates=db.client.query("SELECT j.job_id,j.principal,j.execution_plan_json FROM jobs j JOIN attempts a ON a.attempt_id=j.current_attempt_id WHERE j.resolution IS NULL AND j.desired_state='run' AND a.state='accepted' ORDER BY j.created_at_ms,j.job_id",&[]).map_err(io)?;
        let mut ranked = Vec::new();
        for (order, row) in candidates.iter().enumerate() {
            let plan: RuntimeExecutionPlan = decode(&row.get::<_, String>(2))?;
            let s = self.scheduling_contract(&plan)?;
            let v = usage.get(&s.owner).copied().unwrap_or_default();
            let dominant = (v.0 as f64 / node.cpu_millis.max(1) as f64)
                .max(v.1 as f64 / node.memory_total_bytes.max(1) as f64)
                .max(v.2 as f64 / node.pid_capacity.max(1) as f64);
            ranked.push((
                s.priority,
                dominant,
                order,
                row.get::<_, String>(0),
                row.get::<_, String>(1),
            ));
        }
        let mut dispatched = 0_u32;
        while dispatched < 32 {
            if ranked.is_empty() {
                break;
            }
            // Refresh dominant shares after every successful allocation so a
            // single owner cannot fill a whole batch ahead of queued peers.
            let mut scored = Vec::new();
            for (index, (priority, _, order, job, _)) in ranked.iter().enumerate() {
                let row = db
                    .client
                    .query_one(
                        "SELECT execution_plan_json FROM jobs WHERE job_id=$1",
                        &[job],
                    )
                    .map_err(io)?;
                let plan: RuntimeExecutionPlan = decode(&row.get::<_, String>(0))?;
                let spec = self.scheduling_contract(&plan)?;
                let u = usage.get(&spec.owner).copied().unwrap_or_default();
                let share = (u.0 as f64 / node.cpu_millis.max(1) as f64)
                    .max(u.1 as f64 / node.memory_total_bytes.max(1) as f64)
                    .max(u.2 as f64 / node.pid_capacity.max(1) as f64);
                scored.push((*priority, share, *order, index, spec));
            }
            scored.sort_by(|a, b| {
                b.0.cmp(&a.0)
                    .then_with(|| a.1.total_cmp(&b.1))
                    .then(a.2.cmp(&b.2))
            });
            let (_, _, _, index, spec) = scored.remove(0);
            let (_, _, _, job, principal) = ranked.remove(index);
            self.authorize(&mut db, &job, &principal)?;
            if self.reconcile_inner(&mut db, &job, true).is_ok() {
                let active:bool=db.client.query_one("SELECT EXISTS(SELECT 1 FROM job_allocations x JOIN attempts a ON a.attempt_id=x.attempt_id WHERE a.job_id=$1 AND x.state='active')",&[&job]).map_err(io)?.get(0);
                if active {
                    let u = usage.entry(spec.owner).or_default();
                    u.0 = u.0.saturating_add(u64::from(spec.resources.cpu_millis));
                    u.1 = u.1.saturating_add(spec.resources.memory_bytes);
                    u.2 = u.2.saturating_add(u64::from(spec.resources.pids));
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
