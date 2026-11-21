use super::contract::{validate_source_observation_relation, SourceObservationRequirement};
use crate::runtime::AttemptState;

const COMMITTED: &str = "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const DIFFERENT: &str = "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";

#[test]
fn successful_state_requires_match_even_with_new_terminal_reason() {
    assert_eq!(
        SourceObservationRequirement::for_terminal(
            AttemptState::Succeeded,
            "FUTURE_SUCCESS_REASON"
        ),
        SourceObservationRequirement::MustMatch
    );
    assert_eq!(
        SourceObservationRequirement::for_terminal(
            AttemptState::Succeeded,
            "PROCESS_COMPLETED_BEFORE_STOP_EFFECTIVE"
        ),
        SourceObservationRequirement::MustMatch
    );
    assert_eq!(
        SourceObservationRequirement::for_terminal(
            AttemptState::Failed,
            "WORKSPACE_SOURCE_PRECONDITION_DRIFT"
        ),
        SourceObservationRequirement::MustDiffer
    );
    assert_eq!(
        SourceObservationRequirement::for_terminal(AttemptState::TimedOut, "DEADLINE_EXCEEDED"),
        SourceObservationRequirement::Unconstrained
    );
}

#[test]
fn successful_process_must_not_carry_drifted_source_observation() {
    assert!(
        validate_source_observation_relation(
            Some(DIFFERENT),
            Some(false),
            None,
            COMMITTED,
            SourceObservationRequirement::MustMatch,
        )
        .is_err(),
        "a successful execution must not preserve a source-drift observation"
    );
}

#[test]
fn successful_process_must_not_carry_unresolved_source_observation() {
    assert!(
        validate_source_observation_relation(
            None,
            None,
            Some("UNKNOWN_SOURCE_OBSERVATION"),
            COMMITTED,
            SourceObservationRequirement::MustMatch,
        )
        .is_err(),
        "missing source observation cannot attest a successful process"
    );
}

#[test]
fn successful_process_accepts_committed_source_observation() {
    assert!(validate_source_observation_relation(
        Some(COMMITTED),
        Some(true),
        None,
        COMMITTED,
        SourceObservationRequirement::MustMatch,
    )
    .is_ok());
}

#[test]
fn source_precondition_drift_still_requires_a_real_mismatch() {
    assert!(validate_source_observation_relation(
        Some(DIFFERENT),
        Some(false),
        None,
        COMMITTED,
        SourceObservationRequirement::MustDiffer,
    )
    .is_ok());
    assert!(validate_source_observation_relation(
        Some(COMMITTED),
        Some(true),
        None,
        COMMITTED,
        SourceObservationRequirement::MustDiffer,
    )
    .is_err());
}
