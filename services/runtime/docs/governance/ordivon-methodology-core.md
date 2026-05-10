# Ordivon Methodology Core

> **Governance as executable, auditable, replayable structure.**
>
> Ordivon does not describe governance. Ordivon is a governance operating system
> whose checkers, registries, ledgers, policies, and gates are themselves
> governed objects. This document defines the invariants, algebra, and
> self-calibration doctrine that make that possible.

**Authority**: `source_of_truth`
**Status**: `accepted`
**Phase**: `CI-SelfCalibration`
**Owner**: `ordivon-core-maintainer`
**Last verified**: 2026-05-10
**Stale after**: 90 days
**Lesson refs**: L-CI-SELFCAL-001, L-CI-SELFCAL-002, L-CI-SELFCAL-003
**Derived from**: CI Self-Calibration event (2026-05-10), DGP/LGC governance hardening waves,
                Ordivon companion governance constitution

---

## 1. Purpose

Ordivon treats governance as executable code — testable, attestable, replayable
in-repo. Every document, checker, registry, ledger, policy, and receipt exists
inside the same repository and is subject to the same git/CI/review flow as the
code it governs. This is not an analogy; it is the architecture.

The consequence: **the governance system itself is governable.** Checkers can
drift. Registries can go stale. CI gates can produce false positives. Debt
records can be mistaken for resolution. Ordivon must audit itself.

This document formalizes the invariants, algebra, and self-calibration doctrine
that emerged from Ordivon's own governance hardening — particularly the CI
Self-Calibration event of 2026-05-10, when 8 CI failures across 5 checker jobs
were not suppressed but systematically classified, fixed, and converted into
methodology.

---

## 2. L0 Governance Invariants

These are not guidelines. They are the invariants that make Ordivon's
governance self-calibrating. Violating any of them produces systemic drift that
the checker ecosystem is designed to detect.

### A. Epistemic Invariants — Truth and Evidence Boundaries

These govern **what can be believed to what degree.**

| Invariant | Meaning |
|-----------|---------|
| **Evidence ≠ Claim** | A statement without supporting data is a claim, not a fact. "全绿", "已完成", "全线闭合" are claims — rejected without git diff, before/after counts, raw CLI output. |
| **Generated ≠ Source** | A machine-generated view (wiki index, stats page, manifest) is derived from a source of truth. It can be reconstructed. It is not authoritative. |
| **Summary ≠ Current Truth** | "All checks pass" is a summary. The current truth is the raw checker output, the reconciler counts, the per-doc rows. Summaries compress; compression loses information. |
| **Receipt ≠ Total Proof** | A receipt documents what was checked and what was found. It does not prove the system is correct. It is evidence, not certification. |
| **Analogy ≠ Proof** | Cross-domain analogies (thermodynamics, control theory, law, economics) are design inputs and explanatory frames. They are not formal proofs. Useful for reasoning, not for authorization. |
| **Derived ≠ Duplicated** | A derived entity is programmatically generated from a single source of truth. A duplicated entity is independently maintained. The former is safe; the latter will drift. Never duplicate what can be derived. |

### B. Authority Invariants — Authorization and Execution Boundaries

These govern **what can be allowed, executed, closed, or escalated.**

| Invariant | Meaning |
|-----------|---------|
| **READY ≠ Authorization** | READY means selected checks passed. It does not authorize merge, deploy, release, execution, tool use, policy activation, or external action. READY is a checker-state, not a governance-state. |
| **Authority ≠ Execution** | Having authority to do something does not mean it should be done. Authority is a necessary but not sufficient condition for execution. |
| **Checker ≠ Policy** | A checker detects violations. Policy defines what to do about them. A checker PASS is a signal; a Policy activation is a decision. Do not confuse detection with enforcement. |
| **Ignore ≠ Resolution** | Temporarily ignoring a finding (--ignore-vuln, safe-context, allowlist) is not the same as resolving the underlying issue. Every ignore must carry a debt record, a review trigger, and a removal condition. |
| **Suppress ≠ Fix** | Silencing a checker output (disabling a rule, relaxing a regex without analysis, marking a test as skipped) does not fix the problem the checker was detecting. Suppression is acceptable only when paired with a formal A4 debt record and a plan. |
| **Silent Ignore = Risk Externalized** | Ignoring a finding without recording it externalizes the risk — it becomes invisible to the governance system. Formal debt (A4) internalizes the risk — it stays visible, tracked, and reviewable. |

---

## 3. Governance Loop — Dual Gate Model

The governance loop describes how a governed intent moves from proposal to
closure. The critical insight: **there are two distinct gates**, not one.

```text
Intent
  ↓
Scope / Risk Classification
  ↓
Evaluation (checkers, audits, analysis)
  ↓
═══════════════════════════════════
Pre-Execution Authority Gate
  ├─ Is there an owner?
  ├─ Is there explicit authority?
  ├─ Is execution allowed (write, merge, deploy, publish)?
  ├─ Are preconditions satisfied?
  ╘─ Gate outcome: proceed / BLOCKED / return for more evidence
═══════════════════════════════════
  ↓
Execution
  ↓
Receipt (what was done, what was found)
  ↓
Reconciler (receipt vs reality: drift detection)
  ↓
Debt / Lesson / Finding (classification)
  ↓
═══════════════════════════════════
Post-Execution Review Gate
  ├─ Does the receipt meet evidence standards?
  ├─ Is new debt formally recorded?
  ├─ Can findings be upgraded to lessons?
  ├─ Can lessons be upgraded to CandidateRules?
  ╘─ Gate outcome: VerifiedClosure / CandidateClosure / reopen
═══════════════════════════════════
  ↓
PolicyCandidate / PolicyActivation / Tombstone
  ↓
Intent (loop)
```

Without the Pre-Execution Gate, "Authority → Execution" is ambiguous —
Authority may be misinterpreted as authorization to execute. The Gate makes
explicit that authority is necessary but not sufficient.

Without the Post-Execution Gate, receipts accumulate without review, debt
remains unclassified, and lessons never become policy.

---

## 4. State Algebra

Ordivon uses a three-state algebra for system-level status, and a two-state
model for closure.

### System States

| State | Meaning | CI Exit Code | Action Required |
|-------|---------|--------------|-----------------|
| **READY** | Selected checks passed. No blocking findings. | 0 | None — but READY is a checker-state, not authorization |
| **DEGRADED** | Non-blocking findings exist. System can operate with reduced trust. | 2 | Review findings; schedule remediation |
| **BLOCKED** | Hard failures exist. System must not proceed. | 1 | Fix blocking findings before any governed action |

### Closure States

| State | Meaning | Evidence Required |
|-------|---------|-------------------|
| **CandidateClosure** | Proposed as complete but not yet verified. | Claim only — insufficient |
| **VerifiedClosure** | Reviewed against evidence standard. Receipt, debt, and scope confirmed. | Full evidence packet (git diff, before/after counts, raw output, file paths) |

### Key Principle

```text
Closure ≠ Truth
CandidateClosure ≠ VerifiedClosure
READY ≠ Closure
```

---

## 5. Disposition Matrix (A1–A4)

When a governance checker finds a violation — or the governance system itself
drifts — Ordivon does not binary-classify into "fix" and "ignore." It uses a
four-level disposition matrix.

| Level | Name | Trigger | Action | Example |
|-------|------|---------|--------|---------|
| **A1** | Direct Fix | Stated truth does not match ground truth | Fix the data/document/code | Update hardcoded count 244→435; fix f-string without placeholders |
| **A2** | Logic Refine | Rule intent does not match rule execution | Refine the checker (not delete it) | Widen SAFE_CONTEXTS regex; add authoritative doc allowlist |
| **A3** | System Redesign | Same drift will recur under current design | Change the mechanism to prevent recurrence | Replace hardcoded numbers with generated_view; extract schema to single file |
| **A4** | Debt Formalization | Cannot be fixed now but must not be forgotten | Record as formal debt with review trigger and removal condition | CVE-2026-3219 NO_FIX_UPSTREAM; deferred test suite |

### Key Principles

```text
A1→A4 is a disposition ladder, not a quality ranking.
A2 refines a checker; it does not delete one.
    Checker deletion requires explicit PolicyRetirement receipt.
A4 is not failure — it converts externalized risk into internalized debt.
```

---

## 6. Self-Calibration Doctrine

The governance system is made of the same materials as the system it governs:
code, documents, registries, CI workflows, JSONL ledgers. They live in the same
repository. They go through the same git/CI/review pipeline.

This means:

```text
Ordivon cannot be self-proving.
But it must be self-auditing.
```

### What This Requires

1. **Checker PASS is a Claim, not Truth.** A checker reporting "all checks
   pass" is producing a claim. That claim must be verified against evidence —
   raw output, reconciler counts, git diff.

2. **CI READY is Evidence, not Authorization.** READY means certain checks
   passed at a certain time. It does not mean the system is correct, safe, or
   authorized.

3. **Every governance artifact has an owner, a review date, and a staleness
   threshold.** Including schemas, checker rules, debt records, and this
   document.

4. **Drift in governance artifacts is detected by the governance system.**
   When the governance system itself drifts (dual-checker divergence, hardcoded
   count staleness, schema-consumer mismatch), CI must BLOCK until the drift
   is resolved.

5. **Self-calibration events produce lessons.** Every time the governance
   system catches its own drift, the lesson is recorded, classified, and
   feeds back into methodology. This document is a product of such an event.

### Anti-pattern: The Checker Oracle Fallacy

```text
"Checker says PASS, therefore safe."
"CI is green, therefore ready to merge."
```

Both are false. Checkers produce evidence. Humans (or explicitly governed
automation) make authorization decisions.

---

## 7. Anti-Pattern Catalog

These are recurring failure modes discovered through Ordivon's governance
hardening. Each has been observed, classified, and linked to a lesson.

### AP-1: Hardcoded Count Drift
**Symptom**: 4 documents independently state "244 registered docs." Registry has 435.
**Root cause**: Duplicated representation (see Derived ≠ Duplicated).
**Lesson**: L-CI-SELFCAL-001
**Fix**: A3 — replace hardcoded counts with generated views.

### AP-2: Dual-Checker Trap
**Symptom**: VALID_DOC_TYPES has 20 items in one checker, 17 in another.
**Root cause**: Two independently maintained authority sets.
**Lesson**: L-CI-SELFCAL-002
**Fix**: A3 — schema-first architecture (single schema, multiple consumers).

### AP-3: Atomic Governance Breakage
**Symptom**: 124 new documents committed; registry, doc_types, reference docs not updated in same commits.
**Root cause**: Governance update treated as separate from content update.
**Lesson**: L-CI-SELFCAL-003
**Fix**: One semantic change = one atomic governance unit.

### AP-4: Silent Ignore
**Symptom**: Vulnerability suppressed with --ignore-vuln, no debt record.
**Root cause**: Ignore treated as resolution.
**Lesson**: Dependency audit debt ledger (DEP-AUDIT-PIP-CVE-2026-3219).
**Fix**: Every ignore carries a debt record with review trigger.

### AP-5: Generated-as-Source
**Symptom**: Wiki index or generated stats treated as authoritative.
**Root cause**: Generated views not marked as derived.
**Lesson**: Embedded in document metabolism design (DGP-7).
**Fix**: All generated views carry explicit `generated_view` marker.

### AP-6: CandidateRule-as-Policy
**Symptom**: Advisory rule language treated as binding policy.
**Root cause**: Agentic pattern detection triggered by governance definition documents.
**Lesson**: Agentic pattern checker SAFE_FILES methodology.
**Fix**: Authoritative governance docs exempt from agentic pattern rules (A2).

---

## 8. Receipt Standard

Every governed action that produces a receipt must meet this standard. Summaries
that say "全绿" or "已完成" without evidence are rejected.

### Required Evidence

```text
1. git diff (exact file paths, before/after content)
2. Before/after reconciler counts (not just "pass")
3. Raw CLI output (not just interpreted summary)
4. Per-doc rows for document-level changes
5. Debt entries created or updated
6. Explicit scope boundary (what was NOT checked)
7. READY disclaimer (does not authorize execution/merge/deploy)
```

### Unacceptable

```text
"All green"
"Completed"
"全线闭合"
"All tests pass" (without count or failing test names)
"CI passed" (without job-level detail)
```

---

## 9. Scope Boundaries and Red-Team Notes

This document is **source_of_truth** for Ordivon's methodology. Like any
governed artifact, it has boundaries and must resist its own overclaim.

### What This Document Establishes

- Formal invariants that govern Ordivon's governance
- The dual-gate governance loop
- The state algebra (READY/DEGRADED/BLOCKED + closure states)
- The A1–A4 disposition matrix
- The self-calibration doctrine
- The anti-pattern catalog
- The receipt standard

### What This Document Does NOT Establish

- It does not prove Ordivon is self-consistent (that requires continuous verification)
- It does not authorize any specific action, merge, or deployment
- It does not replace individual checker documentation
- It does not close any A4 debt items
- It does not claim all governance hardening is complete

### Red-Team: Schema-First Is Not Fully Solved

```text
Status: Documented risk
document-types.json removes the dual-write problem for doc_types.
The schema itself still needs: owner, review date, change receipt,
consumer coverage tests, and schema versioning.
Other authority sets (VALID_STATUSES, PROTECTED paths, SAFE_FILES)
may still exhibit dual-write patterns.
```

### Red-Team: READY Is Not Closure

```text
Status: Reinforced invariant
This document formalizes READY as a checker-state, not a governance-state.
Every verify output must carry the READY disclaimer.
Closure requires VerifiedClosure with full evidence packet.
```

### Red-Team: A2 "Refine, Don't Delete" Has an Exception

```text
Status: Documented exception
A2 refines a checker; it does not delete one.
Checker deletion is not forbidden — but it requires an explicit
PolicyRetirement receipt explaining why the rule is no longer needed.
Silent deletion is forbidden.
```

### Red-Team: Self-Calibration Is Not Self-Proof

```text
Status: Explicit boundary
Ordivon can audit itself. It cannot prove itself correct.
Self-auditing produces evidence. Evidence is not proof.
This document is a methodology framework — it is not a formal
verification of Ordivon's consistency.
```

---

## 10. Verdict

This document was produced by the CI Self-Calibration event of 2026-05-10,
when 8 CI failures across 5 checker jobs (ruff, pr-fast, product-tests,
governance-tests, verify-native) were not suppressed but systematically
classified and resolved through the A1–A4 disposition matrix.

The event demonstrated that Ordivon's governance system can detect its own
drift, classify it, fix it, record lessons from it, and upgrade those lessons
into methodology. This is not a claim. It is evidenced by the commit chain
`dff9209..e73104b` and the lesson ledger entries L-CI-SELFCAL-001 through 003.

**What was verified**: CI failure → systematic classification → A1/A2/A3/A4
disposition → schema-first architecture deployed → lessons recorded → roadmap
updated → methodology extracted.

**What remains candidate**: Full atomic governance gate (designed, not fully
implemented). Doc count generator + verify CI gate (pending). CVE-2026-3219
review cron (pending). A4 deferred 02-TESTS failures (backlog, not closure).

**No-Go**: Do not claim governance hardening is complete. Do not treat this
document as proof of correctness. Do not mistake READY for closure.

---

```text
READY means selected checks passed; it does not authorize execution,
does not authorize merge, does not authorize deployment, and does not
authorize release, tool use, policy activation, or external action.
```
