//! dispatch cases: native PG18 behavior tests.
use super::*;

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_runner_bound_exact_dispatch_becomes_running() {
    let dsn = physical_pg_test_dsn();
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    let input = payload("bound", "job-bound", "ws-bound", 2);
    store.admit(&input).unwrap();
    allocate_fixture(&mut scratch, &input);
    let bundle = format!("sha256:{}", "b".repeat(64));
    store
        .commit_bundle_ready_pg(&PgBundleReady {
            attempt_id: input.attempt_id.clone(),
            expected_row_version: 0,
            bundle_digest: bundle.clone(),
            observed_at_ms: input.created_at_ms + 1,
            expected_source_sha256: input.expected_source_sha256.clone(),
        })
        .unwrap();
    store
        .mark_dispatch_issued_pg(
            &PgDispatchIssued {
                attempt_id: input.attempt_id.clone(),
                expected_row_version: 1,
                expected_bundle_digest: bundle.clone(),
                observed_at_ms: input.created_at_ms + 2,
                expected_source_sha256: input.expected_source_sha256.clone(),
            },
            None,
            None,
        )
        .unwrap();
    let witness = PgRunnerBound {
        attempt_id: input.attempt_id.clone(),
        expected_row_version: 2,
        expected_bundle_digest: bundle,
        runner_start_digest: format!("sha256:{}", "c".repeat(64)),
        native_invocation_id: "invocation-one".into(),
        observed_at_ms: input.created_at_ms + 3,
        expected_source_sha256: input.expected_source_sha256.clone(),
    };
    let mut invalid = witness.clone();
    invalid.expected_source_sha256 = "f".repeat(64);
    assert!(matches!(
        store.mark_runner_bound_pg(&invalid),
        Err(PgAdmissionError::Unqualified)
    ));
    assert_eq!(store.mark_runner_bound_pg(&witness).unwrap(), 3);
    let row = scratch
        .admin
        .query_one(
            "SELECT state,row_version,started_at_ms FROM attempts WHERE attempt_id=$1",
            &[&input.attempt_id],
        )
        .unwrap();
    assert_eq!(row.get::<_, String>(0), "running");
    assert_eq!(row.get::<_, i64>(1), 3);
    assert_eq!(row.get::<_, Option<i64>>(2), Some(witness.observed_at_ms));
    let event = scratch.admin.query_one(
            "SELECT event_type,origin,previous_state,new_state,reason_code,detail_json FROM job_events WHERE job_id=$1 AND event_sequence=6",
            &[&input.job_id],
        ).unwrap();
    assert_eq!(event.get::<_, String>(0), "RUNNER_BOUND");
    assert_eq!(event.get::<_, String>(1), "SYSTEM_OBSERVED");
    assert_eq!(
        event.get::<_, Option<String>>(2).as_deref(),
        Some("starting")
    );
    assert_eq!(
        event.get::<_, Option<String>>(3).as_deref(),
        Some("running")
    );
    assert_eq!(event.get::<_, String>(4), "SUPERVISOR_OWNER_MATCHED");
    let detail: serde_json::Value = serde_json::from_str(&event.get::<_, String>(5)).unwrap();
    assert_eq!(detail["runnerStartDigest"], witness.runner_start_digest);
    assert_eq!(detail["invocationId"], witness.native_invocation_id);
    assert_eq!(scratch.count("job_events"), 6);
    assert!(matches!(
        store.mark_runner_bound_pg(&witness),
        Err(PgAdmissionError::Blocked)
    ));
    assert_eq!(scratch.count("job_events"), 6);

    // Existing terminal CAS, reservation release and replay must retain
    // their original semantics after the new positive native start.
    let terminal = PgTerminalNoArtifacts {
        attempt_id: input.attempt_id.clone(),
        expected_row_version: 3,
        terminal_state: "succeeded".into(),
        result_digest: format!("sha256:{}", "d".repeat(64)),
        reason_code: "PROCESS_EXIT_ZERO".into(),
        exit_code: Some(0),
        finished_at_ms: witness.observed_at_ms + 1,
        expected_source_sha256: input.expected_source_sha256.clone(),
    };
    assert_eq!(
        store.commit_terminal_no_artifacts(&terminal).unwrap(),
        PgTerminalOutcome::Committed(input.job_id.clone()),
    );
    assert_eq!(
        store.commit_terminal_no_artifacts(&terminal).unwrap(),
        PgTerminalOutcome::Existing(input.job_id.clone()),
    );
    let final_state = scratch
        .admin
        .query_one(
            "SELECT j.resolution,j.current_attempt_id,r.state FROM jobs j \
             JOIN attempts a ON a.job_id=j.job_id \
             JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id WHERE j.job_id=$1",
            &[&input.job_id],
        )
        .unwrap();
    assert_eq!(
        final_state.get::<_, Option<String>>(0).as_deref(),
        Some("succeeded")
    );
    assert_eq!(final_state.get::<_, Option<String>>(1), None);
    assert_eq!(final_state.get::<_, String>(2), "released");
    assert_eq!(scratch.count("job_events"), 8);

    // Cancellation between dispatch intent and positive start must win:
    // even a guessed current row version cannot revive the Attempt.
    let cancelled = payload(
        "cancel-after-issue",
        "job-cancel-after",
        "ws-cancel-after",
        2,
    );
    store.admit(&cancelled).unwrap();
    allocate_fixture(&mut scratch, &cancelled);
    let cancelled_bundle = format!("sha256:{}", "e".repeat(64));
    store
        .commit_bundle_ready_pg(&PgBundleReady {
            attempt_id: cancelled.attempt_id.clone(),
            expected_row_version: 0,
            bundle_digest: cancelled_bundle.clone(),
            observed_at_ms: cancelled.created_at_ms + 1,
            expected_source_sha256: cancelled.expected_source_sha256.clone(),
        })
        .unwrap();
    store
        .mark_dispatch_issued_pg(
            &PgDispatchIssued {
                attempt_id: cancelled.attempt_id.clone(),
                expected_row_version: 1,
                expected_bundle_digest: cancelled_bundle.clone(),
                observed_at_ms: cancelled.created_at_ms + 2,
                expected_source_sha256: cancelled.expected_source_sha256.clone(),
            },
            None,
            None,
        )
        .unwrap();
    store
        .request_cancel_intent(&PgCancelIntent {
            job_id: cancelled.job_id.clone(),
            observed_at_ms: cancelled.created_at_ms + 3,
            expected_source_sha256: cancelled.expected_source_sha256.clone(),
        })
        .unwrap();
    let revoked = PgRunnerBound {
        attempt_id: cancelled.attempt_id.clone(),
        expected_row_version: 3,
        expected_bundle_digest: cancelled_bundle,
        runner_start_digest: format!("sha256:{}", "c".repeat(64)),
        native_invocation_id: "invocation-cancelled".into(),
        observed_at_ms: cancelled.created_at_ms + 4,
        expected_source_sha256: cancelled.expected_source_sha256.clone(),
    };
    assert!(matches!(
        store.mark_runner_bound_pg(&revoked),
        Err(PgAdmissionError::Blocked),
    ));
    let cancelled_state = scratch
        .admin
        .query_one(
            "SELECT a.state,COUNT(e.event_id) FILTER(WHERE e.event_type='RUNNER_BOUND') \
             FROM attempts a LEFT JOIN job_events e ON e.attempt_id=a.attempt_id \
             WHERE a.attempt_id=$1 GROUP BY a.state",
            &[&cancelled.attempt_id],
        )
        .unwrap();
    assert_eq!(cancelled_state.get::<_, String>(0), "stopping");
    assert_eq!(cancelled_state.get::<_, i64>(1), 0);
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_bundle_and_dispatch_commit_before_external_effect() {
    let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
        .expect("explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification required");
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    let a = payload("dispatch-request", "dispatch-job", "dispatch-ws", 2);
    assert_eq!(
        store.admit(&a).unwrap(),
        PgAdmissionOutcome::Created(a.job_id.clone())
    );
    allocate_fixture(&mut scratch, &a);
    let digest = format!("sha256:{}", "b".repeat(64));
    let issued = PgDispatchIssued {
        attempt_id: a.attempt_id.clone(),
        expected_row_version: 1,
        expected_bundle_digest: digest.clone(),
        observed_at_ms: a.created_at_ms + 2,
        expected_source_sha256: a.expected_source_sha256.clone(),
    };
    assert!(matches!(
        store.mark_dispatch_issued_pg(&issued, None, None),
        Err(PgAdmissionError::Blocked)
    ));
    assert_eq!(scratch.count("job_events"), 3);
    let prepared = PgBundleReady {
        attempt_id: a.attempt_id.clone(),
        expected_row_version: 0,
        bundle_digest: digest.clone(),
        observed_at_ms: a.created_at_ms + 1,
        expected_source_sha256: a.expected_source_sha256.clone(),
    };
    assert_eq!(store.commit_bundle_ready_pg(&prepared).unwrap(), 1);
    assert!(matches!(
        store.commit_bundle_ready_pg(&prepared),
        Err(PgAdmissionError::Blocked)
    ));
    assert_eq!(scratch.count("job_events"), 4);
    // Wrong source cut and missing original bundle evidence must never
    // permit an attempted dispatch, even when the Attempt row looks ready.
    let mut wrong_source = issued.clone();
    wrong_source.expected_source_sha256 = "f".repeat(64);
    assert!(matches!(
        store.mark_dispatch_issued_pg(&wrong_source, None, None),
        Err(PgAdmissionError::Unqualified)
    ));
    let original_detail = serde_json::json!({"bundleDigest": digest}).to_string();
    let original_digest = format!(
        "sha256:{}",
        hex::encode(Sha256::digest(original_detail.as_bytes()))
    );
    scratch.admin.execute(
            "UPDATE job_events SET detail_digest='sha256:tampered'              WHERE job_id=$1 AND event_type='BUNDLE_READY'",
            &[&a.job_id],
        ).unwrap();
    assert!(matches!(
        store.mark_dispatch_issued_pg(&issued, None, None),
        Err(PgAdmissionError::Blocked)
    ));
    assert_eq!(scratch.count("job_events"), 4);
    scratch.admin.execute(
            "UPDATE job_events SET detail_digest=$1              WHERE job_id=$2 AND event_type='BUNDLE_READY'",
            &[&original_digest, &a.job_id],
        ).unwrap();
    assert_eq!(
        store.mark_dispatch_issued_pg(&issued, None, None).unwrap(),
        2
    );
    assert_eq!(scratch.count("job_events"), 5);
    assert!(matches!(
        store.mark_dispatch_issued_pg(&issued, None, None),
        Err(PgAdmissionError::Blocked)
    ));
    assert_eq!(scratch.count("job_events"), 5);
    let row = scratch
        .admin
        .query_one(
            "SELECT state,row_version,bundle_digest FROM attempts WHERE attempt_id=$1",
            &[&a.attempt_id],
        )
        .unwrap();
    assert_eq!(row.get::<_, String>(0), "starting");
    assert_eq!(row.get::<_, i64>(1), 2);
    assert_eq!(
        row.get::<_, Option<String>>(2).as_deref(),
        Some(digest.as_str())
    );
    let event = scratch.admin.query_one(
            "SELECT origin,reason_code,previous_state,new_state FROM job_events WHERE job_id=$1 AND event_sequence=5",
            &[&a.job_id],
        ).unwrap();
    assert_eq!(event.get::<_, String>(0), "SYSTEM_DERIVED");
    assert_eq!(event.get::<_, String>(1), "AT_MOST_ONCE_BOUNDARY_COMMITTED");
    assert_eq!(
        event.get::<_, Option<String>>(2).as_deref(),
        Some("accepted")
    );
    assert_eq!(
        event.get::<_, Option<String>>(3).as_deref(),
        Some("starting")
    );
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_concurrent_dispatch_has_one_committed_issuer() {
    let dsn = physical_pg_test_dsn();
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    let input = payload("dispatch-race", "job-dispatch-race", "ws-dispatch-race", 2);
    store.admit(&input).unwrap();
    allocate_fixture(&mut scratch, &input);
    let bundle = format!("sha256:{}", "b".repeat(64));
    assert_eq!(
        store
            .commit_bundle_ready_pg(&PgBundleReady {
                attempt_id: input.attempt_id.clone(),
                expected_row_version: 0,
                bundle_digest: bundle.clone(),
                observed_at_ms: input.created_at_ms + 1,
                expected_source_sha256: input.expected_source_sha256.clone(),
            })
            .unwrap(),
        1
    );
    let issued = PgDispatchIssued {
        attempt_id: input.attempt_id.clone(),
        expected_row_version: 1,
        expected_bundle_digest: bundle.clone(),
        observed_at_ms: input.created_at_ms + 2,
        expected_source_sha256: input.expected_source_sha256.clone(),
    };

    // Independent connections, both contending for the same committed version.
    // A database serialization loser is not a second dispatch authorization.
    let gate = Arc::new(Barrier::new(3));
    let workers: Vec<_> = (0..2)
        .map(|_| {
            let mut contender = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
            let issued = issued.clone();
            let gate = gate.clone();
            thread::spawn(move || {
                gate.wait();
                contender.mark_dispatch_issued_pg(&issued, None, None)
            })
        })
        .collect();
    gate.wait();
    let mut winners = 0;
    let mut rejected = 0;
    for worker in workers {
        match worker.join().unwrap() {
            Ok(2) => winners += 1,
            Err(PgAdmissionError::Blocked) => rejected += 1,
            Err(PgAdmissionError::Database(error))
                if error.code() == Some(&postgres::error::SqlState::T_R_SERIALIZATION_FAILURE) =>
            {
                rejected += 1;
            }
            unexpected => panic!("unsafe concurrent dispatch result: {unexpected:?}"),
        }
    }
    assert_eq!((winners, rejected), (1, 1));

    // Independently read persisted state and events, not only return values.
    let row = scratch
        .admin
        .query_one(
            "SELECT a.state,a.row_version,a.bundle_digest,j.current_attempt_id,r.state, \
             (SELECT COUNT(*) FROM job_events e WHERE e.attempt_id=a.attempt_id \
              AND e.event_type='DISPATCH_ISSUED') \
             FROM attempts a JOIN jobs j ON j.job_id=a.job_id \
             JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id \
             WHERE a.attempt_id=$1",
            &[&input.attempt_id],
        )
        .unwrap();
    assert_eq!(row.get::<_, String>(0), "starting");
    assert_eq!(row.get::<_, i64>(1), 2);
    assert_eq!(row.get::<_, Option<String>>(2), Some(bundle));
    assert_eq!(
        row.get::<_, Option<String>>(3),
        Some(input.attempt_id.clone())
    );
    assert_eq!(row.get::<_, String>(4), "active");
    assert_eq!(row.get::<_, i64>(5), 1);
    assert_eq!(scratch.count("job_events"), 5);
    assert!(matches!(
        store.mark_dispatch_issued_pg(&issued, None, None),
        Err(PgAdmissionError::Blocked)
    ));
    assert_eq!(scratch.count("job_events"), 5);
    // This fixture commits the database fence; it never calls the OS launcher.
}
