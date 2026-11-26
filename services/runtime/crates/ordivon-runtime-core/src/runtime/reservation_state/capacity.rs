//! One capacity slot: Active and HeldOrphaned are holders; Released never reopens.
use super::super::ReservationState;
use super::ReservationContract;

impl ReservationContract {
    pub(crate) fn initial_state() -> ReservationState {
        ReservationState::Active
    }

    #[cfg(any(test, feature = "operator-tools", kani))]
    pub(crate) fn holds_capacity(state: ReservationState) -> bool {
        matches!(
            state,
            ReservationState::Active | ReservationState::HeldOrphaned
        )
    }

    pub(crate) fn capacity_exhausted(active: u32, limit: u32) -> bool {
        active >= limit
    }

    #[cfg(any(test, feature = "operator-tools", kani))]
    pub(crate) fn can_transition(state: ReservationState, next: ReservationState) -> bool {
        match state {
            ReservationState::Active => {
                matches!(
                    next,
                    ReservationState::HeldOrphaned | ReservationState::Released
                )
            }
            ReservationState::HeldOrphaned => {
                matches!(
                    next,
                    ReservationState::HeldOrphaned | ReservationState::Released
                )
            }
            ReservationState::Released => next == ReservationState::Released,
        }
    }
}
