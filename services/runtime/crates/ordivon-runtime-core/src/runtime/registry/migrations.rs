// Historical migrations are immutable. A descriptor is the one transition
// contract, not a second migration ledger or a new database authority.
struct MigrationDescriptor {
    version: i64,
    name: &'static str,
    checksum: &'static str,
    sql: &'static str,
}

const MIGRATIONS: [MigrationDescriptor; MAX_MIGRATION_VERSION as usize] = [
    MigrationDescriptor {
        version: MIGRATION_V1,
        name: MIGRATION_V1_NAME,
        checksum: RUNTIME_MIGRATION_CHECKSUM,
        sql: MIGRATION_V1_SQL,
    },
    MigrationDescriptor {
        version: MIGRATION_V2,
        name: MIGRATION_V2_NAME,
        checksum: RUNTIME_ORPHAN_RECOVERY_MIGRATION_CHECKSUM,
        sql: MIGRATION_V2_SQL,
    },
    MigrationDescriptor {
        version: MIGRATION_V3,
        name: MIGRATION_V3_NAME,
        checksum: RUNTIME_TERMINAL_REPAIR_MIGRATION_CHECKSUM,
        sql: MIGRATION_V3_SQL,
    },
    MigrationDescriptor {
        version: MIGRATION_V4,
        name: MIGRATION_V4_NAME,
        checksum: RUNTIME_ORPHAN_RECLAIM_MIGRATION_CHECKSUM,
        sql: MIGRATION_V4_SQL,
    },
    MigrationDescriptor {
        version: CONDITION_RETIREMENT_MIGRATION_VERSION,
        name: MIGRATION_V5_NAME,
        checksum: RUNTIME_CONDITION_RETIREMENT_MIGRATION_CHECKSUM,
        sql: MIGRATION_V5_SQL,
    },
    MigrationDescriptor {
        version: WORKSPACE_PATCH_RETIREMENT_MIGRATION_VERSION,
        name: MIGRATION_V6_NAME,
        checksum: RUNTIME_WORKSPACE_PATCH_RETIREMENT_MIGRATION_CHECKSUM,
        sql: MIGRATION_V6_SQL,
    },
];

fn migration_prefix(connection: &Connection) -> RuntimeResult<usize> {
    let has_table: bool = connection.query_row(
        "SELECT EXISTS(SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations')",
        [], |row| row.get(0),
    ).map_err(|e| RuntimeError::from_sql(e, "cannot inspect schema migrations"))?;
    if !has_table {
        return Ok(0);
    }
    let mut statement = connection
        .prepare("SELECT version,name,checksum FROM schema_migrations ORDER BY version")
        .map_err(|e| RuntimeError::from_sql(e, "cannot prepare migration prefix"))?;
    let mut rows = statement
        .query([])
        .map_err(|e| RuntimeError::from_sql(e, "cannot read migration prefix"))?;
    let mut prefix = 0;
    while let Some(row) = rows
        .next()
        .map_err(|e| RuntimeError::from_sql(e, "cannot read migration row"))?
    {
        let version: i64 = row
            .get(0)
            .map_err(|e| RuntimeError::from_sql(e, "cannot decode migration version"))?;
        if version > MAX_MIGRATION_VERSION {
            return Err(RuntimeError::new(
                RuntimeErrorCode::SchemaVersionUnsupported,
                format!(
                    "registry schema {version} is newer than supported {MAX_MIGRATION_VERSION}"
                ),
                None,
                false,
            ));
        }
        let name: String = row
            .get(1)
            .map_err(|e| RuntimeError::from_sql(e, "cannot decode migration name"))?;
        let checksum: String = row
            .get(2)
            .map_err(|e| RuntimeError::from_sql(e, "cannot decode migration checksum"))?;
        let Some(expected) = MIGRATIONS
            .get(prefix)
            .filter(|m| m.version == version && m.name == name)
        else {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                format!("invalid migration prefix at version {version}"),
                None,
                false,
            ));
        };
        if checksum != expected.checksum {
            return Err(RuntimeError::new(
                RuntimeErrorCode::MigrationChecksumMismatch,
                format!(
                    "{} checksum does not match the compiled migration",
                    expected.name
                ),
                None,
                false,
            ));
        }
        prefix += 1;
    }
    if prefix == 0 {
        return Err(RuntimeError::new(
            RuntimeErrorCode::RegistryCorrupt,
            "schema_migrations is empty",
            None,
            false,
        ));
    }
    Ok(prefix)
}

impl Registry {
    fn apply_migrations(&self, connection: &mut Connection) -> RuntimeResult<()> {
        loop {
            // Inspect after taking the native writer lock: two Registry instances
            // cannot both use the same stale prefix to apply the same migration.
            let tx = immediate(self, connection, "Runtime migration transition")?;
            let prefix = migration_prefix(&tx)?;
            let Some(migration) = MIGRATIONS.get(prefix) else {
                return Ok(());
            };
            tx.execute_batch(migration.sql)
                .map_err(|e| RuntimeError::from_sql(e, "cannot apply Runtime migration"))?;
            tx.execute(
                "INSERT INTO schema_migrations(version,name,checksum,applied_at_ms) VALUES(?1,?2,?3,?4)",
                params![migration.version,migration.name,migration.checksum,now_ms()?],
            ).map_err(|e| RuntimeError::from_sql(e, "cannot record Runtime migration"))?;
            // Validate the whole resulting prefix before commit (including triggers
            // that might mutate another ledger row or suppress the insertion).
            if migration_prefix(&tx)? != prefix + 1 {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "migration did not advance exactly one version",
                    None,
                    false,
                ));
            }
            tx.commit()
                .map_err(|e| RuntimeError::from_sql(e, "cannot commit Runtime migration"))?;
        }
    }
}
