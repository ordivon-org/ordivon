use super::super::{pg_writer_epoch_digest, PgAdmissionError, PgAdmissionInput, PgAdmissionStore};
use super::{PgBundleReady, PgDispatchIssued, PgRunnerBound};
use postgres::{Client, NoTls};
use uuid::Uuid;

struct Scratch {
    admin: Client,
    schema: String,
}
impl Drop for Scratch {
    fn drop(&mut self) {
        let _ = self.admin.batch_execute(&format!(
            "SET search_path TO public; DROP SCHEMA IF EXISTS \"{}\" CASCADE",
            self.schema
        ));
    }
}

#[test]
#[ignore = "requires isolated ORDIVON_PG_TEST_DSN for real PostgreSQL 18"]
fn pg18_runner_bound_requires_original_dispatch_issued_evidence() {
    let dsn = std::env::var("ORDIVON_PG_TEST_DSN").expect("native disposable PG only");
    let schema = format!("test_dispatch_{}", Uuid::now_v7().simple());
    let mut admin = Client::connect(&dsn, NoTls).expect("real physical PG");
    admin
        .batch_execute(&format!("CREATE SCHEMA \"{schema}\""))
        .unwrap();
    let mut scratch = Scratch {
        admin,
        schema: schema.clone(),
    };
    scratch
        .admin
        .query_one(
            "SELECT set_config('search_path',$1,false)",
            &[&format!("\"{schema}\"")],
        )
        .unwrap();
    scratch
        .admin
        .batch_execute(include_str!(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/sql/pg_fresh_epoch.sql"
        )))
        .unwrap();
    let source = "a".repeat(64);
    scratch
        .admin
        .execute(
            "INSERT INTO _stage_control VALUES('source','QUALIFIED_WRITER',$1,true)",
            &[&source],
        )
        .unwrap();
    let physical = scratch
        .admin
        .query_one(
            "SELECT (SELECT system_identifier::text FROM pg_control_system()),
                (SELECT timeline_id FROM pg_control_checkpoint())",
            &[],
        )
        .unwrap();
    let epoch = pg_writer_epoch_digest(
        &source,
        &physical.get::<_, String>(0),
        physical.get::<_, i32>(1),
    );
    scratch
        .admin
        .execute(
            "INSERT INTO _stage_control VALUES('epoch','QUALIFIED_EPOCH',$1,true)",
            &[&epoch],
        )
        .unwrap();
    let mut store = PgAdmissionStore::connect(&dsn, &schema).unwrap();
    let input = PgAdmissionInput {
        job_id: "job-dispatch-proof".into(),
        attempt_id: "attempt-dispatch-proof".into(),
        reservation_id: "reservation-dispatch-proof".into(),
        principal: "native-pg-proof".into(),
        client_request_id: "dispatch-original-proof".into(),
        request_digest: "sha256:original-request".into(),
        operation_digest: "sha256:original-operation".into(),
        workspace_id: "ws-original-proof".into(),
        workspace_snapshot_json: "{}".into(),
        execution_plan_json: "{}".into(),
        execution_plan_digest: "sha256:original-plan".into(),
        launch_token_digest: "sha256:original-token".into(),
        bundle_path: "/nonproduction/pg-dispatch-proof".into(),
        unit_name: "ordivon-physical-dispatch-proof.service".into(),
        global_limit: 2,
        created_at_ms: 1234567,
        expected_source_sha256: source.clone(),
    };
    store.admit(&input).unwrap();
    scratch.admin.execute(
        "INSERT INTO job_allocations(attempt_id,resources_json,workspace_access_json,owner,state,acquired_at_ms)
         VALUES($1,'{}','{}',$2,'active',$3)",
        &[&input.attempt_id,&input.principal,&input.created_at_ms],
    ).unwrap();
    let bundle = format!("sha256:{}", "b".repeat(64));
    assert_eq!(
        store
            .commit_bundle_ready_pg(&PgBundleReady {
                attempt_id: input.attempt_id.clone(),
                expected_row_version: 0,
                bundle_digest: bundle.clone(),
                observed_at_ms: input.created_at_ms + 1,
                expected_source_sha256: source.clone(),
            })
            .unwrap(),
        1
    );
    assert_eq!(
        store
            .mark_dispatch_issued_pg(
                &PgDispatchIssued {
                    attempt_id: input.attempt_id.clone(),
                    expected_row_version: 1,
                    expected_bundle_digest: bundle.clone(),
                    observed_at_ms: input.created_at_ms + 2,
                    expected_source_sha256: source.clone(),
                },
                None,
                None
            )
            .unwrap(),
        2
    );
    // Durable Attempt and allocation still look eligible. Remove only the
    // original PG event. Neither event order nor physical start may be invented.
    assert_eq!(
        scratch
            .admin
            .execute(
                "DELETE FROM job_events WHERE job_id=$1 AND attempt_id=$2
         AND event_type='DISPATCH_ISSUED'",
                &[&input.job_id, &input.attempt_id],
            )
            .unwrap(),
        1
    );
    let witness = PgRunnerBound {
        attempt_id: input.attempt_id.clone(),
        expected_row_version: 2,
        expected_bundle_digest: bundle,
        runner_start_digest: format!("sha256:{}", "c".repeat(64)),
        native_invocation_id: "original-native-invocation".into(),
        observed_at_ms: input.created_at_ms + 3,
        expected_source_sha256: source,
    };
    assert!(
        matches!(
            store.mark_runner_bound_pg(&witness),
            Err(PgAdmissionError::Blocked)
        ),
        "a nonoriginal, unissued Runner must never become RUNNING"
    );
    let attempt = scratch
        .admin
        .query_one(
            "SELECT state,row_version FROM attempts WHERE attempt_id=$1",
            &[&input.attempt_id],
        )
        .unwrap();
    assert_eq!(attempt.get::<_, String>(0), "starting");
    assert_eq!(attempt.get::<_, i64>(1), 2);
    let bound_count: i64 = scratch
        .admin
        .query_one(
            "SELECT count(*) FROM job_events WHERE attempt_id=$1 AND event_type='RUNNER_BOUND'",
            &[&input.attempt_id],
        )
        .unwrap()
        .get(0);
    assert_eq!(bound_count, 0);
}
