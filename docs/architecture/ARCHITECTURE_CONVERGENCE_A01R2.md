# Architecture Convergence A01-R2 — Current-Source Authority Audit

Date: 2026-09-21
Status: ACCEPTED / SUPERSEDES STALE HISTORICAL A01 CONCLUSION

## Scope

This audit corrects an earlier architecture census that inspected historical pre-retirement Agent Service source.

Current canonical source is the Ordivon monorepo plus its accepted current-source owner subtrees. The historical Agent Service is **RETIRED** and MUST NOT be reconstructed.

## Current owners

| Concern | Current natural owner | Standing |
|---|---|---|
| physical Workspace / Job / Attempt / execution / cancellation / Artifact | Runtime | KEEP |
| semantic external-continuity checkpoint / re-entry / Board collaboration | Host | KEEP |
| bounded Agent Run, model/context loop, provider/tool continuity | Harness | KEEP |
| Skill procedure/package semantics | Agent Skills / client | ADOPT |
| MCP transport/capability semantics | MCP client/server owners | ADOPT |
| portable Plugin envelope | Agent Plugins standard/client | ADOPT |
| external effects | Distribution/provider-native APIs | KEEP EXTERNAL |
| authentication / credentials / OAuth grants | provider/IAM/OAuth owner | KEEP EXTERNAL |
| long-lived workflow/orchestration when needed | Temporal/BPM/native owner | KEEP EXTERNAL |
| scientific/domain semantic truth | study/domain owner | KEEP EXTERNAL |
| northbound compatibility/routing/projection | planned thin Gateway | BUILD NON-AUTHORITATIVE RESIDUAL |

## Historical Agent Service interpretation

The deleted Agent Service tables and coordinators remain useful historical requirements evidence, not forward implementation authority. They established useful non-regression distinctions—semantic work is not one Runtime Job, unknown external outcomes must be reconciled before unsafe retry, process success is not semantic completion, credentials/effect authority stay external, and projections do not become canonical truth.

Those invariants survive only where current owners need them. The old SQLite control plane, Goal/Task/Session stores, transport/credential stores, failover coordinators, MCP canary, and provider-specific adapters remain retired.

## Current-source non-regression rule

Per `meta/next/policies/external-ownership-boundary.json`:

- Agent Service type ceiling is empty;
- reintroduction requires a new externally owned, non-authoritative integration justification;
- permitted post-baseline local roles are adapter/client/error/projection/reader/verifier;
- no old Agent Service compatibility path is accepted.

Gateway B01 is therefore admissible only as an adapter/projection over natural owners.

## Corrected architecture

```text
Client / ChatGPT
      |
      v
Cloudflare / OAuth edge
      |
      v
Thin Ordivon Gateway
 stable MCP ABI
 capability projection
 owner routing
 error/correlation normalization
      |
 +----+---------+----------------+
 |              |                |
 v              v                v
Runtime         Host          Harness / providers
physical        continuity    Agent Run / effects
truth           truth
```

Skills and Agent Plugins remain independently consumable package surfaces. Method Router is a Skill, not Gateway authority.

## Verdict

- old Agent Service: **RETIRED / DO NOT RECONSTRUCT**
- Runtime: **KEEP**
- Host: **KEEP**
- Harness: **KEEP**
- Modular Monorepo: **CURRENT PRIMARY SOURCE**
- Gateway: **BUILD THIN NON-AUTHORITATIVE RESIDUAL**
- Method Router: **BUILD AS SKILL**
- Tool Binding: **BUILD AS REBUILDABLE PROJECTION ONLY**
