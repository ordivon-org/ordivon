//! PostgreSQL physical fixture and domain-specific real PG18 tests.
use super::*;
use std::sync::{Arc, Barrier};
use std::thread;

fn physical_pg_test_dsn() -> String {
    std::env::var("ORDIVON_PG_TEST_DSN").expect(
        "physical PostgreSQL tests require ORDIVON_PG_TEST_DSN; run the dedicated mise task",
    )
}

fn historical_pg_stage_test_dsn() -> String {
    std::env::var("ORDIVON_PG_STAGE_TEST_DSN").expect(
            "historical stage qualification requires ORDIVON_PG_STAGE_TEST_DSN; run the dedicated stage task",
        )
}

// An operator supplies an isolated PostgreSQL DSN for physical tests.
// No environment value means the ordinary CI suite never mutates PG.
const SCHEMA: &str = include_str!(concat!(
    env!("CARGO_MANIFEST_DIR"),
    "/sql/pg_fresh_epoch.sql"
));

struct Scratch {
    admin: Client,
    name: String,
}
impl Scratch {
    fn new(dsn: &str) -> Self {
        let name = format!("test_admit_{}", Uuid::now_v7().simple());
        let mut admin = Client::connect(dsn, NoTls).expect("test PG18 connection");
        admin
            .batch_execute(&format!("CREATE SCHEMA \"{name}\""))
            .expect("private test schema");
        admin
            .query_one(
                "SELECT set_config('search_path',$1,false)",
                &[&format!("\"{name}\"")],
            )
            .expect("test-only search path");
        admin
            .batch_execute(SCHEMA)
            .expect("native PG fixture constraints");
        admin
            .execute(
                "INSERT INTO _stage_control VALUES('source','VERIFIED_NON_AUTHORITY',$1,false)",
                &[&"a".repeat(64)],
            )
            .expect("non-authority fixture");
        Self { admin, name }
    }
    fn qualify(&mut self) {
        self.admin.execute(
                "UPDATE _stage_control SET state='QUALIFIED_WRITER',promotion_allowed=true WHERE id='source'",
                &[]
            ).expect("test-only synthetic qualifier");
        let pg = self.admin.query_one(
                "SELECT (SELECT system_identifier::text FROM pg_control_system()),                         (SELECT timeline_id FROM pg_control_checkpoint())",
                &[],
            ).expect("native physical PostgreSQL epoch");
        let digest = pg_writer_epoch_digest(
            &"a".repeat(64),
            &pg.get::<_, String>(0),
            pg.get::<_, i32>(1),
        );
        self.admin.execute(
                "INSERT INTO _stage_control VALUES('epoch','QUALIFIED_EPOCH',$1,true)                  ON CONFLICT(id) DO UPDATE SET state='QUALIFIED_EPOCH',source_sha256=EXCLUDED.source_sha256,promotion_allowed=true",
                &[&digest],
            ).expect("operator-owned epoch fixture");
    }
    fn count(&mut self, table: &str) -> i64 {
        self.admin
            .query_one(&format!("SELECT count(*) FROM {table}"), &[])
            .unwrap()
            .get(0)
    }
}
impl Drop for Scratch {
    fn drop(&mut self) {
        // A dedicated scratch namespace, never an installed Runtime
        // schema; do not retain test effects across test runs.
        let _ = self.admin.batch_execute(&format!(
            "SET search_path TO public; DROP SCHEMA IF EXISTS \"{}\" CASCADE",
            self.name
        ));
    }
}
fn allocate_fixture(scratch: &mut Scratch, input: &PgAdmissionInput) {
    // Test-only scheduling decision. These SQL tests qualify transaction
    // fencing, not a native-resource probe or physical process launch.
    scratch.admin.execute("INSERT INTO job_allocations(attempt_id,resources_json,workspace_access_json,owner,state,acquired_at_ms) VALUES($1,'{}','{}',$2,'active',$3)",&[&input.attempt_id,&input.principal,&input.created_at_ms]).unwrap();
}
fn payload(client_key: &str, job: &str, workspace: &str, cap: i32) -> PgAdmissionInput {
    PgAdmissionInput {
        job_id: job.to_string(),
        attempt_id: format!("attempt-{job}"),
        reservation_id: format!("reservation-{job}"),
        principal: "pg-native-test".into(),
        client_request_id: client_key.to_string(),
        request_digest: format!("sha256:request-{client_key}"),
        operation_digest: format!("sha256:operation-{client_key}"),
        workspace_id: workspace.into(),
        workspace_snapshot_json: "{}".into(),
        execution_plan_json: "{}".into(),
        execution_plan_digest: "sha256:test-plan".into(),
        launch_token_digest: "sha256:launch".into(),
        bundle_path: "/nonproduction/pg-test".into(),
        unit_name: format!("{job}.service"),
        global_limit: cap,
        created_at_ms: 1234567,
        expected_source_sha256: "a".repeat(64),
    }
}

mod admission_cases;
mod artifact_index_cases;
mod cancellation_cases;
mod crash_cut_cases;
mod dispatch_cases;
mod issuer_cases;
mod terminal_cases;

mod stateful_model_cases;

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
