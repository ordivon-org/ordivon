//! One actual Python Tool Intent/Fence/Receipt CAS producer -> A PG18 verified
//! readback -> B versioned Tool recovery semantics. No physical Runtime call.
use ordivon_harness_loop_b_probe::pg_tool_head::{
    inspect_pg_tool_head, ToolHeadError, ToolHeadStanding,
};
use ordivon_harness_pg::ReadError;
use postgres::{Client, NoTls};
use serde_json::Value;

#[test]
#[ignore = "private A-owned PG18 + genuine Python source producer"]
fn python_pg_tool_source_intent_fence_receipt_and_unknown_are_distinct_from_dispatch() {
    let dsn = std::env::var("HARNESS_RUST_TEST_PG_DSN").unwrap();
    let schema = std::env::var("HARNESS_RUST_TEST_SCHEMA").unwrap();
    assert!(schema.starts_with("hpg_rust_isolated_a_"));
    let raw =
        std::fs::read_to_string(std::env::var("HARNESS_RUST_TEST_FIXTURE_PATH").unwrap()).unwrap();
    let json: Value = serde_json::from_str(&raw).unwrap();
    let cases = &json["rust_tool_heads"];
    let mut db = Client::connect(&dsn, NoTls).unwrap();

    for label in ["prepared", "unknown_redacted", "stale_revision"] {
        let case = &cases[label];
        let run = case["runId"].as_str().unwrap();
        let head = inspect_pg_tool_head(&mut db, &schema, run)
            .unwrap_or_else(|e| panic!("{label} genuine Python Tool HEAD invalid {e:?}"))
            .unwrap();
        assert_eq!(head.run_id(), run);
        assert_eq!(head.run_revision(), case["revision"].as_i64().unwrap());
        assert_eq!(
            head.prepared_revision(),
            case["preparedRevision"].as_i64().unwrap()
        );
        assert_eq!(head.intent_digest(), case["intentDigest"].as_str().unwrap());
        assert_eq!(head.fence_digest(), case["fenceDigest"].as_str().unwrap());
        assert_eq!(
            head.client_request_id(),
            case["clientRequestId"].as_str().unwrap()
        );
        assert_eq!(head.tool_call_id(), case["toolCallId"].as_str().unwrap());
        assert_eq!(head.recovery_consequence(), "observation-only");
        assert_eq!(
            head.prepared_revision_is_current(),
            case["preparedRevisionCurrent"].as_bool().unwrap()
        );
        let standing = if label == "unknown_redacted" {
            ToolHeadStanding::UnknownRequiresOwnerReconciliation
        } else {
            ToolHeadStanding::PreparedNeedsOwnerAdmission
        };
        assert_eq!(head.standing(), standing);
    }

    for label in [
        "generic_no_intent",
        "cross_run",
        "bad_fence_digest",
        "extra_reference",
        "receipt_event_mismatch",
        "bad_snapshot_binding",
        "bad_snapshot_budget",
    ] {
        let run = cases[label]["runId"].as_str().unwrap();
        assert!(
            matches!(
                inspect_pg_tool_head(&mut db, &schema, run),
                Err(ToolHeadError::Invalid(_)
                    | ToolHeadError::Mismatch(_)
                    | ToolHeadError::Run(ReadError::Corruption(_)))
            ),
            "{label}: generic Journal or stolen other-Run Intent is never qualified"
        );
    }
    let empty = json["no_tool"]["runId"].as_str().unwrap();
    assert!(inspect_pg_tool_head(&mut db, &schema, empty)
        .unwrap()
        .is_none());
    println!("PG18_PYTHON_TYPED_TOOL_INTENT_FENCE_UNKNOWN_RECOVERY_PASS");
    // A readonly role is used (no actual Tool, Runtime or Provider request).
    let can_write: bool = db
        .query_one(
            &format!("SELECT has_table_privilege(current_user,'{schema}.run_events','INSERT')"),
            &[],
        )
        .unwrap()
        .get(0);
    assert!(!can_write);
}
