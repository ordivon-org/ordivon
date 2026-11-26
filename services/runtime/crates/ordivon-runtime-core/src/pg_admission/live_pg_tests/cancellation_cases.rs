//! cancellation cases: native PG18 behavior tests.
use super::*;

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_cancel_commit_readback_is_exact_and_fail_closed_after_ack_loss() {
    let dsn = physical_pg_test_dsn();
    let mut scratch = Scratch::new(&dsn);
    let mut writer = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    let mut observer = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    let input = payload("readback-cancel", "job-readback", "ws-readback", 1);
    let intent = PgCancelIntent {
        job_id: input.job_id.clone(),
        observed_at_ms: 1234600,
        expected_source_sha256: input.expected_source_sha256.clone(),
    };
    assert!(matches!(
        observer.observe_cancel_intent(&intent),
        Err(PgAdmissionError::Unqualified)
    ));
    scratch.qualify();
    writer.admit(&input).unwrap();
    assert_eq!(
        observer.observe_cancel_intent(&intent).unwrap(),
        PgCancelObservation::Inconclusive
    );
    writer.request_cancel_intent(&intent).unwrap();
    // Reconcile on a separate native PG connection after a simulated
    // loss of the write-side acknowledgement.
    assert_eq!(
        observer.observe_cancel_intent(&intent).unwrap(),
        PgCancelObservation::Confirmed(input.job_id.clone())
    );
    let mut wrong_request = intent.clone();
    wrong_request.observed_at_ms += 1;
    assert_eq!(
        observer.observe_cancel_intent(&wrong_request).unwrap(),
        PgCancelObservation::Inconclusive
    );
    scratch
        .admin
        .execute(
            "UPDATE concurrency_reservations SET state='held_orphaned' WHERE attempt_id=$1",
            &[&input.attempt_id],
        )
        .unwrap();
    assert_eq!(
        observer.observe_cancel_intent(&intent).unwrap(),
        PgCancelObservation::Inconclusive
    );
    scratch
        .admin
        .execute(
            "UPDATE concurrency_reservations SET state='active' WHERE attempt_id=$1",
            &[&input.attempt_id],
        )
        .unwrap();
    scratch.admin.execute(
            "UPDATE job_events SET detail_digest='sha256:tampered' WHERE job_id=$1 AND event_type='STOP_REQUESTED'",
            &[&input.job_id],
        ).unwrap();
    assert_eq!(
        observer.observe_cancel_intent(&intent).unwrap(),
        PgCancelObservation::Inconclusive
    );
    assert_eq!(scratch.count("job_events"), 4);
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_cancel_intent_is_atomic_replayable_and_never_implies_dispatch_stopped() {
    let dsn = physical_pg_test_dsn();
    let mut scratch = Scratch::new(&dsn);
    let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    let first = payload("cancel-before-dispatch", "job-cancel-accepted", "ws-a", 2);
    let cancel = PgCancelIntent {
        job_id: first.job_id.clone(),
        observed_at_ms: 1234569,
        expected_source_sha256: first.expected_source_sha256.clone(),
    };
    assert!(matches!(
        store.request_cancel_intent(&cancel),
        Err(PgAdmissionError::Unqualified)
    ));
    scratch.qualify();
    store.admit(&first).unwrap();
    assert_eq!(
        store.request_cancel_intent(&cancel).unwrap(),
        PgCancelOutcome::IntentRecorded(first.job_id.clone())
    );
    assert_eq!(
        store.request_cancel_intent(&cancel).unwrap(),
        PgCancelOutcome::Existing(first.job_id.clone())
    );
    let row = scratch.admin.query_one(
            "SELECT j.desired_state,j.resolution,a.state,a.termination_intent,r.state FROM jobs j JOIN attempts a ON a.job_id=j.job_id JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id WHERE j.job_id=$1",
            &[&first.job_id],
        ).unwrap();
    assert_eq!(row.get::<_, String>(0), "cancelled");
    assert_eq!(row.get::<_, Option<String>>(1), None);
    assert_eq!(row.get::<_, String>(2), "accepted");
    assert_eq!(row.get::<_, String>(3), "stop_requested");
    assert_eq!(row.get::<_, String>(4), "active");
    assert_eq!(scratch.count("job_events"), 4);
    assert!(matches!(
        store.admit(&payload("new-job", "new-job", "ws-a", 2)),
        Ok(PgAdmissionOutcome::Created(_))
    ));
    let wrong_source = PgCancelIntent {
        expected_source_sha256: "b".repeat(64),
        ..cancel
    };
    assert!(matches!(
        store.request_cancel_intent(&wrong_source),
        Err(PgAdmissionError::Unqualified)
    ));
    assert_eq!(scratch.count("job_events"), 7);
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_cancel_intent_running_orphan_and_missing_reservation_fences() {
    let dsn = physical_pg_test_dsn();
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    let running = payload("cancel-running", "job-running", "ws-a", 3);
    store.admit(&running).unwrap();
    scratch
        .admin
        .execute(
            "UPDATE attempts SET state='running',row_version=row_version+1 WHERE attempt_id=$1",
            &[&running.attempt_id],
        )
        .unwrap();
    let cancel = PgCancelIntent {
        job_id: running.job_id.clone(),
        observed_at_ms: 1234570,
        expected_source_sha256: running.expected_source_sha256.clone(),
    };
    assert_eq!(
        store.request_cancel_intent(&cancel).unwrap(),
        PgCancelOutcome::IntentRecorded(running.job_id.clone())
    );
    let state: String = scratch
        .admin
        .query_one(
            "SELECT state FROM attempts WHERE attempt_id=$1",
            &[&running.attempt_id],
        )
        .unwrap()
        .get(0);
    assert_eq!(state, "stopping");
    assert_eq!(
        store.request_cancel_intent(&cancel).unwrap(),
        PgCancelOutcome::Existing(running.job_id.clone())
    );
    let terminal = PgTerminalNoArtifacts {
        attempt_id: running.attempt_id.clone(),
        expected_row_version: 2,
        terminal_state: "cancelled".into(),
        result_digest: "sha256:stopped-by-runner".into(),
        reason_code: "PG_CANCEL_RUNNER_OBSERVED".into(),
        exit_code: None,
        finished_at_ms: 1234571,
        expected_source_sha256: running.expected_source_sha256.clone(),
    };
    assert_eq!(
        store.commit_terminal_no_artifacts(&terminal).unwrap(),
        PgTerminalOutcome::Committed(running.job_id.clone())
    );
    assert_eq!(
        store.request_cancel_intent(&cancel).unwrap(),
        PgCancelOutcome::Existing(running.job_id.clone())
    );
    let released: String = scratch
        .admin
        .query_one(
            "SELECT state FROM concurrency_reservations WHERE attempt_id=$1",
            &[&running.attempt_id],
        )
        .unwrap()
        .get(0);
    assert_eq!(released, "released");

    let orphan = payload("cancel-orphan", "job-orphan", "ws-a", 3);
    store.admit(&orphan).unwrap();
    store
        .commit_terminal_no_artifacts(&PgTerminalNoArtifacts {
            attempt_id: orphan.attempt_id.clone(),
            expected_row_version: 0,
            terminal_state: "orphaned".into(),
            result_digest: "sha256:orphan".into(),
            reason_code: "ORPHAN_OBSERVED".into(),
            exit_code: None,
            finished_at_ms: 1234572,
            expected_source_sha256: orphan.expected_source_sha256.clone(),
        })
        .unwrap();
    let orphan_cancel = PgCancelIntent {
        job_id: orphan.job_id.clone(),
        observed_at_ms: 1234573,
        expected_source_sha256: orphan.expected_source_sha256.clone(),
    };
    assert_eq!(
        store.request_cancel_intent(&orphan_cancel).unwrap(),
        PgCancelOutcome::IntentRecorded(orphan.job_id.clone())
    );
    let orphan_row=scratch.admin.query_one(
            "SELECT j.resolution,j.desired_state,a.state,a.termination_intent,r.state FROM jobs j JOIN attempts a ON a.job_id=j.job_id JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id WHERE j.job_id=$1",
            &[&orphan.job_id],
        ).unwrap();
    assert_eq!(orphan_row.get::<_, String>(0), "orphaned");
    assert_eq!(orphan_row.get::<_, String>(1), "cancelled");
    assert_eq!(orphan_row.get::<_, String>(2), "orphaned");
    assert_eq!(orphan_row.get::<_, String>(3), "stop_requested");
    assert_eq!(orphan_row.get::<_, String>(4), "held_orphaned");
    assert_eq!(
        store.request_cancel_intent(&orphan_cancel).unwrap(),
        PgCancelOutcome::Existing(orphan.job_id.clone())
    );

    let invalid = payload("missing-reservation", "job-missing", "ws-b", 3);
    store.admit(&invalid).unwrap();
    scratch
        .admin
        .execute(
            "DELETE FROM concurrency_reservations WHERE attempt_id=$1",
            &[&invalid.attempt_id],
        )
        .unwrap();
    let before = scratch.count("job_events");
    let failed = PgCancelIntent {
        job_id: invalid.job_id.clone(),
        observed_at_ms: 1234574,
        expected_source_sha256: invalid.expected_source_sha256.clone(),
    };
    assert!(matches!(
        store.request_cancel_intent(&failed),
        Err(PgAdmissionError::Blocked)
    ));
    let desired: String = scratch
        .admin
        .query_one(
            "SELECT desired_state FROM jobs WHERE job_id=$1",
            &[&invalid.job_id],
        )
        .unwrap()
        .get(0);
    assert_eq!(desired, "run");
    assert_eq!(scratch.count("job_events"), before);
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_cancelled_after_issue_before_native_call_has_real_cas_not_fake_process_exit() {
    let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
        .expect("physical disposable PostgreSQL test DSN required");
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    let a = payload("r58-pre-handoff", "r58-job", "r58-workspace", 2);
    assert_eq!(
        store.admit(&a).unwrap(),
        PgAdmissionOutcome::Created(a.job_id.clone())
    );
    allocate_fixture(&mut scratch, &a);
    let digest = format!("sha256:{}", "a".repeat(64));
    assert_eq!(
        store
            .commit_bundle_ready_pg(&PgBundleReady {
                attempt_id: a.attempt_id.clone(),
                expected_row_version: 0,
                bundle_digest: digest.clone(),
                observed_at_ms: a.created_at_ms + 1,
                expected_source_sha256: a.expected_source_sha256.clone(),
            })
            .unwrap(),
        1
    );
    assert_eq!(
        store
            .mark_dispatch_issued_pg(
                &PgDispatchIssued {
                    attempt_id: a.attempt_id.clone(),
                    expected_row_version: 1,
                    expected_bundle_digest: digest.clone(),
                    observed_at_ms: a.created_at_ms + 2,
                    expected_source_sha256: a.expected_source_sha256.clone(),
                },
                None,
                None
            )
            .unwrap(),
        2
    );
    let original_issuer = PgDispatchIssued {
        attempt_id: a.attempt_id.clone(),
        expected_row_version: 2,
        expected_bundle_digest: digest.clone(),
        observed_at_ms: a.created_at_ms + 3,
        expected_source_sha256: a.expected_source_sha256.clone(),
    };
    assert!(
        !store
            .settle_cancel_before_native_handoff(&original_issuer)
            .unwrap(),
        "a live noncancelled issuer must still be permitted to submit native OS"
    );
    assert_eq!(
        store
            .request_cancel_intent(&PgCancelIntent {
                job_id: a.job_id.clone(),
                observed_at_ms: a.created_at_ms + 4,
                expected_source_sha256: a.expected_source_sha256.clone(),
            })
            .unwrap(),
        PgCancelOutcome::IntentRecorded(a.job_id.clone())
    );
    let mut bad = original_issuer.clone();
    bad.expected_bundle_digest = format!("sha256:{}", "f".repeat(64));
    assert!(matches!(
        store.settle_cancel_before_native_handoff(&bad),
        Err(PgAdmissionError::Blocked)
    ));
    assert!(
        store
            .settle_cancel_before_native_handoff(&original_issuer)
            .unwrap(),
        "unique original issuer owns no systemd call and must now settle cancellation"
    );
    let row = scratch.admin.query_one(
            "SELECT a.state,a.termination_intent,a.result_digest,j.desired_state,                     j.resolution,j.current_attempt_id,r.state FROM attempts a              JOIN jobs j ON j.job_id=a.job_id              JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id              WHERE a.attempt_id=$1",
            &[&a.attempt_id],
        ).unwrap();
    assert_eq!(row.get::<_, String>(0), "cancelled");
    assert_eq!(row.get::<_, String>(1), "stop_requested");
    assert!(row.get::<_, String>(2).starts_with("sha256:"));
    assert_eq!(row.get::<_, String>(3), "cancelled");
    assert_eq!(
        row.get::<_, Option<String>>(4).as_deref(),
        Some("cancelled")
    );
    assert_eq!(row.get::<_, Option<String>>(5), None);
    assert_eq!(row.get::<_, String>(6), "released");
    let counts = scratch.admin.query_one(
            "SELECT COUNT(*) FILTER(WHERE event_type='DISPATCH_ISSUED'),              COUNT(*) FILTER(WHERE event_type='STOP_REQUESTED'),              COUNT(*) FILTER(WHERE event_type='NATIVE_HANDOFF_PREVENTED'),              COUNT(*) FILTER(WHERE event_type='PROCESS_EXITED'),              COUNT(*) FILTER(WHERE event_type='JOB_TERMINAL')              FROM job_events WHERE job_id=$1",
            &[&a.job_id],
        ).unwrap();
    assert_eq!(counts.get::<_, i64>(0), 1);
    assert_eq!(counts.get::<_, i64>(1), 1);
    assert_eq!(counts.get::<_, i64>(2), 1);
    assert_eq!(
        counts.get::<_, i64>(3),
        0,
        "there was no OS process to exit"
    );
    assert_eq!(counts.get::<_, i64>(4), 1);
    let original_proof_digest: String = scratch.admin.query_one(
            "SELECT detail_digest FROM job_events WHERE job_id=$1 AND event_type='NATIVE_HANDOFF_PREVENTED'",
            &[&a.job_id],
        ).unwrap().get(0);
    match store
        .observe_job_readonly(&a.job_id, &a.expected_source_sha256)
        .unwrap()
    {
        crate::pg_readback::PgJobReadback::Observed(record) => {
            assert_eq!(record.resolution.as_deref(), Some("cancelled"));
            assert_eq!(record.reservation_state, "released");
            assert_eq!(record.desired_state, "cancelled");
        }
        other => panic!("original consumer cannot read pre-handoff cancellation: {other:?}"),
    }
    scratch
        .admin
        .execute(
            "UPDATE job_events SET detail_digest='sha256:tampered'
             WHERE job_id=$1 AND event_type='NATIVE_HANDOFF_PREVENTED'",
            &[&a.job_id],
        )
        .unwrap();
    assert_eq!(
        store
            .observe_job_readonly(&a.job_id, &a.expected_source_sha256)
            .unwrap(),
        crate::pg_readback::PgJobReadback::Inconclusive,
        "tampered non-Runner terminal evidence must not qualify a cancelled Job"
    );
    scratch
        .admin
        .execute(
            "UPDATE job_events SET detail_digest=$2
             WHERE job_id=$1 AND event_type='NATIVE_HANDOFF_PREVENTED'",
            &[&a.job_id, &original_proof_digest],
        )
        .unwrap();
    assert!(matches!(
        store.observe_job_readonly(&a.job_id, &a.expected_source_sha256).unwrap(),
        crate::pg_readback::PgJobReadback::Observed(record)
            if record.resolution.as_deref() == Some("cancelled")
    ));
    // Even a digest-correct no-native-call terminal cannot coexist with
    // independently recorded physical Runner admission.
    scratch.admin.execute(
            "INSERT INTO job_events(event_id,job_id,attempt_id,event_sequence,event_type,origin,previous_state,new_state,reason_code,detail_json,detail_digest,observed_at_ms)
             SELECT 'event-r58-forged-native-start',job_id,attempt_id,
                    (SELECT MAX(event_sequence)+1 FROM job_events WHERE job_id=$1),
                    'RUNNER_BOUND','SYSTEM_OBSERVED','starting','running',
                    'FORGED_TEST','{}','sha256:forged',observed_at_ms
             FROM job_events WHERE job_id=$1 AND event_type='DISPATCH_ISSUED'",
            &[&a.job_id],
        ).unwrap();
    assert_eq!(
        store
            .observe_job_readonly(&a.job_id, &a.expected_source_sha256)
            .unwrap(),
        crate::pg_readback::PgJobReadback::Inconclusive,
        "native Runner-bound and no-native-handoff terminal cannot both be true"
    );
    scratch
        .admin
        .execute(
            "DELETE FROM job_events WHERE event_id='event-r58-forged-native-start'",
            &[],
        )
        .unwrap();
    assert!(matches!(
        store.observe_job_readonly(&a.job_id, &a.expected_source_sha256).unwrap(),
        crate::pg_readback::PgJobReadback::Observed(record)
            if record.resolution.as_deref() == Some("cancelled")
    ));
    assert!(
        matches!(
            store.settle_cancel_before_native_handoff(&original_issuer),
            Err(PgAdmissionError::Blocked)
        ),
        "a resolved Job may never be passed to the original OS dispatcher again"
    );
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_cancellation_blocks_unissued_dispatch_without_false_terminal() {
    let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
        .expect("explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification required");
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    let a = payload("cancel-pre-dispatch", "cancel-job", "cancel-ws", 2);
    assert_eq!(
        store.admit(&a).unwrap(),
        PgAdmissionOutcome::Created(a.job_id.clone())
    );
    allocate_fixture(&mut scratch, &a);
    let digest = format!("sha256:{}", "d".repeat(64));
    let ready = PgBundleReady {
        attempt_id: a.attempt_id.clone(),
        expected_row_version: 0,
        bundle_digest: digest.clone(),
        observed_at_ms: a.created_at_ms + 1,
        expected_source_sha256: a.expected_source_sha256.clone(),
    };
    assert_eq!(store.commit_bundle_ready_pg(&ready).unwrap(), 1);
    assert_eq!(
        store
            .request_cancel_intent(&PgCancelIntent {
                job_id: a.job_id.clone(),
                observed_at_ms: a.created_at_ms + 2,
                expected_source_sha256: a.expected_source_sha256.clone(),
            })
            .unwrap(),
        PgCancelOutcome::IntentRecorded(a.job_id.clone())
    );
    let issued = PgDispatchIssued {
        attempt_id: a.attempt_id.clone(),
        expected_row_version: 2,
        expected_bundle_digest: digest.clone(),
        observed_at_ms: a.created_at_ms + 3,
        expected_source_sha256: a.expected_source_sha256.clone(),
    };
    assert!(matches!(
        store.mark_dispatch_issued_pg(&issued, None, None),
        Err(PgAdmissionError::Blocked)
    ));
    let row = scratch.admin.query_one(
            "SELECT a.state,j.desired_state,j.resolution,r.state FROM attempts a JOIN jobs j ON j.job_id=a.job_id JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id WHERE a.attempt_id=$1",
            &[&a.attempt_id],
        ).unwrap();
    assert_eq!(row.get::<_, String>(0), "accepted");
    assert_eq!(row.get::<_, String>(1), "cancelled");
    assert_eq!(row.get::<_, Option<String>>(2), None);
    assert_eq!(row.get::<_, String>(3), "active");
    assert_eq!(scratch.count("job_events"), 5);
}
