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
        }
    }
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
    if !valid_schema(schema) || first_seen_at_ms < 0 {
        return Err(WriteError::Invalid("invalid Provider CAS schema/time"));
    }
    let (kind_name, protocol_kind) = kind.names();
    if document.field("kind").and_then(|v| v.as_str()) != Some(protocol_kind) {
        return Err(WriteError::Invalid("Provider CAS kind/document mismatch"));
    }
    if kind == ProviderCasKind::RecordV4
        && document
            .field("schemaVersion")
            .and_then(|v| v.integer_text())
            != Some("4")
    {
        return Err(WriteError::Invalid("Provider V4 CAS version mismatch"));
    }
    let bytes = canonical_bytes(document);
    if bytes.len() > 1_048_576 {
        return Err(WriteError::Invalid("Provider CAS object too large"));
    }
    let digest = digest_bytes(&bytes);
    let len = i64::try_from(bytes.len()).map_err(|_| WriteError::Overflow)?;
    let mut tx = db.transaction()?;
    check_schema(&mut tx, schema)?;
    // Reuses the same immutable CAS writer as native create_run, including
    // verification of immutable bytes/kind if the digest already exists.
    store_cas(&mut tx, &digest, kind_name, &bytes, first_seen_at_ms)?;
    tx.commit()?;
    Ok(StoredRef {
        digest,
        kind: kind_name.to_string(),
        byte_length: len,
    })
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
