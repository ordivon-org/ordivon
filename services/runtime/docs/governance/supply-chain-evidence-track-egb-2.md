# Supply-Chain Evidence Track (EGB-2)

Status: **CURRENT** | Date: 2026-05-05 | Phase: EGB-2
Tags: `egb-2`, `supply-chain`, `slsa-inspired`, `openssf-inspired`, `verify`
Authority: `source_of_truth` | AI Read Priority: 2

## Purpose

This track defines a local, verify-only supply-chain evidence shape for Ordivon
Verify. It may use SLSA/OpenSSF-inspired evidence language, but it must never
claim a SLSA level, OpenSSF score, certification, compliance, endorsement,
partnership, equivalence, public standard, or production readiness.

## Evidence Surfaces

- Source state
- Dependency update state
- CI/test state
- Package artifact membership
- Private-path audit
- Build/install smoke evidence
- Future provenance or attestation placeholder

## Boundary

Supply-chain evidence is not release approval. A clean package audit does not
authorize publication, deployment, merge, trading, or external action.

## Future Work

Future phases may add a read-only supply-chain evidence checker after Alpha and
public-wedge case evidence stabilizes.
