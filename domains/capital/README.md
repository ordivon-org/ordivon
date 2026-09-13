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

Wave B / M1 admits bounded historical execution through pinned QuantConnect LEAN. Wave B / M2 additionally lowers target weights through LEAN's own buying-power/order-sizing machinery with an explicit execution reserve, preventing the negative-cash feasibility failure exposed by M1. No broker credentials or external financial writes are admitted. Production/live authorization remains not granted. See `docs/WAVE_B_M1_ACCEPTANCE_2026-09-13.md` and `docs/WAVE_B_M2_ACCEPTANCE_2026-09-13.md`.

This repository does not import legacy Ordivon finance/Market Capital code or schemas.
