//! Pure PG behavioral contracts; no source-layout pinning.
use super::*;
#[test]
fn physical_epoch_fingerprint_is_domain_and_timeline_bound() {
    let source = "a".repeat(64);
    let previous = pg_writer_epoch_digest(&source, "77123", 1);
    assert_eq!(previous.len(), 64);
    assert_ne!(previous, pg_writer_epoch_digest(&source, "77123", 2));
    assert_ne!(previous, pg_writer_epoch_digest(&source, "77124", 1));
    assert_ne!(
        previous,
        pg_writer_epoch_digest(&"b".repeat(64), "77123", 1)
    );
    assert_eq!(previous, pg_writer_epoch_digest(&source, "77123", 1));
}

#[test]
fn schema_boundary_fails_closed() {
    for name in ["", "public", "pg_catalog", "_secret", "x;DROP SCHEMA"] {
        assert!(!exact_schema(name), "unsafe {name}");
    }
    assert!(exact_schema("runtime_pg_qualified_r1"));
}
#[test]
fn non_object_durable_json_is_rejected_before_postgres_effects() {
    // RuntimeExecutionPlan and Workspace snapshots are records. Parsing as
    // arbitrary JSON Value would accept a scalar/array that a consumer
    // cannot decode as a valid durable state object.
    let qualified = PgAdmissionInput {
        job_id: "job".into(),
        attempt_id: "attempt".into(),
        reservation_id: "reservation".into(),
        principal: "principal".into(),
        client_request_id: "request".into(),
        request_digest: "sha256:r".into(),
        operation_digest: "sha256:o".into(),
        workspace_id: "ws".into(),
        workspace_snapshot_json: "{}".into(),
        execution_plan_json: "{}".into(),
        execution_plan_digest: "sha256:plan".into(),
        launch_token_digest: "sha256:l".into(),
        bundle_path: "/tmp/test".into(),
        unit_name: "unit".into(),
        global_limit: 1,
        created_at_ms: 1,
        expected_source_sha256: "a".repeat(64),
    };
    assert!(qualified.validate().is_ok(), "fixture must be admitted");
    for raw in ["null", "true", "false", "[]", "42", "\"text\""] {
        let mut invalid_snapshot = qualified.clone();
        invalid_snapshot.workspace_snapshot_json = raw.into();
        assert!(
            matches!(
                invalid_snapshot.validate(),
                Err(PgAdmissionError::InvalidInput)
            ),
            "workspace_snapshot_json accepted non-object {raw}"
        );
        let mut invalid_plan = qualified.clone();
        invalid_plan.execution_plan_json = raw.into();
        assert!(
            matches!(invalid_plan.validate(), Err(PgAdmissionError::InvalidInput)),
            "execution_plan_json accepted non-object {raw}"
        );
    }
}

#[test]
fn duplicate_nested_json_keys_are_rejected_before_durable_pg_effects() {
    let qualified = PgAdmissionInput {
        job_id: "job".into(),
        attempt_id: "attempt".into(),
        reservation_id: "reservation".into(),
        principal: "principal".into(),
        client_request_id: "request".into(),
        request_digest: "sha256:r".into(),
        operation_digest: "sha256:o".into(),
        workspace_id: "ws".into(),
        workspace_snapshot_json: r#"{"snapshot":{"revision":1}}"#.into(),
        execution_plan_json: r#"{"plan":{"timeoutMs":1000}}"#.into(),
        execution_plan_digest: "sha256:plan".into(),
        launch_token_digest: "sha256:l".into(),
        bundle_path: "/tmp/test".into(),
        unit_name: "unit".into(),
        global_limit: 1,
        created_at_ms: 1,
        expected_source_sha256: "a".repeat(64),
    };
    assert!(
        qualified.validate().is_ok(),
        "ordinary nested objects qualify"
    );
    for raw in [
        r#"{"revision":1,"revision":2}"#,
        r#"{"snapshot":{"revision":1,"revision":2}}"#,
        r#"{"snapshots":[{"revision":1,"revision":2}]}"#,
        r#"{"\u0061":1,"a":2}"#,
    ] {
        let mut invalid_snapshot = qualified.clone();
        invalid_snapshot.workspace_snapshot_json = raw.into();
        assert!(
            matches!(
                invalid_snapshot.validate(),
                Err(PgAdmissionError::InvalidInput)
            ),
            "workspace_snapshot_json admitted ambiguous JSON {raw}"
        );
        let mut invalid_plan = qualified.clone();
        invalid_plan.execution_plan_json = raw.into();
        assert!(
            matches!(invalid_plan.validate(), Err(PgAdmissionError::InvalidInput)),
            "execution_plan_json admitted ambiguous JSON {raw}"
        );
    }
}

#[test]
fn source_identity_must_be_present() {
    let i = PgAdmissionInput {
        job_id: "j".into(),
        attempt_id: "a".into(),
        reservation_id: "r".into(),
        principal: "p".into(),
        client_request_id: "c".into(),
        request_digest: "sha256:r".into(),
        operation_digest: "sha256:o".into(),
        workspace_id: "ws".into(),
        workspace_snapshot_json: "{}".into(),
        execution_plan_json: "{}".into(),
        execution_plan_digest: "sha256:plan".into(),
        launch_token_digest: "sha256:l".into(),
        bundle_path: "/tmp/test".into(),
        unit_name: "unit".into(),
        global_limit: 1,
        created_at_ms: 1,
        expected_source_sha256: String::new(),
    };
    assert!(matches!(i.validate(), Err(PgAdmissionError::InvalidInput)));
}
