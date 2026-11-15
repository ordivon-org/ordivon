//! Source-bound Python -> Rust Work differential corpus.
//! No PostgreSQL connection: real CAS/replay/installed-MCP checks are separate.
//! Generated from Python Host Pydantic + RFC8785 at the frozen SourceCut.
use ordivon_host_rust::work::{canonical_digest, WorkSnapshot};
use serde_json::{json, Value};

fn source_oracle() -> Value {
    serde_json::from_str(include_str!("../../tests/rust_work_parity_r1.json"))
        .expect("valid frozen Python oracle")
}

#[test]
fn rust_work_snapshot_bytes_and_request_identities_match_python() {
    let oracle = source_oracle();
    assert_eq!(oracle["kind"], "ordivon.host-rust-work-parity");
    assert_eq!(oracle["postgresqlEffectsProven"], false);
    for case in oracle["validSnapshots"].as_array().expect("snapshot cases") {
        let id = case["id"].as_str().expect("case id");
        let snapshot: WorkSnapshot = serde_json::from_value(case["input"].clone())
            .unwrap_or_else(|error| panic!("{id}: Rust rejected Python-valid input: {error}"));
        snapshot
            .validate()
            .unwrap_or_else(|error| panic!("{id}: Rust validation rejected Python: {error}"));
        let payload = serde_json::to_value(&snapshot).expect("Rust snapshot serialization");
        assert_eq!(payload, case["canonicalPayload"], "{id}: aliases/defaults");
        let bytes = serde_json_canonicalizer::to_vec(&payload).expect("Rust RFC8785");
        assert_eq!(
            hex::encode(bytes),
            case["canonicalUtf8Hex"].as_str().expect("hex"),
            "{id}: RFC8785 UTF-8 bytes"
        );
        assert_eq!(
            canonical_digest(&payload).expect("snapshot digest"),
            case["snapshotDigest"],
            "{id}: snapshot SHA256"
        );

        let work_ref = case["workRef"].as_str().unwrap();
        let actor_ref = case["actorRef"].as_str().unwrap();
        let state = case["state"].as_str().unwrap();
        let revision = case["expectedRevision"].as_i64().unwrap();
        let request = json!({
            "operation": "work.snapshot.commit",
            "workRef": work_ref,
            "expectedRevision": revision,
            "snapshot": payload,
            "actorRef": actor_ref,
            "state": state,
        });
        assert_eq!(
            canonical_digest(&request).expect("store request digest"),
            case["storeRequestDigest"],
            "{id}: PostgreSQL command receipt identity"
        );
        let create = json!({
            "operation": "work.create",
            "workRef": work_ref,
            "kind": case["workKind"],
            "actorRef": actor_ref,
            "initialSnapshot": payload,
        });
        assert_eq!(
            canonical_digest(&create).expect("create digest"),
            case["storeCreateDigest"],
            "{id}: Work.create receipt identity"
        );

        let disposition = match state {
            "open" => "continue",
            "completed" => "complete",
            "abandoned" => "abandon",
            _ => panic!("{id}: unknown state"),
        };
        let mcp_request = json!({
            "workRef": work_ref,
            "expectedRevision": revision,
            "snapshot": payload,
            "actorRef": actor_ref,
            "continuityDisposition": disposition,
        });
        let digest = canonical_digest(&mcp_request).expect("MCP id digest");
        assert_eq!(digest, case["mcpRequestDigest"], "{id}: MCP digest");
        assert_eq!(
            format!(
                "work-snapshot-commit:{}",
                digest.strip_prefix("sha256:").expect("prefix")
            ),
            case["mcpClientRequestId"],
            "{id}: source-derived clientRequestId"
        );
    }
}

#[test]
fn rust_rejects_inputs_python_host_rejects() {
    let oracle = source_oracle();
    for case in oracle["invalidSnapshots"]
        .as_array()
        .expect("invalid cases")
    {
        let id = case["id"].as_str().expect("id");
        if let Ok(snapshot) = serde_json::from_value::<WorkSnapshot>(case["input"].clone()) {
            assert!(
                snapshot.validate().is_err(),
                "{id}: Rust silently accepted Python-invalid input"
            );
        }
    }
}

#[test]
fn python_strip_boundary_does_not_overreject_embedded_control() {
    let oracle = source_oracle();
    let internal = oracle["validSnapshots"]
        .as_array()
        .unwrap()
        .iter()
        .find(|case| case["id"] == "embedded_python_only_whitespace")
        .expect("internal U+001C oracle");
    let snapshot: WorkSnapshot = serde_json::from_value(internal["input"].clone()).unwrap();
    assert!(snapshot.validate().is_ok());
    let rejected = oracle["invalidSnapshots"]
        .as_array()
        .unwrap()
        .iter()
        .filter(|case| {
            case["id"]
                .as_str()
                .unwrap_or("")
                .starts_with("python_only_strip_U+")
        })
        .count();
    assert_eq!(
        rejected, 4,
        "complete Python-only edge whitespace counterexamples"
    );
}
