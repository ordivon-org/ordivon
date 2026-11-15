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
