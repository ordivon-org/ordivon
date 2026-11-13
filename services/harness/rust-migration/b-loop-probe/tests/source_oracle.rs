//! Differential qualification: execute the existing Python source, not a copy.
use ordivon_harness_loop_b_probe::{
    observation_gate, select_tool_indices, Gate, GateLimits, ProgressCounters, ToolSelectionError,
};
use std::path::Path;
use std::process::Command;

#[test]
fn python_source_oracle_400_cases() {
    let harness = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    let src = harness.join("src");
    let oracle = Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/python_oracle.py");
    let original_path = std::env::var("PYTHONPATH").unwrap_or_default();
    let pythonpath = if original_path.is_empty() {
        src.display().to_string()
    } else {
        format!("{}:{}", src.display(), original_path)
    };
    let output = Command::new(std::env::var("HARNESS_PYTHON").unwrap_or_else(|_| "python".into()))
        .arg(oracle)
        .env("PYTHONPATH", pythonpath)
        .output()
        .expect("Python 3.15 with Harness source is REQUIRED for source-oracle qualification");
    assert!(
        output.status.success(),
        "Python oracle failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let data = String::from_utf8(output.stdout).expect("Python oracle output must be UTF-8");
    let mut checked = 0usize;
    for line in data.lines() {
        let fields: Vec<&str> = line.split('\t').collect();
        match fields.as_slice() {
            ["S", available, chosen, expected] => {
                let catalog = csv(available);
                let selected = if *chosen == "*" {
                    None
                } else {
                    Some(csv(chosen))
                };
                let actual = select_tool_indices(&catalog, selected.as_deref());
                let result = match actual {
                    Ok(indices) => format!(
                        "ok:{}",
                        indices
                            .iter()
                            .map(usize::to_string)
                            .collect::<Vec<_>>()
                            .join(",")
                    ),
                    Err(ToolSelectionError::DuplicateSelectedNames) => "error:duplicate".into(),
                    Err(ToolSelectionError::OutsideAdmittedSurface(missing)) => {
                        format!("error:missing:{}", missing.join(","))
                    }
                };
                assert_eq!(result, *expected, "Tool selection parity: {line}");
            }
            ["G", count_n, count_o, max_n, max_o, expected] => {
                let count_n: u64 = count_n.parse().unwrap();
                let count_o: u64 = count_o.parse().unwrap();
                let max_n: u64 = max_n.parse().unwrap();
                let max_o: u64 = max_o.parse().unwrap();
                let gate = observation_gate(
                    ProgressCounters {
                        no_progress_turns: count_n,
                        observation_only_turns: count_o,
                    },
                    GateLimits {
                        max_no_progress_turns: max_n,
                        max_observation_only_turns: max_o,
                    },
                );
                let reason = gate.map(Gate::reason).unwrap_or_else(|| "none".into());
                assert_eq!(reason, *expected, "Budget gate parity: {line}");
            }
            _ => panic!("unexpected Python oracle vector: {line}"),
        }
        checked += 1;
    }
    assert_eq!(checked, 400);
}

fn csv(raw: &str) -> Vec<&str> {
    if raw.is_empty() {
        Vec::new()
    } else {
        raw.split(',').collect()
    }
}
