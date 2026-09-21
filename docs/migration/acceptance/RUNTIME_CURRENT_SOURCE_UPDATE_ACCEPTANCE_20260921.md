# Runtime Current-Source Update Acceptance — 2026-09-21

Standing: **ACCEPTED_SOURCE_ONLY**

Scope: identity-preserving linear source update of services/runtime. This record accepts the Runtime source under the canonical monorepo path. It does **not** authorize production cutover, service replacement, credential migration, deletion of /root/projects/ordivon-runtime, or retirement of any rollback/recovery authority.

## Source freeze

- Source repository: /root/projects/ordivon-runtime
- Previous imported source revision: ced757ce077ab6eff1fc05fc5288e649f7e75b4b
- Accepted source revision: 5d9b44ea514cd49bc9fff370e19d17cf82bb6e42
- Source ref in frozen bundle: refs/heads/migration/monorepo-integration-source-r1-20260921
- Frozen bundle: /root/ordivon-migration-backups/2026-09-20/runtime-monorepo-integration-source-r1.bundle
- Bundle SHA-256: 38492c8c3fb08ba2d8707f4ed9dc012d637d422d12e50295e42e1c2c6908c60b
- Identity-preserving update merge: 6002eb21c2aab9cdb128206fc9bac59d0f1d7a6e
- Update receipt commit accepted on monorepo main: 48dd329768c3bcac0700c51d7850571e888c1179
- Target path: services/runtime
- Previous source tree: 0fb1c488e70182c0cf8973af36acffa9baf9f557
- Accepted source tree: c790c13fb61a30c6ee61e7935ee6d8d9fa641162

The accepted source is a linear descendant of the previously imported source. Therefore this migration used the identity-preserving **update** path, not supersession.

## Source-side acceptance

Before monorepo update, the accepted source revision was validated independently.

- cargo fmt --check: PASS
- cargo clippy --workspace --all-targets --all-features -- -D warnings: PASS
- all-features core: **264 passed, 36 ignored, 0 failed**
- MCP tests: **63 passed, 0 failed**
- auth tests: **10 passed, 0 failed**
- transactional Runtime: **241 passed, 36 ignored, 0 failed**
- operational Python tests: **152 passed**
- systemd integration tests: **36 passed**
- final scripts/local-acceptance run: **PASS**
- final source acceptance checks: **119**
- source acceptance receipt SHA-256: cfd8dbdb8c10fe6dfc0b4dab259e7f1d94ce31b80c18fe1789b3f5ffd2392438

The source-side acceptance fixed two acceptance-harness assumptions without changing Runtime execution or reconciliation semantics:

1. integration fixtures now create their own minimal Git source authority instead of depending on repository-root placement;
2. MCP E2E acceptance now follows the advertised optional Windows target contract and the current mutation journey state.

## Canonical monorepo-path acceptance

Acceptance then ran again from the actual owner path:

/root/ordivon-migration-tmp/monorepo-runtime-update-r1/services/runtime

Git semantics observed by the tests:

- repository root: /root/ordivon-migration-tmp/monorepo-runtime-update-r1
- owner prefix: services/runtime/
- accepted monorepo commit: 48dd329768c3bcac0700c51d7850571e888c1179
- root-level Cargo.toml: absent
- owner services/runtime/Cargo.toml: present
- owner services/runtime/Cargo.lock: present

Canonical-path gates:

- cargo fmt --check: PASS
- cargo clippy --workspace --all-targets --all-features -- -D warnings: PASS
- all-features core: **264 passed, 36 ignored, 0 failed**
- MCP tests: **63 passed, 0 failed**
- auth tests: **10 passed, 0 failed**
- transactional Runtime: **241 passed, 36 ignored, 0 failed**
- operational Python tests: **152 passed**
- documentation contract: PASS
- scripts/local-acceptance check: PASS
- real systemd integration tests: **36 passed, 0 failed**
- MCP E2E journey: PASS
- final canonical-path acceptance: **119 checks, status=passed**
- canonical-path acceptance receipt SHA-256: 8adc2ecd56a3a02ffdae2f38d6f8ab463a7cdcb47f1b2d6befe11f1a6b6348d2

Candidate binary identities from the canonical-path receipt:

- ordivon-runtime: sha256:74832e5c775ae9d3623b1754c8c542136cc4085169f8e5f358f500e0412ecee9
- ordivon-runtime-runner: sha256:895fd87435bedbc789d62c2c30d30b147452c1e38b1b0f2bbb0447efd3d23f13

## Identity-preserving migration evidence

The update used tools/repo/migration/update-owner-preserve-history.sh.

Verified properties:

- original runtime.md and runtime.commit-map remain retained;
- runtime.update.md and runtime.update.commit-map record the append-only update;
- services/runtime at the accepted monorepo commit equals the accepted source tree byte-for-byte;
- source revision 5d9b44ea... is retained as a parent-side ancestor in monorepo history;
- previous source revision ced757ce... remains in history;
- the physical monorepo main advanced from dc1aa5d0... to 48dd3297... by --ff-only;
- the fast-forward occurred only after canonical-path acceptance completed;
- no production cutover was performed by this migration.

## Production boundary

**Production cutover remains NOT PERFORMED by this source acceptance.**

The deployed Runtime, its service lifecycle, deployment receipt authority, rollback state, credentials, and external release effects remain separate operational concerns. A future production cutover must bind its own exact candidate manifest, deployment receipt, readiness evidence, and rollback boundary; this source acceptance must not be interpreted as that authorization.
