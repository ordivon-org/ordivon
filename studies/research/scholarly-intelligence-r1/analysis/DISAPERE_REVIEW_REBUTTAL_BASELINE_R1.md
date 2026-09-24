# DISAPERE Review–Rebuttal Discourse Baseline R1

Date: 2026-09-23
Source asset: `disapere-bounded-core-r1`
Scope: **DISAPERE 506-pair annotated corpus only**

## Corpus

The bounded corpus contains **506 review–rebuttal pairs**, **9,946 review sentences**, **11,103 rebuttal sentences**, and **21,675 explicit local review-sentence links**. The normalized analytical layer contains no reviewer or annotator identity fields.

## Explicit local alignment coverage

- all review sentences: **4,096/9,946 (41.18%)**;
- request sentences: **1,441/1,971 (73.11%)**;
- negative-polarity sentences: **2,004/2,927 (68.47%)**;
- clarity sentences: **600/1,102 (54.45%)**;
- soundness/correctness sentences: **626/953 (65.69%)**;
- replicability sentences: **214/284 (75.35%)**.

This is **explicit local sentence alignment**, not a response-rate estimator. DISAPERE separately represents global and in-rebuttal context.

## Rebuttal structure

Across all rebuttal sentences, stance counts are `{'nonarg': 3995, 'dispute': 1751, 'concur': 5296, 'other': 61}`. Alignment kinds are `{'context_global': 816, 'context_in-rebuttal': 647, 'context_sentences': 9416, 'context_none': 152, 'context_unknown': 11, 'context_error': 61}`. For the **9,416** locally aligned rebuttal sentences, the number of linked review sentences has median **2.0**, IQR **1.0–3.0**, and maximum **25**.

Among **5,220** rebuttal sentences explicitly linked to at least one review request, stance counts are `{'concur': 3397, 'nonarg': 1352, 'dispute': 471}`. The dominant response action is `rebuttal_answer` (**2,496**), followed by structuring, done, summary, and several reject/concede/mitigate actions.

## Ordivon implication

The data supports a typed circuit rather than a scalar reviewer score:

`ConcernType -> ExplicitContext -> ResponseStance -> ResponseAction -> ResolutionCandidate -> RevisionEffect`

`ExplicitContext` must allow local-sentence, global, in-rebuttal, none, unknown, and error states. Stance and action remain descriptive annotations; they do not authorize scientific or submission decisions.

## Rights boundary

The canonical repository applies **CC BY-NC 4.0**. This snapshot is admitted for current non-commercial research only. It is **not** authorized for future commercial product/service use without another rights basis.
