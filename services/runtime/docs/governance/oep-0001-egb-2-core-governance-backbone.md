# OEP-0001: EGB-2 Core Governance Backbone

Status: **shadow_tested** | Date: 2026-05-05 | Phase: EGB-2
Owner: EGB
Authority: proposal

## Summary

EGB-2 adds a benchmark-informed governance backbone: external source registry,
OEP process, ownership manifest, freeze protocol, trust-budget reporting, and
read-only boundaries for supply-chain and agent evidence.

## Required Metadata

- oep_id: OEP-0001
- title: EGB-2 Core Governance Backbone
- owner: EGB
- status: shadow_tested
- affected_layers: docs, checker, scripts, stage-template
- authority_impact: evidence only; no action authorization
- public_surface_impact: docs only

## Motivation

Ordivon already has many checkers, registries, receipts, and stage documents.
EGB-2 turns external engineering governance lessons into process-shaped
controls so Ordivon does not merely add more checks. The goal is a local
proposal, ownership, maturity, freeze, and diagnostic metric loop.

## Non-Goals

- No public standard.
- No compliance, certification, endorsement, partnership, or equivalence claim.
- No release approval.
- No policy activation.
- No agent runtime or MCP tool execution.
- No merge, deploy, trading, publication, or external action authorization.

## Design

The EGB-2 core backbone adds:

- external benchmark source registry
- OEP process and template
- ownership manifest
- full-profile escalation checkers for source registry, OEP, and ownership
- freeze protocol fields in stage templates
- local trust-budget and delivery metrics reporter
- supply-chain evidence boundary document
- agent evidence import boundary document

The first version is shadow-first. New checkers are full-profile escalation
checks and do not enter pr-fast.

## Alternatives

- Hard-gate immediately: rejected because historical governance data could be
  blocked before the new process is calibrated.
- Docs only: rejected because Ordivon requires machine-verifiable governance
  where practical.
- Implement all supply-chain and agent import checkers now: deferred to avoid
  widening Alpha/EGB scope before the core process stabilizes.

## Risks

- Process inflation: mitigated by requiring OEP only for cross-boundary or
  high-consequence changes.
- False comfort: mitigated by keeping new checks escalation-only until fixtures
  and red-team cases mature.
- External benchmark drift: mitigated by source registry freshness windows.
- Authorization laundering: mitigated by forbidden-language checks and repeated
  evidence-only boundaries.

## Security Review

EGB-2 core does not add network calls, tokens, agent execution, external tool
execution, package publication, or deployment. It adds local read-only checks
and documents security/supply-chain evidence boundaries.

## Test Plan

- Source registry fixtures: valid, missing field, stale, forbidden language.
- OEP fixtures: valid, missing required sections, authorization laundering.
- Ownership fixtures: valid, missing role, invalid staleness, missing coverage.
- Stage runner tests: freeze protocol appears in dry-run and receipt while old
  templates remain compatible.
- Delivery metrics tests: JSON output is stable and read-only.

## Rollback Plan

Remove EGB-2 checkers from the checker registry discovery path by deleting the
checker directories, remove the EGB-2 JSONL registries and docs, and revert
stage-template freeze fields. Since EGB-2 is shadow-first, rollback does not
need to relax pr-fast hard gates.

## Graduation Criteria

- Shadow-tested: source registry, OEP, ownership, freeze, and reporter tests
  pass locally.
- Red-teamed: negative fixtures catch forbidden external claims, missing
  required OEP sections, and ownerless path coverage.
- Active: one later phase promotes selected EGB-2 checkers after owner approval
  and receipt evidence.
- Stable: at least two stages use OEP/ownership/freeze without false comfort.

## Authority Boundary

This OEP is evidence for review only. It does not authorize merge, release,
deployment, publication, trading, policy activation, or external action.
