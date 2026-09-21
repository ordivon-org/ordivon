# Browser Decision Provider Duel R1

## Standing

**NO_TRAINING_JUSTIFIED_R1**

This is a controlled-fixture research result. It does not authorize production route changes and
does not establish open-web provider superiority.

## Frozen corpus

Browser Decision Corpus R1 contains 42 non-singleton decision cases generated from browser-owned
AX semantics plus strict DOM effect-safety metadata.

- CLICK: 30
- FILL: 7
- SELECT: 5
- context-required: 8
- candidate set sizes: 2 to 24

A singleton FILL case was rejected during corpus construction rather than sent to a decision model.
The architecture invariant is:

`|Candidates| = 1 -> deterministic binding; no ranking model required.`

## Same-corpus provider results

| Provider | Coverage | Accuracy | MRR | Brier | NLL | Median latency |
|---|---:|---:|---:|---:|---:|---:|
| ms-marco MiniLM CrossEncoder | 42/42 | 92.86% | 0.9643 | 0.1499 | 0.2503 | 14.13 ms |
| base Laya, independent noul normalization | 42/42 | 11.90% | 0.2579 | 0.8804 | 2.4671 | 114.92 ms |
| Jev fast Windows route | 0/42 | not observed | not observed | not observed | not observed | not observed |

Jev is not scored as wrong. Existing route readiness blocks execution because
`TYPESAFE_API_KEY` is absent.

## What the CrossEncoder actually learned here

A zero-training name-only lexical baseline already reaches 36/42 (85.7%). Therefore the overall
92.9% CrossEncoder score must not be interpreted as 42 hard semantic decisions.

The useful difference is concentrated in context-dependent cases:

- CrossEncoder context-required: 8/8
- name-only lexical context-required: 4/8

The CrossEncoder's three misses are:

1. `g17-nested-button`: chose a sibling gridcell over the nested button.
2. `g20-frame-apply`: chose the frame query textbox-click over the Apply button.
3. `t03-find-stays`: chose the destination searchbox-click over the Find stays button.

## Decision-layer reduction probe

A diagnostic reduction distinguishes CLICK-to-focus from CLICK-to-activate before ranking:

- explicit focus goal -> editable click candidates;
- other click goals -> non-editable candidates when available.

This is not a production natural-language parser. It is a falsification probe for whether the
three misses require model training.

Result:

- CrossEncoder baseline: 39/42
- diagnostic reduction + same CrossEncoder pair scores: 41/42
- changed cases: exactly `g20-frame-apply` and `t03-find-stays`
- newly broken cases: 0
- candidate pairs: 638 -> 416 (-34.8%)
- median candidate count: 16.5 -> 8

The reduction therefore explains two of the three errors as effect-class competition rather than
model-capacity failure.

## Why g17 is not training evidence

Live Chromium AX ancestry inspection shows:

- `Nested cell button` is a button child of a gridcell also named `Nested cell button`;
- the projector intentionally removes that parent gridcell because it has an actionable descendant;
- `Scholarship cell`, which the CrossEncoder selected, is a sibling gridcell in the same row.

The benchmark wording says "not its parent grid cell", but that parent is not present in the
decision candidate set. The case therefore reintroduces an observation-layer ambiguity already
eliminated upstream. It remains useful as a negative benchmark-design finding, but it is not clean
evidence that the reranker needs training.

## Laya result

Base Laya using one independent noul question per candidate does not provide a competitive browser
reranker in this composition:

- CLICK: 1/30
- FILL: 0/7
- SELECT: 4/5

Its per-candidate probabilities are also nearly flat in many CLICK cases. This result only rejects
this **base-model + independent-noul + normalization composition**. It does not establish that a
Browser-specific trained Laya model could not work.

## Current architecture decision

Do not train a Browser CrossEncoder or Laya on these 42 controlled cases.

The next evidence gate is a larger real-page / real-application candidate census that preserves:

1. browser-owned AX semantics;
2. DOM effect-safety gating;
3. operation/effect-class partitioning before ranking;
4. singleton deterministic bypass;
5. digest-bound dynamic-choice observations;
6. separate coverage for BLOCKED/ERROR rather than treating them as wrong predictions.

Training should reopen only if the larger corpus leaves a reproducible residual that cannot be
explained by observation completeness, effect partitioning, deterministic reduction, or benchmark
contamination.
