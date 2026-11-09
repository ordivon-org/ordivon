# BASELINE_AFTER_AUDIT — stock-only source audit (2026-11-10)

## Identity and coverage
- Starting Git SourceCut: ef17d6879d12faa61fff3bb762b0d500d73c9113.
- Mechanically read and SHA256-hashed 5,002/5,002 tracked files (123,199,041 bytes). Original per-file path, Owner, size, lines, SHA256 and source kind are in INVENTORY_FILES.tsv, sha256 424a029a9df32a48425e03715350b7e49ba7abbb98264f5010ad011129a130fe.
- Parsed 1,460 Python AST, 1,315 JSON and 50 TOML with zero parse failures. This is mechanical coverage, NOT 5,002 separate semantic reviews.
- tools/repo/owners.toml schema_version=1 lists 21 natural Owners and source regions. Meaningful per-file semantic review focused on all 35 original apps/web tracked files, including its 16 TS source files. Other 20 Owner semantic reviews remain independent/ongoing; no claim of completion.

## Actual existing-code correction
- apps/web/src/config.ts: replace file URL .pathname (percent-encoded) with native Node fileURLToPath(new URL(...)) for SQLite default path; Node native probe confirms a folder containing spaces would otherwise be incorrectly encoded.
- apps/web/src/config.ts: replace permissive parseInt with explicit ASCII decimal literal guard, then Number and existing safe-positive integer checks. Independent peer pointed out Number alone also accepts scientific notation/whitespace; final patch excludes those.
- No new feature, tests, consumers, schemas, dependencies, hook systems, product routes or foreign framework. Web canary SQLite, existing Security contract and WebStore transaction authority unchanged.

## Current native verification
- Original Web owner native mise run verify: TypeScript and 18/18 existing Node tests PASS, zero skipped.
- Final patched Web owner native mise run verify: TypeScript and 18/18 existing Node tests PASS, zero skipped.
- Final actual loadConfig() native Node 26 probe: valid 8789 and 0012 ACCEPT, malformed 8789evil, 1e2, whitespace-wrapped 123, 0, -1, empty string REJECT; 8/8 expected. Native path resolution equals fileURLToPath. This probe produced no new test file.
- Broader repo:ci on an earlier, pre-final candidate passed owner boundary/architecture/SQL checks and 533 repository tests, but remained active afterward. Cancellation intent was requested and not yet confirmed terminal. This is NOT full repo:ci PASS and not final version qualification. Targeted root checks and GitHub checks must be read independently.

## Cross-agent peer, retained boundaries, residual concerns
- Existing Host capability forum Space cleanup Topic: Phase P0/P1 handoff seq25958; source/owner correction seq25970; targeted counterexample request seq25963; independent peer seq25982; acceptance of critique seq25983.
- Retain apps/web/planning/lego-plan-r1.json: tools/repo/check_architecture_docs.py:227 is a real consumer. Do not delete by name or age.
- Do not edit root docs/architecture/OWNER_MODULARITY_STRUCTURE_LIFECYCLE_PROGRAM_R1.md: historical 20 Owners and Host schema 11 conflict with current source 21 owners and Host required schema 13, but parallel PRs #2006/#2010/#2013 own consolidation. Do not erase legitimate historical deployment account.
- apps/web/src/agent-authority.ts:37-72 invokes synchronous Python Security evaluator from Web request flow; this may block Node event loop. Evidence is source only, not a confirmed production incident. Deferred for consumer-qualified bounded repair instead of new speculative async tests in this stock-only batch.

## Standing, rollback, remaining scope
- The existing-code fix is a SOURCE candidate; merged/installed/production consumer qualification is not claimed by this document. Check GitHub PR and owner-native installed source separately.
- Change is reversible through git revert of published source commit; immutable base Git SourceCut retains original bytes and file inventory. No OS/PG/Web production state was changed.
- Full monorepo mechanical inventory COMPLETE. Web source/contract scrutiny and smallest stock-only repair COMPLETE. Independent semantic deep review and change convergence for all 21 Owners: NOT COMPLETE in this one Owner branch. Related Owner PRs have separate source and status.

Decision: ACCEPT native config correctness fix. KEEP native DDD/hexagonal state boundaries, canary DB and current plan consumers. Do not add Nx/Turbo, a registry, extra tests or a new agent policy layer.
