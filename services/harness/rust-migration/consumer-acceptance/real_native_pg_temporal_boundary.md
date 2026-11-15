# R22: genuine Harness PG issuer to Gateway to native Runtime PG Runner

Status: **source-only, opt-in physical consumer test; not a production
authorization system, not merged or deployed**. This deliberately reuses the
single Harness PG Store and versioned Intent/DispatchFence, the current Gateway
MCP Owner adaptor, Runtime principal-scoped Job identity and native systemd
Runner. No new registry, scheduler, Store or global authority is implemented.

## Confirmed authentic E2E

With ORDIVON_GATEWAY_PG_E2E_REAL_HARNESS_SOURCE=1 in the existing owner
Gateway PostgreSQL test:

1. The existing production Python Harness Store writes a real RunContract,
   ToolIntent, DispatchFenceV2 and immutable CAS/Journal in one temporary PG18
   instance, with separate Harness and Runtime schemas.
2. Official Harness source first validates the exact original runtime request
   SHA and then appends precisely one source Fence reference.
3. The real Gateway MCP -> HTTP PG Runtime -> native Runner executes harmless
   printf and freezes source references into the native PostgreSQL Job.
4. The test *simulates losing the original submit reply* at Harness, persists
   UNKNOWN, queries and verifies the original Runtime Job and native terminal
   result, rejects a different successful Job in the same Workspace/principal,
   and writes a confirmed Harness Receipt with the UNKNOWN predecessor digest.
   The native PG Job has one DISPATCH_ISSUED. The domain goal was NOT assessed.

The response loss is simulated; no real network partition or process crash is
proven. Disposable clusters stop and clean up automatically. No production
PostgreSQL, Gateway, systemd unit or external Provider was modified.

## Real native issuer-currentness failure, NOT just a stub

With the additional ORDIVON_GATEWAY_PG_E2E_STALE_FENCE_FALSIFY=1:

1. A genuine Harness producer commits its Intent/Fence and checks currentness.
2. A different legitimate writer then commits a new Run revision.
3. The Harness source validator *correctly rejects* that old Fence
   independently, even with expiry checking disabled.
4. The genuine Gateway HTTP/PG Runtime/Runner with existing Runtime Owner
   credentials nevertheless accepts and PHYSICALLY EXECUTES harmless printf
   with the unchanged, now-stale ForeignReference.

Observed native Job job-01a1caf6-3d37-76f4-a1e5-423d12f549af succeeded and
printed R22_P0_STALE_HARNESS_FENCE_ADMITTED_AND_PHYSICALLY_EXECUTED_BY_METADATA_ONLY_NATIVE_OWNER.
The related other Agent temporal source test commit 551441 proved three
issuer revoke scenarios with a stub Owner; this R22 test is independent
*real native systemd Runner* evidence for the Run revision scenario.

A PostgreSQL-frozen ForeignReference is caller-declared provenance metadata,
not a current authorization certificate. PR #2116 correctly preserved the
reference without minting a new capability. This unclosed behavior therefore
requires a separate **issuer-backed Owner admission/fencing contract**, not
reverting metadata preservation or adding another static SHA test.

## R24: historic exact replay after Issuer Run revision changes

Opt-in ORDIVON_GATEWAY_PG_E2E_POST_REVOKE_REPLAY=1 extends the
**same genuine** Harness Issuer PG18 -> northbound Gateway MCP ->
Runtime PG native Runner acceptance instead of creating a second
simulation framework.

1. Harness physically executes harmless printf exactly once through the
   original Owner Job, then records UNKNOWN -> OBSERVED with its immutable
   previous Receipt digest and native execution_result.
2. The Harness Run advances to the settled Receipt's later revision, and
   a separate legal PG writer appends another Run event. The issuer's
   assert_dispatch_fence_current now raises **HarnessSuperseded** for the
   original Fence *even with expiry excluded*. The original historical
   UNKNOWN/OBSERVED Receipt chain stays immutable and independently
   readable; the original Fence's generation is intentionally not confused
   with the Run's later current revision.
3. Call execution.submit again over the **real** Agent SDK -> Gateway
   -> Runtime Owner HTTP MCP, with exact original principal,
   clientRequestId, command, environment, timeout, output byte ceilings
   and all unmodified source references. Native PG returns the **existing**
   operation ref, jobs still has exactly one row and the original Job
   still has exactly one DISPATCH_ISSUED. Frozen original physical
   execution plan and Harness Receipt digest remain unchanged.
4. Submitting the same clientRequestId with changed stdout byte
   allowance instead returns the original Owner's structured
   IDEMPOTENCY_CONFLICT, not a newly authorized Job or ambiguous success.

Real isolated native PostgreSQL18 + HTTP MCP + systemd Runner witness:
Job job-01a1cb9e-4853-7318-bc02-2fe5f9fc9566 **SUCCEEDED**.
This positive history replay **does not** mean the stale Fence is
authorized for any *new* physical execution. The immediately adjacent
test continues reproducing the still-open P0: a brand-new Job carrying a
genuinely superseded Harness Fence **is** physically admitted by the
existing metadata-only Runtime credential path.

**Therefore authority currentness and historical truth must be separate
LEGO contracts**: new-effect admission must check the relevant trusted
issuer and physical receiver at the chosen linearization cut; existing
exact RequestID/Digest replay must expose the original immutable
Owner Job/Receipt without a second physical effect. Requiring a fresh
Issuer-current Permit for every replay would erase recoverability after
legitimate revocation and turn UNKNOWN into an unsafe retry problem.
Do not conflate the two requests merely because their caller-supplied
foreignReferences look alike.

## Independent second source-to-physical-request contract gap

The exact original Harness workspace.exec Intent commits both
stdoutLimitBytes and stderrLimitBytes as 262144. The earlier Gateway
execution.submit API did not accept or forward those fields. Directly
comparing the frozen physical PG Plan proved the real pre-fix mismatch:
Harness 262144/262144 versus native Runtime 1048576/1048576.
Job job-01a1cb23-3eab-73d2-b2ae-ddb9a19ceb6c was an actual RED.

This local R22 source integration extends only the existing Gateway public
optional execution limits and Runtime Owner forwarding, and adds the same
forwarding in the existing Harness GatewayMcpRuntimeAdapter. The existing
Runtime validation bounds are retained, with no second authority or default
value. Native PG RED became GREEN in
job-01a1cb28-7bca-7414-a5d0-62182ec95ed8: the signed original command,
args, environment, timeout, stdout/stderr limits and normalized physical cwd
match the Owner PG Plan. Same-key changed output limits must conflict.

This fix is LOCAL SOURCE ONLY, not in production Gateway, not merged into
the natural Gateway Owner PR #2118. The production Gateway Owner should
selectively integrate the minimal source-only fix after normal independent
review and protected CI. It advances the SDK-discovered Gateway MCP surface
from epoch 9/version 0.10.8 to epoch 10/version 0.10.9 using the official
38-tool native SDK contract digest. The exact editable package lock self
version was updated with NO change to any third-party locked version or hash;
the native release verifier, release surface version guard and full Gateway
tests pass in an isolated, real Python 3.15.1/MCP 2.3.0 environment.
Source request digest equality *before* adapter lowering still does not by
itself prove actual Owner Plan equivalence: the test must verify source to
actual native Plan. No new Registry is needed.

## Future exact acceptance profiles

- **Admission cut:** Current issuer Run/Grant/Fence must be checked as part of
  one durable, race-free new Owner Job admission. A loose read of the Harness
  Run followed by an unrelated Runtime PG transaction still has TOCTOU.
  Consider a source-issued durable reservation/conditional admission protocol
  or target Owner fencing; reuse existing Harness PG Lease/Journal and Runtime
  Job identity rather than a new general-purpose authorization service.
- **Spawn cut:** Define whether revocation after admission but before process
  spawn prevents execution. Stronger policy requires a trustworthy token or
  issuer validation *at physical spawn*, not just an admission snapshot.
- **Ongoing cut:** Define how to handle revocation after physical start.
  Cancellation is cooperative and cannot undo external effects. Stale
  effect receivers must themselves enforce fencing when needed.
- **Idempotency:** exact principal+clientRequestId+requestDigest replay is the
  same Job; changed Fence or any enforceable physical byte conflicts. UNKNOWN
  is reconciled with the original Owner, never blindly re-dispatched.
- **Evidence:** Job committed, Runner launched, Process exited, Artifact
  delivered, Harness receipt written and Domain completed are independent
  facts. UNKNOWN must never be coerced into FALSE or SUCCESS.

The original A/C Harness owners, Runtime physical effect owner, and Gateway
owner must independently review this exact candidate before promotion.

## R25: a single wire source fact across Gateway aliases and real SDK receipts

**One source and one consumer, not a new authority.** The candidate integrates the
existing Harness Gateway receipt identity validation with the R22–R24 original
Harness PostgreSQL Intent/Fence -> Gateway MCP -> native Runtime PostgreSQL18
Job -> systemd Runner -> immutable UNKNOWN/OBSERVED receipt chain.

The additional opt-in gate
ORDIVON_GATEWAY_PG_E2E_HARNESS_ADAPTER=1 uses the actual existing Gateway
native PG acceptance test and production GatewayMcpRuntimeAdapter as a
consumer. A test-only thread-safe synchronous/async SDK bridge forwards the
already-committed, exact original workspace.exec identity to the
in-process northbound official MCP SDK client, which calls Gateway and the
real downstream HTTP Runtime service. It does not invent or create a second
physical Runtime Job. The adapter's submit, recovery resolve and terminal
observe each bind the same native Job, capability, operation reference and
source clientRequestId; native PG readback verifies DISPATCH_ISSUED remains one.

The same test also injects one **synthetic** contradictory ownerId alias
*after* the real SDK has returned an otherwise legitimate physical Owner
receipt. This is a consumer trust-boundary falsifier, not an assertion that
the real Gateway currently emits contradictory wire fields. The Harness
adapter must reject it **before** retaining either ephemeral Job identity
map; the physical Owner still has exactly one dispatch.

The root fault is source ambiguity: the existing shared _gateway_field
projection silently picked snake_case when both snake_case and camelCase
were present but contradicted each other. This affects execution.submit,
execution.resolve, execution.get and execution.cancel, not just owner_id.
It must reject incompatible **JSON types** as well as unequal values
because Python False == 0 and True == 1 are not valid JSON identity
equivalences. The entire solution is one source decoder and one use
of it for owner_id, not four duplicate validators or any extra Cache,
Registry, or State machine.

Source-only differential tests prove 18 incompatible alias payloads were
accepted before the shared fix and fail closed after; four redundant,
equal-value alias cases stay compatible. Existing production Gateway
snake_case source, canonical EventSourcedRunContinuity and Runtime contracts
remain unchanged. A complete private PG18 native acceptance plus all
Gateway/Harness tests must be rerun on the same **exact committed source
revision** before any PR promotion.

**Still unsupported**: This alias/identity work does not authenticate a
caller-minted foreignReference, validate Issuer-current authorization for a
new physical Job or establish a receiver-side Spawn fencing protocol.
The opt-in native E2E continues to retain the real stale-Fence physical
counterexample and the distinct post-revocation historical exact-replay
positive control.
