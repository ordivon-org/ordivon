//! Pure classification of candidate corruption and scoped reconciliation errors.
//! These decisions have no PostgreSQL or native OS side effects.
use super::*;

/// A corrupt committed candidate is a Job-local *invalid request*, not a
/// failed PostgreSQL Registry. Preserve that distinction in Job events so an
/// Agent does not mistake one poisoned row for a node-wide database outage.
pub(super) fn decode_accepted_candidate(raw: &str) -> RuntimeResult<RuntimeExecutionPlan> {
    serde_json::from_str(raw).map_err(|parse| {
        RuntimeError::new(
            RuntimeErrorCode::InvalidRequest,
            format!("committed accepted Job has invalid execution plan: {parse}"),
            Some("executionPlan"),
            false,
        )
    })
}

/// Only a local, explicitly attributable failure may be isolated. A broken
/// PostgreSQL writer/transaction or unknown node observation applies to the
/// entire scheduler and must remain UNKNOWN rather than skipping all jobs.
pub(super) fn is_job_scoped_reconciliation_error(error: &RuntimeError) -> bool {
    matches!(
        error.code,
        RuntimeErrorCode::ProviderStateMismatch
            | RuntimeErrorCode::LaunchIdentityMismatch
            | RuntimeErrorCode::WorkspaceStateMismatch
            | RuntimeErrorCode::WorkspaceNotFound
            | RuntimeErrorCode::ResultIdentityConflict
            | RuntimeErrorCode::ArtifactIdentityConflict
            | RuntimeErrorCode::ReconciliationRequired
            | RuntimeErrorCode::DispatchOutcomeUnknown
    )
}
