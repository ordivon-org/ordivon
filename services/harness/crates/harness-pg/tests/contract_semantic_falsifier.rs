//! Deliberately RED semantic corpus until Rust Contract consumer parity exists.
//! All cases are SHA256-valid, PG-revision-valid, but Python-invalid Contracts.
//! Must not be confused with a production corruption report or a new writer.
use ordivon_harness_pg::{read_run_readonly, ReadError};

#[test]
#[ignore = "opt-in source-level consumer adversarial corpus, scratch PG18 only"]
fn rejects_digested_but_semantically_invalid_legacy_contracts() {
    let dsn = std::env::var("HARNESS_RUST_TEST_PG_DSN").expect("isolated PG DSN");
    let schema = std::env::var("HARNESS_RUST_TEST_SCHEMA").expect("scratch PG schema");
    // A newline-separated "scenario|run_id" avoids introducing serde_json
    // or a second JSON codec into the PG crate merely to read test metadata.
    let cases = std::env::var("HARNESS_RUST_TEST_INVALID_CONTRACT_CASES")
        .expect("Python source-oracle cases");
    let mut client = postgres::Client::connect(&dsn, postgres::NoTls).expect("PG");
    let mut accepted = Vec::new();
    let mut checked = 0;
    for line in cases.lines() {
        let (name, run_id) = line.split_once('|').expect("name|run ID");
        checked += 1;
        match read_run_readonly(&mut client, &schema, run_id) {
            Err(ReadError::Corruption(reason)) => {
                assert!(
                    reason.contains("contract") || reason.contains("Contract"),
                    "{name} classified as unrelated corruption: {reason}"
                );
            }
            Err(error) => panic!("{name} unexpected error classification: {error}"),
            Ok(_) => accepted.push(name.to_owned()),
        }
    }
    assert!(
        checked >= 20,
        "missing adversarial Contract cases: {checked}"
    );
    assert!(
        accepted.is_empty(),
        "Rust incorrectly ACCEPTED {} Python-invalid digest-valid Contract cases: {accepted:?}",
        accepted.len()
    );
}
