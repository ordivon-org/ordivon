# Dependabot Supply-Chain Strategy

Status: **ACTIVE** (Phase 4.10 — Node/pnpm minimal enablement)
Date: 2026-04-29
Phase: 4.4 → 4.5 → 4.6 → 4.7 → 4.8 → 4.9 → 4.10
Tags: `dependabot`, `supply-chain`, `dependencies`, `security`, `enabled`, `github-actions`, `uv`, `pnpm`, `uv-enabled`, `pnpm-enabled`

## 1. Purpose

Define the Dependabot adoption strategy for Ordivon/AegisOS. Dependabot
is a GitHub-native dependency update tool that creates PRs for outdated
or vulnerable dependencies. Unlike scanners (Gitleaks, Bandit, CodeQL),
Dependabot is an **external actor** that modifies the repo by creating PRs.

This document establishes the gate semantics, noise-control strategy,
and rollout plan **before** any Python or Node ecosystem is enabled.

**Phase 4.8 is a strategy refinement phase**: it corrects the ecosystem
naming to reflect our real T0 tooling (uv / pnpm) before enabling
Python or Node Dependabot. No new Dependabot configuration is deployed.

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

## 3. Tool Identity vs Ecosystem Key (CRITICAL)

Dependabot's `package-ecosystem` key is a **GitHub upstream adapter identifier**.
It tells GitHub's dependency graph which parser to use for discovering
dependencies. It is NOT a directive about which local tool to use for
installation, locking, or building.

| Concern | Governed By |
|---------|-------------|
| **Execution truth** (install, build, lock) | Project toolchain: `uv`, `pnpm`, `bun` |
| **Dependabot ecosystem key** (upstream parser) | GitHub dependency graph adapter |
| **CI verification** (test after bump) | Project CI: `uv run`, `pnpm test`, etc. |
| **Lockfile format** (what Dependabot modifies) | Determined by ecosystem key + Dependabot support |

**Rule**: Never let the Dependabot ecosystem key dictate the project toolchain.
The ecosystem key is the upstream adapter; the project toolchain is the
execution truth. These are separate concerns.

### 3.1 Why `uv` vs `pip` Matters

Dependabot has a `uv` ecosystem key (supported since ~2025). It understands
`uv.lock` format and `pyproject.toml` with uv-compatible dependency specs.
Using `pip` as the ecosystem key when the project uses `uv` would mean:

- Dependabot parses `requirements.txt` style entries, not `uv.lock`
- Dependabot may miss dependencies declared only in `uv.lock`
- Dependabot PRs may not regenerate `uv.lock` correctly
- The ecosystem key misleads contributors into thinking `pip` is the tool

**Decision**: Use `package-ecosystem: uv` for Python. This is the correct
adapter for a uv-managed project.

### 3.2 Why `npm` Key for pnpm Is Acceptable

Dependabot does not have a dedicated `pnpm` ecosystem key. The `npm` key
is the general Node.js dependency graph adapter, and it supports pnpm
workspaces and `pnpm-lock.yaml` in Dependabot v2+.

**Decision**: Use `package-ecosystem: npm` for Node/pnpm. This is a
GitHub platform naming constraint, not an endorsement of `npm install`.
The project toolchain remains `pnpm`.

## 4. Current Dependency Ecosystems

### 4.1 Python (uv)

| Property | Value |
|----------|-------|
| Manifest | `pyproject.toml` |
| Lockfile | `uv.lock` |
| Package manager | **uv** (execution truth) |
| Dependabot ecosystem | `uv` (upstream adapter key) |
| Directory | `/` (root) |

**Key packages**: fastapi, uvicorn, pydantic, sqlalchemy, duckdb,
duckdb-engine, psycopg2-binary, alembic, redis, httpx, openai,
opentelemetry-*, python-dotenv, sentry-sdk, pytz.

**Dev dependencies** (separate group): bandit, pip-audit, import-linter,
mypy, vulture, pytest, pytest-asyncio, ruff.

**pip status**: pip is NOT the project toolchain entry point.
`pip install` and `pip freeze` are not used in Ordivon workflows.
The Dependabot ecosystem key `uv` reflects this — there is no `pip`
ecosystem configured.

### 4.2 Node / TypeScript (pnpm workspace)

| Property | Value |
|----------|-------|
| Root manifest | `package.json` |
| Web manifest | `apps/web/package.json` |
| Lockfile | `pnpm-lock.yaml` |
| Package manager | **pnpm@10.33.0** (execution truth) |
| Dependabot ecosystem | `npm` (GitHub Node.js adapter key) |
| Directory | `/` (root, monorepo root) |

Workspace: `apps/web` (Next.js dashboard). Root has e2e/dev tooling;
`apps/web` has the application dependencies.

**npm status**: The `npm` ecosystem key is a GitHub platform naming
convention for all Node.js dependency graphs. It does NOT mean the
project uses `npm install`. The project toolchain is `pnpm`, and CI
verification uses `pnpm test` / `pnpm run build`.

### 4.3 GitHub Actions

| Property | Value |
|----------|-------|
| Workflow count | 5 (ci, codeql, security, nightly-regression, delivery) |
| Dependabot ecosystem | `github-actions` |
| Directory | `.github/workflows/` |

**Current action versions**: checkout@v6, setup-python@v6, setup-uv@v8.1.0,
pnpm/action-setup@v6, setup-node@v6, gitleaks-action@v2, upload-artifact@v4,
codeql-action/init@v3, codeql-action/analyze@v3.

### 4.4 Bun (Runtime / Tooling Only)

| Property | Value |
|----------|-------|
| Status | Optional runtime/tooling — NOT a governed dependency ecosystem |
| Dependabot ecosystem | **Not configured** |
| Lockfile | `bun.lock` (not present / not governed) |

Bun is used as an optional runtime for scripts and tests where fast startup
is beneficial. It is not the primary package manager (pnpm is), and its
lockfile is not the governed supply-chain artifact.

**Decision**: Bun is excluded from Dependabot. It will only be considered
for `package-ecosystem: bun` if and when `bun.lock` becomes the primary,
governed lockfile for the Node.js dependency tree. This is not expected
in the current architecture.

### 4.5 Docker

No Dockerfile detected. Docker ecosystem deferred until containerization.

## 5. Recommended v1 Ecosystems

| # | Ecosystem | Directory | Rationale |
|---|-----------|-----------|-----------|
| 1 | `github-actions` | `/` | Lowest noise, highest value — action versions matter for CI security |
| 2 | `uv` | `/` | Core application dependencies; uv.lock is the governed lockfile |
| 3 | `npm` | `/` | Root + workspace Node dependencies; pnpm-lock.yaml via npm adapter |

GitHub Actions first because:
- No lockfile churn
- PRs are single-line YAML changes
- Low false positive rate
- Directly improves CI supply-chain security
- Already enabled and observed (Phase 4.5–4.7)

Python/uv second because:
- Core runtime dependencies — highest supply-chain impact
- `uv` ecosystem key is the correct adapter
- Validates Dependabot + uv.lock compatibility before Node enablement

Node/pnpm third because:
- Web dashboard dependencies
- `npm` key supports pnpm-lock.yaml
- Lower blast radius than Python core

## 6. Noise-Control Strategy

### 6.1 Schedule

| Trigger | Rationale |
|---------|-----------|
| Weekly (Monday 09:00 UTC+8) | Batches updates; predictable review window |
| No daily schedule | Prevents reviewer fatigue |
| No on-demand trigger | Initial phase is controlled |

### 6.2 Open PR Limit

```yaml
open-pull-requests-limit: 5
```

Across all ecosystems combined. Prevents PR flood on first enablement.

### 6.3 Grouping Strategy

| Group | Contents | Rationale |
|-------|----------|-----------|
| `uv-patch` | uv patch updates | Low risk, batch review |
| `uv-minor` | uv minor updates | Medium risk, smaller batches |
| `uv-major` | uv major updates | **Ungrouped** — one PR per major bump |
| `npm-patch` | npm/pnpm patch updates | Low risk, batch review |
| `npm-minor` | npm/pnpm minor updates | Medium risk, batch review |
| `npm-major` | npm/pnpm major updates | **Ungrouped** — one PR per major bump |
| `github-actions` | All action updates | Single PR for all actions |

**Rule**: Minor and patch updates are grouped to reduce PR count.
Major updates are never grouped — each is a separate PR requiring
independent changelog review and test verification.

### 6.4 Auto-Merge

**Disabled.** Phase 4.4–4.12: all Dependabot PRs require human review
and merge. Auto-merge may be evaluated after 3+ months of clean
Dependabot PR history across all ecosystems.

## 7. Repo Governance Interaction

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

## 8. Security vs Version Updates

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

## 9. Proposed dependabot.yml v2 (Draft — Not Deployed)

```yaml
# Draft: .github/dependabot.yml v2 (Phase 4.10 DEPLOYED — all 3 ecosystems active)
#
# github-actions + uv + npm (pnpm adapter) are now enabled.
# bun is deferred.

version: 2
updates:
  # --- GitHub Actions (already enabled, unchanged) ---
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
      prefix: deps
      include: scope
    groups:
      actions:
        patterns:
          - "*"

  # --- Python (uv — NOT pip) ---
  - package-ecosystem: uv
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
      uv-patch:
        update-types:
          - patch
      uv-minor:
        update-types:
          - minor
    # Major updates ungrouped — individual PRs

  # --- Node.js (npm adapter key for pnpm) ---
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
| `package-ecosystem: uv` not `pip` | uv is the project's execution truth; `uv` key parses `uv.lock` |
| `package-ecosystem: npm` for pnpm | GitHub has no `pnpm` key; `npm` key supports `pnpm-lock.yaml` |
| `open-pull-requests-limit: 5` across all ecosystems | Cap total concurrent PRs |
| Groups share the same limit | Prevents one ecosystem from dominating |
| Major updates ungrouped | Requires individual changelog review |
| `timezone: Asia/Shanghai` | Matches project timezone (PFIOS_TIMEZONE) |
| `commit-message.prefix: build` / `deps` | Matches conventional commits |
| No `target-branch` | Defaults to default branch (main) |
| Bun NOT configured | `bun.lock` is not a governed lockfile |

### Known Limitations

| Limitation | Impact | Mitigation |
|-----------|--------|------------|
| `uv` ecosystem may not regenerate all lockfile metadata | PR bumps pyproject.toml but lockfile may need manual `uv lock` | CI should run `uv lock --check` or reviewer regenerates |
| `npm` ecosystem works with pnpm-lock.yaml | Dependabot v2+ supports pnpm | Confirm during Phase 4.11 testing |
| Group `update-types` may not work with all package managers | Grouping may fail silently | Monitor first PRs; fall back to ungrouped |
| `uv-major` ungrouped may produce many PRs on first run | Initial backlog of major updates | Acceptable for first run; tune after baseline |

## 10. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| PR noise (too many PRs) | Medium | High (reviewer fatigue) | `open-pull-requests-limit: 5`, weekly schedule, grouping |
| Lockfile churn (uv.lock) | Medium | Medium | `uv` ecosystem supported; CI runs `uv lock --check` |
| Ecosystem incompatibility (uv + Dependabot) | Low-Medium | Medium | Test in Phase 4.9; fallback to manual pip-audit |
| `pnpm-lock.yaml` format changes break Dependabot | Low | Medium | Monitor pnpm compatibility during Phase 4.11 |
| Grouped update blast radius | Low | Medium | Keep groups small; separate major updates |
| Supply-chain compromise (malicious dep) | Low | Critical | Human review of changelogs; pip-audit gate |
| Governance adapter escalation (missing Test Plan) | Medium | Low | Adapt governance or add Dependabot template |
| Ecosystem key confusion (pip/npm misdirection) | Medium | Medium | **Mitigated in Phase 4.8**: docs clarify uv/pnpm as execution truth |

## 11. Rollout Plan

| Phase | Action | Timeline | Risk | Status |
|-------|--------|----------|------|--------|
| **4.4** | Strategy plan (this doc v1) | 2026-04-28 | Zero | ✅ Complete |
| **4.5** | Enable github-actions only | 2026-04-28 | Low | ✅ Complete |
| **4.6** | Observe first Dependabot PRs | 2026-04-28 | Medium | ✅ Complete |
| **4.7** | Tune grouping, labels, ignore rules | 2026-04-28 | Low | ✅ Complete |
| **4.8** | **uv/pnpm strategy refinement** | 2026-04-29 | Low | ✅ Complete |
| **4.9** | Enable Python/uv minimal config | 2026-04-29 | Medium | ✅ Complete |
| **4.10** | **Enable Node/pnpm minimal config** | 2026-04-29 | Medium | ▶️ Current |
| **4.11** | Observe first Node/pnpm Dependabot PR | After 4.10 deploy | Medium | 📋 Plan |
| **4.x** | Evaluate auto-merge for patch updates | 3+ months of clean history | Medium | 📋 Plan |

### Phase 4.8: uv/pnpm Strategy Refinement (Complete)

**What was done:**
- Clarified tool identity vs ecosystem key distinction
- Corrected Python ecosystem from `pip` to `uv` in documentation
- Clarified Node ecosystem uses `npm` key but `pnpm` is execution truth
- Defined Bun governance boundary (not included in Dependabot)
- Defined phased rollout order: uv first, then npm
- Established governance rules for future enablement

### Phase 4.9: Python/uv Minimal Enablement (Complete)

**What was deployed:**
- `.github/dependabot.yml` updated: `package-ecosystem: uv` added
- Schedule: weekly Monday 09:00 Asia/Shanghai
- Open PR limit: 2 per ecosystem
- Labels: `dependencies`, `security/supply-chain`, `python`
- Commit prefix: `deps`
- GitHub Actions ecosystem unchanged
- Config accepted by GitHub; no uv PR generated yet (no-update baseline)

### Phase 4.10: Node/pnpm Minimal Enablement (This Phase)

**What is deployed:**
- `.github/dependabot.yml` updated: `package-ecosystem: npm` added
- Schedule: weekly Monday 09:00 Asia/Shanghai
- Open PR limit: 2 per ecosystem
- Labels: `dependencies`, `security/supply-chain`, `node`, `pnpm`
- Commit prefix: `deps`
- GitHub Actions + uv ecosystems unchanged

**What is NOT deployed:**
- No bun ecosystem
- No auto-merge
- No grouping configuration (baseline observation first)
- npm key is GitHub Node.js adapter — pnpm remains execution truth

### Phase 4.4–4.7: Completed (GitHub Actions Baseline)

- [x] `.github/dependabot.yml` deployed (github-actions only)
- [x] `open-pull-requests-limit: 2` configured
- [x] Labels: `dependencies`, `security/supply-chain`
- [x] First Dependabot PR observed (PR #3: codeql-action 3→4)
- [x] Evidence artifact chain validated for Dependabot PRs
- [x] Dependabot PRs pass CI gates

### Phase 4.9: Python/uv Minimal Enablement (Future)

**Required conditions before enabling:**
- Phase 4.8 sealed with clean verification
- Python/uv Dependabot compatibility confirmed via research
- Governance adapter ready for Dependabot PRs with lockfile changes

**What will be deployed:**
```yaml
- package-ecosystem: uv
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
    uv-patch:
      update-types:
        - patch
    uv-minor:
      update-types:
        - minor
```

**What will NOT be in Phase 4.9:**
- No auto-merge
- No pip ecosystem
- No Node/pnpm ecosystem
- No Bun ecosystem

### Phase 4.10: Python/uv First PR Observation (Future)

Wait for weekly Dependabot scan to produce first uv PR. Verify:
- PR modifies correct files (pyproject.toml + uv.lock)
- CI gates pass (backend-static, verification-fast, secret-scan, repo-governance-pr)
- Evidence artifact is generated
- Lockfile regenerates correctly (or reviewer instructions are clear)

### Phase 4.11: Node/pnpm Minimal Enablement (Future)

**Required conditions before enabling:**
- Phase 4.10 completed with ≥1 clean uv PR observed
- pnpm-lock.yaml compatibility with Dependabot `npm` key confirmed

**What will NOT be in Phase 4.11:**
- No auto-merge
- No npm ecosystem (the key is `npm` but the tool is pnpm)
- No Bun ecosystem

### Phase 4.12: Node/pnpm First PR Observation (Future)

Same observation protocol as Phase 4.10, applied to pnpm-lock.yaml.

## 12. Governance Rules for Dependabot Ecosystem Enablement

These rules apply to all future Dependabot ecosystem enablement phases
(4.9, 4.11, and any future ecosystems):

| # | Rule | Rationale |
|---|------|-----------|
| 1 | **One ecosystem at a time** | Enabling uv + npm simultaneously creates two unknown variables. Isolate each enablement for clean observation. |
| 2 | **No auto-merge** | All Dependabot PRs require human review. This is non-negotiable until 3+ months of clean history. |
| 3 | **Lockfile changes are supply-chain evidence** | Every lockfile modification must be traceable to a Dependabot PR. `uv.lock` and `pnpm-lock.yaml` diffs are audit artifacts. |
| 4 | **Dependabot PRs must pass all CI gates** | `backend-static`, `verification-fast`, `secret-scan`, `repo-governance-pr`, `CodeQL` — no bypass. |
| 5 | **Evidence artifact required** | Each Dependabot PR must produce a verifiable evidence artifact (same as human PRs). |
| 6 | **No CandidateRule or PolicyProposal in enablement phases** | Observation phases (4.9–4.12) are for data collection. Governance rules come after observation. |
| 7 | **Ecosystem key ≠ tool recommendation** | The Dependabot `package-ecosystem` key is an upstream adapter. Project toolchain (`uv`, `pnpm`) remains authoritative. |
| 8 | **pip and npm CLI are not project entry points** | No workflow, script, or CI job should use `pip install` or `npm install` as the primary dependency command. `uv` and `pnpm` are the T0 tools. |

## 13. Non-Goals (Phase 4.10)

Per Ordivon governance:

- ❌ No bun ecosystem enabled
- ❌ No auto-merge
- ❌ No pyproject.toml changes
- ❌ No uv.lock changes (this phase)
- ❌ No package.json changes (this phase)
- ❌ No pnpm-lock.yaml changes (this phase — Dependabot may modify it in future PRs)
- ❌ No CI workflow changes
- ❌ No source code changes
- ❌ No test changes
- ❌ No PR comment / Checks API integration
- ❌ No CandidateRule or PolicyProposal creation
- ❌ No grouping configuration (baseline first)
- ❌ npm key is NOT a directive to use `npm install` — pnpm is the execution truth

## 14. Related Documents

| Document | Relationship |
|----------|-------------|
| `docs/adr/ADR-008-tooling-adoption-strategy.md` | Build/buy decision for Dependabot |
| `docs/architecture/security-platform-baseline.md` | Security gate classification |
| `docs/runtime/codeql-onboarding-plan.md` | Preceding security tool onboarding |
| `docs/runtime/codeql-findings-triage.md` | Triage methodology (reusable for deps) |
| `docs/runtime/verification-ci-gate-plan.md` | CI gate roadmap |
| `docs/runtime/dependabot-first-pr-observation.md` | Phase 4.6 first PR observation |
| `docs/runtime/dependabot-pr3-artifact-validation.md` | Phase 4.7 artifact validation |
