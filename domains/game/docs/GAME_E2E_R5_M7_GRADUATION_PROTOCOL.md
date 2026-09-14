---
schema_version: 1
id: game.e2e.r5.m7.graduation-protocol
title: Ordivon Game E2E R5 M7 — Graduation / Current-Carrier Closure Protocol
profile: research-engineering
lifecycle: frozen-protocol
source_role: normative-for-r5-m7-only
visibility: public
owners:
  - ordivon-game
updated: 2026-09-10
---
# Game E2E R5 M7 — Graduation / Current-Carrier Closure Protocol

## 0. Purpose and anti-collapse boundary

M7 answers one bounded question: whether the R5 Game E2E infrastructure/domain boundary can become the default Game E2E carrier without laundering project-specific, Human, rights, artifact, Workstation, Distribution, or Operations standing.

M7 does **not** complete Veilwild, collect Human sessions, clear rights, expand Distribution, build a second game, replace Godot, or redesign Host/Runtime. Findings in those areas are routed as separate work unless they falsify an M7 graduation invariant.

Final Game E2E verdict vocabulary is exactly:

```text
GRADUATED | HOLD | REJECTED
```

A project may remain HOLD/UNKNOWN while the Game E2E evaluator itself graduates, provided the evaluator preserves that uncertainty correctly.

## 1. Frozen research question

> After the R5 subtraction of duplicate generic infrastructure, does the remaining Game-owned kernel contain the necessary and sufficient Game-specific semantics to compose mature owner-external E2Es, preserve historical failure detection, and fail closed when evidence does not justify a higher-level claim?

This question is frozen for M7. Discovery of adjacent useful work does not broaden it.

## 2. Exact opening evidence cut

M7 re-enters the independently destroyed M6 candidate:

```text
Game candidate revision: a3cae0c403a4d758c3975f0508c7c267b4299efe
M6 sourceStateDigest:    sha256:c3b0676b9f38ebef0feccf4667577fdd15f749c5a2b6a5671ff6780942087a71
M6 verdict:              PASS_BOUNDED
M7 workspace:            ws-game-e2e-r5-m7-graduation-20260910-v1
```

Fresh M7 dependency materialization used the exact pnpm lockfile with `--offline --frozen-lockfile`, reused 8 packages, downloaded 0, and was followed by a fresh full `pnpm check` of 386/386 PASS:

```text
materialization job: job-01a08b9d-347b-7903-a680-592fe0355c20
baseline full check:  job-01a08b9d-5df0-78e0-b9d2-f414fe0c7bc9
```

The initial pre-materialization `tsc not found` failure is retained as an environment-readiness observation and is not rewritten as a code failure.

## 3. Estimands

### E1 — Subtraction sufficiency

Estimate whether removing the duplicate embedded Host lifecycle reduces Game-specific judgment or failure-detection power.

Failure witness: at least one previously meaningful Game failure or authority distinction cannot be detected or represented after subtraction.

### E2 — Boundary sufficiency

Estimate whether the residual Game-owned evidence/kernel boundary is necessary for Game-specific semantics rather than a hidden copy of another owner's generic infrastructure.

Current residual implementation under test:

```text
src/integration/local-evidence-journal.ts
src/integration/game-evidence.ts
src/team/commitment-view.ts
```

Failure witness: a residual component has no deletion-sensitive Game-specific invariant, or it mints Host/Artifact/Research/Workstation authority that Game does not own.

### E3 — Compositional sufficiency

Estimate whether Game can consume owner-external Research, Engineering, Artifact, Workstation, Host/Runtime, Distribution and Operations capabilities through explicit edges without inheriting their internal authority or requiring Game-local reimplementation.

Failure witness: a current required Game edge depends on an unbounded owner-internal representation, caller-supplied physical authority, or duplicated generic lifecycle.

### E4 — Graduation-semantics sufficiency

Estimate whether evidence and standing are prevented from climbing abstraction layers without an explicit admissible edge.

Failure witness: technical/mechanical/artifact/provenance success can silently produce Human, rights, product, release, candidate-nomination, or current-carrier success.

## 4. Falsifiable hypotheses

The following hypotheses are targets for destruction, not assumptions to be confirmed:

- **H1 Subtraction preservation** — deletion of the generic embedded Host lifecycle does not reduce Game-specific failure detection.
- **H2 Authority isolation** — the Game kernel does not require concrete Host/Runtime/Workstation/Artifact internal schemas to assign Game meaning.
- **H3 No standing laundering** — technical PASS does not establish a Human-experience claim; `provenance/artifact PASS + rights INCONCLUSIVE` remains release-blocking; mechanical study readiness with zero participant sessions leaves Human-state claims unobserved/UNKNOWN. Historical evidence objects may retain their original `humanEvidenceStanding` field names.
- **H4 Historical observability** — historical Veilwild/Station Zero failure conditions remain distinguishable by exact evaluation condition rather than being rewritten by newer green state.
- **H5 Current-carrier uniqueness** — one immutable Game E2E current carrier can be named mechanically, with all competing refs classified as CURRENT, SUPERSEDED, HISTORICAL, or QUARANTINED.

## 5. Forbidden inference

M7 MUST NOT infer any of the following:

```text
process exit 0                  => Game oracle PASS
technical PASS                 => Human-experience claim supported
browser/mechanical readiness   => Human participant evidence
artifact/provenance valid      => distribution rights
Game E2E GRADUATED             => Veilwild nominated/releasable
one owner-edge candidate PASS  => owner production-current
branch name `main`              => authoritative current source
later green evaluation         => earlier negative condition never occurred
```

The same rule applies transitively: truth does not climb abstraction layers without an explicit evidence edge.

## 6. External mature-pattern anchors

M7 uses external standards as constraints, not as a claim that Game E2E is formally certified:

- **ISO/IEC 25010:2023** — product quality model; supports explicit product-quality requirements, evaluation, quality-control and acceptance criteria rather than one undifferentiated PASS.
- **ISO/IEC 25019:2023** — quality-in-use model; context of use is prerequisite to quality-in-use claims and must be respecified when context changes.
- **ISO 9241-11:2018** — usability is an outcome of use; supports keeping usability claims about a defined Human population/context distinct from apparatus readiness.
- **ISO 9241-210:2019** — human-centred design activities apply through the interactive-system lifecycle; supports using relevant Human participant evidence for Human-state claims rather than substituting technical readiness for those claims.
- **SLSA v1.2** — provenance is verifiable information about where/when/how an artifact was produced; it does not by itself establish Game meaning, Human outcome, or legal distribution rights.

These anchors define useful separations. M7 does not create local replacements for these standards or register them as universal Game primitives.

## 7. Current-carrier opening observation

Local Git refs observed from the exact M7 candidate workspace on 2026-09-10:

```text
game-e2e-r5-candidate = a3cae0c403a4d758c3975f0508c7c267b4299efe
local main            = fc31c1e1e4536fc7a672970c7e5afd6bc4d8627f
local origin/main     = ca8f207b8d08ccd3c0e263810c35ac70b1511aee
```

`origin/main...game-e2e-r5-candidate` is `1 left / 49 right`. The sole observed origin/main-only commit is:

```text
ca8f207 policy: record public rights and publication standing
```

and changes only:

```text
.ordivon/publication.yaml
.ordivon/rights.yaml
```

This is a real source-current divergence. M7 must reconcile its semantic impact before current-carrier promotion; neither side is promoted by branch naming alone.

## 8. Engineering sequence

M7 Engineering MUST proceed in this order:

1. **Current-carrier closure** — reconcile source refs and classify every competing carrier.
2. **Cross-owner edge currentness** — test only edges Game currently consumes; do not audit entire owner systems.
3. **Authority-laundering destroyer** — inject false-PASS/false-READY/false-Human/false-rights/currentness pressure.
4. **Historical falsifier matrix** — replay retained failure conditions and verify exact condition-sensitive standing.
5. **Minimal-kernel destruction** — attempt to remove/bypass each residual 552-LOC component and identify the exact lost invariant; delete/move/derive anything with no Game-specific necessity proof.
6. **Freeze candidate** — no further producer changes after freeze except a new superseding candidate.
7. **Independent graduation adjudication** — fresh workspace, frozen protocol, independent destructive replay.

Repair is admitted only after a concrete failure witness. Passing code is not refactored merely to make the architecture look cleaner.

## 9. Cross-owner edge rule

M7 does not require every horizontal E2E to be globally mature. It requires every **currently consumed Game edge** to have explicit standing.

Each edge must be classified:

```text
CURRENT_PASS
BOUNDED_CANDIDATE
NOT_CURRENT
NOT_REQUIRED_FOR_M7
UNKNOWN
```

`BOUNDED_CANDIDATE` and `UNKNOWN` cannot be silently upgraded to production-current.

## 10. Required authority-laundering attacks

At minimum the destroyer must demonstrate fail-closed behavior for:

1. mechanical/technical PASS with the relevant Human-state claim still UNKNOWN;
2. browser study readiness with zero participant sessions;
3. artifact/provenance success with rights INCONCLUSIVE;
4. Workstation executable existence without admitted Workstation authority;
5. Host/Runtime success with missing authoritative Game receipt/evidence;
6. later successful Veilwild condition without erasing the cold/import-readiness failure condition;
7. branch/ref naming without exact current-carrier reconciliation;
8. exact evidence from one candidate composed with another candidate without explicit impact reasoning.

## 11. Historical falsifier matrix requirement

For each retained historical falsifier, record:

```text
failureId
historical exact condition
current detector/oracle
expected standing
observed standing
source/artifact/environment identities
whether later evidence can supersede, coexist, or must not compose
```

The matrix is an evidence-retention test, not a demand to preserve obsolete implementation internals.

## 12. Minimal-kernel necessity test

LOC reduction is not an optimization target. Each residual component must answer:

> If this component is removed or replaced by a thinner derived/owner-external mechanism, which Game-specific invariant becomes unprovable or false?

If no such invariant can be demonstrated, disposition is `DELETE`, `MOVE`, or `DERIVE` rather than `KEEP`.

## 13. Stopping rules

M7 stops with **GRADUATED** only when all are true:

- exact current Game E2E carrier is mechanically unique;
- required consumed owner edges have explicit non-laundered currentness standing;
- all mandatory authority-laundering attacks fail closed;
- historical falsifier matrix preserves required judgment;
- residual Game kernel has bounded necessity evidence or explicit retained debt;
- frozen candidate passes independent fresh-workspace full regression and destructive replay;
- final manifest keeps Game E2E standing separate from project/Human/rights/release standing.

M7 stops with **HOLD** when the Game architecture is not falsified but one or more externally resolvable/currentness blockers prevent graduation. HOLD must name exact blocker and wake condition.

M7 stops with **REJECTED** when a core M7 hypothesis is falsified in a way that requires reopening the R5 architecture (for example, subtraction loses meaningful Game judgment or the residual kernel still owns generic lifecycle authority).

No fourth verdict is allowed.

## 14. DO-NOT-INHERIT

Regardless of the M7 verdict, do not inherit or upgrade:

```text
Veilwild candidate nomination       NOT_YET_NOMINATED
Veilwild distribution rights        INCONCLUSIVE until independently changed
Veilwild Human-state claim standing UNKNOWN until relevant Human participant evidence
Station Zero fresh-player claims    UNKNOWN until relevant Human participant evidence
full external evidence substitution NOT_ADMITTED unless a lossless owner edge is proven
```

Game E2E graduation proves an evaluator/composition boundary, not the success of every evaluated product.
