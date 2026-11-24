//! Independent full versioned Contract semantic gate for the existing Writer.
//! Uses Python-created invalid and valid Run Contracts in disposable PG18.
use ordivon_harness_core::CanonicalDocument;
use ordivon_harness_pg::journal_write::{append_events, Admission, EventWrite, WriteError};
use ordivon_harness_pg::lease::acquire_run_lease;
use ordivon_harness_pg::read_run_readonly;
use postgres::{Client, NoTls};

fn trace(id: &str, at: i64) -> EventWrite {
    EventWrite {
        event_id: id.to_owned(),
        event_kind: "harness.trace-recorded".to_owned(),
        data: CanonicalDocument::object(vec![("note".to_owned(), CanonicalDocument::string(id))])
            .unwrap(),
        recorded_at_ms: at,
        caused_by_event_id: None,
        referenced_objects: vec![],
    }
}

#[test]
#[ignore = "independent writer semantic admission falsification on disposable PG18"]
fn native_writer_must_not_extend_a_semantically_invalid_contract_run() {
    use ordivon_harness_pg::ReadError;

    let dsn = std::env::var("HARNESS_RUST_TEST_PG_DSN").unwrap();
    let schema = std::env::var("HARNESS_RUST_TEST_SCHEMA").unwrap();
    assert!(schema.starts_with("hpg_rust_isolated_a_"));
    let cases = std::env::var("HARNESS_RUST_TEST_INVALID_CONTRACT_CASES").unwrap();
    let mut db = Client::connect(&dsn, NoTls).unwrap();
    let mut checked = 0;
    for line in cases.lines() {
        let (scenario, run_id) = line.split_once('|').expect("invalid case|Run ID");
        checked += 1;
        assert!(
            matches!(
                read_run_readonly(&mut db, &schema, run_id),
                Err(ReadError::Corruption(_))
            ),
            "{scenario}: source Reader must reject"
        );
        // Deliberately show that obtaining the exact physical Run lease does
        // not prove the versioned semantic Contract is admissible to Writer.
        let lease = acquire_run_lease(
            &mut db,
            &schema,
            run_id,
            "rust:bad-contract-falsifier",
            10000,
            1000,
            Some(1),
        )
        .expect("a lease is not a semantic Contract proof");
        let id = format!("event:invalid-contract-writer-falsifier-{scenario}");
        let result = append_events(
            &mut db,
            &schema,
            run_id,
            &[trace(&id, 1200)],
            1,
            &lease,
            1100,
        );
        assert!(
            matches!(result, Err(WriteError::Read(ReadError::Corruption(_)))),
            "{scenario}: Writer must share Reader semantic rejection, observed {result:?}"
        );
        let row = db
            .query_one(
                &format!("SELECT revision FROM {schema}.runs WHERE harness_run_id=$1"),
                &[&run_id],
            )
            .unwrap();
        assert_eq!(row.get::<_, i64>(0), 1, "{scenario}: invalid Run changed");
        let inserted = db
            .query_one(
                &format!("SELECT COUNT(*)::bigint FROM {schema}.run_events WHERE event_id=$1"),
                &[&id],
            )
            .unwrap();
        assert_eq!(
            inserted.get::<_, i64>(0),
            0,
            "{scenario}: forbidden Event persisted"
        );
    }
    assert_eq!(checked, 24, "missing Python source invalid Contract cases");
    println!("PG18_WRITER_REJECTED_PYTHON_INVALID_CONTRACTS=24");
}

#[test]
#[ignore = "independent valid legacy/current Contract writer parity on disposable PG18"]
fn native_writer_keeps_all_ten_python_valid_contract_variants() {
    let dsn = std::env::var("HARNESS_RUST_TEST_PG_DSN").unwrap();
    let schema = std::env::var("HARNESS_RUST_TEST_SCHEMA").unwrap();
    assert!(schema.starts_with("hpg_rust_isolated_a_"));
    let cases = std::env::var("HARNESS_RUST_TEST_VALID_CONTRACT_CASES").unwrap();
    let mut db = Client::connect(&dsn, NoTls).unwrap();
    let mut checked = 0;
    for line in cases.lines() {
        let (scenario, run_id) = line.split_once('|').expect("valid case|Run ID");
        checked += 1;
        assert_eq!(
            read_run_readonly(&mut db, &schema, run_id)
                .unwrap()
                .projection
                .revision,
            1
        );
        let lease = acquire_run_lease(
            &mut db,
            &schema,
            run_id,
            "rust:valid-contract-parity",
            10000,
            1000,
            Some(1),
        )
        .unwrap();
        let id = format!("event:valid-contract-writer-parity-{scenario}");
        let ev = trace(&id, 1200);
        assert_eq!(
            append_events(
                &mut db,
                &schema,
                run_id,
                std::slice::from_ref(&ev),
                1,
                &lease,
                1100
            )
            .unwrap(),
            Admission::Created,
            "{scenario}"
        );
        let readback = read_run_readonly(&mut db, &schema, run_id).unwrap();
        assert_eq!(readback.projection.revision, 2, "{scenario}");
        assert_eq!(
            append_events(&mut db, &schema, run_id, &[ev], 1, &lease, 1100).unwrap(),
            Admission::Existing,
            "{scenario}: exact replay needs no renewed Lease"
        );
    }
    assert_eq!(checked, 10, "missing Python source valid Contract cases");
    println!("PG18_WRITER_ACCEPTED_PYTHON_VALID_CONTRACTS=10");
}
