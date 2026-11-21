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
mod cancellation_cases;
mod dispatch_cases;
mod issuer_cases;
mod terminal_cases;
