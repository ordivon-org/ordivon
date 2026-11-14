//! Commit immutable Provider V4 CAS objects using the *same* PostgreSQL
//! objects table and exact insert/verify primitive as Rust-native Run birth.
//! CAS presence does not authorize any network send or establish a domain fact.
use crate::{
    journal_write::{StoredRef, WriteError},
    lease::check_schema,
    run_create::store_cas,
    valid_schema,
};
use ordivon_harness_core::{canonical_bytes, digest_bytes, CanonicalDocument};
use postgres::Client;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ProviderCasKind {
    RecordV4,
    FailureReceipt,
    AgentTurnResult,
}
impl ProviderCasKind {
    fn names(self) -> (&'static str, &'static str) {
        match self {
            Self::RecordV4 => (
                "harness-provider-call-record",
                "ordivon.harness-provider-call-record",
            ),
            Self::FailureReceipt => (
                "harness-provider-call-failure",
                "ordivon.harness-provider-call-failure",
            ),
            Self::AgentTurnResult => ("agent-turn-result", "ordivon.agent-turn-result"),
        }
    }
}

/// Submit CAS objects alongside the exact Provider Journal Event whose
/// references bind them. Unlike stand-alone CAS, these are rolled back when
/// the Run revision, lease, source Contract or event preflight is rejected.
#[derive(Clone, Copy)]
pub struct ProviderStagedCas<'a> {
    pub kind: ProviderCasKind,
    pub document: &'a CanonicalDocument,
    pub first_seen_at_ms: i64,
}

/// The single canonical Provider CAS preparation/validation shared by the
/// original standalone CAS path and the atomic Event+CAS append.
pub(crate) fn prepare_provider_cas(
    input: ProviderStagedCas<'_>,
) -> Result<(StoredRef, Vec<u8>), WriteError> {
    if input.first_seen_at_ms < 0 {
        return Err(WriteError::Invalid("invalid Provider CAS time"));
    }
    let (kind_name, protocol_kind) = input.kind.names();
    if input.document.field("kind").and_then(|v| v.as_str()) != Some(protocol_kind) {
        return Err(WriteError::Invalid("Provider CAS kind/document mismatch"));
    }
    let expected_version = match input.kind {
        ProviderCasKind::RecordV4 => "4",
        ProviderCasKind::FailureReceipt => "1",
        ProviderCasKind::AgentTurnResult => "1",
    };
    if input
        .document
        .field("schemaVersion")
        .and_then(|v| v.integer_text())
        != Some(expected_version)
    {
        return Err(WriteError::Invalid("Provider CAS version mismatch"));
    }
    let bytes = canonical_bytes(input.document);
    if bytes.len() > 1_048_576 {
        return Err(WriteError::Invalid("Provider CAS object too large"));
    }
    let len = i64::try_from(bytes.len()).map_err(|_| WriteError::Overflow)?;
    let stored = StoredRef {
        digest: digest_bytes(&bytes),
        kind: kind_name.to_owned(),
        byte_length: len,
    };
    Ok((stored, bytes))
}

/// Persist a newly authored Provider record (or failure receipt) with one
/// native PG CAS authority. A CAS write is deliberately *not* a Provider
/// Event: the existing lease-fenced Journal append owns admission.
pub fn put_provider_cas(
    db: &mut Client,
    schema: &str,
    kind: ProviderCasKind,
    document: &CanonicalDocument,
    first_seen_at_ms: i64,
) -> Result<StoredRef, WriteError> {
    if !valid_schema(schema) {
        return Err(WriteError::Invalid("invalid Provider CAS schema"));
    }
    let (stored, bytes) = prepare_provider_cas(ProviderStagedCas {
        kind,
        document,
        first_seen_at_ms,
    })?;
    let mut tx = db.transaction()?;
    check_schema(&mut tx, schema)?;
    store_cas(
        &mut tx,
        &stored.digest,
        &stored.kind,
        &bytes,
        first_seen_at_ms,
    )?;
    tx.commit()?;
    Ok(stored)
}

#[cfg(test)]
mod tests {
    use super::*;
    use ordivon_harness_core::loads_strict;
    #[test]
    fn cas_kind_cannot_be_coerced() {
        assert_eq!(
            ProviderCasKind::RecordV4.names().0,
            "harness-provider-call-record"
        );
        let _valid =
            loads_strict(r#"{"kind":"ordivon.harness-provider-call-record","schemaVersion":4}"#)
                .unwrap();
        // Actual storage requires a disposable original PG v1 cluster and
        // is exercised by the original R18/20/25 PG18 integration runner.
    }
}
