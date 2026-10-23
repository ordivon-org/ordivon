# ADR — Research Publication Closure and Publication-Carrier Boundary

Date: 2026-09-21

Status: **R1 IMPLEMENTED**

## Problem

Paper3 demonstrated that strong scientific, reproducibility, and PDF-structural evidence can still leave publication-carrier defects:

- deterministic rendering can deterministically reproduce wrong metadata;
- a valid PDF can preserve literal source-language residue;
- duplicate captions can be structurally valid while looking unfinished;
- venue-required front matter can be absent without breaking PDF structure;
- a figure can be unclipped yet difficult to read at normal reviewer zoom.

Therefore:

**reproducible carrier != conformant carrier != reviewer-ready carrier.**

## Decision

Keep the accepted Research owner boundary:

- shared Research remains a composition profile and authority-binding protocol;
- Study authority owns scientific truth, claims, and scientific freeze decisions;
- Artifact owns reusable carrier mechanics and contract evaluation;
- mature renderers and PDF tools remain external replaceable providers;
- Runtime provides exact physical execution evidence when needed;
- venue policy remains a dated external authority binding;
- Human perceptual review remains explicit and cannot be inferred from machine layout PASS.

## Closure ordering

For submission closure, prefer:

    SCIENCE_FREEZE
      -> CLAIM_FREEZE
      -> MANUSCRIPT_SEMANTIC_FREEZE
      -> CARRIER_BUILD
      -> CARRIER_SEMANTIC_LINT
      -> VENUE_CONTRACT_VALIDATION
      -> PERCEPTUAL_REVIEW
      -> ARTIFACT_CARRIER_REBIND
      -> COLD_REPLAY
      -> SUBMISSION_FREEZE

This is not a universal research lifecycle. It is a closure ordering that prevents artifact digests from being frozen before publication-carrier QA.

## Artifact R1

Reusable implementation:

- capabilities/artifact/artifact_capabilities/publication/contract.py
- capabilities/artifact/artifact_capabilities/publication/probe.py
- capabilities/artifact/scripts/publication_carrier_verify.py

The probe delegates PDF observation to mature tools: qpdf, pdfinfo, pdftotext, and pdffonts.

The evaluator interprets a declarative authority-bound contract. It does not encode FSE-specific policy in Python.

## Research profiles

- meta/research/publication-closure-profile-r1.json
- meta/research/venues/fse-2027-research-r1.json

The FSE profile is dated and points to the official FSE 2027 Research Papers page and ACM acmart documentation. If venue policy changes, refresh the binding rather than changing Artifact semantics.

## Human evidence

machineStanding=PASS can still produce standing=PENDING_HUMAN.

This is intentional. Normal-zoom readability, apparent professionalism, and other perceptual properties remain Human evidence unless a later task proves a sufficiently strong and externally grounded automatic oracle.

## Paper3 dogfood

The first real workload used the final Paper3 carrier:

- PDF SHA-256: e2412d9aeb8f1fff72fd8fca925cb042efa06b8f334984fba0146f9f48c08f60;
- machine carrier evaluation: PASS;
- overall standing: PENDING_HUMAN.

Dogfood also falsified the first heading parser assumption: acmart review-mode line numbers appear in the PDF text layer and must be treated as carrier annotations rather than manuscript heading content.

## Non-goals

- no generic Research runtime;
- no universal claims ontology;
- no venue-policy copy hidden in code;
- no replacement for peer review;
- no automatic upgrade from machine layout success to Human readability;
- no reopening of scientific work solely because a carrier defect was repaired.
