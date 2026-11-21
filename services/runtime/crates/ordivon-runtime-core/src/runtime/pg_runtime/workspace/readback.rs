//! Exact Workspace get and PG/Git physical record projection.
use super::{
    io, universal, workspace_consumer_sql, PgRuntime, RuntimeError, RuntimeErrorCode,
    RuntimeResult, RuntimeWorkspaceGetRequest, UniversalExecutorConfig,
};
use serde_json::json;
use std::path::Path;

impl PgRuntime {
    pub fn executor_config(&self) -> UniversalExecutorConfig {
        self.config.executor.clone()
    }
    /// Read-only, source-bound projection. A list page has its own batched
    /// PostgreSQL readback; an exact get retains its own authoritative lookup.
    /// The cheap list projection must never compute a digest and then discard it.
    pub(in crate::runtime::pg_runtime::workspace) fn get_workspace_projected(
        &self,
        request: &RuntimeWorkspaceGetRequest,
        include_source_state_digest: bool,
        known_active_jobs: Option<Vec<String>>,
        known_git: Option<
            Result<(String, universal::WorkspaceHeadMode, bool), universal::UniversalExecError>,
        >,
        inventory_record: Option<&universal::WorkspaceRecord>,
    ) -> RuntimeResult<serde_json::Value> {
        if request.schema_version != 1 {
            return Err(RuntimeError::invalid(
                "schemaVersion must be 1",
                "schemaVersion",
            ));
        }
        let record = universal::load_workspace_record(&self.config.executor, &request.workspace_id)
            .map_err(crate::runtime::error::map_universal_error)?;
        if let Some(observed) = inventory_record {
            // The page's Git probe may run concurrently with a close/reopen.
            // Never attach HEAD/dirty from that earlier physical identity to
            // a new durable Workspace record with the same public ID.
            if &record != observed {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::WorkspaceStateMismatch,
                    "Workspace identity changed between physical list inventory and Git projection",
                    Some("workspaceId"),
                    true,
                ));
            }
        }
        let (head, head_mode, dirty) = known_git
            .unwrap_or_else(|| {
                universal::workspace_head_and_dirty_at(Path::new(&record.workspace_path))
            })
            .map_err(crate::runtime::error::map_universal_error)?;
        let jobs = if let Some(known) = known_active_jobs {
            known
        } else {
            let mut db = self.store()?;
            db.client
                .query(
                    &workspace_consumer_sql(
                        "j.job_id",
                        "j.workspace_id=$1",
                        " ORDER BY j.created_at_ms DESC",
                    ),
                    &[&record.workspace_id],
                )
                .map_err(io)?
                .iter()
                .map(|row| row.get::<_, String>(0))
                .collect::<Vec<_>>()
        };
        let mut result = json!({
            "workspaceId":record.workspace_id,
            "sourceRepo":record.source_repo,
            "sourceRevision":record.source_revision,
            "currentHeadRevision":head,
            "createdAtMs":record.created_unix_ms,
            "headMode":head_mode.as_str(),
            "dirty":dirty,
            "activeJobIds":jobs,
        });
        if include_source_state_digest {
            result["sourceStateDigest"] = json!(universal::workspace_source_state_digest(
                &self.config.executor,
                &request.workspace_id
            )
            .map_err(io)?);
        }
        Ok(result)
    }

    /// Precise get retains the complete source digest and the exact PG
    /// unresolved-or-held consumer readback used to protect close/mutate.
    pub fn get_workspace(
        &self,
        request: &RuntimeWorkspaceGetRequest,
    ) -> RuntimeResult<serde_json::Value> {
        self.get_workspace_projected(request, true, None, None, None)
    }
}
