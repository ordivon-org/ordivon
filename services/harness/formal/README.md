# Harness Provider Claim R1

This owner-bounded TLA+/TLC model reuses the digest-verified official tool
exposed by Runtime. It is not a new Agent scheduler, source of truth, custom
proof engine, or complete Python implementation-refinement proof.

Owner source correspondence:
- sqlite_run_store.py claim_provider_call: Claim, ExpireClaim, ReplaceExpiredClaim.
- sqlite_run_store.py mark_provider_call_dispatching: AdmitDispatch with current
  holder and generation; durable fence before physical dispatch.
- Actual Adapter.invoke: separate opaque PhysicalCall event.
- sqlite_run_store.py complete_provider_call: CommitResult.
- Caller-visible StandaloneHarnessRunner.run: DeliverAcknowledgement.
- Lost response/uncertain physical effect: LoseKnowledge, no blind retry.

The model checks at-most-one physical call, no acknowledgement before durable
result, generation preservation after admission and unknown-state fencing.
Two competing holders and an expired pre-dispatch claim are represented.
Expected counterexamples establish physical-but-unacknowledged execution,
replacement of an expired CLAIMED lease, and reachable successful delivery,
avoiding a vacuous no-dispatch proof.

Harness queue and verify run the native model. Concrete SQLite consumer:
tests/test_p0_standalone_runner.py (twelve concurrent workers), observing
physical calls, event lineage and caller successes separately.
This is NOT a proof of actual SQLite transaction isolation, arbitrary concurrent
process safety, external Provider idempotency, domain outcome or liveness.
A concrete trace-refinement witness remains UNKNOWN and must be tested with
Owner implementation evidence. Use CEGAR to separate realizable defects
from spurious abstract counterexamples before refining the model.


## Privacy and caller-delivery CEGAR refinement (2026-10-25)

The real twelve-worker CDC exposed durable Provider completion with one physical
call and zero caller acknowledgements under metadata-only privacy. The older
model allowed acknowledgement from durableResult alone. CommitResult now
distinguishes (1) durable digest, (2) content-authorized replayable result,
and (3) the original caller's ephemeral result envelope. Losing the envelope
before acknowledgement is a separate transition and does not permit dispatch
again. DeliverAcknowledgement needs one permitted result source.

Both privacy modes can acknowledge a fresh result. Only content-authorized
runs may replay after losing the original envelope. Native TLC checks the
privacy-retention and acknowledgement safety invariants, plus two deliberate
reachability counterexample probes for fresh metadata-only acknowledgement
and redacted completed-but-unacknowledged records.

Independent concrete consumers: test_p0_sqlite_agent_loop.py tests
metadata-only recovery fencing and content-authorized replay. The 12-worker
test's explicit privacy premise is already provided by PR #668, not duplicated
here. The ephemeral result is symbolic: no machine-checked concrete SQLite
trace refinement or delivery liveness is claimed.

## H04 Conversation Binding PostgreSQL cutover — bounded CEGAR R1

Model: `ConversationBindingCutoverR1.tla` and the three independent
negative reachability configs. The existing Runtime-owned, SHA-verified
official TLA+/TLC checker runs through the Harness native
`formal:verify` task and therefore the existing queue/verify gates.

Representation / explicit assumptions:

- `legacyRows` is a bounded set of source identities; `pgRows` is a
  bounded set of PG identities (not actual row bytes or SQL constraints).
- `QuiesceOldWriter` models an **externally qualified** stop of legacy
  writers. The model cannot establish Windows/WSL process quiescence.
- `CommitPgImport` and `SealOldWriter` are **two separate durable
  authorities** with no imaginary atomic cross-database transaction.
- `LoseMigrationResponse` makes the PG-committed, source-not-yet-sealed
  gap reachable; PG binding admission remains forbidden in that state.
- `ReplaySourceCutover` explicitly permits newer PG-only identities
  **after** sealed source identities remain a subset of PG records.
- `AdmitPgBinding` requires committed PG import, sealed legacy writer,
  and qualified old-writer quiescence; no implicit SQLite fallback.

This is a finite safety abstraction, **not** a refinement proof of
`postgres_conversation_binding.py`, SQL triggers, loaded source path,
serializable isolation, external writer-stop checks, or deployment. Real
PostgreSQL 18 consumers in
`tests/test_postgres_conversation_binding.py` and Browserless no-fallback
consumers in `tests/test_conversation_binding_pg_selection.py` remain
independent mandatory evidence. Under CEGAR, a real counterexample takes
priority over this abstraction even if TLC reports PASS. No additional
formal engine, source registry, or migration framework is introduced.
