# Runtime-owned Workspace consumer claim — R1

**Status (2026-11-20 installed readback):** historical R1 physical-Claim design;
Native-first Harness Run-birth is installed separately. The ordinary raw
`workspace.claim.release` default-DENY (#2493) and claim-only code (#2502)
are included in the installed Linux Runtime SourceCut `c343558e2ee1ba7c8194b62c23fa6e68be84098c`.
An authenticated ordinary `/mcp` readback showed `workspace.claim.get` visible,
`workspace.claim.release` absent and a raw synthetic release call denied.
This confirms the **ordinary route guard only**, not a deployed dedicated
`/harness/mcp` Finalizer or complete Domain/OS release qualification.
**Not:** a certified independent Domain Finalizer or permission to remove an
original PAUSED/ACTIVE Run's Workspace.

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
- `workspace.claim.release`: make that original authenticated owner's
  `held→released` transition under the same Runtime lock. This is an explicit
  consumer assertion, **not** proof of Run completion, recipient delivery or
  OS effect drain. In the merged SOURCE (#2493), ordinary `/mcp` **always**
  denies this operation at the raw `tools/call` handler and omits it from
  `tools/list`, **even without** a configured dedicated Harness profile.
  A separately authenticated `/harness/mcp` token file and principal can
  enable **Claim-only** release (#2502), which does **not** require a
  Harness Job issuer schema or a copied Harness PostgreSQL database.
  Configuring the optional issuer schema activates the distinct existing
  same-PG Job Issuer contract. These are separate capabilities.
  The earlier PID 1854/source-only observation is superseded: a qualified
  Runtime ReleaseEffect deployed SourceCut `c343558e...` on 2026-11-20;
  the installed service readback reported PID 2604301 and Runner digest
  `sha256:88d2625db83c3f61865fa55d252b5d9bb3cc748c6072dd44da62e013972439b9`.
  Ordinary release is now denied in the installed native MCP route, but a
  dedicated caller with release credentials can still release prematurely
  without independently authenticated full-output and NoFutureSpawn evidence.

The schema includes the canonical native `store_root` because Workspace IDs
are store-local. Absolute path-based scope is adequate only within the
qualified Runtime store authority where roots are unique; cross-machine
identical paths require an independently proven Runtime authority identity.

## Multi-database handoff — partial Native-first installation

Harness R27 has an installed native-first Run-birth consumer: reserve a real
Runtime PG Claim, then create the original Harness PG Run. This protects new
Runs against ordinary close while the Claim stays HELD; it does **not** protect
historical unclaimed PAUSED Runs. Ordinary raw release is denied by the
installed 2026-11-20 Runtime, but privileged Finalizer/domain acceptance
and all-issued OS Manager handoff drainage remain unqualified. The following list is
the **target complete consumer contract**, not a claim
that all five stages are already installed and accepted:

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
- Before any source→Installed cutover, independently qualify the original
  Claim's `(principal,clientRequestId)` owner; an older HELD Claim cannot be
  recovered by swapping to a new bearer/principal. Keep old/unknown consumers
  HELD rather than rewriting a physical pin based on elapsed time.
- A dedicated `/harness/mcp` bearer and principal provide a Claim-only
  route from #2502 when independently configured and authenticated.
  The installed ordinary route now denies raw release; neither change certifies a `COMPLETED`
  Harness Run, original recipient byte ACK, or all issued OS effects drained.
  A historical claim held by the old ordinary principal is **not** silently
  transferable to the new principal; do not restore general release just
  to clear old rows. A qualified original consumer/explicit abandon must
  resolve its real ownership and retained output first. Installed native `trusted_local` jobs currently execute
  with root authority: another root-owned `0600` bearer file is not a
  security boundary against those already authorized root Jobs.
  Qualify the ordinary-execution OS identity, original Trust/Finalizer role,
  caller/recipient byte ACK and native close before enabling automatic GC.
  See [Runtime LEGO consumer boundary](guides/runtime-legos.md).
- The source-level fixture `python3 services/runtime/tests/run_workspace_claim_pg18.py`
  creates and destroys its **own PG18 cluster**. It tests two-database lock
  independence, additive SQL migration, scoped same-name Workspaces, native
  reserve/close concurrency and postclose birth. It never touches installed
  PostgreSQL.
- The remaining GC work (no-Job/failed-Job liveness, ignored binary deliverables,
  pressure ranking, legacy retention refs) is separate. Do not weaken the
  existing dirty/source/physical checks to make a green cleanup count.
