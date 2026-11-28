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
        let snapshot = match db
            .observe_job_readonly(job, &self.config.source_sha256)
            .map_err(pg)?
        {
            PgJobReadback::Observed(s) => s,
            _ => return Err(error("inconclusive PG lifecycle")),
        };
        let (a, p, operation) = self.readback_attempt(&mut db, &snapshot)?;
        let j = db
            .client
            .query_one(
                "SELECT client_request_id,created_at_ms FROM jobs WHERE job_id=$1",
                &[&job],
            )
            .map_err(pg_read_error)?;
        let artifacts = read_artifact_summary(&mut db.client, job)?;
        let created = j.get::<_, i64>(1) as u64;
        let (episodes, timeline, events_truncated) =
            event_projection::read_job_events(&mut db.client, job, created, event_limit)?;
        let terminal = snapshot.resolution.is_some();
        let exit = db
            .client
            .query_one(
                "SELECT exit_code FROM attempts WHERE attempt_id=$1",
                &[&a.attempt_id],
            )
            .map_err(pg_read_error)?
            .get(0);
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
                result_available: terminal && artifacts.by_kind.contains_key("execution_result"),
                reservation_state: ReservationState::parse(&snapshot.reservation_state)?,
                reservation_release_reason: None,
                conditions: vec![],
                artifact_count: artifacts.count,
                artifact_bytes: artifacts.bytes,
                truncated_artifacts: artifacts.truncated,
            }],
            attempts_truncated: false,
            artifacts,
            episodes,
            timeline,
            events_truncated,
        })
    }
}

// Count and classification are observations of the same statement snapshot.
// The empty grouping set guarantees a zero total even without any artifacts.
fn read_artifact_summary(
    client: &mut postgres::Client,
    job: &str,
) -> RuntimeResult<RuntimeInspectionArtifactSummary> {
    let rows = client
        .query(
            "SELECT kind,count(*),COALESCE(sum(byte_length),0)::bigint,
                    count(*) FILTER(WHERE truncated),GROUPING(kind)
             FROM artifacts WHERE job_id=$1
             GROUP BY GROUPING SETS ((),(kind))",
            &[&job],
        )
        .map_err(pg_read_error)?;
    let mut total = None;
    let mut by_kind = std::collections::BTreeMap::new();
    for row in rows {
        let count = row.get::<_, i64>(1) as u64;
        if row.get::<_, i32>(4) == 1 {
            total = Some((
                count,
                row.get::<_, i64>(2) as u64,
                row.get::<_, i64>(3) as u64,
            ));
        } else {
            by_kind.insert(row.get::<_, String>(0), count);
        }
    }
    let (count, bytes, truncated) = total.ok_or_else(|| error("missing artifact summary"))?;
    Ok(RuntimeInspectionArtifactSummary {
        count,
        bytes,
        truncated,
        by_kind,
    })
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
            "CREATE TEMP TABLE artifacts(job_id text NOT NULL, kind text NOT NULL,
                byte_length bigint NOT NULL CHECK(byte_length>=0), truncated boolean NOT NULL);
             INSERT INTO artifacts VALUES
                ('j','stdout',0,false),('j','stdout',12,true),('j','stderr',3,false),
                ('other','stdout',99,true);",
        )
        .unwrap();
        let got = read_artifact_summary(&mut db, "j").unwrap();
        assert_eq!((got.count, got.bytes, got.truncated), (3, 15, 1));
        assert_eq!(got.by_kind.get("stdout"), Some(&2));
        assert_eq!(got.by_kind.get("stderr"), Some(&1));
        assert_eq!(got.by_kind.values().sum::<u64>(), got.count);
        let empty = read_artifact_summary(&mut db, "missing").unwrap();
        assert_eq!((empty.count, empty.bytes, empty.truncated), (0, 0, 0));
        assert!(empty.by_kind.is_empty());
    }
}
