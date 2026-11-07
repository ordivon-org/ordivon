---
name: finance-demo-execution
description: Use the existing Capital Trading owner to read OKX Demo SPOT, submit one admitted Demo limit intent, recover UNKNOWN external effects by clOrdId, query fills/cancel, and reconcile with Accounting PostgreSQL. Never claim broker success from a Runtime exit code.
compatibility: Ordivon domains/capital; Python; credential-bound Runtime; OKX Demo API v5
metadata:
  source-authority: Ordivon Capital Trading, Governance and Accounting
---

# Finance Demo Execution — Agent Capability Router

This is an operational capability router, not a second Agent scheduler, OMS,
portfolio optimizer or accounting system. Canonical operator:
ordivon_capital.trading.okx_demo_execution. Native entrypoint:
domains/capital/scripts/run-okx-demo-execution.

Use for real *Demo* external execution and recovery, not retrospective replay.
Provider owns orders and fills, Trading owns normalized venue facts,
Accounting PostgreSQL owns journal truth, Runtime owns Job/Attempt recovery.

## Agent procedure — before any external POST

1. Inspect domains/capital/config/demo_execution_policy.json and the latest
   provider account/instrument rules. The default source policy is
   PREPARED_NOT_ADMITTED and cannot qualify external effects by itself.
2. Bind a separate Demo-only API credential with existing Runtime
   CredentialAuthority and LoadCredentialEncrypted. Never print, store
   or pass credentials through command-line, environment literals, Git or logs.
3. Bind exact instrument, order mode, limits, real cash, fees, and Risk /
   Governance authorization. Persist an immutable proposed intent with a
   unique clOrdId in the existing PostgreSQL owner before submitting any POST.
4. Execute the native CLI from domains/capital:
   scripts/run-okx-demo-execution --request request.json [--proxy-url URL]
   The versioned request is JSON with schemaVersion=1, operation,
   parameters. ACCOUNT_CONFIG and BALANCE use empty parameters.
   PLACE_LIMIT needs instrument_id, side, size, limit_price, client_order_id.
   ORDER, FILLS, CANCEL need instrument_id, venue_order_id.
   RECOVER_UNKNOWN_PLACE needs instrument_id, client_order_id.
   Write operations are denied unless current Governance policy is admitted.
5. POST ACK -> ACCEPTED_NOT_FILLED, cancel ACK ->
   CANCEL_REQUEST_ACCEPTED_NOT_CONFIRMED. On OkxDemoEffectUnknown NEVER
   automatically reissue POST. Query using persisted client_order_id.
   OKX permits terminal order clOrdId reuse; a discovered row is only
   CLIENT_ID_MATCH_REQUIRES_INTENT_CORRELATION. Match the immutable
   intent, venue order ID, creation time and fill evidence separately.
6. Query exact external order, fills and account balance, then reuse
   trading.execution_reconciliation and accounting.postgres_ledger for
   actual effect reconciliation and durable readback. Missing history
   stays UNKNOWN; no-fill cannot be inferred from a recent fills window.

## Human guidance

This is OKX SPOT cash Demo only, never LIVE. Report account readiness,
frozen intent and relevant financial constraints, exact provider order/trade
IDs, cancellation standing, PG readback and every still-UNKNOWN fact.
Source release does not mean a Demo order, a settled trade or live funds effect.

## Acceptance

Run the existing domain-native mise verify and focused test
tests/test_okx_demo_execution.py. Tests validate bounded wire formation,
effect uncertainty and provider identity, not actual orders. An external
Demo provider receipt, restart/reconciliation and PG balance readback
are separate evidence requirements. Do not add a second Agent registry,
order engine, financial ledger, or SQLite archive.

## Native PostgreSQL intent precommit (current executable entrypoint)

The current Trading CLI *enforces* precommit. Use the existing Capital
PostgreSQL DSN named ORDIVON_CAPITAL_PG_DSN through the authorized Runtime.
First call the operation STAGE_INTENT (schemaVersion: 1) with parameters
containing DemoIntent fields: intent_id, account_ref, client_order_id,
instrument_id, side, size, limit_price, decision_ref,
risk_evidence_digest and policy_evidence_digest. The last two are actual
sha256: plus 64 lowercase hex evidence identities, not fabricated values.
Result includes intentId, digest and STAGED. Operation INSPECT_INTENT
with top-level intentId reads the durable row without provider secrets.

For PLACE_LIMIT include the same top-level intentId in the JSON request.
The CLI verifies actual order fields match the frozen PG intent, then
atomically claims EFFECT_UNKNOWN in PostgreSQL before external HTTP POST.
On observed provider ACK it records the external ordId. Competing
processes cannot claim that intent again. CANCEL additionally requires
the PG-acknowledged venue_order_id and records a separate uncertain
cancel claim before POST; cancel ACK is not final cancellation.

This reuses the transactional-outbox/unknown-effect principle but
implements only the minimal Trading consumer. The PG intent is not
an Accounting settlement, custody or real venue fill.

The real PG tests are in tests/test_postgres_demo_intent.py, run
with ORDIVON_CAPITAL_PG_TEST_DSN pointing to an isolated disposable
PostgreSQL cluster. A missing test DSN produces skip, not PG proof.

## Official upstream provider integration (v1.5.0)

The Trading entrypoint selects --transport official by default. The exact
external implementation is OKX Agent Trade Kit CLI 1.5.0, pinned in
domains/capital/tools/okx_official_cli/package.json and pnpm-lock.yaml.
Run from Capital: mise run provider:okx:install, then
mise run verify:provider:okx-official. The latter runs the physical
official CLI binary against a loopback Demo protocol endpoint: signed
HTTP evidence, not an external OKX order or settled Accounting journal.

The --transport reference fallback retains the prior small Python REST
client only until provider-account and accounting parity is independently
proven. Do not build another order management service or signing SDK.
Both transports use the SAME precommitted PostgreSQL intent and unique
effect claim in okx_demo_execution.main.

Human use: scripts/run-okx-demo-execution --request request.json
--transport official. Demo credentials arrive from Runtime's dedicated
CREDENTIALS_DIRECTORY, and are projected into a private process-scoped
tmpfs config.toml profile, never process argv, environment variables
or the shared home directory. The file is removed after every invocation.
The CLI forces --demo --json --env and verifies Demo identity from the
returned JSON envelope. Regional accounts must use their actual site
(ORDIVON_OKX_SITE) and matching valid OKX HTTPS origin.

Agent behavior: first STAGE_INTENT, then INSPECT_INTENT, next a single
PG-claimed PLACE_LIMIT, then external order and fill query. CLI exit
status does not prove a venue effect; provider error and lost POST
response must not cause automatic reposting. clOrdId matches still
require original immutable intent and order time correlation.
No recent fills is not complete order-history evidence.
