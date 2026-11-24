//! Test original sealed Artifact and UTF-8 consumer behavior, not source file layout.
use super::*;

#[test]
fn pg_artifact_integrity_mismatch_is_not_a_registry_failure() {
    let committed = b"initial sealed receipt";
    let digest = universal::sha256_bytes(committed);
    require_pg_artifact_identity(committed, committed.len() as i64, &digest).unwrap();
    for (bytes, expected_length) in [
        (
            b"initial sealed receipt".as_slice(),
            committed.len() as i64 + 1,
        ),
        (b"initial sealed receipT".as_slice(), committed.len() as i64),
    ] {
        let err = require_pg_artifact_identity(bytes, expected_length, &digest).unwrap_err();
        assert_eq!(err.code, RuntimeErrorCode::ArtifactIdentityConflict);
        assert_eq!(err.field.as_deref(), Some("artifactId"));
        assert!(!err.retryable);
    }
}

#[test]
fn pg_artifact_page_rejects_zero_progress_in_the_middle_of_utf8() {
    let source = "A中文B🙂C\n";
    for (offset, max_bytes) in [(1, 1), (1, 2), (8, 1), (8, 2), (8, 3)] {
        let failure = artifact_utf8_window(source, offset, max_bytes).unwrap_err();
        assert_eq!(failure.field.as_deref(), Some("maxBytes"));
    }
}

#[test]
fn pg_artifact_page_preserves_valid_byte_cursor_boundaries() {
    let source = "A中文B🙂C\n";
    for (offset, max_bytes, expected) in [
        (0, 5, (0, 4)),
        (4, 4, (4, 8)),
        (8, 4, (8, 12)),
        (12, 2, (12, 14)),
        (14, 1, (14, 14)),
    ] {
        let (begin, end) = artifact_utf8_window(source, offset, max_bytes).unwrap();
        assert_eq!((begin, end), expected);
    }
    let failure = artifact_utf8_window(source, 2, 4).unwrap_err();
    assert_eq!(failure.field.as_deref(), Some("offset"));
}

/// An authorized Job's registration cannot redirect either read path into a
/// different Job's Attempt, even when the retained bytes match the digest.
#[test]
#[ignore = "requires explicitly disposable Unix-only ORDIVON_PG_TEST_DSN"]
fn pg18_artifact_readers_reject_cross_job_attempt_origin() {
    let dsn = std::env::var("ORDIVON_PG_TEST_DSN").expect("disposable PG DSN");
    let mut admin = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
    assert!(
        admin
            .query_one(
                "SELECT inet_server_addr() IS NULL AND current_setting('listen_addresses') = ''",
                &[],
            )
            .unwrap()
            .get::<_, bool>(0)
    );
    let id = Uuid::now_v7().simple().to_string();
    let schema = format!("test_artifact_{id}");
    let role = format!("test_artifact_app_{id}");
    struct Cleanup<'a> {
        dsn: &'a str,
        schema: &'a str,
        role: &'a str,
    }
    impl Drop for Cleanup<'_> {
        fn drop(&mut self) {
            if let Ok(mut db) = postgres::Client::connect(self.dsn, postgres::NoTls) {
                let _ = db.batch_execute(&format!(
                    "DROP SCHEMA IF EXISTS {} CASCADE; DROP ROLE IF EXISTS {}",
                    self.schema, self.role
                ));
            }
        }
    }
    let _cleanup = Cleanup {
        dsn: &dsn,
        schema: &schema,
        role: &role,
    };
    admin
        .batch_execute(&format!(
            "CREATE ROLE {role} LOGIN; CREATE SCHEMA {schema}; SET search_path TO {schema}"
        ))
        .unwrap();
    admin
        .batch_execute(include_str!(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/sql/pg_fresh_epoch.sql"
        )))
        .unwrap();
    let source = "a".repeat(64);
    let epoch = admin
        .query_one(
            "SELECT (SELECT system_identifier::text FROM pg_control_system()),
                (SELECT timeline_id FROM pg_control_checkpoint())",
            &[],
        )
        .unwrap();
    let epoch_digest = crate::pg_admission::pg_writer_epoch_digest(
        &source,
        &epoch.get::<_, String>(0),
        epoch.get::<_, i32>(1),
    );
    admin
        .execute(
            "INSERT INTO _stage_control(id,state,source_sha256,promotion_allowed)
         VALUES('source','QUALIFIED_WRITER',$1,true),('epoch','QUALIFIED_EPOCH',$2,true)",
            &[&source, &epoch_digest],
        )
        .unwrap();
    admin
        .batch_execute(&format!(
            "GRANT USAGE ON SCHEMA {schema} TO {role};
         GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA {schema} TO {role};
         REVOKE ALL ON TABLE _stage_control FROM {role};
         GRANT SELECT,UPDATE(id) ON TABLE _stage_control TO {role};
         GRANT pg_monitor TO {role};"
        ))
        .unwrap();

    let root = tempfile::TempDir::new().unwrap();
    let bundle_a = root.path().join("attempt-a");
    let bundle_b = root.path().join("attempt-b");
    fs::create_dir(&bundle_a).unwrap();
    fs::create_dir(&bundle_b).unwrap();
    let bytes = b"synthetic exact bytes";
    fs::write(bundle_a.join("out"), bytes).unwrap();
    fs::write(bundle_b.join("out"), bytes).unwrap();
    let digest = universal::sha256_bytes(bytes);
    admin.batch_execute(
        "INSERT INTO jobs(job_id,principal,client_request_id,request_digest,operation_digest,
                          workspace_id,workspace_snapshot_json,execution_plan_json,execution_plan_digest,
                          created_at_ms,desired_state)
         VALUES ('jobA','principalA','keyA','a','a','wsA','{}','{}','a',1,'run'),
                ('jobB','principalB','keyB','b','b','wsB','{}','{}','b',1,'run')"
    ).unwrap();
    admin
        .execute(
            "INSERT INTO attempts(attempt_id,job_id,attempt_number,state,termination_intent,
                              launch_token_digest,bundle_path,unit_name,created_at_ms)
         VALUES ('attemptA','jobA',1,'succeeded','none','a',$1,'unitA',1),
                ('attemptB','jobB',1,'succeeded','none','b',$2,'unitB',1)",
            &[&bundle_a.to_str().unwrap(), &bundle_b.to_str().unwrap()],
        )
        .unwrap();
    admin.execute(
        "INSERT INTO artifacts(artifact_id,job_id,attempt_id,kind,relative_path,digest,media_type,byte_length)
         VALUES ('artifactA','jobA','attemptA','stdout','out',$1,'text/plain',$2),
                ('artifactB','jobB','attemptB','stdout','out',$1,'text/plain',$2),
                ('foreign','jobA','attemptB','other','out',$1,'text/plain',$2)",
        &[&digest, &(bytes.len() as i64)],
    ).unwrap();
    let runtime = PgRuntime::new(PgRuntimeConfig {
        dsn: format!("{dsn} user={role}"),
        schema: schema.clone(),
        source_sha256: source,
        harness_issuer_schema: None,
        harness_dispatch_issuer: None,
        executor: UniversalExecutorConfig {
            store_root: root.path().join("store"),
            workspace_root: None,
            workspace_uid: None,
            workspace_gid: None,
            runner_path: Some("/usr/bin/true".into()),
            allowed_executable_roots: vec!["/usr/bin".into()],
            max_runtime_ms: 10000,
            max_output_bytes: 1024 * 1024,
        },
        workspace_headroom: vec![],
    })
    .unwrap();
    let read_text = |principal: &str, job: &str, artifact: &str| {
        runtime.read_artifact(
            principal,
            &ArtifactReadRequest {
                schema_version: 1,
                job_id: job.into(),
                artifact_id: artifact.into(),
                offset: 0,
                max_bytes: 128,
            },
        )
    };
    let read_bytes = |principal: &str, job: &str, artifact: &str| {
        runtime.read_artifact_content(
            principal,
            &ArtifactContentRequest {
                schema_version: 1,
                job_id: job.into(),
                artifact_id: artifact.into(),
                max_bytes: 128,
            },
        )
    };
    assert_eq!(
        read_text("principalA", "jobA", "artifactA")
            .unwrap()
            .content
            .as_bytes(),
        bytes
    );
    assert_eq!(
        read_bytes("principalB", "jobB", "artifactB").unwrap().bytes,
        bytes
    );
    assert_eq!(
        read_bytes("principalA", "jobB", "artifactB")
            .unwrap_err()
            .code,
        RuntimeErrorCode::JobNotFound
    );
    assert_eq!(
        read_text("principalA", "jobA", "absent").unwrap_err().code,
        RuntimeErrorCode::ArtifactNotFound
    );
    let text = read_text("principalA", "jobA", "foreign");
    let content = read_bytes("principalA", "jobA", "foreign");
    assert!(
        text.is_err() && content.is_err(),
        "cross-Job Attempt origin accepted: text={text:?}, content={content:?}"
    );
    for error in [text.unwrap_err(), content.unwrap_err()] {
        assert_eq!(error.code, RuntimeErrorCode::ArtifactIdentityConflict);
        assert_eq!(error.field.as_deref(), Some("artifactId"));
        assert!(!error.retryable);
    }
}
