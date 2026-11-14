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
