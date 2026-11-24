//! Scheduling business contract: fairness, capacity uncertainty, committed PG identity.
use super::*;

fn node() -> NodeResources {
    NodeResources {
        cpu_millis: 1_000,
        memory_total_bytes: 1_000,
        memory_available_bytes: 1_000,
        pid_capacity: 1_000,
        pids_available: 1_000,
        cpu_pressure: 0.0,
        memory_pressure: 0.0,
        io_pressure: 0.0,
    }
}

fn candidate(owner: &str, priority: i16, order: usize) -> PendingCandidate {
    let spec = ResourceScheduling {
        owner: owner.into(),
        priority,
        ..Default::default()
    };
    PendingCandidate {
        priority,
        order,
        job: format!("job-{order}"),
        principal: owner.into(),
        attempt_id: format!("attempt-{order}"),
        workspace_id: "workspace-test".into(),
        spec,
    }
}

fn realistic_node() -> NodeResources {
    NodeResources {
        cpu_millis: 1_000,
        memory_total_bytes: 2 * 1024 * 1024 * 1024,
        memory_available_bytes: 1024 * 1024 * 1024,
        pid_capacity: 10_000,
        pids_available: 9_000,
        cpu_pressure: 0.0,
        memory_pressure: 0.0,
        io_pressure: 0.0,
    }
}

#[test]
fn invalid_accepted_plan_is_job_scoped_not_registry_unavailable() {
    let error = decode_accepted_candidate("{not-valid-json").unwrap_err();
    assert_eq!(error.code, RuntimeErrorCode::InvalidRequest);
    assert_eq!(error.field.as_deref(), Some("executionPlan"));
    assert!(!error.retryable);
}

#[test]
fn global_failures_are_never_categorized_as_local_candidate_errors() {
    for code in [
        RuntimeErrorCode::RegistryUnavailable,
        RuntimeErrorCode::RegistryBusy,
        RuntimeErrorCode::RegistryCorrupt,
        RuntimeErrorCode::ToolFailed,
    ] {
        let error = RuntimeError::new(code, "global unknown", None, true);
        assert!(!is_job_scoped_reconciliation_error(&error));
    }
    let provider = RuntimeError::new(
        RuntimeErrorCode::ProviderStateMismatch,
        "native runner changed after admission",
        Some("executionProvider"),
        false,
    );
    assert!(is_job_scoped_reconciliation_error(&provider));
    assert!(!is_job_scoped_reconciliation_error(&native_resource_error(
        "missing cgroup controls"
    )));
}

#[test]
fn missing_node_observation_is_not_resource_infeasible() {
    let error = native_resource_error("missing /proc/pressure/memory");
    assert_eq!(error.code, RuntimeErrorCode::ToolFailed);
    assert!(error.retryable);
    assert_eq!(error.field.as_deref(), Some("scheduling.resources"));
    assert!(!is_job_scoped_reconciliation_error(&error));
    assert!(!error
        .message
        .contains("resource pressure or workspace lease"));
}

#[test]
fn native_allocation_missing_controller_is_unknown_not_zero_usage() {
    let root = std::env::temp_dir().join(format!(
        "ordivon-pg-native-observation-{}",
        uuid::Uuid::now_v7()
    ));
    fs::create_dir(&root).unwrap();
    let group = root.join("ordivon-pg-attempt.service");
    fs::create_dir(&group).unwrap();
    fs::write(group.join("memory.current"), "128\n").unwrap();
    let request = ResourceRequest {
        memory_bytes: 1024,
        pids: 16,
        ..Default::default()
    };
    let error = unspent_native_allocation(&group, &request)
        .expect_err("missing pids.current is UNKNOWN, not zero usage");
    assert_eq!(error.code, RuntimeErrorCode::ToolFailed);
    fs::remove_dir_all(root).unwrap();
}

#[test]
fn native_allocation_missing_unit_reserves_full_budget_but_malformed_is_unknown() {
    let root = std::env::temp_dir().join(format!(
        "ordivon-pg-native-observation-{}",
        uuid::Uuid::now_v7()
    ));
    fs::create_dir(&root).unwrap();
    let group = root.join("not-yet-started.service");
    let request = ResourceRequest {
        memory_bytes: 1024,
        pids: 16,
        ..Default::default()
    };
    assert_eq!(
        unspent_native_allocation(&group, &request).unwrap(),
        (1024, 16)
    );
    fs::create_dir(&group).unwrap();
    fs::write(group.join("memory.current"), "malformed\n").unwrap();
    fs::write(group.join("pids.current"), "3\n").unwrap();
    let error = unspent_native_allocation(&group, &request)
        .expect_err("bad controller output must preserve UNKNOWN");
    assert_eq!(error.code, RuntimeErrorCode::ToolFailed);
    fs::write(group.join("memory.current"), "128\n").unwrap();
    assert_eq!(
        unspent_native_allocation(&group, &request).unwrap(),
        (896, 13)
    );
    fs::remove_dir_all(root).unwrap();
}

#[test]
fn preflight_filters_only_known_infeasible_candidates() {
    let node = realistic_node();
    let first = candidate("a", 0, 0);
    let second = candidate("b", 0, 1);
    let mut preflight = SchedulerPreflight::default();
    assert!(preflight.allows(&first, &node));
    assert!(preflight.record_allocation(&first));
    assert!(!preflight.record_allocation(&first));
    // Exclusive Workspace lease conflicts even when CPU is plentiful.
    assert!(!preflight.allows(&second, &node));
    // Existing Attempt must resume through the idempotent PG claim.
    assert!(preflight.allows(&first, &node));

    let mut elsewhere = candidate("b", 0, 2);
    elsewhere.workspace_id = "independent-workspace".into();
    assert!(preflight.allows(&elsewhere, &node));
    preflight.reserved_cpu = 950;
    assert!(!preflight.allows(&elsewhere, &node));

    preflight.reserved_cpu = 0;
    let mut pressured = realistic_node();
    pressured.memory_pressure = 6.0;
    assert!(!preflight.allows(&elsewhere, &pressured));
    assert!(preflight.allows(&first, &pressured));
    let mut no_memory = realistic_node();
    no_memory.memory_available_bytes = 1024;
    assert!(!preflight.allows(&elsewhere, &no_memory));
}

#[test]
fn preflight_preserves_concurrent_readers() {
    let node = realistic_node();
    let mut first = candidate("a", 0, 0);
    first.spec.workspace_access.read_only = true;
    let mut second = candidate("b", 0, 1);
    second.spec.workspace_access.read_only = true;
    let mut preflight = SchedulerPreflight::default();
    assert!(preflight.record_allocation(&first));
    assert!(preflight.allows(&second, &node));
}

#[test]
fn scheduler_preserves_priority_before_share_and_fifo() {
    let candidates = [
        candidate("a", 0, 0),
        candidate("b", 1, 1),
        candidate("c", 1, 2),
    ];
    let mut usage = BTreeMap::new();
    usage.insert("b".into(), (900, 0, 0));
    assert_eq!(next_candidate(&candidates, &usage, &node()), Some(2));
    usage.insert("c".into(), (900, 0, 0));
    assert_eq!(next_candidate(&candidates, &usage, &node()), Some(1));
}

#[test]
fn scheduler_recomputes_owner_shares_after_allocation() {
    let candidates = [candidate("a", 0, 0), candidate("b", 0, 1)];
    let mut usage = BTreeMap::new();
    assert_eq!(next_candidate(&candidates, &usage, &node()), Some(0));
    usage.insert("a".into(), (100, 0, 0));
    assert_eq!(next_candidate(&candidates, &usage, &node()), Some(1));
    assert_eq!(next_candidate(&[], &usage, &node()), None);
}

#[test]
fn preflight_accounts_for_new_claims_not_yet_visible_in_native_snapshot() {
    let node = realistic_node();
    let mut first = candidate("a", 0, 0);
    first.spec.resources.memory_bytes = 600 * 1024 * 1024;
    let mut second = candidate("b", 0, 1);
    second.workspace_id = "other-workspace".into();
    second.spec.resources.memory_bytes = 600 * 1024 * 1024;

    let mut preflight = SchedulerPreflight::default();
    assert!(preflight.allows(&first, &node));
    assert!(preflight.record_allocation(&first));
    assert_eq!(preflight.newly_reserved_memory, 600 * 1024 * 1024);
    // No second PG claim/cgroup scan for a capacity estimate already
    // contradicted by allocations made since the OS snapshot.
    assert!(!preflight.allows(&second, &node));
    // An already admitted Attempt must still resume idempotently.
    assert!(preflight.allows(&first, &node));
    assert!(!preflight.record_allocation(&first));
    assert_eq!(preflight.newly_reserved_memory, 600 * 1024 * 1024);

    let mut fresh = SchedulerPreflight::default();
    fresh.active_attempts.insert(first.attempt_id.clone());
    fresh.reserved_cpu = u64::from(first.spec.resources.cpu_millis);
    // Old active reservations already reflected by native observation
    // must not be double-charged to the newly reserved budget.
    assert!(fresh.allows(&second, &node));
}

#[test]
fn preflight_accounts_for_unobserved_pid_reservations() {
    let node = realistic_node();
    let mut first = candidate("a", 0, 0);
    first.spec.resources.pids = 6_000;
    let mut second = candidate("b", 0, 1);
    second.workspace_id = "other-workspace".into();
    second.spec.resources.pids = 6_000;

    let mut preflight = SchedulerPreflight::default();
    assert!(preflight.allows(&first, &node));
    assert!(preflight.record_allocation(&first));
    assert_eq!(preflight.newly_reserved_pids, 6_000);
    assert!(!preflight.allows(&second, &node));
    assert!(preflight.allows(&first, &node));
    assert!(!preflight.record_allocation(&first));
    assert_eq!(preflight.newly_reserved_pids, 6_000);
}

#[test]
fn initial_preflight_keeps_late_eligible_and_existing_idempotent_attempts() {
    let node = realistic_node();
    let mut preflight = SchedulerPreflight::default();
    preflight
        .leases
        .insert("busy".into(), vec![WorkspaceAccess::default()]);
    let mut ranked = (0..3_000)
        .map(|order| {
            let mut candidate = candidate("blocked", 0, order);
            candidate.workspace_id = "busy".into();
            candidate
        })
        .collect::<Vec<_>>();
    // Existing Allocation must be revisited even when a Workspace lease
    // would otherwise reject a second new claim.
    preflight
        .active_attempts
        .insert(ranked[0].attempt_id.clone());
    let mut tail = candidate("eligible", 10, 3_000);
    tail.workspace_id = "independent".into();
    ranked.push(tail);

    preflight.retain_initially_feasible(&mut ranked, &node);
    assert_eq!(ranked.len(), 2);
    assert_eq!(ranked[0].order, 0);
    assert_eq!(ranked[1].order, 3_000);
    assert_eq!(next_candidate(&ranked, &BTreeMap::new(), &node), Some(1));
}

#[test]
fn initial_preflight_does_not_skip_candidates_later_blocked_by_new_claims() {
    let node = realistic_node();
    let mut preflight = SchedulerPreflight::default();
    let mut first = candidate("a", 1, 0);
    first.workspace_id = "workspace-1".into();
    first.spec.resources.memory_bytes = 600 * 1024 * 1024;
    let mut second = candidate("b", 0, 1);
    second.workspace_id = "workspace-2".into();
    second.spec.resources.memory_bytes = 600 * 1024 * 1024;
    let mut ranked = vec![first, second];

    // Both fit the initial OS snapshot. Removing either would violate
    // Priority/DRF/FIFO eligibility, even if only one can later commit.
    preflight.retain_initially_feasible(&mut ranked, &node);
    assert_eq!(ranked.len(), 2);
    assert_eq!(next_candidate(&ranked, &BTreeMap::new(), &node), Some(0));
    assert!(preflight.record_allocation(&ranked.remove(0)));
    assert!(!preflight.allows(&ranked[0], &node));
}

#[test]
#[ignore = "requires explicit disposable ORDIVON_PG_TEST_DSN"]
fn native_pg_pending_requires_attempt_to_belong_to_its_job() {
    // This intentionally reproduces a cross-Job current_attempt_id link:
    // attempts.attempt_id is PK but jobs.current_attempt_id is not UNIQUE.
    // TEMP tables keep this test isolated from any persistent Registry.
    let dsn =
        std::env::var("ORDIVON_PG_TEST_DSN").expect("explicit disposable PG test DSN required");
    let mut db = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
    db.batch_execute(
        "CREATE TEMP TABLE jobs (
                job_id text PRIMARY KEY,
                principal text NOT NULL,
                execution_plan_json text NOT NULL,
                current_attempt_id text NOT NULL,
                resolution text,
                desired_state text NOT NULL,
                created_at_ms bigint NOT NULL
             );
             CREATE TEMP TABLE attempts (
                attempt_id text PRIMARY KEY,
                job_id text NOT NULL,
                state text NOT NULL
             );
             CREATE TEMP TABLE job_runtime_release_effects(job_id text PRIMARY KEY);
             INSERT INTO jobs VALUES
                ('job-a','principal-a','{}','attempt-a',NULL,'run',1),
                ('job-b','principal-b','{}','attempt-a',NULL,'run',2);
             INSERT INTO attempts VALUES ('attempt-a','job-a','accepted');",
    )
    .unwrap();
    let found = db.query(PENDING_JOBS_SQL, &[]).unwrap();
    assert_eq!(found.len(), 1);
    assert_eq!(found[0].get::<_, String>(0), "job-a");
    assert_eq!(found[0].get::<_, String>(3), "attempt-a");
}

#[test]
fn scheduler_readback_does_not_invent_placement_failure_cause() {
    let req = ResourceScheduling::default();
    let pending = scheduling_readback(req.clone(), Some("accepted"), "run", None, false);
    assert_eq!(pending["state"], "pending");
    assert_eq!(pending["pendingReason"], "cause_unobserved");

    let cancelled = scheduling_readback(req.clone(), Some("accepted"), "cancelled", None, false);
    assert_eq!(cancelled["state"], "released");
    assert!(cancelled["pendingReason"].is_null());
    let resolved = scheduling_readback(req.clone(), Some("accepted"), "run", Some("lost"), false);
    assert_eq!(resolved["state"], "released");
    let starting = scheduling_readback(req.clone(), Some("starting"), "run", None, false);
    assert_eq!(starting["state"], "released");
    let allocated = scheduling_readback(req, Some("running"), "run", None, true);
    assert_eq!(allocated["state"], "allocated");
    assert!(allocated["pendingReason"].is_null());
}

#[test]
#[ignore = "requires explicit disposable ORDIVON_PG_TEST_DSN"]
fn native_pg_scheduling_uses_current_attempt_not_highest_attempt_number() {
    let dsn = std::env::var("ORDIVON_PG_TEST_DSN").expect("explicit disposable PG DSN required");
    let mut db = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
    db.batch_execute(
        "CREATE TEMP TABLE jobs (
               job_id text PRIMARY KEY, execution_plan_json text,
               current_attempt_id text, desired_state text, resolution text
             );
             CREATE TEMP TABLE attempts (
               attempt_id text PRIMARY KEY, job_id text, attempt_number bigint, state text
             );
             CREATE TEMP TABLE job_allocations (attempt_id text, state text);
             INSERT INTO jobs VALUES ('job-r3','{}','attempt-current','run',NULL);
             INSERT INTO attempts VALUES ('attempt-current','job-r3',1,'accepted'),
                 ('attempt-later','job-r3',2,'running');",
    )
    .unwrap();
    let row = db.query_one(SCHEDULING_READBACK_SQL, &[&"job-r3"]).unwrap();
    assert_eq!(row.get::<_, Option<String>>(1).as_deref(), Some("accepted"));
    assert_eq!(row.get::<_, String>(3), "run");
    assert!(row.get::<_, Option<String>>(4).is_none());
}
