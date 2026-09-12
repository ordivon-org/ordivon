# Artifact v2 independent source-authority acceptance — 2026-09-12

## Standing

**ACCEPTED AS FORWARD SOURCE AUTHORITY.**

`/root/projects/ordivon-artifact-v2` is the forward source authority for Artifact Build & Delivery. The historical `/root/workstation-lab` repository remains Git provenance for pre-split history but is no longer a valid runtime or deployment source.

This standing does not claim that every formal release profile is locally satisfiable. Formal target-render, visual, accessibility, companion, delivery-readback and cryptographic-trust gates remain fail-closed and retain their own evidence requirements.

## Differential source acceptance

The migration began from `/root/workstation-lab` revision `9d83ab3e40e3cf5dc9145ede3fa269b19dd7b0da`.

- 70 explicitly named Artifact-owned tracked files were imported byte-for-byte in `df1de54cbcc6cbf521fb2f665a19077ce8e707da`.
- `scripts/powerpoint_render_worker.ps1` was discovered by dependency-closure testing and imported byte-for-byte in `9dd50d82eb63f916ff3b29fc93e5fad48b78409d`.
- 11 residual Artifact-owned OPC/OpenXML/R2 files, independently classified by Workstation v2 retirement policy as `MOVE_OTHER_E2E`, were imported byte-for-byte in `e11e714df56e24d7e8783d03ea769b88e9f32ba0`.
- Only source-authority path fences were changed after byte-preserving import.

Old/new execution of `presentation-native-smoke-request-r1.json` produced the same PPTX bytes:

`sha256:2e5970e05bc8b823e9ca2f4fcaa2fa97de43b619c896c85afde92058fae0c9e9`

Both copies passed the selected Open XML SDK 3.5.1 structural validator.

## Development-only durable workflow acceptance

A checked-in development-only acceptance fixture was added rather than weakening a formal release profile:

- profile: `presentation-local-development-r1.json`;
- source: `presentation-local-development-source-r1.json`;
- request: `presentation-local-development-request-r1.json`.

Only `profileSchema`, `structural`, and `semantic` gates are required. It has no release companion, no required target renderer, and its only delivery target is `local-development-only`.

Direct build/verify/package acceptance passed with:

- `profileVerificationComplete=true`;
- `trustStanding=LOCAL_UNSIGNED_DEVELOPMENT`;
- `releaseReady=false`;
- three local unsigned VSAs;
- exact PPTX digest equal to the original native smoke build.

Production-green Temporal workflow acceptance then completed on `127.0.0.1:17233`:

- Workflow ID: `artifact-v2-source-authority-smoke-20260912-02`;
- Run ID: `01a09407-cfec-7f42-98ec-85f18fb8814e`;
- status: `COMPLETED`;
- task queue: `ordivon-artifact-delivery`;
- prepare/build/verify/package receipts: present;
- package standing: `LOCAL_UNSIGNED_DEVELOPMENT`;
- `releaseReady=false`;
- artifact SHA-256: `2e5970e05bc8b823e9ca2f4fcaa2fa97de43b619c896c85afde92058fae0c9e9`.

The preceding workflow `artifact-v2-source-authority-smoke-20260912-01` intentionally used the formal PDU/SDU release profile and failed at package assembly because required target/visual/delivery gates were absent. That failure is retained as positive fail-closed evidence; no formal release profile was weakened to make migration pass.

## Live runtime authority

The active systemd worker is sourced from this repository:

- unit: `ordivon-artifact-temporal-worker.service`;
- `WorkingDirectory=/root/projects/ordivon-artifact-v2`;
- Temporal address: `127.0.0.1:17233`;
- task queue: `ordivon-artifact-delivery`;
- observed restarts at acceptance: `0`.

The stable Artifact Python runtime was re-materialized from this repository and retained generation:

`63a6762fa5672df4828e924d8279c56de6a0b6ea2ba01907c235ee725ab4bb39`

The stable OpenXML method runtime was re-materialized from this repository as generation:

`573eb82efffdeeee034ff5ae1cc354340b1f7ef1a50fa16e89154cb9971b2c6a`

Its frozen external-evidence corpus remained:

- standing: `PASS_BOUNDED_EXTERNAL_EVIDENCE`;
- IV&V standing: `NOT_CLAIMED`;
- method promotion: `GRADUATED_BOUNDED_STRUCTURAL_GATE`;
- corpus result digest: `sha256:3a0b9739903e4279e25528f3c5a52a4a7d0708ae2803436ffec57b684298b778`.

## Regression acceptance

After runtime re-materialization:

- all `tests/test_artifact*.py`: **132 PASS/8 skipped**;
- `tests.test_temporal_artifact_delivery_contract`: **11 PASS**;
- Temporal production-green cluster: `SERVING`;
- Artifact worker: `active`, `NRestarts=0`.

## Next boundary

Artifact Build & Delivery ends at a verified/package-ready Artifact fact. External publication/provider effects belong to the Integration/Distribution boundary. A future n8n handoff must consume an Artifact result contract; n8n workflow IDs or provider-specific identifiers must not become Artifact domain authority.
