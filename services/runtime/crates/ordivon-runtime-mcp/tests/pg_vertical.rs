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
            .args(["-h", "", "-p", "5432", "-c", "fsync=off"]);
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
        }
    }
    fn endpoint(&mut self) -> String {
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
        let output = fs::File::create(self.root.join("endpoint.log")).unwrap();
        self.endpoint = Some(
            Command::new(env!("CARGO_BIN_EXE_ordivon-runtime-pg"))
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
                .env("ORDIVON_PG_PRINCIPAL", "pg-consumer")
                .stdout(Stdio::null())
                .stderr(output)
                .spawn()
                .unwrap(),
        );
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
    rpc(url, "tools/call", json!({"name":name,"arguments":args}))
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
    assert_eq!(names.len(), 19);
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
#[ignore = "requires PostgreSQL binaries and authorized systemd/cgroup execution"]
fn fresh_pg_mcp_native_runner_success_and_cancel() {
    let mut fixture = Fixture::new();
    let repo = fixture.repo();
    let endpoint = fixture.endpoint();
    let open = call(
        &endpoint,
        "workspace.open",
        json!({"workspaceId":"ws-physical","sourceRepo":repo,"sourceRevision":"HEAD"}),
    );
    assert_ne!(open["isError"], true, "{open}");
    let exec = call(
        &endpoint,
        "workspace.exec",
        json!({"clientRequestId":"pg-native-physical-0001","execution":{"workspaceId":"ws-physical","executable":"/usr/bin/printf","args":["native-proof"],"cwdRelative":".","timeoutMs":5000},"waitMs":10000}),
    );
    assert_ne!(
        exec["isError"], true,
        "physical native launch required: {exec}"
    );
    assert_eq!(
        exec["structuredContent"]["executionDisposition"], "succeeded",
        "{exec}"
    );
    assert_eq!(exec["structuredContent"]["stdoutTail"], "native-proof");
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
    let planned = call(&endpoint, "workspace.execPlan", plan_request.clone());
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
    let observed = call(
        &endpoint,
        "job.observe",
        json!({"jobId":job,"waitMs":10000}),
    );
    // A stop request is not proof of an OS terminal outcome. If the Runner
    // does not publish terminal evidence, retain the honest stopping state.
    assert_eq!(
        observed["structuredContent"]["terminationIntent"], "stop_requested",
        "{observed}"
    );
    if observed["structuredContent"]["executionTerminal"] != true {
        assert_eq!(
            observed["structuredContent"]["attemptState"], "stopping",
            "{observed}"
        );
        assert_eq!(
            observed["structuredContent"]["resultAvailable"], false,
            "{observed}"
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
