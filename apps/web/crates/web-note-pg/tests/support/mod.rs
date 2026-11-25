// Fixture subset of WebStore schema, not a production migration.
// Preserve text representations and nullable Audit fields.
pub const SCHEMA: &str = "
CREATE TABLE principals(principal_id TEXT PRIMARY KEY,user_name TEXT NOT NULL UNIQUE,display_name TEXT NOT NULL,created_at BIGINT NOT NULL);
CREATE TABLE canary_notes(note_id TEXT PRIMARY KEY,principal_id TEXT NOT NULL REFERENCES principals(principal_id),content TEXT NOT NULL,state TEXT NOT NULL CHECK(state IN ('DRAFT','PUBLISHED')),created_at BIGINT NOT NULL,published_at BIGINT);
CREATE INDEX canary_notes_principal_created ON canary_notes(principal_id,created_at DESC,note_id ASC);
CREATE TABLE audit_events(event_id TEXT PRIMARY KEY,principal_id TEXT,event_type TEXT NOT NULL,object_type TEXT,object_id TEXT,detail_json TEXT NOT NULL,created_at BIGINT NOT NULL);
CREATE INDEX audit_events_created_note ON audit_events(object_id) WHERE event_type='canary.note.created' AND object_type='canary-note';
INSERT INTO principals VALUES ('p','p','P',1),('q','q','Q',1);
";

use ordivon_web_note_pg::{PgNoteStore, PoolLimits};
use std::{path::PathBuf, time::Duration};
use tokio_postgres::{Client, Config, NoTls};
pub async fn fixture() -> (PgNoteStore, Client) {
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
    let store = PgNoteStore::local_bounded(
        &socket,
        port,
        &user,
        "postgres",
        PoolLimits {
            max_size: 2,
            wait: Duration::from_millis(250),
        },
    )
    .unwrap();
    (store, client)
}
pub async fn counts(client: &Client) -> (i64, i64) {
    let row = client
        .query_one(
            "SELECT (SELECT count(*) FROM canary_notes),(SELECT count(*) FROM audit_events)",
            &[],
        )
        .await
        .unwrap();
    (row.get(0), row.get(1))
}
pub async fn reset(client: &Client) {
    client.batch_execute("DROP TABLE IF EXISTS canary_notes,audit_events,principals CASCADE; DROP FUNCTION IF EXISTS fault() CASCADE;").await.unwrap();
    client.batch_execute(SCHEMA).await.unwrap();
}
