# H2: long-lived Harness Run holds on a Runtime Workspace (source candidate)

Status: **source-only, not installed, no production cutover claimed**.

## Why this is a distinct contract

An active Runtime Job reservation is not a long-lived Agent consumer. Two
independent Harness Runs may share one Runtime Workspace. After A reaches a
terminal Run state, B may still be paused between Jobs. Even with
`consumerReleased=true` from A, B's Workspace MUST remain open.

## Minimal carrier and scope

- Harness's existing **one PG Run Journal** owns the Run identity and terminal
  revision. A `run_workspace_claims` relation inside the **same Harness PG
  schema** records only one (Run, Workspace) hold and explicit release. It is
  not a second Job/Attempt registry and has no scheduler or supervisor.
  The claim foreign key RESTRICTs deletion of its Run (not CASCADE):
  deleting an unfinished Run must not silently erase its Workspace hold.
- A Run using the existing typed Gateway execution grant or direct Runtime
  execution binding registers its hold in the **same transaction as Run birth**,
  sharing Runtime's existing global PG advisory admission/close lock.
- Terminal Run success **does not release** a Workspace. The caller must
  complete its actual Artifact delivery/handoff and call exact
  `release_workspace_claim(run_id, workspace_id, expected_run_revision)`.
  This remains an owner-side handoff assertion: a terminal Journal record by
  itself does not prove consumer acceptance. Do not automate release on expiry.
- When operator-qualified `harness_issuer_schema` is configured for the
  **same PG cluster**, Runtime `workspace.close` reads the Harness schema's
  SECURITY DEFINER **aggregate count** inside its existing PG admission lock.
  A nonzero count blocks closure even when the caller supplies
  `consumerReleased=true`, and a missing function/permission fails closed.
  A nonterminal historical Run without classified Workspace ownership
  makes the aggregate return -1 (UNKNOWN), which the Runtime maps to
  ReconciliationRequired instead of pretending no consumer exists. This is
  intentionally conservative during PG schema migration: even a NoTool
  nonterminal Run may need qualification before broad Workspace GC.

- The aggregate function reveals only the number of unrelinquished claims;
  Runtime cannot read Harness private Run contracts or arbitrary table rows.
  The operator must explicitly grant EXECUTE only to the qualified Runtime
  PG role after applying `services/harness/sql/runtime_workspace_consumer_claim_r1.sql`.
  Do not grant it to PUBLIC and do not configure the issuer before migration.

## Limits / unfinished consumer proof

This protects **registered Harness-managed Runs only**, not arbitrary other
Agent processes, unregistered Workspaces, or direct tool consumers. It is not
yet a complete global Workspace ownership system. Every *new* consumer must
register its scope before effect admission, and real Gateway producer and
Artifact-delivery consumers must be tested end to end before enabling production
cleanup based on this signal. The initial Workspace source/Git identity,
closure FS effect and physical process checks remain Runtime responsibilities.

Physical validation gates: actual A/B PG Run birth => two holds; A terminal =>
two holds; A explicitly relinquishes => one hold; B nonterminal cannot
relinquish; Runtime native PG close rejects with B held under the SAME
advisory lock; B terminal + handoff + relinquishment => zero holds; only
then Runtime's pre-existing Job/PG/Git/FS checks can decide whether to close.

A missing observation is UNKNOWN, never permission to delete. No SQLite,
second GC daemon, cross-owner direct SQL table grant, automatic retry,
or unqualified production database mutation is introduced.

## Formal refinement and independent negative tests

The existing WorkspaceMultiAgentReleaseR1 already shows that one consumer
cannot release another. RuntimeWorkspaceClaimBirthR2 further separates two
independent facts:

1. Registered claims: the same-PG advisory fence serializes Harness Run
   birth with native Workspace close, and blocks close while a claim is held.
   Real PG18 tests exercise the implemented source candidate.
2. Prospective Run birth / Workspace epoch: Runtime has no durable consumer
   intent for Runs not yet created. A claim-only close can remove a Workspace
   before B registers; HarnessAgentRun.create can also register B after a
   physical close because no shared positive Workspace-open epoch is checked
   inside its PG birth transaction.

The pinned TLA+ toolchain checks the qualified source design using
scripts/tla-formal check-h2-claim and falsify-h2-claim. The positive model
checks 17 states. Three named counterexamples prove legal close reachable,
claim-only close ignoring future intent, and post-close Run birth violating
the no-closed-held-claims invariant.

**Do not call H2 production complete or enable automatic Workspace cleanup
based on these claims until a source-qualified Workspace-open epoch /
prospective-consumer admission protocol proves the missing boundary.**
An empty Job list, a four-hour timer, or a caller Boolean is not that proof.

## Physical consumer graph and implementation ownership

- AGENT: HarnessAgentRun.create and HarnessAgentRun.open bind one source-qualified
  execution grant (or explicit Runtime execution binding) to one existing Run.
- RUN AUTHORITY: PostgresHarnessStore.create_run writes the Run's original
  Journal and run_workspace_claims under one transaction and Runtime's
  existing 79245017 advisory lock. Every active known consumer has a hold
  until exact terminal revision plus owner-side explicit relinquishment.
- CROSS-OWNER PORT: the operator migrates only the existing Harness PG schema
  and grants a private SECURITY DEFINER aggregate, never direct Harness row
  access, to the Runtime role.
- PHYSICAL AUTHORITY: PgRuntime::close_workspace holds the same PG admission
  lock, rejects active Runtime Jobs / reservations, unknown older Harness
  Runs and nonzero claims, then applies its preexisting Git/source/dirty
  validation and native Workspace close.
- TEST CONSUMERS: actual PG18 A/B Run facts, SQL role permission negative,
  concurrent birth versus Runtime lock, Rust original Harness SQL consumer,
  mature TLA+ finite counterexamples, Rust Core/Clippy, owner-boundary checker.
- LIMIT: direct Gateway/Runtime users and Workspace-to-Run future handoff are
  not currently registered by this Harness-only carrier. Both require
  consumer evidence before the full cleanup gate can be declared qualified.

Source paths: services/harness/src/ordivon_harness/postgres_store.py,
services/harness/src/ordivon_harness/agent_run.py,
services/runtime/crates/ordivon-runtime-core/src/runtime/pg_runtime/workspace.rs,
services/runtime/formal/RuntimeWorkspaceClaimBirthR2.tla,
services/harness/scripts/test_runtime_workspace_claims_pg18.sh.

This graph is source evidence, not a statement that any installed Runtime
service already consumes the new aggregate function or SQL migration.
