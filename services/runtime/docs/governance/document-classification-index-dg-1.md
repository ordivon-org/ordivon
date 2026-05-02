# Document Classification Index (DG-1)

Status: **current** | Date: 2026-05-02 | Phase: DG-1
Tags: `dg-1`, `classification`, `index`, `truth-substrate`, `detector-consumable`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

This is the canonical classification index for Ordivon governance documents.
It defines the dimensions by which every governed document is classified,
making the document system consumable by ADP-3 detectors, PV surface checks,
New AI Context Checks, and human reviewers.

## Classification Dimensions

### 1. Governance Plane

Every document belongs to one governance plane:

| Plane | Description | Example docs |
|-------|-------------|-------------|
| `truth_governance` | Defines current project identity, status, boundaries | AGENTS.md, current-phase-boundaries.md, root-context.md |
| `document_governance` | Governs the document system itself | document-registry.jsonl, taxonomy, lifecycle, authority model |
| `verification_governance` | Verification checkers, detectors, debt tracking | ADP detector, receipt checker, debt ledger |
| `product_governance` | Product identity, stage summits, contracts | Stage Summit docs, product notes, versioning policy |
| `action_governance` | Governs what actions are allowed/blocked/NO-GO | Phase boundaries, capability declarations, risk ladder |
| `evidence` | Runtime evidence, receipts, ledgers | Closure receipts, paper dogfood ledger, runtime docs |
| `exposure_governance` | Public surface, package, release boundaries | PV public-surface docs, package manifest, changelog policy |
| `archive` | Historical records, superseded docs | Archived receipts, superseded runtime docs |

### 2. Artifact Type

| Type | Description | Authority default |
|------|-------------|-------------------|
| `root_context` | Root entry point (AGENTS.md) | source_of_truth |
| `ai_onboarding` | AI agent onboarding docs | current_status |
| `phase_boundary` | Current phase boundaries | source_of_truth |
| `governance_pack` | Governance pack contracts, policies, taxonomies | source_of_truth or current_status |
| `architecture` | Architecture decision records, ontologies | source_of_truth |
| `design_spec` | Design specifications, contracts | source_of_truth or proposal |
| `stage_summit` | Phase closure summits | source_of_truth (current phase) or supporting_evidence (historical) |
| `closure_receipt` | Phase closure receipts with verification | supporting_evidence |
| `runtime` | Runtime evidence, closure reviews | supporting_evidence |
| `runbook` | Operating procedures, how-to guides | current_status |
| `schema` | JSON schemas, JSONL ledgers, manifests | source_of_truth |
| `ledger` | JSONL evidence ledgers | supporting_evidence |
| `tracker` | Readiness trackers, status trackers | current_status |
| `receipt` | Individual task/phase receipts | supporting_evidence |
| `product` | Product notes, stage notes | source_of_truth |
| `template` | Prompt templates, receipt templates | example |
| `fixture` | Test fixtures | supporting_evidence |

### 3. Authority

| Authority | Can define current truth? | Can authorize action? | Detector consumable? |
|-----------|--------------------------|----------------------|---------------------|
| `source_of_truth` | YES | NO | YES — stable |
| `current_status` | YES (phase/status only) | NO | YES — requires freshness |
| `supporting_evidence` | NO | NO | YES — evidence only |
| `historical_record` | NO | NO | Conditional — archive context |
| `proposal` | NO (not adopted) | NO | Conditional — not binding |
| `example` | NO (illustrative) | NO | Conditional — not normative |
| `archive` | NO | NO | NO — must not be current |

**Invariant**: No authority type can authorize a live financial action, broker write,
auto-trading, or credential access. Authority is about truth, not execution permission.

### 4. AI Read Priority

| Priority | When to read | Examples |
|----------|-------------|----------|
| L0 | First — before any work | AGENTS.md |
| L1 | Before any task | root-context, boundaries, working-rules, architecture-map, output-contract |
| L2 | Before domain-specific work | governance pack docs, stage summits, product notes |
| L3 | Contextual, as needed | runtime evidence, ledgers, individual receipts |
| L4 | Only when explicitly needed | archive, historical records, individual trade receipts |

### 5. Detector Consumability

| Flag | Meaning |
|------|---------|
| `true` | Document is parsed by ADP-3 structure/registry/PV checks |
| `false` | Document is not directly consumed by detectors |

Detector-consumable docs must maintain stable authority, status, and freshness fields.

### 6. Public Surface Relevance

| Flag | Meaning |
|------|---------|
| `true` | Document touches public/package/release surface — PV checks apply |
| `false` | Internal-only document |

### 7. Freshness

| Field | Required for | Description |
|-------|-------------|-------------|
| `last_verified` | L0/L1 docs, source_of_truth docs | ISO 8601 date of last verification |
| `stale_after_days` | L0/L1 docs, source_of_truth docs | Days before doc is considered stale |
| `freshness_owner` or `owner` | DEGRADED entries | Who is responsible for freshness |

### 8. Lifecycle

| Field | Description |
|-------|-------------|
| `supersedes` | doc_id this document replaces |
| `superseded_by` | doc_id that replaces this document (must NOT be `current`) |
| `status` | current, accepted, closed, superseded, archived, deferred, draft |

## Registry Stats (as of DG-1)

| Metric | Count |
|--------|-------|
| Total entries | 79 |
| source_of_truth | 26 |
| current_status | 22 |
| supporting_evidence | 28 |
| historical_record | 0 |
| High-priority AI (L0-L1) | 22 |
| With last_verified | 8 |
| With stale_after_days | 6 |
| Stale + superseded | 1 |
| Doc types | 15 |
| No freshness violations | 0 |
| No completeness violations | 0 |
