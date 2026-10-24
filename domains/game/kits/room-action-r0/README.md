# Room Action Kit — R3 genre LEGO consumer

**Genre LEGO assembly, not a game product.** This new native Bevy consumer does not continue Echo Relay; any former game and its named Echo mechanic remain retired history. No narrative, visual art, animation, audio, procedural dungeon framework, or special powers are in scope.

The exact first playable contract: move (WASD), aim (mouse), fire (left click), defeat two pursuing enemies, cross the green door, automatically gain +1 attack and recover 1 health, defeat three enemies, cross the door to win. Enemy contact causes damage; after defeat or victory, press **R** to restart. Coloured primitive sprites are diagnostics, not commissioned art.

### Replaceable genre LEGO, not an engine rewrite

- GameConfig is the single typed gameplay recipe: positive player health / starting
  attack, one or more rooms, enemy positions / hit points and per-exit reward.
- RoomSpec / EnemySpec / Reward are immutable-to-the-consumer data shapes.
  For R0, edit GameConfig::default in src/lib.rs to change the built-in game
  recipe; no Bevy ECS behavior code or plugin should change.
- Run::with_config checks the recipe before admitting a run; restart keeps the
  same recipe. The native Bevy spawn_enemies adapter reads run.current_room.
  The ECS consumer test swaps every value and verifies actual spawned
  entities, room transition and attack reward—not only pure Rust structs.

### R3: Encounter Waves, Dash and Seeded Room Selection

These LEGO deliberately reuse existing game state and Bevy Systems:

- RoomSpec.reinforcement_waves: an optional list of nonempty EnemySpec waves;
  original enemies form wave zero. Run::advance_wave only proceeds after the
  ECS-derived live enemy count reaches zero. Until the final wave is cleared,
  Run::enter_gate fails even if an intermediate clear temporarily marks
  GateOpen. A boss is initially just a durable configured enemy in a later
  wave; it is not an extra bespoke execution framework.
- GameConfig.dash: optional DashSpec with speed, active_ms, cooldown_ms.
  Space triggers the player mobility dash while a direction is held. DashState
  is independent of Bevy, is reset on restart and rejects repeated triggers
  while cooling down. It deliberately has no implied invulnerability window.
- rooms_from_seed(seed, templates, count): deterministic sampling with
  replacement from existing RoomSpec templates. It consumes the stable
  rand crate under Cargo.lock; it does NOT fabricate procedural room geometry,
  a dungeon graph or guaranteed unique rooms. Save the seed plus exact
  source and lock revisions for reproducible replay across upgrades.

Example: same enemy vocabulary, now a boss after a normal encounter:

~~~rust
let mut cfg = GameConfig::default();
cfg.rooms[0].reinforcement_waves = vec![vec![EnemySpec {
    x: 180, y: 0, health: 20, speed: 40,
    behavior: EnemyBehavior::KeepDistance {
        min_distance: 70, max_distance: 150,
    },
}]];
cfg.dash = Some(DashSpec {
    speed: 620, active_ms: 200, cooldown_ms: 800,
});
cfg.rooms = rooms_from_seed(314159, &cfg.rooms, 4)?;
let run = Run::with_config(cfg)?;
~~~

Headless Bevy tests explicitly prove that a pending boss wave blocks the gate,
dash changes the actual player movement, and a seeded room template creates
the intended live entities. Keep interfaces small and use native Bevy ECS
scheduling and the locked mature random-number implementation.

### R5: bounded piercing projectile LEGO

The optional WeaponSpec.pierce field counts **extra distinct enemies** a single
projectile may hit after the first target. Default 0 preserves earlier JSON
recipes and normal single-target bullet behavior. Values above 8 are rejected.
The built-in LegoPalette includes a simple piercing weapon with pierce=2;
choose one with seeded generation or edit any exported palette.json / recipe.json.

    cargo run --locked --bin room-action -- --palette-json > palette.json
    cargo run --locked --bin room-action -- --seed 42 --rooms 4 --palette palette.json --json > recipe.json
    # set recipe.json weapon.pierce = 1, then run:
    cargo run --locked --bin room-action -- --recipe recipe.json

Native ECS projectile collisions keep per-shot hit-target identity to avoid
repeating damage against the same living enemy on later frames. The shot is
retired after the configured number of distinct targets; encounter clearing
remains authoritative from actually living foes. Pure recipe validation,
real shot spawning, same-frame multi-hit, cross-frame no-double-hit, JSON
backward compatibility, Golden Path and replay are covered by cargo tests.

This is overlap-based collision, not continuous swept collision or a
general-purpose physics engine. Ricochet, elemental effects, projectile
reflection and enemy ranged attacks remain separate optional LEGO for
consumers that require them.

### R4: Agent-native JSON recipes

The authority remains the actual Bevy consumer, not a new parser or a
Python copy of the game. Standard serde + serde_json connect the existing
validated GameConfig and LegoPalette to CLI-Anything-style JSON I/O.

    cargo run --locked --bin room-action -- --palette-json > palette.json
    # Edit the catalog's weapon, enemy or room templates.
    cargo run --locked --bin room-action -- --seed 42 --rooms 4 --palette palette.json --json > recipe.json
    # Edit the concrete weapon, reward, or room JSON without changing Rust.
    cargo run --locked --bin room-action -- --recipe recipe.json --json
    cargo run --locked --bin room-action -- --recipe recipe.json

Without flags, the original two-room playable remains the default. With
--json, the command prints the validated concrete recipe without opening a
window or requiring graphics. --palette-json exposes the built-in catalog
for discovery; --palette FILE changes eligible LEGO for seeded generation.
--recipe FILE loads a concrete recipe through the same Run::with_config and
Bevy Session used by all other consumers.

Strict JSON deserialization rejects unknown fields; invalid game values are
rejected before entity creation. JSON inputs are capped at 1 MiB and CLI
failures return nonzero exit status with readable errors. Recipe generation
and replay identity depend on source and Cargo.lock; when source schema or
dependencies change, repeat the native locked consumer contract. No extra
agent, bespoke DSL, stateful command service or second runtime is necessary.

### LEGO generator — bounded R3 composition

`LegoPalette` is a finite catalog of room templates, weapon specs and enemy
archetypes (health, speed, behavior). `compose_game(seed, count, palette)`
selects real existing LEGO to build an ordinary validated `GameConfig`.
It reuses the pre-existing `rooms_from_seed` and `rand` rather than a
homegrown PRNG. Room positions/reinforcement waves come from room templates;
enemy stats/behaviors and the weapon are independently selected from the
palette. The result still uses the existing Bevy Session, shot, encounter,
wave, reward and restart systems.

Run the default two-room game unchanged:

    mise run play

Or generate a reproducible four-room variation without editing code:

    cargo run --locked --bin room-action -- --seed 42 --rooms 4

`--rooms` defaults to four with `--seed`. The generator supports 1..=32
rooms and rejects empty, invalid and oversized catalogs. The same seed,
palette and pinned `rand` / Cargo.lock produces a reproducible recipe;
changing the catalog or dependency version may change generation results.
Extend `LegoPalette::default()` or supply a typed custom palette to add
new compositions. Tests verify replay, invalid input rejection and real ECS
spawn fidelity. This is a finite seeded composition tool, not an AI content
artist, an unlimited procedural map builder or proof of enjoyable gameplay.

### R2: Weapon and Enemy Behavior Recipes

A single `GameConfig` still owns the run; two responsibilities are now
replaceable **without a second engine layer**:

- `WeaponSpec`: damage, cooldown_ms, projectile_speed, pellets (1..=9),
  spread_degrees (0..=120). `Run::weapon_damage` composes weapon base
  damage with the current attack reward using saturating math. A projectile
  snapshots the damage at fire time. One pellet always aims centrally.
- `EnemySpec`: spawn position, health, speed, and `EnemyBehavior`:
  `Chase` or `KeepDistance {min_distance,max_distance}`. Keeping
  distance retreats when too close, approaches when far, and waits in
  the specified band. Overlapping coordinates never trap an enemy forever.

To compose a three-pellet fan with a skirmisher, only edit the recipe:

~~~rust
let mut config = GameConfig::default();
config.weapon = WeaponSpec {
    damage: 3, cooldown_ms: 120, projectile_speed: 420,
    pellets: 3, spread_degrees: 30,
};
config.rooms[0].enemies[0].behavior = EnemyBehavior::KeepDistance {
    min_distance: 50, max_distance: 100,
};
config.rooms[0].enemies[0].speed = 115;
let run = Run::with_config(config)?;
~~~

The Bevy ECS consumer tests verify real spread projectiles and changed
enemy movement, with the original Golden Path, replay and failure injection
unchanged. Neither runtime file loading nor ranged enemy attacks are part
of this minimal LEGO, unless actual consumers demand them.

The responsibilities intentionally share one small Rust crate rather than
creating a universal scene grammar, asset pipeline, or separate config service.
Use native Bevy Assets / Scenes if real content consumers later need runtime
editable files.

**LEGO boundaries:** `src/lib.rs` owns deterministic run/encounter/gate/reward/damage/restart rules. `src/main.rs` consumes Bevy 0.20 ECS for input, sprites, movement, projectiles, simple proximity hits and instantiation. This is deliberately one crate, without a proprietary common game runtime. Physics and UI can be replaced with mature engine components when demanded by a real consumer; no duplicate universal framework.

Requires stable Rust 1.99.1. Lock Bevy 0.20.0 and all transitive dependencies in `Cargo.lock`.

From this directory:

```sh
mise run rules     # fast rules, no Bevy rendering build
mise run verify    # Bevy ECS Golden Path, replay, injected extra enemy, collision
mise run play      # native graphics/keyboard/mouse, real device needed
```

Testing a pure rule does not prove real graphics, keyboard/mouse or fun. The playable requires a graphical desktop and working GPU driver (or functioning Vulkan software renderer). This WSL runtime can compile/link it but its current Vulkan/GL display path reports no compatible GPU; real rendering and input are UNVERIFIED. Visually review on a supported native desktop before claiming full acceptance.


The headless Bevy consumer contracts do **not** need a GPU. They run a real
`App` with ECS entities and real encounter / projectile / gate systems.
The trajectory test compares the complete projected run state and live enemy
count after each scripted action; it is deterministic **scripted ECS replay**,
not a recording of real player keyboard/mouse input.

Failure-injection contracts include extra live enemies and simultaneous
projectiles. A gate must be blocked while a live foe exists; concurrent hits
must never count the same death twice. The Game state is a projection of
Bevy's authoritative live enemy entities at the integration boundary.

Bevy 0.20.0 and Rust 1.99.1 are the verified current stable versions as of
2026-10-23. When upgrading, use the native Cargo owner:
`cargo update` updates `Cargo.lock` to compatible available versions;
then run `mise run verify` and actual `mise run play` on a desktop
consumer. Set CARGO_NET_OFFLINE=true for a pre-cached offline check; cold CI consumers may fetch via Cargo. Do not claim a lock-only upgrade succeeded.

### Windows active-user and real input boundary

For the native Windows consumer use the existing Runtime windows_native target
with windowsAuthority=active_user: the Windows service identity has a different
PATH and cannot prove ownership of a real user's interactive foreground desktop.
The active user's mise Rust is already available on the tested workstation.

From a user-accessible exact-source Windows copy, run:

    cargo test --locked --all-targets
    cargo build --locked --bin room-action
    python scripts/windows_foreground_guard.py target\debug\room-action.exe

This tiny stdlib-only foreground guard returns PASS only when the exact game
executable, not LockApp or an unrelated process, owns the foreground HWND.
HOLD (exit 20) is the expected result for a locked desktop. An active-user token
and a created native window alone do not prove keyboard/mouse consumption.
Only a legitimately unlocked, already game-focused desktop may proceed to
separately bounded real-control testing. The guard never unlocks, focuses or
sends input and is not a production game dependency.
