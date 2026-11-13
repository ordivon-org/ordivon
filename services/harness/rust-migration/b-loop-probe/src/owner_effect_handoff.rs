//! Qualification of ONE candidate physical Owner request against B's already
//! source-authenticated Harness Tool Intent/Fence CAS observations.
//!
//! We neither dispatch nor mint an execution permit. This is a pure proof
//! obligation on bytes to be handed to the natural Runtime/Gateway Owner.
//! Owner principal, live Run revision, idempotent Job admission, external
//! receipt and UNKNOWN reconciliation remain authoritative elsewhere.
//!
//! Mature A sealed canonical representation is reused byte-for-byte:
//! no second JSON codec, registry, manager, or mutable global cache.

use ordivon_harness_core::{canonical_bytes, digest_bytes, CanonicalDocument, CanonicalRef};

use crate::pg_tool_head::{ObservedToolHead, ToolHeadStanding};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum OwnerHandoffError {
    UnqualifiedHistoricalToolHead,
    CommittedRequestMismatch,
    InvalidOwnerRequest,
    UnboundDispatchFence,
}

/// Equality of all sorted, bounded canonical JSON object fields except one
/// field that has a precisely defined Source protocol augmentation.
fn same_object_except(
    original: CanonicalRef<'_>,
    final_view: CanonicalRef<'_>,
    excluded: &str,
) -> bool {
    match (
        original.object_len(),
        final_view.object_len(),
        original.object_entries(),
    ) {
        (Some(before), Some(after), Some(fields)) if before == after => fields
            .filter(|(key, _)| *key != excluded)
            .all(|(key, value)| {
                final_view
                    .field(key)
                    .is_some_and(|v| value.canonical_bytes() == v.canonical_bytes())
            }),
        _ => false,
    }
}

/// Validates only the exact bytes of a pre-Owner workspace.exec request.
///
/// The recorded Python Harness ToolIntent SHA covers the original request.
/// Source Python appends one Fence reference after journaling, and NOTHING
/// ELSE may change. This prevents proposal/foreign-reference/owner-request
/// drift before a future Native Rust Runner submits a physical action.
///
/// A successful return means *request bytes are source-bound*, not that
/// the underlying Run is still live or the Owner accepted execution.
pub fn qualify_workspace_exec_owner_handoff(
    observed: &ObservedToolHead,
    original_request: &CanonicalDocument,
    outbound_request: &CanonicalDocument,
) -> Result<(), OwnerHandoffError> {
    if observed.standing() != ToolHeadStanding::PreparedNeedsOwnerAdmission
        || !observed.prepared_revision_is_current()
        || observed.runtime_operation() != "workspace.exec"
    {
        return Err(OwnerHandoffError::UnqualifiedHistoricalToolHead);
    }
    if digest_bytes(&canonical_bytes(original_request))
        != observed.original_runtime_request_digest()
        || original_request
            .field("clientRequestId")
            .and_then(|v| v.as_str())
            != Some(observed.client_request_id())
    {
        return Err(OwnerHandoffError::CommittedRequestMismatch);
    }

    if outbound_request
        .field("clientRequestId")
        .and_then(|v| v.as_str())
        != Some(observed.client_request_id())
        || !same_object_except(
            original_request.as_borrowed(),
            outbound_request.as_borrowed(),
            "execution",
        )
    {
        return Err(OwnerHandoffError::InvalidOwnerRequest);
    }
    let original_execution = original_request
        .field("execution")
        .ok_or(OwnerHandoffError::InvalidOwnerRequest)?;
    let actual_execution = outbound_request
        .field("execution")
        .ok_or(OwnerHandoffError::InvalidOwnerRequest)?;
    if !same_object_except(original_execution, actual_execution, "foreignReferences") {
        return Err(OwnerHandoffError::InvalidOwnerRequest);
    }
    let before = original_execution
        .field("foreignReferences")
        .ok_or(OwnerHandoffError::InvalidOwnerRequest)?;
    let after = actual_execution
        .field("foreignReferences")
        .ok_or(OwnerHandoffError::InvalidOwnerRequest)?;
    let before_len = before
        .array_len()
        .ok_or(OwnerHandoffError::InvalidOwnerRequest)?;
    if after.array_len() != Some(before_len + 1) {
        return Err(OwnerHandoffError::UnboundDispatchFence);
    }
    for idx in 0..before_len {
        let old = before
            .index(idx)
            .ok_or(OwnerHandoffError::InvalidOwnerRequest)?;
        let actual = after
            .index(idx)
            .ok_or(OwnerHandoffError::InvalidOwnerRequest)?;
        if old.object_len().is_none() || old.canonical_bytes() != actual.canonical_bytes() {
            return Err(OwnerHandoffError::InvalidOwnerRequest);
        }
        if old.field("type").and_then(|v| v.as_str()) == Some("dispatch_fence") {
            return Err(OwnerHandoffError::UnboundDispatchFence);
        }
    }
    let last = after
        .index(before_len)
        .ok_or(OwnerHandoffError::UnboundDispatchFence)?;
    let generation = observed.prepared_revision().to_string();
    if last.object_len() != Some(5)
        || last.field("namespace").and_then(|v| v.as_str()) != Some("ordivon.harness")
        || last.field("type").and_then(|v| v.as_str()) != Some("dispatch_fence")
        || last.field("id").and_then(|v| v.as_str()) != Some(observed.fence_id())
        || last.field("generation").and_then(|v| v.as_str()) != Some(&generation)
        || last.field("digest").and_then(|v| v.as_str()) != Some(observed.fence_digest())
    {
        return Err(OwnerHandoffError::UnboundDispatchFence);
    }
    Ok(())
}
