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

## R26 — authenticated issuer profile on one existing PG Runtime

The formal protected merge of PR #2085 is source commit
5cb7f1536f20431c200cc90285286818e9df313f, NOT an installed release.
The R25 isolated whole-process issuer mode denies ordinary unfenced Jobs and
must not be enabled directly on the shared production Runtime service.

R26 reuses exactly one Runtime process, PG writer schema, native Runner and
scheduler, exposing two authenticated profiles. There is no second Registry
or PostgreSQL data authority:
- Existing /mcp retains existing local, remote and Access authentication,
  ORDIVON_PG_PRINCIPAL and unfenced execution.linux behavior.
- Dedicated /harness/mcp uses a DIFFERENT private-file Bearer set through
  ORDIVON_PG_HARNESS_TOKEN_FILE and separate authenticated
  ORDIVON_PG_HARNESS_PRINCIPAL, and requires
  ORDIVON_PG_HARNESS_ISSUER_SCHEMA for source-current NEW Job admission.
- Gateway execution.harness routes to owner key runtime.harness using
  ORDIVON_GATEWAY_HARNESS_RUNTIME_URL and
  ORDIVON_GATEWAY_HARNESS_RUNTIME_BEARER_TOKEN_FILE.
  This is an endpoint/profile alias of the SAME physical Runtime, not a new
  natural Owner service or an invented Agent identity. The two credentials
  cannot authenticate the opposite ingress, and ordinary Principal cannot
  inspect Harness Job IDs.
- The issuer role needs schema USAGE and function EXECUTE only: NO access
  to private source Run UPDATE or CAS SELECT. The token file must be a
  regular private, non-symlink file and Harness Principal distinct from
  the regular Runtime Principal.

Real disposable PG18 regression adds the native issuer-isolated opt-in
ORDIVON_GATEWAY_PG_E2E_ISSUER_ISOLATED=1 alongside the R25 source flags.
It exercises normal unfenced real Job, cross-token HTTP401, real
Harness SQL Run/Intent/Fence, Gateway SDK, native systemd Runner,
original UNKNOWN -> authenticated Owner Receipt, real native artifacts,
exact job replay and cross-principal denial, old revocation, expiry,
physical-plan tampering and concurrent issuer row-lock tests. A physical
success always retains semanticCompletionEvaluated=false; domain acceptance
is separately owned by the domain, never inferred from Runner exit 0.

Production acceptance remains UNKNOWN until qualified source install,
Harness PG schema migration and read-only role permission proof, operator
secret file placement, Gateway configured route, connector catalogue
refresh, structured Runtime ReleaseEffect deployment receipt, main PID
and Runner byte identities, original ordinary workload and new Harness
consumer positive/negative checks, and rollback. Do not substitute
generic workspace.exec for the root-qualified ReleaseEffect.

Important limits: Admission-current only, NOT currentness at the later
systemd spawn or ongoing revocation of an arbitrary side effect.
An authorized ordinary caller still has the legacy execution.linux route;
using execution.harness does not automatically revoke other actors' prior
permissions. Gateway/Security must authorize which caller can request the
dedicated route; foreignReferences cannot confer this authorization.
