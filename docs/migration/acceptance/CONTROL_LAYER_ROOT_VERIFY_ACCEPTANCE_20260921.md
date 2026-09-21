# Control-layer root verification acceptance — 2026-09-21

Standing: **ACCEPTED_REPOSITORY_ORCHESTRATION**

## Scope

The modular monorepo root now exposes repository-navigation tasks for the principal control/composition owners without injecting monorepo-only verification blocks into owner source trees.

Root tasks:

- host:verify → services/host
- harness:verify → services/harness
- workstation:verify → platform/workstation

These tasks orchestrate owner-native gates; they do not redefine owner semantics or move deployment authority into the monorepo root.

## Host

host:verify reproduces the ordinary locked Host CI path:

- lock/sync — PASS
- Ruff — PASS
- pytest — 18 passed / 18 integration tests skipped without a test DSN

A separate migration acceptance used disposable PostgreSQL 18.6 and proved the complete Host suite at 36/36 with zero skips.

## Harness

harness:verify follows the deterministic Harness CI/release gate and passed from services/harness under the monorepo Git root:

- runtime-search physical profile — PASS (/bin/bash, /usr/bin/awk, /usr/bin/rg)
- locked environment and lock check — PASS
- compileall — PASS
- Ruff 0.15.17 — PASS
- pytest — **919 passed + 156 subtests**
- dependency contract — PASS
- documentation contract — PASS
- evidence contract — PASS
- deterministic demo — PASS
- wheel build — PASS
- installed-wheel verification — PASS
- hostFreeHarnessVerified=true

Host therefore remains absent from Harness runtime dependencies; root orchestration did not reintroduce Host coupling.

## Workstation

workstation:verify executes the owner Python CI and Cloudflare provider CI:

- locked Python environment — PASS
- Ruff — PASS
- Workstation pytest — **148 passed**
- Cloudflare provider frozen pnpm install — PASS
- TypeScript typecheck — PASS
- Node tests — **29 passed**
- provider Python controller suites — PASS
- policy checks — PASS
- operations checks — PASS
- Wrangler dry-run build — PASS

The independent GitHub ShellCheck job remains owner CI authority; this root task does not recreate the GitHub Action scanner semantics.

## Architectural consequence

The root now owns navigation/orchestration; Host, Harness, and Workstation continue to own their source, toolchain pins, contracts, state, and release/deployment semantics. This is the intended modular-monorepo boundary: central discovery and composition without collapsing bounded-context authority.
