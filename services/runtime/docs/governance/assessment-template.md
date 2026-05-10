# Ordivon Governance Assessment Template — Evidence-First State Ledger

> **This document is a template, not an assessment.** It defines the only
> acceptable structure for making claims about Ordivon's system state.
> Use it. Do not improvise summary claims.

**Authority**: `source_of_truth`
**Status**: `current`
**Phase**: `CI-SelfCalibration`
**Owner**: `ordivon-core-maintainer`
**Freshness**: 2026-05-10
**AI Read Priority**: 1
**Lesson refs**: L-CI-SELFCAL-004, L-CI-SELFCAL-006
**Derived from**: Two overclaim incidents in CI-SelfCalibration, controlled claim vocabulary

---

## 1. Why This Template Exists

Two overclaim incidents occurred during CI-SelfCalibration:

```
Incident 1: "FOUNDATION COMPLETE — 9/9 VerifiedClosure"
  Reality:     6/9 READY, 3/9 with gaps
  Root cause:  Dimensions compressed into a single number.
               Checker-state (READY) misrepresented as governance-state (VerifiedClosure).

Incident 2: "We are honest."
  Reality:     A self-evaluation with no verifiable truth condition.
  Root cause:  Used a word not in the controlled claim vocabulary.
               Self-evaluation is inherently unverifiable.
```

Both failures share the same structure:

```text
Observation → Compression → Label → Declaration
```

The fix is structural, not behavioral:

```text
Observation → Preserve granularity → Display → Stop
```

This template enforces that structure. It bans synthetic conclusions when
system dimensions are in different states. It allows synthesis ONLY when
all dimensions share the same verified state.

---

## 2. The Template

```text
## [Assessment Subject] — State Ledger
## Date: [YYYY-MM-DD]
## Assessor: [name or role]

### 1. What Exists
[For each dimension independently, state evidence. Do not cross-reference
 dimensions. Each stands alone. Prefer machine-verifiable evidence.]

Format:
  Dimension: [name]
  State:     READY | BLOCKED | DEGRADED | VERIFIED
  Evidence:  [concrete, reproducible: counts, exit codes, file paths, commit hashes]

### 2. What Is Missing
[For each gap independently. Use OPEN debt IDs where applicable.
 Do not compress. Do not explain away. Do not minimize.]

Format:
  Gap:       [description]
  Debt ID:   [if registered as formal debt]
  Status:    OPEN
  Next step: [concrete action or review trigger]

### 3. Gap Disposition
[Previously identified gaps. What happened to each.]

Format:
  Gap:       [original description]
  Disposition:  actioned | debt | deployed | parked
  Evidence:  [what changed]

### 4. Vocabulary Constraint
This assessment uses only words from claim-vocabulary.json `allowed_claims`.
No forbidden words were used. Verify: run `detect_overclaim.py` on this document.

### 5. Synthesis (Only If Homogeneous)
If and only if ALL dimensions share the same state, a synthesis is permitted:

  ALL dimensions READY → "System state: READY"
  ALL debts CLOSED    → "Debt ledger: CLOSED"

If dimensions differ, this section MUST read:

  "No homogeneous synthesis is possible. See per-dimension states above."
```

---

## 3. Anti-Patterns — What This Template Prevents

### Anti-Pattern A: Dimension Compression

```text
WRONG:
  "9/9 VerifiedClosure" ← 9 dimensions compressed to 1 number

RIGHT:
  "Document governance: VERIFIED. Checker ecosystem: READY (1 draft).
   CI gates: READY (2 advisory). Lesson pipeline: DEGRADED (4 pending)."
```

The number 9 hides that the 9 dimensions are in different states.

### Anti-Pattern B: Forbidden Words

```text
WRONG:
  "COMPLETE" ← no verifiable truth condition
  "honest"   ← self-evaluation, inherently unverifiable
  "done"     ← no evidence standard
  "全绿"     ← compresses all signal into a color

RIGHT:
  READY, BLOCKED, DEGRADED, OPEN, CLOSED, VERIFIED
  Every word maps to a machine-verifiable condition.
```

### Anti-Pattern C: Checker-State Upgrading

```text
WRONG:
  "oridivon-verify returns exit 0 → CLAIM: system is correct"

RIGHT:
  "oridivon-verify returns exit 0 → CLAIM: selected checks passed.
   Do not upgrade checker-state to governance-state."
```

---

## 4. Why This Template Works

```text
Not "be more careful." Structure forces correctness.

Controlled vocabulary    → Can only say verifiable words
Per-dimension isolation  → Cannot compress across dimensions  
Forbidden synthesis      → Cannot substitute a summary for evidence
Vocabulary verification  → detect_overclaim.py catches violations automatically
```

---

## 5. Usage

```bash
# Before publishing any assessment:
python scripts/detect_overclaim.py <assessment-file>

# If findings > 0:
# Fix the forbidden words. Do not add an exception. Fix the text.
```

---

## 6. Controlled Vocabulary Reference

See `docs/governance/schemas/claim-vocabulary.json`.

```text
Allowed in governance claims:
  READY      ← selected checks pass (ordivon-verify exit 0)
  BLOCKED    ← hard failure exists (ordivon-verify exit 1)
  DEGRADED   ← non-blocking issues exist (ordivon-verify exit 2)
  PASS       ← specific named checker returns exit 0
  OPEN       ← debt/lesson has status=OPEN with review trigger
  CLOSED     ← debt has status=CLOSED with resolution evidence
  VERIFIED   ← receipt + evidence + scope boundary present

Forbidden in governance claims:
  complete, completed, 全线闭合
  all done, all green, 全绿
  honest, perfect, finished
  100%, zero issues, no problems
  全部通过, 已完成, done
```

---

## 7. The Hardest Thing About This Template

It refuses to give the reader a summary.

This is uncomfortable. People want a conclusion. "Is it done or not?"

The template does not answer that question when dimensions differ.
It says: "Here is the state of each dimension. Judge for yourself."

This is not indifference. It is epistemic integrity.

```text
Medicine:  "Temperature 36.5, BP 120/80, WBC elevated. Recommend follow-up."
           ← Does not say "patient is fine."

Law:       "Two claims upheld. One dismissed. Appeal window: 30 days."
           ← Does not say "case won."

Engineering: "14/16 tests pass. 2 skipped (env mismatch). Deploy gate not cleared."
           ← Does not say "system complete."

Ordivon:   "Document governance: VERIFIED. Lesson pipeline: DEGRADED.
           4 OPEN debts. 1 draft checker. Pre-execution gate: not CI-enforced."
           ← Does not say "foundation complete."
```

This is what professional domains do. Ordivon treats governance as a
professional domain, not as a management presentation.

---

```text
READY means selected checks passed; it does not authorize execution,
does not authorize merge, does not authorize deployment, and does not
authorize release, tool use, policy activation, or external action.
```
