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

- Obligation: eight stable critical witness identities spanning admission,
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
