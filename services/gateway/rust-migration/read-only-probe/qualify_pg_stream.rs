// Test fragment appended to a generated copy of Runtime's own pg_vertical.rs.
// Its Fixture starts an isolated PostgreSQL Unix socket, real MCP and Runner.
// No production database or bearer is used.
#[test]
#[ignore = "isolated native PG and systemd Runner; explicit Gateway consumer qualification"]
fn gateway_r21_real_pg_stream_consumer() {
    use std::io::Write;
    let probe =
        PathBuf::from(std::env::var_os("ORDIVON_GATEWAY_STREAM_PROBE").expect("probe path"));
    assert!(probe.is_absolute() && probe.is_file());
    let mut fixture = Fixture::new();
    fixture.host_visible_test_runner = true;
    let repo = fixture.repo();
    let endpoint = fixture.endpoint();
    let open = call(
        &endpoint,
        "workspace.open",
        json!({
            "workspaceId":"ws-gateway-stream","sourceRepo":repo,"sourceRevision":"HEAD"
        }),
    );
    assert_ne!(open["isError"], true, "{open}");
    let text = "中文🙂abcé";
    use sha2::{Digest, Sha256};
    let issuer = "fixture-issuer";
    let principal = "pg-consumer";
    let public_request = "gateway-r21-real-pg-stream";
    let scoped_request = format!(
        "request:gw-principal:{}",
        hex::encode(Sha256::digest(
            serde_json::to_vec(&[
                "ordivon.gateway-principal-scoped-execution-request.v1",
                issuer,
                principal,
                "execution.linux",
                public_request
            ])
            .unwrap()
        ))
    );
    let mut observed = call(
        &endpoint,
        "workspace.exec",
        json!({
            "clientRequestId":scoped_request,
            "execution":{"workspaceId":"ws-gateway-stream","executable":"/usr/bin/printf",
                "args":["%s",text],"cwdRelative":".","timeoutMs":5000},
            "waitMs":10000,"stdoutTailBytes":0
        }),
    );
    assert_ne!(observed["isError"], true, "{observed}");
    let job = observed["structuredContent"]["jobId"]
        .as_str()
        .unwrap()
        .to_owned();
    for _ in 0..30 {
        if observed["structuredContent"]["executionTerminal"] == true {
            break;
        }
        observed = call(
            &endpoint,
            "job.observe",
            json!({"jobId":job,"waitMs":1000,"stdoutTailBytes":0}),
        );
        assert_ne!(observed["isError"], true, "{observed}");
    }
    let receipt = &observed["structuredContent"];
    assert_eq!(receipt["executionDisposition"], "succeeded", "{receipt}");
    let descriptor = receipt["artifacts"]
        .as_array()
        .unwrap()
        .iter()
        .find(|d| d["kind"] == "stdout")
        .expect("native stdout")
        .clone();
    assert_eq!(descriptor["retainedBytes"], text.len());
    let id = descriptor["artifactId"].as_str().unwrap();
    let credential = fixture.root.join("gateway-r21-fixture-bearer");
    fs::write(&credential, "p".repeat(32)).unwrap();
    fs::set_permissions(&credential, fs::Permissions::from_mode(0o600)).unwrap();
    let input = json!({"operationRef":format!("ordivon-exec:v1:runtime.linux:{job}"),
        "descriptor":descriptor,"maxTotalBytes":text.len(),"maxWindows":20,"chunkBytes":4});
    let run_mode = |input: &Value, mode: &str| -> Value {
        let mut child = Command::new(&probe)
            .arg(mode)
            .arg(&endpoint)
            .arg(&credential)
            .arg("auto")
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .unwrap();
        child
            .stdin
            .take()
            .unwrap()
            .write_all(input.to_string().as_bytes())
            .unwrap();
        let output = child.wait_with_output().unwrap();
        assert!(output.status.success(), "probe exit {:?}", output.status);
        let stdout = String::from_utf8(output.stdout).unwrap();
        assert!(!stdout.contains(&"p".repeat(32)));
        assert!(!String::from_utf8_lossy(&output.stderr).contains(&"p".repeat(32)));
        serde_json::from_str(&stdout).unwrap()
    };
    let run = |v: &Value| run_mode(v, "verify-protected-artifact-stream-fixture");
    let verified = run(&input);
    assert_eq!(
        verified,
        json!({"outcome":"stream","evidence":{"standing":"verified","received_bytes":text.len(),"windows":5}})
    );
    let mut bounded = input.clone();
    bounded["maxWindows"] = json!(1);
    assert_eq!(
        run(&bounded),
        json!({"outcome":"stream","evidence":{"standing":"incomplete","received_bytes":3,"windows":1}})
    );
    let mut scoped = input.clone();
    scoped["binding"] = json!({"issuer":issuer,"principal":principal,"capability":"execution.linux","request_id":public_request,"operation_ref":input["operationRef"]});
    let run_scoped = |v: &Value| run_mode(v, "verify-scoped-artifact-stream-fixture");
    let bound = run_scoped(&scoped);
    assert_eq!(bound["outcome"], "scoped_stream", "{bound}");
    assert_eq!(bound["evidence"]["operation_ref"], input["operationRef"]);
    assert_eq!(bound["evidence"]["descriptor"], input["descriptor"]);
    assert_eq!(bound["evidence"]["evidence"]["standing"], "verified");
    for field in [
        "issuer",
        "principal",
        "request_id",
        "capability",
        "operation_ref",
    ] {
        let mut foreign = scoped.clone();
        foreign["binding"][field] = json!("foreign");
        let denied = run_scoped(&foreign);
        assert_eq!(
            denied["evidence"]["standing"], "rejected",
            "{field}: {denied}"
        );
    }
    eprintln!("GATEWAY_R22_REAL_PG_SCOPED_PASS exact original namespace and 5 foreign controls");
    fs::write(&credential, "wrong-token").unwrap();
    assert_eq!(run(&input)["outcome"], "owner_failure");
    fs::write(&credential, "p".repeat(32)).unwrap();
    let row=fixture.db.query_one("SELECT a.bundle_path,r.relative_path FROM artifacts r JOIN attempts a ON a.attempt_id=r.attempt_id WHERE r.job_id=$1 AND r.artifact_id=$2",&[&job,&id]).unwrap();
    let path = PathBuf::from(row.get::<_, String>(0)).join(row.get::<_, String>(1));
    assert!(path.starts_with(&fixture.root));
    fs::write(path, vec![b'x'; text.len()]).unwrap();
    let damaged = run(&input);
    assert_eq!(damaged["outcome"], "owner_failure", "{damaged}");
    assert_eq!(damaged["failure"]["failure"], "tool", "{damaged}");
    assert_eq!(
        damaged["failure"]["evidence"]["action"], "stop-consumption",
        "{damaged}"
    );
    let jobs: i64 = fixture
        .db
        .query_one("SELECT count(*) FROM jobs", &[])
        .unwrap()
        .get(0);
    assert_eq!(jobs, 1, "no redispatch");
    eprintln!(
        "GATEWAY_R21_REAL_PG_STREAM_PASS verified={} windows=5 incomplete wrong-token corruption jobs=1",
        text.len()
    );
}
