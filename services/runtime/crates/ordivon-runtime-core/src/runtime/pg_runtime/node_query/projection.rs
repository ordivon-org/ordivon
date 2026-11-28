//! PG-qualified Job row read-only view: malformed frozen Plan stays row-local UNKNOWN.
use super::super::{
    decode, now, pg_delivery_disposition, reconciliation::needs_recovery_observation, AttemptState,
    PgRuntime, RuntimeExecutionPlan, RuntimeResult,
};
use serde_json::json;
use std::path::Path;

impl PgRuntime {
    pub(super) fn project_job_list_row(
        &self,
        r: &postgres::Row,
    ) -> RuntimeResult<serde_json::Value> {
        // A corrupt frozen Plan is a row-local UNKNOWN during a read-only
        // listing. Preserve qualified PG identity rather than treating one
        // malformed Job as a globally unavailable Registry. The scheduler
        // records its own bounded per-Job issue; never invent plan values.
        let plan = decode::<RuntimeExecutionPlan>(&r.get::<_, String>(13)).ok();
        let at = r.get::<_, i64>(4).max(0) as u64;
        let started = r.get::<_, Option<i64>>(11).map(|v| v.max(0) as u64);
        let finished = r.get::<_, Option<i64>>(12).map(|v| v.max(0) as u64);
        let resolution: Option<String> = r.get(6);
        let attempt_state: Option<String> = r.get(8);
        let count: i64 = r.get(14);
        let end = finished.unwrap_or(now()?.max(0) as u64);
        let cwd_relative = plan.as_ref().map(|plan| {
            Path::new(&plan.cwd)
                .strip_prefix(&plan.workspace_path)
                .map(|p| {
                    if p.as_os_str().is_empty() {
                        ".".into()
                    } else {
                        p.to_string_lossy().into_owned()
                    }
                })
                .unwrap_or_else(|_| ".".into())
        });
        let desired: String = r.get(5);
        let scheduling = plan
            .as_ref()
            .and_then(|plan| self.scheduling_contract(plan).ok())
            .map(|spec| {
                super::super::scheduling::scheduling_readback(
                    spec,
                    attempt_state.as_deref(),
                    &desired,
                    resolution.as_deref(),
                    r.get::<_, bool>(16),
                )
            });
        let delivery = pg_delivery_disposition(
            resolution.as_deref(),
            finished.is_some() && r.get::<_, bool>(15),
        );
        // Listing preserves its row-local finished-at qualification; the
        // detailed observation uses the independently qualified terminal flag.
        let recovery_required = attempt_state
            .as_deref()
            .and_then(AttemptState::known_db_state)
            .is_some_and(|state| needs_recovery_observation(state, finished.is_some()));
        Ok(json!({
            "jobId":r.get::<_,String>(0),
            "operationDigest":r.get::<_,String>(1),
            "clientRequestId":r.get::<_,String>(2),
            "workspaceId":r.get::<_,String>(3),
            "createdAtMs":at,
            "desiredState":desired,
            "status":resolution.clone().or_else(||attempt_state.clone()).unwrap_or_else(||"accepted".into()),
            "attemptId":r.get::<_,Option<String>>(7),
            "attemptState":attempt_state,
            "terminationIntent":r.get::<_,Option<String>>(9),
            "exitCode":r.get::<_,Option<i32>>(10),
            "startedAtMs":started,"finishedAtMs":finished,
            "executionTerminal":resolution.is_some(),
            "executionDisposition":resolution,
            "executionReasonCode":r.get::<_,Option<String>>(17),
            "deliveryDisposition":delivery,
            "recoveryRequired":recovery_required,
            "semanticCompletionEvaluated":false,
            "sourceRevision":plan.as_ref().map(|plan| &plan.source_revision),
            "executableName":plan.as_ref().map(|plan| {
                Path::new(&plan.executable).file_name()
                    .map(|p|p.to_string_lossy().into_owned()).unwrap_or_default()
            }),
            "cwdRelative":cwd_relative,
            "durationMs":end.saturating_sub(started.unwrap_or(at)),
            "resultAvailable":finished.is_some() && r.get::<_,bool>(15),
            "scheduling":scheduling,
            "artifactsAvailable":count>0,"artifactCount":count,
        }))
    }
}
