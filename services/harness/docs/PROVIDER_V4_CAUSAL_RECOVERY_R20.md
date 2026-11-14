# Harness R20 — native Provider V4 causal recovery

2026-11-15 (Asia/Shanghai). Status: PRIVATE SOURCE-CANDIDATE ONLY.
Parent SourceCut: a0196e98fa5b3c5e46c2df6cdaa91f23440cdfdd.
No production installation, paid Provider request, physical Tool, or DomainSuccess.

## Consumer goal and exact existing capabilities

When an Agent loses a Provider response or process, a committed PG Provider
Head is evidence about prior Provider status, NOT a Tool execution permission.
One valid CAS object is insufficient if its previousRecordDigest was not
actually a predecessor in the exact same Harness Run.

Reuse the source-owned V4 constructors and original Python PostgresHarnessStore;
the existing Rust PG lease.acquire_run_lease / journal_write.append_events /
observe_exact_batch / read_run_readonly; and the existing Rust
pg_domain_read.inspect_pg_provider_head, provider_head.inspect_v4.
Do not invent a second Writer, scheduler, registry, inference gateway or
generic Agent runtime.

Real graph:
- L1 original caller RunContract and provider/model identity
- L5/L6 source Provider V4 claimed -> dispatching -> unknown Journal events
- L11 original PG18 CAS/Run Readback and real SELECT-only PG role
- L12 causal predecessor and failure receipt independent verification
- L9/L10 native Tool issuer/fence/effect NOT proved here
- L14 independent caller DomainSuccess NOT proved here

## First actual falsification and patch

Existing Rust Provider Head Consumer checked the current V4 record, immutable
CAS digest, event Kind/Status, exact typed edges, failure receipt and model
selection, but did not check previousRecordDigest against the causal Event
stream in the same PostgreSQL Run.

Native Python V4 construction (not a mock of Rust) created:
1. wrong_previous_record — fully valid UNKNOWN V4, but previousRecordDigest
   named a hash-shaped digest absent from that Run.
2. wrong_previous_identity — current DISPATCHING V4 pointed to an actual
   earlier CLAIMED CAS record in that Run belonging to a different ProviderCall.

RED actual PG18: job-01a1daf3-ef45-70dc-b39b-df34f5eec828, expected
negative failed under old Rust reader while original positive remained PASS.

Smallest source-native fix: for NON-CLAIMED current V4 heads, use the
already source-authenticated A read-only PG snapshot, locate its nearest
preceding Provider Event without crossing Run head clears, and require:
- its original V4 CAS digest equals previousRecordDigest;
- its own Provider status agrees with prior Event kind;
- providerCallId, turnId, turnSequence, claimGeneration, requestDigest
  and providerRequestDigest equal those in the current Head.
No new SQL query or owned Provider registry. Existing checks for current
CAS/edges/FailureReceipt and exact model identity remain mandatory.

GREEN after fix: job-01a1daf4-d342-7759-9e60-62aa9bc81cab, real PG18
Provider V4 Rust 2/2, original Python Store history readback and original
Rust no-Tool HTTP Loop 1/1 PASS; isolated PostgreSQL instance removed.
The second valid-prior-but-wrong-call negative also passed in
job-01a1daf6-2133-7760-bdd1-3d490b37649e.

## Real cross-owner continuity proof (separate from external effects)

The original Python provider fixture authors immutable V4 CAS contents.
Existing Rust PG Writer acquires one native Lease and commits
CLAIMED->DISPATCHING->UNKNOWN to actual PG18; the Writer connection
disappears, then read-only Rust observer reconciles the exact Event batch
and rejects forged replay. Python original Store reads the same history.
This tests a *synthetic unknown Provider status*. No actual network
Provider request or payment occurred; UNKNOWN never means safe retry.

The existing R18 PG18 runner was COMPOSED, not duplicated, by an
optional --provider-v4 mode. The default no-Tool test still runs.
One disposable PG18 cluster runs all source readback paths, with a
separate genuine SELECT-only database role and Writer DSN.

Installed Gateway v0.10.8 generic execution.linux -> native PG Linux Runtime
-> real disposable PG18 tests also passed with independent Gateway/Runtime
terminal exit 0, job-01a1daf6-9501-74ce-99b3-fd987a3851e4.
This is only the generic infrastructure route; installed
execution.harness remains absent.

## Source-guided CLAIMED refinements, not an overstrict false policy

The original Python run_continuity explicitly allows two different legitimate
CLAIMED successors: an expired/reclaimed same ProviderCall with larger
claimGeneration, and a new next-turn ProviderCall after prior COMPLETED.
The Reader must NOT demand unchanged callId, turnId or generation for CLAIMED
when the predecessor is source-authenticated.

R20 tested both positive cases in a fresh real PG18 database and retained
claimed/unknown/failed/completed source V4 recovery. It also falsified two
more claimed cases (original V4 constructor still produces CAS-valid objects):
- claimed_bad_previous: a first-generation CLAIMED head supplies a foreign
  previousRecordDigest even though no prior source Event exists.
  Actual RED job-01a1dafd-17bb-7256-b880-4c1040313705,
  GREEN job-01a1dafd-fb00-7149-beec-11112f3e22bd.
- claimed_missing_previous: after a completed Provider Event remains active
  in the same Run, a new CLAIMED record omits previousRecordDigest.
  Actual RED job-01a1db01-30f0-7405-b223-2fbc2e23798d,
  GREEN job-01a1db01-c4e8-7478-a0de-630fab2f765b.

The refined reader now uses ONE scan of the A-verified Event list, stopping
at the source-defined Provider-head-clear boundary. Any *present* previous
digest (including CLAIMED) must name that nearest same-Run V4 CAS.
A CLAIMED with *absent* previous digest is allowed only if no active
preceding Provider event exists before the current head. A non-CLAIMED
transition must also bind unchanged call/turn/generation/request identity.
This is a partial source-to-implementation refinement of causal admission,
not a global issuer, lease, dispatch or exactly-once physical-effect proof.

The final source helper/duplicate-scan simplification was checked against the
original real PG18 source and both positive CLAIMED variants in
job-01a1db03-65de-7083-8f2c-afb9458d63cb, native PG18 Provider V4 2/2,
source Python historical readback and original HTTP Loop 1/1 all PASS.
No real upstream model call, billing or physical Tool in these fixtures.

## LEGO and evidence limits

Thought: Event Sourcing, Design by Contract, causal provenance, capability
security, independent falsification, TDD RED->GREEN, UNKNOWN!=FALSE,
Intent!=Effect, Effect!=DomainSuccess, DELETE-CUSTOM->REUSE->COMPOSE.
Logic: L1, L5-L7, L11-L12; Tool Owner L9-L10 and domain L14 are future
consumers rather than effects of this local source change.
Ability: original Python V4 CAS source and PG Store, original Rust PG
Lease/Writer/Readback/Provider Head, genuine PG18 fixture, original Rust
HTTP Loop, installed Gateway and Runtime. Modified only consumer-side
causal check, two negative fixtures and existing PG18 test runner.

IMPORTANT: this is a SOURCE candidate, not a deployed binary. This guarded
non-Claimed latest Head is NOT a complete formal refinement of the V4 state
machine: initial/superseding Claims, cancelled/stale revisions, concurrent
writers, issuer-at-spawn, actual Provider billing, physical Tool Owner and
domain verifier still require separate independent tests. Future Quint/TLA+
models must refine to real PG CAS, relevant SQL source, Runner effects and
UNKNOWN reconciliation; a sampled model never replaces those tests.

## P0 next

A single REAL, authorized external-model Run, durable original PG Provider
Claim/Dispatch/Outcome, current issuer/fence at spawn, installed Harness
Gateway route, real native Runtime Owner effect, qualified OwnerReceipt and
independent Coding DomainSuccess with true token/cost/latency. The synthetic
V4 fixture is evidence of journal correctness only, not model/business
completion. Do not blindly resend UNKNOWN Provider calls.