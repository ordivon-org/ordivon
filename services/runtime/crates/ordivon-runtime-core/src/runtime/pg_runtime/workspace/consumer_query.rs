//! One PG consumer predicate for get/list, write leases and close; no state copy.
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

pub(super) fn workspace_consumer_sql(select: &str, scope: &str, order_by: &str) -> String {
    format!("SELECT {select} FROM jobs j WHERE {scope} AND {WORKSPACE_ACTIVE_OR_HELD}{order_by}")
}

#[cfg(test)]
mod query_contract_tests {
    use super::*;

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
