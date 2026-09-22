---
name: research-publication-perceptual-conformance
description: Compose deterministic carrier evidence, isolated perceptual observer reports, fail-closed consensus, specialist escalation, and hash-bound carrier attestation without turning difficult QA into author labor.
---

# Research Publication Perceptual Conformance

Use this skill after deterministic carrier/venue checks and before artifact
freeze or submission freeze.

## Authority boundary

The invariant is:

`HumanRequired = HumanAuthorityRequired, not HardToAutomate.`

Do not route ordinary publication QA to the author merely because the check is
non-deterministic.

Human authority remains required for authorship, conflicts, originality,
ethics/legal declarations, and final submission authorization.

## Execution model

1. Bind the exact carrier SHA-256.
2. Build deterministic carrier inventory and canonical rasters.
3. Run deterministic visual regression if a previous accepted carrier exists.
4. Run three isolated observer roles:
   - BLIND_VISION;
   - VENUE_AWARE_VISION;
   - SEMANTIC_LAYOUT.
5. Require exact carrier binding and complete page/figure/table coverage.
6. Run the Artifact consensus evaluator.
7. If unanimous and clean, emit `PASS_AGENT_ENSEMBLE`.
8. If uncertain or observer isolation/coverage is incomplete, emit
   `ESCALATE_SPECIALIST`.
9. If a blocker/major finding or observer FAIL exists, emit `FAIL`.
10. Bind the result into an independent release-verification receipt and carrier
    attestation.

## Observer isolation

BLIND_VISION must not receive manuscript source, expected conclusions, previous
QA conclusions, or other observer findings.

VENUE_AWARE_VISION may receive page images and venue presentation rubric, but
not previous observer findings.

SEMANTIC_LAYOUT may receive text-layer/layout/inventory evidence and venue
structural rules, but not the other observer outputs.

Do not call reports independent merely because prompts say so. Preserve distinct
execution/provenance identities and record an `independenceKey` for each
observer receipt.

## Findings

Normalize findings to:

- BLOCKER
- MAJOR
- MINOR
- INFO
- UNCERTAIN

Do not let free-form prose silently determine release standing.

## Consensus

R1 is 3-of-3 unanimous, not majority vote.

A PASS requires:

- deterministic carrier PASS;
- all three roles exactly once;
- distinct observer IDs and independence keys;
- 100% pages, figures, and tables reviewed;
- no blocker/major/uncertain findings;
- every observer standing PASS.

Uncertainty escalates to an independent publication specialist, not the author.

## Stop rules

- perceptual conformance is not scientific correctness;
- visual regression detects change, not correctness;
- do not reopen science for carrier-only defects absent contradictory evidence;
- do not treat a model label as proof of independence;
- do not emit carrier attestation before release standing is PASS;
- do not automatically submit to a venue.
