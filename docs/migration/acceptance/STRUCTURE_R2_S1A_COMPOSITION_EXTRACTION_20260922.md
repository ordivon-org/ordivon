# Structure R2 S1A — Composition Extraction Acceptance

Date: 2026-09-22
Status: **ACCEPTED CANDIDATE — requires main integration/post-merge verification**

## Scope

S1A extracts only generic task-local composition mechanics from historical `meta/next` into `packages/composition`.

Moved ownership:

- Cognitive Circuit R1 implementation;
- Interface Contract Evolution R2 implementation;
- five public JSON Schemas used by those mechanisms;
- Cognitive Circuit owner-native unit tests;
- canonical owner documentation for Cognitive Circuit R1 and Interface R2.

`packages/composition` is registered as an independent repository owner with `composition:verify`.

## Public seam

`meta/next` consumes `ordivon-composition` through a declared local Python package dependency in `meta/next/pyproject.toml`. Repository dependency policy records this as `PUBLIC_PACKAGE_DEPENDENCY`.

Historical `meta/next/scripts/cognitive_circuit_r1.py` and `meta/next/scripts/interface_contract_r2.py` remain thin compatibility facades. They contain no generic implementation authority.

## Deliberately not moved

- Method Router or method-selection semantics;
- automatic capability discovery or ranking;
- R3 Research↔Artifact or Web↔Security seam-specific verifiers;
- Admission Fabric task-local manifests/tests;
- interface dogfood/evidence tied to current consumers;
- workflow, scheduling, retry, credentials, permissions, or domain verdicts.

This prevents `packages/composition` from becoming a universal control plane or verifier.

## Verification

Candidate evidence:

- `packages/composition`: `mise run verify` — PASS.
- `meta/next`: full `mise run verify` with local `ordivon-composition` dependency — PASS.
- repository affected-owner tests — PASS.
- repository convergence tests — PASS.
- owner-boundary unit tests — PASS.
- owner-boundary scan — PASS at 1,936 active files / 18 seams / 23 references.
- full root `mise run repo:ci` — PASS.
- post-merge verification remains required before S1A becomes current main truth.

## Remaining S1B

S1B remains open. It may migrate remaining Next consumers directly to the public package API and retire compatibility facades only after consumer inventory proves they are unnecessary. Facade retirement is not required merely for directory aesthetics.
