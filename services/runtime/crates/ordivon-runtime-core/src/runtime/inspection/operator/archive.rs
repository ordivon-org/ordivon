pub const DEFAULT_ARCHIVE_SAMPLE_LIMIT: u32 = 20;
pub const MAX_ARCHIVE_SAMPLE_LIMIT: u32 = 100;

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeOperatorArchiveInspection {
    pub schema_version: u32,
    pub generated_at_ms: u64,
    pub migration_version: i64,
    pub by_classification: Vec<RuntimeOperatorArchiveClassification>,
    pub eligible_closure: RuntimeOperatorArchiveClosure,
    pub eligible_sample: Vec<RuntimeOperatorArchiveSample>,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeOperatorArchiveClassification {
    pub classification: String,
    pub jobs: u64,
    pub oldest_created_at_ms: u64,
    pub newest_created_at_ms: u64,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeOperatorArchiveClosure {
    pub jobs: u64,
    pub attempts: u64,
    pub idempotency_keys: u64,
    pub reservations: u64,
    pub events: u64,
    pub artifacts: u64,
    pub conditions: u64,
    pub execution_providers: u64,
    pub host_dependencies: u64,
    pub supervisor_owners: u64,
    pub artifact_logical_payload_bytes: u64,
    pub job_json_logical_bytes: u64,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeOperatorArchiveSample {
    pub job_id: String,
    pub client_request_id: String,
    pub workspace_id: String,
    pub resolution: String,
    pub job_current_attempt_id: Option<String>,
    pub effective_attempt_id: String,
    pub bundle_path: String,
    pub created_at_ms: u64,
}

const ARCHIVE_CLASSIFICATION_SQL: &str = r#"
WITH classified AS (
    SELECT
        j.job_id,
        j.created_at_ms,
        CASE
            WHEN j.resolution IS NULL THEN 'unresolved'
            WHEN j.resolution IN ('lost','orphaned') THEN 'repairable_terminal'
            WHEN j.resolution NOT IN ('succeeded','failed','timed_out','cancelled')
                THEN 'unsupported_resolution'
            WHEN j.created_at_ms >= ?1 THEN 'younger_than_minimum_age'
            WHEN EXISTS(
                SELECT 1 FROM job_runtime_release_effects r WHERE r.job_id=j.job_id
            ) THEN 'runtime_release_effect'
            WHEN j.current_attempt_id IS NOT NULL AND NOT EXISTS(
                SELECT 1 FROM attempts a
                WHERE a.attempt_id=j.current_attempt_id AND a.job_id=j.job_id
            ) THEN 'current_attempt_invalid'
            WHEN NOT EXISTS(
                SELECT 1 FROM attempts a WHERE a.job_id=j.job_id
            ) THEN 'attempt_missing'
            WHEN EXISTS(
                SELECT 1 FROM attempts a
                WHERE a.job_id=j.job_id
                  AND a.state NOT IN ('succeeded','failed','timed_out','cancelled')
            ) THEN 'attempt_not_stable_terminal'
            WHEN /* recovery_guard */ THEN 'recovery_required_or_unknown'
            WHEN EXISTS(
                SELECT 1
                FROM attempts a
                JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id
                WHERE a.job_id=j.job_id
                  AND r.state IN ('active','held_orphaned')
            ) THEN 'active_or_held_reservation'
            WHEN EXISTS(
                SELECT 1
                FROM attempts a
                JOIN attempt_supervisor_owners o ON o.attempt_id=a.attempt_id
                WHERE a.job_id=j.job_id
            ) THEN 'supervisor_owner_present'
            ELSE 'eligible'
        END AS classification
    FROM jobs j
)
"#;

// Recovery state moved from attempt_conditions to attempts in schema 5.
// Missing markers are normal for settled historical attempts; they do not
// certify consumer release. Explicit non-false markers must not be eligible.
fn archive_classification_sql(migration_version: i64) -> String {
    let recovery_guard = if migration_version < CONDITION_RETIREMENT_MIGRATION_VERSION {
        "EXISTS(SELECT 1 FROM attempts a JOIN attempt_conditions c ON c.attempt_id=a.attempt_id WHERE a.job_id=j.job_id AND c.condition_type='recovery_required' AND c.status IS NOT 'false')"
    } else {
        "EXISTS(SELECT 1 FROM attempts a WHERE a.job_id=j.job_id AND a.recovery_required IS NOT NULL AND a.recovery_required <> 0)"
    };
    ARCHIVE_CLASSIFICATION_SQL.replace("/* recovery_guard */", recovery_guard)
}

fn validate_archive_registry_capabilities(
    connection: &Connection,
    migration_version: i64,
) -> RuntimeResult<()> {
    let required: &[(&str, &[&str])] = &[
        ("schema_migrations", &["version"]),
        (
            "jobs",
            &[
                "job_id",
                "principal",
                "client_request_id",
                "request_digest",
                "operation_digest",
                "workspace_id",
                "workspace_snapshot_json",
                "execution_plan_json",
                "execution_plan_digest",
                "created_at_ms",
                "resolution",
                "current_attempt_id",
            ],
        ),
        (
            "attempts",
            &[
                "attempt_id",
                "job_id",
                "attempt_number",
                "state",
                "bundle_path",
                "created_at_ms",
            ],
        ),
        (
            "idempotency_keys",
            &[
                "principal",
                "client_request_id",
                "operation_digest",
                "job_id",
                "created_at_ms",
            ],
        ),
        (
            "concurrency_reservations",
            &["reservation_id", "attempt_id", "state"],
        ),
        (
            "job_events",
            &[
                "event_id",
                "job_id",
                "attempt_id",
                "detail_json",
                "detail_digest",
            ],
        ),
        (
            "artifacts",
            &[
                "artifact_id",
                "job_id",
                "attempt_id",
                "kind",
                "relative_path",
                "digest",
                "media_type",
                "byte_length",
            ],
        ),
        (
            "job_execution_providers",
            &["job_id", "snapshot_json", "snapshot_digest"],
        ),
        (
            "job_runtime_release_effects",
            &["job_id", "effect_id", "binding_digest"],
        ),
        (
            "job_host_dependencies",
            &["job_id", "bindings_json", "bindings_digest"],
        ),
        (
            "attempt_supervisor_owners",
            &["attempt_id", "owner_json", "owner_digest"],
        ),
    ];
    let mut missing = Vec::<String>::new();
    for (table, columns) in required {
        let present = registry_table_columns(connection, table)?;
        if present.is_empty() {
            missing.push(format!("table:{table}"));
            continue;
        }
        for column in *columns {
            if !present.contains(*column) {
                missing.push(format!("column:{table}.{column}"));
            }
        }
    }
    if migration_version < CONDITION_RETIREMENT_MIGRATION_VERSION {
        let present = registry_table_columns(connection, "attempt_conditions")?;
        let legacy = [
            "attempt_id",
            "condition_type",
            "status",
            "reason_code",
            "evidence_digest",
        ];
        if present.is_empty() {
            missing.push("table:attempt_conditions".to_string());
        } else {
            for column in legacy {
                if !present.contains(column) {
                    missing.push(format!("column:attempt_conditions.{column}"));
                }
            }
        }
    }
    if migration_version >= CONDITION_RETIREMENT_MIGRATION_VERSION
        && !registry_table_columns(connection, "attempts")?.contains("recovery_required")
    {
        missing.push("column:attempts.recovery_required".to_string());
    }
    if !missing.is_empty() {
        return Err(RuntimeError::new(
            RuntimeErrorCode::SchemaVersionUnsupported,
            format!(
                "Runtime Registry lacks archive-inspection capabilities: {}",
                missing.join(", ")
            ),
            None,
            false,
        ));
    }
    Ok(())
}

pub fn inspect_registry_archive(
    config: &RuntimeInspectionConfig,
    cutoff_ms: u64,
    sample_limit: u32,
) -> RuntimeResult<RuntimeOperatorArchiveInspection> {
    if sample_limit > MAX_ARCHIVE_SAMPLE_LIMIT {
        return Err(RuntimeError::invalid(
            format!("sampleLimit must be at most {MAX_ARCHIVE_SAMPLE_LIMIT}"),
            "sampleLimit",
        ));
    }
    let (connection, _) = open_operator_read_only(config)?;
    let migrations = registry_table_columns(&connection, "schema_migrations")?;
    if migrations.is_empty() || !migrations.contains("version") {
        return Err(RuntimeError::new(
            RuntimeErrorCode::SchemaVersionUnsupported,
            "Runtime Registry lacks archive-inspection capabilities: table:schema_migrations",
            None,
            false,
        ));
    }
    let migration_version: Option<i64> = connection
        .query_row("SELECT MAX(version) FROM schema_migrations", [], |row| {
            row.get(0)
        })
        .map_err(|error| {
            RuntimeError::from_sql(error, "read archive Registry migration version")
        })?;
    let migration_version = migration_version.ok_or_else(|| {
        RuntimeError::new(
            RuntimeErrorCode::SchemaVersionUnsupported,
            "schema_migrations is empty",
            None,
            false,
        )
    })?;
    validate_archive_registry_capabilities(&connection, migration_version)?;
    let classification_cte = archive_classification_sql(migration_version);

    let classification_sql = format!(
        "{classification_cte} SELECT classification,COUNT(*) AS jobs,MIN(created_at_ms) AS oldest_ms,MAX(created_at_ms) AS newest_ms FROM classified GROUP BY classification ORDER BY classification"
    );
    let mut statement = connection
        .prepare(&classification_sql)
        .map_err(|error| RuntimeError::from_sql(error, "prepare archive classifications"))?;
    let rows = statement
        .query_map([cutoff_ms], |row| {
            Ok(RuntimeOperatorArchiveClassification {
                classification: row.get(0)?,
                jobs: row.get(1)?,
                oldest_created_at_ms: row.get(2)?,
                newest_created_at_ms: row.get(3)?,
            })
        })
        .map_err(|error| RuntimeError::from_sql(error, "query archive classifications"))?;
    let by_classification = rows
        .map(|row| {
            row.map_err(|error| RuntimeError::from_sql(error, "decode archive classification"))
        })
        .collect::<RuntimeResult<Vec<_>>>()?;

    let condition_count_sql = if migration_version < CONDITION_RETIREMENT_MIGRATION_VERSION {
        "(SELECT COUNT(*) FROM eligible e CROSS JOIN attempts a ON a.job_id=e.job_id CROSS JOIN attempt_conditions c ON c.attempt_id=a.attempt_id)"
    } else {
        "0"
    };
    // SQLite otherwise inlines eligibility into every relation aggregate.
    // Materialize the narrow Job identity set once and drive indexed joins
    // from that set. Materialization alone can scan whole child relations on
    // sparse cohorts, hence the explicit eligible-first CROSS JOIN order.
    let closure_sql = format!(
        r#"{classification_cte}, eligible AS MATERIALIZED (
            SELECT job_id FROM classified WHERE classification='eligible'
        )
        SELECT
            (SELECT COUNT(*) FROM eligible),
            (SELECT COUNT(*) FROM eligible e CROSS JOIN attempts a ON a.job_id=e.job_id),
            (SELECT COUNT(*) FROM eligible e CROSS JOIN idempotency_keys i ON i.job_id=e.job_id),
            (SELECT COUNT(*) FROM eligible e CROSS JOIN attempts a ON a.job_id=e.job_id CROSS JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id),
            (SELECT COUNT(*) FROM eligible e CROSS JOIN job_events x ON x.job_id=e.job_id),
            (SELECT COUNT(*) FROM eligible e CROSS JOIN artifacts x ON x.job_id=e.job_id),
            {condition_count_sql},
            (SELECT COUNT(*) FROM eligible e CROSS JOIN job_execution_providers p ON p.job_id=e.job_id),
            (SELECT COUNT(*) FROM eligible e CROSS JOIN job_host_dependencies h ON h.job_id=e.job_id),
            (SELECT COUNT(*) FROM eligible e CROSS JOIN attempts a ON a.job_id=e.job_id CROSS JOIN attempt_supervisor_owners o ON o.attempt_id=a.attempt_id),
            (SELECT COALESCE(SUM(x.byte_length),0) FROM eligible e CROSS JOIN artifacts x ON x.job_id=e.job_id),
            (SELECT COALESCE(SUM(OCTET_LENGTH(j.execution_plan_json)+OCTET_LENGTH(j.workspace_snapshot_json)),0) FROM eligible e CROSS JOIN jobs j ON j.job_id=e.job_id)"#
    );
    let eligible_closure = connection
        .query_row(&closure_sql, [cutoff_ms], |row| {
            Ok(RuntimeOperatorArchiveClosure {
                jobs: row.get(0)?,
                attempts: row.get(1)?,
                idempotency_keys: row.get(2)?,
                reservations: row.get(3)?,
                events: row.get(4)?,
                artifacts: row.get(5)?,
                conditions: row.get(6)?,
                execution_providers: row.get(7)?,
                host_dependencies: row.get(8)?,
                supervisor_owners: row.get(9)?,
                artifact_logical_payload_bytes: row.get(10)?,
                job_json_logical_bytes: row.get(11)?,
            })
        })
        .map_err(|error| RuntimeError::from_sql(error, "query archive eligible closure"))?;

    let eligible_sample = if sample_limit == 0 {
        Vec::new()
    } else {
        let sample_sql = format!(
            "{classification_cte} SELECT c.job_id,c.created_at_ms,j.resolution,j.workspace_id,j.client_request_id,j.current_attempt_id,a.attempt_id AS effective_attempt_id,COALESCE(a.bundle_path,'None') FROM classified c JOIN jobs j ON j.job_id=c.job_id JOIN attempts a ON a.attempt_id=COALESCE(j.current_attempt_id,(SELECT latest.attempt_id FROM attempts latest WHERE latest.job_id=j.job_id ORDER BY latest.attempt_number DESC LIMIT 1)) WHERE c.classification='eligible' ORDER BY c.created_at_ms,c.job_id LIMIT ?2"
        );
        let mut statement = connection
            .prepare(&sample_sql)
            .map_err(|error| RuntimeError::from_sql(error, "prepare archive eligible sample"))?;
        let rows = statement
            .query_map(params![cutoff_ms, sample_limit], |row| {
                Ok(RuntimeOperatorArchiveSample {
                    job_id: row.get(0)?,
                    created_at_ms: row.get(1)?,
                    resolution: row.get(2)?,
                    workspace_id: row.get(3)?,
                    client_request_id: row.get(4)?,
                    job_current_attempt_id: row.get(5)?,
                    effective_attempt_id: row.get(6)?,
                    bundle_path: row.get(7)?,
                })
            })
            .map_err(|error| RuntimeError::from_sql(error, "query archive eligible sample"))?;
        rows.map(|row| {
            row.map_err(|error| RuntimeError::from_sql(error, "decode archive eligible sample"))
        })
        .collect::<RuntimeResult<Vec<_>>>()?
    };

    Ok(RuntimeOperatorArchiveInspection {
        schema_version: RUNTIME_INSPECTION_SCHEMA_VERSION,
        generated_at_ms: now_ms()?,
        migration_version,
        by_classification,
        eligible_closure,
        eligible_sample,
    })
}
