//! Pure Rust migration probe for existing Python Harness turn decisions.
//! SourceCut: c2ab551a4c858d8a960a117eba66a0d9d9310a6a.
//! This is not a PG writer, Agent loop, Provider or Runtime dispatcher.

pub mod evidence;
pub mod provider_head;

use std::collections::HashSet;
use std::fmt;

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum ToolSelectionError {
    DuplicateSelectedNames,
    OutsideAdmittedSurface(Vec<String>),
}

impl fmt::Display for ToolSelectionError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::DuplicateSelectedNames => write!(f, "Turn Tool Working Set names must be unique"),
            Self::OutsideAdmittedSurface(names) => write!(
                f,
                "Turn Tool Working Set references Tools outside the admitted surface: {:?}",
                names
            ),
        }
    }
}
impl std::error::Error for ToolSelectionError {}

/// Mirror select_turn_tool_working_set from turn_projection.py.
/// Preserve admitted catalog order; never discover or authorize new Tools.
pub fn select_tool_indices(
    admitted_names: &[&str],
    selected_names: Option<&[&str]>,
) -> Result<Vec<usize>, ToolSelectionError> {
    let Some(names) = selected_names else {
        return Ok((0..admitted_names.len()).collect());
    };
    let selected: HashSet<&str> = names.iter().copied().collect();
    if selected.len() != names.len() {
        return Err(ToolSelectionError::DuplicateSelectedNames);
    }
    let available: HashSet<&str> = admitted_names.iter().copied().collect();
    let mut missing: Vec<String> = selected
        .difference(&available)
        .map(|name| (*name).to_string())
        .collect();
    if !missing.is_empty() {
        missing.sort();
        return Err(ToolSelectionError::OutsideAdmittedSurface(missing));
    }
    Ok(admitted_names
        .iter()
        .enumerate()
        .filter_map(|(i, name)| selected.contains(name).then_some(i))
        .collect())
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct ProgressCounters {
    pub no_progress_turns: u64,
    pub observation_only_turns: u64,
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct GateLimits {
    /// Zero disables the corresponding gate.
    pub max_no_progress_turns: u64,
    pub max_observation_only_turns: u64,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Gate {
    NoProgress { turns: u64 },
    ObservationOnly { turns: u64 },
}

impl Gate {
    pub fn reason(self) -> String {
        match self {
            Self::NoProgress { turns } => format!(
                "external observation gate closed after {turns} consecutive turns without a mutation, check, materially new bounded observation, or conclusion"
            ),
            Self::ObservationOnly { turns } => format!(
                "external observation gate closed after {turns} consecutive observation-only turns without a mutation, check, or conclusion"
            ),
        }
    }
}

/// Exact RunBudget.observation_gate_reason precedence, expressed as a pure rule.
pub fn observation_gate(counters: ProgressCounters, limits: GateLimits) -> Option<Gate> {
    if limits.max_no_progress_turns > 0
        && counters.no_progress_turns >= limits.max_no_progress_turns
    {
        Some(Gate::NoProgress {
            turns: counters.no_progress_turns,
        })
    } else if limits.max_observation_only_turns > 0
        && counters.observation_only_turns >= limits.max_observation_only_turns
    {
        Some(Gate::ObservationOnly {
            turns: counters.observation_only_turns,
        })
    } else {
        None
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ProgressError {
    CounterOverflow,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ProgressDecision {
    pub observation_only: bool,
    pub action_progress: bool,
    pub new_evidence: bool,
    pub counters: ProgressCounters,
    pub gate: Option<Gate>,
}

/// Mirrors Python progress/counter/gate semantics only.
/// Caller MUST provide just status==observed Tool names and an independently
/// verified new_evidence flag from the unchanged evidence identity scorer.
/// Unknown Tool outcomes do not magically become observed progress.
pub fn decide_progress(
    observed_names: &[&str],
    observation_only_names: &[&str],
    new_evidence: bool,
    prior: ProgressCounters,
    limits: GateLimits,
) -> Result<ProgressDecision, ProgressError> {
    let allowed: HashSet<&str> = observation_only_names.iter().copied().collect();
    let observed: HashSet<&str> = observed_names.iter().copied().collect();
    let observation_only =
        !observed.is_empty() && observed.iter().all(|name| allowed.contains(name));
    let action_progress = observed.iter().any(|name| !allowed.contains(name));

    let counters = ProgressCounters {
        observation_only_turns: if observation_only {
            prior
                .observation_only_turns
                .checked_add(1)
                .ok_or(ProgressError::CounterOverflow)?
        } else {
            0
        },
        no_progress_turns: if action_progress || new_evidence {
            0
        } else {
            prior
                .no_progress_turns
                .checked_add(1)
                .ok_or(ProgressError::CounterOverflow)?
        },
    };
    let gate = observation_gate(counters, limits);
    Ok(ProgressDecision {
        observation_only,
        action_progress,
        new_evidence,
        counters,
        gate,
    })
}

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
