//! Pure game-type rules. The playable Bevy adapter lives in main.rs.
//! No graphics, input devices, engine objects or product-specific Echo mechanic.

use serde::{Deserialize, Serialize};

pub const MAX_HEALTH: i32 = 5;

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct WeaponSpec {
    pub damage: i32,
    pub cooldown_ms: u16,
    pub projectile_speed: u16,
    pub pellets: u8,
    pub spread_degrees: u16,
    /// Additional distinct enemies a shot can hit after its first target.
    #[serde(default)]
    pub pierce: u8,
}
impl Default for WeaponSpec {
    fn default() -> Self {
        Self {
            damage: 1,
            cooldown_ms: 190,
            projectile_speed: 540,
            pellets: 1,
            spread_degrees: 0,
            pierce: 0,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub enum EnemyBehavior {
    #[default]
    Chase,
    /// Retreat when too close, approach when far, wait within the band.
    KeepDistance {
        min_distance: u16,
        max_distance: u16,
    },
}
impl EnemyBehavior {
    pub fn movement_sign(self, distance: f32) -> f32 {
        match self {
            Self::Chase => 1.0,
            Self::KeepDistance {
                min_distance,
                max_distance,
            } => {
                if distance < f32::from(min_distance) {
                    -1.0
                } else if distance > f32::from(max_distance) {
                    1.0
                } else {
                    0.0
                }
            }
        }
    }
    fn is_valid(self) -> bool {
        match self {
            Self::Chase => true,
            Self::KeepDistance {
                min_distance,
                max_distance,
            } => min_distance > 0 && max_distance > min_distance,
        }
    }
}

/// Game-type data only: replacing a room recipe must not change the game loop.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EnemySpec {
    pub x: i32,
    pub y: i32,
    pub health: i32,
    pub speed: u16,
    pub behavior: EnemyBehavior,
}

#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Reward {
    pub attack: i32,
    pub healing: i32,
}

/// Optional mobility LEGO. Milliseconds make the cooldown independent of frame count.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DashSpec {
    pub speed: u16,
    pub active_ms: u16,
    pub cooldown_ms: u16,
}
impl Default for DashSpec {
    fn default() -> Self {
        Self {
            speed: 620,
            active_ms: 200,
            cooldown_ms: 800,
        }
    }
}
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct DashState {
    active_ms: u32,
    cooldown_ms: u32,
}
impl DashState {
    pub fn active(&self) -> bool {
        self.active_ms != 0
    }
    pub fn try_start(&mut self, spec: &DashSpec) -> bool {
        if self.cooldown_ms != 0 {
            return false;
        }
        self.active_ms = u32::from(spec.active_ms);
        self.cooldown_ms = u32::from(spec.cooldown_ms);
        true
    }
    pub fn tick(&mut self, ms: u32) {
        self.active_ms = self.active_ms.saturating_sub(ms);
        self.cooldown_ms = self.cooldown_ms.saturating_sub(ms);
    }
}

/// Standard rand PRNG, rather than an in-house generator.
/// Seed is reproducible under the pinned rand and Cargo.lock version.
pub fn rooms_from_seed(
    seed: u64,
    templates: &[RoomSpec],
    count: usize,
) -> Result<Vec<RoomSpec>, &'static str> {
    use rand::{RngExt, SeedableRng};
    if templates.is_empty() || count == 0 || count > 1000 {
        return Err("invalid room-pool size or requested length");
    }
    let mut rng = rand::rngs::StdRng::seed_from_u64(seed);
    Ok((0..count)
        .map(|_| templates[rng.random_range(0..templates.len())].clone())
        .collect())
}

/// Reusable enemy behavior/health/speed without embedding the spawn coordinates.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EnemyArchetype {
    pub health: i32,
    pub speed: u16,
    pub behavior: EnemyBehavior,
}

/// Finite input LEGO palette: templates in, an ordinary GameConfig out.
/// No new runtime entity registry or bespoke random number generator.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct LegoPalette {
    pub rooms: Vec<RoomSpec>,
    pub weapons: Vec<WeaponSpec>,
    pub enemies: Vec<EnemyArchetype>,
}

impl Default for LegoPalette {
    fn default() -> Self {
        let defaults = GameConfig::default();
        Self {
            rooms: defaults.rooms,
            weapons: vec![
                WeaponSpec::default(),
                WeaponSpec {
                    damage: 2,
                    cooldown_ms: 290,
                    projectile_speed: 460,
                    pellets: 3,
                    spread_degrees: 30,
                    pierce: 0,
                },
                WeaponSpec {
                    damage: 1,
                    cooldown_ms: 220,
                    projectile_speed: 600,
                    pellets: 1,
                    spread_degrees: 0,
                    pierce: 2,
                },
            ],
            enemies: vec![
                EnemyArchetype {
                    health: 2,
                    speed: 78,
                    behavior: EnemyBehavior::Chase,
                },
                EnemyArchetype {
                    health: 3,
                    speed: 104,
                    behavior: EnemyBehavior::KeepDistance {
                        min_distance: 65,
                        max_distance: 155,
                    },
                },
            ],
        }
    }
}

/// Generate a validated game recipe. Same seed+catalog+locked rand version
/// produces the same content, independently of the Bevy frame scheduler.
/// The returned GameConfig is consumed by the *existing* Session and ECS.
pub fn compose_game(
    seed: u64,
    room_count: usize,
    palette: &LegoPalette,
) -> Result<GameConfig, &'static str> {
    use rand::{RngExt, SeedableRng};

    if !(1..=32).contains(&room_count)
        || palette.rooms.is_empty()
        || palette.weapons.is_empty()
        || palette.enemies.is_empty()
        || palette.rooms.len() > 64
        || palette.weapons.len() > 64
        || palette.enemies.len() > 64
    {
        return Err("empty or oversized game LEGO palette");
    }

    // Fail closed even if an invalid catalog entry would not be selected.
    let baseline = GameConfig::default();
    for room in &palette.rooms {
        Run::with_config(GameConfig {
            rooms: vec![room.clone()],
            ..baseline.clone()
        })?;
    }
    for weapon in &palette.weapons {
        Run::with_config(GameConfig {
            weapon: weapon.clone(),
            ..baseline.clone()
        })?;
    }
    for candidate in &palette.enemies {
        Run::with_config(GameConfig {
            rooms: vec![RoomSpec {
                enemies: vec![EnemySpec {
                    x: 0,
                    y: 0,
                    health: candidate.health,
                    speed: candidate.speed,
                    behavior: candidate.behavior,
                }],
                reinforcement_waves: vec![],
                exit_reward: Reward::default(),
            }],
            ..baseline.clone()
        })?;
    }

    // Existing seeded room generator owns room-template selection.
    let rooms = rooms_from_seed(seed, &palette.rooms, room_count)?;
    let mut rng = rand::rngs::StdRng::seed_from_u64(seed);
    let mut config = GameConfig {
        rooms,
        weapon: palette.weapons[rng.random_range(0..palette.weapons.len())].clone(),
        ..baseline
    };
    for room in &mut config.rooms {
        for foe in room
            .enemies
            .iter_mut()
            .chain(room.reinforcement_waves.iter_mut().flatten())
        {
            let candidate = &palette.enemies[rng.random_range(0..palette.enemies.len())];
            foe.health = candidate.health;
            foe.speed = candidate.speed;
            foe.behavior = candidate.behavior;
        }
    }
    Run::with_config(config.clone())?;
    Ok(config)
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RoomSpec {
    pub enemies: Vec<EnemySpec>,
    pub reinforcement_waves: Vec<Vec<EnemySpec>>,
    pub exit_reward: Reward,
}
impl RoomSpec {
    pub fn enemies_for_wave(&self, wave: usize) -> &[EnemySpec] {
        if wave == 0 {
            &self.enemies
        } else {
            &self.reinforcement_waves[wave - 1]
        }
    }
    pub fn wave_count(&self) -> usize {
        self.reinforcement_waves.len() + 1
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GameConfig {
    pub rooms: Vec<RoomSpec>,
    pub max_health: i32,
    pub initial_attack: i32,
    pub weapon: WeaponSpec,
    pub dash: Option<DashSpec>,
}

impl Default for GameConfig {
    fn default() -> Self {
        fn foe(x: i32, y: i32) -> EnemySpec {
            EnemySpec {
                x,
                y,
                health: 2,
                speed: 78,
                behavior: EnemyBehavior::Chase,
            }
        }
        Self {
            rooms: vec![
                RoomSpec {
                    reinforcement_waves: vec![],
                    enemies: vec![foe(115, 120), foe(180, -115)],
                    exit_reward: Reward {
                        attack: 1,
                        healing: 1,
                    },
                },
                RoomSpec {
                    reinforcement_waves: vec![],
                    enemies: vec![foe(115, 120), foe(180, -115), foe(20, -25)],
                    exit_reward: Reward::default(),
                },
            ],
            max_health: MAX_HEALTH,
            initial_attack: 1,
            weapon: WeaponSpec::default(),
            dash: Some(DashSpec::default()),
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Phase {
    Fighting,
    GateOpen,
    Victory,
    Defeat,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Run {
    pub room: usize,
    pub wave: usize,
    pub remaining: u32,
    pub health: i32,
    pub attack: i32,
    pub phase: Phase,
    config: GameConfig,
}

impl Default for Run {
    fn default() -> Self {
        Self::with_config(GameConfig::default()).expect("built-in room recipe is valid")
    }
}

impl Run {
    pub fn with_config(config: GameConfig) -> Result<Self, &'static str> {
        if config.rooms.is_empty()
            || config.max_health <= 0
            || config.initial_attack <= 0
            || config.weapon.damage <= 0
            || config.weapon.cooldown_ms == 0
            || config.weapon.projectile_speed == 0
            || config.weapon.pellets == 0
            || config.weapon.pellets > 9
            || config.weapon.spread_degrees > 120
            || config.weapon.pierce > 8
            || config.dash.is_some_and(|dash| {
                dash.speed == 0 || dash.active_ms == 0 || dash.cooldown_ms < dash.active_ms
            })
            || config.rooms.iter().any(|room| {
                room.enemies.is_empty()
                    || room.enemies.len() > u32::MAX as usize
                    || room.reinforcement_waves.iter().any(|wave| {
                        wave.is_empty()
                            || wave.len() > u32::MAX as usize
                            || wave.iter().any(|foe| {
                                foe.health <= 0 || foe.speed == 0 || !foe.behavior.is_valid()
                            })
                    })
                    || room
                        .enemies
                        .iter()
                        .any(|foe| foe.health <= 0 || foe.speed == 0 || !foe.behavior.is_valid())
                    || room.exit_reward.attack < 0
                    || room.exit_reward.healing < 0
            })
        {
            return Err("invalid room-action recipe");
        }
        Ok(Self {
            room: 0,
            wave: 0,
            remaining: config.rooms[0].enemies.len() as u32,
            health: config.max_health,
            attack: config.initial_attack,
            phase: Phase::Fighting,
            config,
        })
    }

    pub fn config(&self) -> &GameConfig {
        &self.config
    }

    /// A weapon's damage composes multiplicatively with progression's attack.
    pub fn weapon_damage(&self) -> i32 {
        self.attack.saturating_mul(self.config.weapon.damage)
    }

    pub fn current_room(&self) -> &RoomSpec {
        &self.config.rooms[self.room]
    }

    pub fn current_wave_enemies(&self) -> &[EnemySpec] {
        self.current_room().enemies_for_wave(self.wave)
    }

    /// Continue the encounter only when all actual live enemies are gone.
    pub fn advance_wave(&mut self) -> bool {
        if self.phase != Phase::GateOpen || self.wave + 1 >= self.current_room().wave_count() {
            return false;
        }
        self.wave += 1;
        self.remaining = self.current_wave_enemies().len() as u32;
        self.phase = Phase::Fighting;
        true
    }

    pub fn enemy_defeated(&mut self) -> bool {
        if self.phase != Phase::Fighting || self.remaining == 0 {
            return false;
        }
        self.remaining -= 1;
        if self.remaining == 0 {
            self.phase = Phase::GateOpen;
        }
        true
    }

    /// Reconcile the room projection with the authoritative live enemy entities.
    /// Covers additional spawns, external despawns and simultaneous kills.
    pub fn reconcile_living_enemies(&mut self, living: u32) {
        if !matches!(self.phase, Phase::Fighting | Phase::GateOpen) {
            return;
        }
        self.remaining = living;
        self.phase = if living == 0 {
            Phase::GateOpen
        } else {
            Phase::Fighting
        };
    }

    pub fn enter_gate(&mut self) -> bool {
        if self.phase != Phase::GateOpen || self.wave + 1 < self.current_room().wave_count() {
            return false;
        }
        if self.room + 1 == self.config.rooms.len() {
            self.phase = Phase::Victory;
        } else {
            let reward = &self.config.rooms[self.room].exit_reward;
            self.attack = self.attack.saturating_add(reward.attack);
            self.health = self
                .health
                .saturating_add(reward.healing)
                .min(self.config.max_health);
            self.room += 1;
            self.wave = 0;
            self.remaining = self.current_wave_enemies().len() as u32;
            self.phase = Phase::Fighting;
        }
        true
    }

    pub fn take_hit(&mut self) -> bool {
        if !matches!(self.phase, Phase::Fighting | Phase::GateOpen) {
            return false;
        }
        self.health = (self.health - 1).max(0);
        if self.health == 0 {
            self.phase = Phase::Defeat;
        }
        true
    }

    pub fn can_act(&self) -> bool {
        matches!(self.phase, Phase::Fighting | Phase::GateOpen)
    }

    pub fn restart(&mut self) {
        *self = Self::with_config(self.config.clone()).expect("active room recipe was validated");
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn closed_room_never_allows_early_travel() {
        let mut run = Run::default();
        assert!(!run.enter_gate());
        assert!(run.enemy_defeated());
        assert_eq!(run.remaining, 1);
        assert_eq!(run.phase, Phase::Fighting);
        assert!(!run.enter_gate());
    }

    #[test]
    fn golden_path_two_rooms_reward_then_victory() {
        let mut run = Run::default();
        for _ in 0..2 {
            assert!(run.enemy_defeated());
        }
        assert_eq!(run.phase, Phase::GateOpen);
        assert!(!run.enemy_defeated());
        assert!(run.enter_gate());
        assert_eq!((run.room, run.remaining, run.attack), (1, 3, 2));
        for _ in 0..3 {
            assert!(run.enemy_defeated());
        }
        assert!(run.enter_gate());
        assert_eq!(run.phase, Phase::Victory);
        assert!(!run.enter_gate());
        assert!(!run.take_hit());
    }

    #[test]
    fn replacement_room_recipe_changes_enemies_reward_and_restart_without_code_changes() {
        let config = GameConfig {
            max_health: 7,
            initial_attack: 2,
            weapon: WeaponSpec::default(),
            dash: None,
            rooms: vec![
                RoomSpec {
                    reinforcement_waves: vec![],
                    enemies: vec![EnemySpec {
                        x: 91,
                        y: 42,
                        health: 4,

                        speed: 78,
                        behavior: EnemyBehavior::Chase,
                    }],
                    exit_reward: Reward {
                        attack: 3,
                        healing: 2,
                    },
                },
                RoomSpec {
                    reinforcement_waves: vec![],
                    enemies: vec![
                        EnemySpec {
                            x: -31,
                            y: 80,
                            health: 2,

                            speed: 78,
                            behavior: EnemyBehavior::Chase,
                        },
                        EnemySpec {
                            x: 55,
                            y: -80,
                            health: 3,

                            speed: 78,
                            behavior: EnemyBehavior::Chase,
                        },
                    ],
                    exit_reward: Reward::default(),
                },
            ],
        };
        let mut run = Run::with_config(config.clone()).unwrap();
        assert_eq!((run.health, run.attack, run.remaining), (7, 2, 1));
        assert_eq!(run.current_room().enemies[0].x, 91);
        assert!(run.enemy_defeated());
        assert!(run.enter_gate());
        assert_eq!((run.room, run.remaining, run.attack), (1, 2, 5));
        assert_eq!(run.current_room().enemies[0].health, 2);
        assert!(run.take_hit());
        run.restart();
        assert_eq!(
            (run.room, run.remaining, run.health, run.attack),
            (0, 1, 7, 2)
        );
        assert_eq!(run.config(), &config);
    }

    #[test]
    fn invalid_room_recipe_rejected_before_consumption() {
        let invalid = GameConfig {
            max_health: 5,
            initial_attack: 1,
            weapon: WeaponSpec::default(),
            dash: None,
            rooms: vec![RoomSpec {
                reinforcement_waves: vec![],
                enemies: vec![],
                exit_reward: Reward::default(),
            }],
        };
        assert!(Run::with_config(invalid).is_err());
    }

    #[test]
    fn reward_heals_without_overflow_and_restart_clears_state() {
        let mut run = Run::default();
        assert!(run.take_hit());
        assert_eq!(run.health, 4);
        for _ in 0..2 {
            run.enemy_defeated();
        }
        run.enter_gate();
        assert_eq!(run.health, MAX_HEALTH);
        for _ in 0..MAX_HEALTH {
            assert!(run.take_hit());
        }
        assert_eq!(run.phase, Phase::Defeat);
        assert!(!run.enemy_defeated());
        assert!(!run.enter_gate());
        run.restart();
        assert_eq!(run, Run::default());
    }
    #[test]
    fn weapon_recipe_and_behavior_are_replaceable_without_gameplay_forks() {
        let mut config = GameConfig {
            weapon: WeaponSpec {
                damage: 3,
                cooldown_ms: 120,
                projectile_speed: 420,
                pellets: 3,
                spread_degrees: 30,
                pierce: 0,
            },
            ..GameConfig::default()
        };
        config.rooms[0].enemies[0].behavior = EnemyBehavior::KeepDistance {
            min_distance: 50,
            max_distance: 100,
        };
        config.rooms[0].enemies[0].speed = 115;
        let mut run = Run::with_config(config.clone()).unwrap();
        assert_eq!(run.config().weapon.pellets, 3);
        assert_eq!(run.weapon_damage(), 3);
        assert_eq!(run.current_room().enemies[0].speed, 115);
        assert_eq!(
            run.current_room().enemies[0].behavior.movement_sign(20.0),
            -1.0
        );
        assert_eq!(
            run.current_room().enemies[0].behavior.movement_sign(75.0),
            0.0
        );
        assert_eq!(
            run.current_room().enemies[0].behavior.movement_sign(160.0),
            1.0
        );
        assert_eq!(EnemyBehavior::Chase.movement_sign(20.0), 1.0);
        for _ in 0..run.remaining {
            assert!(run.enemy_defeated());
        }
        run.enter_gate();
        run.restart();
        assert_eq!(run.config(), &config);
        assert_eq!(run.weapon_damage(), 3);
    }

    #[test]
    fn invalid_weapon_or_kiting_config_is_rejected_before_bevy() {
        let mut config = GameConfig::default();
        config.weapon.pellets = 0;
        assert!(Run::with_config(config.clone()).is_err());
        config.weapon.pellets = 3;
        config.weapon.projectile_speed = 0;
        assert!(Run::with_config(config.clone()).is_err());
        config.weapon.projectile_speed = 420;
        config.rooms[0].enemies[0].behavior = EnemyBehavior::KeepDistance {
            min_distance: 100,
            max_distance: 50,
        };
        assert!(Run::with_config(config).is_err());
    }
    #[test]
    fn reinforcement_wave_blocks_gate_until_final_enemy_and_survives_restart() {
        let mut cfg = GameConfig::default();
        cfg.rooms[0].reinforcement_waves = vec![vec![EnemySpec {
            x: 180,
            y: 0,
            health: 20,
            speed: 40,
            behavior: EnemyBehavior::KeepDistance {
                min_distance: 70,
                max_distance: 150,
            },
        }]];
        let mut run = Run::with_config(cfg).unwrap();
        assert_eq!(run.wave, 0);
        run.reconcile_living_enemies(0);
        assert!(
            !run.enter_gate(),
            "a pending boss wave must not allow room traversal"
        );
        assert!(run.advance_wave());
        assert_eq!(
            (run.wave, run.remaining, run.phase),
            (1, 1, Phase::Fighting)
        );
        assert_eq!(run.current_wave_enemies()[0].health, 20);
        run.reconcile_living_enemies(0);
        assert!(!run.advance_wave());
        assert!(run.enter_gate());
        run.restart();
        assert_eq!((run.room, run.wave, run.remaining), (0, 0, 2));
    }

    #[test]
    fn dash_cooldown_is_reusable_gameplay_rule_and_invalid_dashes_reject() {
        let spec = DashSpec {
            speed: 620,
            active_ms: 200,
            cooldown_ms: 800,
        };
        let mut d = DashState::default();
        assert!(d.try_start(&spec));
        assert!(!d.try_start(&spec));
        assert!(d.active());
        d.tick(200);
        assert!(!d.active());
        assert!(!d.try_start(&spec));
        d.tick(600);
        assert!(d.try_start(&spec));
        let mut cfg = GameConfig {
            dash: Some(spec),
            ..GameConfig::default()
        };
        assert!(Run::with_config(cfg.clone()).is_ok());
        cfg.dash = Some(DashSpec { speed: 0, ..spec });
        assert!(Run::with_config(cfg).is_err());
    }

    #[test]
    fn generator_catalog_exposes_piercing_weapon_as_reusable_lego() {
        let palette = LegoPalette::default();
        assert!(palette.weapons.iter().any(|weapon| weapon.pierce == 2));
        assert!((0..50).any(|seed| compose_game(seed, 4, &palette).unwrap().weapon.pierce == 2));
    }

    #[test]
    fn projectile_pierce_is_backward_compatible_json_and_validated() {
        let mut config = GameConfig::default();
        config.weapon.pierce = 2;
        let json = serde_json::to_value(&config).unwrap();
        assert_eq!(json["weapon"]["pierce"], 2);
        let parsed: GameConfig = serde_json::from_value(json).unwrap();
        assert_eq!(parsed.weapon.pierce, 2);
        assert!(Run::with_config(parsed).is_ok());
        config.weapon.pierce = 9;
        assert!(Run::with_config(config.clone()).is_err());
        // R4 recipes omit this new optional key. They must still load unchanged.
        let mut old: serde_json::Value = serde_json::to_value(&config).unwrap();
        old["weapon"].as_object_mut().unwrap().remove("pierce");
        let loaded: GameConfig = serde_json::from_value(old).unwrap();
        assert_eq!(loaded.weapon.pierce, 0);
    }

    #[test]
    fn recipe_json_round_trip_matches_consumed_run() {
        let recipe = compose_game(42, 4, &LegoPalette::default()).unwrap();
        let text = serde_json::to_string_pretty(&recipe).unwrap();
        let decoded: GameConfig = serde_json::from_str(&text).unwrap();
        assert_eq!(Run::with_config(decoded).unwrap().config(), &recipe);
    }

    #[test]
    fn palette_json_round_trip_preserves_generator_and_validation() {
        let palette = LegoPalette::default();
        let text = serde_json::to_string_pretty(&palette).unwrap();
        let decoded: LegoPalette = serde_json::from_str(&text).unwrap();
        assert_eq!(palette, decoded);
        assert_eq!(
            compose_game(7, 3, &decoded).unwrap(),
            compose_game(7, 3, &palette).unwrap()
        );
    }

    #[test]
    fn catalog_generator_replays_identically_and_composes_across_categories() {
        let palette = LegoPalette::default();
        let a = compose_game(42, 5, &palette).unwrap();
        let b = compose_game(42, 5, &palette).unwrap();
        assert_eq!(a, b);
        assert_eq!(a.rooms.len(), 5);
        assert!(palette.weapons.contains(&a.weapon));
        for room in &a.rooms {
            assert!(
                palette
                    .rooms
                    .iter()
                    .any(|r| r.enemies.len() == room.enemies.len())
            );
            for foe in room
                .enemies
                .iter()
                .chain(room.reinforcement_waves.iter().flatten())
            {
                assert!(
                    palette
                        .enemies
                        .iter()
                        .any(|candidate| foe.health == candidate.health
                            && foe.speed == candidate.speed
                            && foe.behavior == candidate.behavior)
                );
            }
        }
        assert!(Run::with_config(a).is_ok());
        let variants: std::collections::HashSet<_> = (0..40)
            .map(|seed| format!("{:?}", compose_game(seed, 5, &palette).unwrap()))
            .collect();
        assert!(variants.len() >= 8, "seed must change more than the label");
    }

    #[test]
    fn catalog_generator_rejects_invalid_inputs_before_any_game_spawns() {
        let mut palette = LegoPalette::default();
        assert!(compose_game(12, 0, &palette).is_err());
        assert!(compose_game(12, 33, &palette).is_err());
        palette.weapons.clear();
        assert!(compose_game(12, 2, &palette).is_err());
        palette = LegoPalette::default();
        palette.enemies[1].speed = 0; // invalid even if unselected
        assert!(compose_game(12, 2, &palette).is_err());
    }

    #[test]
    fn same_seed_reuses_exact_room_recipe_while_different_seeds_vary() {
        let sample = GameConfig::default();
        let pool = sample.rooms.clone();
        let a = rooms_from_seed(314159, &pool, 20).unwrap();
        let b = rooms_from_seed(314159, &pool, 20).unwrap();
        let c = rooms_from_seed(314160, &pool, 20).unwrap();
        assert_eq!(a, b);
        assert_ne!(a, c);
        assert!(rooms_from_seed(1, &pool, 0).is_err());
        assert!(rooms_from_seed(1, &[], 4).is_err());
    }
}
