# Harness Browser current-source convergence acceptance — 2026-09-21

Standing: **ACCEPTED_SOURCE_ONLY**

Scope: converge the clean Browser/System-1 research line from the standalone Harness source into the canonical monorepo owner at services/harness while preserving exact standalone commit identity and keeping the separately extracted Skills owner retired from Harness.

This acceptance does not retire /root/projects/ordivon-harness and does not include the later dirty Mind2Web workspace.

## Source identities

- previously accepted shared source baseline: b2823f38d1d46360a4df058fb834b99b2d0b34df
- clean standalone source head: 696674531b7908a15a99e80e16a7d0e2d678a125
- source bundle: /root/ordivon-migration-backups/2026-09-21-harness-browser-convergence/harness-current-main.bundle
- source bundle SHA-256: bf1df880394960951a1c0b1c632f390e0773eb920076abefe4ff64c32c9d439b
- exact source delta manifest: /root/ordivon-migration-backups/2026-09-21-harness-browser-convergence/harness-post-b282-source-delta.tsv
- delta manifest SHA-256: 84eed82490aece442b53f0244ab2018a394d2c4e290ee2f01618d7b9f74ed6b1
- clean post-baseline source delta: 39 paths

The eight source commits after b2823f3 are preserved as their original commit identities:

- efec7944 — system-one decision benchmark
- 7a2b8f16 — Laya cardinality falsification
- a28d47ac — Laya architecture duel
- a0a68cd7 — Browser decision architecture
- e778e455 — semantic freshness witness
- 31ad216a — AX projection experiment
- dc6031cb — AX generalization
- 69667453 — decision-provider benchmark

## Merge semantics

The standalone source and monorepo owner have the exact common ancestor b2823f38d1d46360a4df058fb834b99b2d0b34df.

The accepted convergence commit is:

70163836ed4766c1fec82154806ea1745d262667

Its parents are, in order:

1. 61d76b6c423005e2ac827bd01633cb7c513d9e4b — monorepo parent
2. 696674531b7908a15a99e80e16a7d0e2d678a125 — exact standalone Browser source head

The accepted merge tree is:

f09422de1c4394b1ca3e79ed5cd72ac1537a5db7

Git initially identified eleven file-location conflicts caused by the historical repository-root to services/harness relocation. After bounded resolution, all 39 post-b282 source delta paths exist only below services/harness and are byte-identical to their source blobs at 6966745.

No source-delta copy remains at the monorepo root.

## Extracted owner non-resurrection

The convergence deliberately does not restore the historical Harness-owned Skills implementation.

The following remain absent from services/harness:

- src/ordivon_harness/skills
- scripts/skills_mcp.py
- scripts/skills_mcp_consumer_readiness.py
- systemd/ordivon-skills-mcp.service
- plugins/ordivon-skills-bridge
- historical Skills MCP R2/R3 tests

The canonical Skills owner remains platform/skills.

Monorepo-specific Harness state also remains present, including the post-Skills extraction evidence, Security owner locator regression, owner-local mise configuration, and canonical Security path bindings.

## Acceptance

Focused Browser/System-1 gate:

- Ruff: PASS
- compileall: PASS
- focused tests: 36 passed

Full canonical services/harness owner verification:

- Python profile: 3.14.7
- complete pytest: 877 passed
- subtests: 122 passed
- dependency contract: PASS
- documentation contract: PASS
- evidence contract: PASS
- historical evidence receipts: 90
- verified current receipt: 1
- deterministic demo: PASS
- pip-audit: no known vulnerabilities
- wheel build: PASS
- wheel public/installed contract: PASS
- host-free Harness verification: PASS
- final tree after verification: f09422de1c4394b1ca3e79ed5cd72ac1537a5db7

## Remaining boundary

The standalone Harness repository remains active as a temporary carrier because Runtime still has standalone-sourced workspaces. In particular, ws-browser-mind2web-adapter-r1-20260921 contains dirty Mind2Web research work based on 6966745 and must be losslessly migrated before standalone retirement can be evaluated.

Two older dirty workspaces also require explicit disposition:

- ws-harness-current-monorepo-readiness-r1-20260921 — readiness log/return-code residual
- ws-harness-bridge-reduction-r2-20260920 — pre-extraction Skills bridge reduction WIP, now superseded in ownership terms but not yet discarded without recovery evidence

Therefore this record accepts source convergence only. It does not authorize physical retirement of /root/projects/ordivon-harness.
