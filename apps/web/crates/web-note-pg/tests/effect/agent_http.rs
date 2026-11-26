use super::fixture::setup;
use axum::{
    Router,
    body::{Body, to_bytes},
    http::{Request, StatusCode, header},
};
use ordivon_web_note_pg::{
    PgNoteStore,
    effect::{ApprovalWrite, GrantCreate, PreparedGrant},
    http::{AgentConfig, AgentState, agent_router},
};
use serde_json::{Value, json};
use std::{
    path::{Path, PathBuf},
    process::Stdio,
    time::{Duration, SystemTime, UNIX_EPOCH},
};
use tokio::{
    io::{AsyncBufReadExt, AsyncWriteExt, BufReader},
    process::{Child, ChildStdin, ChildStdout, Command},
};
use tower::ServiceExt;
use uuid::Uuid;
const ORIGIN: &str = "https://web.example";
const CREATE: &str = "/api/agent/canary/notes";
fn now() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs() as i64
}
fn executable(name: &str) -> PathBuf {
    let out = std::process::Command::new("sh")
        .args(["-c", &format!("command -v {name}")])
        .output()
        .unwrap();
    assert!(out.status.success());
    let p = PathBuf::from(String::from_utf8(out.stdout).unwrap().trim());
    if p.to_string_lossy().contains("/mise/shims/") {
        let out = std::process::Command::new("mise")
            .args(["which", name])
            .output()
            .unwrap();
        assert!(out.status.success());
        PathBuf::from(String::from_utf8(out.stdout).unwrap().trim())
            .canonicalize()
            .unwrap()
    } else {
        p.canonicalize().unwrap()
    }
}
fn node() -> PathBuf {
    let out = std::process::Command::new(std::env::var("WEB_NOTE_TEST_NODE").unwrap())
        .args(["-p", "process.execPath"])
        .output()
        .unwrap();
    assert!(out.status.success());
    PathBuf::from(String::from_utf8(out.stdout).unwrap().trim())
}
struct Issuer {
    child: Child,
    input: ChildStdin,
    output: BufReader<ChildStdout>,
    url: String,
}
impl Issuer {
    async fn start() -> Self {
        let mut child = Command::new(node())
            .arg(concat!(
                env!("CARGO_MANIFEST_DIR"),
                "/tests/agent-issuer-fixture.mjs"
            ))
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .kill_on_drop(true)
            .spawn()
            .unwrap();
        let input = child.stdin.take().unwrap();
        let mut output = BufReader::new(child.stdout.take().unwrap());
        let mut line = String::new();
        assert!(
            tokio::time::timeout(Duration::from_secs(5), output.read_line(&mut line))
                .await
                .unwrap()
                .unwrap()
                > 0
        );
        let v: Value = serde_json::from_str(&line).unwrap();
        let url = v["issuer"].as_str().unwrap().into();
        Self {
            child,
            input,
            output,
            url,
        }
    }
    async fn proof(&mut self, path: &str, variant: &str, client: &str) -> Value {
        self.input
            .write_all(
                format!(
                    "{}\n",
                    json!({"path":path,"variant":variant,"client":client})
                )
                .as_bytes(),
            )
            .await
            .unwrap();
        let mut line = String::new();
        assert!(
            tokio::time::timeout(Duration::from_secs(5), self.output.read_line(&mut line))
                .await
                .unwrap()
                .unwrap()
                > 0
        );
        serde_json::from_str(&line).unwrap()
    }
    async fn stop(mut self) {
        drop(self.input);
        assert!(
            tokio::time::timeout(Duration::from_secs(5), self.child.wait())
                .await
                .unwrap()
                .unwrap()
                .success()
        )
    }
}
fn store_for(name: &str) -> PgNoteStore {
    PgNoteStore::local(
        &PathBuf::from(std::env::var_os("WEB_NOTE_TEST_SOCKET").unwrap()),
        std::env::var("WEB_NOTE_TEST_PORT")
            .unwrap()
            .parse()
            .unwrap(),
        &std::env::var("WEB_NOTE_TEST_USER").unwrap(),
        name,
    )
    .unwrap()
}
fn app(store: PgNoteStore, issuer: &str) -> Router {
    let evaluator = Path::new(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../../../platform/security/contracts/agent-admission-v1/evaluate.py"
    ));
    app_with_evaluator(store, issuer, evaluator)
}
fn app_with_evaluator(store: PgNoteStore, issuer: &str, evaluator: &Path) -> Router {
    let node = node();
    let opa = executable("opa");
    let python = Path::new("/usr/bin/python3");
    let verifier = Path::new(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../verifier/agent-request.ts"
    ));
    agent_router(
        AgentState::new(
            store,
            AgentConfig {
                origin: ORIGIN,
                issuer,
                allow_loopback_http: true,
                node: &node,
                verifier_script: verifier,
                python,
                admission_script: evaluator,
                opa_dir: opa.parent().unwrap(),
                max_parallel: 4,
                deadline: Duration::from_secs(8),
            },
            now,
        )
        .unwrap(),
    )
}
async fn call(
    app: &Router,
    path: &str,
    proof: &Value,
    effect: &str,
    body: Value,
) -> (StatusCode, Value) {
    let response = app
        .clone()
        .oneshot(
            Request::builder()
                .method("POST")
                .uri(path)
                .header(header::CONTENT_TYPE, "application/json")
                .header("authorization", proof["authorization"].as_str().unwrap())
                .header("dpop", proof["dpop"].as_str().unwrap())
                .header("x-ordivon-effect-id", effect)
                .body(Body::from(body.to_string()))
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(response.headers()[header::CACHE_CONTROL], "no-store");
    let status = response.status();
    let bytes = to_bytes(response.into_body(), 262144).await.unwrap();
    (
        status,
        serde_json::from_slice(&bytes).unwrap_or(Value::Null),
    )
}
fn eid(c: char) -> String {
    format!("sha256:{}", c.to_string().repeat(64))
}
fn grant(id: &str, agent: &str) -> PreparedGrant {
    PreparedGrant::new(
        GrantCreate {
            grant_id: id.into(),
            principal_id: "p".into(),
            agent_id: format!("oauth-client:{agent}"),
            audience: ORIGIN.into(),
            allowed_actions: vec!["canary.note.create".into(), "canary.note.publish".into()],
            resource_prefixes: vec!["/canary/notes".into()],
            expires_at_epoch_seconds: now() + 600,
            max_risk_class: "R4".into(),
            step_up_at_or_above: "R4".into(),
            remaining_effects: 3,
        },
        Uuid::new_v4(),
        now(),
    )
    .unwrap()
}
#[tokio::test]
async fn actual_security_agent_effect_and_replay() {
    let (store, peer) = setup("agent_http").await;
    let g = grant("http-agent-grant", "agent-test");
    store.issue_grant(&g).await.unwrap();
    let mut issuer = Issuer::start().await;
    let app = app(store_for("agent_http"), &issuer.url);
    let content = json!({"content":"hello\n中文 🚀"});
    let id = eid('a');
    for variant in [
        "audience",
        "binding",
        "method",
        "path",
        "expired",
        "token-signature",
    ] {
        let p = issuer.proof(CREATE, variant, "agent-test").await;
        let (s, b) = call(&app, CREATE, &p, &id, content.clone()).await;
        assert_eq!(s, StatusCode::UNAUTHORIZED, "{variant}: {b:?}");
    }
    assert_eq!(
        peer.query_one("SELECT count(*) FROM dpop_proofs", &[])
            .await
            .unwrap()
            .get::<_, i64>(0),
        0
    );
    let proof = issuer.proof(CREATE, "ok", "agent-test").await;
    let (s, b) = call(&app, CREATE, &proof, &id, content.clone()).await;
    assert_eq!(s, StatusCode::CREATED, "{b:?}");
    assert_eq!(b["receipt"]["agentId"], "oauth-client:agent-test");
    assert_eq!(
        b["receipt"]["result"]["note"]["content"],
        content["content"]
    );
    assert_eq!(b["replayed"], false);
    let note = b["receipt"]["result"]["note"]["noteId"].as_str().unwrap();
    // Exact effect digest against independent Node JSON.stringify reference.
    let js=std::process::Command::new(node()).args(["-e","const {createHash}=require('node:crypto');process.stdout.write('sha256:'+createHash('sha256').update(JSON.stringify({action:'canary.note.create',resource:'/canary/notes',content:process.argv[1]})).digest('hex'))",content["content"].as_str().unwrap()]).output().unwrap();
    assert_eq!(
        b["receipt"]["effectDigest"],
        String::from_utf8(js.stdout).unwrap()
    );
    assert_eq!(
        call(&app, CREATE, &proof, &id, content.clone()).await.0,
        StatusCode::UNAUTHORIZED
    );
    let p = issuer.proof(CREATE, "ok", "agent-test").await;
    let (s, replay) = call(&app, CREATE, &p, &id, content.clone()).await;
    assert_eq!(s, StatusCode::OK);
    assert_eq!(replay["receipt"], b["receipt"]);
    assert_eq!(replay["replayed"], true);
    let p = issuer.proof(CREATE, "ok", "agent-test").await;
    assert_eq!(
        call(&app, CREATE, &p, &id, json!({"content":"different"}))
            .await
            .0,
        StatusCode::CONFLICT
    );
    let p = issuer.proof(CREATE, "ok", "other-agent").await;
    assert_eq!(
        call(&app, CREATE, &p, &id, content.clone()).await.0,
        StatusCode::FORBIDDEN
    );
    let path = format!("/api/agent/canary/notes/{note}/publish");
    let pub_id = eid('b');
    let p = issuer.proof(&path, "ok", "agent-test").await;
    let (s, step) = call(&app, &path, &p, &pub_id, json!({})).await;
    assert_eq!(s, StatusCode::PRECONDITION_REQUIRED, "{step:?}");
    assert_eq!(
        store
            .get_grant("http-agent-grant")
            .await
            .unwrap()
            .remaining_effects,
        2
    );
    // Trusted native approval fixture, not a physical WebAuthn approval ceremony.
    store
        .put_verified_approval(&ApprovalWrite {
            effect_id: pub_id.clone(),
            effect_digest: step["effectDigest"].as_str().unwrap().into(),
            principal_id: "p".into(),
            credential_id: "credential".into(),
            verified_at: now(),
            expires_at: now() + 120,
        })
        .await
        .unwrap();
    let p = issuer.proof(&path, "ok", "agent-test").await;
    let (s, published) = call(&app, &path, &p, &pub_id, json!({})).await;
    assert_eq!(s, StatusCode::OK, "{published:?}");
    assert_eq!(published["replayed"], false);
    assert_eq!(published["receipt"]["result"]["note"]["state"], "PUBLISHED");
    assert_eq!(
        store
            .get_grant("http-agent-grant")
            .await
            .unwrap()
            .remaining_effects,
        1
    );
    assert!(
        peer.query_one(
            "SELECT consumed_at FROM effect_approvals WHERE effect_id=$1",
            &[&pub_id]
        )
        .await
        .unwrap()
        .get::<_, Option<i64>>(0)
        .is_some()
    );
    let current = store.get_grant("http-agent-grant").await.unwrap();
    store
        .revoke_grant(
            "p",
            &current.grant_id,
            &current.grant_digest,
            Uuid::new_v4(),
            now(),
        )
        .await
        .unwrap();
    let p = issuer.proof(CREATE, "ok", "agent-test").await;
    assert_eq!(
        call(&app, CREATE, &p, &eid('c'), content.clone()).await.0,
        StatusCode::FORBIDDEN
    );
    let p = issuer.proof(&path, "ok", "agent-test").await;
    let (s, replay) = call(&app, &path, &p, &pub_id, json!({})).await;
    assert_eq!(s, StatusCode::OK);
    assert_eq!(replay["receipt"], published["receipt"]);
    assert_eq!(
        peer.query_one(
            "SELECT count(*) FROM agent_effects WHERE agent_id='oauth-client:agent-test'",
            &[]
        )
        .await
        .unwrap()
        .get::<_, i64>(0),
        2
    );
    issuer.stop().await;
    println!(
        "real loopback discovery/JWKS, RSA JWT+ES256 DPoP, existing Security+OPA, native durable replay, create, step-up, trusted approval, publish, exact replay, actor/digest mismatch, revoke"
    );
}

#[path = "agent_http_races.rs"]
mod races;
