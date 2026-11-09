---
schema_version: 1
id: harness.operations
title: Harness operational contract
type: operations
profile: engineering
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-harness
audience:
  - operator
  - builder
  - agent
updated: 2026-11-07
summary: Canonical operational contract for Harness Run execution, concurrent worker fencing, targeted reopen validation, Doctor, recovery, and escalation.
evidence_status: verified
readiness: READY
applies_to:
  - ordivon-harness
related:
  - harness.start
  - harness.architecture
  - harness.authority
---
# Operations

## Authority

The first-party CLI uses one operator-provisioned PostgreSQL Harness schema.
It is independent of Host and Runtime truth and never falls back to SQLite.

```bash
export HARNESS_PG_DSN='postgresql://<provisioned-role>@<host>/<db>'
ordivon-harness doctor
ordivon-harness status HARNESS_RUN_ID
ordivon-harness inspect HARNESS_RUN_ID
```

## Store administration

```bash
ordivon-harness store-init
ordivon-harness store-doctor
ordivon-harness store-events HARNESS_RUN_ID
```

The CLI `store-backup`, `store-verify-backup`, and `store-restore` verbs
reject PostgreSQL mode; use native PostgreSQL administration under the DBA's
authority instead. `doctor` / `store-doctor` checks the selected Harness
Store; external Provider/Runtime effects require their own reconciliation.

## Run handling

A CREATED Run is executed with `run`. A PAUSED Run requires `resume`. A terminal Run is inspected rather than executed again. Contract digest conflicts fail closed.

Multiple workers may open the same PostgreSQL Harness schema, but execution leases and Provider claim holders are instance-unique. Competing workers must lose before physical Provider/Runtime delivery; deterministic event identity is for replay/idempotency, not permission for multiple workers to execute the same dispatch.

## Provider recovery

Retained Provider Call status controls the next action. A safely failed pre-dispatch call may be retried within budget. A lost response after durable completion is replayed from Store. Ambiguous dispatch remains UNKNOWN until reconciled; transport loss is not implicit redispatch permission.

## Tool recovery

Tool intents and dispatch fences bind the exact Runtime operation and request identity. Observation-only failures may return to the model. Potentially effectful ambiguous delivery requires Runtime/domain reconciliation. The caller-supplied Runtime client remains the physical truth source.

## Escalation

| Problem | Authority |
| --- | --- |
| Harness Journal/CAS, Run revision, Provider/Tool continuity | Harness Doctor / Store tools |
| physical Workspace, Job, Attempt, Artifact or cancellation | Runtime |
| Task meaning, commitment, final verification | caller/domain/optional Host |
| unresolved ambiguous external effect | caller plus relevant external authority |

Harness may read externally supplied evidence during reconciliation but does not replace another owner's repair procedure.

## Browserless identity/effect migration procedures (independent consumers)

The remaining procedures describe *separate* Browserless conversation, wake,
and effect authorities, not the first-party Harness Run Store. Existing legacy
migration paths are not prerequisites for a fresh PG-only Harness Run epoch.
Where disposable legacy runtime data is intentionally discarded, use the
specific fresh bootstrap path only if that consumer supports it; do not
infer a live sender has stopped from the absence of its SQLite file.

### PostgreSQL role-binding cutover (independent H04 subowner)

This procedure concerns only Browserless conversation-role adoption and
affinity binding. It does not migrate general Harness Journal/CAS, CFT/session/
materialization ledgers, Runtime Job/Attempt state, or provider sessions.
PostgreSQL becomes the binding Owner only after exact SQLite identities are
imported and old write access is retired.

First identify the exact loaded Browserless config.ledger path, stop ALL old
Browserless binding writers, retain a verified source backup, and provision
the authenticated and durable PostgreSQL 18 database. This command does not
stop physical processes, prove quiescence, or contact Provider services.

The one-time cutover reads the old source with an exclusive SQLite writer
lock, imports identities in a serializable PG transaction, rejects
conflicting/missing/additional identities on first cutover, and installs
legacy write-denial triggers before releasing the source lock.
This is one-time old-authority retirement, not an SQLite repair campaign.

    export ORDIVON_CONVERSATION_BINDING_POSTGRES_DSN='postgresql://...'
    python scripts/postgres_conversation_binding.py \
      --legacy-ledger /exact/loaded/materialization-ledger.sqlite \
      --confirm-old-writers-quiesced

Capture the returned identity digest and row counts as a source-bound receipt.
The command prints no credentials. After qualifying the source, restart
Browserless with that DSN. Both the read (conversation_affinity) and write
(adopt_conversation) select PostgreSQL; every PG admission checks the old
source seal and exact identity readback without any SQLite fallback.
For a truly new installation with no legacy ledger ever present, explicit
ORDIVON_CONVERSATION_BINDING_FRESH_BOOTSTRAP=1 is possible only after
independently proving that absence. Never set that flag for migration.

Replay of an already-completed cutover accepts PG-only new roles while the
sealed older identities remain identical; a first migration requires exact
PG/source equality, not a subset. SQLite and PostgreSQL have no common atomic
two-database commit here. After ambiguous partial commit, do NOT enable PG
admission: reconcile and retry until source sealing is proven. Do not resume
old SQLite writes. Native tests use an isolated disposable PostgreSQL and
temporary SQLite fixtures, never deployed data.


### Fresh PostgreSQL Wake/Turn identities (no historical SQLite import)

When the operator explicitly discards **all prior wake/turn runtime identities**,
the existing PostgreSQL Wake Owner can admit an empty epoch without copying
SQLite. This is **not** permission to replay or resend an ambiguous external
effect: stop and reconcile old Browserless/Temporal workers and unfinished
Provider sends *before* selecting fresh identity, then prove the exact legacy
wake ledger is absent. Merely deleting an open SQLite path is not process
quiescence. Coordinate the deployed consumer atomically with the PG authority.

After provisioning an isolated PostgreSQL database, invoke the already
installed PG Owner in an operator-only process (not on a Provider effect path):

    export ORDIVON_WAKE_TURN_POSTGRES_DSN='postgresql://...'
    python -c 'import os; from pathlib import Path; from scripts.postgres_wake_turn_map import PostgresWakeTurnMap; print(PostgresWakeTurnMap(os.environ["ORDIVON_WAKE_TURN_POSTGRES_DSN"]).activate_empty_fresh(Path("/exact/absent/old-turn-ledger.sqlite")))'

This commits only the existing PG `wake_cutover=ACTIVE` marker after proving
zero destination rows; it rejects a present old source, a pending historical
migration, or a pre-populated destination. It cannot independently prove no
old process will recreate SQLite. Once old writers are stopped, enable the
consumer with **both**:

    ORDIVON_WAKE_TURN_POSTGRES_DSN=...
    ORDIVON_WAKE_TURN_FRESH_BOOTSTRAP=1

The consumer checks the absent legacy path at each wake and sends all new
wake identities to PostgreSQL. With the fresh flag set but no PG DSN, the
consumer **fails closed** rather than writing an SQLite identity. Without the
explicit fresh flag the prior sealed-source migration requirement remains.
This Wake cutover does not by itself switch Harness Run/CAS, conversation
materialization, conversation role-binding, or Turn Effect send receipts.
Do not mark those separate Owners as cut over.

### PG-only Browserless identity/effect consumer selection

The deployed Browserless owner has **three independent identity/effect seams**:
conversation role binding, wake-to-turn mapping, and external turn-send effect
receipts. To prevent a partially configured release from quietly writing a
different SQLite authority, set
`ORDIVON_BROWSERLESS_PG_IDENTITIES_EFFECTS_REQUIRED=1` **only after** all
three existing PG authorities have been independently activated, all old
Browserless/Temporal effect senders quiesced, and a coherent installed release
prepared. The following three existing DSNs are then **mandatory**:

- `ORDIVON_CONVERSATION_BINDING_POSTGRES_DSN` — affinity read/adopt
- `ORDIVON_WAKE_TURN_POSTGRES_DSN` — wake-to-turn identity allocation
- `ORDIVON_TURN_EFFECT_POSTGRES_DSN` — effect read / Provider send

In this mode, a missing DSN fails closed *before* any legacy SQLite call at
each corresponding consumer, including the separate Playwright send process.
No new registry, shared credentials file, or alternate provider transport is
introduced. Fresh wake identities additionally require
`ORDIVON_WAKE_TURN_FRESH_BOOTSTRAP=1` with an absent old wake file.
Conversation binding and turn effects retain their own established PG
activation obligations: this selection switch does **not** grant authority
to initialize them automatically and does not override the live SQLite
materialization ledger. This is a **scoped** PG-only cutover: general Harness
Run/CAS and Browserless materialization remain separate owners.

### PG-first Turn Effects: retire legacy effect writer (explicit operator cutover)

`PostgresTurnEffects.stage_legacy` deliberately stays `PENDING`; it is a copy,
not an active effect sender. To switch an **existing**, nonempty Turn Effects
owner, identify the exact Browserless effect ledger configured for that sender;
stop and reconcile all in-flight Browserless/provider effect workers first,
verify a source backup, and qualify a separate PostgreSQL 18 database with
appropriate credentials. Stopping external workers is an independent physical
obligation: the CLI's confirmation flag is not proof of quiescence.

    export ORDIVON_TURN_EFFECT_POSTGRES_DSN='postgresql://...'
    python scripts/postgres_turn_effects.py \
      --legacy-ledger /exact/loaded/turn-effects.sqlite \
      --confirm-old-writers-quiesced

The cutover command stages a canonical source digest in PG (`PENDING`), locks
the existing source against writes, rechecks all identities and PG target
rows, installs exact old-writer rejection barriers, durably commits them,
then promotes PG to `ACTIVE` only after exact post-seal readback. On an
interruption between source seal and PG commit, PG remains `PENDING` and no
new effect SEND is permitted; rerun against the same stage and source after
reconciling the interruption. After qualification, route the sender and reader
consumers to the same PG DSN, with no fallback to an old writable ledger.
The command never contacts Provider services and never authorizes their SEND.

Do **not** point this at a running production sender without verified old
worker quiescence and consumer deployment coordination. The physical PG tests
use isolated, disposable PostgreSQL databases and do not certify production
worker absence or cross-store atomicity. Retire old schema/code only after
consumer penetration proves there is no remaining durable writer.
