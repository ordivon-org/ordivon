# Wave A / M3 — Market Data Boundary

## Purpose

Establish the distinction between public official market-structure data and credential/licence-gated symbol-level price data.

## Public official path

Cboe publishes U.S. equities historical market-volume files based on UTDF and CTS consolidated data feeds. M3 consumes the 2026 daily CSV and produces a validated Parquet dataset containing:

- total daily shares across reported market centers;
- total daily notional;
- total daily trade count;
- shares reported through TRFs;
- TRF share of reported market volume.

This is market-structure/context data, **not symbol-level price history**.

## Symbol-level bars

Production-grade symbol-level historical/delayed/real-time bars remain `CREDENTIAL_GATED`.
Preferred future paths:

1. Nasdaq Data Link / exchange-provided data under the appropriate subscription or trial;
2. the selected broker/venue feed when broker admission begins.

Yahoo Finance and Stooq may be useful convenience research sources in other contexts, but they must not be promoted to execution/reconciliation authority in Market Capital.
