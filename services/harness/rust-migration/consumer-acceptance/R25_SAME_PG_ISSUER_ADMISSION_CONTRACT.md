# R25 — issuer-bound new Job admission on one PostgreSQL transaction

**Status:** verified isolated-source candidate, opt-in only, not deployed.
This implements Admission-current only; it is not a claim of Spawn-current,
ongoing-revocable process authority or cross-cluster consensus.

## The hard contract

For a new Runtime physical Job J associated with a Harness Run R, the issuer
must validate the exact operation that the Runtime commits. Both checks must
serialize with real issuer revision/stop in the SAME PostgreSQL transaction.
Neither a caller-supplied ForeignReference nor an old unlocked currentness
SELECT is sufficient to prove that new effects are authorized.

The source binding includes the immutable tool-prepared Run Journal event,
the original Tool Intent T, the versioned Dispatch Fence F, the live Run
revision and the original physical execution digest E. Admission requires:

- Run status ACTIVE and revision equal to F.runRevision.
- F unexpired by the PG server clock, correct Run/Intent/clientRequestId.
- T and F valid canonical CAS bytes matching the current tool-prepared Event.
- E from that same prepared Event equals the digest reconstructed from the
  actual Runtime immutable physical execution plan, including workspace,
  executable, args, cwd relative to Workspace, env, time/output bounds and
  original foreignReferences followed by the exact source Fence.
- No steps, custom budget or host dependencies unsupported by the source.
- The original Harness Run row is locked FOR SHARE against its writer FOR
  UPDATE throughout the native Runtime Job/Attempt/idempotency transaction.

The existing Runtime exact-key idempotency lookup runs FIRST. Replaying an
already committed request after issuer revocation resolves the SAME Job
without re-dispatch. Changed bytes still return IDEMPOTENCY_CONFLICT.

## No second Store, Registry or raw tool-argument persistence

The existing source tool-prepared Journal Event optionally includes only
physicalExecutionDigest = canonical_digest(original_request.execution).
The original Runtime request is verified at preparation against the existing
Tool Intent runtimeArgumentsDigest, then its raw args/env are discarded.
This preserves metadata-only/model-only privacy requirements, while a new
opt-in issuer-bound Job requires this committed digest. Existing non-physical
tool routes do not change.

The existing Harness PostgreSQL schema creates a narrowly scoped
SECURITY DEFINER function named harness_current_dispatch_cut with its original
tables; there is NO new authority table. This function locks the source
Run row until caller transaction COMMIT and returns only source Event/CAS
identity records: the prepared payload, matching Fence and Tool Intent.
Rust independently verifies their SHA-256 digests, schema kinds, source
relations and the SHA of the actual resolved physical proposal.

### Explicit same-database activation

Use only a deliberately configured Runtime endpoint whose connection points
to the SAME PostgreSQL database as the Harness issuer. Opt in with:

    ORDIVON_PG_HARNESS_ISSUER_SCHEMA=harness_schema

The issuer-controlled schema function must be installed by a qualified source
migration. Grant the Runtime SQL role ONLY this function's EXECUTE and
issuer schema USAGE, never issuer Run UPDATE or private CAS SELECT:

    GRANT USAGE ON SCHEMA harness_schema TO runtime_app;
    GRANT EXECUTE ON FUNCTION
      harness_schema.harness_current_dispatch_cut(text,bigint,text)
      TO runtime_app;

The isolated PostgreSQL 18 test explicitly verifies runtime_app cannot
UPDATE source runs or SELECT private source objects.

When the env variable is absent, Runtime retains the old correlation-only
mode; DO NOT label it issuer-authorized. Legacy Tool Intents without a physical
digest are intentionally not admitted as NEW issuer-bound effects. Historical
committed Job readback/replay continues unaffected. A separate database or
cluster does not inherit this single-transaction property.

## Real PostgreSQL18 / Gateway / Native Runner acceptance

The existing opt-in physical fixture is
services/gateway/tests/test_pg_real_runtime_owner.py. Provide prebuilt
qualified real Runtime and Runner executables and the Harness Python env:

    ORDIVON_GATEWAY_PG_E2E_BINARY=/path/to/ordivon-runtime-pg
    ORDIVON_GATEWAY_PG_E2E_RUNNER=/path/to/ordivon-runtime-runner
    ORDIVON_GATEWAY_PG_E2E_HARNESS_PYTHON=/path/to/harness/bin/python
    ORDIVON_GATEWAY_PG_E2E_REAL_HARNESS_SOURCE=1
    ORDIVON_GATEWAY_PG_E2E_ISSUER_ADMISSION=1
    python -m pytest -q -s services/gateway/tests/test_pg_real_runtime_owner.py

It creates only a disposable private PostgreSQL18 cluster and exercises
actual Harness PG Run/CAS/Intent/Fence -> Gateway SDK/HTTP MCP -> native
Rust Runtime PG Job -> systemd Runner and physical result. It confirms:

- Current issuer accepts exactly one genuinely executed new Job;
- a durable Run revision, terminal Run, expired Fence, absent issuer reference,
  or a forged executable argument are all denied BEFORE a new Job;
- denied effects are typed AUTHORIZATION_DENIED, not disguised as PG outages;
- a second independent PG client holds the source Run revision row lock
  after a real Event update but before COMMIT: new Runtime admission waits,
  then sees its committed revocation and refuses the Job;
- exact original Job request replay after source revocation returns the
  existing Job without another DISPATCH_ISSUED.

## Unsolved stronger effect policies

**Spawn-current** is not established. The R24 true counterexample shows a
durable DISPATCH_ISSUED record can precede issuer revocation, and only
afterward can systemd launch the previously accepted process. The actual
launch receiver needs a qualified issuer reservation / monotonic fencing
handshake to guarantee a stronger source-current-at-spawn policy. An extra
currentness read cannot close this cut.

**Ongoing-revocable** is not established. An already running arbitrary native
process or external side effect cannot be rolled back by Lease expiry, Run
stop or operating-system cancellation. Unsupported profiles must fail closed
rather than turning UNKNOWN into FALSE.

This candidate does not establish cross-cluster atomicity, production
TLS/role qualification, unknown commit reconciliation, all physical plan
forms, installed binary identity, or semantic task success. True production
promotion still needs independent source-HEAD review, a verified schema
migration, deployment-specific evidence and rollback.
