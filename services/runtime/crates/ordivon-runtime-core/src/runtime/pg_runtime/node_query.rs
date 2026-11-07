//! PostgreSQL Runtime node capability and read-only Job listing.
use super::*;

impl PgRuntime {
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
                "immutableInputs":false,"hostDependencyCommitments":true,
                "hostDependencyContinuityScope":"runtime_host_namespace_path_witness",
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
}
