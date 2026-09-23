# Context24 Evidence Content Baseline R1

The public Task-1 training carrier contains 679 annotated gold evidence-identity links. At upstream commit `457d3b5c`, **256/679 (37.70%)** resolve by exact citekey + evidence-label path to an upstream PNG, representing **223 unique figure/table images**. The other **423** links remain identity-only; R1 does not guess filenames or substitute semantically similar media.

The focal full-text carriers cover all claim citekeys used by the current claim sets: Task-1 train **229/229** and Task-1 test **46/46**. Test gold remains withheld and is not inferred from the available test media/full text.

The byte binding establishes `EvidenceIdentity -> EvidenceContent`; it does not establish evidence adequacy, scientific truth, causal support, or ClaimPermission. The dataset card is observed as CC BY 4.0, while underlying source-paper media rights are not independently verified here, so external redistribution and commercial media reuse remain fail-closed.
