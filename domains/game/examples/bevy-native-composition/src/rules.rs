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
    pub phase: Phase,
    pub collected: usize,
    pub target: usize,
    pub lives: u8,
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

    pub fn collect(&mut self) {
        if self.phase != Phase::Playing {
            return;
        }
        self.collected += 1;
        if self.collected == self.target {
            self.phase = Phase::Won;
        }
    }

    pub fn take_hit(&mut self) {
        if self.phase != Phase::Playing {
            return;
        }
        self.lives -= 1;
        if self.lives == 0 {
            self.phase = Phase::Lost;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn collecting_all_goals_wins_and_terminal_state_is_stable() {
        let mut run = RunState::new(3, 2);
        for n in 1..=3 {
            run.collect();
            assert_eq!(run.collected, n);
        }
        assert_eq!(run.phase, Phase::Won);
        run.collect();
        run.take_hit();
        assert_eq!(run.collected, 3);
        assert_eq!(run.lives, 2);
        assert_eq!(run.phase, Phase::Won);
    }

    #[test]
    fn enemy_damage_can_lose_but_never_underflows() {
        let mut run = RunState::new(1, 2);
        run.take_hit();
        assert_eq!(run.phase, Phase::Playing);
        run.take_hit();
        assert_eq!(run.phase, Phase::Lost);
        run.take_hit();
        run.collect();
        assert_eq!(run.lives, 0);
        assert_eq!(run.collected, 0);
    }

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
