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

/// Physical SQL qualification of the SAME existing Job event writer.
/// This does not simulate a kernel witness or install a Windows PG binary:
/// caller-side native Win32 qualification is independently required.
#[test]
#[ignore = "requires explicit disposable ORDIVON_PG_TEST_DSN PostgreSQL instance"]
fn windows_native_drain_event_is_current_attempt_fenced_and_never_terminal_on_its_own() {
    use crate::pg_admission::{PgNativeWindowsDrainInput, PgNativeWindowsDrainOutcome};
    let dsn = physical_pg_test_dsn();
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    let mut input = payload(
        "win-native-drain-r1",
        "job-win-native-drain-r1",
        "workspace-win-native-drain-r1",
        2,
    );
    input.launch_token_digest = format!("sha256:{}", "b".repeat(64));
    let request_digest = format!("sha256:{}", "c".repeat(64));
    let mut owner = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    assert!(matches!(
        owner.admit(&input).unwrap(),
        PgAdmissionOutcome::Created(_)
    ));
    allocate_fixture(&mut scratch, &input);
    // Only test fixture moves the record to a native issued state.
    // The real caller must pass through immutable bundle + issue fences.
    owner.client.execute(
        "UPDATE attempts SET state='starting',bundle_digest=$1,row_version=row_version+1              WHERE attempt_id=$2",
        &[&request_digest, &input.attempt_id],
    ).unwrap();
    let row_version: i64 = owner
        .client
        .query_one(
            "SELECT row_version FROM attempts WHERE attempt_id=$1",
            &[&input.attempt_id],
        )
        .unwrap()
        .get(0);
    let native = PgNativeWindowsDrainInput {
        job_id: input.job_id.clone(),
        attempt_id: input.attempt_id.clone(),
        expected_row_version: row_version,
        expected_source_sha256: "a".repeat(64),
        launch_token_digest: input.launch_token_digest.clone(),
        request_digest: request_digest.clone(),
        result_digest: format!("sha256:{}", "d".repeat(64)),
        launcher_process_id: 1244,
        launcher_creation_file_time: 8192000,
        observed_at_ms: input.created_at_ms + 9,
    };
    assert!(!owner.qualified_native_windows_drain(&native).unwrap());
    let mut stale = native.clone();
    stale.expected_row_version += 1;
    assert!(matches!(
        owner.record_native_windows_drain(&stale),
        Err(PgAdmissionError::Blocked)
    ));
    let mut wrong_source = native.clone();
    wrong_source.expected_source_sha256 = "0".repeat(64);
    assert!(matches!(
        owner.record_native_windows_drain(&wrong_source),
        Err(PgAdmissionError::Unqualified)
    ));
    assert_eq!(
        owner.record_native_windows_drain(&native).unwrap(),
        PgNativeWindowsDrainOutcome::Committed(input.job_id.clone()),
    );
    assert_eq!(
        owner.record_native_windows_drain(&native).unwrap(),
        PgNativeWindowsDrainOutcome::Existing(input.job_id.clone()),
    );
    assert!(owner.qualified_native_windows_drain(&native).unwrap());
    // Simulate a new Runtime connection after loss of the original ACK:
    // journal durability, NOT the original in-memory observation time,
    // is the recovery truth. Reconciliation can continue after restart.
    let mut reopened = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    let mut after_restart = native.clone();
    after_restart.observed_at_ms += 1000;
    assert!(reopened
        .qualified_native_windows_drain(&after_restart)
        .unwrap());
    let mut incorrect = native.clone();
    incorrect.launcher_process_id += 1;
    assert!(!owner.qualified_native_windows_drain(&incorrect).unwrap());
    assert!(matches!(
        owner.record_native_windows_drain(&incorrect),
        Err(PgAdmissionError::IdempotencyConflict)
    ));
    assert_eq!(scratch.count("artifacts"), 0);
    assert_eq!(scratch.count("job_events"), 4); // 3 admission + 1 native
    let attempt: String = owner
        .client
        .query_one(
            "SELECT state FROM attempts WHERE attempt_id=$1",
            &[&input.attempt_id],
        )
        .unwrap()
        .get(0);
    assert_eq!(attempt, "starting");
    let resolution: Option<String> = owner
        .client
        .query_one(
            "SELECT resolution FROM jobs WHERE job_id=$1",
            &[&input.job_id],
        )
        .unwrap()
        .get(0);
    assert_eq!(resolution, None);
    let reserved: String = owner
        .client
        .query_one(
            "SELECT state FROM concurrency_reservations WHERE attempt_id=$1",
            &[&input.attempt_id],
        )
        .unwrap()
        .get(0);
    assert_eq!(reserved, "active");
    scratch
        .admin
        .execute(
            "UPDATE jobs SET current_attempt_id=NULL WHERE job_id=$1",
            &[&input.job_id],
        )
        .unwrap();
    assert!(!owner.qualified_native_windows_drain(&native).unwrap());
    // Even if a malicious/buggy database writer edits a journal event,
    // a digest mismatch must no longer qualify native terminal evidence.
    scratch.admin.execute(
        "UPDATE job_events SET detail_json='{}' WHERE job_id=$1 AND event_type='WINDOWS_NATIVE_JOB_DRAIN_OBSERVED'",
        &[&input.job_id],
    ).unwrap();
    assert!(!reopened
        .qualified_native_windows_drain(&after_restart)
        .unwrap());
}
