//! Original principal-scoped qualified-epoch PostgreSQL Job cursor, one repeatable-read transaction.
use super::super::{error, io, pg, PgRuntime, RuntimeError, RuntimeJobListRequest, RuntimeResult};
use serde_json::json;

impl PgRuntime {
    /// Principal-scoped, read-only cursor over new-epoch PostgreSQL Job identity.
    pub fn list(
        &self,
        principal: &str,
        request: &RuntimeJobListRequest,
    ) -> RuntimeResult<serde_json::Value> {
        if request.limit == 0 || request.limit > 100 {
            return Err(RuntimeError::invalid("limit must be 1..100", "limit"));
        }
        let mut db = self.store()?;
        // This is a projection of CURRENT Runtime truth, not an archival SQL
        // browser. Read stage, physical PG epoch and rows from one consistent
        // snapshot; never report a branch-restored Job as current after PITR.
        let mut tx = db
            .client
            .build_transaction()
            .isolation_level(postgres::IsolationLevel::RepeatableRead)
            .read_only(true)
            .start()
            .map_err(io)?;
        let stage = tx.query_opt(
            "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='source'",
            &[],
        ).map_err(io)?.ok_or_else(|| error("PG Runtime source writer not qualified"))?;
        if stage.get::<_, String>(0) != "QUALIFIED_WRITER"
            || stage.get::<_, String>(1) != self.config.source_sha256
            || !stage.get::<_, bool>(2)
        {
            return Err(error("PG Runtime source writer not qualified"));
        }
        crate::pg_admission::require_pg_writer_epoch(&mut tx, &self.config.source_sha256, false)
            .map_err(pg)?;
        let cursor_at = request.cursor.as_ref().map(|c| c.created_at_ms as i64);
        let cursor_id = request.cursor.as_ref().map(|c| c.job_id.clone());
        let limit = i64::from(request.limit) + 1;
        let rows=tx.query(
            "SELECT j.job_id,j.operation_digest,j.client_request_id,j.workspace_id,j.created_at_ms,              j.desired_state,j.resolution,a.attempt_id,a.state,a.termination_intent,a.exit_code,              a.started_at_ms,a.finished_at_ms,j.execution_plan_json,              (SELECT count(*) FROM artifacts r WHERE r.job_id=j.job_id), EXISTS(SELECT 1 FROM artifacts z WHERE z.job_id=j.job_id AND z.kind='execution_result'), EXISTS(SELECT 1 FROM job_allocations x WHERE x.attempt_id=a.attempt_id AND x.state='active')              FROM jobs j LEFT JOIN attempts a ON a.attempt_id=COALESCE(j.current_attempt_id,              (SELECT last.attempt_id FROM attempts last WHERE last.job_id=j.job_id              ORDER BY last.attempt_number DESC LIMIT 1)) AND a.job_id=j.job_id              WHERE j.principal=$1              AND ($2::text IS NULL OR j.client_request_id=$2::text)              AND ($3::text IS NULL OR j.workspace_id=$3::text)              AND ($4::bigint IS NULL OR (j.created_at_ms,j.job_id)<($4::bigint,$5::text))              ORDER BY j.created_at_ms DESC,j.job_id DESC LIMIT $6",
            &[&principal,&request.client_request_id,&request.workspace_id,&cursor_at,&cursor_id,&limit]
        ).map_err(io)?;
        tx.commit().map_err(io)?;
        let more = rows.len() > request.limit as usize;
        let mut jobs = Vec::new();
        for r in rows.iter().take(request.limit as usize) {
            jobs.push(self.project_job_list_row(r)?);
        }
        let next_cursor = if more {
            jobs.last()
                .map(|v| json!({"createdAtMs":v["createdAtMs"],"jobId":v["jobId"]}))
        } else {
            None
        };
        Ok(json!({"jobs":jobs,"nextCursor":next_cursor}))
    }
}
