# Ordivon Root Context

Status: **DOCUMENTED** (Phase 6R)
Date: 2026-04-29
Phase: 6R
Tags: `ordivon`, `root-context`, `identity`, `governance`, `doctrine`, `ai-onboarding`

## 1. What Ordivon Is

Ordivon is a **governance operating system**.

It is NOT:
- A trading bot
- An AI wrapper or LLM product
- A generic dashboard or admin panel
- A CI pipeline
- A GitHub bot

It IS:
- A system that governs decisions across multiple domains through evidence, policy, shadow evaluation, and human review
- A platform where governance rules are modeled as Policies that progress through a lifecycle: CandidateRule → PolicyProposal → Evidence Gate → Shadow Evaluation → Approval → Activation (deferred)
- An architecture that separates Core (domain-agnostic governance) from Packs (domain-specific business logic), Adapters (external system interfaces), and Evidence (verifiable observation)

### First-Principles Identity

From the Phase 4 Stage Summit:

> Ordivon does not produce financial outcomes. It governs the process by which financial outcomes are pursued. It does not run models. It arranges the evidence, rules, and review loops that surround model behavior. A financial loss that follows governance is acceptable. A financial loss without governance is not.

## 2. Governance Doctrine (Compressed)

These are the non-negotiable rules. Every agent working in Ordivon must follow them.

### 2.1 Evidence Before Belief

Never assume. Always verify. Before asserting any fact about project state, have fresh evidence from a verifiable source (API response, file read, git log, subprocess output).

### 2.2 Fresh > Stale

Evidence has freshness. A check run from 3 hours ago on a pre-patch PR branch is stale if main has since been updated. Always note evidence timestamp and source state.

| Freshness | Action |
|-----------|--------|
| CURRENT (≤60s) | Trust, with timestamp |
| STALE (>1 min, ≤15 min) | Downgrade confidence, prefer re-verify |
| DEGRADED (>15 min) | Do not use for critical decisions |
| MISSING | No evidence — "I don't know" is valid |

### 2.3 Actor Identity from Trusted Metadata

Trust `pr.user.login` and `event.sender.login`. Never trust PR title, body, labels, or branch name for identity. A human can write "deps: bump react" — that doesn't make it a Dependabot PR.

### 2.4 Adapter Output Is Evidence, Not Truth

A policy engine's "reject" is a classification, not a fact about danger. Adapters may have bugs. Output should be recorded and respected, but with awareness of its classification nature.

### 2.5 CandidateRule Is Not Policy

| CandidateRule | Policy |
|---------------|--------|
| Advisory observation | Blocking rule |
| Dry-run mode | Active enforcement |
| Collects data | Blocks CI / rejects PRs |
| No stakeholder sign-off needed | Requires sign-off |

Promotion requires: ≥2 weeks observation, ≥3 real interceptions, documented bypass conditions, stakeholder sign-off.

### 2.6 Shadow Is Not Enforcement

Shadow evaluation produces advisory verdicts (WOULD_EXECUTE, WOULD_ESCALATE, WOULD_REJECT). These inform human judgment but do not block anything. active_shadow is design-ready but runtime-deferred. active_enforced is **NO-GO**.

### 2.7 Human Exception Requires Receipt

If a human overrides governance, record: why, who, when, what evidence, what risk accepted. Unexplained override = governance violation.

### 2.8 Governance Must Reduce Net Risk, Not Maximize Process

A check that fires on every PR and is always ignored is worse than no check. Before adding any gate, ask: what specific risk does it prevent? What's the false positive rate? Who acts on the escalation?

### 2.9 High-Risk Actions Disabled by Default

Place Live Order, Connect Broker API, Enable Auto Trading — permanently disabled with governance reasons. No UI action implies Ordivon placed an order.

## 3. Architecture Layers

```
L10 — Product / Frontend        (apps/web, UI consoles)
L9  — Policy Platform           (domains/policies)
L8  — Learning Platform         (domains/candidate_rules, journal)
L7  — Verification / CI         (scripts/, evals/)
L6  — Intelligence / Runtime    (domains/intelligence_runs)
L5  — Execution / Receipt       (domains/execution_records)
L4  — Capability / API Bridge   (capabilities/)
L3  — Pack Layer                (packs/finance, packs/coding)
L2  — Domain State              (state/)
L1  — Governance Core           (governance/)
L0  — Application Shell         (apps/web layout, runtime)
```

**Guard rule**: Imports flow downward. Core never imports Pack/domain nouns/provider. Upper layers may import lower layers. Lower layers must not import upper layers.

## 4. Tool Truth

| Layer | Tool | Dependabot Key |
|-------|------|---------------|
| Python | uv | `uv` |
| Node | pnpm | `npm` |
| Bun | Not governed | (deferred) |

Dependabot ecosystem key is an upstream parsing adapter — it does NOT represent local execution tool. We use uv and pnpm. pip and npm are NOT primary workflows.

## 5. Current Phase

Phase 1–5: **COMPLETE**
Phase 6: **ACTIVE** (Design Pack, UI Governance, Finance Observation)
Phase 7: **NOT STARTED** (Finance Live Micro-Capital Dogfood)

See `docs/ai/current-phase-boundaries.md` for detailed status.
