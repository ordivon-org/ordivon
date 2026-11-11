//! Deliberately RED until Rust consumer parity is implemented.
//! The legacy Python HarnessRunContract.from_dict rejects a digest-consistent
//! event chain whose Provider ID is blank. The PG reader must not admit it.
use ordivon_harness_pg::{read_run_readonly, ReadError};

#[test]
#[ignore = "deliberate semantic consumer falsifier, run with scratch PG18 and --ignored"]
fn rejects_digested_but_semantically_invalid_legacy_contract() {
    let dsn = std::env::var("HARNESS_RUST_TEST_PG_DSN").expect("isolated PG DSN");
    let schema = std::env::var("HARNESS_RUST_TEST_SCHEMA").expect("test PG schema");
    let run_id =
        std::env::var("HARNESS_RUST_TEST_INVALID_CONTRACT_RUN_ID").expect("invalid Run ID");
    let mut client = postgres::Client::connect(&dsn, postgres::NoTls).expect("PG");
    match read_run_readonly(&mut client, &schema, &run_id) {
        Err(ReadError::Corruption(reason)) => {
            assert!(
                reason.contains("contract"),
                "unexpected rejection: {reason}"
            )
        }
        Err(error) => panic!("unexpected error classification for invalid contract: {error}"),
        Ok(readback) => panic!(
            "Rust read-only consumer accepted a contract Python rejects: run={}, revision={}",
            readback.projection.harness_run_id, readback.projection.revision
        ),
    }
}
