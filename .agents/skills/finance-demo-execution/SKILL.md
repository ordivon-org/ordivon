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
