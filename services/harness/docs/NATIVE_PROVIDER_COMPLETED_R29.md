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
