# Claim–Evidence Interface R2

R2 extends the existing Context24 identity interface with exact evidence content bytes while retaining R1 authority boundaries.

```text
Claim
  | annotated_supporting_evidence_identity
  v
EvidenceIdentity
  | materializes_evidence_identity
  v
EvidenceContent (exact upstream PNG bytes)
```

Task-1 public training gold contains 679 evidence-identity links. At the bound upstream release, 256 links map by exact `citekey/evidence-label` path to 223 unique PNG objects. The remaining 423 identities remain `identity_only`; R2 does not guess missing filenames.

Focal full-text carriers cover all current claim citekeys used by Task-1 train (229/229) and test (46/46), but full-text availability is not method adequacy or claim validity. Challenge-test gold remains withheld and is never inferred from test media.

`EvidenceContent` proves byte identity only. It does not establish support strength, scientific truth, causal support, or ClaimPermission. The dataset card is observed as CC BY 4.0, but underlying source-paper media rights are not independently verified, so external redistribution and commercial media reuse remain fail-closed.
