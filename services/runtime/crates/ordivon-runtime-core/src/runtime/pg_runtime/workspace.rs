//! PostgreSQL Runtime Workspace identity, mutation and inventory.
//! Consumer-safe retirement is isolated in workspace/retirement.rs.
use super::*;
mod retirement;

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

// Reuse the existing legacy Runtime bounded-Git-probe pattern (452e0c):
// the PG-only page already batches SQL and still needs current Git truth.
const WORKSPACE_LIST_LIVE_GIT_PARALLELISM: usize = 4;

// One conservative PG protection predicate for get/list/mutate/close.
// A Job is absent from the protection set only when its resolution agrees
// with a latest Attempt, it has no current pointer, every persisted Attempt
// has a known settled state + terminal witnesses + released reservation,
// and every recorded allocation has a release witness. An absent allocation
// is permitted by the historical schema; a missing reservation is not.
// These IDs are protection roots (including ambiguous durable state), NOT
// a claim that each Job is physically running. Age is a separate retirement
// prerequisite; a caller release never waives unsettled roots.
// Use one set-shaped query scoped to the requested Workspace page; values
// remain PostgreSQL bind arguments, and off-page history is not a root.
const WORKSPACE_ACTIVE_OR_HELD: &str = "(
    j.resolution IS NULL OR j.current_attempt_id IS NOT NULL OR j.job_id IN (
        SELECT a.job_id FROM attempts a JOIN scoped_jobs own ON own.job_id=a.job_id
        LEFT JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id
        WHERE a.state NOT IN ('succeeded','failed','timed_out','cancelled','lost')
           OR a.finished_at_ms IS NULL OR a.finished_at_ms < 0
           OR a.result_digest IS NULL OR a.result_digest = ''
           OR r.state IS DISTINCT FROM 'released'
           OR r.released_at_ms IS NULL OR r.released_at_ms < 0
        UNION ALL
        SELECT a.job_id FROM attempts a JOIN scoped_jobs own ON own.job_id=a.job_id JOIN job_allocations al
            ON al.attempt_id=a.attempt_id
        WHERE al.state IS DISTINCT FROM 'released'
           OR al.released_at_ms IS NULL OR al.released_at_ms < 0
        UNION ALL
        SELECT owned.job_id FROM scoped_jobs owned LEFT JOIN (
            SELECT DISTINCT ON (a.job_id) a.job_id,a.state FROM attempts a JOIN scoped_jobs own ON own.job_id=a.job_id
            ORDER BY a.job_id,a.attempt_number DESC
        ) latest ON latest.job_id=owned.job_id
        WHERE owned.resolution IS DISTINCT FROM latest.state
    )
)";

fn workspace_consumer_sql(select: &str, scope: &str, order_by: &str) -> String {
    format!("WITH scoped_jobs AS MATERIALIZED (
        SELECT j.job_id,j.workspace_id,j.resolution,j.current_attempt_id,j.created_at_ms,j.execution_plan_json
        FROM jobs j WHERE {scope}
    ) SELECT {select} FROM scoped_jobs j WHERE {WORKSPACE_ACTIVE_OR_HELD}{order_by}")
}

impl PgRuntime {
    /// Common qualified, lock-ordered transaction for every Workspace write.
    /// Do not take a SERIALIZABLE/REPEATABLE READ snapshot while *waiting* on
    /// the global advisory lock: it can predate a completed Job admission.
    pub(super) fn begin_workspace_effect_tx<'a>(
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
        known_git: Option<
            Result<(String, universal::WorkspaceHeadMode, bool), universal::UniversalExecError>,
        >,
        inventory_record: Option<&universal::WorkspaceRecord>,
    ) -> RuntimeResult<serde_json::Value> {
        if request.schema_version != 1 {
            return Err(RuntimeError::invalid(
                "schemaVersion must be 1",
                "schemaVersion",
            ));
        }
        let record = universal::load_workspace_record(&self.config.executor, &request.workspace_id)
            .map_err(super::super::error::map_universal_error)?;
        if let Some(observed) = inventory_record {
            // The page's Git probe may run concurrently with a close/reopen.
            // Never attach HEAD/dirty from that earlier physical identity to
            // a new durable Workspace record with the same public ID.
            if &record != observed {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::WorkspaceStateMismatch,
                    "Workspace identity changed between physical list inventory and Git projection",
                    Some("workspaceId"),
                    true,
                ));
            }
        }
        let (head, head_mode, dirty) = known_git
            .unwrap_or_else(|| {
                universal::workspace_head_and_dirty_at(Path::new(&record.workspace_path))
            })
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
        self.get_workspace_projected(request, true, None, None, None)
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
        // Git status is the real source of HEAD/dirty truth. Bound read-only
        // fan-out within the selected physical page; never cache these results
        // or treat a successful Git probe as original Run consumer release.
        // Exact digest mode intentionally stays serial to bound disk pressure.
        let live_git = if records.len() <= 1 || request.include_source_state_digest {
            records
                .iter()
                .map(|record| {
                    universal::workspace_head_and_dirty_at(Path::new(&record.workspace_path))
                })
                .collect::<Vec<_>>()
        } else {
            let workers = records.len().min(WORKSPACE_LIST_LIVE_GIT_PARALLELISM);
            let chunk_size = records.len().div_ceil(workers);
            std::thread::scope(|scope| -> RuntimeResult<Vec<_>> {
                let mut threads = Vec::with_capacity(workers);
                for (chunk_index, chunk) in records.chunks(chunk_size).enumerate() {
                    threads.push(scope.spawn(move || {
                        chunk
                            .iter()
                            .enumerate()
                            .map(|(offset, record)| {
                                (
                                    chunk_index * chunk_size + offset,
                                    universal::workspace_head_and_dirty_at(Path::new(
                                        &record.workspace_path,
                                    )),
                                )
                            })
                            .collect::<Vec<_>>()
                    }));
                }
                let mut indexed = Vec::with_capacity(records.len());
                for worker in threads {
                    indexed.extend(worker.join().map_err(|_| {
                        RuntimeError::new(
                            RuntimeErrorCode::ToolFailed,
                            "Workspace live Git projection worker panicked",
                            Some("workspaceId"),
                            false,
                        )
                    })?);
                }
                indexed.sort_by_key(|(index, _)| *index);
                Ok(indexed.into_iter().map(|(_, git)| git).collect())
            })?
        };
        let mut workspaces = Vec::with_capacity(records.len());
        for (record, git) in records.into_iter().zip(live_git) {
            let workspace_id = record.workspace_id.clone();
            let jobs = active_jobs.remove(&workspace_id).unwrap_or_default();
            match self.get_workspace_projected(
                &RuntimeWorkspaceGetRequest {
                    schema_version: 1,
                    workspace_id: workspace_id.clone(),
                },
                request.include_source_state_digest,
                Some(jobs),
                Some(git),
                Some(&record),
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
        super::workspace_headroom::ensure_workspace_headroom(&self.config.workspace_headroom)?;
        let mut result = universal::create_git_workspace(&self.config.executor, request)
            .map_err(super::super::error::map_universal_error)?;
        workspace_effect_commit(tx.commit(), "workspace.open")?;
        result.retention_notice = Some(
            "PG Runtime Workspace is temporary. The systemd lifecycle timer may be disabled; when enabled, its cadence is operator-defined and no cleanup is guaranteed. Four hours after the latest Job activity is a minimum quiet period, not an ownership lease or promised cleanup time. An eligible clean Workspace may be reclaimed after native Job, source, and policy checks. Other Agent or external consumers are not proven absent by Job completion or a caller's consumerReleased assertion. Publish valuable source and ignored outputs to their real Git/Artifact/destination consumers and read them back before relinquishing the Workspace. Continue unfinished work in a new or retained Workspace."
                .to_string(),
        );
        Ok(result)
    }
}

#[cfg(test)]
mod workspace_active_consumer_tests {
    use super::*;

    /// Check actual PostgreSQL joins, not a mock predicate. Terminal Job
    /// labels cannot hide unresolved, malformed, or held resource roots.
    /// All normal read/effect projections share this protection predicate.
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
                execution_plan_json TEXT, created_at_ms BIGINT, current_attempt_id TEXT
            );
            CREATE TEMP TABLE attempts (
                attempt_id TEXT PRIMARY KEY, job_id TEXT, attempt_number BIGINT,
                state TEXT NOT NULL, finished_at_ms BIGINT, result_digest TEXT
            );
            CREATE TEMP TABLE concurrency_reservations (
                attempt_id TEXT PRIMARY KEY, state TEXT NOT NULL, released_at_ms BIGINT
            );
            CREATE TEMP TABLE job_allocations (
                attempt_id TEXT PRIMARY KEY, state TEXT NOT NULL, released_at_ms BIGINT
            );
            INSERT INTO jobs VALUES
                ('pending','ws-contract',NULL,'pending-plan',30,NULL),
                ('held-terminal','ws-contract','succeeded','held-plan',20,NULL),
                ('released-terminal','ws-contract','succeeded','released-plan',10,NULL),
                ('unsettled-terminal','ws-contract','succeeded','unsettled-plan',15,NULL),
                ('unrelated','ws-other','succeeded','unrelated-plan',35,NULL);
            INSERT INTO attempts VALUES
                ('a-held','held-terminal',1,'orphaned',1,'result'),
                ('a-released','released-terminal',1,'succeeded',1,'result'),
                ('a-old','unsettled-terminal',1,'running',NULL,NULL),
                ('a-new','unsettled-terminal',2,'succeeded',1,'result'),
                ('a-unrelated','unrelated',1,'running',NULL,NULL);
            INSERT INTO concurrency_reservations VALUES
                ('a-held','held_orphaned',NULL),('a-released','released',1),
                ('a-old','released',1),('a-new','released',1),
                ('a-unrelated','active',NULL);",
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
        assert_eq!(
            exact,
            vec!["pending", "held-terminal", "unsettled-terminal"]
        );
        assert_eq!(list, exact, "get/list must not hide PG-held consumers");
        assert_eq!(
            close_count, 3,
            "close must protect every projected consumer"
        );
        assert_eq!(plans.len(), 3, "mutate must see the same PG consumers");
        assert!(plans.contains(&"held-plan".to_string()));
        assert!(!plans.contains(&"released-plan".to_string()));

        // Independent counterexamples: each mutation changes the durable
        // evidence of a previously fully settled Job, not a file layout.
        // Every restore must remove the extra protection root again.
        for (change, restore) in [
            (
                "UPDATE attempts SET state='running' WHERE attempt_id='a-released'",
                "UPDATE attempts SET state='succeeded' WHERE attempt_id='a-released'",
            ),
            (
                "UPDATE attempts SET state='future_state' WHERE attempt_id='a-released'",
                "UPDATE attempts SET state='succeeded' WHERE attempt_id='a-released'",
            ),
            (
                "UPDATE attempts SET finished_at_ms=NULL WHERE attempt_id='a-released'",
                "UPDATE attempts SET finished_at_ms=1 WHERE attempt_id='a-released'",
            ),
            (
                "UPDATE attempts SET result_digest='' WHERE attempt_id='a-released'",
                "UPDATE attempts SET result_digest='result' WHERE attempt_id='a-released'",
            ),
            (
                "DELETE FROM concurrency_reservations WHERE attempt_id='a-released'",
                "INSERT INTO concurrency_reservations VALUES ('a-released','released',1)",
            ),
            (
                "UPDATE concurrency_reservations SET state='unknown' WHERE attempt_id='a-released'",
                "UPDATE concurrency_reservations SET state='released' WHERE attempt_id='a-released'",
            ),
            (
                "UPDATE concurrency_reservations SET released_at_ms=NULL WHERE attempt_id='a-released'",
                "UPDATE concurrency_reservations SET released_at_ms=1 WHERE attempt_id='a-released'",
            ),
            (
                "INSERT INTO job_allocations VALUES ('a-released','active',NULL)",
                "DELETE FROM job_allocations WHERE attempt_id='a-released'",
            ),
            (
                "INSERT INTO job_allocations VALUES ('a-released','released',NULL)",
                "DELETE FROM job_allocations WHERE attempt_id='a-released'",
            ),
            (
                "UPDATE jobs SET current_attempt_id='a-released' WHERE job_id='released-terminal'",
                "UPDATE jobs SET current_attempt_id=NULL WHERE job_id='released-terminal'",
            ),
            (
                "UPDATE attempts SET state='failed' WHERE attempt_id='a-released'",
                "UPDATE attempts SET state='succeeded' WHERE attempt_id='a-released'",
            ),
            (
                "INSERT INTO jobs VALUES ('missing-attempt','ws-contract','succeeded','plan',5,NULL)",
                "DELETE FROM jobs WHERE job_id='missing-attempt'",
            ),
        ] {
            let count = |pg: &mut postgres::Client| -> i64 {
                pg.query_one(
                    &workspace_consumer_sql("count(*)", "j.workspace_id=$1", ""),
                    &[&"ws-contract"],
                )
                .unwrap()
                .get(0)
            };
            pg.batch_execute(change).unwrap();
            assert_eq!(count(&mut pg), 4, "{change}");
            pg.batch_execute(restore).unwrap();
            assert_eq!(count(&mut pg), 3, "{restore}");
        }
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
            assert!(query.contains("r.state IS DISTINCT FROM 'released'"));
            assert!(query.contains("j.resolution IS NULL"));
            // PostgreSQL can hash this ownership set once for the bounded
            // Workspace page; a correlated EXISTS can degenerate into one
            // nested-loop probe per historical Job under a large ledger.
            assert!(query.contains("j.job_id IN ("));
            assert!(query.contains("WITH scoped_jobs AS MATERIALIZED"));
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
