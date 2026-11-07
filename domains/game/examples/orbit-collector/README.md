# Orbit Collector — native Bevy LEGO composition consumer

This is an **original, independently playable Rust game example**, not a new game
engine, generic Mod runtime, reusable framework, or a revival of retired Game products.

- **Mature provider:** upstream [Bevy 0.20](https://bevy.org/news/bevy-0-20/)
  native ECS, Plugin, keyboard input, Sprite, Transform, Text, schedules and resource
  lifecycle; no hand-written ECS, renderer, event broker or asset store.
- **Replaceable product rule LEGO:** `src/rules.rs` describes the bounded collection,
  damage, win and lose transitions without knowing Bevy, UI or input. `src/gameplay.rs`
  is the concrete consumer adapter (Bevy systems + game-specific scene data), not a
  library intended for unrelated games. `src/main.rs` only wires the native App.
- **Composition:** keyboard → Bevy input → player transform → proximity interactions
  → independent rules → Bevy Text/visual state; `R` restores the game with the same
  configuration. Uses engine-native shapes with no licensed third-party media files.
- **Currentness:** `Cargo.toml` pins Bevy `=0.20.1`; `Cargo.lock` is the resolved
  dependency SourceCut. Bevy version changes require a native build and re-run.
- **Bounded verification:** `cargo test` tests the pure rules and goal recipe;
  `cargo check --all-targets` checks Rust/Bevy integration. The executable
  `cargo run` requires a display/input environment. A compile PASS is **not**
  equivalent to verified human playability or any commercial release.
- **Player goal:** collect five yellow beacons before losing three lives to the red
  moving drone; WASD/arrows move, R restarts.

## Use

```sh
cd domains/game/examples/orbit-collector
cargo test --locked
cargo check --locked --all-targets
cargo run --locked
```

This bounded consumer establishes that a game-specific rule can be composed with
the upstream engine without any global Ordivon Game runtime. It does not make this
prototype a reusable gameplay LEGO until another actual product demonstrates
its replaceability and acceptance.

## Source ownership

The game product owns recipe, rules, balance and desired player experience. Bevy
owns ECS scheduling, keyboard input, rendering, UI and window integration.
The surrounding `domains/game/knowledge` collection is advisory evidence, not
a runtime dependency or implicit validator of player satisfaction.

## Human and Agent workflows

**Human:** From domains/game run mise run build:bevy for the pinned native Rust build. Run cargo run --locked inside examples/orbit-collector on a graphical computer to actually play. WASD/arrows move; R restarts. Compilation does not establish player enjoyment.

**Agent:** From domains/game run mise run test:bevy; it exercises the real Bevy ECS, player rules and HUD using Cargo.lock. This is source/state test evidence, not visual perception or a persistent interactive episode. Use mature upstream gameplay observation/control only when a real graphical consumer exists.

**Distribution:** The Cargo target executable is not a signed installer or store release. Qualify native platform packaging and player behavior independently.

## Upstream Bevy feature selection

The pinned Bevy 0.20.1 dependency enables a consumer-qualified set of
2D graphics, sprite rendering, UI, window/input (X11), default font and
multithreaded features instead of all-platform defaults. This game has no
audio, 3D, gamepad or Wayland consumer. The narrow native feature set
avoids linking unused host libraries and permits Game owner CI on
standard Linux runners without a root workflow change. Should a real
consumer require one of those capabilities, enable its upstream Bevy
feature and test the native dependency on that target.

The exact source binding remains Cargo.toml plus Cargo.lock and the
existing Game native test/build commands. Graphical Human play is
still a distinct acceptance claim.
