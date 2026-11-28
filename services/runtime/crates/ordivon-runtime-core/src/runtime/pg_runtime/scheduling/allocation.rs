//! Original PG resource reservation under the single qualified-writer transaction.
use super::native_capacity::native_resource_error;
#[cfg(not(windows))]
use super::native_capacity::unspent_native_allocation;
use super::{
    decode, encode, io, now, AttemptRecord, PgAdmissionStore, PgRuntime, RuntimeError,
    RuntimeExecutionPlan, RuntimeResult,
};
use crate::resource_scheduling::{
    NodeResources, ResourceRequest, ResourceScheduling, WorkspaceAccess,
};
#[cfg(not(windows))]
use std::path::Path;

impl PgRuntime {
    pub(in crate::runtime::pg_runtime) fn scheduling_contract(
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
    pub(in crate::runtime::pg_runtime) fn claim_resources(
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
        let claimable: bool = tx
            .query_one(
                super::LOCKED_CLAIMABLE_ATTEMPT_SQL,
                &[&a.attempt_id, &a.job_id],
            )
            .map_err(io)?
            .get(0);
        if !claimable {
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
            #[cfg(not(windows))]
            let (memory, pids) = {
                let attempt: String = row.get(0);
                let group = Path::new("/sys/fs/cgroup/system.slice")
                    .join(format!("ordivon-pg-{attempt}.service"));
                unspent_native_allocation(&group, &resources)
                    .map_err(|e| e.with_operation_id(&a.job_id))?
            };
            // Until a qualified JobObject usage read is available, reserve the
            // whole existing request; conservative double-counting is not
            // an assertion of zero Windows usage or a new capacity authority.
            #[cfg(windows)]
            let (memory, pids) = (resources.memory_bytes, u64::from(resources.pids));
            unspent_memory = unspent_memory.saturating_add(memory);
            unspent_pids = unspent_pids.saturating_add(pids);
        }
        if !node.fits(cpu, &spec.resources, unspent_memory, unspent_pids) {
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
}
