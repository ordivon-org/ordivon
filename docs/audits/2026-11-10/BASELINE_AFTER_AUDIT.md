# Baseline after the bounded brownfield audit

**Census SourceCut:** ef17d6879d12faa61fff3bb762b0d500d73c9113.
**Method:** existing 21 natural Owner manifest plus per-byte scan of 5,002 source files. Inventory and criteria were written only for this dated audit; their conclusions are not a new registry, policy authority or durable production observation.
**Audit status:** P0/complete source scoping; P1/complete mechanical file census, **not** 5,002 semantic judgments; P2/focused owner and file-level findings; P3/stock-only execution plan; P4/two verified Web existing-code maintenance changes in companion Web source PR #2019; P5/a bounded **post-change source baseline**, not entire system installed acceptance.

## What actually changed in the two independently reviewable stock-only deliveries

- Retired one redundant SHA-256 JSON digest implementation from apps/web/src/agent-authority.ts, reusing the already-present stableDigest from apps/web/src/identity-digests.ts at the **two existing** apps/web/src/app.ts effect sites. No effect or public route added; exact digest prefix, JSON serialization and identity preserved.
- Corrected apps/web/src/config.ts positive-integer environment parsing: Number.parseInt previously silently mapped the malformed ORDIVON_WEB_PORT=8080garbage to 8080. It now rejects nondigit forms, still accepts normal positive decimal integers and checks safe integer bounds. No feature or test file added. It is an existing contract repair, not a new option.
- Created the explicitly requested dated audit artifacts: AUDIT_SCOPE.md, MODERN_CRITERIA.md, INVENTORY.md (complete 5,002-file path/digest/size source list), AUDIT_REPORT.md and REFACTOR_PLAN.md. They must not be mistaken for independently verified behavior or an additional Owner execution framework.

## Real verification evidence

- Frozen source pre-edit: tools/repo/check_owner_boundaries.py **PASS**, with 2,320 active files, 10 packages, 31 declared seams, 38 references; tools/repo/check_architecture_docs.py **PASS**.
- Web negative observation **before** fix: ORDIVON_WEB_PORT=8080garbage produced port=8080. **After** fix: 8080garbage, 1.2 and 1e3 REJECTED; 8080 accepted as 8080.
- Digest identity before deletion: stableEffectDigest(sample) == stableDigest(sample) was observed true. After deletion: stableDigest(sample) equals Node crypto SHA-256(JSON.stringify(sample)) including sha256: prefix.
- Web owner native **mise run web:verify PASS**: frozen pnpm installation, TypeScript tsc --noEmit PASS and existing Node owner test suite 18/18 PASS, 0 failed, 0 skipped. This is a local source/contract check, not live deployment proof.
- No new tests, consumer endpoints, features, schema migrations, runtime services or cross-owner relationships were created.
- GitHub review, merge/CI/installed source and domain acceptance are separate standings; this branch's GitHub outcome must be read from its actual current PR after publication.

## Known not-yet-closed obligations

- PR #2006, #2010 and later #2013/#2014 affect the same Owner programme and Agent Spec. Their authors must converge the current carrier and retire the obsolete 220-line Agent outcome plan without an additional duplicate document.
- PR #2017 (Chaoxing demo), #2015 (Harness stale runners), #2008 (Workstation Host-v1 projector), #2007 (Distribution evidence), #2012 (Repo mechanics), #2011 (Skills), #2016 (Host plans) are natural Owner work; current review does not claim they are merged or installed.
- The full semantically inspected set is **smaller** than the 5,002 mechanically inventoried files. Per-Owner installed/mutable-state readback, dynamic edge closure and individual source-exact business outcomes remain scoped UNKNOWN outside the changed Web source.
- Nx/Turborepo patterns were compared as boundary principles. Root already has a cross-language owner checker; replacing its environment with Nx/Turbo was **not** justified. Likewise no always-on ECC hook manager or new formal R2.1 checker was built.

## Rollback, retention, and follow-up

Both PR source changes are independently Git-revertible. Revert the specific changed Web files if regression is observed; do not restore duplicate digest logic as a second authority merely for temporary familiarity. Audit snapshots may be retired from current main once their bounded research consumer is satisfied; Git retains evidence. Do not promote this dated baseline to a live operational status page.


## Source-convergence follow-up — 2026-11-10

At Git main e037af933b66cdfccc7e13e3e6392847e7f84fc8, original [Web PR #2019](https://github.com/ordivon-org/ordivon/pull/2019), original [root inventory PR #2021](https://github.com/ordivon-org/ordivon/pull/2021), root [PR #2033](https://github.com/ordivon-org/ordivon/pull/2033), Capital [PR #2040](https://github.com/ordivon-org/ordivon/pull/2040), and Runtime [PR #2028](https://github.com/ordivon-org/ordivon/pull/2028) were independently read back as MERGED. Their old reports describing these PRs as OPEN are dated observations, not live truth.

The prior duplicate candidate [Web PR #2036](https://github.com/ordivon-org/ordivon/pull/2036) was CLOSED unmerged because the actual Web code fixes were already present on main and its seven additional reports would duplicate this audit set. The custom Network Circuit/formal pilot [PR #1982](https://github.com/ordivon-org/ordivon/pull/1982) was CLOSED unmerged because it adds tests, CI/formal machinery without a current native Network consumer, outside the stock-only scope. Neither close reverts any installed system effect.

Three additional merged report/ledger directories were consolidated into the original six report names here, deleting redundant current copies while leaving exact historical Git records and naturally owned code fixes intact. Old Runtime and Capital Markdown references were updated to this report set. This is a SOURCE-only documentation maintenance change, with existing repo architecture checks required; no product features, tests, runtime, database, or consumer interfaces were added. The original frozen inventory still contains exactly 5,002 distinct Git paths and is not a semantic review of each file.
