//! PostgreSQL Runtime Workspace lifecycle and mutation.
use super::*;

// The advisory lock serializes Job admission, terminal/lease updates and
// Workspace effects. A PostgreSQL SERIALIZABLE snapshot is frozen when the
// lock-acquisition SELECT starts, i.e. *before* the transaction actually
// acquires a contended lock. Such a snapshot can miss newly committed leases,
// even after the holder releases the lock and this transaction later commits.
// READ COMMITTED takes the Workspace guard queries' snapshots after the lock
// is acquired, matching the existing PG scheduler's lock+isolation protocol.
// The global lock is deliberately retained across Git/FS physical effects:
// moving them outside this fence requires an independently recoverable intent.
const WORKSPACE_EFFECT_ISOLATION: postgres::IsolationLevel =
    postgres::IsolationLevel::ReadCommitted;

// An automated collector does not have evidence that the consumer released
// its Workspace merely because the final Job exited successfully. The native
// PG owner must re-read latest activity INSIDE the same admission/close fence,
// not trust the sweep's earlier global SQL snapshot. Explicit
// consumerReleased=true remains the caller's separate release assertion.
const WORKSPACE_JOB_CONTINUATION_HOLD_MS: i64 = 4 * 60 * 60 * 1000;

// Read committed AFTER the shared admission lock, so a recently completed
// Job no longer listed in activeJobIds still retains the Workspace long
// enough for consumers to inspect artifacts and source.
// Reuse existing PG jobs/attempts/events, with no additional registry/table.
fn require_recent_pg_job_consumer_continuation(
    tx: &mut postgres::Transaction<'_>,
    workspace_id: &str,
) -> RuntimeResult<()> {
    let row = tx
        .query_one(
            "WITH owned_jobs AS (
                SELECT job_id, created_at_ms FROM jobs WHERE workspace_id=$1
            )
            SELECT GREATEST(
                COALESCE((SELECT MAX(created_at_ms) FROM owned_jobs),0),
                COALESCE((SELECT MAX(a.finished_at_ms) FROM attempts a
                          JOIN owned_jobs j ON j.job_id=a.job_id),0),
                COALESCE((SELECT MAX(e.observed_at_ms) FROM job_events e
                          JOIN owned_jobs j ON j.job_id=e.job_id),0)
            ),
            (EXTRACT(EPOCH FROM clock_timestamp()) * 1000)::bigint",
            &[&workspace_id],
        )
        .map_err(io)?;
    let last_job_activity_ms: i64 = row.get(0);
    let now_ms: i64 = row.get(1);
    if last_job_activity_ms > now_ms.saturating_sub(WORKSPACE_JOB_CONTINUATION_HOLD_MS) {
        return Err(RuntimeError::new(
            RuntimeErrorCode::WorkspaceStateMismatch,
            "Workspace has recent PG Job activity inside the consumer continuation window; an explicit consumerReleased is required before close",
            Some("consumerReleased"),
            true,
        ));
    }
    Ok(())
}

// The same PG consumer definition must govern Workspace mutation/close
// admission AND workspace.get/list projections. A resolved Job can still own
// an active or held_orphaned Attempt reservation: projecting only unresolved
// Jobs would incorrectly report activeJobIds=[] while close remains blocked.
// Build only trusted static query fragments; values remain PostgreSQL bind args.
const WORKSPACE_ACTIVE_OR_HELD: &str = "(
    j.resolution IS NULL OR j.job_id IN (
        SELECT a.job_id FROM attempts a
        JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id
        WHERE r.state IN ('active','held_orphaned')
    )
)";

fn workspace_consumer_sql(select: &str, scope: &str, order_by: &str) -> String {
    format!("SELECT {select} FROM jobs j WHERE {scope} AND {WORKSPACE_ACTIVE_OR_HELD}{order_by}")
}

impl PgRuntime {
    /// Common qualified, lock-ordered transaction for every Workspace write.
    /// Do not take a SERIALIZABLE/REPEATABLE READ snapshot while *waiting* on
    /// the global advisory lock: it can predate a completed Job admission.
    fn begin_workspace_effect_tx<'a>(
        &self,
        db: &'a mut PgAdmissionStore,
    ) -> RuntimeResult<postgres::Transaction<'a>> {
        let mut tx = db
            .client
            .build_transaction()
            .isolation_level(WORKSPACE_EFFECT_ISOLATION)
            .start()
            .map_err(io)?;
        tx.query_one("SELECT pg_advisory_xact_lock($1)", &[&79245017_i64])
            .map_err(io)?;
        self.require_qualified_writer_tx(&mut tx)?;
        Ok(tx)
    }
    /// Close only when PG proves no active or held consumer, then reuse the
    /// existing workspace source/dirty/continuation and dependency checks.
    pub fn close_workspace(
        &self,
        request: &WorkspaceCloseRequest,
    ) -> RuntimeResult<WorkspaceCloseResult> {
        let mut db = self.store()?;
        let mut tx = self.begin_workspace_effect_tx(&mut db)?;
        let active: i64 = tx
            .query_one(
                &workspace_consumer_sql("count(*)", "j.workspace_id=$1", ""),
                &[&request.workspace_id],
            )
            .map_err(io)?
            .get(0);
        if active != 0 {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ConcurrencyLimit,
                "Workspace has PG-owned active or held Jobs",
                Some("workspaceId"),
                false,
            ));
        }
        if !request.consumer_released {
            // The external lifecycle script's initial PG snapshot is
            // advisory only: a Job can start and complete during the scan.
            // This guard shares the native admission lock with workspace.close
            // and must precede any Git/worktree effect.
            require_recent_pg_job_consumer_continuation(&mut tx, &request.workspace_id)?;
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
            .map_err(super::super::error::map_universal_error)?;
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
        let mut tx = self.begin_workspace_effect_tx(&mut db)?;
        request
            .validate_shape()
            .map_err(super::super::error::map_universal_error)?;
        let paths = request
            .mutations
            .iter()
            .map(|m| m.relative_path.clone())
            .collect::<Vec<_>>();
        let access = crate::resource_scheduling::WorkspaceAccess {
            read_only: false,
            read_paths: paths.clone(),
            write_paths: paths,
        };
        let consumers = tx
            .query(
                &workspace_consumer_sql("j.execution_plan_json", "j.workspace_id=$1", ""),
                &[&request.workspace_id],
            )
            .map_err(io)?;
        for row in consumers {
            let plan: RuntimeExecutionPlan = decode(&row.get::<_, String>(0))?;
            if self
                .scheduling_contract(&plan)?
                .workspace_access
                .conflicts(&access)
            {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::ConcurrencyLimit,
                    "Mutation conflicts with a committed Workspace read/write lease",
                    Some("mutations"),
                    true,
                ));
            }
        }
        let result = universal::mutate_workspace(&self.config.executor, request)
            .map_err(super::super::error::map_universal_error)?;
        workspace_effect_commit(tx.commit(), "workspace.mutate")?;
        Ok(result)
    }
    pub fn executor_config(&self) -> UniversalExecutorConfig {
        self.config.executor.clone()
    }
    /// Read-only, source-bound projection. A list page has its own batched
    /// PostgreSQL readback; an exact get retains its own authoritative lookup.
    /// The cheap list projection must never compute a digest and then discard it.
    fn get_workspace_projected(
        &self,
        request: &RuntimeWorkspaceGetRequest,
        include_source_state_digest: bool,
        known_active_jobs: Option<Vec<String>>,
    ) -> RuntimeResult<serde_json::Value> {
        if request.schema_version != 1 {
            return Err(RuntimeError::invalid(
                "schemaVersion must be 1",
                "schemaVersion",
            ));
        }
        let record = universal::load_workspace_record(&self.config.executor, &request.workspace_id)
            .map_err(super::super::error::map_universal_error)?;
        let (head, head_mode, dirty) =
            universal::workspace_head_and_dirty_at(Path::new(&record.workspace_path))
                .map_err(super::super::error::map_universal_error)?;
        let jobs = if let Some(known) = known_active_jobs {
            known
        } else {
            let mut db = self.store()?;
            db.client
                .query(
                    &workspace_consumer_sql(
                        "j.job_id",
                        "j.workspace_id=$1",
                        " ORDER BY j.created_at_ms DESC",
                    ),
                    &[&record.workspace_id],
                )
                .map_err(io)?
                .iter()
                .map(|row| row.get::<_, String>(0))
                .collect::<Vec<_>>()
        };
        let mut result = json!({
            "workspaceId":record.workspace_id,
            "sourceRepo":record.source_repo,
            "sourceRevision":record.source_revision,
            "currentHeadRevision":head,
            "createdAtMs":record.created_unix_ms,
            "headMode":head_mode.as_str(),
            "dirty":dirty,
            "activeJobIds":jobs,
        });
        if include_source_state_digest {
            result["sourceStateDigest"] = json!(universal::workspace_source_state_digest(
                &self.config.executor,
                &request.workspace_id
            )
            .map_err(io)?);
        }
        Ok(result)
    }

    /// Precise get retains the complete source digest and the exact PG
    /// unresolved-or-held consumer readback used to protect close/mutate.
    pub fn get_workspace(
        &self,
        request: &RuntimeWorkspaceGetRequest,
    ) -> RuntimeResult<serde_json::Value> {
        self.get_workspace_projected(request, true, None)
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
            .map_err(super::super::error::map_universal_error)?;
        let mut issues = inventory
            .issues
            .into_iter()
            .map(|issue| {
                let error = super::super::error::map_universal_error(issue.error);
                json!({
                    "workspaceId": issue.workspace_id,
                    "stage": "inventory",
                    "code": error.code.as_str(),
                    "message": error.message,
                    "retryable": error.retryable
                })
            })
            .collect::<Vec<_>>();
        if let Some(cursor) = &request.cursor {
            universal::validate_id(&cursor.workspace_id, "cursor.workspaceId")
                .map_err(super::super::error::map_universal_error)?;
        }
        // Page physical records *before* invoking Git/PG projections. The former
        // implementation inspected every open Workspace, even for limit=1;
        // one damaged old Worktree or expensive source hash could fail or stall
        // the entire list, preventing an Agent from seeing the healthy page.
        let mut records = inventory.records;
        records.sort_by(|a, b| {
            b.created_unix_ms
                .cmp(&a.created_unix_ms)
                .then_with(|| a.workspace_id.cmp(&b.workspace_id))
        });
        if let Some(cursor) = &request.cursor {
            records.retain(|record| {
                record.created_unix_ms < u128::from(cursor.created_at_ms)
                    || (record.created_unix_ms == u128::from(cursor.created_at_ms)
                        && record.workspace_id.as_str() > cursor.workspace_id.as_str())
            });
        }
        let more = records.len() > request.limit as usize;
        records.truncate(request.limit as usize);
        // Advance over the physical page, not just projected successes, so a
        // corrupt Git checkout cannot trap callers on an identical cursor.
        let next_cursor = if more {
            records.last().map(|record| {
                json!({
                    "createdAtMs": record.created_unix_ms,
                    "workspaceId": record.workspace_id
                })
            })
        } else {
            None
        };
        // One PostgreSQL readback for the selected page, rather than one new
        // connection, qualification check, and SQL query per Workspace.
        // This is a projection of one PG observation, not a claim that Git
        // and PostgreSQL participate in the same physical snapshot.
        let ids = records
            .iter()
            .map(|record| record.workspace_id.clone())
            .collect::<Vec<_>>();
        let mut active_jobs: std::collections::BTreeMap<String, Vec<String>> =
            std::collections::BTreeMap::new();
        if !ids.is_empty() {
            let mut db = self.store()?;
            for row in db
                .client
                .query(
                    &workspace_consumer_sql(
                        "j.workspace_id,j.job_id",
                        "j.workspace_id = ANY($1::TEXT[])",
                        " ORDER BY j.created_at_ms DESC",
                    ),
                    &[&ids],
                )
                .map_err(io)?
            {
                active_jobs
                    .entry(row.get::<_, String>(0))
                    .or_default()
                    .push(row.get::<_, String>(1));
            }
        }
        let mut workspaces = Vec::with_capacity(records.len());
        for record in records {
            let workspace_id = record.workspace_id;
            let jobs = active_jobs.remove(&workspace_id).unwrap_or_default();
            match self.get_workspace_projected(
                &RuntimeWorkspaceGetRequest {
                    schema_version: 1,
                    workspace_id: workspace_id.clone(),
                },
                request.include_source_state_digest,
                Some(jobs),
            ) {
                Ok(value) => {
                    workspaces.push(value);
                }
                Err(error) if error.is_reconciliation_fatal() => return Err(error),
                Err(error) => issues.push(json!({
                    "workspaceId": workspace_id,
                    "stage": "projection",
                    "code": error.code.as_str(),
                    "message": error.message,
                    "retryable": error.retryable
                })),
            }
        }
        Ok(json!({
            "workspaces": workspaces,
            "nextCursor": next_cursor,
            "issues": issues
        }))
    }
    pub fn open_workspace(
        &self,
        request: &GitWorkspaceCreateRequest,
    ) -> RuntimeResult<CompactWorkspaceOpenResult> {
        let mut db = self.store()?;
        let tx = self.begin_workspace_effect_tx(&mut db)?;
        // Both host VHD backing and guest PostgreSQL/worktree carriers must
        // pass while the existing PG Workspace effect/admission lock is held.
        super::engine::ensure_workspace_headroom(&self.config.workspace_headroom)?;
        let mut result = universal::create_git_workspace(&self.config.executor, request)
            .map_err(super::super::error::map_universal_error)?;
        workspace_effect_commit(tx.commit(), "workspace.open")?;
        result.retention_notice = Some(
            "PG Runtime Workspace is temporary. The installed systemd lifecycle timer has an operator-defined cadence; do not assume an hourly sweep. Four hours after the latest Job activity is a minimum quiet period, not an ownership lease or promised cleanup time. An eligible clean Workspace may be reclaimed after native Job, source, and policy checks. Other Agent or external consumers are not proven absent by Job completion or a caller's consumerReleased assertion. Publish valuable source and ignored outputs to their real Git/Artifact/destination consumers and read them back before relinquishing the Workspace. Continue unfinished work in a new or retained Workspace."
                .to_string(),
        );
        Ok(result)
    }
}

#[cfg(test)]
mod workspace_active_consumer_tests {
    use super::*;

    /// Check actual PostgreSQL joins, not a mock predicate. A terminal Job
    /// with an orphaned/held reservation must appear in both consumer read
    /// projections because Workspace.close and mutate still own that lease.
    /// No production tables are touched; all fixture tables are TEMP.
    #[test]
    #[ignore = "requires explicitly disposable ORDIVON_PG_TEST_DSN"]
    fn native_pg_held_terminal_job_is_visible_to_workspace_reads_and_guards() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("dedicated disposable PostgreSQL cluster required");
        let mut pg = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
        pg.batch_execute(
            "CREATE TEMP TABLE jobs (
                job_id TEXT PRIMARY KEY, workspace_id TEXT, resolution TEXT,
                execution_plan_json TEXT, created_at_ms BIGINT
            );
            CREATE TEMP TABLE attempts (attempt_id TEXT PRIMARY KEY, job_id TEXT);
            CREATE TEMP TABLE concurrency_reservations (attempt_id TEXT, state TEXT);
            INSERT INTO jobs VALUES
                ('pending','ws-contract',NULL,'pending-plan',30),
                ('held-terminal','ws-contract','succeeded','held-plan',20),
                ('released-terminal','ws-contract','succeeded','released-plan',10);
            INSERT INTO attempts VALUES ('a-held','held-terminal'),('a-released','released-terminal');
            INSERT INTO concurrency_reservations VALUES
                ('a-held','held_orphaned'),('a-released','released');",
        )
        .unwrap();

        let exact = pg
            .query(
                &workspace_consumer_sql(
                    "j.job_id",
                    "j.workspace_id=$1",
                    " ORDER BY j.created_at_ms DESC",
                ),
                &[&"ws-contract"],
            )
            .unwrap()
            .iter()
            .map(|row| row.get::<_, String>(0))
            .collect::<Vec<_>>();
        let ids = vec!["ws-contract".to_string()];
        let list = pg
            .query(
                &workspace_consumer_sql(
                    "j.workspace_id,j.job_id",
                    "j.workspace_id = ANY($1::TEXT[])",
                    " ORDER BY j.created_at_ms DESC",
                ),
                &[&ids],
            )
            .unwrap()
            .iter()
            .map(|row| row.get::<_, String>(1))
            .collect::<Vec<_>>();
        let close_count: i64 = pg
            .query_one(
                &workspace_consumer_sql("count(*)", "j.workspace_id=$1", ""),
                &[&"ws-contract"],
            )
            .unwrap()
            .get(0);
        let plans = pg
            .query(
                &workspace_consumer_sql("j.execution_plan_json", "j.workspace_id=$1", ""),
                &[&"ws-contract"],
            )
            .unwrap()
            .iter()
            .map(|row| row.get::<_, String>(0))
            .collect::<Vec<_>>();
        assert_eq!(exact, vec!["pending", "held-terminal"]);
        assert_eq!(list, exact, "get/list must not hide PG-held consumers");
        assert_eq!(
            close_count, 2,
            "close must protect every projected consumer"
        );
        assert_eq!(plans.len(), 2, "mutate must see the same PG consumers");
        assert!(plans.contains(&"held-plan".to_string()));
        assert!(!plans.contains(&"released-plan".to_string()));
    }

    #[test]
    fn workspace_consumer_sql_reuses_one_pg_ownership_predicate() {
        for query in [
            workspace_consumer_sql("count(*)", "j.workspace_id=$1", ""),
            workspace_consumer_sql("j.execution_plan_json", "j.workspace_id=$1", ""),
            workspace_consumer_sql("j.job_id", "j.workspace_id=$1", ""),
            workspace_consumer_sql(
                "j.workspace_id,j.job_id",
                "j.workspace_id = ANY($1::TEXT[])",
                "",
            ),
        ] {
            assert!(query.contains(WORKSPACE_ACTIVE_OR_HELD));
            assert!(query.contains("r.state IN ('active','held_orphaned')"));
            assert!(query.contains("j.resolution IS NULL"));
            // PostgreSQL can hash this ownership set once for the bounded
            // Workspace page; a correlated EXISTS can degenerate into one
            // nested-loop probe per historical Job under a large ledger.
            assert!(query.contains("j.job_id IN ("));
        }
    }
}

#[cfg(test)]
mod workspace_lock_snapshot_tests {
    use super::*;
    use std::sync::mpsc;

    /// Reproduce the actual PostgreSQL advisory-lock MVCC order, not an
    /// in-memory model. All writes are confined to an explicitly disposable
    /// ORDIVON_PG_TEST_DSN. A Job inserted by the preceding lock owner MUST
    /// be visible to Workspace.close/mutate after acquiring that same lock.
    #[test]
    #[ignore = "requires explicit disposable ORDIVON_PG_TEST_DSN"]
    fn native_pg_workspace_lock_wait_observes_newly_committed_job_lease() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("dedicated disposable PostgreSQL cluster required");
        let mut admin = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
        let table = format!("runtime_workspace_lock_{}", uuid::Uuid::now_v7().simple());
        admin
            .batch_execute(&format!("CREATE TABLE {table} (job_id TEXT PRIMARY KEY)"))
            .unwrap();
        let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            for (legacy, expected) in [(true, 0_i64), (false, 1_i64)] {
                admin
                    .batch_execute(&format!("TRUNCATE TABLE {table}"))
                    .unwrap();
                let mut holder = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
                let mut waiter = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
                let waiter_pid: i32 = waiter
                    .query_one("SELECT pg_backend_pid()", &[])
                    .unwrap()
                    .get(0);
                let mut holder_tx = holder
                    .build_transaction()
                    .isolation_level(postgres::IsolationLevel::Serializable)
                    .start()
                    .unwrap();
                holder_tx
                    .query_one("SELECT pg_advisory_xact_lock($1)", &[&79245017_i64])
                    .unwrap();
                holder_tx
                    .execute(
                        &format!("INSERT INTO {table} VALUES ('admitted-before-release')"),
                        &[],
                    )
                    .unwrap();

                let (started, observed) = mpsc::sync_channel::<()>(1);
                let selected = table.clone();
                let thread = std::thread::spawn(move || {
                    let mut waiting_tx = waiter
                        .build_transaction()
                        .isolation_level(if legacy {
                            postgres::IsolationLevel::Serializable
                        } else {
                            WORKSPACE_EFFECT_ISOLATION
                        })
                        .start()
                        .unwrap();
                    started.send(()).unwrap();
                    waiting_tx
                        .query_one("SELECT pg_advisory_xact_lock($1)", &[&79245017_i64])
                        .unwrap();
                    let count: i64 = waiting_tx
                        .query_one(
                            &format!(
                                "SELECT count(*) FROM {selected} WHERE job_id='admitted-before-release'"
                            ),
                            &[],
                        )
                        .unwrap()
                        .get(0);
                    waiting_tx.commit().unwrap();
                    count
                });
                observed
                    .recv_timeout(std::time::Duration::from_secs(2))
                    .unwrap();
                let deadline = std::time::Instant::now() + std::time::Duration::from_secs(4);
                loop {
                    let waiting = admin
                        .query_one(
                            "SELECT wait_event_type='Lock' AND wait_event='advisory' \
                         FROM pg_stat_activity WHERE pid=$1",
                            &[&waiter_pid],
                        )
                        .unwrap();
                    if waiting.get::<_, Option<bool>>(0) == Some(true) {
                        break;
                    }
                    assert!(
                        std::time::Instant::now() < deadline,
                        "second PG transaction never waited on the actual advisory lock"
                    );
                    std::thread::sleep(std::time::Duration::from_millis(20));
                }
                // Only now may the prior Job admission complete. SERIALIZABLE
                // already pinned its MVCC snapshot before this COMMIT;
                // READ COMMITTED takes its next snapshot after this COMMIT.
                holder_tx.commit().unwrap();
                let seen = thread.join().unwrap();
                assert_eq!(
                    seen, expected,
                    "Workspace SQL must see a newly committed Job after lock acquisition; legacy SERIALIZABLE is a negative control"
                );
            }
        }));
        admin.batch_execute(&format!("DROP TABLE {table}")).unwrap();
        if let Err(panic) = result {
            std::panic::resume_unwind(panic);
        }
    }
}
