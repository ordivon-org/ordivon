# ARIES Review-to-Revision Baseline R1

Date: 2026-09-23
Source asset: `aries-bounded-core-r1`
Scope: **manual ARIES test annotations only**

## Result

The manual test slice contains **196 review comments** across **42 documents**. **87 comments (44.39%)** have at least one annotated positive edit correspondence; **109 (55.61%)** have none. The positive comments carry **182 positive links**, or **2.09 links per positive comment on average**. ARIES supplies **24,738 candidate-negative links** for this slice.

Positive-link multiplicity is concentrated at zero/one: `{'0': 109, '1': 50, '2': 18, '3': 4, '4': 2, '5': 7, '6': 4, '8': 1, '9': 1}`. Candidate-set size per comment has median **92.5**, IQR **69.0–165.0**, max **424**.

The associated review comments have median **25.0 whitespace-token words** (IQR 18.0–37.0). The papers represented by those comments expose a median **92.5 edit units** in ARIES. Across all 1,720 ARIES paper-edit documents, the median is **95.0**, with maximum **1976**.

## Interpretation ceiling

This is a dataset baseline for **comment↔edit correspondence**, not a peer-review population estimate. Positive alignment does not establish that a reviewer caused an edit or that the edit adequately resolves the concern. Dev labels are synthetic and excluded from the primary rates. The bounded core omits S2ORC paragraph text, so this R1 baseline does not judge edit semantics.

## Why it matters for Ordivon

The useful object is not a scalar reviewer score. ARIES gives us a typed relation:

`Concern/comment -> candidate edit set -> annotated correspondence`

That supports a future `Concern -> ResolutionCandidate -> RevisionEffect` circuit while preserving correspondence, causal, and adequacy boundaries as separate authorities.
