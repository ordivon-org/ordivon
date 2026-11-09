# Runtime Workspace Contract — Implementation Plan

> **For agentic workers:** Follow existing Runtime Owner verification; use Matt-style tracer bullets, Superpowers red/green/verify, and ECC's scoped verification loop. This document is a temporary execution plan, not a second Runtime authority.

**Goal:** Make source-owned PG Workspace reclaim safe *and live* under a 4h temporary-workspace policy, independently verifiable even with weak/conservative Agent implementations.

**Architecture:** Adopt the actual installed PG native reclaim entrypoint as versioned Runtime source, remove unnecessary success/main/ctime eligibility gates, retain rechecked Runtime `workspace.close`, then integrate the existing release/CI path. Separate cross-Owner lease and Windows cutover from the first independent Linux delivery.

**Tech Stack:** Rust Runtime/MCP, Python operator adapter/tests, Git, PostgreSQL, systemd, GitHub Merge Queue, Mise.

**Spec:** `services/runtime/docs/runtime-workspace-reclaim-spec.md`

**Base:** `3b43977e682d8c7668f6371ffd998c7821e4312a` (source snapshot; refresh merge-base before merge).

## Global Constraints

- One authoritative Linux PG Runtime writer, no SQLite fallback in the PG lifecycle path.
- No new Registry/Broker/Agent workflow platform.
- Preserve Windows SQLite while active.
- The caller must not claim Task semantic success from terminal execution or `consumerReleased`.
- Read-only first. Physical cleanup only through `workspace.close` after exact revalidation.
- 4h default; no success-only, origin/main-only, or ctime-only retention.
- Preserve UNKNOWN for unavailable PG/MCP/Git observations; never turn unavailable evidence into a deletion candidate.
- Prefer existing Runtime CLI, MCP, release manifest and CI over new governance infrastructure.

## Review Focus (independent adversarial cases)

1. An untouched empty Workspace (no Jobs): old policy must fail, repaired path allows closure.
2. Failed/lost terminal Job: outcome isn't semantic success, but no physical lifetime claim justifies infinite Workspace retention.
3. Active Job and active process cwd: ineligible irrespective of age.
4. HEAD not in main but reachable from a durable branch or tag: preserve source and free worktree.
5. Repeated metadata ctime changes without new runtime activity: GC still eventually eligible.

## Task graph

### T0 — Pin specification and behavior seams
**Blocked by:** none.
**Files:** create `docs/runtime-workspace-reclaim-spec.md`, `planning/runtime-workspace-reclaim-implementation-20261109.md`.
**Proof:** exact source and installed path observations; check docs and diff.
- [x] Read original upstream Skill files and root/Runtime Agent contracts.
- [x] Verify current Git SourceCut, installed PG reclaim, Windows split.
- [ ] Commit spec/plan to isolated branch.

### T1 — Source-owned PG reclaim CLI (vertical slice)
**Blocked by:** T0.
**Files:** create `scripts/ordivon-runtime-pg-reclaim`, `scripts/tests/test_pg_native_reclaim.py`.
**Interface:** existing CLI `--env-file --workspace-root --source-repo --min-age-hours --apply` and Runtime MCP `workspace.get/close`.
**Acceptance:** dry-run reports eligible clean old Workspace with zero Job; active/dirty/unknown remain ineligible.
- [x] Write failing CLI-facing test (RED) before changing production logic.
- [x] Copy and simplify currently installed PG reclaim adapter into tracked source; use existing PG/MCP/Git owners.
- [x] Run targeted tests GREEN; introduce regression mutation/negative test showing RED reappears.

### T2 — Terminal-failure and persistent-ref behavior (vertical slice)
**Blocked by:** T1.
**Files:** modify PG CLI, PG-native test.
**Acceptance:** terminal failed/lost/cancelled no longer form eternal hold; nonterminal remains blocked; HEAD in durable tag/branch qualifies without origin/main merge; unanchored source cannot be dropped.
- [x] New tests RED for resolved failures and non-main durable references.
- [x] Minimal implementation GREEN; reuse Runtime close digest/currentness recheck.
- [x] Run targeted tests and explicit negative tests.

### T3 — Source/install release closure (vertical slice)
**Blocked by:** T1.
**Files:** `scripts/ordivon-runtime-deploy`, `packaging/systemd/ordivon-runtime-lifecycle.service` or a separate PG packaging unit, `scripts/tests/test_deploy_reclaim.py`, `scripts/tests/test_lifecycle.py`.
**Acceptance:** PG reclaim adapter is included by exact digest in the existing release artifact set; a PG installation no longer points to non-versioned script or retired SQLite data. Legacy Windows remains separate.
- [x] RED manifest and Unit tests for actual PG-only release carrier.
- [x] GREEN by extending existing packaging without independent release mechanism.
- [ ] Run deployment script tests, lint, docs, affected Owner verification.

### T4 — Independent CI/Agent correctness gate
**Blocked by:** T2, T3.
**Files:** prefer existing Runtime native tests and Mise task; avoid new owner/registry.
**Acceptance:** deliberately reintroducing success-only/ctime-only rule fails Owner tests; no source-only PASS is reported as installed.
- [ ] Verify red-green regression using defect mutation.
- [ ] Run existing `runtime:verify` or focused actual Owner task with full result.
- [ ] Review diff against both spec and repo standards; retire superseded path.

### T5 — Physical acceptance and installation readback
**Blocked by:** T4.
**Target:** isolated PG/systemd or safe non-production candidate first, then installed release via existing rollout.
**Acceptance:** six-case native integration, process/PG readback, exact installed artifact digest and service Unit match committed source, no duplicate writer.
- [ ] Stage candidate and run dry-run against real PG.
- [ ] Apply through the existing release mechanism if qualifications pass.
- [ ] Compare Installed/Loaded/Executed/Consumed separately.

### T6 — Cross-Owner lease and remaining legacy retirement (subsequent independently scoped spec)
**Blocked by:** T5 and qualified Host consumer contracts.
**Acceptance:** durable and observable consumer leases; stale lease expiry and reconciliation; Windows PG cutover proven before deleting SQLite.
- [ ] Specify Host/Runtime lease consumer and exact proof obligations.
- [ ] Port and qualify Windows PG semantics; retire SQLite only after consumer closure.
- [ ] Remove now-unreferenced old lifecycle code, docs, and temporary plan.

## Implementation ledger

- 2026-11-09: spec anchored to latest observed origin/main `3b43977e...`; existing installed script is PG-only but outside current tracked source. Next executable slice T1.

- RED: untracked installed operator absent; after source adoption, 9 behavior scenarios yielded 5 logically failing cases under original ctime/success-only/main-only gates.
- GREEN: 9/9 after correcting the registered PG operator logic, then 13/13 after a newly failing fresh-PG-projection race case was fixed.
- RED/GREEN release: 3/3 new release/Unit expectations initially failed and then passed after packaging was corrected.
- Expanded regression (with installed \`ORDIVON_RUNTIME_INSPECT\`): 59/59 lifecycle, 26/26 cache, 75/75 deployment/release tests pass. Without the inspector those legacy suites are ENV_BLOCKED, not PASS.
- Live read-only rehearsal of the tracked operator: checked=47, eligible=0, closed=0, errors=0; it did not deploy or replace the installed operator.
- Source state remains BRANCH-ONLY until commit/PR, and INSTALLED/CONSUMED remains unverified. The full Owner Rust/formal gate is not claimed as PASS.

## Exact verification commands

From \`services/runtime/\`:

\`\`\`sh
python3 -m unittest discover -s scripts/tests -p test_pg_native_reclaim.py -q
python3 -m unittest discover -s scripts/tests -p test_lifecycle.py -q
python3 -m unittest discover -s scripts/tests -p test_cache.py -q
python3 -m unittest discover -s scripts/tests -p test_deploy_reclaim.py -q
python3 scripts/check_docs.py
git diff --check
\`\`\`

The legacy lifecycle/cache/deploy suites require \`ORDIVON_RUNTIME_INSPECT\` to reference a qualified native inspector binary; use \`scripts/owner-environment test-lifecycle\` for the source-built environment. The full Runtime CI contract remains \`mise run runtime:verify\` from repository root, which is distinct from this focused evidence.

For source-only readback of the new operator (never add \`--apply\` during diagnosis):

\`\`\`sh
python3 scripts/ordivon-runtime-pg-reclaim \
  --env-file /etc/ordivon/ordivon-runtime-pg-only.env \
  --source-repo /root/projects/ordivon \
  --workspace-root /var/lib/ordivon/pg-candidate/workspaces \
  --receipt-root /var/lib/ordivon/pg-candidate/lifecycle-receipts \
  --lock-file /run/ordivon-runtime-pg-reclaim.lock \
  --min-age-hours 4 --limit 25
\`\`\`

Production Unit source, candidate manifest, installed script digest and operating node must be compared explicitly before T5 can be marked complete.
