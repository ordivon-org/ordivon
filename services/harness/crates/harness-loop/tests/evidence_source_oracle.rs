//! Differential test: Python production scorer owns the oracle result.
//! Rust consumes identity-bearing evidence units; this test does not establish
//! byte parity of the independent canonical codec or PG/Provider correctness.

use ordivon_harness_loop::evidence::{evaluate_turn, EvidenceState, Observation, SearchUnit};
use ordivon_harness_loop::{Gate, GateLimits, ProgressCounters};
use std::collections::HashMap;
use std::path::Path;
use std::process::Command;

#[test]
fn python_source_evidence_640_stateful_transitions() {
    let harness = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    let src = harness.join("src");
    let oracle = Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/evidence_oracle.py");
    let previous = std::env::var("PYTHONPATH").unwrap_or_default();
    let pythonpath = if previous.is_empty() {
        src.display().to_string()
    } else {
        format!("{}:{}", src.display(), previous)
    };
    let output = Command::new(std::env::var("HARNESS_PYTHON").unwrap_or_else(|_| "python3".into()))
        .arg(oracle)
        .env("PYTHONPATH", pythonpath)
        .output()
        .expect("Python with current Harness source is required");
    assert!(
        output.status.success(),
        "Python oracle failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let data = String::from_utf8(output.stdout).expect("UTF-8 oracle expected");
    let mut state_by_scenario: HashMap<usize, EvidenceState> = HashMap::new();
    let mut checked = 0;
    for line in data.lines() {
        let fields: Vec<&str> = line.split('\t').collect();
        let ["E", scenario, tool, status, signature, encoded, expected_only, expected_action, expected_new, expected_signatures, expected_keys, expected_members, prior_n, prior_o, max_n, max_o, next_n, next_o, expected_gate] =
            fields.as_slice()
        else {
            panic!("malformed oracle vector: {line}");
        };
        let scenario: usize = scenario.parse().unwrap();
        let search_units = if *encoded == "*" {
            None
        } else {
            Some(
                encoded
                    .split('|')
                    .map(|unit| {
                        let parts: Vec<&str> = unit.split('~').collect();
                        assert_eq!(parts.len(), 3, "bad unit {unit}");
                        SearchUnit {
                            query: parts[0],
                            relative_path: parts[1],
                            matches: if parts[2].is_empty() {
                                Vec::new()
                            } else {
                                parts[2].split(',').collect()
                            },
                        }
                    })
                    .collect::<Vec<_>>(),
            )
        };
        let input = Observation {
            tool_name: tool,
            status,
            evidence_signature: signature,
            search_units,
        };
        let prior = state_by_scenario.entry(scenario).or_default();
        let result = evaluate_turn(
            prior,
            &[input],
            &["search_workspace", "read_workspace", "read_artifact"],
            ProgressCounters {
                no_progress_turns: prior_n.parse().unwrap(),
                observation_only_turns: prior_o.parse().unwrap(),
            },
            GateLimits {
                max_no_progress_turns: max_n.parse().unwrap(),
                max_observation_only_turns: max_o.parse().unwrap(),
            },
        )
        .expect("Python corpus counters are bounded");
        let transition = &result.evidence;
        assert_eq!(
            transition.observation_only,
            *expected_only == "1",
            "only: {line}"
        );
        assert_eq!(
            transition.action_progress,
            *expected_action == "1",
            "action: {line}"
        );
        assert_eq!(transition.new_evidence, *expected_new == "1", "new: {line}");
        assert_eq!(
            transition.state.signatures.len(),
            expected_signatures.parse::<usize>().unwrap(),
            "signatures: {line}"
        );
        assert_eq!(
            transition.state.search.len(),
            expected_keys.parse::<usize>().unwrap(),
            "keys: {line}"
        );
        assert_eq!(
            transition
                .state
                .search
                .values()
                .map(std::collections::HashSet::len)
                .sum::<usize>(),
            expected_members.parse::<usize>().unwrap(),
            "members: {line}"
        );
        assert_eq!(
            result.progress.counters.no_progress_turns,
            next_n.parse::<u64>().unwrap(),
            "no-progress counter: {line}"
        );
        assert_eq!(
            result.progress.counters.observation_only_turns,
            next_o.parse::<u64>().unwrap(),
            "observation-only counter: {line}"
        );
        assert_eq!(
            result
                .progress
                .gate
                .map(Gate::reason)
                .unwrap_or_else(|| "none".into()),
            *expected_gate,
            "gate: {line}"
        );
        *prior = result.evidence.state;
        checked += 1;
    }
    assert_eq!(checked, 640);
}
