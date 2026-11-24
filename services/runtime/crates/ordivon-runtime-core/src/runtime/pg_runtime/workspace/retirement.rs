//! Workspace retirement uses Runtime-owned PG Claim and active Job admission fences.
//! A caller's release assertion never overrides a still-HELD Claim.
//! PostgreSQL commit and Git worktree removal are separate effects; ambiguity remains explicit.
use super::*;

// An automated collector does not have evidence that the consumer released
// its Workspace merely because the final Job exited successfully. The native
// PG owner must re-read latest activity INSIDE the same admission/close fence,
// not trust the sweep's earlier global SQL snapshot. Explicit
// consumerReleased=true remains the caller's separate release assertion.
const WORKSPACE_JOB_CONTINUATION_HOLD_MS: i64 = 4 * 60 * 60 * 1000;

// Read committed AFTER the shared admission lock, so a recently completed
// Job no longer listed in activeJobIds still retains the Workspace long
// enough for consumers to inspect artifacts and source.
// Reuse existing PG jobs/attempts/events, with no additional registry/table.
fn require_recent_pg_job_consumer_continuation(
    tx: &mut postgres::Transaction<'_>,
    workspace_id: &str,
) -> RuntimeResult<()> {
    let row = tx
        .query_one(
            "WITH owned_jobs AS (
                SELECT job_id, created_at_ms FROM jobs WHERE workspace_id=$1
            )
            SELECT GREATEST(
                COALESCE((SELECT MAX(created_at_ms) FROM owned_jobs),0),
                COALESCE((SELECT MAX(a.finished_at_ms) FROM attempts a
                          JOIN owned_jobs j ON j.job_id=a.job_id),0),
                COALESCE((SELECT MAX(e.observed_at_ms) FROM job_events e
                          JOIN owned_jobs j ON j.job_id=e.job_id),0)
            ),
            (EXTRACT(EPOCH FROM clock_timestamp()) * 1000)::bigint",
            &[&workspace_id],
        )
        .map_err(io)?;
    let last_job_activity_ms: i64 = row.get(0);
    let now_ms: i64 = row.get(1);
    if last_job_activity_ms > now_ms.saturating_sub(WORKSPACE_JOB_CONTINUATION_HOLD_MS) {
        return Err(RuntimeError::new(
            RuntimeErrorCode::WorkspaceStateMismatch,
            "Workspace has recent PG Job activity inside the consumer continuation window; an explicit consumerReleased is required before close",
            Some("consumerReleased"),
            true,
        ));
    }
    Ok(())
}

impl PgRuntime {
    /// Close only when PG proves no active or held consumer, then reuse the
    /// existing workspace source/dirty/continuation and dependency checks.
    pub fn close_workspace(
        &self,
        request: &WorkspaceCloseRequest,
    ) -> RuntimeResult<WorkspaceCloseResult> {
        let mut db = self.store()?;
        let mut tx = self.begin_workspace_effect_tx(&mut db)?;
        let active: i64 = tx
            .query_one(
                &workspace_consumer_sql("count(*)", "j.workspace_id=$1", ""),
                &[&request.workspace_id],
            )
            .map_err(io)?
            .get(0);
        if active != 0 {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ConcurrencyLimit,
                "Workspace has PG-owned active or held Jobs",
                Some("workspaceId"),
                false,
            ));
        }
        // A Harness Run may be paused between Jobs for an arbitrary duration.
        // Its physical claim lives here, in this Runtime DB and lock domain.
        // This guard is NEVER bypassed by a caller's consumerReleased=true.
        let claimed: i64 = tx
            .query_one(
                "SELECT count(*) FROM workspace_consumer_claims
             WHERE store_root=$1 AND workspace_id=$2 AND state='held'",
                &[
                    &self
                        .config
                        .executor
                        .canonical_store_root()
                        .map_err(io)?
                        .to_string_lossy()
                        .into_owned(),
                    &request.workspace_id,
                ],
            )
            .map_err(io)?
            .get(0);
        if claimed != 0 {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ConcurrencyLimit,
                "Workspace has Runtime-owned long-lived consumer Claims",
                Some("workspaceId"),
                false,
            ));
        }
        if !request.consumer_released {
            // The external lifecycle script's initial PG snapshot is
            // advisory only: a Job can start and complete during the scan.
            // This guard shares the native admission lock with workspace.close
            // and must precede any Git/worktree effect.
            require_recent_pg_job_consumer_continuation(&mut tx, &request.workspace_id)?;
        }
        let dependents =
            universal::workspace_cleanup_dependents(&self.config.executor, &request.workspace_id)
                .map_err(io)?;
        if !dependents.is_empty() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ConcurrencyLimit,
                "Workspace has dependent Workspaces",
                Some("workspaceId"),
                false,
            ));
        }
        let result = universal::remove_git_workspace(&self.config.executor, request)
            .map_err(super::super::error::map_universal_error)?;
        workspace_effect_commit(tx.commit(), "workspace.close")?;
        Ok(result)
    }
}
