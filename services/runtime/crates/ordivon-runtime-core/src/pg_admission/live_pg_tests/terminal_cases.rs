//! terminal cases: native PG18 behavior tests.
use super::*;

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_rejects_shallow_release_and_artifact_owner_constraints() {
    let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
        .expect("explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification required");
    let mut release = Scratch::new(&dsn);
    release.qualify();
    assert!(PgAdmissionStore::connect(&dsn, &release.name).is_ok());
    release.admin.batch_execute(
            "ALTER TABLE job_runtime_release_effects DROP CONSTRAINT job_runtime_release_effects_effect_id_key"
        ).expect("test-only weakened release uniqueness");
    assert!(matches!(
        PgAdmissionStore::connect(&dsn, &release.name),
        Err(PgAdmissionError::Unqualified)
    ));

    let mut artifact = Scratch::new(&dsn);
    artifact.qualify();
    assert!(PgAdmissionStore::connect(&dsn, &artifact.name).is_ok());
    artifact
        .admin
        .batch_execute(
            "ALTER TABLE artifacts DROP CONSTRAINT artifacts_attempt_id_kind_relative_path_key",
        )
        .expect("test-only weakened artifact uniqueness");
    assert!(matches!(
        PgAdmissionStore::connect(&dsn, &artifact.name),
        Err(PgAdmissionError::Unqualified)
    ));
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_terminal_cas_replay_orphan_hold_and_atomic_rollback() {
    let dsn = physical_pg_test_dsn();
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    let input = payload("terminal-one", "job-terminal", "workspace-term", 2);
    store.admit(&input).unwrap();
    let terminal = PgTerminalNoArtifacts {
        attempt_id: input.attempt_id.clone(),
        expected_row_version: 0,
        terminal_state: "failed".into(),
        result_digest: "sha256:result".into(),
        reason_code: "NATIVE_PG_TEST".into(),
        exit_code: Some(3),
        finished_at_ms: 1234578,
        expected_source_sha256: input.expected_source_sha256.clone(),
    };
    let mut stale = terminal.clone();
    stale.expected_row_version = 1;
    assert!(matches!(
        store.commit_terminal_no_artifacts(&stale),
        Err(PgAdmissionError::Blocked)
    ));
    assert_eq!(scratch.count("job_events"), 3);
    assert_eq!(
        store.commit_terminal_no_artifacts(&terminal).unwrap(),
        PgTerminalOutcome::Committed(input.job_id.clone())
    );
    assert_eq!(
        store.commit_terminal_no_artifacts(&terminal).unwrap(),
        PgTerminalOutcome::Existing(input.job_id.clone())
    );
    assert_eq!(scratch.count("job_events"), 5);
    let state: String = scratch
        .admin
        .query_one(
            "SELECT state FROM concurrency_reservations WHERE attempt_id=$1",
            &[&input.attempt_id],
        )
        .unwrap()
        .get(0);
    assert_eq!(state, "released");
    let mut conflicting = terminal.clone();
    conflicting.result_digest = "sha256:other".into();
    assert!(matches!(
        store.commit_terminal_no_artifacts(&conflicting),
        Err(PgAdmissionError::IdempotencyConflict)
    ));
    assert_eq!(scratch.count("job_events"), 5);

    let orphan = payload("orphan", "job-orphan", "workspace-term", 2);
    store.admit(&orphan).unwrap();
    let hold = PgTerminalNoArtifacts {
        attempt_id: orphan.attempt_id.clone(),
        expected_row_version: 0,
        terminal_state: "orphaned".into(),
        result_digest: "sha256:orphan".into(),
        reason_code: "ORPHAN".into(),
        exit_code: None,
        finished_at_ms: 1234580,
        expected_source_sha256: input.expected_source_sha256.clone(),
    };
    store.commit_terminal_no_artifacts(&hold).unwrap();
    let held: String = scratch
        .admin
        .query_one(
            "SELECT state FROM concurrency_reservations WHERE attempt_id=$1",
            &[&orphan.attempt_id],
        )
        .unwrap()
        .get(0);
    assert_eq!(held, "held_orphaned");
    assert!(matches!(
        store.admit(&payload("after-orphan", "job-after", "workspace-term", 2)),
        Ok(PgAdmissionOutcome::Created(_))
    ));
    assert_eq!(scratch.count("jobs"), 3);
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_stale_attempt_cannot_terminalize_current_job() {
    let dsn = physical_pg_test_dsn();
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    let input = payload("stale-terminal", "job-stale-terminal", "workspace-stale", 2);
    store.admit(&input).unwrap();
    scratch.admin.execute(
            "INSERT INTO attempts(attempt_id,job_id,attempt_number,state,termination_intent,launch_token_digest,bundle_path,unit_name,created_at_ms,row_version) VALUES($1,$2,2,'accepted','natural','launch-new','/nonproduction/new','newer.service',$3,0)",
            &[&"attempt-newer", &input.job_id, &input.created_at_ms],
        ).unwrap();
    scratch
        .admin
        .execute(
            "UPDATE jobs SET current_attempt_id='attempt-newer' WHERE job_id=$1",
            &[&input.job_id],
        )
        .unwrap();

    let old_attempt = PgTerminalNoArtifacts {
        attempt_id: input.attempt_id.clone(),
        expected_row_version: 0,
        terminal_state: "failed".into(),
        result_digest: "sha256:stale".into(),
        reason_code: "STALE_ATTEMPT".into(),
        exit_code: Some(5),
        finished_at_ms: input.created_at_ms + 1,
        expected_source_sha256: input.expected_source_sha256.clone(),
    };
    assert!(matches!(
        store.commit_terminal_no_artifacts(&old_attempt),
        Err(PgAdmissionError::Blocked)
    ));
    assert_eq!(scratch.count("job_events"), 3, "no stale terminal event");
    let state: String = scratch
        .admin
        .query_one(
            "SELECT state FROM attempts WHERE attempt_id=$1",
            &[&input.attempt_id],
        )
        .unwrap()
        .get(0);
    assert_eq!(state, "accepted", "old Attempt must remain unchanged");
    let job = scratch
        .admin
        .query_one(
            "SELECT resolution,current_attempt_id FROM jobs WHERE job_id=$1",
            &[&input.job_id],
        )
        .unwrap();
    let resolution: Option<String> = job.get(0);
    let current: Option<String> = job.get(1);
    assert_eq!((resolution, current), (None, Some("attempt-newer".into())));
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_artifact_bearing_terminal_is_denied_until_full_owner_exists() {
    let dsn = physical_pg_test_dsn();
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    let input = payload("has-artifact", "job-artifact", "workspace-artifact", 1);
    store.admit(&input).unwrap();
    scratch
        .admin
        .execute(
            "INSERT INTO artifacts(artifact_id,job_id,attempt_id) VALUES('artifact-test',$1,$2)",
            &[&input.job_id, &input.attempt_id],
        )
        .unwrap();
    let terminal = PgTerminalNoArtifacts {
        attempt_id: input.attempt_id.clone(),
        expected_row_version: 0,
        terminal_state: "failed".into(),
        result_digest: "sha256:result".into(),
        reason_code: "ARTIFACT_STOP".into(),
        exit_code: Some(1),
        finished_at_ms: 1234599,
        expected_source_sha256: input.expected_source_sha256.clone(),
    };
    assert!(matches!(
        store.commit_terminal_no_artifacts(&terminal),
        Err(PgAdmissionError::Blocked)
    ));
    let standing: String = scratch
        .admin
        .query_one(
            "SELECT state FROM attempts WHERE attempt_id=$1",
            &[&input.attempt_id],
        )
        .unwrap()
        .get(0);
    assert_eq!(standing, "accepted");
    assert_eq!(scratch.count("job_events"), 3);
    assert_eq!(scratch.count("concurrency_reservations"), 1);
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_readonly_job_projection_fences_stage_and_incoherent_terminal() {
    use crate::PgJobReadback;
    let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
        .expect("explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification required");
    let mut scratch = Scratch::new(&dsn);
    let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    let input = payload("readback-req", "readback-job", "readback-workspace", 2);
    assert!(matches!(
        store.observe_job_readonly(&input.job_id, &input.expected_source_sha256),
        Err(PgAdmissionError::Unqualified)
    ));
    scratch.qualify();
    assert_eq!(
        store
            .observe_job_readonly(&input.job_id, &input.expected_source_sha256)
            .unwrap(),
        PgJobReadback::Inconclusive,
    );
    store.admit(&input).unwrap();
    let events_before = scratch.count("job_events");
    let first = store
        .observe_job_readonly(&input.job_id, &input.expected_source_sha256)
        .unwrap();
    let PgJobReadback::Observed(first) = first else {
        panic!("admitted PG job must be read coherently");
    };
    assert_eq!(first.attempt_id, input.attempt_id);
    assert_eq!(first.attempt_state, "accepted");
    assert_eq!(first.resolution, None);
    assert_eq!(first.reservation_state, "active");
    assert_eq!(first.started_at_ms, None);
    // Source is still QUALIFIED_WRITER, but its physical epoch is no
    // longer operator-qualified. A restored/historical Job must not be
    // advertised through this API as current authoritative state.
    scratch
        .admin
        .execute(
            "UPDATE _stage_control SET promotion_allowed=false WHERE id='epoch'",
            &[],
        )
        .unwrap();
    assert!(matches!(
        store.observe_job_readonly(&input.job_id, &input.expected_source_sha256),
        Err(PgAdmissionError::Unqualified)
    ));
    scratch
        .admin
        .execute(
            "UPDATE _stage_control SET promotion_allowed=true WHERE id='epoch'",
            &[],
        )
        .unwrap();
    let true_epoch: String = scratch
        .admin
        .query_one(
            "SELECT source_sha256 FROM _stage_control WHERE id='epoch'",
            &[],
        )
        .unwrap()
        .get(0);
    scratch
        .admin
        .execute(
            "UPDATE _stage_control SET source_sha256=$1 WHERE id='epoch'",
            &[&"f".repeat(64)],
        )
        .unwrap();
    assert!(matches!(
        store.observe_job_readonly(&input.job_id, &input.expected_source_sha256),
        Err(PgAdmissionError::Unqualified)
    ));
    scratch
        .admin
        .execute(
            "UPDATE _stage_control SET source_sha256=$1 WHERE id='epoch'",
            &[&true_epoch],
        )
        .unwrap();
    assert!(matches!(
        store.observe_job_readonly(&input.job_id, &input.expected_source_sha256),
        Ok(PgJobReadback::Observed(_))
    ));
    assert_eq!(
        scratch.count("job_events"),
        events_before,
        "readback must not append effects"
    );
    assert!(matches!(
        store.observe_job_readonly(&input.job_id, &"f".repeat(64)),
        Err(PgAdmissionError::Unqualified)
    ));
    let cancel = PgCancelIntent {
        job_id: input.job_id.clone(),
        observed_at_ms: 1234570,
        expected_source_sha256: input.expected_source_sha256.clone(),
    };
    store.request_cancel_intent(&cancel).unwrap();
    let cancelling = store
        .observe_job_readonly(&input.job_id, &input.expected_source_sha256)
        .unwrap();
    let PgJobReadback::Observed(cancelling) = cancelling else {
        panic!("cancel intent must not erase the active Attempt");
    };
    assert_eq!(cancelling.desired_state, "cancelled");
    assert_eq!(cancelling.resolution, None);
    assert_eq!(cancelling.reservation_state, "active");
    store
        .commit_terminal_no_artifacts(&PgTerminalNoArtifacts {
            attempt_id: input.attempt_id.clone(),
            expected_row_version: 1,
            terminal_state: "cancelled".into(),
            result_digest: "sha256:terminal".into(),
            reason_code: "READBACK_TEST".into(),
            exit_code: None,
            finished_at_ms: 1234571,
            expected_source_sha256: input.expected_source_sha256.clone(),
        })
        .unwrap();
    let terminal = store
        .observe_job_readonly(&input.job_id, &input.expected_source_sha256)
        .unwrap();
    let PgJobReadback::Observed(terminal) = terminal else {
        panic!("verified PG terminal transaction must be projected");
    };
    assert_eq!(terminal.resolution.as_deref(), Some("cancelled"));
    assert_eq!(terminal.reservation_state, "released");
    assert_eq!(terminal.current_attempt_id, None);
    let original_digest: String = scratch
        .admin
        .query_one(
            "SELECT detail_digest FROM job_events WHERE job_id=$1 AND event_type='JOB_TERMINAL'",
            &[&input.job_id],
        )
        .unwrap()
        .get(0);
    scratch.admin.execute(
            "UPDATE job_events SET detail_digest='sha256:tampered' WHERE job_id=$1 AND event_type='JOB_TERMINAL'",
            &[&input.job_id],
        ).unwrap();
    assert_eq!(
        store
            .observe_job_readonly(&input.job_id, &input.expected_source_sha256)
            .unwrap(),
        PgJobReadback::Inconclusive,
    );
    scratch
        .admin
        .execute(
            "UPDATE job_events SET detail_digest=$1 WHERE job_id=$2 AND event_type='JOB_TERMINAL'",
            &[&original_digest, &input.job_id],
        )
        .unwrap();

    // A hash-valid pair with inverted durable causal order is not an
    // observed effect followed by its derived terminal. Swap their sequence
    // values using a temporary positive slot to preserve SQL uniqueness.
    let source_sequence: i64 = scratch
        .admin
        .query_one(
            "SELECT event_sequence FROM job_events WHERE job_id=$1 AND event_type='PROCESS_EXITED'",
            &[&input.job_id],
        )
        .unwrap()
        .get(0);
    let terminal_sequence: i64 = scratch
        .admin
        .query_one(
            "SELECT event_sequence FROM job_events WHERE job_id=$1 AND event_type='JOB_TERMINAL'",
            &[&input.job_id],
        )
        .unwrap()
        .get(0);
    assert_eq!(terminal_sequence, source_sequence + 1);
    let swap =
        |client: &mut Client, first: i64, second: i64| {
            let temporary = terminal_sequence + 100;
            let mut tx = client.transaction().unwrap();
            for (from, to) in [(first, temporary), (second, first), (temporary, second)] {
                assert_eq!(tx.execute(
                "UPDATE job_events SET event_sequence=$1 WHERE job_id=$2 AND event_sequence=$3",
                &[&to, &input.job_id, &from],
            ).unwrap(), 1);
            }
            tx.commit().unwrap();
        };
    swap(&mut scratch.admin, source_sequence, terminal_sequence);
    assert_eq!(
        store
            .observe_job_readonly(&input.job_id, &input.expected_source_sha256)
            .unwrap(),
        PgJobReadback::Inconclusive,
        "a derived terminal may not precede its physical/source witness"
    );
    swap(&mut scratch.admin, terminal_sequence, source_sequence);
    assert!(matches!(
        store.observe_job_readonly(&input.job_id, &input.expected_source_sha256),
        Ok(PgJobReadback::Observed(_))
    ));

    // A gap is also impossible for the original atomic pair. Keep both
    // event contents and digests unchanged to isolate the sequence witness.
    scratch
        .admin
        .execute(
            "UPDATE job_events SET event_sequence=$1 WHERE job_id=$2 AND event_type='JOB_TERMINAL'",
            &[&(terminal_sequence + 1), &input.job_id],
        )
        .unwrap();
    assert_eq!(
        store
            .observe_job_readonly(&input.job_id, &input.expected_source_sha256)
            .unwrap(),
        PgJobReadback::Inconclusive,
    );
    scratch
        .admin
        .execute(
            "UPDATE job_events SET event_sequence=$1 WHERE job_id=$2 AND event_type='JOB_TERMINAL'",
            &[&terminal_sequence, &input.job_id],
        )
        .unwrap();
    assert!(matches!(
        store.observe_job_readonly(&input.job_id, &input.expected_source_sha256),
        Ok(PgJobReadback::Observed(_))
    ));

    // A corrupt durable reservation must never yield a successful readback.
    scratch
        .admin
        .execute(
            "UPDATE concurrency_reservations SET state='active' WHERE attempt_id=$1",
            &[&input.attempt_id],
        )
        .unwrap();
    assert_eq!(
        store
            .observe_job_readonly(&input.job_id, &input.expected_source_sha256)
            .unwrap(),
        PgJobReadback::Inconclusive,
    );
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_projection_snapshot_remains_coherent_during_concurrent_terminal_commit() {
    use crate::PgJobReadback;
    let dsn = physical_pg_test_dsn();
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    let mut writer = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    let mut reader = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    let input = payload(
        "projection-race",
        "job-projection-race",
        "workspace-projection",
        2,
    );
    writer.admit(&input).unwrap();
    let mut tx = reader
        .client
        .build_transaction()
        .isolation_level(postgres::IsolationLevel::RepeatableRead)
        .read_only(true)
        .start()
        .unwrap();
    let PgJobReadback::Observed(before) = PgAdmissionStore::observe_job_snapshot(
        &mut tx,
        &input.job_id,
        &input.expected_source_sha256,
    )
    .unwrap() else {
        panic!("initial admitted snapshot must be coherent");
    };
    assert_eq!(before.attempt_state, "accepted");
    assert_eq!(before.resolution, None);

    let artifact = PgArtifactRegistration {
        artifact_id: "projection-artifact".into(),
        kind: "stdout".into(),
        relative_path: "output/stdout.txt".into(),
        digest: format!("sha256:{}", "a".repeat(64)),
        media_type: "text/plain".into(),
        byte_length: 14,
        truncated: false,
        created_at_ms: input.created_at_ms + 1,
    };
    let terminal = PgTerminalNoArtifacts {
        attempt_id: input.attempt_id.clone(),
        expected_row_version: before.attempt_row_version,
        terminal_state: "failed".into(),
        result_digest: "sha256:projection-race-result".into(),
        reason_code: "PROJECTION_RACE_TEST".into(),
        exit_code: Some(1),
        finished_at_ms: input.created_at_ms + 2,
        expected_source_sha256: input.expected_source_sha256.clone(),
    };
    assert_eq!(
        writer
            .commit_terminal_with_artifacts(&terminal, &[artifact])
            .unwrap(),
        PgTerminalOutcome::Committed(input.job_id.clone())
    );

    // A fresh statement with the old versions cannot rebind: this is the
    // original split-snapshot error, not an incoherent persisted lifecycle.
    fn versions(client: &mut impl postgres::GenericClient, input: &PgAdmissionInput) -> (i64, i64) {
        let row = client
            .query_one(
                "SELECT j.row_version,a.row_version FROM jobs j JOIN attempts a
             ON a.job_id=j.job_id WHERE j.job_id=$1 AND a.attempt_id=$2",
                &[&input.job_id, &input.attempt_id],
            )
            .unwrap();
        (row.get(0), row.get(1))
    }
    let old = (before.job_row_version, before.attempt_row_version);
    assert_ne!(versions(&mut writer.client, &input), old);
    assert_eq!(versions(&mut tx, &input), old);
    assert_eq!(
        PgAdmissionStore::observe_job_snapshot(
            &mut tx,
            &input.job_id,
            &input.expected_source_sha256
        )
        .unwrap(),
        PgJobReadback::Observed(before)
    );
    let old_counts = tx
        .query_one(
            "SELECT (SELECT count(*) FROM artifacts WHERE job_id=$1),
                (SELECT count(*) FROM job_events WHERE job_id=$1)",
            &[&input.job_id],
        )
        .unwrap();
    assert_eq!(
        (old_counts.get::<_, i64>(0), old_counts.get::<_, i64>(1)),
        (0, 3)
    );
    tx.commit().unwrap();

    let PgJobReadback::Observed(after) = reader
        .observe_job_readonly(&input.job_id, &input.expected_source_sha256)
        .unwrap()
    else {
        panic!("fresh terminal snapshot must be coherent");
    };
    assert_eq!(after.resolution.as_deref(), Some("failed"));
    assert_eq!(after.current_attempt_id, None);
    assert_eq!(after.reservation_state, "released");
    assert_eq!(after.attempt_id, input.attempt_id);
    assert_eq!(scratch.count("artifacts"), 1);
    assert_eq!(scratch.count("job_events"), 5);
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_artifact_metadata_terminal_is_atomic_replayable_and_rejects_corruption() {
    let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
        .expect("explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification required");
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    let first = payload(
        "artifact-request-one",
        "artifact-job-one",
        "artifact-workspace",
        2,
    );
    store.admit(&first).unwrap();
    let artifact = PgArtifactRegistration {
        artifact_id: "artifact-A".into(),
        kind: "stdout".into(),
        relative_path: "output/stdout.txt".into(),
        digest: format!("sha256:{}", "a".repeat(64)),
        media_type: "text/plain".into(),
        byte_length: 14,
        truncated: false,
        created_at_ms: 1234568,
    };
    let terminal = PgTerminalNoArtifacts {
        attempt_id: first.attempt_id.clone(),
        expected_row_version: 0,
        terminal_state: "failed".into(),
        result_digest: "sha256:result-with-artifact".into(),
        reason_code: "PG_ARTIFACT_TERMINAL_TEST".into(),
        exit_code: Some(1),
        finished_at_ms: 1234569,
        expected_source_sha256: first.expected_source_sha256.clone(),
    };
    let mut invalid = artifact.clone();
    invalid.relative_path = "../outside".into();
    assert!(matches!(
        store.commit_terminal_with_artifacts(&terminal, &[invalid]),
        Err(PgAdmissionError::InvalidInput)
    ));
    assert_eq!(scratch.count("artifacts"), 0);
    assert_eq!(scratch.count("job_events"), 3);
    assert_eq!(
        store
            .commit_terminal_with_artifacts(&terminal, std::slice::from_ref(&artifact))
            .unwrap(),
        PgTerminalOutcome::Committed(first.job_id.clone())
    );
    assert_eq!(scratch.count("artifacts"), 1);
    assert_eq!(scratch.count("job_events"), 5);
    assert_eq!(
        store
            .commit_terminal_with_artifacts(&terminal, std::slice::from_ref(&artifact))
            .unwrap(),
        PgTerminalOutcome::Existing(first.job_id.clone()),
        "identical replay never writes duplicate Artifact"
    );
    assert!(matches!(
        store.commit_terminal_no_artifacts(&terminal),
        Err(PgAdmissionError::Blocked)
    ));
    let mut corrupted = artifact.clone();
    corrupted.digest = format!("sha256:{}", "b".repeat(64));
    assert!(matches!(
        store.commit_terminal_with_artifacts(&terminal, &[corrupted]),
        Err(PgAdmissionError::IdempotencyConflict)
    ));
    let observed = store
        .observe_job_readonly(&first.job_id, &first.expected_source_sha256)
        .unwrap();
    assert!(matches!(observed, crate::PgJobReadback::Observed(_)));
    let current: String = scratch
        .admin
        .query_one(
            "SELECT digest FROM artifacts WHERE artifact_id=$1",
            &[&"artifact-A"],
        )
        .unwrap()
        .get(0);
    scratch
        .admin
        .execute(
            "UPDATE artifacts SET digest=$1 WHERE artifact_id=$2",
            &[&format!("sha256:{}", "c".repeat(64)), &"artifact-A"],
        )
        .unwrap();
    assert_eq!(
        store
            .observe_job_readonly(&first.job_id, &first.expected_source_sha256)
            .unwrap(),
        crate::PgJobReadback::Inconclusive,
        "existing terminal event must bind the exact Artifact manifest"
    );
    scratch
        .admin
        .execute(
            "UPDATE artifacts SET digest=$1 WHERE artifact_id=$2",
            &[&current, &"artifact-A"],
        )
        .unwrap();
    let second = payload(
        "artifact-request-two",
        "artifact-job-two",
        "another-workspace",
        2,
    );
    store.admit(&second).unwrap();
    let second_terminal = PgTerminalNoArtifacts {
        attempt_id: second.attempt_id.clone(),
        expected_row_version: 0,
        terminal_state: "failed".into(),
        result_digest: "sha256:second-result".into(),
        reason_code: "PG_DUPLICATE_ARTIFACT".into(),
        exit_code: Some(1),
        finished_at_ms: 1234570,
        expected_source_sha256: second.expected_source_sha256.clone(),
    };
    // Global Artifact ID collision rejects the WHOLE terminal transaction.
    assert!(matches!(
        store.commit_terminal_with_artifacts(&second_terminal, &[artifact]),
        Err(PgAdmissionError::Database(_))
    ));
    assert_eq!(scratch.count("artifacts"), 1);
    assert_eq!(
        scratch.count("job_events"),
        8,
        "second Job keeps only its 3 admission events"
    );
    let projection = store
        .observe_job_readonly(&second.job_id, &second.expected_source_sha256)
        .unwrap();
    let crate::PgJobReadback::Observed(projection) = projection else {
        panic!("failed artifact insert must not terminalize Attempt or free capacity");
    };
    assert_eq!(projection.resolution, None);
    assert_eq!(projection.attempt_state, "accepted");
    assert_eq!(projection.reservation_state, "active");
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_composed_admit_dispatch_artifact_terminal_is_one_consumer_chain() {
    let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
        .expect("explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification required");
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    let request = payload("chain-request", "chain-job", "chain-workspace", 2);
    assert_eq!(
        store.admit(&request).unwrap(),
        PgAdmissionOutcome::Created(request.job_id.clone())
    );
    allocate_fixture(&mut scratch, &request);
    let bundle = PgBundleReady {
        attempt_id: request.attempt_id.clone(),
        expected_row_version: 0,
        bundle_digest: format!("sha256:{}", "b".repeat(64)),
        observed_at_ms: 1234568,
        expected_source_sha256: request.expected_source_sha256.clone(),
    };
    assert_eq!(store.commit_bundle_ready_pg(&bundle).unwrap(), 1);
    let dispatch = PgDispatchIssued {
        attempt_id: request.attempt_id.clone(),
        expected_row_version: 1,
        expected_bundle_digest: bundle.bundle_digest,
        observed_at_ms: 1234569,
        expected_source_sha256: request.expected_source_sha256.clone(),
    };
    assert_eq!(
        store
            .mark_dispatch_issued_pg(&dispatch, None, None)
            .unwrap(),
        2
    );
    assert!(matches!(
        store.mark_dispatch_issued_pg(&dispatch, None, None),
        Err(PgAdmissionError::Blocked),
    ));
    let artifact = PgArtifactRegistration {
        artifact_id: "chain-artifact".into(),
        kind: "stdout".into(),
        relative_path: "output/chain.txt".into(),
        digest: format!("sha256:{}", "c".repeat(64)),
        media_type: "text/plain".into(),
        byte_length: 8,
        truncated: false,
        created_at_ms: 1234570,
    };
    let terminal = PgTerminalNoArtifacts {
        attempt_id: request.attempt_id.clone(),
        expected_row_version: 2,
        terminal_state: "failed".into(),
        result_digest: "sha256:chain-result".into(),
        reason_code: "CHAIN_TEST".into(),
        exit_code: Some(1),
        finished_at_ms: 1234571,
        expected_source_sha256: request.expected_source_sha256.clone(),
    };
    assert_eq!(
        store
            .commit_terminal_with_artifacts(&terminal, std::slice::from_ref(&artifact))
            .unwrap(),
        PgTerminalOutcome::Committed(request.job_id.clone()),
    );
    assert_eq!(
        scratch.count("job_events"),
        7,
        "admission 3, dispatch 2, terminal 2"
    );
    assert_eq!(scratch.count("artifacts"), 1);
    let outcome = store
        .observe_job_readonly(&request.job_id, &request.expected_source_sha256)
        .unwrap();
    let crate::PgJobReadback::Observed(snapshot) = outcome else {
        panic!("full PG lifecycle must remain coherently observable");
    };
    assert_eq!(snapshot.resolution.as_deref(), Some("failed"));
    assert_eq!(snapshot.reservation_state, "released");
    assert_eq!(snapshot.attempt_row_version, 3);
    assert_eq!(
        store
            .commit_terminal_with_artifacts(&terminal, &[artifact])
            .unwrap(),
        PgTerminalOutcome::Existing(request.job_id.clone()),
    );
    assert_eq!(
        scratch.count("job_events"),
        7,
        "retry may not append a second terminal"
    );
    assert_eq!(scratch.count("artifacts"), 1);
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_readback_rejects_detached_unsettled_historical_attempt() {
    use crate::PgJobReadback;
    let dsn = physical_pg_test_dsn();
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    let input = payload("history-readback", "history-job", "history-workspace", 2);
    store.admit(&input).unwrap();
    store
        .commit_terminal_no_artifacts(&PgTerminalNoArtifacts {
            attempt_id: input.attempt_id.clone(),
            expected_row_version: 0,
            terminal_state: "failed".into(),
            result_digest: "sha256:terminal".into(),
            reason_code: "HISTORY_TEST".into(),
            exit_code: Some(1),
            finished_at_ms: input.created_at_ms + 1,
            expected_source_sha256: input.expected_source_sha256.clone(),
        })
        .unwrap();
    let read = |store: &mut PgAdmissionStore| {
        store
            .observe_job_readonly(&input.job_id, &input.expected_source_sha256)
            .unwrap()
    };
    assert!(matches!(read(&mut store), PgJobReadback::Observed(_)));
    // Admin-only, schema-valid historical contradiction. This is not a claim
    // that the ordinary Runtime can admit such a history.
    scratch
        .admin
        .execute(
            "UPDATE attempts SET attempt_number=2 WHERE attempt_id=$1",
            &[&input.attempt_id],
        )
        .unwrap();
    let earlier = "attempt-history-earlier";
    scratch.admin.execute(
        "INSERT INTO attempts(attempt_id,job_id,attempt_number,state,termination_intent,launch_token_digest,bundle_path,unit_name,created_at_ms,row_version) VALUES($1,$2,1,'running','natural','launch-old','/nonproduction/old','older.service',$3,0)",
        &[&earlier, &input.job_id, &input.created_at_ms],
    ).unwrap();
    scratch.admin.execute(
        "INSERT INTO concurrency_reservations(reservation_id,attempt_id,global_limit,state,acquired_at_ms,state_observed_at_ms) VALUES('reservation-history-earlier',$1,2,'active',$2,$2)",
        &[&earlier, &input.created_at_ms],
    ).unwrap();
    assert_eq!(
        read(&mut store),
        PgJobReadback::Inconclusive,
        "latest terminal Attempt cannot hide a detached live predecessor"
    );
    scratch
        .admin
        .execute(
            "UPDATE attempts SET state='orphaned' WHERE attempt_id=$1",
            &[&earlier],
        )
        .unwrap();
    scratch
        .admin
        .execute(
            "UPDATE concurrency_reservations SET state='held_orphaned' WHERE attempt_id=$1",
            &[&earlier],
        )
        .unwrap();
    assert_eq!(
        read(&mut store),
        PgJobReadback::Inconclusive,
        "held orphan cannot be hidden by a terminal successor"
    );
    scratch.admin.execute(
        "UPDATE attempts SET state='lost',result_digest='sha256:old',finished_at_ms=$2 WHERE attempt_id=$1",
        &[&earlier, &input.created_at_ms],
    ).unwrap();
    scratch.admin.execute(
        "UPDATE concurrency_reservations SET state='released',released_at_ms=$2 WHERE attempt_id=$1",
        &[&earlier, &input.created_at_ms],
    ).unwrap();
    assert!(
        matches!(read(&mut store), PgJobReadback::Observed(_)),
        "settled historical predecessor must not invalidate the latest result"
    );
    // Scheduler allocations are separate from admission reservations.
    // A genuine terminal writer releases both. Absence of an allocation is
    // legal (never-dispatched); a present active allocation is not settled.
    for attempt in [earlier, input.attempt_id.as_str()] {
        scratch.admin.execute(
            "INSERT INTO job_allocations(attempt_id,resources_json,workspace_access_json,owner,state,acquired_at_ms) VALUES($1,'{}','{}',$2,'active',$3) ON CONFLICT(attempt_id) DO UPDATE SET state='active',released_at_ms=NULL",
            &[&attempt, &input.principal, &input.created_at_ms],
        ).unwrap();
        assert_eq!(
            read(&mut store),
            PgJobReadback::Inconclusive,
            "terminal projection cannot hide active allocation for {attempt}"
        );
        scratch
            .admin
            .execute(
                "UPDATE job_allocations SET state='released',released_at_ms=$2 WHERE attempt_id=$1",
                &[&attempt, &input.created_at_ms],
            )
            .unwrap();
        assert!(matches!(read(&mut store), PgJobReadback::Observed(_)));
    }
    scratch
        .admin
        .execute(
            "DELETE FROM concurrency_reservations WHERE attempt_id=$1",
            &[&earlier],
        )
        .unwrap();
    assert_eq!(
        read(&mut store),
        PgJobReadback::Inconclusive,
        "missing historical reservation is not evidence of release"
    );
}
