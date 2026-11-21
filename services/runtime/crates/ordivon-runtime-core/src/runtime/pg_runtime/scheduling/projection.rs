//! Read-only scheduling status projection; cannot create a PG allocation.
use super::super::{io, PgRuntime, RuntimeResult};
use super::failure_policy::decode_accepted_candidate;
use super::policy::scheduling_readback;

pub(super) const SCHEDULING_READBACK_SQL: &str = "SELECT j.execution_plan_json,a.state,EXISTS(SELECT 1 FROM job_allocations x WHERE x.attempt_id=a.attempt_id AND x.state='active'),j.desired_state,j.resolution,a.attempt_id FROM jobs j LEFT JOIN attempts a ON a.attempt_id=COALESCE(j.current_attempt_id,(SELECT last.attempt_id FROM attempts last WHERE last.job_id=j.job_id ORDER BY last.attempt_number DESC LIMIT 1)) AND a.job_id=j.job_id WHERE j.job_id=$1";

impl PgRuntime {
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
}
