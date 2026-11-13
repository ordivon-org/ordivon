//! Disposable PostgreSQL 18 native Rust writer/reader acceptance.
#![forbid(unsafe_code)]
use ordivon_harness_core::{loads_strict, CanonicalDocument};
use ordivon_harness_pg::{
    create_run,
    journal_write::{Admission, WriteError},
    read_run_readonly,
};
use postgres::{Client, NoTls};
use std::env;

fn contract(run: &str, caller_ref: &str) -> CanonicalDocument {
    let zero = format!("sha256:{}", "0".repeat(64));
    let json = format!(
        r#"{{
      "schemaVersion":2,
      "kind":"ordivon.harness-run-contract",
      "harnessRunId":"{run}",
      "harnessImplementationId":"rust-native-1",
      "callerId":"caller:rust-smoke",
      "callerRunRef":"{caller_ref}",
      "objectiveRef":{{"ref":"objective:smoke","kind":"objective","digest":"{zero}"}},
      "contextRefs":[{{"ref":"context:smoke","kind":"context","digest":"{zero}"}}],
      "providerId":"provider:script","adapterId":"adapter:rust","requestedModelId":"rust-test",
      "toolCatalogDigest":"{zero}","toolGrantDigest":"{zero}",
      "budget":{{"maxTurns":2}},
      "completionContract":{{"mode":"plain-text"}},
      "systemManifestRef":{{"ref":"manifest:smoke","kind":"system-manifest","digest":"{zero}"}},
      "createdAtMs":2000,"sourceRefs":[],"priorArtifactRefs":[],
      "privacy":{{"contentPolicy":"metadata-only","allowModelContent":false,"allowToolContent":false}},
      "deadlineMs":null
    }}"#
    );
    loads_strict(&json).expect("native current contract fixture")
}
#[test]
#[ignore = "requires a disposable PG18 cluster and pre-provisioned Harness test schema"]
fn native_run_birth_duplicate_conflict_and_readback() {
    let dsn = env::var("HARNESS_RUST_NATIVE_PG_DSN").expect("explicit disposable PG DSN");
    let schema = env::var("HARNESS_RUST_NATIVE_PG_SCHEMA").expect("explicit disposable schema");
    let mut db = Client::connect(&dsn, NoTls).expect("private PG");
    let run = format!("harness-run:rust-native-{}", std::process::id());
    let valid = contract(&run, "one-call");
    assert_eq!(
        create_run(&mut db, &schema, &valid).unwrap(),
        Admission::Created
    );
    assert_eq!(
        create_run(&mut db, &schema, &valid).unwrap(),
        Admission::Existing
    );
    let read = read_run_readonly(&mut db, &schema, &run).expect("exact native PG read");
    assert_eq!(read.projection.revision, 1);
    assert_eq!(read.projection.status, "created");
    assert_eq!(read.events.len(), 1);
    assert_eq!(read.events[0].event_kind, "harness.run-created");
    assert_eq!(
        read.projection.contract_object_digest,
        read.projection.contract_digest
    );
    let forged = contract(&run, "changed-call");
    assert!(matches!(
        create_run(&mut db, &schema, &forged),
        Err(WriteError::Conflict(_))
    ));
    let alias = contract("harness-run:another-run", "one-call");
    assert!(create_run(&mut db, &schema, &alias).is_err());
    let still = read_run_readonly(&mut db, &schema, &run).expect("rollback preserved first Run");
    assert_eq!(still.events.len(), 1);
    assert_eq!(still.projection.revision, 1);
    println!("NATIVE_PG_RUN_BIRTH_REPLAY_AND_CONFLICT_PASS");
}

#[test]
#[ignore = "requires a disposable PG18 cluster and pre-provisioned Harness test schema"]
fn native_run_birth_two_real_pg_clients_converge() {
    use std::sync::{Arc, Barrier};
    use std::thread;
    let dsn = env::var("HARNESS_RUST_NATIVE_PG_DSN").expect("disposable PG DSN");
    let schema = env::var("HARNESS_RUST_NATIVE_PG_SCHEMA").expect("disposable schema");
    let run = format!("harness-run:rust-native-parallel-{}", std::process::id());
    let contract = contract(&run, "parallel-call");
    let barrier = Arc::new(Barrier::new(2));
    let workers: Vec<_> = (0..2)
        .map(|_| {
            let dsn = dsn.clone();
            let schema = schema.clone();
            let contract = contract.clone();
            let barrier = barrier.clone();
            thread::spawn(move || {
                let mut client = Client::connect(&dsn, NoTls).expect("independent PG client");
                barrier.wait();
                create_run(&mut client, &schema, &contract)
                    .expect("native PG row/CAS concurrency must converge")
            })
        })
        .collect();
    let mut outcomes = workers
        .into_iter()
        .map(|job| job.join().unwrap())
        .collect::<Vec<_>>();
    outcomes.sort_by_key(|outcome| match outcome {
        Admission::Created => 0,
        Admission::Existing => 1,
    });
    assert_eq!(outcomes, [Admission::Created, Admission::Existing]);
    let mut db = Client::connect(&dsn, NoTls).unwrap();
    let result = read_run_readonly(&mut db, &schema, &run).unwrap();
    assert_eq!(result.projection.revision, 1);
    assert_eq!(result.events.len(), 1);
    println!("RUST_NATIVE_PG18_TWO_CLIENT_CONVERGENCE_PASS");
}
