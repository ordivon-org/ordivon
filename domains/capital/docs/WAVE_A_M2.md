# Wave A / M2 — Official Issuer Fundamentals

## Purpose

Add an authoritative issuer/fundamental information path without introducing a trading runtime or a custom financial-data ontology.

```text
SEC CIK configuration
  -> SEC data.sec.gov Company Facts API
  -> US-GAAP facts extracted from issuer XBRL filings by SEC
  -> annual 10-K fact selection
  -> Research E2E / pandas / Pandera
  -> Parquet research features
  -> MLflow lineage
```

## Selected concepts

M2 deliberately uses only concepts present consistently across the current validation universe:

- `us-gaap:NetIncomeLoss`
- `us-gaap:Assets`
- `us-gaap:StockholdersEquity`

It does **not** force a universal revenue field: the observed issuers do not expose one common current annual revenue concept consistently enough for a fail-closed first implementation.

## Research calculations

- ROA proxy = annual NetIncomeLoss / year-end Assets from the same 10-K filing.
- ROE proxy = annual NetIncomeLoss / year-end StockholdersEquity from the same 10-K filing.
- Equity/assets = year-end StockholdersEquity / year-end Assets from the same 10-K filing.

These are validation features, not alpha claims or investment recommendations.

## Arelle status

Arelle 2.44.7 is installed and already passed local XBRL validation in earlier admission work. Direct Runtime access to the SEC archive filing HTML endpoint currently returns HTTP 403 on direct and both local proxy paths, so a **real SEC filing -> local Arelle** validation remains an explicit network/access gate rather than being falsely marked complete. SEC Company Facts remains authoritative SEC-published XBRL-derived data and is sufficient for this M2 slice.
