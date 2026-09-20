# Monorepo import receipt: runtime

- Source repository: /root/projects/ordivon-runtime
- Source revision: ced757ce077ab6eff1fc05fc5288e649f7e75b4b
- Rewritten revision: 291b88bcf4f852f4093b89908f82a9b24d2f6821
- Merge revision: abd00b0facf49bef27355435b54702b8753e8290
- Target path: services/runtime
- Bundle: /root/ordivon-migration-backups/2026-09-20/runtime.bundle
- Bundle SHA-256: d37af0b218e980e6ea277916ce06c798d9d1271bbfc546ca9d799c8d3b3fba6c

## Verified import identity

The rewritten history is path-prefixed: its repository root contains `services/runtime/`.
Therefore the correct owner-tree identity relation is:

- source `ced757ce077ab6eff1fc05fc5288e649f7e75b4b^{tree}` = `0fb1c488e70182c0cf8973af36acffa9baf9f557`
- rewritten `291b88bcf4f852f4093b89908f82a9b24d2f6821:services/runtime` = `0fb1c488e70182c0cf8973af36acffa9baf9f557`
- merge `abd00b0facf49bef27355435b54702b8753e8290:services/runtime` = `0fb1c488e70182c0cf8973af36acffa9baf9f557`

A comparison against `291b88bc...^{tree}` is intentionally false because that tree includes the outer `services/` prefix.

Post-import acceptance on the canonical monorepo path:

- `cargo fmt --check`: PASS
- `cargo clippy --workspace --all-targets --all-features -- -D warnings`: PASS
- `cargo test --workspace --all-targets --all-features`: PASS
- `cargo test -p ordivon-runtime-core --no-default-features --features transactional-runtime`: PASS (241 passed, 36 ignored, 0 failed)
- source/rewritten/merge owner-tree byte identity: PASS
- production cutover: NOT PERFORMED by this source import receipt
