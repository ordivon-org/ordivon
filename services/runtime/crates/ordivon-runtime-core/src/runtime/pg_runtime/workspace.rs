//! PostgreSQL Runtime Workspace lifecycle and mutation.
use super::*;

impl PgRuntime {
    /// Close only when PG proves no active or held consumer, then reuse the
    /// existing workspace source/dirty/continuation and dependency checks.
    pub fn close_workspace(
        &self,
        request: &WorkspaceCloseRequest,
    ) -> RuntimeResult<WorkspaceCloseResult> {
        let mut db = self.store()?;
        let mut tx = db
            .client
            .build_transaction()
            .isolation_level(postgres::IsolationLevel::Serializable)
            .start()
            .map_err(io)?;
        tx.query_one("SELECT pg_advisory_xact_lock($1)", &[&79245017_i64])
            .map_err(io)?;
        self.require_qualified_writer_tx(&mut tx)?;
        let active:i64=tx.query_one(
            "SELECT count(*) FROM jobs j WHERE j.workspace_id=$1 AND (j.resolution IS NULL OR              EXISTS(SELECT 1 FROM attempts a JOIN concurrency_reservations r              ON r.attempt_id=a.attempt_id WHERE a.job_id=j.job_id AND r.state IN ('active','held_orphaned')))",
            &[&request.workspace_id]
        ).map_err(io)?.get(0);
        if active != 0 {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ConcurrencyLimit,
                "Workspace has PG-owned active or held Jobs",
                Some("workspaceId"),
                false,
            ));
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
    /// Mutations reuse the upstream atomic file batch, fenced against PG Job admission.
    /// No SQLite authority, historical Job import, or dual writer is involved.
    pub fn mutate_workspace(
        &self,
        request: &WorkspaceMutateRequest,
    ) -> RuntimeResult<WorkspaceMutateResult> {
        let mut db = self.store()?;
        let mut tx = db
            .client
            .build_transaction()
            .isolation_level(postgres::IsolationLevel::Serializable)
            .start()
            .map_err(io)?;
        tx.query_one("SELECT pg_advisory_xact_lock($1)", &[&79245017_i64])
            .map_err(io)?;
        self.require_qualified_writer_tx(&mut tx)?;
        request
            .validate_shape()
            .map_err(super::super::error::map_universal_error)?;
        let paths = request
            .mutations
            .iter()
            .map(|m| m.relative_path.clone())
            .collect::<Vec<_>>();
        let access = crate::resource_scheduling::WorkspaceAccess {
            read_only: false,
            read_paths: paths.clone(),
            write_paths: paths,
        };
        let consumers=tx.query("SELECT execution_plan_json FROM jobs j WHERE j.workspace_id=$1 AND (j.resolution IS NULL OR EXISTS(SELECT 1 FROM attempts a JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id WHERE a.job_id=j.job_id AND r.state IN ('active','held_orphaned')))",&[&request.workspace_id]).map_err(io)?;
        for row in consumers {
            let plan: RuntimeExecutionPlan = decode(&row.get::<_, String>(0))?;
            if self
                .scheduling_contract(&plan)?
                .workspace_access
                .conflicts(&access)
            {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::ConcurrencyLimit,
                    "Mutation conflicts with a committed Workspace read/write lease",
                    Some("mutations"),
                    true,
                ));
            }
        }
        let result = universal::mutate_workspace(&self.config.executor, request)
            .map_err(super::super::error::map_universal_error)?;
        workspace_effect_commit(tx.commit(), "workspace.mutate")?;
        Ok(result)
    }
    pub fn executor_config(&self) -> UniversalExecutorConfig {
        self.config.executor.clone()
    }
    /// Read-only, source-bound projection of a fresh-epoch Git Workspace.
    pub fn get_workspace(
        &self,
        request: &RuntimeWorkspaceGetRequest,
    ) -> RuntimeResult<serde_json::Value> {
        if request.schema_version != 1 {
            return Err(RuntimeError::invalid(
                "schemaVersion must be 1",
                "schemaVersion",
            ));
        }
        let record = universal::load_workspace_record(&self.config.executor, &request.workspace_id)
            .map_err(super::super::error::map_universal_error)?;
        // Reuse the canonical Git status-v2 snapshot already consumed by the
        // installed Runtime. HEAD revision, attached/detached mode and dirty
        // state are one physical observation, not two speculative probes.
        let (head, head_mode, dirty) =
            universal::workspace_head_and_dirty_at(Path::new(&record.workspace_path))
                .map_err(super::super::error::map_universal_error)?;
        let digest =
            universal::workspace_source_state_digest(&self.config.executor, &request.workspace_id)
                .map_err(io)?;
        let mut db = self.store()?;
        let jobs=db.client.query(
            "SELECT job_id FROM jobs WHERE workspace_id=$1 AND resolution IS NULL ORDER BY created_at_ms DESC",
            &[&record.workspace_id]
        ).map_err(io)?.iter().map(|r|r.get::<_,String>(0)).collect::<Vec<_>>();
        Ok(json!({
            "workspaceId":record.workspace_id,"sourceRepo":record.source_repo,
            "sourceRevision":record.source_revision,"currentHeadRevision":head,
            "createdAtMs":record.created_unix_ms,"headMode":head_mode.as_str(),
            "dirty":dirty,"sourceStateDigest":digest,"activeJobIds":jobs
        }))
    }
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
            .map_err(super::super::error::map_universal_error)?;
        let issues = inventory
            .issues
            .into_iter()
            .map(|issue| {
                let error = super::super::error::map_universal_error(issue.error);
                json!({
                    "workspaceId": issue.workspace_id,
                    "stage": "inventory",
                    "code": error.code.as_str(),
                    "message": error.message,
                    "retryable": error.retryable
                })
            })
            .collect::<Vec<_>>();
        let mut all = Vec::new();
        for record in inventory.records {
            // Projection failures must not masquerade as a complete inventory.
            let mut value = self.get_workspace(&RuntimeWorkspaceGetRequest {
                schema_version: 1,
                workspace_id: record.workspace_id,
            })?;
            if !request.include_source_state_digest {
                value
                    .as_object_mut()
                    .expect("workspace projection")
                    .remove("sourceStateDigest");
            }
            all.push(value);
        }
        all.sort_by(|a, b| {
            let x = a["createdAtMs"].as_u64().unwrap_or(0);
            let y = b["createdAtMs"].as_u64().unwrap_or(0);
            y.cmp(&x).then_with(|| {
                a["workspaceId"]
                    .as_str()
                    .unwrap_or("")
                    .cmp(b["workspaceId"].as_str().unwrap_or(""))
            })
        });
        if let Some(cursor) = &request.cursor {
            all.retain(|v| {
                let at = v["createdAtMs"].as_u64().unwrap_or(0);
                let id = v["workspaceId"].as_str().unwrap_or("");
                at < cursor.created_at_ms
                    || (at == cursor.created_at_ms && id > cursor.workspace_id.as_str())
            });
        }
        let more = all.len() > request.limit as usize;
        all.truncate(request.limit as usize);
        let next_cursor = if more {
            all.last()
                .map(|v| json!({"createdAtMs":v["createdAtMs"],"workspaceId":v["workspaceId"]}))
        } else {
            None
        };
        Ok(json!({"workspaces":all,"nextCursor":next_cursor,"issues":issues}))
    }
    pub fn open_workspace(
        &self,
        request: &GitWorkspaceCreateRequest,
    ) -> RuntimeResult<CompactWorkspaceOpenResult> {
        let mut db = self.store()?;
        let mut tx = db
            .client
            .build_transaction()
            .isolation_level(postgres::IsolationLevel::Serializable)
            .start()
            .map_err(io)?;
        tx.query_one("SELECT pg_advisory_xact_lock($1)", &[&79245017_i64])
            .map_err(io)?;
        self.require_qualified_writer_tx(&mut tx)?;
        let result = universal::create_git_workspace(&self.config.executor, request)
            .map_err(super::super::error::map_universal_error)?;
        workspace_effect_commit(tx.commit(), "workspace.open")?;
        Ok(result)
    }
}
