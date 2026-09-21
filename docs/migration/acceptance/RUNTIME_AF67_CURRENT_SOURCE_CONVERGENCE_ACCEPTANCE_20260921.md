# Runtime current-source convergence acceptance — 2026-09-21

Standing: **ACCEPTED_SOURCE_ONLY**

Scope: source/history convergence of services/runtime from the previously accepted d3613c2e supersession line to af67ed76, which joins the current Runtime product line with the separately accepted monorepo-relocation acceptance fixes. This record accepts source/history under the canonical monorepo path. It does **not** deploy, restart, replace, or retire a Runtime service or source carrier.

## Lineage and source freeze

- Previous canonical source revision: d3613c2e3fb3e298a9c248f6a12ea2e10d1b5692
- Previously accepted migration-line revision: 5d9b44ea514cd49bc9fff370e19d17cf82bb6e42
- Common pre-divergence base: ced757ce077ab6eff1fc05fc5288e649f7e75b4b
- Converged source revision: af67ed760a31813562745412c2553b8297a10e67
- Convergence first parent: d3613c2e3fb3e298a9c248f6a12ea2e10d1b5692
- Convergence second parent: 5d9b44ea514cd49bc9fff370e19d17cf82bb6e42
- Converged source tree: fc7fa5cd029eb19d47b28f76a4aa00bb8762ac49
- Frozen source ref: refs/heads/migration/current-main-convergence-r1-20260921
- Frozen bundle: /root/ordivon-migration-backups/2026-09-21/runtime-current-convergence-af67.bundle
- Bundle SHA-256: f0ac11d4d443d21f425e9951206dd8fc0499af203670911075cddfb946587158

The two source lines changed disjoint path sets relative to their common base and produced a conflict-free merge-tree. The convergence therefore preserves both source identities rather than selecting or replaying one side over the other.

After full source-side acceptance, /root/projects/ordivon-runtime/main advanced by --ff-only from d3613c2e to af67ed76. No source-history rewrite was used.

## Source-side acceptance

The converged source was first validated independently in the isolated source worktree before it became standalone main.

- cargo fmt --check: PASS
- cargo clippy --workspace --all-targets --all-features -- -D warnings: PASS
- Runtime Core all-features: **265 passed, 36 ignored, 0 failed**
- MCP tests: **64 passed, 0 failed**
- auth tests: **10 passed, 0 failed**
- transactional Runtime: **242 passed, 36 ignored, 0 failed**
- operator Python tests: **154 passed**
- documentation contract: PASS
- real systemd integration tests: **36 passed, 0 failed**
- MCP E2E journey: PASS
- final source acceptance: **119 checks, status=passed**
- source acceptance receipt SHA-256: d3b878a0a9f38e9d3c1ce89f5561c06690060ee96aa52d55f49ee8f7af26effb
- durable source receipt: /root/ordivon-migration-backups/2026-09-21-runtime-convergence/source-local-acceptance.json

## Repeatable monorepo update protocol

Before applying this second linear owner update, tools/repo/migration/update-owner-preserve-history.sh was upgraded from a single-update receipt model to an append-only repeatable model.

The compatibility rule is:

- the first historical update retains <id>.update.md and <id>.update.commit-map;
- later updates use <id>.update-<full-source-revision>.md and the corresponding commit map;
- prior update receipts/maps are checksum-verified and must remain byte-identical;
- exact replay of the same later source revision collides deterministically and fails closed;
- a target subtree that does not equal the declared previous source tree still fails closed.

A dedicated regression exercised the first update, a second linear update, old-evidence immutability, exact-replay collision, and owner-tree divergence before the Runtime update used this protocol.

## Canonical monorepo update

The previously accepted Runtime supersession established the canonical owner tree from d3613c2e:

- previous owner tree: c6e6423e097b4534f5ef6d166718788ad8c09536

Because af67ed76 is a descendant of d3613c2e, the next owner change is again an identity-preserving **linear update**, not another supersession.

- Identity-preserving update merge: e93f2e06433d22360eb2785c9f54b924da7393c6
- Update receipt commit: 1936e265870f51c7cd685b0135e5c2c14c0e1bb3
- Accepted target path: services/runtime
- Accepted owner tree: fc7fa5cd029eb19d47b28f76a4aa00bb8762ac49
- Deterministic update receipt: docs/migration/receipts/runtime.update-af67ed760a31813562745412c2553b8297a10e67.md
- Update receipt SHA-256: eac1a0bc607b5689280c1ba4e59c74eeb5dc6310dbe6c7067ae51205dc36e895
- Update commit-map SHA-256: 59e4d6a98e50d3ae81b7f2519acef2e678639d4bf956cd142afe105599c09390

The original import receipt, the legacy first-update receipt, and the d3613c2e supersession receipt remained byte-identical during this update.

## Canonical monorepo-path acceptance

Acceptance was run from the actual owner path:

/root/ordivon-migration-tmp/monorepo-runtime-af67-update-r2/services/runtime

with Git root above services/runtime/.

Validated gates:

- cargo fmt --check: PASS
- cargo clippy --workspace --all-targets --all-features -- -D warnings: PASS
- Runtime Core all-features: **265 passed, 36 ignored, 0 failed**
- MCP tests: **64 passed, 0 failed**
- auth tests: **10 passed, 0 failed**
- transactional Runtime: **242 passed, 36 ignored, 0 failed**
- operator Python tests: **154 passed**
- documentation contract: PASS
- scripts/local-acceptance check: PASS
- real systemd integration tests: **36 passed, 0 failed**
- MCP E2E journey: PASS
- final canonical-path acceptance: **119 checks, status=passed**
- canonical-path acceptance receipt SHA-256: 9142c1d0e4f4e72baf6431bc74fce942ce5d05ebcec36852e5f766a9e7dd48d2
- durable canonical receipt: /root/ordivon-migration-backups/2026-09-21-runtime-convergence/monorepo-local-acceptance-af67.json

The first combined canonical-path command completed all-features validation, then reached the long-running transactional property suite and hit its outer Runtime command deadline. This was an observation-envelope timeout, not a failed test. The remaining gates were rerun as separately bounded commands; transactional, operator/docs, and final local acceptance all completed successfully.

Final canonical acceptance binary identities:

- ordivon-runtime: sha256:6286c246700e9a6922450c0059e9de85facd1032bb5086a84d9e1ea9d615290f
- ordivon-runtime-runner: sha256:bb0dbd6906536cee6bf159079f0169079fc7a12c4ccf1d20bcbfcdce75e21b54

The accepted candidate was reconciled against the then-latest monorepo main. Concurrent main work was confined to Host/control-layer paths; changed-path overlap with this Runtime candidate was empty and the merge-tree was conflict-free. The accepted Runtime candidate was then merged without replacing the concurrent main lineage. The resulting Runtime owner tree remains exactly fc7fa5cd029eb19d47b28f76a4aa00bb8762ac49.

## Production and retirement boundary

**No production cutover was performed by this convergence or monorepo update.**

The earlier d3613c2e acceptance records that its Runtime product line had independently passed its deployment lifecycle. This af67ed76 convergence does not extend that deployment claim to the converged source revision. A deployment of af67ed76 or a descendant requires its own exact candidate manifest, deployment receipt, readiness evidence, and rollback authority.

Standalone /root/projects/ordivon-runtime remains a recoverable source carrier. Retirement or deletion remains a separate gate.
