# Ordivon Market Capital — Clean Room

Clean-room composition of mature external standards and implementations.

Business backbone: CFA investment-management process.
Trading semantics: FIX.
Trading runtime: pinned QuantConnect LEAN (installed and admitted for bounded non-live Wave B execution).
Post-trade reference semantics: PFMI + ISO 20022; broker/custodian infrastructure remains authoritative.
Issuer reporting: XBRL/iXBRL + Arelle.
Research: existing Ordivon Research E2E / MLflow.

## Current standing

Wave A is closed on the investment side:

`Mandate / IPS -> authoritative data -> research artifact -> portfolio construction -> target portfolio`

Wave B / M1 admits bounded historical execution through pinned QuantConnect LEAN. M2 adds LEAN-native pre-trade feasibility, M3 admits provenance-recorded Nasdaq historical OHLCV while remaining non-causal, M4 inserts QuickFIX/n FIX 4.4 `NewOrderSingle` semantics, M5 adds a fail-closed causal-shadow gate, M6 freezes a pre-market shadow order plan from the last pre-decision provider-origin close, and M6.1 binds every current trading runner to the exact external `market-capital-v2` authority-waist revision/contracts before LEAN starts. M5 is currently `WAITING_FOR_POST_DECISION_DATA`; M6 has emitted no LEAN orders or external effects. No FIX session, broker credential, venue write, or external financial write is admitted. Production/live authorization remains `BLOCK_NOT_GRANTED`. See the Wave B documents under `docs/`.

This repository does not import legacy Ordivon finance/Market Capital code or schemas.
