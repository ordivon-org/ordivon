//! Fresh PostgreSQL execution vertical. No SQLite Registry is opened.
//! One durable dispatch generation; ambiguous launch is never automatically retried.
use super::job_attempt_state::{JobIdentityContract, OperationIdentityBindings};
use super::*;
use crate::pg_admission::*;
use crate::universal::{self, RunnerRequest, RunnerStartEvidence};
use crate::{
    CompactWorkspaceOpenResult, GitWorkspaceCreateRequest, PgJobReadback, UniversalExecutorConfig,
    WorkspaceCloseRequest, WorkspaceCloseResult, WorkspaceMutateRequest, WorkspaceMutateResult,
};
use serde_json::json;
use std::{
    fs,
    path::{Path, PathBuf},
    thread,
    time::{Duration, Instant},
};
use uuid::Uuid;

#[derive(Clone)]
pub struct PgRuntimeConfig {
    pub dsn: String,
    pub schema: String,
    pub source_sha256: String,
    pub executor: UniversalExecutorConfig,
}

#[derive(Clone)]
pub struct PgRuntime {
    config: PgRuntimeConfig,
}

fn error(message: impl Into<String>) -> RuntimeError {
    RuntimeError::new(RuntimeErrorCode::RegistryUnavailable, message, None, false)
}
fn pg(e: PgAdmissionError) -> RuntimeError {
    let code = match e {
        PgAdmissionError::IdempotencyConflict => RuntimeErrorCode::IdempotencyConflict,
        PgAdmissionError::Capacity => RuntimeErrorCode::ConcurrencyLimit,
        PgAdmissionError::UnknownCommit => RuntimeErrorCode::DispatchOutcomeUnknown,
        _ => RuntimeErrorCode::RegistryUnavailable,
    };
    RuntimeError::new(code, format!("PostgreSQL Runtime: {e:?}"), None, false)
}
fn io(e: impl std::fmt::Display) -> RuntimeError {
    error(e.to_string())
}

// Shared by existing Workspace effect paths; the filesystem effect has
// already happened when this PostgreSQL COMMIT acknowledgment is inspected.
fn workspace_effect_commit<E: std::fmt::Display>(
    receipt: Result<(), E>,
    operation: &str,
) -> RuntimeResult<()> {
    receipt.map_err(|e| {
        RuntimeError::new(
            RuntimeErrorCode::DispatchOutcomeUnknown,
            format!(
                "{operation} filesystem effect may have completed; PostgreSQL COMMIT outcome is unknown ({e}); inspect Workspace state before retry"
            ),
            None,
            false,
        )
    })
}
fn now() -> RuntimeResult<i64> {
    Ok(universal::now_unix_ms().map_err(io)? as i64)
}
fn encode<T: serde::Serialize>(v: &T) -> RuntimeResult<String> {
    serde_json::to_string(v).map_err(io)
}
fn decode<T: serde::de::DeserializeOwned>(s: &str) -> RuntimeResult<T> {
    serde_json::from_str(s).map_err(io)
}

mod artifact;
mod job;
mod node_query;
mod workspace;

impl PgRuntime {
    pub fn new(config: PgRuntimeConfig) -> RuntimeResult<Self> {
        // Pure preflight first: an unqualified or unreachable PG writer must
        // never create Workspace/cache directories before source admission.
        config.executor.validate().map_err(io)?;
        if config.source_sha256.len() != 64
            || !config.source_sha256.bytes().all(|b| b.is_ascii_hexdigit())
        {
            return Err(RuntimeError::invalid(
                "source SHA-256 required",
                "sourceSha256",
            ));
        }
        let runtime = Self { config };
        // Fail closed before advertising a live MCP endpoint. Schema existence is
        // NOT permission to admit new Jobs. Qualification is an external,
        // operator-owned PG record and must match the exact configured source.
        // Never bootstrap, promote, or silently authorize this process.
        let mut db = runtime.store()?;
        let row=db.client.query_opt(
            "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='source'",
            &[]
        ).map_err(io)?;
        let qualified = match row {
            Some(row) => {
                row.get::<_, String>(0) == "QUALIFIED_WRITER"
                    && row.get::<_, String>(1) == runtime.config.source_sha256
                    && row.get::<_, bool>(2)
            }
            None => false,
        };
        if !qualified {
            return Err(error(
                "PG Runtime source writer not qualified; refusing startup",
            ));
        }
        crate::pg_admission::require_pg_writer_epoch(
            &mut db.client,
            &runtime.config.source_sha256,
            false,
        )
        .map_err(pg)?;
        // Authorization includes the independently controlled app-role
        // privilege check in store(); only now may native paths be created.
        runtime.config.executor.ensure_store().map_err(io)?;
        Ok(runtime)
    }
    fn store(&self) -> RuntimeResult<PgAdmissionStore> {
        let mut db =
            PgAdmissionStore::connect(&self.config.dsn, &self.config.schema).map_err(pg)?;
        // Qualification is not independently controlled if the app owns the
        // stage table, inherits its owner's role, or can rewrite protected
        // fields. The authenticated session_user can SET ROLE NONE to regain
        // its privileges, so the current effective role alone is insufficient.
        // This does NOT attest pg_hba or service authentication.
        let app_can_promote: Option<bool> = db
            .client
            .query_opt(
                "SELECT pg_has_role(current_user,c.relowner,'MEMBER') \
                    OR pg_has_role(current_user,n.nspowner,'MEMBER') \
                    OR has_schema_privilege(current_user,n.oid,'CREATE') \
                    OR (SELECT rolsuper FROM pg_catalog.pg_roles WHERE rolname=current_user) \
                    OR has_table_privilege(current_user,c.oid,'INSERT') \
                    OR has_table_privilege(current_user,c.oid,'DELETE') \
                    OR has_table_privilege(current_user,c.oid,'TRUNCATE') \
                    OR has_column_privilege(current_user,c.oid,'state','UPDATE') \
                    OR has_column_privilege(current_user,c.oid,'source_sha256','UPDATE') \
                    OR has_column_privilege(current_user,c.oid,'promotion_allowed','UPDATE') \
                    OR pg_has_role(session_user,c.relowner,'MEMBER') \
                    OR pg_has_role(session_user,n.nspowner,'MEMBER') \
                    OR has_schema_privilege(session_user,n.oid,'CREATE') \
                    OR (SELECT rolsuper FROM pg_catalog.pg_roles WHERE rolname=session_user) \
                    OR has_table_privilege(session_user,c.oid,'INSERT') \
                    OR has_table_privilege(session_user,c.oid,'DELETE') \
                    OR has_table_privilege(session_user,c.oid,'TRUNCATE') \
                    OR has_column_privilege(session_user,c.oid,'state','UPDATE') \
                    OR has_column_privilege(session_user,c.oid,'source_sha256','UPDATE') \
                    OR has_column_privilege(session_user,c.oid,'promotion_allowed','UPDATE') \
             FROM pg_catalog.pg_class c
             JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
             WHERE n.nspname=$1 AND c.relname='_stage_control' AND c.relkind='r'",
                &[&self.config.schema],
            )
            .map_err(io)?
            .map(|row| row.get(0));
        if app_can_promote != Some(false) {
            return Err(error(
                "PG Runtime control table not independently qualified; refusing startup",
            ));
        }
        Ok(db)
    }

    // A startup-qualified process may outlive operator revocation. Gate each
    // new filesystem-changing Workspace effect on the existing PG writer
    // source, while holding a row lock against concurrent qualification edits.
    fn require_qualified_writer_tx(&self, tx: &mut postgres::Transaction<'_>) -> RuntimeResult<()> {
        let row = tx
            .query_opt(
                "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='source' FOR SHARE",
                &[],
            )
            .map_err(io)?;
        let qualified = row.is_some_and(|row| {
            row.get::<_, String>(0) == "QUALIFIED_WRITER"
                && row.get::<_, String>(1) == self.config.source_sha256
                && row.get::<_, bool>(2)
        });
        if !qualified {
            return Err(error(
                "PG Runtime source writer revoked; refusing Workspace effect",
            ));
        }
        crate::pg_admission::require_pg_writer_epoch(tx, &self.config.source_sha256, true)
            .map_err(pg)?;
        Ok(())
    }
    fn authorize(
        &self,
        db: &mut PgAdmissionStore,
        job: &str,
        principal: &str,
    ) -> RuntimeResult<()> {
        match db
            .client
            .query_opt("SELECT principal FROM jobs WHERE job_id=$1", &[&job])
            .map_err(io)?
        {
            Some(r) if r.get::<_, String>(0) == principal => Ok(()),
            _ => Err(RuntimeError::new(
                RuntimeErrorCode::JobNotFound,
                "Job not found for principal",
                Some("jobId"),
                false,
            )),
        }
    }
    fn attempt(
        &self,
        db: &mut PgAdmissionStore,
        job: &str,
    ) -> RuntimeResult<(AttemptRecord, RuntimeExecutionPlan, String)> {
        let r=db.client.query_one("SELECT a.attempt_id,a.state,a.termination_intent,a.launch_token_digest,a.bundle_path,a.unit_name,a.created_at_ms,a.row_version,a.bundle_digest,j.execution_plan_json,j.operation_digest FROM attempts a JOIN jobs j ON j.job_id=a.job_id WHERE j.job_id=$1 ORDER BY a.attempt_number DESC LIMIT 1", &[&job]).map_err(io)?;
        let a:AttemptRecord=serde_json::from_value(json!({"attemptId":r.get::<_,String>(0),"jobId":job,"attemptNumber":1,"state":r.get::<_,String>(1),"terminationIntent":r.get::<_,String>(2),"launchTokenDigest":r.get::<_,String>(3),"bundlePath":r.get::<_,String>(4),"unitName":r.get::<_,String>(5),"createdAtMs":r.get::<_,i64>(6),"rowVersion":r.get::<_,i64>(7),"bundleDigest":r.get::<_,Option<String>>(8)})).map_err(io)?;
        let expected = self
            .config
            .executor
            .store_root
            .join("pg-attempts")
            .join(&a.attempt_id);
        if Path::new(&a.bundle_path) != expected {
            return Err(error("Attempt bundle outside PG store"));
        }
        Ok((a, decode(&r.get::<_, String>(9))?, r.get(10)))
    }
    fn reconcile(&self, db: &mut PgAdmissionStore, job: &str) -> RuntimeResult<()> {
        let (mut a, plan, operation) = self.attempt(db, job)?;
        let provider: serde_json::Value = decode(
            &db.client
                .query_one(
                    "SELECT workspace_snapshot_json FROM jobs WHERE job_id=$1",
                    &[&job],
                )
                .map_err(io)?
                .get::<_, String>(0),
        )?;
        if a.state == AttemptState::Accepted
            && a.termination_intent == AttemptTerminationIntent::Natural
        {
            let runner = self
                .config
                .executor
                .runner_path
                .as_deref()
                .ok_or_else(|| error("runner missing"))?;
            super::platform::validate_runner(runner)?;
            if provider["executionProvider"]["executableDigest"].as_str()
                != Some(&universal::sha256_file(runner).map_err(io)?)
            {
                return Err(error("native runner changed after admission"));
            }
            // Revalidate the *committed* bytes before dispatch; Runner owns
            // continuous path-drift witnessing after it starts.
            super::host_dependency::verify_committed_bindings(&plan.host_dependencies)?;
            let token = universal::sha256_bytes(
                format!("runtime-launch-v1\0{}\0{operation}", a.attempt_id).as_bytes(),
            );
            if universal::sha256_bytes(token.as_bytes()) != a.launch_token_digest {
                return Err(error("launch token mismatch"));
            }
            let req = RunnerRequest {
                schema_version: 1,
                job_id: Some(job.into()),
                attempt_id: Some(a.attempt_id.clone()),
                launch_token: Some(token),
                unit_name: Some(a.unit_name.clone()),
                payload: None,
                inherit_host_environment: true,
                task_id: a.attempt_id.clone(),
                workspace_id: plan.workspace_id.clone(),
                workspace_path: plan.workspace_path.clone(),
                workspace_source_digest: plan.workspace_source_digest.clone(),
                build_target_backing: None,
                input_presentation_root: None,
                input_commitments: vec![],
                host_dependencies: plan
                    .host_dependencies
                    .iter()
                    .map(|binding| universal::RunnerHostDependencyCommitment {
                        path: binding.path.clone(),
                        digest: binding.expected_digest.clone(),
                    })
                    .collect(),
                executable: plan.executable.clone(),
                executable_digest: plan.executable_digest.clone(),
                args: plan.args.clone(),
                cwd: plan.cwd.clone(),
                env: plan.env.clone(),
                steps: plan
                    .steps
                    .iter()
                    .map(|step| universal::RunnerExecutionStep {
                        id: step.id.clone(),
                        executable: step.executable.clone(),
                        executable_digest: step.executable_digest.clone(),
                        args: step.args.clone(),
                        cwd: step.cwd.clone(),
                        env: step.env.clone(),
                        timeout_ms: step.timeout_ms,
                        continue_on_error: step.continue_on_error,
                    })
                    .collect(),
                timeout_ms: plan.timeout_ms,
                stdout_limit_bytes: plan.stdout_limit_bytes,
                stderr_limit_bytes: plan.stderr_limit_bytes,
            };
            fs::create_dir_all(&a.bundle_path).map_err(io)?;
            let request_path = Path::new(&a.bundle_path).join("request.json");
            let bytes = serde_json::to_vec(&req).map_err(io)?;
            // Existing published bytes must match; never replace a committed bundle.
            if request_path.exists() {
                if fs::read(&request_path).map_err(io)? != bytes {
                    return Err(error("bundle bytes differ"));
                }
            } else {
                universal::write_bytes_atomic(&request_path, &bytes).map_err(io)?;
            }
            let digest = universal::sha256_bytes(&bytes);
            if a.bundle_digest.is_none() {
                a.row_version = db
                    .commit_bundle_ready_pg(&PgBundleReady {
                        attempt_id: a.attempt_id.clone(),
                        expected_row_version: a.row_version as i64,
                        bundle_digest: digest.clone(),
                        observed_at_ms: now()?,
                        expected_source_sha256: self.config.source_sha256.clone(),
                    })
                    .map_err(pg)? as u64;
            } else if a.bundle_digest.as_deref() != Some(&digest) {
                return Err(error("bundle digest mismatch"));
            }
            // This commit is intent only. Never reissue a physical launch after this boundary.
            db.mark_dispatch_issued_pg(&PgDispatchIssued {
                attempt_id: a.attempt_id.clone(),
                expected_row_version: a.row_version as i64,
                expected_bundle_digest: digest,
                observed_at_ms: now()?,
                expected_source_sha256: self.config.source_sha256.clone(),
            })
            .map_err(pg)?;
            let output = super::platform::systemd_run(&super::platform::SystemdRunSpec {
                unit_name: &a.unit_name,
                runner: self
                    .config
                    .executor
                    .runner_path
                    .as_deref()
                    .ok_or_else(|| error("runner missing"))?,
                bundle_path: Path::new(&a.bundle_path),
                workspace_path: Path::new(&plan.workspace_path),
                workspace_git_common_dir: None,
                input_set_path: None,
                credential_source_root: None,
                credential_names: &[],
                runtime_ceiling_ms: plan
                    .timeout_ms
                    .checked_add(5000)
                    .ok_or_else(|| error("timeout overflow"))?,
                budget: &plan.budget,
                execution_profile: plan.execution_profile,
                environment: &plan.env,
            })?;
            if !output.status.success() {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::DispatchOutcomeUnknown,
                    format!(
                        "native launch not confirmed for Job {job}: {}",
                        String::from_utf8_lossy(&output.stderr)
                    ),
                    Some("jobId"),
                    false,
                )
                .with_operation_id(job.to_string()));
            }
            a = self.attempt(db, job)?.0;
        }
        let path = Path::new(&a.bundle_path);
        if !a.state.is_terminal() && path.join("result.json").exists() {
            // Reuse native identity, stdout/stderr digest and result validators.
            let start: RunnerStartEvidence =
                serde_json::from_slice(&fs::read(path.join("runner-start.json")).map_err(io)?)
                    .map_err(io)?;
            if start.job_id != job
                || start.attempt_id != a.attempt_id
                || start.launch_token_digest != a.launch_token_digest
                || start.unit_name != a.unit_name
                || start.invocation_id.is_empty()
            {
                return Err(error("runner start identity mismatch"));
            }
            let properties = super::platform::systemctl_show(&a.unit_name)?;
            if super::platform::unit_is_active(&properties)
                || super::platform::unit_has_pending_job(&properties)
            {
                return Ok(());
            }
            if super::platform::nonempty_property(&properties, "InvocationID")
                .is_some_and(|v| v != start.invocation_id)
                || super::platform::cgroup_has_processes(&start.control_group)?
            {
                return Err(error("runner process ownership has not converged"));
            }
            if start.runner_executable_digest.as_deref()
                != provider["executionProvider"]["executableDigest"].as_str()
            {
                return Err(error("runner evidence provider mismatch"));
            }
            let mut terminal = super::evidence::prepare_runner_terminal_from_bundle(&a)?;
            if let Some(artifact) = super::evidence::validate_workspace_source_observation_artifact(
                &a,
                plan.workspace_source_digest.as_deref(),
                true,
                super::evidence::SourceObservationRequirement::for_terminal(
                    terminal.state,
                    &terminal.reason_code,
                ),
            )? {
                terminal.artifacts.push(artifact);
            }
            let input = PgTerminalNoArtifacts {
                attempt_id: a.attempt_id.clone(),
                expected_row_version: a.row_version as i64,
                terminal_state: terminal.state.as_db().into(),
                result_digest: terminal.result_digest,
                reason_code: terminal.reason_code,
                exit_code: terminal.exit_code,
                finished_at_ms: terminal.finished_at_ms as i64,
                expected_source_sha256: self.config.source_sha256.clone(),
            };
            let artifacts = terminal
                .artifacts
                .into_iter()
                .map(|v| PgArtifactRegistration {
                    artifact_id: v.artifact_id,
                    kind: v.kind,
                    relative_path: v.relative_path,
                    digest: v.digest,
                    media_type: v.media_type,
                    byte_length: v.byte_length as i64,
                    truncated: v.truncated,
                    created_at_ms: input.finished_at_ms,
                })
                .collect::<Vec<_>>();
            db.commit_terminal_with_artifacts(&input, &artifacts)
                .map_err(pg)?;
        }
        Ok(())
    }
    fn project(
        &self,
        db: &mut PgAdmissionStore,
        request: &JobObserveRequest,
    ) -> RuntimeResult<JobObservation> {
        let snapshot = match db
            .observe_job_readonly(&request.job_id, &self.config.source_sha256)
            .map_err(pg)?
        {
            PgJobReadback::Observed(s) => s,
            _ => return Err(error("inconclusive PG lifecycle")),
        };
        let (a, p, operation) = self.attempt(db, &request.job_id)?;
        let terminal = snapshot.resolution.is_some();
        let rows=db.client.query("SELECT artifact_id,kind,digest,byte_length,truncated,relative_path FROM artifacts WHERE job_id=$1 ORDER BY artifact_id", &[&request.job_id]).map_err(io)?;
        let artifacts=rows.iter().map(|r|json!({"artifactId":r.get::<_,String>(0),"attemptId":a.attempt_id,"kind":r.get::<_,String>(1),"digest":r.get::<_,String>(2),"retainedBytes":r.get::<_,i64>(3),"truncated":r.get::<_,bool>(4)})).collect::<Vec<_>>();
        let exit: Option<i32> = db
            .client
            .query_one(
                "SELECT exit_code FROM attempts WHERE attempt_id=$1",
                &[&a.attempt_id],
            )
            .map_err(io)?
            .get(0);
        let mut value = json!({"jobId":request.job_id,"operationDigest":operation,"status":snapshot.resolution.clone().unwrap_or(snapshot.attempt_state.clone()),"desiredState":snapshot.desired_state,"attemptId":a.attempt_id,"attemptState":snapshot.attempt_state,"terminationIntent":snapshot.termination_intent,"exitCode":exit,"executionTerminal":terminal,"executionDisposition":snapshot.resolution,"deliveryDisposition":if terminal {"committed"} else {"in_progress"},"effectiveLimits":{"timeoutMs":p.timeout_ms,"stdoutLimitBytes":p.stdout_limit_bytes,"stderrLimitBytes":p.stderr_limit_bytes},"recoveryRequired":!terminal && a.state==AttemptState::Starting,"semanticCompletionEvaluated":false,"resultAvailable":terminal,"artifactsAvailable":!artifacts.is_empty(),"artifacts":artifacts});
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
            let path = Path::new(&a.bundle_path).join(format!("{kind}.log"));
            if path.exists() {
                let bytes = {
                    use std::io::Read;
                    let file = fs::File::open(path).map_err(io)?;
                    let mut bytes = vec![];
                    file.take(self.config.executor.max_output_bytes + 1)
                        .read_to_end(&mut bytes)
                        .map_err(io)?;
                    if bytes.len() as u64 > self.config.executor.max_output_bytes {
                        return Err(error("output exceeds retained ceiling"));
                    }
                    bytes
                };
                let begin = offset
                    .unwrap_or((bytes.len() as u64).saturating_sub(limit))
                    .min(bytes.len() as u64) as usize;
                let end = (begin as u64 + limit).min(bytes.len() as u64) as usize;
                if terminal {
                    // Terminal stdout/stderr are registered evidence, not a
                    // mutable preview. Reuse the same PostgreSQL digest/size
                    // commitment enforced by artifact.read, on the very bytes
                    // returned to the Agent.
                    let expected = rows
                        .iter()
                        .find(|row| row.get::<_, String>(1) == kind)
                        .ok_or_else(|| error("terminal output Artifact registration missing"))?;
                    if expected.get::<_, String>(5) != format!("{kind}.log")
                        || expected.get::<_, i64>(3) != bytes.len() as i64
                        || expected.get::<_, String>(2) != universal::sha256_bytes(&bytes)
                    {
                        return Err(RuntimeError::new(
                            RuntimeErrorCode::ArtifactIdentityConflict,
                            "terminal output bytes disagree with PostgreSQL Artifact evidence",
                            Some("artifact"),
                            false,
                        ));
                    }
                }
                value[format!("{kind}Tail")] = json!(String::from_utf8_lossy(&bytes[begin..end]));
                value[format!("{kind}Offset")] = json!(begin);
                value[format!("{kind}NextOffset")] = json!(end);
                value[format!("{kind}AvailableBytes")] = json!(bytes.len());
                value[format!("{kind}Eof")] = json!(end == bytes.len());
            } else if terminal {
                return Err(error("terminal output Artifact file missing"));
            }
        }
        serde_json::from_value(value).map_err(io)
    }
}

#[cfg(test)]
mod workspace_effect_commit_tests {
    use super::*;

    #[test]
    fn failed_post_effect_commit_is_unknown_to_existing_mcp_consumer() {
        let effect = std::env::temp_dir().join(format!("ordivon-pg-effect-{}", Uuid::now_v7()));
        fs::write(&effect, b"file changed before SQL COMMIT").unwrap();
        assert_eq!(
            fs::read(&effect).unwrap(),
            b"file changed before SQL COMMIT"
        );
        let receipt = workspace_effect_commit(
            Err(std::io::Error::new(
                std::io::ErrorKind::ConnectionReset,
                "lost COMMIT reply",
            )),
            "workspace.mutate",
        );
        let err = receipt.expect_err("a missing COMMIT receipt cannot prove success");
        assert_eq!(err.code, RuntimeErrorCode::DispatchOutcomeUnknown);
        assert!(!err.retryable, "reconciliation before retry");
        assert!(
            effect.exists(),
            "an error cannot imply the filesystem was rolled back"
        );
        fs::remove_file(effect).unwrap();
    }

    #[test]
    fn real_postgres_connection_loss_after_effect_is_unknown() {
        // Optional native physical test: same disposable PG socket setup as
        // pg_admission live fixtures, never a production database.
        let Ok(dsn) = std::env::var("ORDIVON_PG_TEST_DSN") else {
            return;
        };
        let mut db = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
        let mut tx = db.transaction().unwrap();
        let effect = std::env::temp_dir().join(format!("ordivon-pg-effect-{}", Uuid::now_v7()));
        fs::write(&effect, b"physical effect before database disconnection").unwrap();
        assert!(effect.is_file());
        // Kill only this disposable test session; genuine PostgreSQL protocol
        // connection loss makes the subsequent COMMIT acknowledgement fail.
        let _ = tx.query_one("SELECT pg_terminate_backend(pg_backend_pid())", &[]);
        let receipt = workspace_effect_commit(tx.commit(), "workspace.mutate");
        let err = receipt.expect_err("lost real PG COMMIT acknowledgement");
        assert_eq!(err.code, RuntimeErrorCode::DispatchOutcomeUnknown);
        assert!(!err.retryable);
        assert!(
            effect.exists(),
            "physical change does not roll back with PG"
        );
        fs::remove_file(effect).unwrap();
    }
}
