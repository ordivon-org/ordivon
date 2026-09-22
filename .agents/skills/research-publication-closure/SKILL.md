---
name: research-publication-closure
description: Advisory composition pattern for taking a scientifically frozen paper through publication-carrier QA, venue-contract validation, perceptual review, artifact rebinding, cold replay, and submission freeze without reopening science unnecessarily.
---

# Research Publication Closure

Use this Skill when a Study has a manuscript approaching submission and publication-carrier defects could differ from scientific defects.

## Authority boundary

This Skill is advisory composition knowledge. It does not own scientific truth, venue policy, artifact-format semantics, execution authority, or submission authority.

Bind the current Study authority and dated external venue/template authorities first. Use Artifact for carrier mechanics and Runtime only when exact execution evidence is useful.

## Closure model

A useful default order is:

    science freeze
    -> claim freeze
    -> manuscript semantic freeze
    -> carrier build
    -> carrier semantic lint
    -> venue contract validation
    -> perceptual review
    -> artifact/carrier rebind
    -> cold replay
    -> submission freeze

Do not use the sequence as a universal research lifecycle. It applies to the submission-closure problem.

## Carrier questions

Inspect the carrier as a system rather than as one PDF file:

- source syntax and transformation residue;
- publication metadata such as year, conference, anonymity, CCS and keywords;
- compilation and renderer identity;
- PDF structure, fonts, citations and page boundaries;
- text-layer semantics such as literal Markdown residue, duplicate captions and placeholders;
- visual presentation such as clipping and normal-zoom readability;
- exact digest binding between manuscript, PDF and reviewer artifact.

## Reviewer experience

Mechanical validity is insufficient evidence of reviewer-ready presentation. Preserve an explicit Human perceptual gate for normal-zoom figure/table readability and production-residue review.

## Failure classification

When a gate fails, classify it before changing content:

- scientific contradiction -> reopen the scientific gate that owns the claim;
- manuscript semantic defect -> repair argument/text and re-audit claims;
- carrier-only defect -> repair rendering/metadata/layout without expanding science;
- venue-contract drift -> refresh the dated external authority binding;
- artifact/carrier mismatch -> rebind and cold-replay the reviewer package.

A carrier-only repair should not trigger new experiments merely to make the paper feel more complete.
