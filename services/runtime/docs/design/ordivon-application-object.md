# Ordivon Application Object Baseline

Status: **PROPOSED** (Phase 6A)
Date: 2026-04-29
Phase: 6A
Tags: `design`, `application-object`, `ordivon`, `surface-registry`, `ui`

## 1. Purpose

Ordivon is the first Application Object governed by the Design Pack.
This document defines Ordivon as a design-governed entity: its surfaces,
navigation architecture, data bindings, governance surfaces, and
high-risk action map.

An Application Object is a concrete system that the Design Pack governs.
Ordivon is the reference implementation. Future Application Objects
(e.g., a broker dashboard, a compliance console) would follow the same
pattern.

## 2. AppManifest

```text
AppManifest
  app_id: "ordivon"
  name: "Ordivon Governance Platform"
  version: "2026-04"
  design_pack_version: "6A"
  surface_registry: SurfaceRegistry
  design_token_set_id: "ordivon-core-tokens"
  console_inventory: ConsoleInventory
  maturity: "prototype"       # prototype / preview / production
  governance_layer_count: 10
  governed_packs: ["coding", "finance", "design", "policy"]
```

## 3. SurfaceRegistry

Every governed surface in the Ordivon application.

| Surface ID | Name | Route | Layer | Maturity |
|-----------|------|-------|-------|----------|
| `home` | Live Command Center | `/` | L0 | real |
| `analyze` | Analysis Workspace | `/analyze` | L1-L2 | real |
| `reviews` | Supervision Workbench | `/reviews` | L3 | real |
| `capabilities` | Capabilities Map | `/capabilities` | L4 | real |
| `state` | Trace & Outcome Graph | `/state` | L5 | real |
| `knowledge` | Feedback & Candidate Console | `/knowledge` | L6 | real |
| `execution` | Request & Receipt Console | `/execution` | L7 | real |
| `intelligence` | Runtime & Context Console | `/intelligence` | L8 | preview |
| `governance` | Decision & Approval Console | `/governance` | L9 | preview |
| `orchestration` | Workflow Run Console | `/orchestration` | L10 | future |
| `infrastructure` | Scheduler / Monitoring | `/infrastructure` | — | future |
| `pack-finance` | Finance Pack Console | `/packs/finance` | — | preview |
| `adapter` | External Adapter Console | `/adapters` | — | future |
| `shadow-policy` | Shadow Policy Workbench | `/policy/shadow` | — | future |

## 4. NavigationMap

```text
Primary Navigation:
  Home (Command Center)
  Analyze (Workspace)
  Reviews (Supervision)
  State (Trace & Outcome)
  Knowledge (Learning)
  Governance (Decisions)

Secondary Navigation:
  Execution (Receipts)
  Intelligence (Runtime)
  Capabilities (Map)

Tertiary / Future:
  Orchestration (Workflows)
  Infrastructure (Monitoring)
  Packs (Finance, Coding, Design)
  Adapters (External)
  Policy (Shadow Workbench)
```

## 5. InformationArchitecture

```
Ordivon Application
├── Command Center (home)
│   ├── Live Status Overview
│   ├── Recent Governance Decisions
│   ├── Active Policy Summary
│   └── Quick Actions
├── Analysis Workspace (analyze)
│   ├── New Analysis Intake
│   ├── Analysis History
│   └── Analysis Detail
├── Supervision Workbench (reviews)
│   ├── Review Queue
│   ├── Review Detail
│   ├── Lesson Extraction
│   └── Candidate Rule Draft
├── Trace & Outcome Graph (state)
│   ├── Decision Trace
│   ├── Execution Trace
│   └── Outcome Timeline
├── Learning Console (knowledge)
│   ├── Candidate Rules
│   ├── Policy Proposals
│   ├── Lessons Library
│   └── Evidence Explorer
├── Governance Console (governance)
│   ├── Decision History
│   ├── Approval Queue
│   └── Policy Registry
├── Execution Console (execution)
│   ├── Request History
│   └── Receipt Detail
├── Runtime Console (intelligence)
│   ├── Model Registry
│   ├── Task History
│   └── Context Viewer
├── Finance Pack Console (packs/finance)
│   ├── Decision Intake
│   ├── Outcome Registry
│   └── Risk Monitor
└── Shadow Policy Workbench (policy/shadow)
    ├── Policy Draft Editor
    ├── Shadow Evaluation Results
    ├── Evidence Gate Output
    └── Approval Workflow
```

## 6. DesignTokenBinding

```text
Ordivon Core Design Tokens:
  color-primary: #0A0F1F (deep navy)
  color-surface: #111827 (dark surface)
  color-surface-alt: #1F2937 (elevated surface)
  color-accent: #3B82F6 (blue accent)
  color-accent-alt: #8B5CF6 (purple accent)
  color-success: #10B981 (green)
  color-warning: #F59E0B (amber)
  color-danger: #EF4444 (red)
  color-text-primary: #F9FAFB
  color-text-secondary: #9CA3AF
  color-border: #374151
  font-family: Inter, system-ui, sans-serif
  font-size-base: 14px
  font-size-lg: 16px
  font-size-xl: 20px
  font-size-2xl: 24px
  spacing-unit: 4px
  radius-sm: 4px
  radius-md: 8px
  radius-lg: 12px
  shadow-sm: 0 1px 2px rgba(0,0,0,0.3)
  shadow-md: 0 4px 6px rgba(0,0,0,0.4)
```

## 7. ComponentUsageMap

| Component | Used On | Governance Binding |
|-----------|---------|-------------------|
| `DecisionCard` | reviews, governance, home | Shows verdict + reasons |
| `EvidenceBadge` | reviews, governance, policy | Shows freshness + type |
| `PolicyStateIndicator` | policy, governance | Shows lifecycle state |
| `RiskBadge` | analyze, reviews, finance | Shows risk level |
| `ReviewActionBar` | reviews | Accept / Reject / Escalate |
| `SurfaceHeader` | all surfaces | Surface name + maturity badge |
| `PreviewBanner` | preview surfaces | "PREVIEW — NOT PRODUCTION" |
| `MockDataLabel` | all with sample data | "SAMPLE DATA" |
| `HighRiskActionButton` | finance, execution | Confirmation required |
| `GovernanceDecisionTimeline` | governance, state | Decision history |

## 8. DataBindingMap

| Surface | Data Source | Refresh | Mock Fallback |
|---------|------------|---------|---------------|
| Command Center | `/api/v1/dashboard` | 30s | Yes |
| Analysis Workspace | `/api/v1/analyze` | on demand | Yes |
| Review Queue | `/api/v1/reviews` | on demand | Yes |
| Decision Trace | `/api/v1/audits` | on demand | Yes |
| Execution Receipt | `/api/v1/execution` | on demand | Yes |
| Candidate Rules | `/api/v1/knowledge/candidate-rules` | on demand | Yes |
| Policy Registry | (not yet connected) | — | — |
| Shadow Workbench | (not yet connected) | — | — |

## 9. GovernanceSurfaceMap

Surfaces that display governance decisions and their data requirements.

| Surface | Shows | Requires |
|---------|-------|----------|
| Command Center | Recent decisions, active policies | `/api/v1/dashboard` |
| Review Detail | Decision reasons, severity | `/api/v1/reviews/{id}` |
| Decision Timeline | Decision history, evidence chain | `/api/v1/audits` |
| Policy Registry | Active policy list, states | (future) |
| Shadow Workbench | Shadow evaluation results | (future) |

## 10. EvidenceSurfaceMap

Surfaces that display evidence artifacts and their labeling requirements.

| Surface | Evidence Type | Label |
|---------|--------------|-------|
| Review Detail | repo-governance-report | "CI Artifact" |
| Decision Timeline | AuditEvent | Timestamp + actor |
| Candidate Rule | source_refs, lesson_ids | "Evidence Chain" |
| Shadow Result | matched_evidence_refs | Freshness badge |
| Execution Receipt | side_effects: false | "Read-Only" |

## 11. HighRiskActionMap

Actions that must be explicitly confirmed or are disabled by default.

| Action | Surface | Risk | Default State |
|--------|---------|------|--------------|
| Merge Dependabot PR | reviews | Medium | Requires confirmation |
| Activate Policy | policy/shadow | High | Disabled (Phase 5 NO-GO) |
| Execute Finance Trade | packs/finance | Critical | Disabled (Phase 7 gate) |
| Modify Pack Policy | governance | High | Requires confirmation |
| Promote CandidateRule | knowledge | Medium | Requires confirmation |
| Rollback Policy | governance | High | Requires dual confirmation |
| Edit RiskEngine config | governance | Critical | Disabled by default |

## 12. Non-Goals

- This document does not implement any UI.
- This document does not require a CSS framework or component library.
- Surface maturity labels are aspirational until implementation.
- Data bindings are design contracts, not API specifications.
- High-risk action defaults apply to design proposals, not runtime enforcement.
