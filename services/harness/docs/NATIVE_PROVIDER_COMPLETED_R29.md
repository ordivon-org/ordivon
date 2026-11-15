# Harness R29 — Native source-equivalent Provider COMPLETED

2026-11-15. **Private local source candidate. Not installed production service.**

## Narrow contribution and hard kernel

NativeAgentLoop already had an external HTTP positive wire observation (R27) and
PG-native V4 UNKNOWN (R25), but lacked any source-equivalent *positive* result
CAS and V4 COMPLETED journal path. R29 closes that original PG contract seam.

New `agent_turn_result.rs` authors a strict no-Tool `AgentTurnResult` candidate
with original Python-compatible JSON, `finishReason=stop`, actual decoded
response-body SHA, model identity and **optional** reported token Usage. It rejects
missing witness, unqualified finish, non-completion decisions, and silent
effective-model fallback. Token Usage missing means `usage={}`, not fabricated
0 or billing success. A valid candidate is **not AgentSolved**.

The **existing** Rust PG CAS writer now accepts typed `AgentTurnResult` kind;
same original `store_cas`, lease and `append_events`, with zero additional
PG Writer/SQLite/proxy.

## Independent physical consumer

Original Python Store creates a second source-bound PG Run/State/Source plus
a pure Python `AgentTurnResult` and V4 Claimed/Dispatching/Completed **oracle**;
it does not persist the positive Result or any of its V4 records. Native Rust
makes the exact source-equivalent CAS objects at the correct transitions,
using the existing `DurableJournal` source test adapter.

An actual localhost HTTP server first independently SELECT-verifies PG revision
3 and DISPATCHING, verifies **actual transmitted JSON bytes** match the
source ProviderRequest digest, and returns a complete JSON HTTP 200 with
source-expected text, model and test token Usage. The actual NativeAgentLoop
constructs result and V4 COMPLETED, commits revision 4 with original PG Lease,
and yields `CompletionProposal`. SELECT-only Rust verifies full CAS/event
chain; original Python Store reads and parses the committed Result. The Run
itself remains **active**, not `run-completed`, because completion is a domain
verdict owned by an independent verifier.

Original UNKNOWN/ambiguous-lost-response real PG18 scenarios remain exercised.
The scratch PG18 instance is stopped and removed.

## Status and remaining first-quadrant blockers

R29 makes the positive **business-interface seam** real in an original PG
scratch consumer, but test Journal/clock and loopback Provider remain
nonproduction. Production Journal must bind the live current Run/Provider
authorization, source privacy retention, caller budget, effective model
selection and Security-materialized secret at real send time. Genuine
zero-priced API calls remain pending an approved credentials path (a prior
attempt was blocked by security inspection, never bypassed). Need true
paid/free price/usage settlement, installed Gateway `execution.harness`,
Tool OwnerGrant/Fence at physical spawn, and independently solved coding task.

Thought LEGO: Representation-first, original source Oracle, causal state
machines, immutable CAS, fail-closed model/usage policy, UNKNOWN != FALSE.
Logical LEGO: L2 PG state, L4 NativeLoop, L5 Provider, L8 recovery,
L9 usage, L10 candidate vs DomainSuccess.
Ability LEGO: `agent_turn_result.rs`, `provider_v4_author.rs`,
`provider_cas.rs`, original `journal_write.rs`/`lease.rs`,
original Python `model.AgentTurnResult`, PG18 read-only consumer.

## R30 source-privacy falsification (same document, no R30 documentation layer)

The Rust positive Journal re-reads the same live Run's source PG Contract at
revision 3 and extracts the canonical allowModelContent boolean; no caller
retention hint can override the authoritative privacy bit. A source/passed
flag mismatch aborts before saving any Provider result CAS. The independent
Python source Contract selects allowModelContent=false for the negative case. A second
real localhost HTTP-positive Run receives the same exact response and token
Usage, produces the true Python-equivalent native AgentTurnResult in memory,
but the **same** PG Writer must persist ONLY a Provider V4 COMPLETED record
whose resultDigest names the qualified result. resultObjectDigest is **null**;
the original PG18 objects table contains NO AgentTurnResult object for the
redacted result. A SELECT-only Rust reader verifies the no-CAS condition and
Provider completed head; the original Python Store independently validates
the Run's causal history and no leakage. The permitted-content counterpart
still stores the full result, and UNKNOWN still does not blind retry.

R30 is a source-policy production *capability seam* in the test-only Journal
rather than a newly deployed Security owner. Real Provider credentials, live
currentness, external cost and independently solved Agent tasks stay OPEN.

## R31 atomic CAS+Event hard-core fix (same document)

R30's two independent PostgreSQL transactions (put immutable Result/V4 CAS,
then append a lease-fenced COMPLETED Event) could leave a private, unreferenced
answer object after Event revision failure, even while the Provider record
correctly refused to claim success. R31 composes, rather than replaces, the
mature original PG Journal Writer: `append_events_with_provider_cas` stages
source-referenced typed Result/V4 CAS and the Event+edges+Run projection in
ONE existing PG transaction. `append_events` retains its original interface
by calling this with zero staged objects. CAS preparation and strict kind/
version rules are shared with the existing `put_provider_cas` instead of
duplicating canonical validators. New staged objects MUST appear in the
actual Event references. The original Run row lock, semantic Contract
validation, replay, revision, lease, atomic projection update and rollback
remain the only authority.

Real disposable PG18 independently falsifies the old leak on both permitted
and redacted source Runs: an actually source-valid new model Result is staged
then a stale expected Run revision is submitted with a currently held lease.
The Event transaction rejects revision 3 after actual Run advanced to 4,
and a *separate SELECT-only connection* observes zero object rows for the
new private result digest; existing Run revision 4 remains unchanged. Both
ordinary COMPLETED cases still pass exact original Python Store / Rust reader
parity; physical server sends real localhost HTTP, not a live external API.
This closes the transactional orphan-CAS hole, **not** the issuer-at-spawn
authorization, current model billing or external AgentSolved proof.

## R32 original source Provider dispatch budget under locked PG Run

The mature Python RunBudget/Agent Loop limits maxModelCalls and safe
maxModelRetries, but native PG Writer previously did not constrain physical
Provider DISPATCHING edges if another caller bypassed that cognitive Loop.
R32 reuses the SAME original locked Run PG transaction and the already
validated source Contract to count previously durable DISPATCHING events,
add new ones in the proposed batch, and refuse admissions above
maxModelCalls + maxModelRetries. It first reconciles exact Event replay,
preserving already-committed historical receipt semantics without creating
a second physical effect. A modern v2 source missing these limits fails closed
for physical dispatch; historical v1 lacks modern budgets and retains its
previous source-compatible behavior.

Original Python creates a source PG18 Run constrained to maxModelCalls=1 and
maxModelRetries=0. The first native Rust model call makes a real localhost
HTTP POST and records DISPATCHING/COMPLETED. The second source-valid PG
dispatch candidate is rejected in the same original Writer despite a
currently valid Run lease, and an independent SELECT-only consumer proves
no new Event/Run revision. Replaying the original completed event still
returns Existing. This is a conservative upper bound on total dispatched
physical attempts, NOT monetary budget, observed Token billing nor
permission to redirect model, issue Tool effects or retry UNKNOWN.

## R33 source privacy authority moved into original native PG Writer

R30's source-driven retention lived in the test Provider Journal rather than
the shared PG Writer. R33 makes the same authoritative policy an invariant
of the original locked Run transaction: validated immutable Contract
privacy.allowModelContent=false refuses any staged AgentTurnResult or Event
reference / direct resultObjectDigest to a full model result. Because staged
CAS inserts and Event admissions share the same PG transaction, this check
cannot leak a Result CAS when an untrusted adapter proposes a validly shaped
but privacy-forbidden positive result. Historical exact Event replay reconciles
before new admission so no new side effect is fabricated.

The former standalone put_provider_cas(AgentTurnResult) API is rejected
unconditionally: it has no Run identity, Contract, or atomic Event, and so
cannot establish content-retention authority. Existing standalone RecordV4
and FailureReceipt paths retain source parity.

Real original PG18 redacted Run negative with current valid rev4 lease,
forged model-result Event, and staged private CAS returns source privacy
Invalid; independent SELECT-only SQL verifies zero CAS and zero Event,
same revision. A direct standalone AgentTurnResult put also rejects before
any PG write. The retained-content positive Run and original UNKNOWN
readback remain valid. Test-only consumer and PG hard gate are distinct;
this is not a production-installed live model executor.

## R34 one V4 representation kernel, PG Writer and Loop shared

Critical consumer graph debt: original strict Provider V4 parser
(provider_head.rs) lived inside harness-loop while the original PG Writer
accepted a generic 'provider-call-completed' Event if CAS existed and the
Run lease/revision matched. A caller could relabel a DISPATCHING Event
as COMPLETED, or claim completion with no bound Provider record.

R34 MOVED the source parser, status type, natural recovery posture, numeric
unbounded sequence handling and exact field validation into
`harness-core/src/provider_head.rs`. Loop retains a thin re-export with
no separate duplicate validator; shared identity text validator likewise
now lives in harness-core. The original PG Writer consumes this exact
parser under its already-locked source Run transaction for new V4 completed
events: Event must bind exactly one original Provider record reference;
record CAS must match digest, Run, source adapter/requested model, status,
recorded time, result object edge and an actually durable predecessor
DISPATCHING Event. Legacy source v3 record fields remain admitted with
their original existing semantics; this is not permission for new v4
completions to lack causal evidence.

True disposable PG18 adversarial tests relabel the source DISPATCHING
record to COMPLETED and separately remove the Provider record edge while
holding the current valid Run lease. Both are rejected by the original
PG writer; independent SELECT-only read confirms no forged Event and
Run revision remains unchanged. Normal positive retained/redacted Results,
budget, privacy, original UNKNOWN and Python Store history all remain
accepted. This does NOT prove real Provider send authority at physical
network dispatch nor independent AgentSolved.

## R35 same-attempt causal predecessor as one shared formalizable kernel

R34 proved that a fake COMPLETED label is invalid but checking *any*
historical DISPATCHING reference was still insufficient: a well-formed
new V4 result could reuse an older dispatch after that call had completed,
or point to a different ProviderCallId under the same Run.

R35 factors the immutable non-CLAIMED six-field attempt identity predicate
into harness-core::provider_head::ProviderRecordHead::same_attempt_identity,
reused in the original read-only PG Provider recovery and source PG Writer.
The source current Provider head-clearing predicate is likewise centralized
in the same core. Inside the existing locked PG18 transaction, a new V4
COMPLETED must point to the most recent source-defined Provider predecessor
since the last clearing Event, which must be DISPATCHING, have the exact
previousRecordDigest and the same ProviderCallId, turn, sequence,
claimGeneration, requestDigest and ProviderRequestDigest. A replay of a
previously committed Event still reconciles as Existing without a new send.

Independent PG18 falsification includes:
(1) in rev3 DISPATCHING before valid completion, a *validly authored*
V4 COMPLETED with a different ProviderCallId, same predecessor and
source-real HTTP model response: rejected and no forged CAS;
(2) after the legitimate COMPLETED rev4, an otherwise valid new V4
COMPLETED referencing its old DISPATCHING: rejected, no CAS/Event.
Source-allowed and privacy-redacted retained histories still converge
to original Python Store's exact V4 and AgentTurnResult bytes. The
Journal, SQL and native test servers remain isolated; this is NOT proof
of real model payment, tool grant at physical spawn, or AgentSolved.


## R36 current Provider admission and failure-state causality (P0)

The original PG18 Writer's R35 V4 COMPLETED check was not sufficient
to protect the earlier Provider transitions. A current Run lease plus a
well-formed Event allowed a forged *different Adapter* DISPATCHING record
to be committed. This is an actual RED, not a theoretical replay concern:
real scratch PG18 original Writer admitted it as `Ok(Created)`; source
test Job `job-01a1de23-5202-7366-aeb7-c19ab5c99bfe`.

Reused the existing locked original PG Writer, original Run Contract,
Core `inspect_v4` typed V4 record parser, shared
`ProviderRecordHead::same_attempt_identity`, and the existing current
Provider-head clearing semantics. No new Store, scheduler, Owner, router,
or independent parser. A new CLAIMED/DISPATCHING admission must bind
the CAS Event record to the original Run, Adapter, requested Model,
recorded time, state and request references. DISPATCHING must follow
the *current* same-attempt CLAIMED, not any earlier record. The same
current-predecessor query is reused by V4 COMPLETED instead of
duplicating another causal rule. The immutable Run dispatch-budget
check remains inside the same Run lock and is evaluated before the
other admission predicates. Exact replay still reconciles Existing
before all new-write gates.

A second concrete RED showed a forged *different ProviderCallId*
UNKNOWN after actual durable DISPATCHING could also be committed.
Failure-state admission now checks V4 identity/status, the referenced
FailureReceipt's exact CAS and request identity, and the latest same
ProviderAttempt predecessor. FAILED may follow an authentic CLAIMED
or DISPATCHING, while UNKNOWN after possible send requires the
current DISPATCHING predecessor. No failure label grants actual safe
retries or proves Provider billing settlement.

Genuine PG18 GREEN:
- `job-01a1de26-979d-71df-a28a-3b7c43044aea`: wrong-Adapter dispatch
  rejected, normal positive/redacted/UNKNOWN, budget, original Python
  independent readback and CAS atomic rollback pass.
- `job-01a1de2a-822b-7328-8fad-e245da20e1ee`: wrong-call UNKNOWN
  rejected and its staged CAS rolled back. Native PG V4 4/4, original
  no-Tool HTTP source test, independent Python readback pass; scratch
  PG18 cluster stopped and removed. External LLM calls 0, physical
  Tools 0, DomainSuccess 0.

Owner truth scope: these proofs cover source-owned original PostgreSQL
Writer admission for the tested V4 events. They do NOT prove that the
production NativeAgentLoop is wired to this Journal, that the current
Security Credential owner can materialize secrets, that Gateway has a
deployed `execution.harness` route, or that real HTTP dispatch/Tool
physical effects are authorized at spawn time. No installed production
change, paid Provider call, or automatic retry is claimed.

Thought LEGO: Design by Contract, Event Sourcing, causal ordering, FMEA
failure-state analysis, RED/GREEN independent falsification, UNKNOWN
not FALSE, DELETE-CUSTOM->REUSE->COMPOSE.
Logical LEGO: L1 Run authority, L4 Provider identity, L6 Journal,
L9 admission, L11 evidence, L12 recovery.
Ability LEGO: reused and refined `harness-pg/src/journal_write.rs`,
reused `harness-core/src/provider_head.rs`, extended the original
`harness-loop/tests/pg_provider_head.rs` real PG18 consumer; no
second Writer, Provider, scheduler or registry.


## R37 FailureReceipt shared semantic admission (P0 + important P1 reuse)

R36's source-owned Writer correctly fences the V4 UNKNOWN/FAILED event to
the current ProviderAttempt, but its FailureReceipt check was weaker than
the independent SELECT-only Rust recovery consumer: an exact CAS with a
valid call/request identity and an invalid `dispatchSafety=blind_retry`
could still enter the durable PostgreSQL Journal. The real PG18 negative
test **failed as intended** on original R36:
`job-01a1de32-bbd9-75aa-aaff-8b2ae65c26aa`.
The affected test did not silently pass; a positive event was wrongly
admitted, so the negative integration case failed. That is a source
counterexample, not a physical model billing observation.

DELETE-duplicate: extracted the source-defined eight-field, UTF-8
bounded, Provider failure-code and dispatch-safety enum, canonical
digest and same-attempt identity validation into one pure
`harness-core::provider_head::validate_provider_failure_source`
function. The natural original PG Writer and the existing SELECT-only
`harness-loop::pg_domain_read` consumer now call that SAME function
through their own narrow field projections. The Reader never receives
raw private failure detail: it consumes its existing boolean
detail validity projection; the Writer checks its locally owned
canonical object, within the same PG Run transaction. No new DB, PG
writer, retry service, V4 parser, secret materialization or scheduler.

Genuine PostgreSQL18 GREEN:
`job-01a1de35-0a59-72e8-895e-e5317718fe9c`: native PG V4 4/4,
positive retained+redacted, source budget, wrong Adapter,
foreign Unknown, invalid FailureReceipt enum and CAS rollback all
pass; independent original Python Store validates recovered histories;
scratch PG18 stopped and removed. Native full Cargo Workspace
all-targets offline test passed, and strict clippy -Dwarnings passed
`job-01a1de36-733e-720c-ae2d-ef4e17a21e86` after a small
nested helper syntax cleanup.

This closes *only* the tested original PG FailureReceipt Writer / Reader
source semantic asymmetry. It does not implement production model
credentials, external billing, installed Gateway `execution.harness`,
ToolOwner physical receipt, real multiround Cognition recovery or
DomainSuccess. Those remain explicit P0.

LEGO: thought=Design-by-Contract, fail-closed error taxonomy, Event
Sourcing, single-writer ownership, independent RED/GREEN falsification;
logical=L1 current Run, L5 Provider result shape, L6 atomic Journal,
L11 receipt evidence, L12 UNKNOWN reconciliation; capability=refined
existing `harness-core/src/provider_head.rs` shared pure validator,
reused `harness-loop/src/pg_domain_read.rs` SELECT-only reader,
`harness-pg/src/journal_write.rs` current PG writer, existing real
`harness-loop/tests/pg_provider_head.rs` PG18 scenario.


## R38 current CLAIMED predecessor safety (H01/H09 P0)

A third independent original PG Writer admission counterexample was
reproduced: after one real source PostgreSQL Run was already at
DISPATCHING (the HTTP request may have been sent), an adapter with
a currently valid lease could append a different first-generation
CLAIMED ProviderCall **without** the source-required previousRecordDigest.
The source Python `run_continuity.claim_provider_call` rejects a new
call while an active DISPATCHING requires reconciliation; the existing
Rust read-only recovery checks prior V4 digests, but the original PG
Writer R37 did not yet check CLAIMED causal currentness.

RED genuine PostgreSQL18:
`job-01a1de3c-5557-7536-afb9-68aaef98bc69`: test caught
`Ok(Created)` from the original source Writer for a forged overlapping
first-generation CLAIMED. This is a durable fact counterexample, not
an externally billed model call.

The narrow source fix uses the ALREADY EXISTING
`current_provider_predecessor` under the original PG Run row lock.
CLAIMED may omit a predecessor only when the currently active Provider
head is absent/cleared; when a predecessor exists, it must match the
exact current source CAS, and an unresolved CLAIMED/DISPATCHING/FAILED/
UNKNOWN head cannot be bypassed by authoring an unrelated fresh call.
The admissible next-turn predecessor is a completed call; final
business-domain next-turn sequencing and physical Provider issuer
remain separately owned. No second concurrency gate, Writer or
scheduler is created.

GREEN genuine PostgreSQL18:
`job-01a1de3d-3e69-77dd-b9bc-4fda497f86a7`:
`PG18_PROVIDER_OVERLAPPING_CLAIM_DENIED_PASS`, normal Provider
positive/redacted, valid UNKNOWN, existing budget/identity/invalid
FailureReceipt checks, original Python Store independent recovery
all pass; PG18 V4 4/4 and original noTool real localhost HTTP test
pass, scratch PG18 stopped and removed.

LEGO thought: Event Sourcing current-head causal semantics, contract
refinement, TDD real PG RED/GREEN, UNKNOWN not FALSE.
Logical: L1 Run, L4 Provider identity, L6 Journal, L9 dispatch
admission, L12 recovery.
Ability: one additional guard in the original
`harness-pg/src/journal_write.rs` and one source-owned adversarial
scenario in `harness-loop/tests/pg_provider_head.rs`.
No production installation, external model charges, physical Tool
or independent DomainSuccess has been claimed.


## R39 next-turn CLAIMED source identity and unbounded sequence

A fourth distinct real PG18 admitted-causal-state counterexample:
after a completed ProviderCall and a valid rev4 lease, an adapter
could assign a different ProviderCallId but reuse the SAME old
turnSequence and turnId, while binding the previous completed CAS.
This passed R38's coarse "there is a completed predecessor" check.
It is not a true next-turn claim under the original Python source
`run_continuity.claim_provider_call` rule. RED actual scratch PG18:
`job-01a1de40-6d89-70e3-9945-8dace4f38d90`; positive and
redacted original cases both failed at the expected new negative.

Reused the R38 locked current predecessor and original Core
`ProviderRecordHead`. CLAIMED after current COMPLETED must carry
a DIFFERENT ProviderCallId, exact next numeric turnSequence, and
the same sourceKind/sourceDigest/sourceObjectDigest provenance.
`NonnegativeDecimal::is_immediate_successor_of` is a tiny typed
core primitive that handles the Python source's arbitrarily long
integer identity without truncating to u64; positive and negative
unit controls cover 9->10, u64 overflow and 400-digit transitions.
The original next-turn semantic rule, not a new router/registry,
is the authority. First claims after cleared heads remain allowed;
unresolved prior dispatch remains blocked.

GREEN true PG18: `job-01a1de41-d545-70cf-ad7e-6cd437f591a9`,
`PG18_PROVIDER_COMPLETED_SAME_TURN_RECLAIM_DENIED_PASS`.
Original Python PG Store and positive/redacted completed, legitimate
UNKNOWN, wrong-Adapter, budget and failure-ABI negatives all pass
on 4/4 V4 integration tests; one noTool real local HTTP test also
passes. Scratch PG18 stopped/removed, external Provider 0, Tool 0,
AgentSolved 0. This is source Writer state semantics, not evidence
of a production model or external billing audit.

LEGO thought: Design by Contract, Event Sourcing, original Python
semantic parity, unbounded typed representation, falsification-first.
Logical: L1 current Run, L4 Provider turn, L6 Event/CAS journal,
L9 admissible next dispatch and L12 valid recovery.
Capability: existing `harness-core/src/provider_head.rs`,
`harness-pg/src/journal_write.rs`, original
`harness-loop/tests/pg_provider_head.rs`; no new Store/Owner.


## R40 source-owned native Provider Event Author and actual PG consumer

P0 H01 source-only advance, **not production deployment**. R39's typed
Rust ProviderRecordV4 CAS was already used by the genuine NativeAgentLoop
and original PG18 Writer, but the PG Event's six-field `data` payload and
reference ordering still came from a Python *test Oracle template*.
That is a test seam rather than a native reusable Provider Journal input.

TDD RED: a new Rust consumer in `provider_v4_source.rs` demanded the
reusable `author_provider_event_v4` producer and failed to compile because
the capability did not exist (Job `job-01a1de61-d6d3-7172-aba6-a89f3c650c45`).
GREEN: placed the pure typed event producer adjacent to the existing
`author_provider_v4` in `harness-loop/src/provider_v4_author.rs`.
Its only input is an already valid source V4 record, the original State
and optional Request/Result/Failure CAS references grouped in a small
`ProviderV4EventRefs`, one exact Event identity and recorded time. It
does not write PG, create a new Store, grant Provider dispatch, read a
credential or infer successful domain completion. Event status and CAS
reference presence must match the original V4 record.

The existing `pg_provider_head.rs` real original PG18 consumer now
authors **actual submitted EventWrite data in Rust** for
CLAIMED, DISPATCHING, UNKNOWN and COMPLETED; before the original PG
Writer commits them, an independent original Python pure Source Oracle
checks their exact canonical JSON bytes, reference order and kind.
Positive retained-content, positive redacted-content, ambiguous
transport UNKNOWN, original Source PG CAS rollback and unrelated forged
Event negatives are still exercised through the SAME Writer. The
original Python Store independently reads and validates persisted
Run history. No additional proxy, scheduler, feature switch or native
PG Writer has been created.

Genuine PG18 after Rust source-event author integration:
`job-01a1de68-a813-76e1-b1d3-d0e193085422`,
Provider V4 suite 4/4 PASS, source no-Tool local HTTP PASS,
original Python Store readback true, temporary PG18 stopped/removed,
external Provider calls 0, physical Tool calls 0. Native Rust
Cargo workspace all-target tests, fmt, strict Clippy -D warnings pass
(`job-01a1de68-48de-71c6-9084-e655c7766b6d`).
This qualifies a *native representation producer* and actual
isolated source consumers. It does not prove live production
`DurableJournal`, physical Provider credential at send, installed Gateway
`execution.harness`, Tool OwnerReceipt or independently verified
Coding AgentSolved.

Peer-Agent branch audit (read-only, no cherry-pick): current branch
already contains current Gateway Owner Job identity, delivery enum and
duplicated-tool/catalog checks in
`src/ordivon_harness/plugin_gateway_effect.py`. Historical Structure
Agent branches `feat/harness-b-r24-owner-receipt-identity` and
`integration/harness-r23-owner-fidelity-converged` are older, diverged
sources and should NOT be blindly merged, especially if doing so
would regress current checks. Review `feat/harness-r25-samepg-admission-current-no-second-store`
as a separate original Python/Runtime consumer cut; it is NOT a
native Credential/ToolPort integration and should not spawn a
competing PG owner. Other Agent evidence is source history only,
not a claim of current production install or active independent run.

LEGO: thought=Representation-first, TDD Red-Green, source ownership,
anti-corruption layer by direct composition (not wrapper proliferation),
independent cross-language falsification, UNKNOWN not FALSE;
logical=L4 Provider status, L5 exact typed Event representation,
L6 one original PostgreSQL Writer, L11 independent source evidence;
ability=reused `provider_v4_author.rs`, the exact `EventWrite` and
`append_events_with_provider_cas` from the original PG owner,
existing `pg_provider_head.rs` source consumer. No additional
persistent ledger or approval layer.


## R41 Provider metadata staged in one original PG Event transaction

The original real PG18 source test adapter still wrote native Rust-authored
CLAIMED and DISPATCHING Provider V4 CAS in separate transactions BEFORE
its corresponding original PostgreSQL Run Event admission. This unnecessarily
left orphan metadata objects if the Event/lease failed, in contrast with the
already existing original `append_events_with_provider_cas` path used
for private model Result content since R31.

True PG18 TDD RED: `job-01a1de6d-cacc-733a-98e3-8e8363e3354f`
observed existing claimed/dispatching objects before their Event.
The FIX changes ONLY the existing no-Tool Rust test Journal adapter,
not the original `harness-pg` Writer: native CLAIMED and DISPATCHING
records are constructed and compared against independent Python source
CAS digest expectations, but are not separately stored. Instead, both
typed `ProviderStagedCas::RecordV4` and their R40 Rust-authored Event
objects pass through one pre-existing Writer transaction, under the
same original Run Lease, revision, current identity and budget checks.
A forged foreign-Adapter dispatch negative now stages both legitimate
claimed and forged dispatch CAS so its rejection cannot be a trivial
missing-prerequisite failure.

The adjacent lost-response UNKNOWN path had the same pre-Event
metadata-orphan flaw for the Provider failure receipt and UNKNOWN V4.
The original PG18 RED `job-01a1de6f-c980-70f8-9c8f-4a9defabb6fe`
caught the previously committed failure/unknown CAS before the Event.
Both objects are now staged together with the Rust-authored UNKNOWN
Event inside the SAME original PG Writer transaction. Existing foreign
ProviderCall and malformed failure-enum negatives stage their necessary
source CAS so rejection remains meaningful. No second Writer, registry,
replay layer, or additional authority was added.

Real PG18 GREEN `job-01a1de70-6e1a-71c8-8ad6-eff2fc235a5b`:
Provider V4 4/4, original Python Store readback, positive retained
and redacted content, causal FAILED/UNKNOWN adversarial cases, source
model dispatch budget and original no-Tool local HTTP all PASS;
scratch PG18 stopped and removed. Full native Cargo fmt/all-targets
tests/Clippy `-D warnings` PASS
`job-01a1de70-f5dc-7028-a551-fdf6d065915f`.
No real external Provider call, physical Tool or independent domain
TaskSolved occurred.

Scope boundary: this is an important **test/source Journal producer
cutover**, improving the source-equivalent reusable transactional
seam for H01. It DOES NOT mean `NativeAgentLoop` has a production
registered `DurableJournal`, Security-owned credential materialization,
installed Gateway `execution.harness`, or physical Tool receipt.
Avoid building yet another CAS/PG/replay permission layer; the remaining
H01 hard core is composing the existing source PG Writer/Provider into
one actual supported production Run entrypoint.

Thought LEGO: Event Sourcing, TDD RED/GREEN, ACID transaction atomicity,
delete-duplicate/reuse-mature, independent Python source Oracle,
UNKNOWN not FALSE. Logical LEGO: L4 Provider Call, L5 typed Event source,
L6 original PG Writer, L9 source admission, L11 provenance and L12
uncertain recovery. Ability LEGO: refined existing
`harness-loop/tests/pg_provider_head.rs`, reused
`harness-pg/src/journal_write.rs::append_events_with_provider_cas`
unchanged, and R40 `provider_v4_author.rs` Event type. No new Store.


## R42 PG-bound provider requires one pre-frozen HTTP body

Source P0 physical-effect seam: `HttpModelProvider::new_provider_only_pg_bound`
reads a CAS-backed immutable Provider transport configuration from
the original verified PG Run, but previously inherited the generic
`HttpModelProvider::query` fallback: if no exact outbound JSON request
body had been frozen, it could compose new bytes *at send time*.
A caller that had already persisted an original V4 DISPATCHING with
an expected `providerRequestDigest` could therefore send a different
or unbound request, despite the original Writer's causal and budget gates.

True PG18 + actual localhost HTTP RED
`job-01a1de78-ce3c-7397-a169-a612d44752be`: a freshly constructed,
source-authenticated PG-bound provider called `turn(1, [])`
without freezing; it **reached the wire**, consumed the source local
server's only response, and violated the new pre-send negative.
The source was not merely a mock function. No external LLM/provider
was called.

The narrow fix is in the **existing natural HTTP transport**, NOT a
second authorization/replay wrapper. The PG-bound constructor sets a
private `require_source_frozen_request` bit. Its query refuses a
missing frozen request BEFORE HTTP send, quarantines the Provider
instance, and returns the current conservative UNKNOWN observation;
a new correctly frozen PG-bound Provider sends its exact source
request normally. Ordinary standalone HTTP constructors retain the
prior direct-request behavior. This guard does not prove external
billing status or authorize a future retry.

GREEN true PG18 `job-01a1de79-5b8a-77e5-9ee6-f93c7be2b113`:
original source-bound loopback HTTP 1/1, V4 PG native 4/4,
Python original Store readback positive/redacted/UNKNOWN and CAS
rollback all pass; PostgreSQL scratch instance stopped/removed.
It closes this local *unfrozen physical wire* escape hatch,
not the production journal/credential/issuer bind: the natural
Security owner credentialMaterializationBindings is still absent
on installed Runtime and Gateway `execution.harness` remains absent.

Thought LEGO: source-first Design by Contract, TDD RED/GREEN, TOCTOU
risk control at natural physical-effect owner, no duplicate permission
layer. Logical LEGO: L1 Run, L5 exact Provider wire, L6 PG Journal,
L9 pre-send admission, L12 ambiguous recovery. Ability LEGO:
refined existing `native_provider_http.rs` PG-bound constructor +
query, test `native_pg_no_tool_http.rs` true local HTTP with
original PG source; no new service/Store/credential provider.
