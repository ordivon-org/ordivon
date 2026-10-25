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
