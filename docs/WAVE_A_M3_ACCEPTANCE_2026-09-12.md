# Wave A / M3 Acceptance — 2026-09-12

## Result

**PASS_BOUNDED** — official public U.S. equity market-structure data is operational. Symbol-level production price bars remain credential/licence-gated by design.

## Executed path

```text
Cboe public historical market-volume CSV
  -> pandas parse
  -> source-specific schema and duplicate checks
  -> daily aggregation
  -> Pandera validation
  -> Parquet
  -> DuckDB independent readback
  -> MLflow lineage
```

## Source semantics

Cboe states the public historical market-volume files are based on UTDF and CTS consolidated data feeds and contain daily shares, notional value and trade counts by U.S. market center and tape. M3 does not reinterpret this dataset as symbol-level price history.

## Latest observed context

As of 2026-09-11 in the downloaded file:

- total reported shares: approximately 14.453 billion;
- total reported notional: approximately USD 841.068 billion;
- TRF shares / total reported shares: approximately 0.5067.

These values are market-structure context only, not investment signals.

## Test evidence

Nine M1–M3 unit tests passed. M3 specifically proves:

- daily market-center aggregation;
- TRF-share calculation;
- duplicate day/participant rows fail closed;
- non-negative source values;
- Parquet can be read independently by DuckDB.

Final MLflow run: `3405cffda9644ca9a2f2aa7458429129`.

## Symbol-level price boundary

Production-grade symbol-level bars are recorded as `CREDENTIAL_GATED`.
Preferred future sources are exchange-provided Nasdaq Data Link data or the selected broker/venue feed. Convenience feeds such as Yahoo Finance or Stooq are explicitly not promoted to execution or reconciliation authority.

## Boundary

No broker, LEAN runtime, FIX session, order, transfer, withdrawal, or external financial write occurred in M3.
