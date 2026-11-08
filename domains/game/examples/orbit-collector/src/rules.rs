//! Product-owned rules, independent of the engine, renderer and input API.
//! The native Bevy ECS stores this state as a Resource in the consumer.

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Phase {
    Playing,
    Won,
    Lost,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RunState {
    // Private representation invariant: callers may observe but cannot forge
    // unreachable states, underflow lives or over-collect past the target.
    phase: Phase,
    collected: usize,
    target: usize,
    lives: u8,
}

impl RunState {
    pub fn new(target: usize, lives: u8) -> Self {
        assert!(
            target > 0 && lives > 0,
            "a playable recipe needs goals and lives"
        );
        Self {
            phase: Phase::Playing,
            collected: 0,
            target,
            lives,
        }
    }

    pub fn phase(&self) -> Phase {
        self.phase
    }

    pub fn collected(&self) -> usize {
        self.collected
    }

    pub fn target(&self) -> usize {
        self.target
    }

    pub fn lives(&self) -> u8 {
        self.lives
    }

    // Executable abstraction predicate for formal one-step induction.
    // Does not assert the engine ECS or renderer satisfies this predicate.
    pub fn invariant(&self) -> bool {
        if self.target == 0 || self.collected > self.target {
            return false;
        }
        match self.phase {
            Phase::Playing => self.collected < self.target && self.lives > 0,
            Phase::Won => self.collected == self.target && self.lives > 0,
            Phase::Lost => self.collected < self.target && self.lives == 0,
        }
    }

    pub fn collect(&mut self) {
        if self.phase != Phase::Playing {
            return;
        }
        debug_assert!(self.invariant());
        // The private Playing invariant implies collected < target <= usize::MAX,
        // so increment is not an overflow even for a maximum-sized goal.
        self.collected += 1;
        if self.collected == self.target {
            self.phase = Phase::Won;
        }
        debug_assert!(self.invariant());
    }

    pub fn take_hit(&mut self) {
        if self.phase != Phase::Playing {
            return;
        }
        debug_assert!(self.invariant());
        // The Playing invariant implies a positive u8 lives counter.
        self.lives -= 1;
        if self.lives == 0 {
            self.phase = Phase::Lost;
        }
        debug_assert!(self.invariant());
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // Native restart consumer stays: Kani proves the actual collect/hit source
    // for any constructible state. Their redundant single-example checks were
    // retired only after four successful source-level Kani harnesses.
    #[test]
    fn restart_creates_independent_clean_state() {
        let mut old = RunState::new(5, 3);
        old.collect();
        old.take_hit();
        let new = RunState::new(5, 3);
        assert_eq!(new.collected, 0);
        assert_eq!(new.lives, 3);
        assert_eq!(new.phase, Phase::Playing);
        assert_ne!(old, new);
    }
}

// Kani bit-precise one-step induction on the actual Rust implementation.
// These harnesses do not execute in normal cargo tests and are not accepted
// as proved unless the pinned Kani runner really discharges each obligation.
#[cfg(kani)]
mod kani_proofs {
    use super::*;

    #[kani::proof]
    fn constructor_preserves_invariant() {
        let target: usize = kani::any();
        let lives: u8 = kani::any();
        kani::assume(target > 0 && lives > 0);
        let run = RunState::new(target, lives);
        assert!(run.invariant());
    }

    #[kani::proof]
    fn collect_preserves_invariant_and_bounds() {
        let target: usize = kani::any();
        let collected: usize = kani::any();
        let lives: u8 = kani::any();
        kani::assume(target > 0 && lives > 0 && collected < target);
        let mut run = RunState {
            phase: Phase::Playing,
            collected,
            target,
            lives,
        };
        run.collect();
        assert!(run.invariant());
        assert!(run.collected() <= target);
        assert_eq!(run.phase() == Phase::Won, collected == target - 1);
    }

    #[kani::proof]
    fn hit_preserves_invariant_and_prevents_underflow() {
        let target: usize = kani::any();
        let collected: usize = kani::any();
        let lives: u8 = kani::any();
        kani::assume(target > 0 && lives > 0 && collected < target);
        let mut run = RunState {
            phase: Phase::Playing,
            collected,
            target,
            lives,
        };
        run.take_hit();
        assert!(run.invariant());
        assert_eq!(run.phase() == Phase::Lost, lives == 1);
    }

    #[kani::proof]
    fn terminal_state_is_absorbing() {
        let target: usize = kani::any();
        let collected: usize = kani::any();
        let lives: u8 = kani::any();
        let won: bool = kani::any();
        kani::assume(target > 0 && collected <= target);
        kani::assume(if won {
            collected == target && lives > 0
        } else {
            collected < target && lives == 0
        });
        let mut run = RunState {
            phase: if won { Phase::Won } else { Phase::Lost },
            collected,
            target,
            lives,
        };
        let original = run.clone();
        run.collect();
        run.take_hit();
        assert_eq!(run, original);
        assert!(run.invariant());
    }
}
