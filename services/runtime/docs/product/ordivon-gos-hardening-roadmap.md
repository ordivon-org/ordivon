# Ordivon Governance OS — Next Phase Roadmap (GOS-N1 → GOS-N4)

> **This is a roadmap, not a receipt.** No phase has been executed.
> All statuses below are CANDIDATE, not VERIFIED.
>
> **Direction**: Harden the demonstrable self-governance control plane.
> **Anti-pattern avoided**: Expanding features before closing drift surfaces.

**Authority**: `proposal`
**Status**: `proposed`
**Phase**: `CI-SelfCalibration → GOS-Hardening`
**Owner**: `ordivon-core-maintainer`
**Freshness**: 2026-05-10
**AI Read Priority**: 1

---

## 0. Current State (per GOS assessment template)

```
Governance Control Plane:      VERIFIED (demonstrable)
Governance Coverage:           READY with known gaps
AI Governance Enforcement:     DEGRADED (requires protocol adhesion)
External Governance:           NOT APPLICABLE (self-governance only)
Full Closure:                  NOT CLAIMED

Open debts:                    4
Draft checkers:                1 (policy-shadow)
CandidateRules:                4 draft, 0 activated
Governed files:                308/540
```

## 0.1 Roadmap Principles — Five Rules

```text
1. Eliminate drift surfaces before adding new capabilities.
2. Make advisory surfaces governable before escalating to blocking.
3. Constrain AI output adapter before claiming AI governance.
4. Harden internal self-governance before external governance.
5. Every phase MUST include Execute + Seal — no separate "regression closure phase."
```

These are derived from the three systemic anti-patterns identified in
CI-SelfCalibration (L-CI-SELFCAL-001/002/003) and the controlled claim
vocabulary deployed in `claim-vocabulary.json`:

> Schema-Driven Generation — Schema-First Architecture — Atomic Governance Gates

---

## 1. GOS-N1: Drift & Generated View Hardening

**Goal**: Eliminate duplicated representation. All architecture/status counts
must be generated from source ledgers, not duplicated manually.

**Core invariant**: `Derived ≠ Duplicated` · `Generated View ≠ Source of Truth`

**Scope**:
```
In:   registry stats generator · checker inventory generator
      CI job inventory generator · debt/lesson/CR summary generator
      architecture diagram count references · verify-generated-views CI gate

Out:  new checkers · external governance · AI output adapter
```

**Key execution**:
```text
1. Generated governance status view: docs/governance/generated/_governance-status.md
2. Sources: document-registry.jsonl, checker discovery, CI workflow parse,
   lesson-ledger.jsonl, debt ledger, CandidateRule drafts
3. All architecture/assessment docs reference generated status only.
   No more hand-written counts.
4. CI gate: verify-generated-governance-status
```

**Seal evidence required**:
```text
git diff summary
before/after drift examples
raw output: update-governance-status.py, verify-governance-status.py, ordivon-verify all
demo: manual drift → DETECTED
```

---

## 2. GOS-N2: Gate & Lifecycle Hardening

**Goal**: Dual-gate from "methodology + partial checker" to "CI-enforced where safe."
Advisory checkers classified. Lesson/debt/CandidateRule lifecycles defined.

**Scope**:
```
In:   Pre-Execution Gate CI policy · atomic-governance hardening
      overclaim advisory review · policy-shadow maturity review
      blocking/advisory/shadow classification · knowledge lifecycle states

Out:  new checkers · external policy activation · risky auto-execution
```

**Key execution**:
```text
1. Classify all advisory checkers: draft / shadow / advisory / blocking_candidate / blocking
2. Pre-Execution Gate: blocking_candidate → collect false-positive rate
3. Overclaim detector: advisory, with phrase/file/suggestion/severity/escape output
4. policy-shadow: stays shadow unless maturity receipt exists
5. Knowledge lifecycle states:
   Lesson: captured → reviewed → actioned → CR_drafted → rejected → archived
   CandidateRule: draft → reviewed → shadow → active_candidate → activated → rejected → tombstoned
   Debt: open → review_due → mitigated → closed → reopened
6. Review 4 pending lessons. No "continue pending" without review date.
7. CVE-2026-3219 auto recheck trigger.
```

**Seal evidence required**:
```text
checker maturity table
advisory false-positive report
before/after knowledge lifecycle states
no CandidateRule activation without PolicyActivation receipt
```

---

## 3. GOS-N3: AI Output Adapter & Observer Protocol

**Goal**: Close the DEGRADED surface: AI can bypass vocabulary checks.
Protocol-bound AI output enforcement.

**Scope**:
```
In:   AI Output Adapter schema · controlled vocabulary field enforcement
      structured receipt template · AI Observer allowed/forbidden action schema
      synonym/paraphrase overclaim detection · protocol adhesion checker

Out:  AI auto-authorization · AI auto-debt-closure · AI auto-policy-activation
      external agent runtime integration
```

**Key execution**:
```text
1. ai-output-adapter.schema.json: role, allowed_actions, forbidden_actions,
   claim_type, evidence_refs, status_terms, not_claimed, debt_refs, receipt_refs

2. AI Observer output contract:
   MAY: propose finding, classify A1-A4 candidate, draft receipt/lesson, red-team claim
   MAY NOT: authorize, close, suppress, resolve debt, activate policy

3. Controlled vocabulary: text detection → structured field validation

4. Paraphrase detection layer:
   "已经搞定" "彻底解决" "没有问题" "全部正常" "fully solved" → overclaim candidate

5. Dogfood: AI generates violating assessment → adapter blocks or downgrades
```

**Seal evidence required**:
```text
schema file · valid/invalid fixtures · checker output
AI-generated violating sample · corrected AI Observer sample
ordivon-verify all
```

---

## 4. GOS-N4: Coverage Boundary & Externalization Dry-Run

**Goal**: Classify all non-governed files. Rationalize exclusions.
External template: dry-run ONLY. No external authority claim.

**Scope**:
```
In:   non-governed file classification · exclusion reason validation
      high-risk path protection · external template (dry-run)
      project AI onboarding playbook

Out:  global 100% file coverage claim · external authority claim
      auto-modify external projects · external policy activation
```

**Key execution**:
```text
1. Bucket 233 non-governed files: generated/vendored/fixture/archive/external/
   temporary/intentionally-ungoverned/debt

2. High-risk paths require reason for exclusion:
   governance/ · docs/ai/ · checkers/ · scripts/ · src/ · .github/workflows/

3. Repeated out-of-scope → auto backlog candidate

4. Exclusion schema: owner, review_date, reason, expiry

5. External template (dry-run only):
   claim registry · evidence ledger · authority boundary · receipt · debt ledger
   CLI: ordivon verify-template --target <repo> --dry-run
   No file write without explicit flag

6. Dogfood: isolated fixture repo
```

**Seal evidence required**:
```text
non-governed classification report
exclusion schema validation
high-risk exclusion demo (remove reason → BLOCKED)
dry-run output · no external file write proof
```

---

## 5. Execution Order

```text
GOS-N1: Drift & Generated View Hardening
    ↓
GOS-N2: Gate & Lifecycle Hardening
    ↓
GOS-N3: AI Output Adapter & Observer Protocol
    ↓
GOS-N4: Coverage Boundary & Externalization Dry-Run

Logic: prevent self-drift → strengthen gates → constrain AI → prepare external
Do not reverse. Externalizing DEGRADED edges contaminates external projects.
```

---

## 6. Phase Commit Structure

Each GOS-N phase MUST produce:

```
1. Freeze reality commit:   baseline state (git diff, counts, checker output)
2. Implement commit(s):      schema/script/CI changes
3. Seal commit:              evidence receipt, debt updates, lesson extraction
```

No separate "cleanup phase." Execute + Seal in the same phase.

---

## 7. Allowed Status Claims

```text
Roadmap Direction:            READY (proposed, not executed)
GOS-N1 through GOS-N4:       NOT YET EXECUTED
Full Closure:                 NOT CLAIMED
External Governance:          NOT CLAIMED
AI Enforcement:               DEGRADED until GOS-N3 adapter path exists
```

---

```text
READY means selected checks passed; it does not authorize execution,
does not authorize merge, does not authorize deployment, and does not
authorize release, tool use, policy activation, or external action.
```
