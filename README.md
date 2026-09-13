# Ordivon Market Capital — Clean Room

Clean-room composition of mature external standards and implementations.

Business backbone: CFA investment-management process.
Trading semantics: FIX.
Trading runtime: QuantConnect LEAN (admitted in Wave B, not yet installed here).
Post-trade semantics: PFMI + ISO 20022.
Issuer reporting: XBRL/iXBRL + Arelle.
Research: existing Ordivon Research E2E / MLflow.

## Current standing

Wave A is closed on the investment side:

`Mandate / IPS -> authoritative data -> research artifact -> portfolio construction -> target portfolio`

Wave B / M1 admits bounded historical execution through pinned QuantConnect LEAN. M2 adds LEAN-native pre-trade feasibility, M3 replaces synthetic execution prices with provenance-recorded Nasdaq historical OHLCV while explicitly remaining non-causal, M4 inserts QuickFIX/n FIX 4.4 `NewOrderSingle` semantics between sizing and execution, and M5 adds a fail-closed causal-shadow gate anchored to the canonical Wave A decision boundary. The gate is implemented but currently `WAITING_FOR_POST_DECISION_DATA`. No FIX session, broker credential, venue write, or external financial write is admitted. Production/live authorization remains not granted. See the Wave B acceptance/gate documents under `docs/`.

This repository does not import legacy Ordivon finance/Market Capital code or schemas.
