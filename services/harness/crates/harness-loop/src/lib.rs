//! Native Harness execution decision kernel.
//! Tool selection and progress accounting have independent state and tests.

pub mod evidence;
mod identity;
pub mod native_loop;
pub mod native_provider_http;
pub mod owner_effect_handoff;
pub mod pg_domain_read;
pub mod pg_tool_head;
pub mod provider_head;
pub mod runtime_delivery;
pub mod tool_call;
pub mod tool_surface;

mod progress;
mod tool_selection;

pub use progress::{
    decide_progress, observation_gate, Gate, GateLimits, ProgressCounters, ProgressDecision,
    ProgressError,
};
pub use tool_selection::{select_tool_indices, ToolSelectionError};

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn overflow_is_an_explicit_error_not_silent_saturation() {
        let decision = decide_progress(
            &[],
            &[],
            false,
            ProgressCounters {
                no_progress_turns: u64::MAX,
                observation_only_turns: 0,
            },
            GateLimits::default(),
        );
        assert_eq!(decision, Err(ProgressError::CounterOverflow));
    }

    #[test]
    fn all_tools_when_no_selection() {
        assert_eq!(select_tool_indices(&["a", "b"], None), Ok(vec![0, 1]));
    }
    #[test]
    fn explicitly_empty_selection() {
        assert_eq!(select_tool_indices(&["a"], Some(&[])), Ok(vec![]));
    }
    #[test]
    fn selected_tools_preserve_admitted_order() {
        assert_eq!(
            select_tool_indices(&["a", "b", "c"], Some(&["c", "a"])),
            Ok(vec![0, 2])
        );
    }
    #[test]
    fn repeated_selected_tool_is_rejected() {
        assert_eq!(
            select_tool_indices(&["read"], Some(&["read", "read"])),
            Err(ToolSelectionError::DuplicateSelectedNames)
        );
    }
    #[test]
    fn missing_tools_are_sorted_and_rejected() {
        assert_eq!(
            select_tool_indices(&["read"], Some(&["z", "write"])),
            Err(ToolSelectionError::OutsideAdmittedSurface(vec![
                "write".into(),
                "z".into()
            ]))
        );
    }
    #[test]
    fn unicode_tool_name_is_exact() {
        assert_eq!(
            select_tool_indices(&["读取", "write"], Some(&["读取"])),
            Ok(vec![0])
        );
    }
    #[test]
    fn repeated_observation_increments_both_counters() {
        let p = decide_progress(
            &["read_workspace"],
            &["read_workspace"],
            false,
            ProgressCounters {
                no_progress_turns: 1,
                observation_only_turns: 2,
            },
            GateLimits {
                max_no_progress_turns: 3,
                max_observation_only_turns: 6,
            },
        )
        .expect("bounded counters");
        assert_eq!(
            p.counters,
            ProgressCounters {
                no_progress_turns: 2,
                observation_only_turns: 3
            }
        );
        assert_eq!(p.gate, None);
    }
    #[test]
    fn new_evidence_resets_no_progress_but_not_observation_only() {
        let p = decide_progress(
            &["read_workspace"],
            &["read_workspace"],
            true,
            ProgressCounters {
                no_progress_turns: 2,
                observation_only_turns: 1,
            },
            GateLimits {
                max_no_progress_turns: 3,
                max_observation_only_turns: 6,
            },
        )
        .expect("bounded counters");
        assert_eq!(
            p.counters,
            ProgressCounters {
                no_progress_turns: 0,
                observation_only_turns: 2
            }
        );
        assert!(!p.action_progress);
    }
    #[test]
    fn mutation_resets_both_counters() {
        let p = decide_progress(
            &["read_workspace", "edit_workspace"],
            &["read_workspace"],
            false,
            ProgressCounters {
                no_progress_turns: 2,
                observation_only_turns: 5,
            },
            GateLimits {
                max_no_progress_turns: 3,
                max_observation_only_turns: 6,
            },
        )
        .expect("bounded counters");
        assert_eq!(p.counters, ProgressCounters::default());
        assert!(p.action_progress);
    }
    #[test]
    fn unknown_outcome_must_not_count_as_observed_progress() {
        let p = decide_progress(
            &[],
            &["read_workspace"],
            false,
            ProgressCounters {
                no_progress_turns: 2,
                observation_only_turns: 1,
            },
            GateLimits {
                max_no_progress_turns: 3,
                max_observation_only_turns: 6,
            },
        )
        .expect("bounded counters");
        assert_eq!(p.gate, Some(Gate::NoProgress { turns: 3 }));
        assert!(!p.action_progress);
    }
    #[test]
    fn no_progress_has_precedence_if_both_gates_reached() {
        let p = decide_progress(
            &["read_workspace"],
            &["read_workspace"],
            false,
            ProgressCounters {
                no_progress_turns: 2,
                observation_only_turns: 5,
            },
            GateLimits {
                max_no_progress_turns: 3,
                max_observation_only_turns: 6,
            },
        )
        .expect("bounded counters");
        assert_eq!(p.gate, Some(Gate::NoProgress { turns: 3 }));
        assert_eq!(p.gate.unwrap().reason(),
            "external observation gate closed after 3 consecutive turns without a mutation, check, materially new bounded observation, or conclusion");
    }
    #[test]
    fn zero_thresholds_disable_gates() {
        let p = decide_progress(
            &[],
            &[],
            false,
            ProgressCounters {
                no_progress_turns: 999,
                observation_only_turns: 0,
            },
            GateLimits::default(),
        )
        .expect("bounded counters");
        assert_eq!(p.gate, None);
    }
    #[test]
    fn observation_only_reason_preserves_python_wording() {
        let p = decide_progress(
            &["read"],
            &["read"],
            true,
            ProgressCounters {
                no_progress_turns: 0,
                observation_only_turns: 5,
            },
            GateLimits {
                max_no_progress_turns: 3,
                max_observation_only_turns: 6,
            },
        )
        .expect("bounded counters");
        assert_eq!(p.gate.unwrap().reason(),
            "external observation gate closed after 6 consecutive observation-only turns without a mutation, check, or conclusion");
    }
}
