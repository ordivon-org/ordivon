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
    /// Advertise only capabilities implemented by this PostgreSQL-native entrypoint.
    pub fn describe(&self) -> RuntimeResult<serde_json::Value> {
        let runner = self
            .config
            .executor
            .runner_path
            .as_deref()
            .ok_or_else(|| error("native runner missing"))?;
        super::platform::validate_runner(runner)?;
        let digest = universal::sha256_file(runner).map_err(io)?;
        Ok(json!({
            "schemaVersion":1,
            "node":{"nodeId":"linux-pg","platform":"linux","native":true},
            "defaultRuntimeMs":30000,
            "maxRuntimeMs":self.config.executor.max_runtime_ms,
            "maxOutputBytes":self.config.executor.max_output_bytes,
            "allowedExecutableRoots":self.config.executor.allowed_executable_roots.iter()
                .map(|p|p.to_string_lossy().into_owned()).collect::<Vec<_>>(),
            "inputAuthorities":[],
            "credentialAuthorities":[],
            "inputIngressAuthorities":[],
            "credentialMaterializationBindings":[],
            "globalExecutionLimit":4,
            "structuredReleaseConfigured":false,
            "targets":[{
                "target":"local_linux","configured":true,"available":true,
                "executionProfiles":["trusted_local"],"structuredPlan":true,
                "immutableInputs":false,"hostDependencyCommitments":false,
                "executionProvider":{"contract":"local_linux_runner_v1","executableDigest":digest}
            }]
        }))
    }
    /// Principal-scoped, read-only cursor over new-epoch PostgreSQL Job identity.
    pub fn list(
        &self,
        principal: &str,
        request: &RuntimeJobListRequest,
    ) -> RuntimeResult<serde_json::Value> {
        if request.limit == 0 || request.limit > 100 {
            return Err(RuntimeError::invalid("limit must be 1..100", "limit"));
        }
        let mut db = self.store()?;
        // This is a projection of CURRENT Runtime truth, not an archival SQL
        // browser. Read stage, physical PG epoch and rows from one consistent
        // snapshot; never report a branch-restored Job as current after PITR.
        let mut tx = db
            .client
            .build_transaction()
            .isolation_level(postgres::IsolationLevel::RepeatableRead)
            .read_only(true)
            .start()
            .map_err(io)?;
        let stage = tx.query_opt(
            "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='source'",
            &[],
        ).map_err(io)?.ok_or_else(|| error("PG Runtime source writer not qualified"))?;
        if stage.get::<_, String>(0) != "QUALIFIED_WRITER"
            || stage.get::<_, String>(1) != self.config.source_sha256
            || !stage.get::<_, bool>(2)
        {
            return Err(error("PG Runtime source writer not qualified"));
        }
        crate::pg_admission::require_pg_writer_epoch(&mut tx, &self.config.source_sha256, false)
            .map_err(pg)?;
        let cursor_at = request.cursor.as_ref().map(|c| c.created_at_ms as i64);
        let cursor_id = request.cursor.as_ref().map(|c| c.job_id.clone());
        let limit = i64::from(request.limit) + 1;
        let rows=tx.query(
            "SELECT j.job_id,j.operation_digest,j.client_request_id,j.workspace_id,j.created_at_ms,              j.desired_state,j.resolution,a.attempt_id,a.state,a.termination_intent,a.exit_code,              a.started_at_ms,a.finished_at_ms,j.execution_plan_json,              (SELECT count(*) FROM artifacts r WHERE r.job_id=j.job_id)              FROM jobs j LEFT JOIN attempts a ON a.attempt_id=COALESCE(j.current_attempt_id,              (SELECT last.attempt_id FROM attempts last WHERE last.job_id=j.job_id              ORDER BY last.attempt_number DESC LIMIT 1)) AND a.job_id=j.job_id              WHERE j.principal=$1              AND ($2::text IS NULL OR j.client_request_id=$2::text)              AND ($3::text IS NULL OR j.workspace_id=$3::text)              AND ($4::bigint IS NULL OR (j.created_at_ms,j.job_id)<($4::bigint,$5::text))              ORDER BY j.created_at_ms DESC,j.job_id DESC LIMIT $6",
            &[&principal,&request.client_request_id,&request.workspace_id,&cursor_at,&cursor_id,&limit]
        ).map_err(io)?;
        tx.commit().map_err(io)?;
        let more = rows.len() > request.limit as usize;
        let mut jobs = Vec::new();
        for r in rows.iter().take(request.limit as usize) {
            let plan: RuntimeExecutionPlan = decode(&r.get::<_, String>(13))?;
            let at = r.get::<_, i64>(4).max(0) as u64;
            let started = r.get::<_, Option<i64>>(11).map(|v| v.max(0) as u64);
            let finished = r.get::<_, Option<i64>>(12).map(|v| v.max(0) as u64);
            let resolution: Option<String> = r.get(6);
            let attempt_state: Option<String> = r.get(8);
            let count: i64 = r.get(14);
            let end = finished.unwrap_or(now()?.max(0) as u64);
            let cwd_relative = Path::new(&plan.cwd)
                .strip_prefix(&plan.workspace_path)
                .map(|p| {
                    if p.as_os_str().is_empty() {
                        ".".into()
                    } else {
                        p.to_string_lossy().into_owned()
                    }
                })
                .unwrap_or_else(|_| ".".into());
            jobs.push(json!({
                "jobId":r.get::<_,String>(0),
                "operationDigest":r.get::<_,String>(1),
                "clientRequestId":r.get::<_,String>(2),
                "workspaceId":r.get::<_,String>(3),
                "createdAtMs":at,
                "desiredState":r.get::<_,String>(5),
                "status":resolution.clone().or_else(||attempt_state.clone()).unwrap_or_else(||"accepted".into()),
                "attemptId":r.get::<_,Option<String>>(7),
                "attemptState":attempt_state,
                "terminationIntent":r.get::<_,Option<String>>(9),
                "exitCode":r.get::<_,Option<i32>>(10),
                "startedAtMs":started,"finishedAtMs":finished,
                "executionTerminal":resolution.is_some(),
                "executionDisposition":resolution,
                "deliveryDisposition":if finished.is_some(){"committed"}else{"in_progress"},
                "recoveryRequired":finished.is_none() && r.get::<_,Option<String>>(8).as_deref()==Some("starting"),
                "semanticCompletionEvaluated":false,
                "sourceRevision":plan.source_revision,
                "executableName":Path::new(&plan.executable).file_name()
                    .map(|p|p.to_string_lossy().into_owned()).unwrap_or_default(),
                "cwdRelative":cwd_relative,
                "durationMs":end.saturating_sub(started.unwrap_or(at)),
                "resultAvailable":finished.is_some(),
                "artifactsAvailable":count>0,"artifactCount":count,
            }));
        }
        let next_cursor = if more {
            jobs.last()
                .map(|v| json!({"createdAtMs":v["createdAtMs"],"jobId":v["jobId"]}))
        } else {
            None
        };
        Ok(json!({"jobs":jobs,"nextCursor":next_cursor}))
    }
    /// Close only when PG proves no active or held consumer, then reuse the
    /// existing workspace source/dirty/continuation and dependency checks.
    pub fn close_workspace(
        &self,
        request: &WorkspaceCloseRequest,
    ) -> RuntimeResult<WorkspaceCloseResult> {
        let mut db = self.store()?;
        let mut tx = db
            .client
            .build_transaction()
            .isolation_level(postgres::IsolationLevel::Serializable)
            .start()
            .map_err(io)?;
        tx.query_one("SELECT pg_advisory_xact_lock($1)", &[&79245017_i64])
            .map_err(io)?;
        self.require_qualified_writer_tx(&mut tx)?;
        let active:i64=tx.query_one(
            "SELECT count(*) FROM jobs j WHERE j.workspace_id=$1 AND (j.resolution IS NULL OR              EXISTS(SELECT 1 FROM attempts a JOIN concurrency_reservations r              ON r.attempt_id=a.attempt_id WHERE a.job_id=j.job_id AND r.state IN ('active','held_orphaned')))",
            &[&request.workspace_id]
        ).map_err(io)?.get(0);
        if active != 0 {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ConcurrencyLimit,
                "Workspace has PG-owned active or held Jobs",
                Some("workspaceId"),
                false,
            ));
        }
        let dependents =
            universal::workspace_cleanup_dependents(&self.config.executor, &request.workspace_id)
                .map_err(io)?;
        if !dependents.is_empty() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ConcurrencyLimit,
                "Workspace has dependent Workspaces",
                Some("workspaceId"),
                false,
            ));
        }
        let result = universal::remove_git_workspace(&self.config.executor, request)
            .map_err(super::engine::map_universal_error)?;
        workspace_effect_commit(tx.commit(), "workspace.close")?;
        Ok(result)
    }
    /// Mutations reuse the upstream atomic file batch, fenced against PG Job admission.
    /// No SQLite authority, historical Job import, or dual writer is involved.
    pub fn mutate_workspace(
        &self,
        request: &WorkspaceMutateRequest,
    ) -> RuntimeResult<WorkspaceMutateResult> {
        let mut db = self.store()?;
        let mut tx = db
            .client
            .build_transaction()
            .isolation_level(postgres::IsolationLevel::Serializable)
            .start()
            .map_err(io)?;
        tx.query_one("SELECT pg_advisory_xact_lock($1)", &[&79245017_i64])
            .map_err(io)?;
        self.require_qualified_writer_tx(&mut tx)?;
        let active:i64=tx.query_one(
            "SELECT count(*) FROM jobs j WHERE j.workspace_id=$1 AND (j.resolution IS NULL OR              EXISTS(SELECT 1 FROM attempts a JOIN concurrency_reservations r              ON r.attempt_id=a.attempt_id WHERE a.job_id=j.job_id AND r.state IN ('active','held_orphaned')))",
            &[&request.workspace_id]
        ).map_err(io)?.get(0);
        if active != 0 {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ConcurrencyLimit,
                "Workspace has PG-owned active or held Jobs",
                Some("workspaceId"),
                false,
            ));
        }
        let result = universal::mutate_workspace(&self.config.executor, request)
            .map_err(super::engine::map_universal_error)?;
        workspace_effect_commit(tx.commit(), "workspace.mutate")?;
        Ok(result)
    }
    pub fn executor_config(&self) -> UniversalExecutorConfig {
        self.config.executor.clone()
    }
    /// Read-only, source-bound projection of a fresh-epoch Git Workspace.
    pub fn get_workspace(
        &self,
        request: &RuntimeWorkspaceGetRequest,
    ) -> RuntimeResult<serde_json::Value> {
        if request.schema_version != 1 {
            return Err(RuntimeError::invalid(
                "schemaVersion must be 1",
                "schemaVersion",
            ));
        }
        let record = universal::load_workspace_record(&self.config.executor, &request.workspace_id)
            .map_err(super::engine::map_universal_error)?;
        // Reuse the canonical Git status-v2 snapshot already consumed by the
        // installed Runtime. HEAD revision, attached/detached mode and dirty
        // state are one physical observation, not two speculative probes.
        let (head, head_mode, dirty) =
            universal::workspace_head_and_dirty_at(Path::new(&record.workspace_path))
                .map_err(super::engine::map_universal_error)?;
        let digest =
            universal::workspace_source_state_digest(&self.config.executor, &request.workspace_id)
                .map_err(io)?;
        let mut db = self.store()?;
        let jobs=db.client.query(
            "SELECT job_id FROM jobs WHERE workspace_id=$1 AND resolution IS NULL ORDER BY created_at_ms DESC",
            &[&record.workspace_id]
        ).map_err(io)?.iter().map(|r|r.get::<_,String>(0)).collect::<Vec<_>>();
        Ok(json!({
            "workspaceId":record.workspace_id,"sourceRepo":record.source_repo,
            "sourceRevision":record.source_revision,"currentHeadRevision":head,
            "createdAtMs":record.created_unix_ms,"headMode":head_mode.as_str(),
            "dirty":dirty,"sourceStateDigest":digest,"activeJobIds":jobs
        }))
    }
    /// Fresh PG workspaces only; historical SQLite Workspace registries are deliberately absent.
    pub fn list_workspaces(
        &self,
        request: &RuntimeWorkspaceListRequest,
    ) -> RuntimeResult<serde_json::Value> {
        if request.schema_version != 1 || request.limit == 0 || request.limit > 100 {
            return Err(RuntimeError::invalid(
                "invalid workspace listing bounds",
                "limit",
            ));
        }
        // Reuse the canonical physical Workspace inventory. Silently dropping
        // corrupt candidates would falsely imply that the Workspace is absent.
        let inventory = universal::list_open_workspace_record_inventory(&self.config.executor)
            .map_err(super::engine::map_universal_error)?;
        let issues = inventory
            .issues
            .into_iter()
            .map(|issue| {
                let error = super::engine::map_universal_error(issue.error);
                json!({
                    "workspaceId": issue.workspace_id,
                    "stage": "inventory",
                    "code": error.code.as_str(),
                    "message": error.message,
                    "retryable": error.retryable
                })
            })
            .collect::<Vec<_>>();
        let mut all = Vec::new();
        for record in inventory.records {
            // Projection failures must not masquerade as a complete inventory.
            let mut value = self.get_workspace(&RuntimeWorkspaceGetRequest {
                schema_version: 1,
                workspace_id: record.workspace_id,
            })?;
            if !request.include_source_state_digest {
                value
                    .as_object_mut()
                    .expect("workspace projection")
                    .remove("sourceStateDigest");
            }
            all.push(value);
        }
        all.sort_by(|a, b| {
            let x = a["createdAtMs"].as_u64().unwrap_or(0);
            let y = b["createdAtMs"].as_u64().unwrap_or(0);
            y.cmp(&x).then_with(|| {
                a["workspaceId"]
                    .as_str()
                    .unwrap_or("")
                    .cmp(b["workspaceId"].as_str().unwrap_or(""))
            })
        });
        if let Some(cursor) = &request.cursor {
            all.retain(|v| {
                let at = v["createdAtMs"].as_u64().unwrap_or(0);
                let id = v["workspaceId"].as_str().unwrap_or("");
                at < cursor.created_at_ms
                    || (at == cursor.created_at_ms && id > cursor.workspace_id.as_str())
            });
        }
        let more = all.len() > request.limit as usize;
        all.truncate(request.limit as usize);
        let next_cursor = if more {
            all.last()
                .map(|v| json!({"createdAtMs":v["createdAtMs"],"workspaceId":v["workspaceId"]}))
        } else {
            None
        };
        Ok(json!({"workspaces":all,"nextCursor":next_cursor,"issues":issues}))
    }
    pub fn open_workspace(
        &self,
        request: &GitWorkspaceCreateRequest,
    ) -> RuntimeResult<CompactWorkspaceOpenResult> {
        let mut db = self.store()?;
        let mut tx = db
            .client
            .build_transaction()
            .isolation_level(postgres::IsolationLevel::Serializable)
            .start()
            .map_err(io)?;
        tx.query_one("SELECT pg_advisory_xact_lock($1)", &[&79245017_i64])
            .map_err(io)?;
        self.require_qualified_writer_tx(&mut tx)?;
        let result = universal::create_git_workspace(&self.config.executor, request)
            .map_err(super::engine::map_universal_error)?;
        workspace_effect_commit(tx.commit(), "workspace.open")?;
        Ok(result)
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
    pub fn run(&self, proposal: &JobRunProposal) -> RuntimeResult<JobObservation> {
        super::engine::validate_run_proposal_structure(proposal)?;
        let identity = super::types::proposal_request_identity_digest(proposal)?;
        let mut db = self.store()?;
        // Replay before consulting mutable Workspace/executable state or policy.
        if let Some(row) = db.client.query_opt("SELECT job_id,request_digest FROM jobs WHERE principal=$1 AND client_request_id=$2", &[&proposal.principal,&proposal.client_request_id]).map_err(io)? {
            if row.get::<_,String>(1)!=identity { return Err(pg(PgAdmissionError::IdempotencyConflict)); }
            return self.observe(&proposal.principal, &JobObserveRequest { schema_version:1,job_id:row.get(0),wait_ms:proposal.wait_ms,wait_until:JobObserveWaitUntil::Terminal,stdout_tail_bytes:proposal.stdout_tail_bytes,stderr_tail_bytes:proposal.stderr_tail_bytes,stdout_offset:None,stderr_offset:None });
        }
        let e = &proposal.execution;
        if e.execution_target != ExecutionTarget::LocalLinux
            || e.execution_profile != ExecutionProfile::TrustedLocal
            || !e.host_dependencies.is_empty()
            || e.windows_context.is_some()
            || e.windows_authority != WindowsAuthority::Limited
            || !e.foreign_references.is_empty()
        {
            return Err(RuntimeError::invalid(
                "PG vertical supports a single trusted_local local_linux command without bindings",
                "execution",
            ));
        }
        let timeout = e
            .timeout_ms
            .unwrap_or(self.config.executor.max_runtime_ms.min(30_000));
        let stdout = e
            .stdout_limit_bytes
            .unwrap_or(self.config.executor.max_output_bytes.min(1024 * 1024));
        let stderr = e
            .stderr_limit_bytes
            .unwrap_or(self.config.executor.max_output_bytes.min(1024 * 1024));
        if timeout == 0
            || timeout > self.config.executor.max_runtime_ms
            || stdout == 0
            || stderr == 0
            || stdout > self.config.executor.max_output_bytes
            || stderr > self.config.executor.max_output_bytes
        {
            return Err(RuntimeError::invalid(
                "execution limits exceed operator ceilings",
                "execution",
            ));
        }
        let runner = self
            .config
            .executor
            .runner_path
            .as_deref()
            .ok_or_else(|| error("native runner required"))?;
        super::platform::validate_runner(runner)?;
        let record = universal::load_workspace_record(&self.config.executor, &e.workspace_id)
            .map_err(super::engine::map_universal_error)?;
        let cwd =
            universal::resolve_workspace_cwd(&record, &e.cwd_relative, "execution.cwdRelative")
                .map_err(io)?;
        let executable = super::platform::validate_executable(
            &self.config.executor,
            &e.executable,
            "execution.executable",
        )?;
        let source =
            universal::workspace_source_state_digest(&self.config.executor, &e.workspace_id)
                .map_err(io)?;
        // An Agent-authored plan is resolved only at new admission. Every
        // executable and cwd is checked through existing native authorities,
        // then frozen into the PostgreSQL execution plan and Runner bundle.
        let mut frozen_steps = Vec::with_capacity(e.steps.len());
        let mut cumulative_step_budget = 0_u64;
        for (index, step) in e.steps.iter().enumerate() {
            let path = super::platform::validate_executable(
                &self.config.executor,
                &step.executable,
                &format!("execution.steps[{index}].executable"),
            )?;
            let cwd = universal::resolve_workspace_cwd(
                &record,
                &step.cwd_relative,
                &format!("execution.steps[{index}].cwdRelative"),
            )
            .map_err(io)?;
            let ceiling = step
                .timeout_ms
                .unwrap_or(self.config.executor.max_runtime_ms.min(30_000));
            if ceiling == 0 || ceiling > self.config.executor.max_runtime_ms {
                return Err(RuntimeError::invalid(
                    "invalid plan step timeout",
                    "execution.steps",
                ));
            }
            cumulative_step_budget =
                cumulative_step_budget.checked_add(ceiling).ok_or_else(|| {
                    RuntimeError::invalid("plan step budget overflow", "execution.steps")
                })?;
            frozen_steps.push(RuntimeExecutionStep {
                id: step.id.clone(),
                executable: path.to_string_lossy().into_owned(),
                executable_digest: universal::sha256_file(&path).map_err(io)?,
                args: step.args.clone(),
                cwd: cwd.to_string_lossy().into_owned(),
                env: step.env.clone(),
                timeout_ms: ceiling,
                continue_on_error: step.continue_on_error,
            });
        }
        // When a plan supplies no job-wide timeout, the sum of resolved
        // per-step budgets is the exact finite ceiling, as on the mature Runner.
        let timeout = if !frozen_steps.is_empty() && e.timeout_ms.is_none() {
            cumulative_step_budget
        } else {
            timeout
        };
        if timeout == 0 || timeout > self.config.executor.max_runtime_ms {
            return Err(RuntimeError::invalid(
                "plan exceeds configured runtime maximum",
                "execution.timeoutMs",
            ));
        }
        let plan = RuntimeExecutionPlan {
            schema_version: 1,
            workspace_id: e.workspace_id.clone(),
            workspace_path: record.workspace_path.clone(),
            source_revision: record.source_revision.clone(),
            workspace_source_digest: Some(source),
            workspace_git_common_dir: None,
            executable: executable.to_string_lossy().into_owned(),
            executable_digest: universal::sha256_file(&executable).map_err(io)?,
            args: e.args.clone(),
            cwd: cwd.to_string_lossy().into_owned(),
            env: e.env.clone(),
            timeout_ms: timeout,
            stdout_limit_bytes: stdout,
            stderr_limit_bytes: stderr,
            steps: frozen_steps,
            budget: e.budget.clone(),
            execution_profile: e.execution_profile,
            execution_target: e.execution_target,
            windows_authority: e.windows_authority,
            windows_context: None,
            windows_execution_context: None,
            foreign_references: vec![],
            input_set_id: None,
            effective_inputs: vec![],
            credential_set_id: None,
            principal: proposal.principal.clone(),
        };
        let plan_json = encode(&plan)?;
        let plan_digest = universal::sha256_bytes(plan_json.as_bytes());
        // An Operation commits to the resolved execution world and native
        // provider. The proposal identity remains stable for exact replay.
        // Use the existing canonical Job identity contract rather than a
        // PostgreSQL-specific digest scheme.
        let provider_digest = universal::sha256_file(runner).map_err(io)?;
        let operation_digest = JobIdentityContract::operation_digest(
            &identity,
            &plan_digest,
            OperationIdentityBindings::Provider {
                provider_digest: &provider_digest,
            },
        );
        let job = format!("job-{}", Uuid::now_v7());
        let attempt = format!("attempt-{}", Uuid::now_v7());
        let bundle = self
            .config
            .executor
            .store_root
            .join("pg-attempts")
            .join(&attempt);
        let token = universal::sha256_bytes(
            format!("runtime-launch-v1\0{attempt}\0{operation_digest}").as_bytes(),
        );
        let input = PgAdmissionInput {
            job_id: job.clone(),
            attempt_id: attempt.clone(),
            reservation_id: format!("reservation-{}", Uuid::now_v7()),
            principal: proposal.principal.clone(),
            client_request_id: proposal.client_request_id.clone(),
            request_digest: identity,
            operation_digest,
            workspace_id: e.workspace_id.clone(),
            workspace_snapshot_json: encode(
                &json!({"workspace":record,"executionProvider":{"contract":"local_linux_runner_v1","executableDigest":universal::sha256_file(runner).map_err(io)?}}),
            )?,
            execution_plan_digest: plan_digest,
            execution_plan_json: plan_json,
            launch_token_digest: universal::sha256_bytes(token.as_bytes()),
            bundle_path: bundle.to_string_lossy().into_owned(),
            unit_name: format!("ordivon-pg-{attempt}.service"),
            global_limit: i32::try_from(proposal.global_limit).map_err(io)?,
            created_at_ms: now()?,
            expected_source_sha256: self.config.source_sha256.clone(),
        };
        let job = match db.admit(&input).map_err(pg)? {
            PgAdmissionOutcome::Created(j) | PgAdmissionOutcome::Existing(j) => j,
        };
        self.observe(
            &proposal.principal,
            &JobObserveRequest {
                schema_version: 1,
                job_id: job,
                wait_ms: proposal.wait_ms,
                wait_until: JobObserveWaitUntil::Terminal,
                stdout_tail_bytes: proposal.stdout_tail_bytes,
                stderr_tail_bytes: proposal.stderr_tail_bytes,
                stdout_offset: None,
                stderr_offset: None,
            },
        )
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
                host_dependencies: vec![],
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
    pub fn observe(
        &self,
        principal: &str,
        request: &JobObserveRequest,
    ) -> RuntimeResult<JobObservation> {
        if request.schema_version != 1
            || request.wait_ms > MAX_TASK_WAIT_MS
            || request.stdout_tail_bytes > MAX_TASK_TAIL_BYTES
            || request.stderr_tail_bytes > MAX_TASK_TAIL_BYTES
        {
            return Err(RuntimeError::invalid(
                "invalid observation limits",
                "waitMs",
            ));
        }
        let deadline = Instant::now() + Duration::from_millis(request.wait_ms);
        let mut initial_signature = None;
        loop {
            let mut db = self.store()?;
            self.authorize(&mut db, &request.job_id, principal)?;
            self.reconcile(&mut db, &request.job_id)?;
            let value = self.project(&mut db, request)?;
            // Gateway observes change_or_terminal. Only compare durable
            // observable state, not time-dependent display projections.
            let signature = (
                value.status.clone(),
                value.desired_state,
                value.attempt_state,
                value.termination_intent,
                value.execution_terminal,
                value.delivery_disposition,
                value.recovery_required,
                value.stdout_available_bytes,
                value.stderr_available_bytes,
                value.artifacts.len(),
            );
            let changed = initial_signature
                .as_ref()
                .is_some_and(|start| start != &signature);
            if initial_signature.is_none() {
                initial_signature = Some(signature);
            }
            if value.execution_terminal
                || request.wait_ms == 0
                || Instant::now() >= deadline
                || (request.wait_until == JobObserveWaitUntil::ChangeOrTerminal && changed)
            {
                return Ok(value);
            }
            thread::sleep(
                Duration::from_millis(50).min(deadline.saturating_duration_since(Instant::now())),
            );
        }
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
    pub fn cancel(
        &self,
        principal: &str,
        request: &JobCancelRequest,
    ) -> RuntimeResult<JobObservation> {
        if request.schema_version != 1 {
            return Err(RuntimeError::invalid(
                "schemaVersion must be 1",
                "schemaVersion",
            ));
        }
        let mut db = self.store()?;
        self.authorize(&mut db, &request.job_id, principal)?;
        db.request_cancel_intent(&PgCancelIntent {
            job_id: request.job_id.clone(),
            observed_at_ms: now()?,
            expected_source_sha256: self.config.source_sha256.clone(),
        })
        .map_err(pg)?;
        let (a, _, _) = self.attempt(&mut db, &request.job_id)?;
        if !a.state.is_terminal() {
            fs::create_dir_all(&a.bundle_path).map_err(io)?;
            universal::write_json_atomic(
                &Path::new(&a.bundle_path).join("cancel-requested.json"),
                &json!({"requestedAtMs":now()?}),
            )
            .map_err(io)?;
            if a.bundle_digest.is_none() {
                return self.project(
                    &mut db,
                    &JobObserveRequest {
                        schema_version: 1,
                        job_id: request.job_id.clone(),
                        wait_ms: 0,
                        wait_until: JobObserveWaitUntil::Terminal,
                        stdout_tail_bytes: 4096,
                        stderr_tail_bytes: 4096,
                        stdout_offset: None,
                        stderr_offset: None,
                    },
                );
            }
            let output = super::platform::stop_unit_no_block(&a.unit_name)?;
            if !output.status.success() {
                return Err(error(format!(
                    "cancel intent persisted; native stop not confirmed for {}",
                    request.job_id
                )));
            }
        }
        self.observe(
            principal,
            &JobObserveRequest {
                schema_version: 1,
                job_id: request.job_id.clone(),
                wait_ms: 0,
                wait_until: JobObserveWaitUntil::Terminal,
                stdout_tail_bytes: 4096,
                stderr_tail_bytes: 4096,
                stdout_offset: None,
                stderr_offset: None,
            },
        )
    }
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
        let (a, p, operation) = self.attempt(&mut db, job)?;
        let j = db
            .client
            .query_one(
                "SELECT client_request_id,created_at_ms FROM jobs WHERE job_id=$1",
                &[&job],
            )
            .map_err(io)?;
        let counts=db.client.query_one("SELECT count(*),COALESCE(sum(byte_length),0)::bigint,count(*) FILTER(WHERE truncated) FROM artifacts WHERE job_id=$1",&[&job]).map_err(io)?;
        let mut by_kind = std::collections::BTreeMap::new();
        for row in db
            .client
            .query(
                "SELECT kind,count(*) FROM artifacts WHERE job_id=$1 GROUP BY kind",
                &[&job],
            )
            .map_err(io)?
        {
            by_kind.insert(row.get(0), row.get::<_, i64>(1) as u64);
        }
        let events=db.client.query("SELECT event_sequence,event_type,origin,previous_state,new_state,reason_code,observed_at_ms FROM job_events WHERE job_id=$1 ORDER BY event_sequence LIMIT $2",&[&job,&(i64::from(event_limit)+1)]).map_err(io)?;
        let created = j.get::<_, i64>(1) as u64;
        let mut previous = created;
        let timeline = events
            .iter()
            .take(event_limit as usize)
            .map(|r| {
                let at = r.get::<_, i64>(6) as u64;
                let delta = at.saturating_sub(previous);
                previous = at;
                RuntimeInspectionEvent {
                    sequence: r.get::<_, i64>(0) as u64,
                    attempt_id: Some(a.attempt_id.clone()),
                    event_type: r.get(1),
                    origin: r.get(2),
                    previous_state: r.get(3),
                    new_state: r.get(4),
                    reason_code: r.get(5),
                    observed_at_ms: at,
                    elapsed_ms: at.saturating_sub(created),
                    delta_ms: delta,
                    detail: None,
                }
            })
            .collect();
        let terminal = snapshot.resolution.is_some();
        let exit = db
            .client
            .query_one(
                "SELECT exit_code FROM attempts WHERE attempt_id=$1",
                &[&a.attempt_id],
            )
            .map_err(io)?
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
                attempt_number: 1,
                state: a.state,
                termination_intent: a.termination_intent,
                created_at_ms: a.created_at_ms,
                started_at_ms: None,
                finished_at_ms: snapshot.finished_at_ms.map(|v| v as u64),
                duration_ms: None,
                exit_code: exit,
                result_available: terminal,
                reservation_state: ReservationState::parse(&snapshot.reservation_state)?,
                reservation_release_reason: None,
                conditions: vec![],
                artifact_count: counts.get::<_, i64>(0) as u64,
                artifact_bytes: counts.get::<_, i64>(1) as u64,
                truncated_artifacts: counts.get::<_, i64>(2) as u64,
            }],
            attempts_truncated: false,
            artifacts: RuntimeInspectionArtifactSummary {
                count: counts.get::<_, i64>(0) as u64,
                bytes: counts.get::<_, i64>(1) as u64,
                truncated: counts.get::<_, i64>(2) as u64,
                by_kind,
            },
            episodes: RuntimeInspectionEpisodes::default(),
            timeline,
            events_truncated: events.len() > event_limit as usize,
        })
    }
    /// Full byte projection for MCP embedded Artifact resources. PostgreSQL
    /// owns the identity/metadata; no SQLite artifact registry is consulted.
    pub fn read_artifact_content(
        &self,
        principal: &str,
        request: &ArtifactContentRequest,
    ) -> RuntimeResult<ArtifactContentReadResult> {
        if request.schema_version != 1
            || request.max_bytes == 0
            || request.max_bytes > 4 * 1024 * 1024
        {
            return Err(RuntimeError::invalid(
                "invalid artifact content bound",
                "maxBytes",
            ));
        }
        let mut db = self.store()?;
        self.authorize(&mut db, &request.job_id, principal)?;
        let row=db.client.query_opt(
            "SELECT a.bundle_path,r.relative_path,r.digest,r.byte_length,r.media_type,r.truncated              FROM artifacts r JOIN attempts a ON a.attempt_id=r.attempt_id              WHERE r.job_id=$1 AND r.artifact_id=$2",
            &[&request.job_id,&request.artifact_id]
        ).map_err(io)?.ok_or_else(||error("Artifact not found"))?;
        let relative: String = row.get(1);
        universal::validate_relative_path(&relative, "artifactPath").map_err(io)?;
        let base = PathBuf::from(row.get::<_, String>(0));
        let dir = universal::open_directory_nofollow(&base).map_err(io)?;
        let mut file =
            universal::open_regular_file_beneath(&dir, Path::new(&relative), true).map_err(io)?;
        use std::io::Read;
        let mut bytes = Vec::new();
        file.by_ref()
            .take(request.max_bytes + 1)
            .read_to_end(&mut bytes)
            .map_err(io)?;
        if bytes.len() as u64 > request.max_bytes {
            return Err(RuntimeError::invalid(
                "Artifact exceeds maxBytes",
                "maxBytes",
            ));
        }
        let digest: String = row.get(2);
        let len: i64 = row.get(3);
        if bytes.len() as i64 != len || universal::sha256_bytes(&bytes) != digest {
            return Err(error("Artifact bytes do not match PostgreSQL registration"));
        }
        Ok(ArtifactContentReadResult {
            metadata: ArtifactContentMetadata {
                job_id: request.job_id.clone(),
                artifact_id: request.artifact_id.clone(),
                digest,
                media_type: row.get(4),
                byte_length: len as u64,
                truncated: row.get(5),
            },
            bytes,
        })
    }
    pub fn read_artifact(
        &self,
        principal: &str,
        request: &ArtifactReadRequest,
    ) -> RuntimeResult<ArtifactReadResult> {
        if request.schema_version != 1
            || request.max_bytes == 0
            || request.max_bytes > 4 * 1024 * 1024
        {
            return Err(RuntimeError::invalid(
                "invalid artifact read bounds",
                "maxBytes",
            ));
        }
        let mut db = self.store()?;
        self.authorize(&mut db, &request.job_id, principal)?;
        let r=db.client.query_opt("SELECT a.bundle_path,r.relative_path,r.digest,r.byte_length FROM artifacts r JOIN attempts a ON a.attempt_id=r.attempt_id WHERE r.job_id=$1 AND r.artifact_id=$2", &[&request.job_id,&request.artifact_id]).map_err(io)?.ok_or_else(|| error("Artifact not found"))?;
        let bundle: PathBuf = r.get::<_, String>(0).into();
        let relative: String = r.get(1);
        universal::validate_relative_path(&relative, "artifactPath").map_err(io)?;
        let mut file = universal::open_regular_file_beneath(
            &universal::open_directory_nofollow(&bundle).map_err(io)?,
            Path::new(&relative),
            true,
        )
        .map_err(io)?;
        use std::io::Read;
        let mut bytes = vec![];
        file.by_ref()
            .take(self.config.executor.max_output_bytes.max(4 * 1024 * 1024) + 1)
            .read_to_end(&mut bytes)
            .map_err(io)?;
        let digest: String = r.get(2);
        if bytes.len() as i64 != r.get::<_, i64>(3) || universal::sha256_bytes(&bytes) != digest {
            return Err(error("Artifact bytes do not match PG registration"));
        }
        let text = std::str::from_utf8(&bytes).map_err(io)?;
        let begin = usize::try_from(request.offset).map_err(io)?;
        if begin > bytes.len() || !text.is_char_boundary(begin) {
            return Err(RuntimeError::invalid("invalid UTF-8 offset", "offset"));
        }
        let mut end = begin
            .saturating_add(request.max_bytes as usize)
            .min(bytes.len());
        while !text.is_char_boundary(end) {
            end -= 1;
        }
        Ok(ArtifactReadResult {
            job_id: request.job_id.clone(),
            artifact_id: request.artifact_id.clone(),
            content: text[begin..end].into(),
            offset: request.offset,
            next_offset: end as u64,
            eof: end == bytes.len(),
            digest,
        })
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
