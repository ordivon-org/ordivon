# Distribution Optional-Effect Source Acceptance — 2026-09-21

Standing: **ACCEPTED_SOURCE_ONLY**

Scope: `capabilities/distribution` candidate source. No production cutover is authorized by this record.

## Accepted source

- Base source revision: `d579eb56d0ee26289159d3addfa8130d5b07ce60`
- Meta-system downgrade revision: `3f206409989e9274c1645ec25416df61b1662bff`
- Final source revision: `00d919f3f54c636704f6401e407dcff12a685600`
- Frozen source ref: `refs/heads/migration/optional-effect-current-20260921`
- Bundle: `/root/ordivon-migration-backups/2026-09-21-distribution-current/distribution.bundle`
- Bundle SHA-256: `7f225cdad1086f0301fd2d369113fcea105a705d64a65f75b5000370daac553b`

## Architecture result

Distribution is no longer treated as a mandatory cross-provider control plane. The forward source retires:

- Distribution-owned Temporal dispatch smoke;
- Distribution-owned Steam/local preflight implementation, schema, tests and profile.

It retains bounded reference/profile semantics for exact occurrence/payload binding, explicit effect-authority translation where native provider authority is insufficient, provider-observation binding, admission examples and reconciliation examples.

## Gate separation

Repository/source correctness and optional external carrier availability are distinct:

- `bash scripts/test-all.sh` is the deterministic repository contract used by CI;
- `bash scripts/test-external-carriers.sh` is an on-demand provider/tool observation suite;
- retired executable paths are rejected by the structure test if they remain wired into CI or forward scripts.

The deterministic acceptance completed with Python 3.14.7, uv lock/sync, Ruff, compileall, repository reference suite, shell syntax, ShellCheck, retired-surface absence, CI contract and `git diff --check` all passing.

## External carrier observations

Before gate separation, the same candidate observed:

- GitHub provider-native readback: PASS;
- rclone local copy/check: PASS;
- Postiz unauthenticated surface: PASS with HTTP 401;
- OpenAPI Generator container smoke: **UNAVAILABLE** because Docker Hub registry access timed out while pulling `openapitools/openapi-generator-cli:v7.24.0`.

The OpenAPI result is an external availability observation, not a source correctness failure. It does not claim the carrier itself is verified.

## Boundary

`ACCEPTED_SOURCE_ONLY` does not imply deployment, provider authorization, external effect authority, domain acceptance, or old-repository retirement.
