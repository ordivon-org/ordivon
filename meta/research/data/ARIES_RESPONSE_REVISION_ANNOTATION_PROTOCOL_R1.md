# ARIES Response→Revision Semantic Annotation Protocol R1

## Purpose
Construct an independently validated semantic relation between an author response and a concrete manuscript revision. R1 does **not** annotate response adequacy, scientific correctness, or causality.

## Unit
One annotation unit is one review concern with its complete bounded candidate set. Every candidate contains the exact concern text/context, one author response from the same review thread, and one concern-linked positive manuscript edit represented as source text → target text. Candidate sets are many-to-many; zero, one, or multiple semantic links are allowed.

## Primary relation label
- `DIRECT_REALIZATION`: the revision directly realizes, reports, or instantiates a change described by the response.
- `PARTIAL_REALIZATION`: the revision realizes a meaningful part of the response action but not the complete described change.
- `RELATED_NOT_REALIZATION`: topically related, but available text does not show that the revision realizes the response action.
- `NO_RELATION`: the response and revision concern different actions/content.
- `INSUFFICIENT_CONTEXT`: bounded text is insufficient to distinguish the above without guessing.

## Explicit separations
`semantic relation != causal effect != adequacy != scientific correctness`. A 1×1 group is not automatic gold, and lexical/ranking scores never have annotation authority. Every judgment fixes `adequacyStanding=NOT_ANNOTATED_R1` and `causalStanding=NOT_INFERRED`.

## Coding procedure
Read concern → identify the relevant response action → compare source/target as an edit → judge whether the edit realizes the response action → record basis/confidence → judge every candidate. Do not force exactly one positive candidate.

## Independence and blindness
Coder A and B receive equivalent content with independently shuffled group/candidate order. Diagnostic lexical/ranking features are excluded. Outputs are merged only after both cuts are frozen.

## Agreement and adjudication
Report pair-level raw agreement + nominal Krippendorff alpha. At group level report exact linked-set agreement and Jaccard after collapsing `DIRECT_REALIZATION`/`PARTIAL_REALIZATION` to linked. Preserve disagreements and route them to a frozen adjudication file; no coder overwrites another coder's cut.

## Gold admission
Gold requires either identical independent primary labels or explicit adjudication of a frozen disagreement. Training/evaluation remains blocked until complete coverage/provenance gates pass.
