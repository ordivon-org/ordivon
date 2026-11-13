//! Runtime Owner delivery observation, refined from Python
//! runtime_bridge._runtime_delivery_state. A recovery hint, never an execution
//! permit, transport call, retry authority, or domain success.
use ordivon_harness_core::{CanonicalDocument, CanonicalRef};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RuntimeDeliveryDecision {
    Terminal,
    Reconcile,
    Unknown,
}
impl RuntimeDeliveryDecision {
    pub fn as_source_str(self) -> &'static str {
        match self {
            Self::Terminal => "terminal",
            Self::Reconcile => "reconcile",
            Self::Unknown => "unknown",
        }
    }
}
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RuntimeDeliveryError {
    InvalidOwnerObservation,
}
fn required_bool(doc: &CanonicalDocument, key: &str) -> Result<bool, RuntimeDeliveryError> {
    doc.field(key)
        .and_then(CanonicalRef::as_bool)
        .ok_or(RuntimeDeliveryError::InvalidOwnerObservation)
}
fn execution_disposition(doc: &CanonicalDocument) -> Result<Option<&str>, RuntimeDeliveryError> {
    let Some(value) = doc.field("executionDisposition") else {
        return Ok(None);
    };
    if value.is_null() {
        return Ok(None);
    }
    let kind = value
        .as_str()
        .ok_or(RuntimeDeliveryError::InvalidOwnerObservation)?;
    if !matches!(
        kind,
        "succeeded" | "failed" | "timed_out" | "cancelled" | "lost" | "orphaned"
    ) {
        return Err(RuntimeDeliveryError::InvalidOwnerObservation);
    }
    Ok(Some(kind))
}

/// Exact Python source validation order. Runtime status is a legacy summary:
/// only executionTerminal, executionDisposition, deliveryDisposition,
/// recoveryRequired and resultAvailable qualify mechanical delivery.
/// semanticCompletionEvaluated must be False (not domain completion).
pub fn interpret_runtime_delivery(
    payload: &CanonicalDocument,
) -> Result<RuntimeDeliveryDecision, RuntimeDeliveryError> {
    use RuntimeDeliveryDecision as Decision;
    use RuntimeDeliveryError as Error;
    let terminal = required_bool(payload, "executionTerminal")?;
    let execution = execution_disposition(payload)?;
    let delivery = payload
        .field("deliveryDisposition")
        .and_then(CanonicalRef::as_str)
        .ok_or(Error::InvalidOwnerObservation)?;
    if !matches!(
        delivery,
        "in_progress" | "committed" | "reconciliation_required" | "unknown"
    ) || (delivery == "committed" && matches!(execution, Some("lost" | "orphaned")))
    {
        return Err(Error::InvalidOwnerObservation);
    }
    let recovery_required = required_bool(payload, "recoveryRequired")?;
    let result_available = required_bool(payload, "resultAvailable")?;
    if payload
        .field("semanticCompletionEvaluated")
        .and_then(CanonicalRef::as_bool)
        != Some(false)
    {
        return Err(Error::InvalidOwnerObservation);
    }
    if recovery_required || delivery == "reconciliation_required" {
        return Ok(Decision::Reconcile);
    }
    if delivery == "unknown" {
        if !terminal || execution != Some("lost") || !result_available {
            return Err(Error::InvalidOwnerObservation);
        }
        return Ok(Decision::Unknown);
    }
    if delivery == "in_progress" {
        if terminal || execution.is_some() || result_available {
            return Err(Error::InvalidOwnerObservation);
        }
        return Ok(Decision::Reconcile);
    }
    if !terminal || execution.is_none() || !result_available {
        return Err(Error::InvalidOwnerObservation);
    }
    Ok(Decision::Terminal)
}
#[cfg(test)]
mod tests {
    use super::*;
    use ordivon_harness_core::loads_strict;
    #[test]
    fn succeeded_runtime_status_cannot_override_required_reconciliation() {
        let doc=loads_strict(r#"{"status":"succeeded","executionTerminal":true,"executionDisposition":"succeeded","deliveryDisposition":"reconciliation_required","recoveryRequired":false,"resultAvailable":true,"semanticCompletionEvaluated":false}"#).unwrap();
        assert_eq!(
            interpret_runtime_delivery(&doc),
            Ok(RuntimeDeliveryDecision::Reconcile)
        );
    }
    #[test]
    fn lost_unknown_never_maps_to_success_or_retry() {
        let doc=loads_strict(r#"{"status":"succeeded","executionTerminal":true,"executionDisposition":"lost","deliveryDisposition":"unknown","recoveryRequired":false,"resultAvailable":true,"semanticCompletionEvaluated":false}"#).unwrap();
        assert_eq!(
            interpret_runtime_delivery(&doc),
            Ok(RuntimeDeliveryDecision::Unknown)
        );
    }
}

/// The Runtime Owner alone resolves the actual Job. One complete task.list
/// response can bind an immutable clientRequestId + workspaceId to one exact
/// jobId; a paginated/incomplete/ambiguous response cannot yield a Job grant.
/// No response here means "no qualified observation", NEVER "effect absent".
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct QualifiedRuntimeJob {
    job_id: String,
    client_request_id: String,
    workspace_id: String,
}
impl QualifiedRuntimeJob {
    pub fn job_id(&self) -> &str {
        &self.job_id
    }
    pub fn client_request_id(&self) -> &str {
        &self.client_request_id
    }
    pub fn workspace_id(&self) -> &str {
        &self.workspace_id
    }
}
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RuntimeOwnerEvidenceError {
    InvalidIdentity,
    InvalidOwnerPage,
    IdentityMismatch,
    PaginationRequired,
    MissingOrAmbiguousJob,
    ObservationMismatch,
    InvalidOwnerObservation,
}
fn trimmed(value: &str) -> bool {
    // Reuse the canonical Python str.strip-compatible boundary rather
    // than inventing another identity parser for Owner observations.
    crate::identity::valid_trimmed(value, usize::MAX)
}
/// Only the terminal page of a SINGLE-page Runtime task.list result is
/// eligible. Multi-page recovery belongs to the existing Python Owner
/// lookup until an equivalent Rust durable pagination consumer exists.
/// Refuses any claimed match without unique Owner Job identity.
pub fn qualify_single_page_runtime_job(
    page: &CanonicalDocument,
    expected_client_request_id: &str,
    expected_workspace_id: &str,
) -> Result<QualifiedRuntimeJob, RuntimeOwnerEvidenceError> {
    use RuntimeOwnerEvidenceError as Error;
    if !trimmed(expected_client_request_id) || !trimmed(expected_workspace_id) {
        return Err(Error::InvalidIdentity);
    }
    let jobs = page.field("jobs").ok_or(Error::InvalidOwnerPage)?;
    let size = jobs.array_len().ok_or(Error::InvalidOwnerPage)?;
    if page
        .field("nextCursor")
        .is_some_and(|cursor| !cursor.is_null())
    {
        return Err(Error::PaginationRequired);
    }
    if size != 1 {
        return Err(Error::MissingOrAmbiguousJob);
    }
    let only = jobs.index(0).ok_or(Error::InvalidOwnerPage)?;
    let client = only
        .field("clientRequestId")
        .and_then(CanonicalRef::as_str)
        .ok_or(Error::InvalidOwnerPage)?;
    let workspace = only
        .field("workspaceId")
        .and_then(CanonicalRef::as_str)
        .ok_or(Error::InvalidOwnerPage)?;
    if client != expected_client_request_id || workspace != expected_workspace_id {
        return Err(Error::IdentityMismatch);
    }
    let id = only
        .field("jobId")
        .and_then(CanonicalRef::as_str)
        .ok_or(Error::InvalidOwnerPage)?;
    if !trimmed(id) {
        return Err(Error::InvalidOwnerPage);
    }
    Ok(QualifiedRuntimeJob {
        job_id: id.to_owned(),
        client_request_id: client.to_owned(),
        workspace_id: workspace.to_owned(),
    })
}
/// Bind the Runtime Owner's already-filtered task.list observation to a
/// *real A-PG-authenticated* B Tool Intent clientRequestId. The Run snapshot
/// might have been superseded; this stays read-only and cannot issue a Job.
pub fn qualify_runtime_job_for_tool_head(
    tool: &crate::pg_tool_head::ObservedToolHead,
    owner_list_page: &CanonicalDocument,
    workspace_id: &str,
) -> Result<QualifiedRuntimeJob, RuntimeOwnerEvidenceError> {
    qualify_single_page_runtime_job(owner_list_page, tool.client_request_id(), workspace_id)
}
/// A Runtime task.observe payload must match a jobId qualified from the
/// exact owner lookup. Neither a committed Run Journal nor a compatible
/// status string can substitute for this binding.
pub fn interpret_qualified_runtime_observation(
    job: &QualifiedRuntimeJob,
    observation: &CanonicalDocument,
) -> Result<RuntimeDeliveryDecision, RuntimeOwnerEvidenceError> {
    let id = observation
        .field("jobId")
        .and_then(CanonicalRef::as_str)
        .ok_or(RuntimeOwnerEvidenceError::ObservationMismatch)?;
    if id != job.job_id {
        return Err(RuntimeOwnerEvidenceError::ObservationMismatch);
    }
    interpret_runtime_delivery(observation)
        .map_err(|_| RuntimeOwnerEvidenceError::InvalidOwnerObservation)
}
#[cfg(test)]
mod runtime_owner_identity_tests {
    use super::*;
    use ordivon_harness_core::loads_strict;
    #[test]
    fn owner_job_identity_precedes_delivery_status() {
        let page=loads_strict(r#"{"jobs":[{"jobId":"job:one","clientRequestId":"req:one","workspaceId":"ws:one","status":"succeeded"}],"nextCursor":null}"#).unwrap();
        let job = qualify_single_page_runtime_job(&page, "req:one", "ws:one").unwrap();
        let result=loads_strict(r#"{"jobId":"job:one","status":"succeeded","executionTerminal":true,"executionDisposition":"succeeded","deliveryDisposition":"reconciliation_required","recoveryRequired":false,"resultAvailable":true,"semanticCompletionEvaluated":false}"#).unwrap();
        assert_eq!(
            interpret_qualified_runtime_observation(&job, &result),
            Ok(RuntimeDeliveryDecision::Reconcile)
        );
        let forged=loads_strict(r#"{"jobId":"job:other","status":"succeeded","executionTerminal":true,"executionDisposition":"succeeded","deliveryDisposition":"committed","recoveryRequired":false,"resultAvailable":true,"semanticCompletionEvaluated":false}"#).unwrap();
        assert_eq!(
            interpret_qualified_runtime_observation(&job, &forged),
            Err(RuntimeOwnerEvidenceError::ObservationMismatch)
        );
    }
    #[test]
    fn no_job_or_ambiguous_or_cross_workspace_is_not_effect_absence() {
        for (page, err) in [
            (
                r#"{"jobs":[],"nextCursor":null}"#,
                RuntimeOwnerEvidenceError::MissingOrAmbiguousJob,
            ),
            (
                r#"{"jobs":[{"jobId":"job:one","clientRequestId":"req:one","workspaceId":"ws:one"},{"jobId":"job:two","clientRequestId":"req:one","workspaceId":"ws:one"}],"nextCursor":null}"#,
                RuntimeOwnerEvidenceError::MissingOrAmbiguousJob,
            ),
            (
                r#"{"jobs":[{"jobId":"job:one","clientRequestId":"req:one","workspaceId":"ws:two"}],"nextCursor":null}"#,
                RuntimeOwnerEvidenceError::IdentityMismatch,
            ),
            (
                r#"{"jobs":[{"jobId":"job:one","clientRequestId":"req:one","workspaceId":"ws:one"}],"nextCursor":{"createdAtMs":1,"jobId":"job:one"}}"#,
                RuntimeOwnerEvidenceError::PaginationRequired,
            ),
        ] {
            let doc = loads_strict(page).unwrap();
            assert_eq!(
                qualify_single_page_runtime_job(&doc, "req:one", "ws:one").unwrap_err(),
                err
            );
        }
    }
}
