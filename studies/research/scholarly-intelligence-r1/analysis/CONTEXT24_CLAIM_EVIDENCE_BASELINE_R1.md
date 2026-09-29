# Context24 Claim–Evidence Baseline R1

Date: 2026-09-23
Source asset: `context24-identity-core-r1`
Scope: **identity/snippet layer only**

## Exact carrier

Task 1 contains **585 source rows**: **474 train** with public gold findings and **111 challenge-test rows** with findings withheld. The training rows expose **679 annotated evidence-identity links**: **554 figure/supplementary-figure links** and **125 table links**.

Task 2 contains **151 source rows**: **42 train** with public gold context and **109 challenge-test rows** with context withheld. The training rows expose **210 annotated methodological-context snippets**.

## Identity anomaly that must remain visible

Task 1 training has **19 native-ID collision groups**. They decompose into `{'exact_duplicate_rows': 11, 'same_claim_different_finding_set': 5, 'same_claim_same_finding_set_different_order_or_serialization': 2, 'same_native_id_different_claim_text': 1}`. Therefore native `id` is not a primary key. R1 uses `claim_instance_id = task:split:source_row_index` as physical identity and retains the native id as provenance metadata.

There is **0 exact `(citekey, claim)` overlap** between Task 1 train and test, although **6 source papers** occur in both splits. Paper overlap must not be described as claim leakage.

## Evidence multiplicity

Task 1 train evidence multiplicity is `{'1': 349, '2': 89, '3': 10, '4': 17, '5': 4, '6': 3, '7': 1, '9': 1}`. Task 2 train method-context multiplicity is `{'10': 1, '11': 1, '2': 2, '3': 6, '4': 12, '5': 9, '6': 6, '7': 3, '8': 1, '9': 1}`. These are annotation-structure descriptors, not measures of evidential strength.

## Interpretation ceiling

An annotated figure/table identity does not establish scientific truth, causal support, or adequacy. A method-context snippet does not establish that the method is valid. Test gold is withheld and remains absent. R1 deliberately omits figure/table pixels, captions, full text, and the silver 17k-paper expansion; those belong to later content-bound layers.
