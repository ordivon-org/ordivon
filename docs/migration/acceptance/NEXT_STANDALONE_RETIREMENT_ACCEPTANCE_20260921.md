# Next standalone source-carrier retirement acceptance — 2026-09-21

Standing: **RETIRED_ARCHIVED**

Scope: retire the standalone Next source carrier at /root/projects/ordivon-next after identity-preserving current-source supersession into the modular monorepo, current Skill path cutover, live Skills MCP readback, recovery preservation of the divergent Chaoxing MVP work, Runtime drainage, and post-delete owner verification.

This retirement removes only the legacy source carrier. It does not retire the Next capability set, the canonical meta/next owner, the Skills MCP service, or the preserved Chaoxing research lineage.

## Legacy and canonical identities

Legacy standalone identity at retirement:

- path: /root/projects/ordivon-next
- HEAD: 5e556869df0617a7da09e39ae57f646f11061689
- tree: d29ac5ff648efa790613023344fca64f12ce4ad3
- tracked state: clean
- final physical Git worktrees: one, the standalone root itself

Canonical owner:

- source root: /root/projects/ordivon/meta/next
- monorepo head observed by the physical-retirement transaction: e169c7c92f5231c80461725d5753e7e9a2873185
- meta/next tree at that boundary: ca0ee9970039e71647442c4a9effb1f3f99aea10

Earlier migration acceptance established exact current-source supersession of 5e556869 into the monorepo. The canonical owner subsequently evolved forward. Retirement therefore removes an obsolete carrier, not current Next development.

## Final current-path cutover

A final semantic-reference census found one remaining current consumer of the standalone path: the web-provider-routing Agent Skill.

Five executable examples in the Skill still invoked /root/projects/ordivon-next/scripts/web_interaction_route.py. They were moved to /root/projects/ordivon/meta/next/scripts/web_interaction_route.py.

A regression now requires exactly five canonical route references and zero retired route references.

Cutover commit:

7373914976efe37d44d1877986ef9a565a11e479

Verification on the current monorepo owner included the complete meta/next mise verify path:

- lock check and owner environment synchronization: PASS
- pytest: PASS
- Ruff check and format check: PASS
- Authority Catalog checks: PASS
- Standard-Native enterprise checks: PASS
- Reasoning Waist checks: PASS
- Bandit: PASS
- pip-audit: no known vulnerabilities

The full owner verify was repeated after the standalone directory was physically absent and passed again.

## Live Skills MCP consumer proof

The live Skills MCP configuration already bound project identity ordivon-next to /root/projects/ordivon/meta/next. The standalone path was not present in the active configuration. Historical backup configuration files remain historical evidence only.

Before deletion, a real loopback MCP sequence executed against the live service:

skills.search -> skills.resolve -> skills.read

for project-ordivon-next/web-provider-routing.

The readback proved:

- canonical web_interaction_route.py path occurrences: 5
- retired standalone path occurrences: 0
- instruction digest: sha256:114af02d670baf4d6a93303bd5126706a944ab15fff96e643d25c4f7a8ea02ef
- package revision: sha256:d4edb1948e103832ca94d2d0b09a4680490e59693eb9930894707a4c599fa364
- snapshot revision: sha256:6cb7e8aa0b2525261f0d26b23436e26f3c83cfa42adaa8e10cc46aac497412e9

Pre-delete live readback receipt SHA-256:

160ff196686e1b964617caaee80d3a1c030037827d4e55ab427499be15d7eeac

After physical deletion, the same search/resolve/read path passed again with five canonical path occurrences and zero retired path occurrences.

Post-delete live readback receipt SHA-256:

fc290cd49fef552279aa6883b2628b563d6c9a57e16487146095663c21d4b83f

The Skills MCP process remained active at PID 1517315 across retirement. No restart was required.

## Divergent Chaoxing MVP recovery

The final Runtime workspace sourced from the standalone Next repository was ws-chaoxing-mvp-r1-20260917.

It was dirty and therefore was not discarded as cache.

Its line of development diverged from Next main. The workspace head ce5e54898bbd4bb74435c3038c960417427ea3ae contains a Chaoxing autosign assistant MVP lineage that never entered Next main. Its dirty state additionally contained one untracked TDD contract test for a future HTTP adapter.

The untracked test currently represents an expected RED frontier: EXPECTED_RED_UNIMPLEMENTED_HTTP_ADAPTER.

The missing capability is chaoxing_mvp.chaoxing_http.encrypt_login_field. The preserved recovery state does not authorize presence-proof bypass or external submission; the existing MVP safety boundary remains part of the recovery record.

Before closing the workspace, the divergent lineage was elevated to:

refs/ordivon/recovery/chaoxing-mvp-r1-20260917

After exact sourceStateDigest compare-and-close, Runtime added:

refs/ordivon/closed/ws-chaoxing-mvp-r1-20260917

Both refs point exactly to ce5e54898bbd4bb74435c3038c960417427ea3ae.

The recovery capsule preserves the base/head identity, exact dirty status, tracked patch, untracked bytes, ignored paths, expected RED output, frontier metadata, and safety boundary.

Capsule manifest SHA-256:

2d7ae5dfde0ce2e432b6cfe543b148168da6c78b29a848b129524145c005645e

The untracked HTTP-adapter test SHA-256 is:

9a09a1b905dcb93572e5e356ec113e03c8248d58573904fe72787db2f8f9c494

Before and after physical Next deletion, the capsule was replayed from the Git bundle and reproduced the exact Git status and untracked test bytes.

## Complete Git preservation

Final all-refs bundle:

/root/ordivon-migration-backups/2026-09-21-next-retirement/next-all-refs.bundle

SHA-256:

1010d705a7c9e03f80e18841ff6981ece0d4a8d82f192b10e5073497208855ea

Final ordinary refs manifest:

/root/ordivon-migration-backups/2026-09-21-next-retirement/next-all-git-refs.tsv

SHA-256:

1ab3d088a7938481ed2a57f2eaacfbb6306da3f8ff2624ace949c036f1b4a55f

Ordinary Git refs recorded: 432.

The archive was refreshed after the final Runtime workspace close so the Runtime-generated closed ref was included.

Before deletion:

- ordinary refs missing from bundle: 0
- ordinary ref digest mismatches: 0
- Chaoxing recovery ref exact: PASS
- Chaoxing Runtime closed ref exact: PASS

After physical deletion, the bundle was cloned into a new mirror repository and all 432 refs were resolved again with missing=0 and mismatch=0.

## Runtime and physical retirement gates

Immediately before physical removal:

- Runtime workspaces sourced from /root/projects/ordivon-next: 0
- external linked Git worktrees: 0
- process cwd/exe/fd references: 0
- systemd references: 0
- active Skills config old-root references: 0
- current operational source references in Skills/scripts/authority/package surfaces: 0
- tracked standalone status: clean
- ignored entries: 18,522
- ignored non-cache files: 0

The ignored standalone state consisted of rebuildable virtual-environment, bytecode, pytest, Ruff and import-linter cache material.

A tracked literal-reference census retained 17 old-root references in historical migration evidence, frozen plans, dated Atlas source snapshots, historical evidence and negative regression assertions. They are not current operational bindings and were deliberately not rewritten.

## Physical-retirement receipts

Pre-delete receipt:

/root/ordivon-migration-backups/2026-09-21-next-retirement/next-physical-retirement.json

SHA-256:

ca5ba611a6b84ae6eb16ab7ecc59d0097b8bb4ab776f89e1dad5a45e32275904

Post-delete proof:

/root/ordivon-migration-backups/2026-09-21-next-retirement/next-post-retirement-proof.json

SHA-256:

9b403a0ab95ad9fd1ef8a0351895ecb145a2c354951ed3a287fe70d800b97973

## Post-delete functional proof

With /root/projects/ordivon-next physically absent:

- Runtime Next workspace count: 0
- canonical meta/next full mise verify: PASS
- live Skills MCP: active
- Skills MCP PID remained 1517315
- service restart required: no
- live web-provider-routing search/resolve/read: PASS
- canonical route occurrences: 5
- retired route occurrences: 0
- final Git restore: 432 refs, missing=0, mismatch=0
- Chaoxing divergent recovery replay: exact status and untracked test bytes
- canonical source root remained /root/projects/ordivon/meta/next

## Disposition

- active Next source owner: /root/projects/ordivon/meta/next
- legacy standalone Next path: physically absent
- compatibility alias at the old path: NONE
- standalone Git history: archived and restore-proven
- divergent Chaoxing MVP lineage: archived and replay-proven as a separate recovery lineage
- live Skills consumer: canonical and healthy
- production service restart from this retirement: NONE
- provider mutation from this retirement: NONE

If historical Next source or Chaoxing WIP must be recovered, materialize it from the recorded bundle/capsule into a bounded recovery path. Do not recreate /root/projects/ordivon-next as a compatibility alias.


## Post-retirement canonicalization of the recovered Chaoxing lineage

After the standalone source carrier had already been retired, the preserved Chaoxing recovery lineage was re-evaluated against the canonical monorepo.

The recovery evidence had two distinct parts:

1. five committed MVP commits ending at `ce5e54898bbd4bb74435c3038c960417427ea3ae`;
2. one untracked future TDD contract, `tests/test_chaoxing_http_adapter.py`, whose frontier remains `EXPECTED_RED_UNIMPLEMENTED_HTTP_ADAPTER`.

The committed branch patch from the restore-proven capsule applied cleanly under canonical `meta/next`. Before any normalization, the recovered implementation and plan/test files were compared against the restored recovery head. The Chaoxing implementation files under `experiments/chaoxing-autosign-mvp/**` matched byte-for-byte.

The historical test harness did not initially satisfy the current monorepo Ruff gates. Only the test harness was normalized:

- two unused imports were removed;
- the experiment-local package-path injection was made explicit for Ruff;
- Ruff import ordering and formatting were applied.

The experiment implementation bytes were not changed by that normalization.

The recovered committed MVP then passed:

- Chaoxing MVP unit tests: **11/11 PASS**;
- Ruff check: PASS;
- Ruff format check: PASS;
- full canonical `next:verify`: PASS;
- full Next pytest surface observed by the owner gate: **121 passed**;
- dependency vulnerability scan: no known vulnerabilities.

The recovered committed lineage entered canonical main as:

`e9b93799a353b48767d0d1996212e9a0f1510c8a`

Canonical owner location:

`meta/next/experiments/chaoxing-autosign-mvp`

The untracked HTTP-adapter TDD contract was deliberately **not** imported into the executable canonical test suite because its required module remains unimplemented. It remains preserved in the recovery capsule with exact status and byte-level restore proof.

The prior 432-ref retirement archive remains authoritative for reconstructing the historical standalone repository and the original recovery refs. Canonicalization of the recovered MVP does not rewrite or replace that archive.

## Archived-source reference fence

After post-retirement canonicalization, a dedicated archived-source policy was added for the locator:

`/root/projects/ordivon-next`

Allowed references are limited to explicit historical migration records, frozen creation-time topology/evidence/planning snapshots, and two negative regression tests that assert the retired locator is not used by current consumers.

Current operational namespaces under Next/Skills contain zero references to the retired source path. Any future current source, script, Skill, package metadata, or service binding that reintroduces the old locator must fail the repository retirement gate.
