# Wiki Architecture

Status: **ACCEPTED** | Date: 2026-04-30 | Phase: DG-1
Tags: `governance`, `wiki`, `architecture`, `navigation`, `discovery`

## 1. Purpose

This document defines the architecture of a future Ordivon documentation wiki.
The wiki is a navigational and discovery surface over the governed document
corpus — it does not replace the documents but provides a structured way to find,
understand, and verify them.

The wiki is **not implemented in DG-1**. This is a design document.

## 2. Wiki's Role

| Function | Tool | How |
|----------|------|-----|
| **Current truth** | `current-phase-boundaries.md` + `AGENTS.md` | Direct file read |
| **Explanation** | Markdown docs | Direct file read |
| **Evidence** | JSONL ledgers | Checker + summary view |
| **Navigation** | Wiki | Curated page structure with metadata |
| **Discovery** | Wiki | Cross-references, related evidence, tags |
| **Conceptual map** | Wiki | How domains relate, what depends on what |
| **Status overview** | Wiki | What's current, stale, archived, deferred |

The wiki is a **read surface** — it does not generate, edit, or enforce documents.
Documents are the source of truth. The wiki reflects them.

## 3. Page Structure

### 3.1 Every Wiki Page Shows

| Field | Description | Source |
|-------|-------------|--------|
| Title | Page title | Document or topic |
| Status | Lifecycle status | `document-lifecycle.md` |
| Authority | Authority level | `document-taxonomy.md` |
| Freshness | Last verified date | Document metadata |
| Owner | Responsible person/role | If known |
| Related evidence | Links to receipts, ledgers, test results | Document metadata |
| Superseded by | Link to replacement | If `superseded` |
| AI read priority | Priority level for AI onboarding | `document-taxonomy.md` |
| Summary | 1-2 paragraph human-readable summary | Document abstract |

### 3.2 Page Types

| Page Type | Used For | Backed By |
|-----------|----------|-----------|
| **Phase** | Phase timeline entry, status, evidence | Stage Summit + phase-boundaries |
| **Pack** | Pack overview, governed objects, contract | Pack contract doc |
| **Topic** | Cross-cutting concept (e.g., "governance loop") | Multiple source docs |
| **Evidence** | Summary of a runtime evidence run, test corpus | Evidence report + ledger |
| **Policy/CandidateRule** | Rule description, status, lifecycle | CandidateRule/Policy doc |
| **Glossary** | Term definition with context | Dictionary curation |
| **Archive** | Navigation into archived documents | Archive index |

## 4. Site Map (Proposed)

```
Home / Current State
├── What is Ordivon?
├── Current Phase: 7P (CLOSED)
├── Phase 8: DEFERRED (3/10)
├── Next: Document Governance Pack (DG-1 active)
├── Boundaries at a glance
├── Quick start for AI agents
└── Quick start for humans

Phase Timeline
├── Phase 1–5: Core Governance (COMPLETE)
├── Phase 6: Design Pack + Finance Observation (COMPLETE)
├── Phase 7P: Alpaca Paper Dogfood (CLOSED)
│   ├── Evidence matrix (3 round trips, 4 refusals, 0 violations)
│   ├── Ledger (30 events, 16 invariants)
│   └── CandidateRules (3 advisory)
├── Phase 8: Live Micro-Capital (DEFERRED)
│   ├── Readiness tracker (3/10)
│   └── Stage gate requirements
└── DG-1: Document Governance Pack (active)

Packs
├── Finance Pack
│   ├── Observation (Alpaca Paper, read-only)
│   ├── Execution (PaperExecutionAdapter)
│   └── Cancel (governed paper cancel)
├── Design Pack
│   ├── Design system
│   ├── Governance components
│   └── UI patterns
├── Coding Pack
│   └── Repo governance
├── Policy Platform
│   ├── CandidateRules
│   └── Policy proposals (deferred enforcement)
└── Document Governance Pack (this one)

Runtime Evidence
├── Paper Dogfood Evidence
│   ├── PT-001 through PT-004 receipts
│   ├── HOLD/REJECT/NO-GO boundary cases
│   └── JSONL ledger + checker output
├── Verification Baseline
│   ├── Pr-fast: 7/7
│   └── Test counts (204 backend, 57 frontend)
├── Eval Corpus
│   └── Eval results
└── Architecture Checker
    └── Architecture verification results

Policy / CandidateRule
├── CandidateRule lifecycle (advisory → Policy path)
├── CR-7P-001: Market-hours awareness (advisory)
├── CR-7P-002: Review-before-next-trade (advisory)
├── CR-7P-003: Cancel lifecycle discipline (advisory)
└── No active Policy (enforcement deferred)

Finance Paper Dogfood
├── Constitution
├── Execution boundary
├── Repeated dogfood protocol
├── Paper trade ledger
├── Ledger schema + invariants
└── Phase 8 readiness tracker

Design System
├── Design tokens
├── Component specifications
├── Governance UI patterns
└── Surface specifications

Document Governance
├── Pack contract
├── Taxonomy
├── Lifecycle
├── Wiki architecture (this page)
├── AI onboarding policy
├── Registry schema
└── Future document checker spec

Archive
├── Phase 4 Stage Summit
├── Phase 5 Stage Summit
├── Phase 6 Stage Summit
├── Old ADRs
├── Superseded documents
└── Consolidated receipts

Glossary
├── Governance terms
├── Architecture terms
├── Finance terms
└── Document governance terms
```

## 5. Navigation Principles

### 5.1 Status Must Be Visible

Every page shows its status visibly. A user navigating to a Phase 8 page should
immediately see "DEFERRED — Phase 8 is not active." A user navigating to an
archived page should see "ARCHIVED — historical reference only."

### 5.2 Boundaries Must Be Visible

Pages for deferred or NO-GO items must clearly state the boundary. The wiki must
not accidentally imply that a deferred item is active.

### 5.3 Evidence Links

Pages should link to their evidence sources:
- Phase pages link to Stage Summit documents
- Trade pages link to trade receipts
- CandidateRule pages link to observation evidence
- Architecture pages link to architecture checker results

### 5.4 Freshness Indicators

Stale pages should display a staleness banner. Fresh pages should show their
last-verified timestamp.

## 6. Technology (Deferred)

The wiki implementation technology is not decided. Options to evaluate in a
future phase:
- Static site generator (e.g., Docusaurus, already in project)
- Markdown-to-wiki renderer
- DB-backed wiki with document ingestion
- Git-backed wiki using existing docs as source

Key requirement: the wiki reflects documents, not replaces them. The document
corpus under `docs/` remains the source of truth.

## 7. Relationship to Docs Directory

```
docs/                         ← Source of truth (files on disk)
  ai/                         ← AI onboarding
  architecture/               ← Architecture docs
  design/                     ← Design specs
  governance/                 ← Document governance (this pack)
  product/                    ← Product strategy, stage summits
  runbooks/                   ← Operational procedures
  runtime/                    ← Runtime evidence, ledgers
    paper-trades/             ← Phase 7P evidence
    archive/                  ← Archived runtime docs
  audits/                     ← Audit reports

wiki/                         ← Future wiki (rendered navigation surface)
  (generated from docs/ + metadata)
```

The wiki is a **derived artifact** — it is generated from the document corpus plus
metadata (registry entries). Changes to docs are reflected in the wiki.

## 8. Non-Goals for DG-1

- Wiki implementation (code, rendering, generation)
- Wiki hosting or deployment
- Wiki search functionality
- Wiki access control or permissions
- Wiki editing interface

DG-1 defines the architecture. Implementation is deferred.
