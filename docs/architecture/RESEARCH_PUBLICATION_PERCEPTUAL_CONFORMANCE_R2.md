# ADR 鈥?Publication Perceptual Conformance and Human-Authority Boundary

Date: 2026-09-22

Status: **R2 IMPLEMENTING**

Supersedes the reviewer-experience ownership assumption in
`RESEARCH_PUBLICATION_CLOSURE_R1.md`. It does not invalidate the R1 carrier,
venue, Study-authority, or scientific-freeze boundaries.

## Problem

R1 deliberately kept `HUMAN_PERCEPTUAL_SIGNOFF` explicit because machine layout
PASS was insufficient evidence for reviewer-visible quality. That was correct as
a fail-closed intermediate state, but it conflated two different properties:

1. an assessment is non-deterministic or difficult to automate;
2. decision authority must belong to a human author.

They are not equivalent.

The PDF Association's 2026 Matterhorn terminology update explicitly reframes the
older machine/human distinction as deterministic/non-deterministic assessment.
The Ghent Workgroup Universal Proof of Preflight treats preflight outcome,
profile identity, and post-check alteration detection as auditable evidence.
Chromium pixel tests use approved screenshot baselines to detect unexpected
visual change. veraPDF formalizes standards requirements as validation profiles
and exposes machine-readable policy checking.

These mature patterns imply that a publication carrier can use automatic and
agentic perceptual observers without assigning routine QA labor to the author.

## Decision

Adopt:

**HumanRequired = HumanAuthorityRequired, not HardToAutomate.**

Publication closure R2 separates four layers:

    OBSERVE
      -> deterministic carrier evidence and canonical raster

    PERCEIVE
      -> independent non-deterministic visual/semantic observers

    ADJUDICATE
      -> fail-closed consensus and specialist escalation

    ATTEST
      -> independent release verification and hash-bound carrier evidence

The generic R1 perceptual observer roles are:

- `BLIND_VISION`: page rasters only; no source or previous findings;
- `VENUE_AWARE_VISION`: page rasters plus venue presentation rubric;
- `SEMANTIC_LAYOUT`: text/layout/inventory evidence; no other observer findings.

R1 consensus is deliberately conservative:

- all three roles exactly once;
- distinct observer IDs;
- distinct declared independence keys;
- exact carrier-digest binding;
- 100% page, figure, and table coverage;
- no BLOCKER or MAJOR findings;
- no UNCERTAIN findings;
- all observer standings PASS.

Only then is the result `PASS_AGENT_ENSEMBLE`.

Uncertainty produces `ESCALATE_SPECIALIST`, whose default destination is an
independent publication specialist, not the paper author.

## Human authority that remains Human

This ADR does **not** automate or transfer:

- authorship declarations;
- relationship / program-committee conflict attestations;
- originality or simultaneous-submission attestations;
- ethics, legal, or policy declarations where a human must attest;
- final authorization to submit or publish.

Those are authority boundaries, not perceptual QA.

## Artifact ownership

Artifact owns reusable mechanics:

- deterministic carrier inventory;
- canonical page raster manifests;
- raster regression;
- observer-report validation;
- perceptual consensus;
- evidence binding;
- carrier attestation.

Artifact does not own:

- scientific truth;
- venue policy;
- multimodal model internals;
- semantic peer review;
- author legal authority.

Observer providers remain replaceable.

## External patterns

### PDF Association / Matterhorn

The relevant architectural lesson is terminology: prior "human" checkpoints
should be understood as non-deterministic assessment classes rather than a
permanent claim that only a human may perform them.

Authority:
https://pdfa.org/gaad-2026-advancing-accessible-pdf/

### Ghent Workgroup Universal Proof of Preflight

The relevant pattern is a profile-bound audit trail that records which preflight
profile was used, its outcome, and evidence that the checked PDF has not changed.

Authority:
https://gwg.org/technical-specifications/universal-proof-of-preflight/

### Chromium pixel tests

The relevant pattern is screenshot regression against an approved baseline to
detect unintended rendering change. Visual regression detects change; it does
not by itself establish correctness.

Authority:
https://chromium.googlesource.com/chromium/src/+/main/docs/testing/pixel_tests.md

### veraPDF

The relevant pattern is explicit validation profiles plus machine-readable
policy checking. Accessibility support is an optional observer in R1 unless a
venue contract makes it mandatory.

Authority:
https://docs.verapdf.org/validation/
https://docs.verapdf.org/policy/

## R1 implementation

Reusable modules:

- `publication/inventory.py`
- `publication/visual.py`
- `publication/perceptual.py`
- `publication/attestation.py`
- `scripts/publication_perceptual_verify.py`

Schemas:

- `profiles/research/publication/finding-r1.schema.json`
- `profiles/research/publication/observer-report-r1.schema.json`
- `profiles/research/publication/perceptual-conformance-r1.schema.json`
- `profiles/research/publication/carrier-attestation-r1.schema.json`

Profiles/planning:

- `profiles/research/publication/perceptual-conformance-profile-r1.json`
- `profiles/research/publication/publication-closure-profile-r2.json`
- `studies/research/scholarly-intelligence-r1/planning/publication-perceptual-conformance-lego-r1.json`

## Legacy migration

The R1 gate:

    HUMAN_PERCEPTUAL_SIGNOFF

is not deleted. Historical receipts remain historical evidence.

For a new exact carrier, it may be marked:

    SUPERSEDED_BY_PERCEPTUAL_CONFORMANCE_R1

only after exact-digest perceptual evaluation reaches:

    PASS_AGENT_ENSEMBLE

If observers disagree or coverage is incomplete, closure becomes
`ESCALATE_SPECIALIST`; it must not silently fall back to author labor.

## Non-goals

- no claim that multimodal reviewers are infallible;
- no replacement for scientific peer review;
- no 2-of-3 majority shortcut in R1;
- no universal requirement that accessibility checks block every venue;
- no inference of model independence from labels alone;
- no automatic venue submission or legal attestation.
