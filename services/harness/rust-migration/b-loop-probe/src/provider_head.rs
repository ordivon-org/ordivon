//! Provider V4 record construction and recovery projection.
//! A owns sealed Canonical bytes and the durable PG writer.
//! No model request, retry, cancellation, or external effect is sent here.
use ordivon_harness_core::{canonical_bytes, digest_bytes, CanonicalDocument};
use ordivon_harness_pg::journal_write::{EventWrite, StoredRef};
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

/// Construct the existing V4 wire record from its semantic fields, without
/// schemaVersion, kind or recordId. Reuse the sealed Canonical codec and the
/// same record validator used by recovery. This creates bytes, not authority:
/// persistence, current admission and external effects belong to their owners.
pub fn build_v4(
    mut fields: Vec<(String, CanonicalDocument)>,
) -> Result<CanonicalDocument, ProviderRecordError> {
    const ID_FIELDS: [&str; 10] = [
        "providerCallId",
        "holderId",
        "claimGeneration",
        "status",
        "providerRequestDigest",
        "requestObjectDigest",
        "resultDigest",
        "failureDigest",
        "previousRecordDigest",
        "recordedAtMs",
    ];
    let invalid = ProviderRecordError::InvalidV4Record;
    if fields.len() != REQUIRED_FIELDS.len() - 3
        || fields
            .iter()
            .any(|(key, _)| matches!(key.as_str(), "schemaVersion" | "kind" | "recordId"))
    {
        return Err(invalid);
    }
    let identity = CanonicalDocument::object(
        ID_FIELDS
            .iter()
            .map(|key| {
                let value = fields.iter().find(|(name, _)| name == key).ok_or(invalid)?;
                Ok(((*key).to_owned(), value.1.clone()))
            })
            .collect::<Result<Vec<_>, ProviderRecordError>>()?,
    )
    .map_err(|_| invalid)?;
    let digest = digest_bytes(&canonical_bytes(&identity));
    fields.extend([
        (
            "schemaVersion".into(),
            CanonicalDocument::integer_from_decimal("4").map_err(|_| invalid)?,
        ),
        (
            "kind".into(),
            CanonicalDocument::string("ordivon.harness-provider-call-record"),
        ),
        (
            "recordId".into(),
            CanonicalDocument::string(format!("harness-provider-call-record:{}", &digest[7..31])),
        ),
    ]);
    let record = CanonicalDocument::object(fields).map_err(|_| invalid)?;
    inspect_v4(&record)?;
    Ok(record)
}

/// Construct the current Python Provider Event projection, not a dispatch
/// grant. The caller supplies the actual predecessor Event identity obtained
/// from the Journal (historical IDs need not follow today's ID formula).
/// Other object metadata is supplied by its owner and validated by PG on
/// append; this function never grants permission to read or write those bytes.
pub fn build_event_v4(
    record: &CanonicalDocument,
    objects: &[StoredRef],
    caused_by_event_id: Option<String>,
) -> Result<EventWrite, ProviderRecordError> {
    let invalid = ProviderRecordError::InvalidV4Record;
    let head = inspect_v4(record)?;
    let event_kind = match head.status {
        ProviderStatus::Claimed if head.claim_generation.as_str() != "1" => {
            "harness.provider-call-superseded"
        }
        ProviderStatus::Claimed => "harness.provider-call-claimed",
        ProviderStatus::Dispatching => "harness.provider-call-dispatching",
        ProviderStatus::Completed => "harness.provider-call-completed",
        ProviderStatus::Failed => "harness.provider-call-failed",
        ProviderStatus::Unknown => "harness.provider-call-unknown",
    };
    let recorded_at_ms = nonnegative_decimal(record, "recordedAtMs", false)?
        .as_str()
        .parse::<i64>()
        .map_err(|_| invalid)?;
    if head.previous_record_digest.is_some() != caused_by_event_id.is_some() {
        return Err(invalid);
    }
    let record_digest = head.canonical_digest;
    let event_id = format!(
        "event:harness-continuity:provider:{}",
        &record_digest[7..31]
    );
    let mut data = vec![
        (
            "providerCallRecordDigest".into(),
            CanonicalDocument::string(&record_digest),
        ),
        (
            "providerCallRecordObjectDigest".into(),
            CanonicalDocument::string(&record_digest),
        ),
    ];
    let mut references = vec![StoredRef {
        digest: record_digest,
        kind: "harness-provider-call-record".into(),
        byte_length: i64::try_from(canonical_bytes(record).len()).map_err(|_| invalid)?,
    }];
    for (key, kind) in [
        ("stateObjectDigest", "harness-run-state"),
        ("requestObjectDigest", "agent-turn-request"),
        ("resultObjectDigest", "agent-turn-result"),
        ("failureObjectDigest", "harness-provider-call-failure"),
    ] {
        let value = record.get(key).ok_or(invalid)?;
        if let Some(digest) = value.as_string() {
            let mut matches = objects.iter().filter(|object| {
                object.kind == kind && object.digest == digest && object.byte_length >= 0
            });
            let object = matches.next().ok_or(invalid)?;
            if matches.next().is_some() {
                return Err(invalid);
            }
            references.push(object.clone());
        } else if key == "stateObjectDigest" || !field(record, key)?.is_null() {
            return Err(invalid);
        }
        data.push((key.into(), value));
    }
    if references.len() != objects.len() + 1 {
        return Err(invalid);
    }
    Ok(EventWrite {
        event_id,
        event_kind: event_kind.into(),
        data: CanonicalDocument::object(data).map_err(|_| invalid)?,
        recorded_at_ms,
        caused_by_event_id,
        referenced_objects: references,
    })
}

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
fn text(
    document: &CanonicalDocument,
    key: &str,
    prefix: Option<&str>,
    max_bytes: usize,
) -> Result<String, ProviderRecordError> {
    let value = value_text(document, key)?;
    if !crate::python_text::valid_trimmed(&value, max_bytes)
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
    if field(document, key)?.is_null() {
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
