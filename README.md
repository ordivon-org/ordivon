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

Wave B / M1 admits bounded historical execution through pinned QuantConnect LEAN. M2 adds LEAN-native pre-trade feasibility, M3 replaces synthetic execution prices with provenance-recorded Nasdaq historical OHLCV while explicitly remaining non-causal, and M4 inserts QuickFIX/n FIX 4.4 `NewOrderSingle` semantics between sizing and execution. No FIX session, broker credential, venue write, or external financial write is admitted. Production/live authorization remains not granted. See `docs/WAVE_B_M1_ACCEPTANCE_2026-09-13.md` through `docs/WAVE_B_M4_ACCEPTANCE_2026-09-13.md`.

This repository does not import legacy Ordivon finance/Market Capital code or schemas.
