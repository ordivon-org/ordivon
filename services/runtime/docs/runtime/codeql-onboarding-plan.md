# CodeQL Onboarding Plan

Status: **PLAN**
Date: 2026-04-28
Phase: 3.13
Tags: `codeql`, `security`, `onboarding`, `plan`

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

## 6. Proposed Workflow

```yaml
name: CodeQL

on:
  push:
    branches: [main]
  schedule:
    - cron: "0 6 * * 3"  # Weekly Wednesday 06:00 UTC
  # PR trigger deferred to Phase 4.x after baseline is stable

permissions:
  contents: read
  security-events: write

jobs:
  analyze:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        language: [python]
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
| Push to main only (not PR) | First onboarding; avoid PR noise |
| Weekly schedule | Cost amortization; not every commit needs scanning |
| No PR trigger initially | Baseline must be stable before per-PR gating |
| Python only | Ordivon's primary language; JavaScript later if frontend grows |

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

| Phase | Action | Timeline | CI Change |
|-------|--------|----------|-----------|
| **3.13** | Plan only (this doc) | Now | Zero |
| **4.1** | Add CodeQL workflow (dry-run) | Next phase | New `codeql.yml` |
| **4.2** | Tune alert baseline | 2-4 weeks | Review Security tab |
| **4.3** | Promote main branch to hard gate | After baseline stable | `continue-on-error: false` |
| **4.4** | Add PR trigger | After main gate proven | Add `pull_request` event |

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

## 11. Related Documents

| Document | Relationship |
|----------|-------------|
| `docs/adr/ADR-008-tooling-adoption-strategy.md` | Formal build/buy decision |
| `docs/architecture/github-tooling-landscape.md` | Tool category evaluation |
| `docs/architecture/security-platform-baseline.md` | Security gate classification |
| `docs/runtime/verification-ci-gate-plan.md` | CI gate roadmap |
