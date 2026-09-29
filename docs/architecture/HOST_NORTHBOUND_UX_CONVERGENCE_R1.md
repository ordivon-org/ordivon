# Host Northbound UX Convergence R1

## Decision

Keep Host as the headless semantic-continuity authority. Improve Agent UX in read projections and Gateway/Harness vocabulary without adding Host-owned priority, assignment, scheduler, unread/consumption state, execution authority, Runtime/Git currentness, or domain truth.

## LEGO decomposition

| LEGO | Owner | R1 action | Standing |
| --- | --- | --- | --- |
| HUX-0 Host continuity kernel | Host + PostgreSQL | unchanged | frozen |
| HUX-1 public/default ingress | Gateway | direct Host remains operator/admin/recovery only | existing architecture retained |
| HUX-2 continuity discovery | Host projection + Gateway | add mechanical timestamps, `sortKey`, `runtimeWorkspaceId` forwarding, preferred `continuity.find` | implemented |
| HUX-3 change navigation | Host projection + Gateway | retain `attention.delta` internally; add preferred `continuity.changes`; keep `continuity.attention` alias | implemented |
| HUX-4 collaboration scope | Gateway over Host Board | add `collaboration.publish` requiring explicit `global`/`continuity` scope; keep `collaboration.post` compatibility | implemented |
| HUX-5 Harness observation UX | Harness | admit `continuity.find` and `continuity.changes` as observation-only Tools | implemented bounded slice |
| HUX-6 DB call-path optimization | Host substrate | measure before changing connection lifecycle or batching | measurement gate only |

## Contract rules

1. Legacy `task.list` / `continuity.list` keep creation-order behavior so existing cursors remain valid.
2. `continuity.find` defaults to `updated` order and may filter by `goalId` and/or `runtimeWorkspaceId`.
3. Host returns `created_at` and `updated_at` as mechanical projection facts. They are not importance or stale-work verdicts.
4. Updated-order cursors bind `sortKey=updated` into the cursor scope. A cursor cannot be replayed under another ordering.
5. `continuity.changes` is a northbound vocabulary change only; Host remains sequence-based and non-authoritative for priority/consumption.
6. `collaboration.publish(scope=global)` is intentionally explicit. `scope=continuity` requires one exact continuity ID and lowers to Host `board.post(taskId=...)`.
7. A global scoped preferred publish cannot reply to an existing message because Host reply inheritance could silently change the effective scope. The compatibility `collaboration.post` remains available for callers that deliberately need raw Board semantics.
8. Effectful collaboration publication is not admitted into Harness H1 observation-only composition.

## Verification

- Gateway full suite: 65/65 PASS.
- Harness HUX-targeted composition suite: 7/7 PASS.
- Host isolated local PostgreSQL cluster: Alembic 0001 -> 0005 PASS; Host suite 40/40 PASS.
- Host history Doctor after tests: all checks healthy.
- Ruff: Host, Gateway and changed Harness surfaces PASS.
- Harness full-suite probe with the explicit repository import root executed without failures through >85% of the suite, then hit the bounded 120 s Runtime execution deadline; changed-surface tests are complete at 7/7 PASS.

## Deferred gates

- Host DB connection benchmark (isolated PostgreSQL, N=200 trivial queries): direct mean 3.987 ms / p95 4.782 ms; pool mean 0.959 ms / p95 1.259 ms; mean ratio 4.16x. The absolute saving is ~3 ms/call, so pooling remains deferred until end-to-end Host-call latency shows it is material.
- Measure `attention.delta` N+1 query cost before replacing it with batch joins.
- Do not create Host unread/consumed state merely to hide a sequence cursor.
- Public connector removal of direct Host MCP is a deployment/client-catalog cutover, not a Host kernel source change.

## Current-main integration evidence

The original implementation workspace was frozen as commit ef61a3bc73a22bc1a03da1c45125711189e672f2. It was then cleanly cherry-picked onto current monorepo revision f2ec4ec0c77fcf6b29fedd33c9145cea653cf730 in ws-host-ux-integration-r1-20260923, producing pre-evidence-refresh candidate 1928db8ffe1af5191f8b3bfceefafaaea9708e95.

The repository convergence planner classifies the change as SCOPED, with direct owners Host, Harness and Gateway and conservative verification closure Composition, Gateway, Harness, Host, Next, Security, Skills and Web.

Current-main evidence:

- Host/Gateway/HUX-targeted checks: PASS.
- isolated PostgreSQL vertical: Alembic 0001 -> 0005 PASS and Host 40/40 PASS.
- repository CI: PASS.
- Composition, Gateway, Host, Next, Skills and Web owner gates: PASS.
- Harness full owner gate: 1055 tests plus 121 subtests PASS.
- Security owner local checks: 62 tests PASS, then the gate is blocked while fetching the pinned OPA Docker image through the configured external proxy. This is retained as an external verification-substrate blocker, not reclassified as a Host UX regression.

Historical candidate standing at that stage: all required repository convergence-owner gates were green, but that candidate had not yet been merged or deployed. Later sections supersede this deployment standing while preserving the qualification evidence.

### Security verification substrate resolution

The initial Security owner failure was not a policy/test failure. Docker was configured through a stale systemd proxy endpoint at 10.254.177.2:19381, while the current workstation CONNECT sidecar at 127.0.0.1:19081 could reach Docker Registry and Docker Auth. The pinned OPA raw manifest was independently fetched and its SHA-256 matched the locked digest exactly. A temporary local TCP bridge allowed the existing Docker daemon to pull and cache that exact RepoDigest without a daemon restart. Because Runtime workspaces are mode-isolated (700/600) and the pinned OPA image runs as UID 1000:1000, policy read bits were temporarily widened only for the owner verification and restored immediately afterward. The canonical Security owner task then passed unchanged.

## Latest-main qualification — 2026-09-23

HUX was replayed without conflicts onto canonical main `9cab0e9c968dacdb2e7a22462a6a5d98193b0940`, producing source candidate `608b773a50543f6eef59e4858e72a5c1fb749a9f`. The current repository convergence planner classified the change as `SCOPED`, with direct owners Host, Harness and Gateway and verification owners Agent App, Composition, Gateway, Harness, Host, Next, Security, Skills and Web.

Latest qualification evidence for that exact candidate tree:

- repository CI: PASS.
- Agent App owner: PASS.
- Composition owner: PASS.
- Gateway owner: PASS.
- Harness owner: 1065 tests plus 121 subtests PASS.
- Host owner: 21 passed plus 19 integration tests skipped in the owner-local run; a separate isolated PostgreSQL 18.6 UTF8 vertical ran Alembic `0001 -> 0005` and the complete Host suite 40/40 PASS.
- Next owner: PASS.
- Security owner: 62 Python tests PASS plus OPA policy 34/34 PASS using the exact pinned image; Runtime workspace policy permissions were widened only for the non-root OPA read and restored to directory `0700` / files `0600` immediately afterward.
- Skills owner: 81 tests plus 40 subtests PASS.
- Web owner: PASS.

While qualification was running, canonical main advanced from `9cab0e9c...` to `66bdd46b457bca6a9e37e61c9540e1242117f425`. The intervening commits were Research-only and changed none of the 18 HUX paths. The complete HUX patch still passes `git apply --check` against `66bdd46b...`, and repository CI on `66bdd46b...` passes. Integration uses the repository's locked `integrate-main.sh` path with `EXPECTED_MAIN` bound to the exact main revision from the final incremental drift audit. That fence is an operational value, not a durable architecture constant: any further main movement must fail closed and be incrementally requalified rather than silently accepted.

### Incremental merged-tree requalification through `ce764f12...`

The mainline delta from `66bdd46b...` through `ce764f12...` introduced Agent App / Composition / Harness-facing changes without touching any HUX-owned path. The actual merged tree (`ce764f12...` plus HUX) was nevertheless requalified using the repository planner's queue closure. Agent App, Composition, Harness queue, Next, Security, Skills and Web all pass. Harness reports 1065 tests plus 121 subtests PASS. Security reports 62 Python tests plus OPA 34/34 PASS, and the temporary Runtime-workspace policy read permissions were independently confirmed restored to directory `0700` and files `0600`.

Historical pre-integration standing: incremental merged-tree requalification PASS. Final integration subsequently completed through the repository integration lock; the qualification remains evidence for the admitted source tree rather than a claim that integration is still pending.


## Production integration and live closeout — 2026-09-23

HUX is now part of canonical main through integration commit `aea965f212d7dda6b0ab25abec2a9104542f0089`. A later source revision `4b092fa709acb6aca3a43c8f74a09fc3427102ff` was rechecked with no Host/Gateway HUX-path drift and used for the Host production release.

Live server standing:

- stable Gateway runs immutable release `eaa045252ef7fc61d65325aa9dfbb2d40d8f4054` and contains `continuity.find`, `continuity.changes`, `collaboration.publish`, `runtimeWorkspaceId` forwarding, and `sortKey`;
- production Host was atomically cut over from `140f33cc3b2d992c68b05179daae4e9b44e8443e` to immutable release `4b092fa709acb6aca3a43c8f74a09fc3427102ff`;
- isolated canary and production wire acceptance both prove real `created` versus `updated` ordering, non-null `created_at` / `updated_at`, updated-order cursor binding, and cross-sort cursor rejection;
- Host Doctor remains healthy on PostgreSQL journal schema 5 after cutover; no schema migration was required;
- Gateway-to-live-Host E2E acceptance proves `continuity.find` no longer suffers the earlier mixed-version false projection;
- `continuity.changes` passed against the live collaboration sequence projection;
- `collaboration.publish(scope=continuity)` committed Board sequence `17811` for `task:host-northbound-ux-convergence-r1-20260923`.

Consumer standing remains separate from server standing. The ChatGPT connector snapshot observed during closeout still advertises the older Gateway Tool catalog, so `continuity.find`, `continuity.changes`, and `collaboration.publish` require client/connector catalog refresh before normal consumer acceptance. This stale consumer snapshot does not redefine the live server Tool surface, and direct Host remains operator/admin/recovery-only until refreshed Gateway consumer acceptance is proven.

Current standing: **SOURCE_MERGED / GATEWAY_DEPLOYED / HOST_DEPLOYED / SERVER_E2E_ACCEPTED / CONSUMER_CATALOG_REFRESH_PENDING**.
