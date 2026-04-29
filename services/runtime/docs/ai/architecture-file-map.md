# Ordivon Architecture & File Map

Status: **DOCUMENTED** (Phase 6R)
Date: 2026-04-29
Phase: 6R
Tags: `architecture`, `file-map`, `directories`, `code-tree`, `ai-onboarding`

## 1. Directory Tree (Compressed)

```
financial-ai-os/
├── apps/
│   ├── api/                       FastAPI backend (uvicorn)
│   └── web/                       Next.js 15 frontend (React, TypeScript)
│       ├── src/
│       │   ├── app/               App Router pages
│       │   │   ├── page.tsx        / (home)
│       │   │   ├── analyze/        /analyze
│       │   │   ├── audits/         /audits
│       │   │   ├── dashboard/      /dashboard
│       │   │   ├── design/         /design (component workbench)
│       │   │   ├── finance-prep/   /finance-prep (observation layer)
│       │   │   ├── history/        /history
│       │   │   ├── policy-shadow/  /policy-shadow (advisory workbench)
│       │   │   ├── reports/        /reports
│       │   │   └── reviews/        /reviews (supervision workbench)
│       │   ├── components/
│       │   │   ├── features/       Domain feature components
│       │   │   ├── governance/     Ordivon governance UI components
│       │   │   ├── layout/         AppShell, Sidebar
│       │   │   └── workspace/      ConsolePageFrame, WorkspaceProvider
│       │   └── lib/                API client helpers
│       └── package.json            pnpm + Next.js deps
│
├── domains/                        Pure domain models (no ORM, no DB)
│   ├── policies/                   PolicyRecord, state machine, evidence gate
│   ├── candidate_rules/            CandidateRule, draft extraction, bridge
│   ├── journal/                    Review, Lesson, Issue models
│   ├── finance/                    Finance observation models (Phase 6G)
│   ├── finance_outcome/            Manual outcome capture
│   ├── strategy/                   Recommendations, outcomes
│   ├── decision_intake/            Intake repository
│   ├── execution_records/          Execution request/receipt
│   ├── intelligence_runs/          Model runtime records
│   ├── workflow_runs/              Workflow orchestration records
│   ├── research/                   Research models
│   ├── knowledge_feedback/         Feedback/lesson records
│   ├── dashboard/                  Dashboard aggregation service
│   └── ai_actions/                 AI action records
│
├── governance/                     Governance Core (L1)
│   ├── risk_engine.py              RiskEngine.valdiate_intake()
│   ├── policy_source.py            Policy source resolution
│   └── ...
│
├── packs/                          Pack Layer (L3) — domain-specific
│   ├── finance/                    Finance Pack
│   └── coding/                     Coding Pack (5-gate policy)
│
├── adapters/                       External system interfaces
│   └── ...
│
├── scripts/                        CI/CD, verification, governance
│   ├── run_verification_baseline.py  Master gate runner
│   ├── check_architecture.py        Architecture boundary checker
│   ├── check_runtime_evidence.py    Evidence integrity checker
│   └── repo_governance_github_adapter.py  Dependabot/bot PR adapter
│
├── evals/                          Evaluation corpus
│   ├── run_evals.py                Eval runner (24 cases, 3 packs)
│   └── ...
│
├── tests/
│   ├── unit/                       Unit tests (pytest)
│   │   ├── policies/               Policy platform tests (124+ tests)
│   │   ├── finance/                Finance observation tests
│   │   └── ...
│   └── contracts/                  Contract tests
│
├── docs/
│   ├── ai/                         AI onboarding (this directory)
│   ├── architecture/               Architecture decision records
│   ├── design/                     Design Pack + UI specs
│   ├── product/                    Stage summits
│   ├── runtime/                    Closure reviews, red-team reports
│   └── runbooks/                   Agent operating doctrine
│
├── .github/
│   ├── dependabot.yml              Dependabot config (gh-actions, uv, npm)
│   └── workflows/                  CI workflows
│
├── pyproject.toml                  Python project config (uv)
├── uv.lock                         Python lockfile
├── package.json                    Node workspace root
├── pnpm-lock.yaml                  Node lockfile
└── AGENTS.md                       AI agent entry point
```

## 2. Architecture Layer to Directory Mapping

| Layer | Description | Directory |
|-------|-------------|-----------|
| L10 | Product / Frontend | `apps/web/` |
| L9  | Policy Platform | `domains/policies/` |
| L8  | Learning Platform | `domains/candidate_rules/`, `domains/journal/` |
| L7  | Verification / CI | `scripts/`, `evals/`, `tests/` |
| L6  | Intelligence / Runtime | `domains/intelligence_runs/` |
| L5  | Execution / Receipt | `domains/execution_records/` |
| L4  | Capability / API Bridge | `capabilities/` |
| L3  | Pack Layer | `packs/` |
| L2  | Domain State | `state/` |
| L1  | Governance Core | `governance/` |
| L0  | Application Shell | `apps/web/src/components/layout/`, `apps/api/` |

## 3. Import Rules

```
Frontend  ──imports──→  API
Frontend  ──imports──→  Components
Components ──imports──→  (nothing below — UI only)

Governance Core ──imports──→  (nothing domain-specific)
Pack Layer    ──imports──→  Domains, Governance
Domains       ──imports──→  Core types (PolicyRecord, enums)
Adapters      ──imports──→  Domains, Governance
Scripts       ──imports──→  Domains, Governance

NEVER: Core ──imports──→ Pack
NEVER: Domain ──imports──→ Adapter
```

## 4. Testing Conventions

| Language | Runner | Location | Naming |
|----------|--------|----------|--------|
| Python | pytest | `tests/unit/` | `def test_*()` |
| TypeScript | vitest | `src/**/*.test.tsx` | Jest-style `describe`/`test` |

Python tests use standard pytest naming (`def test_*()`). Do NOT use pytest-describe style (`class Describe...` with `def it_...()`). The project does not have pytest-describe installed.

## 5. Key Files for New Agents

| File | What It Is |
|------|-----------|
| `governance/risk_engine.py` | Central intake validator |
| `scripts/repo_governance_github_adapter.py` | Dependabot PR governance adapter |
| `domains/policies/models.py` | PolicyRecord + PolicyState enum |
| `domains/policies/state_machine.py` | Legal/illegal state transitions |
| `domains/finance/__init__.py` | Finance observation models |
| `domains/finance/read_only_adapter.py` | ReadOnlyAdapterCapability |
| `apps/web/src/components/governance/index.tsx` | All governance UI components |
| `scripts/check_architecture.py` | Architecture boundary checker (forbidden patterns) |
