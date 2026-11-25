mod support;
use ordivon_web_note_pg::migration::{Cell, ImportError, Snapshot, import_initial, read_snapshot};
use serde::Deserialize;
use tokio_postgres::{Client, IsolationLevel};
#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct Source {
    original: Snapshot,
    indexes: Vec<String>,
    bad_utf8: Snapshot,
    bad_nul: Snapshot,
}
fn source() -> Source {
    let output = std::process::Command::new(std::env::var("WEB_NOTE_TEST_NODE").unwrap())
        .arg(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/tests/sqlite-migration-reference.ts"
        ))
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    serde_json::from_slice(&output.stdout).unwrap()
}
async fn select_schema(peer: &Client, name: &str) {
    // All caller names are fixed in this isolated test.
    peer.batch_execute(&format!("CREATE SCHEMA {name}; SET search_path TO {name}"))
        .await
        .unwrap();
}
async fn table_count(peer: &Client) -> i64 {
    peer.query_one(
        "SELECT count(*) FROM information_schema.tables WHERE table_schema=current_schema()",
        &[],
    )
    .await
    .unwrap()
    .get(0)
}
#[tokio::test]
async fn actual_owner_schema_exact_import() {
    let (_store, mut peer) = support::fixture().await;
    support::reset(&peer).await;
    assert_eq!(support::counts(&peer).await, (0, 0));
    let source = source();
    select_schema(&peer, "migration_exact").await;
    assert!(matches!(
        import_initial(&mut peer, "public", &source.original).await,
        Err(ImportError::Invalid(_))
    ));
    assert_eq!(table_count(&peer).await, 0);

    import_initial(&mut peer, "migration_exact", &source.original)
        .await
        .unwrap();
    assert_eq!(table_count(&peer).await, 11);
    // Independent native PG index inventory (exclude PK/UNIQUE constraints).
    let indexes=peer.query("SELECT i.relname FROM pg_index x JOIN pg_class i ON i.oid=x.indexrelid JOIN pg_namespace n ON n.oid=i.relnamespace WHERE n.nspname=current_schema() AND NOT x.indisunique ORDER BY i.relname COLLATE \"C\"",&[]).await.unwrap().iter().map(|r|r.get::<_,String>(0)).collect::<Vec<_>>();
    assert_eq!(indexes, source.indexes);
    let tx = peer
        .build_transaction()
        .isolation_level(IsolationLevel::RepeatableRead)
        .read_only(true)
        .start()
        .await
        .unwrap();
    assert_eq!(read_snapshot(&tx).await.unwrap(), source.original);
    tx.rollback().await.unwrap();
    // Independent raw SQL byte/value observations, not importer projections.
    assert_eq!(
        peer.query_one(
            "SELECT encode(public_key,'hex') FROM webauthn_credentials",
            &[]
        )
        .await
        .unwrap()
        .get::<_, String>(0),
        "00ff800100"
    );
    assert_eq!(
        peer.query_one("SELECT result_json FROM agent_effects", &[])
            .await
            .unwrap()
            .get::<_, String>(0),
        " { \"note\": {\"content\":\"🦀\",\"noteId\":\"a\"} } "
    );
    assert_eq!(
        peer.query_one(
            "SELECT count(*) FROM audit_events WHERE object_id='effect'",
            &[]
        )
        .await
        .unwrap()
        .get::<_, i64>(0),
        2
    );
    assert_eq!(
        peer.query_one(
            "SELECT count(*) FROM sessions WHERE user_agent IS NULL",
            &[]
        )
        .await
        .unwrap()
        .get::<_, i64>(0),
        1
    );
    assert_eq!(
        peer.query_one("SELECT count(*) FROM sessions WHERE user_agent=''", &[])
            .await
            .unwrap()
            .get::<_, i64>(0),
        1
    );
    assert_eq!(peer.query("SELECT note_id FROM canary_notes WHERE principal_id='p' ORDER BY created_at DESC,note_id",&[]).await.unwrap().iter().map(|r|r.get::<_,String>(0)).collect::<Vec<_>>(),vec!["a","e\u{301}","é","\u{e000}","🦀"]);
    // A second import cannot overwrite an existing installation.
    assert!(matches!(
        import_initial(&mut peer, "migration_exact", &source.original).await,
        Err(ImportError::Invalid(_))
    ));
    let tx = peer.transaction().await.unwrap();
    assert_eq!(read_snapshot(&tx).await.unwrap(), source.original);
    tx.rollback().await.unwrap();
    println!(
        "actual SQLite to PG: 11 tables / 8 explicit indexes / {} exact rows, binary/JSON/null/Unicode and repeat refusal",
        source
            .original
            .values()
            .map(|t| t.rows.len())
            .sum::<usize>()
    );
    peer.batch_execute("DROP SCHEMA migration_exact CASCADE; SET search_path TO public")
        .await
        .unwrap();
}
#[tokio::test]
async fn malformed_and_native_constraint_import_roll_back() {
    let (_store, mut peer) = support::fixture().await;
    let source = source();
    select_schema(&peer, "migration_negative").await;
    for (name, snapshot) in [
        ("invalid UTF8", source.bad_utf8),
        ("NUL text", source.bad_nul),
    ] {
        assert!(
            matches!(
                import_initial(&mut peer, "migration_negative", &snapshot).await,
                Err(ImportError::Invalid(_))
            ),
            "{name}"
        );
        assert_eq!(table_count(&peer).await, 0);
    }
    let mut bad = source.original.clone();
    bad.get_mut("dpop_proofs").unwrap().rows[0][1] = Cell::Integer(i64::MAX);
    assert!(matches!(
        import_initial(&mut peer, "migration_negative", &bad).await,
        Err(ImportError::Invalid(_))
    ));
    let mut bad = source.original.clone();
    bad.get_mut("dpop_proofs").unwrap().rows[0][1] = Cell::Text(b"100".to_vec());
    assert!(matches!(
        import_initial(&mut peer, "migration_negative", &bad).await,
        Err(ImportError::Invalid(_))
    ));
    let mut bad = source.original.clone();
    bad.remove("audit_events");
    assert!(matches!(
        import_initial(&mut peer, "migration_negative", &bad).await,
        Err(ImportError::Invalid(_))
    ));
    let mut bad = source.original.clone();
    bad.get_mut("canary_notes").unwrap().rows.swap(0, 1);
    assert!(matches!(
        import_initial(&mut peer, "migration_negative", &bad).await,
        Err(ImportError::Invalid(_))
    ));
    assert_eq!(table_count(&peer).await, 0);
    // FK/check constraints fail after prior tables and rows have already been
    // created, proving native transactional DDL/data rollback.
    for (table, column, value, code) in [
        (
            "agent_effects",
            "grant_id",
            Cell::Text(b"missing".to_vec()),
            "23503",
        ),
        (
            "agent_grants",
            "remaining_effects",
            Cell::Integer(-1),
            "23514",
        ),
        (
            "webauthn_credentials",
            "backed_up",
            Cell::Integer(2),
            "23514",
        ),
    ] {
        let mut bad = source.original.clone();
        let t = bad.get_mut(table).unwrap();
        let j = t.columns.iter().position(|c| c == column).unwrap();
        t.rows[0][j] = value;
        let err = import_initial(&mut peer, "migration_negative", &bad)
            .await
            .unwrap_err();
        assert!(
            matches!(err,ImportError::Database(ref e) if e.code().is_some_and(|c|c.code()==code)),
            "{err:?}"
        );
        assert_eq!(table_count(&peer).await, 0);
    }
    import_initial(&mut peer, "migration_negative", &source.original)
        .await
        .unwrap();
    assert_eq!(table_count(&peer).await, 11);
    println!(
        "6 malformed snapshots + 3 native FK/check faults; no partial target; subsequent exact import succeeds"
    );
    peer.batch_execute("DROP SCHEMA migration_negative CASCADE; SET search_path TO public")
        .await
        .unwrap();
}

async fn database(name: &str) -> Client {
    let socket = std::path::PathBuf::from(std::env::var_os("WEB_NOTE_TEST_SOCKET").unwrap());
    let mut config = tokio_postgres::Config::new();
    config
        .host_path(&socket)
        .port(
            std::env::var("WEB_NOTE_TEST_PORT")
                .unwrap()
                .parse()
                .unwrap(),
        )
        .user(std::env::var("WEB_NOTE_TEST_USER").unwrap())
        .dbname(name);
    let (client, driver) = config.connect(tokio_postgres::NoTls).await.unwrap();
    tokio::spawn(async move { driver.await.unwrap() });
    client
}
fn native_tool(tool: &str, args: &[&str]) -> Vec<u8> {
    let socket = std::env::var("WEB_NOTE_TEST_SOCKET").unwrap();
    let user = std::env::var("WEB_NOTE_TEST_USER").unwrap();
    let port = std::env::var("WEB_NOTE_TEST_PORT").unwrap();
    let result = std::process::Command::new(tool)
        .args(["-h", &socket, "-p", &port, "-U", &user, "--no-password"])
        .args(args)
        .output()
        .unwrap();
    assert!(
        result.status.success(),
        "{tool}: {}",
        String::from_utf8_lossy(&result.stderr)
    );
    result.stdout
}

#[tokio::test]
async fn native_dump_restore_and_real_note_consumer() {
    use ordivon_web_note_pg::{NoteObservation, PgNoteStore, PreparedNote};
    let (_store, admin) = support::fixture().await;
    let source = source().original;
    admin
        .batch_execute("CREATE DATABASE web_migration_source TEMPLATE template0")
        .await
        .unwrap();
    admin
        .batch_execute("CREATE DATABASE web_migration_restore TEMPLATE template0")
        .await
        .unwrap();
    // This freshly created, disposable database is empty. The archive
    // includes CREATE SCHEMA public; remove only its template-created schema,
    // never use pg_restore --clean against a populated destination.
    let empty_target = database("web_migration_restore").await;
    empty_target
        .batch_execute("DROP SCHEMA public")
        .await
        .unwrap();
    drop(empty_target);
    let mut src = database("web_migration_source").await;
    import_initial(&mut src, "public", &source).await.unwrap();
    let path = std::path::PathBuf::from(std::env::var_os("WEB_NOTE_TEST_SOCKET").unwrap())
        .join("migration-owner.dump");
    native_tool(
        "pg_dump",
        &[
            "--format=custom",
            "--no-owner",
            "--no-privileges",
            "--schema=public",
            "--file",
            path.to_str().unwrap(),
            "web_migration_source",
        ],
    );
    let archive_bytes = std::fs::metadata(&path).unwrap().len();
    assert!(archive_bytes > 0);
    native_tool(
        "pg_restore",
        &[
            "--exit-on-error",
            "--no-owner",
            "--no-privileges",
            "--single-transaction",
            "--dbname=web_migration_restore",
            path.to_str().unwrap(),
        ],
    );
    let mut restored = database("web_migration_restore").await;
    let tx = restored
        .build_transaction()
        .isolation_level(IsolationLevel::RepeatableRead)
        .read_only(true)
        .start()
        .await
        .unwrap();
    assert_eq!(read_snapshot(&tx).await.unwrap(), source);
    tx.rollback().await.unwrap();
    let store = PgNoteStore::local(
        &std::path::PathBuf::from(std::env::var_os("WEB_NOTE_TEST_SOCKET").unwrap()),
        std::env::var("WEB_NOTE_TEST_PORT")
            .unwrap()
            .parse()
            .unwrap(),
        &std::env::var("WEB_NOTE_TEST_USER").unwrap(),
        "web_migration_restore",
    )
    .unwrap();
    assert_eq!(store.list("p").await.unwrap().len(), 5);
    let operation = PreparedNote::new("p", "restored consumer draft", 123).unwrap();
    let note = store.execute(&operation).await.unwrap();
    assert_eq!(
        store.observe(&operation).await.unwrap(),
        NoteObservation::Exact(note)
    );
    let tx = restored.transaction().await.unwrap();
    let after = read_snapshot(&tx).await.unwrap();
    tx.rollback().await.unwrap();
    for (name, table) in &source {
        if name == "canary_notes" || name == "audit_events" {
            assert_eq!(after[name].rows.len(), table.rows.len() + 1);
            assert!(table.rows.iter().all(|r| after[name].rows.contains(r)));
        } else {
            assert_eq!(&after[name], table);
        }
    }
    assert_eq!(store.list("q").await.unwrap().len(), 1);
    std::fs::remove_file(path).unwrap();
    println!(
        "native pg_dump/pg_restore archive {archive_bytes} bytes, full exact source/restore snapshot; real Rust Note consumer creates one Note/Audit only"
    );
}

#[tokio::test]
async fn copy_faults_rollback_exact_postconditions() {
    let (_store, mut peer) = support::fixture().await;
    let source = source().original;
    select_schema(&peer, "migration_fault").await;
    // Independent native DDL event fixture attaches a trigger to the new
    // audit table at creation. The importer has no test hook or mock writer.
    peer.batch_execute("
      CREATE FUNCTION public.migration_attach_fault() RETURNS event_trigger LANGUAGE plpgsql AS $$
      BEGIN
        IF EXISTS (SELECT 1 FROM pg_event_trigger_ddl_commands() WHERE object_type='table' AND object_identity='migration_fault.audit_events') THEN
          CREATE TRIGGER fixture_fault BEFORE INSERT ON migration_fault.audit_events FOR EACH ROW EXECUTE FUNCTION public.migration_copy_fault();
        END IF;
      END; $$;
      CREATE FUNCTION public.migration_copy_fault() RETURNS trigger LANGUAGE plpgsql AS $$
      BEGIN RETURN NULL; END; $$;
      CREATE EVENT TRIGGER migration_fixture ON ddl_command_end WHEN TAG IN ('CREATE TABLE') EXECUTE FUNCTION public.migration_attach_fault();
    ").await.unwrap();
    let result = import_initial(&mut peer, "migration_fault", &source).await;
    assert!(
        matches!(result, Err(ImportError::ReadbackMismatch)),
        "COPY omitted row must reject: {result:?}"
    );
    assert_eq!(table_count(&peer).await, 0);
    peer.batch_execute("
      CREATE OR REPLACE FUNCTION public.migration_copy_fault() RETURNS trigger LANGUAGE plpgsql AS $$
      BEGIN NEW.detail_json='[]'; RETURN NEW; END; $$;
    ").await.unwrap();
    let result = import_initial(&mut peer, "migration_fault", &source).await;
    assert!(
        matches!(result, Err(ImportError::ReadbackMismatch)),
        "COPY changed bytes must reject: {result:?}"
    );
    assert_eq!(table_count(&peer).await, 0);
    peer.batch_execute("DROP EVENT TRIGGER migration_fixture; DROP FUNCTION public.migration_attach_fault(); DROP FUNCTION public.migration_copy_fault();").await.unwrap();
    // Empty source is a legitimate complete snapshot, not missing inventory.
    let mut empty = source.clone();
    for table in empty.values_mut() {
        table.rows.clear();
    }
    import_initial(&mut peer, "migration_fault", &empty)
        .await
        .unwrap();
    let tx = peer.transaction().await.unwrap();
    assert_eq!(read_snapshot(&tx).await.unwrap(), empty);
    tx.rollback().await.unwrap();
    assert_eq!(table_count(&peer).await, 11);
    peer.batch_execute("DROP SCHEMA migration_fault CASCADE; SET search_path TO public")
        .await
        .unwrap();
    println!(
        "native COPY omitted row and mutated byte controls rejected; zero partial relations; complete empty source accepted"
    );
}
