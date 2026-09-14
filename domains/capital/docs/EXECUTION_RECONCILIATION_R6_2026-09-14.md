# Execution Reconciliation R6 — 2026-09-14

R6 is a thin reconciliation seam, not a replacement order-management system.

- Venue account/order/fill state remains authoritative.
- FIX 4.4 provides the execution lifecycle vocabulary (`ExecType`, `OrdStatus`, `CumQty`, `LeavesQty`).
- Market Capital retains only EffectAuthority disposition for ambiguous external effects.

Fail-closed laws:

1. A matched authoritative fill or positive executed quantity is `POSITIVE_EXECUTION` → `CONSUME`.
2. A known open/non-terminal order is `PARTIAL_OPEN` → `RETAIN`.
3. A terminal cancelled/rejected/expired order can release only when zero execution is observed and fill-query coverage is complete.
4. Mere absence from a broad snapshot is `UNKNOWN` → `RETAIN`.
5. `PROVEN_NO_EFFECT` → `RELEASE` requires an exact authoritative lookup bound to the same venue and `ClOrdID`, with both order and fill absence proven.
6. Unverified read-only permission can never release authority.

No network, credential or financial write is performed by this module.
