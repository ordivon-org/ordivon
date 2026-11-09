# Harness document-retirement evaluation 004

A bounded, model-independent outcome verifier for an Agent tasked with retiring
unconsumed documentation. The intended Agent evaluation workspace contains only a copied `fixture/`
and an objective; the acceptance oracle `verifier.py` remains outside the
candidate workspace. This slice exercises the oracle without a live Agent. Reports, claimed completion receipts, no-op conservatism, or
over-deletion cannot satisfy the consumer.

Run from the repository root:

```sh
python3 -m unittest discover -s services/harness/tests -p test_eval_harness_document_retirement_004.py -v
```

The test checks every one of the 32 possible deletion subsets of five files,
plus report-only, false receipt, content tampering and unrelated addition.
The positive candidate deletes exactly the two historical stage documents.

This checks **only the fixed test fixture**. It does not certify actual external
consumers, broad Agent navigation, provenance at a live SourceCut, model
performance, permission admission, live effects, or universal R2.1 refinement.
The natural Owner retains the real acceptance decision. See GitHub issue #1964.
