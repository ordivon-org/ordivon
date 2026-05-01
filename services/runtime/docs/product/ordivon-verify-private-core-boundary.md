# Ordivon Verify — Private Core Boundary

Status: **PROPOSAL** | Date: 2026-05-01 | Phase: PV-11
Tags: `product`, `verify`, `boundary`, `private-core`, `open-core`
Authority: `proposal`

## 1. Why Private Core

Keeping the main Ordivon repository private is a strategic choice, not a limitation:

- **Protects unfinished core semantics.** The governance ontology (Core/Pack/Adapter planes) is still evolving. Premature exposure would freeze design.
- **Avoids exposing internal dogfood noise.** Phase 7P paper trades, DG Pack evolution, Post-DG hygiene — valuable internally, confusing externally.
- **Allows product boundary to stabilize.** Ordivon Verify must prove itself as a wedge before the broader system is exposed.
- **Protects future enterprise/kernel strategy.** Rust kernel extraction, commercial governance packs, hosted/enterprise layers — not ready for public scrutiny.

## 2. What Private Core Contains

| Layer | Contents |
|-------|---------|
| **Governance Kernel** | RiskEngine, Policy Platform, candidate rule system, Core/Pack/Adapter ontology |
| **DG Pack History** | All DG-1 through DG-Z phases, verification debt ledger, gate manifest, document registry |
| **Finance Pack** | Alpaca adapters (read-only + paper execution), finance domain models, paper dogfood ledger |
| **Internal Receipts** | Phase 7P stage summit, paper trade receipts, Post-DG closure documents |
| **Long-term Roadmap** | Rust kernel scoping, enterprise governance packs, hosted dashboard, audit/compliance |
| **Operational** | AI onboarding docs (docs/ai/), phase scaffolds, internal prompts, AGENTS.md context |

## 3. What Public Wedge Contains

| Layer | Contents |
|-------|---------|
| **CLI** | `ordivon_verify.py` — extracted, package-ready |
| **Trust Report** | JSON schema, human output format |
| **Validators** | Lightweight receipt/debt/gate/doc validators |
| **Schemas** | Debt ledger, gate manifest, document registry schemas |
| **Fixtures** | Bad/clean/standard external fixtures for dogfood + testing |
| **Agent Skill** | SKILL.md for AI coding agents |
| **CI Example** | GitHub Action workflow (example only) |
| **Docs** | README, quickstart, adoption guide, CLI contract, CI example, PR comments |

## 4. Boundary — What Crosses, What Doesn't

| Can Cross to Public | Must Stay Private |
|--------------------|-------------------|
| Ordivon Verify CLI | RiskEngine source |
| Verify trust report schema | Policy Platform |
| External fixture ladder | Alpaca adapter implementations |
| Agent skill (SKILL.md) | Finance domain models |
| GitHub Action example | Paper dogfood ledger |
| PR comment templates | Phase 7P stage summit |
| Public README / quickstart | DG Pack full history |
| Package structure | docs/ai/ onboarding docs |
| Schemas (debt/gate/docs) | Rust kernel design |
| | Commercial roadmap |

## 5. Long-Term Open-Core Model

If Ordivon evolves to a multi-product governance platform:

| Tier | Contents | License |
|------|---------|---------|
| **Open** | Ordivon Verify CLI, schemas, agent skill, examples | Apache-2.0 |
| **Source-Available** | Governance packs (enterprise), advanced policy packs | BSL / commercial |
| **Private** | Hosted dashboard, audit/compliance layer, kernel | Proprietary |

This is a long-term vision, not a current plan.

## 6. Linux Route Analysis

Q: Could Ordivon follow the Linux model — open-source kernel, commercial ecosystem?

A: Yes, long-term. But not by opening the full private repo now. The path is:
1. Curate public wedge (Ordivon Verify) — **current phase**
2. Open Verify as Apache-2.0
3. Expand public surface incrementally (schemas, governance packs)
4. Eventually open Core with governance maturity

Linux started as a hobby kernel and grew. Ordivon starts as a governance OS and can grow outward through curated wedges.

## 7. What This Boundary Protects

| Protects | From |
|----------|------|
| Unfinished governance design | Premature external scrutiny |
| Internal dogfood history | Confusion with product maturity |
| Commercial flexibility | Premature open-source commitment |
| Future enterprise strategy | Competitor visibility |
| Product focus | Feature creep from open-source demands |

## 8. Non-Activation Clause

This document defines a boundary proposal. It does not change repository visibility, apply any license, publish any code, or authorize any action.
