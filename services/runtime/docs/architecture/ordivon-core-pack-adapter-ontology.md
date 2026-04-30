# Ordivon System Ontology — Core / Pack / Adapter

Status: **ACCEPTED** | Date: 2026-04-30 | Phase: DG-6A (Architecture Consolidation)
Tags: `architecture`, `core`, `pack`, `adapter`, `ontology`, `governance-plane`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

This document is the **canonical definition** of Ordivon's structural ontology.
It replaces the earlier 10-layer architecture model with a deeper semantic
framework: vertical structure (Core / Pack / Adapter) crossed by horizontal
governance planes. Every agent, developer, and future Rust kernel must
understand this document before touching code or architecture.

---

## 0. Three-Line Definition

```
Core    = Ordivon 的宪法与通用治理内核
Pack    = Core 在具体领域里的治理应用（领域法律体系）
Adapter = Ordivon 接触外部世界的受控边界接口
```

```
Core determines "what governance means."
Pack determines "how to govern in this domain."
Adapter determines "how to safely touch the external world."
```

```
Core = Why and invariant governance
Pack = Domain-specific how
Adapter = External-world contact under capability control
```

---

## Part A: Vertical Structure

### A1. Core — 治理内核

**Core is Ordivon's domain-neutral governance kernel.**

It defines:

| Component | Description |
|-----------|-------------|
| **Governance Ontology** | What objects exist: Intent, Evidence, Decision, Receipt, Outcome, Review, Lesson, CandidateRule, Policy, Authority, Capability, State, Actor, Pack, Adapter, Surface, Ledger, Archive |
| **Decision Algebra** | ALLOW / HOLD / REJECT / NO-GO / DEFERRED / ADVISORY / PENDING / CANCELED / CLOSED — each with strict semantics |
| **Authority Model** | source_of_truth > current_status > supporting_evidence > historical_record > proposal > example > archive |
| **Evidence Model** | Evidence must have source, timestamp, freshness. Evidence ≠ Authority. Adapter output ≠ Final Truth. |
| **Capability Model** | Capability ≠ Authority. Adapter can do X ≠ Ordivon should do X. paper capability ≠ live permission. |
| **Lifecycle State Machine** | Legal state transitions for every governed object |
| **Receipt / Outcome / Review Contract** | No receipt = not auditable. No outcome = not closed-loop. No review = not learned. |
| **Policy Promotion Model** | Lesson → CandidateRule → Policy requires ≥2 weeks observation, ≥3 real interceptions, documented bypass, stakeholder sign-off. CandidateRule ≠ Policy. Shadow ≠ Active. |
| **Semantic Safety Rules** | "active", "live", "validated", "policy", "authority" — dangerous words with strict usage boundaries |
| **Verification Contract** | 未验证不能 sealed; skipped verification must be recorded; pre-existing debt ≠ clean |

**Core does NOT know**: Alpaca, AAPL, Obsidian, Codex, Next.js, broker URLs, specific file paths, UI components, or any domain-specific nouns.

**Core invariant**:
> Core never imports Pack/domain nouns/provider. Upper layers may import lower layers. Lower layers must not import upper layers.

---

### A2. Pack — 领域治理包

**A Pack is a domain-specific governance application of the Core.**

A Pack translates Core concepts into a field-specific object model, evidence model,
receipt chain, review loop, and NO-GO boundaries.

A thing qualifies as a Pack only if it introduces **new governance semantics**:

| Requirement | Description |
|-------------|-------------|
| Domain vocabulary | Objects and terms specific to this domain |
| Evidence model | What counts as evidence here |
| Decision rules | When ALLOW / HOLD / REJECT / NO-GO |
| Receipt format | What a completed action looks like |
| Review loop | How outcomes become lessons |
| NO-GO boundaries | What must never be allowed |
| Lifecycle | How objects transition through states |
| Verification | checker / eval / tests |
| AI onboarding | What new AI must read |

#### Pack Hierarchy

```
P0 — Core / Kernel Pack    (domain-neutral invariants — near Core)
P1 — Foundation Pack       (cross-domain: Document Governance, Policy Platform)
P2 — Domain Pack           (Finance, Design, Agent Work, Coding)
P3 — Sub-Pack / Workstream (Paper Dogfood, Registry Checker, Freshness Checker)
P4 — Micro-Pack / Pattern  (CandidateRule≠Policy, Ledger=Evidence, No-Live-Disclaimer)
```

#### Current Ordivon Pack Map

```
Core Framework
  └─ governance loop, decision algebra, evidence/receipt/review lifecycle

Finance Pack (P2)
  ├─ observation read-only
  ├─ paper execution
  ├─ paper dogfood (P3)
  ├─ paper ledger (P3)
  └─ Phase 8 readiness (deferred)

Policy Platform Pack (P2)
  ├─ CandidateRule lifecycle
  ├─ shadow/advisory evaluation
  ├─ active_enforced NO-GO
  └─ approval/review surfaces

Design Governance Pack (P2)
  ├─ design tokens
  ├─ governance components
  ├─ preview/advisory labels
  └─ high-risk actions disabled

Document Governance Pack (P1)
  ├─ document taxonomy + lifecycle (DG-1)
  ├─ registry + checker (DG-2)
  ├─ staleness audit (DG-3)
  ├─ freshness + semantic checker (DG-4)
  ├─ baseline integration (DG-5)
  └─ wiki navigation (DG-6)

Future Packs:
  ├─ AI Agent Work Pack (harness governance)
  └─ Rust Kernel Pack (invariant extraction)
```

**Pack invariant**:
> A Pack is a domain governance unit, not a feature bundle. Adapter alone ≠ Pack. Surface alone ≠ Pack. Docs alone ≠ Pack. A Pack must define domain language, evidence, decisions, receipts, reviews, and NO-GO.

---

### A3. Adapter — 受控外部边界

**An Adapter is a controlled boundary module connecting Ordivon to an external system.**

It declares capabilities, enforces local safety invariants, translates external
data into Ordivon objects, executes only explicitly allowed operations, emits
evidence/receipts, and prevents external semantics from becoming internal
authority.

#### Adapter Composition (10 Components)

| # | Component | Role |
|---|-----------|------|
| A1 | **Port / Interface** | Methods exposed to Ordivon. Forbidden methods don't exist on the interface. |
| A2 | **Capability Contract** | What this adapter can technically do (≠ permission to do it) |
| A3 | **Auth / Secret Boundary** | Key management, endpoint validation, secret redaction |
| A4 | **Connector / Client** | HTTP/SDK/protocol layer — no governance judgment |
| A5 | **Request Builder** | Translates Ordivon objects to external request format with constraint enforcement |
| A6 | **Response Translator** | Anti-corruption layer: external semantics → Ordivon domain objects |
| A7 | **Guard / Local Safety Invariant** | Rejects live URLs, live keys, non-GET in read-only, replace/auto forbidden |
| A8 | **Error / Timeout / Retry Boundary** | External failures must be classifiable; retry ≠ auto-trading loop |
| A9 | **Evidence / Receipt Emitter** | Every side-effect action returns structured receipt |
| A10 | **Test Double / Mock Provider** | Must be testable without live external dependency |

#### Adapter Type Taxonomy

| Type | Risk | Examples |
|------|------|----------|
| **Observation Adapter** | R1 read-only | `AlpacaObservationProvider` |
| **Execution Adapter** | R2-R4 write | `AlpacaPaperExecutionAdapter` |
| **Knowledge Adapter** | R0 navigation | `generate_document_wiki.py` |
| **Harness Adapter** | R1-R3 execution | Future Codex/Hermes adapter |
| **Storage Adapter** | R1-R2 persistence | Future DB adapter |
| **Notification Adapter** | R1 messaging | Future webhook adapter |

#### Current Adapter Instances

```
AlpacaObservationProvider
  Type: Observation Adapter
  External: Alpaca Paper Trading API
  Risk: R1 read-only
  Allowed: GET account, market data, positions, fills
  Forbidden: place_order, cancel_order, withdraw, transfer
  Guard: GET-only, secret redaction, paper-api URL enforcement

AlpacaPaperExecutionAdapter
  Type: Execution Adapter
  External: Alpaca Paper Trading API
  Risk: R2 paper write
  Allowed: submit_paper_order, cancel_paper_order
  Forbidden: live_order, auto, replace, withdraw, transfer
  Guard: paper-api only, PK key only, no_live_disclaimer required,
         live URL → NO-GO, auto → NO-GO

Document Wiki Generator
  Type: Knowledge Adapter
  External: Markdown rendering / GitHub / Obsidian-compatible
  Risk: R0 navigation
  Allowed: generate wiki-index.md from registry
  Forbidden: create new authority, bypass checker
  Guard: "not source of truth" banner, registry-derived only
```

**Adapter invariants**:
> 1. Adapter does not decide authority.
> 2. Adapter exposes capability, not permission.
> 3. Adapter output is evidence, not truth.
> 4. Adapter guards must reject impossible/forbidden states.
> 5. Adapter must translate external semantics into Ordivon objects.
> 6. Adapter must not leak secrets.
> 7. Adapter must return receipts for side effects.
> 8. Adapter must be testable without live external dependency.
> 9. Adapter must not become system identity.
> 10. Adapter must be replaceable without changing Core.

---

### A4. Structural Invariants

```
Core defines governance planes.
Pack specializes governance planes.
Adapter is constrained by governance planes.
Surface represents governance planes (but cannot create authority).
Checker verifies governance planes (but cannot authorize action).
Ledger records governance-plane evidence.
Registry indexes governance-plane metadata.
Stage Summit changes governance-plane status.
```

```
Pack cannot override Core.
Adapter cannot define Pack authority.
Surface cannot become Pack truth.
Checker validates consistency; it does not authorize action.
```

---

## Part B: Governance Planes (Horizontal)

Governance planes are the **cross-cutting control surfaces** that apply to every
vertical layer. They ensure that no code, document, adapter, UI, AI output,
ledger, or checker escapes evidence, authority, verification, lifecycle,
knowledge, risk, and trust constraints.

| Governance Plane | Question It Answers | Core Objects |
|-----------------|-------------------|--------------|
| **Evidence / State** | What happened? What is the current state? | receipt, ledger, snapshot, audit |
| **Authority / Policy** | Who or what can guide action? | source_of_truth, Policy, CandidateRule |
| **Verification / Safety** | Has this been verified? Are gates passing? | tests, checker, baseline, eval |
| **Orchestration / Lifecycle** | Is this action proceeding legally? | intake, receipt, outcome, review |
| **Knowledge / Documentation** | How does the system remember itself? | docs/ai, registry, wiki, archive |
| **Risk / Side-effect** | What is the side-effect level? | R0-R5, capability, NO-GO |
| **Actor / Trust** | Who is speaking, executing, authorizing? | human, AI, adapter, checker |
| **Surface / Representation** | Is this correctly displayed? | UI, wiki, README, CLI |

### Plane Invariants

```
Evidence Plane:
  Evidence ≠ Authority. Ledger ≠ Execution Authorization.
  Receipt ≠ Review. Adapter output ≠ Final Truth.

Authority Plane:
  CandidateRule ≠ Policy. Policy ≠ Active Enforcement.
  Proposal ≠ Current Truth. Archive ≠ Active Guidance.
  Stage Summit overrides older receipts for phase status.

Verification Plane:
  未验证不能 sealed. Skipped verification must be recorded.
  Pre-existing debt ≠ clean. Checker pass ≠ action authorization.
  Baseline gate count must be honest.

Lifecycle Plane:
  No receipt = not auditable. No outcome = not closed-loop.
  No review = not learned. No New AI Context Check = not safe to continue.

Knowledge Plane:
  Current Truth ≠ Historical Evidence. Archive ≠ Current Guidance.
  Wiki = Navigation, not Source of Truth. Document ≠ just text; it is system memory.

Risk Plane:
  Read-only ≠ Write. Paper write ≠ Live write.
  Capability ≠ Permission. Paper PnL ≠ Live Readiness.

Actor Plane:
  AI proposes, not silently authorizes. Human GO must be scoped.
  Adapter reports, not decides. External harness ≠ system identity.

Surface Plane:
  Surface displays governance; it does not create authority.
  Preview ≠ Production. Configured ≠ Connected. Advisory ≠ Enforced.
```

---

## Part C: Control-Theoretic View

From control theory, Ordivon can be understood as:

```
External World
    ↓
Adapter (Sensor) → reads external state
    ↓
Pack (Domain Controller) → interprets domain semantics
    ↓
Core (General Controller) → applies governance invariants
    ↓
Pack → generates receipt / review / outcome
    ↓
Adapter (Actuator) → executes only explicitly authorized actions
    ↓
Ledger / Receipt / Review → feedback loop
```

```
Observation Adapter = Sensor
Execution Adapter   = Actuator
Core + Pack         = Controller
Receipt / Outcome   = Feedback
Checker             = Constraint Verification
```

---

## Part D: Relationship to Document Governance Pack

DG Pack is a **P1 Foundation Pack**. It serves Core by making governance-plane
semantics machine-checkable:

| Core Invariant | DG Pack Implementation |
|---------------|----------------------|
| Current Truth ≠ Archive | `document-registry.jsonl` with authority levels |
| Evidence ≠ Authority | Semantic phrase checker (ledger ≠ execution authority) |
| 未验证不能 sealed | `agent-output-contract.md` receipt template |
| CandidateRule ≠ Policy | Semantic phrase checker |
| Phase 8 DEFERRED | Semantic phrase checker |
| Freshness decays authority | `last_verified` + `stale_after_days` checker |
| Wiki ≠ Source of Truth | `wiki-index.md` mandatory banner |
| pre-existing debt ≠ clean | Future `verification-debt-ledger.jsonl` |

DG Pack is **not Core itself** — it is the foundation Pack that operationalizes
Core semantics in the knowledge/documentation domain.

---

## Part E: Quick Reference

```
Core:
  Ordivon's domain-neutral governance kernel.
  Defines invariants, decision algebra, authority boundaries, and lifecycle rules.
  Knows no specific domain, external tool, broker, UI, or document surface.

Pack:
  A domain-specific governance application of Core.
  Translates Core concepts into field-specific object models, evidence,
  receipts, reviews, and NO-GO boundaries.
  Must define domain language, evidence, decisions, receipts, reviews, NO-GO.

Adapter:
  A controlled boundary module connecting Ordivon to an external system.
  Declares capabilities, enforces local safety invariants, translates
  external data, executes only allowed operations, emits receipts.
  Cannot decide authority or create governance truth.

Governance Plane:
  A cross-cutting control surface that applies to all vertical layers.
  Ensures evidence, authority, verification, lifecycle, knowledge,
  risk, actor, and surface constraints are never bypassed.
```

**Ultimate compression**:
> Core 保证 Ordivon 是什么。Pack 决定 Ordivon 如何治理某个领域。Adapter 决定 Ordivon 如何安全接触外部世界。治理平面保证所有这些东西在证据、权威、风险、生命周期、验证和知识记忆上不失真。
