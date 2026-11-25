//! admission cases: native PG18 behavior tests.
use super::*;

/// Independent Windows native evidence reader consumes exact PostgreSQL
/// admission rows. A qualified PG row alone must NOT imply OS launch.
#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn windows_pg_bundle_consumer_reads_real_admission_without_claiming_process() {
    use crate::pg_windows_evidence::{inspect_admitted_windows_pg_bundle, PgWindowsWitnessPhase};
    use std::fs;
    let dsn = physical_pg_test_dsn();
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    let temp = tempfile::tempdir().unwrap();
    let mut input = payload("win-native-witness", "job-win-witness", "workspace-win", 2);
    let attempt = input.attempt_id.clone();
    let bundle = temp.path().join("pg-attempts").join(&attempt);
    fs::create_dir_all(&bundle).unwrap();
    input.bundle_path = bundle.to_string_lossy().into_owned();
    input.unit_name = format!("Ordivon.{attempt}");
    input.launch_token_digest = format!("sha256:{}", "a".repeat(64));
    input.workspace_snapshot_json = serde_json::json!({
        "executionProvider": {
            "contract":"windows_native_launcher_v1",
            "executableDigest":format!("sha256:{}", "c".repeat(64))
        }
    })
    .to_string();
    let request = b"immutable-Windows-Runner-request-v1";
    fs::write(bundle.join("request.json"), request).unwrap();
    let digest = format!("sha256:{}", hex::encode(Sha256::digest(request)));
    let mut owner = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    assert!(matches!(
        owner.admit(&input).unwrap(),
        PgAdmissionOutcome::Created(_)
    ));
    // A current PG reservation/allocation is required before BUNDLE_READY.
    // Reuse the exact same physical fixture contract as the Linux PG tests;
    // a Job row alone must never authorize a launch.
    allocate_fixture(&mut scratch, &input);
    // Absence of a PG-admitted bundle readiness receipt fails closed.
    assert!(inspect_admitted_windows_pg_bundle(
        &dsn,
        &scratch.name,
        &"a".repeat(64),
        &input.principal,
        &input.job_id,
        temp.path()
    )
    .is_err());
    let version: i64 = owner
        .client
        .query_one(
            "SELECT row_version FROM attempts WHERE attempt_id=$1",
            &[&attempt],
        )
        .unwrap()
        .get(0);
    owner
        .commit_bundle_ready_pg(&crate::pg_admission::PgBundleReady {
            attempt_id: attempt.clone(),
            expected_row_version: version,
            bundle_digest: digest.clone(),
            observed_at_ms: input.created_at_ms + 1,
            expected_source_sha256: "a".repeat(64),
        })
        .unwrap();
    let missing = inspect_admitted_windows_pg_bundle(
        &dsn,
        &scratch.name,
        &"a".repeat(64),
        &input.principal,
        &input.job_id,
        temp.path(),
    )
    .unwrap();
    assert_eq!(missing.phase, PgWindowsWitnessPhase::NoLauncherWitness);
    assert!(!missing.terminal_proven);
    // RED before guard: latest Attempt remained readable even when the
    // unresolved Job had no matching current_attempt_id.
    scratch
        .admin
        .execute(
            "UPDATE jobs SET current_attempt_id=NULL WHERE job_id=$1",
            &[&input.job_id],
        )
        .unwrap();
    assert!(inspect_admitted_windows_pg_bundle(
        &dsn,
        &scratch.name,
        &"a".repeat(64),
        &input.principal,
        &input.job_id,
        temp.path(),
    )
    .unwrap_err()
    .contains("current Attempt"));
    scratch
        .admin
        .execute(
            "UPDATE jobs SET current_attempt_id=$1 WHERE job_id=$2",
            &[&input.attempt_id, &input.job_id],
        )
        .unwrap();
    // Resolution also clears the current pointer; a contradictory
    // terminal+current pair must be rejected instead of borrowed.
    scratch
        .admin
        .execute(
            "UPDATE jobs SET resolution='succeeded' WHERE job_id=$1",
            &[&input.job_id],
        )
        .unwrap();
    assert!(inspect_admitted_windows_pg_bundle(
        &dsn,
        &scratch.name,
        &"a".repeat(64),
        &input.principal,
        &input.job_id,
        temp.path(),
    )
    .unwrap_err()
    .contains("resolved PG Job retains"));
    scratch
        .admin
        .execute(
            "UPDATE jobs SET resolution=NULL WHERE job_id=$1",
            &[&input.job_id],
        )
        .unwrap();
    assert!(inspect_admitted_windows_pg_bundle(
        &dsn,
        &scratch.name,
        &"a".repeat(64),
        "another-principal",
        &input.job_id,
        temp.path()
    )
    .is_err());
    fs::write(bundle.join("request.json"), b"tampered").unwrap();
    assert!(inspect_admitted_windows_pg_bundle(
        &dsn,
        &scratch.name,
        &"a".repeat(64),
        &input.principal,
        &input.job_id,
        temp.path()
    )
    .unwrap_err()
    .contains("request digest"));
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_rejects_synthetic_writer_without_event_sequence_uniqueness() {
    let dsn = physical_pg_test_dsn();
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    assert!(PgAdmissionStore::connect(&dsn, &scratch.name).is_ok());
    scratch
        .admin
        .batch_execute(
            "ALTER TABLE job_events DROP CONSTRAINT job_events_job_id_event_sequence_key",
        )
        .expect("test-only weakened catalog");
    assert!(matches!(
        PgAdmissionStore::connect(&dsn, &scratch.name),
        Err(PgAdmissionError::Unqualified)
    ));
    assert_eq!(scratch.count("jobs"), 0);
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_rejects_foreign_key_that_points_at_wrong_pg_target() {
    let dsn = physical_pg_test_dsn();
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    assert!(PgAdmissionStore::connect(&dsn, &scratch.name).is_ok());
    scratch
        .admin
        .batch_execute(
            "CREATE TABLE unrelated_jobs(job_id text PRIMARY KEY);
             ALTER TABLE attempts DROP CONSTRAINT attempts_job_id_fkey;
             ALTER TABLE attempts ADD CONSTRAINT attempts_job_id_fkey
               FOREIGN KEY(job_id) REFERENCES unrelated_jobs(job_id)",
        )
        .expect("test-only misdirected foreign key");
    assert!(matches!(
        PgAdmissionStore::connect(&dsn, &scratch.name),
        Err(PgAdmissionError::Unqualified)
    ));
    assert_eq!(scratch.count("jobs"), 0);
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_rejects_foreign_key_that_points_at_wrong_target_column() {
    let dsn = physical_pg_test_dsn();
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    assert!(PgAdmissionStore::connect(&dsn, &scratch.name).is_ok());
    scratch
        .admin
        .batch_execute(
            "ALTER TABLE jobs ADD CONSTRAINT fixture_unique_request UNIQUE(client_request_id);
         ALTER TABLE attempts DROP CONSTRAINT attempts_job_id_fkey;
         ALTER TABLE attempts ADD CONSTRAINT attempts_job_id_fkey
           FOREIGN KEY(job_id) REFERENCES jobs(client_request_id)",
        )
        .expect("test-only same-table wrong-column reference");
    assert!(
        matches!(
            PgAdmissionStore::connect(&dsn, &scratch.name),
            Err(PgAdmissionError::Unqualified)
        ),
        "writer qualification must reject a constraint to the same table but wrong identity column"
    );
    assert_eq!(scratch.count("jobs"), 0);
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_native_atomic_admission_replay_fence_and_rollback() {
    let dsn = physical_pg_test_dsn();
    let mut scratch = Scratch::new(&dsn);
    let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    let a = payload("request-A", "job-A", "workspace-A", 2);
    assert!(matches!(
        store.admit(&a),
        Err(PgAdmissionError::Unqualified)
    ));
    assert_eq!(scratch.count("jobs"), 0, "no write before PG qualification");
    scratch.qualify();
    for (name, raw) in [
        ("workspace", "null"),
        ("plan", "[]"),
        ("workspace", r#"{"revision":1,"revision":2}"#),
        ("plan", r#"{"plan":{"timeoutMs":1000,"timeoutMs":2000}}"#),
        ("workspace", r#"{"nested":[{"a":1,"a":2}]}"#),
    ] {
        let mut invalid = a.clone();
        if name == "workspace" {
            invalid.workspace_snapshot_json = raw.into();
        } else {
            invalid.execution_plan_json = raw.into();
        }
        assert!(matches!(
            store.admit(&invalid),
            Err(PgAdmissionError::InvalidInput)
        ));
        assert_eq!(scratch.count("jobs"), 0, "invalid JSON persisted a PG Job");
    }
    assert_eq!(
        store.admit(&a).unwrap(),
        PgAdmissionOutcome::Created("job-A".into())
    );
    assert_eq!(
        store.admit(&a).unwrap(),
        PgAdmissionOutcome::Existing("job-A".into())
    );
    assert_eq!(scratch.count("jobs"), 1);
    assert_eq!(scratch.count("attempts"), 1);
    assert_eq!(scratch.count("concurrency_reservations"), 1);
    assert_eq!(scratch.count("idempotency_keys"), 1);
    assert_eq!(scratch.count("job_events"), 3);
    // A release Effect attached to the same ordinary Job is conflicting
    // provenance, NOT an unrelated Effect or a valid ordinary replay.
    // Preserve exact operation identity instead of accepting corruption.
    scratch
            .admin
            .execute(
                "INSERT INTO job_runtime_release_effects(job_id,effect_id,contract,request_digest,workspace_id,commit_revision,candidate_manifest_digest,expected_tool_count,receipt_path,binding_digest) VALUES($1,'effect-fixture','release-v1','test-request','ws-fixture','revision-fixture','manifest-fixture',0,'effect-receipt','effect-binding')",
                &[&a.job_id],
            )
            .unwrap();
    assert!(matches!(
        store.admit(&a),
        Err(PgAdmissionError::IdempotencyConflict)
    ));
    let mut conflicting_during_effect = a.clone();
    conflicting_during_effect.request_digest = "sha256:other-request".into();
    assert!(matches!(
        store.admit(&conflicting_during_effect),
        Err(PgAdmissionError::IdempotencyConflict)
    ));
    assert!(matches!(
        store.admit(&payload(
            "new-during-effect",
            "job-forbidden",
            "other-ws",
            2
        )),
        Err(PgAdmissionError::PendingEffect)
    ));
    assert_eq!(scratch.count("jobs"), 1);
    assert_eq!(scratch.count("job_events"), 3);
    scratch
        .admin
        .execute(
            "DELETE FROM job_runtime_release_effects WHERE job_id=$1",
            &[&a.job_id],
        )
        .unwrap();
    let mut conflict = a.clone();
    conflict.request_digest = "sha256:different-request".into();
    assert!(matches!(
        store.admit(&conflict),
        Err(PgAdmissionError::IdempotencyConflict)
    ));
    assert!(matches!(
        store.admit(&payload("request-B", "job-B", "workspace-A", 2)),
        Ok(PgAdmissionOutcome::Created(_))
    ));
    assert!(matches!(
        store.admit(&payload(
            "request-B-global",
            "job-B-global",
            "workspace-B",
            1
        )),
        Ok(PgAdmissionOutcome::Created(_))
    ));
    assert_eq!(
        scratch.count("job_allocations"),
        0,
        "pending Jobs consumed physical resources"
    );

    // A row uniqueness error after inserting Job must rollback every
    // consumer-visible part of this admission.
    let mut duplicate_attempt = payload("request-C", "job-C", "workspace-B", 2);
    duplicate_attempt.attempt_id = a.attempt_id.clone();
    assert!(matches!(
        store.admit(&duplicate_attempt),
        Err(PgAdmissionError::Database(_))
    ));
    assert_eq!(scratch.count("jobs"), 3);
    assert_eq!(scratch.count("attempts"), 3);
    assert_eq!(scratch.count("idempotency_keys"), 3);
    assert_eq!(scratch.count("job_events"), 9);
    assert_eq!(
        store
            .admit(&payload("request-D", "job-D", "workspace-B", 2))
            .unwrap(),
        PgAdmissionOutcome::Created("job-D".into())
    );
    assert_eq!(scratch.count("jobs"), 4);
    assert_eq!(scratch.count("job_events"), 12);
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_STAGE_TEST_DSN historical-stage qualification"]
fn historical_pg_stage_is_not_an_admission_authority() {
    let dsn = historical_pg_stage_test_dsn();
    let mut inspector = Client::connect(&dsn, NoTls).unwrap();
    let before: i64 = inspector
        .query_one("SELECT count(*) FROM rw12_stage_cutover_r1.jobs", &[])
        .unwrap()
        .get(0);
    let row=inspector.query_one(
            "SELECT state,source_sha256,promotion_allowed FROM rw12_stage_cutover_r1._stage_control WHERE id='source'",
            &[]).unwrap();
    let state: String = row.get(0);
    let source: String = row.get(1);
    let permitted: bool = row.get(2);
    assert_eq!(state, "VERIFIED_NON_AUTHORITY");
    assert!(!permitted);
    assert_eq!(source.len(), 64, "staged source identity exists");
    // A historical row-exact import is not a durable writer schema:
    // fail at connect before any operation can even be admitted.
    assert!(matches!(
        PgAdmissionStore::connect(&dsn, "rw12_stage_cutover_r1"),
        Err(PgAdmissionError::Unqualified)
    ));
    let after: i64 = inspector
        .query_one("SELECT count(*) FROM rw12_stage_cutover_r1.jobs", &[])
        .unwrap()
        .get(0);
    assert_eq!(before, after);
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_admission_readback_is_exact_and_never_claims_absence() {
    let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
        .expect("explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification required");
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    let a = payload("ack-lost", "job-ack-lost", "ws-ack-lost", 2);
    let mut observer = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    assert_eq!(
        observer.observe_admission(&a).unwrap(),
        PgAdmissionObservation::Inconclusive,
        "absence must not prove that the original COMMIT did not happen"
    );

    let mut writer = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    assert_eq!(
        writer.admit(&a).unwrap(),
        PgAdmissionOutcome::Created(a.job_id.clone())
    );
    // Treat writer COMMIT acknowledgement as lost. Read back on an
    // independent qualified connection without issuing a second write.
    assert_eq!(
        observer.observe_admission(&a).unwrap(),
        PgAdmissionObservation::Confirmed(a.job_id.clone())
    );
    assert_eq!(scratch.count("jobs"), 1);
    assert_eq!(scratch.count("attempts"), 1);
    assert_eq!(scratch.count("job_events"), 3);

    let mut conflicting = a.clone();
    conflicting.request_digest = "sha256:altered-request".into();
    assert_eq!(
        observer.observe_admission(&conflicting).unwrap(),
        PgAdmissionObservation::Inconclusive
    );
    conflicting = a.clone();
    conflicting.operation_digest = "sha256:altered-operation".into();
    assert_eq!(
        observer.observe_admission(&conflicting).unwrap(),
        PgAdmissionObservation::Inconclusive
    );
    conflicting = a.clone();
    conflicting.attempt_id = "attempt-unrelated".into();
    assert_eq!(
        observer.observe_admission(&conflicting).unwrap(),
        PgAdmissionObservation::Inconclusive
    );

    // A missing capacity reservation is independently disqualifying,
    // even while the complete original event sequence remains intact.
    scratch
        .admin
        .execute(
            "DELETE FROM concurrency_reservations WHERE attempt_id=$1",
            &[&a.attempt_id],
        )
        .unwrap();
    assert_eq!(
        observer.observe_admission(&a).unwrap(),
        PgAdmissionObservation::Inconclusive
    );
    scratch.admin.execute(
            "INSERT INTO concurrency_reservations(reservation_id,attempt_id,global_limit,state,acquired_at_ms,state_observed_at_ms) VALUES($1,$2,$3,'active',$4,$4)",
            &[&a.reservation_id,&a.attempt_id,&i64::from(a.global_limit),&a.created_at_ms],
        ).unwrap();
    assert_eq!(
        observer.observe_admission(&a).unwrap(),
        PgAdmissionObservation::Confirmed(a.job_id.clone()),
        "restoring the original reservation must restore the complete witness"
    );

    // Conversely, the key/Job/Attempt/reservation rows are not sufficient
    // without all original admission events.
    scratch
        .admin
        .execute(
            "DELETE FROM job_events WHERE job_id=$1 AND event_sequence=2",
            &[&a.job_id],
        )
        .unwrap();
    assert_eq!(
        observer.observe_admission(&a).unwrap(),
        PgAdmissionObservation::Inconclusive
    );
    assert_eq!(scratch.count("jobs"), 1);
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_clean_epoch_needs_no_old_sqlite_requests() {
    let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
        .expect("explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification required");
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    let mut pg = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    // This was an old SQLite request ID, but the owner explicitly
    // retired all old history. In a NEW PG epoch it is simply a new key.
    let request = payload("formerly-old-key", "new-pg-job", "new-workspace", 2);
    assert_eq!(
        pg.admit(&request).unwrap(),
        PgAdmissionOutcome::Created(request.job_id.clone())
    );
    assert_eq!(
        pg.admit(&request).unwrap(),
        PgAdmissionOutcome::Existing(request.job_id.clone())
    );
    let mut changed = request.clone();
    // A changed resolved physical Operation cannot redefine an existing
    // request key: the original replay is valid even after source drift.
    changed.operation_digest = "sha256:different-current-epoch-operation".into();
    assert_eq!(
        pg.admit(&changed).unwrap(),
        PgAdmissionOutcome::Existing(request.job_id.clone())
    );
    changed.request_digest = "sha256:different-current-epoch-request".into();
    assert!(matches!(
        pg.admit(&changed),
        Err(PgAdmissionError::IdempotencyConflict)
    ));
    assert_eq!(scratch.count("jobs"), 1);
    assert_eq!(scratch.count("attempts"), 1);
    assert_eq!(scratch.count("concurrency_reservations"), 1);
    assert_eq!(scratch.count("job_events"), 3);
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_concurrent_duplicate_never_creates_second_job() {
    let dsn = physical_pg_test_dsn();
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    let gate = Arc::new(Barrier::new(5));
    let mut workers = Vec::new();
    for n in 0..4 {
        let dsn = dsn.clone();
        let schema = scratch.name.clone();
        let gate = gate.clone();
        workers.push(thread::spawn(move || {
            let mut store = PgAdmissionStore::connect(&dsn, &schema).unwrap();
            let request = payload("same-key", &format!("job-{n}"), "workspace-one", 2);
            gate.wait();
            store.admit(&request)
        }));
    }
    gate.wait();
    let mut created = 0usize;
    for worker in workers {
        match worker.join().unwrap() {
            Ok(PgAdmissionOutcome::Created(_)) => created += 1,
            Ok(PgAdmissionOutcome::Existing(_)) => (),
            Err(PgAdmissionError::Database(error))
                if error.code() == Some(&postgres::error::SqlState::T_R_SERIALIZATION_FAILURE) => {}
            unexpected => panic!("unsafe concurrent admission result: {unexpected:?}"),
        }
    }
    assert_eq!(created, 1);
    assert_eq!(scratch.count("jobs"), 1);
    assert_eq!(scratch.count("idempotency_keys"), 1);
    assert_eq!(scratch.count("attempts"), 1);
    assert_eq!(scratch.count("concurrency_reservations"), 1);
}

// The operator-owned marker is a new-Job gate, not a writer-epoch change.
// Already admitted work and exact historical replay must remain operable.
#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_maintenance_marker_blocks_new_job_not_replay_or_terminal() {
    let dsn = physical_pg_test_dsn();
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    let first = payload(
        "maintenance-first",
        "job-maintenance-first",
        "maintenance-ws",
        2,
    );
    let second = payload(
        "maintenance-second",
        "job-maintenance-second",
        "maintenance-ws",
        2,
    );
    assert_eq!(
        store.admit(&first).unwrap(),
        PgAdmissionOutcome::Created(first.job_id.clone())
    );
    let mut operator = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    operator
        .close_new_job_admission_for_maintenance(&"a".repeat(64), &"b".repeat(64))
        .unwrap();
    assert_eq!(
        store.admit(&first).unwrap(),
        PgAdmissionOutcome::Existing(first.job_id.clone())
    );
    assert!(
        matches!(
            store.admit(&second),
            Err(PgAdmissionError::MaintenanceClosed)
        ),
        "new admission crossed durable maintenance closure"
    );
    assert_eq!(scratch.count("jobs"), 1);
    assert_eq!(scratch.count("attempts"), 1);
    assert_eq!(scratch.count("concurrency_reservations"), 1);
    let terminal = PgTerminalNoArtifacts {
        attempt_id: first.attempt_id.clone(),
        expected_row_version: 0,
        terminal_state: "failed".into(),
        result_digest: "sha256:maintenance-terminal".into(),
        reason_code: "NATIVE_PG_TEST".into(),
        exit_code: Some(3),
        finished_at_ms: first.created_at_ms + 1,
        expected_source_sha256: first.expected_source_sha256.clone(),
    };
    assert_eq!(
        store.commit_terminal_no_artifacts(&terminal).unwrap(),
        PgTerminalOutcome::Committed(first.job_id.clone())
    );
    assert_eq!(
        store.admit(&first).unwrap(),
        PgAdmissionOutcome::Existing(first.job_id.clone())
    );
    assert!(store.admit(&second).is_err());
    // A malformed or foreign marker is not a grant to reopen.
    scratch.admin.execute("UPDATE _stage_control SET state='UNKNOWN',promotion_allowed=true WHERE id='maintenance'", &[]).unwrap();
    assert!(store.admit(&second).is_err());
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_maintenance_close_fences_stale_snapshots_and_exact_subject() {
    let dsn = physical_pg_test_dsn();
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    let mut writer = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    let mut operator = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    let mut stale = writer
        .client
        .build_transaction()
        .isolation_level(IsolationLevel::Serializable)
        .start()
        .unwrap();
    // Snapshot precedes close; this is the real source-lock predicate in admit_once.
    let initial = stale
        .query_one(
            "SELECT state FROM _stage_control WHERE id='maintenance'",
            &[],
        )
        .unwrap()
        .get::<_, String>(0);
    assert_eq!(initial, "ADMISSION_OPEN");
    assert!(matches!(
        operator.close_new_job_admission_for_maintenance(&"c".repeat(64), &"b".repeat(64)),
        Err(PgAdmissionError::Unqualified)
    ));
    operator
        .close_new_job_admission_for_maintenance(&"a".repeat(64), &"b".repeat(64))
        .unwrap();
    stale
        .query_one("SELECT pg_advisory_xact_lock($1)", &[&79245017_i64])
        .unwrap();
    // Source qualification still succeeds, but the permanent row changed.
    stale
        .query_one(
            "SELECT state FROM _stage_control WHERE id='source' FOR UPDATE",
            &[],
        )
        .unwrap();
    let err = stale
        .query_one(
            "SELECT state FROM _stage_control WHERE id='maintenance' FOR SHARE",
            &[],
        )
        .unwrap_err();
    assert_eq!(
        err.code(),
        Some(&postgres::error::SqlState::T_R_SERIALIZATION_FAILURE)
    );
    stale.rollback().unwrap();
    assert!(matches!(
        writer.admit(&payload("late", "job-late", "ws", 2)),
        Err(PgAdmissionError::MaintenanceClosed)
    ));
    assert_eq!(scratch.count("jobs"), 0);
    operator
        .close_new_job_admission_for_maintenance(&"a".repeat(64), &"b".repeat(64))
        .unwrap();
    assert!(matches!(
        operator.close_new_job_admission_for_maintenance(&"a".repeat(64), &"c".repeat(64)),
        Err(PgAdmissionError::IdempotencyConflict)
    ));
    let marker = scratch.admin.query_one("SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='maintenance'", &[]).unwrap();
    assert_eq!(
        (
            marker.get::<_, String>(0),
            marker.get::<_, String>(1),
            marker.get::<_, bool>(2)
        ),
        ("ADMISSION_CLOSED".into(), "b".repeat(64), false)
    );
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_maintenance_missing_or_malformed_gate_never_bootstraps_open() {
    let dsn = physical_pg_test_dsn();
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    let job = payload("new-gate", "job-new-gate", "ws", 1);
    scratch
        .admin
        .execute("DELETE FROM _stage_control WHERE id='maintenance'", &[])
        .unwrap();
    assert!(matches!(
        store.admit(&job),
        Err(PgAdmissionError::MaintenanceClosed)
    ));
    assert!(matches!(
        store.close_new_job_admission_for_maintenance(&"a".repeat(64), &"b".repeat(64)),
        Err(PgAdmissionError::Unqualified)
    ));
    for (state, digest, flag) in [
        ("ADMISSION_OPEN", "b".repeat(64), true),
        ("ADMISSION_OPEN", "0".repeat(64), false),
        ("UNKNOWN", "0".repeat(64), true),
        ("ADMISSION_CLOSED", "b".repeat(64), false),
    ] {
        scratch.admin.execute("INSERT INTO _stage_control VALUES('maintenance',$1,$2,$3) ON CONFLICT(id) DO UPDATE SET state=EXCLUDED.state,source_sha256=EXCLUDED.source_sha256,promotion_allowed=EXCLUDED.promotion_allowed", &[&state,&digest,&flag]).unwrap();
        assert!(matches!(
            store.admit(&job),
            Err(PgAdmissionError::MaintenanceClosed)
        ));
        assert_eq!(scratch.count("jobs"), 0);
    }
    // Test-only owner initialization is explicit; the library never does this.
    scratch.admin.execute("UPDATE _stage_control SET state='ADMISSION_OPEN',source_sha256=repeat('0',64),promotion_allowed=true WHERE id='maintenance'", &[]).unwrap();
    assert!(matches!(
        store.admit(&job),
        Ok(PgAdmissionOutcome::Created(_))
    ));
    store
        .close_new_job_admission_for_maintenance(&"a".repeat(64), &"b".repeat(64))
        .unwrap();
    let cancel = PgCancelIntent {
        job_id: job.job_id.clone(),
        observed_at_ms: job.created_at_ms + 1,
        expected_source_sha256: job.expected_source_sha256.clone(),
    };
    store.request_cancel_intent(&cancel).unwrap();
    assert_eq!(
        store.observe_cancel_intent(&cancel).unwrap(),
        PgCancelObservation::Confirmed(job.job_id.clone())
    );
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_maintenance_operator_requires_protected_column_privileges() {
    let dsn = physical_pg_test_dsn();
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    let role = format!("test_maintenance_{}", Uuid::now_v7().simple());
    scratch
        .admin
        .batch_execute(&format!(
            "CREATE ROLE \"{role}\" NOLOGIN;
         GRANT USAGE ON SCHEMA \"{schema}\" TO \"{role}\";
         GRANT ALL ON ALL TABLES IN SCHEMA \"{schema}\" TO \"{role}\";
         REVOKE ALL ON \"{schema}\"._stage_control FROM \"{role}\";
         GRANT SELECT,UPDATE(id) ON \"{schema}\"._stage_control TO \"{role}\";
         GRANT EXECUTE ON FUNCTION pg_control_system(),pg_control_checkpoint() TO \"{role}\";",
            schema = scratch.name
        ))
        .unwrap();
    let mut app = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    app.client
        .batch_execute(&format!("SET ROLE \"{role}\""))
        .unwrap();
    let first = payload("role-first", "job-role-first", "ws", 2);
    assert!(matches!(
        app.admit(&first),
        Ok(PgAdmissionOutcome::Created(_))
    ));
    let denied = app
        .close_new_job_admission_for_maintenance(&"a".repeat(64), &"b".repeat(64))
        .unwrap_err();
    assert!(
        matches!(denied,PgAdmissionError::Database(ref e) if e.code()==Some(&postgres::error::SqlState::INSUFFICIENT_PRIVILEGE))
    );
    assert_eq!(
        scratch
            .admin
            .query_one(
                "SELECT state FROM _stage_control WHERE id='maintenance'",
                &[]
            )
            .unwrap()
            .get::<_, String>(0),
        "ADMISSION_OPEN"
    );
    let mut operator = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    operator
        .close_new_job_admission_for_maintenance(&"a".repeat(64), &"b".repeat(64))
        .unwrap();
    assert_eq!(
        app.admit(&first).unwrap(),
        PgAdmissionOutcome::Existing(first.job_id.clone())
    );
    assert!(matches!(
        app.admit(&payload("role-second", "job-role-second", "ws", 2)),
        Err(PgAdmissionError::MaintenanceClosed)
    ));
    // The existing application UPDATE(id) privilege can rename the marker,
    // but missing mandatory identity still cannot grant a new Job.
    app.client
        .execute(
            "UPDATE _stage_control SET id='damaged-maintenance' WHERE id='maintenance'",
            &[],
        )
        .unwrap();
    assert!(matches!(
        app.admit(&payload("role-third", "job-role-third", "ws", 2)),
        Err(PgAdmissionError::MaintenanceClosed)
    ));
    app.client.batch_execute("RESET ROLE").unwrap();
    drop(app);
    scratch
        .admin
        .batch_execute(&format!("DROP OWNED BY \"{role}\"; DROP ROLE \"{role}\";"))
        .unwrap();
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_maintenance_closure_readback_is_exact_and_never_grants_effect() {
    let dsn = physical_pg_test_dsn();
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    let mut operator = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    let mut observer = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    let source = "a".repeat(64);
    let subject = "b".repeat(64);
    assert_eq!(
        observer
            .observe_maintenance_closure(&source, &subject)
            .unwrap(),
        PgMaintenanceClosureObservation::Inconclusive
    );
    operator
        .close_new_job_admission_for_maintenance(&source, &subject)
        .unwrap();
    // A different connection reconciles an assumed lost write acknowledgement.
    assert_eq!(
        observer
            .observe_maintenance_closure(&source, &subject)
            .unwrap(),
        PgMaintenanceClosureObservation::ConfirmedClosed
    );
    assert_eq!(
        observer
            .observe_maintenance_closure(&source, &"c".repeat(64))
            .unwrap(),
        PgMaintenanceClosureObservation::Inconclusive
    );
    assert!(matches!(
        observer.observe_maintenance_closure(&"c".repeat(64), &subject),
        Err(PgAdmissionError::Unqualified)
    ));
    scratch
        .admin
        .execute(
            "UPDATE _stage_control SET promotion_allowed=true WHERE id='maintenance'",
            &[],
        )
        .unwrap();
    assert_eq!(
        observer
            .observe_maintenance_closure(&source, &subject)
            .unwrap(),
        PgMaintenanceClosureObservation::Inconclusive
    );
    scratch
        .admin
        .execute("DELETE FROM _stage_control WHERE id='maintenance'", &[])
        .unwrap();
    assert_eq!(
        observer
            .observe_maintenance_closure(&source, &subject)
            .unwrap(),
        PgMaintenanceClosureObservation::Inconclusive
    );
    assert_eq!(scratch.count("jobs"), 0);
}
