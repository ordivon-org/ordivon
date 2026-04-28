# Dependabot Supply-Chain Strategy

Status: **IMPLEMENTED** (Phase 4.5: github-actions enabled)
Date: 2026-04-28
Phase: 4.4 → 4.5
Tags: `dependabot`, `supply-chain`, `dependencies`, `security`, `plan`, `enabled`, `github-actions`

## 1. Purpose

Define the Dependabot adoption strategy for Ordivon/AegisOS. Dependabot
is a GitHub-native dependency update tool that creates PRs for outdated
or vulnerable dependencies. Unlike scanners (Gitleaks, Bandit, CodeQL),
Dependabot is an **external actor** that modifies the repo by creating PRs.

This document establishes the gate semantics, noise-control strategy,
and rollout plan **before** any `dependabot.yml` is created or any PR
is generated.

## 2. Why Dependabot Is Different from Scanners

| Property | Scanners (CodeQL, Gitleaks, Bandit) | Dependabot |
|----------|-------------------------------------|------------|
| Action | Read-only analysis | Creates PRs (writes to repo) |
| Output | Alerts, SARIF, logs | Code changes (dependency bumps) |
| Frequency | Per push/PR/schedule | Per schedule |
| Repo impact | Zero (no file changes) | Lockfile + manifest changes |
| Governance path | Evidence → Triage → (optional) Fix | PR → CI → Review → Merge |
| Trust model | Scanner output is evidence | PR is a proposal from external actor |

**Dependabot PRs must pass through the same governance gates as human PRs.**
There is no special Dependabot bypass.

## 3. Current Dependency Ecosystems

### 3.1 Python (uv / pip)

| Property | Value |
|----------|-------|
| Manifest | `pyproject.toml` |
| Lockfile | `uv.lock` |
| Package manager | uv (pip-compatible) |
| Dependabot ecosystem | `pip` |
| Directory | `/` (root) |

**Key packages**: fastapi, uvicorn, pydantic, sqlalchemy, duckdb,
duckdb-engine, psycopg2-binary, alembic, redis, httpx, openai,
opentelemetry-*, python-dotenv, sentry-sdk, pytz.

**Dev dependencies** (separate group): bandit, pip-audit, import-linter,
mypy, vulture, pytest, pytest-asyncio, ruff.

### 3.2 Node / TypeScript (pnpm workspace)

| Property | Value |
|----------|-------|
| Root manifest | `package.json` |
| Web manifest | `apps/web/package.json` |
| Lockfile | `pnpm-lock.yaml` |
| Package manager | pnpm@10.33.0 |
| Dependabot ecosystem | `npm` |
| Directory | `/` (root, monorepo root) |

Workspace: `apps/web` (Next.js dashboard). Root has e2e/dev tooling;
`apps/web` has the application dependencies.

### 3.3 GitHub Actions

| Property | Value |
|----------|-------|
| Workflow count | 5 (ci, codeql, security, nightly-regression, delivery) |
| Dependabot ecosystem | `github-actions` |
| Directory | `.github/workflows/` |

**Current action versions**: checkout@v6, setup-python@v6, setup-uv@v8.1.0,
pnpm/action-setup@v6, setup-node@v6, gitleaks-action@v2, upload-artifact@v4,
codeql-action/init@v3, codeql-action/analyze@v3.

### 3.4 Docker

No Dockerfile detected. Docker ecosystem deferred until containerization.

## 4. Recommended v1 Ecosystems

| # | Ecosystem | Directory | Rationale |
|---|-----------|-----------|-----------|
| 1 | `github-actions` | `/` | Lowest noise, highest value — action versions matter for CI security |
| 2 | `pip` | `/` | Core application dependencies; uv.lock needs special handling |
| 3 | `npm` | `/` | Root + workspace dependencies |

GitHub Actions first because:
- No lockfile churn
- PRs are single-line YAML changes
- Low false positive rate
- Directly improves CI supply-chain security

## 5. Noise-Control Strategy

### 5.1 Schedule

| Trigger | Rationale |
|---------|-----------|
| Weekly (Monday 09:00 UTC) | Batches updates; predictable review window |
| No daily schedule | Prevents reviewer fatigue |
| No on-demand trigger | Initial phase is controlled |

### 5.2 Open PR Limit

```yaml
open-pull-requests-limit: 5
```

Across all ecosystems combined. Prevents PR flood on first enablement.

### 5.3 Grouping Strategy

| Group | Contents | Rationale |
|-------|----------|-----------|
| `python-patch` | pip patch updates | Low risk, batch review |
| `python-minor` | pip minor updates | Medium risk, smaller batches |
| `python-major` | pip major updates | **Ungrouped** — one PR per major bump |
| `npm-patch` | npm/pnpm patch updates | Low risk, batch review |
| `npm-minor` | npm/pnpm minor updates | Medium risk, batch review |
| `npm-major` | npm/pnpm major updates | **Ungrouped** — one PR per major bump |
| `github-actions` | All action updates | Single PR for all actions |

**Rule**: Minor and patch updates are grouped to reduce PR count.
Major updates are never grouped — each is a separate PR requiring
independent changelog review and test verification.

### 5.4 Auto-Merge

**Disabled.** Phase 4.4–4.7: all Dependabot PRs require human review
and merge. Auto-merge may be evaluated after 3+ months of clean
Dependabot PR history.

## 6. Repo Governance Interaction

Dependabot PRs are normal PRs. They trigger:

| Gate | Behavior |
|------|----------|
| `backend-static` | Runs on Python dep changes |
| `verification-fast` | Runs on all PRs |
| `secret-scan` | Runs on all PRs |
| `repo-governance-pr` | Runs on all PRs (PR event) |
| `frontend-components` | Runs on JS dep changes |
| `CodeQL` | Runs on all PRs (advisory) |

### Repo Governance Risk

`repo-governance-pr` requires a Test Plan. Dependabot PRs have no
human-authored Test Plan. This may cause **escalation** if the
governance adapter treats missing Test Plan as escalate.

**Mitigation**: Dependabot PR description includes the dependency
changelog. The governance adapter should recognize Dependabot as
a known bot actor and accept the automated changelog as sufficient
evidence for patch/minor updates. Major updates may still escalate.

If governance escalation is too noisy, adjust the adapter or add a
Dependabot-specific Test Plan template via `commit-message` or
`pull-request-body` configuration.

## 7. Security vs Version Updates

| Type | Priority | Behavior |
|------|----------|----------|
| `security-updates` | High | Critical/High CVE fixes; Dependabot opens PR immediately |
| `version-updates` | Controlled | Weekly schedule; grouped; subject to PR limit |

### Security Updates

Dependabot security alerts appear in the Security tab. When a
vulnerable dependency is detected:
1. Dependabot opens a security update PR
2. PR follows the same CI pipeline
3. Reviewer evaluates fix + changelog
4. Merge decisions are human-driven

Security update PRs **do not** auto-merge and **do not** bypass
governance.

### Version Updates

Non-security dependency bumps follow the weekly schedule.
They are maintenance, not incident response.

## 8. Proposed dependabot.yml v1 (Draft — Not Deployed)

```yaml
# Draft: .github/dependabot.yml (Phase 4.4 PLAN ONLY — not created)
#
# This is the proposed v1 configuration. It will be created and
# enabled in Phase 4.5 after stakeholder review.

version: 2
updates:
  # --- GitHub Actions ---
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
      day: monday
      time: "09:00"
      timezone: Asia/Shanghai
    open-pull-requests-limit: 5
    labels:
      - dependencies
      - github-actions
    commit-message:
      prefix: ci
      include: scope
    groups:
      actions:
        patterns:
          - "*"

  # --- Python (pip via pyproject.toml) ---
  - package-ecosystem: pip
    directory: /
    schedule:
      interval: weekly
      day: monday
      time: "09:00"
      timezone: Asia/Shanghai
    open-pull-requests-limit: 5
    labels:
      - dependencies
      - python
    commit-message:
      prefix: build
      include: scope
    groups:
      python-patch:
        update-types:
          - patch
      python-minor:
        update-types:
          - minor
    # Major updates ungrouped — individual PRs
    ignore:
      # Ignore pre-release/dev dependency updates unless security
      - dependency-name: "*"
        update-types: ["version-update:semver-patch"]
        # Not ignored — this section is for demonstration
        # Real ignore rules will be tuned during Phase 4.7

  # --- Node.js (npm/pnpm) ---
  - package-ecosystem: npm
    directory: /
    schedule:
      interval: weekly
      day: monday
      time: "09:00"
      timezone: Asia/Shanghai
    open-pull-requests-limit: 5
    labels:
      - dependencies
      - javascript
    commit-message:
      prefix: build
      include: scope
    groups:
      npm-patch:
        update-types:
          - patch
      npm-minor:
        update-types:
          - minor
    # Major updates ungrouped — individual PRs
```

### Design Notes

| Decision | Rationale |
|----------|-----------|
| `open-pull-requests-limit: 5` across all ecosystems | Cap total concurrent PRs |
| Groups share the same limit | Prevents one ecosystem from dominating |
| Major updates ungrouped | Requires individual changelog review |
| `timezone: Asia/Shanghai` | Matches project timezone (PFIOS_TIMEZONE) |
| `commit-message.prefix: build` / `ci` | Matches conventional commits |
| No `target-branch` | Defaults to default branch (main) |

### Known Limitations

| Limitation | Impact | Mitigation |
|-----------|--------|------------|
| `pip` ecosystem doesn't update `uv.lock` | PR bumps pyproject.toml but lockfile must be regenerated | CI should run `uv lock` or reviewer regenerates |
| `npm` ecosystem works with pnpm-lock.yaml | Dependabot v2+ supports pnpm | Confirm during Phase 4.5 testing |
| Group `update-types` may not work with all package managers | Grouping may fail silently | Monitor first PRs; fall back to ungrouped |
| `python-major` ungrouped may produce many PRs on first run | Initial backlog of major updates | Acceptable for first run; tune after baseline |

## 9. Gate Semantics

| Gate Level | Dependabot Status | Notes |
|------------|-------------------|-------|
| PR Fast | Standard CI | Dependabot PRs run all PR-triggered checks |
| PR Full | Standard CI | Standard governance path |
| Main Branch | No special gate | Merged deps follow normal CI |
| Scheduled Deep | Future: dep health report | Could integrate `pip-audit` + `pnpm audit` summary |

**Finding-severity gate**: Dependabot security alerts appear in the
Security tab. They are evidence, not automatic blocks. Severity-based
gating requires the same policy design as CodeQL finding-severity
(Phase 4.3 deferred).

## 10. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| PR noise (too many PRs) | Medium | High (reviewer fatigue) | `open-pull-requests-limit: 5`, weekly schedule, grouping |
| Lockfile churn (uv.lock) | Medium | Medium | `pip` ecosystem limitations; CI regenerates |
| Ecosystem incompatibility (uv + Dependabot) | Medium | Medium | Test in Phase 4.5; fallback to manual pip-audit |
| Grouped update blast radius | Low | Medium | Keep groups small; separate major updates |
| Supply-chain compromise (malicious dep) | Low | Critical | Human review of changelogs; pip-audit gate |
| Governance adapter escalation (missing Test Plan) | Medium | Low | Adapt governance or add Dependabot template |
| `pnpm-lock.yaml` format changes break Dependabot | Low | Medium | Monitor pnpm compatibility |

## 11. Rollout Plan

| Phase | Action | Timeline | Risk | Status |
|-------|--------|----------|------|--------|
| **4.4** | Strategy plan (this doc) | 2026-04-28 | Zero | ✅ Complete |
| **4.5** | Enable github-actions only | 2026-04-28 | Low | ✅ Complete |
| **4.6** | Observe first Dependabot PRs | 1-2 weeks | Medium | ⏳ Next |
| **4.7** | Tune grouping, labels, ignore rules | After baseline | Low | 📋 Plan |
| **4.8** | Enable pip + npm ecosystems | After 4.6 observation | Medium | 📋 Plan |
| **4.x** | Evaluate auto-merge for patch updates | 3+ months of clean history | Medium | 📋 Plan |

### Phase 4.5: GitHub Actions Only Enablement

**What was deployed:**
- `.github/dependabot.yml` created with `package-ecosystem: github-actions`
- Schedule: weekly Monday 09:00 Asia/Shanghai
- Open PR limit: 2
- Labels: `dependencies`, `security/supply-chain`
- Commit prefix: `deps`
- No pip or npm ecosystem configured

**Why github-actions first:**
- Zero lockfile churn — action versions are single-line YAML changes
- Lowest noise — at most 2 PRs per week for all action bumps combined
- Highest supply-chain value — action versions directly affect CI security
- Validates Dependabot behavior (PR creation, CI triggering, governance path)
  before enabling ecosystems that modify lockfiles

**Why pip/npm deferred:**
- `pip` + `uv.lock`: Dependabot doesn't regenerate uv.lock; PRs would be incomplete
- `npm` + `pnpm-lock.yaml`: Needs verification of pnpm compatibility
- Both introduce lockfile churn — needs observation of github-actions behavior first
- Deferred to Phase 4.8 after github-actions baseline is stable

**Expected behavior:**
- Dependabot checks for outdated GitHub Actions weekly
- If updates found, opens at most 2 PRs (one per action group, if needed)
- PRs trigger full CI pipeline including `repo-governance-pr`
- Human review + merge required (no auto-merge)

### Phase 4.5 Pre-flight Checklist (Revised)

- [x] `.github/dependabot.yml` deployed (github-actions only)
- [x] `open-pull-requests-limit: 2` configured
- [x] Labels: `dependencies`, `security/supply-chain`
- [ ] Observe first Dependabot PR (wait for Monday 09:00 or on-demand trigger)
- [ ] Confirm Dependabot PR triggers `repo-governance-pr`
- [ ] Confirm Dependabot PR passes `backend-static`, `verification-fast`, `secret-scan`
- [ ] pip ecosystem compatibility test (Phase 4.8)
- [ ] npm/pnpm compatibility test (Phase 4.8)

## 12. Non-Goals

Per Ordivon governance:

- ❌ No auto-merge
- ❌ No dependency version changes in this phase
- ❌ No pip or npm ecosystem enabled (Phase 4.8)
- ❌ No Dependabot PRs for lockfile-based ecosystems
- ❌ No source code changes
- ❌ No test changes
- ❌ No CI workflow changes (except adding dependabot.yml)
- ❌ No CandidateRule or PolicyProposal creation
- ❌ No auto-fix or auto-approve
- ❌ No bypass of repo-governance-pr
- ❌ No uv.lock or pnpm-lock.yaml modification

## 13. Related Documents

| Document | Relationship |
|----------|-------------|
| `docs/adr/ADR-008-tooling-adoption-strategy.md` | Build/buy decision for Dependabot |
| `docs/architecture/security-platform-baseline.md` | Security gate classification |
| `docs/runtime/codeql-onboarding-plan.md` | Preceding security tool onboarding |
| `docs/runtime/codeql-findings-triage.md` | Triage methodology (reusable for deps) |
| `docs/runtime/verification-ci-gate-plan.md` | CI gate roadmap |
