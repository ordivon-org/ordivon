# OMPC-v0 Fixture C — Web interaction trajectory dogfood

Fixture C consumes existing **Web-owned** M7 evidence without moving Web authority into Media.

## Exact source and rerun

- observed Web source: `407d151f0939de87286be50ec24ca35fc2c04bb4`;
- M7 runner introduced by `fa3b00c210a14bb58a50350870eb4322fcabed37`;
- runner: `scripts/run-m7-interaction.mjs`;
- source proposition and operation identity are held constant (`op-recovery-42`);
- real Chromium rerun succeeded with evidence digest `sha256:1469ce31fc89f064087ca12a4db163ac1975d84bde4bd115b9dd5d38f25cd14e`.

The first pnpm attempts were bootstrap/equipment failures, not hypothesis failures: one executable path was wrong and a fresh worktree lacked pnpm dependency verification state. After dependencies were materialized, the unchanged Web runner was executed directly with Node and passed.

## Three encounters

```text
lawful
check → checking → unknown → recover → unknown

premature-success
check → Succeeded → unknown → recover → unknown

silent-delay
check → no feedback → unknown → recover → unknown
```

All three share the same source proposition, operation identity, and normalized initial/final static state. All final screenshots also share the same digest `sha256:d2b7d88a...`.

## Destructive tests

### C1 — Endpoint equivalence does not prove encounter equivalence — PASS

All variants report `staticInitialFinalEquivalent=true`, yet the transient states are `checking`, `success`, and `idle` respectively.

### C2 — Premature semantic lifting is trajectory-visible only — PASS

`premature-success` transiently displays `Succeeded` before evidence exists, registering `feedback-claims-success-before-evidence`. The defect disappears from initial+final freeze.

### C3 — Missing feedback is trajectory-visible only — PASS

`silent-delay` remains visually idle after action during the transient window, registering `latency-without-feedback`. The defect also disappears from initial+final freeze.

### C4 — Static omission is a temporal loss operation — PASS

The Web ablation reports `allRegisteredDefectsRequireTrajectory=true`. Therefore a projection that retains only endpoints loses material encounter semantics.

### C5 — Web authority remains external — PASS

Browser source, interaction behavior and evidence remain Web-owned. Media consumes the exact source/evidence fence and adds only the contract consequence.

## OMPC consequence

Fixture C adds **Temporal Coverage Non-Collapse** as invariant 10:

```text
same initial + final != same encounter
static endpoint coverage != trajectory coverage
```

No new semantic role is needed. Temporal coverage belongs inside the existing projection envelope / representation / provenance responsibilities.

## A/B/C comparison and extraction decision

Three materially different fixtures now exist:

1. Host continuity/currentness projection;
2. Studio transformation/provenance/identity;
3. Web interaction trajectory/time/state/feedback.

All reproduce the need for exact source binding, scoped projection, provenance, explicit loss/omission and authority non-lifting. This is enough to treat OMPC-v0 as a credible **shared reference contract/conformance corpus**.

It is **not** enough to admit shared Media implementation code: the three owners do not yet show duplicated implementation machinery that a common SDK/runtime/validator would simplify. The next extraction unit, if needed, should begin as conformance fixtures/checks rather than a Media engine.
