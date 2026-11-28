use super::super::super::{AttemptState, RuntimeError, RuntimeErrorCode, RuntimeResult};

/// Terminal-state-indexed source observation obligation. These states are
/// mutually exclusive; a pair of booleans admitted contradictory requests.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum SourceObservationRequirement {
    Unconstrained,
    MustMatch,
    MustDiffer,
}

impl SourceObservationRequirement {
    pub(crate) fn for_terminal(state: AttemptState, reason: &str) -> Self {
        if state == AttemptState::Succeeded {
            Self::MustMatch
        } else if reason == "WORKSPACE_SOURCE_PRECONDITION_DRIFT" {
            Self::MustDiffer
        } else {
            Self::Unconstrained
        }
    }
}

pub(super) fn validate_source_observation_relation(
    observed: Option<&str>,
    matches: Option<bool>,
    observation_error: Option<&str>,
    committed: &str,
    requirement: SourceObservationRequirement,
) -> RuntimeResult<()> {
    match (observed, matches, observation_error) {
        (Some(observed), Some(matches), None)
            if crate::runtime::types::is_sha256_digest(observed)
                && matches == (observed == committed) =>
        {
            if requirement == SourceObservationRequirement::MustDiffer && matches {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::ArtifactIdentityConflict,
                    "Workspace source drift result carried a matching source observation",
                    Some("workspaceSourceObservation"),
                    false,
                ));
            }
            if requirement == SourceObservationRequirement::MustMatch && !matches {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::ArtifactIdentityConflict,
                    "Successful process carried a mismatching Workspace source observation",
                    Some("workspaceSourceObservation"),
                    false,
                ));
            }
        }
        (None, None, Some(error_code))
            if !error_code.is_empty()
                && requirement == SourceObservationRequirement::Unconstrained => {}
        _ => {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ArtifactIdentityConflict,
                "Workspace source observation digest/error relation is invalid",
                Some("workspaceSourceObservation"),
                false,
            ));
        }
    }
    Ok(())
}
