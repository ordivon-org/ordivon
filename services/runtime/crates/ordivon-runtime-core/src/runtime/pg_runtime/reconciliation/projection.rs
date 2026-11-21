//! Project terminal artifacts or bounded active previews from observed facts.
//! Projection itself never admits or reissues native effects.

use super::*;

impl PgRuntime {
    pub(in crate::runtime::pg_runtime) fn project(
        &self,
        db: &mut PgAdmissionStore,
        request: &JobObserveRequest,
    ) -> RuntimeResult<JobObservation> {
        let snapshot = match db
            .observe_job_readonly(&request.job_id, &self.config.source_sha256)
            .map_err(pg)?
        {
            PgJobReadback::Observed(s) => s,
            PgJobReadback::Inconclusive => {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::ReconciliationRequired,
                    "committed PG Job lacks coherent exact lifecycle evidence",
                    Some("jobId"),
                    false,
                )
                .with_operation_id(&request.job_id))
            }
        };
        let (a, p, operation) = self.readback_attempt(db, &snapshot)?;
        let terminal = snapshot.resolution.is_some();
        let rows=db.client.query("SELECT artifact_id,kind,digest,byte_length,truncated,relative_path FROM artifacts WHERE job_id=$1 ORDER BY artifact_id", &[&request.job_id]).map_err(pg_read_error)?;
        let artifacts=rows.iter().map(|r|json!({"artifactId":r.get::<_,String>(0),"attemptId":a.attempt_id,"kind":r.get::<_,String>(1),"digest":r.get::<_,String>(2),"retainedBytes":r.get::<_,i64>(3),"truncated":r.get::<_,bool>(4)})).collect::<Vec<_>>();
        let exit: Option<i32> = db
            .client
            .query_one(
                "SELECT exit_code FROM attempts WHERE attempt_id=$1",
                &[&a.attempt_id],
            )
            .map_err(pg_read_error)?
            .get(0);
        // Preserve the existing projection for historical terminal variants.
        // An OS-only LOST reconciliation is the new explicit exception:
        // it has a committed native-stop Artifact, not a Runner result.json.
        let result_available = terminal
            && rows
                .iter()
                .any(|row| row.get::<_, String>(1) == "execution_result");
        let delivery = pg_delivery_disposition(snapshot.resolution.as_deref(), result_available);
        let mut value = json!({"jobId":request.job_id,"operationDigest":operation,"status":snapshot.resolution.clone().unwrap_or(snapshot.attempt_state.clone()),"desiredState":snapshot.desired_state,"attemptId":a.attempt_id,"attemptState":snapshot.attempt_state,"terminationIntent":snapshot.termination_intent,"exitCode":exit,"executionTerminal":terminal,"executionDisposition":snapshot.resolution,"deliveryDisposition":delivery,"effectiveLimits":{"timeoutMs":p.timeout_ms,"stdoutLimitBytes":p.stdout_limit_bytes,"stderrLimitBytes":p.stderr_limit_bytes},"recoveryRequired":needs_recovery_observation(a.state, terminal),"semanticCompletionEvaluated":false,"resultAvailable":result_available,"artifactsAvailable":!artifacts.is_empty(),"artifacts":artifacts});
        for (kind, limit, offset) in [
            ("stdout", request.stdout_tail_bytes, request.stdout_offset),
            ("stderr", request.stderr_tail_bytes, request.stderr_offset),
        ] {
            // Lost/orphaned or other no-Artifact terminal outcomes have no
            // committed stream bytes. Do not fail observation merely because
            // a log is absent, and never project unregistered terminal bytes.
            if terminal && !rows.iter().any(|row| row.get::<_, String>(1) == kind) {
                continue;
            }
            let registered = if terminal {
                rows.iter().find(|row| row.get::<_, String>(1) == kind)
            } else {
                None
            };
            let relative: Option<String> = registered.map(|row| row.get(5));
            let relative_path =
                output_projection_relative_path(kind, terminal, relative.as_deref())?;
            let path = Path::new(&a.bundle_path).join(&relative_path);
            if path.exists() {
                let (window, begin, end, available) = if terminal {
                    // The terminal log is immutable evidence. Verify the entire
                    // exact file against PostgreSQL before returning any bytes.
                    let bytes = {
                        use std::io::Read;
                        let dir = universal::open_directory_nofollow(Path::new(&a.bundle_path))
                            .map_err(io)?;
                        let file = universal::open_regular_file_beneath(&dir, &relative_path, true)
                            .map_err(io)?;
                        let mut bytes = vec![];
                        file.take(self.config.executor.max_output_bytes + 1)
                            .read_to_end(&mut bytes)
                            .map_err(io)?;
                        if bytes.len() as u64 > self.config.executor.max_output_bytes {
                            return Err(error("output exceeds retained ceiling"));
                        }
                        bytes
                    };
                    let available = bytes.len() as u64;
                    let begin = offset
                        .unwrap_or(available.saturating_sub(limit))
                        .min(available);
                    let end = begin.saturating_add(limit).min(available);
                    let expected = registered
                        .ok_or_else(|| error("terminal output Artifact registration missing"))?;
                    if expected.get::<_, i64>(3) != bytes.len() as i64
                        || expected.get::<_, String>(2) != universal::sha256_bytes(&bytes)
                    {
                        return Err(RuntimeError::new(
                            RuntimeErrorCode::ArtifactIdentityConflict,
                            "terminal output bytes disagree with PostgreSQL Artifact evidence",
                            Some("artifact"),
                            false,
                        ));
                    }
                    (
                        bytes[begin as usize..end as usize].to_vec(),
                        begin,
                        end,
                        available,
                    )
                } else {
                    active_log_window(&path, self.config.executor.max_output_bytes, offset, limit)?
                };
                value[format!("{kind}Tail")] = json!(String::from_utf8_lossy(&window));
                value[format!("{kind}Offset")] = json!(begin);
                value[format!("{kind}NextOffset")] = json!(end);
                value[format!("{kind}AvailableBytes")] = json!(available);
                value[format!("{kind}Eof")] = json!(end == available);
            } else if terminal {
                return Err(error("terminal output Artifact file missing"));
            }
        }
        serde_json::from_value(value).map_err(io)
    }
}
