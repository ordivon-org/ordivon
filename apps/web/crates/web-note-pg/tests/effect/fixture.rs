use super::support;
use ordivon_web_note_pg::{
    PgNoteStore, PoolLimits,
    effect::{EffectOperation, EffectRequest, GrantFence},
    migration::{Snapshot, import_initial},
};
use serde_json::{Value, json};
use tokio_postgres::{Client, Config, NoTls};
use uuid::Uuid;
pub(super) const NOW: i64 = 100;
pub(super) fn request(id: &str, publish: bool, note: Uuid) -> EffectRequest {
    let action = if publish {
        "canary.note.publish"
    } else {
        "canary.note.create"
    };
    EffectRequest {
        effect_id: id.into(),
        effect_digest: format!("digest-{id}"),
        agent_id: "agent".into(),
        audience: "web".into(),
        action: action.into(),
        resource: if publish {
            format!("/canary/notes/{note}")
        } else {
            "/canary/notes".into()
        },
        effect_type: format!("website.{action}"),
    }
}
pub(super) fn grant(id: &str, revision: i64) -> GrantFence {
    GrantFence {
        grant_id: id.into(),
        grant_digest: format!("digest-{id}"),
        principal_id: "p".into(),
        agent_id: "agent".into(),
        revision,
    }
}
pub(super) fn create(id: Uuid, content: &str) -> EffectOperation {
    EffectOperation::Create {
        note_id: id,
        content: content.into(),
    }
}
pub(super) fn reference() -> Value {
    let out = std::process::Command::new(std::env::var("WEB_NOTE_TEST_NODE").unwrap())
        .arg(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/tests/effect-reference.ts"
        ))
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "{}",
        String::from_utf8_lossy(&out.stderr)
    );
    serde_json::from_slice(&out.stdout).unwrap()
}
pub(super) async fn setup(name: &str) -> (PgNoteStore, Client) {
    let (_store, admin) = support::fixture().await;
    support::reset(&admin).await;
    assert_eq!(support::counts(&admin).await, (0, 0));
    admin
        .batch_execute(&format!("CREATE DATABASE {name} TEMPLATE template0"))
        .await
        .unwrap();
    let socket = std::path::PathBuf::from(std::env::var_os("WEB_NOTE_TEST_SOCKET").unwrap());
    let user = std::env::var("WEB_NOTE_TEST_USER").unwrap();
    let port = std::env::var("WEB_NOTE_TEST_PORT")
        .unwrap()
        .parse()
        .unwrap();
    let (mut client, driver) = Config::new()
        .host_path(&socket)
        .user(&user)
        .port(port)
        .dbname(name)
        .connect(NoTls)
        .await
        .unwrap();
    tokio::spawn(async move { driver.await.unwrap() });
    let snapshot: Snapshot = serde_json::from_value(reference()["source"].clone()).unwrap();
    import_initial(&mut client, "public", &snapshot)
        .await
        .unwrap();
    client
        .batch_execute(ordivon_web_note_pg::migration::LOGIN_COMPLETION_SCHEMA_V2)
        .await
        .unwrap();
    (
        PgNoteStore::local_bounded(
            &socket,
            port,
            &user,
            name,
            PoolLimits {
                max_size: 2,
                wait: std::time::Duration::from_millis(250),
            },
        )
        .unwrap(),
        client,
    )
}
pub(super) async fn state(p: &Client) -> Value {
    let grants = p
        .query(
            "SELECT grant_id,remaining_effects,revision,active FROM agent_grants ORDER BY grant_id",
            &[],
        )
        .await
        .unwrap()
        .iter()
        .map(|r| {
            json!([
                r.get::<_, String>(0),
                r.get::<_, i64>(1),
                r.get::<_, i64>(2),
                r.get::<_, i64>(3)
            ])
        })
        .collect::<Vec<_>>();
    let notes=p.query("SELECT principal_id,content,state,created_at,published_at FROM canary_notes ORDER BY content",&[]).await.unwrap().iter().map(|r|json!([r.get::<_,String>(0),r.get::<_,String>(1),r.get::<_,String>(2),r.get::<_,i64>(3),r.get::<_,Option<i64>>(4)])).collect::<Vec<_>>();
    let approvals = p
        .query(
            "SELECT effect_id,consumed_at FROM effect_approvals ORDER BY effect_id",
            &[],
        )
        .await
        .unwrap()
        .iter()
        .map(|r| json!([r.get::<_, String>(0), r.get::<_, Option<i64>>(1)]))
        .collect::<Vec<_>>();
    let receipts=p.query("SELECT effect_id,effect_digest,principal_id,agent_id,grant_id,action,committed_at,result_json FROM agent_effects ORDER BY effect_id",&[]).await.unwrap().iter().map(|r|{
        let mut result:Value=serde_json::from_str(&r.get::<_,String>(7)).unwrap();
        result["note"].as_object_mut().unwrap().remove("noteId");
        json!([r.get::<_,String>(0),r.get::<_,String>(1),r.get::<_,String>(2),r.get::<_,String>(3),r.get::<_,String>(4),r.get::<_,String>(5),r.get::<_,i64>(6),result])
    }).collect::<Vec<_>>();
    let audits=p.query("SELECT principal_id,event_type,object_type,object_id,detail_json,created_at FROM audit_events ORDER BY object_id",&[]).await.unwrap().iter().map(|r|json!([r.get::<_,Option<String>>(0),r.get::<_,String>(1),r.get::<_,Option<String>>(2),r.get::<_,Option<String>>(3),r.get::<_,String>(4),r.get::<_,i64>(5)])).collect::<Vec<_>>();
    json!({ "grants":grants,"notes":notes,"approvals":approvals,"receipts":receipts,"audits":audits})
}
