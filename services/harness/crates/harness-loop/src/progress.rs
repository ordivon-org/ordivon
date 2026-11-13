use std::collections::HashSet;

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
