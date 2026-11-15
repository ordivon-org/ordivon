# Orbit Collector — completed product archive (2026-11-15)

**Status: ARCHIVED / NO ACTIVE MAINTENANCE.** This is a read-only historical
technical-validation product. It is not a Game Factory production target, a
default Game verification gate, a game-quality success, or a reusable framework.
Other native Game products remain active.

## Purpose and conclusion

The original five-beacon, three-life keyboard collection/avoidance game built
with upstream Rust/Bevy 0.20.1 established a bounded source-to-native
Windows/Linux preview path. The engineering deliverable exists. Human
understanding, gameplay quality, completion, retention, enjoyment, and
cross-device compatibility remain **UNKNOWN**, not PASS.

The original proofs, OS smoke, and dependency work do not justify further
mechanic or infrastructure investment in this low-complexity game. A genuinely
new player/product demand is required to reopen development.

## Immutable public source and distribution

- Exact released source revision:
  1db37d1f0e6aded04c07b12389354bf2f819c71d
- Original release tag:
  game-orbit-collector-linux-preview-20261115-1db37d1f
- Published 2026-11-15:
  https://github.com/ordivon-org/ordivon/releases/tag/game-orbit-collector-linux-preview-20261115-1db37d1f
- Linux orbit-collector-linux-x86_64.tar.gz: 42,327,391 bytes,
  SHA256 ac9d7ce8022a53799e251650c6783b4cf582ab819745ad7fb675b19e2833a788
- Windows orbit-collector-windows-x86_64.zip: 34,861,807 bytes,
  SHA256 2608e976f0b5fcc8be2d42f829d736b0228a67377102f0a7cd09cbdbed943272
- Existing first-play issue:
  https://github.com/ordivon-org/ordivon/issues/2282

The released Windows/Linux archives contain native binaries, play instructions,
source identifiers and upstream dependency licensing notices. The Release tag
and Git history preserve exact original source paths; the archived source below
also remains human-readable in the main repository. Do not delete publicly
distributed files merely to reduce future development work.

## Complete retained inventory

- source/Cargo.toml and source/Cargo.lock: original Rust and Bevy build recipe
- source/src/main.rs: Bevy application and native window entry
- source/src/gameplay.rs: ECS, keyboard, fixed-step movement, hazards, goal
  collection, text HUD, restart and native integration tests
- source/src/rules.rs: independent state machine, native unit test, four Kani
  source proof harnesses
- source/README.md: historical original usage instructions
- source/about.toml and source/about.hbs: upstream cargo-about license recipe
- formal/verify_orbit_rules.py: Z3 model and nine proof obligations
- formal/README.md: bounded formal evidence and limitations
- G07_ARCHIVED.json: historical G07 responsibility and GS4 consumer slice,
  deliberately separate from the active Game capability graph
- legacy-pipeline/package_orbit_linux.sh: original Linux packaging executable
- legacy-pipeline/test_orbit_package_contract.py: original negative cases
- legacy-pipeline/game-orbit-factory.yml: original native Bevy CI workflow
- legacy-pipeline/game-rules-proof.yml: original Kani proof workflow
- legacy-pipeline/original-qualification.md: full historical graphics/native
  acceptance contract and failure boundaries

**Legacy workflow scripts are historical source evidence, not live commands.**
They retain original source-relative paths, so do not run them from the new
archive directory. No new archival build framework is introduced.

## Recover and run original source (explicit opt-in)

Use a disposable Git checkout at the exact public release commit:

    git checkout 1db37d1f0e6aded04c07b12389354bf2f819c71d
    cd domains/game/examples/orbit-collector
    cargo test --locked
    cargo check --locked --all-targets
    cargo run --locked

The build needs native Rust libraries and a supported display/graphics
environment. The old original-path packaging and CI recipes are available at
that source revision. Do not schedule them in routine Game verification.

## Evidence boundary

- Rust and real Bevy ECS tests exercised bounded collection, victory,
  status HUD, restart, and fixed-step scheduling.
- Z3 proved nine properties of its abstract bounded rule model.
- Four Kani proof harnesses on real Rust source were previously verified.
- Linux GitHub Actions observed a native X11/Mesa/Vulkan window and graphics
  adapter; the published Linux archive was compared byte-for-byte with the
  passing CI artifact.
- The public Windows EXE was run in native Windows active-user Session 1; a
  responsive window and native Vulkan GPU initialization were observed.
- These results do **not** establish real Human completion or enjoyment.

## Active dependency and maintenance retirement

- Removed Orbit from the default Game mise verify and factory tasks.
- Moved Orbit-only GitHub Actions workflows out of .github/workflows to
  historical files in this archive; they no longer trigger builds or Kani.
- Removed the retired Cargo directory from active Dependabot paths.
- Moved exact source, proof, build and negative-test material out of the live
  Game source/test paths.
- Removed G07 and its GS4 slice from the active Game LEGO graph without
  reassigning stable identifiers; exact historical fields remain here.
- Preserved all other Game products and their required acceptance work.

**Decision: keep source and the real release; end investment in Orbit as a
product, and use the remaining Game Factory capacity for player-valued games.**
