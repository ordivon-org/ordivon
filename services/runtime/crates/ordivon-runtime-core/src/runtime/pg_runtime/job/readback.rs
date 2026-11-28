//! Projection-only Job inspection; no new dispatch, reconciliation or native effect.
use super::*;
impl PgRuntime {
    /// Projection only: never calls reconciliation or the OS execution provider.
    pub fn get(
        &self,
        principal: &str,
        job: &str,
        event_limit: u32,
    ) -> RuntimeResult<RuntimeJobInspection> {
        if event_limit > MAX_INSPECTION_EVENT_LIMIT {
            return Err(RuntimeError::invalid("event limit exceeded", "eventLimit"));
        }
        let mut db = self.store()?;
        self.authorize(&mut db, job, principal)?;
        let mut tx = db
            .client
            .build_transaction()
            .isolation_level(postgres::IsolationLevel::RepeatableRead)
            .read_only(true)
            .start()
            .map_err(pg_read_error)?;
        let snapshot =
            match PgAdmissionStore::observe_job_snapshot(&mut tx, job, &self.config.source_sha256)
                .map_err(pg)?
            {
                PgJobReadback::Observed(s) => s,
                _ => return Err(error("inconclusive PG lifecycle")),
            };
        let (a, p, operation, exit) = self.readback_attempt(&mut tx, &snapshot)?;
        let j = tx
            .query_one(
                "SELECT client_request_id,created_at_ms FROM jobs WHERE job_id=$1",
                &[&job],
            )
            .map_err(pg_read_error)?;
        let (artifacts, attempt_artifacts) = read_artifact_summaries(&mut tx, job, &a.attempt_id)?;
        let created = j.get::<_, i64>(1) as u64;
        let (episodes, timeline, events_truncated) =
            event_projection::read_job_events(&mut tx, job, created, event_limit)?;
        tx.commit().map_err(pg_read_error)?;
        let terminal = snapshot.resolution.is_some();
        Ok(RuntimeJobInspection {
            schema_version: 2,
            generated_at_ms: now()? as u64,
            migration_version: 0,
            job: RuntimeInspectionJob {
                job_id: job.into(),
                client_request_id: j.get(0),
                operation_digest: operation,
                workspace_id: p.workspace_id,
                source_revision: p.source_revision,
                workspace_source_digest: p.workspace_source_digest,
                created_at_ms: created,
                desired_state: if snapshot.desired_state == "run" {
                    JobDesiredState::Run
                } else {
                    JobDesiredState::Cancelled
                },
                resolution: snapshot
                    .resolution
                    .as_deref()
                    .map(JobResolution::parse)
                    .transpose()?,
                mechanically_converged: terminal,
                semantic_completion_evaluated: false,
            },
            attempts: vec![RuntimeInspectionAttempt {
                attempt_id: a.attempt_id,
                attempt_number: a.attempt_number,
                state: a.state,
                termination_intent: a.termination_intent,
                created_at_ms: a.created_at_ms,
                // Same committed Attempt snapshot as the terminal facts.
                // Runner binding is an observation, not physical process start.
                started_at_ms: snapshot.started_at_ms.and_then(|v| u64::try_from(v).ok()),
                finished_at_ms: snapshot.finished_at_ms.map(|v| v as u64),
                // Do not invent physical duration from mixed clock semantics.
                duration_ms: None,
                exit_code: exit,
                result_available: terminal
                    && attempt_artifacts.by_kind.contains_key("execution_result"),
                reservation_state: ReservationState::parse(&snapshot.reservation_state)?,
                reservation_release_reason: None,
                conditions: vec![],
                artifact_count: attempt_artifacts.count,
                artifact_bytes: attempt_artifacts.bytes,
                truncated_artifacts: attempt_artifacts.truncated,
            }],
            attempts_truncated: false,
            artifacts,
            episodes,
            timeline,
            events_truncated,
        })
    }
}

// Job inventory and selected Attempt evidence share one statement snapshot.
// The empty grouping set guarantees zero totals even without artifacts.
fn read_artifact_summaries(
    client: &mut impl postgres::GenericClient,
    job: &str,
    attempt: &str,
) -> RuntimeResult<(
    RuntimeInspectionArtifactSummary,
    RuntimeInspectionArtifactSummary,
)> {
    let rows = client
        .query(
            "SELECT kind,count(*),COALESCE(sum(byte_length),0)::bigint,
                    count(*) FILTER(WHERE truncated),GROUPING(kind),
                    count(*) FILTER(WHERE attempt_id=$2),
                    COALESCE(sum(byte_length) FILTER(WHERE attempt_id=$2),0)::bigint,
                    count(*) FILTER(WHERE truncated AND attempt_id=$2)
             FROM artifacts WHERE job_id=$1
             GROUP BY GROUPING SETS ((),(kind))",
            &[&job, &attempt],
        )
        .map_err(pg_read_error)?;
    let mut totals = [None, None];
    let mut kinds = [
        std::collections::BTreeMap::new(),
        std::collections::BTreeMap::new(),
    ];
    for row in rows {
        for (i, (count_col, bytes_col, truncated_col)) in [(1_usize, 2_usize, 3_usize), (5, 6, 7)]
            .into_iter()
            .enumerate()
        {
            let count = row.get::<_, i64>(count_col) as u64;
            if row.get::<_, i32>(4) == 1 {
                totals[i] = Some((
                    count,
                    row.get::<_, i64>(bytes_col) as u64,
                    row.get::<_, i64>(truncated_col) as u64,
                ));
            } else if count > 0 {
                kinds[i].insert(row.get::<_, String>(0), count);
            }
        }
    }
    let summary = |total: Option<(u64, u64, u64)>, by_kind| {
        let (count, bytes, truncated) = total.ok_or_else(|| error("missing artifact summary"))?;
        Ok(RuntimeInspectionArtifactSummary {
            count,
            bytes,
            truncated,
            by_kind,
        })
    };
    let [job_total, attempt_total] = totals;
    let [job_kinds, attempt_kinds] = kinds;
    Ok((
        summary(job_total, job_kinds)?,
        summary(attempt_total, attempt_kinds)?,
    ))
}

#[cfg(test)]
mod artifact_summary_tests {
    use super::*;

    #[test]
    #[ignore = "requires isolated native PostgreSQL fixture"]
    fn pg18_job_artifact_summary_groups_and_total_agree() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN").expect("disposable PG DSN");
        let mut db = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
        db.batch_execute(
            "CREATE TEMP TABLE artifacts(job_id text NOT NULL, attempt_id text NOT NULL, kind text NOT NULL,
                byte_length bigint NOT NULL CHECK(byte_length>=0), truncated boolean NOT NULL);
             INSERT INTO artifacts VALUES
                ('j','current','stdout',0,false),('j','current','stdout',12,true),('j','prior','stderr',3,false),
                ('other','current','stdout',99,true);",
        )
        .unwrap();
        let (got, selected) = read_artifact_summaries(&mut db, "j", "current").unwrap();
        assert_eq!(
            (selected.count, selected.bytes, selected.truncated),
            (2, 12, 1)
        );
        assert_eq!(selected.by_kind.get("stdout"), Some(&2));
        assert!(!selected.by_kind.contains_key("stderr"));
        assert_eq!((got.count, got.bytes, got.truncated), (3, 15, 1));
        assert_eq!(got.by_kind.get("stdout"), Some(&2));
        assert_eq!(got.by_kind.get("stderr"), Some(&1));
        assert_eq!(got.by_kind.values().sum::<u64>(), got.count);
        let (empty, selected_empty) =
            read_artifact_summaries(&mut db, "missing", "current").unwrap();
        assert_eq!(selected_empty.count, 0);
        assert!(selected_empty.by_kind.is_empty());
        assert_eq!((empty.count, empty.bytes, empty.truncated), (0, 0, 0));
        assert!(empty.by_kind.is_empty());
    }
}
