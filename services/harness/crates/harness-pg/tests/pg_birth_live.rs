use ordivon_harness_core::loads_strict;
use ordivon_harness_pg::{
    journal_write::{create_run, Admission, WriteError},
    read_run_readonly,
};
use postgres::{Client, NoTls};
use std::sync::{Arc, Barrier};

#[test]
#[ignore = "requires original disposable PG fixture and explicit writer DSN"]
fn native_birth_cas_and_python_interop() {
    let dsn = std::env::var("HARNESS_RUST_TEST_PG_DSN").unwrap();
    let schema = std::env::var("HARNESS_RUST_TEST_SCHEMA").unwrap();
    assert!(schema.starts_with("hpg_rust_isolated_a_"));
    let path = std::env::var("HARNESS_RUST_TEST_FIXTURE_PATH").unwrap();
    let fixture: serde_json::Value =
        serde_json::from_str(&std::fs::read_to_string(path).unwrap()).unwrap();
    let mut db = Client::connect(&dsn, NoTls).unwrap();
    let base = read_run_readonly(&mut db, &schema, fixture["valid"].as_str().unwrap())
        .unwrap()
        .contract;
    let mut contract: serde_json::Value =
        serde_json::from_slice(&ordivon_harness_core::canonical_bytes(&base)).unwrap();
    let run = "harness-run:rust-native-birth";
    contract["harnessRunId"] = serde_json::json!(run);
    contract["callerRunRef"] = serde_json::json!("rust-native-birth");
    let doc = |v: &serde_json::Value| loads_strict(&v.to_string()).unwrap();
    let birth = doc(&contract);
    let gate = Arc::new(Barrier::new(2));
    let mut threads = vec![];
    for _ in 0..2 {
        let (dsn, schema, birth, gate) = (dsn.clone(), schema.clone(), birth.clone(), gate.clone());
        threads.push(std::thread::spawn(move || {
            let mut client = Client::connect(&dsn, NoTls).unwrap();
            gate.wait();
            create_run(&mut client, &schema, &birth).unwrap()
        }));
    }
    let results: Vec<_> = threads.into_iter().map(|t| t.join().unwrap()).collect();
    assert_eq!(
        results.iter().filter(|&&x| x == Admission::Created).count(),
        1
    );
    assert_eq!(
        results
            .iter()
            .filter(|&&x| x == Admission::Existing)
            .count(),
        1
    );
    assert_eq!(
        create_run(&mut db, &schema, &birth).unwrap(),
        Admission::Existing
    );
    let snapshot = read_run_readonly(&mut db, &schema, run).unwrap();
    assert_eq!(snapshot.projection.revision, 1);
    assert_eq!(snapshot.events.len(), 1);
    assert_eq!(snapshot.projection.status, "created");
    let count = |db: &mut Client| -> i64 {
        db.query_one(&format!("SELECT count(*) FROM {schema}.objects"), &[])
            .unwrap()
            .get(0)
    };
    let before = count(&mut db);
    contract["harnessRunId"] = serde_json::json!("harness-run:rust-native-birth-conflict");
    assert!(matches!(
        create_run(&mut db, &schema, &doc(&contract)),
        Err(WriteError::Conflict(_))
    ));
    assert_eq!(count(&mut db), before);
    contract["harnessRunId"] = serde_json::json!(run);
    contract["callerRunRef"] = serde_json::json!("changed");
    assert!(matches!(
        create_run(&mut db, &schema, &doc(&contract)),
        Err(WriteError::Conflict(_))
    ));
    assert_eq!(count(&mut db), before);
    contract["budget"] = serde_json::json!({});
    assert!(create_run(&mut db, &schema, &doc(&contract)).is_err());
    assert_eq!(count(&mut db), before);
    let ro_dsn = std::env::var("HARNESS_RUST_TEST_PG_READONLY_DSN").unwrap();
    let mut ro = Client::connect(&ro_dsn, NoTls).unwrap();
    assert!(create_run(&mut ro, &schema, &birth).is_err());
    println!("NATIVE_BIRTH_ATOMIC_RACE_REPLAY_CONFLICT_CAS_PASS");
}
