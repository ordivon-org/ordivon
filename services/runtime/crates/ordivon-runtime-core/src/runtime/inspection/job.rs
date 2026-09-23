pub fn inspect_job(
    config: &RuntimeInspectionConfig,
    job_id: &str,
    event_limit: u32,
    include_detail: bool,
) -> RuntimeResult<RuntimeJobInspection> {
    if job_id.is_empty() {
        return Err(RuntimeError::invalid("jobId must not be empty", "jobId"));
    }
    if event_limit == 0 || event_limit > MAX_INSPECTION_EVENT_LIMIT {
        return Err(RuntimeError::invalid(
            format!("eventLimit must be in 1..={MAX_INSPECTION_EVENT_LIMIT}"),
            "eventLimit",
        ));
    }
    let (connection, migration_version) = open_read_only(config)?;
    let job = RegistryStorageBoundary::load_job(&connection, job_id)?;
    let plan: RuntimeExecutionPlan =
        serde_json::from_str(&job.execution_plan_json).map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                format!("stored execution plan is invalid: {error}"),
                Some("executionPlan"),
                false,
            )
        })?;

    let mut attempt_ids: Vec<String> = Vec::new();
    let mut statement = connection
        .prepare("SELECT attempt_id FROM attempts WHERE job_id=?1 ORDER BY attempt_number LIMIT ?2")
        .map_err(|error| RuntimeError::from_sql(error, "prepare Job Attempt inspection"))?;
    let rows = statement
        .query_map(params![job_id, MAX_INSPECTION_ATTEMPTS + 1], |row| {
            row.get(0)
        })
        .map_err(|error| RuntimeError::from_sql(error, "query Job Attempts"))?;
    for row in rows {
        attempt_ids.push(
            row.map_err(|error| RuntimeError::from_sql(error, "decode Job Attempt identity"))?,
        );
    }
    let attempts_truncated = attempt_ids.len() > MAX_INSPECTION_ATTEMPTS as usize;
    attempt_ids.truncate(MAX_INSPECTION_ATTEMPTS as usize);

    let mut attempts = Vec::with_capacity(attempt_ids.len());
    for attempt_id in attempt_ids {
        let attempt = RegistryStorageBoundary::load_attempt(&connection, &attempt_id)?;
        let reservation = RegistryStorageBoundary::load_reservation(&connection, &attempt_id)?;
        let conditions = load_conditions(&connection, migration_version, &attempt_id)?;
        let (artifact_count, artifact_bytes, truncated_artifacts) = connection
            .query_row(
                "SELECT COUNT(*),COALESCE(SUM(byte_length),0),COALESCE(SUM(truncated),0) FROM artifacts WHERE attempt_id=?1",
                [&attempt_id],
                |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?)),
            )
            .map_err(|error| RuntimeError::from_sql(error, "summarize Attempt Artifacts"))?;
        attempts.push(RuntimeInspectionAttempt {
            attempt_id: attempt.attempt_id,
            attempt_number: attempt.attempt_number,
            state: attempt.state,
            termination_intent: attempt.termination_intent,
            created_at_ms: attempt.created_at_ms,
            started_at_ms: attempt.started_at_ms,
            finished_at_ms: attempt.finished_at_ms,
            duration_ms: attempt
                .finished_at_ms
                .map(|finished| finished.saturating_sub(attempt.created_at_ms)),
            exit_code: attempt.exit_code,
            result_available: attempt.result_digest.is_some(),
            reservation_state: reservation.state,
            reservation_release_reason: reservation.release_reason,
            conditions,
            artifact_count,
            artifact_bytes,
            truncated_artifacts,
        });
    }

    let artifacts = summarize_job_artifacts(&connection, job_id)?;
    let episodes = summarize_job_episodes(&connection, job_id)?;
    let total_events: u64 = connection
        .query_row(
            "SELECT COUNT(*) FROM job_events WHERE job_id=?1",
            [job_id],
            |row| row.get(0),
        )
        .map_err(|error| RuntimeError::from_sql(error, "count Job events"))?;
    let timeline = load_timeline(
        &connection,
        job_id,
        job.created_at_ms,
        event_limit,
        include_detail,
    )?;
    let recovery_required_sql = if migration_version >= CONDITION_RETIREMENT_MIGRATION_VERSION {
        "SELECT COUNT(*) FROM attempts WHERE job_id=?1 AND recovery_required=1"
    } else {
        "SELECT COUNT(*) FROM attempts a JOIN attempt_conditions c ON c.attempt_id=a.attempt_id WHERE a.job_id=?1 AND c.condition_type='recovery_required' AND c.status='true'"
    };
    let recovery_required: u64 = connection
        .query_row(recovery_required_sql, [job_id], |row| row.get(0))
        .map_err(|error| RuntimeError::from_sql(error, "count active Job recovery conditions"))?;
    let mechanically_converged = job.resolution.is_some()
        && !attempts_truncated
        && recovery_required == 0
        && attempts.iter().all(|attempt| attempt.state.is_terminal())
        && attempts
            .iter()
            .all(|attempt| attempt.reservation_state == ReservationState::Released);

    Ok(RuntimeJobInspection {
        schema_version: RUNTIME_INSPECTION_SCHEMA_VERSION,
        generated_at_ms: now_ms()?,
        migration_version,
        job: RuntimeInspectionJob {
            job_id: job.job_id,
            client_request_id: job.client_request_id,
            operation_digest: job.operation_digest,
            workspace_id: job.workspace_id,
            source_revision: plan.source_revision,
            workspace_source_digest: plan.workspace_source_digest,
            created_at_ms: job.created_at_ms,
            desired_state: job.desired_state,
            resolution: job.resolution,
            mechanically_converged,
            semantic_completion_evaluated: false,
        },
        attempts,
        attempts_truncated,
        artifacts,
        episodes,
        timeline,
        events_truncated: total_events > u64::from(event_limit),
    })
}

fn open_read_only(config: &RuntimeInspectionConfig) -> RuntimeResult<(Connection, i64)> {
    open_read_only_with_schema_policy(config, true)
}

#[cfg(feature = "operator-tools")]
fn open_operator_read_only(config: &RuntimeInspectionConfig) -> RuntimeResult<(Connection, i64)> {
    open_read_only_with_schema_policy(config, false)
}

fn open_read_only_with_schema_policy(
    config: &RuntimeInspectionConfig,
    reject_future_schema: bool,
) -> RuntimeResult<(Connection, i64)> {
    if !config.db_path.is_absolute() {
        return Err(RuntimeError::invalid(
            "database path must be absolute",
            "database",
        ));
    }
    if config.busy_timeout_ms == 0 {
        return Err(RuntimeError::invalid(
            "busyTimeoutMs must be positive",
            "busyTimeoutMs",
        ));
    }
    let flags = OpenFlags::SQLITE_OPEN_READ_ONLY | OpenFlags::SQLITE_OPEN_NO_MUTEX;
    let connection = Connection::open_with_flags(&config.db_path, flags)
        .map_err(|error| RuntimeError::from_sql(error, "cannot open Runtime Registry read-only"))?;
    connection
        .busy_timeout(Duration::from_millis(config.busy_timeout_ms))
        .map_err(|error| RuntimeError::from_sql(error, "cannot set inspection busy timeout"))?;
    connection
        .pragma_update(None, "query_only", true)
        .map_err(|error| {
            RuntimeError::from_sql(error, "cannot enable inspection query-only mode")
        })?;
    connection
        .pragma_update(None, "trusted_schema", false)
        .map_err(|error| RuntimeError::from_sql(error, "cannot disable trusted schema"))?;
    connection
        .execute_batch("BEGIN")
        .map_err(|error| RuntimeError::from_sql(error, "cannot begin inspection read snapshot"))?;
    debug_assert!(!connection.is_autocommit());
    // Ordinary Agent-facing inspection is a bounded projection over one read snapshot.
    // A full Registry integrity scan is deliberately owned by Runtime doctor/repair and
    // backup/restore paths; coupling every projection to PRAGMA integrity_check makes
    // point reads scale with the entire durable Registry rather than the requested object.
    let migration_version: i64 = if reject_future_schema {
        connection
            .query_row(
                "SELECT COALESCE(MAX(version),0) FROM schema_migrations",
                [],
                |row| row.get(0),
            )
            .map_err(|error| RuntimeError::from_sql(error, "cannot read Registry migration version"))?
    } else {
        let has_migrations: bool = connection
            .query_row(
                "SELECT EXISTS(SELECT 1 FROM sqlite_schema WHERE type='table' AND name='schema_migrations')",
                [],
                |row| row.get(0),
            )
            .map_err(|error| RuntimeError::from_sql(error, "cannot inspect Registry migration capability"))?;
        if has_migrations {
            connection
                .query_row(
                    "SELECT COALESCE(MAX(version),0) FROM schema_migrations",
                    [],
                    |row| row.get(0),
                )
                .map_err(|error| RuntimeError::from_sql(error, "cannot read optional Registry migration version"))?
        } else {
            0
        }
    };
    if reject_future_schema && migration_version > MAX_MIGRATION_VERSION {
        return Err(RuntimeError::new(
            RuntimeErrorCode::SchemaVersionUnsupported,
            format!(
                "Registry schema {migration_version} is newer than supported {MAX_MIGRATION_VERSION}"
            ),
            None,
            false,
        ));
    }
    Ok((connection, migration_version))
}

fn load_conditions(
    connection: &Connection,
    migration_version: i64,
    attempt_id: &str,
) -> RuntimeResult<Vec<RuntimeInspectionCondition>> {
    if migration_version < CONDITION_RETIREMENT_MIGRATION_VERSION {
        let mut statement = connection
            .prepare(
                "SELECT condition_type,status,reason_code,observed_at_ms FROM attempt_conditions WHERE attempt_id=?1 ORDER BY condition_type",
            )
            .map_err(|error| RuntimeError::from_sql(error, "prepare legacy Attempt condition inspection"))?;
        let rows = statement
            .query_map([attempt_id], |row| {
                Ok(RuntimeInspectionCondition {
                    condition_type: row.get(0)?,
                    status: row.get(1)?,
                    reason_code: row.get(2)?,
                    observed_at_ms: row.get(3)?,
                })
            })
            .map_err(|error| RuntimeError::from_sql(error, "query legacy Attempt conditions"))?;
        return rows
            .map(|row| {
                row.map_err(|error| {
                    RuntimeError::from_sql(error, "decode legacy Attempt condition")
                })
            })
            .collect();
    }

    let sql = r#"
WITH runner_latest AS (
    SELECT attempt_id,reason_code,observed_at_ms,
           ROW_NUMBER() OVER(PARTITION BY attempt_id ORDER BY event_sequence DESC) AS rn
    FROM job_events WHERE event_type='RUNNER_BOUND'
),
result_event AS (
    SELECT a.attempt_id,e.reason_code,e.observed_at_ms,
           ROW_NUMBER() OVER(PARTITION BY a.attempt_id ORDER BY e.event_sequence DESC) AS rn
    FROM attempts a
    JOIN job_events e ON e.attempt_id=a.attempt_id AND e.observed_at_ms=a.finished_at_ms
    WHERE a.result_digest IS NOT NULL
      AND e.event_type IN ('JOB_TERMINAL','RUNNER_RESULT_RECOVERED','ADMIN_TERMINAL_REPAIR','JOB_RESOLUTION_ADMIN_CORRECTED')
),
derived AS (
    SELECT attempt_id,'bundle_ready' AS condition_type,'true' AS status,reason_code,observed_at_ms
    FROM job_events WHERE event_type='BUNDLE_READY'
    UNION ALL
    SELECT attempt_id,'dispatch_issued','true',reason_code,observed_at_ms
    FROM job_events WHERE event_type='DISPATCH_ISSUED'
    UNION ALL
    SELECT attempt_id,'runner_bound','true',reason_code,observed_at_ms
    FROM runner_latest WHERE rn=1
    UNION ALL
    SELECT attempt_id,'result_available','true',reason_code,observed_at_ms
    FROM result_event WHERE rn=1
    UNION ALL
    SELECT a.attempt_id,'reservation_held',
           CASE r.state WHEN 'active' THEN 'true' WHEN 'held_orphaned' THEN 'held_orphaned' ELSE 'false' END,
           CASE WHEN r.state='active' THEN 'CAPACITY_RESERVED' ELSE r.release_reason END,
           r.state_observed_at_ms
    FROM attempts a JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id
    UNION ALL
    SELECT attempt_id,'recovery_required',CASE recovery_required WHEN 1 THEN 'true' ELSE 'false' END,
           recovery_reason_code,recovery_observed_at_ms
    FROM attempts WHERE recovery_required IS NOT NULL
)
SELECT condition_type,status,reason_code,observed_at_ms
FROM derived WHERE attempt_id=?1 ORDER BY condition_type
"#;
    let mut statement = connection.prepare(sql).map_err(|error| {
        RuntimeError::from_sql(error, "prepare derived Attempt condition inspection")
    })?;
    let rows = statement
        .query_map([attempt_id], |row| {
            Ok(RuntimeInspectionCondition {
                condition_type: row.get(0)?,
                status: row.get(1)?,
                reason_code: row.get(2)?,
                observed_at_ms: row.get(3)?,
            })
        })
        .map_err(|error| RuntimeError::from_sql(error, "query derived Attempt conditions"))?;
    rows.map(|row| {
        row.map_err(|error| RuntimeError::from_sql(error, "decode derived Attempt condition"))
    })
    .collect()
}

fn summarize_job_artifacts(
    connection: &Connection,
    job_id: &str,
) -> RuntimeResult<RuntimeInspectionArtifactSummary> {
    let (count, bytes, truncated): (u64, u64, u64) = connection
        .query_row(
            "SELECT COUNT(*),COALESCE(SUM(byte_length),0),COALESCE(SUM(truncated),0) FROM artifacts WHERE job_id=?1",
            [job_id],
            |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?)),
        )
        .map_err(|error| RuntimeError::from_sql(error, "summarize Job Artifacts"))?;
    let mut by_kind = BTreeMap::new();
    let mut statement = connection
        .prepare("SELECT kind,COUNT(*) FROM artifacts WHERE job_id=?1 GROUP BY kind ORDER BY kind")
        .map_err(|error| RuntimeError::from_sql(error, "prepare Job Artifact kinds"))?;
    let rows = statement
        .query_map([job_id], |row| {
            Ok((row.get::<_, String>(0)?, row.get::<_, u64>(1)?))
        })
        .map_err(|error| RuntimeError::from_sql(error, "query Job Artifact kinds"))?;
    for row in rows {
        let (kind, value) =
            row.map_err(|error| RuntimeError::from_sql(error, "decode Job Artifact kind"))?;
        by_kind.insert(kind, value);
    }
    Ok(RuntimeInspectionArtifactSummary {
        count,
        bytes,
        truncated,
        by_kind,
    })
}

fn summarize_job_episodes(
    connection: &Connection,
    job_id: &str,
) -> RuntimeResult<RuntimeInspectionEpisodes> {
    let counts = grouped_job_event_counts(connection, job_id)?;
    let duplicate_dispatches: u64 = connection
        .query_row(
            "SELECT COALESCE(SUM(extra),0) FROM (SELECT COUNT(*)-1 extra FROM job_events WHERE job_id=?1 AND event_type='DISPATCH_ISSUED' GROUP BY attempt_id HAVING COUNT(*)>1)",
            [job_id],
            |row| row.get(0),
        )
        .map_err(|error| RuntimeError::from_sql(error, "summarize Job duplicate dispatches"))?;
    Ok(RuntimeInspectionEpisodes {
        dispatches: count_key(&counts, "DISPATCH_ISSUED"),
        duplicate_dispatches,
        stop_requests: count_key(&counts, "STOP_REQUESTED"),
        reconciliation_failures: count_key(&counts, "RECONCILIATION_FAILED"),
        reconciliation_convergences: count_key(&counts, "RECONCILIATION_CONVERGED"),
        runner_result_recoveries: count_key(&counts, "RUNNER_RESULT_RECOVERED"),
        resolution_corrections: count_key(&counts, "JOB_RESOLUTION_CORRECTED"),
        administrative_repairs: count_key(&counts, "ADMIN_TERMINAL_REPAIR"),
    })
}

fn load_timeline(
    connection: &Connection,
    job_id: &str,
    created_at_ms: u64,
    event_limit: u32,
    include_detail: bool,
) -> RuntimeResult<Vec<RuntimeInspectionEvent>> {
    let mut statement = connection
        .prepare(
            "SELECT event_sequence,attempt_id,event_type,origin,previous_state,new_state,reason_code,detail_json,observed_at_ms FROM job_events WHERE job_id=?1 ORDER BY event_sequence LIMIT ?2",
        )
        .map_err(|error| RuntimeError::from_sql(error, "prepare Job timeline"))?;
    let rows = statement
        .query_map(params![job_id, event_limit], |row| {
            Ok((
                row.get::<_, u64>(0)?,
                row.get::<_, Option<String>>(1)?,
                row.get::<_, String>(2)?,
                row.get::<_, String>(3)?,
                row.get::<_, Option<String>>(4)?,
                row.get::<_, Option<String>>(5)?,
                row.get::<_, String>(6)?,
                row.get::<_, String>(7)?,
                row.get::<_, u64>(8)?,
            ))
        })
        .map_err(|error| RuntimeError::from_sql(error, "query Job timeline"))?;
    let mut result = Vec::new();
    let mut previous_at = created_at_ms;
    for row in rows {
        let (
            sequence,
            attempt_id,
            event_type,
            origin,
            previous_state,
            new_state,
            reason_code,
            detail_json,
            observed_at_ms,
        ) = row.map_err(|error| RuntimeError::from_sql(error, "decode Job timeline"))?;
        let detail = if include_detail {
            Some(serde_json::from_str(&detail_json).map_err(|error| {
                RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    format!("Job event detail is invalid JSON: {error}"),
                    Some("detailJson"),
                    false,
                )
            })?)
        } else {
            None
        };
        result.push(RuntimeInspectionEvent {
            sequence,
            attempt_id,
            event_type,
            origin,
            previous_state,
            new_state,
            reason_code,
            observed_at_ms,
            elapsed_ms: observed_at_ms.saturating_sub(created_at_ms),
            delta_ms: observed_at_ms.saturating_sub(previous_at),
            detail,
        });
        previous_at = observed_at_ms;
    }
    Ok(result)
}

fn grouped_job_event_counts(
    connection: &Connection,
    job_id: &str,
) -> RuntimeResult<BTreeMap<String, u64>> {
    let mut statement = connection
        .prepare(
            "SELECT event_type,COUNT(*) FROM job_events WHERE job_id=?1 GROUP BY event_type ORDER BY event_type",
        )
        .map_err(|error| RuntimeError::from_sql(error, "prepare Job event counts"))?;
    let rows = statement
        .query_map([job_id], |row| {
            Ok((row.get::<_, String>(0)?, row.get::<_, u64>(1)?))
        })
        .map_err(|error| RuntimeError::from_sql(error, "query Job event counts"))?;
    let mut counts = BTreeMap::new();
    for row in rows {
        let (event_type, value) =
            row.map_err(|error| RuntimeError::from_sql(error, "decode Job event count"))?;
        counts.insert(event_type, value);
    }
    Ok(counts)
}

fn count_key(counts: &BTreeMap<String, u64>, key: &str) -> u64 {
    counts.get(key).copied().unwrap_or(0)
}

fn now_ms() -> RuntimeResult<u64> {
    let value = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryUnavailable,
                format!("system clock is before the Unix epoch: {error}"),
                None,
                false,
            )
        })?
        .as_millis();
    u64::try_from(value).map_err(|_| {
        RuntimeError::new(
            RuntimeErrorCode::RegistryUnavailable,
            "current time exceeds the Runtime timestamp range",
            None,
            false,
        )
    })
}
