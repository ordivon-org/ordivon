# External Engineering Governance Benchmark Plan (EGB-2)

Status: **CURRENT** | Date: 2026-05-05 | Phase: EGB-2
Tags: `egb-2`, `engineering-governance`, `benchmark`, `process`, `source-registry`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

EGB-2 extends EGB-1 beyond frontier-AI governance frameworks into mature
engineering governance practices from leading open-source projects, software
delivery research, security development lifecycle practice, supply-chain
security, and agent-runtime ecosystems.

This document is a benchmark-informed Ordivon planning anchor. It is not a
compliance claim, certification claim, endorsement claim, partnership claim,
public standard, or production-readiness statement.

## Safe-Language Clause

External references in EGB-2 are used only for internal comparison, design
inspiration, gap analysis, and planning. They do not override Ordivon
governance, authorize action, activate policy, approve publication, approve
release, certify compliance, or establish equivalence to any external project
or framework.

## Source Freshness

Sources checked on 2026-05-05:

| Area | Source | Observed governance signal |
|------|--------|----------------------------|
| Kubernetes ownership | <https://www.kubernetes.dev/docs/guide/owners/> | OWNERS files assign reviewers and approvers for two-phase review; path ownership is machine-consumable. |
| Kubernetes enhancement lifecycle | <https://kubernetes.io/blog/2022/08/11/enhancing-kubernetes-one-kep-at-a-time/> | KEPs require motivation, design, risks, tests, graduation criteria, production readiness review, enhancement freeze, and code freeze. |
| Rust governance | <https://www.rust-lang.org/governance/> | Major decisions start as RFCs; teams own language, compiler, library, infrastructure, moderation, and project leadership surfaces. |
| Python PEP process | <https://peps.python.org/pep-0001/> | PEPs should be focused, have a champion, receive public vetting, and often pair design with prototype/reference implementation. |
| Apache governance | <https://www.apache.org/foundation/how-it-works/> | Projects are governed by PMCs; authority is project-local, consensus-based, and release approval is explicitly held by the PMC. |
| GitHub PR review | <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/about-pull-request-reviews> | PR review supports comment/approve/request-changes states; CODEOWNERS can request relevant reviewers; required reviews can gate merges. |
| Google SRE | <https://sre.google/sre-book/service-best-practices/> | Rollouts are staged and monitored; error budgets balance reliability and launch pace; spent budgets freeze most changes. |
| DORA metrics | <https://dora.dev/guides/dora-metrics/> | Delivery performance is tracked through throughput and instability metrics, including change lead time and change fail rate. |
| Microsoft SDL | <https://www.microsoft.com/en-us/securityengineering/sdl/practices> | Security must be integrated across design, code, build/deploy, run, and zero-trust governance. |
| SLSA | <https://slsa.dev/spec/latest/> | Supply-chain assurance improves through levels, provenance, source/build tracks, and verified artifact properties. |
| OpenSSF Scorecard | <https://github.com/ossf/scorecard> | Security health is evaluated through automated checks such as CI tests, code review, branch protection, token permissions, and vulnerabilities. |
| OpenAI Agents SDK tracing/guardrails | <https://openai.github.io/openai-agents-python/tracing/> and <https://openai.github.io/openai-agents-python/guardrails/> | Agent runs produce traces; guardrails exist but do not cover every tool/handoff path. |
| LangGraph persistence | <https://docs.langchain.com/oss/python/langgraph/persistence> | Agent workflows increasingly persist checkpoints for human-in-the-loop, replay, memory, and fault recovery. |
| MCP authorization | <https://modelcontextprotocol.io/specification/draft/basic/authorization> | Agent tool protocols must address authorization, token audience, token passthrough, confused deputy, and privilege restriction risks. |
| Claude Code skills | <https://docs.claude.com/en/docs/claude-code/skills> | Skills are file-backed capability bundles with frontmatter, supporting files, tool permissions, lifecycle behavior, and invocation controls. |

Future EGB work must re-check official sources before updating benchmark
claims. External source drift is expected.

## Benchmark Findings

### 1. Mature projects separate review from approval

Kubernetes distinguishes reviewer quality feedback from approver holistic
acceptance. GitHub PR review similarly separates comments, approvals, and
requested changes. Ordivon should preserve this separation:

```text
review evidence != approval evidence
READY_WITHOUT_AUTHORIZATION != merge/deploy/release permission
```

Current Ordivon strength: receipt/review language checks already defend this.
Gap: ownership and approver responsibility are not yet path-native across all
governed surfaces.

### 2. Mature projects encode ownership as data

Kubernetes OWNERS and GitHub CODEOWNERS show that ownership works best when it
is path-scoped, machine-readable, and stale-owner-aware. Ordivon currently has
owner fields in registries, but ownership is not yet a first-class governance
manifest with reviewer/approver distinctions, emeritus state, or staleness.

### 3. Mature projects make major changes go through proposal lifecycle

Rust RFCs, Python PEPs, and Kubernetes KEPs all make major changes legible
before implementation. The repeated pattern is:

```text
idea -> focused proposal -> public/reviewable discussion -> implementation evidence -> maturity graduation
```

Ordivon already has stage notes, receipts, and extension processes. The gap is
that it lacks one unified Ordivon Enhancement Proposal (OEP) object for changes
that cut across Core/Pack/Adapter/Checker/Application boundaries.

### 4. Mature projects require graduation criteria

Kubernetes features move through alpha/beta/stable, and KEPs carry test plans
and graduation criteria. Ordivon has checker maturity and phase closure, but
feature maturity is scattered across stage notes, registries, and receipts.

Needed Ordivon invariant:

```text
No feature, checker, pack, adapter, or public wedge moves maturity state
without explicit graduation criteria and evidence.
```

### 5. Mature projects use freeze windows and release readiness gates

Kubernetes enhancement freeze and code freeze create a governance pause that
prevents late churn from hiding unfinished work. Ordivon has baseline gates but
does not yet have a formal "governance freeze" for high-risk stages.

Needed Ordivon concept:

```text
governance_freeze: no new scope, only fixes, receipts, docs, and verification
```

### 6. Mature reliability practice uses budgets, not vibes

Google SRE's error budget turns reliability risk into a shared measurable
constraint. Ordivon should not copy service SLOs directly, but it can adopt the
pattern:

```text
trust budget = allowed DEGRADED/BLOCKED/missing-evidence exposure for a stage
```

If the trust budget is spent, the stage freezes expansion and must repair
evidence, tests, owner gaps, stale docs, or checker coverage before continuing.

### 7. Mature engineering organizations measure throughput and instability

DORA's throughput/instability split maps cleanly to Ordivon governance:

| DORA-style concern | Ordivon analog |
|--------------------|----------------|
| Change lead time | Time from proposal to verified receipt |
| Deployment frequency | Verified governance work units per period |
| Failed deployment recovery time | Time from BLOCKED regression to repaired baseline |
| Change fail rate | Ratio of work units that introduce checker/test failures |
| Rework rate | Ratio of work units reopened because evidence was incomplete |

These metrics must remain diagnostic, not vanity scoring.

### 8. Security governance must span design to run

Microsoft SDL and OpenSSF/SLSA show that security cannot be a late scanner. It
needs design review, threat modeling, secure supply chain, secure environment,
testing, monitoring, and provenance.

Ordivon should treat security gates as a lifecycle:

```text
design threat model -> code/static checks -> build provenance -> package audit
-> runtime evidence -> incident/review lessons
```

Current Ordivon strength: CodeQL/Bandit/pip-audit/Dependabot/Scorecard plans
exist. Gap: supply-chain provenance and release artifact attestation are not yet
first-class trust objects.

### 9. Agent-native work creates new evidence objects

OpenAI traces, LangGraph checkpoints, Claude skills, and MCP authorization
show where agent ecosystems are moving:

```text
trace / checkpoint / skill / hook / tool call / token scope / memory record
```

Ordivon should not run those systems. It should verify the evidence they emit
or the risks their artifacts introduce.

### 10. Guardrails are useful but not complete trust boundaries

Agent runtime guardrails, hooks, skills, and tool permissions help reduce risk,
but they do not replace independent governance. Some guardrails do not cover
all tool/handoff paths; skills can carry tool permissions; MCP can suffer token
audience and confused-deputy failures.

Ordivon position:

```text
runtime guardrail != independent verification
tool available != action authorized
skill capability != permission
trace present != truth
checkpoint present != review
```

## Ordivon EGB-2 Plan

### EGB-2.1 External Source Registry

Create a versioned benchmark source registry:

```text
docs/governance/external-benchmark-source-registry.jsonl
```

Each row should include:

```text
source_id, source_name, source_url, source_kind, owner_area,
last_checked, source_version_or_date, use_allowed, use_forbidden,
ordivon_mapping, freshness_days, notes
```

Purpose: prevent stale external claims and avoid memory-driven benchmark drift.

### EGB-2.2 Ordivon Enhancement Proposal (OEP)

Create an OEP template inspired by RFC/PEP/KEP:

```text
oep_id
title
owner
affected_layers
motivation
non_goals
design
alternatives
risks
security_review
test_plan
rollback_plan
graduation_criteria
authority_impact
public_surface_impact
```

Use OEP only for cross-boundary or high-consequence changes. Small local fixes
should continue to use normal receipts.

### EGB-2.3 Ownership Manifest

Introduce path-native ownership:

```text
docs/governance/ownership-manifest.jsonl
```

Minimum fields:

```text
path_pattern, reviewers, approvers, owner_role, backup_owner,
staleness_days, emeritus_reviewers, notes
```

First scope: docs/governance, docs/product, docs/architecture,
src/ordivon_verify, checkers, scripts, tests.

### EGB-2.4 Reviewer/Approver Split

Encode the difference:

```text
reviewer: can provide quality feedback
approver: can approve maturity transition or closure for a governed surface
owner: accountable for freshness and repair
```

This must not create action authorization. It only governs document/checker
maturity transitions.

### EGB-2.5 Maturity Graduation

Unify maturity across checkers, packs, adapters, public wedges, and major docs:

```text
draft -> shadow_tested -> red_teamed -> active -> stable -> deprecated
```

Every promotion requires:

```text
test evidence
red-team fixture or negative case
owner/approver record
rollback/deprecation path
receipt
registry update
```

### EGB-2.6 Governance Freeze Protocol

Create freeze states:

```text
open_scope
enhancement_freeze
verification_freeze
closure_freeze
closed
```

Freeze rules:

- During enhancement freeze, no new scope enters the stage.
- During verification freeze, only tests, docs, receipts, registry fixes, and
  blocker repairs are allowed.
- During closure freeze, only final receipt/summit/registry synchronization is
  allowed.

### EGB-2.7 Trust Budget Metrics

Add diagnostic metrics:

```text
missing_evidence_count
degraded_duration
blocked_repair_time
checker_false_comfort_count
stale_source_count
registry_drift_count
rework_count
```

If trust budget is spent, expansion freezes until repair.

### EGB-2.8 Delivery and Rework Dashboard

Create a local, read-only report:

```text
scripts/report_governance_delivery_metrics.py
```

It should read receipts, checker logs, registries, and optional ledgers. It
must not call external services or authorize action.

### EGB-2.9 Supply-Chain Evidence Track

Map Ordivon Verify packaging to SLSA/OpenSSF-inspired evidence:

```text
source state
dependency update state
CI/test state
package artifact membership
private-path audit
provenance/attestation future placeholder
```

Do not claim SLSA level. Use "SLSA-inspired evidence track" only.

### EGB-2.10 Agent Evidence Import Boundary

Define read-only import contracts for agent traces, checkpoints, skills, hooks,
and MCP manifests:

```text
OpenAI trace -> event evidence
LangGraph checkpoint -> state evidence
Claude skill -> capability boundary evidence
MCP manifest/auth config -> tool boundary evidence
```

All imports remain verify-only. No adapter may execute an agent, invoke a tool,
refresh a token, or approve external action.

## Immediate Execution Order

1. Create external benchmark source registry.
2. Create OEP template and one dogfood OEP for EGB-2 itself.
3. Add ownership manifest for governed surfaces.
4. Add checker for ownership manifest integrity.
5. Extend checker maturity ledger with reviewer/approver split.
6. Create trust-budget metric model and read-only reporter.
7. Add governance freeze protocol to stage templates.
8. Create SLSA/OpenSSF-inspired supply-chain evidence track for Verify only.
9. Create agent evidence import boundary document.
10. Run read-only baseline and produce EGB-2 receipt.

## Non-Goals

EGB-2 does not:

- Claim Ordivon follows Kubernetes, Rust, Python, Apache, Google, Microsoft,
  DORA, SLSA, OpenSSF, OpenAI, LangGraph, MCP, or Claude governance.
- Create a public standard.
- Activate enterprise process.
- Add a hosted dashboard.
- Run agents.
- Execute MCP tools.
- Authorize merges, deployments, releases, trades, or external actions.
- Replace human judgment.

## Closing Thesis

Top projects do not become trustworthy because they have many checks. They
become trustworthy because checks sit inside ownership, proposal, maturity,
freeze, reliability, security, and review systems.

Ordivon's next improvement should therefore be:

```text
more process-shaped governance, not merely more checker count
```

The target is a flywheel where every new capability enters through a proposal,
has an owner, carries evidence, survives red-team pressure, graduates by
criteria, freezes before closure, and leaves behind lessons that improve the
next cycle.
