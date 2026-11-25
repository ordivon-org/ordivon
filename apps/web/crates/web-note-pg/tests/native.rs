mod support;
use ordivon_web_note_pg::{
    Note, NoteError, NoteObservation, PgNoteStore, PoolLimits, PreparedNote,
};
use serde_json::{Value, json};
use std::{path::PathBuf, time::Duration};
use support::{counts, fixture, reset};
use tokio_postgres::Client;

// Test-only shorthand. Actual consumers must hold PreparedNote before await.
trait FixtureCreate {
    async fn create(&self, p: &str, c: &str, t: i64) -> Result<Note, NoteError>;
}
impl FixtureCreate for PgNoteStore {
    async fn create(&self, p: &str, c: &str, t: i64) -> Result<Note, NoteError> {
        self.execute(&PreparedNote::new(p, c, t)?).await
    }
}
async fn trigger(client: &Client, function: &str, definition: &str) {
    client.batch_execute(&format!("CREATE FUNCTION fault() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN {function} END; $$; {definition}")).await.unwrap();
}
fn normalized(note: &Note) -> Value {
    json!({"principalId":note.principal_id,"content":note.content,"state":note.state,"createdAt":note.created_at,"publishedAt":note.published_at})
}
async fn audit_projection(client: &Client, note: &Note) -> Value {
    let row=client.query_one("SELECT principal_id,event_type,object_type,object_id,detail_json,created_at FROM audit_events WHERE object_id=$1",&[&note.note_id]).await.unwrap();
    assert_eq!(row.get::<_, String>(3), note.note_id);
    json!({"principal":row.get::<_,String>(0),"event":row.get::<_,String>(1),"objectType":row.get::<_,String>(2),"detail":row.get::<_,String>(4),"at":row.get::<_,i64>(5)})
}
#[tokio::test]
async fn native_contract_and_differential() {
    let (store, peer) = fixture().await;
    reset(&peer).await;
    let tests = [
        (
            "note omitted",
            "RETURN NULL;",
            "CREATE TRIGGER fault_note BEFORE INSERT ON canary_notes FOR EACH ROW EXECUTE FUNCTION fault()",
            "note-write-not-applied",
        ),
        (
            "note mutated",
            "UPDATE canary_notes SET content='other' WHERE note_id=NEW.note_id; RETURN NEW;",
            "CREATE TRIGGER fault_note AFTER INSERT ON canary_notes FOR EACH ROW EXECUTE FUNCTION fault()",
            "note-business-mismatch",
        ),
        (
            "audit omitted",
            "RETURN NULL;",
            "CREATE TRIGGER fault_audit BEFORE INSERT ON audit_events FOR EACH ROW EXECUTE FUNCTION fault()",
            "note-write-not-applied",
        ),
        (
            "audit mutated",
            "UPDATE audit_events SET detail_json='[]' WHERE event_id=NEW.event_id; RETURN NEW;",
            "CREATE TRIGGER fault_audit AFTER INSERT ON audit_events FOR EACH ROW EXECUTE FUNCTION fault()",
            "note-audit-mismatch",
        ),
        (
            "audit duplicated",
            "IF pg_trigger_depth()=1 THEN INSERT INTO audit_events VALUES ('duplicate',NEW.principal_id,NEW.event_type,NEW.object_type,NEW.object_id,NEW.detail_json,NEW.created_at); END IF; RETURN NEW;",
            "CREATE TRIGGER fault_audit AFTER INSERT ON audit_events FOR EACH ROW EXECUTE FUNCTION fault()",
            "note-audit-mismatch",
        ),
        (
            "audit changes note",
            "UPDATE canary_notes SET content='other' WHERE note_id=NEW.object_id; RETURN NEW;",
            "CREATE TRIGGER fault_audit AFTER INSERT ON audit_events FOR EACH ROW EXECUTE FUNCTION fault()",
            "note-business-mismatch",
        ),
        (
            "audit aborts",
            "RAISE EXCEPTION 'audit failure';",
            "CREATE TRIGGER fault_audit BEFORE INSERT ON audit_events FOR EACH ROW EXECUTE FUNCTION fault()",
            "note-database-error",
        ),
        (
            "deferred audit changes note",
            "UPDATE canary_notes SET content='deferred mutation' WHERE note_id=NEW.object_id; RETURN NEW;",
            "CREATE CONSTRAINT TRIGGER fault_audit AFTER INSERT ON audit_events DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION fault()",
            "note-business-mismatch",
        ),
    ];
    for (name, body, definition, code) in tests {
        trigger(&peer, body, definition).await;
        let failure = store.create("p", "intended", 100).await.unwrap_err();
        assert_eq!(failure.code(), code, "{name}: {failure:?}");
        assert_eq!(counts(&peer).await, (0, 0), "{name}: no partial commit");
        peer.batch_execute("DROP FUNCTION fault() CASCADE")
            .await
            .unwrap();
        let note = store.create("p", "recovery", 101).await.unwrap();
        assert_eq!(store.list("p").await.unwrap(), vec![note.clone()]);
        assert_eq!(counts(&peer).await, (1, 1));
        assert_eq!(audit_projection(&peer, &note).await["detail"], "{}");
        peer.batch_execute("TRUNCATE canary_notes,audit_events")
            .await
            .unwrap();
        println!("native {name}: expected rejection, peer unchanged, fresh connection recovers");
    }
    assert!(matches!(
        store.create("p", "a\0b", 100).await,
        Err(NoteError::Unrepresentable)
    ));
    assert!(matches!(
        store.create("p", "unsafe time", i64::MAX).await,
        Err(NoteError::Unrepresentable)
    ));
    assert_eq!(counts(&peer).await, (0, 0));
    let missing = store
        .create("missing", "invalid fk", 100)
        .await
        .unwrap_err();
    match missing {
        NoteError::Database { phase, source } => {
            assert_eq!(phase, "write-note");
            assert_eq!(source.code().unwrap().code(), "23503");
        }
        other => panic!("{other:?}"),
    }
    assert_eq!(counts(&peer).await, (0, 0));
    let mut trace = Vec::new();
    for (p, content, now) in [
        ("p", "first", 100),
        ("q", "foreign", 102),
        ("p", "emoji 🦀 / 汉字 / \n", 103),
        ("p", "same clock", 103),
    ] {
        let note = store.create(p, content, now).await.unwrap();
        let list = store.list(p).await.unwrap();
        assert!(list.windows(2).all(|v| v[0].created_at > v[1].created_at
            || (v[0].created_at == v[1].created_at && v[0].note_id < v[1].note_id)));
        let mut list: Vec<_> = list.iter().map(normalized).collect();
        list.sort_by_key(|v| v["content"].as_str().unwrap().to_owned());
        trace.push(json!({"note":normalized(&note),"audit":audit_projection(&peer,&note).await,"list":list,"counts":counts(&peer).await}));
    }
    let reference = std::process::Command::new(std::env::var("WEB_NOTE_TEST_NODE").unwrap())
        .arg(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/tests/sqlite-reference.ts"
        ))
        .output()
        .unwrap();
    assert!(
        reference.status.success(),
        "{}",
        String::from_utf8_lossy(&reference.stderr)
    );
    assert_eq!(
        Value::Array(trace),
        serde_json::from_slice::<Value>(&reference.stdout).unwrap()
    );
    println!(
        "actual SQLite/PG domain trace: 4 exact normalized states/audits; UUID order checked independently"
    );
}

#[tokio::test]
async fn pool_saturation_and_precommit_cancellation() {
    let (store, peer) = fixture().await;
    reset(&peer).await;
    peer.batch_execute("SELECT pg_advisory_lock(681231)")
        .await
        .unwrap();
    trigger(&peer,"IF NEW.principal_id='p' THEN PERFORM pg_advisory_xact_lock(681231); END IF; RETURN NEW;",
        "CREATE TRIGGER fault_note BEFORE INSERT ON canary_notes FOR EACH ROW EXECUTE FUNCTION fault()").await;
    let op = PreparedNote::new("p", "blocked", 201).unwrap();
    let pstore = store.clone();
    let held = op.clone();
    let pending = tokio::spawn(async move { pstore.execute(&held).await });
    let mut blocked_pid = None;
    for _ in 0..100 {
        blocked_pid=peer.query_opt("SELECT pid FROM pg_stat_activity WHERE application_name='ordivon-web-note-candidate' AND wait_event='advisory'",&[]).await.unwrap().map(|r|r.get::<_,i32>(0));
        if blocked_pid.is_some() {
            break;
        }
        tokio::time::sleep(Duration::from_millis(20)).await;
    }
    let pid = blocked_pid.expect("native blocked transaction observed");
    let independent = tokio::time::timeout(
        Duration::from_secs(2),
        store.create("q", "independent", 202),
    )
    .await
    .unwrap()
    .unwrap();
    assert_eq!(counts(&peer).await, (1, 1));
    assert_eq!(store.list("q").await.unwrap(), vec![independent]);
    assert_eq!(
        store.observe(&op).await.unwrap(),
        NoteObservation::Unobserved
    );
    // Saturate the bounded pool with a second actual pending transaction.
    let second = PreparedNote::new("p", "also blocked", 202).unwrap();
    let second_store = store.clone();
    let held = second.clone();
    let pending2 = tokio::spawn(async move { second_store.execute(&held).await });
    let mut waiters = Vec::new();
    for _ in 0..100 {
        waiters=peer.query("SELECT pid FROM pg_stat_activity WHERE application_name='ordivon-web-note-candidate' AND wait_event='advisory'",&[]).await.unwrap().iter().map(|r|r.get::<_,i32>(0)).collect();
        if waiters.len() == 2 {
            break;
        }
        tokio::time::sleep(Duration::from_millis(20)).await;
    }
    assert_eq!(waiters.len(), 2);
    assert!(waiters.contains(&pid));
    assert!(matches!(
        store.list("q").await,
        Err(NoteError::Pool(deadpool_postgres::PoolError::Timeout(_)))
    ));
    pending.abort();
    pending2.abort();
    assert!(pending.await.unwrap_err().is_cancelled());
    assert!(pending2.await.unwrap_err().is_cancelled());
    peer.batch_execute("SELECT pg_advisory_unlock(681231)")
        .await
        .unwrap();
    let mut closed = false;
    for _ in 0..100 {
        closed = peer
            .query_one(
                "SELECT NOT EXISTS(SELECT 1 FROM pg_stat_activity WHERE pid=ANY($1))",
                &[&waiters],
            )
            .await
            .unwrap()
            .get(0);
        if closed {
            break;
        }
        tokio::time::sleep(Duration::from_millis(20)).await;
    }
    assert!(closed, "cancelled pooled carriers physically gone");
    assert_eq!(counts(&peer).await, (1, 1));
    assert_eq!(
        store.observe(&op).await.unwrap(),
        NoteObservation::Unobserved
    );
    assert_eq!(
        store.observe(&second).await.unwrap(),
        NoteObservation::Unobserved
    );
    assert!(store.list("p").await.unwrap().is_empty());
    println!(
        "bounded pool: independent commit, two native waiters, third checkout timeout, cancelled PIDs removed"
    );
    peer.batch_execute("DROP FUNCTION fault() CASCADE")
        .await
        .unwrap();
    store
        .create("p", "explicit later invocation", 203)
        .await
        .unwrap();
    assert_eq!(counts(&peer).await, (2, 2));
    println!(
        "actual disjoint commit during native lock wait; cancelled carrier gone, no partial state"
    );
}

#[tokio::test]
async fn commit_ack_loss_and_postcommit_cancellation() {
    let (store, peer) = fixture().await;
    // Real native COMMIT; the local wire fixture discards CommandComplete.
    reset(&peer).await;
    let proxy = PgNoteStore::local(
        &PathBuf::from(std::env::var_os("WEB_NOTE_TEST_ACK_PROXY").unwrap()),
        std::env::var("WEB_NOTE_TEST_PORT")
            .unwrap()
            .parse()
            .unwrap(),
        &std::env::var("WEB_NOTE_TEST_USER").unwrap(),
        "postgres",
    )
    .unwrap();
    let operation = PreparedNote::new("p", "committed but no acknowledgement", 301).unwrap();
    let outcome = proxy.execute(&operation).await.unwrap_err();
    let note_id = match outcome {
        NoteError::CommitUnknown { note_id, .. } => note_id,
        other => panic!("expected CommitUnknown, got {other:?}"),
    };
    assert_eq!(note_id, operation.note_id());
    let restored = PreparedNote::restore(
        uuid::Uuid::parse_str(operation.note_id()).unwrap(),
        uuid::Uuid::parse_str(operation.event_id()).unwrap(),
        "p",
        "committed but no acknowledgement",
        301,
    )
    .unwrap();
    assert_eq!(restored, operation);
    let observed = store.observe(&restored).await.unwrap();
    assert!(matches!(observed,NoteObservation::Exact(ref n) if n.note_id==note_id));
    // Explicit duplicate operation is rejected by the primary key, not replayed.
    assert!(
        matches!(store.execute(&restored).await,Err(NoteError::Database{ref source,..}) if source.code().unwrap().code()=="23505")
    );
    let changed = PreparedNote::restore(
        uuid::Uuid::parse_str(operation.note_id()).unwrap(),
        uuid::Uuid::parse_str(operation.event_id()).unwrap(),
        "q",
        "different intent",
        301,
    )
    .unwrap();
    assert_eq!(
        store.observe(&changed).await.unwrap(),
        NoteObservation::Mismatch
    );
    let different_event = PreparedNote::restore(
        uuid::Uuid::parse_str(operation.note_id()).unwrap(),
        uuid::Uuid::new_v4(),
        "p",
        "committed but no acknowledgement",
        301,
    )
    .unwrap();
    assert_eq!(
        store.observe(&different_event).await.unwrap(),
        NoteObservation::Mismatch
    );
    let duplicate_audit = PreparedNote::restore(
        uuid::Uuid::new_v4(),
        uuid::Uuid::parse_str(operation.event_id()).unwrap(),
        "p",
        "new note same audit ID",
        302,
    )
    .unwrap();
    assert!(
        matches!(store.execute(&duplicate_audit).await,Err(NoteError::Database{ref source,..}) if source.code().unwrap().code()=="23505")
    );
    assert_eq!(
        store.observe(&duplicate_audit).await.unwrap(),
        NoteObservation::Mismatch
    );
    let notes = store.list("p").await.unwrap();
    assert_eq!(notes.len(), 1);
    assert_eq!(notes[0].note_id, note_id);
    assert_eq!(notes[0].content, "committed but no acknowledgement");
    assert_eq!(counts(&peer).await, (1, 1));
    assert_eq!(audit_projection(&peer, &notes[0]).await["detail"], "{}");
    println!(
        "native COMMIT CommandComplete lost: UNKNOWN + independent exact committed Note/Audit, no reissue"
    );

    peer.batch_execute("UPDATE canary_notes SET state='PUBLISHED',published_at=302")
        .await
        .unwrap();
    let published = store.list("p").await.unwrap();
    assert_eq!(
        published[0].state,
        ordivon_web_note_pg::NoteState::Published
    );
    assert_eq!(published[0].published_at, Some(302));
    assert_eq!(
        store.observe(&operation).await.unwrap(),
        NoteObservation::Mismatch
    );
    peer.batch_execute("UPDATE canary_notes SET published_at=9223372036854775807")
        .await
        .unwrap();
    assert!(matches!(
        store.list("p").await,
        Err(NoteError::BusinessMismatch)
    ));
    println!("imported PUBLISHED state exact; unrepresentable historical timestamp rejected");

    reset(&peer).await;
    let socket = PathBuf::from(std::env::var_os("WEB_NOTE_TEST_CANCEL_PROXY").unwrap());
    let cancel_store = PgNoteStore::local(
        &socket,
        std::env::var("WEB_NOTE_TEST_PORT")
            .unwrap()
            .parse()
            .unwrap(),
        &std::env::var("WEB_NOTE_TEST_USER").unwrap(),
        "postgres",
    )
    .unwrap();
    let operation = PreparedNote::new("p", "committed before caller cancellation", 350).unwrap();
    let held = operation.clone();
    let task_store = cancel_store.clone();
    let prior_pids: Vec<i32> = peer
        .query(
            "SELECT pid FROM pg_stat_activity WHERE application_name='ordivon-web-note-candidate'",
            &[],
        )
        .await
        .unwrap()
        .iter()
        .map(|r| r.get(0))
        .collect();
    let pending = tokio::spawn(async move { task_store.execute(&held).await });
    let mut reached = false;
    for _ in 0..100 {
        reached = socket.join("commit-reached").exists();
        if reached {
            break;
        }
        tokio::time::sleep(Duration::from_millis(20)).await;
    }
    assert!(reached, "real COMMIT reached before cancelling caller");
    let committed_pid=peer.query_one("SELECT pid FROM pg_stat_activity WHERE application_name='ordivon-web-note-candidate' AND NOT(pid=ANY($1))",&[&prior_pids]).await.unwrap().get::<_,i32>(0);
    assert!(!pending.is_finished());
    pending.abort();
    assert!(pending.await.unwrap_err().is_cancelled());
    let mut gone = false;
    for _ in 0..100 {
        gone = peer
            .query_one(
                "SELECT NOT EXISTS(SELECT 1 FROM pg_stat_activity WHERE pid=$1)",
                &[&committed_pid],
            )
            .await
            .unwrap()
            .get(0);
        if gone {
            break;
        }
        tokio::time::sleep(Duration::from_millis(20)).await;
    }
    assert!(
        gone,
        "cancelled COMMIT carrier physically gone while pool retained"
    );
    assert!(
        matches!(store.observe(&operation).await.unwrap(),NoteObservation::Exact(ref n) if n.note_id==operation.note_id())
    );
    assert_eq!(counts(&peer).await, (1, 1));
    drop(cancel_store);
    println!(
        "real COMMIT acknowledged by server but held on wire: caller cancelled, retained operation recovers exact committed pair"
    );
    drop(proxy);
    drop(store);
}

#[tokio::test]
async fn pool_reuse_clean_reset_and_reconnect() {
    let (store, peer) = fixture().await;
    drop(store);
    let socket = PathBuf::from(std::env::var_os("WEB_NOTE_TEST_SOCKET").unwrap());
    let user = std::env::var("WEB_NOTE_TEST_USER").unwrap();
    let port = std::env::var("WEB_NOTE_TEST_PORT")
        .unwrap()
        .parse()
        .unwrap();
    let new_store = || {
        PgNoteStore::local_bounded(
            &socket,
            port,
            &user,
            "postgres",
            PoolLimits {
                max_size: 1,
                wait: Duration::from_secs(1),
            },
        )
        .unwrap()
    };
    let mut gone = false;
    for _ in 0..100 {
        gone=peer.query_one("SELECT NOT EXISTS(SELECT 1 FROM pg_stat_activity WHERE application_name='ordivon-web-note-candidate')",&[]).await.unwrap().get(0);
        if gone {
            break;
        }
        tokio::time::sleep(Duration::from_millis(20)).await;
    }
    assert!(gone, "prior pools physically retired");
    reset(&peer).await;
    let store = new_store();
    let op = PreparedNote::new("p", "pool witness", 401).unwrap();
    assert_eq!(
        store.observe(&op).await.unwrap(),
        NoteObservation::Unobserved
    );
    let pid = peer
        .query_one(
            "SELECT pid FROM pg_stat_activity WHERE application_name='ordivon-web-note-candidate'",
            &[],
        )
        .await
        .unwrap()
        .get::<_, i32>(0);
    trigger(&peer,"PERFORM set_config('work_mem','64kB',false); RETURN NEW;",
      "CREATE TRIGGER fault_note BEFORE INSERT ON canary_notes FOR EACH ROW EXECUTE FUNCTION fault()").await;
    let note = store.execute(&op).await.unwrap();
    peer.batch_execute("DROP FUNCTION fault() CASCADE")
        .await
        .unwrap();
    trigger(&peer,"IF current_setting('work_mem')='64kB' THEN RAISE EXCEPTION 'leaked session setting'; END IF; RETURN NEW;",
      "CREATE TRIGGER fault_note BEFORE INSERT ON canary_notes FOR EACH ROW EXECUTE FUNCTION fault()").await;
    store
        .create("p", "clean reused carrier", 402)
        .await
        .unwrap();
    assert_eq!(
        peer.query_one(
            "SELECT pid FROM pg_stat_activity WHERE application_name='ordivon-web-note-candidate'",
            &[]
        )
        .await
        .unwrap()
        .get::<_, i32>(0),
        pid
    );
    assert_eq!(
        store.observe(&op).await.unwrap(),
        NoteObservation::Exact(note)
    );
    peer.batch_execute("DROP FUNCTION fault() CASCADE")
        .await
        .unwrap();
    assert!(
        peer.query_one("SELECT pg_terminate_backend($1)", &[&pid])
            .await
            .unwrap()
            .get::<_, bool>(0)
    );
    let mut dead = false;
    for _ in 0..100 {
        dead = peer
            .query_one(
                "SELECT NOT EXISTS(SELECT 1 FROM pg_stat_activity WHERE pid=$1)",
                &[&pid],
            )
            .await
            .unwrap()
            .get(0);
        if dead {
            break;
        }
        tokio::time::sleep(Duration::from_millis(20)).await;
    }
    assert!(dead);
    assert_eq!(store.list("p").await.unwrap().len(), 2);
    let replacement = peer
        .query_one(
            "SELECT pid FROM pg_stat_activity WHERE application_name='ordivon-web-note-candidate'",
            &[],
        )
        .await
        .unwrap()
        .get::<_, i32>(0);
    assert_ne!(replacement, pid);
    println!(
        "real pool reuse same PID, Clean reset of session setting, terminated backend replaced"
    );
    // Read-only observation must distinguish inconsistent historical evidence.
    let orphan = PreparedNote::new("p", "orphan", 403).unwrap();
    peer.execute(
        "INSERT INTO audit_events VALUES ($1,'p','canary.note.created','canary-note',$2,'{}',403)",
        &[&orphan.event_id(), &orphan.note_id()],
    )
    .await
    .unwrap();
    assert_eq!(
        store.observe(&orphan).await.unwrap(),
        NoteObservation::Mismatch
    );
    peer.execute(
        "DELETE FROM audit_events WHERE event_id=$1",
        &[&orphan.event_id()],
    )
    .await
    .unwrap();
    assert_eq!(
        store.observe(&orphan).await.unwrap(),
        NoteObservation::Unobserved
    );

    assert_eq!(counts(&peer).await, (2, 2));
}
