//! Pure state transition for current Python run_recovery._advance_turn_evidence.
//! Input digests and search units are supplied by an authenticated projection;
//! parsing and hashing of Provider/Tool contents belong to the canonical core.
//! This code performs no external effects or PostgreSQL writes.

use std::collections::{HashMap, HashSet};

use crate::{
    classify_observed_names, decide_progress_from_flags, GateLimits, ProgressCounters,
    ProgressDecision, ProgressError,
};

#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub struct EvidenceState {
    pub signatures: HashSet<String>,
    pub search: HashMap<(String, String), HashSet<String>>,
}

#[derive(Clone, Debug)]
pub struct SearchUnit<'a> {
    pub query: &'a str,
    pub relative_path: &'a str,
    pub matches: Vec<&'a str>,
}

#[derive(Clone, Debug)]
pub struct Observation<'a> {
    pub tool_name: &'a str,
    pub status: &'a str,
    pub evidence_signature: &'a str,
    /// Some implies an actual matching search Tool call. Search evidence
    /// identities (including exit outcome) come from the canonical projection.
    pub search_units: Option<Vec<SearchUnit<'a>>>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct EvidenceTransition {
    pub observation_only: bool,
    pub action_progress: bool,
    pub new_evidence: bool,
    pub state: EvidenceState,
}

/// Exact Python _path_subsumes semantics, including trailing-slash trimming.
/// This is a lexical relation, NOT filesystem path resolution.
pub fn path_subsumes(parent: &str, child: &str) -> bool {
    let parent = parent.trim_end_matches('/');
    let child = child.trim_end_matches('/');
    parent.is_empty()
        || parent == "."
        || parent == child
        || child
            .strip_prefix(parent)
            .is_some_and(|suffix| suffix.starts_with('/'))
}

/// Semantically equivalent to Python _advance_turn_evidence for inputs whose
/// exact signatures and _search_evidence units have already been projected.
/// UNKNOWN/rejected/cancelled Tool outcomes are ignored, never counted as
/// positive observation or an effect. Prior EvidenceState is never mutated.
pub fn advance_evidence(
    prior: &EvidenceState,
    observations: &[Observation<'_>],
    observation_only_names: &[&str],
) -> EvidenceTransition {
    let mut state = prior.clone();
    let (observation_only, action_progress) = classify_observed_names(
        observations
            .iter()
            .filter(|observation| observation.status == "observed")
            .map(|observation| observation.tool_name),
        observation_only_names,
    );
    let mut new_evidence = false;

    for observation in observations {
        if observation.status != "observed" {
            continue;
        }
        if observation.tool_name == "search_workspace" {
            if let Some(units) = &observation.search_units {
                for unit in units {
                    let next_matches: HashSet<String> = unit
                        .matches
                        .iter()
                        .map(|token| (*token).to_owned())
                        .collect();
                    if !state.search.iter().any(|((query, path), existing)| {
                        query == unit.query
                            && path_subsumes(path, unit.relative_path)
                            && next_matches.is_subset(existing)
                    }) {
                        new_evidence = true;
                    }
                    state
                        .search
                        .entry((unit.query.to_owned(), unit.relative_path.to_owned()))
                        .or_default()
                        .extend(next_matches);
                }
                continue;
            }
        }
        if state
            .signatures
            .insert(observation.evidence_signature.to_owned())
        {
            new_evidence = true;
        }
    }
    EvidenceTransition {
        observation_only,
        action_progress,
        new_evidence,
        state,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn observed<'a>(tool: &'a str, signature: &'a str) -> Observation<'a> {
        Observation {
            tool_name: tool,
            status: "observed",
            evidence_signature: signature,
            search_units: None,
        }
    }

    #[test]
    fn lexical_path_subsumption_is_boundary_aware() {
        assert!(path_subsumes(".", "src/a"));
        assert!(path_subsumes("src/", "src/a"));
        assert!(path_subsumes("src", "src"));
        assert!(!path_subsumes("src", "src2/a"));
        assert!(!path_subsumes("src/a", "src"));
    }

    #[test]
    fn unknown_cannot_manufacture_evidence_or_progress() {
        let input = Observation {
            status: "unknown",
            ..observed("edit_workspace", "digest")
        };
        let transition = advance_evidence(&EvidenceState::default(), &[input], &[]);
        assert!(!transition.new_evidence);
        assert!(!transition.action_progress);
        assert!(!transition.observation_only);
        assert_eq!(transition.state, EvidenceState::default());
    }

    #[test]
    fn repeated_observation_does_not_change_prior() {
        let first = advance_evidence(
            &EvidenceState::default(),
            &[observed("read_workspace", "same")],
            &["read_workspace"],
        );
        let second = advance_evidence(
            &first.state,
            &[observed("read_workspace", "same")],
            &["read_workspace"],
        );
        assert!(first.new_evidence);
        assert!(!second.new_evidence);
        assert_eq!(first.state, second.state);
    }

    #[test]
    fn narrow_search_subset_is_not_new_evidence() {
        let broad = Observation {
            search_units: Some(vec![SearchUnit {
                query: "lease",
                relative_path: "src",
                matches: vec!["hit-1", "outcome-success"],
            }]),
            ..observed("search_workspace", "ignored")
        };
        let first = advance_evidence(&EvidenceState::default(), &[broad], &["search_workspace"]);
        let child = Observation {
            search_units: Some(vec![SearchUnit {
                query: "lease",
                relative_path: "src/a",
                matches: vec!["hit-1", "outcome-success"],
            }]),
            ..observed("search_workspace", "ignored-2")
        };
        let second = advance_evidence(&first.state, &[child], &["search_workspace"]);
        assert!(!second.new_evidence);
        assert_eq!(second.state.search.len(), 2);
        assert_eq!(first.state.search.len(), 1);
    }

    #[test]
    fn dominated_child_search_state_cannot_be_deleted_in_general() {
        let step = |prior: &EvidenceState, path: &str, matches: Vec<&str>| {
            advance_evidence(
                prior,
                &[Observation {
                    search_units: Some(vec![SearchUnit {
                        query: "q",
                        relative_path: path,
                        matches,
                    }]),
                    ..observed("search_workspace", "ignored")
                }],
                &["search_workspace"],
            )
        };
        let parent = step(&EvidenceState::default(), "src", vec!["a"]);
        let child = step(&parent.state, "src/a", vec!["a"]);
        assert!(!child.new_evidence);
        let mut pruned = child.state.clone();
        pruned.search.remove(&("q".into(), "src/a".into()));
        let retained_next = step(&child.state, "src/a", vec!["b"]);
        let pruned_next = step(&pruned, "src/a", vec!["b"]);
        assert!(retained_next.new_evidence && pruned_next.new_evidence);
        assert!(!step(&retained_next.state, "src/a", vec!["a", "b"]).new_evidence);
        assert!(step(&pruned_next.state, "src/a", vec!["a", "b"]).new_evidence);
    }

    #[test]
    fn same_matches_with_different_exit_outcome_are_new() {
        let first = advance_evidence(
            &EvidenceState::default(),
            &[Observation {
                search_units: Some(vec![SearchUnit {
                    query: "x",
                    relative_path: ".",
                    matches: vec!["same-hit", "exit-zero"],
                }]),
                ..observed("search_workspace", "one")
            }],
            &["search_workspace"],
        );
        let second = advance_evidence(
            &first.state,
            &[Observation {
                search_units: Some(vec![SearchUnit {
                    query: "x",
                    relative_path: ".",
                    matches: vec!["same-hit", "exit-two"],
                }]),
                ..observed("search_workspace", "two")
            }],
            &["search_workspace"],
        );
        assert!(second.new_evidence);
    }
}

/// One pure turn transition from prior evidence and counters to an actionable
/// progress gate. The effective Tool effects themselves are NOT decided here.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TurnDecision {
    pub evidence: EvidenceTransition,
    pub progress: ProgressDecision,
}

pub fn evaluate_turn(
    prior: &EvidenceState,
    observations: &[Observation<'_>],
    observation_only_names: &[&str],
    counters: ProgressCounters,
    limits: GateLimits,
) -> Result<TurnDecision, ProgressError> {
    let evidence = advance_evidence(prior, observations, observation_only_names);
    let progress = decide_progress_from_flags(
        evidence.observation_only,
        evidence.action_progress,
        evidence.new_evidence,
        counters,
        limits,
    )?;
    Ok(TurnDecision { evidence, progress })
}
