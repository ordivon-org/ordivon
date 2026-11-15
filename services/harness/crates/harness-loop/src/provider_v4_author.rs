//! Typed, pure native ProviderCall V4 author derived from the current
//! Python source `build_provider_call_record_v4` contract.
//! This is a representation producer, not physical Provider permission.
use crate::provider_head::{inspect_v4, ProviderRecordError};
use ordivon_harness_core::{canonical_bytes, digest_bytes, CanonicalDocument};

/// Immutable identity shared by successive records for one Provider Call.
/// The identity is *source supplied*; this constructor does NOT grant an
/// assignment, current lease, credential, or runtime dispatch.
pub struct ProviderV4Seed<'a> {
    pub provider_call_id: &'a str,
    pub harness_run_id: &'a str,
    pub binding_digest: &'a str,
    pub source_kind: &'a str,
    pub source_digest: &'a str,
    pub source_object_digest: &'a str,
    pub state_object_digest: &'a str,
    pub turn_id: &'a str,
    pub turn_sequence: u64,
    pub request_digest: &'a str,
    pub request_object_digest: Option<&'a str>,
    pub provider_request_digest: &'a str,
    pub adapter_id: &'a str,
    pub requested_model_id: &'a str,
    pub holder_id: &'a str,
    pub claim_generation: u64,
    pub issued_at_ms: u64,
    pub expires_at_ms: u64,
}

pub enum ProviderV4Transition<'a> {
    Claimed {
        previous: Option<&'a str>,
    },
    Dispatching {
        previous: &'a str,
    },
    Completed {
        previous: &'a str,
        result_digest: &'a str,
        result_object_digest: Option<&'a str>,
    },
    Failed {
        previous: &'a str,
        failure_digest: &'a str,
        failure_object_digest: &'a str,
    },
    Unknown {
        previous: &'a str,
        failure_digest: &'a str,
        failure_object_digest: &'a str,
    },
}

#[derive(Clone, Copy, Debug)]
pub enum ProviderFailureCode {
    ProviderFailed,
    Timeout,
    TransportFailed,
    Rejected,
    Unavailable,
}
impl ProviderFailureCode {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::ProviderFailed => "provider_failed",
            Self::Timeout => "provider_timeout",
            Self::TransportFailed => "provider_transport_failed",
            Self::Rejected => "provider_rejected",
            Self::Unavailable => "provider_unavailable",
        }
    }
}
#[derive(Clone, Copy, Debug)]
pub enum DispatchSafety {
    PreDispatchSafe,
    ProviderRejected,
    Ambiguous,
}
impl DispatchSafety {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::PreDispatchSafe => "pre_dispatch_safe",
            Self::ProviderRejected => "provider_rejected",
            Self::Ambiguous => "dispatch_ambiguous",
        }
    }
}
pub struct ProviderFailureSpec<'a> {
    pub provider_call_id: &'a str,
    pub request_digest: &'a str,
    pub provider_request_digest: &'a str,
    pub failure_code: ProviderFailureCode,
    pub dispatch_safety: DispatchSafety,
    pub detail: &'a str,
}

/// Pure source-compatible failure receipt; an unknown network outcome is not
/// proof of failed billing, nor authority to resend or change Provider.
pub fn author_provider_failure(
    spec: &ProviderFailureSpec<'_>,
) -> Result<CanonicalDocument, ProviderRecordError> {
    let id = &spec.provider_call_id;
    let valid_digest = |d: &str| {
        d.len() == 71
            && d.starts_with("sha256:")
            && d[7..]
                .bytes()
                .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
    };
    if !id.starts_with("provider-call:")
        || id.len() > 300
        || id.trim() != *id
        || !valid_digest(spec.request_digest)
        || !valid_digest(spec.provider_request_digest)
        || spec.detail.is_empty()
        || spec.detail.trim() != spec.detail
        || spec.detail.len() > 2048
    {
        return Err(ProviderRecordError::InvalidV4Record);
    }
    CanonicalDocument::object(vec![
        (
            "schemaVersion".into(),
            CanonicalDocument::integer_from_decimal("1").expect("one is representable"),
        ),
        (
            "kind".into(),
            CanonicalDocument::string("ordivon.harness-provider-call-failure"),
        ),
        ("providerCallId".into(), txt(id)),
        ("requestDigest".into(), txt(spec.request_digest)),
        (
            "providerRequestDigest".into(),
            txt(spec.provider_request_digest),
        ),
        ("failureCode".into(), txt(spec.failure_code.as_str())),
        ("dispatchSafety".into(), txt(spec.dispatch_safety.as_str())),
        ("detail".into(), txt(spec.detail)),
    ])
    .map_err(|_| ProviderRecordError::InvalidV4Record)
}

fn txt(v: &str) -> CanonicalDocument {
    CanonicalDocument::string(v)
}
fn nullable(v: Option<&str>) -> CanonicalDocument {
    v.map(txt).unwrap_or_else(CanonicalDocument::null)
}
fn num(v: u64) -> CanonicalDocument {
    // Valid u64 decimal is always canonical and valid under the current
    // Python exact integer semantics (unlike converting through f64).
    CanonicalDocument::integer_from_decimal(&v.to_string()).expect("u64 is an exact JSON integer")
}

/// The Python source generates recordId from nine exact canonical fields.
/// Preserve that identity and source bytes, rather than assigning a new Rust
/// request identity. The result can be CAS-stored but has no send authority.
pub fn author_provider_v4(
    seed: &ProviderV4Seed<'_>,
    transition: ProviderV4Transition<'_>,
    recorded_at_ms: u64,
) -> Result<CanonicalDocument, ProviderRecordError> {
    let (status, previous, result, result_object, failure, failure_object) = match transition {
        ProviderV4Transition::Claimed { previous } => ("claimed", previous, None, None, None, None),
        ProviderV4Transition::Dispatching { previous } => {
            ("dispatching", Some(previous), None, None, None, None)
        }
        ProviderV4Transition::Completed {
            previous,
            result_digest,
            result_object_digest,
        } => (
            "completed",
            Some(previous),
            Some(result_digest),
            result_object_digest,
            None,
            None,
        ),
        ProviderV4Transition::Failed {
            previous,
            failure_digest,
            failure_object_digest,
        } => (
            "failed",
            Some(previous),
            None,
            None,
            Some(failure_digest),
            Some(failure_object_digest),
        ),
        ProviderV4Transition::Unknown {
            previous,
            failure_digest,
            failure_object_digest,
        } => (
            "unknown",
            Some(previous),
            None,
            None,
            Some(failure_digest),
            Some(failure_object_digest),
        ),
    };
    let token = CanonicalDocument::object(vec![
        ("providerCallId".into(), txt(seed.provider_call_id)),
        ("holderId".into(), txt(seed.holder_id)),
        ("claimGeneration".into(), num(seed.claim_generation)),
        ("status".into(), txt(status)),
        (
            "providerRequestDigest".into(),
            txt(seed.provider_request_digest),
        ),
        (
            "requestObjectDigest".into(),
            nullable(seed.request_object_digest),
        ),
        ("resultDigest".into(), nullable(result)),
        ("failureDigest".into(), nullable(failure)),
        ("previousRecordDigest".into(), nullable(previous)),
        ("recordedAtMs".into(), num(recorded_at_ms)),
    ])
    .map_err(|_| ProviderRecordError::InvalidV4Record)?;
    let token_hash = digest_bytes(&canonical_bytes(&token));
    let record_id = format!("harness-provider-call-record:{}", &token_hash[7..31]);
    let record = CanonicalDocument::object(vec![
        ("schemaVersion".into(), num(4)),
        ("kind".into(), txt("ordivon.harness-provider-call-record")),
        ("recordId".into(), txt(&record_id)),
        ("providerCallId".into(), txt(seed.provider_call_id)),
        ("harnessRunId".into(), txt(seed.harness_run_id)),
        ("bindingDigest".into(), txt(seed.binding_digest)),
        ("sourceKind".into(), txt(seed.source_kind)),
        ("sourceDigest".into(), txt(seed.source_digest)),
        ("sourceObjectDigest".into(), txt(seed.source_object_digest)),
        ("stateObjectDigest".into(), txt(seed.state_object_digest)),
        ("turnId".into(), txt(seed.turn_id)),
        ("turnSequence".into(), num(seed.turn_sequence)),
        ("requestDigest".into(), txt(seed.request_digest)),
        (
            "requestObjectDigest".into(),
            nullable(seed.request_object_digest),
        ),
        (
            "providerRequestDigest".into(),
            txt(seed.provider_request_digest),
        ),
        ("adapterId".into(), txt(seed.adapter_id)),
        ("requestedModelId".into(), txt(seed.requested_model_id)),
        ("holderId".into(), txt(seed.holder_id)),
        ("claimGeneration".into(), num(seed.claim_generation)),
        ("status".into(), txt(status)),
        ("resultDigest".into(), nullable(result)),
        ("resultObjectDigest".into(), nullable(result_object)),
        ("failureDigest".into(), nullable(failure)),
        ("failureObjectDigest".into(), nullable(failure_object)),
        ("previousRecordDigest".into(), nullable(previous)),
        ("issuedAtMs".into(), num(seed.issued_at_ms)),
        ("expiresAtMs".into(), num(seed.expires_at_ms)),
        ("recordedAtMs".into(), num(recorded_at_ms)),
    ])
    .map_err(|_| ProviderRecordError::InvalidV4Record)?;
    inspect_v4(&record)?;
    Ok(record)
}

/// The exact original Python Provider Event shape, produced from a typed
/// source V4 record. This is a pure Journal input, not an independent Writer,
/// live credential, issuer or physical Provider dispatch permission.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ProviderV4EventKind {
    Claimed,
    Superseded,
    Dispatching,
    Completed,
    Failed,
    Unknown,
}
impl ProviderV4EventKind {
    fn names(self) -> (&'static str, crate::provider_head::ProviderStatus) {
        use crate::provider_head::ProviderStatus;
        match self {
            Self::Claimed => ("harness.provider-call-claimed", ProviderStatus::Claimed),
            Self::Superseded => ("harness.provider-call-superseded", ProviderStatus::Claimed),
            Self::Dispatching => (
                "harness.provider-call-dispatching",
                ProviderStatus::Dispatching,
            ),
            Self::Completed => ("harness.provider-call-completed", ProviderStatus::Completed),
            Self::Failed => ("harness.provider-call-failed", ProviderStatus::Failed),
            Self::Unknown => ("harness.provider-call-unknown", ProviderStatus::Unknown),
        }
    }
}

/// Source CAS references carried directly in the original Event; grouping
/// avoids an extra immutable registry, request parser or Journal layer.
pub struct ProviderV4EventRefs<'a> {
    pub state: &'a ordivon_harness_pg::journal_write::StoredRef,
    pub request: Option<&'a ordivon_harness_pg::journal_write::StoredRef>,
    pub result: Option<&'a ordivon_harness_pg::journal_write::StoredRef>,
    pub failure: Option<&'a ordivon_harness_pg::journal_write::StoredRef>,
}

/// Author a journal Event from the same source V4 record that the existing
/// PostgreSQL Writer atomically commits. The original State/Request references
/// remain pre-existing source CAS; optional model Result and failure CAS must
/// be staged in the SAME existing Writer transaction by its caller.
///
/// Unlike the historic test-only Python Event templates, this pure operation
/// can be used by a native Provider Journal. It deliberately does NOT claim
/// that its caller holds a current PG lease, Provider credential or Tool grant.
pub fn author_provider_event_v4(
    event_id: &str,
    kind: ProviderV4EventKind,
    record: &CanonicalDocument,
    refs: ProviderV4EventRefs<'_>,
    caused_by_event_id: Option<&str>,
    recorded_at_ms: i64,
) -> Result<ordivon_harness_pg::journal_write::EventWrite, ProviderRecordError> {
    use ordivon_harness_pg::journal_write::{EventWrite, StoredRef};
    let invalid = ProviderRecordError::InvalidV4Record;
    let (event_kind, expected) = kind.names();
    let head = inspect_v4(record)?;
    let field = |name: &str| record.field(name).and_then(|value| value.as_str());
    let refs_match = |name: &str, value: Option<&StoredRef>, expected_kind: &str| {
        value.is_none_or(|v| v.kind == expected_kind)
            && field(name) == value.map(|v| v.digest.as_str())
    };
    if !event_id.starts_with("event:")
        || event_id.len() > 300
        || event_id.trim() != event_id
        || recorded_at_ms < 0
        || record.field("recordedAtMs").and_then(|v| v.integer_text())
            != Some(recorded_at_ms.to_string().as_str())
        || head.status != expected
        || refs.state.kind != "harness-run-state"
        || field("stateObjectDigest") != Some(refs.state.digest.as_str())
        || !refs_match("requestObjectDigest", refs.request, "agent-turn-request")
        || !refs_match("resultObjectDigest", refs.result, "agent-turn-result")
        || !refs_match(
            "failureObjectDigest",
            refs.failure,
            "harness-provider-call-failure",
        )
        || (refs.result.is_some() && expected != crate::provider_head::ProviderStatus::Completed)
        || (refs.failure.is_some()
            != matches!(
                expected,
                crate::provider_head::ProviderStatus::Failed
                    | crate::provider_head::ProviderStatus::Unknown
            ))
    {
        return Err(invalid);
    }
    let record_bytes = canonical_bytes(record);
    let record_ref = StoredRef {
        digest: head.canonical_digest.clone(),
        kind: "harness-provider-call-record".into(),
        byte_length: i64::try_from(record_bytes.len()).map_err(|_| invalid)?,
    };
    let data = CanonicalDocument::object(vec![
        ("providerCallRecordDigest".into(), txt(&record_ref.digest)),
        (
            "providerCallRecordObjectDigest".into(),
            txt(&record_ref.digest),
        ),
        ("stateObjectDigest".into(), txt(&refs.state.digest)),
        (
            "requestObjectDigest".into(),
            nullable(refs.request.map(|r| r.digest.as_str())),
        ),
        (
            "resultObjectDigest".into(),
            nullable(refs.result.map(|r| r.digest.as_str())),
        ),
        (
            "failureObjectDigest".into(),
            nullable(refs.failure.map(|r| r.digest.as_str())),
        ),
    ])
    .map_err(|_| invalid)?;
    let mut references = vec![record_ref, refs.state.clone()];
    references.extend(refs.request.cloned());
    references.extend(refs.result.cloned());
    references.extend(refs.failure.cloned());
    Ok(EventWrite {
        event_id: event_id.to_owned(),
        event_kind: event_kind.to_owned(),
        data,
        recorded_at_ms,
        caused_by_event_id: caused_by_event_id.map(str::to_owned),
        referenced_objects: references,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    const D: &str = "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
    fn seed() -> ProviderV4Seed<'static> {
        ProviderV4Seed {
            provider_call_id: "provider-call:test",
            harness_run_id: "harness-run:test",
            binding_digest: D,
            source_kind: "assignment",
            source_digest: D,
            source_object_digest: D,
            state_object_digest: D,
            turn_id: "turn:test",
            turn_sequence: 1,
            request_digest: D,
            request_object_digest: None,
            provider_request_digest: D,
            adapter_id: "adapter:test",
            requested_model_id: "model:test",
            holder_id: "test-holder",
            claim_generation: 1,
            issued_at_ms: 100,
            expires_at_ms: 9000,
        }
    }
    #[test]
    fn source_failure_receipt_is_exact_and_does_not_grant_retry() {
        let spec = ProviderFailureSpec {
            provider_call_id: "provider-call:test",
            request_digest: D,
            provider_request_digest: D,
            failure_code: ProviderFailureCode::TransportFailed,
            dispatch_safety: DispatchSafety::Ambiguous,
            detail: "Transport lost reply after request",
        };
        let doc = author_provider_failure(&spec).unwrap();
        assert_eq!(doc.object_len(), Some(8));
        assert_eq!(
            doc.field("dispatchSafety").unwrap().as_str(),
            Some("dispatch_ambiguous")
        );
        let forged = ProviderFailureSpec {
            detail: " secret ",
            ..spec
        };
        assert!(author_provider_failure(&forged).is_err());
    }

    #[test]
    fn source_v4_chain_is_typed_not_fabricated_dispatch_authority() {
        let first = author_provider_v4(
            &seed(),
            ProviderV4Transition::Claimed { previous: None },
            110,
        )
        .unwrap();
        let prior = digest_bytes(&canonical_bytes(&first));
        let second = author_provider_v4(
            &seed(),
            ProviderV4Transition::Dispatching { previous: &prior },
            120,
        )
        .unwrap();
        let digest2 = digest_bytes(&canonical_bytes(&second));
        let third = author_provider_v4(
            &seed(),
            ProviderV4Transition::Unknown {
                previous: &digest2,
                failure_digest: D,
                failure_object_digest: D,
            },
            130,
        )
        .unwrap();
        assert!(inspect_v4(&third).is_ok());
        assert_eq!(
            third.field("previousRecordDigest").unwrap().as_str(),
            Some(digest2.as_str())
        );
        assert_ne!(prior, digest2);
        assert!(author_provider_v4(
            &seed(),
            ProviderV4Transition::Claimed {
                previous: Some("invalid")
            },
            110
        )
        .is_err());
        assert!(author_provider_v4(
            &seed(),
            ProviderV4Transition::Dispatching {
                previous: "invalid"
            },
            120
        )
        .is_err());
    }
}
