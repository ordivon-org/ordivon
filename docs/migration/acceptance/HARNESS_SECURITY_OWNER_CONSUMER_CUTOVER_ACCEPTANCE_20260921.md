# Harness → Security owner consumer cutover acceptance — 2026-09-21

Standing: **ACCEPTED_SOURCE_ONLY**

Scope: move Harness Browser Security consumers from the retired-location candidate /root/projects/ordivon-security-v2 to the canonical Security owner at /root/projects/ordivon/platform/security, while preserving the semantics of Security revision binding after the Security owner became a monorepo subtree.

This acceptance does not deploy a new Browserless image, mutate provider state, restart production services, cross provider SEND, or physically retire the standalone Security source carrier.

## Why this cutover was required

The standalone Security repository had already been imported and identity-bridged under platform/security. Later monorepo-native Security work added Agent Admission and delegated resource-server laboratory surfaces, so the standalone f5db8508... checkout ceased to represent current Security owner state.

Four executable Harness consumers still resolved Browser Security implementation and fixtures from the standalone location:

- scripts/agent_automation_release.py
- scripts/browser_security_browserless_canary.py
- scripts/browser_security_pool_runner.py
- scripts/browserless_image_promotion.py

The old path was therefore a real runtime/source dependency, not merely provenance.

## Locator and identity contract

The accepted default locator is:

/root/projects/ordivon/platform/security

Harness permits an explicit ORDIVON_SECURITY_ROOT override for bounded alternate/test roots.

A monorepo subtree cannot use repository HEAD as owner revision without conflating unrelated owner changes. The accepted Git-native owner revision is therefore:

git -C <security-owner-root> log -1 --format=%H -- .

Properties covered by regression:

- in a standalone owner repository the result is the owner HEAD;
- in a monorepo owner subtree an unrelated repository commit does not advance the Security revision;
- Security-local changes do advance the revision;
- promotion cleanliness is scoped to the Security subtree;
- unrelated monorepo working-tree dirt does not contaminate Security standing;
- Security-local working-tree dirt still fails closed.

No new owner-identity database, marker registry, or Security-specific revision service was introduced.

## Validated donor

The change was first implemented and validated on an isolated Harness source-carrier branch based on:

- standalone Harness base: b2823f38d1d46360a4df058fb834b99b2d0b34df
- donor commit: d003dea31fcea89f9a13c821164d04d4a87a2b7d
- donor tree: 68681b9654597790a3e665f979108e956468cfff
- donor bundle: /root/ordivon-migration-backups/2026-09-21-harness-security-cutover/harness-security-root-cutover-donor.bundle
- donor bundle SHA-256: 8f853756806532a0477f7510c66eef435891f3089e0b2fb26e0c0362d752791a

The standalone Harness main was deliberately **not** advanced to the donor. During validation, canonical Harness had already evolved independently in the monorepo through Skills-owner extraction. Treating the old standalone repository as current Harness authority would have discarded that forward work.

Source-carrier validation:

- targeted Browser Security / release regression: **71 tests PASS**
- Ruff targeted gate: PASS
- full deterministic suite: **922 tests + 156 subtests PASS**
- dependency contract: PASS
- documentation contract: PASS
- evidence contract: PASS
- deterministic demo: PASS
- wheel build / isolated wheel verification: PASS
- owner scripts/local-acceptance run: PASS, including bounded P0 scale smoke
- old standalone Security locator in the changed live Harness scope: 0

## Canonical composition

Canonical Harness had independently removed/extracted Skills ownership. The changed paths from that work and the six-path Security cutover had zero overlap.

The validated donor delta was therefore replayed byte-for-byte onto the then-current monorepo Harness owner without reverting Skills extraction. Every applied path matched the donor blob OID.

To preserve both histories, the accepted composition commit has two parents:

- current monorepo parent: 60ed225ba271e21127a89a5a3b870f05ce2ff568
- validated donor parent: d003dea31fcea89f9a13c821164d04d4a87a2b7d
- composed commit: 0fe2187bce45b6bbed6c5f5eb47c6aae168ccfc8
- resulting services/harness tree: 47f7b476b74b8578da715310375a4094403d80db

Canonical-path validation after Skills extraction:

- targeted Browser Security / release regression: **71 tests PASS**
- full owner scripts/local-acceptance run: PASS
- deterministic suite: **841 tests + 122 subtests PASS**
- dependency contract: PASS (test=agent-mcp+playwright+pytest)
- documentation contract: PASS
- evidence contract: PASS
- bounded P0 scale smoke: PASS
- deterministic demo: PASS
- wheel build / isolated wheel verification: PASS
- old standalone Security locator in Harness live scripts/tests/current Browser Security doc: 0

The reduced test count relative to the standalone donor is the expected consequence of Skills having become a separate owner; it is not a test regression.

## Main integration and concurrency

Before final integration, monorepo main had concurrently accepted workstation-lab retirement-in-place work. The changed paths had zero overlap with this Harness cutover and the merge-tree was conflict-free.

The composed Harness candidate was merged without replacing the concurrent main lineage:

- integration merge: a1a5f22ef45d409b6aa2583e459e217de2f924ea
- resulting services/harness tree: 47f7b476b74b8578da715310375a4094403d80db
- validated donor d003dea... remains reachable in monorepo ancestry.

## Security retirement boundary

This cutover removes the last known executable Harness dependency on /root/projects/ordivon-security-v2, but it is not itself physical retirement authorization.

Standalone Security may be physically retired only after a fresh bounded census proves:

- zero Runtime Workspaces rooted in the old repository;
- zero linked Git worktrees that require its .git storage;
- zero process cwd/exe/fd references;
- zero systemd/config executable bindings;
- zero live executable/source locators outside historical/provenance records;
- clean old source carrier;
- complete verified all-refs archive / recovery evidence.

The already-created full Security archive is:

/root/ordivon-migration-backups/2026-09-21-security-retirement/security-v2-all-refs.bundle

with SHA-256:

e7bc98b64d42f1f724f4710a44a0e787ead48f93cd583b72139feccaf799bc70

No production or provider mutation is implied by this source cutover.
