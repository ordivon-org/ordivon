# Review consumption

## Purpose

C5 closes the next part of the Agent-first creative loop: an Agent should be able to consume one real review packet, identify a bounded semantic problem, revise only the implicated expression, and return to a new real artifact without turning critique into a permanent approval system.

```text
review packet
      ↓
Agent semantic inspection
      ↓
bounded revision / no-op / targeted calibration
      ↓
new render + new review packet
```

The review packet is durable enough for one working iteration. The Agent's intermediate critique is not durable by default.

## Two evidence planes

A useful review packet needs two different kinds of evidence.

### Render evidence

This is what physically produced or describes the candidate artifact:

- rendered video Blob identity;
- technical media facts and QC;
- exact review frames;
- materially responsible source files and their Blob identities.

### Decision context

This is what the Agent is allowed to use when deciding whether the artifact is semantically appropriate:

- the exact Production source;
- the current Production cognition record;
- the current Claim boundary.

C5 records these as a `decisionContext` snapshot with exact file digests. A path alone is insufficient because the file may change between iterations.

The distinction matters:

> Render evidence explains what artifact was observed. Decision context explains what judgment boundary was applied to it.

Neither plane replaces the owning source. The packet is a snapshot for review, not a new authority.

## Critique is transient by default

C5 intentionally does **not** introduce a persistent `critique.json`, review database, score history, approval object, or chain-of-thought log.

Most Agent critique exists only long enough to choose one of three routes:

```text
supported local problem      → revise
no material problem          → no-op
important human-response gap → targeted calibration
```

What survives is the consequence:

- source diff;
- new artifact/review evidence;
- a scoped Production cognition update when the finding matters for continuation;
- profile/Core promotion only after repeated independent pressure.

This prevents iteration speed from being converted into documentation volume.

## First C5 acceptance

The C4 replay motion showed:

```text
same Job · same Attempt
```

The selected Runtime Receipt independently exposes:

```text
execution.jobId
execution.attemptId
execution.sameJobAfterReplay = true
```

The underlying demonstration and `plan.md` report that exact replay returned both the same Job and Attempt, but the selected Receipt contract does not encode an independent `sameAttemptAfterReplay` invariant. A review Agent consuming the candidate plus its selected Receipt therefore had a weaker machine-verifiable chain for the second half of the banner than for the first.

C5 did **not** invent a new Receipt fact to preserve the existing wording. It narrowed the expression instead:

```text
Recorded Attempt <id>
...
same recorded Job
Exact replay returns this recorded Job. It does not admit a second Job.
```

This keeps the displayed Attempt as a recorded execution identity while placing the replay-equality conclusion only on the Job property explicitly carried by the selected Receipt.

## Bounded revision evidence

The candidate was rendered before and after the semantic revision with the same local render path and review frames.

Observed frame identity:

```text
frame 0   unchanged
frame 75  changed
frame 130 changed
frame 165 changed
frame 179 changed
```

Frame 0 precedes the affected execution/replay wording and retained the same PNG digest. Later selected frames containing the affected identity/confirmation expression changed. This is evidence that the revision was localized rather than a random full-artifact drift.

The new render remains a candidate. `assets.json` is deliberately unchanged because technical success and a bounded semantic improvement do not automatically promote a candidate into the selected Production Asset.

## Boundaries

C5 does not establish:

- autonomous aesthetic correctness;
- pixel-level visual interpretation by the current Agent interface;
- automatic approval or promotion;
- a universal critique ontology;
- mandatory persistence of Agent reasoning;
- that all semantic claims can be decided without human/expert calibration.

The current acceptance is narrower: **review evidence can carry enough stable authority context for an Agent to make and physically verify one bounded semantic revision without inventing a second creative-control system.**
