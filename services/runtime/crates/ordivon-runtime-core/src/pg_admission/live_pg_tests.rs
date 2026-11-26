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
fn pg18_windows_native_drain_event_is_current_attempt_fenced_and_never_terminal_on_its_own() {
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
    assert!(matches!(
        reopened
            .record_native_windows_drain(&after_restart)
            .unwrap(),
        PgNativeWindowsDrainOutcome::Existing(_)
    ));
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

/// Full DB/Artifact *consumer* test, with synthetic Win32 prerequisite.
/// Native original JobObject/pipe evidence is tested on Windows separately:
/// this verifies that the existing PG Writer never substitutes an event
/// for a terminal but DOES atomically register the correct native Result
/// and output bytes after the qualified event and bounded parser agree.
#[test]
#[ignore = "requires explicit disposable ORDIVON_PG_TEST_DSN PostgreSQL instance"]
fn pg18_windows_pg_native_journal_and_result_reach_one_verified_terminal_with_artifacts() {
    use crate::pg_readback::PgJobReadback;
    use crate::pg_windows_evidence::{
        inspect_windows_pg_bundle, terminal::prepare_windows_terminal, PgWindowsWitnessIdentity,
    };
    let dsn = physical_pg_test_dsn();
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    let temp = tempfile::tempdir().unwrap();
    let mut input = payload(
        "winpg-physical-result-r50",
        "job-winpg-native-terminal-r50",
        "workspace-winpg-native-terminal-r50",
        2,
    );
    let id = PgWindowsWitnessIdentity {
        job_id: input.job_id.clone(),
        attempt_id: input.attempt_id.clone(),
        launch_token_digest: format!("sha256:{}", "a".repeat(64)),
        request_digest: format!("sha256:{}", "b".repeat(64)),
        launcher_image_digest: format!("sha256:{}", "c".repeat(64)),
    };
    input.launch_token_digest = id.launch_token_digest.clone();
    input.bundle_path = temp.path().to_string_lossy().into_owned();
    input.unit_name = format!("Ordivon.{}", id.attempt_id);
    input.workspace_snapshot_json = serde_json::json!({
        "executionProvider":{"contract":"windows_native_launcher_v1",
            "executableDigest":id.launcher_image_digest}
    })
    .to_string();
    let mut db = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    assert!(matches!(
        db.admit(&input).unwrap(),
        PgAdmissionOutcome::Created(_)
    ));
    allocate_fixture(&mut scratch, &input);
    // Synthetic native issued state: DOES NOT claim Windows launched.
    db.client.execute(
        "UPDATE attempts SET state='starting',bundle_digest=$1,row_version=row_version+1 WHERE attempt_id=$2",
        &[&id.request_digest,&id.attempt_id],
    ).unwrap();
    let version: i64 = db
        .client
        .query_one(
            "SELECT row_version FROM attempts WHERE attempt_id=$1",
            &[&id.attempt_id],
        )
        .unwrap()
        .get(0);
    let source = "a".repeat(64);
    let stdout = b"PG_TERMINAL_RESULT_R50";
    let stderr = b"";
    std::fs::write(temp.path().join("stdout.log"), stdout).unwrap();
    std::fs::write(temp.path().join("stderr.log"), stderr).unwrap();
    let hash = |v: &[u8]| format!("sha256:{}", hex::encode(Sha256::digest(v)));
    let write = |file: &str, value: serde_json::Value| {
        std::fs::write(temp.path().join(file), serde_json::to_vec(&value).unwrap()).unwrap();
    };
    write(
        "windows-launcher-start.json",
        serde_json::json!({
            "schemaVersion":1,"jobId":id.job_id,"attemptId":id.attempt_id,
            "launchTokenDigest":id.launch_token_digest,"requestDigest":id.request_digest,
            "launcherImageDigest":id.launcher_image_digest,"jobName":input.unit_name,
            "launcherProcessId":200,"launcherProcessCreationTimeFileTime":300,"observedUnixMs":1
        }),
    );
    write(
        "windows-start.json",
        serde_json::json!({
            "schemaVersion":1,"jobId":id.job_id,"attemptId":id.attempt_id,
            "launchTokenDigest":id.launch_token_digest,"requestDigest":id.request_digest,
            "launcherImageDigest":id.launcher_image_digest,"jobName":input.unit_name,
            "launcherProcessId":200,"launcherProcessCreationTimeFileTime":300,"observedUnixMs":2,
            "processId":400,"processCreationTimeFileTime":500
        }),
    );
    write(
        "result.json",
        serde_json::json!({
            "schemaVersion":1,"jobId":id.job_id,"attemptId":id.attempt_id,
            "taskId":id.attempt_id,"launchTokenDigest":id.launch_token_digest,
            "status":"COMPLETED","exitCode":0,"timedOut":false,
            "startedUnixMs":4,"finishedUnixMs":5,
            "stdout":{"fileName":"stdout.log","digest":hash(stdout),"retainedBytes":stdout.len(),"truncated":false},
            "stderr":{"fileName":"stderr.log","digest":hash(stderr),"retainedBytes":stderr.len(),"truncated":false}
        }),
    );
    let witness = inspect_windows_pg_bundle(temp.path(), &id).unwrap();
    let result_digest = witness.result_digest.clone().unwrap();
    let native = PgNativeWindowsDrainInput {
        job_id: id.job_id.clone(),
        attempt_id: id.attempt_id.clone(),
        expected_row_version: version,
        expected_source_sha256: source.clone(),
        launch_token_digest: id.launch_token_digest.clone(),
        request_digest: id.request_digest.clone(),
        result_digest,
        launcher_process_id: 200,
        launcher_creation_file_time: 300,
        observed_at_ms: 6,
    };
    assert!(!db.qualified_native_windows_drain(&native).unwrap());
    assert!(matches!(
        db.record_native_windows_drain(&native).unwrap(),
        PgNativeWindowsDrainOutcome::Committed(_)
    ));
    // Native event is NOT terminal; PG capacity remains reserved.
    assert_eq!(scratch.count("artifacts"), 0);
    let (terminal, artifacts) =
        prepare_windows_terminal(temp.path(), &id, &witness, &source, version).unwrap();
    assert_eq!(artifacts.len(), 3);
    assert_eq!(artifacts[0].byte_length, stdout.len() as i64);
    // Direct Windows native terminal writer *without* a journal can no
    // longer be authorized by merely having the target Result bytes.
    // First physically remove the event only in this disposable test PG
    // schema, verify the very same CAS rejects it, restore original event
    // from the qualified API, then continue to exact terminal.
    let saved_event=db.client.query_one(
        "SELECT event_id,event_sequence,event_type,origin,previous_state,new_state,reason_code,detail_json,detail_digest,observed_at_ms FROM job_events WHERE attempt_id=$1 AND event_type='WINDOWS_NATIVE_JOB_DRAIN_OBSERVED'",
        &[&id.attempt_id],
    ).unwrap();
    db.client.execute(
        "DELETE FROM job_events WHERE attempt_id=$1 AND event_type='WINDOWS_NATIVE_JOB_DRAIN_OBSERVED'",
        &[&id.attempt_id],
    ).unwrap();
    assert!(matches!(
        db.commit_terminal_with_artifacts(&terminal, &artifacts),
        Err(PgAdmissionError::Blocked)
    ));
    assert_eq!(scratch.count("artifacts"), 0);
    db.client.execute(
        "INSERT INTO job_events(event_id,job_id,attempt_id,event_sequence,event_type,origin,previous_state,new_state,reason_code,detail_json,detail_digest,observed_at_ms) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)",
        &[&saved_event.get::<_,String>(0),&id.job_id,&id.attempt_id,
          &saved_event.get::<_,i64>(1),&saved_event.get::<_,String>(2),
          &saved_event.get::<_,String>(3),&saved_event.get::<_,Option<String>>(4),
          &saved_event.get::<_,Option<String>>(5),&saved_event.get::<_,String>(6),
          &saved_event.get::<_,String>(7),&saved_event.get::<_,String>(8),
          &saved_event.get::<_,i64>(9)],
    ).unwrap();
    // Actual R8 donor carried a Linux ".service" unit_name despite a
    // Windows-native executionProvider. Even with a genuine event, this
    // shape must fail closed before source promotion.
    db.client
        .execute(
            "UPDATE attempts SET unit_name='ordivon-pg-wrong-native.service' WHERE attempt_id=$1",
            &[&id.attempt_id],
        )
        .unwrap();
    assert!(matches!(
        db.commit_terminal_with_artifacts(&terminal, &artifacts),
        Err(PgAdmissionError::Blocked)
    ));
    db.client
        .execute(
            "UPDATE attempts SET unit_name=$1 WHERE attempt_id=$2",
            &[&input.unit_name, &id.attempt_id],
        )
        .unwrap();
    let mut stale = terminal.clone();
    stale.expected_row_version += 1;
    assert!(matches!(
        db.commit_terminal_with_artifacts(&stale, &artifacts),
        Err(PgAdmissionError::Blocked)
    ));
    assert_eq!(scratch.count("artifacts"), 0);
    let mut recovered = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    assert!(recovered.qualified_native_windows_drain(&native).unwrap());
    assert_eq!(
        recovered
            .commit_terminal_with_artifacts(&terminal, &artifacts)
            .unwrap(),
        PgTerminalOutcome::Committed(id.job_id.clone())
    );
    assert_eq!(scratch.count("artifacts"), 3);
    assert!(matches!(
        recovered.observe_job_readonly(&id.job_id,&source).unwrap(),
        PgJobReadback::Observed(snapshot)
            if snapshot.resolution.as_deref()==Some("succeeded")
               && snapshot.attempt_state=="succeeded"
               && snapshot.reservation_state=="released"
               && snapshot.current_attempt_id.is_none()
               && snapshot.result_digest.as_deref()==Some(terminal.result_digest.as_str())
    ));
    assert!(matches!(
        recovered
            .commit_terminal_with_artifacts(&terminal, &artifacts)
            .unwrap(),
        PgTerminalOutcome::Existing(_)
    ));
    // Strong readback checks process and terminal event digests, not merely
    // an SQL state string. This remains an SQL consumer test, NOT OS proof.
    let digest: &str = &terminal.result_digest;
    assert_eq!(
        digest,
        hash(&std::fs::read(temp.path().join("result.json")).unwrap())
    );
}

/// One real native Windows process / one real PG18 Job / verified Artifacts.
/// This test is excluded from ordinary CI because it needs an explicitly
/// isolated Windows PostgreSQL DSN and an exact built Launcher executable.
/// No production SCM, schema, Gateway, or old Windows SQLite is touched.
#[cfg(windows)]
#[test]
#[ignore = "requires isolated Windows PG18 DSN, original Launcher and physical Win32 kernel"]
fn winpg_native_real_launcher_and_postgres_same_attempt_terminal_artifact() {
    run_winpg_native_real_attempt(false);
}
#[cfg(windows)]
#[test]
#[ignore = "requires isolated Windows PG18 DSN, original Launcher and physical Win32 kernel"]
fn winpg_native_wrong_peer_cannot_journal_or_terminal() {
    run_winpg_native_real_attempt(true);
}
#[cfg(windows)]
fn run_winpg_native_real_attempt(force_wrong_peer: bool) {
    use crate::pg_readback::PgJobReadback;
    use crate::pg_windows_evidence::{reconcile_windows_native_terminal, PgWindowsWitnessIdentity};
    use std::{
        path::PathBuf,
        process::{Command, Stdio},
        time::{Duration, Instant},
    };
    use windows_sys::Win32::{
        Foundation::{CloseHandle, FILETIME},
        System::Threading::{GetProcessTimes, OpenProcess, PROCESS_QUERY_LIMITED_INFORMATION},
    };
    let dsn = physical_pg_test_dsn();
    let launcher = PathBuf::from(
        std::env::var("ORDIVON_WINPG_TEST_LAUNCHER")
            .expect("explicit original C# Launcher candidate required"),
    );
    let private_root = PathBuf::from(
        std::env::var("ORDIVON_WINPG_TEST_ROOT")
            .expect("explicit own disposable Windows test Workspace required"),
    );
    assert!(launcher.is_file());
    assert!(private_root.is_dir());
    let image = crate::universal::sha256_file(&launcher).expect("exact original binary SHA-256");
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    let bundle = tempfile::tempdir_in(private_root).expect("isolated native Attempt bundle");
    let unique = Uuid::now_v7().simple();
    let job = format!("job-winpg-native-real-{unique}");
    let attempt = format!("attempt-winpg-native-real-{unique}");
    let mut input = payload(
        &format!("winpg-{unique}"),
        &job,
        &format!("workspace-native-{unique}"),
        2,
    );
    input.attempt_id = attempt.clone();
    input.reservation_id = format!("reservation-winpg-{unique}");
    input.launch_token_digest = format!("sha256:{}", "a".repeat(64));
    input.bundle_path = bundle.path().to_string_lossy().into_owned();
    input.unit_name = format!("Ordivon.{attempt}");
    let request = b"{}";
    std::fs::write(bundle.path().join("request.json"), request)
        .expect("immutable synthetic launch request bytes");
    let request_digest = format!("sha256:{}", hex::encode(Sha256::digest(request)));
    let source = "a".repeat(64);
    let id = PgWindowsWitnessIdentity {
        job_id: job.clone(),
        attempt_id: attempt.clone(),
        launch_token_digest: input.launch_token_digest.clone(),
        request_digest: request_digest.clone(),
        launcher_image_digest: image,
    };
    let mut db = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    assert!(matches!(
        db.admit(&input).unwrap(),
        PgAdmissionOutcome::Created(_)
    ));
    allocate_fixture(&mut scratch, &input);
    let ver = db
        .commit_bundle_ready_pg(&PgBundleReady {
            attempt_id: attempt.clone(),
            expected_row_version: 0,
            bundle_digest: request_digest.clone(),
            observed_at_ms: input.created_at_ms + 1,
            expected_source_sha256: source.clone(),
        })
        .unwrap();
    assert_eq!(ver, 1);
    assert_eq!(
        db.mark_dispatch_issued_pg(
            &PgDispatchIssued {
                attempt_id: attempt.clone(),
                expected_row_version: ver,
                expected_bundle_digest: request_digest.clone(),
                observed_at_ms: input.created_at_ms + 2,
                expected_source_sha256: source.clone(),
            },
            None,
            None
        )
        .unwrap(),
        2
    );
    let exe = PathBuf::from(std::env::var("SystemRoot").unwrap_or_else(|_| "C:\\Windows".into()))
        .join("System32")
        .join("cmd.exe");
    assert!(exe.is_file());
    let stdout = bundle.path().join("launcher-piped-stdout.txt");
    let stderr = bundle.path().join("launcher-piped-stderr.txt");
    let argv = vec![
        "--runtime-bundle".into(),
        input.bundle_path.clone(),
        "--runtime-job-id".into(),
        job.clone(),
        "--runtime-attempt-id".into(),
        attempt.clone(),
        "--runtime-launch-token-digest".into(),
        input.launch_token_digest.clone(),
        "--runtime-request-digest".into(),
        request_digest.clone(),
        "--job-name".into(),
        input.unit_name.clone(),
        "--authority".into(),
        "limited".into(),
        "--timeout-ms".into(),
        "17000".into(),
        "--stdout-limit-bytes".into(),
        "4096".into(),
        "--stderr-limit-bytes".into(),
        "4096".into(),
        "--pg-terminal-peer-process-id".into(),
        if force_wrong_peer {
            std::process::id().saturating_add(1)
        } else {
            std::process::id()
        }
        .to_string(),
        "--executable".into(),
        exe.to_string_lossy().into_owned(),
        "--cwd".into(),
        input.bundle_path.clone(),
        "--".into(),
        "/c".into(),
        "echo".into(),
        "WINPG_TRUE_SINGLE_JOB_R50".into(),
    ];
    // Real original Windows process; parent owns the process identity.
    let mut child = Command::new(&launcher)
        .args(&argv)
        .stdout(Stdio::from(std::fs::File::create(stdout).unwrap()))
        .stderr(Stdio::from(std::fs::File::create(stderr).unwrap()))
        .spawn()
        .expect("original Win32 Launcher spawn");
    let pid = child.id();
    let handle = unsafe { OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, 0, pid) };
    assert!(
        !handle.is_null(),
        "original kernel process handle unavailable"
    );
    let blank = FILETIME {
        dwLowDateTime: 0,
        dwHighDateTime: 0,
    };
    let (mut birth, mut exit, mut kernel, mut user) = (blank, blank, blank, blank);
    let ok = unsafe { GetProcessTimes(handle, &mut birth, &mut exit, &mut kernel, &mut user) };
    unsafe {
        CloseHandle(handle);
    }
    assert_ne!(ok, 0, "original process birth FILETIME unavailable");
    let created = ((birth.dwHighDateTime as u64) << 32) | birth.dwLowDateTime as u64;
    assert!(created > 0);
    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_millis() as u64;
    // Parent alone publishes launch identity from the original OS PID and
    // creation FILETIME; Launcher is NOT passed --emit-launcher-start.
    let parent = serde_json::json!({
        "schemaVersion":1,"jobId":job,"attemptId":attempt,
        "launchTokenDigest":input.launch_token_digest,
        "requestDigest":request_digest,"jobName":input.unit_name,
        "launcherProcessId":pid,
        "launcherProcessCreationTimeFileTime":created,
        "launcherImageDigest":id.launcher_image_digest,
        "observedUnixMs":now
    });
    std::fs::write(
        bundle.path().join("windows-launcher-start.json"),
        serde_json::to_vec(&parent).unwrap(),
    )
    .unwrap();
    let deadline = Instant::now() + Duration::from_secs(35);
    let mut committed = false;
    let mut rejected_peer = false;
    while Instant::now() < deadline {
        match reconcile_windows_native_terminal(&mut db, bundle.path(), &id, &source, 2) {
            Ok(true) => {
                committed = true;
                break;
            }
            Ok(false) => std::thread::sleep(Duration::from_millis(50)),
            Err(e) if force_wrong_peer && e.contains("did not confirm client identity") => {
                rejected_peer = true;
                break;
            }
            Err(e) => panic!("native WindowsPG owner/journal/terminal: {e}"),
        }
    }
    let exit = child.wait().expect("native launcher process exit");
    if force_wrong_peer {
        assert!(
            rejected_peer,
            "wrong peer must fail its issuer-side Ready gate"
        );
        assert!(!committed);
        assert!(!exit.success(), "original Launcher must reject wrong peer");
        let journal_count:i64=db.client.query_one(
            "SELECT count(*) FROM job_events WHERE job_id=$1 AND event_type='WINDOWS_NATIVE_JOB_DRAIN_OBSERVED'",
            &[&job],
        ).unwrap().get(0);
        assert_eq!(
            journal_count, 0,
            "wrong peer may not record trusted PG native drain"
        );
        assert_eq!(scratch.count("artifacts"), 0);
        assert!(
            matches!(
                db.observe_job_readonly(&job,&source).unwrap(),
                PgJobReadback::Observed(snapshot)
                    if snapshot.resolution.is_none()
                       && snapshot.attempt_state=="starting"
                       && snapshot.reservation_state=="active"
            ),
            "wrong peer may not terminalize Job or release reservation"
        );
        let launcher_error = std::fs::read_to_string(bundle.path().join("launcher-error.json"))
            .expect("original launcher rejection receipt");
        assert!(launcher_error.contains("peer is not the admission-frozen Runtime process"));
        assert!(std::fs::read_to_string(bundle.path().join("stdout.log"))
            .unwrap()
            .contains("WINPG_TRUE_SINGLE_JOB_R50"));
        println!("WINPG_REAL_OS_WRONG_PEER_NO_PG_JOURNAL_TERMINAL=PASS");
        return;
    }
    assert!(
        committed,
        "native Windows PG must reach same original Attempt terminal"
    );
    assert!(exit.success(), "original Launcher did not exit0: {exit:?}");
    assert!(
        matches!(
            db.observe_job_readonly(&job,&source).unwrap(),
            PgJobReadback::Observed(snapshot)
                if snapshot.resolution.as_deref()==Some("succeeded")
                   && snapshot.attempt_state=="succeeded"
                   && snapshot.reservation_state=="released"
                   && snapshot.current_attempt_id.is_none()
        ),
        "real same PG Job terminal lacks verified readback"
    );
    let rows = db
        .client
        .query(
            "SELECT kind,relative_path,digest,byte_length FROM artifacts WHERE attempt_id=$1",
            &[&attempt],
        )
        .unwrap();
    assert_eq!(rows.len(), 3, "same Attempt must register three Artifacts");
    for row in rows {
        let path: String = row.get(1);
        let expected_digest: String = row.get(2);
        let length: i64 = row.get(3);
        let contents = std::fs::read(bundle.path().join(&path)).unwrap();
        assert_eq!(contents.len() as i64, length);
        assert_eq!(
            format!("sha256:{}", hex::encode(Sha256::digest(&contents))),
            expected_digest
        );
    }
    assert!(std::fs::read_to_string(bundle.path().join("stdout.log"))
        .unwrap()
        .contains("WINPG_TRUE_SINGLE_JOB_R50"));
    println!("WINPG_REAL_OS_SAME_PG_ATTEMPT_TERMINAL_ARTIFACT=PASS");
}
