# Structure R2 S1B — Composition Consumer Cutover Acceptance

Date: 2026-09-22
Status: **ACCEPTED / POST-MERGE VERIFIED**

## Scope

S1B closes only the remaining internal dependency on the historical `meta/next/scripts/cognitive_circuit_r1.py` and `meta/next/scripts/interface_contract_r2.py` facades. Repository-wide inventory after S1A found no external path callers. Remaining consumers were bounded to `meta/next` scripts/tests and already had a declared `PUBLIC_PACKAGE_DEPENDENCY` on `packages/composition`.

## Changes

- Next R3/Admission/interface consumers import `ordivon_composition` directly.
- Both historical Python compatibility facades are removed.
- Seam-specific R3 verifier implementation remains in Next.
- Composition remains generic and non-authoritative.
- Structure R2 machine state marks S1B deployed only when the facades are absent.

## Non-claims

S1B does not move Method Router, capability discovery, R3 seam ownership, Admission semantics, workflow state, permissions, domain truth, or any later Structure R2 wave.

## Candidate verification

- `composition:verify` — PASS.
- `next:verify` — PASS.
- Structure R2 checker and falsification tests — PASS.
- old facade-name grep under `meta/next` — no remaining references.
- root `repo:ci` — PASS.
- owner-boundary scan — PASS at 1,952 active files / 18 seams / 23 references.
- repository checks — 31 passed.
- integrated through serialized main helper as merge commit `cd2bbbbe1bed11519302301f8010fa9d440d6454`.
- post-merge `composition:verify`, `next:verify`, and root `repo:ci` — PASS.
- post-merge owner-boundary scan — PASS at 1,952 active files / 18 seams / 23 references.
- S1 is closed; S2-S9 remain open.
