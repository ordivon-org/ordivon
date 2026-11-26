# Runtime native consumer qualification R1

This refines TESTING_UPSTREAM_ADOPTION_R1 and the cross-core Host Work,
not a new test framework or another state authority.

## Problem and boundary

The existing native PG core qualification and Windows bundle witness do
not execute the distinct pg_vertical HTTP MCP, disposable PG, Git and
systemd consumer test binary. Unit success, core PG success, native MCP
success, installed release and production consumer success are distinct.

The explicit Linux lane is mise run test:postgres-registry:mcp-native.
It reuses the official checksum-qualified Nextest tool and native Rust
fixtures. Ordinary fast verify runs the existing source gate and the small
acceptance adapter tests; it does not claim native consumer coverage.

## Logic and capability map

- Obligation: stable critical witness identities spanning admission,
  execution/cancellation, binary evidence, close/admit race, revoked
  writer, privilege boundary, release fencing, restart/leasing. Discover
  all additional test identities from Nextest JSON, not source grep.
- Environment: exact version from mise, Cargo.lock, clean Git cut, actual
  Linux fixture-owned disposable PG and native Runner; no production DSN.
- Selection: all cases of the exact pg_vertical binary, including ignored
  tests, independent of default filters or inherited Nextest configuration.
- Execution: upstream process-per-test, one test thread, no retries,
  no fail-fast, no new scheduler. The expensive lane is explicit.
- Verdict: native successful exit plus exact same native JUnit identities,
  one PASS each, no skip, missing, duplicate, unexpected, retry or flake.
  Empty inventory or missing critical witnesses fail closed. Domain
  correctness still requires independent oracles.
- Evidence: native JSON discovery and JUnit digest, test identities and
  individual outcomes, source/lock/version identity. For durable raw
  evidence, supply RUNTIME_NATIVE_MCP_EVIDENCE_DIR as an absolute new
  directory outside checkout; publish through existing Artifact consumer
  and verify readback before releasing workspace.
- Release: official CI, Windows-native tests, deployment identity and
  real external consumer/restore remain separate. No production DDL or
  cleanup follows from this lane.

## Acceptance and falsification

The adapter tests independently challenge missing and deselected discovery,
wrong binary/count, empty list, skipped/error/failed, flaky/retried,
missing/duplicate/foreign report identity and forged aggregate.
Environment isolation is tested separately. The exact approved Nextest
binary must also parse real discovery and JUnit from native tests.

P0 full native lane must report all cases, even failures. Report environment
blocks separately; do not delete tests or change expected sets to achieve
green. P1 property/stateful, mutation and temporal failure testing should
extend actual lifecycle/ownership invariants using existing upstream
tools; mutation errors/timeout are not automatically killed mutants.
Do not merge another dependency lock or duplicate Host/Preservation tests.

References: https://nexte.st/docs/machine-readable/list/
https://nexte.st/docs/machine-readable/junit/
https://nexte.st/docs/features/retries/
https://nexte.st/docs/design/why-process-per-test/

## R19: make the native environment correct by construction

The initial strict run executed 33 tests, with 25 PASS and 8 failures.
Six had no host-visible Runner selection and shared a cross-mount
execution failure. Replace the optional switch with the existing
private byte-verified Runner copy in every native endpoint Fixture.
Keep deliberate negative launch and security cases unchanged.
Ordinary MCP exact catalog identity excludes the finalizer-only
claim.release and unqualified release.apply; do not change production
authorization merely to satisfy a stale assertion.

Materialize the actual Harness source lock with the existing uv sync
--locked --no-editable --group test in the suite's private environment;
bind HARNESS_PG_PYTHON explicitly, validate original issuer imports and
lock identity. No implicit system Python or shared project environment.

Make native Nextest inherited-handle leaks fail instead of pass.
This is not a proof that independently launched systemd units are gone.
External-resource acceptance needs exact Fixture identity, private PG
Attempt identity, native Unit carrier and physical state. A retained
failed Unit may be required by the LOST test until its terminal PG
commit: do not change production CollectMode or reset prematurely.
After preserving evidence, only exact test-owned dead Units can be
released, never a broad systemctl reset. Unknown, live or foreign
ownership must block retirement. Separate panic-safe Fixture cleanup
and SIGKILL recovery proof remain explicit obligations.

## R20: async terminal observation as a test consumer contract

The R19 full gate reported 32/33, with a new fail-fast Plan assertion
receiving an accepted, nonterminal Job. That receipt proves admission,
not a final execution outcome. Do not resubmit, change production
scheduler policy or silently turn a pending result into failure.

Reuse the existing MCP client and native PG fixtures. Extract one test
consumer module: qualify ordinary or committed E40001 response, preserve
Job identity and the first known Attempt and Operation digest, observe
only the original Job, and require a typed terminal predicate consistent
with a recognized disposition. Terminal does not mean domain success.
A monotonic per-observation-phase budget caps server waits and HTTP
transport; expiration and unexpected errors remain failures with the
last known receipt when available. This is not a production client or
retry scheduler. The preceding submit has its own existing wait budget.

The independent scripted clock/state sequences reject foreign identities,
unqualified errors, malformed terminal predicates, inconsistent disposition
and unbounded pending; an already-terminal receipt must not be observed
again. Require key observer tests in native Nextest discovery.

Native qualification deliberately submits fail-fast at waitMs=0 and
retains the actual failed result, missing second-step output, exact one
Attempt, one dispatch and one terminal event. A separate held-capacity
case checks real accepted/pending and zero allocation/dispatch, then
retains the existing passive PG convergence check through endpoint
restart before consuming the same Job terminal. Observation must not
rescue a stalled scheduler and hide the original obligation.

Keep the R19 RED and distinguish a verified pending-to-terminal consumer
from a proof of the original scheduling cause. Do not retry the entire
test to turn a failure green. Native suite, compiled source mutants,
exact inventory/JUnit and CI/installed standing remain separate.

Reference: https://learn.microsoft.com/en-us/azure/architecture/patterns/asynchronous-request-reply
https://nexte.st/docs/features/retries/

## R21: fixture lifetime is not test-process lifetime

Compose R18–R20 and the independent native Nextest group before adoption.
A process-per-test runner cannot establish that external transient Units
or a PostgreSQL postmaster are absent. The test runner owns a unique
short /var/tmp scope, not an inherited path or recursive temporary
directory. Rust fixtures create a child there. The constructor owns the
postmaster as soon as spawn succeeds. Normal teardown stops the endpoint,
checks the exact private PG Attempt-to-bundle-to-Unit bindings, and
observes native Unit absence before fast PG shutdown and directory removal.
Unknown or failed Unit readback, shutdown failure, and panic retain the
root. Do not reset failed native Units before the production terminal
evidence consumer has observed them; do not change CollectMode.

The suite requires the actual scope to be empty and removes it with
rmdir only. A missing report or timed-out/killed runner is not qualified;
the scope survives for independent inspection. The original JUnit and
exit standing remain separate from the scope verdict. The new native
panic challenger deliberately creates a PG fixture, unwinds, checks its
retained root and stopped postmaster/socket, and only then removes that
specific test-owned carrier. The independent SIGKILL marker challenger
tests the scope contract, not arbitrary native descendant recovery.

This is a bounded observation of registered Unit identities, not a
linearizable systemd fence or proof that every possible orphan is absent.
The outer gate does not perform blind reaping. SIGKILL of an actual live
Fixture, unregistered Unit detection, and safe retry of physical cleanup
remain separate qualification obligations. Direct libtest runs outside the
strict scope may leave a diagnostic root; use the strict gate for adoption.

R21 integration initially reported 42/42 native JUnit passes but correctly
failed external-resource qualification. The one retained root was the
historical list-result case: private PG readback showed an invented
r6-previous-* historical identity. Both exact native units were absent
and PG shut down. Preserve this original run as RED; use the same native
Attempt identity shape for the synthetic historical row, with history
semantics still expressed by attempt_number. Do not weaken the guard.
Retained diagnostic reason is written inside the exact fixture and the
outer verdict is emitted on stdout even when compiler stderr is capped.
An additional real failed transient Unit challenger verifies that loaded
failure is not absence and only test-owned, dead, identity-bound Unit
retirement enables release.

## R22: actual killed Fixture child and native private PG recovery

The crash challenger is deliberately separate from the adoption candidate
and from production Runtime reconciliation. It starts the same native
Fixture in a single owned test child; a private one-use handshake binds
the child PID, exact PG data directory, PID/start identity and native PG
system identifier. After actual SIGKILL and child wait status, verify
the private PG is still running (pg_ctl status 0) and the same cluster
has no registered Attempts or external Runner. Then use native fast
shutdown, require pg_ctl status 3 and absent PID file/socket, release
only the two exact owned directories. Clear inherited challenger role
from strict gate, require the exact native witness in discovery. No
generic reaper, arbitrary PID signal, production change or concurrent
ownership proof. The native recovery is bounded to this no-writer,
PG-only fixture; arbitrary live Runner/systemd recovery remains open.
