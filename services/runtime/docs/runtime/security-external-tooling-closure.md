# Security and External Tooling Platform — Phase 4 Closure

Status: **CLOSED** (Phase 4.13)
Date: 2026-04-29
Phase: 4.1 → 4.13
Tags: `closure`, `security`, `codeql`, `dependabot`, `governance`, `bot-actor`, `evidence`, `stage-summit`

## 1. Purpose

This document closes the Phase 4 security and external tooling workstream.
It summarizes what was built, what was proven, what remains open, and
what should be carried forward to the Ordivon Stage Summit.

Phase 4 spanned 13 sub-phases (4.1–4.13) across three tooling domains:
CodeQL, Dependabot, and external actor governance. The workstream
validated the principle that external tools produce **evidence** and
Ordivon governance produces **decisions** — these layers must remain
separate.

## 2. Active Security / External Tooling Capabilities

### 2.1 Tool Inventory (as of Phase 4.12F closure)

| Tool | Type | Status | Gate Class | First Active |
|------|------|--------|------------|-------------|
| Gitleaks | Secret scanner | Active | Hard | Pre-4.0 |
| Bandit | Python AST scanner | Active | Advisory | Pre-4.0 |
| pip-audit | Dependency vuln scanner | Active | Advisory | Pre-4.0 |
| pip CVE patch | CI mitigation | Active | Hard | Pre-4.0 |
| CodeQL | Semantic code analysis | Active | Hard (workflow-health) | Phase 4.1 |
| Dependabot (github-actions) | Action version updates | Active | Advisory | Phase 4.5 |
| Dependabot (uv) | Python dependency updates | Active | Advisory | Phase 4.9 |
| Dependabot (npm/pnpm) | Node.js dependency updates | Active | Advisory | Phase 4.10 |

### 2.2 Gate Classification

| Gate Level | Tools | Trigger | Status |
|-----------|-------|---------|--------|
| Hard | Gitleaks, CodeQL (workflow-health), pip CVE | Every PR | Active |
| Escalation | CodeQL findings (future), Dependabot major updates (future) | — | Not yet active |
| Advisory | Bandit, pip-audit, Dependabot, Scorecard (future) | PR / schedule | Active |

### 2.3 Dependabot Ecosystem Map

| Ecosystem Key | Execution Truth | Lockfile | Adapter | Status |
|--------------|----------------|----------|---------|--------|
| `github-actions` | — | — | — | Active (Phase 4.5) |
| `uv` | uv | uv.lock | Dependabot v2 uv parser | Active (Phase 4.9) |
| `npm` | pnpm | pnpm-lock.yaml | Dependabot v2 npm adapter | Active (Phase 4.10) |
| `bun` | bun | bun.lock | Not configured | Deferred |

## 3. What CodeQL Proved (Phases 4.1–4.3)

### 3.1 Proof Points

1. **Zero-config onboarding works**: Adding a single `codeql.yml` workflow
   file to `.github/workflows/` was sufficient for Python + JavaScript/TypeScript
   analysis. No CodeQL configuration file needed.

2. **Zero-alert baseline is achievable**: After Phase 4.2 triage, the project
   reached zero CodeQL alerts. This proves the codebase is clean at the
   semantic analysis level.

3. **Workflow-health hard gate is correct**: Making workflow health (init,
   analyze, upload) a hard gate while keeping finding severity advisory
   prevents CI failures from transient SARIF upload issues without forcing
   human triage on every new finding.

4. **Finding severity gating needs more data**: CodeQL finding severity
   cannot be a hard gate until there is:
   - A documented alert policy
   - A false positive protocol
   - Stakeholder sign-off on what constitutes a blocking finding

### 3.2 Remaining Open

| Item | Status | Recommendation |
|------|--------|---------------|
| Finding-severity hard gate | Deferred | Requires alert policy design (Stage Summit) |
| Semgrep custom rules | Deferred | Evaluate after CandidateRule→Policy matures |
| SARIF integration with Ordivon Evidence Platform | Not started | Low priority; CI artifacts suffice |

## 4. What Dependabot Proved (Phases 4.4–4.12F)

### 4.1 Proof Points

1. **Phased ecosystem rollout works**: Enabling github-actions first (Phase
   4.5), then uv (Phase 4.9), then npm/pnpm (Phase 4.10) allowed each
   ecosystem to be observed independently. Zero PR floods. Zero unexpected
   behavior.

2. **uv ecosystem key is correct for uv projects**: Dependabot's `uv`
   package-ecosystem correctly parses `uv.lock` and `pyproject.toml`.
   PRs modify both files. No compatibility issues found.

3. **npm ecosystem key works for pnpm projects**: Dependabot's `npm`
   package-ecosystem correctly parses `pnpm-lock.yaml`. The `npm` key
   is a GitHub adapter identifier, not a tool recommendation.

4. **Lockfile changes are supply-chain evidence**: Every Dependabot PR
   that modifies `uv.lock` or `pnpm-lock.yaml` produces a visible diff.
   The diff is auditable, traceable, and passes through the same CI gates
   as human PRs.

5. **Bot actor governance requires adapter awareness**: The initial
   Deployment (Phase 4.5–4.10) revealed that the Repo Governance adapter
   did not handle bot PRs. Phases 4.11–4.12F fixed this with:
   - Identity detection via trusted GitHub actor metadata
   - Synthetic test_plan injection for Dependabot PRs
   - Dependency-file allowlisting (not bypassing forbidden-file checks)
   - Identity hardening (title-only signals removed)

6. **Fresh evidence matters**: Stale repo-governance-pr failures on
   pre-patch PR branches were correctly identified as stale, not as
   new problems. The Phase 4.12F "Update branch" flow regenerated fresh
   governance evidence, which correctly returned `execute` for all three
   low-risk PRs.

### 4.2 Merged Dependabot PRs

| PR | Ecosystem | Dependency | From → To | Risk | Merged |
|----|-----------|-----------|-----------|------|--------|
| #3 | github-actions | upload-artifact | v4 → v7 | low | Phase 4.6 |
| #4 | github-actions | codeql-action | v3 → v4 | low | Phase 4.7 |
| #5 | uv | sentry-sdk[fastapi] | >=2.30.0 → >=2.58.0 | low | Phase 4.12F |
| #6 | uv | uvicorn[standard] | >=0.30.0 → >=0.46.0 | low | Phase 4.12F |
| #8 | npm (pnpm) | @types/node | 22.19.17 → 25.6.0 | low | Phase 4.12F |

**Total: 5 PRs merged across all 3 ecosystems.**

### 4.3 Remaining Open

| Item | Status | Recommendation |
|------|--------|---------------|
| PR #7 (react bump) | Open — HOLD | Frontend compatibility issue (Stage Summit) |
| Auto-merge evaluation | Deferred | Requires 3+ months clean history |
| Grouping configuration (patch/minor/major) | Deferred | Baseline first, then tune |
| Dependabot security alerts | Advisory only | No auto-fix; human review required |

## 5. How Bot Actor Governance Now Works

### 5.1 Architecture

```
Dependabot PR created
  │
  ├─ GitHub actor metadata → pr.user.login = "dependabot[bot]"
  │
  ├─ Adapter detects trusted actor → _is_dependabot_pr() = True
  │
  ├─ Synthetic test_plan injected (not extracted from PR body)
  │
  ├─ Expected dependency files filtered from forbidden check
  │   (pyproject.toml, uv.lock, package.json, pnpm-lock.yaml)
  │
  ├─ Non-dependency files (.env, source code) → full RiskEngine
  │
  └─ Decision: execute (if clean) or escalate/reject (if issues)
```

### 5.2 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Identity from actor metadata only | Title/body/labels are user-supplied and untrusted |
| Synthetic test_plan, not bypass | Bot PRs get adapted governance, not skipped governance |
| File allowlist, not full bypass | .env and source code still go through RiskEngine |
| No auto-merge | All merges require human review |

### 5.3 Identity Hardening (Phase 4.11 Patch)

The original detection used title patterns (`deps:`, `bump `) as a
Dependabot signal. This was insecure — any human could write a "deps:"
title. The patch removed all title-based signals, keeping only trusted
GitHub actor metadata (`pr.user.login`, `event.sender.login`).

This is validated by unit tests:
- Human PR with "deps:" title + no user metadata → escalate (correct)
- Dependabot[bot] PR + expected files → execute (correct)

## 6. Why PR #7 (React) Is Still Held

PR #7 attempts to bump React and @types/react in `apps/web/`.

**Failures**:
- `frontend-build`: failure
- `frontend-components`: failure

**Root cause**: The React version jump introduces breaking changes that
the current frontend code does not handle. These are real compatibility
failures, not governance adapter issues.

**Status**: Open. Should be addressed in a dedicated frontend update
phase, not as part of the Dependabot governance workstream.

## 7. Evidence and Artifact Behavior

### 7.1 What Works

| Evidence Type | Source | Status |
|--------------|--------|--------|
| repo-governance-pr JSON output | CI artifact | Active for all PRs |
| repo-governance-report.json | CI artifact | Generated on PR events |
| repo-governance-report.md | CI artifact | Generated on PR events |
| Dependabot PR changelog | PR body | Auto-generated by Dependabot |
| CodeQL SARIF | Security tab | Uploaded on push/PR/schedule |

### 7.2 What Does Not (Yet) Exist

| Capability | Status | Notes |
|-----------|--------|-------|
| ExecutionReceipt for bot PRs | Not implemented | Adapter artifacts ≠ ExecutionReceipts |
| Audit trail in Ordivon DB | Not implemented | CI artifacts suffice for current scope |
| Unified security dashboard | Not implemented | Stage Summit discussion item |

## 8. What Should NOT Be Done Next

Based on the Phase 4 findings, the following should be **explicitly not
started** until the Stage Summit reviews and approves:

1. **Auto-merge for Dependabot PRs**: The 3+ month clean history
   requirement has not been met. Premature auto-merge would bypass
   the human review step that caught the React compatibility issue.

2. **Bun ecosystem in Dependabot**: `bun.lock` is not the governed
   lockfile. Adding a fourth ecosystem before the first three are
   stable adds unnecessary complexity.

3. **CodeQL finding-severity hard gate**: Requires alert policy design
   first. Hard-gating without a false positive protocol would create
   CI noise and desensitize developers.

4. **PR comment or Checks API integration**: Requires write tokens and
   proven artifact stability. Read-only evidence is sufficient for now.

5. **New CandidateRules from Phase 4 incidents**: The governance adapter
   fix addressed the root cause (missing bot awareness). Creating a
   CandidateRule for "Dependabot PRs fail governance" would encode a
   symptom, not a pattern.

6. **Semgrep, Trivy, OPA/Conftest**: These tools solve problems the
   project does not yet have (custom security rules, container scanning,
   policy-as-code). Defer until the use case emerges.

## 9. Stage Summit Agenda

The following questions should be brought to the Ordivon Stage Summit:

### 9.1 Governance Maturity

- Is the bot actor governance model (synthetic test_plan + file allowlist)
  sufficient for future AI agent PRs, or does it need extension?
- Should the adapter be refactored to support pluggable actor profiles
  (Dependabot, future AI agent, human)?

### 9.2 Evidence Platform

- Should bot PR governance decisions produce ExecutionReceipts in the
  Ordivon DB, or do CI artifacts suffice?
- What is the long-term vision for the Ordivon Evidence Platform vs.
  GitHub-native evidence (SARIF, check runs, artifacts)?

### 9.3 Auto-Merge Policy

- What are the criteria for auto-merging Dependabot patch updates?
- Should the governance adapter produce an "auto-mergeable" flag in
  its output (advisory only, human decides)?

### 9.4 Tooling Horizon

- Is OpenSSF Scorecard still a priority?
- When should Semgrep evaluation begin?
- Should the project pursue a unified security dashboard?

### 9.5 React PR #7

- Who owns the React compatibility fix?
- Should it be addressed before or after the Stage Summit?

## 10. Phase 4 Timeline Summary

| Phase | Description | Date | Outcome |
|-------|-------------|------|---------|
| 4.1 | CodeQL onboarding | 2026-04-28 | workflow deployed |
| 4.2 | CodeQL triage | 2026-04-28 | zero alerts |
| 4.3 | CodeQL hard gate | 2026-04-28 | workflow-health hard gate |
| 4.4 | Dependabot strategy plan | 2026-04-28 | strategy documented |
| 4.5 | Dependabot github-actions enable | 2026-04-28 | first ecosystem |
| 4.6 | First Dependabot PR observation | 2026-04-28 | PR #3 observed |
| 4.7 | Dependabot tuning + artifact validation | 2026-04-28 | PR #4 validated |
| 4.8 | uv/pnpm strategy refinement | 2026-04-29 | ecosystem keys corrected |
| 4.9 | Python/uv enablement | 2026-04-29 | uv ecosystem active |
| 4.10 | Node/pnpm enablement | 2026-04-29 | npm ecosystem active |
| 4.11 | Bot governance + identity hardening | 2026-04-29 | adapter fixed |
| 4.12 | Fresh governance observation | 2026-04-29 | stale evidence identified |
| 4.12F | Fresh governance + merge | 2026-04-29 | 3 PRs merged |
| 4.13 | Closure review | 2026-04-29 | this document |

**Total: 14 sub-phases. 7 tools active. 5 Dependabot PRs merged.
1 PR held. 0 regressions.**

## 11. Related Documents

| Document | Relationship |
|----------|-------------|
| `docs/architecture/security-platform-baseline.md` | Security gate classification |
| `docs/runtime/dependabot-strategy.md` | Dependabot adoption strategy |
| `docs/runtime/codeql-onboarding-plan.md` | CodeQL deployment plan |
| `docs/runtime/dependabot-first-pr-observation.md` | First PR observation |
| `docs/runtime/dependabot-pr3-artifact-validation.md` | Artifact validation |
| `docs/runbooks/ordivon-agent-operating-doctrine.md` | Agent operating rules |
| `docs/adr/ADR-008-tooling-adoption-strategy.md` | Build/buy decisions |
