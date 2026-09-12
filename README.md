# Ordivon Market Capital — Clean Room

Clean-room composition of mature external standards and implementations.

Business backbone: CFA investment-management process.
Trading semantics: FIX.
Trading runtime: QuantConnect LEAN (admitted in Wave B, not yet installed here).
Post-trade semantics: PFMI + ISO 20022.
Issuer reporting: XBRL/iXBRL + Arelle.
Research: existing Ordivon Research E2E / MLflow.

## Wave A / M1

`Mandate / IPS -> authoritative data -> research artifact -> portfolio construction -> target portfolio`

This repository does not import legacy Ordivon finance/Market Capital code or schemas.
