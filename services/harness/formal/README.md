# Harness Provider Claim R1

This owner-bounded TLA+/TLC model reuses the digest-verified official tool
exposed by Runtime. It is not a new Agent scheduler, source of truth, custom
proof engine, or complete Python implementation-refinement proof.

Owner source correspondence:
- run_continuity.py claim_provider_call: Claim, ExpireClaim, ReplaceExpiredClaim.
- run_continuity.py mark_provider_call_dispatching: AdmitDispatch with current
  holder and generation; durable fence before physical dispatch.
- Actual Adapter.invoke: separate opaque PhysicalCall event.
- run_continuity.py complete_provider_call: CommitResult.
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

## R45 Tool UNKNOWN recovery — bounded safety refinement (2026-11-16)

Model: `ToolUnknownRecoveryR1.tla`. The existing Harness `formal:verify`
task uses the Runtime-owned official SHA-pinned TLC checker; no replacement
model checker, second Run Store or Owner execution engine is introduced.

The finite state representation distinguishes original PG Intent, one
physically admitted Owner submission, a lost response before/after admission,
an UNKNOWN Receipt, `effect-dispatch-pending` Pause, Owner reachability,
exact original Owner resolution and later bounded Run completion. Run
completion is NOT independently verified domain TaskSolved. A lost reply
before Owner admission may remain paused: missing Owner proof is not effect
absence and never authorizes blind resubmission.

Safety: at most one physical Owner submit; an observed/completed Tool step
requires an observed original-Owner receipt; an UNKNOWN Pause stays UNKNOWN
until exact Owner evidence arrives; reconciling requires the same Owner.

Four intentionally false counterexample probes reach a physical submission,
an ordinary recovered completion, a pre-admission unknown pause, and under
a separately enabled unsafe retry rule the duplicate physical effect.
This prevents a vacuous no-Tool-action safety proof.

**Truth boundary:** TLC checks the finite abstraction, not actual SQL
isolation, Gateway `execution.resolve` correctness, Runtime process launch,
or arbitrary Provider behavior. Concrete consumers remain the scratch
PostgreSQL18 `test_gateway_cli_consumer.py` plus the explicitly opt-in
`test_live_gateway_unknown_recovery.py` real Gateway/Runtime Owner test.
Any mismatch requires explicit independent falsification and refinement.

## R38 original source coverage — bounded refinement (2026-11-24)

`OriginalSourceCutR1.tla` models all bounded revision sequences of length
0..N, including omissions, duplicates, permutations and an independent
integrity verdict. The old last-revision-only guard has a concrete omitted
revision counterexample. The exact-cut guard requires every position and
integrity; the positive model checks coverage independently, and a deliberate
acceptance reachability counterexample rules out vacuous rejection of all reads.
The existing Runtime-owned SHA-pinned TLC gate checks all three configs.
The integrity verdict is a premise, not an implementation proof of PostgreSQL,
CAS or native Runtime drain. Concrete tests in
`tests/test_postgres_harness_store.py` retain the partial projection and actual
detached PG payload-edge counterexamples. No claim release follows from this
model alone.

### R39 second Tool admission refinement

The existing `ToolUnknownRecoveryR1` model now reaches a second prepared
Intent after the first is observed. It distinguishes a fresh key from reuse
of the first key. The unsafe old admission probe reaches key reuse, and the
fresh-key probe reaches legitimate second admission. This is a two-Intent
bounded source rule, not proof of arbitrary SQL execution, cross-Run
principal-level keys, physical second execution, or native drain.
The real PG consumer is
`test_issued_epoch_rejects_reused_runtime_client_request_id`; the test retains
an old-writer fault to demonstrate that historical duplicates still block
complete source enumeration. All older Tool UNKNOWN probes remain.

### R40 original Store terminal source refinement

The existing SourceCut model includes an original pending revision, visibility
in the read cut, and normal terminal acceptance. The unsafe tail-only model
can omit the pending revision and terminal incorrectly; the exact cut model
checks that no normal terminal has an outstanding source and the independent
positive probe reaches a clean terminal. UNKNOWN quarantine remains separate.
The real PG writer now validates the exact original events it uses under its
existing Run row lock before normal terminal admission. This reuses the
original Doctor history/edge validator and does not prove OS or Domain release.

### R41 global Doctor snapshot qualification

`DoctorSnapshotR1` models two Runs with one creation Event each and a
concurrent new Run insertion after the initial count. Its weak snapshot
probe reaches a mixed healthy report; its positive probe reaches a
coherent older snapshot despite concurrent creation. The positive model
requires a stable snapshot for a healthy global report. It intentionally
does not model arbitrary SQL histories, CAS contents, or physical effects.
The real PG test drives the original Doctor and a second live Store
connection and retains the valid per-Run nested row-lock path.

### R41 continuation: verified source consumption

OriginalSourceCutR1 now distinguishes original validated content from a
substituted second read with the same revision positions. The reread probe
reaches a substituted consumption after valid acceptance; the positive probe
reaches actual consumption of the original cut. This abstracts content
identity, not a proof of database cryptographic integrity.

### R42 new distinct effect admission

OriginalSourceCutR1 extends its existing exact-cut model to admission of a
new distinct effect, with a weak partial-cut omission counterexample and a
positive clean-admission reachability probe. The original Provider same-ID
replay/supersession remains a separate state machine; this bounded model
does not qualify native external effects.
