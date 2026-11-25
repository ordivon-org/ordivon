use super::fixture::{NOW, create, grant, reference, request, setup, state};
use ordivon_web_note_pg::{
    PgNoteStore,
    effect::{EffectError, EffectOperation},
};
use serde_json::json;
use uuid::Uuid;
#[tokio::test]
async fn actual_create_publish_sqlite_differential() {
    let (store, peer) = setup("effect_diff").await;
    let id = Uuid::from_u128(1);
    let mut observed = Vec::new();
    for (e, g, rev, publish, agent, digest) in [
        ("E", "g1", 1, false, "agent", "digest-E"),
        ("E", "g2", 1, false, "agent", "digest-E"),
        ("E", "g2", 1, false, "agent", "different"),
        ("E", "g2", 1, false, "other", "digest-E"),
        ("F", "g1", 1, false, "agent", "digest-F"),
        ("P", "g1", 2, true, "agent", "digest-P"),
        ("P", "g1", 1, true, "agent", "digest-P"),
        ("X", "g2", 1, true, "agent", "digest-X"),
        ("N", "g2", 1, true, "agent", "digest-N"),
        ("X", "g2", 1, true, "other", "different"),
        ("G", "g2", 1, false, "agent", "digest-G"),
    ] {
        let mut r = request(e, publish, id);
        r.agent_id = agent.into();
        r.effect_digest = digest.into();
        let op = if publish {
            EffectOperation::Publish {
                note_id: id.to_string(),
            }
        } else if e == "G" {
            create(Uuid::from_u128(2), "second")
        } else {
            create(id, "draft 🦀")
        };
        let outcome = match store
            .commit_effect(&grant(g, rev), &r, &op, Uuid::new_v4(), NOW)
            .await
        {
            Ok(v) => {
                assert_eq!(
                    store.observe_effect(&r).await.unwrap(),
                    Some(v.receipt.clone())
                );
                if v.replayed { "replay" } else { "new" }
            }
            Err(e) => e.code(),
        };
        observed.push(json!({"outcome":outcome,"state":state(&peer).await}));
    }
    assert_eq!(json!(observed), reference()["observed"]);
    println!("11 actual SQLite/Rust PG outcomes and five independent state projections match");
}
#[tokio::test]
async fn native_effect_postconditions_rollback() {
    let (store, peer) = setup("effect_faults").await;
    let id = Uuid::from_u128(5);
    let e = request("E", false, id);
    let op = create(id, "fault");
    let prior = state(&peer).await;
    for (table, event, body) in [
        ("canary_notes", "INSERT", "RETURN NULL;"),
        (
            "agent_grants",
            "UPDATE",
            "NEW.remaining_effects=OLD.remaining_effects; RETURN NEW;",
        ),
        (
            "agent_effects",
            "INSERT",
            "NEW.result_json='{}'; RETURN NEW;",
        ),
        (
            "audit_events",
            "INSERT",
            "NEW.detail_json='[]'; RETURN NEW;",
        ),
        (
            "audit_events",
            "INSERT",
            "UPDATE canary_notes SET content='changed'; RETURN NEW;",
        ),
    ] {
        peer.batch_execute(&format!("CREATE FUNCTION fault() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN {body} END; $$; CREATE TRIGGER fault BEFORE {event} ON {table} FOR EACH ROW EXECUTE FUNCTION fault()")).await.unwrap();
        let result = store
            .commit_effect(&grant("g1", 1), &e, &op, Uuid::new_v4(), NOW)
            .await;
        assert!(
            matches!(
                result,
                Err(EffectError::Write(_) | EffectError::Mismatch(_))
            ),
            "{table}: {result:?}"
        );
        assert_eq!(state(&peer).await, prior);
        peer.batch_execute("DROP FUNCTION fault() CASCADE")
            .await
            .unwrap();
    }
    assert!(
        !store
            .commit_effect(&grant("g1", 1), &e, &op, Uuid::new_v4(), NOW)
            .await
            .unwrap()
            .replayed
    );
    let p = request("P", true, id);
    let publish = EffectOperation::Publish {
        note_id: id.to_string(),
    };
    let before = state(&peer).await;
    for (table, event, body) in [
        (
            "effect_approvals",
            "UPDATE",
            "NEW.consumed_at=NULL; RETURN NEW;",
        ),
        (
            "audit_events",
            "INSERT",
            "UPDATE effect_approvals SET consumed_at=NULL WHERE effect_id='P'; RETURN NEW;",
        ),
    ] {
        peer.batch_execute(&format!("CREATE FUNCTION fault() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN {body} END; $$; CREATE TRIGGER fault BEFORE {event} ON {table} FOR EACH ROW EXECUTE FUNCTION fault()")).await.unwrap();
        assert!(matches!(
            store
                .commit_effect(&grant("g1", 2), &p, &publish, Uuid::new_v4(), NOW)
                .await,
            Err(EffectError::Mismatch(_))
        ));
        assert_eq!(state(&peer).await, before);
        peer.batch_execute("DROP FUNCTION fault() CASCADE")
            .await
            .unwrap();
    }
    peer.batch_execute("CREATE FUNCTION fault() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN UPDATE canary_notes SET content='deferred'; RETURN NEW; END; $$; CREATE CONSTRAINT TRIGGER fault AFTER INSERT ON audit_events DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION fault()").await.unwrap();
    assert!(matches!(
        store
            .commit_effect(&grant("g1", 2), &p, &publish, Uuid::new_v4(), NOW)
            .await,
        Err(EffectError::Mismatch("note"))
    ));
    assert_eq!(state(&peer).await, before);
    peer.batch_execute("DROP FUNCTION fault() CASCADE")
        .await
        .unwrap();
    assert!(
        !store
            .commit_effect(&grant("g1", 2), &p, &publish, Uuid::new_v4(), NOW)
            .await
            .unwrap()
            .replayed
    );
    println!(
        "8 actual native trigger faults rejected; complete independent state unchanged, then recovery"
    );
}

#[tokio::test]
async fn effect_commit_ack_loss_is_observable() {
    let (store, peer) = setup("effect_ack").await;
    let socket = std::path::PathBuf::from(std::env::var_os("WEB_EFFECT_TEST_ACK_PROXY").unwrap());
    let proxy = PgNoteStore::local(
        &socket,
        std::env::var("WEB_NOTE_TEST_PORT")
            .unwrap()
            .parse()
            .unwrap(),
        &std::env::var("WEB_NOTE_TEST_USER").unwrap(),
        "effect_ack",
    )
    .unwrap();
    let note = Uuid::from_u128(6);
    let request = request("E", false, note);
    let op = create(note, "ack");
    let audit = Uuid::new_v4();
    let result = proxy
        .commit_effect(&grant("g1", 1), &request, &op, audit, NOW)
        .await;
    assert!(
        matches!(result,Err(EffectError::CommitUnknown{ref effect_id,..}) if effect_id=="E"),
        "{result:?}"
    );
    let receipt = store.observe_effect(&request).await.unwrap().unwrap();
    assert_eq!(receipt.effect_id, "E");
    assert_eq!(
        peer.query_one(
            "SELECT count(*) FROM audit_events WHERE event_id=$1 AND object_id='E'",
            &[&audit.to_string()]
        )
        .await
        .unwrap()
        .get::<_, i64>(0),
        1
    );
    assert_eq!(
        peer.query_one(
            "SELECT remaining_effects FROM agent_grants WHERE grant_id='g1'",
            &[]
        )
        .await
        .unwrap()
        .get::<_, i64>(0),
        2
    );
    let replay = store
        .commit_effect(&grant("g1", 1), &request, &op, audit, NOW)
        .await
        .unwrap();
    assert!(replay.replayed);
    assert_eq!(replay.receipt, receipt);
    assert_eq!(
        peer.query_one("SELECT count(*) FROM agent_effects", &[])
            .await
            .unwrap()
            .get::<_, i64>(0),
        1
    );
    println!(
        "real native COMMIT ACK loss: UNKNOWN, retained identity observes exact receipt, explicit replay has no extra effect"
    );
}
