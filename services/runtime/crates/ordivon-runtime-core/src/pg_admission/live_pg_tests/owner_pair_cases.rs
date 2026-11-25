//! Qualification of a native relational ownership contract on a private PG
//! epoch. This is not a production migration or permission to repair history.
use super::*;
use postgres::error::SqlState;

fn reject_fk(result: Result<u64, postgres::Error>, constraint: &str) {
    let error = result.expect_err("foreign owner pair must be rejected");
    let db = error.as_db_error().expect("native database error");
    assert_eq!(db.code(), &SqlState::FOREIGN_KEY_VIOLATION);
    assert_eq!(db.constraint(), Some(constraint));
}

#[test]
#[ignore = "requires explicit isolated PostgreSQL qualification"]
fn pg18_native_owner_pair_expand_validate_contract() {
    let dsn = physical_pg_test_dsn();
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    let a = payload("owner-a-request", "owner-a-job", "owner-a-ws", 2);
    let b = payload("owner-b-request", "owner-b-job", "owner-b-ws", 2);
    store.admit(&a).unwrap();
    store.admit(&b).unwrap();
    let artifact = "INSERT INTO artifacts(artifact_id,job_id,attempt_id,kind,relative_path)
                    VALUES($1,$2,$3,'stdout',$1)";
    let event = "INSERT INTO job_events(event_id,job_id,attempt_id,event_sequence,event_type,
                 origin,reason_code,detail_json,detail_digest,observed_at_ms)
                 VALUES($1,$2,$3,$4,'FIXTURE','test','TEST','{}','sha256:fixture',1)";
    // The fresh schema rejects both false pairs directly at the write boundary.
    reject_fk(
        scratch
            .admin
            .execute(artifact, &[&"fresh-bad-artifact", &a.job_id, &b.attempt_id]),
        "artifact_owner_pair_fk",
    );
    reject_fk(
        scratch.admin.execute(
            event,
            &[&"fresh-bad-event", &a.job_id, &b.attempt_id, &100_i64],
        ),
        "event_owner_pair_fk",
    );
    let fresh_valid: i64 = scratch.admin.query_one("SELECT count(*) FROM pg_constraint WHERE conrelid IN ('artifacts'::regclass,'job_events'::regclass) AND conname IN ('artifact_owner_pair_fk','event_owner_pair_fk') AND convalidated AND conenforced", &[]).unwrap().get(0);
    assert_eq!(fresh_valid, 2);
    // Reconstruct only this private fixture's legacy shape for migration proof.
    // The real readback must still reject corruption in an unexpanded old schema.
    scratch
        .admin
        .batch_execute(
            "ALTER TABLE artifacts DROP CONSTRAINT artifact_owner_pair_fk;
        ALTER TABLE job_events DROP CONSTRAINT event_owner_pair_fk;
        ALTER TABLE attempts DROP CONSTRAINT idx_attempts_owner_pair;",
        )
        .unwrap();
    // Legacy individual FKs permit a pair of individually valid, unrelated IDs.
    scratch
        .admin
        .execute(artifact, &[&"old-bad-artifact", &a.job_id, &b.attempt_id])
        .unwrap();
    scratch
        .admin
        .execute(
            event,
            &[&"old-bad-event", &a.job_id, &b.attempt_id, &100_i64],
        )
        .unwrap();
    scratch.admin.batch_execute("CREATE UNIQUE INDEX CONCURRENTLY idx_attempts_owner_pair ON attempts(job_id,attempt_id);
        ").unwrap();
    scratch
        .admin
        .batch_execute(
            "ALTER TABLE artifacts ADD CONSTRAINT artifact_owner_pair_fk
          FOREIGN KEY(job_id,attempt_id) REFERENCES attempts(job_id,attempt_id) NOT VALID;
        ALTER TABLE job_events ADD CONSTRAINT event_owner_pair_fk
          FOREIGN KEY(job_id,attempt_id) REFERENCES attempts(job_id,attempt_id) NOT VALID;",
        )
        .unwrap();
    reject_fk(
        scratch
            .admin
            .execute(artifact, &[&"new-bad-artifact", &a.job_id, &b.attempt_id]),
        "artifact_owner_pair_fk",
    );
    reject_fk(
        scratch.admin.execute(
            event,
            &[&"new-bad-event", &a.job_id, &b.attempt_id, &101_i64],
        ),
        "event_owner_pair_fk",
    );
    for (table, constraint) in [
        ("artifacts", "artifact_owner_pair_fk"),
        ("job_events", "event_owner_pair_fk"),
    ] {
        reject_fk(
            scratch.admin.execute(
                &format!("ALTER TABLE {table} VALIDATE CONSTRAINT {constraint}"),
                &[],
            ),
            constraint,
        );
        let valid: bool = scratch
            .admin
            .query_one(
                "SELECT convalidated FROM pg_constraint WHERE conrelid=$1::text::regclass AND conname=$2",
                &[&table, &constraint],
            )
            .unwrap()
            .get(0);
        assert!(!valid);
    }
    // No automatic repair. Remove only the two intentionally invalid fixture rows.
    assert_eq!(
        scratch
            .admin
            .execute(
                "DELETE FROM artifacts WHERE artifact_id='old-bad-artifact'",
                &[]
            )
            .unwrap(),
        1
    );
    assert_eq!(
        scratch
            .admin
            .execute("DELETE FROM job_events WHERE event_id='old-bad-event'", &[])
            .unwrap(),
        1
    );
    scratch
        .admin
        .batch_execute(
            "ALTER TABLE artifacts VALIDATE CONSTRAINT artifact_owner_pair_fk;
        ALTER TABLE job_events VALIDATE CONSTRAINT event_owner_pair_fk;",
        )
        .unwrap();
    let validated: i64 = scratch
        .admin
        .query_one(
            "SELECT count(*) FROM pg_constraint
        WHERE conrelid IN ('artifacts'::regclass,'job_events'::regclass)
        AND conname IN ('artifact_owner_pair_fk','event_owner_pair_fk')
        AND convalidated AND conenforced",
            &[],
        )
        .unwrap()
        .get(0);
    assert_eq!(validated, 2);
    scratch
        .admin
        .execute(artifact, &[&"good-artifact", &a.job_id, &a.attempt_id])
        .unwrap();
    scratch
        .admin
        .execute(event, &[&"good-event", &a.job_id, &a.attempt_id, &102_i64])
        .unwrap();
    // MATCH SIMPLE deliberately preserves the existing job-level nullable Attempt.
    scratch
        .admin
        .execute(
            event,
            &[
                &"job-only-event",
                &a.job_id,
                &Option::<String>::None,
                &103_i64,
            ],
        )
        .unwrap();
    reject_fk(
        scratch.admin.execute(
            "UPDATE artifacts SET job_id=$1 WHERE artifact_id='good-artifact'",
            &[&b.job_id],
        ),
        "artifact_owner_pair_fk",
    );
    reject_fk(
        scratch.admin.execute(
            "UPDATE job_events SET attempt_id=$1 WHERE event_id='good-event'",
            &[&b.attempt_id],
        ),
        "event_owner_pair_fk",
    );
    let error = scratch
        .admin
        .execute(
            "UPDATE attempts SET job_id=$1,attempt_number=2 WHERE attempt_id=$2",
            &[&b.job_id, &a.attempt_id],
        )
        .unwrap_err();
    assert_eq!(error.code(), Some(&SqlState::FOREIGN_KEY_VIOLATION));
    assert!(matches!(
        error.as_db_error().unwrap().constraint(),
        Some("artifact_owner_pair_fk" | "event_owner_pair_fk")
    ));
    // Existing PG write path remains functional under the new contract.
    let c = payload("owner-c-request", "owner-c-job", "owner-c-ws", 3);
    store.admit(&c).unwrap();
    assert_eq!(scratch.count("jobs"), 3);
}
