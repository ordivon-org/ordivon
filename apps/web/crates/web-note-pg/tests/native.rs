mod support;
use ordivon_web_note_pg::{Note, NoteError, PgNoteStore};
use serde_json::{Value, json};
use std::{path::PathBuf, time::Duration};
use tokio_postgres::{Client, Config, NoTls};

async fn fixture() -> (PgNoteStore, Client) {
    let socket =
        PathBuf::from(std::env::var_os("WEB_NOTE_TEST_SOCKET").expect("isolated fixture socket"));
    let user = std::env::var("WEB_NOTE_TEST_USER").unwrap();
    let port: u16 = std::env::var("WEB_NOTE_TEST_PORT")
        .unwrap()
        .parse()
        .unwrap();
    let mut config = Config::new();
    config
        .host_path(&socket)
        .port(port)
        .user(&user)
        .dbname("postgres");
    let (client, conn) = config.connect(NoTls).await.unwrap();
    tokio::spawn(async move {
        conn.await.unwrap();
    });
    // Destructive fixture DDL must never target a live owner database.
    assert!(
        socket
            .file_name()
            .unwrap()
            .to_string_lossy()
            .starts_with("ordivon-web-pg-")
    );
    let actual: String = client
        .query_one("SHOW data_directory", &[])
        .await
        .unwrap()
        .get(0);
    assert_eq!(
        std::fs::canonicalize(actual).unwrap(),
        std::fs::canonicalize(socket.join("data")).unwrap()
    );
    let listen: String = client
        .query_one("SHOW listen_addresses", &[])
        .await
        .unwrap()
        .get(0);
    assert_eq!(listen, "");
    let marker: String = client
        .query_one("SELECT token FROM web_note_fixture_guard", &[])
        .await
        .unwrap()
        .get(0);
    assert_eq!(marker, std::env::var("WEB_NOTE_TEST_GUARD").unwrap());
    let store = PgNoteStore::local(&socket, port, &user, "postgres").unwrap();
    (store, client)
}
async fn counts(client: &Client) -> (i64, i64) {
    let row = client
        .query_one(
            "SELECT (SELECT count(*) FROM canary_notes),(SELECT count(*) FROM audit_events)",
            &[],
        )
        .await
        .unwrap();
    (row.get(0), row.get(1))
}
async fn reset(client: &Client) {
    client.batch_execute("DROP TABLE IF EXISTS canary_notes,audit_events,principals CASCADE; DROP FUNCTION IF EXISTS fault() CASCADE;").await.unwrap();
    client.batch_execute(support::SCHEMA).await.unwrap();
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
    reset(&peer).await;
    peer.batch_execute("SELECT pg_advisory_lock(681231)")
        .await
        .unwrap();
    trigger(&peer,"IF NEW.principal_id='p' THEN PERFORM pg_advisory_xact_lock(681231); END IF; RETURN NEW;",
        "CREATE TRIGGER fault_note BEFORE INSERT ON canary_notes FOR EACH ROW EXECUTE FUNCTION fault()").await;
    let pstore = store.clone();
    let pending = tokio::spawn(async move { pstore.create("p", "blocked", 201).await });
    let mut blocked = false;
    for _ in 0..100 {
        blocked=peer.query_one("SELECT EXISTS(SELECT 1 FROM pg_stat_activity WHERE application_name='ordivon-web-note-candidate' AND wait_event='advisory')",&[]).await.unwrap().get(0);
        if blocked {
            break;
        }
        tokio::time::sleep(Duration::from_millis(20)).await;
    }
    assert!(blocked, "native blocked transaction observed");
    let independent = tokio::time::timeout(
        Duration::from_secs(2),
        store.create("q", "independent", 202),
    )
    .await
    .unwrap()
    .unwrap();
    assert_eq!(counts(&peer).await, (1, 1));
    assert_eq!(store.list("q").await.unwrap(), vec![independent]);
    pending.abort();
    assert!(pending.await.unwrap_err().is_cancelled());
    peer.batch_execute("SELECT pg_advisory_unlock(681231)")
        .await
        .unwrap();
    let mut closed = false;
    for _ in 0..100 {
        closed=peer.query_one("SELECT NOT EXISTS(SELECT 1 FROM pg_stat_activity WHERE application_name='ordivon-web-note-candidate')",&[]).await.unwrap().get(0);
        if closed {
            break;
        }
        tokio::time::sleep(Duration::from_millis(20)).await;
    }
    assert!(closed, "cancelled connection physically gone");
    assert_eq!(counts(&peer).await, (1, 1));
    assert!(store.list("p").await.unwrap().is_empty());
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
    let outcome = proxy
        .create("p", "committed but no acknowledgement", 301)
        .await
        .unwrap_err();
    let note_id = match outcome {
        NoteError::CommitUnknown { note_id, .. } => note_id,
        other => panic!("expected CommitUnknown, got {other:?}"),
    };
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
    peer.batch_execute("UPDATE canary_notes SET published_at=9223372036854775807")
        .await
        .unwrap();
    assert!(matches!(
        store.list("p").await,
        Err(NoteError::BusinessMismatch)
    ));
    println!("imported PUBLISHED state exact; unrepresentable historical timestamp rejected");
}
