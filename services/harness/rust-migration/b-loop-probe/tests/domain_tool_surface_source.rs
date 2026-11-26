//! Source parity: Python DomainToolCatalog/_select/_granted_digest, using
//! A's canonical bytes and B's existing selection logic without a new registry.
use ordivon_harness_core::{loads_strict, CanonicalDocument};
use ordivon_harness_loop_b_probe::tool_surface::{project_domain_tool_surface, ToolSurfaceError};
use std::path::Path;
use std::process::Command;

fn unhex(input: &str) -> Vec<u8> {
    assert_eq!(input.len() % 2, 0);
    (0..input.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&input[i..i + 2], 16).unwrap())
        .collect()
}

fn document(encoded: &str) -> CanonicalDocument {
    let raw = unhex(encoded);
    let text = std::str::from_utf8(&raw).unwrap();
    loads_strict(text).expect("Python supplied only valid canonical JSON values")
}

fn string_array(value: &CanonicalDocument) -> Vec<String> {
    let mut strings = Vec::new();
    let mut index = 0;
    while let Some(item) = value.index(index) {
        strings.push(item.as_str().expect("Tool name is a string").to_owned());
        index += 1;
    }
    strings
}

#[test]
fn python_domain_tool_catalog_grant_selection_and_digest_parity() {
    let harness = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    let oracle = Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/domain_tool_surface_oracle.py");
    let output = Command::new("uv")
        .args(["run", "--offline", "--locked", "python"])
        .arg(oracle)
        .current_dir(harness)
        .output()
        .expect("locked Python Harness source oracle must be installed");
    assert!(
        output.status.success(),
        "Python source oracle: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let stdout = String::from_utf8(output.stdout).expect("Oracle UTF-8");
    let mut all = 0;
    let mut allowed_count = 0;
    for line in stdout.lines() {
        let parts: Vec<&str> = line.split('\t').collect();
        let ["S", valid, catalog_hex, grant_hex, selected_hex, catalog_digest, grant_digest] =
            parts.as_slice()
        else {
            panic!("Unexpected source oracle row {line}");
        };
        let catalog = document(catalog_hex);
        let granted = document(grant_hex);
        let allowed = string_array(&granted);
        let allowed_refs: Vec<&str> = allowed.iter().map(String::as_str).collect();
        let observed = project_domain_tool_surface(&catalog, &allowed_refs);
        if *valid == "1" {
            let projection = observed.unwrap_or_else(|error| {
                panic!("Rust rejected a Python-valid Tool grant: {error:?}, {line}")
            });
            let selected = string_array(&document(selected_hex));
            assert_eq!(projection.ordered_names(), selected.as_slice());
            assert_eq!(projection.catalog_digest(), *catalog_digest);
            assert_eq!(projection.grant_digest(), *grant_digest);
            projection
                .require_contract_binding(catalog_digest, grant_digest)
                .unwrap();
            assert_eq!(
                projection.require_contract_binding(catalog_digest, "sha256:wrong"),
                Err(ToolSurfaceError::BindingMismatch)
            );
            let defs = projection.model_definitions(&catalog).unwrap();
            assert_eq!(defs.len(), selected.len());
            for (definition, expected) in defs.into_iter().zip(selected) {
                assert_eq!(
                    definition.field("name").and_then(|v| v.as_str()),
                    Some(expected.as_str())
                );
            }
            allowed_count += 1;
        } else {
            assert!(
                matches!(
                    observed,
                    Err(ToolSurfaceError::InvalidGrant | ToolSurfaceError::GrantSelection(_))
                ),
                "Rust admitted Python-invalid Tool grant: {line}"
            );
        }
        all += 1;
    }
    assert_eq!(all, 224);
    assert_eq!(allowed_count, 128);
}
