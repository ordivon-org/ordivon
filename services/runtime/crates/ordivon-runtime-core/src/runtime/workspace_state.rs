use super::{RuntimeError, RuntimeErrorCode, RuntimeResult, RuntimeWorkspaceSummary};
use crate::universal::WorkspaceRecord;

pub(crate) struct WorkspaceProjectionFacts {
    pub current_head_revision: String,
    pub dirty: bool,
    pub source_state_digest: Option<String>,
    pub active_job_ids: Vec<String>,
}

pub(crate) fn project_workspace_summary(
    record: &WorkspaceRecord,
    facts: WorkspaceProjectionFacts,
) -> RuntimeWorkspaceSummary {
    RuntimeWorkspaceSummary {
        workspace_id: record.workspace_id.clone(),
        source_repo: record.source_repo.clone(),
        source_revision: record.source_revision.clone(),
        current_head_revision: facts.current_head_revision,
        created_at_ms: u64::try_from(record.created_unix_ms).unwrap_or(u64::MAX),
        head_mode: "detached".to_string(),
        dirty: facts.dirty,
        source_state_digest: facts.source_state_digest,
        active_job_ids: facts.active_job_ids,
    }
}

pub(crate) fn ensure_workspace_mutation_allowed(active_job_ids: &[String]) -> RuntimeResult<()> {
    if active_job_ids.is_empty() {
        return Ok(());
    }
    Err(RuntimeError::new(
        RuntimeErrorCode::WorkspaceBusy,
        format!(
            "workspace source state is committed by active or held Jobs: {}",
            active_job_ids.join(", ")
        ),
        Some("workspaceId"),
        true,
    ))
}

pub(crate) fn ensure_workspace_close_allowed(
    active_job_ids: &[String],
    git_authority_dependents: &[String],
) -> RuntimeResult<()> {
    if !active_job_ids.is_empty() {
        return Err(RuntimeError::new(
            RuntimeErrorCode::WorkspaceBusy,
            format!(
                "workspace has active or held Jobs: {}",
                active_job_ids.join(", ")
            ),
            Some("workspaceId"),
            true,
        ));
    }
    if !git_authority_dependents.is_empty() {
        return Err(RuntimeError::new(
            RuntimeErrorCode::WorkspaceBusy,
            format!(
                "workspace owns paths required as Git authority by open Workspaces: {}",
                git_authority_dependents.join(", ")
            ),
            Some("workspaceId"),
            true,
        ));
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn record() -> WorkspaceRecord {
        WorkspaceRecord {
            schema_version: 1,
            workspace_id: "workspace-contract".to_string(),
            source_repo: "/source/repo".to_string(),
            source_revision: "a".repeat(40),
            workspace_path: "/runtime/workspaces/workspace-contract".to_string(),
            created_unix_ms: 42,
        }
    }

    #[test]
    fn workspace_projection_preserves_opening_lineage_and_current_head_as_distinct_facts() {
        let summary = project_workspace_summary(
            &record(),
            WorkspaceProjectionFacts {
                current_head_revision: "b".repeat(40),
                dirty: true,
                source_state_digest: Some(format!("sha256:{}", "c".repeat(64))),
                active_job_ids: vec!["job-1".to_string()],
            },
        );
        assert_eq!(summary.source_revision, "a".repeat(40));
        assert_eq!(summary.current_head_revision, "b".repeat(40));
        assert!(summary.dirty);
        assert_eq!(summary.active_job_ids, vec!["job-1"]);
        assert_eq!(summary.head_mode, "detached");
    }

    #[test]
    fn workspace_mutation_guard_rejects_active_or_held_job_ownership() {
        let error = ensure_workspace_mutation_allowed(&["job-a".to_string(), "job-b".to_string()])
            .unwrap_err();
        assert_eq!(error.code, RuntimeErrorCode::WorkspaceBusy);
        assert_eq!(error.field.as_deref(), Some("workspaceId"));
        assert!(error.retryable);
        assert_eq!(
            error.message,
            "workspace source state is committed by active or held Jobs: job-a, job-b"
        );
        assert!(ensure_workspace_mutation_allowed(&[]).is_ok());
    }

    #[test]
    fn workspace_close_guard_prioritizes_active_jobs_before_git_authority_dependents() {
        let error = ensure_workspace_close_allowed(
            &["job-a".to_string()],
            &["workspace-child".to_string()],
        )
        .unwrap_err();
        assert_eq!(error.code, RuntimeErrorCode::WorkspaceBusy);
        assert_eq!(error.message, "workspace has active or held Jobs: job-a");

        let dependent =
            ensure_workspace_close_allowed(&[], &["workspace-child".to_string()]).unwrap_err();
        assert_eq!(dependent.code, RuntimeErrorCode::WorkspaceBusy);
        assert_eq!(
            dependent.message,
            "workspace owns paths required as Git authority by open Workspaces: workspace-child"
        );
        assert!(ensure_workspace_close_allowed(&[], &[]).is_ok());
    }
}
