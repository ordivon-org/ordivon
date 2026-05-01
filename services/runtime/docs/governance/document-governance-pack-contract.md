# Document Governance Pack Contract

Status: **ACCEPTED** | Date: 2026-04-30 | Phase: DG-1
Tags: `governance`, `document`, `pack`, `contract`, `taxonomy`, `lifecycle`, `wiki`

## 1. Purpose

This contract defines the Document Governance Pack — a governed Pack that treats
all Ordivon project documentation as first-class system objects subject to
governance, lifecycle rules, authority constraints, and freshness enforcement.

Documents are not static text. They are system memory, evidence, governance
constraints, and AI onboarding surfaces. A stale document is a governance risk.
A duplicated document is a divergence risk. A missing authority marker is an
interpretation risk.

This pack establishes the rules by which Ordivon governs its own knowledge.

## 2. Scope

The Document Governance Pack governs all project documentation under `docs/`,
root-level context files (`AGENTS.md`), and identity-bearing surfaces that
can mislead humans, AI agents, package consumers, or future public extraction.

| In Scope | Out of Scope |
|----------|-------------|
| `docs/` markdown files | Source code comments |
| Root AI context files (AGENTS.md, README.md) | README files in dependency repos |
| JSONL ledgers (evidence schema) | Lint/formatter config files |
| ADRs in docs/ | CI workflow YAML (except identity-bearing conf) |
| Stage Summit receipts | Lockfiles |
| Runtime evidence docs | Test data fixtures |
| Product/architecture docs | App runtime state |
| AI onboarding docs | Database migration files |
| Future wiki pages | Generated files |
| **Identity-bearing surfaces:** | **Excluded from identity check:** |
| `pyproject.toml` (project name) | Runtime config values |
| `package.json` (package name) | API keys, secrets, tokens |
| `apps/*/package.json` (sub-package names) | Duplicate metadata in lockfiles |
| `apps/*/pyproject.toml` (sub-project names) | |
| `README.md` (opening identity header) | |
| `tests/conftest.py` (legacy env pollution) | |

Identity surface governance is about current-truth identity — preventing
stale brand/name references from misrepresenting the project. It does not
govern runtime configuration semantics.

## 3. Non-Goals

- Document Governance Pack does NOT replace the Design Pack, Coding Pack, Finance Pack, or Policy Platform.
- Document Governance Pack does NOT enforce Policy on code changes.
- Document Governance Pack does NOT auto-delete or auto-archive documents.
- Document Governance Pack does NOT create a CMS or DB-backed doc store in this phase.
- Document Governance Pack does NOT activate Policy or RiskEngine for documentation rules.
- Document Governance Pack does NOT change Phase 7P closure status or enable Phase 8.

## 4. Governed Objects

| Object | Definition |
|--------|-----------|
| **Document** | A markdown file, JSONL ledger, or future wiki page in the project docs tree. |
| **Document Type** | Classification in the taxonomy (e.g., receipt, stage_summit, ADR). |
| **Document Status** | Lifecycle stage (draft, proposed, current, closed, deferred, superseded, archived, stale). |
| **Authority Level** | Weight class (source_of_truth, current_status, supporting_evidence, historical_record, proposal, example, archive). |
| **Freshness** | Last verified timestamp. Stale docs lose authority. |
| **Document Registry** | Future manifest linking doc_id → type, status, authority, freshness, relationships. |
| **Wiki Page** | Future navigational surface displaying doc metadata and links. |
| **Ledger** | Machine-readable JSONL evidence (not execution authority). |
| **AI Onboarding Path** | Ordered read path for fresh AI agents entering the project. |

## 5. Authority Model (Summary)

Documents carry authority levels, not all of which are equal for decision-making:

| Level | Weight | Used For Decisions? | Example |
|-------|--------|---------------------|---------|
| `source_of_truth` | Highest | Yes — current guidance | `current-phase-boundaries.md` |
| `current_status` | High | Yes — runtime state | `paper-trade-ledger.md` |
| `supporting_evidence` | Medium | Context only | `paper-dogfood-ledger.jsonl` |
| `historical_record` | Low | Reference only | PT-001 trade receipt |
| `proposal` | None (until accepted) | No | Draft ADR |
| `example` | None | Illustrative only | Template files |
| `archive` | None | Historical interest | Old phase docs |

Full authority model in `document-taxonomy.md`.

## 6. Core Principles

### 6.1 Documents Are Not Static Text

Every document carries metadata (type, status, authority, freshness, owner). A
document without these markers is ambiguous and should be treated as draft.

### 6.2 Markdown Is Explanation; JSONL Is Evidence

- **Markdown** = human-readable explanation, decision, review, context.
- **JSONL** = machine-readable event evidence, checkable by invariant verifiers.
- **DB** = runtime application state (if later needed; not in scope for DG-1).
- **Wiki** = navigation, discovery, conceptual map.

They serve different functions. One does not replace the others.

### 6.3 Freshness Decays Authority

A document's authority decays with staleness. Stale docs must not be treated as
current truth. Archived docs preserve history but are not active guidance.

### 6.4 Receipt Is Evidence, Not Authority

Phase receipts, trade receipts, and stage summit documents are evidence of what
happened. They are not current authority for what is allowed. Only
`current-phase-boundaries.md` holds current authority.

### 6.5 Stage Summit Closes a Phase; It Does Not Open a New One

A Stage Summit can close a phase. It cannot activate forbidden capabilities.
Closing Phase 7P does not enable Phase 8. Only a new Stage Gate can open a new
phase.

### 6.6 CandidateRule ≠ Policy in Documents Too

A document describing a CandidateRule must label it "advisory only — NOT Policy."
No document should describe a CandidateRule as if it were active Policy.

### 6.7 AI Onboarding Must Stay Current

Root AI context files (`AGENTS.md`, `docs/ai/*.md`) must be updated whenever
phase state changes. A fresh AI reading those files must understand current
truth without inferring from archived docs.

## 7. Relationship to Other Packs

| Pack | Relationship |
|------|-------------|
| Design Pack | Document governance follows the same Pack lifecycle patterns. Doc UI is governed by Design Pack. |
| Finance Pack | JSONL ledger governance is Document Pack territory. Finance Pack governs trading semantics. |
| Policy Platform | Document freshness/staleness could inform future document checkers. No Policy activation in DG-1. |
| Repo Governance | Document changes still pass through normal PR governance. |

## 8. Relationship to Phase 7P JSONL Ledger

The 30-event JSONL ledger at `docs/runtime/paper-trades/paper-dogfood-ledger.jsonl`
is **evidence, not execution authority**. It exists under the Document Governance
Pack's jurisdiction as a `ledger`-type document.

The 16-invariant checker validates consistency, not authorization. Fresh AI
agents reading the ledger must not treat it as permission to trade.

## 9. Relationship to Future Wiki

This pack defines the wiki architecture (see `wiki-architecture.md`) but does not
implement it. The wiki is a future delivery surface for document metadata — it
provides navigation, discovery, and conceptual mapping over the governed
document corpus.

## 10. Future Document Checker

A future document checker should verify:
- All active docs have freshness timestamps within acceptable windows.
- No stale doc is linked as current guidance from root AI context.
- No archived doc overrides a current Stage Summit.
- No CandidateRule doc is described as Policy.
- No paper PnL doc is described as live readiness.
- JSONL ledger invariants hold.
- Root AI context matches current phase boundaries.

DG-1 defines the requirements. Implementation is deferred to a future
Document Governance sub-phase.

## 11. Non-Activation Clause

This contract is a **proposal**. It does not activate any Policy, RiskEngine
rule, or enforcement mechanism. It defines what document governance is — it does
not yet enforce it.

Phase 7P remains CLOSED. Phase 8 remains DEFERRED. No live, paper, or order
action is authorized by this document.

## 12. References

- `document-taxonomy.md` — full taxonomy of document types
- `document-lifecycle.md` — statuses, transitions, staleness rules
- `wiki-architecture.md` — future wiki structure
- `ai-onboarding-doc-policy.md` — AI read path specification
- `document-registry-schema.md` — future registry manifest format
- `README.md` — governance docs index
- `../product/alpaca-paper-dogfood-stage-summit-phase-7p.md` — Phase 7P closure
- `../runtime/paper-trades/paper-dogfood-ledger-schema.md` — JSONL schema
