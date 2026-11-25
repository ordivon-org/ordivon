//! Project terminal artifacts or bounded active previews from observed facts.
//! Projection itself never admits or reissues native effects.

use super::{
    active_log_window, error, io, needs_recovery_observation, output_projection_relative_path, pg,
    pg_delivery_disposition, universal, verified_terminal_log_window, JobObservation,
    JobObserveRequest, PgAdmissionStore, PgRuntime, RuntimeError, RuntimeErrorCode, RuntimeResult,
};
use serde_json::json;
use std::path::Path;

impl PgRuntime {
    pub(in crate::runtime::pg_runtime) fn project(
        &self,
        db: &mut PgAdmissionStore,
        request: &JobObserveRequest,
    ) -> RuntimeResult<JobObservation> {
        let readback = match db
            .observe_job_projection_readonly(&request.job_id, &self.config.source_sha256)
            .map_err(pg)?
        {
            Some(s) => s,
            None => {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::ReconciliationRequired,
                    "committed PG Job lacks coherent exact lifecycle evidence",
                    Some("jobId"),
                    false,
                )
                .with_operation_id(&request.job_id))
            }
        };
        let snapshot = readback.snapshot;
        let (a, p, operation) = self.readback_attempt(db, &snapshot)?;
        let terminal = snapshot.resolution.is_some();
        let rows = readback.artifacts;
        let artifacts = rows.iter().map(|row| {
            let r = &row.registration;
            json!({"artifactId":r.artifact_id,"attemptId":row.attempt_id,"kind":r.kind,"digest":r.digest,"retainedBytes":r.byte_length,"truncated":r.truncated})
        }).collect::<Vec<_>>();
        let exit = readback.exit_code;
        // Preserve the existing projection for historical terminal variants.
        // An OS-only LOST reconciliation is the new explicit exception:
        // it has a committed native-stop Artifact, not a Runner result.json.
        let result_available = terminal
            && rows.iter().any(|row| {
                row.attempt_id == a.attempt_id && row.registration.kind == "execution_result"
            });
        let delivery = pg_delivery_disposition(snapshot.resolution.as_deref(), result_available);
        let mut value = json!({"jobId":request.job_id,"operationDigest":operation,"status":snapshot.resolution.clone().unwrap_or(snapshot.attempt_state.clone()),"desiredState":snapshot.desired_state,"attemptId":a.attempt_id,"attemptState":snapshot.attempt_state,"terminationIntent":snapshot.termination_intent,"exitCode":exit,"executionTerminal":terminal,"executionDisposition":snapshot.resolution,"deliveryDisposition":delivery,"effectiveLimits":{"timeoutMs":p.timeout_ms,"stdoutLimitBytes":p.stdout_limit_bytes,"stderrLimitBytes":p.stderr_limit_bytes},"recoveryRequired":needs_recovery_observation(a.state, terminal),"semanticCompletionEvaluated":false,"resultAvailable":result_available,"artifactsAvailable":!artifacts.is_empty(),"artifacts":artifacts});
        for (kind, limit, offset) in [
            ("stdout", request.stdout_tail_bytes, request.stdout_offset),
            ("stderr", request.stderr_tail_bytes, request.stderr_offset),
        ] {
            // Lost/orphaned or other no-Artifact terminal outcomes have no
            // committed stream bytes. Do not fail observation merely because
            // a log is absent, and never project unregistered terminal bytes.
            let registered = if terminal {
                rows.iter()
                    .find(|row| row.attempt_id == a.attempt_id && row.registration.kind == kind)
                    .map(|row| &row.registration)
            } else {
                None
            };
            if terminal && registered.is_none() {
                continue;
            }
            let relative = registered.map(|row| row.relative_path.as_str());
            let relative_path = output_projection_relative_path(kind, terminal, relative)?;
            let path = Path::new(&a.bundle_path).join(&relative_path);
            if path.exists() {
                let (window, begin, end, available) = if terminal {
                    // The terminal log is immutable evidence. Verify the entire
                    // exact file against PostgreSQL before returning any bytes.
                    let expected = registered
                        .ok_or_else(|| error("terminal output Artifact registration missing"))?;
                    let dir = universal::open_directory_nofollow(Path::new(&a.bundle_path))
                        .map_err(io)?;
                    let file = universal::open_regular_file_beneath(&dir, &relative_path, true)
                        .map_err(io)?;
                    verified_terminal_log_window(
                        file,
                        self.config.executor.max_output_bytes,
                        expected.byte_length,
                        &expected.digest,
                        offset,
                        limit,
                    )?
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
