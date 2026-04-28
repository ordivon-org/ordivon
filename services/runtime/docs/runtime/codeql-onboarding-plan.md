# CodeQL Onboarding Plan

Status: **IMPLEMENTED** (Phase 4.1–4.3: workflow deployed, triaged, hard gate)
Date: 2026-04-28
Phase: 3.13 → 4.1 → 4.2 → 4.3
Tags: `codeql`, `security`, `onboarding`, `plan`, `implemented`, `hard-gate`

## 1. Purpose

Define the minimum CodeQL onboarding plan for Ordivon/AegisOS. CodeQL is the
first "Adopt Soon" security tool from ADR-008. This plan specifies permissions,
gate semantics, rollout phases, and stop conditions before any workflow is
created.

## 2. Why CodeQL Next

CodeQL is the next security tool to adopt because:
- **GitHub-native**: first-party Action, no external service dependency
- **Language coverage**: Python (Ordivon's primary language)
- **Low false positive rate**: fewer than Bandit for security-critical patterns
- **Read-only analysis**: does not modify code or dependencies
- **Clear adoption path**: dry-run → advisory → hard gate

Other "Adopt Soon" tools (Dependabot, Scorecard) have lower security urgency
or overlap with existing capabilities.

## 3. What CodeQL Covers

| Category | Examples |
|----------|----------|
| SQL injection | Query string concatenation |
| Path traversal | Unsanitized file paths |
| Hardcoded credentials | API keys, tokens in source |
| Insecure deserialization | pickle, yaml.load without SafeLoader |
| Command injection | os.system, subprocess with shell=True |
| Information exposure | Exception messages with sensitive data |

## 4. What CodeQL Does Not Cover

- Dependency vulnerabilities (pip-audit handles this)
- Secret leaks in commit history (Gitleaks handles this)
- Container vulnerabilities (Trivy handles this — deferred)
- Governance classification (Ordivon RiskEngine handles this)
- Architecture boundary violations (check_architecture.py handles this)
- Formatting/style issues (Ruff handles this)

One tool per problem. No overlapping capabilities.

## 5. Required GitHub Permissions

```yaml
permissions:
  contents: read
  security-events: write
```

### Why `security-events: write` Is Acceptable

`security-events: write` allows uploading SARIF results to GitHub code scanning.
This is a **read-only analysis → write-results** pattern, fundamentally
different from:

- `pull-requests: write` (PR comments, PR modifications)
- `contents: write` (push commits, modify files)
- `checks: write` (create check runs)

Code scanning results appear in the **Security tab** of the repository, not in
PR timeline or PR checks. No PR comment is created. No file is modified. No
commit is pushed.

### What `security-events: write` Does NOT Enable

- ❌ PR comments or annotations
- ❌ File modifications
- ❌ Commit creation
- ❌ PR merge/unmerge
- ❌ Branch protection changes

## 6. Actual Workflow (Phase 4.1)

```yaml
name: CodeQL

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: "0 3 * * 1"  # Weekly Monday 03:00 UTC

permissions:
  contents: read
  security-events: write

jobs:
  analyze:
    name: Analyze (${{ matrix.language }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        language:
          - python
          - javascript-typescript
    steps:
      - uses: actions/checkout@v6
      - uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
      - uses: github/codeql-action/analyze@v3
```

### Key Design Choices

| Choice | Rationale |
|--------|-----------|
| PR trigger included | Task specification (Phase 4.1) includes PR; advisory-only, no blocking |
| Python + JS/TS | Repo has both `pyproject.toml` and `apps/web/package.json` |
| No autobuild step | CodeQL's default Python/JS autobuild is sufficient |
| `security-events: write` only | Upload SARIF results to Security tab; no PR write/comment/push |
| `fail-fast: false` | One language failure does not cancel the other |

### Phase 4.1 Gate Semantics

| Event | Behavior | Blocking? |
|-------|----------|-----------|
| PR push | CodeQL uploads results to Security tab | No |
| Main branch push | CodeQL uploads results to Security tab | No |
| Weekly schedule | CodeQL uploads results to Security tab | No |

This matches the dry-run/advisory phase: establish baseline, understand alert
volume and false positive rate. Zero CI impact — CodeQL workflow runs
independently and does not gate any verification or governance step.

## 7. Gate Semantics

### Phase 1: Dry-Run / Advisory

| Event | Behavior | Blocking? |
|-------|----------|-----------|
| Main branch push | CodeQL uploads results to Security tab | No |
| Weekly schedule | CodeQL uploads results to Security tab | No |

**Goal**: Establish baseline. Understand alert volume and false positive rate.
Zero CI impact.

### Phase 2: Main Branch Hard Gate

| Event | Behavior | Blocking? |
|-------|----------|-----------|
| Main branch push | CodeQL fails CI on new security alerts | Yes |

**Goal**: Prevent new security issues from landing on main. Existing alerts
are acknowledged (suppressed in CodeQL dashboard).

### Phase 3: PR Gating

| Event | Behavior | Blocking? |
|-------|----------|-----------|
| PR to main | CodeQL runs on changed files, fails on new alerts | Yes |

**Goal**: Catch security issues before merge. Requires stable baseline from
Phase 1-2.

## 8. Rollout Phases

| Phase | Action | Timeline | CI Change | Status |
|-------|--------|----------|-----------|--------|
| **3.13** | Plan only (this doc) | 2026-04-28 | Zero | ✅ Complete |
| **4.1** | Add CodeQL workflow (dry-run) | 2026-04-28 | New `codeql.yml` | ✅ Complete |
| **4.2** | Tune alert baseline | 2-4 weeks | Review Security tab | ⏳ Next |
| **4.3** | Promote main branch to hard gate | After baseline stable | `continue-on-error: false` | 📋 Plan |
| **4.4** | Add PR trigger | After main gate proven | Add `pull_request` event | 📋 Plan (PR already present; hardening deferred) |

## 9. Stop Conditions

If any of the following occur, stop CodeQL onboarding and report:

| Condition | Reason |
|-----------|--------|
| CodeQL generates > 20 alerts on first run | Baseline too noisy; false positive rate unacceptable |
| CodeQL runtime exceeds 10 minutes | Too expensive for CI |
| `security-events: write` causes permission conflicts | Permissions too broad for repo policy |
| CodeQL requires modification to source code | Breaks read-only analysis invariant |
| CodeQL auto-comments on PRs | Breaks no-PR-comment invariant |

## 10. Non-Goals

- No auto-fix of CodeQL findings
- No PR comments or annotations from CodeQL
- No dependency PR creation triggered by CodeQL
- No policy activation from CodeQL findings
- No Ordivon CandidateRule extraction from CodeQL alerts (future: Phase 5.x)
- No connection to MCP/IDE/AI agent

## 15. Phase 4.2 Triage Outcome

Date: 2026-04-28
Document: `docs/runtime/codeql-findings-triage.md`

### Alert Summary

| State | Count |
|-------|-------|
| Open | 0 |
| Dismissed | 0 |
| Fixed | 0 |

**Result: Zero-alert baseline.** Both Python and JavaScript/TypeScript
analyses found no security issues at the first run.

### Hard Gate Recommendation

With a zero-alert baseline, CodeQL can be promoted to main-branch hard
gate immediately — it costs nothing (always passes) and provides a
safety net for future commits. See `codeql-findings-triage.md` Section 9
for details.

### Updated Rollout Phases

| Phase | Action | Status |
|-------|--------|--------|
| 3.13 | Plan | ✅ Complete |
| 4.1 | Add CodeQL workflow | ✅ Complete |
| 4.2 | Triage findings | ✅ Complete (zero alerts) |
| 4.3 | Promote to hard gate | ✅ Complete (workflow-health only) |
| 4.x | Dependabot / Scorecard | 📋 Plan |

### Phase 4.3: Workflow-Health Hard Gate

CodeQL is now a **workflow-health hard gate** on main branch.
This means:

| What is gated | What is NOT gated |
|---------------|-------------------|
| CodeQL init failure | Individual finding severity |
| CodeQL analyze failure | Alert count threshold |
| SARIF upload failure | Specific CWE categories |
| Workflow crash/timeout | Security posture score |

**Finding severity remains advisory.** A CodeQL alert is security
evidence requiring human triage, not an automatic CI block. The
zero-alert baseline (Phase 4.2) means this hard gate costs nothing
while providing a safety net for future commits.

**Finding-severity hard gate** (e.g., "block PR if new high-severity
alert") requires a separate policy design phase that addresses:
- Alert-to-severity mapping
- False positive handling protocol
- Baseline alert acknowledgment (suppression)
- Branch protection rule changes
- Owner sign-off

That design is out of scope for Phase 4.3. The foundation is in place.

## 16. Related Documents

| Document | Relationship |
|----------|-------------|
| `docs/adr/ADR-008-tooling-adoption-strategy.md` | Formal build/buy decision |
| `docs/architecture/github-tooling-landscape.md` | Tool category evaluation |
| `docs/architecture/security-platform-baseline.md` | Security gate classification |
| `docs/runtime/verification-ci-gate-plan.md` | CI gate roadmap |
