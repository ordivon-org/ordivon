//! True Python Store→PG18→A verified CAS/Journal→B Provider recovery head.
//! All Provider events are synthetic test-only identities, with zero external
//! model requests. A readonly DB role is enforced by the shared PG runner.
use std::{fs, path::Path};

use ordivon_harness_core::{loads_strict, CanonicalDocument, CanonicalRef};
use ordivon_harness_loop_b_probe::pg_domain_read::{
    inspect_pg_provider_head, ExpectedModel, PgDomainInspectionError, PgProviderRecoveryError,
};
use ordivon_harness_loop_b_probe::provider_head::{ProviderStatus, RecoveryPosture};
use ordivon_harness_pg::ReadError;
use postgres::{Client, NoTls};

fn text<'a>(v: &'a CanonicalDocument, key: &str) -> &'a str {
    v.field(key).and_then(CanonicalRef::as_str).unwrap()
}

#[test]
#[ignore = "requires existing A-owned disposable PostgreSQL18 Store test fixture"]
fn source_python_provider_v4_cas_head_recovery_does_not_dispatch_or_blind_retry() {
    let dsn = std::env::var("HARNESS_RUST_TEST_PG_DSN").unwrap();
    let schema = std::env::var("HARNESS_RUST_TEST_SCHEMA").unwrap();
    let path = std::env::var("HARNESS_RUST_TEST_FIXTURE_PATH").unwrap();
    let raw = fs::read_to_string(Path::new(&path)).unwrap();
    let all = loads_strict(&raw).unwrap();
    let no_tool = all.get("no_tool").unwrap();
    let provider_records = all.get("provider_records").unwrap();
    let expected = ExpectedModel {
        provider_id: text(&no_tool, "providerId"),
        adapter_id: text(&no_tool, "adapterId"),
        requested_model_id: text(&no_tool, "requestedModelId"),
    };
    let mut client = Client::connect(&dsn, NoTls).unwrap();

    for (label, status, posture) in [
        (
            "claimed",
            ProviderStatus::Claimed,
            RecoveryPosture::RecheckClaimAndDurableFence,
        ),
        (
            "unknown",
            ProviderStatus::Unknown,
            RecoveryPosture::RetainUnknownAndReconcile,
        ),
        (
            "completed_redacted",
            ProviderStatus::Completed,
            RecoveryPosture::ReadCommittedResult,
        ),
    ] {
        let item = provider_records.get(label).unwrap();
        let observed =
            inspect_pg_provider_head(&mut client, &schema, text(&item, "runId"), expected)
                .unwrap_or_else(|error| {
                    panic!("{label} provider head could not be recovered: {error:?}")
                })
                .unwrap();
        assert_eq!(observed.run_id(), text(&item, "runId"));
        assert_eq!(observed.status(), status);
        assert_eq!(observed.recovery_posture(), posture);
        assert_eq!(
            observed.record_digest(),
            text(&item, "expectedRecordDigest")
        );
        assert!(observed.run_revision() >= 2);
        if label == "completed_redacted" {
            // The real Python V4 record permits privacy-redacted content while
            // preserving the semantic result SHA256: never invent a body.
            assert_eq!(
                observed.result_digest(),
                item.field("expectedResultDigest")
                    .and_then(CanonicalRef::as_str)
            );
        } else {
            assert_eq!(observed.result_digest(), None);
        }
    }
    {
        let item = provider_records.get("cleared").unwrap();
        let result =
            inspect_pg_provider_head(&mut client, &schema, text(&item, "runId"), expected).unwrap();
        assert!(
            result.is_none(),
            "Python _heads clears Provider head after Run pause"
        );
    }
    let wrong = provider_records.get("wrong_digest").unwrap();
    assert!(matches!(
        inspect_pg_provider_head(&mut client, &schema, text(&wrong, "runId"), expected),
        Err(PgProviderRecoveryError::EventRecordMismatch(_))
    ));
    for label in ["wrong_state", "extra_reference", "wrong_event_status"] {
        let item = provider_records.get(label).unwrap();
        assert!(
            matches!(
                inspect_pg_provider_head(&mut client, &schema, text(&item, "runId"), expected),
                Err(PgProviderRecoveryError::EventRecordMismatch(_))
            ),
            "PG verified a raw CAS/edge set but B must reject invalid Provider semantics: {label}"
        );
    }
    let legacy = provider_records.get("v3_legacy").unwrap();
    assert!(matches!(
        inspect_pg_provider_head(&mut client, &schema, text(&legacy, "runId"), expected),
        Err(PgProviderRecoveryError::UnsupportedV3ProviderRecord)
    ));
    let kind = provider_records.get("wrong_kind").unwrap();
    assert!(matches!(
        inspect_pg_provider_head(&mut client, &schema, text(&kind, "runId"), expected),
        Err(PgProviderRecoveryError::MissingOrAmbiguousEventReference)
    ));
    let corrupted = provider_records.get("tampered_cas").unwrap();
    assert!(matches!(
        inspect_pg_provider_head(&mut client, &schema, text(&corrupted, "runId"), expected),
        Err(PgProviderRecoveryError::Run(
            PgDomainInspectionError::Store(ReadError::Corruption(_))
        ))
    ));
    let empty_run = text(&no_tool, "runId");
    assert!(
        inspect_pg_provider_head(&mut client, &schema, empty_run, expected)
            .unwrap()
            .is_none()
    );
    let claimed = provider_records.get("claimed").unwrap();
    assert!(matches!(
        inspect_pg_provider_head(
            &mut client,
            &schema,
            text(&claimed, "runId"),
            ExpectedModel {
                adapter_id: "adapter:other",
                ..expected
            }
        ),
        Err(PgProviderRecoveryError::Run(
            PgDomainInspectionError::ProviderSelectionMismatch("adapterId")
        ))
    ));
    println!("PG18_PYTHON_PROVIDER_V4_VERIFIED_CAS_RECOVERY_PASS");
}
