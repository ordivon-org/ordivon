//! Bounded Workspace listing and per-page PostgreSQL/Git observation.
use super::{
    io, universal, workspace_consumer_sql, PgRuntime, RuntimeError, RuntimeErrorCode,
    RuntimeResult, RuntimeWorkspaceGetRequest, RuntimeWorkspaceListRequest,
};
use serde_json::json;
use std::path::Path;

// Reuse the existing legacy Runtime bounded-Git-probe pattern (452e0c):
// the PG-only page already batches SQL and still needs current Git truth.
const WORKSPACE_LIST_LIVE_GIT_PARALLELISM: usize = 4;

impl PgRuntime {
    /// Fresh PG workspaces only; historical SQLite Workspace registries are deliberately absent.
    pub fn list_workspaces(
        &self,
        request: &RuntimeWorkspaceListRequest,
    ) -> RuntimeResult<serde_json::Value> {
        if request.schema_version != 1 || request.limit == 0 || request.limit > 100 {
            return Err(RuntimeError::invalid(
                "invalid workspace listing bounds",
                "limit",
            ));
        }
        // Reuse the canonical physical Workspace inventory. Silently dropping
        // corrupt candidates would falsely imply that the Workspace is absent.
        let inventory = universal::list_open_workspace_record_inventory(&self.config.executor)
            .map_err(crate::runtime::error::map_universal_error)?;
        let mut issues = inventory
            .issues
            .into_iter()
            .map(|issue| {
                let error = crate::runtime::error::map_universal_error(issue.error);
                json!({
                    "workspaceId": issue.workspace_id,
                    "stage": "inventory",
                    "code": error.code.as_str(),
                    "message": error.message,
                    "retryable": error.retryable
                })
            })
            .collect::<Vec<_>>();
        if let Some(cursor) = &request.cursor {
            universal::validate_id(&cursor.workspace_id, "cursor.workspaceId")
                .map_err(crate::runtime::error::map_universal_error)?;
        }
        // Page physical records *before* invoking Git/PG projections. The former
        // implementation inspected every open Workspace, even for limit=1;
        // one damaged old Worktree or expensive source hash could fail or stall
        // the entire list, preventing an Agent from seeing the healthy page.
        let mut records = inventory.records;
        records.sort_by(|a, b| {
            b.created_unix_ms
                .cmp(&a.created_unix_ms)
                .then_with(|| a.workspace_id.cmp(&b.workspace_id))
        });
        if let Some(cursor) = &request.cursor {
            records.retain(|record| {
                record.created_unix_ms < u128::from(cursor.created_at_ms)
                    || (record.created_unix_ms == u128::from(cursor.created_at_ms)
                        && record.workspace_id.as_str() > cursor.workspace_id.as_str())
            });
        }
        let more = records.len() > request.limit as usize;
        records.truncate(request.limit as usize);
        // Advance over the physical page, not just projected successes, so a
        // corrupt Git checkout cannot trap callers on an identical cursor.
        let next_cursor = if more {
            records.last().map(|record| {
                json!({
                    "createdAtMs": record.created_unix_ms,
                    "workspaceId": record.workspace_id
                })
            })
        } else {
            None
        };
        // One PostgreSQL readback for the selected page, rather than one new
        // connection, qualification check, and SQL query per Workspace.
        // This is a projection of one PG observation, not a claim that Git
        // and PostgreSQL participate in the same physical snapshot.
        let ids = records
            .iter()
            .map(|record| record.workspace_id.clone())
            .collect::<Vec<_>>();
        let mut active_jobs: std::collections::BTreeMap<String, Vec<String>> =
            std::collections::BTreeMap::new();
        if !ids.is_empty() {
            let mut db = self.store()?;
            for row in db
                .client
                .query(
                    &workspace_consumer_sql(
                        "j.workspace_id,j.job_id",
                        "j.workspace_id = ANY($1::TEXT[])",
                        " ORDER BY j.created_at_ms DESC",
                    ),
                    &[&ids],
                )
                .map_err(io)?
            {
                active_jobs
                    .entry(row.get::<_, String>(0))
                    .or_default()
                    .push(row.get::<_, String>(1));
            }
        }
        // Git status is the real source of HEAD/dirty truth. Bound read-only
        // fan-out within the selected physical page; never cache these results
        // or treat a successful Git probe as original Run consumer release.
        // Exact digest mode intentionally stays serial to bound disk pressure.
        let live_git = if records.len() <= 1 || request.include_source_state_digest {
            records
                .iter()
                .map(|record| {
                    universal::workspace_head_and_dirty_at(Path::new(&record.workspace_path))
                })
                .collect::<Vec<_>>()
        } else {
            let workers = records.len().min(WORKSPACE_LIST_LIVE_GIT_PARALLELISM);
            let chunk_size = records.len().div_ceil(workers);
            std::thread::scope(|scope| -> RuntimeResult<Vec<_>> {
                let mut threads = Vec::with_capacity(workers);
                for (chunk_index, chunk) in records.chunks(chunk_size).enumerate() {
                    threads.push(scope.spawn(move || {
                        chunk
                            .iter()
                            .enumerate()
                            .map(|(offset, record)| {
                                (
                                    chunk_index * chunk_size + offset,
                                    universal::workspace_head_and_dirty_at(Path::new(
                                        &record.workspace_path,
                                    )),
                                )
                            })
                            .collect::<Vec<_>>()
                    }));
                }
                let mut indexed = Vec::with_capacity(records.len());
                for worker in threads {
                    indexed.extend(worker.join().map_err(|_| {
                        RuntimeError::new(
                            RuntimeErrorCode::ToolFailed,
                            "Workspace live Git projection worker panicked",
                            Some("workspaceId"),
                            false,
                        )
                    })?);
                }
                indexed.sort_by_key(|(index, _)| *index);
                Ok(indexed.into_iter().map(|(_, git)| git).collect())
            })?
        };
        let mut workspaces = Vec::with_capacity(records.len());
        for (record, git) in records.into_iter().zip(live_git) {
            let workspace_id = record.workspace_id.clone();
            let jobs = active_jobs.remove(&workspace_id).unwrap_or_default();
            match self.get_workspace_projected(
                &RuntimeWorkspaceGetRequest {
                    schema_version: 1,
                    workspace_id: workspace_id.clone(),
                },
                request.include_source_state_digest,
                Some(jobs),
                Some(git),
                Some(&record),
            ) {
                Ok(value) => {
                    workspaces.push(value);
                }
                Err(error) if error.is_reconciliation_fatal() => return Err(error),
                Err(error) => issues.push(json!({
                    "workspaceId": workspace_id,
                    "stage": "projection",
                    "code": error.code.as_str(),
                    "message": error.message,
                    "retryable": error.retryable
                })),
            }
        }
        Ok(json!({
            "workspaces": workspaces,
            "nextCursor": next_cursor,
            "issues": issues
        }))
    }
}
