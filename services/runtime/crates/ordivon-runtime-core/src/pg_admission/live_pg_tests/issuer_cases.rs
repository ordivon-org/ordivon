//! issuer cases: native PG18 behavior tests.
use super::*;

/// The same original PG issue cut must remain current at the later
/// DISPATCH_ISSUED commit. Uses two actual PG connections and an isolated
/// issuer SQL fixture, not a simulated in-memory flag or a native ACK.
#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_harness_issuer_current_at_dispatch_after_admission() {
    fn encoded(value: &serde_json::Value) -> (String, Vec<u8>) {
        let bytes = serde_json::to_vec(value).unwrap();
        (
            format!("sha256:{}", hex::encode(Sha256::digest(&bytes))),
            bytes,
        )
    }
    let dsn = physical_pg_test_dsn();
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    scratch
        .admin
        .batch_execute(
            "CREATE TABLE issuer_cut_fixture (
                run_id text NOT NULL, generation bigint NOT NULL,
                fence_digest text NOT NULL, live boolean NOT NULL,
                payload_digest text NOT NULL, payload_raw bytea NOT NULL,
                fence_raw bytea NOT NULL, intent_digest text NOT NULL,
                intent_raw bytea NOT NULL
            );
            CREATE FUNCTION harness_current_dispatch_cut(text,bigint,text)
            RETURNS TABLE(
                event_kind text,payload_digest text,payload_kind text,
                payload_size bigint,payload_raw bytea,
                fence_kind text,fence_size bigint,fence_raw bytea,
                intent_object_digest text,intent_kind text,intent_len bigint,
                intent_raw bytea
            ) LANGUAGE SQL AS $issuer$
                SELECT 'harness.tool-step-prepared'::text,
                       f.payload_digest, 'ordivon.harness-run-event-payload'::text,
                       octet_length(f.payload_raw)::bigint, f.payload_raw,
                       'harness-dispatch-fence'::text,
                       octet_length(f.fence_raw)::bigint, f.fence_raw,
                       f.intent_digest, 'harness-tool-step-intent'::text,
                       octet_length(f.intent_raw)::bigint, f.intent_raw
                  FROM issuer_cut_fixture f
                 WHERE f.run_id=$1 AND f.generation=$2
                   AND f.fence_digest=$3 AND f.live
            $issuer$;",
        )
        .unwrap();

    let mut harness = payload("original-tool", "original-harness-job", "ws-harness", 2);
    harness.principal = "original-harness-principal".into();
    let run_id = "harness-run:dispatch-current-pg18";
    let fence_id = "harness-dispatch-fence:dispatch-current-pg18";
    let other_ref = serde_json::json!({
        "namespace":"ordivon.harness","type":"harness_run","id":run_id
    });
    let (intent_digest, intent_raw) = encoded(&serde_json::json!({
        "schemaVersion":1,"kind":"ordivon.harness-tool-step-intent",
        "harnessRunId":run_id,"runtimeOperation":"workspace.exec",
        "runtimeArgumentsDigest":format!("sha256:{}", "a".repeat(64)),
        "clientRequestId":harness.client_request_id
    }));
    let (fence_digest, fence_raw) = encoded(&serde_json::json!({
        "schemaVersion":2,"kind":"ordivon.harness-dispatch-fence",
        "fenceId":fence_id,"harnessRunId":run_id,"runRevision":1,
        "clientRequestId":harness.client_request_id,
        "runtimeOperation":"workspace.exec","intentDigest":intent_digest,
        "issuedAtMs":0_i64,"expiresAtMs":32_503_680_000_000_i64
    }));
    let fence_ref = serde_json::json!({
        "namespace":"ordivon.harness","type":"dispatch_fence",
        "id":fence_id,"digest":fence_digest,"generation":"1"
    });
    let (physical_digest, _) = encoded(&serde_json::json!({
        "workspaceId":harness.workspace_id,
        "executable":"/usr/bin/echo","args":["harmless"],
        "cwdRelative":".","env":{},
        "timeoutMs":1000,"stdoutLimitBytes":1024,"stderrLimitBytes":1024,
        "foreignReferences":[other_ref.clone()]
    }));
    let (payload_digest, payload_raw) = encoded(&serde_json::json!({
        "schemaVersion":1,"kind":"ordivon.harness-run-event-payload",
        "eventKind":"harness.tool-step-prepared",
        "data":{
            "dispatchFenceDigest":fence_digest,
            "dispatchFenceObjectDigest":fence_digest,
            "toolStepIntentDigest":intent_digest,
            "toolStepIntentObjectDigest":intent_digest,
            "physicalExecutionDigest":physical_digest
        }
    }));
    harness.execution_plan_json = serde_json::json!({
        "workspaceId":harness.workspace_id,"workspacePath":"/tmp/pg-issuer-fixture",
        "cwd":"/tmp/pg-issuer-fixture",
        "executable":"/usr/bin/echo","args":["harmless"],"env":{},
        "timeoutMs":1000,"stdoutLimitBytes":1024,"stderrLimitBytes":1024,
        "executionProfile":"trusted_local","executionTarget":"local_linux",
        "foreignReferences":[other_ref,fence_ref]
    })
    .to_string();

    scratch
        .admin
        .execute(
            "INSERT INTO issuer_cut_fixture VALUES($1,$2,$3,true,$4,$5,$6,$7,$8)",
            &[
                &run_id,
                &1_i64,
                &fence_digest,
                &payload_digest,
                &payload_raw,
                &fence_raw,
                &intent_digest,
                &intent_raw,
            ],
        )
        .unwrap();
    // An individually digest-valid but different Tool Intent is not the
    // Intent committed by the original Fence. Keep the original semantic
    // digest and update only the object reference and its valid CAS bytes.
    let mut substituted_intent: serde_json::Value = serde_json::from_slice(&intent_raw).unwrap();
    substituted_intent["runtimeArgumentsDigest"] =
        serde_json::Value::String(format!("sha256:{}", "d".repeat(64)));
    let (substituted_intent_digest, substituted_intent_raw) = encoded(&substituted_intent);
    let mut substituted_payload: serde_json::Value = serde_json::from_slice(&payload_raw).unwrap();
    substituted_payload["data"]["toolStepIntentObjectDigest"] =
        serde_json::Value::String(substituted_intent_digest.clone());
    let (substituted_payload_digest, substituted_payload_raw) = encoded(&substituted_payload);
    let issuer_schema = scratch.name.clone();
    let set_objects = |client: &mut Client, wrong: bool| {
        let (pd, pr, id, ir) = if wrong {
            (
                &substituted_payload_digest,
                &substituted_payload_raw,
                &substituted_intent_digest,
                &substituted_intent_raw,
            )
        } else {
            (&payload_digest, &payload_raw, &intent_digest, &intent_raw)
        };
        client
            .execute(
                &format!(
                    "UPDATE \"{}\".issuer_cut_fixture SET payload_digest=$1,payload_raw=$2,intent_digest=$3,intent_raw=$4 WHERE run_id=$5",
                    issuer_schema
                ),
                &[pd, pr, id, ir, &run_id],
            )
            .unwrap()
    };
    let mut source = Client::connect(&dsn, NoTls).unwrap();
    assert_eq!(set_objects(&mut source, true), 1);
    let mut db = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    assert!(
        matches!(
            db.admit_with_workspace_guard(&harness, &|| Ok(()), Some(&scratch.name)),
            Err(PgAdmissionError::IssuerNotCurrent)
        ),
        "a valid CAS object cannot substitute for the Fence's semantic Intent"
    );
    assert_eq!(scratch.count("jobs"), 0);
    assert_eq!(scratch.count("attempts"), 0);
    assert_eq!(set_objects(&mut source, false), 1);
    assert_eq!(
        db.admit_with_workspace_guard(&harness, &|| Ok(()), Some(&scratch.name),)
            .unwrap(),
        PgAdmissionOutcome::Created(harness.job_id.clone())
    );
    allocate_fixture(&mut scratch, &harness);
    let digest = format!("sha256:{}", "b".repeat(64));
    db.commit_bundle_ready_pg(&PgBundleReady {
        attempt_id: harness.attempt_id.clone(),
        expected_row_version: 0,
        bundle_digest: digest.clone(),
        observed_at_ms: harness.created_at_ms + 1,
        expected_source_sha256: harness.expected_source_sha256.clone(),
    })
    .unwrap();
    let issued = PgDispatchIssued {
        attempt_id: harness.attempt_id.clone(),
        expected_row_version: 1,
        expected_bundle_digest: digest,
        observed_at_ms: harness.created_at_ms + 2,
        expected_source_sha256: harness.expected_source_sha256.clone(),
    };

    // An independent source writer revokes the original Run after admission,
    // before the durable dispatch transaction commits.
    assert_eq!(set_objects(&mut source, true), 1);
    assert!(
        matches!(
            db.mark_dispatch_issued_pg(
                &issued,
                Some(&scratch.name),
                Some("original-harness-principal"),
            ),
            Err(PgAdmissionError::IssuerNotCurrent)
        ),
        "the later dispatch must reject a substituted current Intent"
    );
    assert_eq!(
        scratch.count("job_events"),
        4,
        "no dispatch event on mismatched Intent"
    );
    assert_eq!(set_objects(&mut source, false), 1);
    source
        .execute(
            &format!(
                "UPDATE \"{}\".issuer_cut_fixture SET live=false WHERE run_id=$1",
                scratch.name
            ),
            &[&run_id],
        )
        .unwrap();
    assert!(matches!(
        db.mark_dispatch_issued_pg(
            &issued,
            Some(&scratch.name),
            Some("original-harness-principal"),
        ),
        Err(PgAdmissionError::IssuerNotCurrent)
    ));
    let state: String = scratch
        .admin
        .query_one(
            "SELECT state FROM attempts WHERE attempt_id=$1",
            &[&harness.attempt_id],
        )
        .unwrap()
        .get(0);
    assert_eq!(
        state, "accepted",
        "failed currentness must roll back PG dispatch"
    );
    assert_eq!(scratch.count("job_events"), 4, "no durable dispatch event");

    // The same original source resumes authority, and dispatch is admitted
    // once. This positive is PG-only; no OS Unit or Domain effect is claimed.
    source
        .execute(
            &format!(
                "UPDATE \"{}\".issuer_cut_fixture SET live=true WHERE run_id=$1",
                scratch.name
            ),
            &[&run_id],
        )
        .unwrap();
    assert_eq!(
        db.mark_dispatch_issued_pg(
            &issued,
            Some(&scratch.name),
            Some("original-harness-principal"),
        )
        .unwrap(),
        2
    );
    assert_eq!(scratch.count("job_events"), 5);

    // The one ordinary scheduler must still dispatch unrelated Jobs.
    let ordinary = payload("ordinary-request", "ordinary-job", "ws-ordinary", 2);
    db.admit(&ordinary).unwrap();
    allocate_fixture(&mut scratch, &ordinary);
    let ordinary_digest = format!("sha256:{}", "c".repeat(64));
    db.commit_bundle_ready_pg(&PgBundleReady {
        attempt_id: ordinary.attempt_id.clone(),
        expected_row_version: 0,
        bundle_digest: ordinary_digest.clone(),
        observed_at_ms: ordinary.created_at_ms + 1,
        expected_source_sha256: ordinary.expected_source_sha256.clone(),
    })
    .unwrap();
    assert_eq!(
        db.mark_dispatch_issued_pg(
            &PgDispatchIssued {
                attempt_id: ordinary.attempt_id,
                expected_row_version: 1,
                expected_bundle_digest: ordinary_digest,
                observed_at_ms: ordinary.created_at_ms + 2,
                expected_source_sha256: ordinary.expected_source_sha256,
            },
            Some(&scratch.name),
            Some("original-harness-principal")
        )
        .unwrap(),
        2
    );
}

/// Real PG two-connection admission->revoke->dispatch experiment.
/// SQL fixture only models the original Harness source cut, never OS ACK.
#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_original_harness_dispatch_current_two_connections() {
    fn enc(v: serde_json::Value) -> (String, Vec<u8>) {
        let raw = serde_json::to_vec(&v).unwrap();
        (format!("sha256:{}", hex::encode(Sha256::digest(&raw))), raw)
    }
    let dsn = physical_pg_test_dsn();
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    scratch
        .admin
        .batch_execute(
            "CREATE TABLE issuer_cut_fixture(
                run_id text, generation bigint, digest text, live boolean,
                payload_hash text, payload bytea, fence bytea,
                intent_hash text, intent bytea
            );
            CREATE FUNCTION harness_current_dispatch_cut(text,bigint,text)
            RETURNS TABLE(event_kind text,payload_digest text,payload_kind text,
                payload_size bigint,payload_raw bytea,fence_kind text,
                fence_size bigint,fence_raw bytea,intent_object_digest text,
                intent_kind text,intent_len bigint,intent_raw bytea)
            LANGUAGE SQL AS $cut$
                SELECT 'harness.tool-step-prepared'::text,
                    f.payload_hash,'ordivon.harness-run-event-payload'::text,
                    octet_length(f.payload)::bigint,f.payload,
                    'harness-dispatch-fence'::text,
                    octet_length(f.fence)::bigint,f.fence,
                    f.intent_hash,'harness-tool-step-intent'::text,
                    octet_length(f.intent)::bigint,f.intent
                FROM issuer_cut_fixture f
                WHERE f.run_id=$1 AND f.generation=$2 AND f.digest=$3 AND f.live
            $cut$;",
        )
        .unwrap();
    let mut h = payload("original-tool", "harness-dispatch", "harness-ws", 2);
    h.principal = "harness-issuer".into();
    let run = "harness-run:pg18-current";
    let fence_id = "harness-dispatch-fence:pg18-current";
    let other = serde_json::json!({
        "namespace":"ordivon.harness","type":"harness_run","id":run
    });
    let (intent_hash, intent_raw) = enc(serde_json::json!({
        "schemaVersion":1,"kind":"ordivon.harness-tool-step-intent",
        "harnessRunId":run,"runtimeOperation":"workspace.exec",
        "runtimeArgumentsDigest":format!("sha256:{}", "a".repeat(64)),
        "clientRequestId":h.client_request_id
    }));
    let (fence_hash, fence_raw) = enc(serde_json::json!({
        "schemaVersion":2,"kind":"ordivon.harness-dispatch-fence",
        "fenceId":fence_id,"harnessRunId":run,"runRevision":1,
        "clientRequestId":h.client_request_id,"runtimeOperation":"workspace.exec",
        "intentDigest":intent_hash,"issuedAtMs":0_i64,
        "expiresAtMs":32_503_680_000_000_i64
    }));
    let (physical_hash, _) = enc(serde_json::json!({
        "workspaceId":h.workspace_id,"executable":"/usr/bin/echo",
        "args":["harmless"],"cwdRelative":".","env":{},
        "timeoutMs":1000,"stdoutLimitBytes":1024,"stderrLimitBytes":1024,
        "foreignReferences":[other.clone()]
    }));
    let (payload_hash, payload_raw) = enc(serde_json::json!({
        "schemaVersion":1,"kind":"ordivon.harness-run-event-payload",
        "eventKind":"harness.tool-step-prepared","data":{
            "dispatchFenceDigest":fence_hash,
            "dispatchFenceObjectDigest":fence_hash,
            "toolStepIntentDigest":intent_hash,
            "toolStepIntentObjectDigest":intent_hash,
            "physicalExecutionDigest":physical_hash
        }
    }));
    h.execution_plan_json = serde_json::json!({
        "workspaceId":h.workspace_id,"workspacePath":"/tmp/pg18-current",
        "cwd":"/tmp/pg18-current","executable":"/usr/bin/echo",
        "args":["harmless"],"env":{},"timeoutMs":1000,
        "stdoutLimitBytes":1024,"stderrLimitBytes":1024,
        "executionProfile":"trusted_local","executionTarget":"local_linux",
        "foreignReferences":[other,{
            "namespace":"ordivon.harness","type":"dispatch_fence",
            "id":fence_id,"digest":fence_hash,"generation":"1"
        }]
    })
    .to_string();
    scratch
        .admin
        .execute(
            "INSERT INTO issuer_cut_fixture VALUES($1,1,$2,true,$3,$4,$5,$6,$7)",
            &[
                &run,
                &fence_hash,
                &payload_hash,
                &payload_raw,
                &fence_raw,
                &intent_hash,
                &intent_raw,
            ],
        )
        .unwrap();
    let mut runtime = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    assert_eq!(
        runtime
            .admit_with_workspace_guard(&h, &|| Ok(()), Some(&scratch.name))
            .unwrap(),
        PgAdmissionOutcome::Created(h.job_id.clone())
    );
    allocate_fixture(&mut scratch, &h);
    let digest = format!("sha256:{}", "b".repeat(64));
    runtime
        .commit_bundle_ready_pg(&PgBundleReady {
            attempt_id: h.attempt_id.clone(),
            expected_row_version: 0,
            bundle_digest: digest.clone(),
            observed_at_ms: h.created_at_ms + 1,
            expected_source_sha256: h.expected_source_sha256.clone(),
        })
        .unwrap();
    let issued = PgDispatchIssued {
        attempt_id: h.attempt_id.clone(),
        expected_row_version: 1,
        expected_bundle_digest: digest,
        observed_at_ms: h.created_at_ms + 2,
        expected_source_sha256: h.expected_source_sha256.clone(),
    };
    let mut source = Client::connect(&dsn, NoTls).unwrap();
    let update = format!(
        "UPDATE \"{}\".issuer_cut_fixture SET live=$1 WHERE run_id=$2",
        scratch.name
    );
    source.execute(&update, &[&false, &run]).unwrap();
    assert!(matches!(
        runtime.mark_dispatch_issued_pg(&issued, Some(&scratch.name), Some("harness-issuer")),
        Err(PgAdmissionError::IssuerNotCurrent)
    ));
    assert_eq!(
        scratch
            .admin
            .query_one(
                "SELECT state FROM attempts WHERE attempt_id=$1",
                &[&h.attempt_id],
            )
            .unwrap()
            .get::<_, String>(0),
        "accepted"
    );
    assert_eq!(scratch.count("job_events"), 4);

    source.execute(&update, &[&true, &run]).unwrap();
    assert_eq!(
        runtime
            .mark_dispatch_issued_pg(&issued, Some(&scratch.name), Some("harness-issuer"))
            .unwrap(),
        2
    );
    assert_eq!(scratch.count("job_events"), 5);
    // Normal Jobs are never subject to a foreign Run cut.
    let ordinary = payload("ordinary", "ordinary-dispatch", "ordinary-ws", 2);
    runtime.admit(&ordinary).unwrap();
    allocate_fixture(&mut scratch, &ordinary);
    let normal_digest = format!("sha256:{}", "c".repeat(64));
    runtime
        .commit_bundle_ready_pg(&PgBundleReady {
            attempt_id: ordinary.attempt_id.clone(),
            expected_row_version: 0,
            bundle_digest: normal_digest.clone(),
            observed_at_ms: ordinary.created_at_ms + 1,
            expected_source_sha256: ordinary.expected_source_sha256.clone(),
        })
        .unwrap();
    assert_eq!(
        runtime
            .mark_dispatch_issued_pg(
                &PgDispatchIssued {
                    attempt_id: ordinary.attempt_id,
                    expected_row_version: 1,
                    expected_bundle_digest: normal_digest,
                    observed_at_ms: 1234569,
                    expected_source_sha256: ordinary.expected_source_sha256,
                },
                Some(&scratch.name),
                Some("harness-issuer")
            )
            .unwrap(),
        2
    );
}

/// Real original Harness PG Store/Continuity → same-PG restricted Runtime
/// admission → original source UNKNOWN → later PG dispatch must fail closed.
/// Unlike the synthetic issuer SQL test, all Tool/Fence/payload bytes here
/// come from the production Harness Python publisher, not Rust test JSON.
/// This is a PG/Journal boundary test, not an OS spawn or Domain ACK.
#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_original_harness_store_real_issuer_same_job_late_revoke() {
    original_harness_store_issuer_revoke(false);
}

#[test]
#[ignore = "requires explicit disposable PostgreSQL qualification and native Unix process"]
#[cfg(unix)]
fn pg18_original_harness_issuer_receiver_spawn_after_revoke_is_denied() {
    original_harness_store_issuer_revoke(true);
}

fn original_harness_store_issuer_revoke(receiver: bool) {
    use std::{path::PathBuf, process::Command};
    let dsn = physical_pg_test_dsn();
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    let stamp = Uuid::now_v7().simple().to_string();
    let issuer_schema = format!("r17_hpg_{}", &stamp[..19]);
    let role = format!("r17_role_{}", &stamp[..19]);
    let run_id = format!("harness-run:r17-original-{}", &stamp[..19]);
    let workspace_id = format!("r17-test-{}", &stamp[..19]);
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../../../");
    let fixture = root.join("services/harness/tests/original_pg_issuer_native_fixture.py");
    assert!(
        fixture.is_file(),
        "real Harness Python source fixture missing"
    );
    let python = std::env::var("HARNESS_PG_PYTHON").unwrap_or_else(|_| "python3".into());
    let pythonpath = format!(
        "{}:{}",
        root.join("services/harness/src").display(),
        root.join("services/harness").display()
    );
    let invoke = |verb: &str| -> serde_json::Value {
        let run = Command::new(&python)
            .arg(&fixture)
            .arg(verb)
            .arg("--dsn")
            .arg(&dsn)
            .arg("--schema")
            .arg(&issuer_schema)
            .arg("--run")
            .arg(&run_id)
            .arg("--workspace")
            .arg(&workspace_id)
            .env("PYTHONPATH", &pythonpath)
            .output()
            .expect("source Harness Python interpreter");
        assert!(
            run.status.success(),
            "original Harness {verb}: {}",
            String::from_utf8_lossy(&run.stderr)
        );
        serde_json::from_slice(&run.stdout).expect("actual source publisher reports exact JSON")
    };
    let original = invoke("issue");
    assert_eq!(original["runId"], run_id);
    assert_eq!(original["fenceGeneration"], 2);
    assert_eq!(
        original["loweredRequest"]["execution"]["foreignReferences"]
            .as_array()
            .unwrap()
            .len(),
        2
    );
    scratch.admin.batch_execute(
            &format!(
                "CREATE ROLE \"{role}\" LOGIN;
                 GRANT USAGE ON SCHEMA \"{runtime}\",\"{issuer_schema}\" TO \"{role}\";
                 GRANT ALL ON ALL TABLES IN SCHEMA \"{runtime}\" TO \"{role}\";
                 GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA \"{runtime}\" TO \"{role}\";
                 REVOKE ALL ON \"{runtime}\"._stage_control FROM \"{role}\";
                 GRANT SELECT,UPDATE(id) ON \"{runtime}\"._stage_control TO \"{role}\";
                 GRANT EXECUTE ON FUNCTION \"{issuer_schema}\".harness_current_dispatch_cut(text,bigint,text)
                     TO \"{role}\";",
                runtime=scratch.name
            )
        ).unwrap();
    // PostgreSQL's truly limited Runtime SQL role must not read or write
    // the source-owned private Harness tables, only execute its issuer cut.
    let limited_dsn = format!("{dsn} user={role}");
    let mut limited_pg =
        Client::connect(&limited_dsn, NoTls).expect("real restricted Runtime SQL role");
    let current_user: String = limited_pg
        .query_one("SELECT current_user", &[])
        .unwrap()
        .get(0);
    assert_eq!(current_user, role);
    let denied = limited_pg.query(&format!("SELECT * FROM \"{issuer_schema}\".runs"), &[]);
    assert!(
        denied.is_err(),
        "limited Runtime principal can read private Harness PG"
    );
    // A failed permission statement outside an explicit transaction
    // leaves this session usable by the existing runtime PG writer.
    let e = &original["loweredRequest"]["execution"];
    let workspace_root = "/tmp/r17-pg-source-verifier".to_string();
    let plan = serde_json::json!({
        "workspaceId":e["workspaceId"],
        "workspacePath":workspace_root,
        "cwd":workspace_root,
        "executable":e["executable"],
        "args":e["args"],
        "env":e["env"],
        "timeoutMs":e["timeoutMs"],
        "stdoutLimitBytes":e["stdoutLimitBytes"],
        "stderrLimitBytes":e["stderrLimitBytes"],
        "foreignReferences":e["foreignReferences"],
        "executionProfile":"trusted_local",
        "executionTarget":"local_linux"
    });
    let mut original_job = payload("r17-original-client", "job-r17-original", "r17-test-ws", 2);
    original_job.principal = "r17-dedicated-issuer-principal".into();
    original_job.workspace_id = workspace_id.clone();
    original_job.client_request_id = original["clientRequestId"].as_str().unwrap().into();
    original_job.execution_plan_json = serde_json::to_string(&plan).unwrap();
    if receiver {
        original_job.launch_token_digest = format!("sha256:{}", "c".repeat(64));
    }
    // The actual PG source gate requires the same immutable ClientRequestId,
    // original Physical Execution and Fence on admission AND later dispatch.
    let mut runtime = PgAdmissionStore::connect(&limited_dsn, &scratch.name).unwrap();
    assert_eq!(
        runtime
            .admit_with_workspace_guard(&original_job, &|| Ok(()), Some(&issuer_schema))
            .unwrap(),
        PgAdmissionOutcome::Created(original_job.job_id.clone())
    );
    allocate_fixture(&mut scratch, &original_job);
    let bundle = format!("sha256:{}", "b".repeat(64));
    runtime
        .commit_bundle_ready_pg(&PgBundleReady {
            attempt_id: original_job.attempt_id.clone(),
            expected_row_version: 0,
            bundle_digest: bundle.clone(),
            observed_at_ms: original_job.created_at_ms + 1,
            expected_source_sha256: original_job.expected_source_sha256.clone(),
        })
        .unwrap();
    if receiver {
        let issued = PgDispatchIssued {
            attempt_id: original_job.attempt_id.clone(),
            expected_row_version: 1,
            expected_bundle_digest: bundle.clone(),
            observed_at_ms: original_job.created_at_ms + 2,
            expected_source_sha256: original_job.expected_source_sha256.clone(),
        };
        runtime
            .mark_dispatch_issued_pg(&issued, Some(&issuer_schema), Some(&original_job.principal))
            .unwrap();
        // Actual native process while the original source is current;
        // this is the positive control for the receiver-side gate.
        let marker = tempfile::tempdir().unwrap();
        let output = marker.path().join("effect");
        let result = runtime
            .with_current_issued_harness_spawn(
                &original_job.job_id,
                &original_job.attempt_id,
                &original_job.principal,
                &bundle,
                &original_job.launch_token_digest,
                &original_job.expected_source_sha256,
                &issuer_schema,
                || Command::new("/usr/bin/touch").arg(&output).spawn(),
            )
            .unwrap()
            .unwrap()
            .wait()
            .unwrap();
        assert!(result.success() && output.exists());
        std::fs::remove_file(&output).unwrap();
        // Durable original Harness revoke while a native receiver is delayed.
        let revoked = invoke("revoke");
        assert_eq!(revoked["revision"], 3);
        let mut called = false;
        let denied = runtime.with_current_issued_harness_spawn(
            &original_job.job_id,
            &original_job.attempt_id,
            &original_job.principal,
            &bundle,
            &original_job.launch_token_digest,
            &original_job.expected_source_sha256,
            &issuer_schema,
            || {
                called = true;
                Command::new("/usr/bin/touch").arg(&output).spawn()
            },
        );
        assert!(matches!(denied, Err(PgAdmissionError::IssuerNotCurrent)));
        assert!(
            !called && !output.exists(),
            "revoked receiver may not start a native effect"
        );
        let dispatches: i64 = scratch
            .admin
            .query_one(
                "SELECT count(*) FROM job_events WHERE job_id=$1 AND event_type='DISPATCH_ISSUED'",
                &[&original_job.job_id],
            )
            .unwrap()
            .get(0);
        assert_eq!(dispatches, 1);
        scratch
            .admin
            .batch_execute(&format!("DROP SCHEMA \"{issuer_schema}\" CASCADE;"))
            .unwrap();
        return;
    }
    // The *real* original Harness Store emits the UNKNOWN receipt after
    // a valid new-Job admission. This invalidates its source Run revision.
    let revoked = invoke("revoke");
    assert_eq!(revoked["sourceStanding"], "unknown");
    assert_eq!(revoked["finalization"]["sourceStanding"], "blocked");
    assert_eq!(revoked["revision"], 3);
    let issued = PgDispatchIssued {
        attempt_id: original_job.attempt_id.clone(),
        expected_row_version: 1,
        expected_bundle_digest: bundle,
        observed_at_ms: original_job.created_at_ms + 2,
        expected_source_sha256: original_job.expected_source_sha256.clone(),
    };
    assert!(
        matches!(
            runtime.mark_dispatch_issued_pg(
                &issued,
                Some(&issuer_schema),
                Some("r17-dedicated-issuer-principal")
            ),
            Err(PgAdmissionError::IssuerNotCurrent)
        ),
        "a genuine original Harness Run revoked after admission cannot issue PG dispatch"
    );
    let state: String = scratch
        .admin
        .query_one(
            "SELECT state FROM attempts WHERE attempt_id=$1",
            &[&original_job.attempt_id],
        )
        .unwrap()
        .get(0);
    assert_eq!(state, "accepted");
    let dispatches: i64 = scratch
        .admin
        .query_one(
            "SELECT count(*) FROM job_events
             WHERE job_id=$1 AND event_type='DISPATCH_ISSUED'",
            &[&original_job.job_id],
        )
        .unwrap()
        .get(0);
    assert_eq!(dispatches, 0);
    scratch
        .admin
        .batch_execute(&format!("DROP SCHEMA \"{issuer_schema}\" CASCADE;"))
        .unwrap();
}
