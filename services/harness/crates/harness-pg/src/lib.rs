//! Native PostgreSQL Run authority with separate projection/readback/lease/writer.
#![forbid(unsafe_code)]
pub mod contract_semantics;
pub mod journal_write;
pub mod lease;
mod projection;
mod readback;
pub mod run_create;
pub use projection::{
    ProviderFailureTextField, ReadError, Readback, RunEvent, RunProjection,
    VerifiedProviderFailureReference, VerifiedProviderReference, VerifiedReferenceLink,
    VerifiedToolReference, VerifiedToolSnapshotMetadata,
};
pub(crate) use readback::{corrupted, run_projection, transition, valid_schema, CONTRACT_KIND};
pub use readback::{decode_cas, read_run_readonly};
pub use run_create::create_run;

#[cfg(test)]
mod tests {
    use super::*;
    use ordivon_harness_core::{digest_bytes, loads_strict, CanonicalDocument};

    #[test]
    fn debug_never_exposes_private_tool_intent_fields() {
        let token = "private-runtime-request-secret-never-log";
        let entry = VerifiedToolReference {
            event_id: "event:private-tool-debug".into(),
            digest: digest_bytes(token.as_bytes()),
            kind: "harness-tool-step-intent".into(),
            value: CanonicalDocument::object(vec![(
                "clientRequestId".into(),
                CanonicalDocument::string(token),
            )])
            .expect("test CAS semantic object"),
        };
        let record = format!("{entry:?}");
        assert!(record.contains("value: \"<redacted>\""));
        assert!(!record.contains(token));
        assert!(record.contains("harness-tool-step-intent"));
    }

    #[test]
    fn provider_failure_debug_must_not_expose_private_receipt_detail() {
        let receipt = VerifiedProviderFailureReference {
            event_id: "event:test-privacy".to_owned(),
            digest: "sha256:test-only".to_owned(),
            value: loads_strict(
                r#"{"detail":"TEST_ONLY_PRIVATE_RECEIPT_TOKEN","failureCode":"provider_failed"}"#,
            )
            .unwrap(),
        };
        let log = format!("{receipt:?}");
        assert!(log.contains("event:test-privacy"));
        assert!(log.contains("sha256:test-only"));
        assert!(
            !log.contains("TEST_ONLY_PRIVATE_RECEIPT_TOKEN"),
            "Debug must never print raw Provider failure detail"
        );
    }

    #[test]
    fn unqualified_legacy_requires_verified_cas_digest_first() {
        // A historical Python interpreter configured with a larger recursion
        // limit can persist these bytes, but Rust currently bounds nesting.
        let raw = format!("{}0{}", "[".repeat(996), "]".repeat(996)).into_bytes();
        let digest = digest_bytes(&raw);
        assert!(matches!(
            decode_cas(&digest, "legacy", "legacy", raw.len() as i64, &raw),
            Err(ReadError::UnsupportedLegacyRepresentation(_))
        ));
        // The same unparseable bytes under a false digest are objectively
        // corrupt and must NOT hide behind UNKNOWN parser qualification.
        assert!(matches!(
            decode_cas(
                "sha256:tampered",
                "legacy",
                "legacy",
                raw.len() as i64,
                &raw
            ),
            Err(ReadError::Corruption(_))
        ));
        assert!(matches!(
            decode_cas(&digest, "legacy", "wrong", raw.len() as i64, &raw),
            Err(ReadError::Corruption(_))
        ));
    }

    #[test]
    fn rejects_sql_schema_names_and_malformed_objects() {
        for schema in [
            "",
            "Public",
            "pg-test",
            "harness;drop schema public",
            "_hidden",
            "1foo",
            "x y",
        ] {
            assert!(!valid_schema(schema), "{schema}");
        }
        for schema in ["harness", "harness_1", "hpg_test_abc"] {
            assert!(valid_schema(schema), "{schema}");
        }
        let src = br#"{"a":1}"#;
        let digest = digest_bytes(src);
        assert!(decode_cas(&digest, "kind", "kind", src.len() as i64, src).is_ok());
        assert!(decode_cas(&digest, "kind", "wrong", src.len() as i64, src).is_err());
        assert!(decode_cas(&digest, "kind", "kind", src.len() as i64 + 1, src).is_err());
        assert!(decode_cas("sha256:corrupt", "kind", "kind", src.len() as i64, src).is_err());
        assert!(decode_cas(&digest, "kind", "kind", src.len() as i64, br#"{ "a":1}"#).is_err());
        let deep = format!("{}0{}", "[".repeat(996), "]".repeat(996));
        let expected = digest_bytes(deep.as_bytes());
        assert!(matches!(
            decode_cas(
                &expected,
                "kind",
                "kind",
                deep.len() as i64,
                deep.as_bytes()
            ),
            Err(ReadError::UnsupportedLegacyRepresentation(_))
        ));
        let huge_int = "7".repeat(4301);
        let expected = digest_bytes(huge_int.as_bytes());
        assert!(matches!(
            decode_cas(
                &expected,
                "kind",
                "kind",
                huge_int.len() as i64,
                huge_int.as_bytes()
            ),
            Err(ReadError::UnsupportedLegacyRepresentation(_))
        ));
    }
}
