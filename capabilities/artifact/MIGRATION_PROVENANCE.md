# Migration provenance

- historical source repository: `/root/workstation-lab`
- historical source revision: `9d83ab3e40e3cf5dc9145ede3fa269b19dd7b0da`
- initial explicit-name import: 70 tracked Artifact-owned files, byte-identical at `df1de54cbcc6cbf521fb2f665a19077ce8e707da`
- dependency-closure completion: `scripts/powerpoint_render_worker.ps1`, byte-identical at `9dd50d82eb63f916ff3b29fc93e5fad48b78409d`
- residual ownership completion: 11 OPC/OpenXML/R2 Artifact-owned files, byte-identical at `e11e714df56e24d7e8783d03ea769b88e9f32ba0`
- historical Artifact-owned source closure migrated: 82 files before new v2-only fixtures/tests
- migration date: 2026-09-12

The historical repository remains Git provenance for pre-split history. `/root/projects/ordivon-artifact-v2` is the accepted forward source authority after differential tests, stable-runtime re-materialization, and production-green Temporal workflow acceptance. See `docs/SOURCE_AUTHORITY_ACCEPTANCE_20260912.md`.
- historical Workstation Artifact source retired in `/root/workstation-lab` commit `a7f82ded74908af5bca0e956a9b38a7cbd97eecf` after zero remaining tracked technical references were observed.
- post-retirement production-green proof: Workflow `artifact-v2-source-authority-smoke-20260912-03`, Run `01a0940e-0343-75d4-9f42-1cfed2d930bd`, completed PASS with `LOCAL_UNSIGNED_DEVELOPMENT`, `releaseReady=false`, and artifact SHA-256 `2e5970e05bc8b823e9ca2f4fcaa2fa97de43b619c896c85afde92058fae0c9e9`.
