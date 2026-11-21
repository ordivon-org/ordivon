//! Workspace file mutation is one PG-fenced filesystem effect.
use super::*;
impl PgRuntime {
    /// Mutations reuse the upstream atomic file batch, fenced against PG Job admission.
    /// No SQLite authority, historical Job import, or dual writer is involved.
    pub fn mutate_workspace(
        &self,
        request: &WorkspaceMutateRequest,
    ) -> RuntimeResult<WorkspaceMutateResult> {
        let mut db = self.store()?;
        let mut tx = self.begin_workspace_effect_tx(&mut db)?;
        request
            .validate_shape()
            .map_err(crate::runtime::error::map_universal_error)?;
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
        let consumers = tx
            .query(
                &workspace_consumer_sql("j.execution_plan_json", "j.workspace_id=$1", ""),
                &[&request.workspace_id],
            )
            .map_err(io)?;
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
            .map_err(crate::runtime::error::map_universal_error)?;
        workspace_effect_commit(tx.commit(), "workspace.mutate")?;
        Ok(result)
    }
}
