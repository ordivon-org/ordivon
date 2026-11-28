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
    assert_eq!(readback.events[1].event_kind, "harness.trace-recorded");
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
fn actual_typed_provider_unknown_remains_unsettled_in_pg_readback() {
    let Ok(dsn) = std::env::var("HARNESS_RUST_TEST_PG_DSN") else {
        eprintln!("SKIP: isolated PG18 fixture env is not configured");
        return;
    };
    let schema = std::env::var("HARNESS_RUST_TEST_SCHEMA").expect("test schema");
    let run_id = std::env::var("HARNESS_RUST_TEST_UNKNOWN_RUN_ID").expect("UNKNOWN Run");
    let mut connection = postgres::Client::connect(&dsn, postgres::NoTls).expect("PG");
    let readback = read_run_readonly(&mut connection, &schema, &run_id)
        .expect("real typed UNKNOWN Provider history");
    assert_eq!(readback.projection.status, "active");
    assert!(readback.projection.terminal_event_id.is_none());
    assert_eq!(
        readback.events.last().unwrap().event_kind,
        "harness.provider-call-unknown"
    );
    println!("RUST_PG_TYPED_PROVIDER_UNKNOWN_RETAINED_WITHOUT_COMPLETION");
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
fn historical_boolean_contract_is_not_current_executable_readback() {
    let Ok(dsn) = std::env::var("HARNESS_RUST_TEST_PG_DSN") else {
        eprintln!("SKIP: isolated PG18 fixture env is not configured");
        return;
    };
    let schema = std::env::var("HARNESS_RUST_TEST_SCHEMA").expect("test schema");
    let legacy = std::env::var("HARNESS_RUST_TEST_LEGACY_BOOLEAN_RUN_ID").expect("legacy Run");
    let bad = std::env::var("HARNESS_RUST_TEST_LEGACY_BAD_EDGE_RUN_ID").expect("bad legacy Run");
    let mut connection = postgres::Client::connect(&dsn, postgres::NoTls).expect("PG");
    let error = read_run_readonly(&mut connection, &schema, &legacy)
        .expect_err("historical alias must not become current typed readback");
    assert!(
        matches!(error, ReadError::UnsupportedLegacyRepresentation(_)),
        "{error}"
    );
    let error = read_run_readonly(&mut connection, &schema, &bad)
        .expect_err("legacy status must not conceal an inconsistent CAS edge");
    assert!(matches!(error, ReadError::Corruption(_)), "{error}");
    println!("RUST_PG_LEGACY_BOOLEAN_READBACK_BLOCKED_AND_CORRUPTION_DISTINCT");
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

#[test]
fn reject_creation_contract_reference_divergence() {
    let Some((dsn, schema, _, _, _, _)) = fixture() else {
        eprintln!("SKIP: isolated PG18 fixture env is not configured");
        return;
    };
    let mut connection = postgres::Client::connect(&dsn, postgres::NoTls).expect("fixture PG");
    let mut unexpected = Vec::new();
    for variable in [
        "HARNESS_RUST_TEST_MISSING_CONTRACT_RUN_ID",
        "HARNESS_RUST_TEST_EXTRA_CONTRACT_RUN_ID",
        "HARNESS_RUST_TEST_FOREIGN_CONTRACT_RUN_ID",
        "HARNESS_RUST_TEST_LEGACY_MISSING_CONTRACT_RUN_ID",
    ] {
        let run = std::env::var(variable).expect("creation reference fixture");
        if !matches!(
            read_run_readonly(&mut connection, &schema, &run),
            Err(ReadError::Corruption(_))
        ) {
            unexpected.push(variable);
        }
    }
    assert!(
        unexpected.is_empty(),
        "Python History Doctor rejects these fixtures: {unexpected:?}"
    );
}
