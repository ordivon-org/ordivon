//! Differential test against real Python AgentToolCall.from_dict, digest and
//! domain_tools._GrantedDomainToolBridge (no physical effect fake backend).
use std::{collections::HashSet, path::Path, process::Command};

use ordivon_harness_core::{loads_strict, CanonicalDocument};
use ordivon_harness_loop::tool_call::{
    inspect_model_tool_call, preflight_domain_model_call, ModelToolCallStanding,
};
use ordivon_harness_loop::tool_surface::project_domain_tool_surface;

fn unhex(input: &str) -> Vec<u8> {
    assert_eq!(input.len() % 2, 0);
    (0..input.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&input[i..i + 2], 16).unwrap())
        .collect()
}

fn document(input: &str) -> CanonicalDocument {
    let bytes = unhex(input);
    loads_strict(std::str::from_utf8(&bytes).expect("canonical UTF-8 source"))
        .expect("Python emitted valid integer-only canonical JSON")
}

#[test]
fn model_tool_call_python_source_parity_and_no_effect_preflight() {
    let harness = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    let oracle = Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/model_tool_call_oracle.py");
    let output = Command::new("uv")
        .args(["run", "--offline", "--locked", "python"])
        .arg(oracle)
        .current_dir(harness)
        .output()
        .expect("locked Harness Python source oracle installed");
    assert!(
        output.status.success(),
        "Python source oracle: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let stdout = String::from_utf8(output.stdout).unwrap();
    let mut lines = stdout.lines();
    let catalog_line = lines.next().expect("catalog fixture");
    let fields: Vec<&str> = catalog_line.split('\t').collect();
    let ["C", catalog_hex, catalog_digest, grant_digest] = fields.as_slice() else {
        panic!("unexpected domain catalog fixture: {catalog_line}");
    };
    let catalog = document(catalog_hex);
    let surface = project_domain_tool_surface(&catalog, &["edit", "read"]).unwrap();
    assert_eq!(surface.catalog_digest(), *catalog_digest);
    assert_eq!(surface.grant_digest(), *grant_digest);
    let mut count = 0;
    let mut valid_count = 0;
    let mut state_counts = [0_usize; 4];
    for line in lines {
        let fields: Vec<&str> = line.split('\t').collect();
        let ["T", valid, raw_hex, digest, call_id, name, posture, seen] = fields.as_slice() else {
            panic!("bad Python source oracle row: {line}");
        };
        let record = document(raw_hex);
        let inspected = inspect_model_tool_call(&record);
        if *valid == "1" {
            valid_count += 1;
            let call = inspected
                .unwrap_or_else(|err| panic!("Rust rejected valid Python call: {err:?}, {line}"));
            assert_eq!(call.digest(), *digest);
            assert_eq!(call.tool_call_id(), *call_id);
            assert_eq!(call.name(), *name);
            let mut history = HashSet::new();
            if *seen == "1" {
                history.insert(call.tool_call_id().to_owned());
            }
            let standing = preflight_domain_model_call(
                &surface,
                &catalog,
                catalog_digest,
                grant_digest,
                &call,
                &history,
            )
            .expect("frozen synthetic source valid");
            let expected = match *posture {
                "duplicate" => {
                    state_counts[0] += 1;
                    ModelToolCallStanding::DuplicateCallIdentity
                }
                "argument_error" => {
                    state_counts[1] += 1;
                    ModelToolCallStanding::LocallyRejectedProviderArguments
                }
                "not_visible" => {
                    state_counts[2] += 1;
                    ModelToolCallStanding::NotOnVisibleGrantedToolSurface
                }
                "needs_auth" => {
                    state_counts[3] += 1;
                    ModelToolCallStanding::NeedsAuthenticatedContractAndDurableAdmission
                }
                other => panic!("unrecognized Python tool call posture {other}"),
            };
            assert_eq!(standing, expected, "source boundary mismatch: {line}");
        } else {
            assert!(
                inspected.is_err(),
                "Rust accepted Python-invalid ToolCall: {line}"
            );
        }
        count += 1;
    }
    assert_eq!(count, 48 * 24);
    assert_eq!(valid_count, 336);
    assert!(
        state_counts.iter().all(|n| *n > 0),
        "missing a recovery/authority posture: {state_counts:?}"
    );
}
