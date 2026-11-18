# Runtime-owned Workspace consumer claim — R1

**Status:** source implementation and disposable PG18/Git qualification only.
**Not:** a deployed producer, an Artifact finalizer, or a complete Harness Tool grant.

## Hard boundary

The installed Harness and Runtime use separate PostgreSQL databases.
PostgreSQL advisory locks are scoped to a database; matching numeric keys do not
provide cross-database exclusion. The real physical Workspace owner is Runtime,
so `workspace_consumer_claims` must be in the **same qualified Runtime PG
database and schema** as Runtime Jobs and Native `workspace.close`.

Do not deploy the older Harness-local close-fence assumption (#2251) against
different databases. Do not infer that a successful Job releases a logical Run.

## Logic / capability LEGO

| Logic | Owner/capability | Core invariant |
|---|---|---|
| Workspace identity | Native OPEN/CLOSED records and Git worktree | A closed or absent worktree cannot accept a new claim |
| Physical consumer pin | Runtime PG claim + original Workspace admission lock | Any HELD claim blocks Native Close, even with `consumerReleased=true` |
| Semantic Run ownership | Harness existing PG Run state | Reserve is **not** Run READY or Tool execution permission |
| Source/outcome finalizer | Existing Git ref + Artifact + consumer acknowledgment | A local source ref does not certify ignored binary delivery |
| Pressure candidate GC | Existing PG reclaimer/systemd and OS disk readings | Pressure changes ordering, not eligibility |
| Uncertain effect reconcile | Exact `clientRequestId` + Native GET/tombstone | Ambiguous commit is UNKNOWN, never safely retried with a new identity |

## Native claim API

- `workspace.claim.reserve`: authenticating principal + `clientRequestId` +
  `workspaceId` + `runRef` + exact `expectedSourceStateDigest`.
  The Runtime-qualified writer takes its own PostgreSQL admission lock,
  confirms the OPEN identity and real physical Git state, then inserts one
  durable `held` claim. Repeated exact requests read back the original row.
- `workspace.claim.get`: read the original physical claim by the same
  authenticated principal and request key, including state and store scope.
- `workspace.claim.release`: make that owner's `held→released`
  transition under the same Runtime lock. This is an explicit consumer
  assertion, **not** proof that output was published.

The schema includes the canonical native `store_root` because Workspace IDs
are store-local. Absolute path-based scope is adequate only within the
qualified Runtime store authority where roots are unique; cross-machine
identical paths require an independently proven Runtime authority identity.

## Multi-database handoff — not yet implemented

A complete consumer path requires these additional protocol obligations
owned by the actual Harness/Gateway/Runtime editors:

1. Harness allocates a stable Run ID in a non-executable state.
2. Runtime `reserve` succeeds and is read back after uncertain responses.
3. Harness Run transitions to READY, then Runtime grants **execution-capable**
   use through an additional authenticated activation/validation protocol.
   Do **not** interpret `held` as a grant.
4. Gateway/Runtime executions validate the bound grant/Run identity on every
   relevant consumer path. A Run paused between Jobs retains its pin.
5. Harness Run termination and real Git/Artifact output disposition complete;
   owner releases the matching physical claim; NativeClose performs final
   local PG + Git/OS checks and readback.

Lost reserve/activation/release replies must converge with the original
request/claim key. Abandoned claims may only be retired on real evidence that
no executable grant was issued or a qualified Run terminal resolution occurred.
Arbitrary age expiry is not proof that an activated user has released it.

## Release requirements

- Install `sql/pg_workspace_claim_r1.sql` only in the **approved Runtime PG
  schema** as an additive migration, with independently qualified operator
  standing. Grant appropriate SELECT/INSERT/UPDATE DML to the existing
  Runtime app role; do **not** give the app role CREATE, or mutation privilege
  on protected `_stage_control`. Never apply it in Harness PG.
- Current candidate binary explicitly refuses to start if this table or
  required constraints are missing. Cutover requires staged schema +
  new qualified source hash/epoch + actual installed MCP readback.
- Before general release, review remote principal/issuer authorization of
  `reserve` and `release`, and ensure direct Gateway/trusted-local
  consumers are covered. The existing release path is not changed here.
- The source-level fixture `python3 services/runtime/tests/run_workspace_claim_pg18.py`
  creates and destroys its **own PG18 cluster**. It tests two-database lock
  independence, additive SQL migration, scoped same-name Workspaces, native
  reserve/close concurrency and postclose birth. It never touches installed
  PostgreSQL.
- The remaining GC work (no-Job/failed-Job liveness, ignored binary deliverables,
  pressure ranking, legacy retention refs) is separate. Do not weaken the
  existing dirty/source/physical checks to make a green cleanup count.
