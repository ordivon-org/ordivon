use ordivon_harness_pg::{read_run_readonly, ReadError};

fn fixture() -> Option<(String, String, String, String, String, String)> {
    let dsn = std::env::var("HARNESS_RUST_TEST_PG_DSN").ok()?;
    let schema = std::env::var("HARNESS_RUST_TEST_SCHEMA").ok()?;
    let valid = std::env::var("HARNESS_RUST_TEST_RUN_ID").ok()?;
    let corrupt = std::env::var("HARNESS_RUST_TEST_CORRUPT_RUN_ID").ok()?;
    let bad_revision = std::env::var("HARNESS_RUST_TEST_BAD_REVISION_RUN_ID").ok()?;
    let bad_edge = std::env::var("HARNESS_RUST_TEST_BAD_EDGE_RUN_ID").ok()?;
    Some((dsn, schema, valid, corrupt, bad_revision, bad_edge))
}

#[test]
fn read_real_python_pg_store_journal_without_writes() {
    let Some((dsn, schema, valid, _, _, _)) = fixture() else {
        eprintln!("SKIP: isolated PG18 fixture env is not configured");
        return;
    };
    let mut connection = postgres::Client::connect(&dsn, postgres::NoTls).expect("fixture PG");
    let readback = read_run_readonly(&mut connection, &schema, &valid).expect("valid Python store");
    assert_eq!(readback.projection.harness_run_id, valid);
    assert_eq!(readback.projection.status, "completed");
    assert!(readback.projection.revision >= 3);
    assert_eq!(readback.events.len() as i64, readback.projection.revision);
    assert_eq!(readback.events[0].event_kind, "harness.run-created");
    // UNKNOWN must remain an observable event, never collapsed to a failure
    // or a false semantic completion.
    assert_eq!(
        readback.events[1].event_kind,
        "harness.provider-call-unknown"
    );
    assert_eq!(
        readback.events.last().unwrap().event_kind,
        "harness.run-completed"
    );
    assert_eq!(
        readback
            .contract
            .field("harnessRunId")
            .and_then(|v| v.as_str()),
        Some(valid.as_str())
    );
    println!(
        "RUST_PG_READ_SUCCESS revision={} event_count={}",
        readback.projection.revision,
        readback.events.len()
    );
}

#[test]
fn reject_corrupted_python_pg_object() {
    let Some((dsn, schema, _, corrupt, _, _)) = fixture() else {
        eprintln!("SKIP: isolated PG18 fixture env is not configured");
        return;
    };
    let mut connection = postgres::Client::connect(&dsn, postgres::NoTls).expect("fixture PG");
    let error = read_run_readonly(&mut connection, &schema, &corrupt)
        .expect_err("deliberately modified CAS BYTEA must fail closed");
    let description = error.to_string();
    assert!(
        description.contains("CAS"),
        "unexpected error: {description}"
    );
    println!("RUST_PG_CORRUPTION_DETECTED");
}

#[test]
fn reject_projection_revision_divergence() {
    let Some((dsn, schema, _, _, bad_revision, _)) = fixture() else {
        eprintln!("SKIP: isolated PG18 fixture env is not configured");
        return;
    };
    let mut connection = postgres::Client::connect(&dsn, postgres::NoTls).expect("fixture PG");
    let error = read_run_readonly(&mut connection, &schema, &bad_revision)
        .expect_err("tampered PG projection revision must be rejected");
    assert!(error.to_string().contains("projection"), "{error}");
    println!("RUST_PG_REVISION_DIVERGENCE_DETECTED");
}

#[test]
fn reject_missing_payload_edge() {
    let Some((dsn, schema, _, _, _, bad_edge)) = fixture() else {
        eprintln!("SKIP: isolated PG18 fixture env is not configured");
        return;
    };
    let mut connection = postgres::Client::connect(&dsn, postgres::NoTls).expect("fixture PG");
    let error = read_run_readonly(&mut connection, &schema, &bad_edge)
        .expect_err("missing CAS payload edge must be rejected");
    assert!(error.to_string().contains("payload reference"), "{error}");
    println!("RUST_PG_CAS_EDGE_MISSING_DETECTED");
}

#[test]
fn valid_legacy_python_depth_is_not_corrupt() {
    let Ok(dsn) = std::env::var("HARNESS_RUST_TEST_PG_DSN") else {
        eprintln!("SKIP: isolated PG18 fixture env is not configured");
        return;
    };
    let schema = std::env::var("HARNESS_RUST_TEST_SCHEMA").expect("test schema");
    let run_id = std::env::var("HARNESS_RUST_TEST_DEEP_RUN_ID").expect("deep Run");
    let mut connection = postgres::Client::connect(&dsn, postgres::NoTls).expect("PG");
    let error = read_run_readonly(&mut connection, &schema, &run_id)
        .expect_err("Rust cannot silently certify this Python-legitimate deep Run");
    assert!(
        matches!(error, ReadError::UnsupportedLegacyRepresentation(_)),
        "valid legacy CAS outside the current codec domain must be UNKNOWN, not corruption: {error}"
    );
}
