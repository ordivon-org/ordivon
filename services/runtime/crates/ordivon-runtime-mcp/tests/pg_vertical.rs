#![cfg(all(feature = "postgres-runtime", target_os = "linux"))]
use postgres::{Client, NoTls};
use serde_json::{json, Value};
use std::{
    fs,
    os::unix::{
        fs::{MetadataExt, PermissionsExt},
        process::CommandExt,
    },
    path::PathBuf,
    process::{Child, Command, Stdio},
    thread,
    time::{Duration, Instant},
};
use uuid::Uuid;

// A native PostgreSQL disposable cluster, Unix socket only. No production DSN is accepted.
struct Fixture {
    root: PathBuf,
    pg: Child,
    endpoint: Option<Child>,
    db: Client,
    /// Opt in only for an E2E test that executes a sibling native systemd Unit
    /// across Cargo's private sandbox mount. Other fixtures are unchanged.
    host_visible_test_runner: bool,
    /// Opt in only for disposable Harness-issuer dispatch tests.
    harness_dispatch_test: bool,
    /// Permit only the original Run's native Runtime Workspace Claim. There
    /// is intentionally no foreign Harness Schema or issuer SQL function.
    claim_only_profile: bool,
    harness_schema_override: Option<String>,
    // Only the contained-native tests install disposable nonroot payload ownership.
    // Original other PostgreSQL18 fixtures preserve historical owner behavior.
    contained_nonroot_test: bool,
    ordinary_contained_only: bool,
}
impl Fixture {
    fn new() -> Self {
        let root =
            PathBuf::from("/var/tmp").join(format!("runtime-pg-mcp-{}", Uuid::now_v7().simple()));
        fs::create_dir(&root).unwrap();
        fs::set_permissions(&root, fs::Permissions::from_mode(0o777)).unwrap();
        let unprivileged = |c: &mut Command| {
            if fs::metadata("/proc/self").unwrap().uid() == 0 {
                c.uid(65534).gid(65534);
            }
        };
        let mut init = Command::new("initdb");
        init.args([
            "-A",
            "trust",
            "-U",
            "postgres",
            "--no-locale",
            "--encoding=UTF8",
            "-D",
        ])
        .arg(root.join("data"));
        unprivileged(&mut init);
        let output = init.output().expect("native initdb installed");
        assert!(
            output.status.success(),
            "initdb: {}",
            String::from_utf8_lossy(&output.stderr)
        );
        let mut launch = Command::new("postgres");
        launch
            .arg("-D")
            .arg(root.join("data"))
            .arg("-k")
            .arg(&root)
            .args([
                "-h",
                "",
                "-p",
                "5432",
                "-c",
                "fsync=off",
                "-c",
                "dynamic_shared_memory_type=mmap",
            ]);
        unprivileged(&mut launch);
        let log = fs::File::create(root.join("postgres.log")).unwrap();
        launch.stdout(log.try_clone().unwrap()).stderr(log);
        let mut pg = launch.spawn().unwrap();
        let dsn = format!("host={} user=postgres dbname=postgres", root.display());
        let deadline = Instant::now() + Duration::from_secs(10);
        let mut db = loop {
            match Client::connect(&dsn, NoTls) {
                Ok(c) => break c,
                Err(e) => {
                    assert!(
                        Instant::now() < deadline,
                        "PG startup: {e}; {:?}",
                        pg.try_wait()
                    );
                    thread::sleep(Duration::from_millis(50));
                }
            }
        };
        // Multiple isolated PG fixtures run as the same disposable nobody
        // identity. POSIX dynamic shared-memory segments can be removed by
        // unrelated fixture teardown; only this test-owned PostgreSQL process
        // must choose the mature mmap debugging carrier.
        let dsm: String = db
            .query_one("SHOW dynamic_shared_memory_type", &[])
            .unwrap()
            .get(0);
        assert_eq!(
            dsm, "mmap",
            "disposable PG must not share POSIX DSM lifetime"
        );
        db.batch_execute("CREATE SCHEMA fresh; SET search_path TO fresh")
            .unwrap();
        db.batch_execute(include_str!(
            "../../ordivon-runtime-core/sql/pg_fresh_epoch.sql"
        ))
        .unwrap();
        db.execute(
            "INSERT INTO _stage_control VALUES('source','QUALIFIED_WRITER',$1,true)",
            &[&"a".repeat(64)],
        )
        .unwrap();
        let physical = db.query_one(
            "SELECT (SELECT system_identifier::text FROM pg_control_system()),                     (SELECT timeline_id FROM pg_control_checkpoint())", &[],
        ).unwrap();
        let digest = ordivon_runtime_core::pg_admission::pg_writer_epoch_digest(
            &"a".repeat(64),
            &physical.get::<_, String>(0),
            physical.get::<_, i32>(1),
        );
        db.execute(
            "INSERT INTO _stage_control VALUES('epoch','QUALIFIED_EPOCH',$1,true)",
            &[&digest],
        )
        .unwrap();
        // A disposable native PG operator owns this schema, while the
        // application role may lock the control row but not promote itself.
        db.batch_execute(
            "CREATE ROLE runtime_app LOGIN;
             GRANT USAGE ON SCHEMA fresh TO runtime_app;
             GRANT ALL ON ALL TABLES IN SCHEMA fresh TO runtime_app;
             REVOKE ALL ON fresh._stage_control FROM runtime_app;
             GRANT SELECT, UPDATE(id) ON fresh._stage_control TO runtime_app;",
        )
        .unwrap();
        let can_promote: bool = db.query_one(
            "SELECT has_column_privilege('runtime_app','fresh._stage_control','promotion_allowed','UPDATE')",
            &[],
        ).unwrap().get(0);
        assert!(!can_promote, "test app role has operator writer authority");
        assert_eq!(
            db.query_one("SELECT count(*) FROM jobs", &[])
                .unwrap()
                .get::<_, i64>(0),
            0
        );
        Self {
            root,
            pg,
            endpoint: None,
            db,
            host_visible_test_runner: false,
            harness_dispatch_test: false,
            claim_only_profile: false,
            harness_schema_override: None,
            contained_nonroot_test: false,
            ordinary_contained_only: false,
        }
    }
    fn endpoint(&mut self) -> String {
        self.endpoint_for_principal("pg-consumer")
    }
    fn endpoint_for_principal(&mut self, principal: &str) -> String {
        self.endpoint_with_release(principal, false)
    }
    fn endpoint_with_release(&mut self, principal: &str, qualified_release: bool) -> String {
        let listener = std::net::TcpListener::bind("127.0.0.1:0").unwrap();
        let bind = listener.local_addr().unwrap();
        drop(listener);
        // Cargo builds the existing Core runner when this test is run with --workspace.
        let runner = std::env::current_exe()
            .unwrap()
            .parent()
            .unwrap()
            .parent()
            .unwrap()
            .join("ordivon-runtime-runner");
        assert!(
            runner.is_file(),
            "run cargo test --workspace to build the native runner: {}",
            runner.display()
        );
        let runner = if self.host_visible_test_runner {
            // An actual sibling systemd unit cannot execute through Cargo's
            // private source mount. Copy only this disposable Fixture binary
            // into the same private PG test root; never touch installed units.
            let test_runner = self.root.join("ordivon-runtime-runner");
            // This fixture may restart its PG endpoint while the previous
            // native Runner still owns the disposable executable. Re-copying
            // that same executing inode would fail with ETXTBSY, so reuse its
            // exact verified bytes instead of attempting an unsafe overwrite.
            match fs::symlink_metadata(&test_runner) {
                Err(err) if err.kind() == std::io::ErrorKind::NotFound => {
                    fs::copy(&runner, &test_runner).unwrap();
                    fs::set_permissions(&test_runner, fs::Permissions::from_mode(0o755)).unwrap();
                }
                Ok(meta) if meta.file_type().is_file() => {
                    assert_eq!(
                        fs::read(&test_runner).unwrap(),
                        fs::read(&runner).unwrap(),
                        "restarted PG endpoint cannot substitute a different Runner image"
                    );
                }
                other => panic!("disposable Runner copy path changed: {other:?}"),
            }
            test_runner
        } else {
            runner
        };
        let output = fs::File::create(self.root.join("endpoint.log")).unwrap();
        let mut endpoint = Command::new(env!("CARGO_BIN_EXE_ordivon-runtime-pg"));
        endpoint
            .env(
                "ORDIVON_PG_DSN",
                format!(
                    "host={} user=runtime_app dbname=postgres",
                    self.root.display()
                ),
            )
            .env("ORDIVON_PG_SCHEMA", "fresh")
            .env("ORDIVON_PG_SOURCE_SHA256", "a".repeat(64))
            .env("ORDIVON_PG_STORE_ROOT", self.root.join("store"))
            .env("ORDIVON_PG_RUNNER", runner)
            .env("ORDIVON_PG_EXECUTABLE_ROOTS_JSON", r#"["/usr/bin","/bin"]"#)
            .env("ORDIVON_PG_BIND", bind.to_string())
            .env("ORDIVON_PG_TOKEN", "p".repeat(32))
            .env("ORDIVON_PG_PRINCIPAL", principal)
            .stdout(Stdio::null())
            .stderr(output);
        if self.contained_nonroot_test || self.ordinary_contained_only {
            endpoint
                .env("ORDIVON_PG_WORKSPACE_UID", "65534")
                .env("ORDIVON_PG_WORKSPACE_GID", "65534");
        }
        if self.ordinary_contained_only {
            endpoint.env("ORDIVON_PG_ORDINARY_EXECUTION_PROFILE", "contained_local");
        } else {
            endpoint.env_remove("ORDIVON_PG_ORDINARY_EXECUTION_PROFILE");
        }
        if self.harness_dispatch_test || self.claim_only_profile {
            let token_file = self.root.join("r16-dedicated-harness-token");
            fs::write(&token_file, "h".repeat(48)).unwrap();
            fs::set_permissions(&token_file, fs::Permissions::from_mode(0o600)).unwrap();
            endpoint
                .env("ORDIVON_PG_HARNESS_TOKEN_FILE", token_file)
                .env("ORDIVON_PG_HARNESS_PRINCIPAL", "harness-dispatch-r16");
            if self.harness_dispatch_test {
                let private = self.root.join("issuer-receiver-private");
                fs::create_dir_all(&private).unwrap();
                fs::set_permissions(&private, fs::Permissions::from_mode(0o700)).unwrap();
                let dsn_file = private.join("dsn");
                fs::write(
                    &dsn_file,
                    format!(
                        "host={} user=runtime_app dbname=postgres",
                        self.root.display()
                    ),
                )
                .unwrap();
                fs::set_permissions(&dsn_file, fs::Permissions::from_mode(0o600)).unwrap();
                endpoint.env("ORDIVON_PG_DSN_FILE", dsn_file);
                endpoint.env(
                    "ORDIVON_PG_HARNESS_ISSUER_SCHEMA",
                    self.harness_schema_override
                        .as_deref()
                        .unwrap_or("r16_issuer"),
                );
            } else {
                // The explicit opposite of original Harness JobIssuer mode:
                // only Release/Reserve/GET, no cross-database issuer fixture.
                endpoint.env_remove("ORDIVON_PG_HARNESS_ISSUER_SCHEMA");
            }
        }
        if qualified_release {
            let source = self.root.join("release-source");
            let receipts = self.root.join("receipts");
            fs::create_dir(&source).unwrap();
            fs::create_dir(&receipts).unwrap();
            let operator = self.root.join("operator");
            fs::write(
                &operator,
                "#!/bin/sh
exit 0
",
            )
            .unwrap();
            self.db
                .execute(
                    "INSERT INTO fresh._stage_control VALUES ('release','QUALIFIED_RELEASE',$1,true)",
                    &[&"a".repeat(64)],
                )
                .unwrap();
            endpoint
                .env("ORDIVON_PG_RELEASE_SOURCE_REPO", &source)
                .env("ORDIVON_PG_RELEASE_OPERATOR_BIN", &operator)
                .env("ORDIVON_PG_RELEASE_RECEIPT_ROOT", &receipts)
                .env(
                    "ORDIVON_PG_RELEASE_DISPATCH_TIMER",
                    "ordivon-pg-disposable-test.timer",
                );
        }
        self.endpoint = Some(endpoint.spawn().unwrap());
        let deadline = Instant::now() + Duration::from_secs(10);
        while std::net::TcpStream::connect(bind).is_err() {
            assert!(
                Instant::now() < deadline,
                "endpoint startup failed: {}",
                fs::read_to_string(self.root.join("endpoint.log")).unwrap()
            );
            thread::sleep(Duration::from_millis(25));
        }
        format!("http://{bind}/mcp")
    }
    fn repo(&self) -> PathBuf {
        let repo = self.root.join("source");
        fs::create_dir(&repo).unwrap();
        for args in [
            vec!["init"],
            vec![
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.invalid",
                "commit",
                "--allow-empty",
                "-m",
                "fresh",
            ],
        ] {
            assert!(Command::new("git")
                .arg("-C")
                .arg(&repo)
                .args(args)
                .output()
                .unwrap()
                .status
                .success());
        }
        repo
    }
}
impl Drop for Fixture {
    fn drop(&mut self) {
        if let Some(child) = &mut self.endpoint {
            let _ = child.kill();
            let _ = child.wait();
        }
        let _ = self.pg.kill();
        let _ = self.pg.wait();
        let _ = fs::remove_dir_all(&self.root);
    }
}
fn rpc(url: &str, method: &str, params: Value) -> Value {
    tokio::runtime::Runtime::new().unwrap().block_on(async {
    let client=reqwest::Client::new();
    let mut request=client.post(url).bearer_auth("p".repeat(32)).header("Accept","application/json, text/event-stream").header("MCP-Protocol-Version","2026-07-28").header("Mcp-Method",method);
    if let Some(name)=params.get("name").and_then(Value::as_str) {request=request.header("Mcp-Name",name);}
    let mut params=params;
    if let Value::Object(ref mut object)=params {
        object.insert("_meta".into(),json!({"io.modelcontextprotocol/protocolVersion":"2026-07-28","io.modelcontextprotocol/clientCapabilities":{}}));
    }
    let response=request.json(&json!({"jsonrpc":"2.0","id":1,"method":method,"params":params})).send().await.unwrap();
    let status=response.status(); let body=response.text().await.unwrap();
    assert!(status.is_success(),"HTTP {status}: {body}");
    let message:Value=if body.starts_with("event:") || body.starts_with("data:") {serde_json::from_str(body.lines().find_map(|line|line.strip_prefix("data: ")).expect("SSE data")).unwrap()} else {serde_json::from_str(&body).unwrap()};
    assert!(message.get("error").is_none(),"{message}");
    message["result"].clone()
    })
}
fn call(url: &str, name: &str, args: Value) -> Value {
    let response = rpc(url, "tools/call", json!({"name":name,"arguments":args}));
    // This integration client consumes the committed identity, not a
    // transport success boolean. Only read/reconcile the SAME Job after
    // a qualified post-COMMIT 40001; no duplicate workspace.exec submission.
    if name == "workspace.exec" || name == "workspace.execPlan" {
        observe_committed_40001(url, response)
    } else {
        response
    }
}

/// An admitted Job's MCP response can encounter a *later* database
/// serialization abort while reconciling its native result. The consumer
/// must use the committed operationId to re-observe the SAME Job, never
/// resubmit the executable as a new request.
fn committed_40001_job_id(result: &Value) -> Option<&str> {
    let error = result.get("structuredContent")?.get("error")?;
    if result.get("isError")?.as_bool() != Some(true)
        || error.get("commitState")?.as_str() != Some("committed")
        || error.get("retryClass")?.as_str() != Some("reconcile_first")
        || !matches!(
            error.get("code")?.as_str()?,
            "REGISTRY_BUSY" | "REGISTRY_UNAVAILABLE"
        )
        || !error.get("message")?.as_str()?.contains("E40001")
    {
        return None;
    }
    error
        .get("operationId")?
        .as_str()
        .filter(|id| id.starts_with("job-") && id.len() > "job-".len())
}

fn observe_committed_40001(url: &str, original: Value) -> Value {
    let Some(job_id) = committed_40001_job_id(&original) else {
        return original;
    };
    let deadline = Instant::now() + Duration::from_secs(25);
    loop {
        // This is a different *read/observe* MCP operation. Do not invoke
        // workspace.exec again after its admission has already committed.
        let observed = call(
            url,
            "job.observe",
            json!({"jobId": job_id, "waitMs": 4000,
                "stdoutTailBytes":8192,"stderrTailBytes":8192}),
        );
        if observed["isError"] == true {
            assert_eq!(
                committed_40001_job_id(&observed),
                Some(job_id),
                "new or unqualified observation error: {observed}"
            );
        } else {
            assert_eq!(
                observed["structuredContent"]["jobId"], job_id,
                "readback must bind the original committed Job"
            );
            if observed["structuredContent"]["executionTerminal"] == true {
                return observed;
            }
        }
        assert!(
            Instant::now() < deadline,
            "committed 40001 Job did not converge: {observed}"
        );
        thread::sleep(Duration::from_millis(20));
    }
}

#[test]
fn committed_observation_retry_never_reclassifies_uncommitted_effect() {
    let value = json!({"isError":true,"structuredContent":{"error":{
        "commitState":"committed","retryClass":"reconcile_first",
        "code":"REGISTRY_UNAVAILABLE","operationId":"job-known",
        "message":"PostgreSQL: SqlState(E40001)"
    }}});
    // Current PostgreSQL 40001 is REGISTRY_BUSY; historical adapters may
    // project REGISTRY_UNAVAILABLE. Only committed E40001 is safe to observe.
    for code in ["REGISTRY_BUSY", "REGISTRY_UNAVAILABLE"] {
        let mut variant = value.clone();
        variant["structuredContent"]["error"]["code"] = json!(code);
        assert_eq!(committed_40001_job_id(&variant), Some("job-known"));
    }
    for replacement in [
        json!({"commitState":"not_committed"}),
        json!({"retryClass":"safe_same_request"}),
        json!({"code":"INVALID_ARGUMENT"}),
        json!({"message":"other database failure"}),
        json!({"operationId":null}),
    ] {
        let mut mutant = value.clone();
        for (key, value) in replacement.as_object().unwrap() {
            mutant["structuredContent"]["error"][key] = value.clone();
        }
        assert_eq!(committed_40001_job_id(&mutant), None, "{mutant}");
    }
}

/// Production regression: the real PG release row must be examined while
/// #[tokio::main] drives startup and async MCP catalog/tool handlers.
#[test]
#[ignore = "launches disposable PG18 and native MCP with qualified release configuration"]
fn qualified_pg_release_does_not_nest_tokio_on_startup_or_mcp_calls() {
    let mut fixture = Fixture::new();
    let endpoint = fixture.endpoint_with_release("qualified-release", true);
    let listed = rpc(&endpoint, "tools/list", json!({}));
    let names = listed["tools"]
        .as_array()
        .unwrap()
        .iter()
        .filter_map(|item| item["name"].as_str())
        .collect::<Vec<_>>();
    assert!(names.contains(&"release.get"), "{listed}");
    assert!(
        !names.contains(&"release.apply"),
        "synthetic timer must not become release authority"
    );
    let described = call(&endpoint, "runtime.describe", json!({}));
    assert_eq!(
        described["structuredContent"]["structuredReleaseConfigured"], false,
        "{described}"
    );
}

/// A real PG+MCP contract test: an ordinary executed Job is NOT a Release
/// effect; the operator fixture explicitly commits the release side truth.
/// No installer is invoked. This exercises readback integrity, not deployment.
#[test]
#[ignore = "launches a disposable PostgreSQL cluster and native MCP"]
fn pg_release_get_never_claims_deployed_without_verified_operator_receipt() {
    use ordivon_runtime_core::{
        runtime_release_effect_id, runtime_release_request_identity_digest, RuntimeReleaseRequest,
    };
    use sha2::{Digest, Sha256};
    #[derive(serde::Serialize)]
    #[serde(rename_all = "camelCase")]
    struct Binding<'a> {
        contract: &'static str,
        effect_id: &'a str,
        request_digest: &'a str,
        workspace_id: &'a str,
        commit: &'a str,
        candidate_manifest_digest: &'a str,
        expected_tool_count: u32,
        receipt_path: &'a str,
    }

    let mut fixture = Fixture::new();
    // A sibling native systemd Runner cannot execute Cargo's private source
    // path: use the established host-visible per-fixture runner artifact.
    fixture.host_visible_test_runner = true;
    let repo = fixture.repo();
    let commit = String::from_utf8(
        Command::new("git")
            .arg("-C")
            .arg(&repo)
            .args(["rev-parse", "HEAD"])
            .output()
            .unwrap()
            .stdout,
    )
    .unwrap()
    .trim()
    .to_string();
    let endpoint = fixture.endpoint();
    let tools = rpc(&endpoint, "tools/list", json!({}));
    let names = tools["tools"]
        .as_array()
        .unwrap()
        .iter()
        .map(|t| t["name"].as_str().unwrap())
        .collect::<Vec<_>>();
    assert!(names.contains(&"release.get"));
    assert!(
        !names.contains(&"release.apply"),
        "no unqualified release writer"
    );
    let describe = call(&endpoint, "runtime.describe", json!({}));
    assert_eq!(
        describe["structuredContent"]["structuredReleaseConfigured"],
        false
    );
    let missing = call(
        &endpoint,
        "release.get",
        json!({"clientRequestId":"release-no-such-id"}),
    );
    assert_eq!(
        missing["structuredContent"]["error"]["code"],
        "JOB_NOT_FOUND"
    );

    let open = call(
        &endpoint,
        "workspace.open",
        json!({"workspaceId":"ws-release-readback","sourceRepo":repo,"sourceRevision":"HEAD"}),
    );
    assert_ne!(open["isError"], true, "{open}");
    let client_id = "pg-release-readback-test-001";
    let exec = call(
        &endpoint,
        "workspace.exec",
        json!({"clientRequestId":client_id,"execution":{
            "workspaceId":"ws-release-readback","executable":"/usr/bin/true",
            "cwdRelative":".","timeoutMs":5000},"waitMs":5000}),
    );
    assert_ne!(exec["isError"], true, "{exec}");
    let job = exec["structuredContent"]["jobId"]
        .as_str()
        .unwrap()
        .to_string();
    // Test the promised state, not the duration of a submit call. A real
    // native PG/systemd job can still be STARTING after the initial 5s
    // submit wait; grafting a fake ReleaseEffect before the ordinary Job
    // terminates does not test the intended missing-operator-receipt case.
    let terminal_deadline = Instant::now() + Duration::from_secs(70);
    loop {
        let actual = call(
            &endpoint,
            "job.observe",
            json!({"jobId":job,"waitMs":7000,"waitUntil":"terminal",
                "stdoutTailBytes":0,"stderrTailBytes":0}),
        );
        assert_ne!(actual["isError"], true, "{actual}");
        if actual["structuredContent"]["executionTerminal"] == true {
            assert_eq!(
                actual["structuredContent"]["status"], "succeeded",
                "original native ordinary Job did not succeed: {actual}"
            );
            break;
        }
        assert!(
            Instant::now() < terminal_deadline,
            "original native ordinary Job did not reach terminal before release graft: {actual}"
        );
    }
    let release = RuntimeReleaseRequest {
        schema_version: 1,
        client_request_id: client_id.into(),
        principal: "pg-consumer".into(),
        workspace_id: "ws-release-readback".into(),
        commit,
        candidate_manifest_digest: format!("sha256:{}", "a".repeat(64)),
        expected_tool_count: 20,
    };
    let digest = runtime_release_request_identity_digest(&release).unwrap();
    let effect = runtime_release_effect_id(&release);
    let receipt = fixture.root.join("test-release-receipt");
    let receipt_str = receipt.to_string_lossy().to_string();
    let binding = Binding {
        contract: "runtime_release_v1",
        effect_id: &effect,
        request_digest: &digest,
        workspace_id: &release.workspace_id,
        commit: &release.commit,
        candidate_manifest_digest: &release.candidate_manifest_digest,
        expected_tool_count: release.expected_tool_count,
        receipt_path: &receipt_str,
    };
    let binding_bytes = serde_json::to_vec(&binding).unwrap();
    let binding_digest = format!("sha256:{}", hex::encode(Sha256::digest(&binding_bytes)));
    let original: String = fixture
        .db
        .query_one(
            "SELECT workspace_snapshot_json FROM jobs WHERE job_id=$1",
            &[&job],
        )
        .unwrap()
        .get(0);
    let mut snapshot: Value = serde_json::from_str(&original).unwrap();
    snapshot["runtimeReleaseEffectDigest"] = json!(binding_digest);
    fixture
        .db
        .execute(
            "UPDATE jobs SET request_digest=$1,workspace_snapshot_json=$2 WHERE job_id=$3",
            &[&digest, &snapshot.to_string(), &job],
        )
        .unwrap();
    fixture.db.execute(
        "INSERT INTO job_runtime_release_effects(job_id,effect_id,contract,request_digest,\
         workspace_id,commit_revision,candidate_manifest_digest,expected_tool_count,receipt_path,binding_digest)\
         VALUES($1,$2,'runtime_release_v1',$3,$4,$5,$6,$7,$8,$9)",
        &[&job,&effect,&digest,&release.workspace_id,&release.commit,
          &release.candidate_manifest_digest,&(20_i32),&receipt_str,&binding_digest],
    ).unwrap();

    let readback = call(
        &endpoint,
        "release.get",
        json!({"clientRequestId":client_id}),
    );
    // This fixture has deliberately grafted ReleaseEffect data onto a
    // *normal Runner-exited Job*, without any operator dispatch or
    // RELEASE_EFFECT_RECEIPTED event. Never mistake its PROCESS_EXITED
    // event for a qualified installer terminal proof.
    assert_eq!(readback["isError"], true, "{readback}");
    assert_eq!(
        readback["structuredContent"]["error"]["code"], "RECONCILIATION_REQUIRED",
        "synthetic Runner terminal is not a ReleaseEffect receipt: {readback}"
    );

    fs::create_dir(&receipt).unwrap();
    fs::write(
        receipt.join("effect-request.json"),
        b"{\"contract\":\"fake\"}",
    )
    .unwrap();
    let forged = call(
        &endpoint,
        "release.get",
        json!({"clientRequestId":client_id}),
    );
    assert_eq!(forged["isError"], true, "{forged}");
    assert_eq!(
        forged["structuredContent"]["error"]["code"], "RECONCILIATION_REQUIRED",
        "false Runner terminal must fail before even opening the forged receipt"
    );

    fixture
        .db
        .execute(
            "UPDATE job_runtime_release_effects SET binding_digest=$1 WHERE job_id=$2",
            &[&format!("sha256:{}", "0".repeat(64)), &job],
        )
        .unwrap();
    let corrupted = call(
        &endpoint,
        "release.get",
        json!({"clientRequestId":client_id}),
    );
    assert_eq!(
        corrupted["structuredContent"]["error"]["code"],
        "REGISTRY_CORRUPT"
    );
    fixture
        .db
        .execute(
            "UPDATE job_runtime_release_effects SET binding_digest=$1 WHERE job_id=$2",
            &[&binding_digest, &job],
        )
        .unwrap();

    if let Some(mut old) = fixture.endpoint.take() {
        old.kill().unwrap();
        old.wait().unwrap();
    }
    let other = fixture.endpoint_for_principal("different-principal");
    let denied = call(&other, "release.get", json!({"clientRequestId":client_id}));
    assert_eq!(
        denied["structuredContent"]["error"]["code"], "JOB_NOT_FOUND",
        "release identity must not be visible across principals: {denied}"
    );
}

/// The PG installer is not yet published. This proves its low-level
/// transactional ReleaseEffect + Job identity has an independent operator
/// qualification and cannot be dispatched or cancelled as an ordinary Job.
#[test]
#[ignore = "launches a disposable PostgreSQL cluster with native HTTP MCP"]
fn pg_release_effect_atomic_admission_and_generic_dispatch_fence() {
    use ordivon_runtime_core::pg_admission::{
        PgAdmissionError, PgAdmissionInput, PgAdmissionOutcome, PgAdmissionStore,
    };
    use ordivon_runtime_core::{
        runtime_release_effect_id, runtime_release_request_identity_digest, RuntimeReleaseRequest,
    };
    use sha2::{Digest, Sha256};
    #[derive(serde::Serialize)]
    #[serde(rename_all = "camelCase")]
    struct Binding<'a> {
        contract: &'static str,
        effect_id: &'a str,
        request_digest: &'a str,
        workspace_id: &'a str,
        commit: &'a str,
        candidate_manifest_digest: &'a str,
        expected_tool_count: u32,
        receipt_path: &'a str,
    }

    let mut fixture = Fixture::new();
    fixture.host_visible_test_runner = true;
    let repo = fixture.repo();
    let commit = String::from_utf8(
        Command::new("git")
            .arg("-C")
            .arg(&repo)
            .args(["rev-parse", "HEAD"])
            .output()
            .unwrap()
            .stdout,
    )
    .unwrap()
    .trim()
    .to_string();
    let endpoint = fixture.endpoint();
    let open = call(
        &endpoint,
        "workspace.open",
        json!({"workspaceId":"ws-pg-release-native","sourceRepo":repo,"sourceRevision":"HEAD"}),
    );
    assert_ne!(open["isError"], true, "{open}");
    let control = call(
        &endpoint,
        "workspace.exec",
        json!({"clientRequestId":"pg-release-fixture-plan-001","execution":{
            "workspaceId":"ws-pg-release-native","executable":"/usr/bin/true",
            "cwdRelative":".","timeoutMs":5000},"waitMs":5000}),
    );
    assert_ne!(control["isError"], true, "{control}");
    let row = fixture.db.query_one(
        "SELECT j.execution_plan_json,j.execution_plan_digest,j.workspace_snapshot_json FROM jobs j WHERE j.client_request_id='pg-release-fixture-plan-001'",
        &[],
    ).unwrap();
    let plan: String = row.get(0);
    let plan_digest: String = row.get(1);
    let snapshot_raw: String = row.get(2);

    let request = RuntimeReleaseRequest {
        schema_version: 1,
        client_request_id: "pg-release-atomic-fixture-001".into(),
        principal: "pg-consumer".into(),
        workspace_id: "ws-pg-release-native".into(),
        commit,
        candidate_manifest_digest: format!("sha256:{}", "b".repeat(64)),
        expected_tool_count: 20,
    };
    let request_digest = runtime_release_request_identity_digest(&request).unwrap();
    let effect_id = runtime_release_effect_id(&request);
    let receipt = fixture.root.join("release-receipt-atomic-fixture");
    let receipt_s = receipt.to_string_lossy().into_owned();
    let binding = Binding {
        contract: "runtime_release_v1",
        effect_id: &effect_id,
        request_digest: &request_digest,
        workspace_id: &request.workspace_id,
        commit: &request.commit,
        candidate_manifest_digest: &request.candidate_manifest_digest,
        expected_tool_count: request.expected_tool_count,
        receipt_path: &receipt_s,
    };
    let binding_json = serde_json::to_vec(&binding).unwrap();
    let digest = format!("sha256:{}", hex::encode(Sha256::digest(binding_json)));
    let mut snapshot: Value = serde_json::from_str(&snapshot_raw).unwrap();
    snapshot["runtimeReleaseEffectDigest"] = json!(digest);
    let job = format!("job-{}", Uuid::now_v7());
    let attempt = format!("attempt-{}", Uuid::now_v7());
    let input = PgAdmissionInput {
        job_id: job.clone(),
        attempt_id: attempt.clone(),
        reservation_id: format!("reservation-{attempt}"),
        principal: request.principal.clone(),
        client_request_id: request.client_request_id.clone(),
        request_digest,
        operation_digest: format!("sha256:{}", "c".repeat(64)),
        workspace_id: request.workspace_id.clone(),
        workspace_snapshot_json: snapshot.to_string(),
        execution_plan_json: plan,
        execution_plan_digest: plan_digest,
        launch_token_digest: format!("sha256:{}", "d".repeat(64)),
        bundle_path: fixture
            .root
            .join("store/pg-attempts")
            .join(&attempt)
            .to_string_lossy()
            .into_owned(),
        unit_name: format!("ordivon-pg-{attempt}.service"),
        global_limit: 0,
        created_at_ms: 123456789,
        expected_source_sha256: "a".repeat(64),
    };
    let dsn = format!(
        "host={} user=runtime_app dbname=postgres",
        fixture.root.display()
    );
    let mut app = PgAdmissionStore::connect(&dsn, "fresh").unwrap();

    assert!(
        matches!(
            app.admit_release_effect(&input, &request, &receipt),
            Err(PgAdmissionError::Unqualified)
        ),
        "a qualified general Job writer cannot self-qualify a ReleaseEffect"
    );
    assert_eq!(
        fixture
            .db
            .query_one(
                "SELECT count(*) FROM jobs WHERE client_request_id=$1",
                &[&request.client_request_id],
            )
            .unwrap()
            .get::<_, i64>(0),
        0
    );
    assert_eq!(
        fixture
            .db
            .query_one("SELECT count(*) FROM job_runtime_release_effects", &[])
            .unwrap()
            .get::<_, i64>(0),
        0
    );

    // Operator is *independent* of runtime_app; test-only synthetic evidence.
    fixture
        .db
        .execute(
            "INSERT INTO _stage_control VALUES('release','QUALIFIED_RELEASE',$1,true)",
            &[&"a".repeat(64)],
        )
        .unwrap();
    assert_eq!(
        app.admit_release_effect(&input, &request, &receipt)
            .unwrap(),
        PgAdmissionOutcome::Created(job.clone())
    );
    assert_eq!(
        app.admit_release_effect(&input, &request, &receipt)
            .unwrap(),
        PgAdmissionOutcome::Existing(job.clone()),
        "exact replay must not create another effect"
    );
    // Revoking future release authority cannot hide the already committed
    // immutable effect. Replay resolves BEFORE mutable operator eligibility.
    fixture
        .db
        .execute(
            "UPDATE _stage_control SET promotion_allowed=false WHERE id='release'",
            &[],
        )
        .unwrap();
    assert_eq!(
        app.admit_release_effect(&input, &request, &receipt)
            .unwrap(),
        PgAdmissionOutcome::Existing(job.clone()),
        "exact replay after release revocation must retain original identity"
    );
    assert_eq!(
        fixture
            .db
            .query_one(
                "SELECT count(*) FROM job_runtime_release_effects WHERE job_id=$1",
                &[&job],
            )
            .unwrap()
            .get::<_, i64>(0),
        1
    );
    assert_eq!(
        fixture
            .db
            .query_one("SELECT count(*) FROM jobs WHERE job_id=$1", &[&job])
            .unwrap()
            .get::<_, i64>(0),
        1
    );
    assert_eq!(
        fixture
            .db
            .query_one("SELECT count(*) FROM job_events WHERE job_id=$1", &[&job])
            .unwrap()
            .get::<_, i64>(0),
        3
    );

    // Background scheduling and explicit observe cannot use generic Runner.
    thread::sleep(Duration::from_millis(1_100));
    let observed = call(
        &endpoint,
        "job.observe",
        json!({"jobId":job,"waitMs":0,"stdoutTailBytes":0,"stderrTailBytes":0}),
    );
    assert_ne!(observed["isError"], true, "{observed}");
    assert_eq!(observed["structuredContent"]["attemptState"], "accepted");
    assert_eq!(observed["structuredContent"]["executionTerminal"], false);
    assert_eq!(fixture.db.query_one(
        "SELECT count(*) FROM job_allocations x JOIN attempts a ON a.attempt_id=x.attempt_id WHERE a.job_id=$1 AND x.state='active'",
        &[&job],
    ).unwrap().get::<_,i64>(0),0);
    assert_eq!(
        fixture
            .db
            .query_one(
                "SELECT count(*) FROM job_events WHERE job_id=$1 AND event_type='DISPATCH_ISSUED'",
                &[&job],
            )
            .unwrap()
            .get::<_, i64>(0),
        0
    );
    let cancel = call(&endpoint, "job.cancel", json!({"jobId":job}));
    assert_eq!(
        cancel["structuredContent"]["error"]["code"],
        "DEPLOYMENT_IN_PROGRESS"
    );
    let get = call(
        &endpoint,
        "release.get",
        json!({"clientRequestId":request.client_request_id}),
    );
    assert_ne!(get["isError"], true, "{get}");
    assert_eq!(get["structuredContent"]["effectDisposition"], "admitted");
    assert_eq!(get["structuredContent"]["receiptAvailable"], false);
    assert_eq!(get["structuredContent"]["effectTerminal"], false);

    // An admitted release is not a physical cutover. A normal, harmless
    // Job must run and deliver its own bytes while the ReleaseEffect
    // stays untouched. The post-dispatch admission fence is covered by
    // the existing isolated PG admission contract test.
    let ordinary = call(
        &endpoint,
        "workspace.exec",
        json!({"clientRequestId":"pg-release-predispatch-ordinary-001","execution":{
            "workspaceId":"ws-pg-release-native","executable":"/usr/bin/printf",
            "args":["ORDINARY_BEFORE_RELEASE_DISPATCH"],
            "cwdRelative":".","timeoutMs":20000},"waitMs":10000}),
    );
    assert_ne!(ordinary["isError"], true, "{ordinary}");
    let ordinary_id = ordinary["structuredContent"]["jobId"]
        .as_str()
        .unwrap()
        .to_owned();
    let mut actual = ordinary;
    let deadline = Instant::now() + Duration::from_secs(70);
    while actual["structuredContent"]["executionTerminal"] != true {
        actual = call(
            &endpoint,
            "job.observe",
            json!({"jobId":ordinary_id,"waitMs":7000,"waitUntil":"terminal"}),
        );
        assert_ne!(actual["isError"], true, "{actual}");
        assert!(
            Instant::now() < deadline,
            "ordinary Job did not converge: {actual}"
        );
    }
    assert_eq!(
        actual["structuredContent"]["executionDisposition"], "succeeded",
        "{actual}"
    );
    let stdout = actual["structuredContent"]["artifacts"]
        .as_array()
        .unwrap()
        .iter()
        .find(|a| a["kind"] == "stdout")
        .expect("ordinary stdout");
    let readback = call(
        &endpoint,
        "artifact.read",
        json!({"jobId":ordinary_id,"artifactId":stdout["artifactId"],"offset":0,"maxBytes":100}),
    );
    assert_ne!(readback["isError"], true, "{readback}");
    assert_eq!(
        readback["structuredContent"]["content"],
        "ORDINARY_BEFORE_RELEASE_DISPATCH"
    );
    let pending = call(
        &endpoint,
        "release.get",
        json!({"clientRequestId":request.client_request_id}),
    );
    assert_ne!(pending["isError"], true, "{pending}");
    assert_eq!(
        pending["structuredContent"]["effectDisposition"],
        "admitted"
    );
    assert_eq!(pending["structuredContent"]["receiptAvailable"], false);
    assert_eq!(fixture.db.query_one(
        "SELECT count(*) FROM job_events WHERE job_id=$1 AND event_type IN ('DISPATCH_ISSUED','RELEASE_OPERATOR_DISPATCH_ISSUED')",
        &[&job],
    ).unwrap().get::<_,i64>(0),0);
    assert_eq!(fixture.db.query_one(
        "SELECT count(*) FROM jobs WHERE client_request_id='pg-release-predispatch-ordinary-001'", &[]
    ).unwrap().get::<_,i64>(0),1);
    eprintln!("PREDISPATCH_ORDINARY_NATIVE_ARTIFACT_PASS_RELEASE_UNCHANGED");
}

#[test]
#[ignore = "launches disposable PostgreSQL18, real HTTP MCP and Git physical files"]
fn pg_native_mutation_crash_intent_fences_new_jobs_and_close_until_exact_replay() {
    use sha2::Digest as _;
    let mut fixture = Fixture::new();
    let repo = fixture.repo();
    let endpoint = fixture.endpoint();
    let id = "ws-pg-batch-crash";
    let opened = call(
        &endpoint,
        "workspace.open",
        json!({"workspaceId":id,"sourceRepo":repo,"sourceRevision":"HEAD"}),
    );
    assert_ne!(opened["isError"], true, "{opened}");
    let request = json!({
        "workspaceId":id,
        "mutations":[
            {"mode":"WRITE","relativePath":"first.txt","content":"first-committed"},
            {"mode":"WRITE","relativePath":"second.txt","content":"second-committed"}
        ]
    });
    let typed: ordivon_runtime_core::WorkspaceMutateRequest =
        serde_json::from_value(request.clone()).unwrap();
    let digest = |v: &[u8]| format!("sha256:{}", hex::encode(sha2::Sha256::digest(v)));
    let request_digest = digest(&serde_json::to_vec(&typed).unwrap());
    let intent = fixture
        .root
        .join("store/cache/workspaces")
        .join(id)
        .join("pending-mutation-v1.json");
    fs::create_dir_all(intent.parent().unwrap()).unwrap();
    let pending = json!({
        "schemaVersion":1,"workspaceId":id,"requestDigest":request_digest,
        "entries":[
            {"relativePath":"first.txt","beforeContent":null,"beforeDigest":null,
             "afterContent":"first-committed","afterDigest":digest(b"first-committed")},
            {"relativePath":"second.txt","beforeContent":null,"beforeDigest":null,
             "afterContent":"second-committed","afterDigest":digest(b"second-committed")}
        ]
    });
    fs::write(&intent, serde_json::to_vec(&pending).unwrap()).unwrap();
    fs::File::open(&intent).unwrap().sync_all().unwrap();
    let worktree = fixture.root.join("store/workspaces").join(id);
    fs::write(worktree.join("first.txt"), "first-committed").unwrap();
    assert!(!worktree.join("second.txt").exists());
    assert!(intent.is_file());

    let denied_close = call(
        &endpoint,
        "workspace.close",
        json!({"workspaceId":id,"consumerReleased":true,"force":true}),
    );
    assert_eq!(
        denied_close["structuredContent"]["error"]["code"], "RECONCILIATION_REQUIRED",
        "{denied_close}"
    );
    let denied_job = call(
        &endpoint,
        "workspace.exec",
        json!({"clientRequestId":"pg-batch-crash-job-must-not-be-admitted",
            "execution":{"workspaceId":id,"cwdRelative":".","executable":"/usr/bin/true",
            "timeoutMs":10000},"waitMs":0}),
    );
    assert_eq!(denied_job["isError"], true, "{denied_job}");
    assert_eq!(
        denied_job["structuredContent"]["error"]["code"], "WORKSPACE_STATE_MISMATCH",
        "{denied_job}"
    );
    assert_eq!(
        fixture
            .db
            .query_one(
                "SELECT count(*) FROM jobs WHERE client_request_id='pg-batch-crash-job-must-not-be-admitted'",
                &[],
            )
            .unwrap()
            .get::<_, i64>(0),
        0
    );
    let another = call(
        &endpoint,
        "workspace.mutate",
        json!({"workspaceId":id,"mutations":[
            {"mode":"WRITE","relativePath":"unrelated.txt","content":"NO"}
        ]}),
    );
    assert_eq!(
        another["structuredContent"]["error"]["code"], "RECONCILIATION_REQUIRED",
        "{another}"
    );
    assert!(intent.is_file());
    assert!(!worktree.join("unrelated.txt").exists());

    let recovered = call(&endpoint, "workspace.mutate", request);
    assert_ne!(recovered["isError"], true, "{recovered}");
    assert_eq!(
        fs::read_to_string(worktree.join("first.txt")).unwrap(),
        "first-committed"
    );
    assert_eq!(
        fs::read_to_string(worktree.join("second.txt")).unwrap(),
        "second-committed"
    );
    assert!(!intent.exists());
    // Only after the physical batch completed may the same PG Job admission
    // owner issue a new execution. A failed prior attempt was never persisted.
    let allowed = call(
        &endpoint,
        "workspace.exec",
        json!({"clientRequestId":"pg-batch-crash-job-after-recovery",
            "execution":{"workspaceId":id,"cwdRelative":".","executable":"/usr/bin/true",
            "timeoutMs":10000},"waitMs":0}),
    );
    assert_ne!(allowed["isError"], true, "{allowed}");
    assert_eq!(
        fixture
            .db
            .query_one("SELECT count(*) FROM jobs", &[])
            .unwrap()
            .get::<_, i64>(0),
        1
    );
}

#[test]
#[ignore = "launches a disposable native PostgreSQL cluster; run explicitly"]
fn fresh_pg_mcp_real_database_and_no_false_launch_success() {
    let mut fixture = Fixture::new();
    let repo = fixture.repo();
    let endpoint = fixture.endpoint();
    let tools = rpc(&endpoint, "tools/list", json!({}));
    let names = tools["tools"]
        .as_array()
        .unwrap()
        .iter()
        .map(|t| t["name"].as_str().unwrap())
        .collect::<Vec<_>>();
    // Original D #2333 adds exactly the three native physical Claim tools to
    // the already qualified PG-only catalog; a stale 20-tool test must not
    // reject the legitimate exact 23-tool source without inspecting names.
    assert_eq!(names.len(), 23, "{names:?}");
    for claim_tool in [
        "workspace.claim.reserve",
        "workspace.claim.get",
        "workspace.claim.release",
    ] {
        assert!(names.contains(&claim_tool), "{names:?}");
    }
    // Operator startup receipt must describe the *same* catalog advertised
    // by the mature MCP SDK; it cannot silently retain an obsolete count.
    let startup = fs::read_to_string(fixture.root.join("endpoint.log")).unwrap();
    assert!(
        startup.contains(&format!("({} tools)", names.len())),
        "startup catalog differs from actual MCP tools/list: {startup}"
    );
    assert!(names.contains(&"runtime.describe"));
    assert!(names.contains(&"job.list"));
    let describe = call(&endpoint, "runtime.describe", json!({}));
    assert_ne!(describe["isError"], true, "{describe}");
    assert_eq!(describe["structuredContent"]["node"]["nodeId"], "linux-pg");
    // A real MCP client can send an invalid tool argument even if the
    // advertised schema says schemaVersion is an integer. The server must
    // reject, rather than silently treating a malformed version as v1.
    for invalid in [json!("1"), Value::Null, json!(true), json!(1.5)] {
        let malformed_version = call(
            &endpoint,
            "runtime.describe",
            json!({"schemaVersion": invalid}),
        );
        assert_eq!(malformed_version["isError"], true, "{malformed_version}");
    }
    // ECC real MCP schema: the shared RuntimeDescribeRequest contract uses
    // deny_unknown_fields. PG must not silently accept fields the tool schema
    // does not admit (including when schemaVersion itself is omitted).
    for invalid in [
        json!({"schemaVersion": 1, "unexpected": true}),
        json!({"unexpected": "field"}),
    ] {
        let result = call(&endpoint, "runtime.describe", invalid);
        assert_eq!(
            result["isError"], true,
            "PG bypassed shared input contract: {result}"
        );
    }
    let explicit_v1 = call(&endpoint, "runtime.describe", json!({"schemaVersion":1}));
    assert_ne!(explicit_v1["isError"], true, "{explicit_v1}");
    assert_eq!(
        describe["structuredContent"]["targets"][0]["immutableInputs"],
        false
    );
    let empty = call(&endpoint, "job.list", json!({}));
    assert_ne!(empty["isError"], true, "{empty}");
    assert_eq!(
        empty["structuredContent"]["jobs"].as_array().unwrap().len(),
        0
    );
    // ECC / M1->M3: Universal Workspace errors are not MCP adapter outages.
    // Preserve existing ToolError::from(UniversalExecError) public contract.
    for (tool, args) in [
        (
            "workspace.read",
            json!({"workspaceId":"ws-absent-semantic",
            "relativePath":"proof.txt","maxBytes":256,"mode":"FULL"}),
        ),
        (
            "workspace.read",
            json!({"workspaceId":"ws-absent-semantic",
            "relativePath":"proof.txt","maxBytes":256,"mode":"SLICE","offset":0}),
        ),
        (
            "workspace.diff",
            json!({"workspaceId":"ws-absent-semantic","maxBytes":4096}),
        ),
        (
            "workspace.changes",
            json!({"workspaceId":"ws-absent-semantic","limit":10,"maxBytes":2048}),
        ),
    ] {
        let result = call(&endpoint, tool, args);
        assert_eq!(result["isError"], true, "{tool}: {result}");
        assert_eq!(
            result["structuredContent"]["error"]["code"], "WORKSPACE_NOT_FOUND",
            "{tool} reported false internal outage: {result}"
        );
        assert_eq!(
            result["structuredContent"]["error"]["origin"], "workspace_executor",
            "{tool}: {result}"
        );
        assert_eq!(
            result["structuredContent"]["error"]["retryClass"], "never",
            "{tool}: {result}"
        );
        assert_eq!(
            result["structuredContent"]["error"]["commitState"], "not_committed",
            "{tool}: {result}"
        );
    }
    assert!(names.contains(&"workspace.execPlan"));
    assert!(names.contains(&"job.get"));
    fs::write(repo.join("proof.txt"), "PG Workspace proof\n").unwrap();
    use base64::Engine as _;
    let png=base64::engine::general_purpose::STANDARD.decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScL/wwAAAABJRU5ErkJggg=="
    ).unwrap();
    fs::write(repo.join("tiny.png"), &png).unwrap();
    let png_digest = format!("sha256:{}", hex::encode(sha2::Sha256::digest(&png)));
    assert!(Command::new("git")
        .arg("-C")
        .arg(&repo)
        .args(["add", "proof.txt", "tiny.png"])
        .output()
        .unwrap()
        .status
        .success());
    assert!(Command::new("git")
        .arg("-C")
        .arg(&repo)
        .args([
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-m",
            "proof"
        ])
        .output()
        .unwrap()
        .status
        .success());
    let open = call(
        &endpoint,
        "workspace.open",
        json!({"workspaceId":"ws-pg-consumer","sourceRepo":repo,"sourceRevision":"HEAD"}),
    );
    assert_ne!(open["isError"], true, "{open}");
    let duplicate = call(
        &endpoint,
        "workspace.open",
        json!({"workspaceId":"ws-pg-consumer","sourceRepo":repo,"sourceRevision":"HEAD"}),
    );
    assert_eq!(duplicate["isError"], true, "{duplicate}");
    assert_eq!(
        duplicate["structuredContent"]["error"]["code"], "WORKSPACE_EXISTS",
        "M3 duplicate Workspace identity must be preserved across PG M5/M8: {duplicate}"
    );
    let found = call(
        &endpoint,
        "workspace.get",
        json!({"workspaceId":"ws-pg-consumer"}),
    );
    assert_ne!(found["isError"], true, "{found}");
    assert_eq!(found["structuredContent"]["workspaceId"], "ws-pg-consumer");
    assert_eq!(found["structuredContent"]["headMode"], "detached");
    // Real MCP consumer must reflect Git state after Workspace creation.
    // A user can legitimately attach a branch using an execution command;
    // the original PG projection incorrectly hard-coded "detached".
    let physical_workspace = fixture.root.join("store/workspaces/ws-pg-consumer");
    let switch = Command::new("git")
        .arg("-C")
        .arg(&physical_workspace)
        .args(["switch", "-c", "runtime-live-branch"])
        .output()
        .unwrap();
    assert!(switch.status.success(), "{switch:?}");
    let branch = call(
        &endpoint,
        "workspace.get",
        json!({"workspaceId":"ws-pg-consumer"}),
    );
    assert_ne!(branch["isError"], true, "{branch}");
    assert_eq!(
        branch["structuredContent"]["headMode"], "branch",
        "PG workspace.get must report actual Git branch mode"
    );
    let detach = Command::new("git")
        .arg("-C")
        .arg(&physical_workspace)
        .args(["switch", "--detach"])
        .output()
        .unwrap();
    assert!(detach.status.success(), "{detach:?}");
    let missing = call(
        &endpoint,
        "workspace.get",
        json!({"workspaceId":"ws-pg-does-not-exist"}),
    );
    assert_eq!(missing["isError"], true, "{missing}");
    assert_eq!(
        missing["structuredContent"]["error"]["code"], "WORKSPACE_NOT_FOUND",
        "PG Workspace read must preserve M3's precise missing-identity error: {missing}"
    );
    let inventoried = call(&endpoint, "workspace.list", json!({"limit":10}));
    assert_ne!(inventoried["isError"], true, "{inventoried}");
    assert_eq!(
        inventoried["structuredContent"]["workspaces"][0]["workspaceId"],
        "ws-pg-consumer"
    );
    assert!(
        inventoried["structuredContent"]["workspaces"][0]
            .get("sourceStateDigest")
            .is_none(),
        "lightweight list must omit the optional digest: {inventoried}"
    );
    let exact = call(
        &endpoint,
        "workspace.get",
        json!({"workspaceId":"ws-pg-consumer"}),
    );
    let inventoried_with_digest = call(
        &endpoint,
        "workspace.list",
        json!({"limit":10, "includeSourceStateDigest":true}),
    );
    assert_ne!(
        inventoried_with_digest["isError"], true,
        "{inventoried_with_digest}"
    );
    assert_eq!(
        inventoried_with_digest["structuredContent"]["workspaces"][0]["sourceStateDigest"],
        exact["structuredContent"]["sourceStateDigest"],
        "opt-in list digest must use the same canonical workspace source observation"
    );
    // PG must preserve the existing native Runtime inventory uncertainty contract:
    // an invalid physical Workspace must not vanish as if it never existed.
    fs::create_dir(fixture.root.join("store/workspaces/invalid current id")).unwrap();
    let inventory_with_issue = call(&endpoint, "workspace.list", json!({"limit":10}));
    assert_ne!(
        inventory_with_issue["isError"], true,
        "{inventory_with_issue}"
    );
    assert!(
        inventory_with_issue["structuredContent"]["issues"]
            .as_array()
            .is_some_and(|issues| issues.iter().any(|issue| {
                issue["workspaceId"] == "invalid current id"
                    && issue["stage"] == "inventory"
                    && issue["code"] == "INVALID_REQUEST"
            })),
        "PG Workspace inventory falsely hid an invalid physical candidate: {inventory_with_issue}"
    );
    // Real PG MCP regression: list(limit=1) must not inspect every older
    // Workspace or fail the entire page because one Git checkout is corrupt.
    // Its physical cursor must still advance past an unprojectable record.
    let broken_open = call(
        &endpoint,
        "workspace.open",
        json!({"workspaceId":"ws-00-corrupt-list","sourceRepo":repo,"sourceRevision":"HEAD"}),
    );
    assert_ne!(broken_open["isError"], true, "{broken_open}");
    let broken_git = fixture
        .root
        .join("store/workspaces/ws-00-corrupt-list/.git");
    let original_git = fs::read(&broken_git).expect("Git worktree metadata file");
    fs::write(&broken_git, "gitdir: /nonexistent/broken-workspace-list\n").unwrap();
    let broken_page = call(&endpoint, "workspace.list", json!({"limit":1}));
    assert_ne!(broken_page["isError"], true, "{broken_page}");
    assert_eq!(
        broken_page["structuredContent"]["workspaces"]
            .as_array()
            .unwrap()
            .len(),
        0,
        "invalid page must not silently claim a healthy Workspace: {broken_page}"
    );
    assert!(
        broken_page["structuredContent"]["issues"]
            .as_array()
            .is_some_and(|issues| issues.iter().any(|issue| {
                issue["workspaceId"] == "ws-00-corrupt-list" && issue["stage"] == "projection"
            })),
        "PG list must explicitly report a local projection failure: {broken_page}"
    );
    let page_cursor = broken_page["structuredContent"]["nextCursor"].clone();
    assert!(
        page_cursor.is_object(),
        "broken page must advance: {broken_page}"
    );
    let healthy_page = call(
        &endpoint,
        "workspace.list",
        json!({"limit":1, "cursor":page_cursor}),
    );
    assert_ne!(healthy_page["isError"], true, "{healthy_page}");
    assert_eq!(
        healthy_page["structuredContent"]["workspaces"][0]["workspaceId"], "ws-pg-consumer",
        "next page must remain visible after a corrupt earlier Workspace"
    );
    fs::write(&broken_git, original_git).unwrap();
    let broken_close = call(
        &endpoint,
        "workspace.close",
        json!({"workspaceId":"ws-00-corrupt-list","consumerReleased":true}),
    );
    assert_ne!(broken_close["isError"], true, "{broken_close}");
    let text = call(
        &endpoint,
        "workspace.read",
        json!({"workspaceId":"ws-pg-consumer","relativePath":"proof.txt","maxBytes":200,"mode":"FULL"}),
    );
    assert_ne!(text["isError"], true, "{text}");
    assert_eq!(text["structuredContent"]["content"], "PG Workspace proof\n");
    let file_digest = text["structuredContent"]["digest"]
        .as_str()
        .unwrap()
        .to_string();
    let file = call(
        &endpoint,
        "workspace.file",
        json!({"workspaceId":"ws-pg-consumer",
        "relativePath":"proof.txt","expectedDigest":file_digest,"maxBytes":200}),
    );
    assert_ne!(file["isError"], true, "{file}");
    assert_eq!(file["content"][0]["type"], "resource", "{file}");
    assert_eq!(
        file["structuredContent"]["mediaType"],
        "application/octet-stream"
    );
    let image = call(
        &endpoint,
        "workspace.content",
        json!({"workspaceId":"ws-pg-consumer",
        "relativePath":"tiny.png","expectedDigest":png_digest,"maxBytes":4000}),
    );
    assert_ne!(image["isError"], true, "{image}");
    assert_eq!(image["content"][0]["type"], "image", "{image}");
    assert_eq!(image["structuredContent"]["mediaType"], "image/png");
    let image_wrong = call(
        &endpoint,
        "workspace.content",
        json!({"workspaceId":"ws-pg-consumer",
        "relativePath":"tiny.png","expectedDigest":"sha256:".to_string()+&"0".repeat(64),"maxBytes":4000}),
    );
    assert_eq!(image_wrong["isError"], true, "{image_wrong}");
    let diff = call(
        &endpoint,
        "workspace.diff",
        json!({"workspaceId":"ws-pg-consumer","maxBytes":4096}),
    );
    assert_ne!(diff["isError"], true, "{diff}");
    let changes = call(
        &endpoint,
        "workspace.changes",
        json!({"workspaceId":"ws-pg-consumer","limit":10,"maxBytes":2048}),
    );
    assert_ne!(changes["isError"], true, "{changes}");
    // Native M3 Universal Workspace preflight must cross M5/PG and M1 MCP
    // without losing its typed contract. A prior revision is not a
    // PostgreSQL outage; it has not changed any file or committed any effect.
    let stale_revision = call(
        &endpoint,
        "workspace.mutate",
        json!({"workspaceId":"ws-pg-consumer","mutations":[{
            "mode":"WRITE","relativePath":"proof.txt","content":"must-not-write"
        }]}),
    );
    assert_eq!(stale_revision["isError"], true, "{stale_revision}");
    assert_eq!(
        stale_revision["structuredContent"]["error"]["code"], "REVISION_MISMATCH",
        "PG->MCP must preserve native Universal Workspace revision errors: {stale_revision}"
    );
    assert_eq!(
        stale_revision["structuredContent"]["error"]["commitState"], "not_committed",
        "preflight failure must not be an ambiguous filesystem effect: {stale_revision}"
    );
    assert_eq!(
        fs::read_to_string(
            fixture
                .root
                .join("store")
                .join("workspaces")
                .join("ws-pg-consumer")
                .join("proof.txt")
        )
        .unwrap(),
        "PG Workspace proof\n",
        "a stale expectedDigest must not mutate a physical Workspace"
    );
    let modified = call(
        &endpoint,
        "workspace.mutate",
        json!({"workspaceId":"ws-pg-consumer","mutations":[{"mode":"WRITE","relativePath":"fresh-only.txt","content":"new-pg-file"}]}),
    );
    assert_ne!(modified["isError"], true, "{modified}");
    let after = call(
        &endpoint,
        "workspace.read",
        json!({"workspaceId":"ws-pg-consumer","relativePath":"fresh-only.txt","maxBytes":100,"mode":"FULL"}),
    );
    assert_eq!(after["structuredContent"]["content"], "new-pg-file");
    let open2 = call(
        &endpoint,
        "workspace.open",
        json!({"workspaceId":"ws-pg-close","sourceRepo":repo,"sourceRevision":"HEAD"}),
    );
    assert_ne!(open2["isError"], true, "{open2}");
    let dirty_path = fixture
        .root
        .join("store")
        .join("workspaces")
        .join("ws-pg-close")
        .join("user-note.txt");
    fs::write(&dirty_path, "protect uncommitted consumer data").unwrap();
    let dirty_close = call(
        &endpoint,
        "workspace.close",
        json!({"workspaceId":"ws-pg-close","consumerReleased":true}),
    );
    assert_eq!(dirty_close["isError"], true, "{dirty_close}");
    assert_eq!(
        dirty_close["structuredContent"]["error"]["code"], "WORKSPACE_DIRTY",
        "M3 must not lose dirty Workspace protection through M8: {dirty_close}"
    );
    assert!(
        dirty_path.is_file(),
        "preflight failure cannot delete an uncommitted file"
    );
    fs::remove_file(&dirty_path).unwrap();
    let closed = call(
        &endpoint,
        "workspace.close",
        json!({"workspaceId":"ws-pg-close","consumerReleased":true}),
    );
    assert_ne!(closed["isError"], true, "{closed}");
    assert_eq!(closed["structuredContent"]["removed"], true);
    // M4 admission must preserve M3 missing-Workspace semantics to the
    // Gateway's actual workspace.exec consumer. No Job should be admitted.
    let missing_execution = call(
        &endpoint,
        "workspace.exec",
        json!({"clientRequestId":"pg-mcp-missing-workspace-0001",
            "execution":{"workspaceId":"ws-pg-does-not-exist",
            "executable":"/usr/bin/printf","args":["should-not-start"],
            "cwdRelative":".","timeoutMs":5000},"waitMs":0}),
    );
    assert_eq!(missing_execution["isError"], true, "{missing_execution}");
    assert_eq!(
        missing_execution["structuredContent"]["error"]["code"], "WORKSPACE_NOT_FOUND",
        "M4 preflight cannot collapse M3 error into PG outage: {missing_execution}"
    );
    assert_eq!(
        fixture
            .db
            .query_one("SELECT count(*) FROM jobs", &[])
            .unwrap()
            .get::<_, i64>(0),
        0,
        "invalid admission cannot create a durable Job"
    );
    let request = json!({"clientRequestId":"pg-mcp-real-command-0001","execution":{"workspaceId":"ws-pg-consumer","executable":"/usr/bin/printf","args":["real-pg-runner-output"],"cwdRelative":".","timeoutMs":5000},"waitMs":0});
    let exec = call(&endpoint, "workspace.exec", request.clone());
    let job = fixture
        .db
        .query_one("SELECT job_id FROM jobs", &[])
        .unwrap()
        .get::<_, String>(0);
    assert_eq!(
        fixture
            .db
            .query_one("SELECT count(*) FROM jobs", &[])
            .unwrap()
            .get::<_, i64>(0),
        1
    );
    assert_eq!(
        fixture
            .db
            .query_one(
                "SELECT count(*) FROM job_events WHERE event_type='DISPATCH_ISSUED'",
                &[]
            )
            .unwrap()
            .get::<_, i64>(0),
        1
    );
    if exec["isError"] == true {
        assert_eq!(
            exec["structuredContent"]["error"]["code"], "DISPATCH_OUTCOME_UNKNOWN",
            "{exec}"
        );
    }
    let get = call(&endpoint, "job.get", json!({"jobId":job}));
    assert_ne!(get["isError"], true, "{get}");
    assert_eq!(
        get["structuredContent"]["job"]["semanticCompletionEvaluated"],
        false
    );
    // Gateway's live execution_get consumer always supplies change_or_terminal.
    let gateway_observe = call(
        &endpoint,
        "job.observe",
        json!({"jobId":job,"waitMs":0,"waitUntil":"change_or_terminal",
               "stdoutTailBytes":0,"stderrTailBytes":0}),
    );
    assert_ne!(gateway_observe["isError"], true, "{gateway_observe}");
    assert_eq!(gateway_observe["structuredContent"]["jobId"], job);
    let gateway_wait = call(
        &endpoint,
        "job.observe",
        json!({"jobId":job,"waitMs":100,"waitUntil":"change_or_terminal",
               "stdoutTailBytes":0,"stderrTailBytes":0}),
    );
    assert_ne!(gateway_wait["isError"], true, "{gateway_wait}");
    assert_eq!(gateway_wait["structuredContent"]["jobId"], job);
    let listed = call(&endpoint, "job.list", json!({"limit":5}));
    assert_ne!(listed["isError"], true, "{listed}");
    assert_eq!(listed["structuredContent"]["jobs"][0]["jobId"], job);
    assert_eq!(
        listed["structuredContent"]["jobs"]
            .as_array()
            .unwrap()
            .len(),
        1
    );
    let replay = call(&endpoint, "workspace.exec", request);
    assert_ne!(replay["isError"], true, "{replay}");
    assert_eq!(replay["structuredContent"]["jobId"], job);
    assert_eq!(
        fixture
            .db
            .query_one(
                "SELECT count(*) FROM job_events WHERE event_type='DISPATCH_ISSUED'",
                &[]
            )
            .unwrap()
            .get::<_, i64>(0),
        1
    );
    let conflict = call(
        &endpoint,
        "workspace.exec",
        json!({"clientRequestId":"pg-mcp-real-command-0001","execution":{"workspaceId":"ws-pg-consumer","executable":"/usr/bin/false","cwdRelative":"."},"waitMs":0}),
    );
    assert_eq!(
        conflict["structuredContent"]["error"]["code"],
        "IDEMPOTENCY_CONFLICT"
    );
    // Byte-projection fixture, explicitly not a Runner success/terminal fixture.
    let row = fixture
        .db
        .query_one("SELECT attempt_id,bundle_path FROM attempts", &[])
        .unwrap();
    let attempt: String = row.get(0);
    let bundle: String = row.get(1);
    fs::write(
        PathBuf::from(&bundle).join("fixture.txt"),
        b"verified PG artifact",
    )
    .unwrap();
    use sha2::{Digest, Sha256};
    let digest = format!(
        "sha256:{}",
        hex::encode(Sha256::digest(b"verified PG artifact"))
    );
    fixture.db.execute("INSERT INTO artifacts(artifact_id,job_id,attempt_id,kind,relative_path,digest,media_type,byte_length) VALUES('fixture',$1,$2,'test_fixture','fixture.txt',$3,'text/plain',20)",&[&job,&attempt,&digest]).unwrap();
    let artifact = call(
        &endpoint,
        "artifact.read",
        json!({"jobId":job,"artifactId":"fixture","offset":0,"maxBytes":100}),
    );
    assert_eq!(
        artifact["structuredContent"]["content"], "verified PG artifact",
        "{artifact}"
    );
    let raw_artifact = call(
        &endpoint,
        "artifact.content",
        json!({"jobId":job,"artifactId":"fixture","maxBytes":200}),
    );
    assert_ne!(raw_artifact["isError"], true, "{raw_artifact}");
    assert_eq!(
        raw_artifact["content"][0]["type"], "resource",
        "{raw_artifact}"
    );
    assert_eq!(raw_artifact["structuredContent"]["byteLength"], 20);
    fs::write(PathBuf::from(&bundle).join("fixture.txt"), b"corrupt").unwrap();
    let corrupt = call(
        &endpoint,
        "artifact.read",
        json!({"jobId":job,"artifactId":"fixture","offset":0,"maxBytes":100}),
    );
    assert_eq!(corrupt["isError"], true);
    assert!(!fixture.root.join("store/registry.sqlite").exists());
    eprintln!("real PostgreSQL + HTTP MCP verified; native initial launch outcome: {exec}");
}

#[test]
#[ignore = "uses a disposable PG18 and native Runner to consume binary Artifact bytes"]
fn pg_binary_artifact_representation_is_not_registry_failure() {
    use sha2::Digest as _;

    let mut fixture = Fixture::new();
    fixture.host_visible_test_runner = true;
    let repo = fixture.repo();
    let endpoint = fixture.endpoint();
    let opened = call(
        &endpoint,
        "workspace.open",
        json!({"workspaceId":"ws-pg-binary-artifact","sourceRepo":repo,"sourceRevision":"HEAD"}),
    );
    assert_ne!(opened["isError"], true, "{opened}");
    let submitted = call(
        &endpoint,
        "workspace.exec",
        json!({
            "clientRequestId":"pg-binary-artifact-original",
            "execution":{
                "workspaceId":"ws-pg-binary-artifact",
                "executable":"/usr/bin/python3",
                "args":["-c","import sys; sys.stdout.buffer.write(bytes([255,0,65,128]))"],
                "cwdRelative":".",
                "timeoutMs":10000
            },
            "waitMs":12000,
            "stdoutTailBytes":0,
        }),
    );
    assert_ne!(submitted["isError"], true, "{submitted}");
    let observed = &submitted["structuredContent"];
    assert_eq!(observed["executionDisposition"], "succeeded", "{observed}");
    let job = observed["jobId"].as_str().unwrap();
    let stdout = observed["artifacts"]
        .as_array()
        .unwrap()
        .iter()
        .find(|artifact| artifact["kind"] == "stdout")
        .expect("registered stdout");
    let id = stdout["artifactId"].as_str().unwrap();
    let digest = format!(
        "sha256:{}",
        hex::encode(sha2::Sha256::digest([0xff, 0x00, 0x41, 0x80]))
    );
    assert_eq!(stdout["digest"], digest);
    assert_eq!(stdout["retainedBytes"], 4);
    let binary_text = call(
        &endpoint,
        "artifact.read",
        json!({"jobId":job,"artifactId":id,"offset":0,"maxBytes":100}),
    );
    assert_eq!(binary_text["isError"], true, "{binary_text}");
    assert_eq!(
        binary_text["structuredContent"]["error"]["code"], "ARTIFACT_NOT_UTF8",
        "{binary_text}"
    );
    assert_eq!(
        binary_text["structuredContent"]["error"]["retryable"],
        false
    );
    assert_eq!(
        binary_text["structuredContent"]["error"]["field"],
        "artifactId"
    );
    let binary_content = call(
        &endpoint,
        "artifact.content",
        json!({"jobId":job,"artifactId":id,"maxBytes":100}),
    );
    assert_ne!(binary_content["isError"], true, "{binary_content}");
    assert_eq!(binary_content["structuredContent"]["digest"], digest);
    assert_eq!(binary_content["structuredContent"]["byteLength"], 4);
    assert_eq!(binary_content["content"][0]["resource"]["blob"], "/wBBgA==");
    for tool in ["artifact.read", "artifact.content"] {
        let mut args = json!({"jobId":job,"artifactId":"absent-fixture","maxBytes":100});
        if tool == "artifact.read" {
            args["offset"] = json!(0);
        }
        let missing = call(&endpoint, tool, args);
        assert_eq!(missing["isError"], true, "{missing}");
        assert_eq!(
            missing["structuredContent"]["error"]["code"], "ARTIFACT_NOT_FOUND",
            "{missing}"
        );
        assert_eq!(missing["structuredContent"]["error"]["retryable"], false);
        assert_eq!(missing["structuredContent"]["error"]["field"], "artifactId");
    }
    // Same-length damage to our disposable fixture is an integrity conflict,
    // not a representational failure and not a PostgreSQL outage.
    let row = fixture.db.query_one(
        "SELECT a.bundle_path,r.relative_path FROM artifacts r JOIN attempts a ON a.attempt_id=r.attempt_id WHERE r.job_id=$1 AND r.artifact_id=$2",
        &[&job,&id],
    ).unwrap();
    let path = PathBuf::from(row.get::<_, String>(0)).join(row.get::<_, String>(1));
    assert!(path.starts_with(&fixture.root));
    fs::write(path, [0xfe, 0x00, 0x41, 0x80]).unwrap();
    for tool in ["artifact.read", "artifact.content"] {
        let mut args = json!({"jobId":job,"artifactId":id,"maxBytes":100});
        if tool == "artifact.read" {
            args["offset"] = json!(0);
        }
        let damaged = call(&endpoint, tool, args);
        assert_eq!(damaged["isError"], true, "{damaged}");
        assert_eq!(
            damaged["structuredContent"]["error"]["code"], "ARTIFACT_IDENTITY_CONFLICT",
            "{damaged}"
        );
    }
}

/// Real native PG18+HTTP MCP+Git consumer for the existing bounded
/// Workspace.list projection. Pages must remain stable with >4 physical
/// Workspaces; a broken Git checkout is a local issue, not a lost cursor.
#[test]
#[ignore = "uses a disposable PG18 fixture and 12 real Git worktrees"]
fn pg_workspace_list_many_git_worktrees_preserves_order_and_local_issues() {
    use std::collections::BTreeSet;
    let mut fixture = Fixture::new();
    let repo = fixture.repo();
    let endpoint = fixture.endpoint();
    let ids = (0..12)
        .map(|i| format!("ws-r28-page-{i:02}"))
        .collect::<Vec<_>>();
    for id in &ids {
        let opened = call(
            &endpoint,
            "workspace.open",
            json!({"workspaceId":id,"sourceRepo":repo,"sourceRevision":"HEAD"}),
        );
        assert_ne!(opened["isError"], true, "open {id}: {opened}");
    }
    let dirty_id = &ids[4];
    fs::write(
        fixture
            .root
            .join("store/workspaces")
            .join(dirty_id)
            .join("untracked.txt"),
        b"R28_DIRTY_WORKTREE",
    )
    .unwrap();
    let corrupt_id = &ids[8];
    let corrupt_git = fixture
        .root
        .join("store/workspaces")
        .join(corrupt_id)
        .join(".git");
    let original_git = fs::read(&corrupt_git).unwrap();
    fs::write(&corrupt_git, "gitdir: /nonexistent/r28-corrupt-worktree\n").unwrap();

    let start = Instant::now();
    let full = call(&endpoint, "workspace.list", json!({"limit":20}));
    let full_ms = start.elapsed().as_millis();
    assert_ne!(full["isError"], true, "{full}");
    let rows = full["structuredContent"]["workspaces"]
        .as_array()
        .expect("physical Workspace page");
    assert_eq!(
        rows.len(),
        11,
        "corrupt Worktree must remain an issue: {full}"
    );
    assert!(full["structuredContent"]["nextCursor"].is_null(), "{full}");
    let issues = full["structuredContent"]["issues"].as_array().unwrap();
    assert!(
        issues.iter().any(|item| {
            item["workspaceId"] == corrupt_id.as_str() && item["stage"] == "projection"
        }),
        "physical corrupt Worktree was silently hidden: {full}"
    );
    let returned = rows
        .iter()
        .map(|r| r["workspaceId"].as_str().unwrap().to_string())
        .collect::<BTreeSet<_>>();
    assert_eq!(returned.len(), 11);
    for id in &ids {
        assert_eq!(
            returned.contains(id),
            id != corrupt_id,
            "missing or false Workspace {id}"
        );
    }
    assert!(
        rows.iter()
            .find(|r| r["workspaceId"] == dirty_id.as_str())
            .unwrap()["dirty"]
            == true
    );
    for pair in rows.windows(2) {
        let earlier = pair[0]["createdAtMs"].as_u64().unwrap();
        let later = pair[1]["createdAtMs"].as_u64().unwrap();
        assert!(
            earlier > later
                || (earlier == later
                    && pair[0]["workspaceId"].as_str().unwrap()
                        < pair[1]["workspaceId"].as_str().unwrap())
        );
    }

    let mut paged = BTreeSet::new();
    let mut cursor = Value::Null;
    let mut pages = 0;
    let started = Instant::now();
    loop {
        pages += 1;
        assert!(pages <= 7, "physical cursor was stuck on corrupt Workspace");
        let page = call(
            &endpoint,
            "workspace.list",
            json!({"limit":3,"cursor":cursor}),
        );
        assert_ne!(page["isError"], true, "{page}");
        for row in page["structuredContent"]["workspaces"].as_array().unwrap() {
            assert!(
                paged.insert(row["workspaceId"].as_str().unwrap().to_string()),
                "duplicate across stable physical cursors: {page}"
            );
        }
        cursor = page["structuredContent"]["nextCursor"].clone();
        if cursor.is_null() {
            break;
        }
    }
    assert_eq!(paged, returned, "paged and full inventory disagree");
    let paged_ms = started.elapsed().as_millis();
    // Diagnostic only, not a flaky threshold: stable repeated warm reads
    // compare identical real MCP semantics on serial and bounded projections.
    let mut full_samples_ms = Vec::with_capacity(5);
    for _ in 0..5 {
        let t = Instant::now();
        let repeat = call(&endpoint, "workspace.list", json!({"limit":20}));
        assert_ne!(repeat["isError"], true, "{repeat}");
        let seen = repeat["structuredContent"]["workspaces"]
            .as_array()
            .unwrap()
            .iter()
            .map(|r| r["workspaceId"].as_str().unwrap().to_string())
            .collect::<BTreeSet<_>>();
        assert_eq!(seen, returned, "repeated native read changed identity set");
        full_samples_ms.push(t.elapsed().as_millis());
    }
    full_samples_ms.sort_unstable();
    let median_full_ms = full_samples_ms[2];
    fs::write(&corrupt_git, original_git).unwrap();
    eprintln!(
        "R28_PG18_MCP_LIST_12_WORKTREES_P50_MS={median_full_ms} SAMPLES_MS={full_samples_ms:?}"
    );
    eprintln!("R28_PG18_MCP_LIST_12_WORKTREES_PASS full_ms={full_ms} paged_ms={paged_ms} pages={pages} returned={} issues={}",rows.len(),issues.len());
}

/// Cross-owner Harness dispatch fencing carries Runtime-native ForeignReference
/// correlation, not a capability or a new Runtime-owned authority. The PG Job
/// must freeze it in the exact request digest + native Runner plan. Repeating
/// the same request cannot create another Job, while changing the fence
/// generation/digest under the same idempotency key cannot replay the old Job.
/// This is true PostgreSQL + authenticated HTTP MCP + native systemd Runner,
/// not a Python fixture pretending PG accepted metadata.
#[test]
#[ignore = "launches disposable PostgreSQL18, native HTTP MCP and systemd Runner"]
fn native_pg_harness_dispatch_fence_is_frozen_identity_not_authority() {
    let mut fixture = Fixture::new();
    let repo = fixture.repo();
    let endpoint = fixture.endpoint();
    let ws = format!("ws-harness-fence-{}", Uuid::now_v7().simple());
    let opened = call(
        &endpoint,
        "workspace.open",
        json!({"workspaceId":ws,"sourceRepo":repo,"sourceRevision":"HEAD"}),
    );
    assert_ne!(opened["isError"], true, "{opened}");
    let key = format!("harness-fence-{}", Uuid::now_v7().simple());
    let fence_id = format!("fence-{}", Uuid::now_v7().simple());
    let refs = json!([
        {
            "namespace":"ordivon.host",
            "type":"harness_run",
            "id":"run-source-verified-1",
            "generation":"1",
            "digest":format!("sha256:{}", "a".repeat(64))
        },
        {
            "namespace":"ordivon.harness",
            "type":"dispatch_fence",
            "id":fence_id,
            "generation":"3",
            "digest":format!("sha256:{}", "b".repeat(64))
        }
    ]);
    let mut request = json!({
        "clientRequestId":key,
        "execution":{
            "workspaceId":ws,
            "executable":"/usr/bin/printf",
            "args":["harness-fence-pg-native"],
            "cwdRelative":".",
            "timeoutMs":15000,
            "foreignReferences":refs
        },
        "waitMs":0
    });
    let first = call(&endpoint, "workspace.exec", request.clone());
    assert_ne!(
        first["isError"], true,
        "PG Runtime must accept validated identity-only Harness refs, not reject all ForeignReferences: {first}"
    );
    let job = first["structuredContent"]["jobId"]
        .as_str()
        .unwrap()
        .to_owned();
    assert!(!job.is_empty());
    let persisted = fixture
        .db
        .query_one(
            "SELECT request_digest,execution_plan_json FROM jobs WHERE job_id=$1",
            &[&job],
        )
        .unwrap();
    let frozen_identity: String = persisted.get(0);
    assert!(
        frozen_identity.starts_with("runtime-request-v2:"),
        "PG must retain the Runtime-owned canonical proposal identity, not a fabricated digest prefix"
    );
    let frozen_plan: serde_json::Value =
        serde_json::from_str(&persisted.get::<_, String>(1)).unwrap();
    assert_eq!(
        frozen_plan["foreignReferences"], request["execution"]["foreignReferences"],
        "cross-owner references must survive durable PG plan without dropping, sorting, or inventing authority"
    );
    let repeat = call(&endpoint, "workspace.exec", request.clone());
    assert_ne!(
        repeat["isError"], true,
        "exact replay must resolve committed PG identity: {repeat}"
    );
    assert_eq!(repeat["structuredContent"]["jobId"], job);
    assert_eq!(
        fixture
            .db
            .query_one("SELECT count(*) FROM jobs", &[])
            .unwrap()
            .get::<_, i64>(0),
        1
    );

    // The same key with a changed foreign Fence represents a distinct intent,
    // so it cannot quietly borrow or relaunch the original admitted Job.
    request["execution"]["foreignReferences"][1]["generation"] = json!("4");
    let wrong_generation = call(&endpoint, "workspace.exec", request.clone());
    assert_eq!(wrong_generation["isError"], true, "{wrong_generation}");
    assert_eq!(
        wrong_generation["structuredContent"]["error"]["code"], "IDEMPOTENCY_CONFLICT",
        "{wrong_generation}"
    );
    request["execution"]["foreignReferences"][1]["generation"] = json!("3");
    request["execution"]["foreignReferences"][1]["digest"] =
        json!(format!("sha256:{}", "c".repeat(64)));
    let wrong_digest = call(&endpoint, "workspace.exec", request.clone());
    assert_eq!(wrong_digest["isError"], true, "{wrong_digest}");
    assert_eq!(
        wrong_digest["structuredContent"]["error"]["code"], "IDEMPOTENCY_CONFLICT",
        "{wrong_digest}"
    );
    request["execution"]["foreignReferences"][1]["digest"] =
        json!(format!("sha256:{}", "b".repeat(64)));
    let original = request["execution"]["foreignReferences"][1].clone();
    request["clientRequestId"] = json!(format!("harness-invalid-{}", Uuid::now_v7()));
    request["execution"]["foreignReferences"]
        .as_array_mut()
        .unwrap()
        .push(original);
    let duplicate = call(&endpoint, "workspace.exec", request);
    assert_eq!(duplicate["isError"], true, "{duplicate}");
    assert_eq!(
        duplicate["structuredContent"]["error"]["code"], "INVALID_REQUEST",
        "{duplicate}"
    );
    assert_eq!(
        fixture
            .db
            .query_one("SELECT count(*) FROM jobs", &[])
            .unwrap()
            .get::<_, i64>(0),
        1
    );

    let deadline = Instant::now() + Duration::from_secs(70);
    loop {
        let observed = call(
            &endpoint,
            "job.observe",
            json!({"jobId":job,"waitMs":7000,"waitUntil":"terminal",
                "stdoutTailBytes":256,"stderrTailBytes":256}),
        );
        assert_ne!(observed["isError"], true, "{observed}");
        if observed["structuredContent"]["executionTerminal"] == true {
            assert_eq!(
                observed["structuredContent"]["status"], "succeeded",
                "{observed}"
            );
            assert_eq!(
                observed["structuredContent"]["stdoutTail"],
                "harness-fence-pg-native"
            );
            break;
        }
        assert!(
            Instant::now() < deadline,
            "native fenced Job did not converge"
        );
    }
    assert_eq!(
        fixture
            .db
            .query_one(
                "SELECT count(*) FROM job_events WHERE job_id=$1 AND event_type='DISPATCH_ISSUED'",
                &[&job],
            )
            .unwrap()
            .get::<_, i64>(0),
        1,
        "replay/tamper must not launch a second native effect"
    );
    let retained: String = fixture
        .db
        .query_one(
            "SELECT execution_plan_json FROM jobs WHERE job_id=$1",
            &[&job],
        )
        .unwrap()
        .get(0);
    assert_eq!(
        serde_json::from_str::<serde_json::Value>(&retained).unwrap()["foreignReferences"],
        frozen_plan["foreignReferences"]
    );
    assert_eq!(
        fixture
            .db
            .query_one("SELECT request_digest FROM jobs WHERE job_id=$1", &[&job])
            .unwrap()
            .get::<_, String>(0),
        frozen_identity
    );
}

/// A real native MCP process can snapshot a Git Workspace before entering PG
/// admission, while another MCP process closes the Workspace in between.
/// The Git wrapper pauses AFTER the last source-state Git ls-files --others
/// finishes, so it does not fake source contents or alter the git operation.
/// Only the exact PG admission linearization guard can prevent an orphaned Job.
#[test]
#[ignore = "launches disposable PostgreSQL18, two native HTTP MCP services and real Git"]
fn fresh_pg_mcp_run_rejects_workspace_closed_after_source_plan_before_admit() {
    let mut fixture = Fixture::new();
    let repo = fixture.repo();
    let normal_endpoint = fixture.endpoint();
    let id = format!("ws-prelock-{}", Uuid::now_v7().simple());
    let opened = call(
        &normal_endpoint,
        "workspace.open",
        json!({
            "workspaceId":id,
            "sourceRepo":repo,
            "sourceRevision":"HEAD"
        }),
    );
    assert_ne!(opened["isError"], true, "{opened}");

    let shim_dir = fixture.root.join("shim");
    let barrier = fixture.root.join("prelock_barrier");
    fs::create_dir_all(&shim_dir).unwrap();
    fs::create_dir_all(&barrier).unwrap();
    // A second MCP process alone inherits this PATH; the normal MCP and Git
    // close operation continue to use the actual installed git executable.
    let shim = shim_dir.join("git");
    fs::write(
        &shim,
        r#"#!/bin/sh
printf '%s\n' "$*" >> "$ORDIVON_TEST_GIT_BARRIER/invocations"
if [ "$4" = "ls-files" ] && [ "$5" = "--others" ]; then
    /usr/bin/git "$@" > "$ORDIVON_TEST_GIT_BARRIER/real-git-output"
    result=$?
    if [ "$result" -ne 0 ]; then exit "$result"; fi
    : > "$ORDIVON_TEST_GIT_BARRIER/entered"
    n=0
    while [ ! -f "$ORDIVON_TEST_GIT_BARRIER/release" ]; do
      if [ "$n" -gt 300 ]; then exit 73; fi
      n=$((n + 1))
      sleep 0.05
    done
    cat "$ORDIVON_TEST_GIT_BARRIER/real-git-output"
    exit 0
fi
exec /usr/bin/git "$@"
"#,
    )
    .unwrap();
    fs::set_permissions(&shim, fs::Permissions::from_mode(0o755)).unwrap();
    let listener = std::net::TcpListener::bind("127.0.0.1:0").unwrap();
    let addr = listener.local_addr().unwrap();
    drop(listener);
    let runner = std::env::current_exe()
        .unwrap()
        .parent()
        .unwrap()
        .parent()
        .unwrap()
        .join("ordivon-runtime-runner");
    assert!(runner.is_file(), "native Runner binary required");
    let path = format!("{}:{}", shim_dir.display(), std::env::var("PATH").unwrap());
    let log = fs::File::create(fixture.root.join("barrier-endpoint.log")).unwrap();
    let child = Command::new(env!("CARGO_BIN_EXE_ordivon-runtime-pg"))
        .env(
            "ORDIVON_PG_DSN",
            format!(
                "host={} user=runtime_app dbname=postgres",
                fixture.root.display()
            ),
        )
        .env("ORDIVON_PG_SCHEMA", "fresh")
        .env("ORDIVON_PG_SOURCE_SHA256", "a".repeat(64))
        .env("ORDIVON_PG_STORE_ROOT", fixture.root.join("store"))
        .env("ORDIVON_PG_RUNNER", runner)
        .env("ORDIVON_PG_EXECUTABLE_ROOTS_JSON", r#"["/usr/bin","/bin"]"#)
        .env("ORDIVON_PG_BIND", addr.to_string())
        .env("ORDIVON_PG_TOKEN", "p".repeat(32))
        .env("ORDIVON_PG_PRINCIPAL", "pg-consumer")
        .env("ORDIVON_TEST_GIT_BARRIER", &barrier)
        .env("PATH", path)
        .stdout(Stdio::null())
        .stderr(log)
        .spawn()
        .unwrap();
    struct EndpointGuard(Child);
    impl Drop for EndpointGuard {
        fn drop(&mut self) {
            let _ = self.0.kill();
            let _ = self.0.wait();
        }
    }
    let _endpoint_guard = EndpointGuard(child);
    let deadline = Instant::now() + Duration::from_secs(12);
    while std::net::TcpStream::connect(addr).is_err() {
        assert!(
            Instant::now() < deadline,
            "2nd native MCP service failed to start: {}",
            fs::read_to_string(fixture.root.join("barrier-endpoint.log")).unwrap()
        );
        thread::sleep(Duration::from_millis(25));
    }
    let isolated_endpoint = format!("http://{addr}/mcp");
    let request_id = format!("pg-source-prelock-{}", Uuid::now_v7());
    let id_for_job = id.clone();
    let thread = thread::spawn(move || {
        call(
            &isolated_endpoint,
            "workspace.exec",
            json!({
                "clientRequestId":request_id,
                "execution":{
                    "workspaceId":id_for_job,"cwdRelative":".",
                    "executable":"/usr/bin/true","args":[],
                    "timeoutMs":10000
                },
                "waitMs":0
            }),
        )
    });
    let entered = barrier.join("entered");
    let wait_until = Instant::now() + Duration::from_secs(12);
    while !entered.exists() {
        if thread.is_finished() {
            panic!(
                "Job finished before physical source barrier: {}; shim invocations: {}",
                thread.join().unwrap(),
                fs::read_to_string(barrier.join("invocations")).unwrap_or_default()
            );
        }
        assert!(
            Instant::now() < wait_until,
            "Job did not reach Git barrier: {}\nShim invocations: {}",
            fs::read_to_string(fixture.root.join("barrier-endpoint.log")).unwrap(),
            fs::read_to_string(barrier.join("invocations")).unwrap_or_default()
        );
        thread::sleep(Duration::from_millis(25));
    }

    let closed = call(
        &normal_endpoint,
        "workspace.close",
        json!({
            "workspaceId":id,"consumerReleased":true
        }),
    );
    assert_ne!(
        closed["isError"], true,
        "close must be physically permitted before the Job obtains PG admission: {closed}"
    );
    assert_eq!(closed["structuredContent"]["removed"], true, "{closed}");
    // The historical plan's complete Git observations are now returned, and
    // control proceeds to its actual PostgreSQL admission stage.
    fs::write(barrier.join("release"), b"resume").unwrap();
    let result = thread.join().unwrap();
    let count: i64 = fixture
        .db
        .query_one("SELECT count(*) FROM jobs WHERE workspace_id=$1", &[&id])
        .unwrap()
        .get(0);
    assert_eq!(
        count, 0,
        "Job must not be durably admitted for the physically closed Workspace; result={result}"
    );
    assert_eq!(
        result["isError"], true,
        "closed Workspace must fail admission: {result}"
    );
    assert!(
        result.to_string().contains("WORKSPACE_STATE_MISMATCH"),
        "post-lock physical identity mismatch needs exact error, not a successful launch: {result}"
    );
}

/// A source-clean Workspace can have zero active Jobs after a newly
/// completed Job. The original Python lifecycle pre-scan is NOT a durable
/// quiet-period proof. Native close must recheck the last PG Job activity
/// while holding its existing advisory lock and refuse the physical Git
/// removal despite consumerReleased=false.
/// The actual production PostgreSQL Workspace.open must apply both carrier
/// budgets while holding its native PG Workspace-effect lock. Legacy Runtime
/// unit tests cannot prove this separate owner path.
#[test]
#[ignore = "launches an isolated PostgreSQL18 cluster and native Git worktree"]
fn pg_workspace_open_fails_on_either_carrier_before_git_effect() {
    use ordivon_runtime_core::{
        GitWorkspaceCreateRequest, PgRuntime, PgRuntimeConfig, UniversalExecutorConfig,
        WorkspaceHeadroomConfig,
    };

    let fixture = Fixture::new();
    let repo = fixture.repo();
    let path = fixture.root.clone();
    let baseline = PgRuntimeConfig {
        dsn: format!(
            "host={} user=runtime_app dbname=postgres",
            fixture.root.display()
        ),
        schema: "fresh".into(),
        source_sha256: "a".repeat(64),
        harness_spawn_dsn_file: None,
        harness_issuer_schema: None,
        harness_dispatch_issuer: None,
        workspace_headroom: Vec::new(),
        executor: UniversalExecutorConfig {
            store_root: fixture.root.join("store"),
            workspace_root: None,
            workspace_uid: None,
            workspace_gid: None,
            runner_path: None,
            allowed_executable_roots: vec![PathBuf::from("/usr/bin")],
            max_runtime_ms: 30_000,
            max_output_bytes: 1024 * 1024,
        },
    };
    let threshold = |minimum_free_bytes| WorkspaceHeadroomConfig {
        path: path.clone(),
        minimum_free_bytes,
    };
    for (first_minimum, second_minimum, rejected) in
        [(u64::MAX, 1_u64, "first"), (1_u64, u64::MAX, "second")]
    {
        let runtime = PgRuntime::new(PgRuntimeConfig {
            workspace_headroom: vec![threshold(first_minimum), threshold(second_minimum)],
            ..baseline.clone()
        })
        .unwrap();
        let workspace_id = format!("pg-guard-{}-{}", rejected, Uuid::now_v7().simple());
        let result = runtime.open_workspace(&GitWorkspaceCreateRequest {
            schema_version: 1,
            workspace_id: workspace_id.clone(),
            source_repo: repo.to_string_lossy().into_owned(),
            source_revision: "HEAD".into(),
        });
        let error = result.expect_err("guest or host floor must reject PG open");
        assert_eq!(
            error.code,
            ordivon_runtime_core::RuntimeErrorCode::WorkspaceCapacityExceeded,
            "{rejected} carrier should independently deny PG open: {error}"
        );
        assert!(!fixture
            .root
            .join("store/workspaces")
            .join(&workspace_id)
            .exists());
    }

    let runtime = PgRuntime::new(PgRuntimeConfig {
        workspace_headroom: vec![threshold(1), threshold(1)],
        ..baseline
    })
    .unwrap();
    let admitted = runtime
        .open_workspace(&GitWorkspaceCreateRequest {
            schema_version: 1,
            workspace_id: format!("pg-guard-valid-{}", Uuid::now_v7().simple()),
            source_repo: repo.to_string_lossy().into_owned(),
            source_revision: "HEAD".into(),
        })
        .expect("both carrier floors satisfied must preserve real PG workspace.open");
    assert!(fixture
        .root
        .join("store/workspaces")
        .join(&admitted.workspace_id)
        .is_dir());
}

#[test]
#[ignore = "launches an isolated PostgreSQL18 cluster and native Git worktree"]
fn pg_workspace_close_blocks_recent_completed_job_after_stale_reclaim_scan() {
    use ordivon_runtime_core::{
        GitWorkspaceCreateRequest, PgRuntime, PgRuntimeConfig, UniversalExecutorConfig,
        WorkspaceCloseRequest,
    };

    let mut fixture = Fixture::new();
    let repo = fixture.repo();
    let workspace_id = format!("ws-quiet-recheck-{}", Uuid::now_v7().simple());
    let runtime = PgRuntime::new(PgRuntimeConfig {
        dsn: format!(
            "host={} user=runtime_app dbname=postgres",
            fixture.root.display()
        ),
        schema: "fresh".into(),
        source_sha256: "a".repeat(64),
        harness_spawn_dsn_file: None,
        harness_issuer_schema: None,
        harness_dispatch_issuer: None,
        workspace_headroom: Vec::new(),
        executor: UniversalExecutorConfig {
            store_root: fixture.root.join("store"),
            workspace_root: None,
            workspace_uid: None,
            workspace_gid: None,
            runner_path: None,
            allowed_executable_roots: vec![PathBuf::from("/usr/bin")],
            max_runtime_ms: 30_000,
            max_output_bytes: 1024 * 1024,
        },
    })
    .unwrap();
    runtime
        .open_workspace(&GitWorkspaceCreateRequest {
            schema_version: 1,
            workspace_id: workspace_id.clone(),
            source_repo: repo.to_string_lossy().into_owned(),
            source_revision: "HEAD".into(),
        })
        .unwrap();

    // Give the physical carrier an old creation time: otherwise the
    // universal 4h workspace-creation guard would mask the missing PG
    // last-Job guard, and the test would falsely pass on the wrong reason.
    let now_ms = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_millis() as i64;
    let record_file = fixture
        .root
        .join("store/workspace-records")
        .join(format!("{workspace_id}.json"));
    let mut record: Value = serde_json::from_slice(&fs::read(&record_file).unwrap()).unwrap();
    assert!(record["createdUnixMs"].is_number());
    record["createdUnixMs"] = json!(now_ms - 7 * 60 * 60 * 1000);
    fs::write(&record_file, serde_json::to_vec(&record).unwrap()).unwrap();

    // A terminally successful Job was admitted after the reclaimer's
    // hypothetical earlier PG scan. There are no active leases left; Git
    // HEAD and source digest remain unchanged. Prior native close would
    // REMOVE this still-consumed Workspace after the old creation grace.
    let job_id = format!("job-{}", Uuid::now_v7());
    let request_id = format!("pg-recent-terminal-{}", Uuid::now_v7());
    fixture
        .db
        .execute(
            "INSERT INTO jobs (
            job_id,principal,client_request_id,request_digest,operation_digest,
            workspace_id,workspace_snapshot_json,execution_plan_json,
            execution_plan_digest,created_at_ms,desired_state,resolution
         ) VALUES ($1,'quiet-consumer',$2,'sha256:request','sha256:effect',
                   $3,'{}','{}','sha256:plan',$4,'run','succeeded')",
            &[&job_id, &request_id, &workspace_id, &now_ms],
        )
        .unwrap();

    let visible = runtime
        .get_workspace(&ordivon_runtime_core::RuntimeWorkspaceGetRequest {
            schema_version: 1,
            workspace_id: workspace_id.clone(),
        })
        .unwrap();
    assert_eq!(
        visible["activeJobIds"],
        json!([]),
        "the Job has truly completed, and active-only readback is empty"
    );

    let denied = runtime
        .close_workspace(&WorkspaceCloseRequest {
            schema_version: 1,
            workspace_id: workspace_id.clone(),
            force: false,
            consumer_released: false,
            expected_source_state_digest: None,
        })
        .expect_err(
            "the PG-native lock must reject a recently completed Job even when activeJobIds=[]",
        );
    assert_eq!(
        denied.code.as_str(),
        "WORKSPACE_STATE_MISMATCH",
        "{denied:?}"
    );
    assert_eq!(denied.field.as_deref(), Some("consumerReleased"));
    assert!(
        denied.message.contains("recent PG Job activity"),
        "{denied:?}"
    );
    assert!(
        fixture
            .root
            .join("store/workspaces")
            .join(&workspace_id)
            .is_dir(),
        "source Git Workspace must survive the native PG close refusal"
    );
    assert!(runtime
        .get_workspace(&ordivon_runtime_core::RuntimeWorkspaceGetRequest {
            schema_version: 1,
            workspace_id,
        })
        .is_ok());
}

/// End-to-end native PostgreSQL application regression for the lock/snapshot
/// boundary: a real PgAdmissionStore.admit() transaction is queued AHEAD of
/// Workspace.close() while a third session holds the shared global advisory
/// lock. Once admission commits, close must observe the new accepted Job and
/// preserve the actual Git worktree. Under old SERIALIZABLE Workspace
/// transactions the snapshot was pinned BEFORE acquiring the lock, so close
/// could physically remove a Workspace with a newly accepted active consumer.
#[test]
#[ignore = "launches an isolated native PostgreSQL cluster and real Git worktree"]
fn pg_workspace_close_observes_admission_committed_while_waiting_for_global_lock() {
    use ordivon_runtime_core::{
        pg_admission::{PgAdmissionInput, PgAdmissionOutcome, PgAdmissionStore},
        GitWorkspaceCreateRequest, PgRuntime, PgRuntimeConfig, UniversalExecutorConfig,
        WorkspaceCloseRequest,
    };

    let mut fixture = Fixture::new();
    let repo = fixture.repo();
    let workspace_id = format!("ws-r2-lock-{}", Uuid::now_v7().simple());
    let runtime = PgRuntime::new(PgRuntimeConfig {
        dsn: format!(
            "host={} user=runtime_app dbname=postgres",
            fixture.root.display()
        ),
        schema: "fresh".into(),
        source_sha256: "a".repeat(64),
        harness_spawn_dsn_file: None,
        harness_issuer_schema: None,
        harness_dispatch_issuer: None,
        workspace_headroom: Vec::new(),
        executor: UniversalExecutorConfig {
            store_root: fixture.root.join("store"),
            workspace_root: None,
            workspace_uid: None,
            workspace_gid: None,
            runner_path: None,
            allowed_executable_roots: vec![PathBuf::from("/usr/bin")],
            max_runtime_ms: 30_000,
            max_output_bytes: 1024 * 1024,
        },
    })
    .unwrap();
    runtime
        .open_workspace(&GitWorkspaceCreateRequest {
            schema_version: 1,
            workspace_id: workspace_id.clone(),
            source_repo: repo.to_string_lossy().into_owned(),
            source_revision: "HEAD".into(),
        })
        .unwrap();

    let job_id = format!("job-{}", Uuid::now_v7());
    let attempt_id = format!("attempt-{}", Uuid::now_v7());
    let input = PgAdmissionInput {
        job_id: job_id.clone(),
        attempt_id: attempt_id.clone(),
        reservation_id: format!("reservation-{}", Uuid::now_v7()),
        principal: "pg-consumer".into(),
        client_request_id: format!("ws-r2-lease-race-{}", Uuid::now_v7()),
        request_digest: format!("sha256:{}", "b".repeat(64)),
        operation_digest: format!("sha256:{}", "c".repeat(64)),
        workspace_id: workspace_id.clone(),
        workspace_snapshot_json: "{}".into(),
        execution_plan_json: "{}".into(),
        execution_plan_digest: format!("sha256:{}", "d".repeat(64)),
        launch_token_digest: format!("sha256:{}", "e".repeat(64)),
        bundle_path: fixture
            .root
            .join("store/pg-attempts")
            .join(&attempt_id)
            .to_string_lossy()
            .into_owned(),
        unit_name: format!("ordivon-pg-{attempt_id}.service"),
        global_limit: 4,
        created_at_ms: std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_millis() as i64,
        expected_source_sha256: "a".repeat(64),
    };
    let app_dsn = format!(
        "host={} user=runtime_app dbname=postgres",
        fixture.root.display()
    );
    let mut probe = Client::connect(
        &format!(
            "host={} user=postgres dbname=postgres",
            fixture.root.display()
        ),
        NoTls,
    )
    .unwrap();
    // Fixture::new() qualifies an isolated schema, but a fresh superuser
    // connection begins on public; explicitly scope the lease readback.
    probe.batch_execute("SET search_path TO fresh").unwrap();
    let mut holder = fixture
        .db
        .build_transaction()
        .isolation_level(postgres::IsolationLevel::Serializable)
        .start()
        .unwrap();
    holder
        .query_one("SELECT pg_advisory_xact_lock($1)", &[&79245017_i64])
        .unwrap();
    holder
        .query_one(
            "SELECT state FROM _stage_control WHERE id='source' FOR UPDATE",
            &[],
        )
        .unwrap();

    // The two separate codepaths genuinely queue on the SAME global PG lock.
    let (admit_started, admit_rx) = std::sync::mpsc::sync_channel(1);
    let admission = thread::spawn(move || {
        let mut db = PgAdmissionStore::connect(&app_dsn, "fresh").unwrap();
        admit_started.send(()).unwrap();
        db.admit(&input)
    });
    admit_rx.recv_timeout(Duration::from_secs(4)).unwrap();

    let waiters = |probe: &mut Client| -> i64 {
        probe
            .query_one(
                "SELECT count(*) FROM pg_stat_activity \
             WHERE wait_event_type='Lock' AND wait_event='advisory'",
                &[],
            )
            .unwrap()
            .get(0)
    };
    let wait_until = |probe: &mut Client, count: i64| {
        let deadline = Instant::now() + Duration::from_secs(5);
        while waiters(probe) < count {
            assert!(
                Instant::now() < deadline,
                "expected real PG advisory lock wait"
            );
            thread::sleep(Duration::from_millis(20));
        }
    };
    wait_until(&mut probe, 1);

    let runtime_for_close = runtime.clone();
    let id_for_close = workspace_id.clone();
    let (close_started, close_rx) = std::sync::mpsc::sync_channel(1);
    let closer = thread::spawn(move || {
        close_started.send(()).unwrap();
        runtime_for_close.close_workspace(&WorkspaceCloseRequest {
            schema_version: 1,
            workspace_id: id_for_close,
            force: false,
            consumer_released: true,
            expected_source_state_digest: None,
        })
    });
    close_rx.recv_timeout(Duration::from_secs(4)).unwrap();
    wait_until(&mut probe, 2);
    // Required global order: holder -> genuine admission -> Workspace.close.
    holder.commit().unwrap();
    assert!(
        matches!(
            admission.join().unwrap().unwrap(),
            PgAdmissionOutcome::Created(_)
        ),
        "first waiter must durably commit real PG Job and active reservation"
    );
    let denied = closer.join().unwrap().expect_err(
        "Workspace.close must not physically remove a Workspace whose Job committed while it waited on the advisory lock"
    );
    assert_eq!(
        denied.code.as_str(), "CONCURRENCY_LIMIT",
        "close must see the newly committed Job (rather than a stale SERIALIZABLE snapshot): {denied:?}"
    );
    let count: i64 = probe
        .query_one(
            "SELECT count(*) FROM jobs j JOIN attempts a ON a.job_id=j.job_id \
         JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id \
         WHERE j.job_id=$1 AND j.workspace_id=$2 AND j.resolution IS NULL \
           AND r.state='active'",
            &[&job_id, &workspace_id],
        )
        .unwrap()
        .get(0);
    assert_eq!(
        count, 1,
        "native admission must actually own an active PG lease"
    );
    let workspace_root = fixture.root.join("store/workspaces").join(&workspace_id);
    assert!(workspace_root.is_dir(), "real Git worktree must remain");
    assert!(
        runtime
            .get_workspace(&ordivon_runtime_core::RuntimeWorkspaceGetRequest {
                schema_version: 1,
                workspace_id,
            })
            .is_ok(),
        "Git Workspace identity and source must survive the rejected close"
    );
}

#[test]
#[ignore = "launches an isolated native PostgreSQL cluster"]
fn postgres_runtime_startup_requires_exact_qualified_writer() {
    use ordivon_runtime_core::{PgRuntime, PgRuntimeConfig, UniversalExecutorConfig};
    let mut fixture = Fixture::new();
    let config = PgRuntimeConfig {
        dsn: format!(
            "host={} user=runtime_app dbname=postgres",
            fixture.root.display()
        ),
        schema: "fresh".into(),
        source_sha256: "a".repeat(64),
        harness_spawn_dsn_file: None,
        harness_issuer_schema: None,
        harness_dispatch_issuer: None,
        workspace_headroom: Vec::new(),
        executor: UniversalExecutorConfig {
            store_root: fixture.root.join("store"),
            workspace_root: None,
            workspace_uid: None,
            workspace_gid: None,
            runner_path: None,
            allowed_executable_roots: vec![PathBuf::from("/usr/bin")],
            max_runtime_ms: 30_000,
            max_output_bytes: 1024 * 1024,
        },
    };
    assert!(
        !config.executor.store_root.exists(),
        "an isolated candidate must begin without a Workspace store"
    );
    fixture
        .db
        .execute("DELETE FROM _stage_control", &[])
        .unwrap();
    let denied = PgRuntime::new(config.clone())
        .err()
        .expect("empty stage must reject startup");
    assert!(denied.to_string().contains("not qualified"), "{denied}");
    assert!(
        !config.executor.store_root.exists(),
        "denied startup must not create any Workspace store"
    );
    fixture
        .db
        .execute(
            "INSERT INTO _stage_control VALUES('source','QUALIFIED_WRITER',$1,true)",
            &[&"b".repeat(64)],
        )
        .unwrap();
    let mismatched = PgRuntime::new(config.clone())
        .err()
        .expect("wrong source must reject startup");
    assert!(
        mismatched.to_string().contains("not qualified"),
        "{mismatched}"
    );
    assert!(
        !config.executor.store_root.exists(),
        "a wrong SourceCut must not create a Workspace store"
    );
    fixture
        .db
        .execute(
            "UPDATE _stage_control SET source_sha256=$1",
            &[&"a".repeat(64)],
        )
        .unwrap();
    let physical = fixture.db.query_one(
        "SELECT (SELECT system_identifier::text FROM pg_control_system()),                 (SELECT timeline_id FROM pg_control_checkpoint())", &[],
    ).unwrap();
    let digest = ordivon_runtime_core::pg_admission::pg_writer_epoch_digest(
        &"a".repeat(64),
        &physical.get::<_, String>(0),
        physical.get::<_, i32>(1),
    );
    let denied_without_epoch = PgRuntime::new(config.clone())
        .err()
        .expect("source-only writer must NOT qualify without physical epoch");
    assert!(
        denied_without_epoch.to_string().contains("Unqualified"),
        "{denied_without_epoch}",
    );
    fixture
        .db
        .execute(
            "INSERT INTO _stage_control VALUES('epoch','QUALIFIED_EPOCH',$1,true)",
            &[&digest],
        )
        .unwrap();
    // A PITR fork keeps the source SHA but changes the current physical WAL
    // timeline. A stale operator epoch must not requalify that branch.
    let stale_epoch = ordivon_runtime_core::pg_admission::pg_writer_epoch_digest(
        &"a".repeat(64),
        &physical.get::<_, String>(0),
        physical.get::<_, i32>(1) + 1,
    );
    fixture
        .db
        .execute(
            "UPDATE _stage_control SET source_sha256=$1 WHERE id='epoch'",
            &[&stale_epoch],
        )
        .unwrap();
    let stale_denied = PgRuntime::new(config.clone())
        .err()
        .expect("future or stale WAL timeline must fail closed");
    assert!(
        stale_denied.to_string().contains("Unqualified"),
        "{stale_denied}"
    );
    assert!(
        !config.executor.store_root.exists(),
        "wrong timeline must not create Workspace directories",
    );
    fixture
        .db
        .execute(
            "UPDATE _stage_control SET source_sha256=$1 WHERE id='epoch'",
            &[&digest],
        )
        .unwrap();
    let running = PgRuntime::new(config.clone()).expect("exact operator-qualified source starts");
    assert!(
        config.executor.store_root.is_dir(),
        "qualified startup must initialize the existing store"
    );
    // Even with a distinct table owner, a mistaken grant on a protected
    // qualification column must fail before the Runtime advertises tools.
    fixture
        .db
        .batch_execute("GRANT UPDATE(promotion_allowed) ON fresh._stage_control TO runtime_app")
        .unwrap();
    assert!(
        PgRuntime::new(config).is_err(),
        "the application can rewrite promotion_allowed and self-authorize"
    );
    assert!(
        running.list("pg-consumer", &ordivon_runtime_core::RuntimeJobListRequest {
            limit: 1, cursor: None, client_request_id: None, workspace_id: None
        }).is_err(),
        "a long-lived Runtime must not keep accepting the app after operator grants it control mutation"
    );
}

#[test]
#[ignore = "requires disposable PostgreSQL 18 and native systemd Runner"]
fn pg_workspace_exec_routes_cargo_target_to_private_reclaimable_cache() {
    let mut fixture = Fixture::new();
    let source = fixture.repo();
    let endpoint = fixture.endpoint();
    let id = "ws-pg-private-cargo";
    let opened = call(
        &endpoint,
        "workspace.open",
        json!({"workspaceId":id,"sourceRepo":source,"sourceRevision":"HEAD"}),
    );
    assert_ne!(opened["isError"], true, "{opened}");

    // Exercise the real PG admission -> systemd Runner -> physical filesystem,
    // not a mock plan or a pre-set CARGO_TARGET_DIR from the caller.
    let script = r#"import os, subprocess
from pathlib import Path
p = Path(os.environ["CARGO_TARGET_DIR"])
assert p.is_dir()
(p / "pg-private-marker").write_text("PRIVATE_ONLY")
subprocess.run(
    ["/usr/bin/python3", "-c",
     "import os,pathlib; p=pathlib.Path(os.environ['CARGO_TARGET_DIR']); (p/'pg-private-child-marker').write_text('NESTED')"],
    check=True, close_fds=True,
)
print(os.environ["CARGO_TARGET_DIR"])
"#;
    let result = call(
        &endpoint,
        "workspace.exec",
        json!({"clientRequestId":"pg-private-cargo-physical",
              "execution":{"workspaceId":id,"executable":"/usr/bin/python3",
                           "args":["-c",script],"cwdRelative":".","timeoutMs":10000},
              "waitMs":15000,"stdoutTailBytes":1024}),
    );
    assert_ne!(result["isError"], true, "{result}");
    assert_eq!(
        result["structuredContent"]["executionDisposition"], "succeeded",
        "private build target must be a physically usable native Runner FD: {result}"
    );
    assert_eq!(
        result["structuredContent"]["stdoutTail"]
            .as_str()
            .map(str::trim),
        Some("/run/ordivon/cargo-target"),
    );
    let cache = fixture
        .root
        .join("store/cache/build")
        .join(id)
        .join("cargo");
    assert_eq!(
        fs::read_to_string(cache.join("pg-private-marker")).unwrap(),
        "PRIVATE_ONLY"
    );
    assert_eq!(
        fs::read_to_string(cache.join("pg-private-child-marker")).unwrap(),
        "NESTED",
        "nested native subprocess must not lose its private Cargo target"
    );
    assert!(
        !fixture
            .root
            .join("store/workspaces")
            .join(id)
            .join("target")
            .exists(),
        "tool output must not land in Git-ignored source worktree target/"
    );

    // Two live Jobs share the stable lexical Cargo path but NOT physical
    // backing bytes. The systemd mount namespace is the native isolation.
    let other_id = "ws-pg-private-cargo-other";
    let other_open = call(
        &endpoint,
        "workspace.open",
        json!({"workspaceId":other_id,"sourceRepo":source,"sourceRevision":"HEAD"}),
    );
    assert_ne!(other_open["isError"], true, "{other_open}");
    let other_script = script
        .replace("PRIVATE_ONLY", "OTHER_ONLY")
        .replace("NESTED", "NESTED_OTHER");
    let other_result = call(
        &endpoint,
        "workspace.exec",
        json!({"clientRequestId":"pg-private-cargo-other-physical",
              "execution":{"workspaceId":other_id,"executable":"/usr/bin/python3",
                           "args":["-c",other_script],"cwdRelative":".","timeoutMs":10000},
              "waitMs":15000,"stdoutTailBytes":1024}),
    );
    assert_ne!(other_result["isError"], true, "{other_result}");
    assert_eq!(
        other_result["structuredContent"]["executionDisposition"], "succeeded",
        "{other_result}"
    );
    assert_eq!(
        other_result["structuredContent"]["stdoutTail"]
            .as_str()
            .map(str::trim),
        Some("/run/ordivon/cargo-target"),
    );
    let other_cache = fixture
        .root
        .join("store/cache/build")
        .join(other_id)
        .join("cargo");
    assert_eq!(
        fs::read_to_string(other_cache.join("pg-private-marker")).unwrap(),
        "OTHER_ONLY"
    );
    assert_eq!(
        fs::read_to_string(other_cache.join("pg-private-child-marker")).unwrap(),
        "NESTED_OTHER"
    );
    assert_eq!(
        fs::read_to_string(cache.join("pg-private-marker")).unwrap(),
        "PRIVATE_ONLY"
    );
    assert_eq!(
        fs::read_to_string(cache.join("pg-private-child-marker")).unwrap(),
        "NESTED"
    );
    let other_close = call(
        &endpoint,
        "workspace.close",
        json!({"workspaceId":other_id,"force":false,"consumerReleased":true}),
    );
    assert_ne!(other_close["isError"], true, "{other_close}");
    assert!(
        !other_cache.exists(),
        "secondary private backing must be reclaimed"
    );

    // A multi-step PG plan must project the same private target into each
    // Runner step, not only into its job-wide environment.
    let plan_result = call(
        &endpoint,
        "workspace.execPlan",
        json!({"clientRequestId":"pg-private-cargo-multi-step",
              "execution":{"workspaceId":id,"steps":[
                  {"id":"first","executable":"/usr/bin/python3","cwdRelative":".",
                   "args":["-c","import os; from pathlib import Path; (Path(os.environ['CARGO_TARGET_DIR'])/'multi-first').write_text('FIRST')"],
                   "timeoutMs":10000},
                  {"id":"second","executable":"/usr/bin/python3","cwdRelative":".",
                   "args":["-c","import os; from pathlib import Path; (Path(os.environ['CARGO_TARGET_DIR'])/'multi-second').write_text('SECOND')"],
                   "timeoutMs":10000}
              ]},"waitMs":25000}),
    );
    assert_ne!(plan_result["isError"], true, "{plan_result}");
    assert_eq!(
        plan_result["structuredContent"]["executionDisposition"], "succeeded",
        "{plan_result}"
    );
    assert_eq!(
        fs::read_to_string(cache.join("multi-first")).unwrap(),
        "FIRST"
    );
    assert_eq!(
        fs::read_to_string(cache.join("multi-second")).unwrap(),
        "SECOND"
    );
    let plan_id = plan_result["structuredContent"]["jobId"].as_str().unwrap();
    let frozen: String = fixture
        .db
        .query_one(
            "SELECT execution_plan_json FROM jobs WHERE job_id=$1",
            &[&plan_id],
        )
        .unwrap()
        .get(0);
    let plan: Value = serde_json::from_str(&frozen).unwrap();
    for step in plan["steps"].as_array().unwrap() {
        assert_eq!(step["env"]["CARGO_TARGET_DIR"], "/run/ordivon/cargo-target");
    }
    // An explicitly authored path is a real execution input, not a default
    // the Runtime may silently replace.
    let overridden = call(
        &endpoint,
        "workspace.exec",
        json!({"clientRequestId":"pg-private-cargo-custom-explicit",
              "execution":{"workspaceId":id,"executable":"/usr/bin/python3",
                           "args":["-c","import os; print(os.environ['CARGO_TARGET_DIR'])"],
                           "env":{"CARGO_TARGET_DIR":"EXPLICIT_AGENT_VALUE"},
                           "cwdRelative":".","timeoutMs":10000},
              "waitMs":15000}),
    );
    assert_ne!(overridden["isError"], true, "{overridden}");
    assert_eq!(
        overridden["structuredContent"]["executionDisposition"], "succeeded",
        "{overridden}"
    );
    assert_eq!(
        overridden["structuredContent"]["stdoutTail"]
            .as_str()
            .map(str::trim),
        Some("EXPLICIT_AGENT_VALUE")
    );

    // The pre-existing native close already owns private-cache reclamation.
    let closed = call(
        &endpoint,
        "workspace.close",
        json!({"workspaceId":id,"force":false,"consumerReleased":true}),
    );
    assert_ne!(closed["isError"], true, "{closed}");
    assert_eq!(closed["structuredContent"]["removed"], true);
    assert!(
        !cache.exists(),
        "native close must reclaim workspace-private build cache"
    );
}

#[test]
#[ignore = "real PostgreSQL18 + transient systemd timeout; verified LOST without reset-failed"]
fn failed_retained_pg_transient_auto_converges_to_lost_and_releases_capacity() {
    struct TestUnitCleanup(String);
    impl Drop for TestUnitCleanup {
        fn drop(&mut self) {
            // Only clean the disposable UUID-scoped unit created by this test.
            // A RED test must not leave a stopped failed unit behind.
            let _ = Command::new("systemctl").args(["stop", &self.0]).output();
            let _ = Command::new("systemctl")
                .args(["reset-failed", &self.0])
                .output();
        }
    }

    let mut fixture = Fixture::new();
    let repo = fixture.repo();
    let endpoint = fixture.endpoint();
    let opened = call(
        &endpoint,
        "workspace.open",
        json!({"workspaceId":"ws-pg-failed-transient","sourceRepo":repo,"sourceRevision":"HEAD"}),
    );
    assert_ne!(opened["isError"], true, "{opened}");

    // Force a *systemd* timeout while Runner is unable to write result.json.
    // This is the exact production counterexample: CollectMode=inactive keeps
    // a failed Unit loaded even though its kernel cgroup has been removed.
    let admitted = call(
        &endpoint,
        "workspace.exec",
        json!({"clientRequestId":"pg-failed-transient-exact-runner",
               "execution":{"workspaceId":"ws-pg-failed-transient",
                            "executable":"/usr/bin/sleep","args":["60"],
                            "cwdRelative":".","timeoutMs":9000},
               "waitMs":0}),
    );
    assert_ne!(admitted["isError"], true, "{admitted}");
    let job_id = admitted["structuredContent"]["jobId"]
        .as_str()
        .expect("exact committed PG Job")
        .to_owned();
    let (bundle, unit): (String, String) = {
        let row = fixture
            .db
            .query_one(
                "SELECT bundle_path,unit_name FROM attempts WHERE job_id=$1",
                &[&job_id],
            )
            .unwrap();
        (row.get(0), row.get(1))
    };
    assert!(
        unit.starts_with("ordivon-pg-attempt-") && unit.ends_with(".service"),
        "only UUID-scoped disposable PG unit may be stopped: {unit}"
    );
    let _cleanup = TestUnitCleanup(unit.clone());
    let start_file = PathBuf::from(&bundle).join("runner-start.json");
    let start_deadline = Instant::now() + Duration::from_secs(8);
    while !start_file.is_file() && Instant::now() < start_deadline {
        thread::sleep(Duration::from_millis(30));
    }
    assert!(
        start_file.is_file(),
        "real Runner start witness is required"
    );
    let start: Value = serde_json::from_slice(&fs::read(&start_file).unwrap()).unwrap();
    assert_eq!(start["jobId"], job_id);
    assert_eq!(start["unitName"], unit);
    assert_eq!(
        start["controlGroup"],
        format!("/system.slice/{unit}"),
        "exact cgroup identity required"
    );

    // Freeze only this test Runner's main PID. systemd RuntimeMaxSec then
    // terminates its whole cgroup; no user command is restarted or reissued.
    let frozen = Command::new("systemctl")
        .args(["kill", "--signal=STOP", "--kill-whom=main", &unit])
        .output()
        .unwrap();
    assert!(
        frozen.status.success(),
        "freeze only the disposable Runner: {}",
        String::from_utf8_lossy(&frozen.stderr)
    );

    let deadline = Instant::now() + Duration::from_secs(42);
    let final_observation = loop {
        let observed = call(
            &endpoint,
            "job.observe",
            json!({"jobId": job_id, "waitMs": 2000, "stdoutTailBytes":500}),
        );
        assert_ne!(observed["isError"], true, "{observed}");
        if observed["structuredContent"]["executionTerminal"] == true {
            break observed;
        }
        assert!(
            Instant::now() < deadline,
            "failed retained systemd Unit left PG Job running: {observed}"
        );
        thread::sleep(Duration::from_millis(150));
    };
    assert_eq!(
        final_observation["structuredContent"]["executionDisposition"],
        "lost",
        "a dead Runner without result.json can only become LOST, never success: {final_observation}"
    );
    assert_eq!(
        final_observation["structuredContent"]["resultAvailable"],
        false
    );
    // Real systemd Runner death produces a durable PG control terminal but
    // no Runner result. This is the native R4 counterexample consumed by
    // Gateway and Harness: this test qualifies Runtime's projection only.
    assert_eq!(
        final_observation["structuredContent"]["deliveryDisposition"], "unknown",
        "mechanical PG convergence is not execution result delivery: {final_observation}"
    );
    assert_eq!(
        final_observation["structuredContent"]["recoveryRequired"], false,
        "the native cgroup is quiescent; result uncertainty is independent of control recovery"
    );
    let listed = call(
        &endpoint,
        "job.list",
        json!({"clientRequestId":"pg-failed-transient-exact-runner","limit":2}),
    );
    assert_ne!(listed["isError"], true, "{listed}");
    let rows = listed["structuredContent"]["jobs"].as_array().unwrap();
    assert_eq!(
        rows.len(),
        1,
        "the original Job must have one exact owner identity"
    );
    assert_eq!(rows[0]["jobId"], job_id);
    assert_eq!(rows[0]["executionDisposition"], "lost");
    assert_eq!(rows[0]["deliveryDisposition"], "unknown", "{listed}");
    assert_eq!(rows[0]["resultAvailable"], false, "{listed}");
    assert!(
        !PathBuf::from(&bundle).join("result.json").exists(),
        "this case specifically requires OS-only recovery"
    );
    let receipt: Value = serde_json::from_slice(
        &fs::read(PathBuf::from(&bundle).join("native-stop-evidence.json")).unwrap(),
    )
    .unwrap();
    assert_eq!(receipt["terminalState"], "lost");
    assert_eq!(
        receipt["failedUnitInvocationBound"], true,
        "identity-bound failed retained systemd Unit must be the actual reason for convergence: {receipt}"
    );
    assert_eq!(receipt["activeState"], "failed");
    assert_eq!(receipt["loadState"], "loaded");
    assert_eq!(receipt["nativeCgroupState"], "removed");
    assert_eq!(receipt["kernelCgroupRemoved"], true);
    let reservation: String = fixture
        .db
        .query_one(
            "SELECT r.state FROM concurrency_reservations r JOIN attempts a ON a.attempt_id=r.attempt_id WHERE a.job_id=$1",
            &[&job_id],
        )
        .unwrap()
        .get(0);
    assert_eq!(reservation, "released");
    let count: i64 = fixture
        .db
        .query_one(
            "SELECT count(*) FROM job_events WHERE job_id=$1 AND event_type='DISPATCH_ISSUED'",
            &[&job_id],
        )
        .unwrap()
        .get(0);
    assert_eq!(count, 1, "native recovery must not relaunch the attempt");

    // The systemd failed Unit must be retained until the PG terminal commit,
    // then unloaded by the EXISTING terminal-only cleanup, not by the
    // disposable test's Drop guard. Otherwise the root incident is merely
    // shifted from leaked PG reservations to leaked supervisor failed units.
    let unloaded_deadline = Instant::now() + Duration::from_secs(4);
    loop {
        let unit_state = Command::new("systemctl")
            .args(["show", &unit, "--property=LoadState"])
            .output()
            .unwrap();
        assert!(unit_state.status.success());
        let state = String::from_utf8_lossy(&unit_state.stdout);
        if state.trim() == "LoadState=not-found" {
            break;
        }
        assert!(
            Instant::now() < unloaded_deadline,
            "committed LOST must release the failed transient Unit too: {state}"
        );
        thread::sleep(Duration::from_millis(50));
    }
}

#[test]
#[ignore = "requires PostgreSQL binaries and authorized systemd/cgroup execution"]
fn fresh_pg_mcp_native_runner_success_and_cancel() {
    let mut fixture = Fixture::new();
    // Cargo's per-Job /run/ordivon/cargo-target is private to the test's
    // own native Unit. A sibling transient PG Runner must use the existing
    // disposable host-visible fixture copy rather than this private mount.
    fixture.host_visible_test_runner = true;
    let repo = fixture.repo();
    let endpoint = fixture.endpoint();
    let open = call(
        &endpoint,
        "workspace.open",
        json!({"workspaceId":"ws-physical","sourceRepo":repo,"sourceRevision":"HEAD"}),
    );
    assert_ne!(open["isError"], true, "{open}");
    let mut exec = call(
        &endpoint,
        "workspace.exec",
        json!({"clientRequestId":"pg-native-physical-0001","execution":{"workspaceId":"ws-physical","executable":"/usr/bin/printf","args":["native-proof"],"cwdRelative":".","timeoutMs":5000},"waitMs":10000}),
    );
    assert_ne!(
        exec["isError"], true,
        "physical native launch required: {exec}"
    );
    // Resource-aware PG admission can return STARTING while the current
    // physical Job is still queued. Observe the SAME committed Job rather
    // than redispatching a second external effect.
    let admitted_id = exec["structuredContent"]["jobId"]
        .as_str()
        .unwrap()
        .to_owned();
    for _ in 0..30 {
        if exec["structuredContent"]["executionTerminal"] == true {
            break;
        }
        exec = call(
            &endpoint,
            "job.observe",
            json!({"jobId":admitted_id,"waitMs":1000,"stdoutTailBytes":256}),
        );
        assert_ne!(
            exec["isError"], true,
            "existing PG Job observation failed: {exec}"
        );
    }
    assert_eq!(
        exec["structuredContent"]["executionDisposition"], "succeeded",
        "{exec}"
    );
    assert_eq!(exec["structuredContent"]["stdoutTail"], "native-proof");
    // A terminal PostgreSQL Job intentionally has no current_attempt_id.
    // Cancelling a completed effect must return its existing Owner observation,
    // never require a current native Runner or mutate terminal truth.
    let completed_job = exec["structuredContent"]["jobId"].as_str().unwrap();
    let times = fixture
        .db
        .query_one(
            "SELECT started_at_ms,finished_at_ms FROM attempts WHERE job_id=$1",
            &[&completed_job],
        )
        .unwrap();
    let started: i64 = times.get::<_, Option<i64>>(0).expect("native Runner bound");
    let finished: i64 = times.get::<_, Option<i64>>(1).expect("terminal witness");
    let inspection = call(&endpoint, "job.get", json!({"jobId":completed_job}));
    assert_ne!(inspection["isError"], true, "{inspection}");
    // Independent direct SQL oracle for the fused artifact projection:
    // compare the actual durable native Job's full totals and kind counts.
    let expected = fixture
        .db
        .query_one(
            "SELECT count(*),COALESCE(sum(byte_length),0)::bigint,
                count(*) FILTER(WHERE truncated)
         FROM artifacts WHERE job_id=$1",
            &[&completed_job],
        )
        .unwrap();
    let mut expected_kinds = serde_json::Map::new();
    for row in fixture
        .db
        .query(
            "SELECT kind,count(*) FROM artifacts WHERE job_id=$1 GROUP BY kind",
            &[&completed_job],
        )
        .unwrap()
    {
        expected_kinds.insert(row.get::<_, String>(0), json!(row.get::<_, i64>(1)));
    }
    let expected_summary = json!({
        "count":expected.get::<_,i64>(0),
        "bytes":expected.get::<_,i64>(1),
        "truncated":expected.get::<_,i64>(2),
        "byKind":expected_kinds,
    });
    assert!(
        expected.get::<_, i64>(0) > 0,
        "actual native artifact witness required"
    );
    assert_eq!(
        inspection["structuredContent"]["artifacts"],
        expected_summary
    );
    let observed_attempt = &inspection["structuredContent"]["attempts"][0];
    assert_eq!(observed_attempt["artifactCount"], expected_summary["count"]);
    assert_eq!(observed_attempt["artifactBytes"], expected_summary["bytes"]);
    assert_eq!(
        observed_attempt["truncatedArtifacts"],
        expected_summary["truncated"]
    );
    assert_eq!(observed_attempt["resultAvailable"], true);
    println!(
        "FUSED_ARTIFACT_NATIVE_RECIPIENT_MATCH=1 COUNT={}",
        expected.get::<_, i64>(0)
    );
    // The public MCP projection must agree with the real native Job journal,
    // independently of how many timeline events the caller requests.
    let dispatch_count: i64 = fixture
        .db
        .query_one(
            "SELECT count(*) FROM job_events WHERE job_id=$1 AND event_type='DISPATCH_ISSUED'",
            &[&completed_job],
        )
        .unwrap()
        .get(0);
    assert_eq!(dispatch_count, 1);
    for event_limit in [0, 1, 100] {
        let projected = call(
            &endpoint,
            "job.get",
            json!({"jobId":completed_job,"eventLimit":event_limit}),
        );
        assert_ne!(projected["isError"], true, "{projected}");
        let body = &projected["structuredContent"];
        assert_eq!(body["episodes"]["dispatches"], dispatch_count);
        assert_eq!(body["episodes"]["duplicateDispatches"], 0);
        let events = body["timeline"].as_array().unwrap();
        assert!(events.len() <= event_limit as usize);
        if event_limit == 100 {
            let issued = events
                .iter()
                .find(|e| e["eventType"] == "DISPATCH_ISSUED")
                .unwrap();
            assert_eq!(issued["attemptId"], body["attempts"][0]["attemptId"]);
        }
    }
    let attempt = &inspection["structuredContent"]["attempts"][0];
    assert_eq!(attempt["exitCode"], 0);
    assert_eq!(exec["structuredContent"]["exitCode"], attempt["exitCode"]);
    assert_eq!(attempt["startedAtMs"], started);
    assert_eq!(attempt["finishedAtMs"], finished);
    assert!(
        attempt.get("durationMs").is_none(),
        "mixed clock duration is not a physical measurement"
    );
    let listed = call(
        &endpoint,
        "job.list",
        json!({"clientRequestId":"pg-native-physical-0001","limit":1}),
    );
    assert_ne!(listed["isError"], true, "{listed}");
    assert_eq!(
        listed["structuredContent"]["jobs"][0]["startedAtMs"],
        started
    );
    let post_terminal_cancel = call(&endpoint, "job.cancel", json!({"jobId":completed_job}));
    assert_ne!(
        post_terminal_cancel["isError"], true,
        "terminal Job cancel must return the existing observation: {post_terminal_cancel}"
    );
    assert_eq!(
        post_terminal_cancel["structuredContent"]["executionDisposition"],
        "succeeded"
    );
    assert_eq!(
        post_terminal_cancel["structuredContent"]["executionTerminal"],
        true
    );
    let (desired, resolution, current_attempt): (String, Option<String>, Option<String>) = {
        let row = fixture
            .db
            .query_one(
                "SELECT desired_state,resolution,current_attempt_id FROM jobs WHERE job_id=$1",
                &[&completed_job],
            )
            .unwrap();
        (row.get(0), row.get(1), row.get(2))
    };
    assert_eq!(
        desired, "run",
        "terminal cancel must not persist a new stop intent"
    );
    assert_eq!(resolution.as_deref(), Some("succeeded"));
    assert!(
        current_attempt.is_none(),
        "terminal Job current Attempt is released by design"
    );
    let artifacts = exec["structuredContent"]["artifacts"].as_array().unwrap();
    let stdout = artifacts.iter().find(|v| v["kind"] == "stdout").unwrap();
    let read = call(
        &endpoint,
        "artifact.read",
        json!({"jobId":exec["structuredContent"]["jobId"],"artifactId":stdout["artifactId"],"offset":0,"maxBytes":100}),
    );
    assert_eq!(read["structuredContent"]["content"], "native-proof");
    // M6->M7 evidence continuity: a completed stdout Artifact is immutable
    // evidence. The tail in job.observe must not silently bypass the same
    // PostgreSQL digest check that artifact.read enforces.
    let stdout_path: String = fixture
        .db
        .query_one(
            "SELECT a.bundle_path || '/' || r.relative_path FROM artifacts r JOIN attempts a \
         ON a.attempt_id=r.attempt_id WHERE r.artifact_id=$1",
            &[&stdout["artifactId"].as_str().unwrap()],
        )
        .unwrap()
        .get(0);
    // Published stdout must be a separate verified byte carrier from the
    // Runner's mutable source, so a delayed producer append cannot erase an
    // already-received Artifact. This is a genuine PG/Native consumer check.
    let original_stdout = PathBuf::from(&stdout_path).with_file_name("stdout.log");
    assert_ne!(
        PathBuf::from(&stdout_path),
        original_stdout,
        "registered bytes still alias the mutable Runner source"
    );
    fs::write(&original_stdout, b"late-producer-append-after-terminal").unwrap();
    let published_artifact = call(
        &endpoint,
        "artifact.read",
        json!({"jobId":completed_job,"artifactId":stdout["artifactId"],"offset":0,"maxBytes":100}),
    );
    assert_eq!(
        published_artifact["structuredContent"]["content"], "native-proof",
        "a mutable Runner source must not invalidate an already published Artifact"
    );
    // Only the disposable, already terminal fixture may retire its raw log.
    // The public readback must depend on the committed Artifact, not the preview.
    fs::remove_file(&original_stdout).unwrap();
    let retired_raw = call(
        &endpoint,
        "job.observe",
        json!({"jobId":completed_job,"waitMs":0,"stdoutTailBytes":4,"stderrTailBytes":0}),
    );
    assert_ne!(retired_raw["isError"], true, "{retired_raw}");
    assert_eq!(retired_raw["structuredContent"]["stdoutTail"], "roof");
    assert_eq!(retired_raw["structuredContent"]["stdoutOffset"], 8);
    assert_eq!(retired_raw["structuredContent"]["stdoutNextOffset"], 12);
    assert_eq!(retired_raw["structuredContent"]["stdoutAvailableBytes"], 12);
    let after_raw_retire = call(
        &endpoint,
        "artifact.read",
        json!({"jobId":completed_job,"artifactId":stdout["artifactId"],"offset":0,"maxBytes":100}),
    );
    assert_eq!(
        after_raw_retire["structuredContent"]["content"],
        "native-proof"
    );
    fs::write(&stdout_path, b"forged-stdout-after-terminal").unwrap();
    let forged_artifact = call(
        &endpoint,
        "artifact.read",
        json!({
            "jobId":exec["structuredContent"]["jobId"],
            "artifactId":stdout["artifactId"],"offset":0,"maxBytes":100
        }),
    );
    assert_eq!(forged_artifact["isError"], true, "{forged_artifact}");
    let forged_observation = call(
        &endpoint,
        "job.observe",
        json!({
            "jobId":exec["structuredContent"]["jobId"],
            "waitMs":0,"waitUntil":"change_or_terminal",
            "stdoutTailBytes":200,"stderrTailBytes":0
        }),
    );
    assert_eq!(
        forged_observation["isError"], true,
        "terminal stdoutTail bypassed Artifact digest while artifact.read rejected it: {forged_observation}"
    );
    let forged_zero_tail = call(
        &endpoint,
        "job.observe",
        json!({"jobId":completed_job,"waitMs":0,"stdoutTailBytes":0,"stderrTailBytes":0}),
    );
    assert_eq!(forged_zero_tail["isError"], true, "{forged_zero_tail}");
    fs::write(&stdout_path, b"native-proof").unwrap();
    let restored = call(
        &endpoint,
        "job.observe",
        json!({
            "jobId":exec["structuredContent"]["jobId"],"waitMs":0,
            "stdoutTailBytes":200,"stderrTailBytes":0
        }),
    );
    assert_ne!(restored["isError"], true, "{restored}");
    assert_eq!(restored["structuredContent"]["stdoutTail"], "native-proof");
    // The same committed-evidence law must cover stderr, including an
    // originally empty stderr Artifact, not just the nonempty stdout.
    let stderr_artifact = artifacts.iter().find(|v| v["kind"] == "stderr").unwrap();
    let stderr_path: String = fixture
        .db
        .query_one(
            "SELECT a.bundle_path || '/' || r.relative_path FROM artifacts r JOIN attempts a \
         ON a.attempt_id=r.attempt_id WHERE r.artifact_id=$1",
            &[&stderr_artifact["artifactId"].as_str().unwrap()],
        )
        .unwrap()
        .get(0);
    let original_stderr = PathBuf::from(&stderr_path).with_file_name("stderr.log");
    assert_ne!(PathBuf::from(&stderr_path), original_stderr);
    fs::write(&original_stderr, b"late-stderr-after-terminal").unwrap();
    let still_empty_stderr = call(
        &endpoint,
        "job.observe",
        json!({"jobId":completed_job,"waitMs":0,"stdoutTailBytes":0,"stderrTailBytes":200}),
    );
    assert_ne!(still_empty_stderr["isError"], true, "{still_empty_stderr}");
    assert!(
        still_empty_stderr["structuredContent"]["stderrTail"].is_null()
            || still_empty_stderr["structuredContent"]["stderrTail"] == "",
        "empty stderr must not gain bytes from its mutable Runner source: {still_empty_stderr}"
    );
    let still_empty_artifact = call(
        &endpoint,
        "artifact.read",
        json!({"jobId":completed_job,"artifactId":stderr_artifact["artifactId"],"offset":0,"maxBytes":100}),
    );
    assert_ne!(
        still_empty_artifact["isError"], true,
        "{still_empty_artifact}"
    );
    assert_eq!(still_empty_artifact["structuredContent"]["content"], "");
    fs::write(&stderr_path, b"forged-stderr-after-terminal").unwrap();
    let forged_stderr = call(
        &endpoint,
        "job.observe",
        json!({
            "jobId":exec["structuredContent"]["jobId"],
            "waitMs":0,"stdoutTailBytes":0,"stderrTailBytes":200
        }),
    );
    assert_eq!(
        forged_stderr["isError"], true,
        "completed stderrTail cannot bypass Artifact digest: {forged_stderr}"
    );
    fs::write(&stderr_path, b"").unwrap();
    // Cross-module M4/M8 identity must separate the replay-stable request
    // from the world-bound committed Operation. Different new client keys
    // with the same proposal and changed Workspace content should preserve
    // request identity but bind different immutable execution plans.
    let first_id: String = exec["structuredContent"]["jobId"]
        .as_str()
        .unwrap()
        .to_owned();
    let first_digests = fixture.db.query_one(
        "SELECT request_digest,operation_digest,execution_plan_digest FROM jobs WHERE job_id=$1",
        &[&first_id],
    ).unwrap();
    let first_request: String = first_digests.get(0);
    let first_operation: String = first_digests.get(1);
    let first_plan: String = first_digests.get(2);
    let changed = call(
        &endpoint,
        "workspace.mutate",
        json!({
            "workspaceId":"ws-physical",
            "mutations":[{"mode":"WRITE","relativePath":"new-state.txt","content":"new-source"}]
        }),
    );
    assert_ne!(changed["isError"], true, "{changed}");
    // Reusing the committed clientRequestId must not re-interpret the now
    // changed Workspace, compute a fresh operation, or launch twice.
    let replay_after_drift = call(
        &endpoint,
        "workspace.exec",
        json!({
            "clientRequestId":"pg-native-physical-0001",
            "execution":{"workspaceId":"ws-physical","executable":"/usr/bin/printf",
                         "args":["native-proof"],"cwdRelative":".","timeoutMs":5000},
            "waitMs":10000
        }),
    );
    assert_ne!(replay_after_drift["isError"], true, "{replay_after_drift}");
    assert_eq!(replay_after_drift["structuredContent"]["jobId"], first_id);
    let dispatch_count: i64 = fixture
        .db
        .query_one(
            "SELECT count(*) FROM job_events WHERE job_id=$1 AND event_type='DISPATCH_ISSUED'",
            &[&first_id],
        )
        .unwrap()
        .get(0);
    assert_eq!(
        dispatch_count, 1,
        "exact replay must never redispatch the first Attempt"
    );
    let second = call(
        &endpoint,
        "workspace.exec",
        json!({
            "clientRequestId":"pg-native-physical-0002",
            "execution":{"workspaceId":"ws-physical","executable":"/usr/bin/printf",
                         "args":["native-proof"],"cwdRelative":".","timeoutMs":5000},
            "waitMs":10000
        }),
    );
    assert_ne!(second["isError"], true, "{second}");
    assert_eq!(
        second["structuredContent"]["executionDisposition"], "succeeded",
        "{second}"
    );
    let second_id = second["structuredContent"]["jobId"].as_str().unwrap();
    let second_digests = fixture.db.query_one(
        "SELECT request_digest,operation_digest,execution_plan_digest FROM jobs WHERE job_id=$1",
        &[&second_id],
    ).unwrap();
    let second_request: String = second_digests.get(0);
    let second_operation: String = second_digests.get(1);
    let second_plan: String = second_digests.get(2);
    assert_eq!(
        first_request, second_request,
        "clientRequestId is not part of request identity"
    );
    assert_ne!(
        first_plan, second_plan,
        "Workspace source drift must change frozen plan"
    );
    assert_ne!(
        first_operation, second_operation,
        "M4/M8 Operation identity must bind the frozen world, not merely the proposal"
    );
    // Native multi-step plan is one PG Job/Attempt and one Runner launch.
    let plan_request = json!({
        "clientRequestId":"pg-native-plan-0001",
        "execution":{"workspaceId":"ws-physical","steps":[
            {"id":"first","executable":"/usr/bin/printf","args":["pg-plan-first"],"cwdRelative":".","timeoutMs":4000},
            {"id":"second","executable":"/usr/bin/printf","args":["pg-plan-second"],"cwdRelative":".","timeoutMs":4000}
        ]},
        "waitMs":12000,"stdoutTailBytes":8192
    });
    let planned_first = call(&endpoint, "workspace.execPlan", plan_request.clone());
    // The physical Job can already be committed when a later PostgreSQL
    // reconciliation/observation snapshot reports 40001. In that case do
    // NOT resubmit the effect: retain the exact committed operation identity
    // and reconcile by Job ID, as the public MCP retry contract requires.
    let planned = if planned_first["isError"] == true {
        assert_eq!(
            planned_first["structuredContent"]["error"]["commitState"], "committed",
            "{planned_first}"
        );
        assert_eq!(
            planned_first["structuredContent"]["error"]["retryClass"], "reconcile_first",
            "{planned_first}"
        );
        let committed = planned_first["structuredContent"]["error"]["operationId"]
            .as_str()
            .expect("known committed operationId")
            .to_string();
        let mut observed = serde_json::Value::Null;
        for _ in 0..5 {
            observed = call(
                &endpoint,
                "job.observe",
                json!({"jobId":committed,"waitMs":12000,"stdoutTailBytes":8192}),
            );
            if observed["isError"] != true {
                break;
            }
            assert_eq!(
                observed["structuredContent"]["error"]["commitState"], "committed",
                "{observed}"
            );
            assert_eq!(
                observed["structuredContent"]["error"]["operationId"], committed,
                "{observed}"
            );
        }
        observed
    } else {
        planned_first
    };
    assert_ne!(planned["isError"], true, "{planned}");
    assert_eq!(
        planned["structuredContent"]["executionDisposition"], "succeeded",
        "{planned}"
    );
    let plan_output = planned["structuredContent"]["stdoutTail"]
        .as_str()
        .unwrap_or("");
    assert!(plan_output.contains("pg-plan-first"), "{planned}");
    assert!(plan_output.contains("pg-plan-second"), "{planned}");
    let plan_id = planned["structuredContent"]["jobId"]
        .as_str()
        .unwrap()
        .to_string();
    let plan_replay = call(&endpoint, "workspace.execPlan", plan_request);
    assert_ne!(plan_replay["isError"], true, "{plan_replay}");
    assert_eq!(plan_replay["structuredContent"]["jobId"], plan_id);
    let issued: i64 = fixture
        .db
        .query_one(
            "SELECT count(*) FROM job_events WHERE job_id=$1 AND event_type='DISPATCH_ISSUED'",
            &[&plan_id],
        )
        .unwrap()
        .get(0);
    assert_eq!(issued, 1, "idempotent plan replay cannot launch again");

    // Fail-fast is proven by exact Runner output, not simulated by MCP.
    let stopped = call(
        &endpoint,
        "workspace.execPlan",
        json!({
            "clientRequestId":"pg-native-plan-failfast-0001",
            "execution":{"workspaceId":"ws-physical","steps":[
                {"id":"fail","executable":"/usr/bin/false","cwdRelative":".","timeoutMs":3000},
                {"id":"must-not-run","executable":"/usr/bin/printf","args":["FAILFAST_BROKEN"],"cwdRelative":".","timeoutMs":3000}
            ]},"waitMs":12000,"stdoutTailBytes":8192
        }),
    );
    assert_ne!(stopped["isError"], true, "{stopped}");
    assert_eq!(
        stopped["structuredContent"]["executionDisposition"], "failed",
        "{stopped}"
    );
    assert!(
        !stopped["structuredContent"]["stdoutTail"]
            .as_str()
            .unwrap_or("")
            .contains("FAILFAST_BROKEN"),
        "{stopped}"
    );
    // The actual Gateway/Agent job.list consumer must retain the terminal
    // Attempt after jobs.current_attempt_id is cleared on completion.
    let finished_list = call(
        &endpoint,
        "job.list",
        json!({"clientRequestId":"pg-native-plan-failfast-0001","limit":2}),
    );
    assert_ne!(finished_list["isError"], true, "{finished_list}");
    let listed_attempt = &finished_list["structuredContent"]["jobs"][0];
    assert_eq!(listed_attempt["executionTerminal"], true, "{finished_list}");
    assert_eq!(
        listed_attempt["attemptId"], stopped["structuredContent"]["attemptId"],
        "terminal list lost the last Attempt: {finished_list}"
    );
    assert_eq!(
        listed_attempt["exitCode"], stopped["structuredContent"]["exitCode"],
        "terminal list lost the final process exit: {finished_list}"
    );
    assert_eq!(listed_attempt["resultAvailable"], true, "{finished_list}");
    assert_eq!(
        listed_attempt["deliveryDisposition"], "committed",
        "{finished_list}"
    );
    let sleep = call(
        &endpoint,
        "workspace.exec",
        json!({"clientRequestId":"pg-native-cancel-0001","execution":{"workspaceId":"ws-physical","executable":"/usr/bin/sleep","args":["30"],"cwdRelative":".","timeoutMs":40000},"waitMs":500}),
    );
    assert_ne!(sleep["isError"], true, "{sleep}");
    let job = &sleep["structuredContent"]["jobId"];
    // Establish the physical launch identity before requesting systemd stop.
    // Otherwise an absent transient Unit could race with dispatch and cannot
    // justify an OS-only LOST terminal transition.
    let bundle: String = fixture
        .db
        .query_one(
            "SELECT a.bundle_path FROM attempts a WHERE a.job_id=$1",
            &[&job.as_str().unwrap()],
        )
        .unwrap()
        .get(0);
    let start_path = PathBuf::from(bundle).join("runner-start.json");
    let start_deadline = Instant::now() + Duration::from_secs(8);
    while !start_path.exists() && Instant::now() < start_deadline {
        thread::sleep(Duration::from_millis(50));
    }
    assert!(
        start_path.exists(),
        "physical cancellation test requires bound Runner start evidence"
    );
    // Genuine PG→systemd→Runner acceptance: the original long-lived Job must
    // become RUNNING only after the native bound receipt exists, not merely
    // because DISPATCH_ISSUED was committed or stdout was produced.
    let bound_deadline = Instant::now() + Duration::from_secs(8);
    loop {
        let running = call(
            &endpoint,
            "job.observe",
            json!({
                "jobId":job,"waitMs":0,"stdoutTailBytes":0,"stderrTailBytes":0
            }),
        );
        assert_ne!(
            running["isError"], true,
            "native Runner observation failed: {running}"
        );
        if running["structuredContent"]["attemptState"] == "running" {
            break;
        }
        assert!(
            Instant::now() < bound_deadline,
            "native start receipt failed to advance PG Attempt: {running}"
        );
        thread::sleep(Duration::from_millis(70));
    }
    let bound = fixture.db.query_one(
        "SELECT a.state,a.started_at_ms,COUNT(e.event_id) FILTER(WHERE e.event_type='RUNNER_BOUND') \
            FROM jobs j JOIN attempts a ON a.attempt_id=j.current_attempt_id AND a.job_id=j.job_id \
            LEFT JOIN job_events e ON e.job_id=j.job_id AND e.attempt_id=a.attempt_id \
            WHERE j.job_id=$1 GROUP BY a.state,a.started_at_ms",
        &[&job.as_str().unwrap()],
    ).unwrap();
    assert_eq!(bound.get::<_, String>(0), "running");
    assert!(bound.get::<_, Option<i64>>(1).is_some());
    assert_eq!(
        bound.get::<_, i64>(2),
        1,
        "RUNNER_BOUND must be recorded exactly once"
    );
    let unsafe_write = call(
        &endpoint,
        "workspace.mutate",
        json!({"workspaceId":"ws-physical","mutations":[{"mode":"WRITE","relativePath":"during-job.txt","content":"not allowed"}]}),
    );
    assert_eq!(unsafe_write["isError"], true, "{unsafe_write}");
    assert_eq!(
        unsafe_write["structuredContent"]["error"]["code"], "CONCURRENCY_LIMIT",
        "{unsafe_write}"
    );
    let cancelled = call(&endpoint, "job.cancel", json!({"jobId":job}));
    assert_ne!(cancelled["isError"], true, "{cancelled}");
    // Recovery must converge even after the client stops observing.
    let recovery_deadline = Instant::now() + Duration::from_secs(12);
    loop {
        let resolution: Option<String> = fixture
            .db
            .query_one(
                "SELECT resolution FROM jobs WHERE job_id=$1",
                &[&job.as_str().unwrap()],
            )
            .unwrap()
            .get(0);
        if resolution.is_some() {
            break;
        }
        assert!(
            Instant::now() < recovery_deadline,
            "background cancellation recovery did not converge"
        );
        thread::sleep(Duration::from_millis(100));
    }
    let mut observed = call(&endpoint, "job.observe", json!({"jobId":job,"waitMs":3000}));
    for _ in 0..10 {
        if observed["structuredContent"]["executionTerminal"] == true {
            break;
        }
        observed = call(&endpoint, "job.observe", json!({"jobId":job,"waitMs":3000}));
    }
    // A submitted stop alone was never proof of termination. This physical
    // test first observed a bound native Runner start, then requires the
    // installed provider to converge after systemd's cgroup shutdown.
    assert_eq!(
        observed["structuredContent"]["terminationIntent"], "stop_requested",
        "{observed}"
    );
    assert_eq!(
        observed["structuredContent"]["executionTerminal"], true,
        "native stop failed to converge: {observed}"
    );
    assert_ne!(
        observed["structuredContent"]["executionDisposition"], "succeeded",
        "a requested native stop cannot fabricate successful effect: {observed}"
    );
    let reservation: String = fixture
        .db
        .query_one(
            "SELECT r.state FROM concurrency_reservations r JOIN attempts a ON a.attempt_id=r.attempt_id WHERE a.job_id=$1",
            &[&job.as_str().unwrap()],
        )
        .unwrap()
        .get(0);
    assert_eq!(
        reservation, "released",
        "native quiescence did not release capacity"
    );
    if observed["structuredContent"]["executionDisposition"] == "lost" {
        assert_eq!(
            observed["structuredContent"]["resultAvailable"], false,
            "OS-only LOST terminal must not advertise a Runner result: {observed}"
        );
        assert_eq!(
            observed["structuredContent"]["deliveryDisposition"], "unknown",
            "a native-stop Artifact cannot convert LOST into a delivered Runner result: {observed}"
        );
        assert!(
            observed["structuredContent"]["artifacts"]
                .as_array()
                .is_some_and(|items| items.iter().any(|v| v["kind"] == "native_stop_evidence")),
            "LOST terminal must retain digest-bound native stop evidence: {observed}"
        );
    }
    let count: i64 = fixture
        .db
        .query_one(
            "SELECT count(*) FROM job_events WHERE job_id=$1 AND event_type='DISPATCH_ISSUED'",
            &[&job.as_str().unwrap()],
        )
        .unwrap()
        .get(0);
    assert_eq!(
        count, 1,
        "cancellation must not cause a second physical launch"
    );
    // A genuinely admitted Attempt that never crossed dispatch can cancel
    // without any invented native-process evidence. Use the public admission
    // store and an existing valid plan, never hand-edit live lifecycle rows.
    let record = fixture.db.query_one(
        "SELECT workspace_id,workspace_snapshot_json,execution_plan_json,execution_plan_digest FROM jobs WHERE job_id=$1",
        &[&job.as_str().unwrap()],
    ).unwrap();
    let pending_job = format!("job-{}", Uuid::now_v7());
    let pending_attempt = format!("attempt-{}", Uuid::now_v7());
    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_millis() as i64;
    let input = ordivon_runtime_core::pg_admission::PgAdmissionInput {
        job_id: pending_job.clone(),
        attempt_id: pending_attempt.clone(),
        reservation_id: format!("reservation-{}", Uuid::now_v7()),
        principal: "pg-consumer".into(),
        client_request_id: "cancel-before-dispatch-native".into(),
        request_digest: format!("sha256:{}", "b".repeat(64)),
        operation_digest: format!("sha256:{}", "c".repeat(64)),
        workspace_id: record.get(0),
        workspace_snapshot_json: record.get(1),
        execution_plan_json: record.get(2),
        execution_plan_digest: record.get(3),
        launch_token_digest: format!("sha256:{}", "d".repeat(64)),
        bundle_path: fixture
            .root
            .join("store/pg-attempts")
            .join(&pending_attempt)
            .to_string_lossy()
            .into_owned(),
        unit_name: format!("ordivon-pg-{pending_attempt}.service"),
        global_limit: 4,
        created_at_ms: now,
        expected_source_sha256: "a".repeat(64),
    };
    let dsn = format!(
        "host={} user=runtime_app dbname=postgres",
        fixture.root.display()
    );
    ordivon_runtime_core::pg_admission::PgAdmissionStore::connect(&dsn, "fresh")
        .unwrap()
        .admit(&input)
        .unwrap();
    let cancelled = call(&endpoint, "job.cancel", json!({"jobId":pending_job}));
    assert_ne!(cancelled["isError"], true, "{cancelled}");
    assert_eq!(
        cancelled["structuredContent"]["executionDisposition"],
        "cancelled"
    );
    assert_eq!(cancelled["structuredContent"]["resultAvailable"], false);
    let never_bound = call(&endpoint, "job.get", json!({"jobId":pending_job}));
    assert_ne!(never_bound["isError"], true, "{never_bound}");
    let attempt = &never_bound["structuredContent"]["attempts"][0];
    assert!(
        attempt.get("startedAtMs").is_none(),
        "pre-dispatch cancel has no Runner bound observation"
    );
    assert!(attempt.get("durationMs").is_none());
    let dispatched: i64 = fixture
        .db
        .query_one(
            "SELECT count(*) FROM job_events WHERE job_id=$1 AND event_type='DISPATCH_ISSUED'",
            &[&pending_job],
        )
        .unwrap()
        .get(0);
    assert_eq!(
        dispatched, 0,
        "cancelled pre-dispatch Attempt was physically launched"
    );
    // Restart only the MCP control process while its independent native Unit
    // runs. Recovery must consume the existing result, never launch again.
    let running = call(
        &endpoint,
        "workspace.exec",
        json!({
        "clientRequestId":"native-control-restart", "execution":{
            "workspaceId":input.workspace_id,"executable":"/usr/bin/sleep",
            "args":["2"],"cwdRelative":".","timeoutMs":15000},"waitMs":0}),
    );
    assert_ne!(running["isError"], true, "{running}");
    let running_job = running["structuredContent"]["jobId"].as_str().unwrap();
    let old_control = fixture.endpoint.as_mut().unwrap();
    old_control.kill().unwrap();
    old_control.wait().unwrap();
    let restarted_endpoint = fixture.endpoint();
    let deadline = Instant::now() + Duration::from_secs(12);
    loop {
        let resolution: Option<String> = fixture
            .db
            .query_one(
                "SELECT resolution FROM jobs WHERE job_id=$1",
                &[&running_job],
            )
            .unwrap()
            .get(0);
        if resolution.as_deref() == Some("succeeded") {
            break;
        }
        assert!(
            Instant::now() < deadline,
            "native result did not converge after control-plane restart"
        );
        thread::sleep(Duration::from_millis(100));
    }
    let after_restart = call(&restarted_endpoint, "job.get", json!({"jobId":running_job}));
    assert_eq!(
        after_restart["structuredContent"]["job"]["mechanicallyConverged"],
        true
    );
    let dispatches: i64 = fixture
        .db
        .query_one(
            "SELECT count(*) FROM job_events WHERE job_id=$1 AND event_type='DISPATCH_ISSUED'",
            &[&running_job],
        )
        .unwrap()
        .get(0);
    assert_eq!(
        dispatches, 1,
        "control-plane restart duplicated physical execution"
    );
}

// Source qualification must be checked at the time of each new effect.
// A running server may outlive an operator's revocation of its PG writer.
#[test]
#[ignore = "launches a disposable native PostgreSQL cluster; run explicitly"]
fn fresh_pg_revoked_writer_refuses_new_workspace_effects() {
    let mut fixture = Fixture::new();
    let repo = fixture.repo();
    let endpoint = fixture.endpoint();
    let existing = call(
        &endpoint,
        "workspace.open",
        json!({"workspaceId":"ws-revoke-existing","sourceRepo":repo,"sourceRevision":"HEAD"}),
    );
    assert_ne!(existing["isError"], true, "{existing}");
    let list_before = call(&endpoint, "job.list", json!({"limit": 1}));
    assert_ne!(list_before["isError"], true, "{list_before}");

    // Source remains QUALIFIED_WRITER: revoke ONLY the independently bound
    // physical epoch. A long-lived MCP must reject fresh Workspace effects.
    fixture
        .db
        .execute(
            "UPDATE _stage_control SET promotion_allowed=false WHERE id='epoch'",
            &[],
        )
        .unwrap();
    let epoch_denied = call(
        &endpoint,
        "workspace.open",
        json!({"workspaceId":"ws-revoke-epoch","sourceRepo":repo,"sourceRevision":"HEAD"}),
    );
    assert_eq!(
        epoch_denied["isError"], true,
        "source-only writer accepted new work with revoked physical epoch: {epoch_denied}",
    );
    let epoch_list_denied = call(&endpoint, "job.list", json!({"limit": 1}));
    assert_eq!(
        epoch_list_denied["isError"], true,
        "revoked physical epoch falsely projected current Job list: {epoch_list_denied}",
    );
    let epoch_mutation_denied = call(
        &endpoint,
        "workspace.mutate",
        json!({"workspaceId":"ws-revoke-existing","mutations":[{
            "mode":"WRITE","relativePath":"revoked-epoch.txt","content":"must-not-write"
        }]}),
    );
    assert_eq!(
        epoch_mutation_denied["isError"], true,
        "{epoch_mutation_denied}"
    );
    fixture
        .db
        .execute(
            "UPDATE _stage_control SET promotion_allowed=true WHERE id='epoch'",
            &[],
        )
        .unwrap();

    let requalified_list = call(&endpoint, "job.list", json!({"limit": 1}));
    assert_ne!(requalified_list["isError"], true, "{requalified_list}");
    fixture
        .db
        .execute(
            "UPDATE _stage_control SET promotion_allowed=false WHERE id='source'",
            &[],
        )
        .unwrap();

    let opened = call(
        &endpoint,
        "workspace.open",
        json!({"workspaceId":"ws-revoke-new","sourceRepo":repo,"sourceRevision":"HEAD"}),
    );
    assert_eq!(
        opened["isError"], true,
        "unqualified writer created a Workspace: {opened}"
    );

    let changed = call(
        &endpoint,
        "workspace.mutate",
        json!({"workspaceId":"ws-revoke-existing","mutations":[{
            "mode":"WRITE","relativePath":"revoked-writer.txt","content":"must-not-write"
        }]}),
    );
    assert_eq!(
        changed["isError"], true,
        "unqualified writer changed Workspace: {changed}"
    );

    let closed = call(
        &endpoint,
        "workspace.close",
        json!({"workspaceId":"ws-revoke-existing","consumerReleased":true}),
    );
    assert_eq!(
        closed["isError"], true,
        "unqualified writer removed Workspace: {closed}"
    );

    let kept = call(
        &endpoint,
        "workspace.get",
        json!({"workspaceId":"ws-revoke-existing"}),
    );
    assert_ne!(kept["isError"], true, "{kept}");
    assert_eq!(
        kept["structuredContent"]["workspaceId"],
        "ws-revoke-existing"
    );
    assert_eq!(
        fixture
            .db
            .query_one("SELECT count(*) FROM jobs", &[])
            .unwrap()
            .get::<_, i64>(0),
        0
    );
}

#[test]
#[ignore = "launches an isolated native PostgreSQL cluster"]
fn pg_startup_refuses_application_self_qualified_control_table() {
    use ordivon_runtime_core::{PgRuntime, PgRuntimeConfig, UniversalExecutorConfig};
    let fixture = Fixture::new();
    // RED: the current fixture is both the stage-control owner and the app
    // principal. That principal can promote itself without an operator.
    let candidate = PgRuntime::new(PgRuntimeConfig {
        dsn: format!(
            "host={} user=postgres dbname=postgres",
            fixture.root.display()
        ),
        schema: "fresh".into(),
        source_sha256: "a".repeat(64),
        harness_spawn_dsn_file: None,
        harness_issuer_schema: None,
        harness_dispatch_issuer: None,
        workspace_headroom: Vec::new(),
        executor: UniversalExecutorConfig {
            store_root: fixture.root.join("self-qualified-attempt"),
            workspace_root: None,
            workspace_uid: None,
            workspace_gid: None,
            runner_path: None,
            allowed_executable_roots: vec![PathBuf::from("/usr/bin")],
            max_runtime_ms: 30_000,
            max_output_bytes: 1_048_576,
        },
    });
    assert!(
        candidate.is_err(),
        "a role that owns _stage_control cannot independently qualify its own writer"
    );
    assert!(
        !fixture.root.join("self-qualified-attempt").exists(),
        "self-qualified PostgreSQL authority must not create Workspace directories"
    );
}

// A scoped current_user cannot prove separation from the authenticated
// session_user: SET ROLE NONE restores the session owner's privileges.
#[test]
#[ignore = "launches an isolated PostgreSQL cluster; explicit operator-role falsifier"]
fn pg_runtime_refuses_privileged_session_hidden_behind_app_role() {
    use ordivon_runtime_core::{PgRuntime, PgRuntimeConfig, UniversalExecutorConfig};
    let mut fixture = Fixture::new();
    fixture
        .db
        .batch_execute("ALTER ROLE postgres SET role TO runtime_app")
        .unwrap();
    let dsn = format!(
        "host={} user=postgres dbname=postgres",
        fixture.root.display()
    );
    let mut authenticated = Client::connect(&dsn, NoTls).unwrap();
    let row = authenticated
        .query_one("SELECT current_user::text, session_user::text", &[])
        .unwrap();
    let effective: String = row.get(0);
    let session: String = row.get(1);
    assert_eq!(effective, "runtime_app");
    assert_eq!(session, "postgres");
    authenticated.batch_execute("SET ROLE NONE").unwrap();
    let row = authenticated
        .query_one("SELECT current_user::text", &[])
        .unwrap();
    assert_eq!(row.get::<_, String>(0), "postgres");

    let candidate = PgRuntime::new(PgRuntimeConfig {
        dsn,
        schema: "fresh".into(),
        source_sha256: "a".repeat(64),
        harness_spawn_dsn_file: None,
        harness_issuer_schema: None,
        harness_dispatch_issuer: None,
        workspace_headroom: Vec::new(),
        executor: UniversalExecutorConfig {
            store_root: fixture.root.join("session-authority-candidate"),
            workspace_root: None,
            workspace_uid: None,
            workspace_gid: None,
            runner_path: None,
            allowed_executable_roots: vec![PathBuf::from("/usr/bin")],
            max_runtime_ms: 30_000,
            max_output_bytes: 1_048_576,
        },
    });
    assert!(
        candidate.is_err(),
        "the authenticated session owner can regain stage-control authority via SET ROLE NONE"
    );
}

#[test]
#[ignore = "launches disposable native PostgreSQL and systemd Runner; run explicitly"]
fn pg_host_dependencies_real_runner_and_committed_idempotency() {
    use sha2::Digest as _;

    let mut fixture = Fixture::new();
    let repo = fixture.repo();
    let endpoint = fixture.endpoint();
    let reference = fixture.root.join("pg-host-dependency.bin");
    fs::write(&reference, b"immutable-fact-v1").unwrap();
    let digest = format!(
        "sha256:{}",
        hex::encode(sha2::Sha256::digest(fs::read(&reference).unwrap()))
    );

    let opened = call(
        &endpoint,
        "workspace.open",
        json!({"workspaceId":"ws-pg-prerequisite","sourceRepo":repo,"sourceRevision":"HEAD"}),
    );
    assert_ne!(opened["isError"], true, "{opened}");

    let proposal = |key: &str, committed_digest: &str| {
        json!({
            "clientRequestId":key,
            "execution":{
                "workspaceId":"ws-pg-prerequisite",
                "executable":"/usr/bin/printf",
                "args":["pg-prerequisite-witness"],
                "cwdRelative":".",
                "timeoutMs":10000,
                "hostDependencies":[{
                    "path":reference,
                    "expectedDigest":committed_digest,
                }]
            },
            "waitMs":12000,
            "stdoutTailBytes":256,
        })
    };
    let describe = call(&endpoint, "runtime.describe", json!({}));
    assert_eq!(
        describe["structuredContent"]["targets"][0]["hostDependencyCommitments"],
        true
    );
    let rejected = call(
        &endpoint,
        "workspace.exec",
        proposal(
            "pg-prerequisite-wrong-0001",
            &format!("sha256:{}", "0".repeat(64)),
        ),
    );
    assert_eq!(rejected["isError"], true, "{rejected}");
    let no_job: i64 = fixture
        .db
        .query_one(
            "SELECT count(*) FROM jobs WHERE client_request_id=$1",
            &[&"pg-prerequisite-wrong-0001"],
        )
        .unwrap()
        .get(0);
    assert_eq!(no_job, 0, "bad host bytes must not create a PostgreSQL Job");

    let admitted = call(
        &endpoint,
        "workspace.exec",
        proposal("pg-prerequisite-good-0001", &digest),
    );
    assert_ne!(admitted["isError"], true, "{admitted}");
    assert_eq!(
        admitted["structuredContent"]["executionDisposition"], "succeeded",
        "{admitted}"
    );
    assert_eq!(
        admitted["structuredContent"]["stdoutTail"],
        "pg-prerequisite-witness"
    );
    let job = admitted["structuredContent"]["jobId"].as_str().unwrap();
    let row = fixture
        .db
        .query_one(
            "SELECT execution_plan_json FROM jobs WHERE job_id=$1",
            &[&job],
        )
        .unwrap();
    let committed_plan: Value = serde_json::from_str(row.get::<_, String>(0).as_str()).unwrap();
    assert_eq!(
        committed_plan["hostDependencies"][0]["expectedDigest"],
        digest
    );
    // Exact replay resolves the original PostgreSQL Job before inspecting
    // mutable external prerequisites. A new client key cannot ignore drift.
    fs::write(&reference, b"changed-after-commit").unwrap();
    let replay = call(
        &endpoint,
        "workspace.exec",
        proposal("pg-prerequisite-good-0001", &digest),
    );
    assert_ne!(replay["isError"], true, "{replay}");
    assert_eq!(replay["structuredContent"]["jobId"], job);
    let post_drift = call(
        &endpoint,
        "workspace.exec",
        proposal("pg-prerequisite-new-0001", &digest),
    );
    assert_eq!(post_drift["isError"], true, "{post_drift}");
    let dispatched: i64 = fixture
        .db
        .query_one(
            "SELECT count(*) FROM job_events WHERE job_id=$1 AND event_type='DISPATCH_ISSUED'",
            &[&job],
        )
        .unwrap()
        .get(0);
    assert_eq!(dispatched, 1, "an exact replay must never launch again");
}

#[test]
#[ignore = "real PostgreSQL/systemd resource queue and mount contract"]
fn resource_queue_shared_workspace_restart_and_native_write_leases() {
    let mut fixture = Fixture::new();
    let repo = fixture.repo();
    let mut endpoint = fixture.endpoint();
    let opened = call(
        &endpoint,
        "workspace.open",
        json!({"workspaceId":"ws-resource-queue","sourceRepo":repo,"sourceRevision":"HEAD"}),
    );
    assert_ne!(opened["isError"], true, "{opened}");
    let node = call(&endpoint, "runtime.describe", json!({}));
    assert!(node["structuredContent"]["globalExecutionLimit"].is_null());
    let cpu = node["structuredContent"]["scheduling"]["node"]["cpuMillis"]
        .as_u64()
        .unwrap();
    let schedule = |cpu: u64, access: Value| json!({"resources":{"cpuMillis":cpu,"memoryBytes":16777216,"pids":8},"workspaceAccess":access});
    let submit = |endpoint: &str, id: &str, args: Vec<&str>, cpu: u64, access: Value| {
        call(
            endpoint,
            "workspace.exec",
            json!({"clientRequestId":id,"execution":{"workspaceId":"ws-resource-queue","executable":"/usr/bin/sh","args":args,"cwdRelative":".","timeoutMs":120000,"budget":{"scheduling":schedule(cpu,access)}},"waitMs":0,"stdoutTailBytes":0,"stderrTailBytes":0}),
        )
    };
    let wait = |db: &mut Client, jobs: &[String]| {
        let deadline = Instant::now() + Duration::from_secs(20);
        loop {
            let count: i64 = db
                .query_one(
                    "SELECT count(*) FROM jobs WHERE job_id=ANY($1) AND resolution IS NULL",
                    &[&jobs],
                )
                .unwrap()
                .get(0);
            if count == 0 {
                break;
            }
            assert!(Instant::now() < deadline, "queued jobs failed to converge");
            thread::sleep(Duration::from_millis(100));
        }
    };
    // A full CPU request blocks a CPU-consuming peer but not CPU-free waiting work.
    let release_blocker = fixture.root.join("release-blocker");
    let blocker_script = format!(
        "while [ ! -f '{}' ]; do sleep 0.1; done",
        release_blocker.display()
    );
    let blocker = submit(
        &endpoint,
        "resource-blocker",
        vec!["-c", blocker_script.as_str()],
        cpu,
        json!({"readOnly":true}),
    );
    assert_ne!(blocker["isError"], true, "{blocker}");
    let blocked = submit(
        &endpoint,
        "resource-pending",
        vec!["-c", "true"],
        100,
        json!({"readOnly":true}),
    );
    assert_ne!(blocked["isError"], true, "{blocked}");
    assert_eq!(
        blocked["structuredContent"]["scheduling"]["state"], "pending",
        "{blocked}"
    );
    let replay = submit(
        &endpoint,
        "resource-pending",
        vec!["-c", "true"],
        100,
        json!({"readOnly":true}),
    );
    assert_eq!(
        replay["structuredContent"]["jobId"],
        blocked["structuredContent"]["jobId"]
    );
    let queued_cancel = submit(
        &endpoint,
        "resource-pending-cancel",
        vec!["-c", "true"],
        100,
        json!({"readOnly":true}),
    );
    let cancelled = call(
        &endpoint,
        "job.cancel",
        json!({"jobId":queued_cancel["structuredContent"]["jobId"]}),
    );
    assert_eq!(
        cancelled["structuredContent"]["executionDisposition"], "cancelled",
        "{cancelled}"
    );
    let control = fixture.endpoint.as_mut().unwrap();
    assert!(Command::new("kill")
        .args(["-INT", &control.id().to_string()])
        .status()
        .unwrap()
        .success());
    let shutdown_deadline = Instant::now() + Duration::from_secs(5);
    loop {
        if let Some(status) = control.try_wait().unwrap() {
            assert!(status.success(), "unclean scheduler shutdown");
            break;
        }
        assert!(
            Instant::now() < shutdown_deadline,
            "scheduler prevented graceful control shutdown"
        );
        thread::sleep(Duration::from_millis(50));
    }
    endpoint = fixture.endpoint();
    fs::write(&release_blocker, b"release").unwrap();
    wait(
        &mut fixture.db,
        &[
            blocker["structuredContent"]["jobId"]
                .as_str()
                .unwrap()
                .into(),
            blocked["structuredContent"]["jobId"]
                .as_str()
                .unwrap()
                .into(),
        ],
    );
    let release = fixture.root.join("release-readers");
    let shared_wait = format!("while [ ! -f '{}' ]; do sleep 0.1; done", release.display());
    let mut shared = Vec::new();
    for n in 0..6 {
        let result = submit(
            &endpoint,
            &format!("shared-reader-{n}"),
            vec!["-c", shared_wait.as_str()],
            0,
            json!({"readOnly":true}),
        );
        assert_ne!(result["isError"], true, "{result}");
        shared.push(
            result["structuredContent"]["jobId"]
                .as_str()
                .unwrap()
                .to_string(),
        );
    }
    let allocated:i64=fixture.db.query_one("SELECT count(*) FROM job_allocations x JOIN attempts a ON a.attempt_id=x.attempt_id WHERE a.job_id=ANY($1) AND x.state='active'",&[&shared]).unwrap().get(0);
    assert!(
        allocated >= 5,
        "fixed global or per-Workspace count still limits shared work: {allocated}"
    );
    fs::write(&release, b"release").unwrap();
    wait(&mut fixture.db, &shared);
    let changed = call(
        &endpoint,
        "workspace.mutate",
        json!({"workspaceId":"ws-resource-queue","mutations":[{"mode":"WRITE","relativePath":"left/.keep","content":"left"},{"mode":"WRITE","relativePath":"right/.keep","content":"right"}]}),
    );
    assert_ne!(changed["isError"], true, "{changed}");
    let release_writes = fixture.root.join("release-writes");
    let left_script = format!(
        "set -e; echo left > left/out; while [ ! -f '{}' ]; do sleep 0.1; done",
        release_writes.display()
    );
    let right_script = format!(
        "set -e; echo right > right/out; while [ ! -f '{}' ]; do sleep 0.1; done",
        release_writes.display()
    );
    let left = submit(
        &endpoint,
        "scope-left",
        vec!["-c", left_script.as_str()],
        0,
        json!({"readPaths":["left"],"writePaths":["left"]}),
    );
    let right = submit(
        &endpoint,
        "scope-right",
        vec!["-c", right_script.as_str()],
        0,
        json!({"readPaths":["right"],"writePaths":["right"]}),
    );
    assert_ne!(left["isError"], true, "{left}");
    assert_ne!(right["isError"], true, "{right}");
    assert_eq!(
        left["structuredContent"]["scheduling"]["state"], "allocated",
        "{left}"
    );
    assert_eq!(
        right["structuredContent"]["scheduling"]["state"], "allocated",
        "{right}"
    );
    let conflict = submit(
        &endpoint,
        "scope-conflict",
        vec!["-c", "echo serial > left/later"],
        0,
        json!({"readPaths":["left"],"writePaths":["left"]}),
    );
    assert_eq!(
        conflict["structuredContent"]["scheduling"]["state"], "pending",
        "{conflict}"
    );
    let independent_mutation = call(
        &endpoint,
        "workspace.mutate",
        json!({"workspaceId":"ws-resource-queue","mutations":[{"mode":"WRITE","relativePath":"other/independent","content":"independent"}]}),
    );
    assert_ne!(
        independent_mutation["isError"], true,
        "unrelated mutation was blocked by a Workspace count: {independent_mutation}"
    );
    let conflicting_mutation = call(
        &endpoint,
        "workspace.mutate",
        json!({"workspaceId":"ws-resource-queue","mutations":[{"mode":"WRITE","relativePath":"left/blocked","content":"must wait"}]}),
    );
    assert_eq!(
        conflicting_mutation["structuredContent"]["error"]["code"],
        "CONCURRENCY_LIMIT"
    );
    fs::write(&release_writes, b"release").unwrap();
    let ids = [left, right, conflict]
        .iter()
        .map(|v| {
            v["structuredContent"]["jobId"]
                .as_str()
                .unwrap()
                .to_string()
        })
        .collect::<Vec<_>>();
    wait(&mut fixture.db, &ids);
    for job in &ids {
        let state: String = fixture
            .db
            .query_one("SELECT resolution FROM jobs WHERE job_id=$1", &[job])
            .unwrap()
            .get(0);
        if state != "succeeded" {
            let bundle: String = fixture
                .db
                .query_one("SELECT bundle_path FROM attempts WHERE job_id=$1", &[job])
                .unwrap()
                .get(0);
            for name in ["result.json", "stderr.log", "stderr.bin", "stderr"] {
                if let Ok(content) = fs::read_to_string(PathBuf::from(&bundle).join(name)) {
                    eprintln!(
                        "SCOPE_DIAGNOSTIC {job} {name}: {}",
                        &content[..content.len().min(8000)]
                    );
                }
            }
            eprintln!(
                "SCOPE_BUNDLE_FILES {:?}",
                fs::read_dir(&bundle)
                    .unwrap()
                    .map(|v| v.unwrap().file_name())
                    .collect::<Vec<_>>()
            );
        }
        assert_eq!(state, "succeeded", "scoped native write failed for {job}");
    }
    let denied = submit(
        &endpoint,
        "scope-denied",
        vec!["-c", "touch outside-scope"],
        0,
        json!({"readOnly":true}),
    );
    let denied_id = denied["structuredContent"]["jobId"]
        .as_str()
        .unwrap()
        .to_string();
    wait(&mut fixture.db, std::slice::from_ref(&denied_id));
    let state: String = fixture
        .db
        .query_one("SELECT resolution FROM jobs WHERE job_id=$1", &[&denied_id])
        .unwrap()
        .get(0);
    assert_eq!(state, "failed", "native read-only boundary was bypassed");
    let listed = call(&endpoint, "job.list", json!({"limit":100}));
    assert_ne!(listed["isError"], true, "{listed}");
}

#[test]
#[ignore = "real PostgreSQL/systemd dominant-share and idle borrowing"]
fn resource_queue_owner_fairness_and_idle_borrowing() {
    let mut fixture = Fixture::new();
    let repo = fixture.repo();
    let endpoint = fixture.endpoint();
    let opened = call(
        &endpoint,
        "workspace.open",
        json!({"workspaceId":"ws-owner-fairness","sourceRepo":repo,"sourceRevision":"HEAD"}),
    );
    assert_ne!(opened["isError"], true, "{opened}");
    let describe = call(&endpoint, "runtime.describe", json!({}));
    let cpu = describe["structuredContent"]["scheduling"]["node"]["cpuMillis"]
        .as_u64()
        .unwrap();
    let release_blocker = fixture.root.join("release-borrower");
    let release_owners = fixture.root.join("release-owners");
    let submit = |id: &str, owner: &str, cpu: u64, marker: &PathBuf| {
        let script = format!("while [ ! -f '{}' ]; do sleep 0.1; done", marker.display());
        let result = call(
            &endpoint,
            "workspace.exec",
            json!({"clientRequestId":id,"execution":{"workspaceId":"ws-owner-fairness","executable":"/usr/bin/sh","args":["-c",script],"cwdRelative":".","timeoutMs":120000,"budget":{"scheduling":{"owner":owner,"resources":{"cpuMillis":cpu,"memoryBytes":16777216,"pids":8},"workspaceAccess":{"readOnly":true}}}},"waitMs":0}),
        );
        assert_ne!(result["isError"], true, "{result}");
        result["structuredContent"]["jobId"]
            .as_str()
            .unwrap()
            .to_string()
    };
    let borrower = submit("idle-borrower", "idle-owner", cpu, &release_blocker);
    let borrowed:bool=fixture.db.query_one("SELECT EXISTS(SELECT 1 FROM job_allocations x JOIN attempts a ON a.attempt_id=x.attempt_id WHERE a.job_id=$1 AND x.state='active')",&[&borrower]).unwrap().get(0);
    assert!(borrowed, "idle capacity was artificially capped per owner");
    let a1 = submit("owner-a-first", "owner-a", cpu / 2, &release_owners);
    let a2 = submit("owner-a-second", "owner-a", cpu / 2, &release_owners);
    let b1 = submit("owner-b-first", "owner-b", cpu / 2, &release_owners);
    fs::write(&release_blocker, b"release").unwrap();
    let deadline = Instant::now() + Duration::from_secs(20);
    loop {
        let owners=fixture.db.query("SELECT x.owner FROM job_allocations x JOIN attempts a ON a.attempt_id=x.attempt_id WHERE a.job_id=ANY($1) AND x.state='active' ORDER BY x.owner",&[&vec![a1.clone(),a2.clone(),b1.clone()]]).unwrap().iter().map(|r|r.get::<_,String>(0)).collect::<Vec<_>>();
        if owners == vec!["owner-a".to_string(), "owner-b".to_string()] {
            break;
        }
        assert!(
            Instant::now() < deadline,
            "dominant-share scheduling did not share released capacity: {owners:?}"
        );
        thread::sleep(Duration::from_millis(100));
    }
    let second_a_allocated:bool=fixture.db.query_one("SELECT EXISTS(SELECT 1 FROM job_allocations x JOIN attempts a ON a.attempt_id=x.attempt_id WHERE a.job_id=$1 AND x.state='active')",&[&a2]).unwrap().get(0);
    assert!(
        !second_a_allocated,
        "FIFO owner monopolized shared capacity"
    );
    fs::write(&release_owners, b"release").unwrap();
    let deadline = Instant::now() + Duration::from_secs(20);
    loop {
        let pending: i64 = fixture
            .db
            .query_one("SELECT count(*) FROM jobs WHERE resolution IS NULL", &[])
            .unwrap()
            .get(0);
        if pending == 0 {
            break;
        }
        assert!(Instant::now() < deadline, "fair-share jobs did not finish");
        thread::sleep(Duration::from_millis(100));
    }
}

#[test]
#[ignore = "disposable PG18 plus actual native MCP, systemd Runner and Artifacts"]
fn b_r3_native_poisoned_candidates_cannot_block_healthy_job() {
    let mut f = Fixture::new();
    f.host_visible_test_runner = true;
    let repo = f.repo();
    let endpoint = f.endpoint();
    let ws = format!("ws-b-r3-{}", Uuid::now_v7().simple());
    let opened = call(
        &endpoint,
        "workspace.open",
        json!({"workspaceId":ws,"sourceRepo":repo,"sourceRevision":"HEAD"}),
    );
    assert_ne!(opened["isError"], true, "{opened}");

    let seed = call(
        &endpoint,
        "workspace.exec",
        json!({
      "clientRequestId":format!("b-r3-seed-{}",Uuid::now_v7()),
      "execution":{"workspaceId":ws,"executable":"/usr/bin/printf","args":["B_R3_SEED"],
                   "cwdRelative":".","timeoutMs":15000},"waitMs":0}),
    );
    assert_ne!(seed["isError"], true, "{seed}");
    let seed_id = seed["structuredContent"]["jobId"]
        .as_str()
        .unwrap()
        .to_string();
    let seed_deadline = Instant::now() + Duration::from_secs(20);
    loop {
        let seen = call(
            &endpoint,
            "job.observe",
            json!({"jobId":seed_id,"waitMs":2000}),
        );
        assert_ne!(seen["isError"], true, "{seen}");
        if seen["structuredContent"]["executionTerminal"] == true {
            break;
        }
        assert!(
            Instant::now() < seed_deadline,
            "seed did not finish: {seen}"
        );
    }

    let seed_row=f.db.query_one("SELECT workspace_id,workspace_snapshot_json,execution_plan_json,execution_plan_digest,operation_digest FROM jobs WHERE job_id=$1",&[&seed_id]).unwrap();
    let workspace: String = seed_row.get(0);
    let original_snapshot: String = seed_row.get(1);
    let valid_plan: String = seed_row.get(2);
    let plan_digest: String = seed_row.get(3);
    let op_digest: String = seed_row.get(4);
    let mut provider_json: Value = serde_json::from_str(&original_snapshot).unwrap();
    assert!(
        provider_json["executionProvider"]["executableDigest"].is_string(),
        "{provider_json}"
    );
    provider_json["executionProvider"]["executableDigest"] =
        json!(format!("sha256:{}", "0".repeat(64)));
    let broken_provider = provider_json.to_string();
    let bad_plan = "{not-valid-json";
    let corrupt_id = format!("job-{}", Uuid::now_v7());
    let provider_id = format!("job-{}", Uuid::now_v7());
    let corrupt_attempt = format!("attempt-{}", Uuid::now_v7());
    let provider_attempt = format!("attempt-{}", Uuid::now_v7());
    let now_ms = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_millis() as i64;
    // Stage both malformed accepted states atomically before background scheduler sees them.
    let mut tx = f.db.transaction().unwrap();
    for (i, (job, attempt, plan, snapshot)) in [
        (&corrupt_id, &corrupt_attempt, bad_plan, &original_snapshot),
        (
            &provider_id,
            &provider_attempt,
            valid_plan.as_str(),
            &broken_provider,
        ),
    ]
    .into_iter()
    .enumerate()
    {
        let req = format!("b-r3-injected-{}-{}", i, Uuid::now_v7());
        let digest = format!("sha256:{}", "a".repeat(64));
        tx.execute("INSERT INTO jobs(job_id,principal,client_request_id,request_digest,operation_digest,workspace_id,workspace_snapshot_json,execution_plan_json,execution_plan_digest,created_at_ms,desired_state,resolution,current_attempt_id,row_version)
        VALUES($1,'pg-consumer',$2,$3,$4,$5,$6,$7,$8,$9,'run',NULL,$10,0)",
        &[job,&req,&digest,&op_digest,&workspace,snapshot,&plan,&plan_digest,&(now_ms+i as i64),attempt]).unwrap();
        tx.execute("INSERT INTO attempts(attempt_id,job_id,attempt_number,state,termination_intent,launch_token_digest,bundle_path,unit_name,created_at_ms,row_version)
        VALUES($1,$2,1,'accepted','natural',$3,$4,$5,$6,0)",
        &[attempt,job,&digest,&f.root.join("store/pg-attempts").join(attempt).to_string_lossy().to_string(),
          &format!("ordivon-pg-{attempt}.service"),&(now_ms+i as i64)]).unwrap();
        tx.execute("INSERT INTO concurrency_reservations(reservation_id,attempt_id,global_limit,state,acquired_at_ms,state_observed_at_ms)
        VALUES($1,$2,0,'active',$3,$3)",&[&format!("reservation-{}",Uuid::now_v7()),attempt,&now_ms]).unwrap();
    }
    tx.commit().unwrap();
    let good = call(
        &endpoint,
        "workspace.exec",
        json!({
      "clientRequestId":format!("b-r3-good-{}",Uuid::now_v7()),
      "execution":{"workspaceId":ws,"executable":"/usr/bin/printf","args":["B_R3_HEALTHY_NATIVE"],
                   "cwdRelative":".","timeoutMs":15000},"waitMs":0}),
    );
    assert_ne!(good["isError"], true, "{good}");
    let good_id = good["structuredContent"]["jobId"]
        .as_str()
        .unwrap()
        .to_string();
    let deadline = Instant::now() + Duration::from_secs(25);
    let finished = loop {
        let seen = call(
            &endpoint,
            "job.observe",
            json!({"jobId":good_id,"waitMs":2000,"stdoutTailBytes":1024}),
        );
        assert_ne!(seen["isError"], true, "{seen}");
        if seen["structuredContent"]["executionTerminal"] == true {
            break seen;
        }
        assert!(
            Instant::now() < deadline,
            "healthy Job blocked by poisoned accepted Job: {seen}"
        );
    };
    assert_eq!(
        finished["structuredContent"]["executionDisposition"], "succeeded",
        "{finished}"
    );
    assert!(
        finished["structuredContent"]["stdoutTail"]
            .as_str()
            .unwrap_or("")
            .contains("B_R3_HEALTHY_NATIVE"),
        "{finished}"
    );
    let issued: i64 =
        f.db.query_one(
            "SELECT count(*) FROM job_events WHERE job_id=$1 AND event_type='DISPATCH_ISSUED'",
            &[&good_id],
        )
        .unwrap()
        .get(0);
    assert_eq!(issued, 1, "must issue exactly once");
    let original_attempt_state: String =
        f.db.query_one(
            "SELECT a.state FROM attempts a WHERE a.job_id=$1",
            &[&good_id],
        )
        .unwrap()
        .get(0);
    assert_eq!(original_attempt_state, "succeeded");
    let artifact_id: String =
        f.db.query_one(
            "SELECT artifact_id FROM artifacts WHERE job_id=$1 AND kind='stdout' LIMIT 1",
            &[&good_id],
        )
        .unwrap()
        .get(0);
    let exact = call(
        &endpoint,
        "artifact.read",
        json!({"jobId":good_id,"artifactId":artifact_id,"offset":0,"maxBytes":512}),
    );
    assert_ne!(exact["isError"], true, "{exact}");
    let data = exact["structuredContent"].to_string();
    assert!(data.contains("B_R3_HEALTHY_NATIVE"), "{exact}");
    // An already diagnosed attempt must not write an event on each 1s tick.
    let issue_deadline = Instant::now() + Duration::from_secs(12);
    loop {
        let n: i64 =
            f.db.query_one(
                "SELECT count(*) FROM job_events WHERE job_id=$1 AND event_type='SCHEDULER_ISSUE'",
                &[&provider_id],
            )
            .unwrap()
            .get(0);
        if n > 0 {
            break;
        }
        assert!(
            Instant::now() < issue_deadline,
            "provider mismatch did not yield durable issue"
        );
        thread::sleep(Duration::from_millis(100));
    }
    thread::sleep(Duration::from_millis(2200));
    for (job, expected) in [
        (&corrupt_id, "SCHEDULER_CANDIDATE_INVALID"),
        (&provider_id, "SCHEDULER_RECONCILIATION_BLOCKED"),
    ] {
        let row=f.db.query_one("SELECT count(*),min(reason_code) FROM job_events WHERE job_id=$1 AND event_type='SCHEDULER_ISSUE'",&[job]).unwrap();
        assert_eq!(
            row.get::<_, i64>(0),
            1,
            "diagnostic must be bounded per Attempt"
        );
        assert_eq!(row.get::<_, String>(1), expected);
    }
    let provider_read = call(
        &endpoint,
        "job.get",
        json!({"jobId":provider_id,"eventLimit":20}),
    );
    assert_ne!(provider_read["isError"], true, "{provider_read}");
    assert_eq!(
        provider_read["structuredContent"]["scheduling"]["pendingReason"],
        Value::Null
    );
    assert!(
        provider_read
            .to_string()
            .contains("SCHEDULER_RECONCILIATION_BLOCKED"),
        "{provider_read}"
    );
    // The current closed public Scheduling schema requires a frozen
    // ResourceScheduling request. A corrupt plan cannot be materialized
    // without inventing data: tell the Agent that its Job record is invalid,
    // not that the healthy PostgreSQL server is unavailable. A future
    // typed UNKNOWN readback should replace this temporary negative gate.
    let bad_read = call(
        &endpoint,
        "job.get",
        json!({"jobId":corrupt_id,"eventLimit":20}),
    );
    assert_eq!(bad_read["isError"], true, "{bad_read}");
    assert_eq!(
        bad_read["structuredContent"]["error"]["code"], "INVALID_REQUEST",
        "{bad_read}"
    );
    assert_eq!(
        bad_read["structuredContent"]["error"]["field"], "executionPlan",
        "{bad_read}"
    );
    // A's typed partial JobList contract and B's per-candidate isolation must
    // compose at a real PG18 MCP consumer, not merely pass schema tests.
    let native_list = call(&endpoint, "job.list", json!({"limit":100}));
    assert_ne!(
        native_list["isError"], true,
        "PG list must not fail globally on one corrupt Plan: {native_list}"
    );
    let listed_jobs = native_list["structuredContent"]["jobs"]
        .as_array()
        .expect("PG job.list must preserve original jobs");
    let corrupt_listed = listed_jobs
        .iter()
        .find(|entry| entry["jobId"].as_str() == Some(corrupt_id.as_str()))
        .expect("PG job.list must retain corrupt Plan's Job identity");
    assert_eq!(corrupt_listed["executableName"], Value::Null);
    assert_eq!(corrupt_listed["cwdRelative"], Value::Null);
    assert_eq!(corrupt_listed["operationDigest"], op_digest);
    let healthy_listed = listed_jobs
        .iter()
        .find(|entry| entry["jobId"].as_str() == Some(good_id.as_str()))
        .expect("healthy Job must remain discoverable");
    assert_eq!(healthy_listed["executionDisposition"], "succeeded");
    // R31 falsifier: this already-created PG18 accepted Job has no issued
    // Runner/OS Unit. Its immutable Plan is malformed (verified above), but
    // the PostgreSQL STOP_REQUESTED CAS and trusted current Attempt identity
    // must still finish local cancellation and release native reservations.
    // Unlike the issued-running R30 case, no OS stop is permitted here.
    let cancel_bad = call(&endpoint, "job.cancel", json!({"jobId":corrupt_id}));
    let bad_after =
        f.db.query_one(
            "SELECT j.desired_state,j.resolution,j.current_attempt_id,a.state,a.termination_intent
         FROM jobs j JOIN attempts a ON a.job_id=j.job_id WHERE j.job_id=$1",
            &[&corrupt_id],
        )
        .unwrap();
    assert_eq!(bad_after.get::<_, String>(0), "cancelled", "{cancel_bad}");
    assert_eq!(bad_after.get::<_,Option<String>>(1), Some("cancelled".into()),
        "the already-committed pre-dispatch cancel must not stay held behind broken Plan: {cancel_bad}");
    assert_eq!(
        bad_after.get::<_, Option<String>>(2),
        None,
        "resolved current Attempt pointer must be atomically cleared: {cancel_bad}"
    );
    assert_eq!(bad_after.get::<_, String>(3), "cancelled", "{cancel_bad}");
    assert_eq!(
        bad_after.get::<_, String>(4),
        "stop_requested",
        "{cancel_bad}"
    );
    let os_dispatches: i64 =
        f.db.query_one(
            "SELECT count(*) FROM job_events WHERE job_id=$1 AND event_type='DISPATCH_ISSUED'",
            &[&corrupt_id],
        )
        .unwrap()
        .get(0);
    assert_eq!(
        os_dispatches, 0,
        "cannot invent a native launch for a never-issued Attempt"
    );
    let remaining: i64 =
        f.db.query_one(
            "SELECT count(*) FROM concurrency_reservations r JOIN attempts a
         ON a.attempt_id=r.attempt_id
         WHERE a.job_id=$1 AND r.state='active'",
            &[&corrupt_id],
        )
        .unwrap()
        .get(0);
    assert_eq!(
        remaining, 0,
        "cancelled pre-dispatch Job must release PG capacity"
    );
    let proof: i64 =
        f.db.query_one(
            "SELECT count(*) FROM artifacts WHERE job_id=$1 AND kind='admission_cancel_evidence'",
            &[&corrupt_id],
        )
        .unwrap()
        .get(0);
    assert_eq!(
        proof, 1,
        "must retain original PG cancellation proof without dispatch"
    );
    // Agent-facing original PG Tool consumers must observe the completed
    // cancellation without reconstructing untrustworthy Plan properties.
    let after_list = call(&endpoint, "job.list", json!({"limit":100}));
    assert_ne!(after_list["isError"], true, "{after_list}");
    let cancelled = after_list["structuredContent"]["jobs"]
        .as_array()
        .unwrap()
        .iter()
        .find(|x| x["jobId"].as_str() == Some(corrupt_id.as_str()))
        .unwrap();
    assert_eq!(
        cancelled["executionDisposition"], "cancelled",
        "{after_list}"
    );
    assert_eq!(cancelled["executionTerminal"], true, "{after_list}");
    assert_eq!(cancelled["executableName"], Value::Null);
    assert_eq!(cancelled["cwdRelative"], Value::Null);
    // A real MCP Artifact consumer validates the deterministically committed
    // original cancellation bytes, not only the PG row existence.
    let proof_id:String=f.db.query_one(
        "SELECT artifact_id FROM artifacts WHERE job_id=$1 AND kind='admission_cancel_evidence'",
        &[&corrupt_id]).unwrap().get(0);
    let proof_read = call(
        &endpoint,
        "artifact.read",
        json!({
            "jobId":corrupt_id,"artifactId":proof_id,"offset":0,"maxBytes":4096
        }),
    );
    assert_ne!(proof_read["isError"], true, "{proof_read}");
    assert_eq!(proof_read["structuredContent"]["eof"], true);
    let exact: Value =
        serde_json::from_str(proof_read["structuredContent"]["content"].as_str().unwrap()).unwrap();
    assert_eq!(exact["jobId"], corrupt_id);
    assert_eq!(exact["attemptId"], corrupt_attempt);
    assert_eq!(exact["dispatchIssued"], false);
    assert_eq!(exact["terminalState"], "cancelled");
    eprintln!("R31_NATIVE_PG18_CORRUPT_ACCEPTED_CANCEL_RELEASED original_job={corrupt_id} no_dispatch=true capacity_released=true proof=1 original_agent_joblist=true exact_artifact=true");
    eprintln!("A_B_R27_NATIVE_PG18_JOBLIST_AND_SCHEDULER_COMPOSITION_PASS corrupt={corrupt_id} healthy={good_id}");
    eprintln!("B_R3_PG18_NATIVE_GREEN good={good_id} bad={corrupt_id} provider={provider_id} issue_count=1 stdout=B_R3_HEALTHY_NATIVE");
}

/// Regression for the committed-cancel/physical-OS boundary: an accepted
/// immutable plan's corrupted JSON must not prevent stopping its already
/// issued native systemd Attempt. Test-owned PostgreSQL, Git, and native Unit.
#[test]
#[ignore = "requires disposable PG18, native HTTP MCP, real systemd runner"]
fn b_r3_native_cancel_corrupt_frozen_plan_stops_issued_os_unit() {
    let mut f = Fixture::new();
    f.host_visible_test_runner = true;
    let repo = f.repo();
    let endpoint = f.endpoint();
    let ws = format!("ws-r30-cancel-{}", Uuid::now_v7().simple());
    let opened = call(
        &endpoint,
        "workspace.open",
        json!({
            "workspaceId":ws,"sourceRepo":repo,"sourceRevision":"HEAD"
        }),
    );
    assert_ne!(opened["isError"], true, "{opened}");
    let admitted = call(
        &endpoint,
        "workspace.exec",
        json!({
            "clientRequestId":format!("r30-cancel-{}",Uuid::now_v7()),
            "execution":{"workspaceId":ws,"executable":"/usr/bin/sleep",
            "args":["25"],"cwdRelative":".","timeoutMs":35000},
            "waitMs":0
        }),
    );
    assert_ne!(admitted["isError"], true, "{admitted}");
    let job_id = admitted["structuredContent"]["jobId"]
        .as_str()
        .unwrap()
        .to_owned();
    let deadline = Instant::now() + Duration::from_secs(18);
    let unit_name = loop {
        let row =
            f.db.query_opt(
                "SELECT a.state,a.unit_name FROM attempts a JOIN jobs j
             ON j.current_attempt_id=a.attempt_id AND a.job_id=j.job_id
             WHERE j.job_id=$1",
                &[&job_id],
            )
            .unwrap();
        if let Some(row) = row {
            let state: String = row.get(0);
            let unit: String = row.get(1);
            if state == "running" {
                let output = Command::new("/usr/bin/systemctl")
                    .args(["show", &unit, "-p", "ActiveState", "-p", "MainPID"])
                    .output()
                    .unwrap();
                let status = String::from_utf8_lossy(&output.stdout);
                if status.contains("ActiveState=active") && !status.contains("MainPID=0") {
                    break unit;
                }
            }
        }
        assert!(
            Instant::now() < deadline,
            "native Job never reached an active OS Unit"
        );
        thread::sleep(Duration::from_millis(100));
    };
    let mutated =
        f.db.execute(
            "UPDATE jobs SET execution_plan_json=$2 WHERE job_id=$1 AND resolution IS NULL",
            &[&job_id, &"{r30-poisoned-frozen-plan"],
        )
        .unwrap();
    assert_eq!(mutated, 1, "must poison only self-owned running Job");
    let cancel = call(&endpoint, "job.cancel", json!({"jobId":job_id}));
    let desired: String =
        f.db.query_one("SELECT desired_state FROM jobs WHERE job_id=$1", &[&job_id])
            .unwrap()
            .get(0);
    assert_eq!(desired, "cancelled", "cancel intent must persist: {cancel}");
    assert_eq!(
        cancel["structuredContent"]["error"]["commitState"], "committed",
        "post-commit bad Plan must retain committed identity: {cancel}"
    );
    assert_eq!(
        cancel["structuredContent"]["error"]["operationId"], job_id,
        "agent may only reconcile the SAME Job: {cancel}"
    );
    let mut drained = false;
    let stop_deadline = Instant::now() + Duration::from_secs(3);
    while Instant::now() < stop_deadline {
        let output = Command::new("/usr/bin/systemctl")
            .args(["show", &unit_name, "-p", "ActiveState", "-p", "MainPID"])
            .output()
            .unwrap();
        let status = String::from_utf8_lossy(&output.stdout);
        if (status.contains("ActiveState=inactive") || status.contains("ActiveState=failed"))
            && status.contains("MainPID=0")
        {
            drained = true;
            break;
        }
        thread::sleep(Duration::from_millis(100));
    }
    // Preserve native physical cleanup even on expected RED. This test is
    // only allowed to stop its own Attempt's exact committed Unit identity.
    if !drained {
        let _ = Command::new("/usr/bin/systemctl")
            .args(["stop", &unit_name])
            .status();
    }
    assert!(
        drained,
        "committed cancel did not stop its original active OS Unit after a damaged Plan: {cancel}"
    );
    // Corrupt Plan still cannot be called a semantic success; readback must
    // preserve the Job's identity and explicitly project unknown plan fields.
    let listed = call(&endpoint, "job.list", json!({"limit":100}));
    assert_ne!(listed["isError"], true, "{listed}");
    let rows = listed["structuredContent"]["jobs"].as_array().unwrap();
    let row = rows
        .iter()
        .find(|x| x["jobId"].as_str() == Some(job_id.as_str()))
        .unwrap();
    assert_eq!(row["executableName"], Value::Null);
    assert_eq!(row["cwdRelative"], Value::Null);
    eprintln!("R30_NATIVE_PG18_CORRUPT_PLAN_CANCEL_OS_DRAIN_PASS job={job_id} original_unit={unit_name} denied_false_success={}",cancel["isError"]);
}

fn r16_raw_mcp_envelope(url: &str, bearer: &str, name: &str, args: Value) -> (u16, Value) {
    tokio::runtime::Runtime::new().unwrap().block_on(async {
        let client = reqwest::Client::new();
        let response = client
            .post(url)
            .bearer_auth(bearer)
            .header("Accept", "application/json, text/event-stream")
            .header("MCP-Protocol-Version", "2026-07-28")
            .header("Mcp-Method", "tools/call")
            .header("Mcp-Name", name)
            .json(&json!({
                "jsonrpc":"2.0","id":1,"method":"tools/call",
                "params":{"name":name,"arguments":args,
                    "_meta":{
                        "io.modelcontextprotocol/protocolVersion":"2026-07-28",
                        "io.modelcontextprotocol/clientCapabilities":{}
                    }
                }
            }))
            .send()
            .await
            .unwrap();
        let status = response.status().as_u16();
        let body = response.text().await.unwrap();
        if status != 200 {
            return (status, json!({"body":body}));
        }
        let message: Value = if body.starts_with("event:") || body.starts_with("data:") {
            serde_json::from_str(body.lines().find_map(|s| s.strip_prefix("data: ")).unwrap())
                .unwrap()
        } else {
            serde_json::from_str(&body).unwrap()
        };
        (status, message)
    })
}

fn r16_dedicated_call(url: &str, bearer: &str, name: &str, args: Value) -> (u16, Value) {
    let (status, envelope) = r16_raw_mcp_envelope(url, bearer, name, args);
    if status == 200 {
        (status, envelope["result"].clone())
    } else {
        (status, envelope)
    }
}

#[test]
#[ignore = "real disposable PostgreSQL18, native PG MCP, dedicated Claim finalizer bearer"]
fn pg18_claim_finalizer_only_ingress_boots_without_foreign_harness_schema() {
    let mut fixture = Fixture::new();
    fixture.claim_only_profile = true;
    let repo = fixture.repo();
    let id = Uuid::now_v7().simple().to_string();
    let workspace_id = format!("r52-claimonly-{id}");
    let request_id = format!("request:r52-claimonly-{id}");
    let run_ref = format!("harness-run:r52-claimonly-{id}");
    let issuer_functions: i64 = fixture
        .db
        .query_one(
            "SELECT count(*) FROM pg_proc WHERE proname='harness_current_dispatch_cut'",
            &[],
        )
        .unwrap()
        .get(0);
    assert_eq!(
        issuer_functions, 0,
        "no foreign Harness issuer must be present"
    );

    let ordinary = fixture.endpoint();
    let dedicated = ordinary.replacen("/mcp", "/harness/mcp", 1);
    let opened = call(
        &ordinary,
        "workspace.open",
        json!({
            "workspaceId":workspace_id,"sourceRepo":repo,"sourceRevision":"HEAD",
        }),
    );
    assert_ne!(opened["isError"], true, "{opened}");
    let workspace = call(
        &ordinary,
        "workspace.get",
        json!({"workspaceId":workspace_id}),
    );
    assert_ne!(workspace["isError"], true, "{workspace}");
    let original_source_digest = workspace["structuredContent"]["sourceStateDigest"]
        .as_str()
        .expect("native Git original source digest")
        .to_owned();

    let (wrong_bearer, _) = r16_dedicated_call(
        &dedicated,
        &"p".repeat(32),
        "workspace.claim.get",
        json!({"clientRequestId":request_id}),
    );
    assert_eq!(wrong_bearer, 401);

    let (reserve_http, reserve) = r16_dedicated_call(
        &dedicated,
        &"h".repeat(48),
        "workspace.claim.reserve",
        json!({
            "schemaVersion":1,"workspaceId":workspace_id,
            "clientRequestId":request_id,"runRef":run_ref,
            "expectedSourceStateDigest":original_source_digest
        }),
    );
    assert_eq!(reserve_http, 200, "{reserve}");
    assert_ne!(reserve["isError"], true, "{reserve}");
    assert_eq!(reserve["structuredContent"]["state"], "held");
    let claim_id = reserve["structuredContent"]["claimId"]
        .as_str()
        .unwrap()
        .to_owned();
    let key = json!({"schemaVersion":1,"clientRequestId":request_id});

    // Dedicated token only carries original Claim ownership, not Runtime Job
    // execution, Workspace closure, or Root release authority. Both raw calls
    // are denied BEFORE any PG side effect, independent of advertised tools.
    for (tool, arguments) in [
        ("workspace.exec", json!({})),
        (
            "workspace.close",
            json!({"workspaceId":workspace_id,"force":true}),
        ),
        ("release.apply", json!({})),
    ] {
        let (status, result) = r16_dedicated_call(&dedicated, &"h".repeat(48), tool, arguments);
        assert_eq!(status, 200, "PG MCP protocol response: {result}");
        assert_eq!(
            result,
            Value::Null,
            "{tool} must be rejected as JSON-RPC error"
        );
    }
    let active_jobs: i64 = fixture
        .db
        .query_one("SELECT count(*) FROM jobs", &[])
        .unwrap()
        .get(0);
    assert_eq!(
        active_jobs, 0,
        "Claim-only Finalizer spawned or admitted a Job"
    );
    let held = r16_dedicated_call(
        &dedicated,
        &"h".repeat(48),
        "workspace.claim.get",
        key.clone(),
    );
    assert_eq!(held.0, 200);
    assert_eq!(held.1["structuredContent"]["state"], "held");
    assert_eq!(held.1["structuredContent"]["claimId"], claim_id);

    let denied_close = call(
        &ordinary,
        "workspace.close",
        json!({
            "workspaceId":workspace_id,"force":false,"consumerReleased":true,
            "expectedSourceStateDigest":original_source_digest,
        }),
    );
    assert_eq!(
        denied_close["isError"], true,
        "Claim HELD must block NativeClose"
    );

    // Independent Domain output acceptance and every issued native OS Job
    // have not been verified. Even this SAME original dedicated bearer and
    // SAME original immutable key may NOT release a HELD Run. Both first
    // attempt and replay must fail before opening any PG write transaction.
    for _ in 0..2 {
        let (http, response) = r16_raw_mcp_envelope(
            &dedicated,
            &"h".repeat(48),
            "workspace.claim.release",
            key.clone(),
        );
        assert_eq!(http, 200, "{response}");
        assert_eq!(response["error"]["code"], -32602, "{response}");
        assert!(
            response["error"]["message"]
                .as_str()
                .is_some_and(|message| message.contains("independently received")),
            "{response}"
        );
    }
    let (get_http, after) =
        r16_dedicated_call(&dedicated, &"h".repeat(48), "workspace.claim.get", key);
    assert_eq!(get_http, 200);
    assert_eq!(after["structuredContent"]["claimId"], claim_id);
    assert_eq!(after["structuredContent"]["state"], "held");
    let closed = call(
        &ordinary,
        "workspace.close",
        json!({
            "workspaceId":workspace_id,"force":false,"consumerReleased":true,
            "expectedSourceStateDigest":original_source_digest,
        }),
    );
    assert_eq!(closed["isError"], true, "unsafe original Close: {closed}");
    assert_eq!(
        closed["structuredContent"]["error"]["code"], "CONCURRENCY_LIMIT",
        "{closed}"
    );
    let claim_state: String = fixture
        .db
        .query_one(
            "SELECT state FROM workspace_consumer_claims WHERE claim_id=$1",
            &[&claim_id],
        )
        .unwrap()
        .get(0);
    assert_eq!(claim_state, "held", "native PG pin must not be released");

    eprintln!(
        "R65_NATIVE_PG18_DEDICATED_BEARER_NO_DOMAIN_OR_OS_FINALIZER_HELD \
         reserve/read succeed, raw release/replay DENIED before PG, \
         original Workspace nonforce Close DENIED"
    );
}

// A real native PG MCP scheduler/HTTP consumer, with only original Run source
// simulated as definitively revoked. Admission is seeded into disposable PG,
// so this does not claim real Harness authenticated *admission* or Native ACK.
#[test]
#[ignore = "requires native PG18 / test-only systemd Runner and isolated MCP service"]
fn pg_mcp_scheduler_revoked_harness_job_reuses_existing_cancel() {
    use ordivon_runtime_core::pg_admission::{
        PgAdmissionInput, PgAdmissionOutcome, PgAdmissionStore,
    };
    use sha2::{Digest, Sha256};
    let digest =
        |bytes: &[u8]| -> String { format!("sha256:{}", hex::encode(Sha256::digest(bytes))) };
    let mut fixture = Fixture::new();
    fixture.host_visible_test_runner = true;
    let repo = fixture.repo();
    let normal_endpoint = fixture.endpoint();
    let workspace_id = format!("r16-owned-{}", Uuid::now_v7().simple());
    let opened = call(
        &normal_endpoint,
        "workspace.open",
        json!({"workspaceId":workspace_id,"sourceRepo":repo,"sourceRevision":"HEAD"}),
    );
    assert_ne!(
        opened["isError"], true,
        "original native Workspace required: {opened}"
    );
    let normal = call(
        &normal_endpoint,
        "workspace.exec",
        json!({
            "clientRequestId":format!("r16-ordinary-{}",Uuid::now_v7().simple()),
            "execution":{"workspaceId":workspace_id,"executable":"/usr/bin/printf",
                "args":["r16-normal"],"cwdRelative":".","timeoutMs":15000},
            "waitMs":0
        }),
    );
    assert_ne!(
        normal["isError"], true,
        "ordinary admission failed: {normal}"
    );
    let normal_id = normal["structuredContent"]["jobId"]
        .as_str()
        .unwrap()
        .to_owned();
    let deadline = Instant::now() + Duration::from_secs(30);
    loop {
        let observed = call(
            &normal_endpoint,
            "job.observe",
            json!({
                "jobId":normal_id,"waitMs":2000
            }),
        );
        assert_ne!(
            observed["isError"], true,
            "ordinary observe failed: {observed}"
        );
        if observed["structuredContent"]["executionTerminal"] == true {
            assert_eq!(
                observed["structuredContent"]["executionDisposition"], "succeeded",
                "ordinary native runner did not execute: {observed}"
            );
            break;
        }
        assert!(
            Instant::now() < deadline,
            "ordinary native runner not terminal: {observed}"
        );
    }
    let row = fixture
        .db
        .query_one(
            "SELECT workspace_snapshot_json,execution_plan_json FROM jobs WHERE job_id=$1",
            &[&normal_id],
        )
        .unwrap();
    let snapshot: String = row.get(0);
    let mut plan: Value = serde_json::from_str(&row.get::<_, String>(1)).unwrap();

    // Stop only this test's disposable service. It cannot issue an old Job
    // while the new accepted Attempt is prepared in the same isolated PG.
    let mut previous = fixture.endpoint.take().unwrap();
    previous.kill().unwrap();
    previous.wait().unwrap();

    fixture
        .db
        .batch_execute(
            "CREATE SCHEMA r16_issuer;
         CREATE FUNCTION r16_issuer.harness_current_dispatch_cut(text,bigint,text)
         RETURNS TABLE(event_kind text,payload_digest text,payload_kind text,
             payload_len bigint,payload_content bytea,fence_kind text,
             fence_len bigint,fence_content bytea,intent_digest text,
             intent_kind text,intent_len bigint,intent_content bytea)
         LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog
         AS $issuer$ BEGIN RETURN; END $issuer$;
         REVOKE ALL ON FUNCTION
          r16_issuer.harness_current_dispatch_cut(text,bigint,text) FROM PUBLIC;
         GRANT USAGE ON SCHEMA r16_issuer TO runtime_app;
         GRANT EXECUTE ON FUNCTION
          r16_issuer.harness_current_dispatch_cut(text,bigint,text) TO runtime_app;",
        )
        .unwrap();
    // A source-owned issuer returned no current cut: no future physical
    // dispatch may be committed for this previously accepted Test Job.
    let job = format!("job-r16-{}", Uuid::now_v7().simple());
    let attempt = format!("attempt-r16-{}", Uuid::now_v7().simple());
    let operation_digest = digest(format!("r16-operation:{job}").as_bytes());
    let launch_token =
        digest(format!("runtime-launch-v1\0{attempt}\0{operation_digest}").as_bytes());
    let frozen_ref = json!([
        {"namespace":"ordivon.harness","type":"harness_run",
         "id":"harness-run:r16-original"},
        {"namespace":"ordivon.harness","type":"dispatch_fence",
         "id":"harness-dispatch-fence:r16-original",
         "generation":"1","digest":format!("sha256:{}","f".repeat(64))}
    ]);
    plan["principal"] = json!("harness-dispatch-r16");
    plan["foreignReferences"] = frozen_ref;
    if plan["budget"]["scheduling"].is_object() {
        plan["budget"]["scheduling"]["owner"] = json!("harness-dispatch-r16");
    }
    let plan_json = serde_json::to_string(&plan).unwrap();
    let created_at = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_millis() as i64;
    let input = PgAdmissionInput {
        job_id: job.clone(),
        attempt_id: attempt.clone(),
        reservation_id: format!("reservation-{attempt}"),
        principal: "harness-dispatch-r16".into(),
        client_request_id: format!("r16-client-{attempt}"),
        request_digest: digest(format!("r16-request:{job}").as_bytes()),
        operation_digest,
        workspace_id: workspace_id.clone(),
        workspace_snapshot_json: snapshot,
        execution_plan_json: plan_json.clone(),
        execution_plan_digest: digest(plan_json.as_bytes()),
        launch_token_digest: digest(launch_token.as_bytes()),
        bundle_path: fixture
            .root
            .join("store")
            .join("pg-attempts")
            .join(&attempt)
            .to_string_lossy()
            .into_owned(),
        unit_name: format!("ordivon-pg-{attempt}.service"),
        global_limit: 0,
        created_at_ms: created_at,
        expected_source_sha256: "a".repeat(64),
    };
    let dsn = format!(
        "host={} user=postgres dbname=postgres",
        fixture.root.display()
    );
    let mut admission = PgAdmissionStore::connect(&dsn, "fresh").unwrap();
    assert_eq!(
        admission.admit(&input).unwrap(),
        PgAdmissionOutcome::Created(job.clone())
    );
    drop(admission);
    // This is a definite source denial, not a network error/PG UNKNOWN.
    // Single scheduler must consume the *existing* accepted Job rather than
    // launching a new Attempt or blocking unrelated ordinary Jobs.
    fixture.harness_dispatch_test = true;
    let endpoint = fixture.endpoint();
    let deadline = Instant::now() + Duration::from_secs(12);
    loop {
        let row = fixture
            .db
            .query_one("SELECT resolution FROM jobs WHERE job_id=$1", &[&job])
            .unwrap();
        let resolution: Option<String> = row.get(0);
        if resolution.as_deref() == Some("cancelled") {
            break;
        }
        if Instant::now() >= deadline {
            let state = fixture
                .db
                .query_one(
                    "SELECT j.desired_state,j.resolution,a.state,a.row_version,
                    a.bundle_digest,r.state
                 FROM jobs j JOIN attempts a ON a.attempt_id=j.current_attempt_id
                 JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id
                 WHERE j.job_id=$1",
                    &[&job],
                )
                .unwrap();
            let events = fixture
                .db
                .query(
                    "SELECT event_sequence,event_type,reason_code
                 FROM job_events WHERE job_id=$1 ORDER BY event_sequence",
                    &[&job],
                )
                .unwrap();
            let allocation = fixture
                .db
                .query(
                    "SELECT state,owner FROM job_allocations WHERE attempt_id=$1",
                    &[&attempt],
                )
                .unwrap();
            let log = fs::read_to_string(fixture.root.join("endpoint.log")).unwrap_or_default();
            panic!(
                "scheduler timed out. desired={:?} resolved={:?} attempt={:?} version={} bundle={:?} reservation={:?} events={:?} alloc={:?} logTail={}",
                state.get::<_,String>(0),state.get::<_,Option<String>>(1),
                state.get::<_,String>(2),state.get::<_,i64>(3),
                state.get::<_,Option<String>>(4),state.get::<_,String>(5),
                events.iter().map(|r|(r.get::<_,i64>(0),r.get::<_,String>(1),r.get::<_,String>(2))).collect::<Vec<_>>(),
                allocation.iter().map(|r|(r.get::<_,String>(0),r.get::<_,String>(1))).collect::<Vec<_>>(),
                log.chars().rev().take(1700).collect::<String>().chars().rev().collect::<String>()
            )
        }
        thread::sleep(Duration::from_millis(120));
    }
    let state = fixture
        .db
        .query_one(
            "SELECT j.resolution,a.state,r.state
         FROM jobs j JOIN attempts a ON a.job_id=j.job_id
         JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id
         WHERE j.job_id=$1",
            &[&job],
        )
        .unwrap();
    assert_eq!(
        state.get::<_, Option<String>>(0).as_deref(),
        Some("cancelled")
    );
    assert_eq!(state.get::<_, String>(1), "cancelled");
    assert_eq!(state.get::<_, String>(2), "released");
    let issued: i64 = fixture
        .db
        .query_one(
            "SELECT count(*) FROM job_events WHERE job_id=$1 AND event_type='DISPATCH_ISSUED'",
            &[&job],
        )
        .unwrap()
        .get(0);
    assert_eq!(
        issued, 0,
        "revoked original Job must never pass PG dispatch"
    );
    let issue: i64 = fixture
        .db
        .query_one(
            "SELECT count(*) FROM job_events WHERE job_id=$1 AND event_type='SCHEDULER_ISSUE'
         AND reason_code='HARNESS_ISSUER_NOT_CURRENT_AT_DISPATCH'",
            &[&job],
        )
        .unwrap()
        .get(0);
    assert_eq!(issue, 1, "must record a single actionable source denial");
    let artifact: i64 = fixture
        .db
        .query_one(
            "SELECT count(*) FROM artifacts a JOIN attempts t ON t.attempt_id=a.attempt_id
         WHERE t.job_id=$1 AND a.kind='admission_cancel_evidence'",
            &[&job],
        )
        .unwrap()
        .get(0);
    assert_eq!(
        artifact, 1,
        "existing cancelled-before-dispatch Artifact required"
    );
    let live_allocations: i64 = fixture
        .db
        .query_one(
            "SELECT count(*) FROM job_allocations a JOIN attempts t ON t.attempt_id=a.attempt_id
         WHERE t.job_id=$1 AND a.state='active'",
            &[&job],
        )
        .unwrap()
        .get(0);
    assert_eq!(
        live_allocations, 0,
        "source revocation must release capacity"
    );

    // A dedicated Harness MCP consumer reads the exact cancelled Job and
    // its original cancellation Artifact; the ordinary bearer is forbidden.
    let dedicated_endpoint = endpoint.replacen("/mcp", "/harness/mcp", 1);
    let (wrong_status, _) = r16_dedicated_call(
        &dedicated_endpoint,
        &"p".repeat(32),
        "job.get",
        json!({"jobId":job}),
    );
    assert_eq!(
        wrong_status, 401,
        "ordinary bearer must not impersonate Harness"
    );
    let (right_status, readback) = r16_dedicated_call(
        &dedicated_endpoint,
        &"h".repeat(48),
        "job.get",
        json!({"jobId":job}),
    );
    assert_eq!(
        right_status, 200,
        "dedicated Harness bearer must authenticate"
    );
    assert_ne!(
        readback["isError"], true,
        "dedicated Job readback failed: {readback}"
    );
    assert_eq!(
        readback["structuredContent"]["job"]["resolution"], "cancelled",
        "dedicated job.get reports historical Job resolution, not job.observe: {readback}"
    );
    assert_eq!(
        readback["structuredContent"]["job"]["mechanicallyConverged"],
        true
    );
    assert_eq!(
        readback["structuredContent"]["job"]["semanticCompletionEvaluated"], false,
        "native cancellation must not claim domain Tool success"
    );
    assert_eq!(
        readback["structuredContent"]["artifacts"]["byKind"]["admission_cancel_evidence"],
        1
    );
    let artifact_id: String = fixture
        .db
        .query_one(
            "SELECT a.artifact_id FROM artifacts a JOIN attempts t ON t.attempt_id=a.attempt_id
         WHERE t.job_id=$1 AND a.kind='admission_cancel_evidence'",
            &[&job],
        )
        .unwrap()
        .get(0);
    let (artifact_status, artifact_readback) = r16_dedicated_call(
        &dedicated_endpoint,
        &"h".repeat(48),
        "artifact.read",
        json!({"jobId":job,"artifactId":artifact_id,"offset":0,"maxBytes":4096}),
    );
    assert_eq!(artifact_status, 200);
    assert_ne!(
        artifact_readback["isError"], true,
        "dedicated readback must deliver original cancellation evidence: {artifact_readback}"
    );
    let content = artifact_readback["structuredContent"]["content"]
        .as_str()
        .unwrap();
    let evidence: Value = serde_json::from_str(content).unwrap();
    assert_eq!(evidence["jobId"], job);
    assert_eq!(evidence["dispatchIssued"], false);
    assert_eq!(evidence["terminalState"], "cancelled");

    // Normal consumer can still execute after the dedicated source denial.
    let ordinary = call(
        &endpoint,
        "workspace.exec",
        json!({
            "clientRequestId":format!("r16-followup-{}",Uuid::now_v7().simple()),
            "execution":{"workspaceId":workspace_id,"executable":"/usr/bin/printf",
                "args":["ordinary-still-works"],"cwdRelative":".","timeoutMs":15000},
            "waitMs":0
        }),
    );
    assert_ne!(
        ordinary["isError"], true,
        "unrelated Job poisoned: {ordinary}"
    );
    let follow_id = ordinary["structuredContent"]["jobId"]
        .as_str()
        .unwrap()
        .to_owned();
    let deadline = Instant::now() + Duration::from_secs(30);
    loop {
        let observed = call(
            &endpoint,
            "job.observe",
            json!({
                "jobId":follow_id,"waitMs":2000
            }),
        );
        assert_ne!(
            observed["isError"], true,
            "unrelated observe failed: {observed}"
        );
        if observed["structuredContent"]["executionTerminal"] == true {
            assert_eq!(
                observed["structuredContent"]["executionDisposition"], "succeeded",
                "unrelated Job must succeed: {observed}"
            );
            break;
        }
        assert!(
            Instant::now() < deadline,
            "unrelated job stalled: {observed}"
        );
    }
    eprintln!("R16_NATIVE_MCP_SCHEDULER_ISSUER_DENIED_CANCEL_RELEASED_PASS");
}

/// One test-only carrier for the original Harness issuer consumer.
fn original_harness_fixture_command() -> Command {
    let repo_root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../../../");
    let script = repo_root.join("services/harness/tests/original_pg_issuer_native_fixture.py");
    let python = std::env::var("HARNESS_PG_PYTHON").unwrap_or_else(|_| "python3".into());
    let pythonpath = format!(
        "{}:{}",
        repo_root.join("services/harness/src").display(),
        repo_root.join("services/harness").display()
    );
    let mut command = Command::new(python);
    command.arg(script).env("PYTHONPATH", pythonpath);
    command
}

/// Opt-in true Publisher→restricted PG source→authenticated MCP admission→
/// source revocation→single native Scheduler→dedicated client readback.
/// Capacity is held by a **real**, harmless test-owned native Job to produce a
/// deterministic queued interval; no global Scheduler flag or second Registry.
#[test]
#[ignore = "requires disposable PG18, original Harness Python deps and native systemd runner"]
fn pg18_original_harness_issued_dedicated_mcp_admit_then_revoke_before_dispatch() {
    let mut fixture = Fixture::new();
    fixture.host_visible_test_runner = true;
    fixture.harness_dispatch_test = true;
    let repo = fixture.repo();
    let id = Uuid::now_v7().simple().to_string();
    let issuer_schema = format!("r17_hpg_{}", &id[..19]);
    fixture.harness_schema_override = Some(issuer_schema.clone());
    let run_id = format!("harness-run:r17-native-{}", &id[..19]);
    let workspace_id = format!("r17-own-{}", &id[..19]);
    let fixture_dsn = format!(
        "host={} user=postgres dbname=postgres",
        fixture.root.display()
    );
    let original = |action: &str| -> Value {
        let out = original_harness_fixture_command()
            .arg(action)
            .arg("--dsn")
            .arg(&fixture_dsn)
            .arg("--schema")
            .arg(&issuer_schema)
            .arg("--run")
            .arg(&run_id)
            .arg("--workspace")
            .arg(&workspace_id)
            .output()
            .unwrap();
        assert!(
            out.status.success(),
            "real Harness {action} failed: {}",
            String::from_utf8_lossy(&out.stderr)
        );
        serde_json::from_slice(&out.stdout).unwrap()
    };
    let source = original("issue");
    assert_eq!(source["runId"], run_id);
    assert_eq!(source["fenceGeneration"], 2);
    fixture.db.batch_execute(&format!(
        "GRANT USAGE ON SCHEMA \"{issuer_schema}\" TO runtime_app;
         GRANT EXECUTE ON FUNCTION \"{issuer_schema}\".harness_current_dispatch_cut(text,bigint,text)
            TO runtime_app;"
    )).unwrap();
    let original_private_allowed: bool = fixture
        .db
        .query_one(
            "SELECT has_table_privilege('runtime_app',$1,'SELECT')",
            &[&format!("{issuer_schema}.runs")],
        )
        .unwrap()
        .get(0);
    assert!(
        !original_private_allowed,
        "operator Source Run table must never be readable by Runtime app"
    );

    let endpoint = fixture.endpoint();
    let opened = call(
        &endpoint,
        "workspace.open",
        json!({
            "workspaceId":workspace_id,"sourceRepo":repo,"sourceRevision":"HEAD"
        }),
    );
    assert_ne!(
        opened["isError"], true,
        "real disposable native Git workspace: {opened}"
    );
    let described = call(&endpoint, "runtime.describe", json!({}));
    let cpu = described["structuredContent"]["scheduling"]["node"]["cpuMillis"]
        .as_u64()
        .unwrap();
    assert!(cpu > 100, "test machine must have finite CPU headroom");

    // Mature real PG fair-share test pattern: one full-CPU physical Job
    // holds capacity, forcing the genuinely admitted Harness Job to remain
    // accepted until the original PG source has been independently revoked.
    let release = fixture.root.join("r17-release-cpu");
    // An assertion failure must not leave the test-owned native blocker
    // running after its fixture database disappears.
    struct ReleaseOwnBlockerOnDrop(PathBuf);
    impl Drop for ReleaseOwnBlockerOnDrop {
        fn drop(&mut self) {
            let _ = fs::write(&self.0, b"allow own blocker exit");
            thread::sleep(Duration::from_millis(300));
        }
    }
    let _release_on_drop = ReleaseOwnBlockerOnDrop(release.clone());
    let blocker_script = format!("while [ ! -f '{}' ]; do sleep 0.1; done", release.display());
    let blocker = call(
        &endpoint,
        "workspace.exec",
        json!({
            "clientRequestId":format!("r17-blocker-{id}"),
            "execution":{
                "workspaceId":workspace_id,
                "executable":"/usr/bin/sh","args":["-c",blocker_script],
                "cwdRelative":".","timeoutMs":60000,
                "budget":{"scheduling":{
                    "owner":"r17-original-issuer-test",
                    "resources":{"cpuMillis":cpu,"memoryBytes":16777216,"pids":8},
                    "workspaceAccess":{"readOnly":true}
                }}
            },
            "waitMs":0
        }),
    );
    assert_ne!(
        blocker["isError"], true,
        "original benign blocker rejected: {blocker}"
    );
    let blocker_id = blocker["structuredContent"]["jobId"]
        .as_str()
        .unwrap()
        .to_owned();
    let deadline = Instant::now() + Duration::from_secs(12);
    loop {
        let allocated: i64 = fixture
            .db
            .query_one(
                "SELECT count(*) FROM job_allocations x
             JOIN attempts a ON a.attempt_id=x.attempt_id
             WHERE a.job_id=$1 AND x.state='active'",
                &[&blocker_id],
            )
            .unwrap()
            .get(0);
        if allocated == 1 {
            break;
        }
        assert!(
            Instant::now() < deadline,
            "benign full-CPU native Job not allocated: {blocker}"
        );
        thread::sleep(Duration::from_millis(40));
    }

    // Native operator-managed dedicated Bearer, not caller-added foreignRefs
    // or an unqualified open service port.
    let dedicated = endpoint.replacen("/mcp", "/harness/mcp", 1);
    let original_request = source["loweredRequest"].clone();
    let (bad_status, _) = r16_dedicated_call(
        &dedicated,
        &"p".repeat(32),
        "workspace.exec",
        original_request.clone(),
    );
    assert_eq!(
        bad_status, 401,
        "ordinary Runtime bearer cannot impersonate Harness"
    );
    let (status, admitted) = r16_dedicated_call(
        &dedicated,
        &"h".repeat(48),
        "workspace.exec",
        original_request.clone(),
    );
    assert_eq!(
        status, 200,
        "qualified dedicated MCP must accept the request: {admitted}"
    );
    assert_ne!(
        admitted["isError"], true,
        "real original Harness frozen PhysicalRequest rejected: {admitted}"
    );
    let job = admitted["structuredContent"]["jobId"]
        .as_str()
        .expect("real dedicated Harness PG admitted same Job")
        .to_owned();
    let before = fixture
        .db
        .query_one(
            "SELECT a.state,j.principal FROM attempts a JOIN jobs j ON j.job_id=a.job_id
         WHERE j.job_id=$1",
            &[&job],
        )
        .unwrap();
    assert_eq!(
        before.get::<_, String>(0),
        "accepted",
        "full CPU fixture must prove source revoked BEFORE PG dispatch"
    );
    assert_eq!(before.get::<_, String>(1), "harness-dispatch-r16");
    let dispatch_before: i64 = fixture
        .db
        .query_one(
            "SELECT count(*) FROM job_events WHERE job_id=$1 AND event_type='DISPATCH_ISSUED'",
            &[&job],
        )
        .unwrap()
        .get(0);
    assert_eq!(
        dispatch_before, 0,
        "source must be revoked before any dispatch"
    );

    // Produce a second genuine Run/Fence in the original same PG issuer,
    // intentionally colliding its test-only client key with the first.
    // The usual Harness lowering derives keys from the Run binding; this
    // exercises the Runtime invariant even under an explicit collision.
    let second_run = format!("harness-run:r17-native-other-{}", &id[..19]);
    let original_key = source["clientRequestId"].as_str().unwrap();
    let other = original_harness_fixture_command()
        .arg("issue")
        .arg("--dsn")
        .arg(&fixture_dsn)
        .arg("--schema")
        .arg(&issuer_schema)
        .arg("--run")
        .arg(&second_run)
        .arg("--workspace")
        .arg(&workspace_id)
        .arg("--client-request-id")
        .arg(original_key)
        .output()
        .unwrap();
    assert!(
        other.status.success(),
        "original second Harness publisher: {}",
        String::from_utf8_lossy(&other.stderr)
    );
    let other: Value = serde_json::from_slice(&other.stdout).unwrap();
    assert_eq!(other["runId"], second_run);
    assert_eq!(other["clientRequestId"], original_key);
    assert_ne!(other["fenceDigest"], source["fenceDigest"]);
    let (collision_status, collision) = r16_dedicated_call(
        &dedicated,
        &"h".repeat(48),
        "workspace.exec",
        other["loweredRequest"].clone(),
    );
    assert_eq!(collision_status, 200, "{collision}");
    assert_eq!(collision["isError"], true, "{collision}");
    assert_eq!(
        collision["structuredContent"]["error"]["code"], "IDEMPOTENCY_CONFLICT",
        "{collision}"
    );
    let key_jobs: i64 = fixture
        .db
        .query_one(
            "SELECT count(*) FROM jobs WHERE principal=$1 AND client_request_id=$2",
            &[&"harness-dispatch-r16", &original_key],
        )
        .unwrap()
        .get(0);
    assert_eq!(key_jobs, 1);
    let original_job_key: String = fixture
        .db
        .query_one(
            "SELECT job_id FROM idempotency_keys WHERE principal=$1 AND client_request_id=$2",
            &[&"harness-dispatch-r16", &original_key],
        )
        .unwrap()
        .get(0);
    assert_eq!(original_job_key, job);

    let revoked = original("revoke");
    assert_eq!(revoked["sourceStanding"], "unknown");
    assert_eq!(revoked["finalization"]["sourceStanding"], "blocked");
    assert_eq!(revoked["revision"], 3);
    fs::write(&release, b"allow harmless own blocker exit").unwrap();
    let deadline = Instant::now() + Duration::from_secs(25);
    loop {
        let state = fixture
            .db
            .query_one("SELECT resolution FROM jobs WHERE job_id=$1", &[&job])
            .unwrap()
            .get::<_, Option<String>>(0);
        if state.as_deref() == Some("cancelled") {
            break;
        }
        assert!(
            Instant::now() < deadline,
            "real source-revoked accepted Harness Job was not cancelled: {state:?}"
        );
        thread::sleep(Duration::from_millis(100));
    }
    let issued: i64 = fixture
        .db
        .query_one(
            "SELECT count(*) FROM job_events
         WHERE job_id=$1 AND event_type='DISPATCH_ISSUED'",
            &[&job],
        )
        .unwrap()
        .get(0);
    assert_eq!(issued, 0);
    let reason: i64 = fixture
        .db
        .query_one(
            "SELECT count(*) FROM job_events
         WHERE job_id=$1 AND event_type='SCHEDULER_ISSUE'
         AND reason_code='HARNESS_ISSUER_NOT_CURRENT_AT_DISPATCH'",
            &[&job],
        )
        .unwrap()
        .get(0);
    assert_eq!(reason, 1);
    let reservation: String = fixture
        .db
        .query_one(
            "SELECT r.state FROM concurrency_reservations r
         JOIN attempts a ON a.attempt_id=r.attempt_id WHERE a.job_id=$1",
            &[&job],
        )
        .unwrap()
        .get(0);
    assert_eq!(reservation, "released");
    let (read_status, readback) =
        r16_dedicated_call(&dedicated, &"h".repeat(48), "job.get", json!({"jobId":job}));
    assert_eq!(read_status, 200);
    assert_eq!(
        readback["structuredContent"]["job"]["resolution"],
        "cancelled"
    );
    assert_eq!(
        readback["structuredContent"]["job"]["semanticCompletionEvaluated"],
        false
    );
    assert_eq!(readback["structuredContent"]["episodes"]["dispatches"], 0);
    // The exact original request still recovers its existing cancelled
    // Job after the source revocation; it must not create another effect.
    let (replay_status, replay) = r16_dedicated_call(
        &dedicated,
        &"h".repeat(48),
        "workspace.exec",
        original_request,
    );
    assert_eq!(replay_status, 200, "{replay}");
    assert_ne!(replay["isError"], true, "{replay}");
    assert_eq!(replay["structuredContent"]["jobId"], job);
    assert_eq!(
        replay["structuredContent"]["status"], "cancelled",
        "{replay}"
    );
    let final_dispatches: i64 = fixture
        .db
        .query_one(
            "SELECT count(*) FROM job_events WHERE job_id=$1 AND event_type='DISPATCH_ISSUED'",
            &[&job],
        )
        .unwrap()
        .get(0);
    assert_eq!(final_dispatches, 0);
    let final_key_count: i64 = fixture
        .db
        .query_one(
            "SELECT count(*) FROM jobs WHERE principal=$1 AND client_request_id=$2",
            &[&"harness-dispatch-r16", &original_key],
        )
        .unwrap()
        .get(0);
    let final_attempt_count: i64 = fixture
        .db
        .query_one("SELECT count(*) FROM attempts WHERE job_id=$1", &[&job])
        .unwrap()
        .get(0);
    assert_eq!(final_key_count, 1);
    assert_eq!(final_attempt_count, 1);
    eprintln!("R17_CROSS_RUN_COLLISION_REJECTED_EXACT_REPLAY_SAME_CANCELLED_JOB");

    // Keep the only physical native blocker fully terminal before Fixture
    // Drop; never leave an orphaned test-owned systemd Unit or cgroup.
    let deadline = Instant::now() + Duration::from_secs(20);
    loop {
        let row = fixture
            .db
            .query_one(
                "SELECT resolution FROM jobs WHERE job_id=$1",
                &[&blocker_id],
            )
            .unwrap();
        let resolution: Option<String> = row.get(0);
        if resolution.as_deref() == Some("succeeded") {
            break;
        }
        assert!(
            Instant::now() < deadline,
            "test-only native blocker not terminal: {resolution:?}"
        );
        thread::sleep(Duration::from_millis(100));
    }
    eprintln!("R17_GENUINE_ORIGINAL_HARNESS_DEDICATED_MCP_PG_NATIVE_REVOKE_PASS");
}

/// Join original source-issued keys with real dedicated Runtime identities.
/// A terminal source cut closes admission; it is not a whole-Run native
/// settlement or independently accepted Domain-output certificate.
#[test]
#[ignore = "requires disposable PG18, original Harness Python deps and native systemd runner"]
fn pg18_original_harness_terminal_cut_joins_observed_and_unsubmitted_keys() {
    let mut fixture = Fixture::new();
    fixture.host_visible_test_runner = true;
    fixture.harness_dispatch_test = true;
    let repo = fixture.repo();
    let id = Uuid::now_v7().simple().to_string();
    let schema = format!("r6_join_{}", &id[..19]);
    fixture.harness_schema_override = Some(schema.clone());
    let run = format!("harness-run:r6-join-{}", &id[..19]);
    let ws = format!("r6-join-{}", &id[..19]);
    let dsn = format!(
        "host={} user=postgres dbname=postgres",
        fixture.root.display()
    );
    let observation_file = fixture.root.join("r6-original-observation.json");
    let source_call = |action: &str| -> Value {
        let out = original_harness_fixture_command()
            .arg(action)
            .arg("--dsn")
            .arg(&dsn)
            .arg("--schema")
            .arg(&schema)
            .arg("--run")
            .arg(&run)
            .arg("--workspace")
            .arg(&ws)
            .arg("--observation-file")
            .arg(&observation_file)
            .output()
            .unwrap();
        assert!(
            out.status.success(),
            "Harness {action}: {}",
            String::from_utf8_lossy(&out.stderr)
        );
        serde_json::from_slice(&out.stdout).unwrap()
    };
    let first = source_call("issue");
    fixture.db.batch_execute(&format!(
        "GRANT USAGE ON SCHEMA \"{schema}\" TO runtime_app;
         GRANT EXECUTE ON FUNCTION \"{schema}\".harness_current_dispatch_cut(text,bigint,text) TO runtime_app;"
    )).unwrap();
    let endpoint = fixture.endpoint();
    let opened = call(
        &endpoint,
        "workspace.open",
        json!({"workspaceId":ws,"sourceRepo":repo,"sourceRevision":"HEAD"}),
    );
    assert_ne!(opened["isError"], true, "{opened}");
    let dedicated = endpoint.replacen("/mcp", "/harness/mcp", 1);
    let bearer = "h".repeat(48);
    let invoke = |name: &str, args: Value| -> Value {
        let (status, result) = r16_dedicated_call(&dedicated, &bearer, name, args);
        assert_eq!(status, 200, "{name}: {result}");
        result
    };
    let first_request = first["loweredRequest"].clone();
    let admitted = invoke("workspace.exec", first_request.clone());
    assert_ne!(admitted["isError"], true, "{admitted}");
    let job = admitted["structuredContent"]["jobId"]
        .as_str()
        .unwrap()
        .to_owned();
    let deadline = Instant::now() + Duration::from_secs(30);
    let observed = loop {
        let r = invoke("job.observe", json!({"jobId":job,"waitMs":1000}));
        assert_ne!(r["isError"], true, "{r}");
        let c = &r["structuredContent"];
        if c["executionDisposition"] == "succeeded" {
            assert_eq!(c["resultAvailable"], true, "{r}");
            break c.clone();
        }
        assert!(
            Instant::now() < deadline,
            "original native Job not succeeded: {r}"
        );
    };
    fs::write(&observation_file, serde_json::to_vec(&observed).unwrap()).unwrap();
    let recorded = source_call("record-observed");
    assert_eq!(recorded["source"]["originalRunIssuedCount"], 1);
    let next = source_call("issue-next");
    let first_key = first["clientRequestId"].as_str().unwrap();
    let next_key = next["clientRequestId"].as_str().unwrap();
    assert_ne!(first_key, next_key);
    let pre = source_call("inspect-issued");
    assert_eq!(pre["terminal"], false);
    assert_eq!(pre["source"]["originalRunIssuedCount"], 2);
    let sealed = source_call("seal-unsubmitted");
    assert_eq!(sealed["terminal"], true);
    assert_eq!(sealed["source"]["originalRunIssuedCount"], 2);
    assert_eq!(sealed["source"]["safeToAcknowledgeNoFutureSpawn"], false);
    assert_eq!(sealed["source"]["runtimeOwnerProofStanding"], "unknown");
    let entries = sealed["source"]["issuedIntents"].as_array().unwrap();
    let original = entries
        .iter()
        .find(|r| r["clientRequestId"] == first_key)
        .unwrap();
    let never = entries
        .iter()
        .find(|r| r["clientRequestId"] == next_key)
        .unwrap();
    assert_eq!(original["lastRecordedStatus"], "observed");
    assert_eq!(original["sourceOwnerJobRef"], job);
    assert_eq!(never["lastRecordedStatus"], "rejected");
    assert!(never["sourceOwnerJobRef"].is_null());
    assert_eq!(original["dispatchFenceDigest"], first["fenceDigest"]);
    assert_eq!(never["dispatchFenceDigest"], next["fenceDigest"]);
    let exact_jobs = |key: &str| -> Vec<Value> {
        let r = invoke("job.list", json!({"clientRequestId":key,"limit":2}));
        assert_ne!(r["isError"], true, "{r}");
        r["structuredContent"]["jobs"].as_array().unwrap().clone()
    };
    let matching = exact_jobs(first_key);
    assert_eq!(matching.len(), 1);
    assert_eq!(matching[0]["jobId"], job);
    assert!(exact_jobs(next_key).is_empty());
    // Attempt inventory and durable dispatch count come from the disposable
    // Runtime's own authoritative PG, not inferred from latest job.get.
    let count: i64 = fixture
        .db
        .query_one("SELECT count(*) FROM attempts WHERE job_id=$1", &[&job])
        .unwrap()
        .get(0);
    let dispatches: i64 = fixture
        .db
        .query_one(
            "SELECT count(*) FROM job_events WHERE job_id=$1 AND event_type='DISPATCH_ISSUED'",
            &[&job],
        )
        .unwrap()
        .get(0);
    assert_eq!((count, dispatches), (1, 1));
    // A genuine never-submitted source key cannot admit a Job after the
    // original terminal source cut, despite previously valid Fence bytes.
    let denied = invoke("workspace.exec", next["loweredRequest"].clone());
    assert_eq!(denied["isError"], true, "{denied}");
    assert!(exact_jobs(next_key).is_empty());
    let replay = invoke("workspace.exec", first_request);
    assert_ne!(replay["isError"], true, "{replay}");
    assert_eq!(replay["structuredContent"]["jobId"], job);
    assert_eq!(exact_jobs(first_key).len(), 1);
    let after_count: i64 = fixture
        .db
        .query_one("SELECT count(*) FROM attempts WHERE job_id=$1", &[&job])
        .unwrap()
        .get(0);
    let after_dispatches: i64 = fixture
        .db
        .query_one(
            "SELECT count(*) FROM job_events WHERE job_id=$1 AND event_type='DISPATCH_ISSUED'",
            &[&job],
        )
        .unwrap()
        .get(0);
    assert_eq!((after_count, after_dispatches), (1, 1));
    assert_eq!(source_call("inspect-issued"), sealed);
    eprintln!("R6_ORIGINAL_TERMINAL_ISSUED_JOIN_PASS keys=2 jobs=1 attempts=1 dispatches=1 absent=1 exact_replay=1");
}

#[test]
#[ignore = "requires disposable PostgreSQL18 and isolated native Runtime MCP"]
fn pg18_mcp_claim_release_route_holds_original_legacy_claim_across_finalizer_cut() {
    // Real PG18 + two authenticated MCP routes, not a simulated Server::call.
    // This establishes only the ROUTE boundary. The external Domain ACK
    // and trusted Finalizer policy remain separate unqualified obligations.
    let mut fixture = Fixture::new();
    let original_workspace = format!("r28-ordinary-original-{}", Uuid::now_v7().simple());
    let repo = fixture.repo();
    let ordinary_url = fixture.endpoint();
    let opened = call(
        &ordinary_url,
        "workspace.open",
        json!({"workspaceId":original_workspace,"sourceRepo":repo,"sourceRevision":"HEAD"}),
    );
    assert_ne!(opened["isError"], true, "{opened}");
    let original_state = call(
        &ordinary_url,
        "workspace.get",
        json!({"schemaVersion":1,"workspaceId":original_workspace}),
    );
    assert_ne!(original_state["isError"], true, "{original_state}");
    let original_digest = original_state["structuredContent"]["sourceStateDigest"]
        .as_str()
        .unwrap()
        .to_owned();
    let original_key = format!("r28-legacy-claim-{}", Uuid::now_v7().simple());
    let born = call(
        &ordinary_url,
        "workspace.claim.reserve",
        json!({
            "schemaVersion":1,
            "clientRequestId":original_key,
            "workspaceId":original_workspace,
            "runRef":format!("harness-run:r28-legacy-{}",Uuid::now_v7().simple()),
            "expectedSourceStateDigest":original_digest,
        }),
    );
    assert_ne!(born["isError"], true, "{born}");
    assert_eq!(born["structuredContent"]["state"], "held");

    let mut endpoint_process = fixture.endpoint.take().unwrap();
    endpoint_process.kill().unwrap();
    endpoint_process.wait().unwrap();
    // Reuse the existing issuer-shim fixture from R16, without giving
    // runtime_app SELECT/UPDATE on any private Harness Run rows.
    fixture
        .db
        .batch_execute(
            "CREATE SCHEMA r16_issuer;
         CREATE FUNCTION r16_issuer.harness_current_dispatch_cut(text,bigint,text)
         RETURNS TABLE(event_kind text,payload_digest text,payload_kind text,
             payload_len bigint,payload_content bytea,fence_kind text,
             fence_len bigint,fence_content bytea,intent_digest text,
             intent_kind text,intent_len bigint,intent_content bytea)
         LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog
         AS $issuer$ BEGIN RETURN; END $issuer$;
         REVOKE ALL ON FUNCTION
           r16_issuer.harness_current_dispatch_cut(text,bigint,text) FROM PUBLIC;
         GRANT USAGE ON SCHEMA r16_issuer TO runtime_app;
         GRANT EXECUTE ON FUNCTION
           r16_issuer.harness_current_dispatch_cut(text,bigint,text) TO runtime_app;",
        )
        .unwrap();
    fixture.harness_dispatch_test = true;
    let ordinary_url = fixture.endpoint();
    let dedicated_url = ordinary_url.replacen("/mcp", "/harness/mcp", 1);

    // The old principal remains the authoritative owner of its original
    // HELD Claim; enabling a finalizer profile must not silently rebind it.
    let preserved = call(
        &ordinary_url,
        "workspace.claim.get",
        json!({"schemaVersion":1,"clientRequestId":original_key}),
    );
    assert_ne!(preserved["isError"], true, "{preserved}");
    assert_eq!(preserved["structuredContent"]["state"], "held");

    // A direct, handcrafted JSON-RPC tools/call must be denied BEFORE PG,
    // even when the caller knows the exact old original Claim request key.
    let (status, denied) = r16_raw_mcp_envelope(
        &ordinary_url,
        &"p".repeat(32),
        "workspace.claim.release",
        json!({"schemaVersion":1,"clientRequestId":original_key}),
    );
    assert_eq!(status, 200, "{denied}");
    assert_eq!(
        denied["error"]["code"], -32602,
        "raw normal release must fail explicitly before PG, not yield ambiguous null: {denied}"
    );
    assert!(
        denied["error"]["message"]
            .as_str()
            .is_some_and(|message| message.contains("independently received")),
        "the native handler must explain its route-bound denial: {denied}"
    );
    let still_held = call(
        &ordinary_url,
        "workspace.claim.get",
        json!({"schemaVersion":1,"clientRequestId":original_key}),
    );
    assert_eq!(still_held["structuredContent"]["state"], "held");
    let original_close = call(
        &ordinary_url,
        "workspace.close",
        json!({"schemaVersion":1,"workspaceId":original_workspace,
               "force":false,"consumerReleased":true,
               "expectedSourceStateDigest":original_digest}),
    );
    assert_eq!(original_close["isError"], true, "{original_close}");
    assert_eq!(
        original_close["structuredContent"]["error"]["code"], "CONCURRENCY_LIMIT",
        "{original_close}"
    );

    // The new privileged identity is not an alias for the old holder's key.
    let (wrong_route, _) = r16_dedicated_call(
        &dedicated_url,
        &"p".repeat(32),
        "workspace.claim.get",
        json!({"schemaVersion":1,"clientRequestId":original_key}),
    );
    assert_eq!(wrong_route, 401);
    let (right_route, wrong_holder) = r16_dedicated_call(
        &dedicated_url,
        &"h".repeat(48),
        "workspace.claim.get",
        json!({"schemaVersion":1,"clientRequestId":original_key}),
    );
    assert_eq!(right_route, 200);
    assert_eq!(wrong_holder["isError"], true, "{wrong_holder}");

    // Creating a DIFFERENT dedicated-principal original Claim is allowed,
    // but does not certify any future early release as Domain-approved.
    let protected_workspace = format!("r28-dedicated-{}", Uuid::now_v7().simple());
    let second = call(
        &ordinary_url,
        "workspace.open",
        json!({"schemaVersion":1,"workspaceId":protected_workspace,
               "sourceRepo":repo,"sourceRevision":"HEAD"}),
    );
    assert_ne!(second["isError"], true, "{second}");
    let second_state = call(
        &ordinary_url,
        "workspace.get",
        json!({"schemaVersion":1,"workspaceId":protected_workspace}),
    );
    let second_digest = second_state["structuredContent"]["sourceStateDigest"]
        .as_str()
        .unwrap();
    let dedicated_key = format!("r28-dedicated-key-{}", Uuid::now_v7().simple());
    let (dedicated_status, held) = r16_dedicated_call(
        &dedicated_url,
        &"h".repeat(48),
        "workspace.claim.reserve",
        json!({
            "schemaVersion":1,"clientRequestId":dedicated_key,
            "workspaceId":protected_workspace,
            "runRef":format!("harness-run:r28-dedicated-{}", Uuid::now_v7().simple()),
            "expectedSourceStateDigest":second_digest,
        }),
    );
    assert_eq!(dedicated_status, 200);
    assert_ne!(held["isError"], true, "{held}");
    assert_eq!(held["structuredContent"]["state"], "held");
    let (dedicated_read_status, held_after) = r16_dedicated_call(
        &dedicated_url,
        &"h".repeat(48),
        "workspace.claim.get",
        json!({"schemaVersion":1,"clientRequestId":dedicated_key}),
    );
    assert_eq!(dedicated_read_status, 200);
    assert_eq!(held_after["structuredContent"]["state"], "held");

    // A fresh dedicated-principal HELD Claim must also resist the exact same
    // bearer + key before ANY original independent recipient or OS drain.
    let (same_http, protected) = r16_raw_mcp_envelope(
        &dedicated_url,
        &"h".repeat(48),
        "workspace.claim.release",
        json!({"schemaVersion":1,"clientRequestId":dedicated_key}),
    );
    assert_eq!(same_http, 200, "{protected}");
    assert_eq!(protected["error"]["code"], -32602, "{protected}");
    let (held_http, still_held) = r16_dedicated_call(
        &dedicated_url,
        &"h".repeat(48),
        "workspace.claim.get",
        json!({"schemaVersion":1,"clientRequestId":dedicated_key}),
    );
    assert_eq!(held_http, 200);
    assert_eq!(still_held["structuredContent"]["state"], "held");

    eprintln!(
        "R28_NATIVE_PG18_MCP_RAW_RELEASE_ROUTE_DENIED_OLD_CLAIM_PRESERVED_NEW_DEDICATED_HELD_PASS"
    );
}

/// Real PG18, authenticated MCP and actual systemd Runner. This opt-in
/// original consumer test proves offline Git + output receipt work under
/// contained_local while control-plane paths stay inaccessible.
#[test]
#[ignore = "requires disposable PostgreSQL18 and real systemd transient units"]
fn fresh_pg_native_contained_profile_git_and_control_plane_boundary() {
    let mut fixture = Fixture::new();
    fixture.host_visible_test_runner = true;
    // Exercise the actual ordinary-Agent contained-only route while the
    // independent operator config binds its task to nonroot UID/GID.
    // Neither a trusted_local escape nor a root-contained task may green.
    fixture.ordinary_contained_only = true;
    fixture.contained_nonroot_test = true;
    let repo = fixture.repo();
    let endpoint = fixture.endpoint();
    // A normal Agent must discover exactly the profiles the same native PG
    // Job/Attempt and systemd Runner actually admit. Source-only discovery
    // is never mistaken for the installed node's advertisement.
    let described = call(&endpoint, "runtime.describe", json!({}));
    assert_ne!(
        described["isError"], true,
        "native Runtime describe: {described}"
    );
    let targets = described["structuredContent"]["targets"]
        .as_array()
        .expect("PG MCP runtime.describe.targets");
    let linux = targets
        .iter()
        .find(|target| target["target"] == "local_linux")
        .expect("original local_linux execution provider");
    let profiles = linux["executionProfiles"]
        .as_array()
        .expect("original Linux executionProfiles");
    assert_eq!(
        profiles,
        &vec![json!("contained_local")],
        "ordinary ingress must not offer a privileged Git commit escape: {described}"
    );
    let opened = call(
        &endpoint,
        "workspace.open",
        json!({"workspaceId":"ws-contained-git","sourceRepo":repo,"sourceRevision":"HEAD"}),
    );
    assert_ne!(opened["isError"], true, "native Workspace OPEN: {opened}");
    // A second Workspace is the exact scope a different Agent could hold
    // under the same operator-owned test UID/GID. It must not become visible
    // through the first task's native contained mount, even by absolute path.
    let foreign = call(
        &endpoint,
        "workspace.open",
        json!({"workspaceId":"ws-contained-foreign","sourceRepo":repo,"sourceRevision":"HEAD"}),
    );
    assert_ne!(
        foreign["isError"], true,
        "foreign native Workspace: {foreign}"
    );
    let foreign_probe = fixture
        .root
        .join("store/workspaces/ws-contained-foreign/foreign-probe.txt");
    fs::write(&foreign_probe, b"foreign scope must not be read").unwrap();
    // A caller's HOME/TMPDIR/CARGO_TARGET_DIR is untrusted DATA. The
    // ContainedLocal systemd launcher bind-mounts those paths: fail before
    // native Job admission rather than granting arbitrary host mount access.
    for (attempt, execution) in [
        (
            "path",
            json!({"workspaceId":"ws-contained-git",
            "executable":"/usr/bin/true","cwdRelative":".",
            "executionProfile":"contained_local",
            "env":{"HOME":"/etc/ordivon"}}),
        ),
        (
            "step",
            json!({"workspaceId":"ws-contained-git",
            "executable":"/usr/bin/true","cwdRelative":".",
            "executionProfile":"contained_local",
            "steps":[{"id":"unsafe-home","executable":"/usr/bin/true",
                       "cwdRelative":".","env":{"HOME":"/etc/ordivon"}}]}),
        ),
    ] {
        let denied = call(
            &endpoint,
            "workspace.exec",
            json!({"clientRequestId":format!("pg-contained-env-negative-{attempt}"),
                   "execution":execution,"waitMs":200}),
        );
        assert_eq!(
            denied["isError"], true,
            "Agent supplied host mount escaped: {denied}"
        );
        assert_eq!(
            denied["structuredContent"]["error"]["code"], "INVALID_REQUEST",
            "{denied}"
        );
        let count: i64 = fixture
            .db
            .query_one("SELECT count(*) FROM jobs", &[])
            .unwrap()
            .get(0);
        assert_eq!(count, 0, "invalid mount must not admit PG Job");
    }
    // A previous contained task may have replaced its writable HOME cache
    // with a symlink to an unrelated host directory. Syntactic prefix
    // comparison is not mount authority; the resolved original must stay
    // within the Runtime-owned cache root.
    let cache = fixture.root.join("store/cache/workspaces/ws-contained-git");
    fs::create_dir_all(&cache).unwrap();
    let foreign = fixture.root.join("synthetic-host-root-owned");
    fs::create_dir_all(&foreign).unwrap();
    std::os::unix::fs::symlink(&foreign, cache.join("home")).unwrap();
    let poisoned = call(
        &endpoint,
        "workspace.exec",
        json!({"clientRequestId":"pg-contained-symlink-mount-negative",
            "execution":{"workspaceId":"ws-contained-git","executable":"/usr/bin/true",
                 "cwdRelative":".","executionProfile":"contained_local","timeoutMs":10000},
            "waitMs":0}),
    );
    assert_eq!(
        poisoned["isError"], true,
        "foreign symlink accepted as native bind: {poisoned}"
    );
    assert_eq!(
        poisoned["structuredContent"]["error"]["code"], "INVALID_REQUEST",
        "{poisoned}"
    );
    let count: i64 = fixture
        .db
        .query_one("SELECT count(*) FROM jobs", &[])
        .unwrap()
        .get(0);
    assert_eq!(
        count, 0,
        "symlink escape must be rejected before PG job birth"
    );
    fs::remove_file(cache.join("home")).unwrap();

    let command = r#"set -eu
if test -e /etc/ordivon && test -r /etc/ordivon; then echo 'CONTAINED_CONTROL_DIRECTORY_VISIBLE'; exit 53; fi
if test -r /etc/ordivon/runtime-mcp.token; then echo 'CONTAINED_SECRET_VISIBLE'; exit 54; fi
# Only ask the kernel whether the root-owned host credential is readable.
# Do NOT open or print any secret contents. A pass means the process is NOT
# isolated from host-root-owned credentials outside the configured denylist.
if test -r /etc/shadow; then echo 'CONTAINED_HOST_ROOT_READABLE'; exit 57; fi
if test "$(id -u)" != 65534; then echo 'CONTAINED_TASK_NOT_NONROOT'; exit 58; fi
# The real systemd mount table exposes this task's *own* original PG Attempt
# bundle, even if the containing host source path is hidden by /var tmpfs.
# The trusted UID0 Runner writes request/result and cancel marker here; the
# nonroot Agent child must not read that request or create/replace a marker.
# Do not inspect or mutate any other Attempt, secret, or control file.
bundle="$(awk '$5 ~ /\/pg-attempts\/attempt-/ { print $5 }' /proc/self/mountinfo)"
if test -z "$bundle" || test "$(printf '%s\n' "$bundle" | wc -l)" -ne 1; then
    echo 'CONTAINED_OWN_ATTEMPT_BUNDLE_NOT_UNIQUE'; exit 63
fi
if test -r "$bundle/request.json"; then
    echo 'CONTAINED_OWN_ATTEMPT_REQUEST_READABLE'; exit 64
fi
if test -w "$bundle"; then
    echo 'CONTAINED_OWN_ATTEMPT_BUNDLE_WRITABLE'; exit 65
fi
control_probe="$bundle/.r59-benign-noclobber"
if (set -C; printf 'own-bundle-probe' > "$control_probe") 2>/dev/null; then
    rm -f -- "$control_probe"
    echo 'CONTAINED_OWN_ATTEMPT_CONTROL_PROBE_CREATED'; exit 66
fi
# Native Runner retains only CAP_DAC_READ_SEARCH for original-source
# reconciliation; the untrusted child must inherit NO effective capabilities.
while read -r field value _; do
    if test "$field" = "CapEff:" && test "$value" != "0000000000000000"; then
        echo 'CONTAINED_TASK_HAS_EFFECTIVE_CAPS'; exit 62
    fi
done < /proc/self/status
if mv .git .git-moved 2>/dev/null; then echo 'CONTAINED_GIT_POINTER_REBIND'; exit 59; fi
if rm .git 2>/dev/null; then echo 'CONTAINED_GIT_POINTER_DELETE'; exit 60; fi
if test -r "$FOREIGN_PROBE" || test -w "$FOREIGN_PROBE"; then
    echo 'CONTAINED_FOREIGN_WORKSPACE_ACCESS'; exit 61;
fi
printf 'native-contained-workspace' > contained-native.txt
chmod 600 contained-native.txt
git rev-parse --is-inside-work-tree >/dev/null
if ! git add contained-native.txt; then echo 'CONTAINED_PRIVATE_GIT_ADD_FAILED'; git rev-parse --absolute-git-dir; echo GIT_DIR_BIND_PRESENT=${GIT_DIR:+yes}; exit 55; fi
printf 'PG_CONTAINED_GIT_PRIVATE_ADD_AND_CREDENTIAL_BOUNDARY_OK'
"#;
    let mut result = call(
        &endpoint,
        "workspace.exec",
        json!({
            "clientRequestId":"pg-native-contained-git-physical-0001",
            "execution":{
                "workspaceId":"ws-contained-git",
                "executable":"/usr/bin/bash",
                "args":["-lc",command],
                "cwdRelative":".",
                "executionProfile":"contained_local",
                "env":{"FOREIGN_PROBE": foreign_probe.to_string_lossy().into_owned()},
                "timeoutMs":15000
            },
            "waitMs":10000,
            "stdoutTailBytes":1024
        }),
    );
    assert_ne!(
        result["isError"], true,
        "PG must admit contained_local: {result}"
    );
    let job = result["structuredContent"]["jobId"]
        .as_str()
        .unwrap()
        .to_owned();
    for _ in 0..30 {
        if result["structuredContent"]["executionTerminal"] == true {
            break;
        }
        result = call(
            &endpoint,
            "job.observe",
            json!({"jobId":job,"waitMs":2000,"stdoutTailBytes":1024}),
        );
        assert_ne!(
            result["isError"], true,
            "same native contained Job: {result}"
        );
    }
    if result["structuredContent"]["executionDisposition"] != "succeeded" {
        let artifacts = result["structuredContent"]["artifacts"].as_array().unwrap();
        if let Some(receipt) = artifacts.iter().find(|v| v["kind"] == "execution_result") {
            let detail = call(
                &endpoint,
                "artifact.read",
                json!({"jobId":job,"artifactId":receipt["artifactId"],
                       "offset":0,"maxBytes":8192}),
            );
            eprintln!(
                "R55_REAL_NATIVE_FAILURE_RECEIPT: {}",
                detail["structuredContent"]["content"]
            );
        }
    }
    assert_eq!(
        result["structuredContent"]["executionDisposition"], "succeeded",
        "physical systemd contained task failed: {result}"
    );
    assert_eq!(
        result["structuredContent"]["stdoutTail"],
        "PG_CONTAINED_GIT_PRIVATE_ADD_AND_CREDENTIAL_BOUNDARY_OK"
    );
    // Independent trusted Runtime test receiver verifies the real native
    // filesystem metadata, not just a task-printed string or static args.
    // It never reads request.json or another Job's Attempt bundle.
    let own_bundle: String = fixture
        .db
        .query_one("SELECT bundle_path FROM attempts WHERE job_id=$1", &[&job])
        .unwrap()
        .get(0);
    let native_mode = fs::symlink_metadata(&own_bundle).unwrap();
    assert!(native_mode.file_type().is_dir());
    assert_eq!(
        native_mode.uid(),
        0,
        "PG Attempt control bundle must be root-owned"
    );
    assert_eq!(
        native_mode.mode() & 0o777,
        0o700,
        "native Agent's own PG control bundle must be private before request.json"
    );
    let workspace = call(
        &endpoint,
        "workspace.get",
        json!({"workspaceId":"ws-contained-git"}),
    );
    assert_ne!(workspace["isError"], true, "{workspace}");
    assert_eq!(workspace["structuredContent"]["activeJobIds"], json!([]));
    let file = call(
        &endpoint,
        "workspace.read",
        json!({"workspaceId":"ws-contained-git","relativePath":"contained-native.txt",
               "mode":"FULL","maxBytes":200}),
    );
    assert_ne!(file["isError"], true, "{file}");
    assert_eq!(
        file["structuredContent"]["content"],
        "native-contained-workspace"
    );
    let artifacts = result["structuredContent"]["artifacts"].as_array().unwrap();
    let original_stdout = artifacts.iter().find(|v| v["kind"] == "stdout").unwrap();
    let read = call(
        &endpoint,
        "artifact.read",
        json!({"jobId":job,"artifactId":original_stdout["artifactId"],
               "offset":0,"maxBytes":1024}),
    );
    assert_ne!(read["isError"], true, "{read}");
    assert_eq!(
        read["structuredContent"]["content"],
        "PG_CONTAINED_GIT_PRIVATE_ADD_AND_CREDENTIAL_BOUNDARY_OK"
    );
    // The ordinary nonroot Coding task uses standard Git add/commit against
    // its exact-SHA independent Git index/refs. The original protected Git
    // repository never becomes writable and no second trusted Job is needed.
    let original_head = Command::new("git")
        .arg("-C")
        .arg(&repo)
        .args(["rev-parse", "HEAD"])
        .output()
        .unwrap();
    assert!(original_head.status.success());
    let original_head = String::from_utf8(original_head.stdout).unwrap();
    let original_head = original_head.trim();
    let private_commit_script = r#"set -eu
if test -r /etc/ordivon/runtime-mcp.token; then exit 53; fi
if test -r /etc/ordivon; then exit 54; fi
git -c user.name=ContainedAgent -c user.email=agent@example.invalid commit -qm 'original contained source delivery'
printf '%s' "$(git rev-parse HEAD)"
"#;
    let mut candidate = call(
        &endpoint,
        "workspace.exec",
        json!({"clientRequestId":"pg-contained-private-git-candidate-r57",
            "execution":{"workspaceId":"ws-contained-git","executable":"/usr/bin/bash",
                "args":["-lc",private_commit_script],
                "cwdRelative":".","executionProfile":"contained_local","timeoutMs":20000},
            "waitMs":10000,"stdoutTailBytes":1024}),
    );
    assert_ne!(candidate["isError"], true, "{candidate}");
    let candidate_job = candidate["structuredContent"]["jobId"]
        .as_str()
        .unwrap()
        .to_owned();
    for _ in 0..30 {
        if candidate["structuredContent"]["executionTerminal"] == true {
            break;
        }
        candidate = call(
            &endpoint,
            "job.observe",
            json!({"jobId":candidate_job,"waitMs":2000,"stdoutTailBytes":1024}),
        );
        assert_ne!(candidate["isError"], true, "{candidate}");
    }
    if candidate["structuredContent"]["executionDisposition"] != "succeeded" {
        let result_artifact = candidate["structuredContent"]["artifacts"]
            .as_array()
            .and_then(|items| items.iter().find(|item| item["kind"] == "execution_result"))
            .and_then(|item| item["artifactId"].as_str());
        if let Some(artifact_id) = result_artifact {
            let actual = call(
                &endpoint,
                "artifact.read",
                json!({"jobId":candidate_job,"artifactId":artifact_id,
                       "offset":0,"maxBytes":4096}),
            );
            eprintln!(
                "R63_CONTAINED_PRIVATE_GIT_RESULT={}",
                actual["structuredContent"]["content"]
            );
        }
    }
    assert_eq!(
        candidate["structuredContent"]["executionDisposition"], "succeeded",
        "real contained private Git candidate creation: {candidate}"
    );
    let candidate_commit = candidate["structuredContent"]["stdoutTail"]
        .as_str()
        .expect("original contained stdout is candidate SHA");
    assert!(
        candidate_commit.len() == 40 && candidate_commit.bytes().all(|b| b.is_ascii_hexdigit()),
        "native candidate must be one complete Git SHA: {candidate}"
    );
    let private_bare = fixture
        .root
        .join("store/cache/workspaces/ws-contained-git/agent-git");
    let original_without_candidate = Command::new("git")
        .arg("-C")
        .arg(&repo)
        .args(["cat-file", "-e", &format!("{candidate_commit}^{{commit}}")])
        .output()
        .unwrap();
    assert!(
        !original_without_candidate.status.success(),
        "contained Agent must not have written to original repository Git object store"
    );
    let before_import = Command::new("git")
        .arg("-C")
        .arg(&repo)
        .args(["rev-parse", "HEAD"])
        .output()
        .unwrap();
    assert_eq!(
        String::from_utf8(before_import.stdout).unwrap().trim(),
        original_head
    );

    // Independent trusted *source recipient* reads the Agent's immutable
    // candidate using standard Git, not by granting that Agent a Root Job.
    // Fetching only a reviewed ref leaves the original protected HEAD intact.
    let imported = Command::new("git")
        .arg("-C")
        .arg(&repo)
        .arg("fetch")
        .args(["--no-tags"])
        .arg(&private_bare)
        .arg("refs/heads/agent-work:refs/heads/reviewed-contained-output")
        .output()
        .unwrap();
    assert!(
        imported.status.success(),
        "source recipient Git fetch: {}",
        String::from_utf8_lossy(&imported.stderr)
    );
    let accepted = Command::new("git")
        .arg("-C")
        .arg(&repo)
        .args(["rev-parse", "refs/heads/reviewed-contained-output"])
        .output()
        .unwrap();
    assert!(accepted.status.success());
    assert_eq!(
        String::from_utf8(accepted.stdout).unwrap().trim(),
        candidate_commit,
        "trusted recipient must import exact candidate Commit, not a caller-reported hash"
    );
    let original_output = Command::new("git")
        .arg("-C")
        .arg(&repo)
        .args(["show", &format!("{candidate_commit}:contained-native.txt")])
        .output()
        .unwrap();
    assert!(original_output.status.success());
    assert_eq!(original_output.stdout, b"native-contained-workspace");
    let after_import = Command::new("git")
        .arg("-C")
        .arg(&repo)
        .args(["rev-parse", "HEAD"])
        .output()
        .unwrap();
    assert_eq!(
        String::from_utf8(after_import.stdout).unwrap().trim(),
        original_head,
        "separate recipient import must not update protected original HEAD"
    );
    assert!(
        Command::new("git")
            .arg("-C")
            .arg(&repo)
            .args(["fsck", "--connectivity-only"])
            .status()
            .unwrap()
            .success(),
        "source recipient requires connected Git object closure"
    );
    assert_eq!(
        fixture
            .db
            .query_one("SELECT count(*) FROM jobs", &[])
            .unwrap()
            .get::<_, i64>(0),
        2,
        "contained files + contained private Commit: no third trusted_local Job"
    );
    let state = call(
        &endpoint,
        "workspace.get",
        json!({"workspaceId":"ws-contained-git"}),
    );
    assert_ne!(state["isError"], true, "{state}");
    // A Git candidate belongs to the separate original consumer and must
    // remain in this Workspace until independent source acceptance. The
    // original protected HEAD is intentionally unchanged.
    assert_eq!(
        state["structuredContent"]["dirty"], true,
        "source proposal must remain retained until original recipient acceptance: {state}"
    );
    // Cache parent directories are shared operator assets; only original
    // Workspace-private cache descendants may receive the task's group.
    for ancestor in ["cache", "cache/workspaces", "cache/tmp", "cache/build"] {
        let path = fixture.root.join("store").join(ancestor);
        let meta = fs::metadata(&path).expect("shared cache ancestor");
        assert_eq!(meta.uid(), 0, "root owner changed for {ancestor}");
        assert_ne!(
            meta.gid(),
            65534,
            "task group owns shared ancestor {ancestor}"
        );
        assert_eq!(
            meta.permissions().mode() & 0o020,
            0,
            "shared cache ancestor became group writable: {ancestor}"
        );
    }

    // Original-runtime lifecycle falsifier: an ordinary Coding Agent can
    // produce a UNIQUE Git commit with NO change to the original Workspace
    // source files. A caller-asserted consumerReleased and the original
    // sourceStateDigest are not sufficient to GC the only candidate.
    let empty_ws = "ws-contained-git-empty";
    let opened_empty = call(
        &endpoint,
        "workspace.open",
        json!({"workspaceId":empty_ws,"sourceRepo":repo,"sourceRevision":"HEAD"}),
    );
    assert_ne!(opened_empty["isError"], true, "{opened_empty}");
    let mut empty = call(
        &endpoint,
        "workspace.exec",
        json!({"clientRequestId":"pg-contained-only-git-empty-commit-r60",
            "execution":{"workspaceId":empty_ws,"executable":"/usr/bin/bash",
                "args":["-lc",
                    "set -eu; git -c user.name=ContainedAgent -c user.email=agent@example.invalid -c commit.gpgSign=false commit --allow-empty -qm 'native-only-original-git-candidate'; printf '%s' $(git rev-parse HEAD)"],
                "cwdRelative":".","executionProfile":"contained_local","timeoutMs":15000},
            "waitMs":7000,"stdoutTailBytes":256}),
    );
    assert_ne!(empty["isError"], true, "{empty}");
    let empty_job = empty["structuredContent"]["jobId"]
        .as_str()
        .unwrap()
        .to_owned();
    for _ in 0..22 {
        if empty["structuredContent"]["executionTerminal"] == true {
            break;
        }
        empty = call(
            &endpoint,
            "job.observe",
            json!({"jobId":empty_job,"waitMs":1500,"stdoutTailBytes":256}),
        );
        assert_ne!(empty["isError"], true, "{empty}");
    }
    assert_eq!(
        empty["structuredContent"]["executionDisposition"], "succeeded",
        "{empty}"
    );
    let empty_commit = empty["structuredContent"]["stdoutTail"].as_str().unwrap();
    assert_eq!(empty_commit.len(), 40);
    assert_ne!(
        empty_commit, original_head,
        "an empty private commit must advance only Agent Git"
    );

    let empty_original = call(&endpoint, "workspace.get", json!({"workspaceId":empty_ws}));
    assert_ne!(empty_original["isError"], true, "{empty_original}");
    assert_eq!(
        empty_original["structuredContent"]["dirty"], false,
        "the outer root-owned Git tree is intentionally byte-clean: {empty_original}"
    );
    let source_digest = empty_original["structuredContent"]["sourceStateDigest"]
        .as_str()
        .expect("original CAS source state");
    let refused = call(
        &endpoint,
        "workspace.close",
        json!({"workspaceId":empty_ws,"consumerReleased":true,"force":false,
              "expectedSourceStateDigest":source_digest}),
    );
    assert_eq!(
        refused["isError"], true,
        "private-only candidate cannot disappear from the original CAS Close: {refused}"
    );
    assert_eq!(
        refused["structuredContent"]["error"]["code"], "WORKSPACE_DIRTY",
        "{refused}"
    );
    let snapshot = fixture
        .root
        .join("store/cache/workspaces")
        .join(empty_ws)
        .join("agent-git");
    assert!(
        snapshot.join("objects").is_dir(),
        "private candidate must remain"
    );
    let receiver = Command::new("git")
        .arg("-C")
        .arg(&repo)
        .arg("fetch")
        .args(["--no-tags"])
        .arg(&snapshot)
        .arg("refs/heads/agent-work:refs/heads/reviewed-empty-output")
        .output()
        .unwrap();
    assert!(
        receiver.status.success(),
        "consumer must import independently: {}",
        String::from_utf8_lossy(&receiver.stderr)
    );
    let received = Command::new("git")
        .arg("-C")
        .arg(&repo)
        .args(["rev-parse", "refs/heads/reviewed-empty-output"])
        .output()
        .unwrap();
    assert_eq!(
        String::from_utf8(received.stdout).unwrap().trim(),
        empty_commit
    );
    // The independent test-owned consumer now possesses immutable Git
    // objects. Only then may the source-side private ref be relinquished.
    let retired = Command::new("git")
        .arg("--git-dir")
        .arg(&snapshot)
        .args(["update-ref", "refs/heads/agent-work", original_head])
        .output()
        .unwrap();
    assert!(
        retired.status.success(),
        "retire candidate after receiver readback: {}",
        String::from_utf8_lossy(&retired.stderr)
    );
    let closed = call(
        &endpoint,
        "workspace.close",
        json!({"workspaceId":empty_ws,"consumerReleased":true,"force":false,
              "expectedSourceStateDigest":source_digest}),
    );
    assert_ne!(
        closed["isError"], true,
        "candidate accepted, original native Close: {closed}"
    );
    assert_eq!(closed["structuredContent"]["removed"], true, "{closed}");
    assert!(
        !snapshot.exists(),
        "old private Git cache was not collected"
    );
    eprintln!("R60_REAL_PG18_GIT_EMPTY_COMMIT_SOURCECLEAN_NATIVE_CLOSE_DENY_THEN_INDEPENDENT_ACCEPT_CLOSE_PASS");
    eprintln!("R63_ORDINARY_NONROOT_PRIVATE_GIT_ORIGINAL_SOURCE_RECIPIENT_PASS");
}

/**
 * Original PG/Native consumer contract for a real operator cutover:
 * (a) legacy already-committed trusted effect remains reconnectable by
 * exact principal+clientRequestId after new admission is restricted;
 * (b) a new same-bearer trusted_local Job is DENIED before any PG Job birth;
 * (c) a new contained_local Job still launches under the same PG authority.
 * The fixture uses disposable PG18, real HTTP MCP and a native systemd Runner.
 */
#[test]
#[ignore = "requires disposable PostgreSQL18 and real systemd transient units"]
fn pg_normal_contained_only_denies_new_trusted_but_recovers_old_committed_job() {
    let mut fixture = Fixture::new();
    fixture.host_visible_test_runner = true;
    // Original contained_local consumer needs the native nonroot Git owner
    // established on the Workspace BEFORE the trusted->contained cutover.
    // This is the existing mature fixture mechanism, not a new Runtime grant.
    fixture.contained_nonroot_test = true;
    let repo = fixture.repo();
    let initial_endpoint = fixture.endpoint();
    let opened = call(
        &initial_endpoint,
        "workspace.open",
        json!({"workspaceId":"ws-r60-profile","sourceRepo":repo,"sourceRevision":"HEAD"}),
    );
    assert_ne!(opened["isError"], true, "{opened}");

    let old_request = json!({
        "clientRequestId":"r60-original-trusted-before-cutover",
        "execution":{
            "workspaceId":"ws-r60-profile",
            "executable":"/usr/bin/printf",
            "args":["R60_ORIGINAL_TRUSTED_ONCE"],
            "cwdRelative":".",
            "executionProfile":"trusted_local",
            "timeoutMs":15000
        },
        "waitMs":10000,
        "stdoutTailBytes":1024
    });
    let mut original = call(&initial_endpoint, "workspace.exec", old_request.clone());
    assert_ne!(original["isError"], true, "{original}");
    let original_id = original["structuredContent"]["jobId"]
        .as_str()
        .unwrap()
        .to_owned();
    for _ in 0..30 {
        if original["structuredContent"]["executionTerminal"] == true {
            break;
        }
        original = call(
            &initial_endpoint,
            "job.observe",
            json!({
                "jobId":original_id,"waitMs":2000,"stdoutTailBytes":1024
            }),
        );
    }
    assert_eq!(
        original["structuredContent"]["executionDisposition"], "succeeded",
        "{original}"
    );
    assert_eq!(
        original["structuredContent"]["stdoutTail"],
        "R60_ORIGINAL_TRUSTED_ONCE"
    );
    assert_eq!(
        fixture
            .db
            .query_one("SELECT count(*) FROM jobs", &[])
            .unwrap()
            .get::<_, i64>(0),
        1
    );

    let mut old_endpoint = fixture.endpoint.take().unwrap();
    old_endpoint.kill().unwrap();
    old_endpoint.wait().unwrap();
    fixture.ordinary_contained_only = true;
    let restricted_endpoint = fixture.endpoint();

    let described = call(
        &restricted_endpoint,
        "runtime.describe",
        json!({"schemaVersion":1}),
    );
    assert_ne!(described["isError"], true, "{described}");
    let profiles = described["structuredContent"]["targets"]
        .as_array()
        .unwrap()
        .iter()
        .find(|t| t["target"] == "local_linux")
        .unwrap()["executionProfiles"]
        .clone();
    assert_eq!(
        profiles,
        json!(["contained_local"]),
        "Agent-visible discovery must not advertise the unqualified privileged profile"
    );

    let recovered = call(&restricted_endpoint, "workspace.exec", old_request);
    assert_ne!(
        recovered["isError"], true,
        "already committed old Job must remain retrievable across restricted cutover: {recovered}"
    );
    assert_eq!(recovered["structuredContent"]["jobId"], original_id);
    assert_eq!(
        fixture
            .db
            .query_one("SELECT count(*) FROM jobs", &[])
            .unwrap()
            .get::<_, i64>(0),
        1,
        "idempotent replay must never create another external effect"
    );

    let forbidden = call(
        &restricted_endpoint,
        "workspace.exec",
        json!({
            "clientRequestId":"r60-new-trusted-must-not-be-admitted",
            "execution":{"workspaceId":"ws-r60-profile","executable":"/usr/bin/printf",
                "args":["R60_PRIVILEGED_SPAWN_SHOULD_NOT_HAPPEN"],"cwdRelative":".",
                "executionProfile":"trusted_local","timeoutMs":10000},
            "waitMs":0
        }),
    );
    assert_eq!(forbidden["isError"], true, "{forbidden}");
    assert_eq!(
        forbidden["structuredContent"]["error"]["code"], "AUTHORIZATION_DENIED",
        "ordinary bearer cannot self-upgrade execution profile"
    );
    assert_eq!(
        fixture
            .db
            .query_one("SELECT count(*) FROM jobs", &[])
            .unwrap()
            .get::<_, i64>(0),
        1
    );

    let plan_forbidden = call(
        &restricted_endpoint,
        "workspace.execPlan",
        json!({
            "clientRequestId":"r60-trusted-plan-must-be-denied",
            "execution":{"workspaceId":"ws-r60-profile","executionProfile":"trusted_local",
                "steps":[{"id":"unsafe","executable":"/usr/bin/printf",
                    "args":["R60_TRUSTED_PLAN_SHOULD_NOT_RUN"],"cwdRelative":".","timeoutMs":5000}]},
            "waitMs":0
        }),
    );
    assert_eq!(plan_forbidden["isError"], true, "{plan_forbidden}");
    assert_eq!(
        plan_forbidden["structuredContent"]["error"]["code"],
        "AUTHORIZATION_DENIED"
    );
    assert_eq!(
        fixture
            .db
            .query_one("SELECT count(*) FROM jobs", &[])
            .unwrap()
            .get::<_, i64>(0),
        1
    );

    let mut contained = call(
        &restricted_endpoint,
        "workspace.exec",
        json!({
            "clientRequestId":"r60-new-contained-positive-native",
            "execution":{"workspaceId":"ws-r60-profile","executable":"/usr/bin/printf",
                "args":["R60_CONTAINED_NATIVE_WORKS"],"cwdRelative":".",
                "executionProfile":"contained_local","timeoutMs":20000},
            "waitMs":10000,"stdoutTailBytes":1024
        }),
    );
    assert_ne!(contained["isError"], true, "{contained}");
    let contained_id = contained["structuredContent"]["jobId"]
        .as_str()
        .unwrap()
        .to_owned();
    for _ in 0..30 {
        if contained["structuredContent"]["executionTerminal"] == true {
            break;
        }
        contained = call(
            &restricted_endpoint,
            "job.observe",
            json!({
            "jobId":contained_id,"waitMs":2000,"stdoutTailBytes":1024}),
        );
        assert_ne!(contained["isError"], true, "{contained}");
    }
    assert_eq!(
        contained["structuredContent"]["executionDisposition"], "succeeded",
        "{contained}"
    );
    assert_eq!(
        contained["structuredContent"]["stdoutTail"],
        "R60_CONTAINED_NATIVE_WORKS"
    );
    assert_eq!(
        fixture
            .db
            .query_one("SELECT count(*) FROM jobs", &[])
            .unwrap()
            .get::<_, i64>(0),
        2
    );
    let artifacts = contained["structuredContent"]["artifacts"]
        .as_array()
        .unwrap();
    let stdout = artifacts.iter().find(|v| v["kind"] == "stdout").unwrap();
    let bytes = call(
        &restricted_endpoint,
        "artifact.read",
        json!({"jobId":contained_id,"artifactId":stdout["artifactId"],
               "offset":0,"maxBytes":1024}),
    );
    assert_eq!(
        bytes["structuredContent"]["content"],
        "R60_CONTAINED_NATIVE_WORKS"
    );
    eprintln!("R60_AUTHENTICATED_PROFILE_CUTOVER_TRUSTED_DENIED_OLD_REPLAY_CONTAINED_NATIVE_GREEN");
}

/** Direct MCP Tool callers omit executionProfile by original schema default.
 * Only the authenticated restricted ingress may re-interpret the implicit
 * NEW effect after Runtime first checks the old exact request identity.
 */
#[test]
#[ignore = "requires disposable PostgreSQL18 and real native systemd Runner"]
fn pg_direct_implicit_profile_exact_replay_and_explicit_trusted_denial() {
    let mut fixture = Fixture::new();
    fixture.host_visible_test_runner = true;
    fixture.ordinary_contained_only = true;
    let repo = fixture.repo();
    let url = fixture.endpoint();
    let opened = call(
        &url,
        "workspace.open",
        json!({
            "workspaceId":"ws-r61-native-direct","sourceRepo":repo,"sourceRevision":"HEAD"
        }),
    );
    assert_ne!(opened["isError"], true, "{opened}");
    let request = json!({
        "clientRequestId":"r61-native-direct-omitted-profile",
        "execution":{"workspaceId":"ws-r61-native-direct",
            "executable":"/usr/bin/printf","args":["R61_DIRECT_NATIVE_CONTAINED"],
            "cwdRelative":".","timeoutMs":20000},
        "waitMs":10000,"stdoutTailBytes":1024
    });
    let mut current = call(&url, "workspace.exec", request.clone());
    assert_ne!(current["isError"], true, "{current}");
    let id = current["structuredContent"]["jobId"]
        .as_str()
        .unwrap()
        .to_owned();
    for _ in 0..30 {
        if current["structuredContent"]["executionTerminal"] == true {
            break;
        }
        current = call(
            &url,
            "job.observe",
            json!({
                "jobId":id,"waitMs":2000,"stdoutTailBytes":1024
            }),
        );
        assert_ne!(current["isError"], true, "{current}");
    }
    assert_eq!(
        current["structuredContent"]["executionDisposition"], "succeeded",
        "{current}"
    );
    assert_eq!(
        current["structuredContent"]["stdoutTail"],
        "R61_DIRECT_NATIVE_CONTAINED"
    );
    let replay = call(&url, "workspace.exec", request);
    assert_ne!(replay["isError"], true, "{replay}");
    assert_eq!(replay["structuredContent"]["jobId"], id);
    assert_eq!(
        fixture
            .db
            .query_one("SELECT count(*) FROM jobs", &[])
            .unwrap()
            .get::<_, i64>(0),
        1
    );
    let denied = call(
        &url,
        "workspace.exec",
        json!({
            "clientRequestId":"r61-native-direct-explicit-trusted-deny",
            "execution":{"workspaceId":"ws-r61-native-direct",
              "executable":"/usr/bin/true","cwdRelative":".",
              "executionProfile":"trusted_local","timeoutMs":10000},
            "waitMs":0
        }),
    );
    assert_eq!(denied["isError"], true, "{denied}");
    assert_eq!(
        denied["structuredContent"]["error"]["code"],
        "AUTHORIZATION_DENIED"
    );
    assert_eq!(
        fixture
            .db
            .query_one("SELECT count(*) FROM jobs", &[])
            .unwrap()
            .get::<_, i64>(0),
        1
    );

    let plan = json!({
        "clientRequestId":"r61-native-direct-plan-omitted-profile",
        "execution":{"workspaceId":"ws-r61-native-direct",
            "steps":[{"id":"single","executable":"/usr/bin/printf",
                "args":["R61_NATIVE_PLAN_CONTAINED"],
                "cwdRelative":".","timeoutMs":10000}],
            "timeoutMs":20000},
        "waitMs":10000,"stdoutTailBytes":1024
    });
    let mut planned = call(&url, "workspace.execPlan", plan.clone());
    assert_ne!(planned["isError"], true, "{planned}");
    let pid = planned["structuredContent"]["jobId"]
        .as_str()
        .unwrap()
        .to_owned();
    for _ in 0..30 {
        if planned["structuredContent"]["executionTerminal"] == true {
            break;
        }
        planned = call(
            &url,
            "job.observe",
            json!({
                "jobId":pid,"waitMs":2000,"stdoutTailBytes":1024
            }),
        );
        assert_ne!(planned["isError"], true, "{planned}");
    }
    assert_eq!(
        planned["structuredContent"]["executionDisposition"], "succeeded",
        "{planned}"
    );
    assert_eq!(
        planned["structuredContent"]["stdoutTail"],
        "R61_NATIVE_PLAN_CONTAINED"
    );
    let plan_replay = call(&url, "workspace.execPlan", plan);
    assert_ne!(plan_replay["isError"], true, "{plan_replay}");
    assert_eq!(plan_replay["structuredContent"]["jobId"], pid);
    assert_eq!(
        fixture
            .db
            .query_one("SELECT count(*) FROM jobs", &[])
            .unwrap()
            .get::<_, i64>(0),
        2
    );
    let denied_plan = call(
        &url,
        "workspace.execPlan",
        json!({
            "clientRequestId":"r61-direct-explicit-plan-trusted-deny",
            "execution":{
                "workspaceId":"ws-r61-native-direct",
                "executionProfile":"trusted_local",
                "steps":[{"id":"forbidden","executable":"/usr/bin/true",
                    "cwdRelative":".","timeoutMs":5000}],
                "timeoutMs":10000
            },
            "waitMs":0
        }),
    );
    assert_eq!(denied_plan["isError"], true, "{denied_plan}");
    assert_eq!(
        denied_plan["structuredContent"]["error"]["code"],
        "AUTHORIZATION_DENIED"
    );
    assert_eq!(
        fixture
            .db
            .query_one("SELECT count(*) FROM jobs", &[])
            .unwrap()
            .get::<_, i64>(0),
        2
    );
    eprintln!("R61_DIRECT_MCP_IMPLICIT_NATIVE_EXEC_AND_PLAN_EXACT_REPLAY_GREEN");
}

/// Genuine native result plus synthetic prior Attempt in disposable PG.
/// Exact-key Job discovery must not attribute a prior result to the current
/// Attempt even if both the Job identity and registration bytes are valid.
#[test]
#[ignore = "disposable PG18 and native Runner"]
fn pg_job_list_exact_key_does_not_substitute_historical_result() {
    let mut fixture = Fixture::new();
    fixture.host_visible_test_runner = true;
    let repo = fixture.repo();
    let endpoint = fixture.endpoint();
    let opened = call(
        &endpoint,
        "workspace.open",
        json!({
            "workspaceId":"ws-r6-list-result","sourceRepo":repo,"sourceRevision":"HEAD"
        }),
    );
    assert_ne!(opened["isError"], true, "{opened}");
    let key = "r6-list-current-result";
    let submitted = call(
        &endpoint,
        "workspace.exec",
        json!({
            "clientRequestId":key,"execution":{"workspaceId":"ws-r6-list-result","executable":"/usr/bin/printf","args":["R6_CURRENT_NATIVE"],"cwdRelative":".","timeoutMs":15000},
            "waitMs":15000,"stdoutTailBytes":256
        }),
    );
    assert_ne!(submitted["isError"], true, "{submitted}");
    let job = submitted["structuredContent"]["jobId"]
        .as_str()
        .unwrap()
        .to_owned();
    let deadline = Instant::now() + Duration::from_secs(25);
    let current = loop {
        let o = call(
            &endpoint,
            "job.observe",
            json!({"jobId":job,"waitMs":1000,"stdoutTailBytes":256}),
        );
        assert_ne!(o["isError"], true, "{o}");
        if o["structuredContent"]["executionTerminal"] == true {
            assert_eq!(o["structuredContent"]["executionDisposition"], "succeeded");
            assert_eq!(o["structuredContent"]["stdoutTail"], "R6_CURRENT_NATIVE");
            break o["structuredContent"]["attemptId"]
                .as_str()
                .unwrap()
                .to_owned();
        }
        assert!(Instant::now() < deadline, "{o}");
    };
    let lookup = || {
        let result = call(
            &endpoint,
            "job.list",
            json!({"clientRequestId":key,"limit":2}),
        );
        assert_ne!(result["isError"], true, "{result}");
        let rows = result["structuredContent"]["jobs"].as_array().unwrap();
        assert_eq!(rows.len(), 1);
        assert_eq!(rows[0]["jobId"], job);
        assert_eq!(rows[0]["attemptId"], current);
        rows[0].clone()
    };
    let before = lookup();
    assert_eq!(before["resultAvailable"], true);
    assert_eq!(before["deliveryDisposition"], "committed");
    assert_eq!(before["executionReasonCode"], "PROCESS_EXIT_ZERO");
    let at_max = call(
        &endpoint,
        "job.list",
        json!({"clientRequestId":key,"limit":2,"cursor":{"createdAtMs":i64::MAX as u64,"jobId":"z"}}),
    );
    assert_ne!(at_max["isError"], true, "{at_max}");
    assert_eq!(
        at_max["structuredContent"]["jobs"]
            .as_array()
            .unwrap()
            .len(),
        1
    );
    for bad_time in [i64::MAX as u64 + 1, u64::MAX] {
        let bad = call(
            &endpoint,
            "job.list",
            json!({"clientRequestId":key,"limit":2,"cursor":{"createdAtMs":bad_time,"jobId":"z"}}),
        );
        eprintln!("CURSOR_UNREPRESENTABLE {bad_time} => {bad}");
        assert_eq!(
            bad["isError"], true,
            "unrepresentable cursor must not become an empty success: {bad}"
        );
        assert_eq!(
            bad["structuredContent"]["error"]["code"], "INVALID_REQUEST",
            "{bad}"
        );
        assert_eq!(
            bad["structuredContent"]["error"]["field"], "cursor.createdAtMs",
            "{bad}"
        );
    }

    let prior = format!("r6-previous-{}", Uuid::now_v7());
    let prior_bundle = fixture.root.join("store/pg-attempts").join(&prior);
    let row=fixture.db.query_one("SELECT artifact_id,relative_path,byte_length,digest FROM artifacts WHERE job_id=$1 AND attempt_id=$2 AND kind='execution_result'",&[&job,&current]).unwrap();
    let artifact: String = row.get(0);
    let relative: String = row.get(1);
    let len: i64 = row.get(2);
    let digest: String = row.get(3);
    let native_bundle: String = fixture
        .db
        .query_one(
            "SELECT bundle_path FROM attempts WHERE attempt_id=$1",
            &[&current],
        )
        .unwrap()
        .get(0);
    let original = PathBuf::from(native_bundle).join(&relative);
    let historical = prior_bundle.join(&relative);
    assert!(original.starts_with(&fixture.root) && historical.starts_with(&fixture.root));
    fs::create_dir_all(historical.parent().unwrap()).unwrap();
    // Preserve exact native bytes in the synthetic historical bundle. This is
    // a representation falsifier, not evidence of a physical retry.
    fs::copy(&original, &historical).unwrap();
    let mut tx = fixture.db.transaction().unwrap();
    assert_eq!(
        tx.execute(
            "UPDATE attempts SET attempt_number=2 WHERE attempt_id=$1 AND attempt_number=1",
            &[&current]
        )
        .unwrap(),
        1
    );
    tx.execute("INSERT INTO attempts(attempt_id,job_id,attempt_number,state,termination_intent,launch_token_digest,bundle_path,unit_name,created_at_ms,row_version) SELECT $1,job_id,1,'failed','natural',launch_token_digest,$2,$3,created_at_ms,0 FROM attempts WHERE attempt_id=$4",&[&prior,&prior_bundle.to_string_lossy().to_string(),&format!("ordivon-pg-{prior}.service"),&current]).unwrap();
    assert_eq!(
        tx.execute(
            "UPDATE artifacts SET attempt_id=$1 WHERE artifact_id=$2",
            &[&prior, &artifact]
        )
        .unwrap(),
        1
    );
    tx.commit().unwrap();
    let row = fixture
        .db
        .query_one(
            "SELECT attempt_id,byte_length,digest FROM artifacts WHERE artifact_id=$1",
            &[&artifact],
        )
        .unwrap();
    assert_eq!(row.get::<_, String>(0), prior);
    assert_eq!(row.get::<_, i64>(1), len);
    assert_eq!(row.get::<_, String>(2), digest);
    // Exercise exact Attempt attribution and contradictory terminal evidence in
    // this disposable database; no new physical Attempt is asserted.
    let terminal_sequence: i64 = fixture.db.query_one(
        "SELECT event_sequence FROM job_events WHERE job_id=$1 AND attempt_id=$2 AND event_type='JOB_TERMINAL'",
        &[&job, &current],
    ).unwrap().get(0);
    fixture
        .db
        .execute(
            "UPDATE job_events SET attempt_id=$1 WHERE job_id=$2 AND event_sequence=$3",
            &[&prior, &job, &terminal_sequence],
        )
        .unwrap();
    assert!(lookup()["executionReasonCode"].is_null());
    fixture
        .db
        .execute(
            "UPDATE job_events SET attempt_id=$1 WHERE job_id=$2 AND event_sequence=$3",
            &[&current, &job, &terminal_sequence],
        )
        .unwrap();
    let extra_sequence = terminal_sequence + 1;
    fixture.db.execute(
        "INSERT INTO job_events(event_id,job_id,attempt_id,event_sequence,event_type,origin,previous_state,new_state,reason_code,detail_json,detail_digest,observed_at_ms) SELECT $1,job_id,attempt_id,$2,event_type,origin,previous_state,new_state,'CONTRADICTORY_TEST_REASON',detail_json,detail_digest,observed_at_ms FROM job_events WHERE job_id=$3 AND event_sequence=$4",
        &[&format!("reason-conflict-{}", Uuid::now_v7()), &extra_sequence, &job, &terminal_sequence],
    ).unwrap();
    assert!(lookup()["executionReasonCode"].is_null());
    fixture
        .db
        .execute(
            "DELETE FROM job_events WHERE job_id=$1 AND event_sequence=$2",
            &[&job, &extra_sequence],
        )
        .unwrap();
    fixture
        .db
        .execute(
            "UPDATE job_events SET new_state='failed' WHERE job_id=$1 AND event_sequence=$2",
            &[&job, &terminal_sequence],
        )
        .unwrap();
    assert!(lookup()["executionReasonCode"].is_null());
    fixture
        .db
        .execute(
            "UPDATE job_events SET new_state='succeeded' WHERE job_id=$1 AND event_sequence=$2",
            &[&job, &terminal_sequence],
        )
        .unwrap();
    assert_eq!(lookup()["executionReasonCode"], "PROCESS_EXIT_ZERO");
    let historical_only = lookup();
    // Restore the exact native registration before asserting the result.
    fixture
        .db
        .execute(
            "UPDATE artifacts SET attempt_id=$1 WHERE artifact_id=$2",
            &[&current, &artifact],
        )
        .unwrap();
    let restored = lookup();
    assert_eq!(restored["resultAvailable"], true);
    assert_eq!(restored["deliveryDisposition"], "committed");
    eprintln!(
        "EXACT_KEY historical_only resultAvailable={} deliveryDisposition={}",
        historical_only["resultAvailable"], historical_only["deliveryDisposition"]
    );
    assert_eq!(historical_only["artifactCount"], before["artifactCount"]);
    assert_eq!(historical_only["executionTerminal"], true);
    assert_eq!(historical_only["resultAvailable"], false);
    assert_eq!(
        historical_only["deliveryDisposition"],
        "reconciliation_required"
    );
}
