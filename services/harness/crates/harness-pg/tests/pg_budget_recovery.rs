//! Test-only cross-language consumer of the existing verified PG Journal.
use ordivon_harness_core::{
    digest_bytes, loads_strict,
    run_budget::{restore_run_budget, MaterializedRunLimits},
};
use ordivon_harness_pg::read_run_readonly;

#[test]
#[ignore = "requires explicitly provisioned isolated synthetic PG fixture"]
fn original_public_resume_agrees_with_native_budget_recovery() {
    let dsn = std::env::var("HARNESS_RUST_BUDGET_READER_DSN").unwrap();
    let schema = std::env::var("HARNESS_RUST_BUDGET_SCHEMA").unwrap();
    let fixture =
        std::fs::read_to_string(std::env::var("HARNESS_RUST_BUDGET_FIXTURE").unwrap()).unwrap();
    let fixture: serde_json::Value = serde_json::from_str(&fixture).unwrap();
    let run = fixture["run"].as_str().unwrap();
    let mut connection = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
    let readback = read_run_readonly(&mut connection, &schema, run).unwrap();
    let limits_doc = loads_strict(&fixture["limits"].to_string()).unwrap();
    let limits = MaterializedRunLimits::from_document(&limits_doc).unwrap();
    for (name, value) in readback
        .contract
        .field("budget")
        .unwrap()
        .object_entries()
        .unwrap()
    {
        assert_eq!(
            limits_doc.field(name).unwrap().canonical_bytes(),
            value.canonical_bytes()
        );
    }
    let cases = fixture["cases"].as_array().unwrap();
    assert_eq!(cases.len(), 2);
    for (i, case) in cases.iter().enumerate() {
        let raw = case["state"].as_str().unwrap();
        let state_digest = case["state_digest"].as_str().unwrap();
        let snapshot_digest = case["snapshot_digest"].as_str().unwrap();
        assert_eq!(digest_bytes(raw.as_bytes()), state_digest);
        let revision = case["revision"].as_i64().unwrap();
        let event = readback
            .events
            .iter()
            .rev()
            .find(|event| {
                event.run_revision <= revision
                    && matches!(
                        event.event_kind.as_str(),
                        "harness.snapshot-recorded" | "harness.run-paused"
                    )
            })
            .unwrap();
        let edges: Vec<_> = readback
            .verified_reference_links
            .iter()
            .filter(|r| r.event_id() == event.event_id)
            .collect();
        assert!(edges
            .iter()
            .any(|r| r.kind() == "harness-run-state" && r.digest() == state_digest));
        assert!(edges
            .iter()
            .any(|r| r.kind() == "harness-run-snapshot" && r.digest() == snapshot_digest));
        let state = loads_strict(raw).unwrap();
        assert_eq!(state.field("harnessRunId").unwrap().as_str(), Some(run));
        let remaining = state.get("remainingBudget").unwrap();
        let usage = state.field("providerUsage").unwrap();
        let elapsed = state
            .field("activeElapsedMs")
            .map(|n| n.integer_text().unwrap().parse().unwrap());
        let restored =
            restore_run_budget(&limits, &remaining, elapsed.as_ref(), usage, true).unwrap();
        let actual = &case["request_budget"];
        let fields = [
            ("modelCalls", "maxModelCalls", restored.model_calls),
            ("toolCalls", "maxToolCalls", restored.tool_calls),
            (
                "observationBytes",
                "maxObservationBytes",
                restored.observation_bytes,
            ),
            ("totalTokens", "maxTotalTokens", restored.total_tokens),
            ("modelRetries", "maxModelRetries", restored.model_retries),
            (
                "toolCorrections",
                "maxToolCorrections",
                restored.tool_corrections,
            ),
            (
                "conclusionCorrections",
                "maxConclusionCorrections",
                restored.conclusion_corrections,
            ),
            (
                "observationOnlyTurns",
                "maxObservationOnlyTurns",
                restored.observation_only_turns,
            ),
            (
                "noProgressTurns",
                "maxNoProgressTurns",
                restored.no_progress_turns,
            ),
        ];
        for (remaining, limit, spent) in fields {
            let spent = spent.to_string().parse::<u64>().unwrap();
            let bound = fixture["limits"][limit].as_u64().unwrap();
            assert_eq!(
                actual[remaining].as_u64().unwrap(),
                bound.saturating_sub(spent),
                "{remaining}"
            );
        }
        assert_eq!(
            actual["wallTimeMs"].as_u64().unwrap().to_string(),
            restored.remaining_wall_time_ms.to_string()
        );
        assert_eq!(restored.unknown_provider_usage_rows, 1);
        assert_eq!(restored.provider_attempts.to_string(), (i + 1).to_string());
    }
    assert_eq!(readback.projection.status, "completed");
    println!("NATIVE_RECOVERY matches two actual Python public Resume requests; historical state CAS edges verified");
}
