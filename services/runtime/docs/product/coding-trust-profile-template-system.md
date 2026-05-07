# Coding Trust Profile Template System

Status: **CURRENT** | Date: 2026-05-08
Phase: Coding-Trust-Template-System
Authority: `source_of_truth` | AI Read Priority: 1

## Thesis

Ordivon Verify Coding is AI trust infrastructure, not project-specific
governance outsourcing.

```text
AI writes.
Project AI localizes evidence.
Project owner/reviewer decides.
Ordivon Verify checks trust structure.
```

The Coding profile provides reusable evidence templates, discovery hints, trust
signals, and non-authorization boundaries. It must not decide a target
project's canonical gates, release readiness, tool permission, workflow policy,
or owner approval.

CTTS-1 created the generic template system. CTTS-2 validates localization with
dogfood fixtures and a casebook: project AI fills local evidence, while OV keeps
checking structure and boundary language only.

CTTS-3 adds the adoption pack: OV can emit the generic template files into an
explicit output directory for a target project AI to localize. The export is
still not project authority; it is a starter pack plus discovery hints.

## Template Tiers

### minimal

Reminder-level evidence loop for solo developers and vibe-coding projects.

Required template surfaces:

- `ordivon.verify.json`
- `PROJECT_AI_LOCALIZATION.md`
- `AI_TRUST_LEVELS.md`
- `governance/agent-claim-bindings.jsonl`
- `receipts/external-audit-receipt.md`
- `governance/project-ai-onboarding-playbook.md`
- `governance/discovery-candidates.json`

### standard

Basic project AI evidence system for maintained repositories.

Adds:

- `governance/verification-gate-manifest.json`
- `governance/verification-debt-ledger.jsonl`
- `governance/document-registry.jsonl`

### deep

Long-lived team workflow for agent-heavy projects.

Adds:

- `governance/release-claim-map.jsonl`
- `governance/skill-safety-report.json`
- `governance/tool-boundary-map.jsonl`
- `governance/memory-source-ledger.jsonl`
- `governance/lesson-ledger.jsonl`
- `governance/candidate-rule-drafts.jsonl`

## Trust Levels

| Level | Meaning | OV boundary |
|---|---|---|
| L0 Unobserved | AI wrote without structured record | Not READY |
| L1 Claimed | AI claims completion | Claim only |
| L2 Evidenced | Artifacts, tests, receipt exist | Evidence can still be weak |
| L3 Reviewed | Review evidence exists | Review is not approval |
| L4 Gate-Checked | Owner-confirmed gates passed | Still not authorization |
| L5 Release-Evidence | Release/debt/skill/tool surfaces handled | Evidence only |
| L6 Authorized | Project owner authorizes action | OV never emits this |

OV emits only `READY_WITHOUT_AUTHORIZATION`, `DEGRADED`, or `BLOCKED`.

## Project AI Localization Flow

1. Read project docs, tests, workflows, skills, release notes, and local policy.
2. Treat `discovery-candidates.json` as hints, not authority.
3. Choose `minimal`, `standard`, or `deep`.
4. Propose local canonical gates and evidence surfaces.
5. Ask the project owner/reviewer to confirm gate authority and boundaries.
6. Fill templates with project-local evidence.
7. Run OV in `vibe`, `merge`, then `release` stages as needed.
8. Convert `DEGRADED` or `BLOCKED` into evidence repair, claim downgrade, or debt.
9. Close a receipt with lessons and optional CandidateRule or no-rule rationale.

## CTTS-3 Adoption Command

```bash
ordivon-verify check <repo> --profile coding --risk-stage vibe \
  --suggest-config --template minimal --emit-template-dir <out>
```

`--emit-template-dir` writes only to the explicit output directory. The target
repository is not modified unless the user intentionally points the output
directory inside it. Template bodies stay project-independent; project
observations stay in `governance/discovery-candidates.json`.

Adoption sequence:

1. Run discovery.
2. Emit `minimal`, `standard`, or `deep` template pack to a review directory.
3. Target project AI reads `PROJECT_AI_LOCALIZATION.md` and
   `AI_TRUST_LEVELS.md`.
4. Project AI fills local evidence.
5. Owner/reviewer confirms canonical gates and authority boundaries.
6. Rerun OV at `vibe`, `merge`, or `release`.

## Agent-Native Evidence Pack

Coding Trust release-stage audits now treat these as read-only evidence
surfaces:

- Skill/tool boundaries: `SKILL.md`, `allowed-tools`, scripts, credentials, and
  authorization wording.
- Memory/content hygiene: source receipt, freshness, scope, authority, and
  CandidateRule/Policy separation.
- Harness/trace import: trace presence, checkpoint claims, failed tool calls,
  review nodes, and receipt authorization leakage.

OV does not execute skills, run tools, start servers, call SDKs, refresh tokens,
or decide whether evidence is business-approved.

## New AI Context Check

A new AI reading the normal onboarding path must be able to answer:

1. CTTS is the Coding Trust Template System for project-local AI evidence.
2. Template placeholders are generic; project-local evidence is filled by the
   target project's AI or owner.
3. `discovery-candidates.json` contains hints only.
4. Candidates are not canonical gates until owner/reviewer confirmation.
5. `minimal`, `standard`, and `deep` are adoption tiers, not separate products.
6. `READY_WITHOUT_AUTHORIZATION` means evidence sufficiency only.
7. OV cannot grant merge, release, deploy, execution, tool, or skill permission.
8. `DEGRADED`/`BLOCKED` should become evidence repair, claim downgrade, or debt.
9. CandidateRule is advisory until separately promoted by project policy.
10. Skill/tool/workflow existence is capability or evidence, not permission.

## Non-Authorization Boundary

The templates and reports do not authorize merge, release, deploy, execution,
token refresh, tool use, policy activation, trading, or external action.

External benchmark practices such as DORA, SRE, Kubernetes OWNERS, GitHub
CODEOWNERS, OpenAI tracing, Claude Skills, and MCP authorization are design
inputs only. They do not create compliance, certification, endorsement,
partnership, equivalence, production-readiness, or public-standard claims.
