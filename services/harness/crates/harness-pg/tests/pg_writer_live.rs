//! Real PostgreSQL18 Python Store -> Rust Writer -> Python Store conformance.
use std::sync::{Arc, Barrier};
use std::thread;

use ordivon_harness_core::CanonicalDocument as Doc;
use ordivon_harness_pg::journal_write::{
    append_events, observe_exact_batch, Admission, EventWrite, JournalObservation, StoredRef,
    WriteError,
};
use ordivon_harness_pg::lease::{acquire_run_lease, release_run_lease};
use ordivon_harness_pg::read_run_readonly;
use postgres::{Client, NoTls};

fn fixture() -> (String, String, serde_json::Value) {
    let dsn = std::env::var("HARNESS_RUST_TEST_PG_DSN").unwrap();
    let schema = std::env::var("HARNESS_RUST_TEST_SCHEMA").unwrap();
    assert!(schema.starts_with("hpg_rust_isolated_a_"));
    let file = std::env::var("HARNESS_RUST_TEST_FIXTURE_PATH").unwrap();
    let data = serde_json::from_slice(&std::fs::read(file).unwrap()).unwrap();
    (dsn, schema, data)
}
fn run<'a>(v: &'a serde_json::Value, name: &str) -> &'a str {
    v["rust_writer_fixture"]["runs"][name].as_str().unwrap()
}
fn obj(entries: Vec<(&str, Doc)>) -> Doc {
    Doc::object(
        entries
            .into_iter()
            .map(|(k, v)| (k.to_owned(), v))
            .collect(),
    )
    .unwrap()
}
fn number(v: &str) -> Doc {
    Doc::integer_from_decimal(v).unwrap()
}
fn event(
    id: &str,
    kind: &str,
    data: Doc,
    at: i64,
    cause: Option<&str>,
    refs: Vec<StoredRef>,
) -> EventWrite {
    EventWrite {
        event_id: id.to_owned(),
        event_kind: kind.to_owned(),
        data,
        recorded_at_ms: at,
        caused_by_event_id: cause.map(str::to_owned),
        referenced_objects: refs,
    }
}
fn ref_object(v: &serde_json::Value) -> StoredRef {
    let item = &v["rust_writer_fixture"]["referenced"];
    StoredRef {
        digest: item["digest"].as_str().unwrap().to_owned(),
        kind: item["kind"].as_str().unwrap().to_owned(),
        byte_length: item["byteLength"].as_i64().unwrap(),
    }
}
fn trace(id: &str, at: i64) -> EventWrite {
    event(
        id,
        "harness.trace-recorded",
        obj(vec![("note", Doc::string(id))]),
        at,
        None,
        vec![],
    )
}
fn revision(db: &mut Client, schema: &str, run: &str) -> i64 {
    read_run_readonly(db, schema, run)
        .unwrap()
        .projection
        .revision
}

#[test]
#[ignore = "private PG18 with real Python Store source fixture"]
fn native_writer_exact_batch_replay_and_cas() {
    let (dsn, schema, data) = fixture();
    let mut db = Client::connect(&dsn, NoTls).unwrap();
    let id = run(&data, "rust");
    let lease =
        acquire_run_lease(&mut db, &schema, id, "rust:journal", 4000, 1500, Some(1)).unwrap();
    assert_eq!(lease.expires_at_ms(), 5500);
    let batch = vec![
        event(
            "event:rust-native-writer-unknown",
            "harness.tool-step-unknown",
            obj(vec![
                ("reason", Doc::string("unknown-effect")),
                ("attempt", number("1")),
            ]),
            1700,
            None,
            vec![],
        ),
        event(
            "event:rust-native-writer-trace",
            "harness.trace-recorded",
            obj(vec![
                ("consumer", Doc::string("python-source")),
                ("recoverable", Doc::boolean(true)),
            ]),
            1800,
            Some("event:rust-native-writer-unknown"),
            vec![ref_object(&data)],
        ),
    ];
    assert_eq!(
        append_events(&mut db, &schema, id, &batch, 1, &lease, 1600).unwrap(),
        Admission::Created
    );
    let read = read_run_readonly(&mut db, &schema, id).unwrap();
    assert_eq!(read.projection.revision, 3);
    assert_eq!(read.projection.status, "active");
    assert_eq!(read.events.len(), 3);
    assert_eq!(read.events[1].event_kind, "harness.tool-step-unknown");
    assert_eq!(
        read.events[2].caused_by_event_id.as_deref(),
        Some("event:rust-native-writer-unknown")
    );
    assert!(!release_run_lease(&mut db, &schema, &lease).unwrap());

    // Lost commit response: close connection then exact retry on a new client.
    drop(db);
    let mut again = Client::connect(&dsn, NoTls).unwrap();
    let ro_dsn = std::env::var("HARNESS_RUST_TEST_PG_READONLY_DSN").unwrap();
    let mut ro = Client::connect(&ro_dsn, NoTls).unwrap();
    assert_eq!(
        observe_exact_batch(&mut ro, &schema, id, 1, &batch).unwrap(),
        JournalObservation::ExactCommitted
    );
    assert_eq!(
        observe_exact_batch(
            &mut ro,
            &schema,
            id,
            3,
            &[trace("event:not-in-journal", 1900)]
        )
        .unwrap(),
        JournalObservation::NotObserved
    );
    assert_eq!(
        append_events(&mut again, &schema, id, &batch, 1, &lease, 1600).unwrap(),
        Admission::Existing
    );
    assert_eq!(revision(&mut again, &schema, id), 3);
    // Reuse B's CAS reference-edge projection, adding only byte length
    // to the verified metadata. Non-Provider content stays private.
    let written_refs: Vec<_> = read
        .verified_reference_links
        .iter()
        .filter(|reference| reference.event_id() == "event:rust-native-writer-trace")
        .collect();
    assert_eq!(written_refs.len(), 1);
    assert_eq!(written_refs[0].kind(), "test-source-artifact");
    assert_eq!(written_refs[0].digest(), ref_object(&data).digest);
    assert_eq!(written_refs[0].byte_length(), ref_object(&data).byte_length);
    // Private non-Provider objects must not be projected as public content.
    assert!(read.provider_record_references.is_empty());
    let mut wrong_kind = batch.clone();
    wrong_kind[1].referenced_objects[0].kind = "pretend-kind".to_owned();
    assert!(matches!(
        observe_exact_batch(&mut ro, &schema, id, 1, &wrong_kind),
        Err(WriteError::Conflict(_))
    ));
    let mut wrong_length = batch.clone();
    wrong_length[1].referenced_objects[0].byte_length += 1;
    assert!(matches!(
        observe_exact_batch(&mut ro, &schema, id, 1, &wrong_length),
        Err(WriteError::Conflict(_))
    ));
    let mut changed = batch.clone();
    changed[1].data = obj(vec![("consumer", Doc::string("tampered"))]);
    assert!(matches!(
        observe_exact_batch(&mut ro, &schema, id, 1, &changed),
        Err(WriteError::Conflict(_))
    ));
    assert!(matches!(
        append_events(&mut again, &schema, id, &changed, 1, &lease, 1600),
        Err(WriteError::Conflict(_))
    ));
    let mut partial = batch.clone();
    partial.push(trace("event:partial-new", 1900));
    assert!(matches!(
        observe_exact_batch(&mut ro, &schema, id, 1, &partial),
        Err(WriteError::Conflict(_))
    ));
    assert!(matches!(
        append_events(&mut again, &schema, id, &partial, 1, &lease, 1600),
        Err(WriteError::Conflict(_))
    ));
    assert_eq!(revision(&mut again, &schema, id), 3);
    assert!(matches!(
        append_events(
            &mut again,
            &schema,
            id,
            &[trace("event:stale", 1900)],
            1,
            &lease,
            1700
        ),
        Err(WriteError::Revision)
    ));
    println!("PG18_NATIVE_WRITER_ATOMIC_CAS_EXACT_REPLAY_AND_PARTIAL_CONFLICT_PASS");
}

#[test]
#[ignore = "private PG18 with real Python Store source fixture"]
fn native_writer_rollback_terminal_race_and_readonly() {
    let (dsn, schema, data) = fixture();
    let mut db = Client::connect(&dsn, NoTls).unwrap();
    let id = run(&data, "rollback");
    let lease =
        acquire_run_lease(&mut db, &schema, id, "rust:rollback", 1000, 1200, Some(1)).unwrap();
    let bad = vec![
        trace("event:rolledback-first", 1400),
        event(
            "event:rolledback-foreign-cause",
            "harness.trace-recorded",
            obj(vec![("reason", Doc::string("foreign"))]),
            1450,
            Some(
                data["rust_writer_fixture"]["foreignEventId"]
                    .as_str()
                    .unwrap(),
            ),
            vec![],
        ),
    ];
    assert!(matches!(
        append_events(&mut db, &schema, id, &bad, 1, &lease, 1300),
        Err(WriteError::Conflict(_))
    ));
    assert_eq!(revision(&mut db, &schema, id), 1);
    assert_eq!(
        append_events(
            &mut db,
            &schema,
            id,
            &[trace("event:rollback-fixed", 1500)],
            1,
            &lease,
            1350
        )
        .unwrap(),
        Admission::Created
    );
    assert_eq!(revision(&mut db, &schema, id), 2);

    let terminal = run(&data, "terminal");
    let terminal_lease = acquire_run_lease(
        &mut db,
        &schema,
        terminal,
        "rust:terminal",
        5000,
        1300,
        Some(1),
    )
    .unwrap();
    let completed = event(
        "event:rust-native-terminal",
        "harness.run-completed",
        obj(vec![("exit", Doc::string("journal-only"))]),
        1450,
        None,
        vec![],
    );
    assert!(matches!(
        append_events(
            &mut db,
            &schema,
            terminal,
            &[completed.clone(), trace("event:after-terminal", 1500)],
            1,
            &terminal_lease,
            1400
        ),
        Err(WriteError::Terminal)
    ));
    assert_eq!(revision(&mut db, &schema, terminal), 1);
    assert_eq!(
        append_events(
            &mut db,
            &schema,
            terminal,
            &[completed],
            1,
            &terminal_lease,
            1400
        )
        .unwrap(),
        Admission::Created
    );
    assert_eq!(
        read_run_readonly(&mut db, &schema, terminal)
            .unwrap()
            .projection
            .status,
        "completed"
    );

    // Two independent writers present the same lease but different Event IDs.
    // The row lock and Revision CAS admit at most one.
    let race = run(&data, "race").to_owned();
    let race_lease =
        acquire_run_lease(&mut db, &schema, &race, "rust:race", 4000, 1500, Some(1)).unwrap();
    let barrier = Arc::new(Barrier::new(2));
    let handles: Vec<_> = (0..2)
        .map(|i| {
            let dsn = dsn.clone();
            let schema = schema.clone();
            let race = race.clone();
            let lease = race_lease.clone();
            let barrier = Arc::clone(&barrier);
            thread::spawn(move || {
                let mut client = Client::connect(&dsn, NoTls).unwrap();
                let e = trace(&format!("event:parallel-journal-{i}"), 1750);
                barrier.wait();
                append_events(&mut client, &schema, &race, &[e], 1, &lease, 1600)
            })
        })
        .collect();
    let mut committed = 0;
    let mut rejected = 0;
    for h in handles {
        match h.join().unwrap() {
            Ok(Admission::Created) => committed += 1,
            Err(WriteError::Revision) => rejected += 1,
            e => panic!("unexpected PG race result {e:?}"),
        }
    }
    assert_eq!((committed, rejected), (1, 1));
    assert_eq!(revision(&mut db, &schema, &race), 2);

    // SELECT-only role never writes a CAS, Journal event or Run revision.
    let readonly_dsn = std::env::var("HARNESS_RUST_TEST_PG_READONLY_DSN").unwrap();
    let mut read_only = Client::connect(&readonly_dsn, NoTls).unwrap();
    let denied_run = run(&data, "readonly");
    let rw_lease = acquire_run_lease(
        &mut db,
        &schema,
        denied_run,
        "rust:write",
        1000,
        1500,
        Some(1),
    )
    .unwrap();
    let err = append_events(
        &mut read_only,
        &schema,
        denied_run,
        &[trace("event:readonly-forbidden", 1700)],
        1,
        &rw_lease,
        1550,
    )
    .unwrap_err();
    assert!(
        matches!(err,WriteError::Db(ref db_error)
        if db_error.code()==Some(&postgres::error::SqlState::INSUFFICIENT_PRIVILEGE)),
        "unexpected readonly failure {err:?}"
    );
    assert_eq!(revision(&mut db, &schema, denied_run), 1);
    assert!(release_run_lease(&mut db, &schema, &rw_lease).unwrap());
    println!("PG18_NATIVE_WRITER_ROLLBACK_TERMINAL_RACE_READONLY_PASS");
}

#[test]
#[ignore = "private PG18 with Python-origin Run Contract and bounded batch"]
fn native_writer_max_batch_expired_lease_and_failed_cas_are_atomic() {
    let (dsn, schema, data) = fixture();
    let mut db = Client::connect(&dsn, NoTls).unwrap();
    let run_id = run(&data, "bounded");
    let lease =
        acquire_run_lease(&mut db, &schema, run_id, "rust:batch", 8000, 1500, Some(1)).unwrap();
    let values: Vec<_> = (0..256)
        .map(|i| {
            let mut e = trace(&format!("event:bounded-rust-{i}"), 1600 + i);
            if i > 0 {
                e.caused_by_event_id = Some(format!("event:bounded-rust-{}", i - 1));
            }
            e
        })
        .collect();
    let mut too_many = values.clone();
    too_many.push(trace("event:over-256", 1900));
    assert!(matches!(
        append_events(&mut db, &schema, run_id, &too_many, 1, &lease, 1550),
        Err(WriteError::Invalid(_))
    ));
    assert_eq!(revision(&mut db, &schema, run_id), 1);
    assert_eq!(
        append_events(&mut db, &schema, run_id, &values, 1, &lease, 1550).unwrap(),
        Admission::Created
    );
    let after = read_run_readonly(&mut db, &schema, run_id).unwrap();
    assert_eq!(after.projection.revision, 257);
    assert_eq!(after.projection.status, "created");
    assert_eq!(after.events.len(), 257);
    assert_eq!(
        after.events.last().unwrap().caused_by_event_id.as_deref(),
        Some("event:bounded-rust-254")
    );

    // Expiry on the exact boundary must reject admission, roll back all CAS
    // inserts, leave the lease tuple, and allow a successor owner after expiry.
    let expired = run(&data, "expired");
    let old =
        acquire_run_lease(&mut db, &schema, expired, "rust:short", 100, 1500, Some(1)).unwrap();
    let at_boundary = trace("event:expired-at-boundary", 1600);
    assert!(matches!(
        append_events(&mut db, &schema, expired, &[at_boundary], 1, &old, 1600),
        Err(WriteError::Fenced)
    ));
    assert_eq!(revision(&mut db, &schema, expired), 1);
    let next = acquire_run_lease(
        &mut db,
        &schema,
        expired,
        "rust:successor",
        300,
        1600,
        Some(1),
    )
    .unwrap();
    assert_eq!(next.lease_revision(), old.lease_revision() + 1);
    assert!(!release_run_lease(&mut db, &schema, &old).unwrap());
    assert!(release_run_lease(&mut db, &schema, &next).unwrap());

    // Payload CAS is provisionally staged inside a PG transaction. A missing
    // referenced object must roll back the newly staged CAS and Run update.
    let reference_run = run(&data, "reference");
    let held = acquire_run_lease(
        &mut db,
        &schema,
        reference_run,
        "rust:reference",
        600,
        1500,
        Some(1),
    )
    .unwrap();
    assert!(matches!(
        append_events(
            &mut db,
            &schema,
            reference_run,
            &[event(
                "event:unbound-reference",
                "harness.trace-recorded",
                obj(vec![("note", Doc::string("no such object"))]),
                1600,
                None,
                vec![StoredRef {
                    digest: format!("sha256:{}", "c".repeat(64)),
                    kind: "never-stored".into(),
                    byte_length: 77
                }]
            )],
            1,
            &held,
            1550
        ),
        Err(WriteError::Conflict(_))
    ));
    assert_eq!(revision(&mut db, &schema, reference_run), 1);
    assert!(release_run_lease(&mut db, &schema, &held).unwrap());
    println!("PG18_NATIVE_WRITER_BATCH256_EXPIRY_CAS_REF_ROLLBACK_PASS");
}
