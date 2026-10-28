# Room Action Kit — first player-consumable Game LEGO

This is an actually playable, terminal-viewed room action loop powered by the mature Bevy 0.20 ECS. Not a new Ordivon-wide game engine or LEGO registry.

Recursive LEGO R2.1: identity = room-action-kit-r0; one responsibility = consume a player action and advance one complete room encounter; input = five actions w/a/s/d/f; output = grid, HP, enemy count, terminal victory/defeat; behavioral contract = bounded movement, Manhattan adjacent attacks, deterministic enemy reaction, no turn without valid input, no advances after terminal state; acceptance = cargo test plus direct playable CLI.

Material LEGO: room cells and wall layout. Capability LEGO: Bevy ECS movement/attack/health systems. Thinking LEGO: replaceable one-step Manhattan chase policy. High-level consumed LEGO: complete room battle with visible win/loss/replay.

From this directory (Rust 1.99.1 is already installed in the Ordivon Runtime):

- rustup run 1.99.1 cargo test --offline --locked
- rustup run 1.99.1 cargo run --offline --locked
- rustup run 1.99.1 cargo run --offline --locked -- --demo

The default Rust 1.95 toolchain is **too old** for Bevy 0.20 (requires Rust >=1.97.1). Use 1.99.1. This is engine-native execution, not a new package manager.

This is deliberately a terminal-playable vertical slice, not yet a graphical Bevy game. No music, art, saves, procedural maps, mod runtime or whole-Rust Formal refinement claims.
