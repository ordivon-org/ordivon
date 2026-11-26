use super::*;
use ordivon_web_note_pg::OwnerError;
struct Scratch(PathBuf);
impl Scratch {
    fn new() -> Self {
        let p = std::env::temp_dir().join(format!("web-agent-test-{}", Uuid::new_v4()));
        std::fs::create_dir(&p).unwrap();
        Self(p)
    }
    fn gate(&self, mode: &str) -> PathBuf {
        let evaluator = Path::new(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/../../../../platform/security/contracts/agent-admission-v1/evaluate.py"
        ))
        .canonicalize()
        .unwrap();
        let script = self.0.join("gate.py");
        let py = format!(
            "import sys,runpy,json,time,pathlib\nsys.dont_write_bytecode=True\nevaluate=runpy.run_path({})['evaluate']\ndecision=evaluate(json.load(sys.stdin))\nroot=pathlib.Path({})\nif {}=='gate':\n (root/'ready').write_text('ready')\n deadline=time.monotonic()+5\n while not (root/'release').exists():\n  if time.monotonic()>deadline: raise RuntimeError('gate timeout')\n  time.sleep(.01)\nelse:\n decision['effect']['requestDigest']='sha256:'+'0'*64\njson.dump(decision,sys.stdout)\n",
            json!(evaluator),
            json!(self.0),
            json!(mode)
        );
        std::fs::write(&script, py).unwrap();
        script
    }
    async fn ready(&self) {
        tokio::time::timeout(Duration::from_secs(5), async {
            while !self.0.join("ready").exists() {
                tokio::time::sleep(Duration::from_millis(10)).await
            }
        })
        .await
        .unwrap();
    }
    fn release(&self) {
        std::fs::write(self.0.join("release"), "release").unwrap();
    }
}
impl Drop for Scratch {
    fn drop(&mut self) {
        let _ = std::fs::remove_dir_all(&self.0);
    }
}

#[tokio::test]
async fn native_agent_scope_race_and_bound_policy() {
    let (store, mut peer) = setup("agent_scope_race").await;
    let g = grant("race-grant", "agent-test");
    store.issue_grant(&g).await.unwrap();
    let mut issuer = Issuer::start().await;
    let scratch = Scratch::new();
    let script = scratch.gate("gate");
    let gated = app_with_evaluator(store_for("agent_scope_race"), &issuer.url, &script);
    let proof = issuer.proof(CREATE, "ok", "agent-test").await;
    let request = tokio::spawn(async move {
        call(
            &gated,
            CREATE,
            &proof,
            &eid('d'),
            json!({"content":"late ambiguity"}),
        )
        .await
    });
    scratch.ready().await;
    let second = grant("race-second", "agent-test");
    store.issue_grant(&second).await.unwrap();
    scratch.release();
    let (status, body) = request.await.unwrap();
    assert_eq!(status, StatusCode::CONFLICT, "{body:?}");
    assert_eq!(body["code"], "agent-grant-ambiguous");
    assert_eq!(
        store
            .get_grant("race-grant")
            .await
            .unwrap()
            .remaining_effects,
        3
    );
    assert_eq!(
        store
            .get_grant("race-second")
            .await
            .unwrap()
            .remaining_effects,
        3
    );
    let second = store.get_grant("race-second").await.unwrap();
    store
        .revoke_grant(
            "p",
            &second.grant_id,
            &second.grant_digest,
            Uuid::new_v4(),
            now(),
        )
        .await
        .unwrap();
    // Actual real OPA output with one independently modified binding must fail.
    let tamper = Scratch::new();
    let script = tamper.gate("tamper");
    let bad = app_with_evaluator(store_for("agent_scope_race"), &issuer.url, &script);
    let proof = issuer.proof(CREATE, "ok", "agent-test").await;
    let (status, body) = call(
        &bad,
        CREATE,
        &proof,
        &eid('e'),
        json!({"content":"bad decision"}),
    )
    .await;
    assert_eq!(status, StatusCode::SERVICE_UNAVAILABLE, "{body:?}");
    assert_eq!(
        store
            .get_grant("race-grant")
            .await
            .unwrap()
            .remaining_effects,
        3
    );
    // Real in-flight native write, blocked by a trigger on a peer's lock.
    peer.batch_execute("CREATE FUNCTION hold_agent_note() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN PERFORM pg_advisory_xact_lock(812299); RETURN NEW; END $$; CREATE TRIGGER hold_agent_note BEFORE INSERT ON canary_notes FOR EACH ROW EXECUTE FUNCTION hold_agent_note();").await.unwrap();
    let tx = peer.transaction().await.unwrap();
    tx.query_one("SELECT pg_advisory_xact_lock(812299)", &[])
        .await
        .unwrap();
    let normal = app(store_for("agent_scope_race"), &issuer.url);
    let proof = issuer.proof(CREATE, "ok", "agent-test").await;
    let request = tokio::spawn(async move {
        call(
            &normal,
            CREATE,
            &proof,
            &eid('f'),
            json!({"content":"scope held"}),
        )
        .await
    });
    tokio::time::timeout(Duration::from_secs(5),async{
  loop{
   let waiting:bool=tx.query_one("SELECT EXISTS(SELECT 1 FROM pg_locks WHERE locktype='advisory' AND objid=812299 AND NOT granted)",&[]).await.unwrap().get(0);
   if waiting{break}tokio::time::sleep(Duration::from_millis(10)).await;
  }
 }).await.unwrap();
    assert!(matches!(
        store
            .issue_grant(&grant("blocked-grant", "agent-test"))
            .await,
        Err(OwnerError::Busy)
    ));
    store
        .issue_grant(&grant("disjoint-grant", "another-agent"))
        .await
        .unwrap();
    tx.rollback().await.unwrap();
    let (status, body) = request.await.unwrap();
    assert_eq!(status, StatusCode::CREATED, "{body:?}");
    assert_eq!(
        store
            .get_grant("race-grant")
            .await
            .unwrap()
            .remaining_effects,
        2
    );
    assert!(matches!(
        store.get_grant("blocked-grant").await,
        Err(OwnerError::GrantNotFound)
    ));
    assert_eq!(
        peer.query_one(
            "SELECT count(*) FROM agent_effects WHERE agent_id='oauth-client:agent-test'",
            &[]
        )
        .await
        .unwrap()
        .get::<_, i64>(0),
        1
    );
    issuer.stop().await;
    println!(
        "real OPA decision held across new grant, late ambiguity denied; exact bound effect decision tamper denied; native trigger held commit scope, competing issuance BUSY and disjoint scope progresses"
    );
}

#[tokio::test]
async fn native_agent_replay_ack_unknown() {
    let (store, peer) = setup("agent_ack_unknown").await;
    store
        .issue_grant(&grant("ack-grant", "agent-test"))
        .await
        .unwrap();
    let mut issuer = Issuer::start().await;
    let proxy = PgNoteStore::local(
        &PathBuf::from(std::env::var_os("WEB_HTTP_AGENT_TEST_ACK_PROXY").unwrap()),
        std::env::var("WEB_NOTE_TEST_PORT")
            .unwrap()
            .parse()
            .unwrap(),
        &std::env::var("WEB_NOTE_TEST_USER").unwrap(),
        "agent_ack_unknown",
    )
    .unwrap();
    let proxied = app(proxy, &issuer.url);
    let normal = app(store_for("agent_ack_unknown"), &issuer.url);
    let proof = issuer.proof(CREATE, "ok", "agent-test").await;
    let content = json!({"content":"unknown replay claim"});
    let id = eid('1');
    let (status, body) = call(&proxied, CREATE, &proof, &id, content.clone()).await;
    assert_eq!(status, StatusCode::SERVICE_UNAVAILABLE, "{body:?}");
    assert_eq!(body["code"], "agent-replay-unavailable");
    assert!(body.get("receipt").is_none());
    assert_eq!(
        peer.query_one("SELECT count(*) FROM dpop_proofs", &[])
            .await
            .unwrap()
            .get::<_, i64>(0),
        1
    );
    assert_eq!(
        peer.query_one(
            "SELECT count(*) FROM agent_effects WHERE agent_id='oauth-client:agent-test'",
            &[]
        )
        .await
        .unwrap()
        .get::<_, i64>(0),
        0
    );
    assert_eq!(
        store
            .get_grant("ack-grant")
            .await
            .unwrap()
            .remaining_effects,
        3
    );
    assert_eq!(
        call(&normal, CREATE, &proof, &id, content.clone()).await.0,
        StatusCode::UNAUTHORIZED
    );
    let fresh = issuer.proof(CREATE, "ok", "agent-test").await;
    assert_eq!(
        call(&normal, CREATE, &fresh, &id, content).await.0,
        StatusCode::CREATED
    );
    assert_eq!(
        store
            .get_grant("ack-grant")
            .await
            .unwrap()
            .remaining_effects,
        2
    );
    issuer.stop().await;
    println!(
        "native HTTP replay COMMIT ACK loss: proof burned, no effect or quota decrement, old proof denied, fresh explicitly signed proof succeeds"
    );
}
