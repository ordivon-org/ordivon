# Scholarly Intelligence Profile R1

Status: **R2 THIN PROFILE ACCEPTED / POLICY CIRCUITS PENDING**

This directory implements the accepted shared Research boundary in
`docs/architecture/RESEARCH_STUDY_AUTHORITY_R1.md`.

It is not a Research runtime, scientific database, universal claims ontology, reviewer model,
workflow engine, or second copy of Study state.

## Purpose

The shared layer projects only:

- exact Study authority and revision;
- bound Standard-Native authority profile;
- opaque Study-owned references in five coordination roles:
  `requirement`, `claim`, `evidence`, `concern`, `resolution`;
- owner-native state along nine axes:
  requirements, evidence, inference, claims, argument, venue, review, publication, learning;
- explicit non-claims preventing authority laundering.

The referenced object remains owned by its Study or external authority. State strings are opaque;
this layer never normalizes them into a universal PASS/FAIL vocabulary.

## Existing owners reused

- authority identity/currentness: `meta/next/authorities`
- task-local applicability: Standard-Native profiles
- semantic provenance: W3C PROV
- operational lineage: OpenLineage
- research packaging: RO-Crate
- software/build provenance: in-toto/SLSA where applicable
- physical execution: Runtime
- continuity: Host
- routing: Gateway
- scientific truth: concrete Study authority

## R1

- `schemas/scholarly-intelligence-profile-v1.schema.json`
- `profiles/paper1-standard-native-r2-dogfood-r1.json`
- `scripts/check_scholarly_intelligence_r1.py`
- `SCHOLARLY_INTELLIGENCE_R1.md`

R1 dogfoods the already accepted 2026-09-14 Paper1 Standard-Native historical object.
R2 adds exact live projections for Paper1/Paper2/Paper3 and cross-Study pressure evidence.
Neither layer is current scientific or submission authority.

## Growth gate

Action-changing shared rules are admitted only after at least two independent Studies demonstrate
the same irreducible rule after mature external substitution. R2 has admitted only the thin profile protocol after three-Study pressure testing. ClaimPermission, concern/gap routing, experiment-admission contracts, review disagreement and longitudinal decision episodes remain separate candidates and are not executable shared policy.
