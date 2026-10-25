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
