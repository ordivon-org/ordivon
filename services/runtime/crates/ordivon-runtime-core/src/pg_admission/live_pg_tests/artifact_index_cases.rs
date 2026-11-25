//! Physical PG schema and operator migration contract. Never target installed PG.
use super::*;
use std::process::Command;

fn migrate(dsn: &str, schema: &str, source: &str) -> std::process::Output {
    Command::new("psql")
        .args([
            "-X",
            "-w",
            "--dbname",
            dsn,
            "--set",
            &format!("runtime_schema={schema}"),
            "--set",
            &format!("source_sha256={source}"),
            "--file",
            concat!(
                env!("CARGO_MANIFEST_DIR"),
                "/sql/pg_artifact_job_lookup_r1.sql"
            ),
        ])
        .output()
        .expect("native psql operator migration")
}
fn index_oid(s: &mut Scratch) -> Option<i64> {
    s.admin
        .query_one("SELECT to_regclass('idx_artifacts_job')::oid::bigint", &[])
        .unwrap()
        .get(0)
}
fn exact_index(s: &mut Scratch) -> bool {
    s.admin
        .query_one(
            "SELECT EXISTS(SELECT 1 FROM pg_index i JOIN pg_class c ON c.oid=i.indexrelid
          JOIN pg_class t ON t.oid=i.indrelid WHERE c.oid=to_regclass('idx_artifacts_job')
          AND t.oid=to_regclass('artifacts') AND i.indisvalid AND i.indisready AND i.indislive
          AND NOT i.indisunique AND i.indnkeyatts=1 AND i.indnatts=1
          AND i.indpred IS NULL AND i.indexprs IS NULL AND pg_get_indexdef(c.oid,1,true)='job_id')",
            &[],
        )
        .unwrap()
        .get(0)
}
fn assert_success(output: std::process::Output) {
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
}
#[test]
#[ignore = "requires explicit isolated PostgreSQL qualification and psql"]
fn pg18_artifact_job_index_fresh_and_online_migration() {
    let dsn = physical_pg_test_dsn();
    let mut s = Scratch::new(&dsn);
    assert!(
        exact_index(&mut s),
        "fresh schema must include the native lookup index"
    );
    s.admin
        .batch_execute("DROP INDEX idx_artifacts_job")
        .unwrap();
    let source = "a".repeat(64);
    assert!(
        !migrate(&dsn, &s.name, &source).status.success(),
        "non-authoritative source"
    );
    assert_eq!(index_oid(&mut s), None);
    s.qualify();
    assert!(
        !migrate(&dsn, &s.name, &"b".repeat(64)).status.success(),
        "foreign source"
    );
    assert_eq!(index_oid(&mut s), None);
    s.admin
        .execute(
            "UPDATE _stage_control SET source_sha256=$1 WHERE id='epoch'",
            &[&"0".repeat(64)],
        )
        .unwrap();
    assert!(
        !migrate(&dsn, &s.name, &source).status.success(),
        "stale epoch"
    );
    assert_eq!(index_oid(&mut s), None);
    s.qualify();
    let mut store = PgAdmissionStore::connect(&dsn, &s.name).unwrap();
    let input = payload(
        "index-fixture-key",
        "index-fixture-job",
        "index-fixture-ws",
        2,
    );
    store.admit(&input).unwrap();
    s.admin.execute("INSERT INTO artifacts(artifact_id,job_id,attempt_id,kind,relative_path,digest)
      SELECT 'index-artifact-'||i,$1,$2,'stdout','part-'||i,'sha256:fixture' FROM generate_series(1,3)i",
      &[&input.job_id,&input.attempt_id]).unwrap();
    let before: Vec<String> = s
        .admin
        .query(
            "SELECT artifact_id FROM artifacts WHERE job_id=$1 ORDER BY artifact_id",
            &[&input.job_id],
        )
        .unwrap()
        .iter()
        .map(|r| r.get(0))
        .collect();
    assert_success(migrate(&dsn, &s.name, &source));
    let oid = index_oid(&mut s).unwrap();
    assert!(exact_index(&mut s));
    assert_success(migrate(&dsn, &s.name, &source));
    assert_eq!(index_oid(&mut s), Some(oid), "exact retry is no-op");
    let after: Vec<String> = s
        .admin
        .query(
            "SELECT artifact_id FROM artifacts WHERE job_id=$1 ORDER BY artifact_id",
            &[&input.job_id],
        )
        .unwrap()
        .iter()
        .map(|r| r.get(0))
        .collect();
    assert_eq!(before, after);
    assert_eq!(after.len(), 3);
    s.admin
        .batch_execute(
            "DROP INDEX idx_artifacts_job; CREATE INDEX idx_artifacts_job ON artifacts(kind)",
        )
        .unwrap();
    let wrong = index_oid(&mut s);
    assert!(
        !migrate(&dsn, &s.name, &source).status.success(),
        "wrong same-name index must not be accepted or replaced"
    );
    assert_eq!(index_oid(&mut s), wrong);
    s.admin.batch_execute("DROP INDEX idx_artifacts_job; CREATE INDEX idx_artifacts_job ON artifacts(job_id) WHERE truncated").unwrap();
    assert!(
        !migrate(&dsn, &s.name, &source).status.success(),
        "partial same-name index"
    );
    s.admin
        .batch_execute("DROP INDEX idx_artifacts_job")
        .unwrap();
    // Same column but non-default operator class is not the contracted index.
    s.admin
        .batch_execute("CREATE INDEX idx_artifacts_job ON artifacts(job_id text_pattern_ops)")
        .unwrap();
    assert!(
        !migrate(&dsn, &s.name, &source).status.success(),
        "wrong operator class"
    );
    s.admin.batch_execute("DROP INDEX idx_artifacts_job; CREATE INDEX idx_artifacts_job ON artifacts(job_id) INCLUDE(kind)").unwrap();
    assert!(
        !migrate(&dsn, &s.name, &source).status.success(),
        "uncontracted INCLUDE"
    );
    s.admin
        .batch_execute("DROP INDEX idx_artifacts_job")
        .unwrap();
    // PostgreSQL leaves a real invalid index when a concurrent unique build
    // encounters duplicates. The migration must not drop or bless it.
    assert!(s
        .admin
        .batch_execute("CREATE UNIQUE INDEX CONCURRENTLY idx_artifacts_job ON artifacts(job_id)")
        .is_err());
    let invalid = index_oid(&mut s);
    assert!(invalid.is_some() && !exact_index(&mut s));
    assert!(
        !migrate(&dsn, &s.name, &source).status.success(),
        "invalid index"
    );
    assert_eq!(index_oid(&mut s), invalid);
    assert!(
        !migrate(&dsn, "public", &source).status.success(),
        "unscoped schema"
    );
    assert!(
        !migrate(&dsn, "missing_runtime_schema", &source)
            .status
            .success(),
        "missing schema"
    );
    assert_eq!(s.count("artifacts"), 3);
}

#[test]
#[ignore = "requires explicit isolated PostgreSQL qualification and psql"]
fn pg18_artifact_job_index_interrupted_concurrent_build_remains_inconclusive() {
    use std::process::Stdio;
    use std::time::{Duration, Instant};
    let dsn = physical_pg_test_dsn();
    let mut s = Scratch::new(&dsn);
    s.qualify();
    s.admin
        .batch_execute("DROP INDEX idx_artifacts_job")
        .unwrap();
    let source = "a".repeat(64);
    let mut store = PgAdmissionStore::connect(&dsn, &s.name).unwrap();
    let input = payload(
        "interrupt-index-key",
        "interrupt-index-job",
        "interrupt-index-ws",
        2,
    );
    store.admit(&input).unwrap();
    s.admin.execute("INSERT INTO artifacts(artifact_id,job_id,attempt_id) VALUES('interrupt-artifact',$1,$2)", &[&input.job_id,&input.attempt_id]).unwrap();
    let mut writer = Client::connect(&dsn, NoTls).unwrap();
    writer
        .query_one("SELECT set_config('search_path',$1,false)", &[&s.name])
        .unwrap();
    let mut writing = writer.transaction().unwrap();
    writing
        .execute(
            "UPDATE artifacts SET byte_length=1 WHERE artifact_id='interrupt-artifact'",
            &[],
        )
        .unwrap();
    let app = format!("index-test-{}", s.name);
    let child = Command::new("psql")
        .args([
            "-X",
            "-w",
            "--dbname",
            &dsn,
            "--set",
            &format!("runtime_schema={}", s.name),
            "--set",
            &format!("source_sha256={source}"),
            "--file",
            concat!(
                env!("CARGO_MANIFEST_DIR"),
                "/sql/pg_artifact_job_lookup_r1.sql"
            ),
        ])
        .env("PGAPPNAME", &app)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    // An open writer forces CREATE INDEX CONCURRENTLY to wait after its
    // first catalog transaction. Observe the real invalid native index.
    let deadline = Instant::now() + Duration::from_secs(8);
    let invalid = loop {
        let oid = index_oid(&mut s);
        if oid.is_some() && !exact_index(&mut s) {
            break oid;
        }
        if Instant::now() >= deadline {
            break None;
        }
        std::thread::sleep(Duration::from_millis(25));
    };
    let cancelled: bool=s.admin.query_one(
        "SELECT COALESCE(bool_or(pg_cancel_backend(pid)),false) FROM pg_stat_activity WHERE application_name=$1",
        &[&app]).unwrap().get(0);
    writing.rollback().unwrap();
    let output = child.wait_with_output().unwrap();
    assert!(
        invalid.is_some() && cancelled && !output.status.success(),
        "expected real interrupted concurrent build: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert_eq!(index_oid(&mut s), invalid);
    assert!(!exact_index(&mut s));
    assert!(!migrate(&dsn, &s.name, &source).status.success());
    assert_eq!(
        index_oid(&mut s),
        invalid,
        "operator must explicitly resolve incomplete build"
    );
    assert_eq!(s.count("artifacts"), 1);
    // Only this private fixture is deliberately repaired. No live DROP.
    s.admin
        .batch_execute("DROP INDEX idx_artifacts_job")
        .unwrap();
    assert_success(migrate(&dsn, &s.name, &source));
    assert!(exact_index(&mut s));
}
