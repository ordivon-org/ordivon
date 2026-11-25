//! Independent relational oracle against the native PostgreSQL readback.
use super::*;

#[test]
#[ignore = "requires explicit isolated PostgreSQL qualification"]
fn pg18_projection_inventory_owner_matrix() {
    let dsn = physical_pg_test_dsn();
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    let target = payload(
        "matrix-target-req",
        "matrix-target-job",
        "matrix-target-ws",
        2,
    );
    let foreign = payload(
        "matrix-foreign-req",
        "matrix-foreign-job",
        "matrix-foreign-ws",
        2,
    );
    store.admit(&target).unwrap();
    store.admit(&foreign).unwrap();
    let canonical = PgArtifactRegistration {
        artifact_id: "matrix-canonical".into(),
        kind: "stdout".into(),
        relative_path: "sealed-stdout.log".into(),
        digest: format!("sha256:{}", "a".repeat(64)),
        media_type: "text/plain".into(),
        byte_length: 12,
        truncated: false,
        created_at_ms: 1234568,
    };
    store
        .commit_terminal_with_artifacts(
            &PgTerminalNoArtifacts {
                attempt_id: target.attempt_id.clone(),
                expected_row_version: 0,
                terminal_state: "failed".into(),
                result_digest: "sha256:matrix-result".into(),
                reason_code: "MATRIX".into(),
                exit_code: Some(7),
                finished_at_ms: 1234569,
                expected_source_sha256: target.expected_source_sha256.clone(),
            },
            std::slice::from_ref(&canonical),
        )
        .unwrap();
    let historical = "matrix-historical-attempt";
    scratch
        .admin
        .execute(
            "UPDATE attempts SET attempt_number=2 WHERE attempt_id=$1",
            &[&target.attempt_id],
        )
        .unwrap();
    scratch.admin.execute(
        "INSERT INTO attempts(attempt_id,job_id,attempt_number,state,termination_intent,launch_token_digest,bundle_path,unit_name,created_at_ms,row_version,result_digest,finished_at_ms)
         SELECT $2,job_id,1,state,termination_intent,launch_token_digest,bundle_path,$2,created_at_ms,row_version,result_digest,finished_at_ms FROM attempts WHERE attempt_id=$1",
        &[&target.attempt_id, &historical],
    ).unwrap();
    scratch.admin.execute(
        "INSERT INTO concurrency_reservations(reservation_id,attempt_id,global_limit,state,acquired_at_ms,state_observed_at_ms,released_at_ms,release_reason)
         SELECT $2,$2,global_limit,state,acquired_at_ms,state_observed_at_ms,released_at_ms,release_reason FROM concurrency_reservations WHERE attempt_id=$1",
        &[&target.attempt_id,&historical],
    ).unwrap();
    let expected_events = scratch.count("job_events");
    let initial = store
        .observe_job_projection_readonly(&target.job_id, &target.expected_source_sha256)
        .unwrap()
        .unwrap();
    assert_eq!(initial.exit_code, Some(7));
    assert_eq!(initial.artifacts.len(), 1);
    assert_eq!(initial.artifacts[0].registration, canonical);
    // Independent truth table: selected-current extra registration breaks
    // the terminal manifest; historical same-Job metadata is legitimate;
    // either direction of foreign ownership is a contradiction, unrelated
    // foreign rows must not change this Job.
    for (name, job, attempt, expected_count) in [
        (
            "selected extra",
            target.job_id.as_str(),
            target.attempt_id.as_str(),
            None,
        ),
        (
            "same-job history",
            target.job_id.as_str(),
            historical,
            Some(2),
        ),
        (
            "foreign attempt",
            target.job_id.as_str(),
            foreign.attempt_id.as_str(),
            None,
        ),
        (
            "foreign job selected",
            foreign.job_id.as_str(),
            target.attempt_id.as_str(),
            None,
        ),
        (
            "foreign job historical",
            foreign.job_id.as_str(),
            historical,
            None,
        ),
        (
            "unrelated foreign",
            foreign.job_id.as_str(),
            foreign.attempt_id.as_str(),
            Some(1),
        ),
    ] {
        assert_eq!(scratch.admin.execute(
            "INSERT INTO artifacts(artifact_id,job_id,attempt_id,kind,relative_path,digest,media_type,byte_length,truncated,created_at_ms)
             VALUES('matrix-extra',$1,$2,'execution_result','extra.json',$3,'application/json',1,false,1234570)",
            &[&job,&attempt,&format!("sha256:{}", "b".repeat(64))],
        ).unwrap(),1);
        let observed = store
            .observe_job_projection_readonly(&target.job_id, &target.expected_source_sha256)
            .unwrap();
        assert_eq!(
            scratch
                .admin
                .execute(
                    "DELETE FROM artifacts WHERE artifact_id='matrix-extra'",
                    &[]
                )
                .unwrap(),
            1
        );
        assert_eq!(
            observed.as_ref().map(|r| r.artifacts.len()),
            expected_count,
            "{name}"
        );
        if let Some(observed) = observed {
            assert_eq!(observed.snapshot.attempt_id, target.attempt_id, "{name}");
            assert_eq!(observed.exit_code, Some(7), "{name}");
            let canonical_row = observed
                .artifacts
                .iter()
                .find(|a| a.registration.artifact_id == canonical.artifact_id)
                .unwrap();
            assert_eq!(canonical_row.attempt_id, target.attempt_id, "{name}");
            assert_eq!(canonical_row.registration, canonical, "{name}");
            if expected_count == Some(2) {
                let extra = observed
                    .artifacts
                    .iter()
                    .find(|a| a.registration.artifact_id == "matrix-extra")
                    .unwrap();
                assert_eq!(extra.attempt_id, historical, "{name}");
            }
        }
        assert_eq!(
            scratch.count("job_events"),
            expected_events,
            "{name}: readback must be effect-free"
        );
    }
}
