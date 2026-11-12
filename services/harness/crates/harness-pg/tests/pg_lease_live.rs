//! Same PostgreSQL 18 schema, Python Store → Rust native lease → Python Store.
//! Never executes a Tool or touches a production PostgreSQL connection.
use std::sync::{Arc, Barrier};
use std::thread;

use ordivon_harness_pg::lease::{acquire_run_lease, release_run_lease, LeaseError};
use ordivon_harness_pg::read_run_readonly;
use postgres::{Client, NoTls};

fn fixture() -> (String, String, serde_json::Value) {
    let dsn = std::env::var("HARNESS_RUST_TEST_PG_DSN").expect("isolated PG DSN");
    let schema = std::env::var("HARNESS_RUST_TEST_SCHEMA").expect("scratch schema");
    assert!(schema.starts_with("hpg_rust_isolated_a_"));
    let file = std::env::var("HARNESS_RUST_TEST_FIXTURE_PATH").expect("fixture.json");
    let data: serde_json::Value =
        serde_json::from_slice(&std::fs::read(file).expect("fixture bytes"))
            .expect("Python fixture JSON");
    (dsn, schema, data)
}

fn run<'a>(manifest: &'a serde_json::Value, kind: &str) -> &'a str {
    manifest["lease_rust_fixture"][kind]
        .as_str()
        .expect("source Run identity")
}

fn from_db(conn: &mut Client, schema: &str, run_id: &str) -> Option<RunLeaseRow> {
    // Independently check the live transaction result rather than only the
    // Rust-returned value. Dynamic search_path uses the validated test schema.
    assert!(schema
        .bytes()
        .all(|ch| ch.is_ascii_lowercase() || ch.is_ascii_digit() || ch == b'_'));
    let mut tx = conn.transaction().unwrap();
    tx.batch_execute(&format!("SET LOCAL search_path TO {schema}"))
        .unwrap();
    let row = tx
        .query_opt(
            "SELECT owner_id,lease_revision,run_revision,expires_at_ms \
             FROM run_leases WHERE harness_run_id=$1",
            &[&run_id],
        )
        .unwrap();
    let observed = row.map(|r| RunLeaseRow {
        owner_id: r.get("owner_id"),
        lease_revision: r.get("lease_revision"),
        run_revision: r.get("run_revision"),
        expires_at_ms: r.get("expires_at_ms"),
    });
    tx.commit().unwrap();
    observed
}

#[derive(Debug, PartialEq, Eq)]
struct RunLeaseRow {
    owner_id: String,
    lease_revision: i64,
    run_revision: i64,
    expires_at_ms: i64,
}

#[test]
#[ignore = "requires private PG18 and Python-written v1 Run fixtures"]
fn native_run_lease_owner_race_revision_expiry_cross_language() {
    let (dsn, schema, data) = fixture();
    let mut db = Client::connect(&dsn, NoTls).expect("isolated PG writer role");
    let rust_run = run(&data, "rust");
    let python_run = run(&data, "python");
    let handoff_run = run(&data, "handoff");
    let revision_run = run(&data, "revision");
    let race_run = run(&data, "race");
    let tampered_run = run(&data, "tamper");
    let terminal_run = data["valid"].as_str().expect("Python terminal Run");

    // New native lease committed with the exact Python schema version and
    // RunRevision. Repeating the same-owner claim does NOT renew TTL.
    let first = acquire_run_lease(
        &mut db,
        &schema,
        rust_run,
        "rust:owner-A",
        500,
        1000,
        Some(1),
    )
    .expect("Rust native lease creates a PG tuple");
    assert_eq!(
        (
            first.lease_revision(),
            first.run_revision(),
            first.expires_at_ms()
        ),
        (1, 1, 1500)
    );
    assert_eq!(
        from_db(&mut db, &schema, rust_run),
        Some(RunLeaseRow {
            owner_id: "rust:owner-A".to_string(),
            lease_revision: 1,
            run_revision: 1,
            expires_at_ms: 1500,
        })
    );
    assert_eq!(
        acquire_run_lease(
            &mut db,
            &schema,
            rust_run,
            "rust:owner-A",
            900,
            1100,
            Some(1)
        )
        .unwrap(),
        first
    );
    assert!(matches!(
        acquire_run_lease(
            &mut db,
            &schema,
            rust_run,
            "rust:owner-B",
            900,
            1101,
            Some(1)
        ),
        Err(LeaseError::Held)
    ));

    // Exact boundary is expired: expiresAtMs == nowMs is NO longer held.
    let second = acquire_run_lease(
        &mut db,
        &schema,
        rust_run,
        "rust:owner-B",
        1000,
        1500,
        Some(1),
    )
    .expect("expired lease must be replaced");
    assert_eq!(
        (
            second.lease_revision(),
            second.owner_id(),
            second.expires_at_ms()
        ),
        (2, "rust:owner-B", 2500)
    );
    assert!(!release_run_lease(&mut db, &schema, &first).unwrap());
    assert_eq!(
        from_db(&mut db, &schema, rust_run).unwrap().lease_revision,
        2
    );
    assert!(release_run_lease(&mut db, &schema, &second).unwrap());
    assert!(!release_run_lease(&mut db, &schema, &second).unwrap());

    // A SELECT-only PG role must not acquire a lease or delete another
    // execution's lease. Verify the server's actual SQLSTATE 42501, not a
    // mocked Rust gate. The fresh Run remains unleased after this attempt.
    let readonly_dsn =
        std::env::var("HARNESS_RUST_TEST_PG_READONLY_DSN").expect("SELECT-only role DSN");
    let mut readonly = Client::connect(&readonly_dsn, NoTls).expect("read-only PG role");
    let denied = acquire_run_lease(
        &mut readonly,
        &schema,
        rust_run,
        "rust:readonly-attempt",
        100,
        2600,
        Some(1),
    );
    assert!(
        matches!(denied, Err(LeaseError::Database(ref error))
            if error.code() == Some(&postgres::error::SqlState::INSUFFICIENT_PRIVILEGE)),
        "unexpected readonly acquire result: {denied:?}"
    );
    assert!(from_db(&mut db, &schema, rust_run).is_none());

    // Python owns this existing lease. Native Rust cannot silently steal or
    // extend it. At expiry only, the original generation must increment.
    assert!(matches!(
        acquire_run_lease(
            &mut db,
            &schema,
            python_run,
            "rust:after-expiry",
            100,
            1500,
            Some(1)
        ),
        Err(LeaseError::Held)
    ));
    let py_same = acquire_run_lease(
        &mut db,
        &schema,
        python_run,
        "python:source-owner",
        999,
        1800,
        Some(1),
    )
    .unwrap();
    assert_eq!(
        (py_same.lease_revision(), py_same.expires_at_ms()),
        (1, 2000)
    );
    let py_expired = acquire_run_lease(
        &mut db,
        &schema,
        python_run,
        "rust:after-expiry",
        800,
        2000,
        Some(1),
    )
    .unwrap();
    assert_eq!(
        (py_expired.lease_revision(), py_expired.expires_at_ms()),
        (2, 2800)
    );
    assert!(!release_run_lease(&mut db, &schema, &py_same).unwrap());

    // A Rust lease can cross the language boundary in the opposite
    // direction: Python will later re-acquire/release the exact same tuple.
    let handoff = acquire_run_lease(
        &mut db,
        &schema,
        handoff_run,
        "rust:handoff",
        4000,
        1000,
        Some(1),
    )
    .unwrap();
    assert_eq!(handoff.expires_at_ms(), 5000);
    assert_eq!(handoff.harness_run_id(), handoff_run);
    assert_eq!(handoff.owner_id(), "rust:handoff");
    let denied_release = release_run_lease(&mut readonly, &schema, &handoff);
    assert!(
        matches!(denied_release, Err(LeaseError::Database(ref error))
            if error.code() == Some(&postgres::error::SqlState::INSUFFICIENT_PRIVILEGE)),
        "unexpected readonly release result: {denied_release:?}"
    );
    assert_eq!(
        from_db(&mut db, &schema, handoff_run).unwrap().owner_id,
        "rust:handoff"
    );

    // The Python Journal writer changed this Run from rev1 to rev2.
    assert!(matches!(
        acquire_run_lease(
            &mut db,
            &schema,
            revision_run,
            "rust:rev",
            500,
            1200,
            Some(1)
        ),
        Err(LeaseError::RevisionConflict)
    ));
    let current = acquire_run_lease(
        &mut db,
        &schema,
        revision_run,
        "rust:rev",
        500,
        1200,
        Some(2),
    )
    .unwrap();
    assert_eq!(current.run_revision(), 2);
    assert!(release_run_lease(&mut db, &schema, &current).unwrap());

    assert!(matches!(
        acquire_run_lease(
            &mut db,
            &schema,
            terminal_run,
            "rust:terminal",
            500,
            1200,
            Some(3)
        ),
        Err(LeaseError::TerminalConflict)
    ));
    assert!(matches!(
        acquire_run_lease(
            &mut db,
            &schema,
            "harness-run:missing-lease-test",
            "rust:owner",
            500,
            1200,
            None
        ),
        Err(LeaseError::MissingRun(_))
    ));
    assert!(matches!(
        acquire_run_lease(
            &mut db,
            &schema,
            tampered_run,
            "rust:owner",
            500,
            1200,
            Some(1)
        ),
        Err(LeaseError::Store(_))
    ));
    assert!(from_db(&mut db, &schema, tampered_run).is_none());

    // Bad arguments fail before any DB effect. PG bigint overflow never
    // writes a partially valid expired-at timestamp.
    for (owner, ttl, now) in [
        ("", 500, 1000),
        (" bad", 500, 1000),
        ("rust:bad", 0, 1000),
        ("rust:bad", 500, -1),
    ] {
        assert!(matches!(
            acquire_run_lease(&mut db, &schema, handoff_run, owner, ttl, now, None),
            Err(LeaseError::InvalidArguments)
        ));
    }
    assert!(matches!(
        acquire_run_lease(
            &mut db,
            &schema,
            handoff_run,
            "rust:over",
            100,
            i64::MAX - 10,
            None
        ),
        Err(LeaseError::ClockOrGenerationOverflow)
    ));
    assert!(matches!(
        acquire_run_lease(
            &mut db,
            "not.valid;drop",
            rust_run,
            "rust:owner",
            100,
            1000,
            None
        ),
        Err(LeaseError::InvalidSchema)
    ));

    // Two independent PG clients and transactions enter a real row-lock
    // race. Serial execution must leave one winner and one HELD; there is no
    // read-check-write window that allows both to claim simultaneously.
    let barrier = Arc::new(Barrier::new(2));
    let handles: Vec<_> = (0..2)
        .map(|n| {
            let dsn = dsn.clone();
            let schema = schema.clone();
            let race_run = race_run.to_owned();
            let gate = Arc::clone(&barrier);
            thread::spawn(move || {
                let mut client = Client::connect(&dsn, NoTls).unwrap();
                gate.wait();
                let owner = format!("rust:parallel-{n}");
                acquire_run_lease(&mut client, &schema, &race_run, &owner, 1000, 1500, Some(1))
            })
        })
        .collect();
    let mut wins = 0;
    let mut held = 0;
    for handle in handles {
        match handle.join().expect("PG lease contender") {
            Ok(lease) => {
                wins += 1;
                assert_eq!((lease.lease_revision(), lease.expires_at_ms()), (1, 2500));
            }
            Err(LeaseError::Held) => held += 1,
            Err(error) => panic!("unexpected competing lease outcome: {error}"),
        }
    }
    assert_eq!((wins, held), (1, 1));
    assert_eq!(
        (
            from_db(&mut db, &schema, race_run).unwrap().lease_revision,
            wins
        ),
        (1, 1)
    );
    println!("RUST_NATIVE_PG_LEASE_PYTHON_INTEROP_AND_CONCURRENT_FENCE_PASS");
}

#[test]
#[ignore = "after Python consumes native Rust Lease with real Journal transaction"]
fn python_journal_consumed_rust_native_lease_then_rust_replay() {
    let (dsn, schema, data) = fixture();
    let run_id = run(&data, "handoff");
    let mut db = Client::connect(&dsn, NoTls).expect("scratch PG18 writer");
    let result = read_run_readonly(&mut db, &schema, run_id)
        .expect("same Run must survive a cross-language Python Journal commit");
    assert_eq!(result.projection.status, "created");
    assert_eq!(result.projection.revision, 2);
    assert_eq!(result.events.len(), 2);
    assert_eq!(result.events[1].event_kind, "harness.trace-recorded");
    assert_eq!(
        result.events[1]
            .payload
            .field("data")
            .and_then(|value| value.field("source"))
            .and_then(|value| value.as_str()),
        Some("rust-native-lease")
    );
    assert!(
        from_db(&mut db, &schema, run_id).is_none(),
        "Python Writer consumed the Rust lease"
    );
    // Only the v2 RunRevision now admits another lease, not stale v1.
    assert!(matches!(
        acquire_run_lease(&mut db, &schema, run_id, "rust:later", 100, 1500, Some(1)),
        Err(LeaseError::RevisionConflict)
    ));
    let later = acquire_run_lease(&mut db, &schema, run_id, "rust:later", 100, 1500, Some(2))
        .expect("new Rev2 native lease");
    assert_eq!(later.run_revision(), 2);
    assert!(release_run_lease(&mut db, &schema, &later).unwrap());
    println!("PG18_RUST_LEASE_PYTHON_COMMITTED_JOURNAL_RUST_READBACK_PASS");
}
