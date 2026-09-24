# Ordivon Capital — Current State

Truth role: **generated rebuildable projection, not authority**. Run `scripts/build-current-state-r2`; machine-readable authorities win on conflict.

## Source and ownership

Canonical source owner is `domains/capital`. Active source-owner domains: Markets, Trading, Portfolio, Risk, Research, Governance, Accounting. Generic task-local composition mechanics are owned by `packages/composition`; Capital retains financial LEGO, authority/effect, reconciliation and accounting semantics.

## Current authority standing

| Boundary | Current standing |
| --- | --- |
| Protocol identity | `ACTIVE_V2_NO_RUNTIME_V1_SHIM` / schema v2 |
| Execution lane | `NON_LIVE` |
| Production external financial write | `BLOCK_NOT_GRANTED` / allowed=false |
| Portfolio risk budget | `UNSET` / owner `OWNER_PRINCIPAL` |
| Private account data | `NOT_ADMITTED` / allowed=false |
| Local accounting mechanics | `PASS_BOUNDED_SQLITE_WAL_ACCOUNTING` |
| U.S. Treasury nominal/real observation | `ACTIVE_OFFICIAL_PUBLIC_OWNER` / `ACTIVE_OFFICIAL_PUBLIC_OWNER` |
| Brent/WTI observation | `EXTERNAL_CREDENTIAL_REQUIRED_NOT_INTEGRATED` |
| Fed policy repricing observation | `EXTERNAL_SUBSCRIPTION_REQUIRED_NOT_INTEGRATED` |
| SOXL benchmark identity | `NYSE Semiconductor Index` / `ICESEMIT` / daily target `3.0x` |

## R2 architecture

```text
Financial Circuit Spec
        ↓
Capital financial semantic lowering
        ↓
Ordivon Cognitive Circuit + Authority Obligations
        ↓
owner-native Capital functions
        ↓
provider/local reality
        ↓
Capital reconciliation/accounting
```

Registry: 39 entries, 34 canonical; functional LEGO roles: 12.

## Laws

- Provider reality remains authoritative for external financial facts.
- Shared Composition grants no financial/provider/execution authority.
- Capital has no canonical production/live external-write implementation.
- `UNSET` owner risk budget remains `UNSET`; it is never inferred.
- Historical evidence and prior R1 projections do not become current merely because Git is recent.
- Official macro observation owners remain distinct from interpretation and financial decision authority.
- Derivative observations and factor proxies do not replace SOXL cash-fund or benchmark identity authority.
