use ordivon_harness_core::{
    canonical_bytes, digest_bytes, loads_strict,
    run_budget::{restore_run_budget, MaterializedRunLimits},
    CanonicalDocument, CanonicalRef,
};
use ordivon_harness_pg::{read_run_readonly, Readback};
use postgres::{Client, NoTls};

fn text<'a>(doc: CanonicalRef<'a>, key: &str) -> &'a str {
    doc.field(key).unwrap().as_str().unwrap()
}

fn document(value: CanonicalRef<'_>) -> CanonicalDocument {
    loads_strict(std::str::from_utf8(&value.canonical_bytes()).unwrap()).unwrap()
}

fn bound_current_state<'a>(read: &Readback, fixture: CanonicalRef<'a>) -> Option<CanonicalRef<'a>> {
    let state = fixture.field("state")?;
    let revision = fixture
        .field("revision")?
        .integer_text()?
        .parse::<i64>()
        .ok()?;
    let head = read.events.last()?;
    let event = read.events.iter().rev().find(|e| {
        e.payload
            .field("data")
            .and_then(|d| d.field("snapshotObjectDigest"))
            .is_some()
    })?;
    let data = event.payload.field("data")?;
    let state_digest = fixture.field("stateDigest")?.as_str()?;
    let snapshot_digest = fixture.field("snapshotDigest")?.as_str()?;
    if read.projection.status != "paused"
        || read.projection.revision != revision
        || head.run_revision != revision
        || fixture.field("eventId")?.as_str()? != event.event_id
        || data.field("stateObjectDigest")?.as_str()? != state_digest
        || data.field("snapshotObjectDigest")?.as_str()? != snapshot_digest
        || state.field("harnessRunId")?.as_str()? != read.projection.harness_run_id
        || digest_bytes(&state.canonical_bytes()) != state_digest
        || !read.verified_reference_links.iter().any(|r| {
            r.event_id() == event.event_id
                && r.digest() == state_digest
                && r.kind() == "harness-run-state"
        })
        || !read.verified_reference_links.iter().any(|r| {
            r.event_id() == event.event_id
                && r.digest() == snapshot_digest
                && r.kind() == "harness-run-snapshot"
        })
    {
        return None;
    }
    Some(state)
}

#[test]
#[ignore = "requires the existing disposable PG18 fixture and original Python state owner"]
fn cold_paused_budget_uses_exact_current_state_and_observed_usage() {
    let path = std::env::var("HARNESS_RUST_TEST_BUDGET_FIXTURE").unwrap();
    let fixture = loads_strict(&std::fs::read_to_string(path).unwrap()).unwrap();
    let root = fixture.as_borrowed();
    let mut connection =
        Client::connect(&std::env::var("HARNESS_RUST_TEST_PG_DSN").unwrap(), NoTls).unwrap();
    let read = read_run_readonly(
        &mut connection,
        &std::env::var("HARNESS_RUST_TEST_SCHEMA").unwrap(),
        text(root, "runId"),
    )
    .unwrap();
    assert_eq!(
        read.projection.contract_digest,
        text(root, "contractDigest")
    );
    let limits_doc = document(root.field("limits").unwrap());
    let claimed = read.contract.field("budget").unwrap();
    for (name, bound) in claimed.object_entries().unwrap() {
        assert_eq!(
            limits_doc.field(name).unwrap().canonical_bytes(),
            bound.canonical_bytes()
        );
    }
    assert!(bound_current_state(&read, root.field("earlier").unwrap()).is_none());
    let current = root.field("current").unwrap();
    let state = bound_current_state(&read, current).expect("exact current state");
    let state_doc = document(state);
    assert_eq!(
        digest_bytes(&canonical_bytes(&state_doc)),
        text(current, "stateDigest")
    );
    let limits = MaterializedRunLimits::from_document(&limits_doc).unwrap();
    let remaining = document(state.field("remainingBudget").unwrap());
    let elapsed = state
        .field("activeElapsedMs")
        .and_then(|v| v.integer_text())
        .map(|v| v.parse().unwrap());
    let usage = root.field("observedUsage").unwrap();
    for reset in [false, true] {
        let recovered = restore_run_budget(
            &limits,
            &remaining,
            elapsed.as_ref(),
            state.field("providerUsage").unwrap(),
            reset,
        )
        .unwrap();
        assert_eq!(
            recovered.model_calls.to_string(),
            usage.field("modelCalls").unwrap().integer_text().unwrap()
        );
        assert_eq!(
            recovered.total_tokens.to_string(),
            usage.field("totalTokens").unwrap().integer_text().unwrap()
        );
        assert_eq!(
            recovered.unknown_provider_usage_rows.to_string(),
            usage
                .field("tokenCounterCoverage")
                .unwrap()
                .field("uncountableCalls")
                .unwrap()
                .integer_text()
                .unwrap()
        );
        assert_eq!(recovered.provider_attempts.to_string(), "3");
        assert_eq!(recovered.tool_calls.to_string(), "0");
        assert_eq!(recovered.prior_elapsed_ms.to_string(), "0");
        assert_eq!(recovered.remaining_wall_time_ms.to_string(), "10000");
        assert_eq!(
            state.field("seenModelCallIds").unwrap().array_len(),
            Some(3)
        );
    }
    println!("PG18_PUBLIC_PAUSED_OWNER_STATE_NATIVE_BUDGET_PASS");
}
