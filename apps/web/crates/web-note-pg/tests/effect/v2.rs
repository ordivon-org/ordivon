use super::{fixture::setup, support};
use ordivon_web_note_pg::{
    OwnerError, PgNoteStore,
    identity::{ChallengePurpose, LoginObservation, PreparedChallenge, PreparedSession},
    maintenance::ReplayMaintenance,
    migration::{Cell, ImportError, export_v2, import_v2},
};
use tokio_postgres::{Client, Config, NoTls};

async fn database(name: &str) -> Client {
    let (client, conn) = Config::new()
        .host_path(std::path::PathBuf::from(
            std::env::var_os("WEB_NOTE_TEST_SOCKET").unwrap(),
        ))
        .port(
            std::env::var("WEB_NOTE_TEST_PORT")
                .unwrap()
                .parse()
                .unwrap(),
        )
        .user(std::env::var("WEB_NOTE_TEST_USER").unwrap())
        .dbname(name)
        .connect(NoTls)
        .await
        .unwrap();
    tokio::spawn(async move { conn.await.unwrap() });
    client
}
fn native_store(name: &str) -> PgNoteStore {
    PgNoteStore::local(
        &std::path::PathBuf::from(std::env::var_os("WEB_NOTE_TEST_SOCKET").unwrap()),
        std::env::var("WEB_NOTE_TEST_PORT")
            .unwrap()
            .parse()
            .unwrap(),
        &std::env::var("WEB_NOTE_TEST_USER").unwrap(),
        name,
    )
    .unwrap()
}
#[tokio::test]
async fn native_v2_exact_restore_terminal_consumer() {
    let (store, mut src) = setup("owner_v2_source").await;
    let challenge =
        PreparedChallenge::new(ChallengePurpose::Login, "p", "login", "{}".into(), 100, 20)
            .unwrap();
    store.issue_challenge(&challenge).await.unwrap();
    let c = store
        .consume_challenge(
            &challenge.record().challenge_id,
            ChallengePurpose::Login,
            "p",
            101,
        )
        .await
        .unwrap();
    let prior = store.get_active_credential("credential").await.unwrap();
    let s = PreparedSession::new("p", 101, 20, 50, None).unwrap();
    store
        .complete_verified_login(&c, 101, &prior, 0, &s)
        .await
        .unwrap();
    let pending = PreparedChallenge::new(
        ChallengePurpose::Login,
        "p",
        "pending",
        "{}".into(),
        100,
        20,
    )
    .unwrap();
    store.issue_challenge(&pending).await.unwrap();
    let snapshot = export_v2(&mut src, "public").await.unwrap();
    assert_eq!(snapshot.len(), 12);
    assert_eq!(snapshot["webauthn_login_completions"].rows.len(), 2);
    assert!(matches!(
        export_v2(&mut src, "wrong").await,
        Err(ImportError::Invalid(_))
    ));
    src.batch_execute("CREATE TABLE unexpected_v3(id TEXT)")
        .await
        .unwrap();
    assert!(matches!(
        export_v2(&mut src, "public").await,
        Err(ImportError::Invalid(_))
    ));
    src.batch_execute("DROP TABLE unexpected_v3").await.unwrap();
    let (_, admin) = support::fixture().await;
    admin
        .batch_execute("CREATE DATABASE owner_v2_restore TEMPLATE template0;")
        .await
        .unwrap();
    let mut dst = database("owner_v2_restore").await;
    let mut missing = snapshot.clone();
    missing.remove("webauthn_login_completions");
    assert!(matches!(
        import_v2(&mut dst, "public", &missing).await,
        Err(ImportError::Invalid(_))
    ));
    let mut bad = snapshot.clone();
    let row = bad
        .get_mut("webauthn_login_completions")
        .unwrap()
        .rows
        .iter_mut()
        .find(|r| r[1] != Cell::Null)
        .unwrap();
    row[2] = Cell::Integer(102); // FK valid but time binding invalid
    assert!(matches!(
        import_v2(&mut dst, "public", &bad).await,
        Err(ImportError::Invalid(_))
    ));
    let count:i64=dst.query_one("SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public'",&[]).await.unwrap().get(0);
    assert_eq!(count, 0);
    import_v2(&mut dst, "public", &snapshot).await.unwrap();
    assert_eq!(export_v2(&mut dst, "public").await.unwrap(), snapshot);
    assert!(matches!(
        import_v2(&mut dst, "public", &snapshot).await,
        Err(ImportError::Invalid(_))
    ));
    let restored = native_store("owner_v2_restore");
    assert!(matches!(
        restored
            .observe_verified_login(&c, 101, &prior, 0, &s)
            .await
            .unwrap(),
        LoginObservation::Exact(_)
    ));
    let other = PreparedSession::new("p", 101, 20, 50, None).unwrap();
    assert!(matches!(
        restored
            .complete_verified_login(&c, 101, &prior, 0, &other)
            .await,
        Err(OwnerError::LoginCompleted)
    ));
    assert!(
        restored
            .authenticate_session(s.token(), 102, 20)
            .await
            .is_ok()
    );
    let p = restored
        .consume_challenge(
            &pending.record().challenge_id,
            ChallengePurpose::Login,
            "p",
            103,
        )
        .await
        .unwrap();
    let current = restored.get_active_credential("credential").await.unwrap();
    let new = PreparedSession::new("p", 103, 20, 50, None).unwrap();
    assert!(
        restored
            .complete_verified_login(&p, 103, &current, 0, &new)
            .await
            .is_ok()
    );
    println!(
        "V2 12-table typed exact restore, no omitted table, malformed cross-time binding rollback, completed login terminal, pending login eligible, real session consumer"
    );
}
#[tokio::test]
async fn native_bounded_maintenance_consumer() {
    let (store, mut peer) = setup("owner_maintenance").await;
    for i in 0..7 {
        store
            .consume_dpop_proof(&format!("expired-{i}"), 100, 10)
            .await
            .unwrap()
    }
    store.consume_dpop_proof("live", 100, 100).await.unwrap();
    let runner = ReplayMaintenance::new(2, 2).unwrap();
    let report = runner.run_once(&store, 110).await.unwrap();
    assert_eq!(
        (report.deleted, report.batches, report.short_batch),
        (4, 2, false)
    );
    let tx = peer.transaction().await.unwrap();
    tx.query(
        "SELECT * FROM dpop_proofs WHERE expires_at=110 FOR UPDATE",
        &[],
    )
    .await
    .unwrap();
    let report = runner.run_once(&store, 110).await.unwrap();
    assert_eq!(
        (report.deleted, report.batches, report.short_batch),
        (0, 1, true)
    );
    tx.rollback().await.unwrap();
    let report = runner.run_once(&store, 110).await.unwrap();
    assert_eq!(
        (report.deleted, report.batches, report.short_batch),
        (3, 2, true)
    );
    assert!(matches!(
        store.consume_dpop_proof("live", 110, 10).await,
        Err(OwnerError::DpopReplayed)
    ));
    assert_eq!(
        peer.query_one("SELECT count(*) FROM dpop_proofs", &[])
            .await
            .unwrap()
            .get::<_, i64>(0),
        1
    );
    assert!(ReplayMaintenance::new(0, 1).is_err());
    assert!(ReplayMaintenance::new(1, 101).is_err());
    println!(
        "real bounded multi-batch maintenance consumer: cap, short locked batch not proof of absence, live replay retained"
    );
}

#[tokio::test]
async fn native_maintenance_process_consumer() {
    let (store, peer) = setup("owner_maintenance_process").await;
    for i in 0..3 {
        store
            .consume_dpop_proof(&format!("old-{i}"), 100, 10)
            .await
            .unwrap();
    }
    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_secs() as i64;
    store.consume_dpop_proof("current", now, 600).await.unwrap();
    let output = std::process::Command::new(env!("CARGO_BIN_EXE_web-replay-maintenance"))
        .args([
            std::env::var("WEB_NOTE_TEST_SOCKET").unwrap(),
            std::env::var("WEB_NOTE_TEST_PORT").unwrap(),
            std::env::var("WEB_NOTE_TEST_USER").unwrap(),
            "owner_maintenance_process".into(),
            "2".into(),
            "2".into(),
        ])
        .output()
        .unwrap();
    assert!(output.status.success(), "{:?}", output);
    let report: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(
        report,
        serde_json::json!({"status":"confirmed","deleted":3,"batches":2,"shortBatch":true})
    );
    assert_eq!(
        peer.query_one("SELECT count(*) FROM dpop_proofs", &[])
            .await
            .unwrap()
            .get::<_, i64>(0),
        1
    );
    let invalid = std::process::Command::new(env!("CARGO_BIN_EXE_web-replay-maintenance"))
        .output()
        .unwrap();
    assert_eq!(invalid.status.code(), Some(2));
    println!(
        "real maintenance process: explicit local coordinate, 3 expired deleted, live proof retained, invalid config rejected"
    );
}
