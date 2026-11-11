//! B-owned read-only Provider recovery projection of the CURRENT Python v4
//! Provider record. A owns sealed Canonical bytes and the durable PG writer.
//! No model request, retry, cancellation, or external effect is sent here.
use ordivon_harness_core::{canonical_bytes, digest_bytes, CanonicalDocument};
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
) -> Result<ordivon_harness_core::CanonicalRef<'a>, ProviderRecordError> {
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
// CPython str.strip recognizes the four C0 separators 0x1c..0x1f in
// addition to Unicode White_Space. Rust char::is_whitespace does not.
// This guard is source-compatible with the existing Python record codec.
fn python_strip_whitespace(ch: char) -> bool {
    ch.is_whitespace() || ('\u{001c}'..='\u{001f}').contains(&ch)
}

fn text(
    document: &CanonicalDocument,
    key: &str,
    prefix: Option<&str>,
    max_bytes: usize,
) -> Result<String, ProviderRecordError> {
    let value = value_text(document, key)?;
    if value.is_empty()
        || value.trim_matches(python_strip_whitespace) != value
        || value.len() > max_bytes
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
