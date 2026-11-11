//! One actual Python Tool Intent/Fence/Receipt CAS producer -> A PG18 verified
//! readback -> B versioned Tool recovery semantics. No physical Runtime call.
use ordivon_harness_core::loads_strict;
use ordivon_harness_loop_b_probe::pg_tool_head::{
    inspect_pg_tool_head, ToolHeadError, ToolHeadStanding,
};
use ordivon_harness_loop_b_probe::runtime_delivery::{
    interpret_qualified_runtime_observation, qualify_runtime_job_for_tool_head,
    RuntimeDeliveryDecision, RuntimeOwnerEvidenceError,
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

    for label in [
        "prepared",
        "owner_exec_prepared",
        "unknown_redacted",
        "stale_revision",
    ] {
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
        assert_eq!(
            head.recovery_consequence(),
            if label == "owner_exec_prepared" {
                "process-or-external-effect-possible"
            } else {
                "observation-only"
            }
        );
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
        if label == "unknown_redacted" {
            // End-to-end identity join: actual Python-authored Intent CAS
            // comes through A's real PG18 Reader, while Runtime task.list /
            // task.observe are owner-shaped immutable test observations only.
            // There is no Runtime connection or physical effect here.
            let page = serde_json::json!({
                "jobs": [{
                    "jobId": "job:source-recovery",
                    "clientRequestId": head.client_request_id(),
                    "workspaceId": "ws:test-owner-lookup",
                }],
                "nextCursor": null,
            });
            let owner_page = loads_strict(&page.to_string()).unwrap();
            let job = qualify_runtime_job_for_tool_head(&head, &owner_page, "ws:test-owner-lookup")
                .expect("PG Tool Intent must bind one exact Runtime Job identity");
            assert_eq!(job.client_request_id(), head.client_request_id());
            let owner_unknown = loads_strict(
                r#"{
                "jobId":"job:source-recovery",
                "executionTerminal":true,
                "executionDisposition":"lost",
                "deliveryDisposition":"unknown",
                "recoveryRequired":false,
                "resultAvailable":true,
                "semanticCompletionEvaluated":false
            }"#,
            )
            .unwrap();
            assert_eq!(
                interpret_qualified_runtime_observation(&job, &owner_unknown),
                Ok(RuntimeDeliveryDecision::Unknown)
            );
            let wrong_job = loads_strict(
                r#"{
                "jobId":"job:another-tool",
                "status":"succeeded",
                "executionTerminal":true,
                "executionDisposition":"succeeded",
                "deliveryDisposition":"committed",
                "recoveryRequired":false,
                "resultAvailable":true,
                "semanticCompletionEvaluated":false
            }"#,
            )
            .unwrap();
            assert_eq!(
                interpret_qualified_runtime_observation(&job, &wrong_job),
                Err(RuntimeOwnerEvidenceError::ObservationMismatch)
            );
            assert_eq!(
                qualify_runtime_job_for_tool_head(&head, &owner_page, "ws:wrong-workspace")
                    .unwrap_err(),
                RuntimeOwnerEvidenceError::IdentityMismatch,
            );
            println!("PG18_TOOL_INTENT_RUNTIME_OWNER_JOB_IDENTITY_FAIL_CLOSED_PASS");
        }
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
        if matches!(label, "bad_snapshot_binding" | "bad_snapshot_budget") {
            // Source-invalid typed data is not proof that the generic
            // CAS/Journal is corrupt. A read-only Journal still observes
            // the complete hash-valid Event, but tags Tool source invalid.
            let generic = ordivon_harness_pg::read_run_readonly(&mut db, &schema, run).unwrap();
            let latest = generic.events.last().unwrap();
            let source = generic
                .tool_snapshot_metadata
                .iter()
                .find(|s| s.event_id() == latest.event_id)
                .unwrap();
            assert!(!source.source_contract_valid());
        }
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

/// Frozen Python Harness runtime request + actual prepared Fence from PG18
/// must qualify as Rust B's exact, non-executable Owner handoff; any
/// post-Intent mutation must not obtain even a positive source qualification.
#[test]
#[ignore = "private A-owned PG18 + genuine Python owner request and fenced Intent"]
fn python_pg_frozen_effect_request_and_fence_bound_byte_for_byte() {
    use ordivon_harness_core::{loads_strict, CanonicalDocument};
    use ordivon_harness_loop_b_probe::owner_effect_handoff::{
        qualify_workspace_exec_owner_handoff, OwnerHandoffError,
    };
    let dsn = std::env::var("HARNESS_RUST_TEST_PG_DSN").unwrap();
    let schema = std::env::var("HARNESS_RUST_TEST_SCHEMA").unwrap();
    assert!(schema.starts_with("hpg_rust_isolated_a_"));
    let raw =
        std::fs::read_to_string(std::env::var("HARNESS_RUST_TEST_FIXTURE_PATH").unwrap()).unwrap();
    let manifest: Value = serde_json::from_str(&raw).unwrap();
    let fixture = &manifest["rust_owner_handoff"];
    let run_id = fixture["runId"].as_str().unwrap();
    let mut db = Client::connect(&dsn, NoTls).unwrap();
    let head = inspect_pg_tool_head(&mut db, &schema, run_id)
        .unwrap()
        .unwrap();
    let strict = |value: &Value| -> CanonicalDocument {
        loads_strict(&serde_json::to_string(value).unwrap()).unwrap()
    };
    let original = strict(&fixture["originalRequest"]);
    let physical = strict(&fixture["fencedOwnerRequest"]);
    assert_eq!(head.runtime_operation(), "workspace.exec");
    assert_eq!(
        head.standing(),
        ToolHeadStanding::PreparedNeedsOwnerAdmission
    );
    assert!(head.prepared_revision_is_current());
    assert_eq!(
        qualify_workspace_exec_owner_handoff(&head, &original, &physical),
        Ok(())
    );
    for mutation in [
        "executable",
        "arguments",
        "client_request_id",
        "omit_run_contract_grant",
        "wrong_fence_digest",
        "duplicate_fence",
    ] {
        let mut outgoing = fixture["fencedOwnerRequest"].clone();
        match mutation {
            "executable" => {
                outgoing["execution"]["executable"] = Value::String("/usr/bin/false".into())
            }
            "arguments" => outgoing["execution"]["args"] = serde_json::json!(["forged", "."]),
            "client_request_id" => {
                outgoing["clientRequestId"] = Value::String("request:forged-after-prepare".into())
            }
            "omit_run_contract_grant" => {
                let refs = outgoing["execution"]["foreignReferences"]
                    .as_array_mut()
                    .unwrap();
                refs.retain(|item| item["type"] != "tool_grant");
            }
            "wrong_fence_digest" => {
                let refs = outgoing["execution"]["foreignReferences"]
                    .as_array_mut()
                    .unwrap();
                refs.last_mut().unwrap()["digest"] =
                    Value::String("sha256:".to_owned() + "a".repeat(64).as_str());
            }
            "duplicate_fence" => {
                let refs = outgoing["execution"]["foreignReferences"]
                    .as_array_mut()
                    .unwrap();
                refs.push(refs.last().unwrap().clone());
            }
            _ => unreachable!(),
        }
        assert!(
            qualify_workspace_exec_owner_handoff(&head,&original,&strict(&outgoing)).is_err(),
            "{mutation}: Runtime owner request must be byte-identical to prepared Intent + one Fence"
        );
    }
    for label in ["stale_revision", "unknown_redacted"] {
        let stale_run = manifest["rust_tool_heads"][label]["runId"]
            .as_str()
            .unwrap();
        let not_ready = inspect_pg_tool_head(&mut db, &schema, stale_run)
            .unwrap()
            .unwrap();
        assert_eq!(
            qualify_workspace_exec_owner_handoff(&not_ready, &original, &physical),
            Err(OwnerHandoffError::UnqualifiedHistoricalToolHead)
        );
    }
    println!("PG18_PYTHON_FROZEN_OWNER_REQUEST_AND_FENCE_RUST_PURE_HANDOFF_PASS");
}
