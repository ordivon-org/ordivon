# Distribution Monorepo Import Acceptance — 2026-09-21

Standing: **ACCEPTED_SOURCE_ONLY**

Scope: identity-preserving source/history import of Distribution into `capabilities/distribution`. No production cutover or external-effect authorization is performed by this record.

## Import identity

- Source repository: `/root/projects/ordivon-distribution-v2`
- Frozen source revision: `00d919f3f54c636704f6401e407dcff12a685600`
- Frozen source ref: `refs/heads/migration/optional-effect-current-20260921`
- Frozen bundle: `/root/ordivon-migration-backups/2026-09-21-distribution-current/distribution.bundle`
- Bundle SHA-256: `7f225cdad1086f0301fd2d369113fcea105a705d64a65f75b5000370daac553b`
- Import merge: `0403bb8152d23c1506a573474338280179de4e00`
- Target path: `capabilities/distribution`

The frozen source revision remains reachable in the monorepo DAG and the imported subtree is tree-identical to the frozen source tree.

## Canonical-path deterministic acceptance

Acceptance ran from the actual monorepo owner path `capabilities/distribution/`.

- owner prefix: PASS
- Python: 3.14.7
- `uv lock --check`: PASS
- `uv sync --locked`: PASS
- Ruff: PASS
- compileall: PASS
- deterministic repository reference suite: PASS
- shell syntax: PASS
- ShellCheck: PASS
- retired Temporal/preflight surface absence: PASS
- CI repository-contract wiring: PASS
- external-carrier gate separation: PASS
- source/subtree tree identity: PASS
- `git diff --check`: PASS
- final gate: `overall=0`

## External carrier boundary

The external carrier suite remains optional and separately observable. Prior observations retained in the source acceptance record include GitHub readback PASS, rclone PASS, Postiz HTTP 401 observation PASS, and OpenAPI Generator UNAVAILABLE because Docker Hub registry access timed out.

Those observations neither widen nor reduce Distribution's source authority.

## Boundary

`ACCEPTED_SOURCE_ONLY` does not mean that live providers, credentials, effect authority, deployment, or production consumers have been switched to the monorepo.
