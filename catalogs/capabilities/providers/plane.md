# Provider: Plane

- Upstream: `makeplane/plane`
- Selected release target: Community `v1.4.2`
- Role: external work-management provider
- Migration mode: external provider; implementation remains outside Ordivon Core
- Local standing: selected/staged; runtime activation `HOLD_RESOURCE`

## Capabilities

Work items, work-management states/priorities/assignees, relationships, comments, cycles, modules, views/boards, pages, and REST/webhook integration.

## Boundary

Plane may be authoritative for work-management facts. It is not authoritative for domain semantic correctness, Temporal workflow state, Runtime execution, provider effects, scientific evidence or artifact validation.

## Local evidence

Official Community v1.4.2 installer:
`/root/.local/share/ordivon/plane-community-v1.4.2/setup.sh`

SHA-256:
`466b2e0d6137f72b577e10bd8af20a1f5c11268fc1294445fed7571c99d40031`

Activation is deferred until safe memory headroom is established.
