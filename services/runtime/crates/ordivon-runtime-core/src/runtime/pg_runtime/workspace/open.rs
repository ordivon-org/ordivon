//! Original qualified PG lock + native Git Workspace birth.
use super::{
    universal, workspace_effect_commit, CompactWorkspaceOpenResult, GitWorkspaceCreateRequest,
    PgRuntime, RuntimeResult,
};

impl PgRuntime {
    pub fn open_workspace(
        &self,
        request: &GitWorkspaceCreateRequest,
    ) -> RuntimeResult<CompactWorkspaceOpenResult> {
        let mut db = self.store()?;
        let tx = self.begin_workspace_effect_tx(&mut db)?;
        // Both host VHD backing and guest PostgreSQL/worktree carriers must
        // pass while the existing PG Workspace effect/admission lock is held.
        crate::runtime::pg_runtime::workspace_headroom::ensure_workspace_headroom(
            &self.config.workspace_headroom,
        )?;
        let mut result = universal::create_git_workspace(&self.config.executor, request)
            .map_err(crate::runtime::error::map_universal_error)?;
        workspace_effect_commit(tx.commit(), "workspace.open")?;
        result.retention_notice = Some(
            "PG Runtime Workspace is temporary. The systemd lifecycle timer may be disabled; when enabled, its cadence is operator-defined and no cleanup is guaranteed. Four hours after the latest Job activity is a minimum quiet period, not an ownership lease or promised cleanup time. An eligible clean Workspace may be reclaimed after native Job, source, and policy checks. Other Agent or external consumers are not proven absent by Job completion or a caller's consumerReleased assertion. Publish valuable source and ignored outputs to their real Git/Artifact/destination consumers and read them back before relinquishing the Workspace. Continue unfinished work in a new or retained Workspace."
                .to_string(),
        );
        Ok(result)
    }
}
