# Runtime current-source supersession acceptance — 2026-09-21

Standing: **ACCEPTED_SOURCE_ONLY**

Scope: identity-preserving source/history supersession of `services/runtime` from the previously accepted migration line to the current repaired and production-accepted standalone Runtime source. This record does not perform or authorize another production deployment; production Runtime lifecycle remains governed by Runtime deployment receipts and service authority.

## Frozen identities

- Previous accepted source revision: `5d9b44ea514cd49bc9fff370e19d17cf82bb6e42`
- Current source revision: `d3613c2e3fb3e298a9c248f6a12ea2e10d1b5692`
- Common base: `ced757ce077ab6eff1fc05fc5288e649f7e75b4b`
- Identity-preserving supersession commit: `3fc3dd59141594c0f454cd31b07e5d14b9d14b8c`
- Frozen bundle: `/root/ordivon-migration-backups/2026-09-21-runtime-current/runtime.bundle`
- Bundle SHA-256: `a4291aa7bbf4ace1e96c1ccbf8d861a437afdbc3dc54d5520dcf9225e922eb45`
- Current source tree: `c6e6423e097b4534f5ef6d166718788ad8c09536`
- Accepted `services/runtime` tree: `c6e6423e097b4534f5ef6d166718788ad8c09536`

The previous source and current source diverge after `ced757ce077ab6eff1fc05fc5288e649f7e75b4b`; therefore the tested supersession path was used rather than the linear update path. Both source identities remain reachable in the monorepo DAG.

## Canonical monorepo-path acceptance

Executed from `services/runtime/`, with the Git root at the Ordivon modular monorepo:

- `cargo fmt --check` — PASS
- `cargo clippy --workspace --all-targets --all-features -- -D warnings` — PASS
- `cargo test --workspace --all-targets --all-features` — PASS
  - Runtime Core all-features: **265 passed, 36 ignored, 0 failed**
  - MCP: **64 passed, 0 failed**
  - auth: **10 passed, 0 failed**
  - platform-owner boundary tests: PASS
  - systemd supervisor tests remain explicit local opt-in and were ignored by the ordinary source-only suite
- transactional Runtime without default features: **242 passed, 36 ignored, 0 failed**
- Python operator tests: **154 passed**

The first Python operator-suite invocation intentionally used an external Cargo target directory without an inspector binding and failed closed because `ordivon-runtime-cache` could not discover `ordivon-runtime-inspect`. No source defect was inferred from that environment mismatch. The suite was then rerun with:

`ORDIVON_RUNTIME_INSPECT=/var/tmp/ordivon-runtime-monorepo-d361/debug/ordivon-runtime-inspect`

where the bound inspector was built from the same accepted `services/runtime` source. All 154 operator tests passed.

This establishes an explicit monorepo portability rule: Runtime operator tools must receive their executable dependencies through their documented binding mechanisms; acceptance must not depend on standalone-repository sibling-path accidents.

## Production boundary

The current production Runtime had already been independently deployed and closed under the Runtime deployment authority before this source supersession. This monorepo acceptance neither restarts the service nor creates a deployment authorization. It only accepts the exact current source/history under `services/runtime`.

Standalone `/root/projects/ordivon-runtime` remains a recoverable source carrier until a separate retirement gate is accepted.
