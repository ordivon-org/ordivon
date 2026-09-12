# Wave A / M1 Acceptance — 2026-09-12

## Result

**PASS** — first clean-room Market Capital investment-loop slice executed without legacy Market Capital code and without a trading runtime.

## Executed path

```text
CFA-informed IPS
  -> GLEIF production API
  -> exact active/ISSUED legal-entity identity selection
  -> Research E2E Python environment
  -> JSON Schema validation
  -> equal-weight validation portfolio
  -> SHA-256 manifest
  -> MLflow 3.16 SQLite tracking backend
```

## Authoritative reference identities observed

- AAPL / Apple Inc. — LEI `HWUPKR0MPOU8FGXBT394`, ACTIVE, ISSUED, US-CA.
- MSFT / MICROSOFT CORPORATION — LEI `INR2EJN1ERAN0W5ZP974`, ACTIVE, ISSUED, US-WA.
- NVDA / NVIDIA CORPORATION — LEI `549300S4KLFTLO7GSQ80`, ACTIVE, ISSUED, US-DE.

## Target portfolio

Validation-only construction method: `equal_weight_validation`.

- AAPL: 1/3
- MSFT: 1/3
- NVDA: 1/3
- cash: 0
- gross exposure: 1.0

This portfolio is deliberately not an alpha claim. It exists only to validate the CFA-IPS -> authority -> research -> portfolio boundary.

## Test evidence

Four unit tests passed:

1. exact GLEIF ISSUED match;
2. lapsed GLEIF record rejected;
3. position cap enforced;
4. missing authoritative reference fails closed.

MLflow run: `20ba3b7d559542cd9724535d1d8b4d74`.

## Artifact digests

- IPS: `cbfa492e2669ff735ea9e16904f061b1beeb8702223d086dba4906f341818570`
- universe: `fb744be75c58c6de6721616efddd70dfa4356ca617226f7941167fd833a9b4a7`
- reference entities: `2d80c275722501b0e83f35bdc19472e9b9e56cb97e2f2931ab69c6d64e16575d`
- target portfolio: `41c2c2c492fe9a4b739d5fc88c7a780071863aaec0d321e50d8761e6137437e1`

## Boundary

No broker connection, LEAN runtime, FIX session, live order, transfer, withdrawal, or other external financial write occurred in M1.

## Next gate

Wave A / M2 should add a second authoritative financial-information path (issuer/XBRL) and a real research calculation while keeping portfolio construction simple. LEAN belongs to Wave B after the investment-data/research boundary is established.
