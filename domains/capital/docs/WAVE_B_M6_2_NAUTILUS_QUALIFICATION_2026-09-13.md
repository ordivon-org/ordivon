# Market Capital — Wave B / M6.2 NautilusTrader Qualification

## Scope

NautilusTrader `2.0.0rc4` is admitted only as a **shadow qualification candidate**. This milestone does not connect a broker, use credentials, open a network trading session, or permit external financial writes. It is not M7 causal acceptance.

The candidate environment is isolated under `/root/external/nautilus-trader/2.0.0rc4` with Python `3.12.13` and an exact dependency lock digest recorded in `tools/nautilus_rc4/config/nautilus_candidate.json`.

## Result

**PARTIAL_PASS_OMS_RISK_BLOCKED_AT_OPEN_SIMULATION**.

### Proven locally

- the Nautilus order model preserves the exact M6 frozen quantities and ClientOrderIds;
- its model can represent `TimeInForce.AT_THE_OPEN`;
- a separate `DAY` lifecycle control traverses initialized → submitted → accepted → filled for all three M6-sized orders;
- a separate oversized AAPL negative control is denied by RiskEngine with `NOTIONAL_EXCEEDS_FREE_BALANCE`;
- no broker or external financial effect is involved.

### Substitution blocker

The Nautilus simulated venue in `2.0.0rc4` rejects `AT_THE_OPEN` orders with:

`time in force AT_THE_OPEN is not currently supported`

Therefore the candidate cannot currently replace the exact M6/M7 At-the-Opening shadow execution semantics. The frozen M6 experiment must not be weakened to `DAY` merely to make the candidate pass.

This is a candidate qualification finding, not evidence that all Nautilus live adapters reject `AT_THE_OPEN`. Adapter-specific capability must be verified independently before any future broker admission.

## Consequence

- LEAN remains the admitted engine for the exact M6 → M7 causal-shadow path.
- Nautilus remains useful for OMS/Risk/execution/reconciliation qualification outside this unsupported simulated At-the-Opening path.
- Broker integration stays blocked and `ProductionAuthorization` remains `BLOCK_NOT_GRANTED`.
