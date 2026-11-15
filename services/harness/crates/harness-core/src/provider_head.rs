//! B-owned read-only Provider recovery projection of the CURRENT Python v4
//! Provider record. A owns sealed Canonical bytes and the durable PG writer.
//! No model request, retry, cancellation, or external effect is sent here.
use crate::{canonical_bytes, digest_bytes, CanonicalDocument};
use std::cmp::Ordering;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ProviderStatus {
    Claimed,
    Dispatching,
    Completed,
    Failed,
    Unknown,
}

impl ProviderStatus {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Claimed => "claimed",
            Self::Dispatching => "dispatching",
            Self::Completed => "completed",
            Self::Failed => "failed",
            Self::Unknown => "unknown",
        }
    }
}

/// Original Python Run continuity clears the current Provider head after
/// source-defined Snapshot/Tool/Run terminal boundaries. Both PG Writer
/// and read-only recovery must apply exactly the same clearing semantics.
pub fn provider_event_clears_head(event_kind: &str) -> bool {
    matches!(
        event_kind,
        "harness.snapshot-recorded"
            | "harness.working-set-recorded"
            | "harness.run-paused"
            | "harness.tool-step-prepared"
            | "harness.run-stopped"
            | "harness.run-completed"
            | "harness.run-failed"
    )
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum RecoveryPosture {
    /// A claimed record alone is not a current lease, fence or dispatch grant.
    RecheckClaimAndDurableFence,
    /// A durable dispatch marker may represent a sent physical request.
    ReconcileWithProviderOwner,
    /// Result object may have been redacted; canonical result digest remains.
    ReadCommittedResult,
    /// The failure receipt dispatchSafety is necessary before a safe retry.
    CheckFailureReceiptAndRetryBudget,
    /// No inference about actual Provider effect; do not silently resend.
    RetainUnknownAndReconcile,
}

impl ProviderStatus {
    pub fn recovery_posture(self) -> RecoveryPosture {
        match self {
            Self::Claimed => RecoveryPosture::RecheckClaimAndDurableFence,
            Self::Dispatching => RecoveryPosture::ReconcileWithProviderOwner,
            Self::Completed => RecoveryPosture::ReadCommittedResult,
            Self::Failed => RecoveryPosture::CheckFailureReceiptAndRetryBudget,
            Self::Unknown => RecoveryPosture::RetainUnknownAndReconcile,
        }
    }
}

/// Python integer identity retained as normalized decimal text. A's sealed
/// Canonical reader already validates the spelling (including -0 -> 0).
/// Comparison is numeric, not lexicographic: 9 is less than 10.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct NonnegativeDecimal(String);

impl NonnegativeDecimal {
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl Ord for NonnegativeDecimal {
    fn cmp(&self, other: &Self) -> Ordering {
        self.0
            .len()
            .cmp(&other.0.len())
            .then_with(|| self.0.cmp(&other.0))
    }
}

impl PartialOrd for NonnegativeDecimal {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ProviderRecordHead {
    pub provider_call_id: String,
    pub turn_id: String,
    pub turn_sequence: NonnegativeDecimal,
    pub claim_generation: NonnegativeDecimal,
    pub request_digest: String,
    pub provider_request_digest: String,
    pub status: ProviderStatus,
    pub result_digest: Option<String>,
    pub result_object_digest: Option<String>,
    pub failure_digest: Option<String>,
    pub previous_record_digest: Option<String>,
    pub canonical_digest: String,
}

/// Exact same physical Provider Call attempt identity across transitions.
/// The Python Source permits a new-turn CLAIMED to switch ProviderCallId,
/// but non-CLAIMED V4 transitions MUST preserve these six fields.
impl ProviderRecordHead {
    pub fn same_attempt_identity(&self, other: &Self) -> bool {
        self.provider_call_id == other.provider_call_id
            && self.turn_id == other.turn_id
            && self.turn_sequence == other.turn_sequence
            && self.claim_generation == other.claim_generation
            && self.request_digest == other.request_digest
            && self.provider_request_digest == other.provider_request_digest
    }
}

/// Single source-semantic FailureReceipt admission shared by the A-owned
/// PG Writer and the B-owned SELECT-only recovery consumer. The Reader
/// projects only a boolean for private detail; it must never disclose it.
#[derive(Clone, Copy)]
pub struct ProviderFailureSourceView<'a> {
    pub field_count: Option<usize>,
    pub version_one: bool,
    pub kind: Option<&'a str>,
    pub detail_source_valid: bool,
    pub provider_call_id: Option<&'a str>,
    pub request_digest: Option<&'a str>,
    pub provider_request_digest: Option<&'a str>,
    pub failure_code: Option<&'a str>,
    pub dispatch_safety: Option<&'a str>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ProviderFailureSourceError {
    InvalidForm,
    IdentityMismatch,
}

/// Validate complete protocol shape, known retry-safety semantics and
/// cross-Event attempt binding. It is neither a retry grant nor an
/// observation of external billing/physical effects.
pub fn validate_provider_failure_source(
    view: ProviderFailureSourceView<'_>,
    receipt_digest: &str,
    record: &ProviderRecordHead,
) -> Result<(), ProviderFailureSourceError> {
    use ProviderFailureSourceError::{IdentityMismatch, InvalidForm};
    if view.field_count != Some(8)
        || !view.version_one
        || view.kind != Some("ordivon.harness-provider-call-failure")
        || !view.detail_source_valid
    {
        return Err(InvalidForm);
    }
    fn text(source: Option<&str>) -> Result<&str, ProviderFailureSourceError> {
        let value = source.ok_or(InvalidForm)?;
        if !crate::valid_trimmed(value, 512) {
            return Err(InvalidForm);
        }
        Ok(value)
    }
    let call = text(view.provider_call_id)?;
    let request = text(view.request_digest)?;
    let provider_request = text(view.provider_request_digest)?;
    let code = text(view.failure_code)?;
    let safety = text(view.dispatch_safety)?;
    if !call.starts_with("provider-call:")
        || !is_digest(request)
        || !is_digest(provider_request)
        || !matches!(
            code,
            "provider_failed"
                | "provider_timeout"
                | "provider_transport_failed"
                | "provider_rejected"
                | "provider_unavailable"
        )
        || !matches!(
            safety,
            "pre_dispatch_safe" | "provider_rejected" | "dispatch_ambiguous"
        )
    {
        return Err(InvalidForm);
    }
    if record.failure_digest.as_deref() != Some(receipt_digest)
        || call != record.provider_call_id
        || request != record.request_digest
        || provider_request != record.provider_request_digest
    {
        return Err(IdentityMismatch);
    }
    Ok(())
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ProviderRecordError {
    InvalidV4Record,
}

const REQUIRED_FIELDS: [&str; 28] = [
    "schemaVersion",
    "kind",
    "recordId",
    "providerCallId",
    "harnessRunId",
    "bindingDigest",
    "sourceKind",
    "sourceDigest",
    "sourceObjectDigest",
    "stateObjectDigest",
    "turnId",
    "turnSequence",
    "requestDigest",
    "requestObjectDigest",
    "providerRequestDigest",
    "adapterId",
    "requestedModelId",
    "holderId",
    "claimGeneration",
    "status",
    "resultDigest",
    "resultObjectDigest",
    "failureDigest",
    "failureObjectDigest",
    "previousRecordDigest",
    "issuedAtMs",
    "expiresAtMs",
    "recordedAtMs",
];

fn field<'a>(
    document: &'a CanonicalDocument,
    key: &str,
) -> Result<crate::CanonicalRef<'a>, ProviderRecordError> {
    document
        .field(key)
        .ok_or(ProviderRecordError::InvalidV4Record)
}
fn value_text(document: &CanonicalDocument, key: &str) -> Result<String, ProviderRecordError> {
    field(document, key)?
        .as_str()
        .map(ToOwned::to_owned)
        .ok_or(ProviderRecordError::InvalidV4Record)
}
fn is_digest(value: &str) -> bool {
    value.len() == 71
        && value.starts_with("sha256:")
        && value[7..]
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}
fn text(
    document: &CanonicalDocument,
    key: &str,
    prefix: Option<&str>,
    max_bytes: usize,
) -> Result<String, ProviderRecordError> {
    let value = value_text(document, key)?;
    if !crate::valid_trimmed(&value, max_bytes)
        || prefix.is_some_and(|prefix| !value.starts_with(&format!("{prefix}:")))
    {
        return Err(ProviderRecordError::InvalidV4Record);
    }
    Ok(value)
}
fn digest(document: &CanonicalDocument, key: &str) -> Result<String, ProviderRecordError> {
    let value = value_text(document, key)?;
    if !is_digest(&value) {
        return Err(ProviderRecordError::InvalidV4Record);
    }
    Ok(value)
}
fn optional_digest(
    document: &CanonicalDocument,
    key: &str,
) -> Result<Option<String>, ProviderRecordError> {
    field(document, key)?;
    if document.get(key) == Some(CanonicalDocument::null()) {
        Ok(None)
    } else {
        digest(document, key).map(Some)
    }
}
fn nonnegative_decimal(
    document: &CanonicalDocument,
    key: &str,
    minimum_one: bool,
) -> Result<NonnegativeDecimal, ProviderRecordError> {
    let value = field(document, key)?;
    let digits = value
        .integer_text()
        .ok_or(ProviderRecordError::InvalidV4Record)?;
    // Python validates arbitrary-precision integers. Do not narrow a valid
    // historical counter/timestamp into u64 or report it as a corrupt Run.
    if digits.starts_with('-') || (minimum_one && digits == "0") {
        return Err(ProviderRecordError::InvalidV4Record);
    }
    Ok(NonnegativeDecimal(digits.to_owned()))
}

/// Must be called ONLY with bytes authenticated by A's CAS/Journal layer.
/// The sealed JSON parser alone does not authenticate a PG Run or grant
/// Provider dispatch authority. Preserve result digests when content is
/// deliberately absent under the current privacy contract.
pub fn inspect_v4(document: &CanonicalDocument) -> Result<ProviderRecordHead, ProviderRecordError> {
    let keys: Vec<&str> = document
        .object_entries()
        .ok_or(ProviderRecordError::InvalidV4Record)?
        .map(|(key, _)| key)
        .collect();
    if keys.len() != REQUIRED_FIELDS.len()
        || REQUIRED_FIELDS.iter().any(|key| !keys.contains(key))
        || field(document, "schemaVersion")?.integer_text() != Some("4")
        || value_text(document, "kind")? != "ordivon.harness-provider-call-record"
    {
        return Err(ProviderRecordError::InvalidV4Record);
    }

    text(
        document,
        "recordId",
        Some("harness-provider-call-record"),
        300,
    )?;
    let provider_call_id = text(document, "providerCallId", Some("provider-call"), 300)?;
    text(document, "harnessRunId", Some("harness-run"), 300)?;
    digest(document, "bindingDigest")?;
    if !matches!(
        value_text(document, "sourceKind")?.as_str(),
        "assignment" | "snapshot"
    ) {
        return Err(ProviderRecordError::InvalidV4Record);
    }
    for key in ["sourceDigest", "sourceObjectDigest", "stateObjectDigest"] {
        digest(document, key)?;
    }
    let turn_id = text(document, "turnId", Some("turn"), 300)?;
    let turn_sequence = nonnegative_decimal(document, "turnSequence", true)?;
    let request_digest = digest(document, "requestDigest")?;
    optional_digest(document, "requestObjectDigest")?;
    let provider_request_digest = digest(document, "providerRequestDigest")?;
    for key in ["adapterId", "requestedModelId", "holderId"] {
        text(document, key, None, 300)?;
    }
    let claim_generation = nonnegative_decimal(document, "claimGeneration", true)?;
    let status = match value_text(document, "status")?.as_str() {
        "claimed" => ProviderStatus::Claimed,
        "dispatching" => ProviderStatus::Dispatching,
        "completed" => ProviderStatus::Completed,
        "failed" => ProviderStatus::Failed,
        "unknown" => ProviderStatus::Unknown,
        _ => return Err(ProviderRecordError::InvalidV4Record),
    };
    let result_digest = optional_digest(document, "resultDigest")?;
    let result_object_digest = optional_digest(document, "resultObjectDigest")?;
    let failure_digest = optional_digest(document, "failureDigest")?;
    let failure_object_digest = optional_digest(document, "failureObjectDigest")?;
    let previous_record_digest = optional_digest(document, "previousRecordDigest")?;
    let issued = nonnegative_decimal(document, "issuedAtMs", false)?;
    let expires = nonnegative_decimal(document, "expiresAtMs", false)?;
    nonnegative_decimal(document, "recordedAtMs", false)?;
    let initial_claim = status == ProviderStatus::Claimed && claim_generation.as_str() == "1";
    if expires <= issued || (!initial_claim && previous_record_digest.is_none()) {
        return Err(ProviderRecordError::InvalidV4Record);
    }
    if matches!(status, ProviderStatus::Failed | ProviderStatus::Unknown) {
        if failure_digest.is_none() || failure_object_digest.is_none() {
            return Err(ProviderRecordError::InvalidV4Record);
        }
    } else if failure_digest.is_some() || failure_object_digest.is_some() {
        return Err(ProviderRecordError::InvalidV4Record);
    }
    if status == ProviderStatus::Completed {
        if result_digest.is_none() {
            return Err(ProviderRecordError::InvalidV4Record);
        }
    } else if result_digest.is_some() || result_object_digest.is_some() {
        return Err(ProviderRecordError::InvalidV4Record);
    }
    Ok(ProviderRecordHead {
        provider_call_id,
        turn_id,
        turn_sequence,
        claim_generation,
        request_digest,
        provider_request_digest,
        status,
        result_digest,
        result_object_digest,
        failure_digest,
        previous_record_digest,
        canonical_digest: digest_bytes(&canonical_bytes(document)),
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn decimal_order_is_numeric_and_unbounded_by_u64() {
        assert!(NonnegativeDecimal("9".into()) < NonnegativeDecimal("10".into()));
        assert!(
            NonnegativeDecimal("18446744073709551615".into())
                < NonnegativeDecimal("18446744073709551616".into())
        );
        assert!(NonnegativeDecimal("9".repeat(2048)) < NonnegativeDecimal("1".repeat(2049)));
    }

    #[test]
    fn status_does_not_grant_physical_dispatch() {
        assert_eq!(
            ProviderStatus::Claimed.recovery_posture(),
            RecoveryPosture::RecheckClaimAndDurableFence
        );
        assert_eq!(
            ProviderStatus::Dispatching.recovery_posture(),
            RecoveryPosture::ReconcileWithProviderOwner
        );
        assert_eq!(
            ProviderStatus::Unknown.recovery_posture(),
            RecoveryPosture::RetainUnknownAndReconcile
        );
    }
}
