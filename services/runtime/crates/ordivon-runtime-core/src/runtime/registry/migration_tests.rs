use super::*;
use tempfile::TempDir;

// Reuse the single compiled SQL input per migration. Independently specify
// historical names and derive checksums from the SQL bytes, not descriptors
// or ledger constants. A second include_str! spelling creates ambiguous
// rustc dep-info paths without adding an independent source.
const FIXTURES: [(&str, &str); 6] = [
    ("0001_runtime", MIGRATION_V1_SQL),
    ("0002_orphan_recovery", MIGRATION_V2_SQL),
    ("0003_terminal_repair", MIGRATION_V3_SQL),
    ("0004_orphan_reclaim", MIGRATION_V4_SQL),
    ("0005_condition_retirement", MIGRATION_V5_SQL),
    ("0006_workspace_patch_retirement", MIGRATION_V6_SQL),
];

fn fixture_checksum(sql: &str) -> String {
    format!("sha256:{}", hex::encode(Sha256::digest(sql.as_bytes())))
}

fn fixture(prefix: usize) -> (TempDir, RegistryConfig) {
    let root = tempfile::tempdir().unwrap();
    let config = RegistryConfig {
        db_path: root.path().join("registry.sqlite3"),
        store_root: root.path().join("store"),
        busy_timeout_ms: 5000,
    };
    if prefix != 0 {
        let mut connection = Connection::open(&config.db_path).unwrap();
        connection
            .pragma_update(None, "foreign_keys", true)
            .unwrap();
        for (i, (name, sql)) in FIXTURES.iter().take(prefix).enumerate() {
            let tx = connection.transaction().unwrap();
            tx.execute_batch(sql).unwrap();
            tx.execute(
                "INSERT INTO schema_migrations VALUES(?1,?2,?3,0)",
                params![i as i64 + 1, name, fixture_checksum(sql)],
            )
            .unwrap();
            tx.commit().unwrap();
        }
    }
    (root, config)
}

fn ledger(config: &RegistryConfig) -> Vec<(i64, String, String, i64)> {
    let c = Connection::open(&config.db_path).unwrap();
    let mut q = c
        .prepare(
            "SELECT version,name,checksum,applied_at_ms FROM schema_migrations ORDER BY version",
        )
        .unwrap();
    q.query_map([], |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?, r.get(3)?)))
        .unwrap()
        .collect::<Result<Vec<_>, _>>()
        .unwrap()
}

#[test]
fn native_migration_runner_accepts_every_real_prefix_and_reopens() {
    for prefix in 0..=FIXTURES.len() {
        let (_root, config) = fixture(prefix);
        let existing = if prefix == 0 { vec![] } else { ledger(&config) };
        drop(Registry::initialize(config.clone()).unwrap());
        let after = ledger(&config);
        assert_eq!(after.len(), FIXTURES.len());
        assert_eq!(&after[..prefix], &existing);
        for (i, (version, name, checksum, _)) in after.iter().enumerate() {
            assert_eq!(
                (*version, name.as_str(), checksum.as_str()),
                (
                    i as i64 + 1,
                    FIXTURES[i].0,
                    fixture_checksum(FIXTURES[i].1).as_str()
                )
            );
        }
        drop(Registry::initialize(config.clone()).unwrap());
        assert_eq!(ledger(&config), after);
        let c = Connection::open(&config.db_path).unwrap();
        assert_eq!(
            c.query_row("PRAGMA integrity_check", [], |r| r.get::<_, String>(0))
                .unwrap(),
            "ok"
        );
    }
}

#[test]
fn native_migration_runner_rejects_malformed_prefix_without_advancing() {
    for (sql, expected) in [
        (
            "INSERT INTO schema_migrations VALUES(0,'unexpected','x',0)",
            RuntimeErrorCode::RegistryCorrupt,
        ),
        (
            "UPDATE schema_migrations SET name='unexpected' WHERE version=2",
            RuntimeErrorCode::RegistryCorrupt,
        ),
        (
            "DELETE FROM schema_migrations WHERE version=2",
            RuntimeErrorCode::RegistryCorrupt,
        ),
        (
            "UPDATE schema_migrations SET checksum='sha256:wrong' WHERE version=3",
            RuntimeErrorCode::MigrationChecksumMismatch,
        ),
        (
            "INSERT INTO schema_migrations VALUES(7,'future','x',0)",
            RuntimeErrorCode::SchemaVersionUnsupported,
        ),
        (
            "DELETE FROM schema_migrations",
            RuntimeErrorCode::RegistryCorrupt,
        ),
    ] {
        let (_root, config) = fixture(4);
        Connection::open(&config.db_path)
            .unwrap()
            .execute_batch(sql)
            .unwrap();
        let before = ledger(&config);
        let result = Registry::initialize(config.clone());
        assert_eq!(result.unwrap_err().code, expected, "{sql}");
        assert_eq!(ledger(&config), before, "{sql}");
    }
}

#[test]
fn native_migration_runner_rolls_back_ddl_when_ledger_write_fails() {
    let (_root, config) = fixture(5);
    let c = Connection::open(&config.db_path).unwrap();
    c.execute_batch("CREATE TABLE IF NOT EXISTS workspace_patch_operations (legacy_id TEXT PRIMARY KEY); INSERT INTO workspace_patch_operations(legacy_id) VALUES('retained');").unwrap();
    c.execute_batch("CREATE TRIGGER reject_v6 BEFORE INSERT ON schema_migrations WHEN NEW.version=6 BEGIN SELECT RAISE(ABORT,'injected native ledger failure'); END;").unwrap();
    let before = ledger(&config);
    let table_exists = |c: &Connection| {
        c.query_row(
            "SELECT EXISTS(SELECT 1 FROM sqlite_schema WHERE name='workspace_patch_operations')",
            [],
            |r| r.get::<_, bool>(0),
        )
        .unwrap()
    };
    assert!(table_exists(&c));
    drop(c);
    assert!(Registry::initialize(config.clone()).is_err());
    assert_eq!(ledger(&config), before);
    let c = Connection::open(&config.db_path).unwrap();
    assert!(table_exists(&c), "DDL committed without ledger");
    c.execute_batch("DROP TRIGGER reject_v6").unwrap();
    drop(c);
    drop(Registry::initialize(config.clone()).unwrap());
    let c = Connection::open(&config.db_path).unwrap();
    assert!(!table_exists(&c));
    assert_eq!(ledger(&config).len(), 6);
}

#[test]
fn native_migration_runner_rejects_trigger_mutations_before_commit() {
    for trigger in [
        "CREATE TRIGGER mutate_v6 AFTER INSERT ON schema_migrations WHEN NEW.version=6 BEGIN UPDATE schema_migrations SET name='mutated' WHERE version=2; END;",
        "CREATE TRIGGER suppress_v6 BEFORE INSERT ON schema_migrations WHEN NEW.version=6 BEGIN SELECT RAISE(IGNORE); END;",
    ] {
        let (_root, config) = fixture(5);
        let c = Connection::open(&config.db_path).unwrap();
        c.execute_batch("CREATE TABLE IF NOT EXISTS workspace_patch_operations (legacy_id TEXT PRIMARY KEY); INSERT INTO workspace_patch_operations(legacy_id) VALUES('retained');").unwrap();
        c.execute_batch(trigger).unwrap();
        drop(c);
        let before = ledger(&config);
        assert_eq!(Registry::initialize(config.clone()).unwrap_err().code, RuntimeErrorCode::RegistryCorrupt);
        assert_eq!(ledger(&config), before);
        let c = Connection::open(&config.db_path).unwrap();
        assert_eq!(c.query_row("SELECT legacy_id FROM workspace_patch_operations", [], |r| r.get::<_, String>(0)).unwrap(), "retained");
    }
}

#[test]
fn native_migration_runner_serializes_independent_connections() {
    for prefix in [0, 1, 4, 5, 6] {
        let (_root, config) = fixture(prefix);
        let c = Connection::open(&config.db_path).unwrap();
        c.pragma_update(None, "journal_mode", "WAL").unwrap();
        drop(c);
        let barrier = Arc::new(std::sync::Barrier::new(4));
        let threads: Vec<_> = (0..4)
            .map(|_| {
                let registry = Registry {
                    config: config.clone(),
                    write_gate: Arc::new(Mutex::new(())),
                };
                let barrier = Arc::clone(&barrier);
                std::thread::spawn(move || {
                    let mut c = registry.open_connection().unwrap();
                    barrier.wait();
                    registry.apply_migrations(&mut c).unwrap();
                })
            })
            .collect();
        for thread in threads {
            thread.join().unwrap();
        }
        let actual = ledger(&config);
        assert_eq!(actual.len(), FIXTURES.len());
        for (i, (version, name, checksum, _)) in actual.iter().enumerate() {
            assert_eq!(
                (*version, name.as_str(), checksum.as_str()),
                (
                    i as i64 + 1,
                    FIXTURES[i].0,
                    fixture_checksum(FIXTURES[i].1).as_str()
                )
            );
        }
    }
}
